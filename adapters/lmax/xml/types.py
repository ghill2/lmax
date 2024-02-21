from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from xml.etree.ElementTree import Element

import pandas as pd

from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import AssetClass
from nautilus_trader.model.enums import InstrumentClass
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.events.account import AccountState
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.instruments.base import Instrument
from nautilus_trader.model.objects import AccountBalance
from nautilus_trader.model.objects import MarginBalance
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from pytower.adapters.lmax import LMAX_VENUE
from pytower.adapters.lmax.xml.enums import LmaxAssetClass
from pytower.adapters.lmax.xml.enums import LmaxOrderType
from pytower.adapters.lmax.xml.enums import LmaxTimeInForce


@dataclass
class LmaxOrder:
    timeInForce: LmaxTimeInForce
    instructionId: str
    originalInstrumentId: str
    orderId: str
    accountId: int
    instrumentId: int
    quantity: Decimal
    matchedQuantity: Decimal
    matchedCost: Decimal
    cancelledQuantity: Decimal
    timestamp: pd.Timestamp
    orderType: LmaxOrderType
    openQuantity: Decimal
    openCost: Decimal
    cumulativeCost: Decimal
    commission: Decimal
    workingState: str
    price: Decimal | None = None
    stopReferencePrice: Decimal | None = None
    stopLossOffset: Decimal | None = None
    stopProfitOffset: Decimal | None = None

    @property
    def client_order_id(self) -> ClientOrderId:
        return ClientOrderId(self.instructionId)

    @property
    def venue_order_id(self) -> VenueOrderId:
        return VenueOrderId(self.orderId)

    @property
    def security_id(self) -> int:
        return self.instrumentId

    @property
    def side(self) -> OrderSide:
        return OrderSide.BUY if self.quantity > 0 else OrderSide.SELL

    def __repr__(self):
        return f"LmaxOrder({self.client_order_Id}, {self.side}, {self.security_id}, {abs(self.quantity)})"

    @classmethod
    def from_xml(cls, elem: Element) -> LmaxOrder:
        return cls(
            timeInForce=LmaxTimeInForce[elem.findtext("timeInForce")],
            instructionId=elem.findtext("instructionId"),
            originalInstrumentId=elem.findtext("originalInstrumentId"),
            orderId=elem.findtext("orderId"),
            accountId=int(elem.findtext("accountId")),
            instrumentId=int(elem.findtext("instrumentId")),
            quantity=Decimal(elem.findtext("quantity")),
            matchedQuantity=Decimal(elem.findtext("matchedQuantity")),
            matchedCost=Decimal(elem.findtext("matchedCost")),
            cancelledQuantity=Decimal(elem.findtext("cancelledQuantity")),
            timestamp=pd.to_datetime(
                elem.findtext("timestamp"),
                format="%Y-%m-%dT%H:%M:%S",
                utc=True,
            ),
            orderType=LmaxOrderType[elem.findtext("orderType")],
            openQuantity=Decimal(elem.findtext("openQuantity")),
            openCost=Decimal(elem.findtext("openCost")),
            cumulativeCost=Decimal(elem.findtext("cumulativeCost")),
            commission=Decimal(elem.findtext("commission")),
            workingState=elem.findtext("workingState"),
            stopReferencePrice=Decimal(elem.findtext("stopReferencePrice"))
            if elem.get("stopReferencePrice") is not None
            else None,
            stopLossOffset=Decimal(elem.findtext("stopLossOffset"))
            if elem.get("stopLossOffset") is not None
            else None,
            stopProfitOffset=Decimal(elem.findtext("stopProfitOffset"))
            if elem.get("stopProfitOffset") is not None
            else None,
            price=Decimal(elem.findtext("price")) if elem.get("price") is not None else None,
        )


