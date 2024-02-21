'panama' stitching method

creating backadjusted price series from multiple price series:
https://github.com/robcarver17/pysystemtrade/blob/master/sysinit/futures/adjustedprices_from_mongo_multiple_to_mongo.py

https://github.com/robcarver17/pysystemtrade/blob/master/sysinit/futures/multipleprices_from_arcticprices_and_csv_calendars_to_arctic.py
Creating multiple prices from contract prices

IB data limitations: if you are using ibapi or ib_insync, you need to buy the data plan

https://github.com/robcarver17/pysystemtrade/blob/master/data/futures/csvconfig/spreadcosts.csv
https://github.com/robcarver17/pysystemtrade/blob/master/data/futures/csvconfig/instrumentconfig.csv
https://github.com/robcarver17/pysystemtrade/blob/master/data/futures/csvconfig/rollconfig.csv

https://github.com/robcarver17/pysystemtrade/blob/281cc22fe8ec0ed8f7acf836b56411a7eb985047/sysobjects/adjusted_prices.py#L34

FUTURES:


FUTURES

pull backtesting database for daily prices - NOT PRIORITY
-threshold for data invalidation

daily IB data as TradeTicks into backtesting database
decide per instrument roll model for the contract's
create the backadjusted data for each instrument

how to backtest with future contract
-use moving average crossover for trade tick

master strategy with calculations for each sub strategy

config file of id of contract the instrument should be trading
backadjusting prices to current contract in the config file

--------------------------------------------
WHEN I GET BACK:

