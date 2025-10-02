import axiosInstance from '../axiosConfig';

// Types
export interface LeaveApproval {
  leave_id: number;
  approved: boolean;
  comments?: string;
}

export interface TeamMember {
  id: number;
  name: string;
  position: string;
  email: string;
  status: 'AVAILABLE' | 'ON_LEAVE';
  current_leave?: {
    type: string;
    end_date: string;
    days_remaining: number;
  } | null;
  upcoming_leaves: Array<{
    id: number;
    type: string;
    start_date: string;
    end_date: string;
    duration: number;
    status: string;
  }>;
  leave_balance: {
    total_allocated: number;
    used: number;
    available: number;
    utilization: number;
  };
}

export interface TeamOverview {
  team_members: TeamMember[];
  team_size: number;
  available_count: number;
  on_leave_count: number;
  availability_rate: number;
}

export interface CalendarDay {
  date: string;
  day_of_week: string;
  is_weekend: boolean;
  leaves: Array<{
    employee_id: number;
    employee_name: string;
    position: string;
    leave_type: string;
  }>;
  available_count: number;
}

export interface TeamCalendar {
  calendar: CalendarDay[];
  period: {
    start: string;
    end: string;
    days: number;
  };
  team_size: number;
  critical_days: number;
  max_concurrent_leaves: number;
}

export interface TeamInsights {
  summary: {
    team_size: number;
    total_leaves: number;
    total_days: number;
    avg_days_per_person: number;
    period: string;
    most_common_leave_type: string;
  };
  member_breakdown: Array<{
    employee_id: number;
    name: string;
    position: string;
    leaves_taken: number;
    days_taken: number;
  }>;
  risks: Array<{
    type: string;
    severity: string;
    message: string;
    affected_count: number;
  }>;
  insights: string;
}

export interface ForecastDay {
  date: string;
  day_of_week: string;
  is_weekend: boolean;
  available_count: number;
  potential_available: number;
  approved_absences: number;
  pending_absences: number;
  availability_rate: number;
  capacity_level: 'FULL' | 'GOOD' | 'LIMITED' | 'CRITICAL';
}

export interface AvailabilityForecast {
  forecast: ForecastDay[];
  team_size: number;
  critical_periods: number;
  avg_availability: number;
}

export const managersApi = {
  // Existing endpoints
  getPendingLeaves: async (): Promise<any[]> => {
    const response = await axiosInstance.get('/managers/pending-leaves');
    return response.data;
  },

  approveRejectLeave: async (approval: LeaveApproval): Promise<{ message: string; status: string }> => {
    const response = await axiosInstance.post('/managers/leaves/approve', approval);
    return response.data;
  },

  // New team management endpoints
  getTeamOverview: async (): Promise<TeamOverview> => {
    const response = await axiosInstance.get('/managers/team-overview');
    return response.data;
  },

  getTeamCalendar: async (daysAhead: number = 30): Promise<TeamCalendar> => {
    const response = await axiosInstance.get('/managers/team-calendar', {
      params: { days_ahead: daysAhead }
    });
    return response.data;
  },

  getTeamInsights: async (period: 'last_30_days' | 'last_quarter' | 'current_year' = 'last_30_days'): Promise<TeamInsights> => {
    const response = await axiosInstance.get('/managers/team-insights', {
      params: { period }
    });
    return response.data;
  },

  getAvailabilityForecast: async (daysAhead: number = 14): Promise<AvailabilityForecast> => {
    const response = await axiosInstance.get('/managers/team-availability-forecast', {
      params: { days_ahead: daysAhead }
    });
    return response.data;
  }
};