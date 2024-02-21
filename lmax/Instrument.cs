using Com.Lmax.Api;
using Com.Lmax.Api.Order;
using Com.Lmax.Api.OrderBook;
using Com.Lmax.Api.MarketData;
using System;
using System.Threading.Tasks;
using System.IO.Compression;
using System.Text;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Threading.Tasks;
using System;
using System.Net;
using System.Text;
/*
long id
string name
UnderlyingInfo underlying,
    string Symbol,
    string Isin
    string AssetClass
CalendarInfo calendar
    DateTime StartTime
    DateTime ExpiryTime
    TimeSpan Open
    TimeSpan Close
    string TimeZone
    List<DayOfWeek> TradingDays
RiskInfo risk
    decimal MarginRate
    decimal MaximumPosition
OrderBookInfo orderBook
    decimal PriceIncrement
    decimal QuantityIncrement
    decimal VolatilityBandPercentage
ContractInfo contract
    string Currency
    decimal UnitPrice
    string UnitOfMeasure
    string ContractSize
CommercialInfo commercial
    decimal MinimumCommission
    decimal? AggressiveCommissionRate
    decimal? PassiveCommissionRate
    decimal? AggressiveCommissionPerContract
    decimal? PassiveCommissionPerContract
    string FundingBaseRate
    int DailyInterestRateBasis
    decimal? FundingPremiumPercentage
    decimal? FundingReductionPercentage
    decimal? LongSwapPoints
    decimal? ShortSwapPoints
*/

public class InstrumentProvider
{
    public ISession _session = null;
    private List<Instrument>? _instruments = null;
    
    public InstrumentProvider(ISession session)
    {
        _session = session;
    }

    public async Task<Instrument?> FindInstrument(string symbol) {
        
        _instruments = null;
        _session.SearchInstruments(new SearchRequest(symbol, 0), SearchCallback, failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse));
        
        while (_instruments == null) {
            Console.WriteLine("Waiting for instruments...");
            await Task.Yield();
            await Task.Delay(100);
        }
        
        Console.WriteLine(
            string.Format("Found {0} instruments...", _instruments.Count)
        );
        
        if (_instruments.Count == 0) {
            Console.WriteLine("No matches...");
            return null;
        }

        Instrument instrument = _instruments[0];
        
        return instrument;
    }

    private void SearchCallback(List<Instrument> instruments, bool hasMoreResults)
    {
        Console.WriteLine("Instruments Retrieved: {0}", instruments);
        _instruments = instruments;
    }

}