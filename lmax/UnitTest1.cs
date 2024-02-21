
// // https://github.com/dotnet/samples/tree/main/core/getting-started/unit-testing-using-mstest
// using Lmax;
// using Microsoft.VisualStudio.TestTools.UnitTesting;

// namespace Lmax.Tests
// {
//     [TestClass]
//     public class TestClass1
//     {

//         // public TestContext TestContext { get; set; }

//         [TestMethod]
//         public async Task TestMethod1()
//         {
//             // TestContext.WriteLine("GOT TO HERE");
//             Program program = new Program();
//             program.lmax.Start();
//             Dictionary<string, string> json = new Dictionary<string, string>
//                 {
//                     { "id", "100934" },
//                     { "start_date", "2021-05-01" },
//                     { "end_date", "2021-05-07" }
//                 };
//             string text = await program.HandleHistoricJson(json);
//             // Console.WriteLine(text);
            
//         }
//     }
// }
