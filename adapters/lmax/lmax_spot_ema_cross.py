from decimal import Decimal

from dotenv import dotenv_values

from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveExecEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from pytower.adapters.lmax.config import LmaxDataClientConfig
from pytower.adapters.lmax.config import LmaxExecClientConfig
from pytower.adapters.lmax.config import LmaxFixClientConfig
from pytower.adapters.lmax.config import LmaxXmlClientConfig
from pytower.adapters.lmax.factories import LmaxLiveDataClientFactory
from pytower.adapters.lmax.factories import LmaxLiveExecClientFactory
from pytower.strategies.ema_cross_forecast import EMACrossForecast
from pytower.strategies.ema_cross_forecast import EMACrossForecastConfig


# Configure the trading node
config_node = TradingNodeConfig(
    trader_id="TESTER-001",
    logging=LoggingConfig(log_level="DEBUG"),
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_lookback_mins=1440,
        inflight_check_interval_ms=0,
    ),
    # cache_database=CacheDatabaseConfig(type="redis"),
    data_clients={
        "LMAX": LmaxDataClientConfig(
            xml_client=LmaxXmlClientConfig(
                hostname="https://web-order.london-demo.lmax.com",
                username=dotenv_values()["username"],
                password=dotenv_values()["password"],
            ),
            fix_client=LmaxFixClientConfig(
                hostname="fix-marketdata.london-demo.lmax.com",
                username=dotenv_values()["username"],
                password=dotenv_values()["password"],
                target_comp_id="LMXBDM",
            ),
            instrument_provider=InstrumentProviderConfig(load_all=True),
        ),
    },
    exec_clients={
        "LMAX": LmaxExecClientConfig(
            xml_client=LmaxXmlClientConfig(
                hostname="https://web-order.london-demo.lmax.com",
                username=dotenv_values()["username"],
                password=dotenv_values()["password"],
            ),
            fix_client=LmaxFixClientConfig(
                hostname="fix-order.london-demo.lmax.com",
                username=dotenv_values()["username"],
                password=dotenv_values()["password"],
                target_comp_id="LMXBD",
            ),
            instrument_provider=InstrumentProviderConfig(load_all=True),
        ),
    },
    timeout_connection=20.0,
    timeout_reconciliation=10.0,
    timeout_portfolio=10.0,
    timeout_disconnection=10.0,
    timeout_post_stop=5.0,
)

# Instantiate the node with a configuration
node = TradingNode(config=config_node)

# Configure your strategy
strat_config = EMACrossForecastConfig(
    instrument_id="EUR/USD.LMAX",
    # external_order_claims=["ETHUSDT.BINANCE"],
    bar_type="EUR/USD.LMAX-1-SECOND-BID-INTERNAL",
    fast_ema_period=1,
    slow_ema_period=200,
    trade_size=Decimal("0.010"),
    order_id_tag="001",
)
# Instantiate your strategy
strategy = EMACrossForecast(config=strat_config)

# Add your strategies and modules
node.trader.add_strategy(strategy)

# Register your client factories with the node (can take user defined factories)
node.add_data_client_factory("LMAX", LmaxLiveDataClientFactory)
node.add_exec_client_factory("LMAX", LmaxLiveExecClientFactory)
node.build()


# Stop and dispose of the node with SIGINT/CTRL+C
if __name__ == "__main__":
    try:
        node.run()
    finally:
        node.dispose()