@dataclass
class LmaxPosition:
    accountId: int
    instrumentId: int
    valuation: Decimal
    shortUnfilledCost: Decimal
    longUnfilledCost: Decimal
    openQuantity: Decimal
    cumulativeCost: Decimal
    openCost: Decimal

    @property
    def side(self) -> PositionSide:
        return PositionSide.LONG if self.openQuantity > 0 else PositionSide.SHORT

    @property
    def security_id(self) -> int:
        return self.instrumentId

    @classmethod
    def from_xml(cls, elem: Element) -> LmaxPosition:
        return cls(
            accountId=int(elem.findtext("accountId")),
            instrumentId=int(elem.findtext("instrumentId")),
            valuation=Decimal(elem.findtext("valuation")),
            shortUnfilledCost=Decimal(elem.findtext("shortUnfilledCost")),
            longUnfilledCost=Decimal(elem.findtext("longUnfilledCost")),
            openQuantity=Decimal(elem.findtext("openQuantity")),
            cumulativeCost=Decimal(elem.findtext("cumulativeCost")),
            openCost=Decimal(elem.findtext("openCost")),
        )

    def to_nautilus_report(self, instrument: Instrument) -> PositionStatusReport:
        return PositionStatusReport(
            account_id=AccountId(f"LMAX-{self.accountId}"),
            instrument_id=instrument.id,
            position_side=self.side,
            quantity=Quantity(float(abs(self.openQuantity)), instrument.size_precision),
            report_id=UUID4(),
            ts_last=0,  # missing from XML api
            ts_init=dt_to_unix_nanos(pd.Timestamp.utcnow()),
            venue_position_id=None,  # use NETTING account position resolution
        )


"""
TODO:
/// Get the margin rate as a percentage for this instrument.
/// Get the maxium position that can be held by a retail user on this instrument.
/// Get the price increment in which orders can be placed, i.e. the tick size.
"""


