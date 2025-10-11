import { Outlet } from 'react-router-dom';
import { useAppSelector } from '../../store/hooks';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

const RoleBasedLayout = () => {
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  return (
    <div className="min-h-screen bg-gray-50 relative overflow-hidden">
      {/* Navbar fixed at top */}
      <div className="fixed top-0 left-0 right-0 h-20 z-50">
        <Navbar />
      </div>

      {/* Sidebar overlay (always on top of main content) */}
      {sidebarOpen && (
        <div className="fixed top-20 left-0 w-64  z-40 shadow-lg ">
          <Sidebar />
        </div>
      )}

      {/* Main content area (under sidebar visually) */}
      <main
        className={` overflow-y-auto transition-all duration-300 `}
      >
        <Outlet />
      </main>
    </div>
  );
};

export default RoleBasedLayout;
