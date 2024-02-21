import asyncio
from decimal import Decimal

from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import CancelOrder
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.model.orders.limit import LimitOrder
from nautilus_trader.model.orders.market import MarketOrder
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from pytower.adapters.lmax.data import LmaxLiveDataClient
from pytower.adapters.lmax.execution import LmaxLiveExecutionClient
from pytower.adapters.lmax.fix.messages import ExecutionReport
from pytower.adapters.lmax.fix.messages import MarketDataSnapshotFullRefresh
from pytower.adapters.lmax.xml.types import LmaxOrder


DELAY = 0.001


class LMAXOrderSetupDemo:
    """
    Provides a set of helper methods for setting up orders on the LMAX demo server for
    testing.
    """

    def __init__(
        self,
        exec_client: LmaxLiveExecutionClient,
        data_client: LmaxLiveDataClient,
    ):
        self._exec_client = exec_client
        self._data_client = data_client
        self._instrument_provider = exec_client.instrument_provider

    # @property
    # def instrument(self) -> Instrument:
    #     return self._exec_client.instrument_provider.find(instrument_id=instrument_id)

    async def market_order_filled(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        quantity: Quantity = None,
    ) -> MarketOrder:
        order = await self._market_order(
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
        )

        # wait for fill
        tags = {
            11: order.client_order_id.value,  # ClOrdID
            39: "2",  # OrdStatus: filled
        }
        await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
        return order

    async def market_order_rejected(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        quantity: Quantity = None,
    ) -> MarketOrder:
        order = await self._market_order(
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
        )

        # wait for rejected
        tags = {
            11: order.client_order_id.value,  # ClOrdID
            39: "8",  # OrdStatus: rejected
        }
        await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)

        assert order.status == OrderStatus.REJECTED

        return order

    async def market_order_accepted(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        quantity: Quantity = None,
    ) -> MarketOrder:
        order = await self._market_order(
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
        )

        tags = {
            11: order.client_order_id.value,  # ClOrdID
            39: "0",  # OrdStatus: new
        }
        await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
        assert order.status == OrderStatus.ACCEPTED
        # await asyncio.sleep(1)

        return order

    async def _market_order(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        quantity: Quantity = None,
    ) -> MarketOrder:
        await asyncio.sleep(DELAY)

        instrument = self._instrument_provider.find(instrument_id=instrument_id)
        assert instrument is not None

        quantity = quantity or instrument.min_quantity

        order = MarketOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            client_order_id=ClientOrderId(UUID4().value[:20]),
            instrument_id=instrument_id,
            order_side=side,
            quantity=quantity,
            ts_init=0,
            time_in_force=TimeInForce.FOK,
            init_id=UUID4(),
        )
        self._exec_client.cache.add_order(order)

        submit_order = SubmitOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            order=order,
            command_id=UUID4(),
            position_id=None,
            ts_init=0,
        )

        assert self._exec_client.cache.strategy_id_for_order(order.client_order_id) is not None
        await self._exec_client._submit_order(command=submit_order)

        return order

    async def last_quote(self, instrument_id: InstrumentId) -> QuoteTick:
        self._data_client.unsubscribe_quote_ticks(instrument_id=instrument_id)
        self._data_client.subscribe_quote_ticks(instrument_id=instrument_id)
        security_id = self._instrument_provider.get_security_id(instrument_id=instrument_id)
        assert security_id is not None
        await self._data_client.fix_client.wait_for_event(
            cls=MarketDataSnapshotFullRefresh,
            tags={48: str(security_id)},  # SecurityId
        )
        self._data_client.unsubscribe_quote_ticks(instrument_id=instrument_id)
        quote = self._data_client.cache.quote_tick(instrument_id=instrument_id)
        assert quote is not None
        return quote

    async def limit_order_filled(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        price: Price = None,
    ) -> LimitOrder:
        # determine price for immediate fill
        last_quote = await self.last_quote(instrument_id=instrument_id)
        instrument = self._instrument_provider.find(instrument_id=instrument_id)
        assert instrument is not None
        if side == OrderSide.BUY:
            price: Decimal = last_quote.ask_price + (instrument.price_increment * 5)
        elif side == OrderSide.SELL:
            price: Decimal = last_quote.bid_price - (instrument.price_increment * 5)
        price = Price(price, instrument.price_precision)

        order = await self._limit_order(
            instrument_id=instrument_id,
            side=side,
            price=price,
        )

        # wait for fill
        tags = {
            11: order.client_order_id.value,  # ClOrdID
            39: "2",  # OrdStatus: filled
        }
        await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)

        return order

    async def limit_order_rejected(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        price: Price = None,
    ) -> LimitOrder:
        order = await self._limit_order(
            instrument_id=instrument_id,
            side=side,
            price=price,
        )

        # wait for rejected
        tags = {
            11: order.client_order_id.value,  # ClOrdID
            39: "8",  # OrdStatus: rejected
        }
        await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)

        assert order.status == OrderStatus.REJECTED

        return order

    async def limit_order_accepted(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        price: Price = None,
    ) -> LimitOrder:
        order = await self._limit_order(
            instrument_id=instrument_id,
            side=side,
            price=price,
        )
        print(order.client_order_id)
        # 72085147-9be4-4c8a-a
        # 72085147-9be4-4c8a-a

        # 82186a74-bd15-4935-a
        # wait for accepted
        tags = {
            11: order.client_order_id.value,  # ClOrdID
            39: "0",  # OrdStatus: new
        }
        await asyncio.wait_for(
            self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags),
            timeout=10,
        )
        # await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
        # await asyncio.sleep(1)
        assert order.status == OrderStatus.ACCEPTED

        return order

    async def limit_order_canceled(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        price: Price = None,
    ) -> LimitOrder:
        order = await self._limit_order(
            instrument_id=instrument_id,
            side=side,
            price=price,
        )
        await self.cancel(order=order)
        return order

    async def _limit_order(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        price: Price = None,
    ) -> LimitOrder:
        instrument = self._instrument_provider.find(instrument_id=instrument_id)
        assert instrument is not None

        if price is None:
            last_quote = await self.last_quote(instrument_id=instrument_id)
            assert last_quote is not None
            # 1500, 2000 = outside allowed price
            if side is OrderSide.BUY:
                price = last_quote.ask_price - (instrument.price_increment * 1000)
            elif side is OrderSide.SELL:
                price = last_quote.bid_price + (instrument.price_increment * 1000)

            assert price is not None

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=instrument_id,
            client_order_id=ClientOrderId(UUID4().value[:20]),
            order_side=side,
            quantity=instrument.min_quantity,
            price=Price(price, instrument.price_precision),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        self._exec_client.cache.add_order(order)

        submit_order = SubmitOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            order=order,
            command_id=UUID4(),
            position_id=None,
            ts_init=0,
        )

        await self._exec_client._submit_order(command=submit_order)
        return order

    async def cancel(self, order: LimitOrder) -> None:
        cancel_order = CancelOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=order.venue_order_id,
            command_id=UUID4(),
            ts_init=0,
        )
        await self._exec_client._cancel_order(command=cancel_order)

        # wait for cancel
        tags = {
            41: order.client_order_id.value,  # OrigClOrdID
            39: "4",  # OrdStatus: canceled
        }
        await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
        assert order.status == OrderStatus.CANCELED

        return order

    async def cancel_all(self) -> None:
        # close all active orders
        orders: list[LmaxOrder] = await self._exec_client.xml_client.request_orders(open_only=True)

        for order in orders:
            instrument = self._instrument_provider.find_with_security_id(order.security_id)
            cancel_order = CancelOrder(
                trader_id=TestIdStubs.trader_id(),
                strategy_id=TestIdStubs.strategy_id(),
                instrument_id=instrument.id,
                client_order_id=order.client_order_id,
                venue_order_id=order.venue_order_id,
                command_id=UUID4(),
                ts_init=0,
            )
            await self._exec_client._cancel_order(command=cancel_order)
            await asyncio.sleep(0.01)

        # close all positions
        positions = await self._exec_client.xml_client.request_positions()
        for position in positions:
            if float(position.openQuantity) == 0.0:
                continue
            instrument = self._instrument_provider.find_with_security_id(position.security_id)
            assert instrument is not None

            order = await self._market_order(
                instrument_id=instrument.id,
                side=OrderSide.SELL if position.openQuantity > 0 else OrderSide.BUY,
                quantity=instrument.make_qty(abs(position.openQuantity)),
            )
            await asyncio.sleep(0.01)

        # tags = {
        #     11: order.client_order_id.value,  # ClOrdID
        #     39: "0",  # OrdStatus: new
        # }
        # await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
        # assert order.status == OrderStatus.ACCEPTED

        # close all active orders

        # security_id = self._instrument_provider.get_security_id(instrument_id=instrument_id)
        # orders = await self._exec_client.xml_client.request_orders(open_only=True,
        #                                                            security_id=security_id)
        # for order in orders:
        #     instrument = self._instrument_provider.find_with_security_id(order.security_id)

        #     cancel_order = CancelOrder(
        #         trader_id=TestIdStubs.trader_id(),
        #         strategy_id=TestIdStubs.strategy_id(),
        #         instrument_id=instrument.id,
        #         client_order_id=order.client_order_id,
        #         venue_order_id=None,
        #         command_id=UUID4(),
        #         ts_init=0,
        #     )
        #     await self._exec_client._cancel_order(command=cancel_order)

        #     # wait for cancel
        #     tags = {
        #         41: order.client_order_id.value,  # OrigClOrdID
        #         39: "4",  # OrdStatus: canceled
        #     }
        #     await self._exec_client.fix_client.wait_for_event(cls=ExecutionReport, tags=tags)
        #     assert order.status == OrderStatus.CANCELED
