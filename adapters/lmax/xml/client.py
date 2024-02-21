from __future__ import annotations

import asyncio
import socket
import urllib
import xml.dom.minidom
import xml.sax
from collections.abc import Generator
from xml.etree import ElementTree

import aiohttp
import pandas as pd
from aiohttp import ClientResponse

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.common.component import LoggerAdapter
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.events.account import AccountState
from nautilus_trader.model.instruments.base import Instrument
from pytower.adapters.lmax.xml.enums import LmaxOrderType
from pytower.adapters.lmax.xml.sax import LMAXSaxHandler
from pytower.adapters.lmax.xml.types import LmaxAccountState
from pytower.adapters.lmax.xml.types import LmaxInstrument
from pytower.adapters.lmax.xml.types import LmaxOrder
from pytower.adapters.lmax.xml.types import LmaxPosition


class LmaxXmlClient:
    stream_lock = asyncio.Lock()

    _login_lock = asyncio.Lock()

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        clock: LiveClock,
        cache: Cache,
        logger: Logger,
        loop: asyncio.AbstractEventLoop,
        # heartbeat_interval_seconds: int = 60 * 5,
    ):
        self._hostname = hostname
        self._headers = {
            "Host": "web-order.london-demo.lmax.com",
            "Accept": "text/xml",
            "User-Agent": "LMAX .Net API, version: 1.9.0.7, id:",
            "Connection": "Keep-Alive",
            "Content-Type": "text/xml",
        }
        self._id = None
        self._username = username
        self._password = password
        self._clock = clock
        self._cache = cache
        self._log = LoggerAdapter(type(self).__name__, logger)
        self._loop = loop
        self.is_connected = False
        self._lock = asyncio.Lock()

        # self._heartbeat_interval_seconds = heartbeat_interval_seconds
        self._session_id = None
        self._logger = logger

    @property
    def hostname(self) -> str:
        return self._hostname

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def logger(self) -> str | None:
        return self._logger

    async def connect(self) -> None:
        self._log.debug("Connecting...")

        if self.is_connected:
            self._log.debug("Already connected...")
            return

        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=0,
                family=socket.AF_INET,
                ssl=True,
            ),
            base_url=self._hostname,
            headers=self._headers,
            loop=self._loop,
        )
        self.is_connected = True
        self._log.debug("Connected")

    async def disconnect(self) -> None:
        """
        Disconnect the HTTP client session.
        """
        self._log.debug(f"Closing session: {self._session}...")
        await self._session.close()
        self._log.debug("Session closed.")

    async def request_orders(
        self,
        security_id: int | None = None,
        start: pd.Timestamp = None,
        end: pd.Timestamp = None,
        side: OrderSide = None,
        order_types: list[LmaxOrderType] | None = None,
        open_only: bool = False,
    ) -> list[LmaxOrder]:
        """
        FILLED MARKET orders have a workingState of UNKNOWN Active limit orders have
        workingState of ACCEPTED with a matchedQuantity of 0 InstructionID =
        client_order_id orderId = venue_order_id Does not returned completed orders.
        """
        xml_data = await self._get_stream(subscribe="order", target_element="orders")

        root = ElementTree.fromstring(xml_data)
        orders = [LmaxOrder.from_xml(elem) for elem in root.findall(".//order")]

        if open_only is True:
            orders = [order for order in orders if float(order.matchedQuantity) == 0.0]

        filtered = [
            order
            for order in orders
            if (security_id is None or security_id == order.security_id)
            and (side is None or side == order.side)
            and (start is None or order.timestamp >= start)
            and (end is None or order.timestamp <= end)
            and (order_types is None or order.orderType in order_types)
        ]
        return sorted(filtered, key=lambda x: x.timestamp)

    async def request_positions(
        self,
        security_id: int | None = None,
        side: PositionSide = None,
        # open_only=True,
    ) -> str:
        xml_data = await self._get_stream(subscribe="position", target_element="positions")
        root = ElementTree.fromstring(xml_data)

        positions = [LmaxPosition.from_xml(elem) for elem in root.findall(".//position")]

        # if open_only is True:
        #     positions = [position for position in positions if float(position.openQuantity) > 0.0]

        filtered = [
            position
            for position in positions
            if (security_id is None or security_id == position.security_id)
            and (side is None or side == position.side)
        ]

        return filtered

    async def request_account_state(self) -> AccountState:
        xml_data = await self._get_stream(subscribe="account", target_element="accountState")
        root = ElementTree.fromstring(xml_data)
        return LmaxAccountState.from_xml(root).to_nautilus()

    async def request_instruments(self, query: str) -> list[Instrument]:
        """
        There are 2 main forms of the query string:

        To find a specific instrument the "id: (instrumentId)" form can be used.
        To do a general search, use a term such as "CURRENCY", which will find all of the currency instruments. A search term like "UK" will find all of the instruments that have "UK" in the name.
        To search for all instruments, pass an empty query string.

        On a successful call the results will be returned in a List<Instrument> containing the first 25 results, ordered alphabetically by name.
        If there are more results, the parameter hasMoreResults will be set to true.
        To retrieve the next 25 instruments do another search, passing the id from the last instrument as the offsetInstrumentId of this new search
        """
        if query != "":
            query = urllib.parse.quote(str(query).encode("utf-8"), safe="")

        offset = 0

        instruments = []
        pages = []
        async with self.stream_lock:
            while True:
                url = f"/secure/instrument/searchCurrentInstruments?q={query}&offset={offset}"

                await self.login()

                xml_data = await self.post_xml(url)

                pages.append(xml_data)

                root = ElementTree.fromstring(xml_data)
                if root.find("body").findtext("hasMoreResults") == "false":
                    break

                elems = list(root.findall(".//instrument"))
                if len(elems) == 0:
                    break

                offset = elems[-1].findtext("id")

        for xml_data in pages:
            # TODO: handle no instruments found
            root = ElementTree.fromstring(xml_data)
            for elem in root.findall(".//instrument"):
                # filter instruments with unrecognized currencies
                # filter contract instruments
                base = elem.findtext("contractUnitOfMeasure")
                quote = elem.findtext("currency")
                if Currency.from_internal_map(base) is None:
                    continue
                elif Currency.from_internal_map(quote) is None:
                    continue
                elif elem.find("aggressiveCommissionPerContract") is not None:
                    continue

                instruments.append(
                    LmaxInstrument.from_xml(elem).to_nautilus(),
                )

        return instruments

    async def login(self) -> bool:
        body = f"""
        <req>
            <body>
                <username>{self._username}</username>
                <password>{self._password}</password>
                <protocolVersion>1.8</protocolVersion>
                <productType>CFD_LIVE</productType>
            </body>
        </req>
        """

        url = "/public/security/login"
        async with self._login_lock:
            # await asyncio.sleep(0.05)  # Wait for 50 milliseconds before making the login request
            resp = await self.post(url, data=body)
        session_id = resp.cookies.get("JSESSIONID")

        if session_id is None:
            return False  # already logged in

        self._headers["Cookie"] = "JSESSIONID=" + session_id.value
        self._session_id = session_id.value
        # self.pprint(await resp.text())
        return True

    async def logout(self) -> None:
        """
        NOTE: LMAX sends a OK status responses even when not logged in
        """
        xml_data = await self.post_xml(url="/public/security/logout")
        root = ElementTree.fromstring(xml_data)
        if root.find(".//status").text == "OK":
            self._session_id = None
            if "Cookie" in self._headers.keys():
                self._headers.pop("Cookie")
            return True
        else:
            # TODO: handle failure
            pass

    async def subscribe(self, value: str) -> ClientResponse:
        data = f"<req><body><subscription><type>{value}</type></subscription></body></req>"
        return await self.post(url="/secure/subscribe", data=data)

    async def post_xml(self, url: str) -> str:
        resp = await self.post(url=url)
        return await resp.text()

    async def post(self, url: str, data: str | None = None) -> ClientResponse:
        assert self.is_connected
        async with self._session.request(
            method="POST",
            url=url,
            json=data if data is not None else "<req><body/></req>",  # required by LMAX
        ) as resp:
            await resp.text()
            return resp

    async def parse_stream(self, target_element: str) -> str:
        parser = xml.sax.make_parser()
        handler = LMAXSaxHandler(target_element=target_element)
        parser.setContentHandler(handler)

        async for chunk in self._iter_stream():
            if chunk is None:
                raise ValueError("No data returned from the server")
            parser.feed(chunk)

            if handler.get_result() is None:
                await asyncio.sleep(0)
                continue

            return handler.get_result()

    async def _get_stream(self, subscribe: str, target_element: str) -> str:
        async with self.stream_lock:
            await self.logout()
            await self.login()
            await self.subscribe(subscribe)
            xml_data = await self.parse_stream(target_element=target_element)
            await self.logout()
            return xml_data

    async def _iter_stream(self) -> Generator[bytes, None, None]:
        async with self._session.request(
            method="POST",
            url="/push/stream",
        ) as resp:
            # TODO: handle 403 Forbidden
            async for chunk in resp.content.iter_any():
                yield chunk

    # async def _generate_aggregate_urls(
    #                                 self,
    #                                 security_id: int,
    #                                 option: LMAXAggregateOption,
    #                                 resolution: LMAXAggregateResolution,
    #                                 start: pd.Timestamp,
    #                         ) -> list[str]:

    #     url_func = functools.partial(
    #         func=self._request_aggregate_urls,
    #         security_id=security_id,
    #         option=option,
    #         resolution=resolution,
    #     )
    #     async for url in self._generate_urls(url_func=url_func, start=start):
    #         yield url

    # async def _generate_top_of_book_urls(
    #                                 self,
    #                                 security_id: int,
    #                                 start: pd.Timestamp,
    #                                 end: pd.Timestamp,
    #                         ) -> list[str]:

    # async def _generate_urls(self,
    #                          url_func: Coroutine,
    #                          start: pd.Timestamp) -> Generator:
    #     history = set()
    #     end = start
    #     start -= pd.Timedelta(days=1)
    #     while True:

    #         urls = await self.url_func(start=start, end=end)
    #         if len(urls) == 0:
    #             # TODO: catch NoDataException
    #             continue

    #         for url in urls[::-1]:
    #             if url in history:
    #                 continue
    #             yield url
    #             history.add(url)

    #         # https://web-order.london-demo.lmax.com/marketdata/aggregate/4001/2023/09/2023-09-07-21-00-00-000-4001-bid-minute-aggregation.csv.gz
    #         base = urls[0].split("/")[-1]
    #         end = pd.to_datetime(
    #                     "-".join(base.split("-")[:7]),
    #                     format="%Y-%m-%d-%H-%M-%S-%f"
    #         )
    #         start = end - pd.Timedelta(days=1)


