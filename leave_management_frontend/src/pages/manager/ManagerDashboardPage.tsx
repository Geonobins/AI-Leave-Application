import { useEffect, useState } from 'react';
import {  Clock, Users, AlertCircle } from 'lucide-react';
import { managersApi } from '../../api';
import { useAppSelector } from '../../store/hooks';
import Spinner from '../../components/common/Spinner';

const ManagerDashboardPage = () => {
  const { user } = useAppSelector((state) => state.auth);
  const [pendingLeaves, setPendingLeaves] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPendingLeaves();
  }, []);

  const fetchPendingLeaves = async () => {
    try {
      const data = await managersApi.getPendingLeaves();
      setPendingLeaves(data);
    } catch (error) {
      console.error('Failed to fetch pending leaves:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  const highImpact = pendingLeaves.filter(l => l.impact_score.level === 'HIGH').length;
  const mediumImpact = pendingLeaves.filter(l => l.impact_score.level === 'MEDIUM').length;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Manager Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome back, {user?.full_name}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Pending Approvals</p>
              <p className="text-3xl font-bold text-gray-900">{pendingLeaves.length}</p>
            </div>
            <Clock className="w-12 h-12 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">High Impact</p>
              <p className="text-3xl font-bold text-gray-900">{highImpact}</p>
            </div>
            <AlertCircle className="w-12 h-12 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Medium Impact</p>
              <p className="text-3xl font-bold text-gray-900">{mediumImpact}</p>
            </div>
            <Users className="w-12 h-12 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Recent Pending Leaves */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Pending Approvals</h2>
        {pendingLeaves.length > 0 ? (
          <div className="space-y-4">
            {pendingLeaves.slice(0, 5).map((item) => (
              <div
                key={item.leave.id}
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{item.employee_name}</p>
                    <p className="text-sm text-gray-600">{item.employee_position}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {item.leave.leave_type} - {item.leave.start_date} to {item.leave.end_date}
                    </p>
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
                    {item.impact_score.level} Impact
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-gray-600 py-8">No pending approvals</p>
        )}
      </div>
    </div>
  );
};

export default ManagerDashboardPage;