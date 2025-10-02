import { useAppSelector } from '../store/hooks';

export const useAuth = () => {
  const { user, token, loading, error } = useAppSelector((state) => state.auth);
  
  return {
    user,
    token,
    loading,
    error,
    isAuthenticated: !!token && !!user,
    isEmployee: user?.role === 'Employee',
    isManager: user?.role === 'Manager',
    isHR: user?.role === 'HR',
  };
};