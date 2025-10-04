// components/layout/Sidebar.tsx
import { BarChart2, FileText, Home, Users, UserCog, Shield } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAppSelector } from "../../store/hooks";

const Sidebar = () => {
  const { user } = useAppSelector((state) => state.auth);

  const commonLinks = [
    { to: '/dashboard', icon: <Home className="w-5 h-5" />, label: 'Dashboard' },
    { to: '/my-leaves', icon: <FileText className="w-5 h-5" />, label: 'My Leaves' },
    { to: '/leave-balance', icon: <BarChart2 className="w-5 h-5" />, label: 'Leave Balance' },
  ];

  // Role-specific additional links
  const roleLinks = {
    MANAGER: [
      { to: '/team-view', icon: <Users className="w-5 h-5" />, label: 'Team View' },
    ],
    HR: [
      { to: '/analytics', icon: <BarChart2 className="w-5 h-5" />, label: 'Analytics' },
      { to: '/manage-balances', icon: <FileText className="w-5 h-5" />, label: 'Manage Balances' },
      { to: '/manage-users', icon: <UserCog className="w-5 h-5" />, label: 'Manage Users' },
      { to: '/manage-policies', icon: <Shield className="w-5 h-5" />, label: 'Policy Management' },
    ]
  };

  const links = [
    ...commonLinks,
    ...(user?.role ? roleLinks[user.role as keyof typeof roleLinks] || [] : [])
  ];

  return (
    <aside className="bg-white w-64 min-h-screen shadow-lg">
      <nav className="p-4">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors mb-1 ${
                isActive
                  ? 'bg-blue-50 text-blue-600 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              }`
            }
          >
            {link.icon}
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;