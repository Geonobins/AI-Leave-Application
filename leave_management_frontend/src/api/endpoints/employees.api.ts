import axiosInstance from '../axiosConfig';


export const employeesApi = {
  // Conversational leave request
  conversationLeave: async (request: any): Promise<any> => {
    const response = await axiosInstance.post<any>(
      '/conversation',
      request
    );
    return response.data;
  },

  // Create leave (traditional)
  createLeave: async (leave: any): Promise<any> => {
    const response = await axiosInstance.post<any>('/employees/leaves', leave);
    return response.data;
  },

  // Get my leaves
  getMyLeaves: async (): Promise<any[]> => {
    const response = await axiosInstance.get<any[]>('/employees/leaves');
    return response.data;
  },

  // Get specific leave
  getLeave: async (leaveId: number): Promise<any> => {
    const response = await axiosInstance.get<any>(`/employees/leaves/${leaveId}`);
    return response.data;
  },

  // Get leave balances
  getLeaveBalances: async (): Promise<any[]> => {
    const response = await axiosInstance.get<any[]>('/employees/leave-balances');
    return response.data;
  },
};