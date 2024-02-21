# import pytest
# from nautilus_trader.config.live import LiveExecEngineConfig
# from pytower.adapters.lmax.fix.client import LmaxFixClient
# from pytower.adapters.lmax.providers import LmaxInstrumentProvider
# from pytower.adapters.lmax.xml.client import LmaxXmlClient
# from pytower.tests.adapters.lmax.stubs import LMAXStubs
# from nautilus_trader.test_kit.stubs.events import TestEventStubs
# from nautilus_trader.live.execution_engine import LiveExecutionEngine
# from nautilus_trader.portfolio.portfolio import Portfolio
# from nautilus_trader.test_kit.stubs.execution import TestExecStubs
# from nautilus_trader.model.identifiers import AccountId


# @pytest.fixture(scope="function")
# def xml_client() -> LmaxXmlClient:
#     return LMAXStubs.xml_client()


# @pytest.fixture(scope="function")
# def instrument_provider() -> LmaxInstrumentProvider:
#     instrument_provider = LMAXStubs.instrument_provider()
#     # for instrument in instrument_provider.list_all():
#     #     print(instrument.id, instrument.info["id"], instrument.size_precision, instrument.price_precision)
#     return instrument_provider


# @pytest.fixture(scope="function")
# def fix_client() -> LmaxFixClient:
#     return LMAXStubs.fix_client()


# @pytest.fixture(scope="function")
# def instrument_provider():
#     return LMAXStubs.instrument_provider()


# @pytest.fixture(scope="function")
# def data_client():
#     data_client = LMAXStubs.data_client()
#     return data_client


# @pytest.fixture(scope="function")
# def data_engine(data_client):
#     #     self.data_engine = LiveDataEngine(
#     #         loop=self.loop,
#     #         msgbus=self.msgbus,
#     #         cache=self.cache,
#     #         clock=self.clock,
#     #         logger=self.logger,
#     #     )
#     pass  # TODO


# @pytest.fixture(scope="function")
# def exec_client():
#     return LMAXStubs.exec_client()


# @pytest.fixture(scope="function")
# def exec_engine(exec_client):
#     portfolio = Portfolio(
#         msgbus=exec_client.msgbus,
#         cache=exec_client.cache,
#         clock=exec_client.clock,
#         logger=exec_client.logger,
#     )

#     exec_engine = LiveExecutionEngine(
#         loop=exec_client.loop,
#         msgbus=exec_client.msgbus,
#         cache=exec_client.cache,
#         clock=exec_client.clock,
#         logger=exec_client.logger,
#         config=LiveExecEngineConfig(
#             # reconciliation=False,
#             inflight_check_interval_ms=0,
#         ),
#     )

#     account_id = AccountId("LMAX-1")
#     exec_client.cache.add_account(TestExecStubs.margin_account(account_id))
#     exec_client._set_account_id(account_id)

#     portfolio.update_account(TestEventStubs.cash_account_state())

#     exec_engine.register_client(exec_client)

#     exec_engine.start()

#     yield exec_engine
#     exec_engine.stop()
#     # exec_engine.kill()
#     exec_client.loop.run_until_complete(exec_client.loop.shutdown_asyncgens())
#     exec_client.loop.close()


# ##################################################################################################
# # data_client.connect()
# # event_loop.run_until_complete(asyncio.sleep(0.5))
# # async def connect():

# #     await asyncio.sleep(0.5)
# # await asyncio.wait_for(data_client.fix_client.is_logged_on.wait(), timeout=2)
# # assert data_client.is_connected
# # assert xml_client.is_connected

# #     exec_engine.register_client(exec_client)

# #     for instrument in instrument_provider.list_all():
# #         cache.add_instrument(instrument)

# #     exec_engine.start()
# #     # await exec_client_.fix_client.connect()
# #     return exec_client

# #     # portfolio.update_account(TestEventStubs.cash_account_state())


# # def setup_lmax_demo(self, event_loop):

# #     self.loop = event_loop
# #     asyncio.set_event_loop(self.loop)

# #     self.clock = LiveClock()
# #     self.logger = Logger(self.clock)
# #     self.cache = TestComponentStubs.cache()
# #     self.account_id = TestIdStubs.account_id()
# #     self.trader_id = TestIdStubs.trader_id()
# #     self.strategy_id = TestIdStubs.strategy_id()
# #     self.order_side = OrderSide.BUY
# #     self.xml_client = XMLClient(
# #         hostname="https://web-order.london-demo.lmax.com",
# #         username=dotenv_values()["username"],
# #         password=dotenv_values()["password"],
# #         clock=self.clock,
# #         cache=self.cache,
# #         logger=self.logger,
# #     )

# #     self.instrument_provider = LMAXInstrumentProvider(
# #                                 client=self.xml_client,
# #                                 logger=self.logger,
# #                             )
# #     self.instrument = self.instrument_provider.find(InstrumentId.from_str("XBT/USD.LMAX"))

# #     self.msgbus = MessageBus(
# #         trader_id=self.trader_id,
# #         clock=self.clock,
# #         logger=self.logger,
# #     )


# #     self.data_engine = LiveDataEngine(
# #         loop=self.loop,
# #         msgbus=self.msgbus,
# #         cache=self.cache,
# #         clock=self.clock,
# #         logger=self.logger,
# #     )

