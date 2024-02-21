using Com.Lmax.Api;
using Com.Lmax.Api.Order;
using Com.Lmax.Api.OrderBook;
using Com.Lmax.Api.MarketData;
using Com.Lmax.Api.Account;
using System;
using System.Threading.Tasks;
using System.IO.Compression;
using System.Text;
using System.Text.Json.Serialization;
using System.Text.Json;
using System.Collections.Generic;
using System.Net;
using System.Linq;
using System.Net.Sockets;

// namespace Lmax;

public class JsonParser
{

    public static JsonSerializerOptions JSON_OPTIONS = new JsonSerializerOptions {
        Converters = { new DecimalConverter() },
        WriteIndented = true,
    };

    public class DecimalConverter : JsonConverter<decimal> {
        public override decimal Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) {
            return 123.45m;
        }
        public override void Write(Utf8JsonWriter writer, decimal value, JsonSerializerOptions options) {
            writer.WriteStringValue(value.ToString());
        }
    }

    public Dictionary<string, string> Read(HttpListenerContext ctx) {
        // Deserialize the JSON data into a Dictionary<string, string> using System.Text.Json
        string json;
        using (Stream stream = ctx.Request.InputStream) {
        using (StreamReader reader = new StreamReader(stream, Encoding.UTF8)) {
            json = reader.ReadToEnd();
        }}
        return JsonSerializer.Deserialize<Dictionary<string, string>>(json);
    }
    
    public string Jsonify(object obj) {
        if (obj.GetType() == typeof(List<Order>)) {
            return Jsonify((List<Order>)obj);
        } else if (obj.GetType() == typeof(Instrument)) {
            return Jsonify((Instrument)obj);
        } else if (obj.GetType() == typeof(AccountStateEvent)) {
            return Jsonify((Instrument)obj);
            } else if (obj.GetType() == typeof(AccountDetails)) {
            return Jsonify((AccountDetails)obj);
        }
        return "";
    }
    
    public string Jsonify(Dictionary<string, object> data) {
        return JsonSerializer.Serialize(data, JSON_OPTIONS);
    }

    public string Jsonify(AccountStateEvent _event) {
        var data = new Dictionary<string, object> {
            { "AccountId", _event.AccountId },
            { "Balance", _event.Balance },
            { "Cash", _event.Cash },
            { "Credit", _event.Credit },
            { "AvailableToWithdraw", _event.AvailableToWithdraw },
            { "UnrealisedProfitAndLoss", _event.UnrealisedProfitAndLoss },
            { "Margin", _event.Margin },
            { "Wallets", _event.Wallets },
            { "NetOpenPositions", _event.NetOpenPositions }
        };
        return JsonSerializer.Serialize(data, JSON_OPTIONS);
    }

    public string Jsonify(AccountDetails details) {
        var data = new Dictionary<string, object> {
            { "AccountId", details.AccountId },
            { "Username", details.Username },
            { "Currency", details.Currency },
            { "LegalEntity", details.LegalEntity },
            { "DisplayLocale", details.DisplayLocale },
            { "FundingAllowed", details.FundingAllowed },
        };
        return JsonSerializer.Serialize(data, JSON_OPTIONS);
    }

    public static string Jsonify(List<Order> orders) {
        var data = new List<Dictionary<string, object>>();
        foreach (Order order in orders) {
            data.Add(
                new Dictionary<string, object> {
                    { "OriginalInstructionId", order.OriginalInstructionId },
                    { "OrderId", order.OrderId },
                    { "InstrumentId", order.InstrumentId },
                    { "AccountId", order.AccountId },
                    { "OrderType", order.OrderType.ToString() },
                    { "Quantity", order.Quantity },
                    { "FilledQuantity", order.FilledQuantity },
                    { "LimitPrice", order.LimitPrice },
                    { "StopPrice", order.StopPrice },
                    { "CancelledQuantity", order.CancelledQuantity },
                    { "StopLossOffset", order.StopLossOffset },
                    { "StopProfitOffset", order.StopProfitOffset },
                    { "StopReferencePrice", order.StopReferencePrice },
                    { "Commission", order.Commission },
                    { "TimeInForce", order.TimeInForce.ToString() },
                    { "OpeningOrderId", order.OpeningOrderId }
                }
            );
        }
        return JsonSerializer.Serialize(data, JSON_OPTIONS);
    }
    
    // private static JsonifyInstrument(Instrument instrument) {
    //     Dictionary<string, object> underlying = new Dictionary<string, object> {
    //         { "Symbol", instrument.Underlying.Symbol },
    //         { "Isin", instrument.Underlying.Isin },
    //         { "AssetClass", instrument.Underlying.AssetClass },
    //     };

    //     Dictionary<string, object> calendar = new Dictionary<string, object> {
    //         { "StartTime", instrument.Calendar.StartTime },
    //         { "ExpiryTime", instrument.Calendar.ExpiryTime },
    //         { "Open", instrument.Calendar.Open },
    //         { "Close", instrument.Calendar.Close },
    //         { "TimeZone", instrument.Calendar.TimeZone },
    //         { "TradingDays", instrument.Calendar.TradingDays },
    //     };

    //     Dictionary<string, object> risk = new Dictionary<string, object> {
    //         { "MarginRate", instrument.Risk.MarginRate },
    //         { "MaximumPosition", instrument.Risk.MaximumPosition },
    //     };

    //     Dictionary<string, object> orderBook = new Dictionary<string, object> {
    //         { "PriceIncrement", instrument.OrderBook.PriceIncrement },
    //         { "QuantityIncrement", instrument.OrderBook.QuantityIncrement },
    //         { "VolatilityBandPercentage", instrument.OrderBook.VolatilityBandPercentage },
    //     };

    //     Dictionary<string, object> contract = new Dictionary<string, object> {
    //         { "Currency", instrument.Contract.Currency },
    //         { "UnitPrice", instrument.Contract.UnitPrice },
    //         { "UnitOfMeasure", instrument.Contract.UnitOfMeasure },
    //         { "ContractSize", instrument.Contract.ContractSize },
    //     };

    //     Dictionary<string, object> commercial = new Dictionary<string, object> {
    //         { "MinimumCommission", instrument.Commercial.MinimumCommission },
    //         { "AggressiveCommissionRate", instrument.Commercial.AggressiveCommissionRate },
    //         { "PassiveCommissionRate", instrument.Commercial.PassiveCommissionRate },
    //         { "AggressiveCommissionPerContract", instrument.Commercial.AggressiveCommissionPerContract },
    //         { "PassiveCommissionPerContract", instrument.Commercial.PassiveCommissionPerContract },
    //         { "FundingBaseRate", instrument.Commercial.FundingBaseRate },
    //         { "DailyInterestRateBasis", instrument.Commercial.DailyInterestRateBasis },
    //         { "FundingPremiumPercentage", instrument.Commercial.FundingPremiumPercentage },
    //         { "FundingReductionPercentage", instrument.Commercial.FundingReductionPercentage },
    //         { "LongSwapPoints", instrument.Commercial.LongSwapPoints },
    //         { "ShortSwapPoints", instrument.Commercial.ShortSwapPoints },
    //     };

    //     Dictionary<string, object> json = new Dictionary<string, object> {
    //         { "Id", instrument.Id },
    //         { "Name", instrument.Name },
    //         { "Underlying", underlying },
    //         { "Calendar", calendar },
    //         { "Risk", risk },
    //         { "OrderBook", orderBook },
    //         { "Contract", contract },
    //         { "Commercial", commercial },
    //     };

    //     return json;

    // }

}



  
    // public string Write(object data) {
    //     Dictionary<string, object> json = new Dictionary<string, object>();
        
    //     object parsed = null;

    
        
        
    //     Dictionary<string, object>

    //     return JsonSerializer.Serialize(parsed, JSON_OPTIONS);
    // }


    