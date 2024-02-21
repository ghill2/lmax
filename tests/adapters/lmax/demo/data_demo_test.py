import asyncio
import sys
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pandas as pd
import pytest

from nautilus_trader.core.datetime import unix_nanos_to_dt
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from pytower.adapters.lmax.fix.messages import MarketDataRequestReject
from pytower.adapters.lmax.fix.messages import MarketDataSnapshotFullRefresh


class TestLMAXLiveDataClient:
    @pytest.mark.asyncio
    async def test_subscribe_quote_ticks(self, data_client):
        # Arrange & Act
        instrument = data_client.cache.instruments()[0]
        data_client.subscribe_quote_ticks(instrument_id=instrument.id)
        await data_client.fix_client.wait_for_event(cls=MarketDataSnapshotFullRefresh)

        # Assert
        assert data_client.cache.quote_tick(instrument_id=instrument.id) is not None

    @pytest.mark.asyncio
    async def test_unsubscribe_quote_ticks(self, data_client):
        # Arrange
        data_client._handle_reject = AsyncMock()
        instrument = data_client.cache.instruments()[0]

        # Act
        data_client.unsubscribe_quote_ticks(instrument_id=instrument.id)
        await asyncio.sleep(0.25)  # nothing returned on unsubscribe
        data_client.subscribe_quote_ticks(instrument_id=instrument.id)
        await data_client.fix_client.wait_for_event(cls=MarketDataSnapshotFullRefresh)
        data_client.unsubscribe_quote_ticks(instrument_id=instrument.id)
        await asyncio.sleep(0.25)  # nothing returned on unsubscribe

        # Assert
        data_client._handle_reject.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscribe_handle_reject(self, data_client):
        # Arrange
        instrument = data_client.cache.instruments()[0]
        data_client._handle_reject = AsyncMock()

        # Act
        data_client.unsubscribe_quote_ticks(instrument_id=instrument.id)
        await asyncio.sleep(0.25)  # nothing returned on unsubscribe
        data_client.subscribe_quote_ticks(instrument_id=instrument.id)
        await data_client.fix_client.wait_for_event(cls=MarketDataSnapshotFullRefresh)
        data_client.subscribe_quote_ticks(instrument_id=instrument.id)
        await data_client.fix_client.wait_for_event(cls=MarketDataRequestReject)

        # Assert
        data_client._handle_reject.assert_called_once()