@dataclass
class LmaxInstrument:
    id: int
    name: str
    startTime: pd.Timestamp
    openingOffset: int
    closingOffset: int
    timezone: str  # 'Europe/London', 'America/New_York'
    margin: Decimal
    currency: str
    unitPrice: Decimal
    minimumOrderQuantity: Decimal
    orderQuantityIncrement: Decimal
    minimumPrice: Decimal
    maximumPrice: Decimal
    trustedSpread: Decimal
    priceIncrement: Decimal
    stopBuffer: int
    assetClass: LmaxAssetClass
    symbol: str
    maximumPositionThreshold: Decimal
    minimumCommission: Decimal
    tradingDays: list[str]
    retailVolatilityBandPercentage: int
    contractUnitOfMeasure: str
    contractSize: Decimal
    aggressiveCommissionRate: Decimal = None  # Currency excluding USD/RON, EUR/RON, EUR/RUB
    passiveCommissionRate: Decimal = None  # Currency excluding USD/RON, EUR/RON, EUR/RUB
    aggressiveCommissionPerContract: Decimal = None  # Index and USD/RON, EUR/RON, EUR/RUB
    passiveCommissionPerContract: Decimal = None  # Index and USD/RON, EUR/RON, EUR/RUB
    longSwapPoints: Decimal = None  # Currency
    shortSwapPoints: Decimal = None  # Currency
    swapPointValue: Decimal = None  # Currency
    fundingPremiumPercentage: Decimal = None  # Index
    fundingReductionPercentage: Decimal = None  # Index
    fundingBaseRate: Decimal = None  # Index
    dailyInterestRateBasis: Decimal = None  # Index

    @classmethod
    def from_xml(cls, elem: Element) -> LmaxInstrument:
        return cls(
            id=int(elem.findtext("id")),
            name=elem.findtext("name"),
            startTime=pd.to_datetime(elem.findtext("startTime"), format="%Y-%m-%dT%H:%M:%S"),
            openingOffset=int(elem.find("tradingHours").findtext("openingOffset")),
            closingOffset=int(elem.find("tradingHours").findtext("closingOffset")),
            timezone=elem.find("tradingHours").findtext("timezone"),
            margin=Decimal(elem.findtext("margin")),
            currency=elem.findtext("currency"),
            unitPrice=Decimal(elem.findtext("unitPrice")),
            minimumOrderQuantity=Decimal(elem.findtext("minimumOrderQuantity")),
            orderQuantityIncrement=Decimal(elem.findtext("orderQuantityIncrement")),
            minimumPrice=Decimal(elem.findtext("minimumPrice")),
            maximumPrice=Decimal(elem.findtext("maximumPrice")),
            trustedSpread=Decimal(elem.findtext("trustedSpread")),
            priceIncrement=Decimal(elem.findtext("priceIncrement")),
            stopBuffer=int(elem.findtext("stopBuffer")),
            assetClass=LmaxAssetClass[elem.findtext("assetClass")],
            symbol=elem.findtext("symbol"),
            maximumPositionThreshold=Decimal(elem.findtext("maximumPositionThreshold")),
            minimumCommission=Decimal(elem.findtext("minimumCommission")),
            tradingDays=[elem.text for elem in elem.find("tradingDays")],
            retailVolatilityBandPercentage=int(elem.findtext("retailVolatilityBandPercentage")),
            contractUnitOfMeasure=elem.findtext("contractUnitOfMeasure"),
            contractSize=Decimal(elem.findtext("contractSize")),
            aggressiveCommissionRate=Decimal(elem.findtext("aggressiveCommissionRate"))
            if elem.findtext("aggressiveCommissionRate") is not None
            else None,
            passiveCommissionRate=Decimal(elem.findtext("passiveCommissionRate"))
            if elem.findtext("passiveCommissionRate") is not None
            else None,
            aggressiveCommissionPerContract=Decimal(
                elem.findtext("aggressiveCommissionPerContract"),
            )
            if elem.findtext("aggressiveCommissionPerContract") is not None
            else None,
            passiveCommissionPerContract=Decimal(elem.findtext("passiveCommissionPerContract"))
            if elem.findtext("passiveCommissionPerContract") is not None
            else None,
            # longSwapPoints=Decimal(elem.findtext("longSwapPoints"))
            #     if elem.findtext("longSwapPoints") is not None else None,
            # shortSwapPoints=Decimal(elem.findtext("shortSwapPoints"))
            #     if elem.findtext("shortSwapPoints") is not None else None,
            # swapPointValue=Decimal(elem.findtext("swapPointValue"))
            #     if elem.findtext("swapPointValue") is not None else None,
            # fundingPremiumPercentage=Decimal(elem.findtext("fundingPremiumPercentage"))
            #     if elem.findtext("fundingPremiumPercentage") is not None else None,
            # fundingReductionPercentage=Decimal(elem.findtext("fundingReductionPercentage"))
            #     if elem.findtext("fundingReductionPercentage") is not None else None,
            # fundingBaseRate=Decimal(elem.findtext("fundingBaseRate"))
            #     if elem.findtext("fundingBaseRate") is not None else None,
            # dailyInterestRateBasis=Decimal(elem.findtext("dailyInterestRateBasis"))
            #     if elem.findtext("dailyInterestRateBasis") is not None else None,
        )

    def to_nautilus(self) -> Instrument:
        base_currency = Currency.from_str(self.contractUnitOfMeasure)
        quote_currency = Currency.from_str(self.currency)

        if self.assetClass == LmaxInstrumentClass.CURRENCY:
            if Currency.is_crypto(str(base_currency)):
                asset_class = InstrumentClass.CRYPTOCURRENCY
            elif Currency.is_fiat(str(base_currency)) == Decimal(10000):
                asset_class = InstrumentClass.FX
            elif any(key in self.name for key in ["Brent", "Crude", "Gas"]):
                asset_class = InstrumentClass.ENERGY
            else:
                asset_class = InstrumentClass.METAL
        elif self.assetClass == LmaxInstrumentClass.INDEX:
            asset_class = InstrumentClass.EQUITY

        if self.aggressiveCommissionPerContract is not None:
            asset_type = AssetType.CFD
        elif self.aggressiveCommissionRate is not None:
            asset_type = AssetType.SPOT

        # if self.assetClass == LmaxInstrumentClass.INDEX:
        #     return None  # TODO: fix Index instruments

        return Instrument(
            instrument_id=InstrumentId(symbol=Symbol(self.symbol), venue=LMAX_VENUE),
            raw_symbol=Symbol(self.symbol),
            asset_class=asset_class,
            asset_type=asset_type,
            # base_currency=base_currency,
            quote_currency=quote_currency,
            is_inverse=False,
            price_precision=Price.from_str(str(self.priceIncrement)).precision,
            size_precision=Quantity.from_str(str(self.orderQuantityIncrement)).precision,
            price_increment=Price.from_str(str(self.priceIncrement)),
            size_increment=Quantity.from_str(str(self.orderQuantityIncrement)),
            multiplier=Quantity.from_str(str(self.contractSize)),
            lot_size=None,
            max_quantity=Quantity.from_str(str(self.maximumPositionThreshold)),
            min_quantity=Quantity.from_str(str(self.minimumOrderQuantity)),
            max_notional=None,  # missing from LMAX
            min_notional=None,  # missing from LMAX
            min_price=Price.from_str(str(self.minimumPrice)),
            max_price=Price.from_str(str(self.maximumPrice)),
            margin_init=self.margin,
            margin_maint=self.margin,
            taker_fee=self.aggressiveCommissionRate
            if self.aggressiveCommissionRate is not None
            else self.aggressiveCommissionPerContract,
            maker_fee=self.passiveCommissionRate
            if self.passiveCommissionRate is not None
            else self.passiveCommissionPerContract,
            ts_event=0,  # missing from LMAX
            ts_init=dt_to_unix_nanos(pd.Timestamp.utcnow()),
            info={
                "id": self.id,
                "assetClass": self.InstrumentClass.name,
                "retailVolatilityBandPercentage": self.retailVolatilityBandPercentage,
                "maximumPositionThreshold": self.maximumPositionThreshold,
                "startTime": self.startTime,
                "openingOffset": self.openingOffset,
                "closingOffset": self.closingOffset,
                "timezone": self.timezone,
                "unitPrice": self.unitPrice,
                "trustedSpread": self.trustedSpread,
                "stopBuffer": self.stopBuffer,
                "minimumCommission": self.minimumCommission,
                "tradingDays": self.tradingDays,
            },
        )


