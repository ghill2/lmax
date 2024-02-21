from __future__ import annotations

from enum import Enum

from nautilus_trader.model.enums import OrderStatus


class LmaxAggregateOption(Enum):
    BID = "BID"
    ASK = "ASK"


class LmaxAggregateResolution(Enum):
    MINUTE = "MINUTE"
    DAY = "DAY"


class LmaxAssetClass(Enum):
    CURRENCY = "CURRENCY"
    INDEX = "INDEX"


class LmaxOrderType(Enum):
    STOP_COMPOUND_PRICE_LIMIT = 1
    PRICE_LIMIT = 2
    STOP_COMPOUND_MARKET = 3
    MARKET_ORDER = 4
    STOP_LOSS_ORDER = 5
    STOP_PROFIT_ORDER = 6
    STOP_ORDER = 7


class LmaxTimeInForce(Enum):
    FillOrKill = 1
    ImmediateOrCancel = 2
    GoodForDay = 3
    GoodTilCancelled = 4


class LmaxOrderStatus(Enum):
    """
    Tag 39 Identifies current status of order.

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

    def to_nautilus(self) -> OrderStatus:
        if self.value == 0:
            return OrderStatus.SUBMITTED
        elif self.value == 1:
            return OrderStatus.PARTIALLY_FILLED
        elif self.value == 2:
            return OrderStatus.FILLED
        elif self.value == 4:
            return OrderStatus.CANCELED
        elif self.value == 8:
            return OrderStatus.REJECTED

    def from_int(self, value: int) -> LmaxOrderStatus:
        if self.value == 0:
            return LmaxOrderStatus.NEW
        elif self.value == 1:
            return LmaxOrderStatus.PARTIALLY_FILLED
        elif self.value == 2:
            return LmaxOrderStatus.FILLED
        elif self.value == 4:
            return LmaxOrderStatus.CANCELED
        elif self.value == 8:
            return LmaxOrderStatus.REJECTED
