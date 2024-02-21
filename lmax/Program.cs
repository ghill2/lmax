using Com.Lmax.Api;
using Com.Lmax.Api.Order;
using Com.Lmax.Api.OrderBook;
using Com.Lmax.Api.MarketData;
using Com.Lmax.Api.Account;
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
using System;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Text.Json;
using System;
using System.Text.Json;
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using System;
using System.Threading;
using Com.Lmax.Api.Account;

namespace Lmax;

public class Program

{
    public LmaxSession lmax = new LmaxSession();
    public JsonParser jsonParser = new JsonParser();
    static ISession _session = null;
    static private long _nextHeartbeatId;
    static async Task Main(string[] args) {
        
        Console.WriteLine("Hello World!...");
        LmaxApi lmaxApi = new LmaxApi("https://web-order.london-demo.lmax.com");
        LoginRequest loginRequest = new LoginRequest("ghill2", "QVZJQqu8909");
        lmaxApi.Login(loginRequest, LoginCallback, FailureCallback("log in"));
    }
    
    static private void HeartbeatEvent(String token)
    {
        Console.WriteLine("Received heartbeat: {0}", token);
    }

    static void LoginCallback(ISession session) {
        _session = session;
        Console.WriteLine("Logged in, account ID: " + session.AccountDetails.AccountId);
        
        // _session.HeartbeatReceived += HeartbeatEvent;
        // _session.Subscribe(new HeartbeatSubscriptionRequest(),
        //                     () => Console.WriteLine("Subscribed to heartbeat"),
        //                     FailureCallback("subscribe to heartbeats"));
        
        // string token = "token-" + _nextHeartbeatId++;
        // _session.RequestHeartbeat(new HeartbeatRequest(token),
        //         () => Console.WriteLine("Successfully requested heartbeat: " + token),
        //         failureResponse => { throw new Exception("Failed"); });
        
        // session.OrderChanged += OnOrder;
        // session.Subscribe(
        //     new OrderSubscriptionRequest(),
        //     () => Console.WriteLine("OrderSubscriptionRequest successful"),
        //     failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse)
        // );

        


        // ---------------------------------------------------------------------
        // session.RequestAccountState(
        //         new AccountStateRequest(),
        //         () => Console.WriteLine("AccountStateRequest sent"),
        //         failureResponse => Console.Error.WriteLine("AccountStateRequest failed"));
        // session.AccountStateUpdated += OnAccountStateEvent;

        // session.Subscribe(new AccountSubscriptionRequest(),
        //         () => Console.WriteLine("Successful AccountSubscription subscription"),
        //         failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse));
        // ---------------------------------------------------------------------

        // string symbol = "EUR/USD";
        // session.SearchInstruments(
        //             new SearchRequest("", 0),
        //             SearchCallback,
        //             failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse));
        // TopOfBookHistoricMarketDataRequest request =
        //         new TopOfBookHistoricMarketDataRequest(
        //             1,
        //             100934,
        //             DateTime.Parse("2021-01-01"),
        //             DateTime.Parse("2022-01-01"),
        //             Format.Csv
        //         );
        // ---------------------------------------------------------------------
        AggregateHistoricMarketDataRequest request =
            new AggregateHistoricMarketDataRequest(
                    1,
                    100934,
                    DateTime.Parse("2020-05-11"),
                    DateTime.Parse("2020-05-15"),
                    Resolution.Day, Format.Csv,
                    Option.Bid
                    );
        session.HistoricMarketDataReceived += OnHistoricMarketData;
        session.Subscribe(
                new HistoricMarketDataSubscriptionRequest(),
                () => Console.WriteLine("Successful subscription"),
                failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse)
        );
        session.RequestHistoricMarketData(
                                        request,
                                        () => Console.WriteLine("Successful request"),
                                        failureResponse => Console.Error.WriteLine("Failed request: {0}", failureResponse)
                                        );

        session.OpenUri(
            new Uri("https://web-order.london-demo.lmax.com/marketdata/aggregate/100934/2020/05/2020-05-01-00-00-00-000-100934-bid-day-aggregation.csv.gz"),
            OnUriResponse,
            FailureCallback("open uri"));
        // ---------------------------------------------------------------------

