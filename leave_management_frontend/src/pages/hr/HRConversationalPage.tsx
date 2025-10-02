import HRChatInterface from '../../components/hr/HRChatInterface';

const HRConversationalPage = () => {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">HR Assistant</h1>
        <p className="text-gray-600 mt-2">
          Ask anything about leaves, approvals, analytics, and team availability
        </p>
      </div>

      <HRChatInterface />
    </div>
  );
};

export default HRConversationalPage;