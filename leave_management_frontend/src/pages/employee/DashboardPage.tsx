import { useState, useEffect } from 'react';
import { Calendar, TrendingUp, Clock, MessageSquare, CheckCircle, XCircle } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchLeaves, fetchBalances } from '../../features/leaves/leavesSlice';

import UnifiedChatBox from '../../components/common/unifiedChatbox';
import { managersApi } from '../../api';

interface PendingLeave {
  leave: {
    id: number;
    employee_id: number;
    leave_type: string;
    start_date: string;
    end_date: string;
    reason: string;
    status: string;
  };
  employee_name: string;
  employee_position: string;
  impact_score: {
    score: number;
    level: string;
    factors: string[];
  };
}

const DashboardPage = () => {
  const dispatch = useAppDispatch();
  const { leaves, balances } = useAppSelector((state) => state.leaves);
  const { user } = useAppSelector((state) => state.auth);
  const [showChat, setShowChat] = useState(false);
  const [pendingApprovals, setPendingApprovals] = useState<PendingLeave[]>([]);
  const [loadingApprovals, setLoadingApprovals] = useState(false);
  const [processingLeaveId, setProcessingLeaveId] = useState<number | null>(null);

  useEffect(() => {
    dispatch(fetchLeaves());
    dispatch(fetchBalances());
    
    // Load pending approvals for managers/HR
    if (user?.role === 'MANAGER' || user?.role === 'HR') {
      loadPendingApprovals();
    }
  }, [dispatch, user]);

  const loadPendingApprovals = async () => {
    setLoadingApprovals(true);
    try {
      const data = await managersApi.getPendingLeaves();
      setPendingApprovals(data);
    } catch (error) {
      console.error('Failed to load pending approvals:', error);
    } finally {
      setLoadingApprovals(false);
    }
  };

  const handleApproveReject = async (leaveId: number, approved: boolean, comments?: string) => {
    setProcessingLeaveId(leaveId);
    try {
      await managersApi.approveRejectLeave({
        leave_id: leaveId,
        approved,
        comments: comments || (approved ? 'Approved' : 'Rejected'),
      });
      
      // Refresh the list
      await loadPendingApprovals();
      
      // Show success message
      alert(`Leave ${approved ? 'approved' : 'rejected'} successfully!`);
    } catch (error) {
      console.error('Failed to process leave:', error);
      alert('Failed to process leave request');
    } finally {
      setProcessingLeaveId(null);
    }
  };

  const pendingLeaves = leaves.filter((l) => l.status === 'PENDING' && l.employee_id === user?.id).length;
  const approvedLeaves = leaves.filter((l) => l.status === 'APPROVED').length;
  const totalAvailable = balances.reduce((sum, b) => sum + b.available, 0);

  const getRoleSpecificStats = () => {
    if (user?.role === 'MANAGER' || user?.role === 'HR') {
      return (
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Pending Approvals</p>
              <p className="text-3xl font-bold text-gray-900">{pendingApprovals.length}</p>
            </div>
            <Clock className="w-12 h-12 text-orange-500" />
          </div>
        </div>
      );
    }
    return null;
  };

  const getImpactBadgeColor = (level: string) => {
    switch (level) {
      case 'HIGH': return 'bg-red-100 text-red-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'LOW': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.full_name}!
        </h1>
        <p className="text-gray-600 mt-1">{user?.position} - {user?.department}</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">My Pending Requests</p>
              <p className="text-3xl font-bold text-gray-900">{pendingLeaves}</p>
            </div>
            <Clock className="w-12 h-12 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Approved Leaves</p>
              <p className="text-3xl font-bold text-gray-900">{approvedLeaves}</p>
            </div>
            <Calendar className="w-12 h-12 text-green-500" />
          </div>
        </div>

        {getRoleSpecificStats() || (
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Available Days</p>
                <p className="text-3xl font-bold text-gray-900">{totalAvailable}</p>
              </div>
              <TrendingUp className="w-12 h-12 text-purple-500" />
            </div>
          </div>
        )}
      </div>

      {/* Unified Chat Assistant */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-lg p-6 mb-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">AI Assistant</h2>
            <p className="text-blue-100">
              {user?.role === 'HR' 
                ? 'Manage leaves, view analytics, process approvals...'
                : user?.role === 'MANAGER'
                ? 'View team status, approve leaves, check balances...'
                : 'Request leave, check balance, view my leaves...'}
            </p>
          </div>
          <button
            onClick={() => setShowChat(!showChat)}
            className="bg-white text-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-blue-50 flex items-center gap-2"
          >
            <MessageSquare className="w-5 h-5" />
            {showChat ? 'Hide Chat' : 'Open Chat'}
          </button>
        </div>
      </div>

      {showChat && (
        <div className="mb-8">
          <UnifiedChatBox />
        </div>
      )}

      {/* Pending Approvals Section (Manager/HR Only) */}
      {(user?.role === 'MANAGER' || user?.role === 'HR') && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Pending Approvals</h2>
            <button
              onClick={loadPendingApprovals}
              disabled={loadingApprovals}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {loadingApprovals ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {loadingApprovals ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading approvals...</p>
            </div>
          ) : pendingApprovals.length > 0 ? (
            <div className="space-y-4">
              {pendingApprovals.map((item) => (
                <div
                  key={item.leave.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {item.employee_name}
                        </h3>
                        <span className="text-sm text-gray-600">
                          {item.employee_position}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImpactBadgeColor(item.impact_score.level)}`}>
                          {item.impact_score.level} Impact
                        </span>
                      </div>
                      
                      <div className="space-y-1 text-sm text-gray-600 mb-3">
                        <p>
                          <span className="font-medium">Type:</span> {item.leave.leave_type}
                        </p>
                        <p>
                          <span className="font-medium">Duration:</span>{' '}
                          {new Date(item.leave.start_date).toLocaleDateString()} -{' '}
                          {new Date(item.leave.end_date).toLocaleDateString()}
                        </p>
                        <p>
                          <span className="font-medium">Reason:</span> {item.leave.reason}
                        </p>
                      </div>

                      {item.impact_score.factors.length > 0 && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded p-2 mb-3">
                          <p className="text-xs font-medium text-yellow-800 mb-1">Impact Factors:</p>
                          <ul className="text-xs text-yellow-700 space-y-1">
                            {item.impact_score.factors.map((factor, idx) => (
                              <li key={idx}>• {factor}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => handleApproveReject(item.leave.id, true)}
                        disabled={processingLeaveId === item.leave.id}
                        className="flex items-center gap-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve
                      </button>
                      <button
                        onClick={() => {
                          const reason = prompt('Rejection reason (optional):');
                          handleApproveReject(item.leave.id, false, reason || undefined);
                        }}
                        disabled={processingLeaveId === item.leave.id}
                        className="flex items-center gap-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-600">
              <Clock className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p>No pending approvals</p>
            </div>
          )}
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {user?.role === 'MANAGER' || user?.role === 'HR' 
            ? 'Recent Team Activity' 
            : 'My Recent Leaves'}
        </h2>
        {leaves.slice(0, 5).length > 0 ? (
          <div className="space-y-3">
            {leaves.slice(0, 5).map((leave) => (
              <div
                key={leave.id}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">{leave.leave_type}</p>
                  <p className="text-sm text-gray-600">
                    {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    leave.status === 'APPROVED'
                      ? 'bg-green-100 text-green-800'
                      : leave.status === 'REJECTED'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {leave.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600 text-center py-4">No recent leaves</p>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;