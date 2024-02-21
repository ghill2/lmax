from http.cookies import Morsel
from unittest.mock import AsyncMock

import pytest

from nautilus_trader.model.currencies import GBP
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.identifiers import AccountId
from pytower.adapters.lmax.xml.util import unpretty_xml
from pytower.tests.adapters.lmax import XML_RESPONSES


class TestXMLClient:
    @pytest.mark.asyncio()
    async def test_login(self, xml_client):
        # Arrange
        session_id = "session123"
        cookie = Morsel()
        cookie.set("JSESSIONID", session_id, session_id)
        mock_response = AsyncMock()
        mock_response.cookies = {"JSESSIONID": cookie}
        with open(XML_RESPONSES / "login.xml") as f:
            mock_response.text.return_value = f.read()

        xml_client.post = AsyncMock(return_value=mock_response)

        # Act
        success = await xml_client.login()

        # Assert
        assert success
        assert xml_client._headers.get("Cookie") == f"JSESSIONID={session_id}"
        assert xml_client.session_id == session_id

    @pytest.mark.asyncio()
    async def test_login_invalid_credentials(self):
        pass

    @pytest.mark.asyncio()
    async def test_logout(self, xml_client):
        # Arrange
        session_id = "session123"
        xml_client._session_id = session_id
        xml_client._headers["Cookie"] = f"JSESSIONID={session_id}"
        with open(XML_RESPONSES / "logout.xml") as f:
            xml_client.post_xml = AsyncMock(return_value=f.read())

        # Act
        success = await xml_client.logout()

        assert success
        assert xml_client.session_id is None
        assert xml_client._headers.get("Cookie") is None

    @pytest.mark.asyncio()
    async def test_logout_failure(self):
        pass

    @pytest.mark.asyncio()
    async def test_request_orders(self, xml_client):
        # Arrange
        xml_client.login = AsyncMock()
        xml_client.logout = AsyncMock()
        xml_client.subscribe = AsyncMock()

        async def orders_response():
            with open(XML_RESPONSES / "orders.xml") as f:
                yield unpretty_xml(f.read())

        xml_client._iter_stream = orders_response

        # Act
        orders = await xml_client.request_orders()

        # Assert
        assert len(orders) == 14

    @pytest.mark.asyncio()
    async def test_request_orders_with_filter(self, xml_client):
        pass

    @pytest.mark.asyncio()
    async def test_request_positions(self, xml_client):
        # Arrange
        xml_client.login = AsyncMock()
        xml_client.logout = AsyncMock()
        xml_client.subscribe = AsyncMock()

        # Act
        async def positions_response():
            with open(XML_RESPONSES / "positions.xml") as f:
                yield unpretty_xml(f.read())

        xml_client._iter_stream = positions_response

        # Act
        positions = await xml_client.request_positions()
        assert len(positions) == 2

    @pytest.mark.asyncio()
    async def test_request_positions_with_filter(self, xml_client):
        pass

    @pytest.mark.asyncio()
    async def test_request_account_state(self, xml_client):
        xml_client.login = AsyncMock()
        xml_client.logout = AsyncMock()
        xml_client.subscribe = AsyncMock()

        async def account_state_response():
            with open(XML_RESPONSES / "account_state.xml") as f:
                yield unpretty_xml(f.read())

        xml_client._iter_stream = account_state_response

        state = await xml_client.request_account_state()
        assert state.account_id == AccountId("LMAX-1")
        assert state.account_type == AccountType.MARGIN
        assert state.base_currency == GBP
        assert state.is_reported is True
        assert (
            str(state.balances[0])
            == "AccountBalance(total=8_765.72 GBP, locked=778.15 GBP, free=7_987.57 GBP)"
        )
        assert (
            str(state.margins[0])
            == "MarginBalance(initial=788.67 GBP, maintenance=788.67 GBP, instrument_id=None)"
        )

    @pytest.mark.asyncio()
    async def test_request_instruments(self, xml_client):
        xml_client.login = AsyncMock()
        xml_client.logout = AsyncMock()

        # Arrange
        folder = XML_RESPONSES / "currency_pairs"
        paths = [
            folder / "page1.xml",
            folder / "page2.xml",
            folder / "page3.xml",
            folder / "page4.xml",
            folder / "page5.xml",
        ]

        responses = []
        for path in paths:
            with open(path) as f:
                responses.append(unpretty_xml(f.read()))

        xml_client.post_xml = AsyncMock(side_effect=responses)

        # Act
        instruments = await xml_client.request_instruments(query="")

        # Assert
        assert len(instruments) == 84

        urls = [call.args[0] for call in xml_client.post_xml.call_args_list]

        assert len(urls) == 5
        assert urls[0] == "/secure/instrument/searchCurrentInstruments?q=&offset=0"
        assert urls[1] == "/secure/instrument/searchCurrentInstruments?q=&offset=100615"
        assert urls[2] == "/secure/instrument/searchCurrentInstruments?q=&offset=100481"
        assert urls[3] == "/secure/instrument/searchCurrentInstruments?q=&offset=100639"
        assert urls[4] == "/secure/instrument/searchCurrentInstruments?q=&offset=100944"

    # @pytest.mark.asyncio()
    # async def test_request_aggregate_urls(self, xml_client):
    #     xml_client.login = AsyncMock()
    #     xml_client.logout = AsyncMock()
    #     xml_client.post = AsyncMock()
    #     xml_client.subscribe = AsyncMock()

    #     async def urls_response():
    #         with open(XML_RESPONSES / "urls_aggregate.xml", "r") as f:
    #             yield unpretty_xml(f.read())
    #     xml_client._iter_stream = urls_response

    #     urls = await xml_client.request_aggregate_urls(
    #                                 security_id=100934,
    #                                 start=pd.Timestamp("2023-01-01"),
    #                                 end=pd.Timestamp("2023-01-07"),
    #                                 option=LmaxAggregateOption.BID,
    #                                 resolution=LmaxAggregateResolution.MINUTE,
    #     )
    #     assert len(urls) == 7
    #     assert all("/aggregate/" in url for url in urls)

    # @pytest.mark.asyncio()
    # async def test_request_aggregate_urls(self, xml_client):
    #     xml_client.login = AsyncMock()
    #     xml_client.logout = AsyncMock()
    #     xml_client.post = AsyncMock()
    #     xml_client.subscribe = AsyncMock()

    #     async def urls_response():
    #         with open(XML_RESPONSES / "urls_top_of_book.xml", "r") as f:
    #             yield unpretty_xml(f.read())
    #     xml_client._iter_stream = urls_response

    #     urls = await xml_client.request_top_of_book_urls(
    #                                 security_id=100934,
    #                                 start=pd.Timestamp("2023-01-01"),
    #                                 end=pd.Timestamp("2023-01-07"),
    #     )
    #     assert len(urls) == 7
    #     assert all("/orderbook/" in url for url in urls)
