using System.Collections.Generic;
using Com.Lmax.Api.Account;

namespace Com.Lmax.Api.Internal.Events
{
    class AccountStateBuilder
    {
        private long _accountId;
        private decimal _balance;
        private decimal _cash;
        private decimal _credit;
        private decimal _availableFunds;
        private decimal _availableToWithdraw;
        private decimal _unrealisedProfitAndLoss;
        private decimal _margin;
        private Dictionary<string, decimal> _wallets;
        private Dictionary<string, decimal> _netOpenPositions;

        public AccountStateBuilder AccountId(long accountId)
        {
            _accountId = accountId;
            return this;
        }

        public AccountStateBuilder Balance(decimal balance)
        {
            _balance = balance;
            return this;
        }

        public AccountStateBuilder AvailableFunds(decimal availableFunds)
        {
            _availableFunds = availableFunds;
            return this;
        }

        public AccountStateBuilder AvailableToWithdraw(decimal availableToWithdraw)
        {
            _availableToWithdraw = availableToWithdraw;
            return this;
        }

        public AccountStateBuilder UnrealisedProfitAndLoss(decimal unrealisedProfitAndLoss)
        {
            _unrealisedProfitAndLoss = unrealisedProfitAndLoss;
            return this;
        }

        public AccountStateBuilder Margin(decimal margin)
        {
            _margin = margin;
            return this;
        }

        public AccountStateBuilder Wallets(Dictionary<string, decimal> wallets)
        {
            _wallets = wallets;
            return this;
        }

        public AccountStateBuilder NetOpenPositions(Dictionary<string, decimal> netOpenPositions)
        {
            _netOpenPositions = netOpenPositions;
            return this;
        }
        
        public AccountStateBuilder Cash(decimal cash)
        {
            _cash = cash;
            return this;
        }

        public AccountStateBuilder Credit(decimal credit)
        {
            _credit = credit;
            return this;
        }


        public AccountStateEvent NewInstance()
        {
            return new AccountStateEvent(_accountId, _balance, _cash, _credit, _availableFunds, _availableToWithdraw, _unrealisedProfitAndLoss, _margin, _wallets, _netOpenPositions);
        }
    }

}
