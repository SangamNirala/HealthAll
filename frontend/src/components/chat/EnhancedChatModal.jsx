import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { 
  X, Send, Loader2, Bot, User, Sparkles, Pizza, Heart, Lightbulb, CheckCircle2, Brain, Zap, Target,
  Mic, MicOff, Image, Camera, Settings, Download, Search, Tag, Bookmark, ThumbsUp, ThumbsDown,
  Volume2, VolumeX, Moon, Sun, MessageSquare, TrendingUp, BarChart3, Filter, Archive, Star,
  PlusCircle, Edit3, Share, Copy, Trash2, RefreshCw, Eye, EyeOff, Maximize2, Minimize2
} from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Slider } from '../ui/slider';
import { Switch } from '../ui/switch';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';

const EnhancedChatModal = ({ isOpen, onClose }) => {
  // Core state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const [userContext, setUserContext] = useState({});
  
  // Enhanced features state
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeakingEnabled, setIsSpeakingEnabled] = useState(false);
  const [conversationInsights, setConversationInsights] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);
  const [bookmarkedMessages, setBookmarkedMessages] = useState(new Set());
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [conversationSettings, setConversationSettings] = useState({
    responseStyle: 'balanced',
    verbosity: 'medium',
    personality: 'friendly',
    contextLength: 15
  });

  // UI preferences state
  const [showTimestamps, setShowTimestamps] = useState(false);
  const [messageReactions, setMessageReactions] = useState({});
  const [draftMessage, setDraftMessage] = useState('');
  const [messageHistory, setMessageHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [wordCount, setWordCount] = useState(0);

  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const speechSynthesisRef = useRef(null);
  const fileInputRef = useRef(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  // Auto-save draft
  useEffect(() => {
    const savedDraft = localStorage.getItem(`chat_draft_${sessionId}`);
    if (savedDraft && !inputMessage) {
      setInputMessage(savedDraft);
    }
  }, [sessionId]);

  useEffect(() => {
    if (inputMessage && sessionId) {
      localStorage.setItem(`chat_draft_${sessionId}`, inputMessage);
    }
  }, [inputMessage, sessionId]);

  // Initialize user context
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

    // Load theme preference
    const savedTheme = localStorage.getItem('chat_theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
    }

    // Load conversation settings
    const savedSettings = localStorage.getItem('chat_settings');
    if (savedSettings) {
      setConversationSettings(JSON.parse(savedSettings));
    }
  }, []);

  // Save settings when changed
  useEffect(() => {
    localStorage.setItem('chat_settings', JSON.stringify(conversationSettings));
  }, [conversationSettings]);

  // Theme management
  useEffect(() => {
    localStorage.setItem('chat_theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  // Word count tracking
  useEffect(() => {
    setWordCount(inputMessage.trim().split(/\s+/).filter(Boolean).length);
  }, [inputMessage]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Start session on open with enhanced features
  useEffect(() => {
    const startEnhancedSession = async () => {
      if (!isOpen || sessionId) return;
      
      try {
        const res = await fetch(`${backendUrl}/api/chat/start-session`, { method: 'POST' });
        const data = await res.json();
        setSessionId(data.session_id);
        
        const contextualWelcome = userContext.profile_type && userContext.profile_type !== 'general' 
          ? `🌟 Welcome to your Enhanced AI Nutrition Assistant! I'm supercharged with advanced features like voice interaction, image analysis, conversation analytics, and personalized insights. Specialized for ${userContext.profile_type} needs. Let's explore your health journey together!`
          : "🚀 Welcome to the Enhanced AI Nutrition Assistant! I now have advanced capabilities including:\n\n✨ Voice conversations\n📸 Image analysis\n📊 Conversation insights\n🎯 Personalized recommendations\n\nWhat would you like to explore today?";
          
        const welcomeMessage = {
          id: Date.now(),
          type: 'bot',
          content: contextualWelcome,
          timestamp: new Date(),
          title: "🎉 Enhanced AI Assistant Ready!",
          summary: "Your upgraded nutrition assistant with advanced AI capabilities",
          keyPoints: [
            "🎤 Voice interaction support",
            "📷 Image analysis and food recognition", 
            "🧠 Advanced conversation intelligence",
            "📈 Real-time analytics and insights",
            "🎯 Personalized recommendations"
          ],
          actionSteps: [
            "Try asking a nutrition question",
            "Upload a food image for analysis",
            "Use voice input for hands-free interaction"
          ],
          tips: [
            "Click the mic button to start voice chat",
            "Use the camera icon to analyze food images",
            "Check analytics tab for conversation insights"
          ],
          metadata: {
            isWelcomeMessage: true,
            features: ['voice', 'image', 'analytics', 'personalization']
          }
        };
        
        setMessages([welcomeMessage]);
        
        // Load conversation analytics
        await loadConversationInsights(data.session_id);
        
      } catch (e) {
        console.error('Session start error:', e);
        const fallbackWelcome = {
          id: Date.now(),
          type: 'bot',
          content: "Welcome! I'm your enhanced AI nutrition assistant. Even with connection issues, I'm ready to help with your health and nutrition questions!",
          timestamp: new Date(),
          title: "🤖 AI Assistant Ready",
          metadata: { isFallback: true }
        };
        setMessages([fallbackWelcome]);
      }
    };

    if (isOpen) {
      startEnhancedSession();
    }
  }, [isOpen, backendUrl, userContext.profile_type]);

  // Load conversation insights
  const loadConversationInsights = async (sessionId) => {
    try {
      const response = await fetch(`${backendUrl}/api/chat/enhanced/analytics/${sessionId}`);
      if (response.ok) {
        const insights = await response.json();
        setConversationInsights(insights);
      }
    } catch (error) {
      console.error('Failed to load insights:', error);
    }
  };

  // Enhanced message sending with multimodal support
  const sendEnhancedMessage = async (messageData = null) => {
    const messageToSend = messageData || {
      type: 'text',
      content: inputMessage.trim(),
      user_context: userContext,
      metadata: {
        timestamp: new Date().toISOString(),
        wordCount,
        settings: conversationSettings
      }
    };

    if (!messageToSend.content && messageToSend.type === 'text') return;

    const now = Date.now();
    const userMessage = {
      id: now,
      type: 'user',
      content: messageToSend.content,
      originalType: messageToSend.type,
      timestamp: new Date(),
      metadata: messageToSend.metadata || {}
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);
    
    // Add to message history for navigation
    if (messageToSend.type === 'text' && messageToSend.content.trim()) {
      setMessageHistory(prev => [messageToSend.content.trim(), ...prev.slice(0, 19)]);
      setHistoryIndex(-1);
    }

    // Update interaction count
    const newCount = userContext.interaction_count + 1;
    setUserContext(prev => ({ ...prev, interaction_count: newCount }));
    localStorage.setItem('chat_interaction_count', newCount.toString());

    try {
      const response = await fetch(`${backendUrl}/api/chat/enhanced/send-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId || `session_${now}`,
          ...messageToSend
        }),
      });

      if (!response.ok) throw new Error('Failed to get enhanced response');
      const data = await response.json();

      // Simulate typing delay for better UX
      setTimeout(() => {
        setIsTyping(false);
        
        const botMessage = {
          id: now + 1,
          type: 'bot',
          content: data.response,
          timestamp: new Date(),
          structured_data: data.structured_data || {},
          suggestions: data.suggestions || [],
          quickActions: data.quick_actions || [],
          conversationInsights: data.conversation_insights || {},
          metadata: {
            ...data.metadata,
            enhanced: true,
            processingTime: Date.now() - now
          }
        };

        setMessages(prev => [...prev, botMessage]);
        
        // Update insights if available
        if (data.conversation_insights) {
          setConversationInsights(prev => ({
            ...prev,
            ...data.conversation_insights
          }));
        }

        // Text-to-speech for bot response if enabled
        if (isSpeakingEnabled && data.response) {
          speakMessage(data.response);
        }
        
      }, Math.random() * 1000 + 500); // Random delay 500-1500ms
      
    } catch (error) {
      console.error('Enhanced chat error:', error);
      setIsTyping(false);
      
      // Fallback to regular chat
      try {
        const fallbackResponse = await fetch(`${backendUrl}/api/chat/send-message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId || `session_${now}`,
            message: messageToSend.content,
            context_type: 'health_and_nutrition',
            user_context: userContext,
          }),
        });

        if (fallbackResponse.ok) {
          const fallbackData = await fallbackResponse.json();
          const botMessage = {
            id: now + 1,
            type: 'bot',
            content: fallbackData.response,
            timestamp: new Date(),
            suggestions: fallbackData.suggestions || [],
            quickActions: fallbackData.quick_actions || [],
            metadata: { fallback: true, originalError: error.message }
          };
          setMessages(prev => [...prev, botMessage]);
        } else {
          throw new Error('Fallback also failed');
        }
      } catch {
        const errorMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: "I'm experiencing technical difficulties. Please try again in a moment, or try rephrasing your question.",
          timestamp: new Date(),
          metadata: { isError: true }
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Voice recording functionality
  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      const audioChunks = [];
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        // For now, we'll use Web Speech API instead of processing the blob
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Voice recording failed:', error);
      alert('Voice recording is not available. Please check your microphone permissions.');
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Web Speech API for voice input
  const startSpeechRecognition = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in your browser.');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsRecording(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      const confidence = event.results[0][0].confidence;
      
      setInputMessage(transcript);
      
      // Auto-send if confidence is high
      if (confidence > 0.8) {
        setTimeout(() => {
          sendEnhancedMessage({
            type: 'voice',
            content: transcript,
            user_context: userContext,
            metadata: { confidence, language: 'en-US', autoSent: true }
          });
        }, 500);
      }
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();
  };

  // Text-to-speech functionality
  const speakMessage = (text) => {
    if (!isSpeakingEnabled || !('speechSynthesis' in window)) return;

    // Cancel any ongoing speech
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;
    
    const voices = speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.name.includes('Female') || voice.name.includes('Samantha') || voice.name.includes('Karen')
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    speechSynthesis.speak(utterance);
  };

  // Image upload and processing
  const handleImageUpload = async (file) => {
    if (!file || !file.type.startsWith('image/')) {
      alert('Please upload a valid image file.');
      return;
    }

    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64Data = e.target.result.split(',')[1];
      
      const imageMessage = {
        type: 'image',
        content: `Analyzing uploaded image: ${file.name}`,
        user_context: userContext,
        metadata: {
          image_data: base64Data,
          filename: file.name,
          size: file.size,
          format: file.type
        }
      };

      await sendEnhancedMessage(imageMessage);
    };

    reader.readAsDataURL(file);
  };

  // Message reactions
  const addReaction = (messageId, reaction) => {
    setMessageReactions(prev => ({
      ...prev,
      [messageId]: {
        ...prev[messageId],
        [reaction]: (prev[messageId]?.[reaction] || 0) + 1
      }
    }));
  };

  // Bookmark messages
  const toggleBookmark = (messageId) => {
    setBookmarkedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  // Message history navigation
  const navigateHistory = (direction) => {
    if (direction === 'up' && historyIndex < messageHistory.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      setInputMessage(messageHistory[newIndex]);
    } else if (direction === 'down') {
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setInputMessage(messageHistory[newIndex]);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setInputMessage('');
      }
    }
  };

  // Keyboard shortcuts
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendEnhancedMessage();
    } else if (e.key === 'ArrowUp' && inputMessage === '') {
      e.preventDefault();
      navigateHistory('up');
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      navigateHistory('down');
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  // Export conversation
  const exportConversation = () => {
    const exportData = {
      sessionId,
      messages: messages.map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp,
        structured_data: msg.structured_data
      })),
      insights: conversationInsights,
      settings: conversationSettings,
      exportDate: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nutrition-chat-${sessionId}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Filter messages based on search
  const filteredMessages = useMemo(() => {
    if (!searchQuery && selectedTags.length === 0) return messages;
    
    return messages.filter(msg => {
      const matchesSearch = !searchQuery || 
        msg.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        msg.structured_data?.title?.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesTags = selectedTags.length === 0 || 
        selectedTags.some(tag => 
          msg.content.toLowerCase().includes(tag.toLowerCase()) ||
          msg.metadata?.tags?.includes(tag)
        );
      
      return matchesSearch && matchesTags;
    });
  }, [messages, searchQuery, selectedTags]);

  // Get contextual quick questions
  const getContextualQuickQuestions = () => {
    const baseQuestions = [
      { icon: Brain, text: "AI-powered meal analysis", question: "Can you analyze my eating patterns using AI?" },
      { icon: Target, text: 'Smart nutrition goals', question: 'Help me set intelligent nutrition goals with tracking' },
      { icon: TrendingUp, text: 'Advanced progress insights', question: 'Show me advanced analytics of my health progress' },
    ];

    if (userContext.profile_type === 'patient') {
      return [
        { icon: Brain, text: "Clinical AI nutrition insights", question: "What AI-driven nutrition insights align with my medical condition?" },
        { icon: BarChart3, text: "Health data correlation", question: "How does my nutrition correlate with my health metrics?" },
        { icon: Target, text: "Personalized therapeutic nutrition", question: "Create a personalized therapeutic nutrition plan using AI" },
      ];
    } else if (userContext.profile_type === 'family') {
      return [
        { icon: Pizza, text: "AI family meal optimization", question: "Use AI to optimize meals for my entire family's needs" },
        { icon: Brain, text: "Smart child nutrition", question: "AI recommendations for optimal child nutrition and development" },
        { icon: TrendingUp, text: "Family health analytics", question: "Analyze our family's nutrition patterns and suggest improvements" },
      ];
    }

    return baseQuestions;
  };

  const quickQuestions = getContextualQuickQuestions();

  const handleQuickQuestion = (question) => {
    setInputMessage(question);
    setTimeout(() => sendEnhancedMessage(), 50);
  };

  // Theme classes
  const themeClasses = isDarkMode 
    ? 'bg-gray-900 text-white' 
    : 'bg-white text-gray-900';
  
  const cardThemeClasses = isDarkMode 
    ? 'bg-gray-800 border-gray-700' 
    : 'bg-white border-gray-200';

  if (!isOpen) return null;

  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 ${themeClasses}`}>
      <Card className={`w-full ${isFullscreen ? 'h-full max-w-none' : 'max-w-6xl h-[700px]'} flex flex-col ${cardThemeClasses} shadow-2xl`}>
        <CardHeader className={`flex flex-row items-center justify-between space-y-0 pb-2 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <CardTitle className="flex items-center text-lg font-semibold">
            <Bot className="w-5 h-5 mr-2 text-purple-600" />
            <div className="flex flex-col">
              <span className="flex items-center">
                🚀 Enhanced AI Nutrition Assistant
                <Sparkles className="w-4 h-4 ml-2 text-purple-400" />
              </span>
              {userContext.profile_type && (
                <span className="text-xs font-normal text-gray-500 capitalize flex items-center">
                  {userContext.profile_type === 'general' ? 'Personalized for you' : `${userContext.profile_type} mode`}
                  {userContext.interaction_count > 0 && ` • ${userContext.interaction_count} conversations`}
                  {conversationInsights.engagement && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      {conversationInsights.engagement} engagement
                    </Badge>
                  )}
                </span>
              )}
            </div>
          </CardTitle>
          
          <div className="flex items-center space-x-2">
            {/* Voice toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsSpeakingEnabled(!isSpeakingEnabled)}
              className={`h-8 w-8 p-0 ${isSpeakingEnabled ? 'text-green-600' : 'text-gray-400'}`}
              title="Toggle text-to-speech"
            >
              {isSpeakingEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
            </Button>

            {/* Theme toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="h-8 w-8 p-0"
              title="Toggle dark mode"
            >
              {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>

            {/* Analytics toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAnalytics(!showAnalytics)}
              className="h-8 w-8 p-0"
              title="Toggle analytics"
            >
              <BarChart3 className="h-4 w-4" />
            </Button>

            {/* Fullscreen toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="h-8 w-8 p-0"
              title="Toggle fullscreen"
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>

            {/* Export */}
            <Button
              variant="ghost"
              size="sm"
              onClick={exportConversation}
              className="h-8 w-8 p-0"
              title="Export conversation"
            >
              <Download className="h-4 w-4" />
            </Button>

            {/* Close */}
            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <div className="flex flex-1 overflow-hidden">
          {/* Main chat area */}
          <div className="flex-1 flex flex-col">
            <CardContent className="flex flex-col flex-1 p-0">
              {showAnalytics && (
                <div className={`border-b p-4 ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'}`}>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div className="text-center">
                      <div className="font-semibold text-purple-600">{messages.length}</div>
                      <div className="text-gray-500">Messages</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold text-green-600">{conversationInsights.engagement || 'N/A'}</div>
                      <div className="text-gray-500">Engagement</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold text-blue-600">{userContext.interaction_count}</div>
                      <div className="text-gray-500">Total Chats</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold text-orange-600">{wordCount}</div>
                      <div className="text-gray-500">Words Typed</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Search and filter bar */}
              {messages.length > 5 && (
                <div className={`border-b p-3 ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'}`}>
                  <div className="flex items-center space-x-2">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <Input
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search messages..."
                        className="pl-10 h-8"
                      />
                    </div>
                    <Button variant="outline" size="sm" onClick={() => {setSearchQuery(''); setSelectedTags([]);}}>
                      Clear
                    </Button>
                  </div>
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {filteredMessages.map((message) => (
                  <EnhancedMessageBubble
                    key={message.id}
                    message={message}
                    isDarkMode={isDarkMode}
                    onReaction={(reaction) => addReaction(message.id, reaction)}
                    onBookmark={() => toggleBookmark(message.id)}
                    isBookmarked={bookmarkedMessages.has(message.id)}
                    reactions={messageReactions[message.id]}
                    onQuickQuestion={handleQuickQuestion}
                    showTimestamps={showTimestamps}
                  />
                ))}

                {/* Enhanced loading indicator */}
                {(isLoading || isTyping) && (
                  <EnhancedTypingIndicator isDarkMode={isDarkMode} isTyping={isTyping} />
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Quick Questions */}
              {messages.length <= 2 && (
                <div className={`border-t p-4 ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'}`}>
                  <h4 className="text-sm font-medium mb-3 flex items-center">
                    <Sparkles className="w-4 h-4 mr-2 text-purple-600" />
                    Enhanced Quick Start:
                  </h4>
                  <div className="grid grid-cols-1 gap-2">
                    {quickQuestions.map((item, idx) => (
                      <Button 
                        key={idx} 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => handleQuickQuestion(item.question)} 
                        className="w-full justify-start h-auto p-3 text-left hover:bg-purple-50 dark:hover:bg-purple-900/20"
                      >
                        <item.icon className="w-4 h-4 mr-3 text-purple-600 flex-shrink-0" />
                        <span className="text-sm">{item.text}</span>
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Enhanced Input */}
              <div className={`border-t p-4 ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                <div className="flex items-end space-x-2">
                  {/* Voice input */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={isRecording ? stopVoiceRecording : startSpeechRecognition}
                    className={`${isRecording ? 'bg-red-100 border-red-300 text-red-700' : ''}`}
                    disabled={isLoading}
                    title="Voice input"
                  >
                    {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </Button>

                  {/* Image upload */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    title="Upload image"
                  >
                    <Camera className="w-4 h-4" />
                  </Button>

                  {/* Text input */}
                  <Textarea
                    ref={inputRef}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Ask me about food, nutrition, or health... (Enhanced AI ready!)"
                    className={`flex-1 resize-none min-h-[2.5rem] max-h-32 ${isDarkMode ? 'bg-gray-700 border-gray-600' : ''}`}
                    disabled={isLoading}
                  />

                  {/* Send button */}
                  <Button 
                    onClick={() => sendEnhancedMessage()} 
                    disabled={!inputMessage.trim() || isLoading} 
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 min-h-[2.5rem]"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  </Button>
                </div>

                {/* Input helpers */}
                <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
                  <div className="flex items-center space-x-4">
                    <span>{wordCount} words</span>
                    {isRecording && <span className="text-red-500 animate-pulse">🎤 Recording...</span>}
                    {historyIndex >= 0 && <span>History: {historyIndex + 1}/{messageHistory.length}</span>}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch 
                      checked={showTimestamps} 
                      onCheckedChange={setShowTimestamps}
                      size="sm"
                    />
                    <span>Timestamps</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </div>

          {/* Settings sidebar */}
          {showAnalytics && (
            <div className={`w-80 border-l p-4 overflow-y-auto ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'}`}>
              <Tabs defaultValue="analytics" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="analytics">Analytics</TabsTrigger>
                  <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>
                
                <TabsContent value="analytics" className="space-y-4">
                  <ConversationAnalytics 
                    insights={conversationInsights}
                    messages={messages}
                    isDarkMode={isDarkMode}
                  />
                </TabsContent>
                
                <TabsContent value="settings" className="space-y-4">
                  <ConversationSettings
                    settings={conversationSettings}
                    onSettingsChange={setConversationSettings}
                    isDarkMode={isDarkMode}
                  />
                </TabsContent>
              </Tabs>
            </div>
          )}
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={(e) => e.target.files[0] && handleImageUpload(e.target.files[0])}
          className="hidden"
        />
      </Card>
    </div>
  );
};

// Enhanced Message Bubble Component
const EnhancedMessageBubble = ({ 
  message, 
  isDarkMode, 
  onReaction, 
  onBookmark, 
  isBookmarked, 
  reactions, 
  onQuickQuestion,
  showTimestamps 
}) => {
  const [showActions, setShowActions] = useState(false);
  
  const renderFormatted = (msg) => {
    const structuredData = msg.structured_data || {};
    const hasStructure = structuredData.title || structuredData.summary || 
                        (structuredData.key_points && structuredData.key_points.length) || 
                        (structuredData.action_steps && structuredData.action_steps.length);
    
    if (!hasStructure) {
      return String(msg.content || '').split('\n').map((line, i) => (
        <p key={i} className="text-sm leading-relaxed">{line}</p>
      ));
    }

    return (
      <div className="space-y-3">
        {structuredData.title && (
          <div className="font-semibold text-sm text-purple-700 dark:text-purple-300 flex items-center">
            <Brain className="w-4 h-4 mr-2" />
            {structuredData.title}
          </div>
        )}
        
        {structuredData.summary && (
          <div className="text-sm leading-relaxed">{structuredData.summary}</div>
        )}
        
        {structuredData.key_points?.length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
              <Target className="w-3 h-3 mr-1" />
              Key Insights
            </div>
            <ul className="list-disc ml-5 space-y-1">
              {structuredData.key_points.map((kp, idx) => (
                <li key={idx} className="text-sm">{kp}</li>
              ))}
            </ul>
          </div>
        )}
        
        {structuredData.action_steps?.length > 0 && (
          <div>
            <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
              <Zap className="w-3 h-3 mr-1" />
              Action Steps
            </div>
            <ul className="ml-1 space-y-2">
              {structuredData.action_steps.map((step, idx) => (
                <li key={idx} className="flex items-start text-sm">
                  <CheckCircle2 className="w-4 h-4 mr-2 mt-0.5 text-green-600 flex-shrink-0" />
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {structuredData.tips?.length > 0 && (
          <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-purple-900/20' : 'bg-purple-50'}`}>
            <div className="text-xs font-medium text-purple-700 dark:text-purple-300 mb-2 flex items-center">
              <Lightbulb className="w-3 h-3 mr-1" />
              Pro Tips
            </div>
            <ul className="space-y-1">
              {structuredData.tips.map((tip, idx) => (
                <li key={idx} className="text-sm text-purple-800 dark:text-purple-200 flex items-start">
                  <span className="text-purple-400 mr-2">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {message.metadata?.enhanced && (
          <div className={`p-2 rounded border-l-4 border-green-400 ${isDarkMode ? 'bg-green-900/10' : 'bg-green-50'}`}>
            <div className="text-xs font-medium text-green-700 dark:text-green-300 mb-1 flex items-center">
              <Sparkles className="w-3 h-3 mr-1" />
              Enhanced AI Response
            </div>
            <div className="text-xs text-green-600 dark:text-green-400">
              Powered by advanced AI • {message.metadata.model_used} • {message.metadata.processingTime}ms
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div 
      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className={`max-w-[85%] ${message.type === 'user' ? 'order-2' : 'order-1'} relative group`}>
        <div className={`px-4 py-3 rounded-lg ${
          message.type === 'user' 
            ? 'bg-purple-600 text-white' 
            : isDarkMode 
              ? 'bg-gray-700 text-gray-100' 
              : 'bg-gray-100 text-gray-900'
        }`}>
          <div className="flex items-start space-x-2">
            {message.type === 'bot' && <Bot className="w-4 h-4 mt-1 text-purple-600 flex-shrink-0" />}
            {message.type === 'user' && <User className="w-4 h-4 mt-1 text-white flex-shrink-0" />}
            <div className="space-y-2 w-full">
              {message.type === 'bot' ? renderFormatted(message) : (
                <p className="text-sm leading-relaxed">{message.content}</p>
              )}
            </div>
          </div>
        </div>

        {/* Message actions */}
        {showActions && (
          <div className={`absolute top-2 ${message.type === 'user' ? 'left-2' : 'right-2'} flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity`}>
            <Button 
              size="sm" 
              variant="ghost" 
              onClick={() => onReaction('like')} 
              className="h-6 w-6 p-0"
            >
              <ThumbsUp className="w-3 h-3" />
            </Button>
            <Button 
              size="sm" 
              variant="ghost" 
              onClick={onBookmark} 
              className={`h-6 w-6 p-0 ${isBookmarked ? 'text-yellow-500' : ''}`}
            >
              <Bookmark className="w-3 h-3" />
            </Button>
          </div>
        )}

        {/* Suggestions and Quick Actions */}
        {message.suggestions?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {message.suggestions.map((s, idx) => (
              <Button key={idx} size="sm" variant="secondary" onClick={() => onQuickQuestion(s)} className="text-xs">
                {s}
              </Button>
            ))}
          </div>
        )}

        {message.quickActions?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {message.quickActions.map((action, idx) => (
              <Button 
                key={idx} 
                size="sm" 
                variant="outline" 
                onClick={() => console.log('Quick action:', action)} 
                className="text-xs"
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}

        {/* Reactions display */}
        {reactions && Object.keys(reactions).length > 0 && (
          <div className="mt-1 flex space-x-1">
            {Object.entries(reactions).map(([reaction, count]) => (
              <Badge key={reaction} variant="secondary" className="text-xs">
                {reaction === 'like' ? '👍' : reaction} {count}
              </Badge>
            ))}
          </div>
        )}

        {/* Timestamp */}
        {showTimestamps && (
          <div className="text-xs text-gray-500 mt-1 flex items-center justify-between">
            <span>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            {message.metadata?.enhanced && <Badge variant="secondary" className="text-xs">Enhanced</Badge>}
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Typing Indicator
const EnhancedTypingIndicator = ({ isDarkMode, isTyping }) => {
  const messages = [
    "Analyzing your question with advanced AI...",
    "Processing context and conversation history...",
    "Generating personalized insights...",
    "Consulting nutrition knowledge base...",
    "Crafting your enhanced response..."
  ];

  const [currentMessage, setCurrentMessage] = useState(0);

  useEffect(() => {
    if (!isTyping) return;
    
    const interval = setInterval(() => {
      setCurrentMessage(prev => (prev + 1) % messages.length);
    }, 2000);

    return () => clearInterval(interval);
  }, [isTyping, messages.length]);

  return (
    <div className="flex justify-start">
      <div className={`px-4 py-3 rounded-lg max-w-[80%] ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
        <div className="flex items-center space-x-2">
          <Bot className="w-4 h-4 text-purple-600" />
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-300 mt-2">
          {messages[currentMessage]}
        </div>
      </div>
    </div>
  );
};

// Conversation Analytics Component
const ConversationAnalytics = ({ insights, messages, isDarkMode }) => {
  const userMessages = messages.filter(m => m.type === 'user');
  const botMessages = messages.filter(m => m.type === 'bot');
  
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold flex items-center">
        <BarChart3 className="w-4 h-4 mr-2" />
        Conversation Analytics
      </h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'} border`}>
          <div className="text-2xl font-bold text-blue-600">{messages.length}</div>
          <div className="text-xs text-gray-500">Total Messages</div>
        </div>
        
        <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'} border`}>
          <div className="text-2xl font-bold text-green-600">{userMessages.length}</div>
          <div className="text-xs text-gray-500">Your Messages</div>
        </div>
        
        <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'} border`}>
          <div className="text-2xl font-bold text-purple-600">
            {insights.engagement || 'N/A'}
          </div>
          <div className="text-xs text-gray-500">Engagement</div>
        </div>
        
        <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'} border`}>
          <div className="text-2xl font-bold text-orange-600">
            {Math.round((messages.length / Math.max((Date.now() - new Date(messages[0]?.timestamp || Date.now()).getTime()) / (1000 * 60), 1)) * 10) / 10}
          </div>
          <div className="text-xs text-gray-500">Messages/Min</div>
        </div>
      </div>

      {insights.mood && (
        <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'} border`}>
          <h4 className="text-sm font-medium mb-2">Conversation Mood</h4>
          <div className="flex items-center justify-between">
            <Badge variant={insights.mood === 'positive' ? 'default' : insights.mood === 'needs_support' ? 'destructive' : 'secondary'}>
              {insights.mood}
            </Badge>
            <span className="text-xs text-gray-500">{insights.mood_note}</span>
          </div>
        </div>
      )}

      {insights.topic_diversity && (
        <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'} border`}>
          <h4 className="text-sm font-medium mb-2">Topic Coverage</h4>
          <div className="flex items-center justify-between">
            <Badge variant="outline">{insights.topic_diversity}</Badge>
            <span className="text-xs text-gray-500">{insights.topic_note}</span>
          </div>
        </div>
      )}
    </div>
  );
};

// Conversation Settings Component
const ConversationSettings = ({ settings, onSettingsChange, isDarkMode }) => {
  const updateSetting = (key, value) => {
    onSettingsChange(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold flex items-center">
        <Settings className="w-4 h-4 mr-2" />
        Conversation Settings
      </h3>
      
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-2 block">Response Style</label>
          <select 
            value={settings.responseStyle}
            onChange={(e) => updateSetting('responseStyle', e.target.value)}
            className={`w-full p-2 rounded border text-sm ${isDarkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
          >
            <option value="concise">Concise</option>
            <option value="balanced">Balanced</option>
            <option value="detailed">Detailed</option>
          </select>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Personality</label>
          <select 
            value={settings.personality}
            onChange={(e) => updateSetting('personality', e.target.value)}
            className={`w-full p-2 rounded border text-sm ${isDarkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
          >
            <option value="friendly">Friendly</option>
            <option value="professional">Professional</option>
            <option value="casual">Casual</option>
            <option value="enthusiastic">Enthusiastic</option>
            <option value="empathetic">Empathetic</option>
          </select>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Context Length: {settings.contextLength}</label>
          <Slider
            value={[settings.contextLength]}
            onValueChange={([value]) => updateSetting('contextLength', value)}
            min={5}
            max={25}
            step={1}
            className="w-full"
          />
          <div className="text-xs text-gray-500 mt-1">
            How many previous messages to consider for context
          </div>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Verbosity</label>
          <select 
            value={settings.verbosity}
            onChange={(e) => updateSetting('verbosity', e.target.value)}
            className={`w-full p-2 rounded border text-sm ${isDarkMode ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
          >
            <option value="low">Brief responses</option>
            <option value="medium">Medium detail</option>
            <option value="high">Comprehensive</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default EnhancedChatModal;