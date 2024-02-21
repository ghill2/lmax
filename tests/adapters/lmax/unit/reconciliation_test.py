from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.execution.reports import TradeReport
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.events.order import OrderFilled
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import PositionId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.model.position import Position
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from pytower.adapters.lmax.fix.messages import string_to_message
from pytower.tests.adapters.lmax.stubs import LMAXStubs


class TestLMAXReconciliation:
    @pytest.mark.asyncio()
    async def test_recon_no_cached_with_canceled_order(self, exec_client, exec_engine):
        exec_client.generate_position_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=1|59=4|40=1|60=20230825-23:14:16.100|6=26045.58|17=0|527=0|790=1|39=4|150=I|14=0.01|151=0|38=0.02|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)

        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].status == OrderStatus.CANCELED

    @pytest.mark.asyncio()
    async def test_recon_no_cached_with_filled_limit_order(self, exec_client, exec_engine):
        """
        Confirm that a price tag of 6 gets sent when requesting status of a limit order.
        """
        exec_client.generate_position_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=1|59=4|40=2|60=20230825-23:14:16.100|6=26045.58|44=26045.58|17=0|527=0|790=1|39=2|150=I|14=0.01|151=0|38=0.01|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)

        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].status == OrderStatus.FILLED

    @pytest.mark.asyncio()
    async def test_recon_no_cached_with_filled_limit_order(self, exec_client, exec_engine):
        """
        Confirm that a price tag of 6 gets sent when requesting status of a limit order.
        """
        # Arrange
        exec_client.generate_position_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=1|59=4|40=2|60=20230825-23:14:16.100|6=26045.58|44=26045.58|17=0|527=0|790=1|39=2|150=I|14=0.01|151=0|38=0.01|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        # Act
        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].status == OrderStatus.FILLED

    @pytest.mark.asyncio()
    async def test_recon_no_cached_with_filled_market_order(self, exec_client, exec_engine):
        # Arrange

        exec_client.generate_position_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=1|59=4|40=1|60=20230825-23:14:16.100|6=26045.58|44=26045.58|17=0|527=0|790=1|39=2|150=I|14=0.01|151=0|38=0.01|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        # Act
        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].status == OrderStatus.FILLED

    @pytest.mark.asyncio()
    async def test_recon_no_cached_with_partially_filled_market_order(
        self,
        exec_client,
        exec_engine,
    ):
        # Arrange
        exec_client.generate_position_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=1|59=4|40=1|60=20230825-23:14:16.100|6=26045.58|44=26045.58|17=0|527=0|790=1|39=1|150=I|14=0.01|151=0|38=0.02|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        # Act
        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].status == OrderStatus.PARTIALLY_FILLED

    @pytest.mark.asyncio()
    async def test_recon_no_cached_with_rejected_order(self, exec_client, exec_engine):
        exec_client.generate_position_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=1|59=4|40=1|60=20230825-23:14:16.100|6=26045.58|17=0|527=0|790=1|39=8|150=I|14=0.01|151=0|38=0.01|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].status == OrderStatus.REJECTED

    @pytest.mark.asyncio()
    async def test_recon_cached_with_filled_market_order(self, exec_client, exec_engine):
        """
        Test that the cached market order quantity is updated to the report quantity.
        """
        # Arrange
        exec_client.generate_position_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        order = MarketOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.02"),
            init_id=UUID4(),
            ts_init=0,
        )

        exec_client.cache.add_order(order)

        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=1|59=4|40=1|60=20230825-23:14:16.100|6=26045.58|44=26045.58|17=0|527=0|790=1|39=2|150=I|14=0.01|151=0|38=0.01|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        # Act
        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].quantity == Quantity.from_str("0.01")

    @pytest.mark.asyncio()
    async def test_recon_cached_with_filled_limit_order(self, exec_client, exec_engine):
        """
        Test cached limit order price and quantity is updated to report price and
        quantity.
        """
        # Arrange
        exec_client.generate_position_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.02"),
            price=Price.from_str("12345.67"),
            init_id=UUID4(),
            ts_init=0,
        )

        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=1|59=4|40=2|60=20230825-23:14:16.100|6=26045.58|44=26045.58|17=0|527=0|790=1|39=2|150=I|14=0.01|151=0|38=0.01|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        # Act
        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].quantity == Quantity.from_str("0.01")
        assert exec_client.cache.orders()[0].price == Price.from_str("26045.58")

    @pytest.mark.asyncio()
    async def test_recon_no_cached_with_filled_market_order_and_trade(
        self,
        exec_client,
        exec_engine,
    ):
        """
        Test that the cached market order has OrderStatus.FILLED state instead of
        OrderStatus.INITIALIZED.
        """
        # Arrange

        order = MarketOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.02"),
            init_id=UUID4(),
            ts_init=0,
        )

        exec_client.cache.add_order(order)

        exec_client.generate_position_status_reports = AsyncMock(return_value=[])

        # venue_order_id need to match for order status and trade report
        # Mock order status report
        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=AACkAgAAAABDJPWA|59=4|40=1|60=20230825-23:14:16.100|6=26045.58|44=26045.58|17=0|527=0|790=1|39=2|150=I|14=0.01|151=0|38=0.01|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        # Mock order trade report
        msg = "8=FIX.4.4|35=AE|568=1|912=Y|17=YlLkXgAAAAB4gW43|527=QCSAEAAACLBLEI3M|48=100934|22=8|32=0.01|31=29394.47|75=20230810|60=20230825-23:14:16.200|552=1|54=1|37=AACkAgAAAABDJPWA|11=C-001|1=1|10=123|"
        report: TradeReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_trade_reports = AsyncMock(return_value=[report])

        # Act
        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].status == OrderStatus.FILLED

    @pytest.mark.asyncio()
    async def test_recon_no_cached_with_partially_filled_market_order_and_trade(
        self,
        exec_client,
        exec_engine,
    ):
        """
        Test that the cached market order has OrderStatus.FILLED state instead of
        OrderStatus.INITIALIZED.
        """
        # Arrange
        order = MarketOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.02"),
            init_id=UUID4(),
            ts_init=0,
        )

        exec_client.cache.add_order(order)

        # Mock order status report
        msg = "8=FIX.4.4|35=8|1=1|11=C-001|48=100934|22=8|54=1|37=AACkAgAAAABDJPWA|59=4|40=1|60=20230825-23:14:16.100|6=26045.58|44=26045.58|17=0|527=0|790=1|39=1|150=I|14=0.01|151=0|38=0.02|10=0"
        instrument = exec_client.instrument_provider.find_with_security_id(100934)
        report: OrderStatusReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_order_status_reports = AsyncMock(
            return_value=[report],
        )

        # Mock order trade report
        msg = "8=FIX.4.4|35=AE|568=1|912=Y|17=YlLkXgAAAAB4gW43|527=QCSAEAAACLBLEI3M|48=100934|22=8|32=0.01|31=29394.47|75=20230810|60=20230825-23:14:16.200|552=1|54=1|37=AACkAgAAAABDJPWA|11=C-001|1=1|10=123|"
        report: TradeReport = string_to_message(msg).to_nautilus(instrument=instrument)
        exec_client.generate_trade_reports = AsyncMock(return_value=[report])

        exec_client.generate_position_status_reports = AsyncMock(return_value=[])

        # Act
        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.orders()) == 1
        assert exec_client.cache.orders()[0].status == OrderStatus.PARTIALLY_FILLED

    @pytest.mark.asyncio()
    async def test_recon_cached_position(self, exec_client, exec_engine):
        # Arrange
        instrument = exec_client.instrument_provider.find(InstrumentId.from_str("XBT/USD.LMAX"))
        position = LMAXStubs.position(instrumentId=100934, openQuantity=Decimal("1.12"))
        report: PositionStatusReport = position.to_nautilus_report(instrument=instrument)

        exec_client.generate_position_status_reports = AsyncMock(
            return_value=[report],
        )

        exec_client.generate_order_status_reports = AsyncMock(return_value=[])
        exec_client.generate_trade_reports = AsyncMock(return_value=[])

        fill = OrderFilled(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("C-001"),
            venue_order_id=VenueOrderId("12345"),
            account_id=TestIdStubs.account_id(),
            position_id=PositionId("P-001"),
            trade_id=TradeId(UUID4().value),
            order_side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            last_qty=Quantity.from_str("1.12"),
            last_px=Price.from_str("1.12345"),
            currency=instrument.base_currency,
            commission=Money(0, instrument.base_currency),
            liquidity_side=LiquiditySide.TAKER,
            event_id=UUID4(),
            ts_event=0,
            ts_init=0,
        )

        position = Position(instrument=instrument, fill=fill)
        exec_client.cache.add_position(position, OmsType.NETTING)

        # Act
        result = await exec_engine.reconcile_state()

        # Assert
        assert result
        assert len(exec_client.cache.positions()) == 1
        assert exec_client.cache.positions()[0].quantity == Quantity.from_str("1.12")

    #     TestIdStubs.account_id() = TestIdStubs.account_id()
    #     TestIdStubs.trader_id() = TestIdStubs.trader_id()
    #     TestIdStubs.strategy_id() = TestIdStubs.strategy_id()

    #     self.order_factory = OrderFactory(
    #         trader_id=TestIdStubs.trader_id(),
    #         strategy_id=StrategyId("S-001"),
    #         clock=self.clock,
    #     )

    #     self.cache.add_account(TestExecStubs.margin_account(AccountId("LMAX-001")))

    #     self.fix_client.send_message = AsyncMock()

    #     await self.instrument_provider.load_all_async()
    #     for instrument in self.instrument_provider.list_all():
    #         self.cache.add_instrument(instrument)
