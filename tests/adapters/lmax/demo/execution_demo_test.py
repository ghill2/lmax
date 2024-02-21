import asyncio

import pytest

from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import CancelAllOrders
from nautilus_trader.execution.messages import CancelOrder
from nautilus_trader.execution.messages import ModifyOrder
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from pytower.adapters.lmax.fix.messages import ExecutionReport
from pytower.adapters.lmax.fix.messages import OrderCancelReject


# fixtures


# def test_universe_execution()


# class TestIBExecution(TestExecution):


@pytest.mark.parametrize("instrument_id", [1, 2])
class TestExecution:
    # def __init__(self, exec_client, order_setup):
    #     self.exec_client = exec_client
    #     self.order_setup = order_setup

    @pytest.mark.asyncio()
    async def test_market_order_accepted(self, instrument_id, order_side):
        # Arrange & Act
        print("task_mark_order_accepted")
        print(instrument_id)

        order = await self.order_setup.market_order_accepted(
            instrument_id=instrument_id,
            order_side=order_side,
        )

        # Assert
        assert self.exec_client.cache.order(order.client_order_id).status == OrderStatus.ACCEPTED

    @pytest.mark.asyncio()
    async def test_market_order_filled(self, instrument_id, order_side):
        # Arrange & Act

        order = await order_setup.market_order_filled(
            instrument_id=instrument_id,
            order_size=order_side,
        )
        assert self.exec_client._cache.order(order.client_order_id) is not None

        # Assert
        cache = self.exec_client.cache
        assert cache.order(order.client_order_id).status == OrderStatus.FILLED
        assert cache.order(order.client_order_id).quantity == order.quantity
        assert cache.order(order.client_order_id).side == order.side
        assert cache.order(order.client_order_id).client_order_id == order.client_order_id
        assert cache.order(order.client_order_id).instrument_id == order.instrument_id
        assert cache.order(order.client_order_id).order_type == order.order_type

    @pytest.mark.asyncio()
    async def test_market_order_rejected(self, instrument_id, order_side):
        # Arrange & Act

        instrument = self.exec_client.instrument_provider.find(instrument_id=instrument_id)
        assert instrument is not None
        invalid_qty = Quantity(
            float(instrument.max_quantity + instrument.min_quantity),
            instrument.size_precision,
        )

        order = await order_setup.market_order_rejected(
            instrument_id=instrument_id,
            side=order_side,
            quantity=invalid_qty,
        )

        # Assert
        cache = exec_client.cache

        assert order.status == OrderStatus.REJECTED
        assert cache.order(order.client_order_id).status == OrderStatus.REJECTED

    # @pytest.mark.parametrize("side", [OrderSide.BUY])
    # @pytest.mark.parametrize("instrument_id", [InstrumentId.from_str("EUR/USD.LMAX")])
    # class TestExecutionClientLimit:

    @pytest.mark.asyncio()
    async def test_limit_order_same_price(self, instrument_id, order_side):
        order1 = await order_setup.limit_order_accepted(
            instrument_id=instrument_id,
            order_side=order_side,
        )
        order2 = await order_setup.limit_order_accepted(
            instrument_id=instrument_id,
            side=order_side,
            price=order1.price,
        )

        print(order1, order2)
        cancel_order = CancelOrder(
            trader_id=order1.trader_id,
            strategy_id=order1.strategy_id,
            instrument_id=order1.instrument_id,
            client_order_id=order1.client_order_id,
            venue_order_id=None,
            command_id=UUID4(),
            ts_init=0,
        )
        await exec_client._cancel_order(command=cancel_order)
        # wait for cancel
        tags = {
            41: order1.client_order_id.value,  # OrigClOrdID
            39: "4",  # OrdStatus: canceled
        }
        await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
        assert order1.status == OrderStatus.CANCELED

    @pytest.mark.asyncio()
    async def test_cancel_order_unknown_order(self, instrument_id, order_side):
        # Arrange & Act

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=instrument_id,
            client_order_id=ClientOrderId(UUID4().value[:20]),
            order_side=order_side,
            quantity=Quantity.from_int(1),
            price=Price.from_int(1),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        exec_client.cache.add_order(order)

        cancel_order = CancelOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,  # ClientOrderId not on exchange
            venue_order_id=None,
            command_id=UUID4(),
            ts_init=0,
        )
        await exec_client._cancel_order(command=cancel_order)

        # wait for cancel
        tags = {
            # 39: "8",  # OrdStatus: canceled
            58: "UNKNOWN_ORDER",  # OrdStatus: canceled
        }
        await exec_client.fix_client.wait_for_event(cls=OrderCancelReject, tags=tags)
        assert order.status == OrderStatus.INITIALIZED

    @pytest.mark.asyncio()
    async def test_cancel_limit_order(self, instrument_id, order_side):
        # Arrange & Act

        order = await order_setup.limit_order_canceled(
            instrument_id=instrument_id,
            order_side=order_side,
        )

        # Assert
        assert exec_client.cache.order(order.client_order_id).status == OrderStatus.CANCELED

    @pytest.mark.asyncio()
    async def test_modify_limit_order(self, instrument_id, order_side):
        # Arrange & Act

        order = await order_setup.limit_order_accepted(
            instrument_id=instrument_id,
            order_side=order_side,
        )

        instrument = exec_client.instrument_provider.find(instrument_id=instrument_id)
        assert instrument is not None
        new_price = Price(order.price + instrument.min_price, instrument.price_precision)
        new_qty = Quantity(order.quantity + instrument.min_quantity, instrument.size_precision)

        modify_order = ModifyOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=None,
            quantity=new_qty,
            price=new_price,
            trigger_price=None,
            command_id=UUID4(),
            ts_init=0,
        )

        await exec_client._modify_order(command=modify_order)
        tags = {
            41: order.client_order_id.value,  # OrigClOrdID
            39: "0",  # OrdStatus: new
        }
        await exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)

        # Assert
        assert exec_client.cache.order(order.client_order_id).price == new_price
        assert exec_client.cache.order(order.client_order_id).quantity == new_qty
        assert exec_client.cache.order(order.client_order_id).status == OrderStatus.ACCEPTED

    @pytest.mark.asyncio()
    async def test_limit_order_accepted(self, instrument_id, order_side):
        # Arrange & Act

        order = await order_setup.limit_order_accepted(
            instrument_id=instrument_id,
            order_side=order_side,
        )

        # Assert
        assert exec_client.cache.order(order.client_order_id).status == OrderStatus.ACCEPTED
        #  \
        # or exec_client.cache.order(order.client_order_id).status == OrderStatus.FILLED

    @pytest.mark.asyncio()
    async def test_limit_order_rejected(self, instrument_id, side):
        # Arrange & Act

        order = await order_setup.limit_order_rejected(
            instrument_id=instrument_id,
            side=side,
            price=Price.from_str("0"),
        )  # invalid price

        # Assert
        assert exec_client.cache.order(order.client_order_id).status == OrderStatus.REJECTED

    @pytest.mark.skip(reason="limit order is not always filled?")
    @pytest.mark.asyncio()
    async def test_limit_order_filled(self, instrument_id, order_side):
        # Arrange & Act

        order = await order_setup.limit_order_filled(
            instrument_id=instrument_id,
            order_side=order_side,
        )

        # Assert
        cache = exec_client.cache
        assert cache.order(order.client_order_id).status == OrderStatus.FILLED
        assert cache.order(order.client_order_id).quantity == order.quantity
        assert cache.order(order.client_order_id).side == order.side
        assert cache.order(order.client_order_id).client_order_id == order.client_order_id
        assert cache.order(order.client_order_id).instrument_id == order.instrument_id
        assert cache.order(order.client_order_id).order_type == order.order_type

    @pytest.mark.asyncio()
    async def test_modify_order_rejected_invalid_price(
        self,
        exec_client,
        order_setup,
        instrument_id,
        order_side,
    ):
        # Arrange & Act
        order = await order_setup.limit_order_accepted(
            instrument_id=instrument_id,
            order_side=order_side,
        )

        modify_order = ModifyOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=None,
            quantity=order.quantity,
            price=Price.from_str("0"),  # invalid price
            trigger_price=None,
            command_id=UUID4(),
            ts_init=0,
        )

        exec_client.modify_order(command=modify_order)
        # await exec_client.fix_client.wait_for_event(cls=OrderCancelReject, tags=tags)
        await asyncio.sleep(1)

        # Assert
        assert exec_client.cache.order(order.client_order_id).status == OrderStatus.ACCEPTED

    # class TestExecutionClientDemo:

    @pytest.mark.skip(reason="")
    @pytest.mark.asyncio()
    async def test_cancel_all_orders(self, instrument_id, order_side):
        # TODO: won't run on XBT/USD, not enough margin on demo account with current balance

        # Arrange & Act

        order1 = await order_setup.limit_order_accepted(
            instrument_id=instrument_id,
            order_side=order_side,
        )
        order2 = await order_setup.limit_order_accepted(
            instrument_id=instrument_id,
            order_side=order_side,
        )

        cancel_all = CancelAllOrders(
            trader_id=order1.trader_id,
            strategy_id=order1.strategy_id,
            instrument_id=instrument_id,
            order_side=order_side,
            command_id=UUID4(),
            ts_init=0,
        )

        # wait for cancels
        exec_client.cancel_all_orders(command=cancel_all)
        tags = {
            41: order1.client_order_id.value,  # OrigClOrdID
            39: "4",  # OrdStatus: canceled
        }
        await exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
        tags = {
            41: order2.client_order_id.value,  # OrigClOrdID
            39: "4",  # OrdStatus: canceled
        }
        await exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)

        # Assert
        assert exec_client.cache.order(order1.client_order_id).status == OrderStatus.CANCELED
        assert exec_client.cache.order(order2.client_order_id).status == OrderStatus.CANCELED

    @pytest.mark.skip(reason="")
    @pytest.mark.asyncio()
    async def test_modify_order_rejected_invalid_quantity(
        self,
        instrument_id,
        order_side,
    ):
        # Arrange & Act

        order = await order_setup.limit_order_accepted(
            instrument_id=instrument_id,
            order_side=order_side,
        )

        modify_order = ModifyOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=None,
            quantity=Quantity.from_str("0"),  # invalid quantity
            price=order.price,
            trigger_price=None,
            command_id=UUID4(),
            ts_init=0,
        )
        exec_client.modify_order(command=modify_order)
        # await exec_client.fix_client.wait_for_event(cls=OrderCancelReject, tags=tags)
        await asyncio.sleep(1)

        # Assert
        assert exec_client.cache.order(order.client_order_id).status == OrderStatus.ACCEPTED

    @pytest.mark.asyncio()
    async def test_modify_order_unknown_order(
        self,
        exec_client,
        last_quote,
        instrument_id,
        order_side,
    ):
        pass

    @pytest.mark.skip()
    @pytest.mark.asyncio()
    async def test_market_order_rejected_closed_market(
        self,
        exec_client,
        instrument_id,
        order_side,
    ):
        pass


