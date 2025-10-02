import axiosInstance from '../axiosConfig';
// import { any, any } from '@/types';

export const aiApi = {
  suggestDates: async (durationDays: number): Promise<{ suggestions: any[] }> => {
    const response = await axiosInstance.get('/ai/suggest-dates', {
      params: { duration_days: durationDays },
    });
    return response.data;
  },

  suggestResponsiblePerson: async (
    startDate: string,
    endDate: string
  ): Promise<{ suggestions: any[] }> => {
    const response = await axiosInstance.get('/ai/responsible-person-suggestions', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },
};