import { useState, useEffect } from 'react';
import { Edit2, UserCheck, UserX, Save, X } from 'lucide-react';
import { hrApi, type User } from '../../api/endpoints/hr.api';


const ManageUsersPage = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [managers, setManagers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingUser, setEditingUser] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ role: '', manager_id: '' });
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchUsers();
    fetchManagers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await hrApi.getAllUsers();
      setUsers(data);
    } catch (error) {
      setErrorMessage('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const fetchManagers = async () => {
    try {
      const data = await hrApi.getAllManagers();
      setManagers(data);
    } catch (error) {
      console.error('Failed to fetch managers');
    }
  };

  const handleEdit = (user: User) => {
    setEditingUser(user.id);
    setEditForm({
      role: user.role,
      manager_id: user.manager_id?.toString() || '',
    });
  };

  const handleCancelEdit = () => {
    setEditingUser(null);
    setEditForm({ role: '', manager_id: '' });
  };

  const handleSave = async (userId: number) => {
    try {
      const user = users.find(u => u.id === userId);
      if (!user) return;

      // Update role if changed
      if (editForm.role !== user.role) {
        await hrApi.updateUserRole(userId, {
          user_id: userId,
          new_role: editForm.role,
        });
      }

      // Update manager if changed
      const newManagerId = editForm.manager_id ? parseInt(editForm.manager_id) : 0;
      if (newManagerId !== (user.manager_id || 0)) {
        await hrApi.updateUserManager(userId, {
          user_id: userId,
          new_manager_id: newManagerId,
        });
      }

      setSuccessMessage('User updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
      setEditingUser(null);
      fetchUsers();
    } catch (error: any) {
      setErrorMessage(error.response?.data?.detail || 'Failed to update user');
      setTimeout(() => setErrorMessage(''), 3000);
    }
  };

  const handleToggleStatus = async (userId: number) => {
    try {
      await hrApi.toggleUserStatus(userId);
      setSuccessMessage('User status updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
      fetchUsers();
    } catch (error: any) {
      setErrorMessage(error.response?.data?.detail || 'Failed to toggle user status');
      setTimeout(() => setErrorMessage(''), 3000);
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'HR':
        return 'bg-purple-100 text-purple-800';
      case 'MANAGER':
        return 'bg-blue-100 text-blue-800';
      case 'EMPLOYEE':
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoleDisplayName = (role: string) => {
    switch (role) {
      case 'EMPLOYEE':
        return 'Employee';
      case 'MANAGER':
        return 'Manager';
      case 'HR':
        return 'HR';
      default:
        return role;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Manage Users</h1>
        <p className="text-gray-600 mt-1">View and manage all users in the system</p>
      </div>

      {successMessage && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {errorMessage}
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Manager
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className={!user.is_active ? 'bg-gray-50 opacity-60' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
                          {user.full_name.charAt(0).toUpperCase()}
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingUser === user.id ? (
                      <select
                        value={editForm.role}
                        onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                        className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="EMPLOYEE">Employee</option>
                        <option value="MANAGER">Manager</option>
                        <option value="HR">HR</option>
                      </select>
                    ) : (
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleBadgeColor(user.role)}`}>
                        {getRoleDisplayName(user.role)}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{user.department}</div>
                    <div className="text-sm text-gray-500">{user.position}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingUser === user.id ? (
                      <select
                        value={editForm.manager_id}
                        onChange={(e) => setEditForm({ ...editForm, manager_id: e.target.value })}
                        className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">No Manager</option>
                        {managers
                          .filter(m => m.id !== user.id)
                          .map(manager => (
                            <option key={manager.id} value={manager.id}>
                              {manager.full_name} ({manager.role})
                            </option>
                          ))}
                      </select>
                    ) : (
                      <span className="text-sm text-gray-900">
                        {managers.find(m => m.id === user.manager_id)?.full_name || 'None'}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {editingUser === user.id ? (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSave(user.id)}
                          className="text-green-600 hover:text-green-900"
                          title="Save"
                        >
                          <Save className="w-5 h-5" />
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="text-gray-600 hover:text-gray-900"
                          title="Cancel"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(user)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit"
                        >
                          <Edit2 className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleToggleStatus(user.id)}
                          className={user.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}
                          title={user.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {user.is_active ? <UserX className="w-5 h-5" /> : <UserCheck className="w-5 h-5" />}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ManageUsersPage;