# async def read_urls(self, urls: list[str]) -> str:
#     data = ""
#     for i, url in enumerate(sorted(urls)):
#         body = await self.read_url(url)
#         if i == 0:
#             data += body
#         else:
#             data += body.split('\n', 1)[1]  # remove header
#     return data


#     asyncio.create_task(self._heartbeat_loop())

# async def _heartbeat_loop(self) -> None:

#     await self.subscribe("account")  # LMAX uses account to subscribe to heartbeats
#     heartbeat_count = 1

#     while True:

#         await asyncio.sleep(self._heartbeat_interval_seconds)

#         data = f"<req><body><token>token-{heartbeat_count}</token></body></req>"
#         resp = await self.post(url="/secure/read/heartbeat", data=data)
#         heartbeat_count += 1
#         # xml_data = await self.fetch_stream(target_element="token")
#         # NOTE: response from client when not logged in
#         # <res><header><status>WARN</status><warnings><warning><fieldName/><message>UNAUTHORISED</message></warning></warnings></header><body/><auth>UNAUTHORISED</auth></res>

# class LmaxUrlStream:
#     def __init__(self,
#                  client: LmaxHistoricXmlClient,
#                  start: pd.Timestamp,
#                  security_id: int,
#                  ):
#         self._start = start


#     async def __aiter__(self) -> Generator:
#         history = set()
#         start = self._start - pd.Timedelta(days=1)
#         end = self._start
#         while True:

