import { useState, useEffect, useRef } from 'react';
import { Send, Mic, ChevronDown, ChevronUp, CheckCircle, AlertCircle, AlertTriangle, Calendar, Plus, User, Umbrella } from 'lucide-react';
import { useAppSelector } from '../../store/hooks';
import { employeesApi } from '../../api';

// Mock hooks and API for demonstration


// Greeting Component with Quick Actions
const GreetingCard = ({ onQuickAction, disabled }: any) => {
  return (
    <div className={`relative bg-white/5 backdrop-blur-xl rounded-3xl p-4 md:p-8 mb-4 border border-white/10 shadow-2xl transition-all duration-500 ${disabled ? 'opacity-30 pointer-events-none' : 'hover:bg-white/8'}`}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-3xl" />
      <div className="relative">
        <h2 className="text-2xl md:text-3xl font-light text-white mb-2 tracking-wide">Welcome</h2>
        <p className="text-white/60 text-xs md:text-sm mb-4 md:mb-6 font-light">How may I assist you today?</p>
        
        <div className="flex flex-wrap gap-2 md:gap-3">
          <button
            onClick={() => onQuickAction('Apply for Leave')}
            disabled={disabled}
            className="px-4 md:px-6 py-2 md:py-2.5 bg-white/10 backdrop-blur-md text-white rounded-full text-xs md:text-sm font-light border border-white/20 hover:bg-white/15 hover:border-white/30 transition-all duration-300 disabled:cursor-not-allowed shadow-lg"
          >
            Apply for Leave
          </button>
          <button
            onClick={() => onQuickAction('Check Status')}
            disabled={disabled}
            className="px-4 md:px-6 py-2 md:py-2.5 bg-white/10 backdrop-blur-md text-white rounded-full text-xs md:text-sm font-light border border-white/20 hover:bg-white/15 hover:border-white/30 transition-all duration-300 disabled:cursor-not-allowed shadow-lg"
          >
            Check Status
          </button>
          <button
            onClick={() => onQuickAction('Cancel Request')}
            disabled={disabled}
            className="px-4 md:px-6 py-2 md:py-2.5 bg-white/10 backdrop-blur-md text-white rounded-full text-xs md:text-sm font-light border border-white/20 hover:bg-white/15 hover:border-white/30 transition-all duration-300 disabled:cursor-not-allowed shadow-lg"
          >
            Cancel Request
          </button>
        </div>
      </div>
    </div>
  );
};

