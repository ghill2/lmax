using System;
using Com.Lmax.Api.Internal.Xml;

namespace Com.Lmax.Api.Order
{
    /// <summary>
    /// Request to amend stop loss/profit on an existing order.
    /// </summary>
    public sealed class AmendStopLossProfitRequest : IRequest
    {
        private readonly long _instrumentId;
        private readonly string _instructionId;
        private readonly string _originalInstructionId;
        private readonly decimal? _stopLossOffset;
        private readonly string _stopLossInstructionId;
        private readonly decimal? _stopProfitOffset;
        private readonly string _stopProfitInstructionId;

        /// <summary>
        /// Construct an AmendStopLossProfitRequest using the instrument id and the instruction id
        /// of the original order.
        /// </summary>
        /// <param name="instrumentId">The instrument id that the original order was placed on.</param>
        /// <param name="instructionId">The instruction id used to correlate requests with responses.</param>
        /// <param name="originalInstructionId">The instruction id of the original order we want to amend.</param>
        /// <param name="stopLossOffset">The new stop loss offset, use null to
        /// indicate the value should be removed.</param>
        /// <param name="stopProfitOffset">The new stop profit offset, use null to
        /// indicate the value should be removed.</param>
        public AmendStopLossProfitRequest(
            long instrumentId, string instructionId, string originalInstructionId, 
            decimal? stopLossOffset, string stopLossInstructionId,
            decimal? stopProfitOffset, string stopProfitInstructionId)
        {
            _instrumentId = instrumentId;
            _instructionId = instructionId;
            _originalInstructionId = originalInstructionId;
            _stopLossOffset = stopLossOffset;
            _stopLossInstructionId = stopLossInstructionId;
            _stopProfitOffset = stopProfitOffset;
            _stopProfitInstructionId = stopProfitInstructionId;
        }

        /// <summary>
        /// Construct an AmendStopLossProfitRequest using the instrument id and the instruction id
        /// of the original order.
        /// </summary>
        /// <param name="instrumentId">The instrument id that the original order was placed on.</param>
        /// <param name="instructionId">The instruction id used to correlate requests with responses.</param>
        /// <param name="originalInstructionId">The instruction id of the original order we want to amend.</param>
        /// <param name="stopLossOffset">The new stop loss offset, use null to
        /// indicate the value should be removed.</param>
        /// <param name="stopProfitOffset">The new stop profit offset, use null to
        /// indicate the value should be removed.</param>
        public AmendStopLossProfitRequest(long instrumentId, string instructionId, string originalInstructionId, decimal? stopLossOffset, decimal? stopProfitOffset)
            : this(instrumentId, instructionId, originalInstructionId, stopLossOffset, null, stopProfitOffset, null)
        {
        }

        public string Uri
        {
            get { return "/secure/trade/amendOrder"; }
        }

        /// <summary>
        /// Internal: Output this request.
        /// </summary>
        /// <param name="writer">The destination for the content of this request</param>
        public void WriteTo(IStructuredWriter writer)
        {
            writer
                .StartElement("req")
                    .StartElement("body")
                        .ValueOrEmpty("instrumentId", _instrumentId)
                        .ValueOrEmpty("originalInstructionId", _originalInstructionId)
                        .ValueOrEmpty("instructionId", _instructionId)
                        .ValueOrEmpty("stopLossOffset", _stopLossOffset)
                        .ValueOrNone("stopLossInstructionId", _stopLossInstructionId)
                        .ValueOrEmpty("stopProfitOffset", _stopProfitOffset)
                        .ValueOrNone("stopProfitInstructionId", _stopProfitInstructionId)
                    .EndElement("body")
                .EndElement("req");
        }
    }
}
