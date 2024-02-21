from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.config.common import NautilusConfig


class LmaxXmlClientConfig(NautilusConfig, frozen=True, kw_only=True):
    hostname: str
    username: str
    password: str


class LmaxFixClientConfig(NautilusConfig, frozen=True, kw_only=True):
    hostname: str
    username: str
    password: str
    target_comp_id: str
    heartbeat_frequency_seconds: int = 30
    logon_timeout_seconds: int = 10


class LmaxExecClientConfig(LiveExecClientConfig, frozen=True, kw_only=True):
    xml_client: LmaxXmlClientConfig
    fix_client: LmaxFixClientConfig
    instrument_provider: InstrumentProviderConfig = None
    report_timeout_seconds: int = 5


class LmaxDataClientConfig(LiveDataClientConfig, frozen=True, kw_only=True):
    xml_client: LmaxXmlClientConfig
    fix_client: LmaxFixClientConfig
    instrument_provider: InstrumentProviderConfig = None