        // session.Logout(
        //             () => Console.WriteLine("Logout successful"),
        //             failureResponse => Console.Error.WriteLine("Failed to Logout: {0}", failureResponse)
        //             );
        session.Start();
        
    }
    
    static void OnHistoricMarketData(string instructionId, List<Uri> uris)
    {
        Console.WriteLine("OnHistoricMarketData");
        _session.OpenUri(uris[0],
                        OnUriResponse,
                        failureResponse => Console.Error.WriteLine("Failed to open uri: {0}", failureResponse)
                        );
    }

    private static void OnUriResponse(Uri uri, BinaryReader reader)
    {
        using (var stream = new GZipStream(reader.BaseStream, CompressionMode.Decompress))
        {
            const int size = 1024;
            var buffer = new byte[size];
            var numBytes = stream.Read(buffer, 0, size);
            while (numBytes > 0)
            {
                Console.Write(Encoding.UTF8.GetString(buffer, 0, numBytes));
                numBytes = stream.Read(buffer, 0, size);
            }
        }
    }

    static private void SearchCallback(List<Instrument> instruments, bool hasMoreResults)
    {
        Console.WriteLine("Instruments Retrieved: {0}", instruments.Count);
    }
    static public void OnAccountStateEvent(AccountStateEvent accountStateEvent) {
        Console.WriteLine("Account state: {0}", accountStateEvent);
      
    }
    static OnFailure FailureCallback(string failedFunction) {
        return failureResponse => Console.Error.WriteLine("Failed to " + failedFunction + " due to: " + failureResponse.Message);
    }
    
    static void OnOrder(Order order) {
        Console.WriteLine(order.ToString());
    }

    // static async Task Main(string[] args) {
        
    //     Console.WriteLine("Hello World!...");
        
    //     Thread.CurrentThread.Name = "LMAXHttpServer";
    //     Program program = new Program();
    //     LmaxSession lmax = new LmaxSession();
    //     bool success = await lmax.Login("https://web-order.london-demo.lmax.com", "ghill2", "QVZJQqu8909");

    //     program.Listen().Wait();
        
    //     bool logMode = (args.Length > 0 && args[0] == "log");
    //     if (!logMode)  {
    //         program.Listen().Wait();
    //     }

    //     string logFilePath = "log.txt";
    //     using (var logStream = new StreamWriter(logFilePath, append: true)) {
    //         Console.SetOut(logStream);
    //         Console.SetError(logStream);
    //         try {
    //             program.Listen().Wait();
    //         } catch (Exception ex) {
    //             Console.Error.WriteLine("Exception: " + ex.Message);
    //         }
    //     }
        
    // }

    public async Task Listen() {
        Console.WriteLine("Server starting...");
        using (HttpListener listener = new HttpListener()) {
            listener.Prefixes.Add($"http://127.0.0.1:8081/");
            listener.Start();
            Console.WriteLine("Server started. Listening for incoming requests...");
            while (true) {
                HttpListenerContext ctx = await listener.GetContextAsync();
                await HandleRequest(ctx);
            }
        }
    }

    public async Task HandleRequest(HttpListenerContext ctx) {
        
        Dictionary<string, string> requestJson = jsonParser.Read(ctx);
        
        Console.WriteLine(requestJson);

        string path = ctx.Request.Url.AbsolutePath.TrimEnd(Convert.ToChar("/"));
        
        string responseJson = await HandleJson(path, requestJson);
        
        byte[] raw = Encoding.UTF8.GetBytes(responseJson);
        ctx.Response.ContentType = "application/json";
        ctx.Response.ContentLength64 = raw.Length;
        using (Stream stream = ctx.Response.OutputStream) {
            await stream.WriteAsync(raw, 0, raw.Length);
            stream.Close();
        }
    }
    
    private async Task<string> HandleJson(string path, Dictionary<string, string> json) {

        if (path.StartsWith("/logon")) {

            Console.WriteLine("Logging in...");
            bool success = await lmax.Login(json["host"], json["username"], json["password"]);
            // var _data = new Dictionary<string, object> {
            //     {"status": success}
            // };
            var data = new Dictionary<string, object> {
            
                { "status", success }
            };
            return jsonParser.Jsonify(data);
            

        } else if (path.StartsWith("/account/state")) {
            
            Console.WriteLine("Requesting account state...");
            AccountStateEvent _event = await lmax.accountProvider.RequestAccountState();
            return jsonParser.Jsonify(_event);

        } else if (path.StartsWith("/instrument")) {

            Console.WriteLine("Finding instrument...");
            Instrument instrument = await lmax.instrumentProvider.FindInstrument(json["symbol"]);
            return jsonParser.Jsonify(instrument);

        } else if (path.StartsWith("/account/details")) {

            Console.WriteLine("Requesting account state...");
            AccountDetails details = await lmax.accountProvider.RequestAccountDetails();
            return jsonParser.Jsonify(details);

        } else if (path.StartsWith("/orders")) {

            Console.WriteLine("Requesting orders...");
            List<Order> orders = lmax.orderProvider.orders;
            return jsonParser.Jsonify(orders);

        } else {

            return "";  // unhandled request

        }
        
    }
    
}

