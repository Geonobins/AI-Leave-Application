import axiosInstance from '../axiosConfig';

export const authApi = {
  login: async (credentials: any): Promise<any> => {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await axiosInstance.post<any>('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  register: async (data: any): Promise<any> => {
    const response = await axiosInstance.post<any>('/auth/register', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<any> => {
    const response = await axiosInstance.get<any>('/auth/me');
    return response.data;
  },
};