# class TestLMAXInstrumentProviderDemo:
#     @pytest.mark.asyncio()
#     async def test_request_instrument(self, xml_client):
#         # Arrange & Act
#         instrument = await xml_client.request_instrument(InstrumentId.from_str("EUR/USD.LMAX"))

#         # Arrange
#         assert (
#             str(instrument)
#             == "CurrencyPair(id=EUR/USD.LMAX, raw_symbol=EUR/USD, asset_class=FX, asset_type=SPOT, quote_currency=USD, is_inverse=False, price_precision=5, price_increment=0.00001, size_precision=1, size_increment=0.1, multiplier=1, lot_size=10000.00, margin_init=1, margin_maint=1, maker_fee=0.250, taker_fee=0.250, info={'id': 4001, 'retailVolatilityBandPercentage': 2, 'maximumPositionThreshold': Decimal('50000.00'), 'startTime': Timestamp('2010-07-09 13:09:00'), 'openingOffset': -415, 'closingOffset': 1020, 'timezone': 'America/New_York', 'unitPrice': Decimal('10000'), 'trustedSpread': Decimal('0.0036'), 'stopBuffer': 0, 'minimumCommission': Decimal('0'), 'tradingDays': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'], 'longSwapPoints': Decimal('0.950'), 'shortSwapPoints': Decimal('-0.510'), 'swapPointValue': Decimal('1.0')})"
#         )

#     @pytest.mark.asyncio()
#     async def test_request_instruments(self, xml_client):
#         # Arrange & Act
#         instruments = await xml_client.request_instruments(
#             [InstrumentId.from_str("EUR/USD.LMAX"), InstrumentId.from_str("USD/JPY.LMAX")],
#         )

#         # Arrange
#         assert (
#             str(instruments[0])
#             == "CurrencyPair(id=EUR/USD.LMAX, raw_symbol=EUR/USD, asset_class=FX, asset_type=SPOT, quote_currency=USD, is_inverse=False, price_precision=5, price_increment=0.00001, size_precision=1, size_increment=0.1, multiplier=1, lot_size=10000.00, margin_init=1, margin_maint=1, maker_fee=0.250, taker_fee=0.250, info={'id': 4001, 'retailVolatilityBandPercentage': 2, 'maximumPositionThreshold': Decimal('50000.00'), 'startTime': Timestamp('2010-07-09 13:09:00'), 'openingOffset': -415, 'closingOffset': 1020, 'timezone': 'America/New_York', 'unitPrice': Decimal('10000'), 'trustedSpread': Decimal('0.0036'), 'stopBuffer': 0, 'minimumCommission': Decimal('0'), 'tradingDays': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'], 'longSwapPoints': Decimal('0.950'), 'shortSwapPoints': Decimal('-0.510'), 'swapPointValue': Decimal('1.0')})"
#         )
#         assert (
#             str(instruments[1])
#             == "CurrencyPair(id=USD/JPY.LMAX, raw_symbol=USD/JPY, asset_class=FX, asset_type=SPOT, quote_currency=JPY, is_inverse=False, price_precision=3, price_increment=0.001, size_precision=1, size_increment=0.1, multiplier=1, lot_size=10000.00, margin_init=1, margin_maint=1, maker_fee=0.250, taker_fee=0.250, info={'id': 4004, 'retailVolatilityBandPercentage': 2, 'maximumPositionThreshold': Decimal('50000.00'), 'startTime': Timestamp('2010-07-09 13:09:00'), 'openingOffset': -415, 'closingOffset': 1020, 'timezone': 'America/New_York', 'unitPrice': Decimal('10000'), 'trustedSpread': Decimal('0.22'), 'stopBuffer': 0, 'minimumCommission': Decimal('0'), 'tradingDays': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'], 'longSwapPoints': Decimal('0.920'), 'shortSwapPoints': Decimal('-0.820'), 'swapPointValue': Decimal('100')})"
#         )

#     @pytest.mark.asyncio()
#     async def test_request_instruments_all(self, xml_client):
#         # Arrange & Act
#         instruments = await xml_client.request_instruments_all()

#         # Assert
#         assert len(instruments) == 84
