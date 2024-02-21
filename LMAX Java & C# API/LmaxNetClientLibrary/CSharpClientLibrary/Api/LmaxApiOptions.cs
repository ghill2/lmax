using System;
using System.Collections.Generic;
using System.Text;

namespace Com.Lmax.Api
{
    public class LmaxApiOptions
    {
        private string _clientIdentifier;
        private int _defaultConnectionLimit;

        ///<summary>
        /// Constructs an LmaxApiOptions object with default values of:
        /// DefaultConnectionLimit = 5
        /// ClientIdentifier = ""
        ///</summary>
        public LmaxApiOptions() : this ("")
        {
        }

        ///<summary>
        /// Constructs an LmaxApiOptions object with default values of:
        /// DefaultConnectionLimit = 5
        ///</summary>
        ///<param name="clientIdentifier">Identifies the client in HTTP requests for diagnostic purposes (25 characters permitted).</param>
        public LmaxApiOptions(string clientIdentifier)
        {
            _clientIdentifier = clientIdentifier;
            _defaultConnectionLimit = 5;
        }

        /// <summary>
        /// Gets or sets the ClientIdentifier, used to identify the client in HTTP requests for diagnostic purposes (25 characters permitted).
        /// </summary>
        public string ClientIdentifier
        {
            get { return _clientIdentifier;  }
            set { _clientIdentifier = TruncateClientId(value); }
        }

        /// <summary>
        /// Gets or sets the maximum number of concurrent connections allowed by a System.Net.ServicePoint object per login.
        /// 
        /// Note: the larger the value, the more resources used by the API (more sockets openened, threads created, etc.)
        /// </summary>
        public int DefaultConnectionLimit
        {
            get { return _defaultConnectionLimit; }
            set { _defaultConnectionLimit = value; }
        }

        private string TruncateClientId(string clientIdentifier)
        {
            if (clientIdentifier == null)
            {
                return "";
            }
            else
            {
                int length = clientIdentifier.Length;
                if (length < 25)
                {
                    return clientIdentifier;
                }
                else
                {
                    return clientIdentifier.Substring(0, 25);
                }
            }
        }
    }
}
