import asyncio
from functools import lru_cache

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.live.factories import LiveDataClientFactory
from nautilus_trader.live.factories import LiveExecClientFactory
from nautilus_trader.common.component import MessageBus
from pytower.adapters.lmax.config import LmaxDataClientConfig
from pytower.adapters.lmax.config import LmaxExecClientConfig
from pytower.adapters.lmax.data import LmaxLiveDataClient
from pytower.adapters.lmax.execution import LmaxLiveExecutionClient
from pytower.adapters.lmax.fix.client import LmaxFixClient
from pytower.adapters.lmax.providers import LmaxInstrumentProvider
from pytower.adapters.lmax.xml.client import LmaxXmlClient


@lru_cache(1)
def get_cached_lmax_instrument_provider(
    xml_client: LmaxXmlClient,
    config: InstrumentProviderConfig,
    logger: Logger,
) -> LmaxInstrumentProvider:
    return LmaxInstrumentProvider(xml_client=xml_client, config=config, logger=logger)


@lru_cache(1)
def get_cached_lmax_fix_client(
    hostname: str,
    username: str,
    password: str,
    target_comp_id: str,
    logger: Logger,
    loop: asyncio.AbstractEventLoop,
    clock: LiveClock,
    heartbeat_frequency_seconds: int = 30,
    logon_timeout_seconds: int = 10,
) -> LmaxFixClient:
    return LmaxFixClient(
        hostname=hostname,
        username=username,
        password=password,
        target_comp_id=target_comp_id,
        logger=logger,
        loop=loop,
        clock=clock,
        heartbeat_frequency_seconds=heartbeat_frequency_seconds,
        logon_timeout_seconds=logon_timeout_seconds,
    )


@lru_cache(1)
def get_cached_lmax_xml_client(
    hostname: str,
    username: str,
    password: str,
    clock: LiveClock,
    cache: Cache,
    logger: Logger,
    loop: asyncio.AbstractEventLoop,
) -> LmaxXmlClient:
    return LmaxXmlClient(
        hostname=hostname,
        username=username,
        password=password,
        clock=clock,
        cache=cache,
        logger=logger,
        loop=loop,
    )


class LmaxLiveDataClientFactory(LiveDataClientFactory):
    """
    Provides a `Lmax` live data client factory.
    """

    @staticmethod
    def create(  # type: ignore
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: LmaxDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        logger: Logger,
    ) -> LmaxLiveDataClient:
        xml_client: LmaxXmlClient = get_cached_lmax_xml_client(
            hostname=config.xml_client.hostname,
            username=config.xml_client.username,
            password=config.xml_client.password,
            clock=clock,
            cache=cache,
            logger=logger,
            loop=loop,
        )

        # Get instrument provider singleton
        provider = get_cached_lmax_instrument_provider(
            xml_client=xml_client,
            config=config.instrument_provider,
            logger=logger,
        )

        for instrument in provider.list_all():
            cache.add_instrument(instrument)

        fix_client: LmaxFixClient = get_cached_lmax_fix_client(
            hostname=config.fix_client.hostname,
            username=config.fix_client.username,
            password=config.fix_client.password,
            target_comp_id=config.fix_client.target_comp_id,
            logger=logger,
            loop=loop,
            clock=clock,
            heartbeat_frequency_seconds=config.fix_client.heartbeat_frequency_seconds,
            logon_timeout_seconds=config.fix_client.logon_timeout_seconds,
        )

        # Create client
        return LmaxLiveDataClient(
            fix_client=fix_client,
            xml_client=xml_client,
            instrument_provider=provider,
            msgbus=msgbus,
            cache=cache,
            logger=logger,
            loop=loop,
            clock=clock,
        )


class LmaxLiveExecClientFactory(LiveExecClientFactory):
    @staticmethod
    def create(  # type: ignore
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: LmaxExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        logger: Logger,
    ) -> LmaxLiveExecutionClient:
        xml_client: LmaxXmlClient = get_cached_lmax_xml_client(
            hostname=config.xml_client.hostname,
            username=config.xml_client.username,
            password=config.xml_client.password,
            clock=clock,
            cache=cache,
            logger=logger,
            loop=loop,
        )

        # Get instrument provider singleton
        provider = get_cached_lmax_instrument_provider(
            xml_client=xml_client,
            config=config.instrument_provider,
            logger=logger,
        )

        for instrument in provider.list_all():
            cache.add_instrument(instrument)

        fix_client: LmaxFixClient = get_cached_lmax_fix_client(
            hostname=config.fix_client.hostname,
            username=config.fix_client.username,
            password=config.fix_client.password,
            target_comp_id=config.fix_client.target_comp_id,
            logger=logger,
            loop=loop,
            clock=clock,
            heartbeat_frequency_seconds=config.fix_client.heartbeat_frequency_seconds,
            logon_timeout_seconds=config.fix_client.logon_timeout_seconds,
        )

        return LmaxLiveExecutionClient(
            fix_client=fix_client,
            xml_client=xml_client,
            instrument_provider=provider,
            logger=logger,
            loop=loop,
            clock=clock,
            msgbus=msgbus,
            cache=cache,
            report_timeout_seconds=config.report_timeout_seconds,
        )
