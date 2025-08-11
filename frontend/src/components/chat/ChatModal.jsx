import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Loader2, Bot, User, Sparkles, Pizza, Heart, Lightbulb, CheckCircle2, Brain, Zap, Target } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

const ChatModal = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const [userContext, setUserContext] = useState({});
  const messagesEndRef = useRef(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Start session on open
  useEffect(() => {
    const startSession = async () => {
      if (!isOpen) return;
      try {
        const res = await fetch(`${backendUrl}/api/chat/start-session`, { method: 'POST' });
        const data = await res.json();
        setSessionId(data.session_id);
        setMessages([
          {
            id: Date.now(),
            type: 'bot',
            content: data.welcome_message || "Hi! I'm your AI nutrition assistant. I can help you with food questions, health tips, and recommendations. What would you like to know?",
            timestamp: new Date(),
          },
        ]);
      } catch (e) {
        // If session creation fails, still allow chat but show error
        setMessages([
          {
            id: Date.now(),
            type: 'bot',
            content: "Welcome! You can ask me about nutrition, meals, and healthy habits.",
            timestamp: new Date(),
          },
        ]);
      }
    };
    if (isOpen && !sessionId) {
      startSession();
    }
  }, [isOpen, backendUrl, sessionId]);

  const renderFormatted = (msg) => {
    const hasStructure = msg.title || msg.summary || (msg.keyPoints && msg.keyPoints.length) || (msg.actionSteps && msg.actionSteps.length);
    if (!hasStructure) {
      // render plain text with line breaks
      return String(msg.content || '').split('\n').map((line, i) => (
        <p key={i} className="text-sm leading-relaxed">{line}</p>
      ));
    }

    return (
      <div className="space-y-2">
        {msg.title && <div className="font-semibold text-sm text-purple-700">{msg.title}</div>}
        {msg.summary && <div className="text-sm text-gray-800">{msg.summary}</div>}
        {msg.keyPoints?.length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-700 mb-1">Key points</div>
            <ul className="list-disc ml-5 space-y-1">
              {msg.keyPoints.map((kp, idx) => (
                <li key={idx} className="text-sm text-gray-800">{kp}</li>
              ))}
            </ul>
          </div>
        )}
        {msg.actionSteps?.length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-700 mb-1">Action steps</div>
            <ul className="ml-1 space-y-1">
              {msg.actionSteps.map((step, idx) => (
                <li key={idx} className="flex items-start text-sm text-gray-800">
                  <CheckCircle2 className="w-4 h-4 mr-2 mt-0.5 text-green-600 flex-shrink-0" />
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {msg.tips?.length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-700 mb-1">Tips</div>
            <ul className="list-disc ml-5 space-y-1">
              {msg.tips.map((tip, idx) => (
                <li key={idx} className="text-sm text-gray-800">{tip}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    const now = Date.now();

    const userMessage = {
      id: now,
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${backendUrl}/api/chat/send-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId || `session_${now}`,
          message: userMessage.content,
          context_type: 'health_and_nutrition',
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');
      const data = await response.json();

      const botMessage = {
        id: now + 1,
        type: 'bot',
        content: data.response,
        timestamp: new Date(),
        suggestions: data.suggestions || [],
        quickActions: data.quick_actions || [],
        // structured fields
        title: data.title,
        summary: data.summary,
        keyPoints: data.key_points,
        actionSteps: data.action_steps,
        tips: data.tips,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: "I'm sorry, I'm having trouble responding right now. Please try again in a moment.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickQuestions = [
    { icon: Pizza, text: "What's a healthy breakfast?", question: "What would you recommend for a healthy breakfast?" },
    { icon: Heart, text: 'Tips for better nutrition', question: 'Can you give me some tips for better nutrition?' },
    { icon: Lightbulb, text: 'How many calories do I need?', question: 'How do I calculate how many calories I need per day?' },
  ];

  const handleQuickQuestion = (question) => {
    setInputMessage(question);
    setTimeout(() => sendMessage(), 50);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl h-[600px] flex flex-col">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 border-b">
          <CardTitle className="flex items-center text-lg font-semibold">
            <Bot className="w-5 h-5 mr-2 text-purple-600" />
            Quick Chat - AI Nutrition Assistant
            <Sparkles className="w-4 h-4 ml-2 text-purple-400" />
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent className="flex flex-col flex-1 p-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                  <div className={`px-4 py-2 rounded-lg ${message.type === 'user' ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-900'}`}>
                    <div className="flex items-start space-x-2">
                      {message.type === 'bot' && <Bot className="w-4 h-4 mt-1 text-purple-600 flex-shrink-0" />}
                      {message.type === 'user' && <User className="w-4 h-4 mt-1 text-white flex-shrink-0" />}
                      <div className="space-y-2 w-full">
                        {message.type === 'bot' ? (
                          renderFormatted(message)
                        ) : (
                          <p className="text-sm leading-relaxed">{message.content}</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Suggestions and Quick Actions */}
                  {message.suggestions && message.suggestions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {message.suggestions.map((s, idx) => (
                        <Button key={idx} size="sm" variant="secondary" onClick={() => handleQuickQuestion(s)} className="text-xs">
                          {s}
                        </Button>
                      ))}
                    </div>
                  )}

                  {message.quickActions && message.quickActions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {message.quickActions.map((action, idx) => (
                        <Button key={idx} size="sm" variant="outline" onClick={() => console.log('Quick action:', action)} className="text-xs">
                          {action.label}
                        </Button>
                      ))}
                    </div>
                  )}

                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-2 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Bot className="w-4 h-4 text-purple-600" />
                    <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                    <span className="text-sm text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {messages.length &lt;= 1 && (
            <div className="border-t bg-gray-50 p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Questions:</h4>
              <div className="space-y-2">
                {quickQuestions.map((item, idx) => (
                  <Button key={idx} variant="ghost" size="sm" onClick={() => handleQuickQuestion(item.question)} className="w-full justify-start h-auto p-3 text-left hover:bg-purple-50">
                    <item.icon className="w-4 h-4 mr-3 text-purple-600 flex-shrink-0" />
                    <span className="text-sm">{item.text}</span>
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="border-t p-4">
            <div className="flex space-x-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about food, nutrition, or health..."
                className="flex-1 resize-none border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                rows="2"
                disabled={isLoading}
              />
              <Button onClick={sendMessage} disabled={!inputMessage.trim() || isLoading} className="bg-purple-600 hover:bg-purple-700 text-white px-4">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatModal;