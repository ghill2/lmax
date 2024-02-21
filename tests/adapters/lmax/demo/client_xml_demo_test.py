import asyncio

import pandas as pd
import pytest

from pytower.adapters.lmax.xml.enums import LmaxAggregateOption
from pytower.adapters.lmax.xml.enums import LmaxAggregateResolution


class TestXMLClientDemo:
    @pytest.mark.asyncio()
    async def test_heartbeat(self):
        # TODO
        await self.orders.connect()
        await self.orders.login()
        await asyncio.sleep(3)
        await self.orders.logout()
        await asyncio.sleep(3)

    @pytest.mark.asyncio()
    async def test_login(self, xml_client):
        # Arrange & Act
        success = await xml_client.login()

        # Assert
        assert success
        assert xml_client.session_id is not None
        assert xml_client._headers.get("Cookie") is not None

    @pytest.mark.asyncio()
    async def test_login_twice(self, xml_client):
        # Does the JSESSIONID reset if login is called when already logged in?

        # Arrange & Act
        await xml_client.login()

        await xml_client.login()

    @pytest.mark.asyncio()
    async def test_logout(self, xml_client):
        # Arrange & Act
        await xml_client.login()
        await asyncio.sleep(0.1)
        success = await xml_client.logout()

        # Assert
        assert success
        assert xml_client.session_id is None
        assert xml_client._headers.get("Cookie") is None


class TestXMLClient:
    @pytest.mark.asyncio()
    async def test_request_orders(self, xml_client):
        # Arrange & Act
        orders = await xml_client.request_orders()
        print(f"orders: {len(orders)}")

        orders = await xml_client.request_orders()
        print(f"orders: {len(orders)}")

    @pytest.mark.asyncio()
    async def test_request_orders(self, xml_client):
        # Arrange & Act
        await xml_client.subscribe("order")
        xml_data = await xml_client._parse_stream(target_element="orders")
        print(xml_data)

        await xml_client.subscribe("order")
        xml_data = await xml_client._parse_stream(target_element="orders")
        print(xml_data)

    @pytest.mark.asyncio()
    async def test_request_positions(self, xml_client):
        # Arrange & Act
        positions = await xml_client.request_positions()
        print(f"positions: {len(positions)}")

        positions = await xml_client.request_positions()
        print(f"positions: {len(positions)}")

    @pytest.mark.asyncio()
    async def test_request_account_state(self, xml_client):
        # Arrange & Act
        state = await xml_client.request_account_state()
        print(state)
        state = await xml_client.request_account_state()
        print(state)

    @pytest.mark.asyncio()
    async def test_request_aggregate_urls(self, xml_client):
        urls = await xml_client.request_aggregate_urls(
            security_id=100934,
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-07"),
            option=LmaxAggregateOption.BID,
            resolution=LmaxAggregateResolution.MINUTE,
        )
        assert len(urls) == 7
        assert all("/aggregate/" in url for url in urls)

    @pytest.mark.asyncio()
    async def test_read_url(self, xml_client):
        urls = await xml_client.request_aggregate_urls(
            security_id=100934,
            start=pd.Timestamp("2023-09-15"),
            end=pd.Timestamp("2023-09-18"),
            option=LmaxAggregateOption.BID,
            resolution=LmaxAggregateResolution.MINUTE,
        )
        xml_data = await xml_client.read_url(urls[0])
        print(xml_data)

    @pytest.mark.asyncio()
    async def test_request_top_of_book_urls(self, xml_client):
        urls = await xml_client.request_top_of_book_urls(
            security_id=100934,
            start=pd.Timestamp("2023-01-01"),
            end=pd.Timestamp("2023-01-07"),
        )
        assert len(urls) == 7
        assert all("/orderbook/" in url for url in urls)

    @pytest.mark.asyncio()
    async def test_request_instruments(self, xml_client):
        instruments = await xml_client.request_instruments(query="")
        assert len(instruments) == 84

    @pytest.mark.asyncio()
    async def test_request_all(self, xml_client):
        results = await asyncio.gather(
            xml_client.request_orders(),
            xml_client.request_positions(),
            xml_client.request_account_state(),
            xml_client.request_top_of_book_urls(
                security_id=100934,
                start=pd.Timestamp("2023-01-01"),
                end=pd.Timestamp("2023-01-07"),
            ),
            xml_client.request_aggregate_urls(
                security_id=100934,
                start=pd.Timestamp("2023-01-01"),
                end=pd.Timestamp("2023-01-07"),
                option=LmaxAggregateOption.BID,
                resolution=LmaxAggregateResolution.MINUTE,
            ),
            xml_client.request_instruments(query=""),
        )
        print(f"orders: {len(results[0])}")
        print(f"positions: {len(results[1])}")
        print(f"account: {results[2]}")
        print(f"top_of_book_urls: {len(results[3])}")
        print(f"aggregate_urls: {len(results[4])}")
        print(f"instruments: {len(results[5])}")

    # # @patch('requests.post') , mock_post
    # def request_position_status_reports(self):
    #     # mock_response = requests.Response()
    #     # mock_response.status_code = 200
    #     # mock_response.text = xml_str
    #     # mock_post.return_value = mock_response

    #     # Act
    #     self.session.request_position_status_reports()
