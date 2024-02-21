from enum import Enum

from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce


class ExecType(Enum):
    """
    150 ExecType: ExecType Describes the type of execution being reported by this ExecutionReport message.
    Describes the specific ExecutionRpt (i.e. Pending Cancel) while OrdStatus (39) will always identify the current order status (i.e. Partially Filled)
    LMAX supported values:
        0 = New,
        4 = Canceled,
        5 = Replace,
        8 = Rejected,
        F = Trade (partial fill or fill),
        I = Order Status
    """

    NEW = "0"
    CANCELED = "4"
    REPLACE = "5"
    REJECTED = "8"
    TRADE = "F"
    ORDER_STATUS = "I"


class OrdStatus(Enum):
    """
    Identifies current status of order.

    LMAX supported values:
    0 = New
    1 = Partially filled
    2 = Filled
    4 = Canceled
    8 = Rejected

    """

    NEW = 0
    PARTIALLY_FILLED = 1
    FILLED = 2
    CANCELED = 4
    REJECTED = 8


def parse_lmax_exec_type(value: str) -> ExecType:
    """
    Tag 150
    ExecType: ExecType Describes the type of execution being reported by this ExecutionReport message.
    Describes the specific ExecutionRpt (i.e. Pending Cancel) while OrdStatus (39) will always identify the current order status (i.e. Partially Filled)
    LMAX supported values:
        0 = New,
        4 = Canceled,
        5 = Replace,
        8 = Rejected,
        F = Trade (partial fill or fill),
        I = Order Status
    """
    if value == "0":
        return ExecType.NEW
    elif value == "4":
        return ExecType.CANCELED
    elif value == "5":
        return ExecType.REPLACE
    elif value == "8":
        return ExecType.REJECTED
    elif value == "F":
        return ExecType.TRADE
    elif value == "I":
        return ExecType.ORDER_STATUS


def parse_lmax_order_side(value: int) -> OrderSide:
    """
    54      Side    Side of the order.

    Valid values:
    1 = Buy
    2 = Sell

    """
    if value == 1:
        return OrderSide.BUY
    elif value == 2:
        return OrderSide.SELL


def parse_lmax_order_status(value: int) -> OrderStatus:
    """
    Tag 39 Identifies current status of order.

    LMAX supported values:
    0 = New
    1 = Partially filled
    2 = Filled
    4 = Canceled
    8 = Rejected

    """
    if value == 0:
        return OrderStatus.ACCEPTED
    elif value == 1:
        return OrderStatus.PARTIALLY_FILLED
    elif value == 2:
        return OrderStatus.FILLED
    elif value == 4:
        return OrderStatus.CANCELED
    elif value == 8:
        return OrderStatus.REJECTED


def parse_lmax_time_in_force(value: int) -> TimeInForce:
    """
    Tag 59 TimeInForce:     char    Specifies how long the order remains in effect.

    Valid values:
    0 = Day (trading session)
    1 = Good Till Cancel  (GTC)
    3 = Immediate or Cancel  (IOC)
    4 = Fill or Kill  (FOK)

    """
    if value == 0:
        return TimeInForce.DAY
    elif value == 1:
        return TimeInForce.GTC
    elif value == 3:
        return TimeInForce.IOC
    elif value == 4:
        return TimeInForce.FOK


def parse_lmax_order_type(value: int) -> OrderType:
    """
    Tag 40 OrdType  Order type.

    LMAX Supported values:
    1 = Market
    2 = Limit
    3 = Stop
    4 = Stop Limit

    """
    if value == 1:
        return OrderType.MARKET
    elif value == 2:
        return OrderType.LIMIT
    elif value == 3:
        return OrderType.STOP_MARKET
    elif value == 4:
        return OrderType.STOP_LIMIT
