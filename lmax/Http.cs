// #pragma warning disable
// using Com.Lmax.Api;
// using Com.Lmax.Api.Order;
// using Com.Lmax.Api.OrderBook;
// using Com.Lmax.Api.MarketData;
// using System;
// using System.Threading.Tasks;
// using MessagePack;
// using System.IO.Compression;
// using System.Text;
// using System.Collections.Generic;
// using System.Net;
// using System.Net.Sockets;
// using System.Threading.Tasks;
// using System;
// using System.Net;
// using System.Text;

// class HttpServer
// {
//     static void Main()
//     {
//         // Set up the IP address and port number for the server
//         IPAddress ipAddress = IPAddress.Parse("127.0.0.1"); // Localhost
//         int port = 8080;

//         // Create an HTTP listener
//         using (HttpListener listener = new HttpListener())
//         {
//             // Add the base URL to listen to (you can specify multiple prefixes if needed)
//             listener.Prefixes.Add($"http://{ipAddress}:{port}/");

//             // Start listening for incoming HTTP requests
//             listener.Start();

//             Console.WriteLine("Server started. Listening for incoming requests...");

//             while (true)
//             {
//                 // Wait for an incoming request
//                 HttpListenerctx ctx = listener.Getctx();

//                 // Process the request and route to the appropriate handler
//                 string path = ctx.Request.Url.AbsolutePath.TrimEnd("/");
//                 Console.WriteLine(path);
//                 if (path == "/historic")
//                 {
//                     Console.WriteLine("Received Historic Request");
//                     string responseMessage = "Hello, client!";
//                     byte[] data = Encoding.UTF8.GetBytes(responseMessage);

//                     ctx.Response.ContentType = "text/plain";
//                     ctx.Response.ContentLength64 = data.Length;
//                     ctx.Response.OutputStream.Write(data, 0, data.Length);
//                     ctx.Response.OutputStream.Close();

//                     Console.WriteLine("Response sent to client for /historic route.");
//                 }
//                 else
//                 {
//                     HandleNotFound(ctx);
//                 }
//             }

//         }

//         static void HandleNotFound(HttpListenerctx ctx)
//         {
//             ctx.Response.StatusCode = (int)HttpStatusCode.NotFound;
//             ctx.Response.Close();
//         }

//     }

// }