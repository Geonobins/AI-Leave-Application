import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { employeesApi } from '../../api';

interface ChatState {
  messages: any[];
  currentLeaveData: any;
  suggestedPersons: any[];
  isComplete: boolean;
  needsClarification: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [],
  currentLeaveData: {},
  suggestedPersons: [],
  isComplete: false,
  needsClarification: false,
  loading: false,
  error: null,
};

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async (request: any, { rejectWithValue }) => {
    try {
      return await employeesApi.conversationLeave(request);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to send message');
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addUserMessage: (state, action: PayloadAction<string>) => {
      state.messages.push({
        role: 'user',
        content: action.payload,
        timestamp: new Date(),
      });
    },
    clearChat: (state) => {
      state.messages = [];
      state.currentLeaveData = {};
      state.suggestedPersons = [];
      state.isComplete = false;
      state.needsClarification = false;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.loading = false;
        state.messages.push({
          role: 'assistant',
          content: action.payload.response,
          timestamp: new Date(),
        });
        state.currentLeaveData = action.payload.leave_data;
        state.suggestedPersons = action.payload.suggested_responsible_persons;
        state.isComplete = action.payload.is_complete;
        state.needsClarification = action.payload.needs_clarification;
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { addUserMessage, clearChat } = chatSlice.actions;
export default chatSlice.reducer;