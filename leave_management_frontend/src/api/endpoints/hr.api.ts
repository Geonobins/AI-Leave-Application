  import axiosInstance from '../axiosConfig';

  export interface CompanyPolicy {
    id: number;
    filename: string;
    file_type: string;
    upload_date: string;
    uploaded_by: number;
    is_active: boolean;
    version: number;
    extracted_text?: string;
    embedding_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
    effective_date?: string;
    policy_type: string;
  }
  
  export interface PolicyDetails extends CompanyPolicy {
    chunks_count: number;
    preview?: string;
  }
  
  export interface PolicyStats {
    total_policies: number;
    active_policies: number;
    policy_types: Array<{ type: string; count: number }>;
    total_chunks: number;
  }
  
  export interface PolicyQueryResult {
    chunk_id: number;
    policy_id: number;
    policy_name: string;
    content: string;
    section_title?: string;
    similarity: number;
  }
  
  export interface PolicyQueryResponse {
    query: string;
    results: PolicyQueryResult[];
  }
  
  export interface ComplianceCheckRequest {
    leave_request: {
      leave_type: string;
      start_date: string;
      end_date: string;
      reason: string;
      notice_days: number;
    };
  }
  
  export interface ComplianceCheckResponse {
    compliant: boolean;
    violations: string[];
    warnings: string[];
    relevant_policies: Array<{
      section_title?: string;
      content: string;
      policy_name: string;
    }>;
  }
  
  export interface PolicyUploadResponse {
    message: string;
    policy_id: number;
    chunks_created: number;
    filename: string;
  }

  

  export interface User {
    id: number;
    email: string;
    username: string;
    full_name: string;
    role: string;
    department: string;
    position: string;
    manager_id: number | null;
    is_active: boolean;
  }

  export interface RoleUpdate {
    user_id: number;
    new_role: string;
  }

  export interface ManagerUpdate {
    user_id: number;
    new_manager_id: number;
  }

  // ===== LEAVE BALANCE TYPES =====

  export enum LeaveType {
    ANNUAL = 'ANNUAL',
    SICK = 'SICK',
    CASUAL = 'CASUAL',
    MATERNITY = 'MATERNITY',
    PATERNITY = 'PATERNITY',
    UNPAID = 'UNPAID'
  }

  export interface LeaveBalance {
    id: number;
    employee_id: number;
    year: number;
    leave_type: LeaveType;
    total_allocated: number;
    used: number;
    available: number;
  }

  export interface LeaveBalanceCreate {
    employee_id: number;
    year: number;
    leave_type: LeaveType;
    total_allocated: number;
  }

  export interface LeaveBalanceUpdate {
    total_allocated: number;
  }

  export interface LeaveBalanceBulkUpdate {
    year: number;
    leave_allocations: Record<LeaveType, number>;
  }

  export interface EmployeeBalanceSummary {
    employee_id: number;
    employee_name: string;
    year: number | null;
    balances: LeaveBalance[];
    total_allocated: number;
    total_used: number;
    total_available: number;
  }

  // Analytics Types
  export interface AnalyticsRequest {
    timeframe?: string;
    department?: string;
    include_predictions?: boolean;
  }

  export interface AnalyticsSummary {
    total_requests: number;
    approved_requests: number;
    total_days_taken: number;
    avg_duration: number;
    approval_rate: number;
    active_employees: number;
    departments: Record<string, { count: number; days: number }>;
  }

  export interface Trend {
    monthly_trend: Array<{ month: string; requests: number; days: number }>;
    leave_types: Record<string, number>;
    day_of_week: Record<string, number>;
    departments: Record<string, any>;
    seasonal: Record<string, any>;
  }

  export interface Prediction {
    next_90_days: Array<{
      month: string;
      predicted_requests: number;
      predicted_days: number;
    }>;
    high_demand_periods: Array<{
      month: string;
      expected_requests: number;
      above_average: number;
    }>;
    likely_leave_requests: Array<{
      employee: string;
      department: string;
      available_days: number;
      likelihood: string;
      reason: string;
    }>;
    prediction_confidence: string;
  }

  export interface Risk {
    type: string;
    severity: string;
    description: string;
    impact: string;
    recommendation?: string;
    department?: string;
    employee?: string;
  }

  export interface Recommendation {
    priority: string;
    category: string;
    title: string;
    description: string;
    actions: string[];
    impact: string;
  }

  export interface AnalyticsResponse {
    summary: AnalyticsSummary;
    trends: Trend;
    predictions: Prediction;
    risks: {
      critical_risks: Risk[];
      high_risks: Risk[];
      medium_risks: Risk[];
      total_risks: number;
      risk_score: number;
    };
    recommendations: Recommendation[];
    insights: string;
  }

  export interface DepartmentComparison {
    department: string;
    total_leaves: number;
    total_days: number;
    employee_count: number;
    avg_leaves_per_employee: number;
    avg_days_per_employee: number;
  }

  export interface BurnoutIndicator {
    employee_id: number;
    employee_name: string;
    department: string;
    position: string;
    risk_score: number;
    risk_level: string;
    risk_factors: string[];
    days_taken_6m: number;
    leave_utilization: number;
    available_days: number;
  }

  export interface CoverageGap {
    date: string;
    department: string;
    absent_count: number;
    department_size: number;
    absence_rate: number;
    severity: string;
    absent_employees: Array<{
      employee: string;
      position: string;
    }>;
  }

  export const hrApi = {
    // ===== USER MANAGEMENT =====
    
    // Get all users
    getAllUsers: async (): Promise<User[]> => {
      const response = await axiosInstance.get('/hr/users');
      return response.data;
    },

    // Get a specific user by ID
    getUserById: async (userId: number): Promise<User> => {
      const response = await axiosInstance.get(`/hr/users/${userId}`);
      return response.data;
    },

    // Update user role
    updateUserRole: async (userId: number, roleData: RoleUpdate): Promise<{ message: string; user: User }> => {
      const response = await axiosInstance.put(`/hr/users/${userId}/role`, roleData);
      return response.data;
    },

    // Update user manager
    updateUserManager: async (userId: number, managerData: ManagerUpdate): Promise<{ message: string; user: User }> => {
      const response = await axiosInstance.put(`/hr/users/${userId}/manager`, managerData);
      return response.data;
    },

    // Toggle user active status
    toggleUserStatus: async (userId: number): Promise<{ message: string; user: User }> => {
      const response = await axiosInstance.put(`/hr/users/${userId}/activate`);
      return response.data;
    },

    // Get all managers (users with Manager or HR role)
    getAllManagers: async (): Promise<User[]> => {
      const response = await axiosInstance.get('/hr/managers');
      return response.data;
    },

    // ===== LEAVE BALANCE MANAGEMENT =====
    
    // Get all leave balances with optional filters
    getAllLeaveBalances: async (year?: number, employeeId?: number): Promise<LeaveBalance[]> => {
      const params = new URLSearchParams();
      if (year) params.append('year', year.toString());
      if (employeeId) params.append('employee_id', employeeId.toString());
      
      const response = await axiosInstance.get(`/hr/leave-balances?${params.toString()}`);
      return response.data;
    },

    // Get a specific leave balance by ID
    getLeaveBalance: async (balanceId: number): Promise<LeaveBalance> => {
      const response = await axiosInstance.get(`/hr/leave-balances/${balanceId}`);
      return response.data;
    },

    // Create a new leave balance
    createLeaveBalance: async (data: LeaveBalanceCreate): Promise<LeaveBalance> => {
      const response = await axiosInstance.post('/hr/leave-balances', data);
      return response.data;
    },

    // Update a leave balance
    updateLeaveBalance: async (balanceId: number, data: LeaveBalanceUpdate): Promise<LeaveBalance> => {
      const response = await axiosInstance.put(`/hr/leave-balances/${balanceId}`, data);
      return response.data;
    },

    // Delete a leave balance
    deleteLeaveBalance: async (balanceId: number): Promise<void> => {
      await axiosInstance.delete(`/hr/leave-balances/${balanceId}`);
    },

    // Bulk create leave balances for all active employees
    bulkCreateLeaveBalances: async (data: LeaveBalanceBulkUpdate): Promise<{
      message: string;
      year: number;
      employees_processed: number;
      balances_created: number;
      balances_skipped: number;
    }> => {
      const response = await axiosInstance.post('/hr/leave-balances/bulk-create', data);
      return response.data;
    },

    // Reset employee balances for a specific year
    resetEmployeeBalances: async (employeeId: number, year: number): Promise<{
      message: string;
      year: number;
      balances_reset: number;
    }> => {
      const response = await axiosInstance.put(`/hr/leave-balances/employee/${employeeId}/reset?year=${year}`);
      return response.data;
    },

    // Get employee balance summary
    getEmployeeBalanceSummary: async (employeeId: number, year?: number): Promise<EmployeeBalanceSummary> => {
      const params = year ? `?year=${year}` : '';
      const response = await axiosInstance.get(`/hr/leave-balances/employee/${employeeId}/summary${params}`);
      return response.data;
    },

    // ===== ANALYTICS =====
    
    // Get comprehensive AI-powered insights
    getAnalytics: async (request: AnalyticsRequest = {}): Promise<AnalyticsResponse> => {
      const response = await axiosInstance.post('/insights', {
        timeframe: request.timeframe || 'current_year',
        department: request.department || null,
        include_predictions: request.include_predictions !== false
      });
      return response.data;
    },

    // Get department comparison
    getDepartmentComparison: async (): Promise<{ departments: DepartmentComparison[] }> => {
      const response = await axiosInstance.get('/department-comparison');
      return response.data;
    },

    // Get burnout indicators
    getBurnoutIndicators: async (): Promise<{
      at_risk_employees: BurnoutIndicator[];
      total_at_risk: number;
      high_risk: number;
      medium_risk: number;
    }> => {
      const response = await axiosInstance.get('/burnout-indicators');
      return response.data;
    },

    // Get coverage gaps
    getCoverageGaps: async (daysAhead: number = 30): Promise<{
      coverage_gaps: CoverageGap[];
      total_gaps: number;
      days_analyzed: number;
      high_severity: number;
    }> => {
      const response = await axiosInstance.get(`/coverage-gaps?days_ahead=${daysAhead}`);
      return response.data;
    },


    uploadPolicy: async (file: File, policyType: string = 'LEAVE'): Promise<PolicyUploadResponse> => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('policy_type', policyType);
      
      const response = await axiosInstance.post('/policies/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
  
    // Get all policies
    getAllPolicies: async (): Promise<CompanyPolicy[]> => {
      const response = await axiosInstance.get('/policies');
      return response.data;
    },
  
    // Get policy details by ID
    getPolicyDetails: async (policyId: number): Promise<PolicyDetails> => {
      const response = await axiosInstance.get(`/policies/${policyId}`);
      return response.data;
    },
  
    // Delete a policy
    deletePolicy: async (policyId: number): Promise<{ message: string }> => {
      const response = await axiosInstance.delete(`/policies/${policyId}`);
      return response.data;
    },
  
    // Activate a policy
    activatePolicy: async (policyId: number): Promise<{ message: string; policy_id: number; filename: string }> => {
      const response = await axiosInstance.put(`/hr/policies/${policyId}/activate`);
      return response.data;
    },
  
    // Get active policy by type
    getActivePolicy: async (policyType: string): Promise<{ message?: string; policy: PolicyDetails | null }> => {
      const response = await axiosInstance.get(`/policies/active/${policyType}`);
      return response.data;
    },
  
    // Get policy statistics
    getPolicyStats: async (): Promise<PolicyStats> => {
      const response = await axiosInstance.get('/policies/stats');
      return response.data;
    },
  
    // Query policies (semantic search)
    queryPolicies: async (query: string, topK: number = 5): Promise<PolicyQueryResponse> => {
      const response = await axiosInstance.post('/policies/query', null, {
        params: { query, top_k: topK }
      });
      return response.data;
    },
  
    // Check leave request compliance
    checkCompliance: async (request: ComplianceCheckRequest): Promise<ComplianceCheckResponse> => {
      const response = await axiosInstance.post('/policies/check-compliance', request);
      return response.data;
    },
  };