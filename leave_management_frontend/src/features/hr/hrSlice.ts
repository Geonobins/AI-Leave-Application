import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { hrApi } from '../../api';

interface HRState {
  messages: any[];
  currentData: any;
  suggestedActions: string[];
  loading: boolean;
  error: string | null;
}

const initialState: HRState = {
  messages: [],
  currentData: null,
  suggestedActions: [],
  loading: false,
  error: null,
};

export const sendHRMessage = createAsyncThunk(
  'hr/sendMessage',
  async (request: any, { rejectWithValue }) => {
    try {
      return await hrApi.conversation(request);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to send message');
    }
  }
);

const hrSlice = createSlice({
  name: 'hr',
  initialState,
  reducers: {
    addHRUserMessage: (state, action) => {
      state.messages.push({
        role: 'user',
        content: action.payload,
        timestamp: new Date(),
      });
    },
    clearHRChat: (state) => {
      state.messages = [];
      state.currentData = null;
      state.suggestedActions = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendHRMessage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendHRMessage.fulfilled, (state, action) => {
        state.loading = false;
        state.messages.push({
          role: 'assistant',
          content: action.payload.response,
          timestamp: new Date(),
        });
        state.currentData = action.payload.data;
        state.suggestedActions = action.payload.suggested_actions;
      })
      .addCase(sendHRMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { addHRUserMessage, clearHRChat } = hrSlice.actions;
export default hrSlice.reducer;