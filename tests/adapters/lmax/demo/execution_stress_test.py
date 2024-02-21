import pytest

from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from pytower.tests.adapters.lmax.demo.execution_demo_test import TestExecutionClientDemo
from pytower.tests.adapters.lmax.demo.execution_demo_test import TestExecutionClientLimit
from pytower.tests.adapters.lmax.demo.execution_demo_test import TestExecutionClientMarket


instrument_ids = [
    InstrumentId.from_str("EUR/USD.LMAX"),
    InstrumentId.from_str("USD/JPY.LMAX"),
    InstrumentId.from_str("GBP/USD.LMAX"),
    InstrumentId.from_str("USD/CAD.LMAX"),
    InstrumentId.from_str("AUD/USD.LMAX"),
    InstrumentId.from_str("EUR/JPY.LMAX"),
    InstrumentId.from_str("GBP/JPY.LMAX"),
    InstrumentId.from_str("EUR/GBP.LMAX"),
    InstrumentId.from_str("NZD/USD.LMAX"),
    InstrumentId.from_str("EUR/SEK.LMAX"),
    InstrumentId.from_str("USD/TRY.LMAX"),
]


@pytest.mark.parametrize("instrument_id", instrument_ids)
@pytest.mark.parametrize("side", [OrderSide.BUY, OrderSide.SELL])
class TestExecutionClientLimitAllInstruments(TestExecutionClientLimit):
    pass


@pytest.mark.parametrize("instrument_id", instrument_ids)
@pytest.mark.parametrize("side", [OrderSide.BUY, OrderSide.SELL])
class TestExecutionClientMarketAllInstruments(TestExecutionClientMarket):
    pass


@pytest.mark.parametrize("side", [OrderSide.BUY, OrderSide.SELL])
@pytest.mark.parametrize("instrument_id", instrument_ids)
class TestExecutionClientAllInstruments(TestExecutionClientDemo):
    pass


@pytest.mark.parametrize("side", [OrderSide.BUY])
@pytest.mark.parametrize("instrument_id", [InstrumentId.from_str("EUR/USD.LMAX")])
class TestExecutionClientDemoSingleInstrument(TestExecutionClientDemo):
    pass
