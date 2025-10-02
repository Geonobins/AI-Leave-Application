import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { employeesApi } from '../../api';

interface LeavesState {
  leaves: any[];
  balances: any[];
  loading: boolean;
  error: string | null;
}

const initialState: LeavesState = {
  leaves: [],
  balances: [],
  loading: false,
  error: null,
};

export const fetchLeaves = createAsyncThunk('leaves/fetchLeaves', async (_, { rejectWithValue }) => {
  try {
    return await employeesApi.getMyLeaves();
  } catch (error: any) {
    return rejectWithValue(error.response?.data?.detail || 'Failed to fetch leaves');
  }
});

export const fetchBalances = createAsyncThunk('leaves/fetchBalances', async (_, { rejectWithValue }) => {
  try {
    return await employeesApi.getLeaveBalances();
  } catch (error: any) {
    return rejectWithValue(error.response?.data?.detail || 'Failed to fetch balances');
  }
});

export const createLeave = createAsyncThunk(
  'leaves/createLeave',
  async (leave: any, { rejectWithValue }) => {
    try {
      return await employeesApi.createLeave(leave);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create leave');
    }
  }
);

const leavesSlice = createSlice({
  name: 'leaves',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchLeaves.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchLeaves.fulfilled, (state, action) => {
        state.loading = false;
        state.leaves = action.payload;
      })
      .addCase(fetchLeaves.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchBalances.fulfilled, (state, action) => {
        state.balances = action.payload;
      })
      .addCase(createLeave.fulfilled, (state, action) => {
        state.leaves.unshift(action.payload);
      });
  },
});

export const { clearError } = leavesSlice.actions;
export default leavesSlice.reducer;