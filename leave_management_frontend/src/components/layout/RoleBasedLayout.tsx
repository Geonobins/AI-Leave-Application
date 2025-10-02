import { Outlet } from 'react-router-dom';
import { useAppSelector } from '../../store/hooks';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

const RoleBasedLayout = () => {
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar fixed at top */}
      <div className="fixed top-0 left-0 right-0 h-20 z-50">
        <Navbar />
      </div>

      <div className="flex">
        {/* Sidebar fixed on left, below navbar */}
        {sidebarOpen && (
          <div className="fixed top-20 left-0 h-[calc(100vh-80px)] w-64 z-40">
            <Sidebar />
          </div>
        )}

        {/* Main content */}
        <main
          className={`flex-1 p-6 mt-20 transition-all overflow-y-auto 
            ${sidebarOpen ? 'ml-64' : 'ml-0'}
          `}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default RoleBasedLayout;