# BELOW HERE
# from pytower.adapters.lmax.execution import LmaxLiveExecutionClient
# from pytower.adapters.lmax.data import LmaxLiveDataClient


# from pytower.tests.adapters.lmax.demo.setup import setup_limit_order
# from pytower.tests.adapters.lmax.demo.setup import setup_market_order
# from pytower.tests.adapters.lmax.demo.setup import get_last_quote
# from pytower.tests.adapters.lmax.demo.setup import cancel_all_orders
# from pytower.adapters.lmax.conftest import setup_lmax_demo
# def setup_class(self, instrument_id, side):
#     self.order_side = OrderSide.BUY
#     self.instrument_id = InstrumentId.from_str("EUR/USD.LMAX")


# class TestExecutionClientFuckDemo:
#     @pytest.mark.asyncio()
#     async def test_market_order_filled(self, exec_client, order_setup):
#         exec_client = order_setup._exec_client
#         # Arrange & Act
#         instrument_ids = [
#             InstrumentId.from_str("EUR/USD.LMAX"),
#             InstrumentId.from_str("USD/JPY.LMAX"),
#             InstrumentId.from_str("GBP/USD.LMAX"),
#             InstrumentId.from_str("USD/CAD.LMAX"),
#             InstrumentId.from_str("AUD/USD.LMAX"),
#             InstrumentId.from_str("EUR/JPY.LMAX"),
#             InstrumentId.from_str("GBP/JPY.LMAX"),
#             InstrumentId.from_str("EUR/GBP.LMAX"),
#             InstrumentId.from_str("NZD/USD.LMAX"),
#             InstrumentId.from_str("EUR/SEK.LMAX"),
#             InstrumentId.from_str("USD/TRY.LMAX"),
#         ]
#         for instrument_id in instrument_ids:
#             for order_side in (OrderSide.BUY, OrderSide.SELL):
#                 # order = await order_setup.market_order_filled(instrument_id=instrument_id, side=side)
#
#                 order = await order_setup.market_order(
#                     instrument_id=instrument_id,
#                     order_side=order_side,
#                 )
#                 print(order.client_order_id)
#                 # wait for fill
#                 tags = {
#                     11: order.client_order_id.value,  # ClOrdID
#                     39: "2",  # OrdStatus: filled
#                 }
#                 await exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
