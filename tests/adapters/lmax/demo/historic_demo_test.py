import asyncio

import pandas as pd
import pytest
from dotenv import dotenv_values

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import Symbol
from pytower.adapters.lmax.xml.client import LmaxXmlClient
from pytower.adapters.lmax.xml.historic import LmaxBarProvider
from pytower.adapters.lmax.xml.historic import LMAXQuoteTickProvider


class TestLMAXBarProvider:
    def setup(self):
        loop = asyncio.get_event_loop()
        clock = LiveClock(loop=loop)
        secrets = dotenv_values()
        self.logger = Logger(clock=clock)
        cache = Cache(logger=self.logger)

        self.xml_client = LmaxXmlClient(
            hostname="https://web-order.london-demo.lmax.com",
            username=secrets["username"],
            password=secrets["password"],
            clock=clock,
            cache=cache,
            logger=self.logger,
            loop=loop,
        )
        loop.run_until_complete(self.xml_client.connect())

        self.provider = LmaxBarProvider(
            client=self.xml_client,
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            logger=self.logger,
        )

    @pytest.mark.asyncio()
    async def test_request_dataframe_no_data(self):
        start = pd.Timestamp("2010-09-12 10:52:00", tz="UTC")
        end = pd.Timestamp("2010-09-12 10:53:00", tz="UTC")
        df = await self.provider.request_dataframe(start=start, end=end, limit=1)
        assert df.empty

    @pytest.mark.asyncio()
    async def test_request_objects_no_data(self):
        start = pd.Timestamp("2010-09-12 10:52:00", tz="UTC")
        end = pd.Timestamp("2010-09-12 10:53:00", tz="UTC")
        bars = await self.provider.request_objects(start=start, end=end)
        assert bars == []

    @pytest.mark.asyncio()
    async def test_request_dataframe(self):
        # Act
        start = pd.Timestamp("2023-09-08", tz="UTC")
        end = pd.Timestamp("2023-09-09", tz="UTC")
        df = await self.provider.request_dataframe(start=start, end=end, limit=2)

        assert len(df) == 1260
        assert type(df.index) is pd.DatetimeIndex
        assert str(df.index.tz) == "UTC"
        assert df.index.is_monotonic_increasing
        assert (df[df.index >= start & df.index < end]).all()
        assert list(df.reset_index().columns) == [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

    @pytest.mark.asyncio()
    async def test_request_objects(self):
        # Act
        start = pd.Timestamp("2023-09-08", tz="UTC")
        end = pd.Timestamp("2023-09-09", tz="UTC")
        bars = await self.provider.request_objects(start=start, end=end)

        assert len(bars) == 1260
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing

    @pytest.mark.asyncio()
    async def test_request_dataframe_count(self):
        start = pd.Timestamp("2023-09-08", tz="UTC")
        count = 1_000
        df = await self.provider.request_dataframe_count(start=start, count=count)
        await asyncio.sleep(5)
        assert len(df) == count
        assert type(df.index) is pd.DatetimeIndex
        assert str(df.index.tz) == "UTC"
        assert df.index.is_monotonic_increasing
        assert df.index[-1] < start
        assert list(df.reset_index().columns) == [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]


class TestLMAXQuoteTickProvider:
    def setup(self):
        loop = asyncio.get_event_loop()
        clock = LiveClock(loop=loop)
        secrets = dotenv_values()
        self.logger = Logger(clock=clock)
        cache = Cache(logger=self.logger)

        self.xml_client = LmaxXmlClient(
            hostname="https://web-order.london-demo.lmax.com",
            username=secrets["username"],
            password=secrets["password"],
            clock=clock,
            cache=cache,
            logger=self.logger,
            loop=loop,
        )
        loop.run_until_complete(self.xml_client.connect())
        self.provider = LMAXQuoteTickProvider(
            xml_client=self.xml_client,
            symbol=Symbol("EUR/USD"),
            logger=self.logger,
        )

    @pytest.mark.asyncio()
    async def test_request_dataframe_no_data(self):
        start = (pd.Timestamp("2010-09-12 10:52:00", tz="UTC"),)
        end = (pd.Timestamp("2010-09-12 10:53:00", tz="UTC"),)

        await self.xml_client.connect()
        df = await self.provider.request_dataframe(start=start, end=end)
        assert df.empty

    @pytest.mark.asyncio()
    async def test_request_objects_no_data(self):
        start = pd.Timestamp("2010-09-12 10:52:00", tz="UTC")
        end = pd.Timestamp("2010-09-12 10:53:00", tz="UTC")

        await self.xml_client.connect()
        bars = await self.provider.request_objects(start=start, end=end)
        assert bars == []

    @pytest.mark.asyncio()
    async def test_request_dataframe(self):
        # Act
        start = pd.Timestamp("2023-09-08", tz="UTC")
        end = pd.Timestamp("2023-09-09", tz="UTC")

        await self.xml_client.connect()
        df = await self.provider.request_dataframe(start=start, end=end)

        assert len(df) == 39516
        assert type(df.index) is pd.DatetimeIndex
        assert str(df.index.tz) == "UTC"
        assert df.index.is_monotonic_increasing
        assert df.index[0] >= start
        assert df.index[-1] < end
        assert list(df.reset_index().columns) == [
            "timestamp",
            "bid_price",
            "ask_price",
            "bid_size",
            "ask_size",
        ]

    @pytest.mark.asyncio()
    async def test_request_objects(self):
        # Act
        start = pd.Timestamp("2023-09-08", tz="UTC")
        end = pd.Timestamp("2023-09-09", tz="UTC")

        await self.xml_client.connect()
        quotes = await self.provider.request_objects(start=start, end=end)

        assert len(quotes) == 39516
        assert pd.Series([x.ts_init for x in quotes]).is_monotonic_increasing

    @pytest.mark.asyncio()
    async def test_request_dataframe_count(self):
        start = pd.Timestamp("2023-09-08", tz="UTC")
        count = 50_000
        df = await self.provider.request_dataframe_count(start=start, count=count)
        await asyncio.sleep(5)
        assert len(df) == count
        assert type(df.index) is pd.DatetimeIndex
        assert str(df.index.tz) == "UTC"
        assert df.index.is_monotonic_increasing
        assert df.index[-1] < start
        assert list(df.reset_index().columns) == [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]


#         # Act
#         provider = LMAXQuoteTickDataProvider(
#                             client=LMAXMocks.xml_client(),
#                             symbol=Symbol("XBT/USD"),  # 100934
#                             start=pd.Timestamp("2021-01-04 13:00:00"),
#                             end=pd.Timestamp("2021-01-04 15:00:00"),
#                             )
#         quotes = provider.request_objects()

#         assert len(quotes) == 16742
#         assert pd.Series([x.ts_init for x in quotes]).is_monotonic_increasing