just return orders dicts and use fix to query, fix is more simple and don't know the WORKINGSTATES 
of the xml returned when requesting orders
just use xml for requesting historical data, account state, account details, instruments
"""
Is start and end date range important for reconciliation? = No, it's fine to get all open positions.
Is venue_order_id range important for reconciliation? = No, it's fine to get all open positions.

-----------------------------------------------------------------
Only called during reconciliation. Not implementing instrument_id, start, end filtering is fine. Reconciliation gets all by default.
LMAX DLL does not send an OrderEvent for closed orders, will not be able to implement open_only.

-----------------------------------------------------------------
Called in nautilus_trader.live.execution_client.LiveExecutionClient._query_order
    _query order is called when the ExecutionEngine receives a QueryOrder command
    QueryOrder object is used in live.execution_engine.LiveExecutionEngine._check_inflight_orders
    QueryOrder object is used in trading.strategy
    
async def generate_order_status_report(
        self,
        instrument_id: InstrumentId,
        client_order_id: Optional[ClientOrderId] = None,
        venue_order_id: Optional[VenueOrderId] = None,
    ) -> Optional[OrderStatusReport]:
    
Conclusion: filters required to be implemented for MVP to query a specific order.

-----------------------------------------------------------------
async def generate_order_status_reports(
        self,
        instrument_id: InstrumentId = None,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
        open_only: bool = False,
    ) -> list[OrderStatusReport]:
    
    Order{InstructionId: C-064,
        OriginalInstructionId: C-064,
        OrderId: AACkAgAAAABDQSwz,
        InstrumentId: 100934,
        AccountId: 1649599582,
        Price: 29303.01,
        StopLossOffset: ,
        StopProfitOffset: ,
        StopReferencePrice: 29303.01,
        Quantity: 0.01,
        FilledQuantity: 0,
        CancelledQuantity: 0,
        OrderType: LIMIT,
        Commission: 0,
        OpeningOrderId: C-064
        }
    
    <?xml version="1.0" ?>
    <order>
        <timeInForce>GoodTilCancelled</timeInForce>
        <instructionId>C-066</instructionId> = client_order_id
        <originalInstructionId>C-066</originalInstructionId>
        <orderId>AACkAgAAAABDQ5Pk</orderId>
        <accountId>001</accountId>
        <instrumentId>100934</instrumentId>
        <price>29203.01</price>
        <quantity>0.01</quantity>
        <matchedQuantity>0.01</matchedQuantity>
        <matchedCost>292.0301</matchedCost>
        <cancelledQuantity>0</cancelledQuantity>
        <timestamp>2023-08-15T17:13:02</timestamp>
        <orderType>STOP_COMPOUND_PRICE_LIMIT</orderType>
        <openQuantity>0.01</openQuantity>
        <openCost>292.0301</openCost>
        <cumulativeCost>292.0301</cumulativeCost>
        <commission>3</commission>
        <stopReferencePrice>29203.01</stopReferencePrice>
        <stopLossOffset/>
        <stopProfitOffset/>
        <workingState>UNKNOWN</workingState>
    </order>

    account_id : AccountId = accountId
    instrument_id : InstrumentId = get from provider from instrumentId (lmax_id)
    venue_order_id : VenueOrderId = orderId
        The reported order ID (assigned by the venue).
    order_side : OrderSide {``BUY``, ``SELL``} = quantity positive or negative
    order_type : OrderType = orderType
    time_in_force : TimeInForce = timeInForce
    order_status : OrderStatus = MISSING, static value? maybe workingState?
        The reported order status at the exchange.
    quantity : Quantity = quantity
        The reported order original quantity.
    filled_qty : Quantity = matchedQuantity
        The reported filled quantity at the exchange.
    report_id : UUID4
        The report ID.
    ts_accepted : uint64_t = timestamp
        The UNIX timestamp (nanoseconds) when the reported order was accepted.
    ts_last : uint64_t = missing from lmax, use ts_accepted?
        The UNIX timestamp (nanoseconds) of the last order status change.
    ts_init : uint64_t = self._clock.timestamp_ns
        The UNIX timestamp (nanoseconds) when the object was initialized.
    client_order_id : ClientOrderId, optional = instruction_id
        The reported client order ID.
    order_list_id : OrderListId, optional
        The reported order list ID associated with the order.
    contingency_type : ContingencyType, default ``NO_CONTINGENCY``
        The reported order contingency type.
    expire_time : datetime, optional
        The order expiration.
    price : Price, optional = 
        The reported order price (LIMIT).
    trigger_price : Price, optional
        The reported order trigger price (STOP).
    trigger_type : TriggerType, default ``NO_TRIGGER`` = None
    limit_offset : Decimal, optional
        The trailing offset for the order price (LIMIT).
    trailing_offset : Decimal, optional
        The trailing offset for the trigger price (STOP).
    trailing_offset_type : TrailingOffsetType, default ``NO_TRAILING_OFFSET``
        The order trailing offset type.
    avg_px : Decimal, optional = price
        The reported order average fill price.
    display_qty : Quantity, optional
        The reported order quantity displayed on the public book (iceberg).
    post_only : bool, default False
        If the reported order will only provide liquidity (make a market).
    reduce_only : bool, default False
        If the reported order carries the 'reduce-only' execution instruction.
    cancel_reason : str, optional
        The reported reason for order cancellation.
    ts_triggered : uint64_t, optional
        The UNIX timestamp (nanoseconds) when the object was initialized.
    
    commission = opencost

    Conclusion: Get all order_ids by subscribing to Order events using DLL, use commission and and OpeningOrderId (client_order_id)
                query each order with FIX to get create the OrderStatusReport.
                Implement without instrument_id, start, end, open_only filter for MVP.
                Call generate_order_status_report for each client_order_id returned from the DLL.
-----------------------------------------------------------------
Only called during reconciliation. Not implementing instrument_id, start, end filtering is fine. Reconciliation gets all by default.
async def generate_position_status_reports(
        self,
        instrument_id: Optional[InstrumentId] = None,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> list[PositionStatusReport]:
    
    FIX allows to filter by start and end time. DLL does not because there is no timestamp in a PositionEvent and OrderEvent does not have a timestamp.
    FIX allows to filter by venue_order_id. DLL does not because there is no order_id in a PositionEvent and OrderEvent does not have a timestamp.
    
    The fields to satisfy are:
    PositionStatusReport
         account_id : AccountId = accountId
         instrument_id : InstrumentId = instrumentId
         position_side : PositionSide {``FLAT``, ``LONG``, ``SHORT``} = openQuantity neg or pos
         quantity : Quantity = abs(openQuantity)
         ts_last : uint64_t  = 0 # not with FIX either
         venue_position_id : PositionId, optional


    account_id : AccountId
        The account ID for the report.
    instrument_id : InstrumentId
        The reported instrument ID for the position.
    position_side : PositionSide {``FLAT``, ``LONG``, ``SHORT``}
        The reported position side at the exchange.
    quantity : Quantity
        The reported position quantity at the exchange.
    report_id : UUID4
        The report ID.
    ts_last : int
        The UNIX timestamp (nanoseconds) of the last position change.
    ts_init : int
        The UNIX timestamp (nanoseconds) when the object was initialized.
    venue_position_id : PositionId, optional
        The reported venue position ID (assigned by the venue). If the trading
        venue has assigned a position ID / ticket for the trade then pass that
        here, otherwise pass ``None`` and the execution engine OMS will handle
        position ID resolution.

    <position>
            <accountId>001</accountId>
            <instrumentId>100934</instrumentId>
            <valuation>-396.1964</valuation>
            <shortUnfilledCost>0</shortUnfilledCost>
            <longUnfilledCost>0</longUnfilledCost>
            <openQuantity>0.04</openQuantity>
            <cumulativeCost>1179.0983</cumulativeCost>
            <openCost>1171.3796</openCost>
    </position>

    PositionEvent {
        AccountId: 1649599582,
        InstrumentId: 100934,
        ShortUnfilledCost: 0,
        LongUnfilledCost: 293.0301,
        OpenQuantity: 0.07,
        CumulativeCost: 2054.5568,
        OpenCost: 2056.9889
        }
                    
    DLL does not send venue_position_id and no way to query with DLL.
    Conclusion: FIX required, PositionEvent is missing the venue_position_id.
                The reconciliation needs the venue_position_id for hedging accounts.
                LMAX is netting by default so we don't need the venue_position_id
                Implement without instrument_id, start, end, filter for MVP.

-----------------------------------------------------------------
Only called during reconciliation. Not implementing instrument_id, start, end filtering is fine. Reconciliation gets all by default.
async def generate_trade_reports(
        self,
        instrument_id: Optional[InstrumentId] = None,
        venue_order_id: Optional[VenueOrderId] = None,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> list[TradeReport]:
    
    Conclusion: FIX required, DLL does not send PositionEvents/OrderEvents for closed positions/orders.
                Implement without instrument_id, start, end, filter for MVP.
    
    account_id : AccountId
        The account ID for the report.
    instrument_id : InstrumentId
        The reported instrument ID for the trade.
    venue_order_id : VenueOrderId
        The reported venue order ID (assigned by the venue) for the trade.
    trade_id : TradeId
        The reported trade match ID (assigned by the venue).
    order_side : OrderSide {``BUY``, ``SELL``}
        The reported order side for the trade.
    last_qty : Quantity
        The reported quantity of the trade.
    last_px : Price
        The reported price of the trade.
    liquidity_side : LiquiditySide {``NO_LIQUIDITY_SIDE``, ``MAKER``, ``TAKER``}
        The reported liquidity side for the trade.
    report_id : UUID4
        The report ID.
    ts_event : int
        The UNIX timestamp (nanoseconds) when the trade occurred.
    ts_init : int
        The UNIX timestamp (nanoseconds) when the object was initialized.
    client_order_id : ClientOrderId, optional
        The reported client order ID for the trade.
    venue_position_id : PositionId, optional
        The reported venue position ID for the trade. If the trading venue has
        assigned a position ID / ticket for the trade then pass that here,
        otherwise pass ``None`` and the execution engine OMS will handle
        position ID resolution.
    commission : Money, optional
        The reported commission for the trade (can be ``None``).
        
-----------------------------------------------------------------
AccountState conclusion:

    register and send account state on execution client start.
    keep account state subscription open to update nautilus account state.
"""









