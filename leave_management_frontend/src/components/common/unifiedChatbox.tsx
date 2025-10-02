// components/common/UnifiedChatBox.tsx
import { useState, useRef, useEffect } from 'react';
import { Send, CheckCircle } from 'lucide-react';
import { useAppSelector } from '../../store/hooks';
import { employeesApi } from '../../api';

// interface LeaveData {
//   leave_type?: string;
//   start_date?: string;
//   end_date?: string;
//   reason?: string;
//   is_complete?: boolean;
//   needs_clarification?: boolean;
// }

interface PendingLeave {
  leave_type: string;
  start_date: string;
  end_date: string;
  reason?: string;
  responsible_person_id?: number;
  suggested_persons?: Array<{
    id: number;
    name: string;
    position: string;
    reason: string;
  }>;
}

const UnifiedChatBox = () => {
  const { user } = useAppSelector((state) => state.auth);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [pendingLeave, setPendingLeave] = useState<PendingLeave | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const initialSuggestions = getRoleSuggestions(user?.role);
    setSuggestions(initialSuggestions);
  }, [user]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getRoleSuggestions = (role?: string) => {
    if (role === 'HR') {
      return ['Show pending approvals', 'Department analytics', 'Who is on leave today?'];
    } else if (role === 'MANAGER') {
      return ['Team status', 'Pending approvals', 'Show my team leaves'];
    }
    return ['Request leave', 'Check my balance', 'Show my leaves'];
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await employeesApi.conversationLeave({
        message: input,
        chat_history: messages,
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        data: response.data,
        intent: response.intent,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setSuggestions(response.actions || []);

      // Check if this is a complete leave request
      if (response.intent === 'REQUEST_LEAVE' && response.data?.is_complete) {
        const leaveData = response.data.leave_data;
        const suggestedPersons = response.data.suggested_responsible_persons || [];
        
        setPendingLeave({
          leave_type: leaveData.leave_type,
          start_date: leaveData.start_date,
          end_date: leaveData.end_date,
          reason: leaveData.reason,
          suggested_persons: suggestedPersons,
        });
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitLeave = async () => {
    if (!pendingLeave) return;

    setSubmitting(true);
    try {
      // Call the actual POST endpoint
      await employeesApi.createLeave({
        leave_type: pendingLeave.leave_type,
        start_date: pendingLeave.start_date,
        end_date: pendingLeave.end_date,
        reason: pendingLeave.reason,
        responsible_person_id: pendingLeave.responsible_person_id,
      });

      // Show success message
      const successMessage = {
        role: 'assistant',
        content: '✅ Your leave request has been submitted successfully! Your manager will review it soon.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, successMessage]);
      
      // Clear pending leave
      setPendingLeave(null);
      setSuggestions(['Check my leaves', 'Check my balance']);
    } catch (error: any) {
      console.error('Submit error:', error);
      const errorMessage = {
        role: 'assistant',
        content: `❌ Failed to submit: ${error.response?.data?.detail || 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSelectResponsiblePerson = (personId: number) => {
    if (pendingLeave) {
      setPendingLeave({
        ...pendingLeave,
        responsible_person_id: personId,
      });

      const confirmMessage = {
        role: 'assistant',
        content: `Great! I've selected ${pendingLeave.suggested_persons?.find(p => p.id === personId)?.name} as the responsible person. You can now submit your leave request.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, confirmMessage]);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <p className="text-lg font-medium mb-2">How can I help you today?</p>
            <p className="text-sm">Try asking me about leaves, balances, or approvals</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx}>
            <div
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>

            {/* Show responsible person selection */}
            {msg.intent === 'REQUEST_LEAVE' && 
             msg.data?.is_complete && 
             msg.data?.suggested_responsible_persons?.length > 0 && 
             pendingLeave && 
             !pendingLeave.responsible_person_id && (
              <div className="mt-3 ml-4 max-w-[70%]">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-xs font-medium text-blue-900 mb-2">
                    Select responsible person:
                  </p>
                  <div className="space-y-2">
                    {msg.data.suggested_responsible_persons.map((person: any) => (
                      <button
                        key={person.id}
                        onClick={() => handleSelectResponsiblePerson(person.id)}
                        className="w-full text-left px-3 py-2 bg-white border border-blue-300 rounded-md hover:bg-blue-100 text-xs"
                      >
                        <div className="font-medium text-gray-900">{person.name}</div>
                        <div className="text-gray-600">{person.position} • {person.reason}</div>
                      </button>
                    ))}
                    <button
                      onClick={() => setPendingLeave({ ...pendingLeave, responsible_person_id: undefined })}
                      className="w-full text-left px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-100 text-xs text-gray-600"
                    >
                      Skip (no responsible person)
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Show submit button when leave is complete */}
            {msg.intent === 'REQUEST_LEAVE' && 
             msg.data?.is_complete && 
             (
              <div className="mt-3 ml-4">
                <button
                  onClick={handleSubmitLeave}
                  disabled={submitting}
                  className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 text-sm font-medium"
                >
                  <CheckCircle className="w-4 h-4" />
                  {submitting ? 'Submitting...' : 'Submit Leave Request'}
                </button>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && !pendingLeave && (
        <div className="border-t border-gray-200 p-3 bg-gray-50">
          <p className="text-xs font-medium text-gray-700 mb-2">Suggestions:</p>
          <div className="flex gap-2 flex-wrap">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-1 bg-white border border-gray-300 rounded-full text-xs hover:bg-blue-50 hover:border-blue-300"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-gray-200 p-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your message..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default UnifiedChatBox;