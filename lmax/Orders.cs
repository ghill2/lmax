using System;
using System.Collections.Generic;
using Com.Lmax.Api.Order;
using Com.Lmax.Api;

public class OrderProvider
{
    
    public ISession _session = null;

    public OrderProvider(ISession session)
    {
        _session = session;
    }

    public List<Order> orders = new List<Order>();
    
    public void Subscribe() {
        _session.OrderChanged += OnOrder;
        _session.Subscribe(
            new OrderSubscriptionRequest(),
            () => Console.WriteLine("OrderSubscriptionRequest successful"),
            failureResponse => Console.Error.WriteLine("Failed to subscribe: {0}", failureResponse)
        );
    }
    
    private void OnOrder(Order order) {
        Console.WriteLine(order.ToString());
        orders.Append(order);
    }
    
    // self._session.AccountStateUpdated += OnAccountStateEvent(self._on_account_state)
    // self._session.Subscribe(AccountSubscriptionRequest(), on_success, on_failure)
}