A CA file has been bootstrapped using certificates from the system
keychain. To add additional certificates, place .pem files in
  /usr/local/etc/openssl@3/certs

and run
  /usr/local/opt/openssl@3/bin/c_rehash

chmod 600 /usr/local/etc/stunnel/key.pem

https://www.stunnel.org/config_unix.html
https://www.stunnel.org/static/stunnel.html



https://www.youtube.com/watch?v=Big80AStHSU
file:///Users/g1/Downloads/LMAX%20FIX%204.4%20Package/LMAXFIX4.4TradingAPI/brokerFixTradingGateway.html#Instrument
https://www.youtube.com/watch?v=ecs5NMNdEoA&list=PLv-cA-4O3y95w5N01R_BDMw-7iiNwwDla&index=7
https://docs.oracle.com/javase/8/docs/technotes/guides/security/SunProviders.html
https://stackoverflow.com/questions/36082879/quickfix-j-enable-protocols-and-ciphersuite-setting
https://www.quickfixj.org/usermanual/2.3.0/usage/application.html
https://www.openssl.org/source/

https://www.openssl.org/source/fips-doc/openssl-3.0.8-security-policy-2023-05-05.pdf
Appendix A: Installation and Usage Guidance

make sure absolute path is set in the pem file
# How to install fips on macOS
download openssl-3.0.8 https://www.openssl.org/source/old/3.0/
cd openssl-3.0.8

make install_fips

sudo rm /usr/local/bin/stunnel && ./config fips darwin64-x86_64-cc enable-fips && make && sudo make install

# How to fix

