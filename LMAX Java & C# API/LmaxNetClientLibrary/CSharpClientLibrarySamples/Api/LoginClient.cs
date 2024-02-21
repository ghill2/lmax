using System;
using System.Collections.Generic;
using System.Threading;
using Com.Lmax.Api.Order;
using Com.Lmax.Api.OrderBook;

namespace Com.Lmax.Api
{
    class LoginClient
    {
        private ISession _session;
        private readonly List<string> _orderInstructions = new List<string>();
        private readonly long _instrumentId;
        private int _nextInstructionId = new Random().Next();

        private LoginClient(long instrumentId)
        {
            _instrumentId = instrumentId;
        }

        private void MarketDataUpdate(OrderBookEvent orderBookEvent)
        {
            long placeOrderInstructionId = _nextInstructionId++;
            _orderInstructions.Add(placeOrderInstructionId.ToString());
            _session.PlaceLimitOrder(new LimitOrderSpecification(placeOrderInstructionId.ToString(), _instrumentId, 10m, 10m, TimeInForce.GoodForDay),
                                     instructionId => Console.WriteLine("limit order placed with instruction id " + instructionId),
                                     FailureCallback("place limit order for instruction id " + placeOrderInstructionId));            
        }

        private void ClosePositionCreatedBy(Execution execution)
        {            
            long closeOutOrderInstructionId = _nextInstructionId++;
            _orderInstructions.Add(closeOutOrderInstructionId.ToString());
            _session.PlaceClosingOrder(new ClosingOrderSpecification(closeOutOrderInstructionId.ToString(), execution.Order.InstrumentId, -execution.Quantity),
                                       instructionId => Console.WriteLine("closing order placed with instruction id " + closeOutOrderInstructionId),
                                       FailureCallback("place closing order for instruction id " + closeOutOrderInstructionId));
        }

        private void LoginCallback(ISession session)
        {
            Console.WriteLine("My accountId is: " + session.AccountDetails.AccountId);

            _session = session;
            _session.MarketDataChanged += MarketDataUpdate;
            _session.OrderExecuted += ClosePositionCreatedBy;

            _session.Subscribe(new OrderBookSubscriptionRequest(_instrumentId),
                               () => Console.WriteLine("Subscribed to " + ("instrument: " + _instrumentId)),
                               FailureCallback("subscribe to order book " + _instrumentId));
            _session.Subscribe(new ExecutionSubscriptionRequest(),
                               () => Console.WriteLine("Subscribed to execution reports"),
                               FailureCallback("subscribe to execution reports"));

            _session.Start();
        }

        private static OnFailure FailureCallback(string failedFunction)
        {
            return failureResponse =>
                Console.Error.WriteLine("Failed to " + failedFunction + " due to: " + failureResponse.Message);
        }

        public static void Main(string[] args)
        {
            LoginClient loginClient = new LoginClient(4001);

            String url = "https://web-order.london-demo.lmax.com/";
            String username = "john";
            String password = "demopassword";
            ProductType productType = ProductType.CFD_DEMO;

            LmaxApi lmaxApi = new LmaxApi(url);
            lmaxApi.Login(new LoginRequest(username, password, productType), loginClient.LoginCallback, FailureCallback("log in"));
        }
    }

}
