export const storage = {
    getToken: (): string | null => {
      return localStorage.getItem('access_token');
    },
    
    setToken: (token: string): void => {
      localStorage.setItem('access_token', token);
    },
    
    removeToken: (): void => {
      localStorage.removeItem('access_token');
    },
    
    getUser: (): any => {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    },
    
    setUser: (user: any): void => {
      localStorage.setItem('user', JSON.stringify(user));
    },
    
    removeUser: (): void => {
      localStorage.removeItem('user');
    },
    
    clear: (): void => {
      localStorage.clear();
    },
  };