@dataclass
class LmaxWallet:
    currency: str
    balance: Decimal
    cash: Decimal
    availableToWithdraw: Decimal

    @classmethod
    def from_xml(cls, elem: Element) -> LmaxWallet:
        return cls(
            currency=elem.findtext("currency"),
            balance=Decimal(elem.findtext("balance")),
            cash=Decimal(elem.findtext("cash")),
            availableToWithdraw=Decimal(elem.findtext("availableToWithdraw")),
        )


@dataclass
class LmaxAccountState:
    accountId: int
    balance: Decimal
    cash: Decimal
    credit: Decimal
    totalCollateralizedCredit: Decimal
    usedCollateralizedCredit: Decimal
    availableFunds: Decimal
    availableToWithdraw: Decimal
    unrealisedProfitAndLoss: Decimal
    margin: Decimal
    wallets: list[LmaxWallet]
    active: bool

    @classmethod
    def from_xml(cls, elem: Element) -> LmaxAccountState:
        return cls(
            accountId=int(elem.findtext("accountId")),
            balance=Decimal(elem.findtext("balance")),
            cash=Decimal(elem.findtext("cash")),
            credit=Decimal(elem.findtext("credit")),
            totalCollateralizedCredit=Decimal(elem.findtext("totalCollateralizedCredit")),
            usedCollateralizedCredit=Decimal(elem.findtext("usedCollateralizedCredit")),
            availableFunds=Decimal(elem.findtext("availableFunds")),
            availableToWithdraw=Decimal(elem.findtext("availableToWithdraw")),
            unrealisedProfitAndLoss=Decimal(elem.findtext("unrealisedProfitAndLoss")),
            margin=Decimal(elem.findtext("margin")),
            wallets=[LmaxWallet.from_xml(elem) for elem in elem.findall(".//wallet")],
            active=bool(elem.findtext("margin")),
        )

    def to_nautilus_account_balance(self) -> AccountBalance:
        wallet = self.wallets[0]
        currency = Currency.from_str(wallet.currency)

        total = Money(self.balance, currency)
        free = Money(self.availableFunds, currency)
        locked = Money.from_raw(total.raw - free.raw, currency)

        return AccountBalance(
            total=Money(total, currency),
            locked=Money(locked, currency),
            free=Money(free, currency),
        )

    def to_nautilus_margin_balance(self) -> MarginBalance:
        wallet = self.wallets[0]
        currency = Currency.from_str(wallet.currency)
        return MarginBalance(
            initial=Money(self.margin, currency),
            maintenance=Money(self.margin, currency),
        )

    def to_nautilus(self) -> AccountBalance:
        return AccountState(
            account_id=AccountId(f"LMAX-{self.accountId}"),
            account_type=AccountType.MARGIN,
            base_currency=Currency.from_str(self.wallets[0].currency),
            reported=True,
            balances=[self.to_nautilus_account_balance()],
            margins=[self.to_nautilus_margin_balance()],
            info={
                "cash": self.cash,
                "credit": self.credit,
                "totalCollateralizedCredit": self.totalCollateralizedCredit,
                "usedCollateralizedCredit": self.usedCollateralizedCredit,
                "availableFunds": self.availableFunds,
                "availableToWithdraw": self.availableToWithdraw,
                "unrealisedProfitAndLoss": self.unrealisedProfitAndLoss,
                "margin": self.margin,
            },
            event_id=UUID4(),
            ts_event=0,  # missing from LMAX
            ts_init=dt_to_unix_nanos(pd.Timestamp.utcnow()),
        )