// Leave Type Selector Component
const LeaveTypeSelector = ({ onSelect, disabled }: any) => {
  const leaveTypes = [
    { type: 'ANNUAL', label: 'Vacation', icon: Umbrella },
    { type: 'SICK', label: 'Sick Leave', icon: Plus },
    { type: 'CASUAL', label: 'Personal Day', icon: User },
  ];

  return (
    <div className={`relative bg-white/5 backdrop-blur-xl rounded-3xl p-4 md:p-8 mb-4 border border-white/10 shadow-2xl transition-all duration-500 ${disabled ? 'opacity-30 pointer-events-none' : ''}`}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-3xl" />
      <div className="relative">
        <h3 className="text-xl md:text-2xl font-light text-white mb-2 tracking-wide">Leave Type</h3>
        <p className="text-white/50 text-xs md:text-sm mb-4 md:mb-6 font-light">Select your leave category</p>
        
        <div className="space-y-2 md:space-y-3">
          {leaveTypes.map(({ type, label, icon: Icon }) => (
            <button
              key={type}
              onClick={() => onSelect(type)}
              disabled={disabled}
              className="w-full flex items-center justify-between p-4 md:p-5 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 group disabled:cursor-not-allowed shadow-lg"
            >
              <div className="flex items-center gap-3 md:gap-4">
                <div className="p-1.5 md:p-2 bg-white/10 rounded-xl">
                  <Icon className="w-4 h-4 md:w-5 md:h-5 text-white/80" />
                </div>
                <span className="text-white font-light text-base md:text-lg">{label}</span>
              </div>
              <ChevronDown className="w-4 h-4 md:w-5 md:h-5 text-white/40 group-hover:text-white/60 transition-colors rotate-[-90deg]" />
            </button>
          ))}
          
          <div className="grid grid-cols-2 gap-2 md:gap-3 pt-2">
            <button
              onClick={() => onSelect('MATERNITY')}
              disabled={disabled}
              className="px-3 md:px-4 py-3 md:py-3.5 bg-white/5 backdrop-blur-md text-white/70 rounded-xl text-xs md:text-sm font-light border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 disabled:cursor-not-allowed"
            >
              Maternity/Paternity
            </button>
            <button
              onClick={() => onSelect('UNPAID')}
              disabled={disabled}
              className="px-3 md:px-4 py-3 md:py-3.5 bg-white/5 backdrop-blur-md text-white/70 rounded-xl text-xs md:text-sm font-light border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 disabled:cursor-not-allowed"
            >
              Other
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Date Picker Component
const DatePickerCard = ({ onDateSelect, leaveType, disabled }: any) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedDates, setSelectedDates] = useState<number[]>([]);

  const getDaysInMonth = () => {
    const date = new Date();
    const year = date.getFullYear();
    const month = date.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    return Array.from({ length: daysInMonth }, (_, i) => i + 1);
  };

  const handleDateClick = (day: number) => {
    if (disabled) return;
    
    const date = new Date();
    date.setDate(day);
    const dateStr = date.toISOString().split('T')[0];
    
    if (selectedDates.length === 0) {
      setSelectedDates([day]);
      setStartDate(dateStr);
    } else if (selectedDates.length === 1) {
      const newDates = [selectedDates[0], day].sort((a, b) => a - b);
      setSelectedDates(newDates);
      
      const start = new Date();
      start.setDate(newDates[0]);
      const end = new Date();
      end.setDate(newDates[1]);
      
      setStartDate(start.toISOString().split('T')[0]);
      setEndDate(end.toISOString().split('T')[0]);
    } else {
      setSelectedDates([day]);
      setStartDate(dateStr);
      setEndDate('');
    }
  };

  const isDateSelected = (day: number) => {
    if (selectedDates.length === 2) {
      return day >= selectedDates[0] && day <= selectedDates[1];
    }
    return selectedDates.includes(day);
  };

  const handleSubmit = () => {
    if (startDate && endDate && !disabled) {
      onDateSelect(startDate, endDate);
    }
  };

  const calculateDuration = () => {
    if (!startDate || !endDate) return 0;
    const days = Math.ceil((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24)) + 1;
    return days;
  };

  return (
    <div className={`relative bg-white/5 backdrop-blur-xl rounded-3xl p-4 md:p-8 mb-4 border border-white/10 shadow-2xl transition-all duration-500 ${disabled ? 'opacity-30 pointer-events-none' : ''}`}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-3xl" />
      <div className="relative">
        <h3 className="text-xl md:text-2xl font-light text-white mb-4 md:mb-6 tracking-wide">Select Dates</h3>
        
        <div className="bg-white/5 backdrop-blur-md rounded-2xl p-4 md:p-5 mb-4 md:mb-5 border border-white/10">
          <div className="flex items-center justify-between mb-3 md:mb-4">
            <Calendar className="w-4 h-4 md:w-5 md:h-5 text-white/60" />
            <span className="text-white/80 font-light text-xs md:text-sm tracking-wider">CALENDAR</span>
            <div className="w-4 md:w-5" />
          </div>
          
          <div className="grid grid-cols-7 gap-1 md:gap-2 text-center mb-2 md:mb-3">
            {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, idx) => (
              <div key={idx} className="text-white/40 text-xs font-light py-1 tracking-wide">{day}</div>
            ))}
          </div>
          
          <div className="grid grid-cols-7 gap-1 md:gap-2 text-center">
            {getDaysInMonth().map((day) => (
              <button
                key={day}
                onClick={() => handleDateClick(day)}
                disabled={disabled}
                className={`w-8 h-8 md:w-10 md:h-10 rounded-xl text-xs md:text-sm font-light transition-all duration-300 disabled:cursor-not-allowed ${
                  isDateSelected(day)
                    ? 'bg-white/20 text-white border border-white/30 shadow-lg' 
                    : 'text-white/60 hover:bg-white/10 border border-transparent hover:border-white/20'
                }`}
              >
                {day}
              </button>
            ))}
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-5">
          <div>
            <label className="text-xs text-white/40 mb-2 block font-light tracking-wide">START DATE</label>
            <input
              type="text"
              value={startDate ? new Date(startDate).toLocaleDateString('en-GB') : ''}
              readOnly
              placeholder="dd/mm/yyyy"
              className="w-full px-3 md:px-4 py-2.5 md:py-3 bg-white/5 backdrop-blur-md text-white rounded-xl text-xs md:text-sm border border-white/10 focus:border-white/30 outline-none transition-all font-light placeholder-white/30"
            />
          </div>
          <div>
            <label className="text-xs text-white/40 mb-2 block font-light tracking-wide">END DATE</label>
            <input
              type="text"
              value={endDate ? new Date(endDate).toLocaleDateString('en-GB') : ''}
              readOnly
              placeholder="dd/mm/yyyy"
              className="w-full px-3 md:px-4 py-2.5 md:py-3 bg-white/5 backdrop-blur-md text-white rounded-xl text-xs md:text-sm border border-white/10 focus:border-white/30 outline-none transition-all font-light placeholder-white/30"
            />
          </div>
        </div>
        
        <div className="text-xs md:text-sm text-white/60 mb-4 md:mb-5 font-light">
          Duration: <span className="text-white font-normal">{calculateDuration()}</span> working days
        </div>
        
        <button
          onClick={handleSubmit}
          disabled={!startDate || !endDate || disabled}
          className="w-full px-4 md:px-6 py-3 md:py-3.5 bg-white/10 backdrop-blur-md text-white rounded-xl text-sm md:text-base font-light border border-white/20 hover:bg-white/15 hover:border-white/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300 shadow-lg tracking-wide"
        >
          Confirm Selection
        </button>
      </div>
    </div>
  );
};

// Confirmation Card Component
const ConfirmationCard = ({ leaveData, onConfirm, onEdit, disabled, isSubmitting }: any) => {
  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      day: '2-digit', 
      month: '2-digit', 
      year: 'numeric' 
    });
  };

  const calculateDuration = () => {
    if (!leaveData.start_date || !leaveData.end_date) return 0;
    const days = Math.ceil((new Date(leaveData.end_date).getTime() - new Date(leaveData.start_date).getTime()) / (1000 * 60 * 60 * 24)) + 1;
    return days;
  };

  return (
    <div className={`relative bg-white/5 backdrop-blur-xl rounded-3xl p-4 md:p-8 mb-4 border border-white/10 shadow-2xl transition-all duration-500 ${disabled ? 'opacity-30 pointer-events-none' : ''}`}>
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-3xl" />
      <div className="relative">
        <h3 className="text-xl md:text-2xl font-light text-white mb-4 md:mb-6 tracking-wide">
          Confirm Details
        </h3>
        
        <div className="space-y-3 md:space-y-4 mb-6 md:mb-8">
          <div className="flex justify-between items-center p-3 md:p-4 bg-white/5 backdrop-blur-md rounded-xl border border-white/10">
            <span className="text-xs md:text-sm text-white/50 font-light tracking-wide">TYPE</span>
            <span className="text-white font-light text-sm md:text-base">
              {leaveData.leave_type?.replace('_', ' ')}
            </span>
          </div>
          <div className="flex justify-between items-center p-3 md:p-4 bg-white/5 backdrop-blur-md rounded-xl border border-white/10">
            <span className="text-xs md:text-sm text-white/50 font-light tracking-wide">START</span>
            <span className="text-white font-light text-xs md:text-sm">
              {formatDate(leaveData.start_date)}
            </span>
          </div>
          <div className="flex justify-between items-center p-3 md:p-4 bg-white/5 backdrop-blur-md rounded-xl border border-white/10">
            <span className="text-xs md:text-sm text-white/50 font-light tracking-wide">END</span>
            <span className="text-white font-light text-xs md:text-sm">
              {formatDate(leaveData.end_date)}
            </span>
          </div>
          <div className="flex justify-between items-center p-3 md:p-4 bg-white/5 backdrop-blur-md rounded-xl border border-white/10">
            <span className="text-xs md:text-sm text-white/50 font-light tracking-wide">DURATION</span>
            <span className="text-white font-light text-sm md:text-base">
              {calculateDuration()} day{calculateDuration() !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
        
        <div className="flex gap-2 md:gap-3">
          <button
            onClick={onConfirm}
            disabled={disabled || isSubmitting}
            className="flex-1 px-4 md:px-6 py-3 md:py-3.5 bg-white/10 backdrop-blur-md text-white rounded-xl text-sm md:text-base font-light border border-white/20 hover:bg-white/15 hover:border-white/30 transition-all duration-300 shadow-lg disabled:cursor-not-allowed disabled:opacity-30 flex items-center justify-center gap-2 tracking-wide"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Processing</span>
              </>
            ) : (
              'Submit Request'
            )}
          </button>
          <button
            onClick={onEdit}
            disabled={disabled || isSubmitting}
            className="px-4 md:px-6 py-3 md:py-3.5 bg-white/5 backdrop-blur-md text-white/70 rounded-xl text-sm md:text-base font-light border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300 disabled:cursor-not-allowed tracking-wide"
          >
            Edit
          </button>
        </div>
      </div>
    </div>
  );
};

