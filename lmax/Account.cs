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
using Com.Lmax.Api.Account;
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using System;
using System.Text.Json;
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json;
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

public class AccountProvider
{
    public ISession _session = null;
    private AccountStateEvent _event = null;
    
    public AccountProvider(ISession session) {
        _session = session;

        _session.AccountStateUpdated += OnAccountStateEvent;
        session.Subscribe(new AccountSubscriptionRequest(),
                () => Console.WriteLine("Successful AccountSubscriptio subscription"),
                failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse));
    }
    
    public async Task<AccountStateEvent> RequestAccountState() {

        _event = null;
        
        _session.RequestAccountState(
                new AccountStateRequest(),
                () => Console.WriteLine("AccountStateRequest sent"),
                failureResponse => Console.Error.WriteLine("AccountStateRequest failed"));
        Console.WriteLine("Successful subscription");
        while (_event == null) {
            await Task.Yield();
            await Task.Delay(100);
        }
        Console.WriteLine("AccountState completed");
        Console.WriteLine("Account state: {0}", _event.ToString());

        return _event;

    }

    public async Task<AccountDetails> RequestAccountDetails() {
        return _session.AccountDetails;
    }

    public void OnAccountStateEvent(AccountStateEvent accountStateEvent) {
        // Console.WriteLine("Account state: {0}", accountStateEvent);
        _event = accountStateEvent;
    }

}