#     def parse_to_account_balance(self) -> AccountBalance:
# currency = Currency.from_str(self.asset)
# total = Decimal(self.walletBalance)
# locked = Decimal(self.initialMargin) + Decimal(self.maintMargin)
# free = total - locked
# return AccountBalance(
#     total=Money(total, currency),
#     locked=Money(locked, currency),
#     free=Money(free, currency),
# )


# def parse_to_margin_balance(self) -> MarginBalance:
#     currency: Currency = Currency.from_str(self.asset)
#     return MarginBalance(
#         initial=Money(Decimal(self.initialMargin), currency),
#         maintenance=Money(Decimal(self.maintMargin), currency),
#     )

# TODO
# @dataclass
# class LMAXContract(LMAXInstrument):
#     passiveCommissionPerContract: Decimal
#     aggressiveCommissionPerContract: Decimal
#     fundingPremiumPercentage: Decimal
#     fundingReductionPercentage: Decimal

#     contractUnitOfMeasure: str
#     fundingBaseRate: str | None
#     underlyingIsin: str | None

#     @classmethod
#     def from_xml(cls, elem: Element) -> LMAXInstrument:
#         return cls(
#             id=int(elem.findtext("id")),
#             name=elem.findtext("name"),
#             startTime=pd.to_datetime(elem.findtext("startTime"), format="%Y-%m-%dT%H:%M:%S"),
#             openingOffset=int(elem.find("tradingHours").findtext("openingOffset")),
#             closingOffset=int(elem.find("tradingHours").findtext("closingOffset")),
#             timezone=elem.find("tradingHours").findtext("timezone"),
#             margin=Decimal(elem.findtext("margin")),
#             currency=elem.findtext("currency"),
#             unitPrice=Decimal(elem.findtext("unitPrice")),
#             minimumOrderQuantity=Decimal(elem.findtext("unitPrice")),
#             orderQuantityIncrement=Decimal(elem.findtext("orderQuantityIncrement")),
#             minimumPrice=Decimal(elem.findtext("minimumPrice")),
#             maximumPrice=Decimal(elem.findtext("maximumPrice")),
#             trustedSpread=Decimal(elem.findtext("trustedSpread")),
#             priceIncrement=Decimal(elem.findtext("priceIncrement")),
#             stopBuffer=int(elem.findtext("stopBuffer")),
#             assetClass=LMAXAssetClass[elem.findtext("assetClass")],
#             symbol=elem.findtext("symbol"),
#             maximumPositionThreshold=Decimal(elem.findtext("maximumPositionThreshold")),
#             minimumCommission=Decimal(elem.findtext("minimumCommission")),
#             tradingDays=[elem.text for elem in elem.find("tradingDays")],
#             retailVolatilityBandPercentage=int(elem.findtext("retailVolatilityBandPercentage")),
#             passiveCommissionPerContract=Decimal(elem.findtext("passiveCommissionPerContract")),
#             aggressiveCommissionPerContract=Decimal(elem.findtext("aggressiveCommissionPerContract")),
#             fundingPremiumPercentage=Decimal(elem.findtext("fundingPremiumPercentage")),
#             fundingReductionPercentage=Decimal(elem.findtext("fundingReductionPercentage")),
#             contractSize=Decimal(elem.findtext("contractSize")),
#             contractUnitOfMeasure=elem.findtext("contractUnitOfMeasure"),
#             fundingBaseRate=elem.findtext("fundingBaseRate")
#                                 if elem.findtext("fundingBaseRate") is not None else None
#             underlyingIsin=elem.findtext("underlyingIsin")
#                                 if elem.findtext("underlyingIsin") is not None else None
#         )


