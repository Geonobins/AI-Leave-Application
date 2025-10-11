// routes/AppRoutes.tsx
import { Routes, Route } from 'react-router-dom';
import LoginPage from '../pages/auth/LoginPage';
import RegisterPage from '../pages/auth/RegisterPage';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import RoleBasedLayout from '../components/layout/RoleBasedLayout';

// Employee Pages
import ChatDashboard from '../pages/employee/ChatDashboard';
import MyLeavesPage from '../pages/employee/MyLeavesPage';
import LeaveBalancePage from '../pages/employee/LeaveBalancePage';

// Manager Pages
import TeamViewPage from '../pages/manager/TeamViewPage';

// HR Pages
import AnalyticsPage from '../pages/hr/AnalyticsPage';
import ManageBalancesPage from '../pages/hr/ManageBalancesPage';
import ManageUsersPage from '../pages/hr/manageUserPage';
import PolicyManagementPage from '../pages/hr/PolicyManagementPage';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      
      <Route path="/" element={<ProtectedRoute><RoleBasedLayout /></ProtectedRoute>}>
        {/* Common routes - all have access to chat on dashboard */}
        <Route path="dashboard" element={<ChatDashboard />} />
        <Route path="my-leaves" element={<MyLeavesPage />} />
        <Route path="leave-balance" element={<LeaveBalancePage />} />
        
        {/* Manager/HR only */}
        <Route path="team-view" element={<ProtectedRoute requiredRole="MANAGER"><TeamViewPage /></ProtectedRoute>} />
        
        {/* HR only */}
        <Route path="analytics" element={<ProtectedRoute requiredRole="HR"><AnalyticsPage /></ProtectedRoute>} />
        <Route path="manage-balances" element={<ProtectedRoute requiredRole="HR"><ManageBalancesPage /></ProtectedRoute>} />
        <Route path="manage-users" element={<ProtectedRoute requiredRole="HR"><ManageUsersPage /></ProtectedRoute>} />
        <Route path="manage-policies" element={<ProtectedRoute requiredRole="HR"><PolicyManagementPage /></ProtectedRoute>} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;