// Policy Compliance Badge
const PolicyComplianceBadge = ({ compliance }: any) => {
  const [showDetails, setShowDetails] = useState(false);

  if (!compliance) return null;

  if (compliance.compliant) {
    return (
      <div className="bg-white/5 backdrop-blur-xl border border-white/20 rounded-2xl p-4 md:p-5 mb-4 shadow-lg">
        <div className="flex items-center gap-2 md:gap-3">
          <div className="p-1.5 md:p-2 bg-white/10 rounded-lg">
            <CheckCircle className="w-4 h-4 md:w-5 md:h-5 text-white/80" />
          </div>
          <span className="text-xs md:text-sm font-light text-white tracking-wide">Policy Compliant</span>
        </div>
      </div>
    );
  }

  if (!compliance.violations?.length) return null;

  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/20 rounded-2xl mb-4 overflow-hidden shadow-lg">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full flex items-center justify-between gap-2 p-4 md:p-5 hover:bg-white/10 transition-all duration-300"
      >
        <div className="flex items-center gap-2 md:gap-3">
          <div className="p-1.5 md:p-2 bg-white/10 rounded-lg">
            <AlertCircle className="w-4 h-4 md:w-5 md:h-5 text-white/80" />
          </div>
          <span className="text-xs md:text-sm font-light text-white tracking-wide">
            {compliance.violations.length} Policy Violation{compliance.violations.length !== 1 ? 's' : ''}
          </span>
        </div>
        {showDetails ? (
          <ChevronUp className="w-4 h-4 text-white/60" />
        ) : (
          <ChevronDown className="w-4 h-4 text-white/60" />
        )}
      </button>

      {showDetails && (
        <div className="border-t border-white/10 p-4 md:p-5 space-y-4 bg-white/5">
          <div>
            <h4 className="text-xs font-light text-white/50 mb-3 uppercase tracking-wider">Violations</h4>
            <ul className="space-y-2 max-h-40 overflow-y-auto">
              {compliance.violations.slice(0, 5).map((violation: string, index: number) => (
                <li key={index} className="text-xs text-white/70 flex items-start gap-2 font-light">
                  <span className="text-white/40 mt-0.5">•</span>
                  <span>{violation}</span>
                </li>
              ))}
            </ul>
          </div>

          {compliance.warnings?.length > 0 && (
            <div className="pt-3 border-t border-white/10">
              <h4 className="text-xs font-light text-white/50 mb-3 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-3 h-3" />
                Warnings
              </h4>
              <ul className="space-y-2">
                {compliance.warnings.slice(0, 3).map((warning: string, index: number) => (
                  <li key={index} className="text-xs text-white/70 flex items-start gap-2 font-light">
                    <span className="text-white/40 mt-0.5">⚠</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main Chat Dashboard
const ChatDashboard = () => {
  const { user } = useAppSelector((state: any) => state.auth);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeComponentIndex, setActiveComponentIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([{
      role: 'assistant',
      content: `Welcome back! How can I help you today?`,
      timestamp: new Date(),
      ui_state: { component: 'GREETING', stage: 'GREETING', show_quick_actions: true },
      index: 0
    }]);
    setActiveComponentIndex(0);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (messageText = input) => {
    if (!messageText.trim() || loading) return;

    const userMessage = { role: 'user', content: messageText, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await employeesApi.conversationLeave({
        message: messageText,
        chat_history: messages,
      });

      let uiState = response.ui_state;
      if (!uiState && response.data?.leave_data?.ui_state) {
        uiState = response.data.leave_data.ui_state;
      }

      const newIndex = messages.length + 1;
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        data: response.data,
        intent: response.intent,
        ui_state: uiState,
        index: newIndex
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setActiveComponentIndex(newIndex);
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'An error occurred. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = (action: string) => {
    handleSend(action);
  };

  const handleLeaveTypeSelect = (type: string) => {
    handleSend(`I need ${type.toLowerCase()} leave`);
  };

  const handleDateSelect = (startDate: string, endDate: string) => {
    handleSend(`From ${startDate} to ${endDate}`);
  };

  const handleConfirmLeave = async (leaveData: any) => {
    setIsSubmitting(true);
    
    try {
      const leaveRequest = {
        leave_type: leaveData.leave_type,
        start_date: leaveData.start_date,
        end_date: leaveData.end_date,
        reason: leaveData.reason || 'Leave request via Aurora AI',
      };

      const response = await employeesApi.createLeave(leaveRequest);

      const successMessage = {
        role: 'assistant',
        content: `Request submitted successfully.\n\nType: ${leaveData.leave_type}\nDuration: ${leaveData.start_date} to ${leaveData.end_date}\nStatus: Pending Approval\n\nYou will be notified once reviewed.`,
        timestamp: new Date(),
        data: { leave_request: response },
      };

      setMessages((prev) => [...prev, successMessage]);
      setActiveComponentIndex(null);
    } catch (error: any) {
      console.error('Leave submission error:', error);
      
      const errorMessage = {
        role: 'assistant',
        content: `Failed to submit request. ${error.response?.data?.message || 'Please contact HR for assistance.'}`,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderDynamicComponent = (msg: any) => {
    const component = msg.ui_state?.component;
    const data = msg.data;
    const isDisabled = msg.index !== activeComponentIndex;

    if (component === 'GREETING') {
      return <GreetingCard onQuickAction={handleQuickAction} disabled={isDisabled} />;
    }

    if (component === 'TYPE_SELECTOR') {
      return <LeaveTypeSelector onSelect={handleLeaveTypeSelect} disabled={isDisabled} />;
    }

    if (component === 'DATE_PICKER') {
      const leaveType = data?.leave_data?.leave_type || data?.leave_type;
      return (
        <DatePickerCard
          leaveType={leaveType}
          onDateSelect={handleDateSelect}
          disabled={isDisabled}
        />
      );
    }

    if (component === 'CONFIRMATION_CARD') {
      const leaveData = data?.leave_data || data;
      return (
        <ConfirmationCard
          leaveData={leaveData}
          onConfirm={() => handleConfirmLeave(leaveData)}
          onEdit={() => handleSend('edit')}
          disabled={isDisabled}
          isSubmitting={isSubmitting}
        />
      );
    }

    const policyCompliance = data?.policy_compliance || data?.leave_data?.policy_compliance;
    if (policyCompliance) {
      return <PolicyComplianceBadge compliance={policyCompliance} />;
    }

    return null;
  };

  return (
    <div className="min-h-screen inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Animated background effect */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.05),transparent_50%)] pointer-events-none" />
      
      {/* Header */}
      <div className="relative h-[80px]  z-10">
        
      </div>

      {/* Messages Area */}
      <div className="relative flex-1 overflow-y-auto px-3 md:px-6 py-4 md:py-8 space-y-4 md:space-y-6 pb-24 md:pb-28">
        {messages.map((msg: any, idx: number) => (
          <div key={idx}>
            {msg.role === 'user' ? (
              <div className="flex justify-end">
                <div className="max-w-[85%] md:max-w-[75%] bg-white/10 backdrop-blur-xl text-white rounded-3xl rounded-tr-lg px-4 md:px-6 py-3 md:py-4 shadow-xl border border-white/20">
                  <p className="text-xs md:text-sm font-light leading-relaxed">{msg.content}</p>
                </div>
              </div>
            ) : (
              <div className="flex justify-start">
                <div className="max-w-[95%] md:max-w-[90%] w-full">
                  {renderDynamicComponent(msg)}
                  {!msg.ui_state?.component && (
                    <div className="bg-white/5 backdrop-blur-xl text-white rounded-3xl rounded-tl-lg px-4 md:px-6 py-3 md:py-4 shadow-xl border border-white/10">
                      <p className="text-xs md:text-sm font-light leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white/5 backdrop-blur-xl rounded-3xl rounded-tl-lg px-4 md:px-6 py-3 md:py-4 shadow-xl border border-white/10">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Footer branding */}
      <div className="relative text-center py-2 md:py-3 text-white/30 text-[10px] md:text-xs font-light tracking-widest">
        POWERED BY AURORA AI
      </div>

      {/* Input Bar */}
      <div className="fixed bottom-0 backdrop-blur-md w-full px-3 md:px-6 py-3 md:py-4">
        <div className="bg-white/10 backdrop-blur-2xl rounded-full shadow-2xl p-1.5 md:p-2 max-w-3xl mx-auto border border-white/20">
          <div className="flex items-center gap-2 md:gap-3">
            <button className="p-2 md:p-2.5 hover:bg-white/10 rounded-full transition-all duration-300 flex-shrink-0">
              <Mic className="w-4 h-4 md:w-5 md:h-5 text-white/60" />
            </button>
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your message..."
              className="flex-1 px-3 md:px-4 py-2.5 md:py-3 bg-transparent border-none focus:outline-none text-xs md:text-sm text-white placeholder-white/30 font-light"
              disabled={loading}
            />
            
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="p-2 md:p-2.5 bg-white/20 backdrop-blur-md text-white rounded-full hover:bg-white/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300 shadow-lg flex-shrink-0 border border-white/30"
            >
              <Send className="w-4 h-4 md:w-5 md:h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatDashboard;