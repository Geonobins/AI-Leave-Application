    import { Routes, Route } from 'react-router-dom';
    // import { useAppSelector } from '../store/hooks';
    import LoginPage from '../pages/auth/LoginPage';
    import RegisterPage from '../pages/auth/RegisterPage';
    import ProtectedRoute from '../components/auth/ProtectedRoute';
    import RoleBasedLayout from '../components/layout/RoleBasedLayout';

    // Employee Pages
    // import EmployeeDashboard from '../pages/employee/DashboardPage';
    // import RequestLeavePage from '../pages/employee/RequestLeavePage';
    import MyLeavesPage from '../pages/employee/MyLeavesPage';
    import LeaveBalancePage from '../pages/employee/LeaveBalancePage';

    // Manager Pages
    // import ManagerDashboard from '../pages/manager/ManagerDashboardPage';
    // import ApprovalsPage from '../pages/manager/ApprovalsPage';
    import TeamViewPage from '../pages/manager/TeamViewPage';

    // HR Pages
    // import HRDashboard from '../pages/hr/HRDashboardPage';
    // import HRConversationalPage from '../pages/hr/HRConversationalPage';
    import AnalyticsPage from '../pages/hr/AnalyticsPage';
    import ManageBalancesPage from '../pages/hr/ManageBalancesPage';

    // import NotFoundPage from '../pages/NotFoundPage';
import DashboardPage from '../pages/employee/DashboardPage';
import ManageUsersPage from '../pages/hr/manageUserPage';

   // Remove role-specific request pages
// Keep: Dashboard (with chat), My Leaves, Leave Balance, Analytics (HR), Team View (Manager/HR)

const AppRoutes = () => {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        <Route path="/" element={<ProtectedRoute><RoleBasedLayout /></ProtectedRoute>}>
          {/* Common routes - all have access to chat on dashboard */}
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="my-leaves" element={<MyLeavesPage />} />
          <Route path="leave-balance" element={<LeaveBalancePage />} />
          
          {/* Manager/HR only */}
          <Route path="team-view" element={<ProtectedRoute requiredRole="MANAGER"><TeamViewPage /></ProtectedRoute>} />
          
          {/* HR only */}
          <Route path="analytics" element={<ProtectedRoute requiredRole="HR"><AnalyticsPage /></ProtectedRoute>} />
          <Route path="manage-balances" element={<ProtectedRoute requiredRole="HR"><ManageBalancesPage /></ProtectedRoute>} />
          <Route path="manage-users" element={<ProtectedRoute requiredRole="HR"><ManageUsersPage /></ProtectedRoute>} />
        </Route>
      </Routes>
    );
  };

    export default AppRoutes;   