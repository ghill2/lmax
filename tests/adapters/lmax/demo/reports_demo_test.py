import asyncio

import pytest

from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import CancelAllOrders
from nautilus_trader.execution.messages import QueryOrder
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs


class TestLMAXExecutionReportsDemo:
    @pytest.mark.asyncio()
    async def test_query_order(self, exec_client):
        # Arrange & Act
        self.exec_engine.connect()
        await self.exec_client.fix_client.is_logged_on.wait()

        order = await self.setup_limit_order()

        query_order = QueryOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=None,
            command_id=UUID4(),
            ts_init=0,
        )
        exec_client._query_order(command=query_order)
        await exec_client.fix_client.wait_for_events(1)

    @pytest.mark.asyncio()
    async def test_generate_order_status_reports(self, exec_client):
        # Arrange
        cancel_all = CancelAllOrders(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=self.instrument.id,
            order_side=self.order_side,
            command_id=UUID4(),
            ts_init=0,
        )

        exec_client._cancel_all_orders(command=cancel_all)
        await asyncio.sleep(2)

        await self.setup_limit_order()
        await self.setup_limit_order()
        await asyncio.sleep(2)

        # Act
        reports = await exec_client.generate_order_status_reports(
            instrument_id=self.instrument.id,
            open_only=True,
        )
        assert len(reports) == 2

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_market_order_accepted(
        self,
        exec_client,
        order_setup,
    ):
        order = await order_setup.market_order_accepted()
        report = await exec_client.generate_order_status_report(
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
        )
        print(report)

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_not_found(self, exec_client):
        # Arrange & Act
        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("EUR/ZAR.LMAX"),
            client_order_id=ClientOrderId("unknown"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.1"),
            price=Price.from_str("1.12345"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        exec_client.cache.add_order(order)

        report = await exec_client.generate_order_status_report(
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("unknown"),
        )
        print(report)

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_market_order_filled(self, exec_client, order_setup):
        # Arrange & Act
        order = await order_setup.market_order_filled()
        report = await exec_client.generate_order_status_report(
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
        )
        print(report)

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_limit_order_accepted(
        self,
        exec_client,
        order_setup,
    ):
        order = await order_setup.limit_order_accepted()
        report = await exec_client.generate_order_status_report(
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
        )
        print(report)

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_limit_order_filled(self, exec_client, order_setup):
        order = await order_setup.limit_order_filled()
        report = await exec_client.generate_order_status_report(
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
        )
        print(report)

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_limit_order_canceled(
        self,
        exec_client,
        order_setup,
    ):
        order = await order_setup.limit_order_canceled()
        report = await exec_client.generate_order_status_report(
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            # order_side=order.side,
        )
        print(report)
        pass

    @pytest.mark.asyncio()
    async def test_generate_order_status_report_rejected_unknown_order(
        self,
        exec_client,
        order_setup,
    ):
        report = await exec_client._generate_order_status_report(
            instrument_id=order_setup.instrument.id,
            client_order_id=ClientOrderId("AAAEDAAAAABDz8pD"),
            order_side=OrderSide.BUY,
        )
        assert report is None

    @pytest.mark.asyncio()
    async def test_generate_trade_report(self):
        pass

    @pytest.mark.asyncio()
    async def test_generate_position_status_report(self):
        pass


#     def setup(self):

#         self.fix_client = LMAXMocks.fix_client()
#         self.instrument_provider = LMAXMocks.instrument_provider()
#         self.xml_client = LMAXMocks.xml_client()

#         # Mock account id
#         cache = TestComponentStubs.cache()
#         cache.add_account(
#                 TestExecStubs.margin_account(AccountId("LMAX-001"))
#         )

#         self.report_provider = LMAXReportProvider(
#                                     fix_client=self.fix_client,
#                                     xml_client=self.xml_client,
#                                     instrument_provider=self.instrument_provider,
#                                     cache=cache,
#                                     clock=TestComponentStubs.clock(),
#         )

#     @pytest.mark.asyncio
#     async def test_generate_order_status_reports(self):

#         # Act
#         await self.instrument_provider.load_all_async()

#         await self.fix_client.connect()

#         reports = await self.report_provider.generate_order_status_reports()

#         print(reports)
#         assert False

#     @pytest.mark.asyncio
#     async def test_generate_position_status_reports(self):

#         # Act
#         await self.instrument_provider.load_all_async()

#         await self.fix_client.connect()

#         reports = await self.report_provider.generate_position_status_reports()
#         assert False

#     @pytest.mark.asyncio
#     async def test_generate_trade_reports(self):

#         # Act
#         await self.instrument_provider.load_all_async()

#         await self.fix_client.connect()

#         reports = await self.report_provider.generate_trade_reports(
#                                                 start=pd.Timestamp("20230810-17:54:53.896", tz="UTC"),
#         )

#         for report in reports:
#             print(report)
