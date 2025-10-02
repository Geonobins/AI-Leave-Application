import LeaveChatInterface from '../../components/employee/LeaveChatInterface';

const RequestLeavePage = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Request Leave</h1>
        <p className="text-gray-600 mt-2">
          Use the AI assistant to request leave naturally - just describe your leave plans
        </p>
      </div>

      <LeaveChatInterface />
    </div>
  );
};

export default RequestLeavePage;