[!] error queue: crypto/provider_core.c:904: error:07880025:common libcrypto routines::reason(524325)
[!] error queue: crypto/dso/dso_lib.c:152: error:12800067:DSO support routines::could not load the shared library
[!] error queue: crypto/dso/dso_dlfcn.c:118: error:12800067:DSO support routines::could not load the shared library
[!] error queue: crypto/provider_core.c:904: error:07880025:common libcrypto routines::reason(524325)
[!] error queue: crypto/dso/dso_lib.c:152: error:12800067:DSO support routines::could not load the shared library
[!] FIPS PROVIDER: crypto/dso/dso_dlfcn.c:118: error:12800067:DSO support routines::could not load the shared library



# 1 Build openssl source code with fips enabled
export OPENSSL_FIPS=1 && ./Configure enable-fips && make && sudo make install_fips

# 2 Build stunnel using the custom openssl with fips enabled
sudo rm -f /usr/local/bin/stunnel && export OPENSSL_FIPS=1 && ./configure --with-ssl=/Users/g1/Downloads/openssl-3.0.8/ && make && sudo make install

after there is a file README_FIPS.md

export OPENSSL_FIPS=1 &&  ./configure --with-ssl=/Users/g1/Downloads/openssl-3.0.8/

# Enable two lines in the openssl configuration file FIX:

[!] error queue: crypto/provider_core.c:932: error:078C0105:common libcrypto routines::init fail
[!] error queue: providers/fips/fipsprov.c:707: error:1C8000D8:Provider routines::self test post failure
[!] error queue: providers/fips/self_test.c:388: error:1C8000E0:Provider routines::fips module entering error state
[!] error queue: providers/fips/self_test.c:290: error:1C8000D5:Provider routines::missing config data
[!] error queue: crypto/provider_core.c:932: error:078C0105:common libcrypto routines::init fail
[!] error queue: providers/fips/fipsprov.c:707: error:1C8000D8:Provider routines::self test post failure
[!] error queue: providers/fips/self_test.c:388: error:1C8000E0:Provider routines::fips module entering error state
[!] FIPS PROVIDER: providers/fips/self_test.c:290: error:1C8000D5:Provider routines::missing config data

openssl version -d
.include /usr/local/ssl/fipsmodule.cnf
fips = fips_sect




## make sure fps test run
sudo /Users/g1/Downloads/openssl-3.0.8/apps/openssl fipsinstall -out /usr/local/ssl/fipsmodule.cnf -module /usr/local/lib/ossl-modules/fips.dylib

## otool output
/usr/local/bin/stunnel:
	/usr/local/lib/libssl.3.dylib (compatibility version 3.0.0, current version 3.0.0)
	/usr/local/lib/libcrypto.3.dylib (compatibility version 3.0.0, current version 3.0.0)
	/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1311.100.3)

stunnel links to these, they need to link to the other ssl version
/usr/local/lib/libssl.3.dylib
/usr/local/lib/libcrypto.3.dylib

--disable-libwrap
--enable-fips

# stunnel fips install notes
https://github.com/copiousfreetime/stunnel/blob/master/INSTALL.FIPS

# To check if fips is enabled for openssl:
The output should contain fips
openssl version

/etc/ssl/fipsmodule.cnf
/usr/local/bin/stunnel
/usr/local/bin/openssl
/usr/bin/openssl
/usr/local/lib/ossl-modules/fips.dylib
During the installation process, the OpenSSL FIPS Object Module will look for the necessary configuration data in this directory.

/usr/local/ssl/fips

/usr/bin/openssl
/usr/local/lib/libssl.3.dylib
/usr/local/lib//libcrypto.3.dylib

/Users/g1/Downloads/openssl-3.0.8/apps/openssl
/Users/g1/Downloads/openssl-3.0.8/libssl.3.dylib
/Users/g1/Downloads/openssl-3.0.8/libcrypto.3.dylib
/private/etc/ssl

/usr/local/etc/stunnel/stunnel.conf


/usr/local/ssl/openssl.cnf

openssl fipsinstall -out /usr/local/ssl/fipsmodule.cnf -module /usr/local/lib/ossl-modules/fips.dylib



sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mycert.pem -out mycert.pem

