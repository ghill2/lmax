// using Com.Lmax.Api;
// using Com.Lmax.Api.Order;
// using Com.Lmax.Api.OrderBook;
// using Com.Lmax.Api.MarketData;
// using System;
// using System.Threading.Tasks;
// using System.IO.Compression;
// using System.Text;
// using System.Collections.Generic;
// using System.Net;
// using System.Net.Sockets;
// using System.Threading.Tasks;
// using System;
// using System.Net;
// using System.Text;
// using System.Globalization;
// using System.IO;
// using CsvHelper;
// using CsvHelper.Configuration;
// using System.Data;
// using System;
// using System.IO;
// using Microsoft.VisualBasic.FileIO;
// using System.Diagnostics;

// public class DataChunk {}
// public class TopOfBookChunk : DataChunk {
//     // TIMESTAMP,BID_PRICE_1,BID_QTY_1,ASK_PRICE_1,ASK_QTY_1
//     // 1622040030550,39292.76,5,39297.76,4.99
//     public System.Array<ulong?> = timestamp;
//     public System.Array<ulong?> = bid_price;
//     public System.Array<ulong?> = bid_quantity;
//     public System.Array<ulong?> = ask_price;
//     public System.Array<ulong?> = ask_quantity;

//     public TopOfBookChunk(ulong?[] _timestamp,
//                             double[] _bid_price,
//                             string[] arr3,
//                             bool[] arr4) {
//         timestamp = _timestamp;
//         array2 = arr2;
//         array3 = arr3;
//         array4 = arr4;
//     }
    
//     public Dictionary<string, System.Array> toDict() {
//         Dictionary<string, System.Array> data = new Dictionary<string, System.Array> {

//         };
//     };
//     public TopOfBookChunk fromArrays() {

//         TopOfBookChunk chunk = new TopOfBookChunk(
//             Array.ConvertAll<string, ulong?>(arrays[0].ToArray(), x => string.IsNullOrEmpty(x) ? null : ulong.Parse(x)
//         );

//         Dictionary<string, System.Array> data = new Dictionary<string, System.Array> {
//             { "BID_PRICE_1",
//                 Array.ConvertAll<string, double?>
//                     (BID_PRICE_1.ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//             )},
//             { "BID_QTY_1",
//                 Array.ConvertAll<string, double?>
//                     (BID_QTY_1.ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//             )},
//             { "ASK_PRICE_1",
//                 Array.ConvertAll<string, double?>
//                     (ASK_PRICE_1.ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//             )},
//             { "ASK_QTY_1",
//                 Array.ConvertAll<string, double?>
//                     (ASK_QTY_1.ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//             )},
//         };
//         return data;
//     }
// }
// public class HistoricDataProvider
// {
//     public ISession _session = null;
//     private List<Uri> _uris = null;
//     private SortedDictionary<string, string> _data = new SortedDictionary<string, string>();
    
//     // Constructor
//     public HistoricDataProvider(ISession session)
//     {
//         session.HistoricMarketDataReceived += OnHistoricMarketData;
//         session.Subscribe(
//                 new HistoricMarketDataSubscriptionRequest(),
//                 () => Console.WriteLine("Successful subscription"),
//                 failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse)
//         );

//         _session = session;
//     }
    
//     public async Task<DataChunk?> ProcessRequest(IHistoricMarketDataRequest request) {
        
//         string text = await ProcessRequestRaw(request);
//         if (text == null) {
//             return null;
//         }
        
//         // Parse to string dataframe
//         List<List<string>> df = new List<List<string>>();
        
//         string header;
//         using (StringReader reader = new StringReader(text)) {
//             header = reader.ReadLine();
//         }
//         for (int i = 0; i < header.Split(",").Length; i++) {
//             df.Add(new List<string>());
//         }
//         using (var parser = new TextFieldParser(new StringReader(text))) {
//             parser.TextFieldType = FieldType.Delimited;
//             parser.SetDelimiters(",");
//             parser.ReadLine();  // Skip the header row
//             while (!parser.EndOfData) {
//                 string[]? fields = parser.ReadFields();
//                 for (int i = 0; i < fields.Count(); i++) {
//                     string value = fields[i];
//                     df[i].Add(value);
//                 }
//             }
//         }
        
//         FourArrays customArrays = new FourArrays(arr1, arr2, arr3, arr4);

//         // Parse arrays
//         Dictionary<string, System.Array> data = new Dictionary<string, System.Array> {};

