import asyncio
from pathlib import Path

import pytest


RESPONSES_FOLDER = Path("/Users/g1/BU/projects/pytower_develop/pytower/adapters/lmax/xml/responses")


class TestLMAXInstrumentProvider:
    @pytest.mark.asyncio
    async def test_load_async(self):
        pass

    @pytest.mark.asyncio()
    async def test_load_all_async(self, instrument_provider):
        pass


if __name__ == "__main__":

    async def main_():
        await TestLMAXInstrumentProvider().test_load_async()

    asyncio.run(main_())

# def test_request_instrument_currency_pair(self):
#     """
#     <assetClass>INDEX</assetClass>
#     <assetClass>CURRENCY</assetClass>
#     """
#     # # Arrange
#     # mock_response = Mock()
#     # with open(RESPONSES_FOLDER / "currency_pair.xml", "r") as f:
#     #     mock_response.text = f.read()

#     # self.session.make_request = Mock(return_value=mock_response)

#     # Act
#     instrument = self.client.request_instruments("EUR/USD")

#     # Arrange
#     # assert str(instrument) ==
