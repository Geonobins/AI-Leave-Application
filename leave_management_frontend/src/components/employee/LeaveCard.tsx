// LeaveCard.tsx

import { Calendar, Clock } from 'lucide-react';
import { format } from 'date-fns';

interface LeaveCardProps {
  leave: any;
}

const LeaveCard = ({ leave }: LeaveCardProps) => {
  // ✅ Safe formatter for dates
  const safeFormat = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const parsed = new Date(dateString);
    if (isNaN(parsed.getTime())) return 'Invalid Date';
    return format(parsed, 'MMM dd, yyyy');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'REJECTED':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    }
  };

  // ✅ Safe duration calculation
  const duration = (() => {
    if (!leave.start_date || !leave.end_date) return 0;
    const start = new Date(leave.start_date);
    const end = new Date(leave.end_date);
    if (isNaN(start.getTime()) || isNaN(end.getTime())) return 0;

    return (
      Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1
    );
  })();

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {leave.leave_type || 'Leave'}
          </h3>
          <p className="text-sm text-gray-600">{duration} day(s)</p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
            leave.status
          )}`}
        >
          {leave.status || 'PENDING'}
        </span>
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="w-4 h-4" />
          <span>
            {safeFormat(leave.start_date)} - {safeFormat(leave.end_date)}
          </span>
        </div>

        {leave.reason && (
          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
            <strong>Reason:</strong> {leave.reason}
          </p>
        )}

        {leave.manager_comments && (
          <p className="text-sm text-gray-700 bg-blue-50 p-3 rounded border-l-4 border-blue-500">
            <strong>Manager's Comment:</strong> {leave.manager_comments}
          </p>
        )}
      </div>

      <div className="mt-4 text-xs text-gray-500 flex items-center gap-1">
        <Clock className="w-3 h-3" />
        Applied on {safeFormat(leave.created_at)}
      </div>
    </div>
  );
};

export default LeaveCard;