#             urls = await self.request_urls(start=start, end=end)
#             if len(urls) == 0:
#                 # TODO: catch NoDataException
#                 continue

#             for url in urls[::-1]:
#                 if url in history:
#                     continue
#                 yield url
#                 history.add(url)

#             # https://web-order.london-demo.lmax.com/marketdata/aggregate/4001/2023/09/2023-09-07-21-00-00-000-4001-bid-minute-aggregation.csv.gz
#             base = urls[0].split("/")[-1]
#             end = pd.to_datetime(
#                         "-".join(base.split("-")[:7]),
#                         format="%Y-%m-%d-%H-%M-%S-%f"
#             )
#             start = end - pd.Timedelta(days=1)

# class LmaxTopOfBookUrlGenerator(LmaxUrlStream):
#     def __init__(self,
#                  client: LmaxHistoricXmlClient,
#                  start: pd.Timestamp,
#                  security_id: int,
#                  ):

#         self._client = client
#         self._security_id = security_id
#         super().__init__(start=start)

#     async def request_urls(self, start: pd.Timestamp, end: pd.Timestamp) -> list[str]:
#         return await self._client.request_top_of_book_urls(
#                             security_id=self._security_id,
#                             start=start,
#                             end=end,
#             )

# class LmaxAggregateUrlGenerator(LmaxUrlStream):
#     def __init__(self,
#                  client: LmaxHistoricXmlClient,
#                  start: pd.Timestamp,
#                  security_id: int,
#                  option: LMAXAggregateOption,
#                  resolution: LMAXAggregateResolution,
#                  ):

