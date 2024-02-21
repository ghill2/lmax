namespace Com.Lmax.Api.Internal.Protocol
{
    public class OrderResponseHandler : DefaultHandler
    {
        private string _instructionId;
        private const string InstructionIdElementName = "instructionId";

        public OrderResponseHandler() : base(BODY)
        {
            AddHandler(InstructionIdElementName);
        }

        public string InstructionId
        {
            get { return _instructionId; }
        }

        public override void EndElement(string endElement)
        {
            TryGetValue(InstructionIdElementName, out _instructionId);
        }
    }
}
