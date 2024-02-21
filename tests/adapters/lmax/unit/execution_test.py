from unittest.mock import AsyncMock
from unittest.mock import Mock

import pandas as pd
import pytest

from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import CancelAllOrders
from nautilus_trader.execution.messages import CancelOrder
from nautilus_trader.execution.messages import ModifyOrder
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.currencies import XBT
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.events.order import OrderAccepted
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders.limit import LimitOrder
from nautilus_trader.model.orders.market import MarketOrder
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from pytower.adapters.lmax.fix.messages import ExecutionReport
from pytower.adapters.lmax.fix.messages import NewOrderSingle
from pytower.adapters.lmax.fix.messages import OrderCancelReplaceRequest
from pytower.adapters.lmax.fix.messages import OrderCancelRequest
from pytower.adapters.lmax.fix.messages import string_to_message
from pytower.tests.adapters.lmax import FIX_RESPONSES


class TestExecutionClient:
    @pytest.mark.skip(reason="not implemented")
    @pytest.mark.asyncio
    async def test_connect(self, exec_client):
        pass

    @pytest.mark.asyncio
    async def test_submit_limit_order_sell(self, exec_client):
        """
        Test LMAXLiveExecutionClient sends a valid `SubmitOrderSingle` FIX message for a
        `LIMIT` order.
        """
        # Arrange
        exec_client.fix_client.send_message = AsyncMock()
        exec_client.generate_order_submitted = Mock()

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.SELL,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )

        submit_order = SubmitOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            order=order,
            command_id=UUID4(),
            position_id=None,
            ts_init=0,
        )

        # Act
        await exec_client._submit_order(command=submit_order)

        # Assert
        msg = exec_client.fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is NewOrderSingle
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)
        assert msg.get(54) == b"2"  # Side: SELL
        assert msg.get(40) == b"2"  # OrdType: LIMIT
        assert msg.get(11) == b"a90dd4d7-c530-4add-8"  # ClOrdId
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert msg.get(38) == b"0.01"  # OrderQty
        assert msg.get(44) == b"1.23"  # Price
        assert msg.get(18) == b"H"  # ExecInst=H (do not cancel on disconnect)
        assert msg.get(59) == b"1"  # TimeInForce
        assert len(msg.pairs) == 10
        exec_client.generate_order_submitted.assert_called_once()
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["strategy_id"]
            == order.strategy_id
        )
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["instrument_id"]
            == order.instrument_id
        )
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["client_order_id"]
            == order.client_order_id
        )

    @pytest.mark.asyncio
    async def test_submit_limit_order_buy(self, exec_client):
        """
        Test LMAXLiveExecutionClient sends a valid `SubmitOrderSingle` FIX message for a
        `LIMIT` order.
        """
        # Arrange
        exec_client.fix_client.send_message = AsyncMock()
        exec_client.generate_order_submitted = Mock()
        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )

        submit_order = SubmitOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            order=order,
            command_id=UUID4(),
            position_id=None,
            ts_init=0,
        )

        # Act
        await exec_client._submit_order(command=submit_order)

        # Assert
        msg = exec_client.fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is NewOrderSingle
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)
        assert msg.get(54) == b"1"  # Side: BUY
        assert msg.get(40) == b"2"  # OrdType: LIMIT
        assert msg.get(11) == b"a90dd4d7-c530-4add-8"  # ClOrdId
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert msg.get(38) == b"0.01"  # OrderQty
        assert msg.get(44) == b"1.23"  # Price
        assert msg.get(18) == b"H"  # ExecInst=H (do not cancel on disconnect)
        assert msg.get(59) == b"1"  # TimeInForce: GTC
        assert len(msg.pairs) == 10
        exec_client.generate_order_submitted.assert_called_once()
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["strategy_id"]
            == order.strategy_id
        )
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["instrument_id"]
            == order.instrument_id
        )
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["client_order_id"]
            == order.client_order_id
        )

    @pytest.mark.asyncio
    async def test_submit_market_order_sell(self, exec_client):
        # Arrange
        fix_client = exec_client.fix_client
        fix_client.send_message = AsyncMock()

        exec_client.fix_client.send_message = AsyncMock()
        exec_client.generate_order_submitted = Mock()

        order = MarketOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.01"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.FOK,
        )

        submit_order = SubmitOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            order=order,
            command_id=UUID4(),
            position_id=None,
            ts_init=0,
        )

        # Act
        await exec_client._submit_order(command=submit_order)

        # Assert
        msg = fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is NewOrderSingle
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)
        assert msg.get(54) == b"1"  # Side: BUY
        assert msg.get(40) == b"1"  # OrdType: MARKET
        assert msg.get(11) == b"a90dd4d7-c530-4add-8"  # ClOrdId
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert msg.get(38) == b"0.01"  # OrderQty
        assert msg.get(18) == b"H"  # ExecInst=H (do not cancel on disconnect)
        assert msg.get(59) == b"4"  # TimeInForce: GTC
        assert len(msg.pairs) == 9

        exec_client.generate_order_submitted.assert_called_once()
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["strategy_id"]
            == order.strategy_id
        )
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["instrument_id"]
            == order.instrument_id
        )
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["client_order_id"]
            == order.client_order_id
        )

    @pytest.mark.asyncio
    async def test_submit_market_order_buy(self, exec_client):
        fix_client = exec_client.fix_client
        fix_client.send_message = AsyncMock()

        exec_client.fix_client.send_message = AsyncMock()
        exec_client.generate_order_submitted = Mock()

        order = MarketOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.SELL,
            quantity=Quantity.from_str("0.01"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.FOK,
        )

        submit_order = SubmitOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            order=order,
            command_id=UUID4(),
            position_id=None,
            ts_init=0,
        )

        # Act
        await exec_client._submit_order(command=submit_order)

        # Assert
        msg = fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is NewOrderSingle
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)
        assert msg.get(54) == b"2"  # Side: BUY
        assert msg.get(40) == b"1"  # OrdType: MARKET
        assert msg.get(11) == b"a90dd4d7-c530-4add-8"  # ClOrdId
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert msg.get(38) == b"0.01"  # OrderQty
        assert msg.get(18) == b"H"  # ExecInst=H (do not cancel on disconnect)
        assert msg.get(59) == b"4"  # TimeInForce: GTC
        assert len(msg.pairs) == 9

        exec_client.generate_order_submitted.assert_called_once()
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["strategy_id"]
            == order.strategy_id
        )
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["instrument_id"]
            == order.instrument_id
        )
        assert (
            exec_client.generate_order_submitted.call_args.kwargs["client_order_id"]
            == order.client_order_id
        )

    @pytest.mark.asyncio
    async def test_cancel_limit_order(self, exec_client):
        # Arrange
        exec_client.fix_client.send_message = AsyncMock()
        exec_client._generate_request_id = AsyncMock(return_value="request_id1")

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        exec_client.cache.add_order(order)
        cancel_order = CancelOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=order.venue_order_id,
            command_id=UUID4(),
            ts_init=0,
        )
        # Act
        await exec_client._cancel_order(command=cancel_order)

        # Assert
        msg = exec_client.fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is OrderCancelRequest
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)
        assert msg.get(41) == b"a90dd4d7-c530-4add-8"  # OrigClOrdID
        assert msg.get(11) == b"request_id1"  # ClOrdId
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert len(msg.pairs) == 5

    @pytest.mark.asyncio()
    async def test_cancel_all_orders_buy(self, exec_client, monkeypatch):
        # Arrange
        exec_client._cancel_order = AsyncMock()

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        order.apply(
            OrderAccepted(
                trader_id=order.trader_id,
                strategy_id=order.strategy_id,
                instrument_id=order.instrument_id,
                client_order_id=order.client_order_id,
                venue_order_id=TestIdStubs.venue_order_id(),
                account_id=TestIdStubs.account_id(),
                event_id=UUID4(),
                ts_event=0,
                ts_init=0,
                # reconciliation=True,
            ),
        )
        exec_client.cache.add_order(order)
        exec_client.cache.update_order(order)

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-7"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_int(1),
            price=Price.from_str("1.12345"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        order.apply(
            OrderAccepted(
                trader_id=order.trader_id,
                strategy_id=order.strategy_id,
                instrument_id=order.instrument_id,
                client_order_id=order.client_order_id,
                venue_order_id=TestIdStubs.venue_order_id(),
                account_id=TestIdStubs.account_id(),
                event_id=UUID4(),
                ts_event=0,
                ts_init=0,
                # reconciliation=True,
            ),
        )
        exec_client.cache.add_order(order)
        exec_client.cache.update_order(order)

        cancel_all = CancelAllOrders(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            order_side=order.side,
            command_id=UUID4(),
            ts_init=0,
        )

        # Act
        await exec_client._cancel_all_orders(command=cancel_all)

        # Assert
        assert exec_client._cancel_order.call_count == 2

        commands = [call[0][0] for call in exec_client._cancel_order.call_args_list]
        assert commands[0].trader_id == TestIdStubs.trader_id()
        assert commands[0].strategy_id == TestIdStubs.strategy_id()
        assert commands[0].instrument_id == InstrumentId.from_str("XBT/USD.LMAX")
        assert commands[0].client_order_id == ClientOrderId("a90dd4d7-c530-4add-7")
        assert commands[0].venue_order_id == TestIdStubs.venue_order_id()

        assert commands[1].trader_id == TestIdStubs.trader_id()
        assert commands[1].strategy_id == TestIdStubs.strategy_id()
        assert commands[1].instrument_id == InstrumentId.from_str("XBT/USD.LMAX")
        assert commands[1].client_order_id == ClientOrderId("a90dd4d7-c530-4add-8")
        assert commands[1].venue_order_id == TestIdStubs.venue_order_id()

    @pytest.mark.asyncio
    async def test_modify_limit_order_buy(self, exec_client):
        # Arrange
        exec_client.fix_client.send_message = AsyncMock()
        exec_client._generate_request_id = AsyncMock(return_value="request_id1")

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        exec_client.cache.add_order(order)

        modify_order = ModifyOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=None,
            quantity=Quantity.from_str("0.02"),
            price=Price.from_str("1.50"),
            trigger_price=None,
            command_id=UUID4(),
            ts_init=0,
        )

        # Act
        await exec_client._modify_order(command=modify_order)

        # Assert
        msg = exec_client.fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is OrderCancelReplaceRequest
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(11) == b"request_id1"  # ClOrdId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8'
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert msg.get(18) == b"H"  # ExecInst=H (do not cancel on disconnect)
        assert msg.get(41) == b"a90dd4d7-c530-4add-8"  # OrigClOrdID
        assert msg.get(54) == b"1"  # Side
        assert msg.get(38) == b"0.02"  # OrderQty
        assert msg.get(44) == b"1.50"  # Price
        assert msg.get(40) == b"2"  # OrdType: LIMIT
        assert msg.get(59) == b"1"  # TimeInForce: GTC
        assert len(msg.pairs) == 11

    @pytest.mark.asyncio
    async def test_modify_limit_order_sell(self, exec_client):
        # Arrange
        exec_client.fix_client.send_message = AsyncMock()
        exec_client._generate_request_id = AsyncMock(return_value="request_id1")

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.SELL,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        exec_client.cache.add_order(order)

        modify_order = ModifyOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=None,
            quantity=Quantity.from_str("0.02"),
            price=Price.from_str("1.50"),
            trigger_price=None,
            command_id=UUID4(),
            ts_init=0,
        )

        # Act
        await exec_client._modify_order(command=modify_order)

        # Assert
        msg = exec_client.fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is OrderCancelReplaceRequest
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(11) == b"request_id1"  # ClOrdId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8'
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert msg.get(18) == b"H"  # ExecInst=H (do not cancel on disconnect)
        assert msg.get(41) == b"a90dd4d7-c530-4add-8"  # OrigClOrdID
        assert msg.get(54) == b"2"  # Side
        assert msg.get(38) == b"0.02"  # OrderQty
        assert msg.get(44) == b"1.50"  # Price
        assert msg.get(40) == b"2"  # OrdType: LIMIT
        assert msg.get(59) == b"1"  # TimeInForce: GTC
        assert len(msg.pairs) == 11

    @pytest.mark.asyncio
    async def test_modify_limit_order_quantity_none_uses_order_quantity(self, exec_client):
        # Arrange
        exec_client.fix_client.send_message = AsyncMock()
        exec_client._generate_request_id = AsyncMock(return_value="request_id1")

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        exec_client.cache.add_order(order)

        modify_order = ModifyOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=None,
            quantity=None,
            price=Price.from_str("1.23"),
            trigger_price=None,
            command_id=UUID4(),
            ts_init=0,
        )

        # Act
        await exec_client._modify_order(command=modify_order)

        # Assert
        msg = exec_client.fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is OrderCancelReplaceRequest
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(11) == b"request_id1"  # ClOrdId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8'
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert msg.get(18) == b"H"  # ExecInst=H (do not cancel on disconnect)
        assert msg.get(41) == b"a90dd4d7-c530-4add-8"  # OrigClOrdID
        assert msg.get(54) == b"1"  # Side
        assert msg.get(38) == b"0.01"  # OrderQty
        assert msg.get(44) == b"1.23"  # Price
        assert msg.get(40) == b"2"  # OrdType: LIMIT
        assert msg.get(59) == b"1"  # TimeInForce: GTC
        assert len(msg.pairs) == 11

    @pytest.mark.asyncio
    async def test_modify_limit_order_price_none_uses_order_price(self, exec_client):
        # Arrange
        exec_client.fix_client.send_message = AsyncMock()
        exec_client._generate_request_id = AsyncMock(return_value="request_id1")

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        exec_client.cache.add_order(order)

        modify_order = ModifyOrder(
            trader_id=order.trader_id,
            strategy_id=order.strategy_id,
            instrument_id=order.instrument_id,
            client_order_id=order.client_order_id,
            venue_order_id=None,
            quantity=Quantity.from_str("0.02"),
            price=None,
            trigger_price=None,
            command_id=UUID4(),
            ts_init=0,
        )

        # Act
        await exec_client._modify_order(command=modify_order)

        # Assert
        msg = exec_client.fix_client.send_message.call_args[0][0]

        exec_client.fix_client.send_message.assert_called_once()
        assert type(msg) is OrderCancelReplaceRequest
        assert msg.get(48) == b"100934"  # SecurityId
        assert msg.get(11) == b"request_id1"  # ClOrdId
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8'
        assert msg.get(60) == b"19700101-00:00:00"  # TransactTime: required but ignored by LMAX
        assert msg.get(18) == b"H"  # ExecInst=H (do not cancel on disconnect)
        assert msg.get(41) == b"a90dd4d7-c530-4add-8"  # OrigClOrdID
        assert msg.get(54) == b"1"  # Side
        assert msg.get(38) == b"0.02"  # OrderQty
        assert msg.get(44) == b"1.23"  # Price
        assert msg.get(40) == b"2"  # OrdType: LIMIT
        assert msg.get(59) == b"1"  # TimeInForce: GTC
        assert len(msg.pairs) == 11

    @pytest.mark.asyncio
    async def test_handle_order_accepted(self, exec_client):
        """
        Test the LMAXLiveExecutinClient handles an ExecutionReport sent when a limit
        order is ACCEPTED.
        """
        # Arrange
        with open(FIX_RESPONSES / "limit_order_accepted.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_accepted = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_accepted.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("a90dd4d7-c530-4add-8"),
            venue_order_id=VenueOrderId("AACkAgAAAABD0xrA"),
            ts_event=1694773854928000000,
        )

    @pytest.mark.asyncio()
    async def test_handle_limit_order_filled_buy(self, exec_client):
        """
        Test the LMAXLiveExecutinClient handles an ExecutionReport sent when a limit
        order is FILLED.
        """
        # Arrange
        with open(FIX_RESPONSES / "limit_order_filled_buy.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_filled = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_filled.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("0e704426-d7cf-4eb3-a"),
            venue_order_id=VenueOrderId("AACkAgAAAABD0y1W"),
            venue_position_id=None,  # missing from LMAX
            trade_id=TradeId("QCSAEAAACNNJTCCL"),
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            last_qty=Quantity.from_int(1),
            last_px=Price.from_str("26627.25"),
            quote_currency=USD,
            commission=Money(0, XBT),  # missing from LMAX
            liquidity_side=LiquiditySide.TAKER,
            ts_event=1694774929193000000,
        )

    @pytest.mark.asyncio()
    async def test_handle_limit_order_filled_sell(self, exec_client):
        # Arrange
        with open(FIX_RESPONSES / "limit_order_filled_buy.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_filled = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_filled.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("0e704426-d7cf-4eb3-a"),
            venue_order_id=VenueOrderId("AACkAgAAAABD0y1W"),
            venue_position_id=None,  # missing from LMAX
            trade_id=TradeId("QCSAEAAACNNJTCCL"),
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            last_qty=Quantity.from_str("1.00"),
            last_px=Price.from_str("26627.25"),
            quote_currency=USD,
            commission=Money(0, XBT),  # missing from LMAX
            liquidity_side=LiquiditySide.TAKER,
            ts_event=1694774929193000000,
        )

    @pytest.mark.asyncio()
    async def test_handle_market_order_filled_buy(self, exec_client):
        # Arrange
        with open(FIX_RESPONSES / "limit_order_filled_buy.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_filled = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_filled.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("0e704426-d7cf-4eb3-a"),
            venue_order_id=VenueOrderId("AACkAgAAAABD0y1W"),
            venue_position_id=None,  # missing from LMAX
            trade_id=TradeId("QCSAEAAACNNJTCCL"),
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            last_qty=Quantity.from_int(1),
            last_px=Price.from_str("26627.25"),
            quote_currency=USD,
            commission=Money(0, XBT),  # missing from LMAX
            liquidity_side=LiquiditySide.TAKER,
            ts_event=1694774929193000000,
        )

    @pytest.mark.asyncio()
    async def test_handle_market_order_filled_sell(self, exec_client):
        # Arrange
        with open(FIX_RESPONSES / "market_order_filled_sell.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_filled = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_filled.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("5aef2f20-290b-474e-a"),
            venue_order_id=VenueOrderId("AACkAgAAAABD0zDO"),
            venue_position_id=None,  # missing from LMAX
            trade_id=TradeId("QCSAEAAACNNJ0K3C"),
            order_side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            last_qty=Quantity.from_int(1),
            last_px=Price.from_str("26639.17"),
            quote_currency=USD,
            commission=Money(0, XBT),  # missing from LMAX
            liquidity_side=LiquiditySide.TAKER,
            ts_event=1694775144479000000,
        )

    @pytest.mark.asyncio()
    async def test_handle_order_update(self, exec_client):
        # TODO: make response
        pass

    @pytest.mark.asyncio()
    async def test_handle_order_rejected(self, exec_client):
        """
        Test `LMAXExecutionClient` handles a `ExecutionReport` message where the format
        is `REJECTED`
        """
        # Arrange
        with open(FIX_RESPONSES / "limit_order_rejected.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_rejected = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_rejected.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("ecec3594-e669-441e-9"),
            reason="Illegal price for limit order",
            ts_event=1694775448548000000,
        )

    @pytest.mark.asyncio()
    async def test_handle_order_canceled(self, exec_client):
        """
        Test `LMAXExecutionClient` handles a `ExecutionReport` message where the format
        is `CANCELED`
        """
        # Arrange
        with open(FIX_RESPONSES / "limit_order_canceled.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_canceled = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_canceled.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("8e2b0a7f-0349-4cf9-9"),
            venue_order_id=VenueOrderId("AACkAgAAAABD00Pn"),
            ts_event=1694776175766000000,
        )

    @pytest.mark.asyncio()
    async def test_handle_cancel_order_reject(self, exec_client):
        # Arrange
        with open(FIX_RESPONSES / "") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_cancel_rejected = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_cancel_rejected.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("8e2b0a7f-0349-4cf9-9"),
            venue_order_id=VenueOrderId("AACkAgAAAABD00Pn"),
            ts_event=1694776175766000000,
        )

    @pytest.mark.asyncio()
    async def test_handle_modify_order_reject(self, exec_client):
        # Arrange
        with open(FIX_RESPONSES / "modify_order_cancel_reject_invalid_price.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        exec_client.generate_order_modify_rejected = Mock()
        exec_client._strategy_id = Mock(return_value=TestIdStubs.strategy_id())
        exec_client._utc_now = Mock(
            return_value=pd.Timestamp("2023-09-16 10:29:44.694348+00:00", tz="UTC"),
        )

        order = LimitOrder(
            trader_id=TestIdStubs.trader_id(),
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("8aea6b10-d1ac-4c95-8"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.01"),
            price=Price.from_str("1.23"),
            init_id=UUID4(),
            ts_init=0,
            time_in_force=TimeInForce.GTC,
        )
        order.apply(
            OrderAccepted(
                trader_id=order.trader_id,
                strategy_id=order.strategy_id,
                instrument_id=order.instrument_id,
                client_order_id=order.client_order_id,
                venue_order_id=VenueOrderId("AACkAgAAAABD00Pn"),
                account_id=TestIdStubs.account_id(),
                event_id=UUID4(),
                ts_event=0,
                ts_init=0,
            ),
        )
        exec_client.cache.add_order(order)
        exec_client.cache.update_order(order)

        # Act
        exec_client.handle_message(msg)

        # Assert
        exec_client.generate_order_modify_rejected.assert_called_once_with(
            strategy_id=TestIdStubs.strategy_id(),
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
            client_order_id=ClientOrderId("8aea6b10-d1ac-4c95-8"),
            venue_order_id=VenueOrderId("AACkAgAAAABD00Pn"),
            reason="PRICE_NOT_VALID",
            ts_event=1694860184694348000,
        )

    # @pytest.mark.asyncio()
    # async def test_cancel_order_rejected_unknown_order(self, exec_client, last_quote):
    #     # Arrange & Act
    #     order = await self.setup_limit_order(exec_client, last_quote=last_quote)
    #     print(f"order.client_order_id: {order.client_order_id}")
    #     CancelOrder(
    #         trader_id=order.trader_id,
    #         strategy_id=order.strategy_id,
    #         instrument_id=order.instrument_id,
    #         client_order_id=ClientOrderId("unknown"),  # invalid ClientOrderId
    #         venue_order_id=None,
    #         command_id=UUID4(),
    #         ts_init=0,
    #     )


# def test_handle_execution_report_order_submitted(self):
#     """
#     Test `LMAXExecutionClient` handles a `ExecutionReport` message where the format
#     is `SUBMITTED`
#     """

#     # Arrange
#     exec_client = LMAXMocks.exec_client()

#     instrument = LMAXMocks.xbt_usd_instrument()
#     exec_client.instrument_provider.add(instrument)

#     strategy_id = StrategyId("S-001")
#     client_order_id = ClientOrderId("C-001")
#     order_side = OrderSide.BUY
#     quantity = Quantity.from_str("0.01")

#     msg = f"8=FIX.4.4|9=208|35=8|34=2|49=LMXBD|52=20230811-18:02:15.002|56=|1=1649599582|6=0|11={client_order_id}|14=0|17=YlLkXgAAAAB4ifJm|22=8|37=AACkAgAAAABDLI4l|38=0.01|39=0|40=1|48=100934|54=1|59=4|60=20230811-18:02:15.000|150=0|151=0.01|527=0|10=38|"

#     order = MarketOrder(
#         trader_id=TraderId("001"),
#         strategy_id=strategy_id,
#         client_order_id=client_order_id,
#         instrument_id=instrument.id,
#         init_id=UUID4(),
#         order_side=order_side,
#         quantity=quantity,
#         ts_init=0,
#         time_in_force=TimeInForce.IOC,
#     )

#     exec_client._cache.add_order(order, PositionId("001"))
#     exec_client._set_account_id(AccountId("LMAX-001"))

#     exec_client.generate_order_submitted = Mock()

#     # Act
#     exec_client._client._handle_raw(string_to_raw(msg))

#     # Assert
#     exec_client.generate_order_submitted.assert_called_once_with(
#         strategy_id=strategy_id,
#         instrument_id=instrument.id,
#         client_order_id=client_order_id,
#         ts_event=1691776935000000000,
#     )


# @pytest.mark.asyncio
# async def test_submit_limit_order(self):
#     """
#     Test ExecutionClient sends a valid SubmitOrderSingle message.
#     """

#     # Arrange
#     exec_client = LMAXMocks.exec_client()

#     instrument = LMAXMocks.xbt_usd_instrument()
#     exec_client.instrument_provider.add(instrument)

#     order = LimitOrder(
#         trader_id=TraderId("001"),
#         strategy_id=StrategyId("S-001"),
#         instrument_id=instrument.id,
#         client_order_id=ClientOrderId("C-001"),
#         order_side=OrderSide.BUY,
#         quantity=Quantity.from_int(1),
#         price=Price.from_str("29450"),
#         init_id=UUID4(),
#         ts_init=0,
#         time_in_force=TimeInForce.FOK,
#     )

#     submit_order = SubmitOrder(
#         trader_id=order.trader_id,
#         strategy_id=order.strategy_id,
#         order=order,
#         command_id=UUID4(),
#         position_id=None,
#         ts_init=0,
#     )

#     exec_client._client.send_message = Mock()

#     # Act
#     await exec_client._submit_order(command=submit_order)

#     # Assert
#     msg = exec_client._client.send_message.call_args[0][0]
#     assert (
#         str(msg)
#         == "35=D|11=C-001|48=XBT/USD|22=100934|55=8|54=1|60=20200101-00:00:00.000000|38=1.0|40=1|59=4"
#     )

# class TestLMAXExecutionReports:
#     def setup(self):

#         self.exec_client = LMAXMocks.exec_client()
#         self.report_provider = self.exec_client._report_provider
#         self.instrument_provider = self.exec_client._instrument_provider
#         self.fix_client = self.exec_client._client
#         self.xml_client = self.exec_client._xml_client

#         # Add instrument
#         self.instrument = LMAXMocks.xbt_usd_instrument()
#         self.instrument_provider.add(self.instrument)

#         # Mock client send message
#         # self.send_mock = AsyncMock()
#         # self.fix_client.send_message = self.send_mock


# @pytest.mark.asyncio
# async def test_generate_order_status_report(self):
#     pass
# @pytest.mark.asyncio
# async def test_generate_position_status_reports_timeout(self):
#     pass

# @pytest.mark.asyncio
# async def test_cancel_order(self):
#     # TODO: finish when implementing limit orders
#     """
#     Test ExecutionClient sends a valid OrderCancelRequest message
#     """

#     # Arrange
#     exec_client = LMAXMocks.exec_client()

#     instrument = LMAXMocks.btc_usd_instrument()
#     exec_client.instrument_provider.add(instrument)

#     order = MarketOrder(
#         trader_id=TraderId("001"),
#         strategy_id=strategy_id,
#         client_order_id=client_order_id,
#         instrument_id=instrument.id,
#         init_id=UUID4(),
#         order_side=order_side,
#         quantity=quantity,
#         ts_init=0,
#         time_in_force=TimeInForce.IOC,
#     )

#     submit_order = CancelOrder(
#                     trader_id=TraderId("001"),
#                     strategy_id=StrategyId("S-001"),
#                     instrument_id=instrument.id,
#                     client_order_id=ClientOrderId("C-006"),
#                     venue_order_id=VenueOrderId("V-001"),
#                     command_id=UUID4(),
#                     ts_init=0,
#     )

#     exec_client._client.send_message = Mock()

#     # Act
#     await exec_client._cancel_order(command=submit_order)

#     # Assert
#     msg = exec_client._client.send_message.call_args[0][0]
#     assert str(msg) == "8=FIX.4.4|9=70|35=F|11=C-006|22=8|41=V-001|48=100934|55=BTC/USD|60=00060101-01:01:01|10=137|"

# @pytest.mark.asyncio
# async def test_modify_order(self):
#     # TODO finish when implementing limit orders
#     exec_client = LMAXMocks.exec_client()

#     instrument = LMAXMocks.btc_usd_instrument()
#     exec_client.instrument_provider.add(instrument)

#     exec_client._client.send_message = Mock()

#     msg = exec_client._client.send_message.call_args[0][0]

# @pytest.mark.asyncio
# async def test_cancel_all_orders(self):
#     # Arrange
#     exec_client = LMAXMocks.exec_client()

#     instrument = LMAXMocks.btc_usd_instrument()
#     exec_client.instrument_provider.add(instrument)

#     cancel_all_orders = CancelAllOrders(
#                     trader_id=TraderId("001"),
#                     strategy_id=StrategyId("S-001"),
#                     instrument_id=instrument.id,
#                     order_side=OrderSide.BUY,
#                     command_id=UUID4(),
#                     ts_init=0,
#     )

#     exec_client._client.send_message = Mock()

#     msg = exec_client._client.send_message.call_args[0][0]
#     # assert str(msg).replace(chr(1), "|") == "8=FIX.4.4|9=70|35=F|11=C-006|22=8|41=V-001|48=100934|55=BTC/USD|60=00060101-01:01:01|10=137|"

# venue_order_id = exec_client._cache.venue_order_id(order.client_order_id)
# await asyncio.sleep(0)


#         print(venue_order_id)
# venue_order_id = None
# while venue_order_id is None:
# time.sleep(1)
# await asyncio.sleep(0)

# print(venue_order_id)

# print(venue_order_id)
# exit()
# cancel_order = CancelOrder(
#                 trader_id=order.trader_id,
#                 strategy_id=order.strategy_id,
#                 instrument_id=order.instrument_id,
#                 client_order_id=order.client_order_id,
#                 venue_order_id=venue_order_id,
#                 command_id=UUID4(),
#                 ts_init=0,
# )

# exec_engine.disconnect()
# await asyncio.sleep(0)


# await exec_client._submit_order(command=cancel_order)

# @pytest.mark.asyncio
# async def test_generate_position_status_reports(self):
#     """
#     Test the ExecutionClient sends a valid TradeCaptureReportRequest message
#     """

#     # Arrange
#     exec_client = LMAXMocks.exec_client()

#     instrument = LMAXMocks.xbt_usd_instrument()
#     exec_client.instrument_provider.add(instrument)

#     exec_client._client.send_message = Mock()

#     # Act
#     await exec_client.generate_position_status_reports(
#                             instrument_id=instrument.id,
#                             start=pd.Timestamp("2023-08-10"),
#                             end=pd.Timestamp("2023-08-11"),
#                             )

#     # Assert
#     msg = exec_client._client.send_message.call_args[0][0]
#     msg.remove(568)  # TradeRequestID
#     assert str(msg).replace("\x01", "|") == "8=FIX.4.4|9=78|35=AD|2=2|60=20230810-00:00:00.000000|60=20230811-00:00:00.000000|569=0|580=2|10=122|"

# @pytest.mark.asyncio
# async def test_generate_position_status_reports_start_end_none(self):
#     """
#     Test the ExecutionClient sends a valid TradeCaptureReportRequest message when the start and end parameters are `None`
#     """

#     # Arrange
#     exec_client = LMAXMocks.exec_client()

#     instrument = LMAXMocks.xbt_usd_instrument()
#     exec_client.instrument_provider.add(instrument)

#     exec_client._client.send_message = Mock()

#     # Act
#     await exec_client.generate_position_status_reports(instrument_id=instrument.id)

#     # Assert
#     msg = exec_client._client.send_message.call_args[0][0]
#     msg.remove(568)  # TradeRequestID
#     assert str(msg) == f"8=FIX.4.4|9=78|35=AD|2=2|60=19700101-00:00:00.000000|60=22620411-23:47:16.854775|569=0|580=2|10=185|"


# def test_handle_limit_order_rejected(self):
#         """
#         Test `LMAXExecutionClient` handles a `ExecutionReport` message where the format
#         is `REJECTED`
#         """

#         # Arrange
#         exec_client = LMAXMocks.exec_client()

#         instrument = LMAXMocks.btc_usd_instrument()
#         exec_client.instrument_provider.add(instrument)

#         strategy_id = StrategyId("S-001")
#         client_order_id = ClientOrderId("C-001")
#         order_side = OrderSide.BUY
#         quantity = Quantity.from_str("1_000_000")  # invalid size

#         msg = f"8=FIX.4.4|9=213|35=8|34=2|49=LMXBD|52=20230811-11:48:15.801|56=ghill2|1=1649599582|6=0|11={client_order_id}|14=0|17=YlLkXgAAAAB4hu4t|22=8|37=0|39=8|48=100934|54=7|58=MAXIMUM_POSITION_EXCEEDED|60=20230811-11:48:15.801|103=0|150=8|151=0|527=0|10=179|"

#         order = MarketOrder(
#             trader_id=TraderId("001"),
#             strategy_id=strategy_id,
#             client_order_id=client_order_id,
#             instrument_id=instrument.id,
#             init_id=UUID4(),
#             order_side=order_side,
#             quantity=quantity,
#             ts_init=0,
#             time_in_force=TimeInForce.IOC,
#         )

#         exec_client._cache.add_order(order, PositionId("001"))
#         exec_client._set_account_id(AccountId("LMAX-001"))

#         exec_client.generate_order_rejected = Mock()

#         # Act
#         exec_client._client._handle_text(msg)

#         # Assert
#         exec_client.generate_order_rejected.assert_called_once_with(
#             strategy_id=strategy_id,
#             instrument_id=InstrumentId.from_str("BTC/USD.LMAX"),
#             client_order_id=client_order_id,
#             reason="MAXIMUM_POSITION_EXCEEDED",
#             ts_event=1691754495801000000,
#         )

# exec_client._cache.add_order(order, PositionId("001"))
# exec_client._set_account_id(AccountId("LMAX-001"))

# exec_client._generate_request_id = AsyncMock(return_value="request_id1")
# exec_client._utc_now = Mock(return_value=pd.Timestamp("2023-09-16 10:29:44.694348+00:00", tz="UTC"))

# exec_client._generate_request_id = AsyncMock(return_value="request_id1")
# exec_client._utc_now = Mock(return_value=pd.Timestamp("2023-09-16 10:29:44.694348+00:00", tz="UTC"))
# exec_client.fix_client.send_message = AsyncMock()
# exec_client._generate_request_id = AsyncMock(return_value="request_id1")
# exec_client._utc_now = Mock(return_value=pd.Timestamp("2023-09-16 10:29:44.694348+00:00", tz="UTC"))
# exec_client._generate_request_id = AsyncMock(return_value="request_id1")
# exec_client._utc_now = Mock(return_value=pd.Timestamp("2023-09-16 10:29:44.694348+00:00", tz="UTC"))
