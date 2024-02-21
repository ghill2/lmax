import asyncio
import ssl
from collections import deque
from collections.abc import Callable

from simplefix import FixMessage
from simplefix import FixParser

from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.common.component import LoggerAdapter
from nautilus_trader.core.datetime import unix_nanos_to_dt
from pytower.adapters.lmax.fix.messages import Heartbeat
from pytower.adapters.lmax.fix.messages import Logon
from pytower.adapters.lmax.fix.messages import Logout
from pytower.adapters.lmax.fix.messages import Reject
from pytower.adapters.lmax.fix.messages import TestRequest
from pytower.adapters.lmax.fix.messages import downcast_message


class LmaxFixClient:
    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        target_comp_id: str,
        logger: Logger,
        loop: asyncio.AbstractEventLoop,
        clock: LiveClock,
        heartbeat_frequency_seconds: int = 30,
        logon_timeout_seconds: int = 10,
    ):
        self._logger = logger
        self._loop = loop
        self._handlers = set()
        self._host = hostname
        self._username = username
        self._password = password
        self._target_comp_id = target_comp_id
        self._heartbeat_frequency_seconds = heartbeat_frequency_seconds
        self._logon_timeout_seconds = logon_timeout_seconds
        self._message_sequence_number = 1
        self._clock = clock
        self.is_logged_on = asyncio.Event()
        self.is_connected = False
        self.processed_count = 0
        self._event_history: deque[FixMessage] = deque(maxlen=200)
        self._log = LoggerAdapter(type(self).__name__ + self._target_comp_id, logger)

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def event_history(self):
        return self._event_history

    @property
    def clock(self) -> LiveClock:
        return self._clock

    async def connect(self) -> None:
        if self.is_connected:
            self._log.info("Already connected")
            return

        # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # ssl_context.load_verify_locations(cafile=self._cafile)

        # Define a custom SSL context with custom trust settings
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False  # Disable hostname verification
        ssl_context.verify_mode = ssl.CERT_NONE  # Disable certificate verification

        self._log.info("Opening connection")

        self._reader, self._writer = await asyncio.open_connection(self._host, 443, ssl=ssl_context)

        self._log.info("Starting recv loop")
        self._loop.create_task(self.listen())

        # Logon
        # task = asyncio.wait_for(self.is_logged_on.wait(), timeout=self._logon_timeout_seconds)
        self._log.info("Logging on...")
        await self.logon()
        await asyncio.sleep(0.25)

        self._log.info("Waiting for logon...")

        self._log.info("Connection routine completed...")

        self.is_connected = True

    # async def wait_for_logon(self) -> None:
    #     self._log.info("Waiting for logon...")
    async def wait_for_events(self, count: int) -> None:
        target = self.processed_count + count
        self._log.info(f"Waiting for processed_count: {target}")
        while True:
            await asyncio.sleep(0)
            if self.processed_count >= target:
                break
        self._log.info("Events received")
        await asyncio.sleep(0)

    async def wait_for_event(
        self,
        cls: type,
        tags: dict[str, str] | None = None,
        timeout_seconds=2,
    ) -> FixMessage:
        self._log.info(f"Waiting msg type {cls.__name__}: tags: {tags}")
        try:
            return await asyncio.wait_for(
                self._wait_for_event(cls=cls, tags=tags),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as e:
            self._log.error(
                f"Timeout occurred while waiting for event {cls.__name__} with tags {tags}",
            )
            raise e  # re-raise

    async def _wait_for_event(self, cls: type, tags: dict[str, str] | None = None) -> FixMessage:
        while True:
            await asyncio.sleep(0)
            for msg in self._event_history:
                if type(msg) is cls and (
                    tags is None
                    or all(
                        msg.get(key) is not None and msg.get(key).decode() == value
                        for key, value in tags.items()
                    )
                ):
                    # await asyncio.sleep(0)
                    return msg
            # await asyncio.sleep(0)

    async def disconnect(self) -> None:
        self._writer.close()
        await self._writer.wait_closed()

    async def listen(self):
        # try:
        parser = FixParser(
            allow_empty_values=True,  # LMAX sends empty TargetCompID
            # allow_missing_begin_string=True,
            # strip_fields_before_begin_string=False,
        )
        while True:
            # 2048 / 8
            # TODO: high byte counts are dropping messages
            raw = await self._reader.read(24)

            parser.append_buffer(raw)

            msg: FixMessage = parser.get_message()
            if msg is not None:
                await self._handle_message(downcast_message(msg))

            await asyncio.sleep(0)

        # except Exception as e:
        #     self._log.info(f"Error occurred while receiving message: {e}")
        # self._log.info(f"Handling raw: {raw.decode()})")
        # msg = raw_to_message(raw)

    async def _handle_message(self, msg: FixMessage) -> None:
        self._log.info(f"Handling message: {type(msg).__name__}({msg})")

        if type(msg) is Logon:
            await self._handle_logon(msg)
            return
        elif type(msg) is TestRequest:
            await self._handle_test_request(msg)
            return
        elif type(msg) is Logout:
            await self._handle_logout(msg)
            return
        elif type(msg) is Reject:
            await self._handle_reject(msg)
            return
        elif type(msg) is Heartbeat:
            return

        for handler in self._handlers:
            await handler(msg)

        self.processed_count += 1
        # self._log.debug(f"Processed count: {self.processed_count}")
        self._event_history.appendleft(msg)

    async def _handle_reject(self, msg: Reject) -> None:
        """
        45      RefSeqNum       MsgSeqNum of rejected message   Y       SeqNum 371
        RefTagID        The tag number of the FIX field being referenced.

        N       int 372     RefMsgType      The MsgType of the FIX message being
        referenced.        N       String 373     SessionRejectReason     Code to
        identify reason for a session-level Reject message.     N       int 58      Text
        Where possible, message to explain reason for rejection

        """

    async def _handle_logon(self, msg: Logon) -> None:
        if not self.is_logged_on.is_set():
            self._log.info("Logon response received. Client successfully logged in.")
            self.is_logged_on.set()

    async def _handle_logout(self, msg: Logout) -> None:
        reason = msg.get(58)  # Text
        self._log.info(f"Client logged out reason: {reason}")
        self.is_logged_on.clear()

    async def _handle_test_request(self, msg: TestRequest) -> None:
        return
        msg = Heartbeat()
        request_id = msg.get(112)  # TestReqID
        msg.append_pair(112, request_id)  # TestReqID
        await self.send_message(msg)

    async def send_message(self, msg: FixMessage) -> None:
        """
        Send a message to the server.
        """
        msg.append_pair(8, "FIX.4.4", header=True)  # BeginString
        msg.append_pair(35, msg.message_type, header=True)  # MsgType
        msg.append_pair(49, self._username, header=True)  # SenderCompID
        msg.append_pair(56, self._target_comp_id, header=True)  # SenderCompID
        msg.append_pair(34, self._message_sequence_number, header=True)  # MsgSeqNum

        now = unix_nanos_to_dt(self._clock.timestamp_ns())
        msg.append_pair(52, now.strftime("%Y%m%d-%H:%M:%S.%f"), header=True)  # SendingTime

        self._log.info(f"Sending message: {type(msg).__name__}({msg})")
        self._writer.write(msg.encode())

        await self._writer.drain()

        self._message_sequence_number += 1

        await asyncio.sleep(0.002)

    def register_handler(self, handler: Callable) -> None:
        """
        Register the handler for the FIX messages.
        """
        self._handlers.add(handler)

    # @property
    # def is_logged_on(self) -> bool:
    #     return self._is_logged_on.is_set()

    async def logon(self) -> None:
        msg = Logon()

        msg.append_pair(98, 0)  # EncryptMethod
        msg.append_pair(108, self._heartbeat_frequency_seconds)  # HeartBtInt
        msg.append_pair(553, self._username)
        msg.append_pair(554, self._password)
        msg.append_pair(141, "Y")  # ResetSeqNumFlag

        await self.send_message(msg)


# if __name__ == "__main__":
#
#     from nautilus_trader.common.component import Logger
#     from dotenv import dotenv_values
#     from nautilus_trader.common.component import LiveClock
#     import asyncio
#     import time
#     async def main_():
#         client = LMAXMocks.fix_client()
#         await client.connect()
#         await asyncio.sleep(0.1)

#         # raw = await client._reader.read(4096)
#         # print(raw)
#         # self._log.info(f"Handling raw: {raw})")
#         # time.sleep(1)
#         # await asyncio.sleep(0)

#     asyncio.run(main_())

# @property
# def utc_timestamp(self) -> str:
#     """
#     Return a valid UTC timestamp with LMAX format.
#     """
#     return self._clock.utc_now().strftime()

# @property
# def timestamp_ns(self) -> str:
#     """
#     Return a valid UTC timestamp with LMAX format.
#     """
#     return self._clock.utc_now().timestamp_ns()


# self._log.info("Connecting socket")
# self._socket.connect((self._host, self._port))
#     msg = raw_to_message(raw, validate=True)
#     msg = downcast_message(msg)

#     if self.__handler is None:
#         self._log.error("No handler registered.")
#     else:
#         self.__handler(msg)

# def subscribe_data(self, *args, **kwargs) -> None:
#     self.send_message(self._create_subscribe_market_data(*args, **kwargs))

# def submit_order(self, *args, **kwargs) -> None:
#     self.send_message(self._create_new_order_single(*args, **kwargs))

# def send_trade_report_request(self, *args, **kwargs) -> None:
#     self.send_message(self._create_trade_capture_report_request(*args, **kwargs))

# async def _logon(self):
#     message = FIXMessageFactory.create_logon(
#                         clock=self._clock,
#                         username=self._username,
#                         password=self._password,
#                         heartbeat_frequency_seconds=self._heartbeat_frequency_seconds,
#                 )
#     self.send_message(message)

# def send_message(self, type: str, *args, **kwargs):
#     msg = msg.append_pair(Field.MsgType.value, "V", header=True)

# def send_raw_message(self, message: bytes) -> None:

#     try:
#         self._socket.send(message)
#         self._log.info(f"Sent message: {message}")
#     except Exception as e:
#         self._log.info(f"Error occurred while sending message: {e}")


# self.send_logon_message()
# try:

# except ConnectionRefusedError:
# self._log.error("Connection refused. The server may be down or unavailable.")


# self.message_factory = FIXMessageFactory(
#                         clock=clock,
#                         username=username,
#                         target_comp_id=username,
# )
# self._hostname = hostname
# self._port = port
# self._username = username
# self._password = password

# self._heartbeat_frequency_seconds = heartbeat_frequency_seconds
# self._clock = clock

# self._message_sequence_number = 1
# self._callback = None

# def register_callback(self, callback: Callable):
#     self._callback = callback
# await self._logon()

# def send_message(self, message: FixMessage) -> None:
#     # msg = self.message_factory.add_header(message, self._message_sequence_number)
#     raw: bytes = message.encode()
#     self.send_raw_message(raw)


# Setup socket
# self._log.info("Connecting socket")
# self._socket.connect((self._hostname, self._port))

# Open an asynchronous SSL-wrapped connection
# self._reader, self._writer = await asyncio.open_connection(self._hostname, 443, ssl=self._context)
# self._log.info("Starting listener")


# try:
#     async def wait_for_logon():
#         # not self._is_logged_on
#         # await asyncio.sleep(0.1)
#         print("Waiting for logon...")
#         while not self._is_logged_on:
#             print(self._is_logged_on)
#             await asyncio.sleep(1)
#     await wait_for_logon() # asyncio.wait_for(self._logon_timeout_seconds)
#     self._log.info("Logon completed")
# except asyncio.TimeoutError:
#     self._log.error("Logon failed. The client timed out while waiting for the server's logon response")
# print(type(msg))
# print(msg.toXML())


# self.__handler = None  # registered using self.register_handler
# self._username = username
# self._password = password
# self._target_comp_id = target_comp_id
# self._heartbeat_frequency_seconds = heartbeat_frequency_seconds
# self._message_sequence_number = 1
# self._logon_timeout_seconds = logon_timeout_seconds

# context = ssl.SSLContext(purpose=ssl.Purpose.SERVER_AUTH)
# context.load_verify_locations(cafile=cafile)


# cls = _MESSAGE_TYPE_MAP[msg_type]
# msg = cls()
# msg.setString(body.replace("|", chr(1)), False)
# msg.getHeader().setField(fix.MsgType(msg_type))

# header = chr(1).join([
#         f"35={msg_type}",  # MsgType
#         f"49={self._username}",  # SenderCompID
#         f"56={self._target_comp_id}",  # TargetCompID
#         f"34={self._message_sequence_number}",  # MsgSeqNum
#         f"52={now.strftime('%Y%m%d-%H:%M:%S')}"  # SendingTime

# ])
# calculate body: the total length of the message body, excluding the FIX protocol version (8=FIX.x.y) and the body length field itself (9=xxx).

# buf += b'9=' + body_length + SOH_BYTE
# buf += b'8=' + "FIX.4.4" + SOH_BYTE
# msg = chr(1).join([
#             "8=FIX.4.4",
#             f"9={len(msg)}",
#             msg
# ])

# calculate checksum: sum up the ASCII values of all characters taking the modulo 256 of the sum.
# checksum = "{:03X}".format(sum(ord(c) for c in msg) % 256)

# msg = msg + f"10={checksum}{chr(1)}"
# msg = msg.replace("|", chr(1))
# print(msg)
# print(buf)
# fix.Message(buf.decode("ascii"), True)

# raw = msg.encode("ascii")
# ssl.PROTOCOL_TLSv1_2
# ssl_context.load_cert_chain(certfile="/Users/g1/Desktop/certificate.pem", keyfile="/Users/g1/Desktop/private.pem")
# ssl_context.load_verify_locations(cafile=cafile)
# ssl_context.verify_mode = ssl.CERT_REQUIRED
# ssl_context.check_hostname = True

# self._context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
# self._context.load_verify_locations(cafile=cafile)
# self._socket_client = SocketClient(
#     loop=loop,
#     logger=logger,
#     host=host,
#     port=port,
#     handler=self._handle_raw,
#     ssl=ssl_context,
#     encoding="ascii",
# )
# msg.setField(98, fix.EncryptMethod(0))
# msg.setField(fix.HeartBtInt(int(self._heartbeat_frequency_seconds)))
# msg.setField(fix.Username(self._username))
# msg.setField(fix.Password(self._password))
# msg.setField(fix.ResetSeqNumFlag(True))
# async def listen(self) -> None:
#     try:
#         while True:
#             raw: bytes = self._socket.recv(8192)

#             if not raw:
#                 continue  # break

#             self._handle_raw(raw)

#             await asyncio.sleep(0)

#     except Exception as e:
#         traceback.print_exc(e)
#         self._log.error(f"Error occurred while listening: {e}")

# import asyncio

# async def disconnect(self):
#     # Gracefully disconnect
#     try:
#         # Initiate a graceful shutdown
#         self._socket.shutdown(socket.SHUT_RDWR)
#     except OSError as e:
#         # Handle exceptions if the socket is already closed or has issues
#         self._log.info(f"Error during socket shutdown: {e}")
#     finally:
#         # Close the socket
#         self._socket.close()
#     self._log.info("Disconnected from the server.")

# TODO
# self._log.info("Waiting for logon response...")
# await asyncio.sleep(0)
# time.sleep(2)
# while not self._is_logged_on:
# time.sleep(0.2)
# await asyncio.sleep(0)
# self._log.info("Waiting for logon response...")
# await asyncio.sleep(0)
