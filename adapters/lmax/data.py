"""
The DataClient class is responsible for subscribing and unsubscribing to data.
"""

import asyncio
from functools import partial

import pandas as pd
from simplefix import FixMessage

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.live.data_client import LiveMarketDataClient
from nautilus_trader.model.data import BarAggregation
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import DataType
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.enums import bar_aggregation_to_str
from nautilus_trader.model.enums import price_type_to_str
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.common.component import MessageBus
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler
from pytower.adapters.lmax import LMAX_VENUE
from pytower.adapters.lmax.fix.client import LmaxFixClient
from pytower.adapters.lmax.fix.messages import MarketDataRequest
from pytower.adapters.lmax.fix.messages import MarketDataRequestReject
from pytower.adapters.lmax.fix.messages import MarketDataSnapshotFullRefresh
from pytower.adapters.lmax.fix.parsing import parse_lmax_timestamp_ns
from pytower.adapters.lmax.providers import LmaxInstrumentProvider
from pytower.adapters.lmax.xml.client import LmaxXmlClient
from pytower.adapters.lmax.xml.enums import LmaxAggregateOption
from pytower.adapters.lmax.xml.enums import LmaxAggregateResolution
from pytower.adapters.lmax.xml.historic import LmaxBarDataGenerator
from pytower.adapters.lmax.xml.historic import LmaxQuoteTickDataGenerator


