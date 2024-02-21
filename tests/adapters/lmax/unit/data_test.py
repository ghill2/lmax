import sys
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pandas as pd
import pytest

from nautilus_trader.core.datetime import unix_nanos_to_dt
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from pytower.adapters.lmax.fix.messages import string_to_message
from pytower.tests.adapters.lmax import FIX_RESPONSES
from pytower.tests.adapters.lmax.mocks import LmaxMocks


class TestLMAXLiveDataClient:
    @pytest.mark.asyncio
    async def test_connect(self):
        # TODO: mock Logon response
        pass

    @pytest.mark.asyncio
    async def test_handle_market_data_snapshot_full_refresh(self, data_client):
        # Arrange
        data_client._handle_data = Mock()

        with open(FIX_RESPONSES / "market_data_snapshot_full_refresh.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        # Act
        await data_client.handle_message(msg)

        # Assert
        quote_tick = data_client._handle_data.call_args[0][0]
        assert str(quote_tick) == "XBT/USD.LMAX,29384.72,29389.00,4.97,4.95,1690801479440000000"

    @pytest.mark.asyncio
    async def test_handle_market_data_snapshot_full_refresh_with_no_data(self, data_client):
        # Arrange
        data_client._handle_data = Mock()

        with open(FIX_RESPONSES / "market_data_snapshot_full_refresh_no_data.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())

        # Act
        await data_client.handle_message(msg)

        # Assert
        assert data_client._handle_data.call_count == 0

    @pytest.mark.asyncio
    async def test_subscribe_quote_ticks_returns_when_instrument_none(self, data_client):
        data_client.fix_client.send_message = AsyncMock()

        await data_client._subscribe_quote_ticks(
            instrument_id=InstrumentId.from_str("UN/KNOWN.LMAX"),
        )

        assert data_client.fix_client.send_message.call_count == 0

    @pytest.mark.asyncio
    async def test_subscribe_quote_ticks_sends_expected(self, data_client):
        # Arrange
        data_client.fix_client.send_message = AsyncMock()

        # Act
        await data_client._subscribe_quote_ticks(
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
        )

        # Assert
        msg = data_client.fix_client.send_message.call_args[0][0]
        assert msg.get(262) == b"QuoteTick-XBT/USD.LMAX"  # MDReqID
        assert msg.get(263) == b"1"  # SubscriptionRequestType: Snapshot + Updates (Subscribe)
        assert msg.get(264) == b"1"  # MarketDepth: 1 = Top of Book
        assert msg.get(267) == b"2"  # NoMDEntryTypes
        assert msg.get(269, nth=1) == b"0"  # MDEntryType: Bid
        assert msg.get(269, nth=2) == b"1"  # MDEntryType: Ask
        assert msg.get(146) == b"1"  # NoRelatedSym
        assert msg.get(48) == b"100934"  # SecurityID
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)
        assert len(msg.pairs) == 9

    @pytest.mark.asyncio
    async def test_unsubscribe_quote_ticks_sends_expected(self, data_client):
        # Arrange
        data_client.fix_client.send_message = AsyncMock()

        # Act
        await data_client._unsubscribe_quote_ticks(
            instrument_id=InstrumentId.from_str("XBT/USD.LMAX"),
        )

        # Assert
        msg = data_client.fix_client.send_message.call_args[0][0]
        assert msg.get(262) == b"QuoteTick-XBT/USD.LMAX"  # MDReqID
        assert (
            msg.get(263) == b"2"
        )  # SubscriptionRequestType: Disable previous Snapshot + Updates Request (Unsubscribe)
        assert msg.get(264) == b"1"  # MarketDepth: 1 = Top of Book
        assert msg.get(267) == b"2"  # NoMDEntryTypes
        assert msg.get(269, nth=1) == b"0"  # MDEntryType: Bid
        assert msg.get(269, nth=2) == b"1"  # MDEntryType: Ask
        assert msg.get(146) == b"1"  # NoRelatedSym
        assert msg.get(48) == b"100934"  # SecurityID
        assert msg.get(22) == b"8"  # SecurityIDSource: Must contain the value '8' (Exchange Symbol)
        assert len(msg.pairs) == 9

    @pytest.mark.asyncio
    async def test_handle_reject(self, data_client):
        with open(FIX_RESPONSES / "market_data_request_reject.txt") as f:
            msg: ExecutionReport = string_to_message(f.readline())
        data_client._handle_market_data_reject = Mock()

        # Act
        await data_client.handle_message(msg)
        assert data_client._handle_market_data_reject.call_count == 1

    @pytest.mark.asyncio
    async def test_request_second_bars_with_limit_only(self, data_client):
        data_client._handle_bars = Mock()

        data_gen = LmaxMocks().quotes_data_gen(xml_client=data_client.xml_client)
        data_client._get_data_generator = Mock(return_value=data_gen)

        await data_client._request_bars(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-SECOND-BID-EXTERNAL"),
            limit=100,
            correlation_id=UUID4(),
        )

        bars = data_client._handle_bars.call_args.kwargs["bars"]
        assert len(bars) == 100
        print(unix_nanos_to_dt(bars[0].ts_init))
        assert unix_nanos_to_dt(bars[0].ts_init) == pd.Timestamp(
            "2023-01-04 23:50:49+00:00",
            tz="UTC",
        )
        assert unix_nanos_to_dt(bars[-1].ts_init) == pd.Timestamp(
            "2023-01-04 23:59:58+0000",
            tz="UTC",
        )
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing

    @pytest.mark.asyncio
    async def test_request_second_bars_with_start_only(self, data_client):
        pass  # : TODO

    @pytest.mark.asyncio
    async def test_request_bars_with_limit_only(self, data_client):
        data_client._handle_bars = Mock()

        await data_client._process_bar_generator(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            data_gen=LmaxMocks().bars_data_gen(xml_client=data_client.xml_client),
            limit=100,
            correlation_id=UUID4(),
        )

        bars = data_client._handle_bars.call_args.kwargs["bars"]
        assert len(bars) == 100
        assert unix_nanos_to_dt(bars[0].ts_init) == pd.Timestamp(
            "2023-01-03 21:16:00+00:00",
            tz="UTC",
        )
        assert unix_nanos_to_dt(bars[-1].ts_init) == pd.Timestamp("2023-01-03 23-00-00", tz="UTC")
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing

    @pytest.mark.asyncio
    async def test_request_bars_with_start_only(self, data_client):
        data_client._handle_bars = Mock()

        start = pd.Timestamp("2023-01-03 21-00-00", tz="UTC")
        end = pd.Timestamp("2023-01-03 23-00-00", tz="UTC")

        await data_client._process_bar_generator(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            data_gen=LmaxMocks().bars_data_gen(xml_client=data_client.xml_client),
            limit=sys.maxsize,
            correlation_id=UUID4(),
            stop=start,
        )

        bars = data_client._handle_bars.call_args.kwargs["bars"]
        assert len(bars) == 116
        assert unix_nanos_to_dt(bars[0].ts_init) == start
        assert unix_nanos_to_dt(bars[-1].ts_init) == end
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing

    @pytest.mark.asyncio
    async def test_request_bars_limit_lower_than_start(self, data_client):
        data_client._handle_bars = Mock()

        await data_client._process_bar_generator(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            data_gen=LmaxMocks().bars_data_gen(xml_client=data_client.xml_client),
            limit=100,
            correlation_id=UUID4(),
            stop=pd.Timestamp("2023-01-03 21-00-00", tz="UTC"),
        )

        bars = data_client._handle_bars.call_args.kwargs["bars"]
        assert len(bars) == 100
        assert pd.Series([x.ts_init for x in bars]).is_monotonic_increasing
        assert unix_nanos_to_dt(bars[0].ts_init) == pd.Timestamp(
            "2023-01-03 21:16:00+00:00",
            tz="UTC",
        )
        assert unix_nanos_to_dt(bars[-1].ts_init) == pd.Timestamp("2023-01-03 23-00-00", tz="UTC")

    @pytest.mark.asyncio
    async def test_request_bars_with_limit_higher_than_start(self, data_client):
        data_client._handle_bars = Mock()
        start = pd.Timestamp("2023-01-03 21-00-00", tz="UTC")
        end = pd.Timestamp("2023-01-03 23-00-00", tz="UTC")

        await data_client._process_bar_generator(
            bar_type=BarType.from_str("EUR/USD.LMAX-1-MINUTE-BID-EXTERNAL"),
            data_gen=LmaxMocks().bars_data_gen(xml_client=data_client.xml_client),
            limit=200,
            correlation_id=UUID4(),
            stop=pd.Timestamp("2023-01-03 21-00-00", tz="UTC"),
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

        await data_client._process_quote_tick_generator(
            instrument_id=InstrumentId.from_str("EUR/USD.LMAX"),
            data_gen=LmaxMocks().quotes_data_gen(xml_client=data_client.xml_client),
            limit=limit,
            correlation_id=UUID4(),
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
        await data_client._process_quote_tick_generator(
            instrument_id=InstrumentId.from_str("EUR/USD.LMAX"),
            data_gen=LmaxMocks().quotes_data_gen(xml_client=data_client.xml_client),
            limit=sys.maxsize,
            correlation_id=UUID4(),
            stop=start,
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
        limit = 20

        await data_client._process_quote_tick_generator(
            instrument_id=InstrumentId.from_str("EUR/USD.LMAX"),
            data_gen=LmaxMocks().quotes_data_gen(xml_client=data_client.xml_client),
            limit=limit,
            correlation_id=UUID4(),
            stop=start,
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
        await data_client._process_quote_tick_generator(
            instrument_id=InstrumentId.from_str("EUR/USD.LMAX"),
            data_gen=LmaxMocks().quotes_data_gen(xml_client=data_client.xml_client),
            limit=55500,
            correlation_id=UUID4(),
            stop=start,
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


# if __name__ == "__main__":

#     async def main_():
#         client = LMAXMocks.data_client()
#         client.connect()
#         instrument_id = InstrumentId.from_str("EUR/USD.LMAX")
#         client.subscribe_quote_ticks(instrument_id=instrument_id)
#         while True:
#             asyncio.sleep(1)

#     asyncio.run(main_())
#     # TestLMAXLiveDataClient().test_subscribe_quote_ticks()

# urls = [
#     "https://web-order.london-demo.lmax.com/marketdata/aggregate/4001/2023/01/2023-01-03-22-00-00-000-4001-bid-minute-aggregation.csv.gz",
#     "https://web-order.london-demo.lmax.com/marketdata/aggregate/4001/2023/01/2023-01-02-22-00-00-000-4001-bid-minute-aggregation.csv.gz",
# ]
