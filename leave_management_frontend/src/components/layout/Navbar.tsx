import { useNavigate } from 'react-router-dom';
import { Menu, LogOut, User, X } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { logout } from '../../features/auth/authSlice';
import { toggleSidebar } from '../../features/ui/uiSlice';

const Navbar = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const handleLogout = () => {
    setShowUserMenu(false);
    dispatch(logout());
    navigate('/login');
  };

  const handleToggleSidebar = () => {
    dispatch(toggleSidebar());
  };

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <>
      <nav className=" h-[80px] backdrop-blur-sm relative">
        <div className="px-4 sm:px-6 py-3 h-full flex items-center justify-between">
          {/* Left Section */}
          <div className="flex items-center gap-3 sm:gap-4 w-full">
            <button
              onClick={handleToggleSidebar}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors backdrop-blur-sm:block"
              aria-label="Toggle sidebar"
            >
              <Menu className="w-5 h-5 text-white" />
            </button>

           

            <h1 className="text-lg sm:text-xl font-light  text-white flex-1  flex justify-center items-center w-full">
              <span>
              alibi.ai
              </span>
              </h1>
          </div>

          {/* Right Section - Desktop */}
          <div className="hidden md:flex items-center gap-4 min-w-fit">
            <div className="flex items-center gap-3 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20">
              <div className="w-8 h-8 bg-gradient-to-br from-slate-900 to-slate-900 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="text-sm">
                <p className="font-medium text-white">{user?.full_name || 'User'}</p>
                <p className="text-slate-300 text-xs">{user?.role || 'Employee'}</p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="p-2.5 hover:bg-red-500/20 text-red-300 hover:text-red-200 rounded-full transition-all backdrop-blur-sm border border-red-400/20 hover:border-red-400/40"
              aria-label="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>

          {/* Right Section - Mobile */}
          <div className="flex md:hidden items-center relative" ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu((prev) => !prev)}
              className="w-8 h-8 bg-gradient-to-br from-slate-900 to-slate-900 rounded-full flex items-center justify-center"
            >
              <User className="w-4 h-4 text-white" />
            </button>

            {/* Mobile User Menu */}
            {showUserMenu && (
              <div
                className="absolute right-0 top-12 w-40 bg-slate-800/90 backdrop-blur-xl border border-white/10 rounded-xl shadow-lg overflow-hidden animate-fadeIn z-50"
              >
                <div className="px-4 py-3 border-b border-white/10">
                  <p className="text-sm font-medium text-white">{user?.full_name || 'User'}</p>
                  <p className="text-xs text-slate-400">{user?.role || 'Employee'}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2.5 text-red-300 hover:text-red-100 hover:bg-red-500/10 flex items-center gap-2 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>
    </>
  );
};

export default Navbar;