// async Task<object> HandleHistoricRequest(string path, Dictionary<string, string> json) {
            // } else if (path.StartsWith("/historic")) {
//         IHistoricMarketDataRequest request = null;
//         if (path.StartsWith("/historic/bar")) {
//             request = new TopOfBookHistoricMarketDataRequest(
//                 1,
//                 long.Parse(json["id"]),
//                 DateTime.Parse(json["start_date"]),
//                 DateTime.Parse(json["end_date"]),
//                 Format.Csv
//             );
//         }
//         else if (path.StartsWith("/historic/quotetick")) {
//             request = new AggregateHistoricMarketDataRequest(
//                         1,
//                         long.Parse(json["id"]),
//                         DateTime.Parse(json["start_date"]),
//                         DateTime.Parse(json["end_date"]),
//                         (Resolution)Enum.Parse(typeof(Resolution), json["resolution"], true),  // case insensitive
//                         Format.Csv,
//                         (Option)Enum.Parse(typeof(Option), json["option"], true)  // case insensitive
//                         );
//         }
        
//         if (request != null && path.EndsWith("raw")) {
//             return await lmax.dataProvider.ProcessRequestRaw(request);
//         } else {
//             return await lmax.dataProvider.ProcessRequest(request);
//         }
    
//     } else {
//         return "";
//     }

// }

// class Program
// {
//     static async Task Main(string[] args)
//     {
        
//         // Lmax lmax = new Lmax();
//         // lmax.Login();
//         // lmax.Listen();

//         HttpServer server = HttpServer();
        


//         await StartAsyncLoop();

//     }
    

//     static async Task StartAsyncLoop()
//     {
//         while (true)
//         {
//             await Task.Delay(1000);
//         }
//     }
// }

// class TradingBot
// {

//     private ISession _session;

//     void LoginCallback(ISession session)
//     {
//         Console.WriteLine("Logged in, account ID: " + session.AccountDetails.AccountId);
//         _session = session;
//         _session.HistoricMarketDataReceived += OnHistoricMarketData;
//         _session.Subscribe(new HistoricMarketDataSubscriptionRequest(),
//                         () => Console.WriteLine("Successful subscription"),
//                         failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse));

//         _session.RequestHistoricMarketData(new AggregateHistoricMarketDataRequest(1, 100934,
//                                                                                 DateTime.Parse("2011-05-11"),
//                                                                                 DateTime.Parse("2011-06-13"),
//                                                                                 Resolution.Day, Format.Csv,
//                                                                                 Option.Bid),
//                                         () => Console.WriteLine("Successful request"),
//                                         failureResponse => Console.Error.WriteLine("Failed request: {0}", failureResponse));

//         session.Start();
//     }

//     static OnFailure FailureCallback(string failedFunction)
//     {
//         return failureResponse => Console.Error.WriteLine("Failed to " + failedFunction + " due to: " + failureResponse.Message);
//     }

//     public static void Main(string[] args)
//     {
//         string url = "https://web-order.london-demo.lmax.com";
//         LmaxApi lmaxApi = new LmaxApi(url);
//         LoginRequest loginRequest = new LoginRequest("ghill2", "QVZJQqu8909");
//         lmaxApi.Login(loginRequest, LoginCallback, FailureCallback("log in"));
//     }

// }




                                    


// static async Task Main(string[] args)
// {
    
//     // Start the async loop
//     await StartAsyncLoop();
    
//     // The program will keep running as long as the async loop is active.
//     // You can add other code here if needed.
    
//     Console.WriteLine("Press any key to exit.");
//     Console.ReadKey();
// }

// static async Task StartAsyncLoop()
// {
//     while (true)
//     {
//         Console.WriteLine("Hello, World!");

//         string url = "https://web-order.london-demo.lmax.com";
//         LmaxApi lmaxApi = new LmaxApi(url);

//         LoginRequest loginRequest = new LoginRequest("ghill2", "QVZJQqu8909");
        
        
//         lmaxApi.Login(loginRequest, LoginCallback, FailureCallback("log in"));

//         // Delay the loop for a specified interval (e.g., 1 second).
//         await Task.Delay(1000);
//     }
// }

// static async Task StartAsyncLoop()
// {
//     while (true)
//     {
//         Console.WriteLine("Hello, World!");

//         string url = "https://web-order.london-demo.lmax.com";
//         LmaxApi lmaxApi = new LmaxApi(url);

//         // Delay the loop for a specified interval (e.g., 1 second).
//         await Task.Delay(1000);
//     }
// }

//

