import React, { useState, useEffect } from 'react';
import { AlertTriangle, TrendingUp, Users, Calendar, Brain, AlertCircle, CheckCircle, Clock, BarChart3 } from 'lucide-react';
import { type AnalyticsResponse, type DepartmentComparison, type BurnoutIndicator, type CoverageGap, hrApi } from '../../api/endpoints/hr.api';

const AnalyticsPage = () => {
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [deptComparison, setDeptComparison] = useState<DepartmentComparison[]>([]);
  const [burnoutData, setBurnoutData] = useState<BurnoutIndicator[]>([]);
  const [coverageGaps, setCoverageGaps] = useState<CoverageGap[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'predictions' | 'risks' | 'departments'>('overview');
  const [timeframe, setTimeframe] = useState('current_year');
  const [error, setError] = useState('');

  useEffect(() => {
    loadAnalytics();
  }, [timeframe]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError('');
      
      const [analyticsData, deptData, burnoutInfo, gapData] = await Promise.all([
        hrApi.getAnalytics({ timeframe, include_predictions: true }),
        hrApi.getDepartmentComparison(),
        hrApi.getBurnoutIndicators(),
        hrApi.getCoverageGaps(30)
      ]);
      
      setAnalytics(analyticsData);
      setDeptComparison(deptData.departments);
      setBurnoutData(burnoutInfo.at_risk_employees);
      setCoverageGaps(gapData.coverage_gaps);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analytics');
      console.error('Analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
      case 'HIGH':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'MEDIUM':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      URGENT: 'bg-red-100 text-red-800',
      HIGH: 'bg-orange-100 text-orange-800',
      MEDIUM: 'bg-yellow-100 text-yellow-800',
      LOW: 'bg-gray-100 text-gray-800'
    };
    return colors[priority as keyof typeof colors] || colors.LOW;
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error || 'Failed to load analytics'}
          <button 
            onClick={loadAnalytics}
            className="ml-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <Brain className="w-8 h-8 text-blue-600" />
              AI-Powered Analytics
            </h1>
            <p className="text-gray-600 mt-1">Actionable insights and predictions for leave management</p>
          </div>
          
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          >
            <option value="current_year">Current Year</option>
            <option value="last_6_months">Last 6 Months</option>
            <option value="last_quarter">Last Quarter</option>
          </select>
        </div>
      </div>

      {/* AI Insights Banner */}
      {analytics.insights && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6">
          <div className="flex items-start gap-3">
            <Brain className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">AI Insights Summary</h3>
              <p className="text-gray-700 leading-relaxed">{analytics.insights}</p>
            </div>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      {analytics.summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Requests</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.summary.total_requests || 0}</p>
              </div>
              <Calendar className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Approval Rate</p>
                <p className="text-2xl font-bold text-green-600">{analytics.summary.approval_rate || 0}%</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Duration</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.summary.avg_duration || 0} days</p>
              </div>
              <Clock className="w-8 h-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Risk Score</p>
                <p className={`text-2xl font-bold ${analytics.risks?.risk_score > 50 ? 'text-red-600' : 'text-yellow-600'}`}>
                  {analytics.risks?.risk_score || 0}
                </p>
              </div>
              <AlertTriangle className={`w-8 h-8 ${analytics.risks?.risk_score > 50 ? 'text-red-600' : 'text-yellow-600'}`} />
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b border-gray-200">
          <div className="flex overflow-x-auto">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'predictions', label: 'Predictions', icon: TrendingUp },
              { id: 'risks', label: 'Risks & Alerts', icon: AlertTriangle },
              { id: 'departments', label: 'Departments', icon: Users }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-6 py-3 border-b-2 font-medium transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Monthly Trend */}
              {analytics.trends?.monthly_trend && analytics.trends.monthly_trend.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Leave Trend</h3>
                  <div className="space-y-2">
                    {analytics.trends.monthly_trend.slice(-6).map((item: any, idx: number) => {
                      const maxRequests = Math.max(...analytics.trends.monthly_trend.map((t: any) => t.requests));
                      const percentage = maxRequests > 0 ? (item.requests / maxRequests) * 100 : 0;
                      
                      return (
                        <div key={idx} className="flex items-center gap-3">
                          <div className="w-24 text-sm text-gray-600">{item.month}</div>
                          <div className="flex-1 bg-gray-200 rounded-full h-8 relative">
                            <div
                              className="bg-blue-600 h-8 rounded-full flex items-center justify-end pr-3 text-white text-sm font-medium transition-all duration-500"
                              style={{ width: `${percentage}%` }}
                            >
                              {item.requests > 0 && `${item.requests} requests`}
                            </div>
                          </div>
                          <div className="w-24 text-sm text-gray-600 text-right">{item.days} days</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Leave Types Distribution */}
              {analytics.trends?.leave_types && Object.keys(analytics.trends.leave_types).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Leave Types Distribution</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(analytics.trends.leave_types).map(([type, count]) => (
                      <div key={type} className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                        <p className="text-sm text-gray-600 capitalize">{type.toLowerCase().replace('_', ' ')}</p>
                        <p className="text-2xl font-bold text-gray-900">{count as number}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Coverage Gaps */}
              {coverageGaps.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Coverage Gaps (Next 30 Days)</h3>
                  <div className="space-y-3">
                    {coverageGaps.slice(0, 5).map((gap, idx) => (
                      <div key={idx} className={`border rounded-lg p-4 ${getSeverityColor(gap.severity)}`}>
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-semibold">{gap.department} - {new Date(gap.date).toLocaleDateString()}</p>
                            <p className="text-sm mt-1">
                              {gap.absent_count} of {gap.department_size} employees absent ({gap.absence_rate}%)
                            </p>
                          </div>
                          <span className="text-xs font-semibold px-2 py-1 rounded bg-white">
                            {gap.severity}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Predictions Tab */}
          {activeTab === 'predictions' && (
            <div className="space-y-6">
              {analytics.predictions?.prediction_confidence && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    Prediction Confidence: <strong>{analytics.predictions.prediction_confidence}%</strong>
                  </p>
                </div>
              )}

              {/* Next 90 Days */}
              {analytics.predictions?.next_90_days && analytics.predictions.next_90_days.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Next 90 Days Forecast</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {analytics.predictions.next_90_days.map((pred: any, idx: number) => (
                      <div key={idx} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <p className="font-semibold text-gray-900">{pred.month}</p>
                        <div className="mt-2 space-y-1">
                          <p className="text-sm text-gray-600">
                            Expected Requests: <span className="font-medium text-gray-900">{pred.predicted_requests}</span>
                          </p>
                          <p className="text-sm text-gray-600">
                            Expected Days: <span className="font-medium text-gray-900">{pred.predicted_days}</span>
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* High Demand Periods */}
              {analytics.predictions?.high_demand_periods && analytics.predictions.high_demand_periods.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">High Demand Periods</h3>
                  <div className="space-y-3">
                    {analytics.predictions.high_demand_periods.map((period: any, idx: number) => (
                      <div key={idx} className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-gray-900">{period.month}</p>
                            <p className="text-sm text-gray-600 mt-1">
                              Expected {period.expected_requests} requests ({period.above_average}% above average)
                            </p>
                          </div>
                          <AlertCircle className="w-6 h-6 text-orange-600" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Likely Leave Requests */}
              {analytics.predictions?.likely_leave_requests && analytics.predictions.likely_leave_requests.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Employees Likely to Request Leave Soon</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Available Days</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Likelihood</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {analytics.predictions.likely_leave_requests.map((req: any, idx: number) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{req.employee}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{req.department}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{req.available_days}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-semibold rounded ${
                                req.likelihood === 'HIGH' ? 'bg-red-100 text-red-800' : 
                                req.likelihood === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                              }`}>
                                {req.likelihood}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-600">{req.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Risks Tab */}
          {activeTab === 'risks' && (
            <div className="space-y-6">
              {/* Critical Risks */}
              {analytics.risks?.critical_risks && analytics.risks.critical_risks.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-red-600 mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Critical Risks ({analytics.risks.critical_risks.length})
                  </h3>
                  <div className="space-y-3">
                    {analytics.risks.critical_risks.map((risk: any, idx: number) => (
                      <div key={idx} className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <div className="flex items-start justify-between">
                              <div>
                                <p className="font-semibold text-gray-900">{risk.title}</p>
                                <p className="text-sm text-gray-700 mt-1">{risk.description}</p>
                              </div>
                              <span className="text-xs font-semibold px-2 py-1 rounded bg-red-100 text-red-800">
                                {risk.severity || 'HIGH'}
                              </span>
                            </div>
                            {risk.impact && (
                              <p className="text-sm text-gray-600 mt-2">
                                <strong>Impact:</strong> {risk.impact}
                              </p>
                            )}
                            {risk.affected_employees && risk.affected_employees.length > 0 && (
                              <p className="text-sm text-gray-600 mt-1">
                                <strong>Affected:</strong> {risk.affected_employees.join(', ')}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Burnout Indicators */}
              {burnoutData.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-orange-600 mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Burnout Risk Employees ({burnoutData.length})
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Level</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Days Taken (6M)</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Utilization</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Factors</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {burnoutData.map((employee, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div>
                                <p className="text-sm font-medium text-gray-900">{employee.employee_name}</p>
                                <p className="text-sm text-gray-500">{employee.position}</p>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {employee.department}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs font-semibold rounded ${
                                employee.risk_level === 'HIGH' 
                                  ? 'bg-red-100 text-red-800' 
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {employee.risk_level}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {employee.risk_score}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {employee.days_taken_6m}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {employee.leave_utilization}%
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-600">
                              <div className="space-y-1">
                                {employee.risk_factors.map((factor: string, factorIdx: number) => (
                                  <div key={factorIdx} className="flex items-center gap-1">
                                    <AlertCircle className="w-3 h-3 text-orange-500" />
                                    <span>{factor}</span>
                                  </div>
                                ))}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {analytics.recommendations && analytics.recommendations.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-green-600 mb-4 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    Recommendations ({analytics.recommendations.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analytics.recommendations.map((rec: any, idx: number) => (
                      <div key={idx} className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-semibold text-gray-900">{rec.title}</p>
                            <p className="text-sm text-gray-700 mt-1">{rec.description}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <span className={`text-xs font-semibold px-2 py-1 rounded ${getPriorityBadge(rec.priority)}`}>
                                {rec.priority}
                              </span>
                              {rec.impact && (
                                <span className="text-xs text-gray-600">Impact: {rec.impact}</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Departments Tab */}
          {activeTab === 'departments' && (
            <div className="space-y-6">
              {/* Department Comparison */}
              {deptComparison.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Department Comparison</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employees</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Leaves</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Days</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Leaves/Employee</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Days/Employee</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {deptComparison.map((dept, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {dept.department}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                              {dept.employee_count}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {dept.total_leaves}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {dept.total_days}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {dept.avg_leaves_per_employee}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {dept.avg_days_per_employee}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Department Utilization */}
              {analytics.summary?.departments && Object.keys(analytics.summary.departments).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Leave Utilization by Department</h3>
                  <div className="space-y-4">
                    {Object.entries(analytics.summary.departments).map(([dept, stats]: [string, any]) => {
                      const deptInfo = deptComparison.find(d => d.department === dept);
                      const avgDaysPerEmp = deptInfo ? deptInfo.avg_days_per_employee : 0;
                      
                      return (
                        <div key={dept} className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-gray-900">{dept}</h4>
                            <span className="text-sm text-gray-600">
                              {stats.count} leaves • {stats.days} total days
                            </span>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span>Average days per employee</span>
                              <span className="font-medium">{avgDaysPerEmp} days</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                                style={{ 
                                  width: `${Math.min(100, (avgDaysPerEmp / 20) * 100)}%` 
                                }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;