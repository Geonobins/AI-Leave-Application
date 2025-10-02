//import { LeaveBalance } from '../../types/leave.types';

interface LeaveBalanceCardProps {
  balance: any;
}

const LeaveBalanceCard = ({ balance }: LeaveBalanceCardProps) => {
  const percentage = (balance.used / balance.total) * 100;

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{balance.leave_type}</h3>
      
      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Total</span>
          <span className="font-medium">{balance.total} days</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Used</span>
          <span className="font-medium text-red-600">{balance.used} days</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Available</span>
          <span className="font-medium text-green-600">{balance.available} days</span>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                percentage > 75 ? 'bg-red-500' : percentage > 50 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${percentage}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(0)}% utilized</p>
        </div>
      </div>
    </div>
  );
};

export default LeaveBalanceCard;