class LmaxLiveDataClient(LiveMarketDataClient):
    def __init__(
        self,
        fix_client: LmaxFixClient,
        xml_client: LmaxXmlClient,
        instrument_provider: LmaxInstrumentProvider,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        logger: Logger,
        loop: asyncio.AbstractEventLoop,
    ):
        super().__init__(
            loop=loop,
            client_id=ClientId(LMAX_VENUE.value),
            venue=LMAX_VENUE,
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            logger=logger,
        )

        self._fix_client = fix_client
        self._xml_client = xml_client
        self._fix_client.register_handler(self.handle_message)
        self._instrument_provider = instrument_provider
        self._logger = logger

    @property
    def xml_client(self) -> LmaxXmlClient:
        return self._xml_client

    @property
    def fix_client(self) -> LmaxFixClient:
        return self._fix_client

    @property
    def instrument_provider(self) -> LmaxInstrumentProvider:
        return self._instrument_provider

    @property
    def cache(self) -> Cache:
        return self._cache

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    @property
    def msgbus(self) -> MessageBus:
        return self._msgbus

    @property
    def clock(self) -> LiveClock:
        return self._clock

    @property
    def logger(self) -> Logger:
        return self._logger

    async def _connect(self) -> None:
        await self._xml_client.connect()
        await self._fix_client.connect()

        await self._instrument_provider.initialize()

        # Pass any preloaded instruments into the engine
        if self._instrument_provider.count == 0:
            await self._instrument_provider.load_all_async()
        instruments = self._instrument_provider.list_all()
        self._log.debug(f"Loading {len(instruments)} instruments from provider into cache, ")
        for instrument in instruments:
            self._handle_data(instrument)

        self._log.debug(
            f"DataEngine has {len(self._cache.instruments(LMAX_VENUE))} Lmax instruments",
        )

    async def _disconnect(self) -> None:
        await self._fix_client.disconnect()
        await self._xml_client.disconnect()

    async def _subscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        self._log.info(f"Subscribing to quote ticks: {instrument_id}")
        await self._send_market_data_request(
            cls=QuoteTick,
            instrument_id=instrument_id,
            subscribe=True,
        )

    async def _unsubscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
        self._log.info(f"Unsubscribing to quote ticks: {instrument_id}")
        await self._send_market_data_request(
            cls=QuoteTick,
            instrument_id=instrument_id,
            subscribe=False,
        )

    async def _send_market_data_request(
        self,
        cls: DataType,
        instrument_id: InstrumentId,
        subscribe: bool,
    ) -> None:
        instrument = self._instrument_provider.find(instrument_id)
        if instrument is None:
            self._log.error(f"Instrument not found: {instrument_id}")
            return

        msg = MarketDataRequest()

        msg.append_pair(262, cls.__name__ + "-" + instrument.id.value)  # MDReqID

        if subscribe:
            # SubscriptionRequestType: Snapshot + Updates (Subscribe)
            msg.append_pair(263, 1)
        else:
            # SubscriptionRequestType: Disable previous Snapshot + Updates Request (Unsubscribe)
            msg.append_pair(263, 2)

        msg.append_pair(264, 1)  # MarketDepth: 1 = Top of Book

        msg.append_pair(267, 2)  # NoMDEntryTypes
        msg.append_pair(269, 0)  # MDEntryType: Bid
        msg.append_pair(269, 1)  # MDEntryType: Ask

        msg.append_pair(146, 1)  # NoRelatedSym
        msg.append_pair(48, instrument.info["id"])  # SecurityID
        msg.append_pair(22, 8)  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)

        await self._fix_client.send_message(msg)

    async def _subscribe_instrument(self, instrument_id: InstrumentId) -> None:
        self._instrument_provider.load(instrument_id)
        instrument = self._instrument_provider.find(instrument_id)
        self._handle_data(instrument)

    async def _subscribe_instruments(self) -> None:
        for instrument in self._instrument_provider.list_all():
            self._handle_data(instrument)

    async def handle_message(self, msg: FixMessage) -> None:
        self._log.info(f"Handling: {type(msg).__name__}({msg})")
        if type(msg) is MarketDataSnapshotFullRefresh:
            self._handle_market_data_update(msg)
        elif type(msg) is MarketDataRequestReject:
            self._handle_market_data_reject(msg)

    def _handle_market_data_reject(self, msg: MarketDataRequestReject) -> None:
        reason = msg.get(58).decode()  # Text
        self._log.error(f"Market data subscription request rejected: {reason}")

    def _handle_market_data_update(self, msg: MarketDataSnapshotFullRefresh) -> None:
        if int(msg.get(268)) == 0:
            self._log.warning(
                "Market Closed. The exchange sent a empty MarketDataSnapshotFullRefresh message",
            )
            return

        instrument = self._instrument_provider.find_with_security_id(int(msg.get(48)))  # SecurityID
        self._log.info(f"Handling quote tick update: {instrument.id}")

        # Parse ts_event
        date = msg.get(272).decode()  # MDEntryDate
        time = msg.get(273).decode()  # MDEntryTime

        # Parse prices
        bid_price = float(msg.get(270, nth=1))  # MDEntryPx
        ask_price = float(msg.get(270, nth=2))  # MDEntryPx

        # Parse sizes
        bid_size = float(msg.get(271, nth=1))  # MDEntrySize
        ask_size = float(msg.get(271, nth=2))  # MDEntrySize

        # instrument_id = InstrumentId.from_str() # MDReqID
        quote_tick = QuoteTick(
            instrument_id=instrument.id,
            bid_price=Price(bid_price, instrument.price_precision),
            bid_size=Quantity(bid_size, instrument.size_precision),
            ask_price=Price(ask_price, instrument.price_precision),
            ask_size=Quantity(ask_size, instrument.size_precision),
            ts_event=parse_lmax_timestamp_ns(date + "-" + time),
            ts_init=self._clock.timestamp_ns(),
        )

        self._handle_data(quote_tick)

    async def _request_instrument(self, instrument_id: InstrumentId, correlation_id: UUID4) -> None:
        pass

    async def _request_instruments(self, venue: Venue, correlation_id: UUID4) -> None:
        pass

    async def _request_quote_ticks(
        self,
        instrument_id: InstrumentId,
        limit: int,
        correlation_id: UUID4,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> None:
        instrument = self._instrument_provider.find(instrument_id)
        if instrument is None:
            self._log.error(f"Instrument not found: {instrument_id}")
            return

        data_generator = self._get_data_generator(
            instrument_id=instrument_id,
            aggregation=BarAggregation.TICK,
            start=end if end is not None else self._clock.utc_now(),
        )

        df = await data_generator.request_dataframe(stop=start, limit=limit)

        wrangler = QuoteTickDataWrangler(instrument=instrument)

        ticks = wrangler.process(df)

        self._handle_quote_ticks(
            instrument_id=instrument_id,
            ticks=ticks,
            correlation_id=correlation_id,
        )
        return ticks

    async def _request_bars(
        self,
        bar_type: BarType,
        limit: int,
        correlation_id: UUID4,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> None:
        # if bar_type.is_internally_aggregated():
        #     self._log.error(
        #         f"Cannot request {bar_type}: "
        #         f"only historical bars with EXTERNAL aggregation available from LMAX.",
        #     )
        #     return

        if not bar_type.spec.is_time_aggregated():
            self._log.error(
                f"Cannot request {bar_type}: only time bars are aggregated by Lmax",
            )
            return

        instrument = self._instrument_provider.find(bar_type.instrument_id)
        if instrument is None:
            self._log.error(f"Instrument not found: {bar_type.instrument_id}")
            return

        # TODO: check price_type is BID or ASK
        # TODO: check aggregation is SECOND, MINUTE, or DAY

        aggregation = bar_type.spec.aggregation
        price_type = bar_type.spec.price_type

        data_generator = self._get_data_generator(
            instrument_id=bar_type.instrument_id,
            aggregation=aggregation,
            price_type=price_type,
            start=end if end is not None else self._clock.utc_now(),
        )

        # upsample quotes to SECOND bars
        if aggregation == BarAggregation.SECOND:
            processor = partial(
                self._upsample_quotes,
                freq=pd.Timedelta("1s"),
                price_type=price_type,
            )
        else:
            processor = None

        df = await data_generator.request_dataframe(stop=start, limit=limit, processor=processor)

        wrangler = BarDataWrangler(instrument=instrument, bar_type=bar_type)
        bars = wrangler.process(df)

        self._handle_bars(
            bar_type=bar_type,
            bars=bars,
            partial=bars[0],
            correlation_id=correlation_id,
        )
        return bars

    def _get_data_generator(
        self,
        instrument_id: InstrumentId,
        aggregation: BarAggregation,
        start: pd.Timestamp,
        price_type: PriceType = None,
    ) -> LmaxBarDataGenerator | LmaxQuoteTickDataGenerator:
        security_id = self._instrument_provider.get_security_id(instrument_id)

        if aggregation == BarAggregation.TICK or aggregation == BarAggregation.SECOND:
            return LmaxQuoteTickDataGenerator(
                xml_client=self._xml_client,
                security_id=security_id,
                logger=self._logger,
                start=start,
            )
        else:
            return LmaxBarDataGenerator(
                xml_client=self._xml_client,
                security_id=security_id,
                start=start,
                option=LmaxAggregateOption[price_type_to_str(price_type)],
                resolution=LmaxAggregateResolution[bar_aggregation_to_str(aggregation)],
                logger=self._logger,
            )

    @staticmethod
    def _upsample_quotes(
        df: pd.DataFrame,
        freq: pd.Timedelta,
        price_type: PriceType,
    ) -> pd.DataFrame:
        price_key = f"{price_type_to_str(price_type).lower()}_price"
        size_key = f"{price_type_to_str(price_type).lower()}_size"
        info = {price_key: "ohlc", size_key: "sum"}
        upsampled = df.groupby(pd.Grouper(freq=freq)).agg(info).dropna()
        return pd.DataFrame.from_dict(
            {
                "timestamp": upsampled.index,
                "open": upsampled[price_key]["open"],
                "high": upsampled[price_key]["high"],
                "low": upsampled[price_key]["low"],
                "close": upsampled[price_key]["close"],
            },
        ).set_index("timestamp")

    @staticmethod
    def _upsample_bars(df: pd.DataFrame, freq: pd.Timedelta) -> pd.DataFrame:
        ohlc = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }

        return df.resample(freq).apply(ohlc).dropna()

        # async def _request_dataframe(self, bar_type: BarType, limit: int, start: pd.Timestamp = None) -> pd.DataFrame:

    #     generator = self._get_data_generator(bar_type=bar_type, start=end or self._clock.utc_now())
    #     buffer = DataFrameBuffer(start=start, limit=limit)
    #     df = None
    #     for data in generator:

    #         if aggregation == BarAggregation.SECOND:
    #             data = self._upsample_quotes(df=data, freq=pd.Timedelta("1s"), price_type=price_type)
    #         elif aggregation != BarAggregation.MINUTE and aggregation != BarAggregation.DAY:
    #             data = self._upsample_bars(df=data, freq=pd.Timedelta("1s"))

    #         buffer.prepend(data)

    #         if buffer.is_full():
    #             df = buffer.get_result()

    # df = await data_gen.process_until(stop=start, limit=limit)

    # await self._process_bar_generator(
    #         bar_type=bar_type,
    #         limit=limit,
    #         correlation_id=correlation_id,
    #         data_gen=LmaxBarDataGenerator(
    #                     xml_client=self._xml_client,
    #                     security_id=security_id,
    #                     start=end or self._clock.utc_now(),
    #                     option=option,
    #                     resolution=resolution,
    #                     logger=self._logger,
    #         ),
    #         stop=start,
    # )

    # async def _process_bar_generator(
    #             self,
    #             bar_type: BarType,
    #             limit: int,
    #             correlation_id: UUID4,
    #             data_gen: LmaxBarDataGenerator,
    #             stop: pd.Timestamp = None,
    #             ) -> pd.DataFrame:

    #     df = await data_gen.process_until(stop=stop, limit=limit)

    #     if df.empty:
    #         return []

    # async def _iterate_data(self,
    #             provider: LMAXDataProvider,
    #             limit: int,
    #             start: pd.Timestamp,
    #             stop: pd.Timestamp | None,
    #             window_size: pd.Timedelta,
    #             ) -> list[DataType]:

    #     if stop is not None:
    #         stop_ns = dt_to_unix_nanos(stop)

    #     end = start + window_size
    #     data = []
    #     while True:
    #         self._log.info(f"Requesting {start} > {end}")
    #         items = await provider.request_objects(start=start, end=end)

    #         self._log.info(f"Data items downloaded = {len(items)}")
    #         if len(items) > 0:

    #             data.extend(items)

    #             if stop is not None and data[0].ts_init <= stop_ns:
    #                 data = [x for x in data if x.ts_init >= stop_ns]
    #                 break
    #             if len(data) >= limit:
    #                 break

    #             print(len(data))

    #         start -= window_size
    #         end -= window_size

    #     if len(data) > limit:
    #         data = data[len(data) - limit:]


#         return data


# if __name__ == "__main__":
#

#     async def main_():
#         data_client = LMAXMocks.data_client()
#         instrument = LMAXMocks.btc_usd_instrument()
#         data_client.instrument_provider.add(instrument)

#         await data_client._connect()
#         await data_client._subscribe_quote_ticks(instrument.id)

#         # while True:
#         #     await asyncio.sleep(1)

#     asyncio.run(main_())

# await data_client._client.listen()
# while True:
#     await asyncio.sleep(1)

# await data_client._subscribe_quote_ticks()

# try:
#     asyncio.get_event_loop().run_forever()
# except KeyboardInterrupt:
#     thread.join()  # Wait for the thread to finish gracefully

# # Create a new thread and start the listen method in that thread

# You can continue with other tasks or wait for the thread to finish if needed
# For example, you can call the asyncio event loop's run_forever() to keep the program running:
# try:
#     asyncio.get_event_loop().run_forever()
# except KeyboardInterrupt:
#     print("Program terminated.")
#     server.disconnect()
#     thread.join()  # Wait for the thread to finish gracefully

# await client.connect()
# await client.logon()
# await client.listen()

# async def _unsubscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
#     self._fix_client.session.MarketDataChanged

# async def _subscribe_order_book_deltas(
#     self,
#     instrument_id: InstrumentId,
#     book_type: BookType,
#     depth: Optional[int] = None,
#     kwargs: dict = None,
# ) -> None:

#     # session.Start() # starts the connection to the asynchronous event stream
# how to only subscribe to L3
#     raise NotImplementedError("method must be implemented in the subclass")  # pragma: no cover

# async def _subscribe_order_book_snapshots(
#     self,
#     instrument_id: InstrumentId,
#     book_type: BookType,
#     depth: Optional[int] = None,
#     kwargs: dict = None,
# ) -> None:
#     raise NotImplementedError("method must be implemented in the subclass")  # pragma: no cover

# async def _unsubscribe_quote_ticks(self, instrument_id: InstrumentId) -> None:
#     raise NotImplementedError("method must be implemented in the subclass")  # pragma: no cover

# def _on_order_book_to_quote_tick(self, event: OrderBookEvent, instrument_id: InstrumentId):
#     """
#     LMAX has no functionality to subscribe to QuoteTicks directly.
#     Instead, we subscribe to OrderBook and convert the events to QuoteTicks.
#     """
#     quote_tick = lmax_order_book_event_to_nautilus_quote_tick(event=event, instrument_id=instrument_id)
#     print(quote_tick)
#     self._handle_data(quote_tick)

# self._fix_client.start()
# self.create_task(self._fix_client.listen())

# async def _run():
#     while True:
#         self._fix_client._initiator.poll()
#         await asyncio.sleep(1)

# self._fix_client._initiator.start()
# self.create_task(_run())
# import time
# wait for session to be activate
# async def _wait():
# while self._fix_client._session is None:
#     self._log.info("Waiting...")
# await asyncio.sleep(1)
# time.sleep(1)
# session = fix.Session.lookupSession(self._fix_client._sessionID)

# self._log.info(f"Session {session}")
# self._log.info("Session activated")

#     await self._process_quote_tick_generator(
#             instrument_id=instrument_id,
#             limit=limit,
#             correlation_id=correlation_id,
#             data_gen=LmaxQuoteTickDataGenerator(
#                 xml_client=self._xml_client,
#                 security_id=security_id,
#                 logger=self._logger,
#                 start=end or self._clock.utc_now(),
#             ),
#             stop=start,
#     )

# async def _process_quote_tick_generator(
#             self,
#             instrument_id: InstrumentId,
#             limit: int,
#             correlation_id: UUID4,
#             data_gen: LmaxBarDataGenerator,
#             stop: pd.Timestamp = None,
#             ) -> pd.DataFrame:
