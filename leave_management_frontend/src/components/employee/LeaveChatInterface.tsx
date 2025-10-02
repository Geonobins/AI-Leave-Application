import { useState, useRef, useEffect } from 'react';
import { Send, Users } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { sendMessage, addUserMessage } from '../../features/chat/chatSlice';
import { employeesApi } from '../../api';

const LeaveChatInterface = () => {
  const dispatch = useAppDispatch();
  const { messages, currentLeaveData, suggestedPersons, isComplete, loading } = useAppSelector(
    (state) => state.chat
  );
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    dispatch(addUserMessage(input));
    
    const request = {
      message: input,
      chat_history: messages,
      context: currentLeaveData,
    };

    setInput('');
    await dispatch(sendMessage(request));
  };

  const handleSubmit = async () => {
    if (!isComplete) return;

    try {
      await employeesApi.createLeave({
        leave_type: currentLeaveData.leave_type,
        start_date: currentLeaveData.start_date,
        end_date: currentLeaveData.end_date,
        reason: currentLeaveData.reason || '',
        responsible_person_id: currentLeaveData.responsible_person_id,
      });
      alert('Leave request submitted successfully!');
    } catch (error) {
      console.error('Failed to submit leave:', error);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-t-lg">
        <h2 className="text-xl font-bold">Request Leave</h2>
        <p className="text-sm text-blue-100">Tell me about your leave plans...</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg:any, idx:any) => (
          <div
            key={idx}
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
              <span className="text-xs opacity-70 mt-1 block">
                {new Date(msg.timestamp!).toLocaleTimeString()}
              </span>
            </div>
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

      {/* Suggested Persons */}
      {suggestedPersons.length > 0 && (
        <div className="border-t border-gray-200 p-3 bg-blue-50">
          <p className="text-xs font-medium text-gray-700 mb-2 flex items-center gap-1">
            <Users className="w-3 h-3" />
            Suggested handover contacts:
          </p>
          <div className="flex gap-2 flex-wrap">
            {suggestedPersons.map((person:any) => (
              <button
                key={person.id}
                className="px-3 py-1 bg-white border border-blue-300 rounded-full text-xs hover:bg-blue-100"
              >
                {person.name} - {person.position}
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
          placeholder="e.g., I need sick leave tomorrow"
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

      {/* Submit Button */}
      {isComplete && (
        <div className="border-t border-gray-200 p-4 bg-green-50">
          <button
            onClick={handleSubmit}
            className="w-full py-3 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600"
          >
            Submit Leave Request
          </button>
        </div>
      )}
    </div>
  );
};

export default LeaveChatInterface;