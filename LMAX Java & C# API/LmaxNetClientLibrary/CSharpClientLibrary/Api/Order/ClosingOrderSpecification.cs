using System;
using Com.Lmax.Api.Internal.Xml;

namespace Com.Lmax.Api.Order
{    
    ///<summary>
    /// Closing Order Specification.  Allows you to place an order which closes out a given quantity,
    /// either against an instrument position, or against a specific order.
    ///</summary>
    public class ClosingOrderSpecification : IRequest
    {
        private static readonly string NoInstructionId = null;
        
        private long _instrumentId;
        private decimal? _quantity;
        private string _instructionId;
        private string _originalInstructionId;

        /// <summary>
        /// Get/Set the instruction id use for tracking the order.
        /// </summary>
        public string InstructionId
        {
            get { return _instructionId; }
            set { _instructionId = value; }
        }
        
        /// <summary>
        /// Get/Set the instrument id that the order should be placed on.
        /// </summary>
        public long InstrumentId
        {
            get { return _instrumentId; }
            set { _instrumentId = value; }
        }

        /// <summary>
        /// Get/Set the of the order, the sign infers the side of the order.
        /// A positive value is a buy, negative indicates sell.
        /// </summary>
        public decimal? Quantity
        {
            get { return _quantity; }
            set { _quantity = value; }
        }
        
        ///<summary>
        /// Get/Set the original instrument id that this specification refers to
        ///</summary>
        public string OriginalInstructionId
        {
            get { return _originalInstructionId; }
            set { _originalInstructionId = value; }
        }
       
        ///<summary>
        /// Construct a ClosingOrderSpecification. This allows you to close a quantity of your position on a given instrument by
        /// placing a market order in the opposite direction of your existing position.
        ///</summary>
        ///<param name="instructionId">The user-defined correlation id</param>
        ///<param name="instrumentId">The id of the instrument for the order book to close position on</param>
        ///<param name="quantity">The quantity to close.  A signed value, where the sign indicates the side of the
        ///                       market that order is placed.  Positive implies a buy order, where as negative is a sell</param>
        public ClosingOrderSpecification(string instructionId, long instrumentId, decimal? quantity)
        {
            InstrumentId = instrumentId;
            Quantity = quantity;
            InstructionId = instructionId;
        }

        ///<summary>
        /// Construct a ClosingOrderSpecification. This allows you to close a quantity of your position on a given instrument by
        /// placing a market order in the opposite direction of your existing position.
        ///</summary>
        ///<param name="instructionId">The user-defined correlation id</param>
        ///<param name="instrumentId">The id of the instrument for the order book to close position on</param>
        ///<param name="originalInstructionId">the instruction ID of the original order to close</param>
        ///<param name="quantity">The quantity to close.  A signed value, where the sign indicates the side of the
        ///                       market that order is placed.  Positive implies a buy order, where as negative is a sell</param>
        public ClosingOrderSpecification(string instructionId, long instrumentId, string originalInstructionId, decimal? quantity): this(instructionId, instrumentId, quantity)
        {
            OriginalInstructionId = originalInstructionId;
        }

        public string Uri
        {
            get { return IsSpecificationForClosingAnIndividualOrder() ? "/secure/trade/closeOutOrder" : "/secure/trade/closeOutInstrumentPosition"; }            
        }

        /// <summary>
        /// Internal: Output this request.
        /// </summary>
        /// <param name="writer">The destination for the content of this request</param>
        public void WriteTo(IStructuredWriter writer)
        {
            Validate();
            writer.
                StartElement("req").
                    StartElement("body").
                        ValueOrNone("instructionId", InstructionId).
                        ValueOrNone("instrumentId", NullIfUnset(InstrumentId, 0)).
                        ValueOrNone("originalInstructionId", OriginalInstructionId).
                        ValueOrNone("quantity", Quantity).
                    EndElement("body").
                EndElement("req");
        }

        private bool IsSpecificationForClosingAnIndividualOrder()
        {
            return OriginalInstructionId != NoInstructionId;
        }

        private void Validate()
        {
            if (Quantity == null)
            {
                throw new ArgumentException("Quantity required");
            }
        }
        
        private static long? NullIfUnset(long InstrumentId, long nullValue)
        {
            return (InstrumentId == nullValue) ? (long?) null : InstrumentId;
        }
    }
}
