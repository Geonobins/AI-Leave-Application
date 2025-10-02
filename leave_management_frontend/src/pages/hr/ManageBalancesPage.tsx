import { useState, useEffect } from 'react';
import { 
  Users, 
  Plus, 
  Edit, 
  Trash2, 
  Search, 
  RefreshCw,
  Upload,
  X
} from 'lucide-react';
import { hrApi, type LeaveBalance, LeaveType, type User, type LeaveBalanceCreate } from '../../api/endpoints/hr.api';

const ManageBalancesPage = () => {
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [editingBalance, setEditingBalance] = useState<LeaveBalance | null>(null);

  const [createForm, setCreateForm] = useState<LeaveBalanceCreate>({
    employee_id: 0,
    year: new Date().getFullYear(),
    leave_type: LeaveType.ANNUAL,
    total_allocated: 0
  });

  const [bulkForm, setBulkForm] = useState({
    year: new Date().getFullYear(),
    leave_allocations: {
      [LeaveType.ANNUAL]: 20,
      [LeaveType.SICK]: 10,
      [LeaveType.CASUAL]: 5,
      [LeaveType.MATERNITY]: 90,
      [LeaveType.PATERNITY]: 15,
      [LeaveType.UNPAID]: 0
    }
  });

  useEffect(() => {
    loadData();
  }, [selectedYear]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [balancesData, usersData] = await Promise.all([
        hrApi.getAllLeaveBalances(selectedYear),
        hrApi.getAllUsers()
      ]);
      setBalances(balancesData);
      setUsers(usersData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBalance = async () => {
    try {
      await hrApi.createLeaveBalance(createForm);
      setShowCreateModal(false);
      loadData();
      alert('Leave balance created successfully!');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create balance');
    }
  };

  const handleUpdateBalance = async (balanceId: number, newTotal: number) => {
    try {
      await hrApi.updateLeaveBalance(balanceId, { total_allocated: newTotal });
      loadData();
      setEditingBalance(null);
      alert('Balance updated successfully!');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update balance');
    }
  };

  const handleDeleteBalance = async (balanceId: number) => {
    if (!confirm('Are you sure you want to delete this balance?')) return;
    
    try {
      await hrApi.deleteLeaveBalance(balanceId);
      loadData();
      alert('Balance deleted successfully!');
    } catch (error) {
      alert('Failed to delete balance');
    }
  };

  const handleBulkCreate = async () => {
    if (!confirm(`Create leave balances for all active employees for year ${bulkForm.year}?`)) return;
    
    try {
      const result = await hrApi.bulkCreateLeaveBalances(bulkForm);
      setShowBulkModal(false);
      loadData();
      alert(`Success! Created ${result.balances_created} balances for ${result.employees_processed} employees.`);
    } catch (error) {
      alert('Failed to create bulk balances');
    }
  };

  const handleResetBalances = async (employeeId: number) => {
    if (!confirm('Reset all balances for this employee? This will set used days to 0.')) return;
    
    try {
      await hrApi.resetEmployeeBalances(employeeId, selectedYear);
      loadData();
      alert('Balances reset successfully!');
    } catch (error) {
      alert('Failed to reset balances');
    }
  };

  const groupedBalances = balances.reduce((acc, balance) => {
    const user = users.find(u => u.id === balance.employee_id);
    if (!user) return acc;
    
    if (!acc[balance.employee_id]) {
      acc[balance.employee_id] = {
        user,
        balances: []
      };
    }
    acc[balance.employee_id].balances.push(balance);
    return acc;
  }, {} as Record<number, { user: User; balances: LeaveBalance[] }>);

  const filteredEmployees = Object.values(groupedBalances).filter(({ user }) =>
    user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.department.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const leaveTypeColors: Record<LeaveType, string> = {
    [LeaveType.ANNUAL]: 'bg-blue-100 text-blue-800',
    [LeaveType.SICK]: 'bg-red-100 text-red-800',
    [LeaveType.CASUAL]: 'bg-green-100 text-green-800',
    [LeaveType.MATERNITY]: 'bg-purple-100 text-purple-800',
    [LeaveType.PATERNITY]: 'bg-indigo-100 text-indigo-800',
    [LeaveType.UNPAID]: 'bg-gray-100 text-gray-800'
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Manage Leave Balances</h1>
        <p className="text-gray-600 mt-2">Configure and manage leave allocations for all employees</p>
      </div>

      {/* Action Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex gap-3 flex-wrap">
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus size={20} />
              Add Balance
            </button>
            <button
              onClick={() => setShowBulkModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Upload size={20} />
              Bulk Create
            </button>
            <button
              onClick={loadData}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              <RefreshCw size={20} />
              Refresh
            </button>
          </div>

          <div className="flex gap-3 items-center">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search employees..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border rounded-lg w-64"
              />
            </div>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="px-4 py-2 border rounded-lg"
            >
              {[2023, 2024, 2025, 2026].map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Total Employees</div>
          <div className="text-2xl font-bold">{Object.keys(groupedBalances).length}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Total Balances</div>
          <div className="text-2xl font-bold">{balances.length}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Total Allocated</div>
          <div className="text-2xl font-bold">{balances.reduce((sum, b) => sum + b.total_allocated, 0)}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Total Available</div>
          <div className="text-2xl font-bold text-green-600">{balances.reduce((sum, b) => sum + b.available, 0)}</div>
        </div>
      </div>

      {/* Balances List */}
      {loading ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading balances...</p>
        </div>
      ) : filteredEmployees.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Users size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600">No leave balances found for {selectedYear}</p>
          <button
            onClick={() => setShowBulkModal(true)}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Balances for All Employees
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredEmployees.map(({ user, balances }) => (
            <div key={user.id} className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-gray-50 px-6 py-4 flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-lg">{user.full_name}</h3>
                  <p className="text-sm text-gray-600">{user.position} - {user.department}</p>
                </div>
                <button
                  onClick={() => handleResetBalances(user.id)}
                  className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                >
                  <RefreshCw size={16} />
                  Reset Balances
                </button>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {balances.map(balance => (
                    <div key={balance.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${leaveTypeColors[balance.leave_type]}`}>
                          {balance.leave_type}
                        </span>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditingBalance(balance)}
                            className="text-gray-400 hover:text-blue-600"
                          >
                            <Edit size={16} />
                          </button>
                          <button
                            onClick={() => handleDeleteBalance(balance.id)}
                            className="text-gray-400 hover:text-red-600"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Allocated:</span>
                          <span className="font-semibold">{balance.total_allocated} days</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Used:</span>
                          <span className="font-semibold text-orange-600">{balance.used} days</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Available:</span>
                          <span className="font-semibold text-green-600">{balance.available} days</span>
                        </div>
                        <div className="mt-2 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${(balance.used / balance.total_allocated) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Balance Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Create Leave Balance</h2>
              <button onClick={() => setShowCreateModal(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Employee</label>
                <select
                  value={createForm.employee_id}
                  onChange={(e) => setCreateForm({ ...createForm, employee_id: Number(e.target.value) })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value={0}>Select Employee</option>
                  {users.filter(u => u.is_active).map(user => (
                    <option key={user.id} value={user.id}>
                      {user.full_name} - {user.department}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Year</label>
                <input
                  type="number"
                  value={createForm.year}
                  onChange={(e) => setCreateForm({ ...createForm, year: Number(e.target.value) })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Leave Type</label>
                <select
                  value={createForm.leave_type}
                  onChange={(e) => setCreateForm({ ...createForm, leave_type: e.target.value as LeaveType })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {Object.values(LeaveType).map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Total Allocated (days)</label>
                <input
                  type="number"
                  value={createForm.total_allocated}
                  onChange={(e) => setCreateForm({ ...createForm, total_allocated: Number(e.target.value) })}
                  className="w-full border rounded-lg px-3 py-2"
                  min="0"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleCreateBalance}
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                  disabled={createForm.employee_id === 0}
                >
                  Create
                </button>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Create Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Bulk Create Leave Balances</h2>
              <button onClick={() => setShowBulkModal(false)}>
                <X size={24} />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              This will create leave balances for all active employees
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Year</label>
                <input
                  type="number"
                  value={bulkForm.year}
                  onChange={(e) => setBulkForm({ ...bulkForm, year: Number(e.target.value) })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              <div className="space-y-3">
                <label className="block text-sm font-medium">Leave Allocations (days)</label>
                {Object.entries(bulkForm.leave_allocations).map(([type, days]) => (
                  <div key={type} className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium w-24 ${leaveTypeColors[type as LeaveType]}`}>
                      {type}
                    </span>
                    <input
                      type="number"
                      value={days}
                      onChange={(e) => setBulkForm({
                        ...bulkForm,
                        leave_allocations: {
                          ...bulkForm.leave_allocations,
                          [type]: Number(e.target.value)
                        }
                      })}
                      className="flex-1 border rounded-lg px-3 py-2"
                      min="0"
                    />
                  </div>
                ))}
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleBulkCreate}
                  className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
                >
                  Create for All Employees
                </button>
                <button
                  onClick={() => setShowBulkModal(false)}
                  className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Balance Modal */}
      {editingBalance && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Edit Leave Balance</h2>
              <button onClick={() => setEditingBalance(null)}>
                <X size={24} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Leave Type</label>
                <div className={`px-3 py-2 rounded ${leaveTypeColors[editingBalance.leave_type]}`}>
                  {editingBalance.leave_type}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Current Used Days</label>
                <div className="px-3 py-2 bg-gray-100 rounded">
                  {editingBalance.used} days
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Total Allocated (days)</label>
                <input
                  type="number"
                  defaultValue={editingBalance.total_allocated}
                  id="edit-allocated"
                  className="w-full border rounded-lg px-3 py-2"
                  min={editingBalance.used}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Must be at least {editingBalance.used} (days already used)
                </p>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    const input = document.getElementById('edit-allocated') as HTMLInputElement;
                    handleUpdateBalance(editingBalance.id, Number(input.value));
                  }}
                  className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                >
                  Update
                </button>
                <button
                  onClick={() => setEditingBalance(null)}
                  className="flex-1 bg-gray-200 py-2 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManageBalancesPage;