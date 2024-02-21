import asyncio
import itertools
import secrets

import pandas as pd
from simplefix import FixMessage

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.core.datetime import unix_nanos_to_dt
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import CancelAllOrders
from nautilus_trader.execution.messages import CancelOrder
from nautilus_trader.execution.messages import ModifyOrder
from nautilus_trader.execution.messages import SubmitOrder

# from nautilus_trader.model.identifiers import VenuePositionId
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.execution.reports import TradeReport
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.currencies import GBP
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import StrategyId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.common.component import MessageBus
from pytower.adapters.lmax import LMAX_VENUE
from pytower.adapters.lmax.common import EvictingDict
from pytower.adapters.lmax.fix.client import LmaxFixClient
from pytower.adapters.lmax.fix.enums import ExecType
from pytower.adapters.lmax.fix.enums import parse_lmax_exec_type
from pytower.adapters.lmax.fix.enums import parse_lmax_order_side
from pytower.adapters.lmax.fix.enums import parse_lmax_order_status
from pytower.adapters.lmax.fix.enums import parse_lmax_order_type
from pytower.adapters.lmax.fix.messages import ExecutionReport
from pytower.adapters.lmax.fix.messages import NewOrderSingle
from pytower.adapters.lmax.fix.messages import OrderCancelReject
from pytower.adapters.lmax.fix.messages import OrderCancelReplaceRequest
from pytower.adapters.lmax.fix.messages import OrderCancelRequest
from pytower.adapters.lmax.fix.messages import OrderStatusRequest
from pytower.adapters.lmax.fix.messages import TradeCaptureReport
from pytower.adapters.lmax.fix.messages import TradeCaptureReportRequest
from pytower.adapters.lmax.fix.messages import TradeCaptureReportRequestAck
from pytower.adapters.lmax.fix.parsing import format_lmax_timestamp
from pytower.adapters.lmax.fix.parsing import parse_lmax_timestamp_ns
from pytower.adapters.lmax.providers import LmaxInstrumentProvider
from pytower.adapters.lmax.xml.client import LmaxOrder
from pytower.adapters.lmax.xml.client import LmaxXmlClient
from pytower.adapters.lmax.xml.types import LmaxOrder


