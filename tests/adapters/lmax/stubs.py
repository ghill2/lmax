import asyncio
from decimal import Decimal
from xml.etree import ElementTree

from dotenv import dotenv_values

from nautilus_trader.common.enums import LogLevel
from nautilus_trader.common.component import Logger
from nautilus_trader.common.component import MessageBus
from nautilus_trader.test_kit.stubs.component import TestComponentStubs
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from pytower.adapters.lmax.data import LmaxLiveDataClient
from pytower.adapters.lmax.execution import LmaxLiveExecutionClient
from pytower.adapters.lmax.fix.client import LmaxFixClient
from pytower.adapters.lmax.providers import LmaxInstrumentProvider
from pytower.adapters.lmax.xml.client import LmaxXmlClient
from pytower.adapters.lmax.xml.types import LmaxInstrument
from pytower.adapters.lmax.xml.types import LmaxOrder
from pytower.adapters.lmax.xml.types import LmaxPosition
from pytower.adapters.lmax.xml.util import unpretty_xml
from pytower.tests.adapters.lmax import XML_RESPONSES


class LMAXStubs:
    @staticmethod
    def order(instrumentId: int, instructionId: str, quantity: float) -> LmaxOrder:
        return LmaxOrder(
            timeInForce=None,
            instructionId=instructionId,
            originalInstrumentId=None,
            orderId=None,
            accountId=None,
            instrumentId=instrumentId,
            quantity=Decimal(quantity),
            matchedQuantity=None,
            matchedCost=None,
            cancelledQuantity=None,
            timestamp=None,
            orderType=None,
            openQuantity=None,
            openCost=None,
            cumulativeCost=None,
            commission=None,
            workingState=None,
        )

    @staticmethod
    def position(instrumentId: int, openQuantity: Decimal) -> LmaxPosition:
        return LmaxPosition(
            accountId=None,
            instrumentId=instrumentId,
            valuation=None,
            shortUnfilledCost=None,
            longUnfilledCost=None,
            openQuantity=openQuantity,
            cumulativeCost=None,
            openCost=None,
        )

    @staticmethod
    def xml_client(loop: asyncio.AbstractEventLoop | None = None) -> LmaxXmlClient:
        return LmaxXmlClient(
            hostname="https://web-order.london-demo.lmax.com",
            username=dotenv_values()["username"],
            password=dotenv_values()["password"],
            clock=TestComponentStubs.clock(),
            cache=TestComponentStubs.cache(),
            logger=TestComponentStubs.logger(),
            loop=loop if loop is not None else asyncio.get_event_loop(),
        )

    @classmethod
    def instrument_provider(cls, loop: asyncio.AbstractEventLoop | None = None):
        clock = TestComponentStubs.clock()
        logger = Logger(
            clock=clock,
            level_stdout=LogLevel.DEBUG,
            # bypass=True,
        )
        xml_client = LmaxXmlClient(
            hostname="https://web-order.london-demo.lmax.com",
            username=dotenv_values()["username"],
            password=dotenv_values()["password"],
            clock=clock,
            cache=TestComponentStubs.cache(),
            logger=logger,
            loop=loop if loop is not None else asyncio.get_event_loop(),
        )

        instrument_provider = LmaxInstrumentProvider(
            xml_client=xml_client,
            logger=logger,
        )
        cls._load_all_instruments(instrument_provider)
        return instrument_provider

    @staticmethod
    def _load_all_instruments(instrument_provider: LmaxInstrumentProvider):
        return
        # load all instruments into the instrumentprovider
        folder = XML_RESPONSES / "currency_pairs"
        paths = [
            folder / "page1.xml",
            folder / "page2.xml",
            folder / "page3.xml",
            folder / "page4.xml",
            folder / "page5.xml",
        ]

        for path in paths:
            with open(path) as f:
                root = ElementTree.fromstring(unpretty_xml(f.read()))
                for elem in root.findall(".//instrument"):
                    instrument_provider.add(
                        LmaxInstrument.from_xml(elem).to_nautilus(),
                    )

    @classmethod
    def data_client(cls, loop: asyncio.AbstractEventLoop | None = None) -> LmaxLiveDataClient:
        loop = loop or asyncio.get_event_loop()
        cache = TestComponentStubs.cache()
        clock = TestComponentStubs.clock()
        logger = Logger(
            clock=clock,
            level_stdout=LogLevel.DEBUG,
            # bypass=True,
        )
        msgbus = MessageBus(
            trader_id=TestIdStubs.trader_id(),
            clock=clock,
            logger=logger,
        )

        xml_client = LmaxXmlClient(
            hostname="https://web-order.london-demo.lmax.com",
            username=dotenv_values()["username"],
            password=dotenv_values()["password"],
            clock=clock,
            cache=cache,
            logger=logger,
            loop=loop,
        )

        instrument_provider = LmaxInstrumentProvider(
            xml_client=xml_client,
            logger=logger,
        )

        fix_client = LmaxFixClient(
            hostname="fix-marketdata.london-demo.lmax.com",
            username=dotenv_values()["username"],
            password=dotenv_values()["password"],
            target_comp_id="LMXBDM",
            logger=logger,
            loop=loop,
            clock=clock,
        )

        data_client = LmaxLiveDataClient(
            fix_client=fix_client,
            xml_client=xml_client,
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            logger=logger,
            loop=loop,
            clock=clock,
        )

        # prepare components
        # data_engine.register_client(data_client)
        # data_engine.start()

        cls._load_all_instruments(instrument_provider)
        for instrument in instrument_provider.list_all():
            cache.add_instrument(instrument)

        return data_client

    @classmethod
    def exec_client(cls, loop: asyncio.AbstractEventLoop | None = None) -> LmaxLiveDataClient:
        loop = loop or asyncio.get_event_loop()
        cache = TestComponentStubs.cache()
        clock = TestComponentStubs.clock()
        logger = Logger(
            clock=clock,
            level_stdout=LogLevel.DEBUG,
            # bypass=True,
        )
        msgbus = MessageBus(
            trader_id=TestIdStubs.trader_id(),
            clock=clock,
            logger=logger,
        )

        xml_client = LmaxXmlClient(
            hostname="https://web-order.london-demo.lmax.com",
            username=dotenv_values()["username"],
            password=dotenv_values()["password"],
            clock=clock,
            cache=cache,
            logger=logger,
            loop=loop,
        )

        instrument_provider = LmaxInstrumentProvider(
            xml_client=xml_client,
            logger=logger,
        )

        fix_client = LmaxFixClient(
            hostname="fix-order.london-demo.lmax.com",
            username=dotenv_values()["username"],
            password=dotenv_values()["password"],
            target_comp_id="LMXBD",
            logger=logger,
            loop=loop,
            clock=clock,
        )

        exec_client = LmaxLiveExecutionClient(
            fix_client=fix_client,
            xml_client=xml_client,
            instrument_provider=instrument_provider,
            logger=logger,
            loop=loop,
            clock=clock,
            msgbus=msgbus,
            cache=cache,
        )

        # prepare components

        cls._load_all_instruments(instrument_provider)
        for instrument in instrument_provider.list_all():
            cache.add_instrument(instrument)

        return exec_client

    # @staticmethod
    # def fix_client(host: str = ,
    #                 target_comp_id: str,

    #                 loop: asyncio.AbstractEventLoop = None,
    #                 logger: Logger = None,
    #                 clock: LiveClock = None,
    #                ) -> FIXClient:
    #     return FIXClient(
    #         host="fix-marketdata.london-demo.lmax.com",
    #         port=443,
    #         cafile="/Users/g1/BU/projects/pytower_develop/pytower/adapters/lmax/server.pem",
    #         username=dotenv_values()["username"],
    #         password=dotenv_values()["password"],
    #         target_comp_id=target_comp_id,
    #         logger=logger if logger is not None else TestComponentStubs.logger(),
    #         loop=loop if loop is not None else asyncio.get_event_loop(),
    #         clock=clock if clock is not None else TestComponentStubs.clock(),
    #     )

    # @classmethod
    # def instrument_provider(cls,
    #                 loop: asyncio.AbstractEventLoop = None,
    #                 logger: Logger = None,
    #                 cache: Cache = None,
    #                 ) -> LMAXInstrumentProvider:

    #     return LMAXInstrumentProvider(
    #             xml_client=cls.xml_client(loop=loop, cache=cache),
    #             logger=logger if logger is not None else TestComponentStubs.logger(),
    #         )
