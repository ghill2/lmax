import gzip
from collections.abc import Callable
from copy import copy
from io import BytesIO
from io import StringIO
from xml.etree import ElementTree

import pandas as pd

from nautilus_trader.common.component import Logger
from nautilus_trader.common.component import LoggerAdapter
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.core.datetime import nanos_to_millis
from pytower.adapters.lmax.xml.client import LmaxXmlClient
from pytower.adapters.lmax.xml.enums import LmaxAggregateOption
from pytower.adapters.lmax.xml.enums import LmaxAggregateResolution
from pytower.adapters.lmax.xml.util import unpretty_xml


class DataFrameBuffer:
    def __init__(self, limit: int, start: pd.Timestamp = None):
        self._buf = pd.DataFrame()
        self._limit = limit
        self._start = start

    async def prepend(self, df: pd.DataFrame) -> pd.DataFrame:
        self._buf = pd.concat([df, self._buf])
        self._log.debug(f"Total items: {len(self._buf)}...")

    def is_full(self) -> bool:
        return (self._start is not None or self._buf.index[0] <= self._start) or len(
            self._buf,
        ) >= self._limit

    def get_result(self):
        if self._start is not None:
            self._buf = self._buf[self._buf.index >= self._start]
        return self._buf.iloc[-self._limit :]