class LmaxLiveExecutionClient(LiveExecutionClient):
    def __init__(
        self,
        fix_client: LmaxFixClient,
        xml_client: LmaxXmlClient,
        instrument_provider: LmaxInstrumentProvider,
        logger: Logger,
        loop: asyncio.AbstractEventLoop,
        clock: LiveClock,
        msgbus: MessageBus,
        cache: Cache,
        report_timeout_seconds: int = 5,
    ):
        super().__init__(
            loop=loop,
            client_id=ClientId(LMAX_VENUE.value),
            venue=LMAX_VENUE,
            oms_type=OmsType.NETTING,
            account_type=AccountType.MARGIN,
            base_currency=GBP,  # TODO
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            logger=logger,
        )

        self._fix_client = fix_client
        self._xml_client = xml_client
        self._instrument_provider = instrument_provider
        self._pending = EvictingDict(max_size=100_000)
        self._reports = EvictingDict(max_size=100_000)
        self._request_id_lock = asyncio.Lock()
        self._report_timeout_seconds = report_timeout_seconds
        self._fix_client.register_handler(self.handle_message)
        self._logger = logger

    @property
    def xml_client(self):
        return self._xml_client

    @property
    def fix_client(self):
        return self._fix_client

    @property
    def instrument_provider(self):
        return self._instrument_provider

    @property
    def cache(self) -> Cache:
        return self._cache

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    @property
    def msgbus(self) -> MessageBus:
        return self._msgbus

    @property
    def clock(self) -> LiveClock:
        return self._clock

    @property
    def logger(self) -> Logger:
        return self._logger

    async def _connect(self) -> None:
        await self._fix_client.connect()
        await self._xml_client.connect()
        await self._instrument_provider.initialize()

        # state: AccountState = await self._xml_client.request_account_state()
        # self._send_account_state(state)

    async def _disconnect(self) -> None:
        await self._fix_client.disconnect()
        await self._xml_client.disconnect()

    async def handle_message(self, msg: FixMessage) -> None:
        self._log.info(f"Handling message {type(msg).__name__}")
        if type(msg) is ExecutionReport:
            if msg.request_id is None:
                await self._handle_execution_report(msg)

        elif type(msg) is OrderCancelReject:
            await self._handle_order_cancel_reject(msg)

        elif type(msg) is TradeCaptureReportRequestAck:
            request_id = msg.get(568).decode()  # TradeRequestID
            self._reports[request_id] = []

        elif type(msg) is TradeCaptureReport:
            request_id = msg.get(568).decode()  # TradeRequestID
            self._reports.setdefault(request_id, []).append(msg)

    async def _handle_order_cancel_reject(self, msg: OrderCancelReject) -> None:
        # TODO: handle case If CxlRejReason=”Unknown order” this will be “NONE”.

        # reason = int(msg.get(102))  # CxlRejReason
        # client_order_id = ClientOrderId(msg.get(11).decode())  # ClOrdID
        # if reason == 1:  # Unknown order
        #     self._log.error(
        #         f"Unknown order found on exchange, client_order_id {client_order_id}",
        #     )
        #     return
        # elif reason == 6:  # Duplicate ClOrdID
        #     # should not happen occur, same client_order_id sent by client for the new order
        #     self._log.error(
        #         f"Unable to cancel order: client_order_id: {client_order_id}"
        #         " Duplicate ClOrdID(11) received for Order Cancel Replace Request",
        #     )
        #     return
        # elif reason == 2:  # Broker / Exchange Option
        #     pass
        order = self._pending.get(msg.get(11).decode())  # ClOrdId
        assert order is not None

        reponse_to = int(msg.get(434))  # CxlRejResponseTo
        if reponse_to == 1:  # Order Cancel Request
            self.generate_order_cancel_rejected(
                strategy_id=order.strategy_id,
                instrument_id=order.instrument_id,
                client_order_id=order.client_order_id,
                venue_order_id=order.venue_order_id,
                reason=msg.get(58).decode(),  # Text
                ts_event=dt_to_unix_nanos(self._utc_now()),
            )
        elif reponse_to == 2:  # 2 = Order Cancel/Replace Request
            self.generate_order_modify_rejected(
                strategy_id=order.strategy_id,
                instrument_id=order.instrument_id,
                client_order_id=order.client_order_id,
                venue_order_id=order.venue_order_id,
                reason=msg.get(58).decode(),  # Text
                ts_event=dt_to_unix_nanos(self._utc_now()),
            )

    # async def _handle_cancel_reject(self, msg: OrderCancelReject) -> None:
    #     """
    #     NOTE: Tag 37: OrderId is always None
    #     Need to get value of VenueOrderId from cache

    #     """

    #     client_order_id = ClientOrderId(msg.get(11).decode())  # OrigClOrdId

    #     order = self._cache.order(client_order_id)
    #     if order is None:
    #         self._log.error(f"Order not found for client_order_id: {client_order_id}")
    #         return

    # async def _handle_modify_reject(self, msg: OrderCancelReject) -> None:
    #     client_order_id = ClientOrderId(msg.get(41).decode())  # OrigClOrdId

    #     order = self._cache.order(client_order_id)
    #     if order is None:
    #         self._log.error(f"Order not found for client_order_id: {client_order_id}")
    #         return

    async def _handle_execution_report(self, msg: ExecutionReport) -> None:
        """
        This method only handles ExecutionReport messages without a request_id.
        """
        self._log.info(f"Handling execution report {type(msg).__name__}{msg}")

        order_status = parse_lmax_order_status(int(msg.get(39)))  # OrdStatus
        exec_type = parse_lmax_exec_type(msg.get(150).decode())  # ExecType
        if order_status == OrderStatus.ACCEPTED and exec_type == ExecType.NEW:
            await self._handle_order_accepted(msg)
        elif order_status == OrderStatus.ACCEPTED and exec_type == ExecType.REPLACE:
            await self._handle_order_updated(msg)
        elif order_status == OrderStatus.FILLED and exec_type == ExecType.TRADE:
            await self._handle_order_filled(msg)
        elif order_status == OrderStatus.REJECTED and exec_type == ExecType.REJECTED:
            await self._handle_order_rejected(msg)
        elif order_status == OrderStatus.CANCELED:
            await self._handle_order_canceled(msg)
        else:
            self._log.info("Unhandled execution report")

    async def _handle_order_accepted(self, msg: ExecutionReport) -> None:
        self._log.info("generate_order_accepted")
        instrument = self._instrument_provider.find_with_security_id(int(msg.get(48)))  # SecurityID
        assert instrument is not None  # TODO: handle this case
        client_order_id = ClientOrderId(msg.get(11).decode())
        self.generate_order_accepted(
            strategy_id=self._strategy_id(client_order_id),
            instrument_id=instrument.id,
            client_order_id=client_order_id,  # ClOrdID
            venue_order_id=VenueOrderId(msg.get(37).decode()),  # OrderID
            ts_event=parse_lmax_timestamp_ns(msg.get(60).decode()),  # TransactTime
        )

    async def _handle_order_updated(self, msg: ExecutionReport) -> None:
        self._log.info("generate_order_updated")
        instrument = self._instrument_provider.find_with_security_id(int(msg.get(48)))  # SecurityID
        assert instrument is not None  # TODO: handle this case
        client_order_id = ClientOrderId(msg.get(41).decode())  # OrigClOrdID
        self.generate_order_updated(
            strategy_id=self._strategy_id(client_order_id),
            instrument_id=instrument.id,
            client_order_id=client_order_id,
            venue_order_id=VenueOrderId(msg.get(37).decode()),  # OrderID,
            quantity=Quantity(float(msg.get(38)), instrument.size_precision),  # OrderQty
            price=Price(float(msg.get(44)), instrument.price_precision),  # Price
            trigger_price=None,
            ts_event=parse_lmax_timestamp_ns(msg.get(60).decode()),  # TransactTime
            venue_order_id_modified=True,
        )
        self._pending.pop(msg.get(11).decode())  # ClOrdId

    async def _handle_order_filled(self, msg: ExecutionReport) -> None:
        self._log.info("generate_order_filled")
        instrument = self._instrument_provider.find_with_security_id(int(msg.get(48)))  # SecurityID
        assert instrument is not None  # TODO: handle this case
        client_order_id = ClientOrderId(msg.get(11).decode())

        if self._cache.order(client_order_id) is None:
            for order in await self._xml_client.request_orders():
                print(order)

            print(msg)
            print(client_order_id)
            exit()

        assert self._cache.order(client_order_id) is not None
        self.generate_order_filled(
            strategy_id=self._strategy_id(client_order_id),
            instrument_id=instrument.id,
            client_order_id=client_order_id,  # ClOrdId
            venue_order_id=VenueOrderId(msg.get(37).decode()),  # OrderID,
            venue_position_id=None,  # missing from LMAX
            trade_id=TradeId(msg.get(527).decode()),  # SecondaryExecId
            order_side=parse_lmax_order_side(int(msg.get(54))),  # OrdStatus
            order_type=parse_lmax_order_type(int(msg.get(40))),  #  OrdType
            last_qty=Quantity(float(msg.get(32)), instrument.size_precision),  # LastQty
            last_px=Price(float(msg.get(31)), instrument.price_precision),  # LastPx
            quote_currency=instrument.quote_currency,
            commission=Money(0, instrument.base_currency),  # missing from LMAX FIX
            liquidity_side=LiquiditySide.TAKER,
            ts_event=parse_lmax_timestamp_ns(msg.get(60).decode()),  # TransactTime
        )

    async def _handle_order_rejected(self, msg: ExecutionReport) -> None:
        # rej_reason = parse_lmax_reject_reason(int(msg.get(103)))
        instrument = self._instrument_provider.find_with_security_id(int(msg.get(48)))  # SecurityID
        assert instrument is not None  # TODO: handle this case
        reason = msg.get(58).decode()  # Text
        self._log.error("generate_order_rejected")
        self._log.error(f"order rejected: {reason}")
        client_order_id = ClientOrderId(msg.get(11).decode())
        self.generate_order_rejected(
            strategy_id=self._strategy_id(client_order_id),
            instrument_id=instrument.id,
            client_order_id=client_order_id,
            reason=reason,
            ts_event=parse_lmax_timestamp_ns(msg.get(60).decode()),  # TransactTime
        )

    async def _handle_order_canceled(self, msg: ExecutionReport) -> None:
        instrument = self._instrument_provider.find_with_security_id(int(msg.get(48)))  # SecurityID
        assert instrument is not None  # TODO: handle this case
        self._log.info("generate_order_canceled")
        client_order_id = ClientOrderId(msg.get(41).decode())  # OrigClOrdID
        if self._cache.order(client_order_id) is None:
            self._log.error(f"Order not found for client_order_id: {client_order_id}...")
            return
        self.generate_order_canceled(
            strategy_id=self._strategy_id(client_order_id),
            instrument_id=instrument.id,
            client_order_id=client_order_id,
            venue_order_id=VenueOrderId(msg.get(37).decode()),  # OrderID,
            ts_event=parse_lmax_timestamp_ns(msg.get(60).decode()),  # TransactTime
        )
        self._pending.pop(msg.get(11).decode())  # ClOrdId

    async def _submit_order(self, command: SubmitOrder) -> None:
        security_id = self._instrument_provider.get_security_id(command.instrument_id)
        if security_id is None:
            self._log.error(f"Instrument not found for lmax_id: {command.instrument_id}")
            return

        order = command.order
        if order.order_type == OrderType.MARKET:
            if order.time_in_force != TimeInForce.FOK:
                self._log.error(f"{order.time_in_force} unsupported for order type MARKET")
                return
        elif order.order_type == OrderType.LIMIT:
            if order.time_in_force != TimeInForce.GTC:
                self._log.error(f"{order.time_in_force} unsupported for order type LIMIT")
                return
        else:
            self._log.error(f"unsupported order type: {order.type}")
            return

        self._log.info(f"Submitting order: {order}")

        msg = NewOrderSingle()

        msg.append_pair(11, order.client_order_id.value)  # ClOrdID

        msg.append_pair(48, security_id)  # SecurityID
        msg.append_pair(22, 8)  # SecurityIDSource: Must contain the value '8'

        msg.append_pair(54, int(order.side))  # Side

        # TransactTime: required but ignored by LMAX. Can't be an empty string. YYYYMMDD-HH:MM:SS
        msg.append_pair(60, "19700101-00:00:00")

        msg.append_pair(38, str(order.quantity))  # OrderQty

        msg.append_pair(18, "H")  # ExecInst=H (do not cancel on disconnect)

        if order.order_type == OrderType.MARKET:
            msg.append_pair(40, 1)  # OrdType: 1 = MARKET
            msg.append_pair(59, 4)  # TimeInForce: FOK
        elif order.order_type == OrderType.LIMIT:
            msg.append_pair(40, 2)  # OrdType: 2 = LIMIT
            msg.append_pair(44, str(order.price))  # Price
            msg.append_pair(59, 1)  # TimeInForce: GTC

        # assert order.time_in_force == TimeInForce.FOK  # TODO: only FOK for

        # self.generate_order_submitted(
        #     strategy_id=command.strategy_id,
        #     instrument_id=command.order.instrument_id,
        #     client_order_id=command.order.client_order_id,
        #     ts_event=self._clock.timestamp_ns(),
        # )

        await self._fix_client.send_message(msg)

    async def _cancel_all_orders(self, command: CancelAllOrders) -> None:
        self._log.info(f"Cancelling all orders: {command}")

        security_id = self._instrument_provider.get_security_id(command.instrument_id)
        if security_id is None:
            self._log.error(f"Instrument not found for lmax_id: {command.instrument_id}")
            return

        orders: list[LmaxOrder] = await self._xml_client.request_orders(
            security_id=security_id,
            side=command.order_side,
            open_only=True,
        )

        # orders = self._cache.orders_open(instrument_id=command.instrument_id)
        # for order in orders:
        #     print(order)

        if len(orders) == 0:
            self._log.info(
                f"Nothing to cancel, no open orders for instrument {command.instrument_id}",
            )
            return

        tasks = [
            self._cancel_order(
                CancelOrder(
                    trader_id=command.trader_id,
                    strategy_id=command.strategy_id,
                    instrument_id=command.instrument_id,
                    client_order_id=order.client_order_id,
                    venue_order_id=order.venue_order_id,
                    command_id=UUID4(),
                    ts_init=self._clock.timestamp_ns(),
                ),
            )
            for order in orders
        ]
        return await asyncio.gather(*tasks)

    async def _cancel_order(self, command: CancelOrder) -> None:
        self._log.info(f"Cancelling: {command}")

        security_id = self._instrument_provider.get_security_id(command.instrument_id)
        if security_id is None:
            self._log.error(f"Instrument not found for lmax_id: {command.instrument_id}")
            return

        msg = OrderCancelRequest()

        request_id = await self._generate_request_id()

        msg.append_pair(11, request_id)  # ClOrdID:

        msg.append_pair(41, command.client_order_id.value)  # OrigClOrdID

        msg.append_pair(48, security_id)  # SecurityID
        msg.append_pair(22, 8)  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)

        # TransactTime: required but ignored by LMAX. Can't be an empty string. YYYYMMDD-HH:MM:SS
        msg.append_pair(60, "19700101-00:00:00")  # TransactTime

        self._cache.order(command.client_order_id)
        # assert order is not None

        self._pending[request_id] = self._cache.order(command.client_order_id)

        await self._fix_client.send_message(msg)

    async def _modify_order(self, command: ModifyOrder) -> None:
        self._log.info(f"Modifying: {command}")
        security_id = self._instrument_provider.get_security_id(command.instrument_id)
        if security_id is None:
            self._log.error(f"Instrument not found for lmax_id: {command.instrument_id}")
            return

        order = self._cache.order(command.client_order_id)
        if order.order_type == OrderType.LIMIT:
            if order.time_in_force != TimeInForce.GTC:
                self._log.error(f"{order.time_in_force} unsupported for order type LIMIT")
                return
        else:
            self._log.error(f"unsupported order type: {order.type}")
            return

        msg = OrderCancelReplaceRequest()

        request_id = await self._generate_request_id()

        msg.append_pair(11, request_id)  # ClOrdID

        msg.append_pair(41, command.client_order_id.value)  # OrigClOrdID

        msg.append_pair(48, security_id)  # SecurityID
        msg.append_pair(22, 8)  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)

        # TransactTime: required but ignored by LMAX. Can't be an empty string. YYYYMMDD-HH:MM:SS
        msg.append_pair(60, "19700101-00:00:00")  # TransactTime

        # msg.append_pair(60, format_lmax_timestamp(self._utc_now()))  # TransactTime
        msg.append_pair(18, "H")  # ExecInst=H (do not cancel on disconnect)

        msg.append_pair(54, int(order.side))  # OrdSide

        quantity = command.quantity if command.quantity is not None else order.quantity
        msg.append_pair(38, str(quantity))  # OrderQty

        price = command.price if command.price is not None else order.price
        msg.append_pair(44, str(price))  # Price

        msg.append_pair(40, 2)  # OrdType: Limit
        msg.append_pair(59, 1)  # TimeInForce: GTC

        order = self._cache.order(command.client_order_id)
        # assert order is not None

        self._pending[request_id] = order

        await self._fix_client.send_message(msg)

    async def _generate_request_id(self) -> str:
        r"""
        790 OrdStatusReqID:
            restricted to a maximum of 16 hexadecimal characters with no leading 0 characters (essentially this is a 64bit number)
        11 ClOrdID
            Restricted to a maximum of 20 arbitrary ASCII characters
        568 TradeRequestID
            String with maximum length of 16 ASCII characters. Must be unique while a request is active. For example &%^aUk1-\+4rk;!p
        """
        async with self._request_id_lock:
            request_id = secrets.token_hex(8)
            while (
                self._pending.get(request_id) is not None
                or self._reports.get(request_id) is not None
                or request_id[0] == "0"
            ):
                request_id = secrets.token_hex(8)
            return request_id

    async def generate_order_status_reports(
        self,
        instrument_id: InstrumentId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
        open_only: bool = False,
    ) -> list[OrderStatusReport]:
        """
        LMAX XML api only returns incomplete orders. Cache is used to get completed
        orders.

        OrderStatus reconciliation stage:
        1) gets client_order_id from cache using report.client_order_id
        2) if order is not found in creates an order in the system
        3) generates a new order in the system if the order status of the report does not equal the order's orderstatus
        4) if order has been filled, it reconciles the trade, see reconiling trade report

        """
        # for order in self._cache.orders_inflight(venue=LMAX_VENUE) \
        #             + self._cache.orders_open(venue=LMAX_VENUE):
        #     orders.add((
        #             order.client_order_id,
        #             order.side,
        #             int(self._instrument_provider.instrument_id_to_lmax_id(order.instrument_id)),
        #         )
        #     )
        # security_id = self._instrument_provider.get_security_id(instrument_id=instrument_id)
        orders: list[LmaxOrder] = await self._xml_client.request_orders(
            # security_id=security_id,
            start=start,
            end=end,
            open_only=open_only,
        )

        if len(orders) == 0:
            return []

        tasks = []
        for order in orders:
            instrument = self._instrument_provider.find_with_security_id(order.instrumentId)
            if instrument is None:
                self._log.error(f"Instrument not found for instrument_id: {instrument_id}")
                continue

            tasks.append(
                self._generate_order_status_report(
                    instrument_id=instrument.id,
                    client_order_id=order.client_order_id,
                    side=order.side,
                ),
            )

        reports = await asyncio.gather(*tasks)
        reports = [report for report in reports if report is not None]
        return sorted(reports, key=lambda x: x.ts_accepted)

    async def generate_order_status_report(
        self,
        instrument_id: InstrumentId,
        client_order_id: ClientOrderId | None = None,
        venue_order_id: VenueOrderId | None = None,
    ) -> OrderStatusReport | None:
        if client_order_id is None and venue_order_id is None:
            self._log.error(
                "To request an order status report a client_order_id"
                " or venue_order_id must be provided",
            )
            return None

        if client_order_id is None:
            client_order_id = self._cache.client_order_id(venue_order_id)
            if client_order_id is None:
                self._log.error(
                    f"client_order_id not found from venue_order_id: {venue_order_id}",
                )
                return None

        order = self._cache.order(client_order_id)
        if order is None:
            self._log.error(
                f"Order not found for client_order_id: {client_order_id}",
            )
            return None

        return await self._generate_order_status_report(
            instrument_id=instrument_id,
            client_order_id=client_order_id,
            side=order.side,
        )

    async def _generate_order_status_report(
        self,
        instrument_id: InstrumentId,
        client_order_id: ClientOrderId,
        side: OrderSide,
    ) -> OrderStatusReport | None:
        instrument = self._instrument_provider.find(instrument_id)
        if instrument is None:
            self._log.error(f"Instrument not found for instrument_id: {instrument_id}")
            return None

        request_id = await self._generate_request_id()

        request = OrderStatusRequest()
        request.append_pair(790, request_id)  # OrdStatusReqID
        request.append_pair(11, client_order_id.value)  # ClOrdID
        request.append_pair(54, int(side))  # OrdSide
        request.append_pair(48, instrument.info["id"])  # SecurityID
        request.append_pair(22, 8)  # SecurityIDSource

        await self._fix_client.send_message(request)

        report = await self._wait_for_execution_report(request_id=request_id)

        return report.to_nautilus(instrument=instrument) if report is not None else None

    async def _wait_for_execution_report(self, request_id: str) -> ExecutionReport | None:
        try:
            report = await self._fix_client.wait_for_event(
                cls=ExecutionReport,
                # ExecType, OrdStatusReqId
                tags={150: "I", 790: request_id},
                timeout_seconds=self._report_timeout_seconds,
            )
        except asyncio.TimeoutError:
            self._log.warning("Timeout occurred when waiting for report")
            return None

        if report.get(103) is not None:  # OrdRejReason
            reason = report.get(58).decode()
            self._log.warning(f"ExecutionReport was rejected: reason={reason}")
            return None

        return report

    async def generate_position_status_reports(
        self,
        instrument_id: InstrumentId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> list[PositionStatusReport]:
        reports = []
        for position in await self._xml_client.request_positions(open_only=True):
            instrument = self._instrument_provider.find_with_security_id(position.instrumentId)
            assert instrument is not None
            self._log.info(str(position))
            reports.append(
                position.to_nautilus_report(instrument=instrument),
            )
        return reports

    async def generate_trade_reports(
        self,
        instrument_id: InstrumentId | None = None,
        venue_order_id: VenueOrderId | None = None,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> list[TradeReport]:
        """
        Trade Report reconciliation stage:
        1) client_order_id found in cache from venue_order_id
        2) order found in cache from client_order_id
        3) instrument found in cache from instrumet_id
        4) returns true if the report's trade_id is in the order's trade_ids
        5) uses report.ts_event to compare to order.ts_last to warn if fill applied out of chronological order from report
        """
        if end is None:
            end = unix_nanos_to_dt(self._clock.timestamp_ns())

        if start is None:
            pass  # TODO: handle this case, start should not be None

        tasks = []
        stop = end
        while True:
            end = start + pd.Timedelta(days=6)
            tasks.append(
                self._generate_trade_reports(start, end),
            )
            start += pd.Timedelta(days=6)
            if start >= stop:
                break

        reports = list(itertools.chain(*await asyncio.gather(*tasks)))
        return sorted(reports, key=lambda x: x.ts_event)

    async def _generate_trade_reports(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> list[TradeReport]:
        request = TradeCaptureReportRequest()

        request_id = await self._generate_request_id()

        request.append_pair(568, request_id)
        request.append_pair(569, 1)
        # request.append_pair(563, 263)

        request.append_pair(580, 2)
        request.append_pair(60, format_lmax_timestamp(start))
        request.append_pair(60, format_lmax_timestamp(end))

        await self._fix_client.send_message(request)

        # wait for acknowledgment
        try:
            ack = await self._fix_client.wait_for_event(
                cls=TradeCaptureReportRequestAck,
                tags={568: request_id},  # TradeRequestID
                timeout_seconds=self._report_timeout_seconds,
            )
        except asyncio.TimeoutError:
            self._log.warning("Timeout occurred when waiting for report acknowledgment")
            return []

        success = self._handle_trade_report_ack(msg=ack)
        if not success:
            return []

        # wait for last report
        try:
            await self._fix_client.wait_for_event(
                cls=TradeCaptureReport,
                # LastRptRequested, TradeRequestID
                tags={912: "Y", 568: request_id},
                timeout_seconds=self._report_timeout_seconds,
            )
        except asyncio.TimeoutError:
            self._log.warning("Timeout occurred when waiting for the last report")
            return []

        reports = self._reports.get(request_id)
        if reports is None:
            return []

        del self._reports[request_id]

        trade_reports = []
        for report in reports:
            lmax_id = int(report.get(48))  # SecurityId
            instrument = self._instrument_provider.find_with_security_id(lmax_id)
            if instrument is None:
                self._log.error(f"No instrument found for lmax_id: {lmax_id}")
                continue
            trade_reports.append(
                report.to_nautilus(instrument=instrument),
            )
        return trade_reports

    def _handle_trade_report_ack(self, msg: TradeCaptureReportRequestAck) -> bool:
        count = msg.get(748)  # TotNumTradeReports
        result = int(msg.get(749))  # TradeRequestResult
        status = int(msg.get(750))  # TradeRequestStatus
        if count == b"0":
            self._log.error("There are no trades in the requested period.")
            return False  # no trades exist
        elif result == 99 and status == 2:
            reason = msg.get(58).decode()  # Text
            self._log.error(f"Invalid trade report request: {reason}")
            return False  # invalid request
        elif result == 0 and status == 0:
            return True

    def _utc_now(self) -> pd.Timestamp:
        return self._clock.utc_now()

    def _strategy_id(self, client_order_id: ClientOrderId) -> StrategyId:
        strategy_id = self._cache.strategy_id_for_order(client_order_id)
        if strategy_id is None:
            self._log.error(
                f"Unable to process ExecutionReport:"
                f" strategy_id not found for client_order_id: {client_order_id}",
            )
            return
        return strategy_id

    # async def _generate_order_status_report(self,
    #                                         order_book_id: int,
    #                                         client_order_id: ClientOrderId,
    #                                         order_side: OrderSide
    #                                         ) -> OrderStatusReport:
    #     request = OrderStatusRequest(
    #                     order_book_id=order_book_id,
    #                     client_order_id=client_order_id,
    #                     order_side=order_side,
    #                 )
    #     reports = await self._report_provider.handle_request(request=request)
    #     report = reports[0]
    #     return self._execution_report_to_order_status_report(report)

    # async def generate_order_status_report(
    #     self,
    #     instrument_id: InstrumentId,
    #     client_order_id: Optional[ClientOrderId] = None,
    #     venue_order_id: Optional[VenueOrderId] = None,
    # ) -> Optional[OrderStatusReport]:

    #     # instrument_id = self._instrument_provider.instrument_id_to_lmax_id(instrument_id)
    #     order_book_id = self._instrument_provider.instrument_id_to_lmax_id(instrument_id)
    #     # TODO: get order_side from cache order_side = self._cache.
    #     request = OrderStatusRequest(
    #                 order_book_id=order_book_id,
    #                 client_order_id=ClientOrderId("C-994"),
    #                 order_side=OrderSide.BUY,
    #                 )

    #     reports = await self._report_provider.handle_request(request=request)
    #     return self._execution_report_to_order_status_report(reports[0])

    # async def generate_position_status_reports(
    #     self,
    #     instrument_id: Optional[InstrumentId] = None,
    #     start: Optional[pd.Timestamp] = None,
    #     end: Optional[pd.Timestamp] = None,
    # ) -> list[PositionStatusReport]:

    #     # TODO: start and end cannot be none
    #     msg = TradeCaptureReportRequest(start=start, end=end)
    #     reports = await self._report_provider.request_trade_reports(msg)

    #     return [
    #         self._trade_capture_report_to_position_status_report(report)
    #         for report in reports
    #     ]

    # async def generate_position_status_reports(self, *args, **kwargs):
    #     return await self._reports.generate_position_status_reports()

    # TradeRequestID
    # count = int(msg.get(552))  # NoSides
    # PositionStatusReport(
    #     account_id=account_id,
    #     instrument_id=self._instrument_provider.lmax_id_to_instrument_id(lmax_id),
    #     position_side=PositionSide(msg.get())
    # )

    # async def generate_trade_reports(
    #     self,
    #     instrument_id: Optional[InstrumentId] = None,
    #     venue_order_id: Optional[VenueOrderId] = None,
    #     start: Optional[pd.Timestamp] = None,
    #     end: Optional[pd.Timestamp] = None,
    # ) -> list[TradeReport]:
    #     """
    #     Generate a list of `TradeReport`s with optional query filters.

    #     The returned list may be empty if no trades match the given parameters.

    #     Parameters
    #     ----------
    #     instrument_id : InstrumentId, optional
    #         The instrument ID query filter.
    #     venue_order_id : VenueOrderId, optional
    #         The venue order ID (assigned by the venue) query filter.
    #     start : pd.Timestamp, optional
    #         The start datetime query filter.
    #     end : pd.Timestamp, optional
    #         The end datetime query filter.

    #     Returns
    #     -------
    #     list[TradeReport]

    #     """
    #     # raise NotImplementedError("method must be implemented in the subclass")  # pragma: no cover

    # """
    #     StrategyId strategy_id,
    #     InstrumentId instrument_id,
    #     ClientOrderId client_order_id,
    #     VenueOrderId venue_order_id,
    #     PositionId venue_position_id,
    #     TradeId trade_id,
    #     OrderSide order_side,
    #     OrderType order_type,
    #     Quantity last_qty,
    #     Price last_px,
    #     Currency quote_currency,
    #     Money commission,
    #     LiquiditySide liquidity_side,
    #     uint64_t ts_event,
    #     """

    # """
    # UtcTimeStamp( int hour, int minute, int second, int millisecond,
    #         int date, int month, int year )
    # """

    # msg.setField(fix.NoDates(2))

    # tag = fix.TransactTime().getTag()

    # group = fix.Group(tag, 2)
    # msg.addGroup(group)

    # print(msg.toString().replace(chr(1), "|"))
    # exit()

    # # def getGroupRef(self, num, tag):
    # msg.getGroupRef(1, tag).setField(fix.TransactTime(fix.UtcTimeStamp(
    #                                 start.hour,
    #                                 start.minute,
    #                                 start.second,
    #                                 start.microsecond,
    #                                 start.day,
    #                                 start.month,
    #                                 start.year,
    #                                 6,
    #                             )))
    # msg.getGroupRef(1, tag).setField(fix.TransactTime(fix.UtcTimeStamp(
    #                                 end.hour,
    #                                 end.minute,
    #                                 end.second,
    #                                 end.microsecond,
    #                                 end.day,
    #                                 end.month,
    #                                 end.year,
    #                                 6,
    #                             )))

    # msg.addGroup(group)

    # fix.NoDates().getTag()
    # start_fix = fix.TransactTime()
    # start_fix.setString(start.strftime("%Y%m%d-%H:%M:%S.%f"))
    # group.setField(start_fix)
    # group.setField(end)

    # end_fix = fix.TransactTime()
    # end_fix.setString(end.strftime("%Y%m%d-%H:%M:%S.%f"))

    # msg.addGroup(group)
    # 580=2|TradeDate=20230811|TransactTime=20230811-15:30:45|TransactTime=20230812-10:00:00

    # Ignored by LMAX.
    # dt: pd.Timestamp = unix_nanos_to_dt(self._clock.timestamp_ns())
    # msg.setField(fix.TransactTime(fix.UtcTimeStamp(
    #                                                 dt.hour,
    #                                                 dt.minute,
    #                                                 dt.second,
    #                                                 dt.microsecond,
    #                                                 dt.day,
    #                                                 dt.month,
    #                                                 dt.year,
    #                                                 6,
    #                                             )))

    # For OrdType = Market: Valid values: 3 = Immediate or Cancel (IOC); 4 = Fill or Kill (FOK)
    # assert order.time_in_force in (TimeInForce.IOC, TimeInForce.FOK)  # TODO: only FOK & IOC for now
    # if order.time_in_force == TimeInForce.IOC:
    #     msg.setField(fix.TimeInForce("3"))
    # elif order.time_in_force == TimeInForce.FOK:


# """
#         trader_id : TraderId
#             The trader ID for the command.
#         strategy_id : StrategyId
#             The strategy ID for the command.
#         order : Order
#             The order to submit.
#         command_id : UUID4
#             The commands ID.
#         ts_init : uint64_t
#             The UNIX timestamp (nanoseconds) when the object was initialized.
#         position_id : PositionId, optional
#             The position ID for the command.
#         client_id : ClientId, optional
#             The execution client ID for the command.
#         pass

#         class Order
#         # Identifiers
#         self.trader_id = init.trader_id
#         self.strategy_id = init.strategy_id
#         self.instrument_id = init.instrument_id
#         self.client_order_id = init.client_order_id
#         self.venue_order_id = None  # Can be None
#         self.position_id = None  # Can be None
#         self.account_id = None  # Can be None
#         self.last_trade_id = None  # Can be None

#         # Properties
#         self.side = init.side
#         self.order_type = init.order_type
#         self.quantity = init.quantity
#         self.time_in_force = init.time_in_force
#         self.liquidity_side = LiquiditySide.NO_LIQUIDITY_SIDE
#         self.is_post_only = init.post_only
#         self.is_reduce_only = init.reduce_only
#         self.emulation_trigger = init.emulation_trigger
#         self.contingency_type = init.contingency_type
#         self.order_list_id = init.order_list_id  # Can be None
#         self.linked_order_ids = init.linked_order_ids  # Can be None
#         self.parent_order_id = init.parent_order_id  # Can be None
#         self.exec_algorithm_id = init.exec_algorithm_id  # Can be None
#         self.exec_algorithm_params = init.exec_algorithm_params  # Can be None
#         self.exec_spawn_id = init.exec_spawn_id  # Can be None
#         self.tags = init.tags

#         # Execution
#         self.filled_qty = Quantity.zero_c(precision=0)
#         self.leaves_qty = init.quantity
#         self.avg_px = 0.0  # No fills yet
#         self.slippage = 0.0

#         # Timestamps
#         self.init_id = init.id
#         self.ts_init = init.ts_init
#         self.ts_last = 0  # No fills yet
#         """


# msg.addGroup(tag, group)


# )
# msg.addGroup(group)
# msg.addGroup(fix.TransactTime(fix.UtcTimeStamp(
#                                 start.hour,
#                                 start.minute,
#                                 start.second,
#                                 start.microsecond,
#                                 start.day,
#                                 start.month,
#                                 start.year,
#                                 6,
#                             )))


# msg.setField(fix.TransactTime(fix.UtcTimeStamp(start.strftime("%Y%m%d-%H:%M:%S.%f"))))
# msg.setField(fix.TransactTime(fix.UtcTimeStamp(end.strftime("%Y%m%d-%H:%M:%S.%f"))))dt: pd.Timestamp = unix_nanos_to_dt(self._clock.timestamp_ns())

# assert int(msg.get(40)) == 1  # OrdType == Market
# symbol = Symbol(msg.getField(fix.Symbol()).getString())
# last_qty = Quantity(last_qty, instrument.size_precision)
# last_px = Price(last_px, instrument.price_precision)


# # unknown order check
# report = self.generate_order_status_report(
#                 instrument_id=command.instrument_id,
#                 client_order_id=command.client_order_id,
#                 venue_order_id=command.venue_order_id,
# )
# if report is None:
#     self._log.error(f"Order does not exist on exchange")
#     self.generate_order_modify_rejected(
#         strategy_id=command.strategy_id,
#         instrument_id=command.instrument_id,
#         client_order_id=command.client_order_id,
#         venue_order_id=command.venue_order_id,
#         reason="Unknown Order",
#         ts_event=self._clock.timestamp_ns(),
#     )
#     return
# unknown order check
# report = self.request_order_status_report()
# if report is None:
#     self._log.error(f"Order does not exist on exchange")
#     self.generate_order_cancel_rejected(
#         strategy_id=command.strategy_id,
#         instrument_id=command.instrument_id,
#         client_order_id=command.client_order_id,
#         venue_order_id=command.venue_order_id,
#         reason="Unknown Order",
#         ts_event=self._clock.timestamp_ns(),
#     )
#     return


# request_id = msg.get(11).decode()  # ClOrdID

# if self._pending.get(request_id) is None:
#     self._log.error(f"No pending cancel/modify for {request_id}")
#     return

# order = self._pending[request_id]
# del self._pending[request_id]
# get instrument_id from security id
# ts_event = TransactTime


# instrument = self._instrument_provider.find_with_lmax_id(int(msg.get(48)))  # SecurityID
# assert instrument is not None  # TODO: handle this case

# # ts_event = parse_lmax_timestamp_ns(msg.get(60).decode())  # TransactTime
# # venue_order_id = VenueOrderId(msg.get(37).decode())  # OrderID

# # if exec_type == ExecType.REPLACE or exec_type == ExecType.CANCELED:
# #     client_order_id = ClientOrderId(msg.get(41).decode())  # OrigClOrdID
# # else:
# #     client_order_id = ClientOrderId(msg.get(11).decode())

# # order = self._cache.order(client_order_id)
# # if order is None:
# #     self._log.error(
# #         f"Unable to process ExecutionReport:"
# #         f" order not found for client_order_id: {client_order_id}"
# #         f" order_status: {order_status} exec_type: {exec_type}",
# #     )
# #     return
# # strategy_id = self._strategy_id(client_order_id)
# # venue_order_id = self._cache.venue_order_id(client_order_id)
