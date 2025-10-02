export const validateEmail = (email: string): boolean => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };
  
  export const validatePassword = (password: string): string | null => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!/[0-9]/.test(password)) {
      return 'Password must contain at least one number';
    }
    return null;
  };
  
  export const validateDateRange = (startDate: string, endDate: string): string | null => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (start > end) {
      return 'End date must be after start date';
    }
    
    if (start < new Date()) {
      return 'Start date cannot be in the past';
    }
    
    return null;
  };