class LmaxDataGenerator:
    def __init__(
        self,
        xml_client: LmaxXmlClient,
        logger: Logger,
        start: pd.Timestamp,
        processor: Callable | None = None,
    ):
        self._xml_client = xml_client
        self._log = LoggerAdapter(type(self).__name__, logger)
        self._start = start
        self._processor = processor

    async def _request_urls(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> list[str]:
        raise NotImplementedError("method must be implemented in the subclass")  # pragma: no cover

    async def request_dataframe(
        self,
        limit: int,
        stop: pd.Timestamp,
        processor: Callable | None = None,
    ) -> pd.DataFrame:
        total = pd.DataFrame()
        async with self._xml_client.stream_lock:
            async for df in self:
                if processor is not None:
                    df = processor(df)

                total = pd.concat([df, total])

                self._log.debug(f"Read items: {len(df)}, Total items: {len(total)}...")

                if stop is not None and total.index[0] <= stop:
                    return total[total.index >= stop].iloc[-limit:]
                if len(total) >= limit:
                    return total.iloc[-limit:]

    async def __aiter__(self):
        async for csv_data in self._iterate_csv_data():
            df = pd.read_csv(StringIO(csv_data))

            df = self._process_dataframe(df)

            df = df[df.index <= self._start]

            if df.empty:
                continue

            self._log.debug(f"Read items: {len(df)}")

            yield df

    async def _iterate_csv_data(self):
        end = copy(self._start)
        start = copy(self._start) - pd.Timedelta(days=1)

        history = set()

        while True:
            urls = await self._request_urls(start=start, end=end)

            if len(urls) == 0:
                # TODO: catch NoDataException
                start -= pd.Timedelta(days=1)
                end -= pd.Timedelta(days=1)
                continue

            for url in urls[::-1]:
                if url in history:
                    continue
                self._log.debug(f"Reading url: {url}")
                csv_data = await self._read_url(url=url)
                yield csv_data
                history.add(url)

            # marketdata/aggregate/4001/2023/09/2023-09-07-21-00-00-000-4001-bid-minute-aggregation.csv.gz
            base = urls[0].split("/")[-1]
            end = pd.to_datetime(
                "-".join(base.split("-")[:7]),
                format="%Y-%m-%d-%H-%M-%S-%f",
            )
            start = end - pd.Timedelta(days=1)

    async def _fetch_urls(self, body: str) -> list[str]:
        await self._xml_client.logout()
        await self._xml_client.login()
        await self._xml_client.subscribe("historicMarketData")
        url = "/secure/read/marketData/requestHistoricMarketData"

        await self._xml_client.post(url=url, data=body)
        # returns: <res><header><status>OK</status></header><body/></res>

        # will stall if urls have already been sent
        xml_data = await self._xml_client.parse_stream(target_element="historicMarketData")

        root = ElementTree.fromstring(xml_data)
        if root.find("noMatchingData") is not None:
            return []

        urls = [elem.text for elem in root.findall(".//url")]

        return sorted(urls)

    async def _read_url(self, url: str) -> str:
        """
        NOTE: The JSESSIONID cookie needs to be the same as when the urls were requested
        """
        url = "/marketdata/" + url.split("/marketdata/")[1]
        assert self._xml_client.is_connected
        await self._xml_client.login()
        # resp = await self.get(url=url)
        async with self._xml_client._session.request(
            method="GET",
            url=url,
        ) as resp:
            with gzip.GzipFile(fileobj=BytesIO(await resp.read()), mode="rb") as f:
                return f.read().decode()


class LmaxBarDataGenerator(LmaxDataGenerator):
    def __init__(
        self,
        xml_client: LmaxXmlClient,
        security_id: int,
        start: pd.Timestamp,
        option: LmaxAggregateOption,
        resolution: LmaxAggregateResolution,
        logger: Logger,
    ):
        super().__init__(xml_client=xml_client, logger=logger, start=start)
        self._security_id = security_id
        self._option = option
        self._resolution = resolution

    async def _request_urls(self, start: pd.Timestamp, end: pd.Timestamp) -> list[str]:
        self._log.info(
            f"Requesting aggregate urls for: "
            f"security_id: {self._security_id} resolution: {self._resolution} "
            f"option: {self._option} start: {start} end: {end}",
        )

        start_ms = nanos_to_millis(dt_to_unix_nanos(start))
        end_ms = nanos_to_millis(dt_to_unix_nanos(end))

        body = f"""
            <req>
                <body>
                    <instructionId>1</instructionId>
                    <orderBookId>{self._security_id}</orderBookId>
                    <from>{start_ms}</from>
                    <to>{end_ms}</to>
                    <aggregate>
                    <options>
                        <option>{self._option.value}</option>
                    </options>
                    <resolution>{self._resolution.value}</resolution>
                    <depth>1</depth>
                    <format>CSV</format>
                    </aggregate>
                </body>
            </req>
        """
        body = unpretty_xml(body)

        urls = await self._fetch_urls(body=body)

        return urls

    @staticmethod
    def _process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        INTERVAL_START_TIMESTAMP,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,UP_VOLUME,D
        OWN_VOLUME,UNCHANGED_VOLUME,UP_TICKS,DOWN_TICKS,UNCHANGED_TICKS 1609538700000,29
        271.91,33316.97,29037.85,31672.6,26914.65,22889.59,816.09,5462,4656,188.
        """
        df = df.dropna()
        if df.empty:
            return pd.DataFrame()

        df = df.rename(
            columns={
                "INTERVAL_START_TIMESTAMP": "timestamp",
                "OPEN_PRICE": "open",
                "HIGH_PRICE": "high",
                "LOW_PRICE": "low",
                "CLOSE_PRICE": "close",
            },
        )

        df["volume"] = df["UP_VOLUME"] + df["DOWN_VOLUME"] + df["UNCHANGED_VOLUME"]

        keep = ["timestamp", "open", "high", "low", "close", "volume"]

        df = df.filter(items=keep)[keep]

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        df = df.set_index("timestamp")

        return df


class LmaxQuoteTickDataGenerator(LmaxDataGenerator):
    def __init__(
        self,
        xml_client: LmaxXmlClient,
        security_id: int,
        start: pd.Timestamp,
        logger: Logger,
    ):
        super().__init__(xml_client=xml_client, logger=logger, start=start)
        self._security_id = security_id

    @staticmethod
    def _process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna()

        if df.empty:
            return pd.DataFrame()

        df = df.rename(
            columns={
                "TIMESTAMP": "timestamp",
                "BID_PRICE_1": "bid_price",
                "BID_QTY_1": "bid_size",
                "ASK_PRICE_1": "ask_price",
                "ASK_QTY_1": "ask_size",
            },
        )

        keep = ["timestamp", "bid_price", "ask_price", "bid_size", "ask_size"]
        df = df.filter(items=keep)[keep]

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

        df = df.set_index("timestamp")

        return df

    async def _request_urls(self, start: pd.Timestamp, end: pd.Timestamp) -> list[str]:
        self._log.info(
            f"Requesting top of book urls for {self._security_id} from {start} to {end}",
        )

        start_ms = nanos_to_millis(dt_to_unix_nanos(start))
        end_ms = nanos_to_millis(dt_to_unix_nanos(end))

        body = f"""
            <req>
                <body>
                    <instructionId>1</instructionId>
                    <orderBookId>{self._security_id}</orderBookId>
                    <from>{start_ms}</from>
                    <to>{end_ms}</to>
                    <orderBook>
                    <options>
                        <option>BID</option>
                        <option>ASK</option>
                    </options>
                    <depth>1</depth>
                    <format>CSV</format>
                    </orderBook>
                </body>
            </req>
            """
        body = unpretty_xml(body)

        urls = await self._fetch_urls(body=body)

        return urls


####################################################################################################
# class LmaxDataProvider:

#     _instruction_id = 0

#     def __init__(self,
#                 xml_client: LmaxXmlClient,
#                 instrument_provider: LmaxInstrumentProvider,
#                 logger: Logger,
#                 ):

#         self._xml_client = xml_client
#         # self._security_id = instrument.info["id"]
#         self._log = LoggerAdapter(type(self).__name__, logger)
#         self._instrument_provider = instrument_provider

#     # @staticmethod
# def _process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
#     raise NotImplementedError("method must be implemented in the subclass")  # pragma: no cover


# class LmaxBarProvider(LmaxDataProvider):
#     def __init__(self,
#                 client: LmaxXmlClient,
#                 instrument_provider: LmaxInstrumentProvider,
#                 logger: Logger,
#                 ):

#         super().__init__(xml_client=client,
#                          instrument_provider=instrument_provider,
#                          logger=logger
#                          )

#     @property
#     def data_generator(self) -> LmaxBarDataGenerator:
#         return self._data_generator

#     async def request_objects(self,
#                             bar_type: BarType,
#                             limit: int,
#                             end: pd.Timestamp,
#                             start: pd.Timestamp | None = None,
#                             ) -> list[Bar]:


####################################################################################################

# if self._aggregation == BarAggregation.MINUTE and self._step == 1 \
#     or self._aggregation == BarAggregation.DAY and self._step == 1:
#     return df
# else:
#     return self._upsample_bars(df=df, spec=self._bar_type.spec)

# async def instrument(self) -> Instrument:
#     instrument_id = InstrumentId(symbol=self._symbol, venue=LMAX_VENUE)
#     return await self._xml_client.request_instrument(instrument_id=instrument_id)


# async def request_objects_count(self, start: pd.Timestamp, count: int) -> list[QuoteTick | Bar]:
#     df = await self.request_dataframe(start=start, count=count)
#     if df.empty:
#         return []
#     return await self._to_objects(df)


# async def request_dataframe(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
#     async for df in self._bfill_dataframe(start=end):
#         if df.index[0] < start:
#             return df[start:]

# async def request_dataframe_count(self, start: pd.Timestamp, count: int) -> pd.DataFrame:
#     async for df in self._bfill_dataframe(start=start):
#         if len(df) >= count:
#             return df.iloc[:count]
