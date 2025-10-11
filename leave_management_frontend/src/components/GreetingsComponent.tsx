import React from 'react';

interface GreetingComponentProps {
  userName: string;
  role?: string;
  onAction: (action: string) => void;
}

const GreetingComponent: React.FC<GreetingComponentProps> = ({
  userName,
  role,
  onAction,
}) => {
  const getQuickActions = () => {
    if (role === 'HR') {
      return [
        { text: 'Apply for Leave', color: 'from-[#8B7BA8] to-[#9B8BB8]' },
        { text: 'Check Status', color: 'from-[#6B9BD1] to-[#7BABD9]' },
        { text: 'Cancel Request', color: 'from-[#87C7C7] to-[#97D7D7]' },
      ];
    } else if (role === 'MANAGER') {
      return [
        { text: 'Pending Approvals', color: 'from-[#8B7BA8] to-[#9B8BB8]' },
        { text: 'Team Status', color: 'from-[#6B9BD1] to-[#7BABD9]' },
        { text: 'View Analytics', color: 'from-[#87C7C7] to-[#97D7D7]' },
      ];
    }
    return [
      { text: 'Apply for Leave', color: 'from-[#8B7BA8] to-[#9B8BB8]' },
      { text: 'Check Status', color: 'from-[#6B9BD1] to-[#7BABD9]' },
      { text: 'Cancel Request', color: 'from-[#87C7C7] to-[#97D7D7]' },
    ];
  };

  const actions = getQuickActions();

  return (
    <div className="space-y-4 animate-fadeIn">
      {/* Welcome Card */}
      <div className="bg-gradient-to-br from-[#3B5578]/80 to-[#4A5D7E]/80 backdrop-blur-lg rounded-3xl p-6 shadow-xl">
        <h2 className="text-2xl font-bold text-white mb-2">Welcome!</h2>
        <p className="text-blue-200 text-sm">How can I help you today?</p>
      </div>

      {/* Quick Action Buttons */}
      <div className="flex gap-3 flex-wrap justify-center">
        {actions.map((action, idx) => (
          <button
            key={idx}
            onClick={() => onAction(action.text)}
            className={`px-5 py-2.5 bg-gradient-to-r ${action.color} text-white text-sm font-medium rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200`}
          >
            {action.text}
          </button>
        ))}
      </div>
    </div>
  );
};

export default GreetingComponent;