make install_fips output
created directory `/usr/local/ssl'
*** Installing FIPS module
install providers/fips.dylib -> /usr/local/lib/ossl-modules/fips.dylib
*** Installing FIPS module configuration
install providers/fipsmodule.cnf -> /usr/local/ssl/fipsmodule.cnf

deleted
/usr/local/bin/openssl

# print openssl directory with configuration files
openssl version -d

https://github.com/openssl/openssl/issues/17282#issuecomment-994938195


/usr/local/ssl/openssl.conf
# creating a .pem file
# error:0A00018F:SSL routines::ee key too small
sudo openssl req -x509 -newkey rsa:2048 -keyout stunnel.key -out stunnel.crt -days 365 -nodes
sudo cat stunnel.key stunnel.crt > stunnel.pem
sudo chmod 600 stunnel.crt stunnel.key stunnel.pem

# create a .pem file on macOS
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
openssl req -new -key private_key.pem -out certificate.csr
cat certificate.csr private_key.pem > combined.pem

# 
openssl req -newkey rsa:4096 -nodes -keyout stunnel.pem -x509 -days 365 -out stunnel.pem
openssl pkey -in stunnel.pem -out stunnel-fips.pem -aes256



# 
openssl req -newkey rsa:4096 -nodes -keyout stunnel.pem -x509 -days 365 -out
openssl req -new -key private.key -x509 -days 365 -out certificate.crt
cat private.key certificate.crt > stunnel.pem


# 
openssl genpkey -algorithm RSA -outform PEM -out private.key -pkeyopt rsa_keygen_bits:8192
openssl req -new -key private.key -x509 -days 365 -out certificate.crt
cat private.key certificate.crt > stunnel.pem

# 
openssl req -x509 -nodes -days 365  -newkey rsa:16384 -keyout ./private.pem -out certificate.pem



# How to build openssl source code with fips enabled
sudo rm /usr/local/bin/openssl && export OPENSSL_FIPS=1 && ./config fips darwin64-x86_64-cc enable-fips && make && sudo make install_fips

# [!] error queue: ssl/ssl_rsa.c:221: error:0A00018F:SSL routines::ee key too small
# securityLevel = 0



fips = fips_sect

[default_sect]
activate = 1
securityLevel=0

# 
# openssl genpkey -algorithm RSA -out private.key -pkeyopt rsa_keygen_bits:4096

openssl req -x509 -nodes -days 365  -newkey rsa:4096 -keyout ./private.pem -out certificate.pem
cat private.pem certificate.pem > stunnel.pem


"""
        It is not possible to get a timestamp value from the XML client.
        There is no way get open positions using FIX?
        Fix venue position id = tag 37

        Does LMAX report active positions with TradeCaptureReports?
        Yes, in addition to closed positions.

        Is there a way to filter closed position in TradeCaptureReports?

        Is there a way to tell difference between a closed and open position with TradeCaptureReports?
        Use XML to get currently open trade reports

        No way to fill in timestamp by getting fixtrade report because you can't get a trade report for 
        a specific order


        1) get trade reports
        
        Does LMAX make a dict xml for each position? YES

        Does LMAX make a trade report for each position?

        1) Get all trade reports

        2) Filter currently open trade reports.
        Position Report reconciliation stage:
            The reconciliation stage works with open positions? Not sure, the call to cache uses position() method which gets closed positions too.
            The reconilication matches the venue_position_id to a position in the cache and checks the quantity.
            If the quantity mismatches the reconciliation fails.
        """
        """
            1) get open instruction ids
            2) get trade reports
            3) match instruction ids to trade_reports to filter open positions
            
            
            """


            """
The client listens to FIX messages from the server

[Demo-Trading]
client = yes
accept = 127.0.0.1:40001
connect = fix-order.london-demo.lmax.com:443
sslVersion = TLSv1
options = NO_SSLv24
options = NO_SSLv3


https://github.com/gloryofrobots/fixsim/blob/master/fixsim/client.py
https://quickfixengine.org/c/documentation/
https://stocksharp.com/topic/11089/the-fix-protocol_-fix-message-architecture_/
https://github.com/darwinex/dwx-fix-connector/tree/master/python
https://github.com/HarukaMa/ctrader-fix-demo/blob/master/fix.py

/usr/local/etc/stunnel/stunnel.conf
https://gist.github.com/marshalhayes/ca9508f97d673b6fb73ba64a67b76ce8
https://datacenteroverlords.com/2012/03/01/creating-your-own-ssl-certificate-authority/

QuickFIX Documentation
https://www.quickfixj.org/usermanual/2.3.0/usage/configuration.html

https://github.com/quickfix/quickfix/blob/master/src/C%2B%2B/Message.h#L126
https://pypi.org/project/fixtrate/
https://github.com/jeromegit/fixations
https://github.com/quickfix/quickfix/blob/master/src/python/quickfix.i
"""