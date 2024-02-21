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

public class LmaxSession
{
    public ISession session = null;
    // public HistoricDataProvider dataProvider = null;  // TODO
    public InstrumentProvider instrumentProvider = null;
    public AccountProvider accountProvider = null;
    public OrderProvider orderProvider = null;
    
    public async Task<bool> Login(string hostname, string username, string password) {

        if (session == null) {

            Console.WriteLine("Logging in...");
            // string url = "https://web-order.london-demo.lmax.com";
            LmaxApi lmaxApi = new LmaxApi(hostname);
            LoginRequest loginRequest = new LoginRequest(username, password);
            lmaxApi.Login(loginRequest, LoginCallback, FailureCallback("log in"));
            while (session == null) {
                await Task.Delay(100);
                await Task.Yield();
            }

            // dataProvider = new HistoricDataProvider(session);  // TODO
            instrumentProvider = new InstrumentProvider(session);
            accountProvider = new AccountProvider(session);
            orderProvider = new OrderProvider(session);
            orderProvider.Subscribe();

            Task.Run(() => session.Start());

            while (session.IsRunning == false) {
                await Task.Delay(100);
                await Task.Yield();
            }
            Console.WriteLine("Listening...");
            
        } else {
            Console.WriteLine("Already logged on...");
        }

        return session.IsRunning;
    }
        
    private void LoginCallback(ISession _session) {
        Console.WriteLine("Logged in, account ID: " + _session.AccountDetails.AccountId);
        session = _session;
    }

    static OnFailure FailureCallback(string failedFunction) {
        return failureResponse => Console.Error.WriteLine("Failed to " + failedFunction + " due to: " + failureResponse.Message);
    }
    
}