//         if (request is TopOfBookHistoricMarketDataRequest) {
//             // TIMESTAMP,BID_PRICE_1,BID_QTY_1,ASK_PRICE_1,ASK_QTY_1
//             // 1622040030550,39292.76,5,39297.76,4.99
            
//         } else if (request is AggregateHistoricMarketDataRequest) {
//             // INTERVAL_START_TIMESTAMP,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,UP_VOLUME,DOWN_VOLUME,UNCHANGED_VOLUME,UP_TICKS,DOWN_TICKS,UNCHANGED_TICKS
//             // 1588367100000,8930.55,9016.65,8813.4,8931.75,8256.34,6917.35,75.73,1654,1386,17
//             data = new Dictionary<string, System.Array> {
//                 { "TIMESTAMP",
//                     Array.ConvertAll<string, ulong?>
//                         (df[0].ToArray(), x => string.IsNullOrEmpty(x) ? null : ulong.Parse(x)
//                 )},
//                 { "OPEN_PRICE",
//                     Array.ConvertAll<string, double?>
//                         (df[1].ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//                 )},
//                 { "HIGH_PRICE",
//                     Array.ConvertAll<string, double?>
//                         (df[2].ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//                 )},
//                 { "LOW_PRICE",
//                     Array.ConvertAll<string, double?>
//                         (df[3].ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//                 )},
//                 { "CLOSE_PRICE",
//                     Array.ConvertAll<string, double?>
//                         (df[4].ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//                 )},
//                 { "UP_VOLUME",
//                     Array.ConvertAll<string, double?>
//                         (df[5].ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//                 )},
//                 { "DOWN_VOLUME",
//                     Array.ConvertAll<string, double?>
//                         (df[6].ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//                 )},
//                 { "UNCHANGED_VOLUME",
//                     Array.ConvertAll<string, double?>
//                         (df[7].ToArray(), x => string.IsNullOrEmpty(x) ? null : double.Parse(x)
//                 )},
//                 { "UP_TICKS",
//                     Array.ConvertAll<string, ulong?>
//                         (df[8].ToArray(), x => string.IsNullOrEmpty(x) ? null : ulong.Parse(x)
//                 )},
//                 { "DOWN_TICKS",
//                     Array.ConvertAll<string, ulong?>
//                         (df[9].ToArray(), x => string.IsNullOrEmpty(x) ? null : ulong.Parse(x)
//                 )},
//                 { "UNCHANGED_TICKS",
//                     Array.ConvertAll<string, ulong?>
//                         (df[10].ToArray(), x => string.IsNullOrEmpty(x) ? null : ulong.Parse(x)
//                 )},
//             };
            
//         }
        
//         int firstLength = data.Values.First().Length;
//         bool equalLength = data.Values.All(arr => arr.Length == firstLength);
//         Debug.Assert(equalLength, "The arrays should be equal length");

//         return data;
//     }

//     public async Task<string?> ProcessRequestRaw(IHistoricMarketDataRequest request) {
//         Console.WriteLine("processing...");
//         _uris = null;
//         _data.Clear();
            
//         _session.RequestHistoricMarketData(request,
//                                         () => Console.WriteLine("Successful request"),
//                                         failureResponse => Console.Error.WriteLine("Failed request: {0}", failureResponse)
//                                         );

//         Console.WriteLine("uris not null, proceeding...");
        
//         while (_uris == null) {
//             // await Task.Delay(500);
//             await Task.Yield();
//         }
//         if (_uris.Count == 0) {
//             Console.WriteLine("No data available...");
//             return null;
//         }
//         foreach (var uri in _uris)
//         {
//             Console.WriteLine(uri.AbsoluteUri);
//         }

//         foreach (Uri uri in _uris) {
//             Console.WriteLine(uri.AbsoluteUri);
//             _session.OpenUri(uri,
//                         OnUriResponse,
//                         failureResponse => Console.Error.WriteLine("Failed to open uri: {0}", failureResponse)
//                         );
//         }

//         Console.WriteLine(_uris.Count);
//         while (_data.Count != _uris.Count) {
//             Console.WriteLine("Waiting for data...");
//             await Task.Yield();
//             await Task.Delay(500);
//         }
        
//         string header = null;
//         string text = null;
//         foreach (string value in _data.Values) {
//             using (StringReader reader = new StringReader(value))
//             {
//                 header = reader.ReadLine();
//                 text += reader.ReadToEnd();
//             }
//         }
//         char[] newLineChars = { '\n', '\r' };
//         text = text.TrimStart(newLineChars).TrimEnd(newLineChars);
//         text = header + "\n" + text;
        
//         return text;

//     }

