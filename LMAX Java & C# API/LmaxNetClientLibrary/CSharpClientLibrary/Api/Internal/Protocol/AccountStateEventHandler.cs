using System.Collections.Generic;
using Com.Lmax.Api.Internal.Events;

namespace Com.Lmax.Api.Internal.Protocol
{
    public class AccountStateEventHandler : DefaultHandler
    {
        public event OnAccountStateEvent AccountStateUpdated;

        private const string RootNodeName = "accountState";
        private const string AccountIdNodeName = "accountId";
        private const string BalanceNodeName = "balance";
        private const string CashNodeName = "cash";
        private const string CreditNodeName = "credit";
        private const string AvailableFundsNodeName = "availableFunds";
        private const string AvailableToWithdrawNodeName = "availableToWithdraw";
        private const string UnrealisedProfitAndLossNodeName = "unrealisedProfitAndLoss";
        private const string MarginNodeName = "margin";
        private const string ActiveNodeName = "active";

        private readonly WalletsHandler _walletsHandler = new WalletsHandler();

        public AccountStateEventHandler() : base(RootNodeName)
        {
            AddHandler(AccountIdNodeName);
            AddHandler(BalanceNodeName);
            AddHandler(CashNodeName);
            AddHandler(CreditNodeName);
            AddHandler(AvailableFundsNodeName);
            AddHandler(AvailableToWithdrawNodeName);
            AddHandler(UnrealisedProfitAndLossNodeName);
            AddHandler(MarginNodeName);
            AddHandler(_walletsHandler);
            AddHandler(ActiveNodeName);
        }

        public override void EndElement(string endElement)
        {
            if (AccountStateUpdated != null && RootNodeName.Equals(endElement))
            {
                long accountId;
                decimal balance;
                decimal cash;
                decimal credit;
                decimal availableFunds;
                decimal availableToWithdraw;
                decimal unrealisedProfitAndLoss;
                decimal margin;

                TryGetValue(AccountIdNodeName, out accountId);
                TryGetValue(BalanceNodeName, out balance);
                TryGetValue(CashNodeName, out cash);
                TryGetValue(CreditNodeName, out credit);
                TryGetValue(AvailableFundsNodeName, out availableFunds);
                TryGetValue(AvailableToWithdrawNodeName, out availableToWithdraw);
                TryGetValue(UnrealisedProfitAndLossNodeName, out unrealisedProfitAndLoss);
                TryGetValue(MarginNodeName, out margin);

                AccountStateBuilder accountStateBuilder = new AccountStateBuilder();
                accountStateBuilder.AccountId(accountId).Balance(balance).Cash(cash).Credit(credit).AvailableFunds(availableFunds).
                    AvailableToWithdraw(availableToWithdraw).UnrealisedProfitAndLoss(unrealisedProfitAndLoss).Margin(margin).
                    Wallets(_walletsHandler.GetAndResetWallets()).
                    NetOpenPositions(_walletsHandler.GetAndResetNetOpenPositions());

                AccountStateUpdated(accountStateBuilder.NewInstance());
            }
        }
    }

    internal class WalletsHandler : DefaultHandler
    {
        private const string RootNodeName = "wallet";
        private const string CurrencyNodeName = "currency";
        private const string BalanceNodeName = "balance";
        private const string NetOpenPositionNodeName = "netOpenPosition";
        private Dictionary<string, decimal> _wallets = new Dictionary<string, decimal>();
        private Dictionary<string, decimal> _netOpenPositions = new Dictionary<string, decimal>();

        public WalletsHandler()
            : base(RootNodeName)
        {
            AddHandler(CurrencyNodeName);
            AddHandler(BalanceNodeName);
            AddHandler(NetOpenPositionNodeName);
            //<wallets><wallet><currency>GBP</currency><balance>15000</balance></wallet></wallets>
        }

        public override void EndElement (string endElement)
        {
            if (RootNodeName.Equals(endElement))
            {
                decimal balance;
                TryGetValue(BalanceNodeName, out balance);
                decimal netOpenPosition;
                _wallets[GetStringValue(CurrencyNodeName)] = balance;
                if (TryGetValue(NetOpenPositionNodeName, out netOpenPosition))
                {
                    _netOpenPositions[GetStringValue(CurrencyNodeName)] = netOpenPosition;
                }
                ResetAll();
            }
        }

        public Dictionary<string, decimal> GetAndResetWallets()
        {
            Dictionary<string, decimal> copy = new Dictionary<string, decimal>(_wallets);
            _wallets.Clear();
            return copy;
        }

        public Dictionary<string, decimal> GetAndResetNetOpenPositions()
        {
            Dictionary<string, decimal> copy = new Dictionary<string, decimal>(_netOpenPositions);
            _netOpenPositions.Clear();
            return copy;
        }
    }
}