# #     self.exec_engine = LiveExecutionEngine(
# #         loop=self.loop,
# #         msgbus=self.msgbus,
# #         cache=self.cache,
# #         clock=self.clock,
# #         logger=self.logger,
# #         config=LiveExecEngineConfig(
# #                 reconciliation=False,
# #                 inflight_check_interval_ms=0,
# #         )
# #     )

# #     self.fix_client = FIXClient(
# #         host="fix-order.london-demo.lmax.com",
# #         port=443,
# #         cafile="/Users/g1/BU/projects/pytower_develop/pytower/adapters/lmax/server.pem",
# #         username=dotenv_values()["username"],
# #         password=dotenv_values()["password"],
# #         target_comp_id="LMXBD",
# #         logger=self.logger,
# #         loop=self.loop,
# #         clock=self.clock,
# #     )

# #     self.report_provider = LMAXReportProvider(
# #         fix_client=self.fix_client,
# #         xml_client=self.xml_client,
# #         instrument_provider=self.instrument_provider,
# #         cache=self.cache,
# #         clock=self.clock,
# #     )

# #     self.exec_client = LMAXLiveExecutionClient(
# #                 fix_client=self.fix_client,
# #                 xml_client=self.xml_client,
# #                 report_provider=self.report_provider,
# #                 instrument_provider=self.instrument_provider,
# #                 logger=self.logger,
# #                 loop=self.loop,
# #                 clock=self.clock,
# #                 msgbus=self.msgbus,
# #                 cache=self.cache,
# #     )
# #     # self.portfolio.update_account(TestEventStubs.cash_account_state())
# #     self.exec_engine.register_client(self.exec_client)

# #     self.account_id = AccountId("LMAX-001")

# #     self.cache.add_account(TestExecStubs.margin_account(self.account_id))

# #     self.instrument_provider.load_all()
# #     for instrument in self.instrument_provider.list_all():
# #         self.cache.add_instrument(instrument)

# #     self.exec_client._set_account_id(self.account_id)

# #     self.data_client = LMAXLiveDataClient(
# #                         fix_client=FIXClient(
# #                             host="fix-marketdata.london-demo.lmax.com",
# #                             port=443,
# #                             cafile="/Users/g1/BU/projects/pytower_develop/pytower/adapters/lmax/server.pem",
# #                             username=dotenv_values()["username"],
# #                             password=dotenv_values()["password"],
# #                             target_comp_id="LMXBDM",
# #                             logger=self.logger,
# #                             loop=self.loop,
# #                             clock=self.clock,
# #                         ),
# #                         instrument_provider=self.instrument_provider,
# #                         msgbus=self.msgbus,
# #                         cache=self.cache,
# #                         logger=self.logger,
# #                         loop=self.loop,
# #                         clock=self.clock,

# #     )
# #     self.data_engine.register_client(self.data_client)
# #     self.data_engine.start()
# #     self.exec_engine.start()
# #     self.strategy_id = TestIdStubs.strategy_id()
# #     self.trader_id = TestIdStubs.trader_id()
# #     self.instrument = self.instrument_provider.find(InstrumentId.from_str("XBT/USD.LMAX"))

# #     # connect the clients
# #     async def connect():
# #         # if not self.data_client.is_connected:
# #         self.exec_engine.connect()
# #         await asyncio.sleep(0.5) # LMAX will reject logon if too many logon requests are sent at once
# #         self.data_engine.connect()
# #         # if not self.exec_client.is_connected:
# #         await asyncio.gather(
# #             self.data_client.fix_client.is_logged_on.wait(),
# #             self.exec_client.fix_client.is_logged_on.wait(),
# #         )
# #     self.loop.run_until_complete(connect())
# #     assert self.exec_client.is_connected
# #     assert self.data_client.is_connected


# # self.instrument_id = InstrumentId.from_str("XBT/USD.LMAX")

# # @pytest.fixture(scope="session")
# # def components():
# #     clock = LiveClock()
# #     logger = Logger(clock)
# #     cache = TestComponentStubs.cache()
# #     trader_id = TestIdStubs.trader_id()
# #     msgbus = MessageBus(
# #         trader_id=trader_id,
# #         clock=clock,
# #         logger=logger,
# #     )
# #     return clock, logger, cache, msgbus


# # @pytest.fixture(scope="session")
# # def instrument_provider(components, xml_client):
# #     clock, logger, cache, msgbus = components

# #     instrument_provider = LMAXInstrumentProvider(
# #                                 client=xml_client,
# #                                 logger=logger,
# #                             )

# #     instrument_provider.load_all()
# #     return instrument_provider

# # @pytest.fixture(scope="session")
# # def instrument(instrument_provider) -> Instrument:
# #     return instrument_provider.find(InstrumentId.from_str("XBT/USD.LMAX"))

# # @pytest.fixture(scope="session")
# # def xml_client(components):
# #     clock, logger, cache, msgbus = components

# #     xml_client = XMLClient(
# #         hostname="https://web-order.london-demo.lmax.com",
# #         username=dotenv_values()["username"],
# #         password=dotenv_values()["password"],
# #         clock=clock,
# #         cache=cache,
# #         logger=logger,
# #     )