"""
blance, cash, credit, availableFunds
blance = total
free = availableFunds
locked =

cash = balance - money for orders


"""
"""
account_id : AccountId
    The account ID (with the venue).
account_type : AccountId
    The account type for the event.
base_currency : Currency, optional
    The account base currency. Use None for multi-currency accounts.
reported : bool
    If the state is reported from the exchange (otherwise system calculated).
balances : list[AccountBalance]
    The account balances.
margins : list[MarginBalance]
    The margin balances (can be empty).
info : dict [str, object]
    The additional implementation specific account information.
event_id : UUID4
    The event ID.
ts_event : uint64_t
    The UNIX timestamp (nanoseconds) when the account state event occurred.
ts_init : uint64_t
    The UNIX timestamp (nanoseconds) when the object was initialized.
"""
"""
Represents a margin balance optionally associated with a particular instrument.

Parameters
----------
initial : Money
    The initial (order) margin requirement for the instrument.
maintenance : Money
    The maintenance (position) margin requirement for the instrument.
instrument_id : InstrumentId, optional
    The instrument ID associated with the margin.

Account Balance
total : Money
    The total account balance.
locked : Money
    The account balance locked (assigned to pending orders).
free : Money
    The account balance free for trading.

"""

# class BinanceFuturesBalanceInfo(msgspec.Struct, frozen=True):
#     """
#     HTTP response 'inner struct' from `Binance Futures` GET /fapi/v2/account (HMAC
#     SHA256).
#     """

#     asset: str  # asset name
#     walletBalance: str  # wallet balance
#     unrealizedProfit: str  # unrealized profit
#     marginBalance: str  # margin balance
#     maintMargin: str  # maintenance margin required
#     initialMargin: str  # total initial margin required with current mark price
#     positionInitialMargin: str  # initial margin required for positions with current mark price
#     openOrderInitialMargin: str  # initial margin required for open orders with current mark price
#     crossWalletBalance: str  # crossed wallet balance
#     crossUnPnl: str  # unrealized profit of crossed positions
#     availableBalance: str  # available balance
#     maxWithdrawAmount: str  # maximum amount for transfer out
#     # whether the asset can be used as margin in Multi - Assets mode
#     marginAvailable: Optional[bool] = None
#     updateTime: Optional[int] = None  # last update time

#     def parse_to_account_balance(self) -> AccountBalance:
#         currency = Currency.from_str(self.asset)
#         total = Decimal(self.walletBalance)
#         locked = Decimal(self.initialMargin) + Decimal(self.maintMargin)
#         free = total - locked
#         return AccountBalance(
#             total=Money(total, currency),
#             locked=Money(locked, currency),
#             free=Money(free, currency),
#         )

#     def parse_to_margin_balance(self) -> MarginBalance:
#         currency: Currency = Currency.from_str(self.asset)
#         return MarginBalance(
#             initial=Money(Decimal(self.initialMargin), currency),
#             maintenance=Money(Decimal(self.maintMargin), currency),
#         )