#         self._client = client
#         self._security_id = security_id
#         self._option = option
#         self._resolution = resolution
#         super().__init__(start=start)

#     async def request_urls(self, start: pd.Timestamp, end: pd.Timestamp) -> list[str]:
#         return await self._client.request_aggregate_urls(
#                                     security_id=self._security_id,
#                                     start=start,
#                                     end=end,
#                                     option=self._option,
#                                     resolution=self._resolution,
#             )

# # remove completed
# self._parsers = [
#     parser for parser in self._parsers
#     if parser.getContentHandler().get_result() is not None
# ]

# for parser in self._parsers:
# async def parse_stream(self) -> str:
#     self._log.debug("Listening to XML stream...")
#     async with self._session.request(
#         method="POST",
#         url="/push/stream",
#     ) as resp:
#         async for chunk in resp.content.iter_any():

#             # # remove completed
#             # self._parsers = [
#             #     parser for parser in self._parsers
#             #     if parser.getContentHandler().get_result() is not None
#             # ]

#             for parser in self._parsers:
#                 parser.feed(chunk.decode('utf-8'))

#             await asyncio.sleep(0)

# response = requests.post(url, verify=True, headers=self._headers, data=data)
# return response

# root = ElementTree.fromstring(response.text)
# status = root.find("header").find("status").text

# # TODO handle a response where the status code is not 200 OK
# # if the response to the HTTP result was not an "200 OK" then a system failure will be generated
# if status == "WARN":
#     reason = root.find("body").find("failureType").text
#     # TODO raise exception
#     assert False
# elif status == "OK":
#     return response
# else:
#     print(response.text)
#     assert False


# url = f"/secure/account/requestAccountState"
# body = """
# <req>
# <body/>
# </req>
# """

# def request_instrument(self, symbol: Symbol) -> Instrument:
#     instrument = self._instruments[symbol].get()
#     if instrument is not None:
#         return instrument
#     instrument = self._request_instrument(symbol)
#     self._instruments[symbol] = instrument
#     self._instruments_lmax[symbol] = instrument
#     return instrument
# # save responses
# from pathlib import Path
# RESPONSES_FOLDER = Path("/Users/g1/BU/projects/pytower_develop/pytower/adapters/lmax/http/responses")
# path = RESPONSES_FOLDER / f"instruments/all/all.xml"
# with open(path, "a+") as f:
#     f.write(
#         xml.dom.minidom.parseString(response.text).toprettyxml(indent="\t")
#     )