// Console.WriteLine(data);
        
        
        
        

        // // Loop over the values of the dictionary
        // // Split the string into lines using Environment.NewLine or "\n"
        // string[] lines = text.Split(new string[] { Environment.NewLine, "\n" }, StringSplitOptions.None);

        // // Loop over the lines and print them
        // foreach (string line in lines)
        // {
        //     Console.WriteLine(line);
        // }

        // foreach (string value in _data.Values)
        // {
        //     Console.WriteLine(value);
            

        // }
            
        // string input = "1.2 3.4 5.6 7.8"; // Example input text with space-separated doubles

        // string[] elements = input.Split(' '); // Split the input text by spaces
        // double[] numbers = new double[elements.Length];

        // for (int i = 0; i < elements.Length; i++)
        // {
        //     double.TryParse(elements[i], out numbers[i]); // Convert each element to double
        // }






//         class Program
// {
    
//     static async Task Main(string[] args)
//     {
        
//         // Set up the IP address and port number for the server
//         IPAddress ipAddress = IPAddress.Parse("127.0.0.1"); // Localhost
//         int port = 8080;

//         // Create a TCP/IP socket
//         TcpListener listener = new TcpListener(ipAddress, port);

//         // Lmax lmax = new Lmax();
//         // lmax.Login();
//         // lmax.Listen();
        
//         // string data = await lmax.RequestMarketData();
//         // byte[] bytesToSend = Encoding.UTF8.GetBytes(dataToSend);

//         // await StartAsyncLoop();
        
//         try
//         {
//             // Add the base URL to listen to (you can specify multiple prefixes if needed)
//             listener.Prefixes.Add($"http://{ipAddress}:{port}/");
//                 AddRoute(listener, "/historic", HandleHistoricRequest);
//             listener.Start();

//             Console.WriteLine("Server started. Listening for incoming connections...");

//             while (true)
//             {
//                 // Accept a pending connection request asynchronously
//                 TcpClient client = await listener.AcceptTcpClientAsync();

//                 // Handle the incoming client connection asynchronously
//                 _ = HandleClientAsync(client);
//             }
//         }
//         catch (Exception ex)
//         {
//             Console.WriteLine("Error: " + ex.Message);
//         }
//         finally
//         {
//             // Stop listening and clean up
//             listener.Stop();
//             Console.WriteLine("Server stopped.");
//         }

//     }
    
//     static void ProcessRequest(HttpListenerContext context)
//     {
//         // Prepare the response message as bytes
//         string responseMessage = "Hello, client!";
//         byte[] data = Encoding.UTF8.GetBytes(responseMessage);

//         // Set the content type and content length headers in the response
//         context.Response.ContentType = "text/plain";
//         context.Response.ContentLength64 = data.Length;

//         // Write the bytes as the response
//         context.Response.OutputStream.Write(data, 0, data.Length);

//         // Close the response stream to send the response to the client
//         context.Response.OutputStream.Close();

//         // Close the context to indicate that we have finished processing the request
//         context.Response.Close();

//         Console.WriteLine("Response sent to client.");
//     }

// }


        // public static void Main(string[] args)
        // {
        //     Console.WriteLine("Hello World!...");
        // }

        // await program.Connect();
        // public async Task Connect() {
        //     lmax.Start();
        //     Listen();
        // }
        // Dictionary<string, object> data = await program.lmax.instrumentProvider.FindInstrument("EUR/USD");
        
        // Console.WriteLine(json);
        // Dictionary<string, object> data = await program.lmax.accountProvider.RequestAccountState();
        
        // TopOfBookHistoricMarketDataRequest request =
        //         new TopOfBookHistoricMarketDataRequest(
        //             1,
        //             100934,
        //             DateTime.Parse("2021-01-01"),
        //             DateTime.Parse("2022-01-01"),
        //             Format.Csv
        //         );
        
        // AggregateHistoricMarketDataRequest request =
        //     new AggregateHistoricMarketDataRequest(
        //             1,
        //             100934,
        //             DateTime.Parse("2020-05-11"),
        //             DateTime.Parse("2020-05-15"),
        //             Resolution.Day, Format.Csv,
        //             Option.Bid
        //             );

        // Dictionary<string, System.Array> data = await program.lmax.dataProvider.ProcessRequest(request);
        // string json = JsonSerializer.Serialize(data, JSON_OPTIONS);
        // Console.WriteLine(json);
        // string text = await program.HandleHistoric(json);
        // Console.WriteLine(text);

        // Process the request and route to the appropriate handler
        
        // Send Response
        // ctx.Response.StatusCode = (int)HttpStatusCode.NotFound;
        // ctx.Response.Close();