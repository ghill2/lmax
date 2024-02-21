using System;
using System.Collections.Generic;

namespace Com.Lmax.Api.Internal.Protocol
{
    public class HistoricMarketDataEventHandler : DefaultHandler
    {
        private const string RootNodeName = "historicMarketData";
        private const string InstructionIdNodeName = "instructionId";
        public event OnHistoricMarketDataEvent HistoricMarketDataReceived;

        private readonly List<Uri> _urls;
        private readonly URLHandler _urlHandler;

        public HistoricMarketDataEventHandler()
            : base(RootNodeName)
        {
            _urls = new List<Uri>();
            _urlHandler = new URLHandler(_urls);
            AddHandler(InstructionIdNodeName);
            AddHandler(_urlHandler);
        }

        public override void EndElement(string endElement)
        {
            if (HistoricMarketDataReceived != null && RootNodeName.Equals(endElement))
            {
                string instructionId;

                TryGetValue(InstructionIdNodeName, out instructionId);

                HistoricMarketDataReceived(instructionId, _urlHandler.GetFiles());
            }
        }

        public override void Reset(string element)
        {
            base.Reset(element);
            if (RootNodeName.Equals(element))
            {
                _urls.Clear();
            }
        }
    }

    internal class URLHandler : Handler
    {
        private const string RootNodeName = "url";
        
        private readonly List<Uri> _urls;

        public URLHandler(List<Uri> urls)
            : base(RootNodeName)
        {
            _urls = urls;
        }

        public override void EndElement (string endElement)
        {
            if (RootNodeName.Equals(endElement))
            {
                _urls.Add(new Uri(Content));
                
            }
        }

        public List<Uri> GetFiles()
        {
            return _urls;
        }
    }
}