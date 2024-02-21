import asyncio
from unittest.mock import AsyncMock

import pandas as pd
import pytest

from nautilus_trader.core.uuid import UUID4
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.events.order import OrderAccepted
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from pytower.adapters.lmax.fix.messages import OrderStatusRequest
from pytower.adapters.lmax.fix.messages import string_to_message
from pytower.adapters.lmax.xml.client import LmaxOrder
from pytower.tests.adapters.lmax import FIX_RESPONSES
from pytower.tests.adapters.lmax.stubs import LMAXStubs


class TestLMAXExecutionReports:
    @pytest.mark.asyncio()
    async def test_generate_request_id(self, exec_client):
        # Arrange
        fix_client = exec_client.fix_client

        fix_client.send_message = AsyncMock()
        fix_client.wait_for_event = AsyncMock(side_effect=asyncio.TimeoutError)

        # Act
        await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )
        await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-002"),
            side=OrderSide.SELL,
        )

        requests = [call[0][0] for call in fix_client.send_message.call_args_list]

        # Assert
        request_id1, request_id2 = requests[0].get(790), requests[1].get(790)
        assert request_id1 is not None and request_id2 is not None
        assert request_id1.decode() != request_id2.decode()
        assert len(request_id1) == 16
        assert len(request_id2) == 16

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_none_when_venue_order_id_and_client_order_id_is_none(
        self,
        exec_client,
    ):
        # Arrange & Act
        report = await exec_client.generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=None,
            venue_order_id=None,
        )

        # Assert
        assert report is None

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_none_when_order_not_found_in_cache(
        self,
        exec_client,
    ):
        # Arrange & Act
        report1 = await exec_client.generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
        )

        report2 = await exec_client.generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            venue_order_id=VenueOrderId("C-001"),
        )

        # Assert
        assert report1 is None
        assert report2 is None

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_none_when_no_instrument_found(
        self,
        exec_client,
    ):
        # Arrange & Act
        report = await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("UN/KNOWN.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )

        # Assert
        assert report is None

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_none_when_unknown_order_on_exchange(
        self,
        exec_client,
    ):
        # Arrange
        fix_client = exec_client.fix_client
        exec_client._generate_request_id = AsyncMock(return_value="630eed65972e3e5e")

        with open(FIX_RESPONSES / "order_status_request_unknown_order.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        async def send_report(_):
            await fix_client._handle_message(msg)

        fix_client.send_message = AsyncMock(side_effect=send_report)

        # Act
        report = await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("unknown"),
            side=OrderSide.BUY,
        )
        assert report is None

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_sends_expected_with_venue_order_id(
        self,
        exec_client,
    ):
        # Arrange
        fix_client = exec_client.fix_client
        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.1"),
            price=Price.from_str("1.12345"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        exec_client.cache.add_order(order)

        order_accepted = OrderAccepted(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=VenueOrderId("AACkAgAAAABD00Pn"),
            account_id=TestIdStubs.account_id(),
            event_id=UUID4(),
            ts_event=0,
            ts_init=0,
        )
        order.apply(order_accepted)
        exec_client.cache.update_order(order)

        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")
        fix_client.send_message = AsyncMock()
        fix_client.wait_for_event = AsyncMock(side_effect=asyncio.TimeoutError)

        # Act
        await exec_client.generate_order_status_report(
            instrument_id=order.instrument_id,
            venue_order_id=order_accepted.venue_order_id,
        )

        # Assert
        request: OrderStatusRequest = fix_client.send_message.call_args[0][0]
        assert type(request) is OrderStatusRequest
        assert request.get(790) == b"mock_request_id1"
        assert request.get(11) == b"C-001"
        assert request.get(54) == b"1"
        assert request.get(48) == b"100543"
        assert request.get(22) == b"8"
        assert len(request.pairs) == 5

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_sends_expected_with_client_order_id(
        self,
        exec_client,
    ):
        # Arrange
        fix_client = exec_client.fix_client
        fix_client.send_message = AsyncMock()
        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")
        fix_client.wait_for_event = AsyncMock(side_effect=asyncio.TimeoutError)

        # Act
        await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )

        # Assert
        request: OrderStatusRequest = fix_client.send_message.call_args[0][0]
        assert type(request) is OrderStatusRequest
        assert request.get(790) == b"mock_request_id1"
        assert request.get(11) == b"C-001"
        assert request.get(54) == b"1"
        assert request.get(48) == b"100543"
        assert request.get(22) == b"8"
        assert len(request.pairs) == 5

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_expected(self, exec_client):
        # Arrange
        fix_client = exec_client.fix_client

        message = "8=FIX.4.4|35=8|1=1|11=C-001|48=100543|22=8|54=1|37=V-001|59=1|40=2|60=20230825-23:14:16.000|6=26045.58|17=0|527=0|790=mock_request_id1|39=2|150=I|14=0.1|151=0|38=0.1|10=0"

        async def send_report(_):
            await fix_client._handle_message(string_to_message(message))

        fix_client.send_message = AsyncMock(side_effect=send_report)
        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")

        # Act
        report = await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )

        # Assert
        assert report.account_id == AccountId("LMAX-1")
        assert report.instrument_id == InstrumentId.from_str("EUR/ZAR.LMAX")
        assert report.client_order_id == ClientOrderId("C-001")
        assert report.venue_order_id == VenueOrderId("V-001")
        assert report.order_side == OrderSide.BUY
        assert report.order_type == OrderType.LIMIT
        assert report.time_in_force == TimeInForce.GTC
        assert report.order_status == OrderStatus.FILLED
        assert report.quantity == Quantity.from_str("0.1")
        assert report.filled_qty == Quantity.from_str("0.1")
        assert report.avg_px == Price.from_str("26045.58")
        assert report.ts_accepted == 1693005256000000000
        assert report.ts_last == 1693005256000000000

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_none_on_timeout(self, exec_client):
        # Arrange
        fix_client = exec_client.fix_client

        fix_client.send_message = AsyncMock()
        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")
        fix_client.wait_for_event = AsyncMock(side_effect=asyncio.TimeoutError)

        # Act
        report = await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )

        # Assert
        assert report is None

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_none_on_reject(self, exec_client):
        # Arrange
        fix_client = exec_client.fix_client

        exec_client._generate_request_id = AsyncMock(return_value="630eed65972e3e5e")

        async def send_report(_):
            with open(FIX_RESPONSES / "order_status_request_unknown_order.txt") as f:
                msg: ExecutionReport = string_to_message(f.readline())
                await fix_client._handle_message(msg)

        fix_client.send_message = AsyncMock(side_effect=send_report)

        # Act
        report = await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )

        # Assert
        assert report is None

    @pytest.mark.asyncio
    async def test_request_order_status_reports_filters_none_from_results(self, exec_client):
        pass

    @pytest.mark.asyncio()
    async def test_generate_order_status_reports_sends_expected(self, exec_client):
        # Arrange
        orders: list[LmaxOrder] = [
            LMAXStubs.order(instrumentId=100543, instructionId="C-001", quantity=0.1),
            LMAXStubs.order(instrumentId=100485, instructionId="C-002", quantity=-0.1),
        ]

        exec_client.xml_client.request_orders = AsyncMock(return_value=orders)
        exec_client._generate_order_status_report = AsyncMock(return_value=None)

        # Act
        await exec_client.generate_order_status_reports()

        # Assert
        calls = exec_client._generate_order_status_report.call_args_list

        calls[0].assert_called_with(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )
        calls[1].assert_called_with(
            instrument_id=InstrumentId.from_str("EUR/DKK.LMAX"),
            client_order_id=ClientOrderId("C-002"),
            side=OrderSide.SELL,
        )

    @pytest.mark.asyncio()
    async def test_generate_order_status_reports_skips_when_no_instrument_found_for_lmax_order(
        self,
        exec_client,
    ):
        orders: list[LmaxOrder] = [
            LMAXStubs.order(instrumentId=100543, instructionId="C-001", quantity=0.1),
            LMAXStubs.order(instrumentId=0, instructionId="C-002", quantity=-0.1),
        ]

        exec_client.xml_client.request_orders = AsyncMock(return_value=orders)
        exec_client._generate_order_status_report = AsyncMock(return_value=None)

        # Act
        await exec_client.generate_order_status_reports()

        # Assert
        exec_client._generate_order_status_report.assert_called_once_with(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )

    @pytest.mark.asyncio()
    async def test_generate_order_status_reports_returns_empty_list_when_no_lmax_orders(
        self,
        exec_client,
    ):
        orders: list[LmaxOrder] = []
        exec_client.xml_client.request_orders = AsyncMock(return_value=orders)

        # Act
        reports = await exec_client.generate_order_status_reports()

        assert len(reports) == 0

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_expected_eur_zar(self, exec_client):
        # Arrange
        fix_client = exec_client.fix_client

        msg: ExecutionReport = string_to_message(
            "8=FIX.4.4|35=8|1=1|11=C-001|48=100543|22=8|54=1|37=V-001|59=4|40=1|60=20230825-23:14:16.000|6=26045.58|17=0|527=0|790=mock_request_id1|39=2|150=I|14=0.1|151=0|38=0.1|10=0",
        )

        async def send_report(_):
            await fix_client._handle_message(msg)

        fix_client.send_message = AsyncMock(side_effect=send_report)

        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")

        # Act
        report = await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            side=OrderSide.BUY,
        )

        # Assert
        assert report.account_id == AccountId("LMAX-1")
        assert report.instrument_id == InstrumentId.from_str("EUR/ZAR.LMAX")
        assert report.client_order_id == ClientOrderId("C-001")
        assert report.venue_order_id == VenueOrderId("V-001")
        assert report.order_side == OrderSide.BUY
        assert report.order_type == OrderType.MARKET
        assert report.time_in_force == TimeInForce.FOK
        assert report.order_status == OrderStatus.FILLED
        assert report.quantity == Quantity.from_str("0.1")
        assert report.filled_qty == Quantity.from_str("0.1")
        assert report.avg_px == Price.from_str("26045.58")
        assert report.ts_accepted == 1693005256000000000
        assert report.ts_last == 1693005256000000000

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_expected_eur_dkk(self, exec_client):
        # Arrange
        fix_client = exec_client.fix_client

        msg: ExecutionReport = string_to_message(
            "8=FIX.4.4|35=8|1=1|11=C-002|48=100485|22=8|54=1|37=V-002|59=4|40=2|60=20230825-23:14:16.100|6=24045.58|17=0|527=0|790=mock_request_id1|39=2|150=I|14=0.1|151=0|38=0.1|10=0",
        )

        async def send_report(_):
            await fix_client._handle_message(msg)

        fix_client.send_message = AsyncMock(side_effect=send_report)

        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")

        # Act
        report = await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("EUR/DKK.LMAX"),
            client_order_id=ClientOrderId("C-002"),
            side=OrderSide.BUY,
        )

        # Assert
        assert report.account_id == AccountId("LMAX-1")
        assert report.instrument_id == InstrumentId.from_str("EUR/DKK.LMAX")
        assert report.client_order_id == ClientOrderId("C-002")
        assert report.venue_order_id == VenueOrderId("V-002")
        assert report.order_side == OrderSide.BUY
        assert report.order_type == OrderType.LIMIT
        assert report.time_in_force == TimeInForce.FOK
        assert report.order_status == OrderStatus.FILLED
        assert report.quantity == Quantity.from_str("0.1")
        assert report.filled_qty == Quantity.from_str("0.1")
        assert report.avg_px == Price.from_str("24045.58")
        assert report.ts_accepted == 1693005256100000000
        assert report.ts_last == 1693005256100000000

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_returns_expected_gbp_mxn(self, exec_client):
        fix_client = exec_client.fix_client

        msg: ExecutionReport = string_to_message(
            "8=FIX.4.4|35=8|1=1|11=C-003|48=100505|22=8|54=2|37=V-003|59=4|40=2|60=20230825-23:14:16.200|6=24045.58|17=0|527=0|790=mock_request_id1|39=2|150=I|14=0.1|151=0|38=0.1|10=0",
        )

        async def send_report(_):
            await fix_client._handle_message(msg)

        fix_client.send_message = AsyncMock(side_effect=send_report)

        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")

        # Act
        report = await exec_client._generate_order_status_report(
            instrument_id=InstrumentId.from_str("GBP/MXN.LMAX"),
            client_order_id=ClientOrderId("C-003"),
            side=OrderSide.SELL,
        )

        assert report.account_id == AccountId("LMAX-1")
        assert report.instrument_id == InstrumentId.from_str("GBP/MXN.LMAX")
        assert report.client_order_id == ClientOrderId("C-003")
        assert report.venue_order_id == VenueOrderId("V-003")
        assert report.order_side == OrderSide.SELL
        assert report.order_type == OrderType.LIMIT
        assert report.time_in_force == TimeInForce.FOK
        assert report.order_status == OrderStatus.FILLED
        assert report.quantity == Quantity.from_str("0.1")
        assert report.filled_qty == Quantity.from_str("0.1")
        assert report.avg_px == Price.from_str("24045.58")
        assert report.ts_accepted == 1693005256200000000
        assert report.ts_last == 1693005256200000000

    @pytest.mark.asyncio
    async def test_generate_trade_reports_returns_expected(self, exec_client):
        """
        Test `LMAXExecutionClient` generates `TradeCaptureReport` reports.
        """
        # Arrange
        fix_client = exec_client.fix_client

        # mock request ids
        request_ids = [
            "mock_request_id1",
            "mock_request_id2",
        ]
        exec_client._generate_request_id = AsyncMock(side_effect=request_ids)

        # mock messages
        messages = [
            [
                "8=FIX.4.4|35=AQ|568=mock_request_id1|569=1|263=0|749=0|750=0|10=166|",
                "8=FIX.4.4|35=AE|568=mock_request_id1|912=N|17=YlLkXgAAAAB4gW43|527=T-001|48=100485|22=8|32=0.1|31=1.00001|75=20230810|60=20230810-17:50:39.100|552=1|54=1|37=V-001|11=C-001|1=1|10=123|",
                "8=FIX.4.4|35=AE|568=mock_request_id1|912=Y|17=YlLkXgAAAAB4gXUg|527=T-002|48=100479|22=8|32=0.1|31=1.0002|75=20230810|60=20230810-17:50:39.200|552=1|54=2|37=V-002|11=C-002|1=1|10=207|",
            ],
            [
                "8=FIX.4.4|35=AQ|568=mock_request_id2|569=1|263=0|749=0|750=0|10=166|",
                "8=FIX.4.4|35=AE|568=mock_request_id2|912=N|17=YlLkXgAAAAB4gW43|527=T-003|48=100944|22=8|32=2|31=1.002|75=20230810|60=20230810-17:50:39.300|552=1|54=1|37=V-003|11=C-003|1=1|10=123|",
                "8=FIX.4.4|35=AE|568=mock_request_id2|912=Y|17=YlLkXgAAAAB4gXUg|527=T-004|48=100940|22=8|32=0.02|31=3|75=20230810|60=20230810-17:50:39.400|552=1|54=2|37=V-004|11=C-004|1=1|10=207|",
            ],
        ]

        async def send_reports(_):
            for message in messages.pop(0):
                await fix_client._handle_message(string_to_message(message))

        fix_client.send_message = AsyncMock(side_effect=send_reports)

        # Act
        end = pd.to_datetime("20230810-17:54:53.896")
        reports = await exec_client.generate_trade_reports(
            start=end - pd.Timedelta(days=8),
            end=end,
        )

        # EUR/CZK.LMAX, id=100485, size_precision=1, price_precision=5
        assert reports[0].account_id == AccountId("LMAX-1")
        assert reports[0].instrument_id == InstrumentId.from_str("EUR/DKK.LMAX")
        assert reports[0].venue_order_id == VenueOrderId("V-001")
        assert reports[0].trade_id == TradeId("T-001")
        assert reports[0].order_side == OrderSide.BUY
        assert reports[0].last_qty == Quantity.from_str("0.1")
        assert reports[0].last_px == Price.from_str("1.00001")
        assert reports[0].ts_event == 1691689839100000000
        assert reports[0].liquidity_side == LiquiditySide.TAKER
        assert reports[0].client_order_id == ClientOrderId("C-001")

        # EUR/CZK.LMAX, id=100479, size_precision=1, price_precision=4
        assert reports[1].account_id == AccountId("LMAX-1")
        assert reports[1].instrument_id == InstrumentId.from_str("EUR/CZK.LMAX")
        assert reports[1].venue_order_id == VenueOrderId("V-002")
        assert reports[1].trade_id == TradeId("T-002")
        assert reports[1].order_side == OrderSide.SELL
        assert reports[1].last_qty == Quantity.from_str("0.1")
        assert reports[1].last_px == Price.from_str("1.0002")
        assert reports[1].ts_event == 1691689839200000000
        assert reports[1].liquidity_side == LiquiditySide.TAKER
        assert reports[1].client_order_id == ClientOrderId("C-002")

        # XRP/JPY.LMAX, id=100944, size_precision=0, price_precision=3
        assert reports[2].account_id == AccountId("LMAX-1")
        assert reports[2].instrument_id == InstrumentId.from_str("XRP/JPY.LMAX")
        assert reports[2].venue_order_id == VenueOrderId("V-003")
        assert reports[2].trade_id == TradeId("T-003")
        assert reports[2].order_side == OrderSide.BUY
        assert reports[2].last_qty == Quantity.from_str("2")
        assert reports[2].last_px == Price.from_str("1.002")
        assert reports[2].ts_event == 1691689839300000000
        assert reports[2].liquidity_side == LiquiditySide.TAKER
        assert reports[2].client_order_id == ClientOrderId("C-003")

        # XBT/JPY.LMAX, id=100940, size_precision=2, price_precision=0
        assert reports[3].account_id == AccountId("LMAX-1")
        assert reports[3].instrument_id == InstrumentId.from_str("XBT/JPY.LMAX")
        assert reports[3].venue_order_id == VenueOrderId("V-004")
        assert reports[3].trade_id == TradeId("T-004")
        assert reports[3].order_side == OrderSide.SELL
        assert reports[3].last_qty == Quantity.from_str("0.02")
        assert reports[3].last_px == Price.from_str("3")
        assert reports[3].ts_event == 1691689839400000000
        assert reports[3].liquidity_side == LiquiditySide.TAKER
        assert reports[3].client_order_id == ClientOrderId("C-004")

    @pytest.mark.asyncio
    async def test_generate_trade_reports_returns_empty_list_on_invalid_request(self, exec_client):
        # Arrange
        fix_client = exec_client.fix_client

        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")

        async def send_report(_):
            message = "8=FIX.4.4|35=AQ|568=mock_request_id1|569=1|263=0|749=99|750=2|58=INVALID DATE RANGE|10=166|"
            await fix_client._handle_message(string_to_message(message))

        fix_client.send_message = AsyncMock(side_effect=send_report)

        # Act
        # Act
        end = pd.to_datetime("20230810-17:54:53.896")
        reports = await exec_client.generate_trade_reports(
            start=end - pd.Timedelta(days=8),
            end=end,
        )

        # Assert
        assert len(reports) == 0
        assert isinstance(reports, list)

    @pytest.mark.asyncio
    async def test_generate_trade_reports_returns_empty_list_when_no_trades_found(
        self,
        exec_client,
    ):
        # Arrange
        fix_client = exec_client.fix_client

        exec_client._generate_request_id = AsyncMock(return_value="mock_request_id1")

        async def send_report(_):
            message = "8=FIX.4.4|35=AQ|568=mock_request_id1|569=1|263=0|748=0|749=99|750=2|58=NO TRADES FOUND|10=166|"
            await fix_client._handle_message(string_to_message(message))

        fix_client.send_message = AsyncMock(side_effect=send_report)

        # Act
        # Act
        end = pd.to_datetime("20230810-17:54:53.896")
        reports = await exec_client.generate_trade_reports(
            start=end - pd.Timedelta(days=8),
            end=end,
        )

        # Assert
        assert len(reports) == 0
        assert isinstance(reports, list)

    @pytest.mark.asyncio
    async def test_request_trade_reports_returns_empty_list_when_no_trades_found(self, exec_client):
        pass

    # @pytest.mark.asyncio()
    # async def test_generate_order_status_reports_returns_expected(self, exec_client):
    #     xml_client = exec_client.xml_client
    #     fix_client = exec_client.fix_client

    #     # mock request ids
    #     request_ids = [
    #         "mock_request_id1",
    #         "mock_request_id2",
    #         "mock_request_id3",
    #     ]
    #     exec_client._generate_request_id = AsyncMock(side_effect=request_ids)

    #     # mock messages
    #     messages = [
    #         "8=FIX.4.4|35=8|1=1|11=C-001|48=100543|22=8|54=1|37=V-001|59=4|40=1|60=20230825-23:14:16.000|6=26045.58|17=0|527=0|790=mock_request_id1|39=2|150=I|14=0.1|151=0|38=0.1|10=0",
    #         "8=FIX.4.4|35=8|1=1|11=C-002|48=100485|22=8|54=1|37=V-002|59=4|40=2|60=20230825-23:14:16.100|6=24045.58|17=0|527=0|790=mock_request_id2|39=2|150=I|14=0.1|151=0|38=0.1|10=0",
    #         "8=FIX.4.4|35=8|1=1|11=C-003|48=100505|22=8|54=2|37=V-003|59=4|40=2|60=20230825-23:14:16.200|6=24045.58|17=0|527=0|790=mock_request_id3|39=2|150=I|14=0.1|151=0|38=0.1|10=0",
    #     ]
    #     async def send_report(_):
    #         await fix_client._handle_message(string_to_message(messages.pop(0)))

    #     fix_client.send_message = AsyncMock(side_effect=send_report)

    #     # mock xml orders
    #     orders = [
    #         LMAXStubs.order(instrumentId=100543, instructionId="C-001", quantity=0.1),
    #         LMAXStubs.order(instrumentId=100485, instructionId="C-002", quantity=0.1),
    #         LMAXStubs.order(instrumentId=100505, instructionId="C-003", quantity=-0.1),
    #     ]
    #     xml_client.request_orders = Mock(return_value=orders)

    #     # Act
    #     reports = await exec_client.generate_order_status_reports()

    #     # Assert
    #     assert len(reports) == 3

    #     assert reports[0].account_id == AccountId("LMAX-1")
    #     assert reports[0].instrument_id == InstrumentId.from_str("EUR/ZAR.LMAX")
    #     assert reports[0].client_order_id == ClientOrderId("C-001")
    #     assert reports[0].venue_order_id == VenueOrderId("V-001")
    #     assert reports[0].order_side == OrderSide.BUY
    #     assert reports[0].order_type == OrderType.MARKET
    #     assert reports[0].time_in_force == TimeInForce.FOK
    #     assert reports[0].order_status == OrderStatus.FILLED
    #     assert reports[0].quantity == Quantity.from_str("0.1")
    #     assert reports[0].filled_qty == Quantity.from_str("0.1")
    #     assert reports[0].avg_px == Price.from_str("26045.58")
    #     assert reports[0].ts_accepted == 1693005256000000000
    #     assert reports[0].ts_last == 1693005256000000000

    #     assert reports[1].account_id == AccountId("LMAX-1")
    #     assert reports[1].instrument_id == InstrumentId.from_str("EUR/DKK.LMAX")
    #     assert reports[1].client_order_id == ClientOrderId("C-002")
    #     assert reports[1].venue_order_id == VenueOrderId("V-002")
    #     assert reports[1].order_side == OrderSide.BUY
    #     assert reports[1].order_type == OrderType.LIMIT
    #     assert reports[1].time_in_force == TimeInForce.FOK
    #     assert reports[1].order_status == OrderStatus.FILLED
    #     assert reports[1].quantity == Quantity.from_str("0.1")
    #     assert reports[1].filled_qty == Quantity.from_str("0.1")
    #     assert reports[1].avg_px == Price.from_str("24045.58")
    #     assert reports[1].ts_accepted == 1693005256100000000
    #     assert reports[1].ts_last == 1693005256100000000

    #     assert reports[2].account_id == AccountId("LMAX-1")
    #     assert reports[2].instrument_id == InstrumentId.from_str("GBP/MXN.LMAX")
    #     assert reports[2].client_order_id == ClientOrderId("C-003")
    #     assert reports[2].venue_order_id == VenueOrderId("V-003")
    #     assert reports[2].order_side == OrderSide.SELL
    #     assert reports[2].order_type == OrderType.LIMIT
    #     assert reports[2].time_in_force == TimeInForce.FOK
    #     assert reports[2].order_status == OrderStatus.FILLED
    #     assert reports[2].quantity == Quantity.from_str("0.1")
    #     assert reports[2].filled_qty == Quantity.from_str("0.1")
    #     assert reports[2].avg_px == Price.from_str("24045.58")
    #     assert reports[2].ts_accepted == 1693005256200000000
    #     assert reports[2].ts_last == 1693005256200000000
    # 8=FIX.4.4|35=AQ|568=1|569=1|263=0|58=TIME_RANGE_REQUESTED_GREATER_THAN_7_DAYS|749=99|750=2|10=129

    # assert len(reports) == 2
    # assert all(type(report) is TradeReport for report in reports)
    # assert str(reports[0]) == report1_str
    # assert str(reports[1]) == report2_str

    # # Assert
    # request = self.send_mock.call_args[0][0]
    # assert type(request) is TradeCaptureReportRequest
    # assert str(request)== "569=1|580=2|60=20230810-17:50:39|60=20230810-17:54:53|568=dDDLGTBTGMqIifzn"\

    # @pytest.mark.asyncio
    # async def test_request_trade_reports(self):
    #     """
    #     Test `LMAXExecutionClient` generates `TradeCaptureReport` reports
    #     """
    #     # Arrange
    #     # msg = "8=FIX.4.4|9=147|35=AD|56=LMXBD|34=2|52=20230814-09:45:34.343750|568=qxv2rC6znT1t5Oif|569=1|580=2|60=20100101-00:00:00.000000|60=20240101-00:00:00.000000|10=224|"
    #     report1_str = "8=FIX.4.4|9=259|35=AE|49=LMXBD|34=4|52=20230814-17:05:26.094|568=dDDLGTBTGMqIifzn|912=N|17=YlLkXgAAAAB4gW43|527=QCSAEAAACLBLEI3M|48=100934|22=8|32=1|31=29394.47|75=20230810|60=20230810-17:50:39.474|552=1|54=2|37=AACkAgAAAABDJPWA|11=4858568989367916213|1=1649599582|10=123|"
    #     report2_str = "8=FIX.4.4|9=248|35=AE|49=LMXBD|34=5|52=20230814-17:05:26.094|568=dDDLGTBTGMqIifzn|912=Y|17=YlLkXgAAAAB4gXUg|527=QCSAEAAACLBLQPOO|48=100934|22=8|32=0.01|31=29400.44|75=20230810|60=20230810-17:54:53.896|552=1|54=1|37=AACkAgAAAABDJPwc|11=C-002|1=1649599582|10=207|"
    #     messages = [
    #         "8=FIX.4.4|9=100|35=AQ|49=LMXBD|34=2|52=20230814-17:05:26.094|568=dDDLGTBTGMqIifzn|569=1|263=0|749=0|750=0|10=166|",
    #         report1_str,
    #         report2_str
    #     ]

    #     # Mock request id
    #     self.request_id = "dDDLGTBTGMqIifzn"
    #     self.report_provider._generate_request_id = Mock(return_value=self.request_id)

    #     # Act
    #     async def send_messages():
    #         asyncio.sleep(0.1)
    #         for message in messages:
    #             self.report_provider.handle_message(string_to_message(message))

    #     asyncio.get_event_loop().create_task(send_messages())

    #     msg = TradeCaptureReportRequest(
    #                 start=pd.Timestamp("20230810-17:50:39.474"),
    #                 end=pd.Timestamp("20230810-17:54:53.896"),
    #     )
    #     reports = await self.report_provider.request_trade_reports(msg=msg)
    #     assert len(reports) == 2
    #     assert all(type(report) is TradeReport for report in reports)
    #     assert str(reports[0]) == report1_str
    #     assert str(reports[1]) == report2_str

    #     # Assert
    #     request = self.send_mock.call_args[0][0]
    #     assert type(request) is TradeCaptureReportRequest
    #     assert str(request)== "569=1|580=2|60=20230810-17:50:39|60=20230810-17:54:53|568=dDDLGTBTGMqIifzn"

    # # Mock report_id
    # monkeypatch.setattr(UUID4, mockreturn)
    # mock_uuid.return_value = UUID4("cdee91b9-1e1d-4133-9728-16bd76ae4ef9")
    # self.report_id = mock_uuid
    # import pytower
    # pytower.adapters.lmax.reports.UUID4 = Mock(return_value=self.report_id)

    # def setup(self):

    #     instrument_provider = LMAXMocks.instrument_provider()

    #     # Mock client
    #     self.client = LMAXMocks.fix_client()
    #     self.client.send_message = Mock()

    #     self.report_provider = LMAXReportProvider(
    #         client=self.client,
    #         instrument_provider=instrument_provider,
    #         cache=TestComponentStubs.clock(),
    #         clock=TestComponentStubs.clock(),
    #     )

    #     # Mock request id
    #     self.request_id = "&%^aUk1-s+4rk;!p"
    #     self.report_provider._generate_request_id = Mock(return_value=self.request_id)

    #     self.instrument = LMAXMocks.xbt_usd_instrument()
    #     instrument_provider.add(self.instrument)
    # def setup(self):

    #     self.fix_client = LMAXMocks.fix_client()
    #     self.instrument_provider = LMAXMocks.instrument_provider()
    #     self.xml_client = LMAXMocks.xml_client()

    #     # Mock account id
    #     cache = TestComponentStubs.cache()
    #     cache.add_account(
    #             TestExecStubs.margin_account(AccountId("LMAX-001"))
    #     )

    #     # Mock clock
    #     self.clock = Mock()
    #     self.clock.timestamp_ns.return_value = 1692036618172901000

    #     # Mock send message
    #     self.send_mock = AsyncMock()
    #     self.fix_client.send_message = self.send_mock

    #     # Add instrument
    #     self.instrument_provider.load_all_sync()
