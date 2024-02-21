using System;
using System.Collections.Generic;
using System.Text;

namespace Com.Lmax.Api.Account
{
    /// <summary>
    /// A event that contains all of the top level information about an account's
    /// current state.
    /// </summary>
    public sealed class AccountStateEvent : IEquatable<AccountStateEvent>
    {
        private readonly long _accountId;
        private readonly decimal _balance;
        private readonly decimal _cash;
        private readonly decimal _credit;
        private readonly decimal _availableFunds;
        private readonly decimal _availableToWithdraw;
        private readonly decimal _unrealisedProfitAndLoss;
        private readonly decimal _margin;
        private readonly Dictionary<string, decimal> _walletByCurrency;
        private readonly Dictionary<string, decimal> _netOpenPositionByCurrency;

        /// <summary>
        /// Construct an AccountStateEvent, visible for testing
        /// </summary>
        public AccountStateEvent(
            long accountId, decimal balance, decimal cash, decimal credit, 
            decimal availableFunds,
            decimal availableToWithdraw,
            decimal unrealisedProfitAndLoss, decimal margin,
            Dictionary<string, decimal> walletByCurrency, Dictionary<string, decimal> netOpenPositionByCurrency)
        {
            _accountId = accountId;
            _balance = balance;
            _cash = cash;
            _credit = credit;
            _availableFunds = availableFunds;
            _availableToWithdraw = availableToWithdraw;
            _unrealisedProfitAndLoss = unrealisedProfitAndLoss;
            _margin = margin;
            _walletByCurrency = walletByCurrency;
            _netOpenPositionByCurrency = netOpenPositionByCurrency;
        }

        /// <summary>
        /// Get the account id that this event pertains to.
        /// </summary>
        public long AccountId
        {
            get { return _accountId; }
        }

        /// <summary>
        /// Get the accounts current balance.
        /// </summary>
        public decimal Balance
        {
            get { return _balance; }
        }

        /// <summary>
        /// Get the accounts cash balance.
        /// </summary>
        public decimal Cash
        {
            get { return _cash; }
        }

        /// <summary>
        /// Get the accounts credit balance.
        /// </summary>
        public decimal Credit
        {
            get { return _credit; }
        }

        /// <summary>
        /// Get the account's available funds.
        /// </summary>
        public decimal AvailableFunds
        {
            get { return _availableFunds; }
        }

        /// <summary>
        /// Get the amount that this account is available to withdraw.
        /// </summary>
        public decimal AvailableToWithdraw
        {
            get { return _availableToWithdraw; }
        }

        /// <summary>
        /// Get a signed amount that is the account's unrealised profit (or loss)
        /// </summary>
        public decimal UnrealisedProfitAndLoss
        {
            get { return _unrealisedProfitAndLoss; }
        }

        /// <summary>
        /// Get the account's total margin.
        /// </summary>
        public decimal Margin
        {
            get { return _margin; }
        }

        /// <summary>
        /// Get the account's balances by currency.  The Dictionary is keyed by
        /// 3 letter currency symbol, e.g. GBP.
        /// </summary>
        public Dictionary<string, decimal> Wallets
        {
            get { return _walletByCurrency; }
        }

        /// <summary>
        /// Get the account's net open currency positions by currency (only applicable to accounts using net margin).
        /// The Dictionary is keyed by 3 letter currency symbol, e.g. GBP.
        /// </summary>
        public Dictionary<string, decimal> NetOpenPositions
        {
            get { return _netOpenPositionByCurrency; }
        }

        public bool Equals(AccountStateEvent other)
        {
            if (ReferenceEquals(null, other)) return false;
            if (ReferenceEquals(this, other)) return true;
            return other._accountId == _accountId && other._balance == _balance &&
                   other._availableFunds == _availableFunds && other._availableToWithdraw == _availableToWithdraw &&
                   other._unrealisedProfitAndLoss == _unrealisedProfitAndLoss && other._margin == _margin &&
                   other._cash == _cash && other._credit == _credit &&
                   walletsEquals(_walletByCurrency, other._walletByCurrency) &&
                   walletsEquals(_netOpenPositionByCurrency, other._netOpenPositionByCurrency);
        }

        public override bool Equals(object obj)
        {
            if (ReferenceEquals(null, obj)) return false;
            if (ReferenceEquals(this, obj)) return true;
            if (obj.GetType() != typeof (AccountStateEvent)) return false;
            return Equals((AccountStateEvent) obj);
        }

        public override int GetHashCode()
        {
            unchecked
            {
                int result = _accountId.GetHashCode();
                result = (result*397) ^ _balance.GetHashCode();
                result = (result*397) ^ _cash.GetHashCode();
                result = (result*397) ^ _credit.GetHashCode();
                result = (result*397) ^ _availableFunds.GetHashCode();
                result = (result*397) ^ _availableToWithdraw.GetHashCode();
                result = (result*397) ^ _unrealisedProfitAndLoss.GetHashCode();
                result = (result*397) ^ _margin.GetHashCode();
                result = (result*397) ^ (_walletByCurrency != null ? _walletByCurrency.GetHashCode() : 0);
                result = (result*397) ^ (_netOpenPositionByCurrency != null ? _netOpenPositionByCurrency.GetHashCode() : 0);
                return result;
            }
        }

        public static bool operator ==(AccountStateEvent left, AccountStateEvent right)
        {
            return Equals(left, right);
        }

        public static bool operator !=(AccountStateEvent left, AccountStateEvent right)
        {
            return !Equals(left, right);
        }

        private bool walletsEquals(Dictionary<string, decimal> thisWallets, Dictionary<string, decimal> otherWallets)
        {
            bool walletsAreEqual = true;
            if (otherWallets.Count != thisWallets.Count)
            {
                return false;
            }
            foreach (KeyValuePair<string, decimal> wallet in otherWallets)
            {
                decimal balanceValue = 0m;
                walletsAreEqual &= thisWallets.TryGetValue(wallet.Key, out balanceValue);
                walletsAreEqual &= thisWallets.ContainsKey(wallet.Key) && balanceValue == wallet.Value;
            }
            return walletsAreEqual;
        }

        public override string ToString()
        {
            return
                string.Format(
                    "AccountId: {0}, Balance: {1}, Cash: {8}, Credit: {9}, AvailableFunds: {2}, AvailableToWithdraw: {3}, UnrealisedProfitAndLoss: {4}, Margin: {5}, WalletByCurrency: {6}, NetOpenPositionByCurrency: {7}",
                    _accountId, _balance, _availableFunds, _availableToWithdraw, _unrealisedProfitAndLoss, _margin,
                    DictionaryToString(_walletByCurrency, null), DictionaryToString(_netOpenPositionByCurrency, null), 
                    _cash, _credit);
        }

        private static string DictionaryToString<T, V>(IEnumerable<KeyValuePair<T, V>> items, string format)
        {
            format = String.IsNullOrEmpty(format) ? "{0}='{1}' " : format;

            StringBuilder itemString = new StringBuilder();
            foreach (KeyValuePair<T, V> item in items)
            {
                itemString.AppendFormat(format, item.Key, item.Value);
            }

            return itemString.ToString();
        }
    }
}