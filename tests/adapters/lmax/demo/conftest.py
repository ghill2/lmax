# from nautilus_trader.live.data_engine import LiveDataEngine
# import pytest
# from nautilus_trader.config.live import LiveExecEngineConfig
# from pytower.tests.adapters.lmax.stubs import LMAXStubs
# from nautilus_trader.test_kit.stubs.events import TestEventStubs
# from nautilus_trader.live.execution_engine import LiveExecutionEngine
# from nautilus_trader.portfolio.portfolio import Portfolio
# from nautilus_trader.test_kit.stubs.execution import TestExecStubs
# from nautilus_trader.model.identifiers import AccountId
# import pytest
# import asyncio
# from pytower.tests.adapters.lmax.stubs import LMAXStubs
# from pytower.tests.adapters.lmax.demo.setup import LMAXOrderSetupDemo
# from pytower.tests.adapters.lmax.demo.setup import LMAXOrderSetupDemo
# import pytest
# from nautilus_trader.model.identifiers import InstrumentId

# @pytest.fixture(scope="session")
# def event_loop():
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     asyncio.set_event_loop(loop)
#     yield loop
#     loop.close()


# @pytest.fixture(scope="session")
# def xml_client(event_loop):
#     xml_client = LMAXStubs.xml_client()
#     event_loop.run_until_complete(xml_client.connect())
#     yield xml_client
#     # event_loop.run_until_complete(xml_client.disconnect())


# @pytest.fixture(scope="session")
# def instrument_provider(event_loop):
#     instrument_provider = LMAXStubs.instrument_provider(loop=event_loop)
#     event_loop.run_until_complete(instrument_provider.xml_client.connect())
#     instrument_provider.load_all()
#     yield instrument_provider
#     # event_loop.run_until_complete(instrument_provider.xml_client.disconnect())


# @pytest.fixture(scope="session")
# def data_client(event_loop):
#     data_client = LMAXStubs.data_client(loop=event_loop)
#     event_loop.run_until_complete(data_client._connect())
#     data_client.instrument_provider.load_all()
#     yield data_client
#     event_loop.run_until_complete(data_client._disconnect())


# @pytest.fixture(scope="session")
# def exec_client(event_loop):
#     exec_client = LMAXStubs.exec_client(loop=event_loop)
#     event_loop.run_until_complete(exec_client._connect())
#     exec_client.instrument_provider.load_all()
#     yield exec_client
#     event_loop.run_until_complete(exec_client._disconnect())


# @pytest.fixture(scope="session")
# def order_setup(exec_client, data_client):
#     data_engine = LiveDataEngine(
#         loop=data_client.loop,
#         msgbus=data_client.msgbus,
#         cache=data_client.cache,
#         clock=data_client.clock,
#         logger=data_client.logger,
#     )

#     portfolio = Portfolio(
#         msgbus=exec_client.msgbus,
#         cache=exec_client.cache,
#         clock=exec_client.clock,
#         logger=exec_client.logger,
#     )
#     portfolio.update_account(TestEventStubs.cash_account_state())

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
#     exec_engine.register_client(exec_client)
#     data_engine.register_client(data_client)
#     data_engine.start()
#     exec_engine.start()

#     order_setup = LMAXOrderSetupDemo(exec_client=exec_client, data_client=data_client)

#     exec_client.loop.run_until_complete(order_setup.cancel_all())

#     yield order_setup

#     data_engine.stop()
#     exec_engine.stop()
#     # exec_engine.kill()
#     exec_client.loop.run_until_complete(exec_client.loop.shutdown_asyncgens())
