import { useEffect, useState } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import { managersApi } from '../../api';
import { useAppDispatch } from '../../store/hooks';
import { addToast } from '../../features/ui/uiSlice';
import Spinner from '../../components/common/Spinner';
import Button from '../../components/common/Button';

const ApprovalsPage = () => {
  const dispatch = useAppDispatch();
  const [pendingLeaves, setPendingLeaves] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeave, setSelectedLeave] = useState<number | null>(null);
  const [comments, setComments] = useState('');

  useEffect(() => {
    fetchPendingLeaves();
  }, []);

  const fetchPendingLeaves = async () => {
    try {
      const data = await managersApi.getPendingLeaves();
      setPendingLeaves(data);
    } catch (error) {
      console.error('Failed to fetch:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (leaveId: number, approved: boolean) => {
    try {
      await managersApi.approveRejectLeave({
        leave_id: leaveId,
        approved,
        comments: comments || undefined,
      });

      dispatch(addToast({
        message: `Leave ${approved ? 'approved' : 'rejected'} successfully`,
        type: 'success',
      }));

      setPendingLeaves(pendingLeaves.filter(l => l.leave.id !== leaveId));
      setSelectedLeave(null);
      setComments('');
    } catch (error) {
      dispatch(addToast({
        message: 'Failed to process leave',
        type: 'error',
      }));
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Leave Approvals</h1>

      {pendingLeaves.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <p className="text-gray-600">All caught up! No pending approvals.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {pendingLeaves.map((item) => (
            <div key={item.leave.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {item.employee_name}
                  </h3>
                  <p className="text-sm text-gray-600">{item.employee_position}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    item.impact_score.level === 'HIGH'
                      ? 'bg-red-100 text-red-800'
                      : item.impact_score.level === 'MEDIUM'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }`}
                >
                  Impact: {item.impact_score.level}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div>
                  <span className="text-gray-600">Leave Type:</span>
                  <span className="ml-2 font-medium">{item.leave.leave_type}</span>
                </div>
                <div>
                  <span className="text-gray-600">Duration:</span>
                  <span className="ml-2 font-medium">
                    {item.leave.start_date} to {item.leave.end_date}
                  </span>
                </div>
              </div>

              {item.leave.reason && (
                <div className="bg-gray-50 p-3 rounded mb-4">
                  <p className="text-sm text-gray-700">
                    <strong>Reason:</strong> {item.leave.reason}
                  </p>
                </div>
              )}

              {selectedLeave === item.leave.id ? (
                <div className="space-y-3">
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder="Add comments (optional)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                  />
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleApproval(item.leave.id, true)}
                      variant="success"
                      className="flex items-center gap-2"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Approve
                    </Button>
                    <Button
                      onClick={() => handleApproval(item.leave.id, false)}
                      variant="danger"
                      className="flex items-center gap-2"
                    >
                      <XCircle className="w-4 h-4" />
                      Reject
                    </Button>
                    <Button
                      onClick={() => {
                        setSelectedLeave(null);
                        setComments('');
                      }}
                      variant="secondary"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  onClick={() => setSelectedLeave(item.leave.id)}
                  className="w-full"
                >
                  Review & Decide
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ApprovalsPage;