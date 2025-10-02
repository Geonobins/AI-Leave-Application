import { useState, useRef, useEffect } from 'react';
import { Send, BarChart3, Users, Calendar, TrendingUp } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { sendHRMessage, addHRUserMessage } from '../../features/hr/hrSlice';

const HRChatInterface = () => {
  const dispatch = useAppDispatch();
  const { messages, currentData, suggestedActions, loading } = useAppSelector((state) => state.hr);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickActions = [
    { icon: <Users className="w-4 h-4" />, text: "Who's on leave today?", color: "bg-blue-500" },
    { icon: <Calendar className="w-4 h-4" />, text: "Show pending approvals", color: "bg-yellow-500" },
    { icon: <TrendingUp className="w-4 h-4" />, text: "Leave trends this month", color: "bg-purple-500" },
    { icon: <BarChart3 className="w-4 h-4" />, text: "Backend team availability", color: "bg-green-500" },
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (message = input) => {
    if (!message.trim() || loading) return;

    dispatch(addHRUserMessage(message));

    const request = {
      message,
      chat_history: messages,
      context: {},
    };

    setInput('');
    await dispatch(sendHRMessage(request));
  };

  return (
    <div className="flex flex-col h-[700px] bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-t-lg">
        <h2 className="text-xl font-bold">HR Assistant</h2>
        <p className="text-sm text-blue-100">AI-powered leave management & analytics</p>
      </div>

      {/* Quick Actions */}
      <div className="border-b border-gray-200 p-3 bg-gray-50">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {quickActions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(action.text)}
              className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:shadow-md transition-all text-sm font-medium text-gray-700 whitespace-nowrap"
            >
              <span className={`p-1 ${action.color} text-white rounded`}>
                {action.icon}
              </span>
              {action.text}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="mb-2">Ask me anything about leaves, approvals, or analytics</p>
            <p className="text-sm">Try: "Who's on leave today?" or "Show pending approvals"</p>
          </div>
        )}

        {messages.map((msg:any, idx:any) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Actions */}
      {suggestedActions.length > 0 && !loading && (
        <div className="border-t border-gray-200 p-3 bg-blue-50">
          <p className="text-xs font-medium text-gray-700 mb-2">Suggested actions:</p>
          <div className="flex gap-2 flex-wrap">
            {suggestedActions.map((action:any, idx:any) => (
              <button
                key={idx}
                onClick={() => handleSend(action)}
                className="px-3 py-1.5 bg-white border border-blue-300 rounded-full text-xs font-medium text-blue-700 hover:bg-blue-50"
              >
                {action}
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
          placeholder="Ask about leaves, approvals, analytics..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default HRChatInterface;