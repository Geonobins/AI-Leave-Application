import { useState, useEffect } from 'react';
import { Calendar, TrendingUp, Clock, MessageSquare, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchLeaves, fetchBalances } from '../../features/leaves/leavesSlice';
import UnifiedChatBox from '../../components/common/unifiedChatbox';
import { managersApi } from '../../api';

interface PolicyCompliance {
  compliant: boolean;
  has_violations: boolean;
  violations: string[];
  warnings: string[];
  relevant_policies: Array<{
    section_title: string | null;
    content: string;
    policy_name: string;
  }>;
}

interface PendingLeave {
  leave_id: number;
  employee_id: number;
  employee_name: string;
  employee_position: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  duration: number;
  reason: string | null;
  created_at: string;
  responsible_person_id: number | null;
  impact_score: {
    score: number;
    level: string;
    factors: string[];
  };
  policy_compliance: PolicyCompliance;
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
      
      await loadPendingApprovals();
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

  const violationsCount = pendingApprovals.filter(p => p.policy_compliance?.has_violations).length;
  const warningsCount = pendingApprovals.filter(p => p.policy_compliance?.warnings?.length > 0).length;

  // Sort: violations first, then by creation date
  const sortedApprovals = [...pendingApprovals].sort((a, b) => {
    if (a.policy_compliance?.has_violations && !b.policy_compliance?.has_violations) return -1;
    if (!a.policy_compliance?.has_violations && b.policy_compliance?.has_violations) return 1;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  const getRoleSpecificStats = () => {
    if (user?.role === 'MANAGER' || user?.role === 'HR') {
      return (
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Pending Approvals</p>
              <p className="text-3xl font-bold text-gray-900">{pendingApprovals.length}</p>
              {violationsCount > 0 && (
                <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  {violationsCount} with violations
                </p>
              )}
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
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Pending Approvals</h2>
                {violationsCount > 0 && (
                  <p className="text-sm text-red-600 mt-1 flex items-center gap-1">
                    <AlertTriangle className="w-4 h-4" />
                    {violationsCount} request(s) have policy violations requiring review
                  </p>
                )}
              </div>
              <button
                onClick={loadPendingApprovals}
                disabled={loadingApprovals}
                className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
              >
                {loadingApprovals ? 'Loading...' : 'Refresh'}
              </button>
            </div>
          </div>

          <div className="p-6">
            {loadingApprovals ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">Loading approvals...</p>
              </div>
            ) : sortedApprovals.length > 0 ? (
              <div className="space-y-4">
                {sortedApprovals.map((item) => (
                  <div
                    key={item.leave_id}
                    className={`border rounded-lg p-5 transition-all ${
                      item.policy_compliance?.has_violations
                        ? 'border-red-300 bg-red-50'
                        : 'border-gray-200 hover:shadow-md'
                    }`}
                  >
                    {/* Policy Violations Alert */}
                    {item.policy_compliance?.has_violations && (
                      <div className="mb-4 bg-red-100 border border-red-300 rounded-lg p-3">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="font-semibold text-red-900 text-sm mb-2">
                              Policy Violations Detected
                            </p>
                            <ul className="space-y-1 text-sm text-red-800">
                              {item.policy_compliance.violations.map((violation, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <span className="text-red-600 flex-shrink-0">•</span>
                                  <span>{violation}</span>
                                </li>
                              ))}
                            </ul>
                            {item.policy_compliance.relevant_policies?.length > 0 && (
                              <div className="mt-2 pt-2 border-t border-red-200">
                                <p className="text-xs font-medium text-red-900 mb-1">
                                  Relevant Policy:
                                </p>
                                <p className="text-xs text-red-700">
                                  {item.policy_compliance.relevant_policies[0].section_title || 
                                   item.policy_compliance.relevant_policies[0].policy_name}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Leave Details */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <h3 className="font-semibold text-gray-900 text-lg">
                            {item.employee_name}
                          </h3>
                          <span className="text-sm text-gray-600">
                            {item.employee_position}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImpactBadgeColor(item.impact_score.level)}`}>
                            {item.impact_score.level} Impact
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                          <div>
                            <span className="font-medium text-gray-700">Type:</span>{' '}
                            <span className="text-gray-900">{item.leave_type}</span>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Duration:</span>{' '}
                            <span className="text-gray-900">{item.duration} day(s)</span>
                          </div>
                          <div className="col-span-2">
                            <span className="font-medium text-gray-700">Period:</span>{' '}
                            <span className="text-gray-900">
                              {new Date(item.start_date).toLocaleDateString()} -{' '}
                              {new Date(item.end_date).toLocaleDateString()}
                            </span>
                          </div>
                          {item.reason && (
                            <div className="col-span-2">
                              <span className="font-medium text-gray-700">Reason:</span>{' '}
                              <span className="text-gray-900">{item.reason}</span>
                            </div>
                          )}
                        </div>

                        {/* Warnings */}
                        {item.policy_compliance?.warnings?.length > 0 && (
                          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-3">
                            <p className="text-xs font-medium text-yellow-800 mb-1 flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" />
                              Policy Warnings:
                            </p>
                            <ul className="text-xs text-yellow-700 space-y-1">
                              {item.policy_compliance.warnings.map((warning, idx) => (
                                <li key={idx}>• {warning}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Impact Factors */}
                        {item.impact_score.factors.length > 0 && (
                          <div className="bg-blue-50 border border-blue-200 rounded p-3">
                            <p className="text-xs font-medium text-blue-800 mb-1">Impact Factors:</p>
                            <ul className="text-xs text-blue-700 space-y-1">
                              {item.impact_score.factors.map((factor, idx) => (
                                <li key={idx}>• {factor}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex flex-col gap-2 ml-4">
                        <button
                          onClick={() => handleApproveReject(item.leave_id, true)}
                          disabled={processingLeaveId === item.leave_id || item.policy_compliance?.has_violations}
                          className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title={item.policy_compliance?.has_violations ? 'Cannot approve: Policy violations exist' : 'Approve request'}
                        >
                          <CheckCircle className="w-4 h-4" />
                          Approve
                        </button>
                        <button
                          onClick={() => {
                            const reason = prompt('Rejection reason (optional):');
                            handleApproveReject(item.leave_id, false, reason || undefined);
                          }}
                          disabled={processingLeaveId === item.leave_id}
                          className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
              <div className="text-center py-12 text-gray-600">
                <Clock className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p className="font-medium">No pending approvals</p>
                <p className="text-sm mt-1">All leave requests have been processed</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {user?.role === 'MANAGER' || user?.role === 'HR' 
            ? 'Recent Team Activity' 
            : 'My Recent Leaves'}
        </h2>
        {leaves.length > 0 ? (
          <div className="space-y-3">
            {leaves.map((leave) => (
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