class TestLMAXLiveDataClientHistoric:
    @pytest.mark.asyncio
    async def test_request_bars_with_limit_only(self, data_client):
        data_client._handle_bars = Mock()
        end = pd.Timestamp("2023-01-03 23-00-00", tz="UTC")
        await data_client._request_bars(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            limit=100,
            correlation_id=UUID4(),
            end=end,
        )

        bars = data_client._handle_bars.call_args.kwargs["bars"]
        assert len(bars) == 100
        assert unix_nanos_to_dt(bars[0].ts_init) == pd.Timestamp(
            "2023-01-03 21:16:00+00:00",
            tz="UTC",
        )
        assert unix_nanos_to_dt(bars[-1].ts_init) == end
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing

    @pytest.mark.asyncio
    async def test_request_bars_with_start_only(self, data_client):
        data_client._handle_bars = Mock()
        import sys

        start = pd.Timestamp("2023-01-03 21-00-00", tz="UTC")
        end = pd.Timestamp("2023-01-03 23-00-00", tz="UTC")
        await data_client._request_bars(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            limit=sys.maxsize,
            correlation_id=UUID4(),
            start=start,
            end=end,
        )

        bars = data_client._handle_bars.call_args.kwargs["bars"]
        assert len(bars) == 116
        assert unix_nanos_to_dt(bars[0].ts_init) == start
        assert unix_nanos_to_dt(bars[-1].ts_init) == end
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing

    @pytest.mark.asyncio
    async def test_request_bars_limit_lower_than_start(self, data_client):
        data_client._handle_bars = Mock()
        start = pd.Timestamp("2023-01-03 21-00-00", tz="UTC")
        end = pd.Timestamp("2023-01-03 23-00-00", tz="UTC")
        await data_client._request_bars(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            limit=100,
            correlation_id=UUID4(),
            start=start,
            end=end,
        )

        bars = data_client._handle_bars.call_args.kwargs["bars"]
        assert len(bars) == 100
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing
        assert unix_nanos_to_dt(bars[0].ts_init) == pd.Timestamp(
            "2023-01-03 21:16:00+00:00",
            tz="UTC",
        )
        assert unix_nanos_to_dt(bars[-1].ts_init) == end

    @pytest.mark.asyncio
    async def test_request_bars_with_start_and_limit_higher_than_start(self, data_client):
        data_client._handle_bars = Mock()
        start = pd.Timestamp("2023-01-03 21-00-00", tz="UTC")
        end = pd.Timestamp("2023-01-03 23-00-00", tz="UTC")
        await data_client._request_bars(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            limit=200,
            correlation_id=UUID4(),
            start=start,
            end=end,
        )

        bars = data_client._handle_bars.call_args.kwargs["bars"]
        assert len(bars) == 116
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing
        assert unix_nanos_to_dt(bars[0].ts_init) == start
        assert unix_nanos_to_dt(bars[-1].ts_init) == end

    @pytest.mark.asyncio
    async def test_request_quote_ticks_with_limit_only(self, data_client):
        data_client._handle_quote_ticks = Mock()
        limit = 20
        end = pd.Timestamp("2023-01-05", tz="UTC")
        await data_client._request_quote_ticks(
            instrument_id=InstrumentId.from_str("EUR/USD.LMAX"),
            limit=limit,
            correlation_id=UUID4(),
            end=end,
        )
        quotes = data_client._handle_quote_ticks.call_args.kwargs["ticks"]
        assert len(quotes) == limit
        assert pd.Series([x.ts_init for x in quotes]).is_monotonic_increasing
        assert unix_nanos_to_dt(quotes[0].ts_init) == pd.Timestamp(
            "2023-01-04 23:59:01.642000+00:00",
            tz="UTC",
        )
        assert unix_nanos_to_dt(quotes[-1].ts_init) == pd.Timestamp(
            "2023-01-04 23:59:58.958000+00:00",
            tz="UTC",
        )

    @pytest.mark.asyncio
    async def test_request_quote_ticks_with_start_only(self, data_client):
        data_client._handle_quote_ticks = Mock()

        start = pd.Timestamp("2023-01-04", tz="UTC")
        end = pd.Timestamp("2023-01-05", tz="UTC")

        await data_client._request_quote_ticks(
            instrument_id=InstrumentId.from_str("EUR/USD.LMAX"),
            limit=sys.maxsize,
            correlation_id=UUID4(),
            start=start,
            end=end,
        )

        quotes = data_client._handle_quote_ticks.call_args.kwargs["ticks"]
        assert len(quotes) == 55409
        assert pd.Series([x.ts_init for x in quotes]).is_monotonic_increasing
        assert unix_nanos_to_dt(quotes[0].ts_init) == pd.Timestamp(
            "2023-01-04 00:00:00.691000+00:00",
            tz="UTC",
        )
        assert unix_nanos_to_dt(quotes[-1].ts_init) == pd.Timestamp(
            "2023-01-04 23:59:58.958000+00:00",
            tz="UTC",
        )

    @pytest.mark.asyncio
    async def test_request_quote_ticks_limit_lower_than_start(self, data_client):
        data_client._handle_quote_ticks = Mock()

        start = pd.Timestamp("2023-01-04", tz="UTC")
        end = pd.Timestamp("2023-01-05", tz="UTC")
        limit = 20
        await data_client._request_quote_ticks(
            instrument_id=InstrumentId.from_str("EUR/USD.LMAX"),
            limit=limit,
            correlation_id=UUID4(),
            start=start,
            end=end,
        )

        quotes = data_client._handle_quote_ticks.call_args.kwargs["ticks"]
        assert len(quotes) == limit
        assert pd.Series([x.ts_init for x in quotes]).is_monotonic_increasing
        assert unix_nanos_to_dt(quotes[0].ts_init) == pd.Timestamp(
            "2023-01-04 23:59:01.642000+00:00",
            tz="UTC",
        )
        assert unix_nanos_to_dt(quotes[-1].ts_init) == pd.Timestamp(
            "2023-01-04 23:59:58.958000+00:00",
            tz="UTC",
        )

    @pytest.mark.asyncio
    async def test_request_quote_ticks_limit_higher_than_start(self, data_client):
        data_client._handle_quote_ticks = Mock()

        start = pd.Timestamp("2023-01-04", tz="UTC")
        end = pd.Timestamp("2023-01-05", tz="UTC")
        await data_client._request_quote_ticks(
            instrument_id=InstrumentId.from_str("EUR/USD.LMAX"),
            limit=55500,
            correlation_id=UUID4(),
            start=start,
            end=end,
        )

        quotes = data_client._handle_quote_ticks.call_args.kwargs["ticks"]
        assert len(quotes) == 55409
        assert pd.Series([x.ts_init for x in quotes]).is_monotonic_increasing
        assert unix_nanos_to_dt(quotes[0].ts_init) == pd.Timestamp(
            "2023-01-04 00:00:00.691000+0000",
            tz="UTC",
        )
        assert unix_nanos_to_dt(quotes[-1].ts_init) == pd.Timestamp(
            "2023-01-04 23:59:58.958000+00:00",
            tz="UTC",
        )

    # @pytest.mark.asyncio
    # async def test_request_bars_with_upsample(self, data_client):
    #     data_client._handle_bars = Mock()
    #     import sys

    #     start = pd.Timestamp("2023-01-03 21-00-00", tz="UTC")
    #     end = pd.Timestamp("2023-01-03 22-00-00", tz="UTC")
    #     await data_client._request_bars(
    #         bar_type=BarType.from_str("EUR/USD.LMAX-4-MINUTE-BID-EXTERNAL"),
    #         limit=sys.maxsize,
    #         correlation_id=UUID4(),
    #         start=start,
    #         end=end,
    #     )

    #     bars = data_client._handle_bars.call_args.kwargs["bars"]
    #     assert len(bars) == 15
    #     assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing
    #     timestamps = pd.Series([unix_nanos_to_dt(x.ts_init) for x in bars])
    #     assert all(timestamps.diff()[1:] == pd.Timedelta(minutes=4))
    #     assert unix_nanos_to_dt(bars[0].ts_init) == start
    #     assert unix_nanos_to_dt(bars[-1].ts_init) == pd.Timestamp(
    #         "2023-01-03 21:56:00+0000",
    #         tz="UTC",
    #     )
    #     # minimum day 30 minutes
    #     # 6 minutes = couple of hours
