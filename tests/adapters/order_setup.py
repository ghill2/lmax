import asyncio
from decimal import Decimal

from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import CancelAllOrders
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.model.orders import Order
from nautilus_trader.test_kit.stubs.execution import TestExecStubs
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from pytower.adapters.interactive_brokers.data import InteractiveBrokersDataClient
from pytower.adapters.interactive_brokers.execution import InteractiveBrokersExecutionClient
from pytower.adapters.lmax.data import LmaxLiveDataClient
from pytower.adapters.lmax.execution import LmaxLiveExecutionClient


class OrderSetup:
    def __init__(
        self,
        exec_client: LmaxLiveExecutionClient | InteractiveBrokersExecutionClient,
        data_client: LmaxLiveDataClient | InteractiveBrokersDataClient,
    ):
        self.cache = exec_client._cache
        self.trader_id = TestIdStubs.trader_id()
        self.strategy_id = TestIdStubs.strategy_id()

        self.exec_client = exec_client
        self.client = exec_client.client
        self.data_client = data_client
        self._instrument_provider = exec_client.instrument_provider

    async def submit_market_order(
        self,
        instrument_id: InstrumentId,
        order_side: OrderSide,
        quantity: Quantity = None,
    ) -> MarketOrder:
        instrument = self._instrument_provider.find(instrument_id=instrument_id)
        assert instrument is not None

        market_order = TestExecStubs.market_order(
            instrument_id=instrument_id,
            order_side=order_side,
            quantity=quantity or Quantity.from_int(1),
            client_order_id=ClientOrderId(str(await self.client.request_next_order_id())),
            trader_id=self.trader_id,
            strategy_id=self.strategy_id,
        )

        self.cache.add_order(market_order)

        submit_order = SubmitOrder(
            trader_id=market_order.trader_id,
            strategy_id=market_order.strategy_id,
            order=market_order,
            command_id=UUID4(),
            ts_init=0,
        )

        await self.exec_client._submit_order(submit_order)

        await asyncio.sleep(0)

        return market_order

    async def submit_limit_order(
        self,
        instrument_id: InstrumentId,
        order_side: OrderSide,
        quantity: Quantity,
        price: Price = None,
        active: bool = True,
    ) -> LimitOrder:
        print(instrument_id)
        print(self._instrument_provider.list_all())
        instrument = self._instrument_provider.find(instrument_id=instrument_id)
        assert instrument is not None

        if price is None:
            if active:
                # determine active limit order price
                last_quote = await self.exec_client.request_last_quote_tick(instrument.id)
                if order_side is OrderSide.BUY:
                    price: Decimal = last_quote.ask_price - (instrument.price_increment * 1000)
                elif order_side is OrderSide.SELL:
                    price: Decimal = last_quote.bid_price + (instrument.price_increment * 1000)
            else:
                # determine immediate fill limit order price
                last_quote = await self.exec_client.request_last_quote_tick(instrument.id)
                if order_side == OrderSide.BUY:
                    price: Decimal = last_quote.ask_price + (instrument.price_increment * 50)
                elif order_side == OrderSide.SELL:
                    price: Decimal = last_quote.bid_price - (instrument.price_increment * 50)

            if price <= 0:
                price = instrument.price_increment

            price = Price(price, instrument.price_precision)

        limit_order = TestExecStubs.limit_order(
            instrument_id=instrument_id,
            order_side=order_side,
            quantity=quantity,
            client_order_id=ClientOrderId(str(await self.client.request_next_order_id())),
            trader_id=self.trader_id,
            strategy_id=self.strategy_id,
            price=price,
        )

        self.cache.add_order(limit_order)

        submit_order = SubmitOrder(
            trader_id=limit_order.trader_id,
            strategy_id=limit_order.strategy_id,
            order=limit_order,
            command_id=UUID4(),
            ts_init=0,
        )

        await self.exec_client._submit_order(submit_order)

        await asyncio.sleep(0)

        return limit_order

    # async def _limit_order_active_price(
    #     self,
    #     instrument: Instrument,
    #     order_side: OrderSide,
    #     ) -> Price:

    async def close_all(self) -> None:
        await self._close_all_positions()
        self.client._client.reqGlobalCancel()
        # await self._cancel_active_limit_orders()

    async def _close_all_positions(self) -> None:
        for report in await self.exec_client.generate_position_status_reports():
            market_order = MarketOrder(
                trader_id=TestIdStubs.trader_id(),
                strategy_id=TestIdStubs.strategy_id(),
                instrument_id=report.instrument_id,
                client_order_id=ClientOrderId(str(await self.client.request_next_order_id())),
                order_side=Order.closing_side(report.position_side),
                quantity=report.quantity,
                init_id=UUID4(),
                ts_init=0,
                time_in_force=TimeInForce.GTC,
            )
            self.cache.add_order(market_order)
            submit_order = SubmitOrder(
                trader_id=TestIdStubs.trader_id(),
                strategy_id=TestIdStubs.strategy_id(),
                order=market_order,
                command_id=UUID4(),
                ts_init=0,
            )
            await self.exec_client._submit_order(submit_order)

    async def _cancel_active_limit_orders(self) -> None:
        # for instrument in self._exec_client._instrument_provider.list_all():
        # for order_side in (OrderSide.BUY, OrderSide.SELL):
        for report in await self.exec_client.generate_order_status_reports():
            if report.order_type != OrderType.LIMIT:
                continue

            print(f"Cancelling {report.instrument_id} {report.order_side}")

            await self.exec_client._cancel_all_orders(
                command=CancelAllOrders(
                    trader_id=TestIdStubs.trader_id(),
                    strategy_id=TestIdStubs.strategy_id(),
                    instrument_id=report.instrument_id,
                    client_id=self.exec_client.id,
                    command_id=UUID4(),
                    ts_init=0,
                    order_side=report.order_side,
                ),
            )
            await asyncio.sleep(0.05)

    # async def limit_order(
    #     self,
    #     instrument_id,
    #     order_side=None,
    #     price=None,
    #     quantity=None,
    #     time_in_force=None,
    #     trader_id: Optional[TradeId] = None,
    #     strategy_id: Optional[StrategyId] = None,
    #     client_order_id: Optional[ClientOrderId] = None,
    #     expire_time=None,
    #     tags=None,
    # ) -> LimitOrder:
    #     """
    #     nautilus_trader/test_kit/stubs/execution.py
    #     limit_order with price from last quote
    #     """
    #     instrument = self._instrument_provider.find(instrument_id=instrument_id)
    #     assert instrument is not None

    #     if price is None:
    #         last_quote = await self.last_quote(instrument_id=instrument_id)
    #         assert last_quote is not None
    #         # 1500, 2000 = outside allowed price
    #         if order_side is OrderSide.BUY:
    #             price = last_quote.ask_price - (instrument.price_increment * 1000)
    #         elif order_side is OrderSide.SELL:
    #             price = last_quote.bid_price + (instrument.price_increment * 1000)

    #         assert price is not None
    #     order = TestExecStubs.limit_order(
    #         instrument_id=instrument_id,
    #         order_side=order_side,
    #         price=Price(price, instrument.price_precision),
    #         quantity=instrument.min_quantity,
    #         time_in_force=time_in_force,
    #         trader_id=trader_id,
    #         strategy_id=strategy_id,
    #         client_order_id=client_order_id,
    #         expire_time=expire_time,
    #         tags=tags,
    #     )
    #     # self._exec_client._cache.add_order(order)

    #     return order

    # async def limit_order_filled(
    #     self,
    #     instrument_id: InstrumentId,
    #     order_side: OrderSide,
    #     price: Price = None,
    # ) -> LimitOrder:
    #     # determine price for immediate fill
    #     last_quote = await self.last_quote(instrument_id=instrument_id)
    #     instrument = self._instrument_provider.find(instrument_id=instrument_id)
    #     assert instrument is not None
    #     if order_side == OrderSide.BUY:
    #         price: Decimal = last_quote.ask_price + (instrument.price_increment * 5)
    #     elif order_side == OrderSide.SELL:
    #         price: Decimal = last_quote.bid_price - (instrument.price_increment * 5)
    #     price = Price(price, instrument.price_precision)

    #     order = await self.limit_order(
    #         instrument_id=instrument_id,
    #         order_side=order_side,
    #         price=price,
    #         client_order_id=ClientOrderId(UUID4().value[:20]),
    #     )
    #     await self.submit_order(order)

    # async def last_quote(self, instrument_id: InstrumentId) -> QuoteTick:
    #     self._data_client.unsubscribe_quote_ticks(instrument_id=instrument_id)
    #     self._data_client.subscribe_quote_ticks(instrument_id=instrument_id)
    #     security_id = self._instrument_provider.get_security_id(instrument_id=instrument_id)
    #     assert security_id is not None
    #     await self._data_client.fix_client.wait_for_event(
    #         cls=MarketDataSnapshotFullRefresh,
    #         tags={48: str(security_id)},  # SecurityId
    #     )
    #     self._data_client.unsubscribe_quote_ticks(instrument_id=instrument_id)
    #     quote = self._data_client.cache.quote_tick(instrument_id=instrument_id)
    #     assert quote is not None
    #     return quote

    # async def cancel(self, order: LimitOrder) -> None:
    #     cancel_order = CancelOrder(
    #         trader_id=order.trader_id,
    #         strategy_id=order.strategy_id,
    #         instrument_id=order.instrument_id,
    #         client_order_id=order.client_order_id,
    #         venue_order_id=order.venue_order_id,
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

    #     return order

    # async def submit_order(self, order) -> None:
    #     # self._exec_client._cache.add_order(order)
    #     command = TestCommandStubs.submit_order_command(order=order)
    #     assert self._exec_client._cache.strategy_id_for_order(order.client_order_id) is not None
    #     self._exec_client.submit_order(command=command)

    # async def cancel_all(self) -> None:
    #     # OLD LMAX CODE
    #     # close all active orders
    #     orders: list[LmaxOrder] = await self._exec_client.xml_client.request_orders(open_only=True)

    #     for order in orders:
    #         instrument = self._instrument_provider.find_with_security_id(order.security_id)
    #         cancel_order = CancelOrder(
    #             trader_id=TestIdStubs.trader_id(),
    #             strategy_id=TestIdStubs.strategy_id(),
    #             instrument_id=instrument.id,
    #             client_order_id=order.client_order_id,
    #             venue_order_id=order.venue_order_id,
    #             command_id=UUID4(),
    #             ts_init=0,
    #         )
    #         await self._exec_client._cancel_order(command=cancel_order)
    #         await asyncio.sleep(0.01)

    #     # close all positions
    #     positions = await self._exec_client.xml_client.request_positions()
    #     for position in positions:
    #         if float(position.openQuantity) == 0.0:
    #             continue
    #         instrument = self._instrument_provider.find_with_security_id(position.security_id)
    #         assert instrument is not None

    #         order = await self._market_order(
    #             instrument_id=instrument.id,
    #             side=OrderSide.SELL if position.openQuantity > 0 else OrderSide.BUY,
    #             quantity=instrument.make_qty(abs(position.openQuantity)),
    #         )
    #         await asyncio.sleep(0.01)
