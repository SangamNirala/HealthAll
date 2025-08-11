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

  // Initialize user context from localStorage or role context
  useEffect(() => {
    const storedUserRole = localStorage.getItem('selectedRole');
    const storedUserId = localStorage.getItem('patient_user_id') || 
                        localStorage.getItem('provider_user_id') || 
                        localStorage.getItem('family_user_id') ||
                        localStorage.getItem('guest_session_id');
    
    setUserContext({
      profile_type: storedUserRole || 'general',
      user_id: storedUserId,
      health_goals: JSON.parse(localStorage.getItem('health_goals') || '[]'),
      dietary_restrictions: JSON.parse(localStorage.getItem('dietary_restrictions') || '[]'),
      interaction_count: parseInt(localStorage.getItem('chat_interaction_count') || '0')
    });
  }, []);

  // Update interaction count
  const updateInteractionCount = () => {
    const newCount = userContext.interaction_count + 1;
    setUserContext(prev => ({ ...prev, interaction_count: newCount }));
    localStorage.setItem('chat_interaction_count', newCount.toString());
  };

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
        const contextualWelcome = userContext.profile_type && userContext.profile_type !== 'general' 
          ? `Hi! I'm your enhanced AI nutrition assistant, specialized for ${userContext.profile_type} needs. I have advanced context awareness and can provide personalized guidance based on your unique situation. What would you like to explore today?`
          : data.welcome_message || "Hi! I'm your enhanced AI nutrition assistant with advanced context awareness. I can provide highly personalized guidance for food, health, and nutrition. What would you like to know?";
          
        setMessages([
          {
            id: Date.now(),
            type: 'bot',
            content: contextualWelcome,
            timestamp: new Date(),
            title: "Welcome to Enhanced AI Nutrition Chat",
            summary: contextualWelcome,
            personalization: userContext.profile_type ? `I'm configured for ${userContext.profile_type} users and will provide contextually relevant guidance.` : "I'm learning about you to provide increasingly personalized advice.",
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
      <div className="space-y-3">
        {msg.title && (
          <div className="font-semibold text-sm text-purple-700 flex items-center">
            <Brain className="w-4 h-4 mr-2" />
            {msg.title}
          </div>
        )}
        {msg.summary && <div className="text-sm text-gray-800 leading-relaxed">{msg.summary}</div>}
        
        {msg.keyPoints?.length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-700 mb-2 flex items-center">
              <Target className="w-3 h-3 mr-1" />
              Key Insights
            </div>
            <ul className="list-disc ml-5 space-y-1">
              {msg.keyPoints.map((kp, idx) => (
                <li key={idx} className="text-sm text-gray-800">{kp}</li>
              ))}
            </ul>
          </div>
        )}
        
        {msg.actionSteps?.length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-700 mb-2 flex items-center">
              <Zap className="w-3 h-3 mr-1" />
              Action Steps
            </div>
            <ul className="ml-1 space-y-2">
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
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-purple-700 mb-2 flex items-center">
              <Lightbulb className="w-3 h-3 mr-1" />
              Pro Tips
            </div>
            <ul className="space-y-1">
              {msg.tips.map((tip, idx) => (
                <li key={idx} className="text-sm text-purple-800 flex items-start">
                  <span className="text-purple-400 mr-2">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {msg.personalization && (
          <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-400">
            <div className="text-xs font-medium text-blue-700 mb-1">Personalized for you</div>
            <div className="text-sm text-blue-800">{msg.personalization}</div>
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
    setIsTyping(true);
    
    // Update interaction count
    updateInteractionCount();

    try {
      const response = await fetch(`${backendUrl}/api/chat/send-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId || `session_${now}`,
          message: userMessage.content,
          context_type: 'health_and_nutrition',
          user_context: userContext,
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');
      const data = await response.json();

      // Simulate typing delay for better UX
      setTimeout(() => {
        setIsTyping(false);
        
        const botMessage = {
          id: now + 1,
          type: 'bot',
          content: data.response,
          timestamp: new Date(),
          suggestions: data.suggestions || [],
          quickActions: data.quick_actions || [],
          // Enhanced structured fields
          title: data.title,
          summary: data.summary,
          keyPoints: data.key_points,
          actionSteps: data.action_steps,
          tips: data.tips,
          personalization: data.personalization,
          confidenceLevel: data.confidence_level,
          followUpPriority: data.follow_up_priority,
        };

        setMessages((prev) => [...prev, botMessage]);
      }, 800);
      
    } catch (error) {
      console.error('Chat error:', error);
      setIsTyping(false);
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

  const getContextualQuickQuestions = () => {
    const baseQuestions = [
      { icon: Pizza, text: "What's a healthy breakfast?", question: "What would you recommend for a healthy breakfast?" },
      { icon: Heart, text: 'Tips for better nutrition', question: 'Can you give me some tips for better nutrition?' },
      { icon: Lightbulb, text: 'How many calories do I need?', question: 'How do I calculate how many calories I need per day?' },
    ];

    // Contextual questions based on user profile
    if (userContext.profile_type === 'patient') {
      return [
        { icon: Target, text: "Clinical nutrition guidance", question: "What nutrition advice aligns with my health conditions?" },
        { icon: Heart, text: "Heart-healthy eating", question: "How can I eat for better heart health?" },
        { icon: Brain, text: "Medication and food interactions", question: "Are there foods I should avoid with my medications?" },
      ];
    } else if (userContext.profile_type === 'family') {
      return [
        { icon: Pizza, text: "Family meal planning", question: "How can I plan healthy meals for the whole family?" },
        { icon: Heart, text: "Kids' nutrition tips", question: "What are the best nutrition practices for children?" },
        { icon: Target, text: "Budget-friendly healthy eating", question: "How can we eat healthy on a budget?" },
      ];
    } else if (userContext.health_goals?.includes('weight_loss')) {
      return [
        { icon: Target, text: "Weight loss strategies", question: "What are the most effective strategies for sustainable weight loss?" },
        { icon: Zap, text: "Metabolism boosting foods", question: "Which foods can help boost my metabolism?" },
        { icon: Heart, text: "Portion control tips", question: "How can I better control my portion sizes?" },
      ];
    }

    return baseQuestions;
  };

  const quickQuestions = getContextualQuickQuestions();

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
            <div className="flex flex-col">
              <span>Enhanced AI Nutrition Assistant</span>
              {userContext.profile_type && (
                <span className="text-xs font-normal text-gray-500 capitalize">
                  {userContext.profile_type === 'general' ? 'Personalized for you' : `${userContext.profile_type} mode`}
                  {userContext.interaction_count > 0 && ` • ${userContext.interaction_count} conversations`}
                </span>
              )}
            </div>
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

            {/* Enhanced loading indicator with typing animation */}
            {(isLoading || isTyping) && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-3 rounded-lg max-w-[80%]">
                  <div className="flex items-center space-x-2">
                    <Bot className="w-4 h-4 text-purple-600" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-gray-600">
                      {isTyping ? 'Thinking deeply about your question...' : 'Processing...'}
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {messages.length <= 1 && (
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