# self.pprint(response.text)

#     data = """
# <req>
#     <body>
#         <instructionId>1</instructionId>
#         <orderBookId>100934</orderBookId>
#         <from>1589155200000</from>
#         <to>1589500800000</to>
#         <aggregate>
#         <options>
#             <option>BID</option>
#         </options>
#         <resolution>DAY</resolution>
#         <depth>1</depth>
#         <format>CSV</format>
#         </aggregate>
#     </body>
# </req>
# """
# def request_orders(self) -> set[tuple[ClientOrderId, OrderSide, int]]:
#     return {
#         (
#             ClientOrderId(order["instructionId"]),
#             OrderSide.BUY if float(order["quantity"]) > 0 else OrderSide.SELL,
#             int(order["instrumentId"]),
#         )
#         for order in self._request_orders()
#     }
# filter orders by instrument_id, start, end, order_side
# def filter_order(order) -> bool:
#     if instrument_id is not None and not (order.instrument_id == instrument_id):
#         return False
#     if security_id is not None and not (order.security_id == security_id):
#         pass
#     elif side is not None and (side == OrderSide.SELL and order.quantity <= 0):
#         pass
#     elif side is not None and side == OrderSide.BUY and order.quantity >= 0:
#         pass
#     elif start is not None and order.timestamp >= start:
#         pass
#     elif end is not None and order.timestamp <= end:
#         pass
#     elif order_types is not None and order.order_type not in order_types:
#         pass
#     elif open_only is True and float(order.matched_qty) == 0.0:
#         print(float(order.matched_qty))
#         pass
# filtered = []
# for order in orders:
#     order.instrument_id == instrument_id

#     if instrument_id is not None and order.instrument_id == instrument_id
#         and \

#         pass
#     elif security_id is not None and order.security_id == security_id:
#         pass
#     elif order_side is not None and order_side == OrderSide.SELL and order.quantity <= 0:
#         pass
#     elif order_side is not None and order_side == OrderSide.BUY and order.quantity >= 0:
#         pass
#     elif start is not None and order.timestamp >= start:
#         pass
#     elif end is not None and order.timestamp <= end:
#         pass
#     elif order_types is not None and order.order_type not in order_types:
#         pass
#     elif open_only is True and float(order.matched_qty) == 0.0:
#         print(float(order.matched_qty))
#         pass
#     else:
#         continue

#     filtered.append(order)

# handler = LMAXSaxHandler(target_element=target_element)
# parser = xml.sax.make_parser()
# parser.setContentHandler(handler)

# url = f"/push/stream"
# result = None
# while result is None:
#     response = requests.post(url, verify=True, headers=self._headers, stream=True)
#     for c in response.iter_content(decode_unicode=True):
#         parser.feed(c)
#         result = handler.get_result()
#         if result is not None:
#             return result

# class LMAXInstrumentProvider(XMLClient):
#     async def request_instruments(self, instrument_ids: list[InstrumentId]) -> list[Instrument]:
#         return [
#             await self.request_instrument(instrument_id) for instrument_id in instrument_ids
#         ]

#     async def request_instrument(self, instrument_id: InstrumentId) -> Instrument:
#         instruments = await self._query_instruments(query=f"symbol: {instrument_id.symbol.value}")
#         return instruments[0]

# async def request_instruments_all(self) -> list[Instrument]:
#     return await self._query_instruments(query="CURRENCY")


# async def _get_stream(self,
#                       subscribe: str,
#                       target_element: str,
#                       url: str = None,
#                       body: str = None,
#                       reset: bool = False,
#                       ):

#     async with self._stream_lock:

#         if reset:
#             await self.logout()
#             await self.login()

#         await self.subscribe(subscribe)


#         xml_data = await self.parse_stream(target_element=target_element)

#         return xml_data