//     void OnHistoricMarketData(string instructionId, List<Uri> uris)
//     {
//         Console.WriteLine("OnHistoricMarketData");
//         _uris = uris;
//     }

//     void OnUriResponse(Uri uri, BinaryReader reader)
//     {
//         Console.WriteLine("OnUriResponse" + uri.AbsoluteUri);
//         using (var stream = new GZipStream(reader.BaseStream, CompressionMode.Decompress))
//         {

//             int size = 1024;
//             byte[] buffer = new byte[size];
//             StringBuilder data = new StringBuilder();
            
//             int numBytes = stream.Read(buffer, 0, size);
//             while (numBytes > 0)
//             {
//                 data.Append(Encoding.UTF8.GetString(buffer, 0, numBytes));
//                 numBytes = stream.Read(buffer, 0, size);
//             }
            
//             string key = uri.LocalPath;
            
//             if (_data.ContainsKey(key)) {
//                 throw new DivideByZeroException("Cannot divide by zero.");
//             }
//             _data.Add(key, data.ToString());
            
//         }
//     }

// }

// // using (var parser = new TextFieldParser(new StringReader(csvText)))
//             // {
//             //     parser.TextFieldType = FieldType.Delimited;
//             //     parser.SetDelimiters(",");

//             //     while (!parser.EndOfData)
//             //     {
//             //         string[] fields = parser.ReadFields();
//             //         int?[] numericArray = Array.ConvertAll(fields, int.TryParse);

//             //         // Print the parsed array
//             //         string joinedValues = string.Join(", ", numericArray.Select(val => val?.ToString() ?? "null"));
//             //         Console.WriteLine(joinedValues);
//             //     }
//             // }

//             // using (var parser = new TextFieldParser(new StringReader(data)))
//             // {
//             //     parser.TextFieldType = FieldType.Delimited;
//             //     parser.SetDelimiters(",");
                
//             //     List<long?> TIMESTAMP = List<long?>();
//             //     List<double?> BID_PRICE_1 = List<double?>();
//             //     List<long?> BID_QTY_1 = List<long?>();
//             //     List<double?> ASK_PRICE_1 = List<double?>();
//             //     List<long?> ASK_QTY_1 = List<long?>();

//             //     while (!parser.EndOfData)
//             //     {

//             //         string[] fields = parser.ReadFields();
//             //         TIMESTAMP.add(string.IsNullOrEmpty(fields[0]) ? null : fields[0])
//             //         BID_PRICE_1.add(string.IsNullOrEmpty(fields[1]) ? null : fields[1])
//             //         BID_QTY_1.add(string.IsNullOrEmpty(fields[2]) ? null : fields[2])
//             //         ASK_PRICE_1.add(string.IsNullOrEmpty(fields[3]) ? null : fields[3])
//             //         ASK_QTY_1.add(string.IsNullOrEmpty(fields[4]) ? null : fields[4])
//             //     }

//             // }

//             // using (var reader = new StreamReader("path\\to\\file.csv"))
//             // using (StringReader reader = new StringReader(data))
//             // using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
//             // {
//             //     // csv.Configuration.DefaultReadFields = null; // Set missing fields to null
//             //     using (var dr = new CsvDataReader(csv))
//             //     {
//             //         var dt = new DataTable();
//             //         dt.Columns.Add("TIMESTAMP", typeof(System.Nullable<long>));
//             //         dt.Columns.Add("BID_PRICE_1", typeof(System.Nullable<double>));
//             //         dt.Columns.Add("BID_QTY_1", typeof(System.Nullable<long>));
//             //         dt.Columns.Add("ASK_PRICE_1", typeof(System.Nullable<double>));
//             //         dt.Columns.Add("ASK_QTY_1", typeof(System.Nullable<long>));
//             //         dt.Load(dr);
//             //     }
//             // }
//             // Get header
//         // string header = null;
//         // string text = null;
//         // foreach (string text in _data.Values) {
//         //     using (StringReader reader = new StringReader(text))
//         //     {
//         //         header = reader.ReadLine();
//         //         text += reader.ReadToEnd();
//         //     }
//         // }
        
//         // Console.WriteLine(text[data.Length - 1] == Convert.ToChar("\n"));

//         // char[] newLineChars = { '\n', '\r' };
//         // text = data.TrimStart(newLineChars).TrimEnd(newLineChars);
        
//         // Console.WriteLine(text[data.Length - 1] == Convert.ToChar("\n"));
//         // Console.WriteLine("Last character: " + lastCharacter);
//         // Console.WriteLine(header);
//         // text = header + "\n" + text;
        