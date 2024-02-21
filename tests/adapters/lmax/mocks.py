from pathlib import Path

import pandas as pd

from pytower.adapters.lmax.xml.enums import LmaxAggregateOption
from pytower.adapters.lmax.xml.enums import LmaxAggregateResolution
from pytower.adapters.lmax.xml.historic import LmaxBarDataGenerator
from pytower.adapters.lmax.xml.historic import LmaxQuoteTickDataGenerator
from pytower.tests.adapters.lmax import XML_RESPONSES


class MockLmaxBarDataGeneratorEURUSD(LmaxBarDataGenerator):
    async def _iterate_csv_data(self):
        responses_dir = Path(XML_RESPONSES / "historic/EUR-USD-2023-01-03-23-00-00")
        for path in sorted(responses_dir.iterdir()):
            yield path.read_text()


class MockLmaxQuoteTickDataGeneratorEURUSD(LmaxQuoteTickDataGenerator):
    async def _iterate_csv_data(self):
        responses_dir = Path(XML_RESPONSES / "historic/quotetick")
        for path in sorted(responses_dir.iterdir()):
            yield path.read_text()


class LmaxMocks:
    def bars_data_gen(self, xml_client):
        return MockLmaxBarDataGeneratorEURUSD(
            xml_client=xml_client,
            logger=xml_client.logger,
            security_id=4001,
            start=pd.Timestamp("2023-01-03 23-00-00", tz="UTC"),
            option=LmaxAggregateOption.BID,
            resolution=LmaxAggregateResolution.MINUTE,
        )

    def quotes_data_gen(self, xml_client):
        return MockLmaxQuoteTickDataGeneratorEURUSD(
            xml_client=xml_client,
            logger=xml_client.logger,
            security_id=4001,
            start=pd.Timestamp("2023-01-05", tz="UTC"),
        )
