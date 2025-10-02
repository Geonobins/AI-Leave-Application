import { useState, useEffect } from 'react';
import { managersApi, type TeamOverview, type TeamCalendar, type TeamInsights, type AvailabilityForecast }  from '../../api/endpoints/managers.api';
import { Calendar, Users, TrendingUp, AlertTriangle, Clock, CheckCircle, XCircle } from 'lucide-react';

const TeamViewPage = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'calendar' | 'insights' | 'forecast'>('overview');
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<TeamOverview | null>(null);
  const [calendar, setCalendar] = useState<TeamCalendar | null>(null);
  const [insights, setInsights] = useState<TeamInsights | null>(null);
  const [forecast, setForecast] = useState<AvailabilityForecast | null>(null);
  const [insightsPeriod, setInsightsPeriod] = useState<'last_30_days' | 'last_quarter' | 'current_year'>('last_30_days');
  const [calendarDays, setCalendarDays] = useState(30);
  const [forecastDays, setForecastDays] = useState(14);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [overviewData, calendarData, insightsData, forecastData] = await Promise.all([
        managersApi.getTeamOverview(),
        managersApi.getTeamCalendar(calendarDays),
        managersApi.getTeamInsights(insightsPeriod),
        managersApi.getAvailabilityForecast(forecastDays)
      ]);
      setOverview(overviewData);
      setCalendar(calendarData);
      setInsights(insightsData);
      setForecast(forecastData);
    } catch (error) {
      console.error('Error loading team data:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshInsights = async () => {
    try {
      const data = await managersApi.getTeamInsights(insightsPeriod);
      setInsights(data);
    } catch (error) {
      console.error('Error refreshing insights:', error);
    }
  };

  const refreshCalendar = async () => {
    try {
      const data = await managersApi.getTeamCalendar(calendarDays);
      setCalendar(data);
    } catch (error) {
      console.error('Error refreshing calendar:', error);
    }
  };

  const refreshForecast = async () => {
    try {
      const data = await managersApi.getAvailabilityForecast(forecastDays);
      setForecast(data);
    } catch (error) {
      console.error('Error refreshing forecast:', error);
    }
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

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Team View</h1>
        <p className="text-gray-600">Monitor your team's availability and leave patterns</p>
      </div>

      {/* Quick Stats */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Team Size</p>
                <p className="text-3xl font-bold text-gray-900">{overview.team_size}</p>
              </div>
              <Users className="h-10 w-10 text-blue-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Available Now</p>
                <p className="text-3xl font-bold text-green-600">{overview.available_count}</p>
              </div>
              <CheckCircle className="h-10 w-10 text-green-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">On Leave</p>
                <p className="text-3xl font-bold text-orange-600">{overview.on_leave_count}</p>
              </div>
              <XCircle className="h-10 w-10 text-orange-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Availability</p>
                <p className="text-3xl font-bold text-blue-600">{overview.availability_rate}%</p>
              </div>
              <TrendingUp className="h-10 w-10 text-blue-600" />
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {[
              { id: 'overview', label: 'Team Overview', icon: Users },
              { id: 'calendar', label: 'Calendar', icon: Calendar },
              { id: 'insights', label: 'Insights', icon: TrendingUp },
              { id: 'forecast', label: 'Forecast', icon: Clock }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-6 py-4 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-5 w-5" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Team Overview Tab */}
          {activeTab === 'overview' && overview && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {overview.team_members.map((member) => (
                  <div key={member.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-gray-900">{member.name}</h3>
                        <p className="text-sm text-gray-600">{member.position}</p>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          member.status === 'AVAILABLE'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-orange-100 text-orange-800'
                        }`}
                      >
                        {member.status === 'AVAILABLE' ? 'Available' : 'On Leave'}
                      </span>
                    </div>

                    {member.current_leave && (
                      <div className="bg-orange-50 border border-orange-200 rounded p-3 mb-3">
                        <p className="text-sm font-medium text-orange-900">Currently on {member.current_leave.type}</p>
                        <p className="text-xs text-orange-700">Returns: {new Date(member.current_leave.end_date).toLocaleDateString()} ({member.current_leave.days_remaining} days)</p>
                      </div>
                    )}

                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Leave Balance</span>
                        <span className="font-medium">{member.leave_balance.available}/{member.leave_balance.total_allocated} days</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${100 - member.leave_balance.utilization}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{member.leave_balance.utilization}% used</p>
                    </div>

                    {member.upcoming_leaves.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">Upcoming Leaves:</p>
                        <div className="space-y-2">
                          {member.upcoming_leaves.slice(0, 2).map((leave) => (
                            <div key={leave.id} className="text-xs bg-gray-50 rounded p-2">
                              <div className="flex justify-between">
                                <span className="font-medium">{leave.type}</span>
                                <span className={`px-2 py-0.5 rounded ${
                                  leave.status === 'APPROVED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                                }`}>
                                  {leave.status}
                                </span>
                              </div>
                              <p className="text-gray-600 mt-1">
                                {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()} ({leave.duration} days)
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Calendar Tab */}
          {activeTab === 'calendar' && calendar && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Team Calendar</h2>
                  <p className="text-sm text-gray-600">
                    {new Date(calendar.period.start).toLocaleDateString()} - {new Date(calendar.period.end).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <select
                    value={calendarDays}
                    onChange={(e) => {
                      setCalendarDays(Number(e.target.value));
                      setTimeout(refreshCalendar, 100);
                    }}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value={14}>14 days</option>
                    <option value={30}>30 days</option>
                    <option value={60}>60 days</option>
                    <option value={90}>90 days</option>
                  </select>
                </div>
              </div>

              {calendar.critical_days > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-900">Critical Coverage Days Detected</p>
                    <p className="text-sm text-red-700">{calendar.critical_days} day(s) with more than 30% team absence</p>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 gap-2 max-h-96 overflow-y-auto">
                {calendar.calendar.filter(day => !day.is_weekend && day.leaves.length > 0).map((day) => (
                  <div
                    key={day.date}
                    className={`border rounded-lg p-3 ${
                      day.available_count < calendar.team_size * 0.7
                        ? 'border-red-300 bg-red-50'
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div>
                        <span className="font-medium text-gray-900">{new Date(day.date).toLocaleDateString()}</span>
                        <span className="text-sm text-gray-500 ml-2">({day.day_of_week})</span>
                      </div>
                      <div className="text-sm">
                        <span className="font-medium text-gray-900">{day.available_count}/{calendar.team_size}</span>
                        <span className="text-gray-600 ml-1">available</span>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {day.leaves.map((leave, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                        >
                          {leave.employee_name} ({leave.leave_type})
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Insights Tab */}
          {activeTab === 'insights' && insights && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Team Insights</h2>
                <select
                  value={insightsPeriod}
                  onChange={(e) => {
                    setInsightsPeriod(e.target.value as any);
                    setTimeout(refreshInsights, 100);
                  }}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="last_30_days">Last 30 Days</option>
                  <option value="last_quarter">Last Quarter</option>
                  <option value="current_year">Current Year</option>
                </select>
              </div>

              {/* AI Insights */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <TrendingUp className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-blue-900 mb-1">AI Analysis</h3>
                    <p className="text-sm text-blue-800">{insights.insights}</p>
                  </div>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Total Leaves</p>
                  <p className="text-2xl font-bold text-gray-900">{insights.summary.total_leaves}</p>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Total Days</p>
                  <p className="text-2xl font-bold text-gray-900">{insights.summary.total_days}</p>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Avg per Person</p>
                  <p className="text-2xl font-bold text-gray-900">{insights.summary.avg_days_per_person}</p>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Most Common</p>
                  <p className="text-lg font-bold text-gray-900">{insights.summary.most_common_leave_type}</p>
                </div>
              </div>

              {/* Risks */}
              {insights.risks.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Risk Alerts</h3>
                  <div className="space-y-3">
                    {insights.risks.map((risk, idx) => (
                      <div
                        key={idx}
                        className={`border rounded-lg p-4 ${
                          risk.severity === 'HIGH' || risk.severity === 'CRITICAL'
                            ? 'border-red-300 bg-red-50'
                            : 'border-yellow-300 bg-yellow-50'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <AlertTriangle
                            className={`h-5 w-5 mt-0.5 ${
                              risk.severity === 'HIGH' || risk.severity === 'CRITICAL'
                                ? 'text-red-600'
                                : 'text-yellow-600'
                            }`}
                          />
                          <div className="flex-1">
                            <div className="flex justify-between items-start">
                              <p className="font-medium text-gray-900">{risk.message}</p>
                              <span
                                className={`px-2 py-1 rounded text-xs font-medium ${
                                  risk.severity === 'HIGH' || risk.severity === 'CRITICAL'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-yellow-100 text-yellow-800'
                                }`}
                              >
                                {risk.severity}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                              Affects {risk.affected_count} team member(s)
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Member Breakdown */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Individual Breakdown</h3>
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Leaves</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Days</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {insights.member_breakdown.map((member) => (
                        <tr key={member.employee_id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{member.name}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{member.position}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{member.leaves_taken}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{member.days_taken}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Forecast Tab */}
          {activeTab === 'forecast' && forecast && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Availability Forecast</h2>
                  <p className="text-sm text-gray-600">Plan ahead based on confirmed and pending leaves</p>
                </div>
                <select
                  value={forecastDays}
                  onChange={(e) => {
                    setForecastDays(Number(e.target.value));
                    setTimeout(refreshForecast, 100);
                  }}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={30}>30 days</option>
                  <option value={60}>60 days</option>
                </select>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Team Size</p>
                  <p className="text-2xl font-bold text-gray-900">{forecast.team_size}</p>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Avg Availability</p>
                  <p className="text-2xl font-bold text-green-600">{forecast.avg_availability}%</p>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Critical Periods</p>
                  <p className="text-2xl font-bold text-red-600">{forecast.critical_periods}</p>
                </div>
              </div>

              <div className="space-y-2">
                {forecast.forecast.filter(day => !day.is_weekend).map((day) => (
                  <div
                    key={day.date}
                    className={`border rounded-lg p-4 ${
                      day.capacity_level === 'CRITICAL'
                        ? 'border-red-300 bg-red-50'
                        : day.capacity_level === 'LIMITED'
                        ? 'border-yellow-300 bg-yellow-50'
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-medium text-gray-900">{new Date(day.date).toLocaleDateString()}</span>
                        <span className="text-sm text-gray-500 ml-2">({day.day_of_week})</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm text-gray-600">Available</p>
                          <p className="text-lg font-bold text-gray-900">{day.available_count}/{forecast.team_size}</p>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            day.capacity_level === 'FULL'
                              ? 'bg-green-100 text-green-800'
                              : day.capacity_level === 'GOOD'
                              ? 'bg-blue-100 text-blue-800'
                              : day.capacity_level === 'LIMITED'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {day.capacity_level}
                        </span>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-sm">
                      <span className="text-gray-600">
                        Approved absences: <span className="font-medium">{day.approved_absences}</span>
                      </span>
                      {day.pending_absences > 0 && (
                        <span className="text-orange-600">
                          Pending: <span className="font-medium">{day.pending_absences}</span>
                        </span>
                      )}
                    </div>
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            day.capacity_level === 'CRITICAL'
                              ? 'bg-red-600'
                              : day.capacity_level === 'LIMITED'
                              ? 'bg-yellow-600'
                              : 'bg-green-600'
                          }`}
                          style={{ width: `${day.availability_rate}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeamViewPage;