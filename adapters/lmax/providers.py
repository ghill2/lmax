from nautilus_trader.common.component import Logger
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config.common import InstrumentProviderConfig
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments.base import Instrument
from pytower.adapters.lmax import LMAX_VENUE
from pytower.adapters.lmax.xml.client import LmaxXmlClient


class LmaxInstrumentProvider(InstrumentProvider):
    def __init__(
        self,
        xml_client: LmaxXmlClient,
        logger: Logger,
        config: InstrumentProviderConfig = None,
    ):
        super().__init__(
            venue=LMAX_VENUE,
            logger=logger,
            config=config,
        )
        self._instrument_map = {}  # dict[int, Instrument]
        self._xml_client = xml_client

    @property
    def xml_client(self) -> LmaxXmlClient:
        return self._xml_client

    async def load_all_async(self, filters: dict | None = None) -> None:
        instruments = await self._xml_client.request_instruments(query="")
        for instrument in instruments:
            self.add(instrument)
        # self._instrument_map =
        # for instrument in self._instrument_map.values():
        # self.add(instrument)

    def add(self, instrument: Instrument) -> None:
        self._instrument_map[instrument.info["id"]] = instrument
        super().add(instrument)

    def find_with_security_id(self, instrument_id: int) -> Instrument | None:
        return self._instrument_map.get(instrument_id)

    def get_security_id(self, instrument_id: InstrumentId) -> int | None:
        instrument = self.find(instrument_id)
        return instrument.info["id"] if instrument is not None else None

    # async def request_instrument_map(self) -> dict[int, Instrument]:
    #     """
    #     Return a map to convert from an LMAX security id to an Instrument.
    #     """
    #     return {
    #         instrument.info["id"]: instrument
    #         for instrument in await self._xml_client.request_instruments(query="")
    #     }

    # async def load_ids_async(
    #     self,
    #     instrument_ids: list[InstrumentId],
    #     filters: dict | None = None,
    # ) -> None:

    #     for instrument_id in instrument_ids:
    #         await self.load_async(instrument_id)

    # async def load_async(
    #     self,
    #     instrument_id: InstrumentId,
    #     filters: dict | None = None,
    # ) -> None:
    #     instruments = await self._query_instruments(query=f"symbol: {instrument_id.symbol.value}")
    #     instrument = instruments[0]
    #     self.add(instrument)
    #     self._instrument_for_security_id[instrument.info["id"]] = instrument


# async def load_async(self, instrument_id: InstrumentId, filters: Optional[dict] = None):
#     instrument = self._client.request_instruments(query=f"symbol: {instrument_id.symbol}")[0]
#     self._add(instrument)

# if __name__ == "__main__":
#     from dotenv import dotenv_values
#     from nautilus_trader.common.component import LiveClock
#     async def main_():

#         logger = Logger(clock=LiveClock())

#         dll = LMAXDLL(
#                     username=dotenv_values()['username'],
#                     password=dotenv_values()['password'],
#                     hostname="https://web-order.london-demo.lmax.com",
#         )
#         await dll.connect()

#         provider = LMAXInstrumentProvider(dll=dll, logger=logger)

#         await provider.load_async(InstrumentId.from_str("EUR/USD.LMAX"))

#     asyncio.run(main_())


"""
"Instrument",
"BettingInstrument",
"CryptoFuture",
"CryptoPerpetual",
"CurrencyPair",
"Equity",
"FuturesContract",
"OptionsContract",
"""

"""
Instrument
    Id
    Name
    Underlying
        Symbol
        Isin
        AssetClass
        GetHashCode()
        ToString()
    Calendar
        StartTime
        ExpiryTime
        Open
        Close
        TimeZone
        TradingDays
    Risk
        MarginRate -> decimal  /// Get the margin rate as a percentage for this instrument.
        MaximumPosition -> decimal
    OrderBook
        PriceIncrement
        QuantityIncrement
        VolatilityBandPercentage
    Contract
        Currency -> String
        UnitPrice -> decimal
        UnitOfMeasure -> String
        ContractSize -> decimal
    Commercial
        MinimumCommission -> decimal  /// Get the minimum commission applied for a trade on this instrument.
        AggressiveCommissionRate -> decimal
        PassiveCommissionRate -> decimal
        PassiveCommissionPerContract -> decimal
        FundingBaseRate -> string
        FundingPremiumPercentage -> decimal
        FundingReductionPercentage -> decimal
        LongSwapPoints -> decimal
        ShortSwapPoints -> decimal
"""


# async def load_all_async(self, filters: Optional[dict] = None) -> None:
#     raise NotImplementedError("method must be implemented in the subclass")  # pragma: no cover

# async def load_ids_async(
#     self,
#     instrument_ids: list[InstrumentId],
#     filters: Optional[dict] = None,
# ) -> None:
#     raise NotImplementedError("method must be implemented in the subclass")  # pragma: no cover

# async def load_async(self, instrument_id: InstrumentId, filters: Optional[dict] = None):
#     """
#     To find a specific instrument the "id: (instrumentId)" form can be used.
#     To do a general search, use a term such as "CURRENCY", which will find all of the currency instruments.
#     A search term like "UK" will find all of the instruments that have "UK" in the name.
#     """
#     self._log.info(f"Searching for {instrument_id}")

#     future = asyncio.Future()
#     def _on_search_callback(self, instruments: list[LMAXInstrument], _: bool) -> list[Instrument]:
#         self._log.info(f"Received {len(instruments)} instruments.")
#         if len(instruments) == 0:
#             return future.set_result(None)
#         else:
#             instruments = [
#                 lmax_instrument_to_nautilus_instrument(instrument)
#                 for instrument in instruments
#             ]
#         future.set_result(instruments)

#     request = SearchRequest(str(instrument_id.symbol), 0)
#     callback = OnSearchResponse(self._on_search_callback)
#     self.dll.session.SearchInstruments(request, callback, on_failure)
#     return await future
