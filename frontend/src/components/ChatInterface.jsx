import React, { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar";
import { Badge } from "./ui/badge";
import { Card, CardContent } from "./ui/card";
import { ArrowUp, Menu, AlertTriangle } from "lucide-react";
import { mockConversations } from "../mock/mockData";

const ChatInterface = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [currentStep, setCurrentStep] = useState("initial");
  const [userInfo, setUserInfo] = useState({ age: "", sex: "" });
  const [isTyping, setIsTyping] = useState(false);
  const [consultationStarted, setConsultationStarted] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    if (location.state?.initialMessage) {
      const initialMessage = location.state.initialMessage;
      setMessages([
        {
          id: 1,
          type: "user",
          content: initialMessage,
          timestamp: new Date(),
        },
      ]);
      setConsultationStarted(true);
      
      // Simulate AI response
      setTimeout(() => {
        setIsTyping(true);
        setTimeout(() => {
          setIsTyping(false);
          setMessages(prev => [...prev, {
            id: 2,
            type: "ai",
            content: "Absolutely, I can help with that. Quick question - what's your age and biological sex? It helps me give you more relevant and personalized information.",
            timestamp: new Date(),
          }]);
          setCurrentStep("collect_info");
        }, 2000);
      }, 1000);
    }
  }, [location.state]);

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const newMessage = {
      id: messages.length + 1,
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage("");
    
    // Handle different conversation steps
    if (currentStep === "collect_info") {
      handleUserInfoResponse(inputMessage);
    } else if (currentStep === "symptom_analysis") {
      handleSymptomAnalysis(inputMessage);
    } else {
      handleGeneralResponse(inputMessage);
    }
  };

  const handleUserInfoResponse = (message) => {
    // Extract age and sex from user input
    const ageMatch = message.match(/(\d+)/);
    const sexMatch = message.toLowerCase().match(/(male|female|man|woman)/);
    
    if (ageMatch || sexMatch) {
      setUserInfo({
        age: ageMatch ? ageMatch[1] : "",
        sex: sexMatch ? (sexMatch[1].includes('m') ? 'male' : 'female') : ""
      });
    }

    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: prev.length + 1,
        type: "ai",
        content: "Thank you for that information. Now, can you tell me more about your headaches? Specifically:\n\n• When did they start?\n• How would you rate the pain from 1-10?\n• Where exactly do you feel the pain?\n• Any other symptoms like nausea, sensitivity to light, or vision changes?",
        timestamp: new Date(),
      }]);
      setCurrentStep("symptom_analysis");
    }, 2000);
  };

  const handleSymptomAnalysis = (message) => {
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: prev.length + 1,
        type: "ai",
        content: "Based on your symptoms, here are the most likely conditions:\n\n**Tension Headache** (65% probability)\n• Most common type of headache\n• Often stress-related\n• Usually responds well to rest and over-the-counter pain relief\n\n**Migraine** (25% probability)\n• Can be triggered by various factors\n• May include nausea or light sensitivity\n• May require prescription medication\n\n**Dehydration Headache** (10% probability)\n• Often overlooked cause\n• Easily treatable with proper hydration\n\n**Recommendations:**\n✓ Stay well hydrated\n✓ Get adequate sleep\n✓ Try over-the-counter pain relief\n✓ Consider stress management techniques\n\n⚠️ **Seek immediate medical attention if you experience:**\n• Sudden, severe headache unlike any before\n• Headache with fever, stiff neck, or rash\n• Changes in vision or speech\n• Headache after head injury\n\nWould you like me to connect you with a licensed physician for a video consultation ($39)?",
        timestamp: new Date(),
      }]);
      setCurrentStep("recommendations");
    }, 3000);
  };

  const handleGeneralResponse = (message) => {
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      const responses = [
        "I understand your concern. Can you provide more details about your symptoms?",
        "That's helpful information. Let me ask a few follow-up questions to better assist you.",
        "Based on what you've shared, I'd like to gather a bit more information to provide the most accurate guidance."
      ];
      setMessages(prev => [...prev, {
        id: prev.length + 1,
        type: "ai",
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date(),
      }]);
    }, 1500);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div className="flex items-center space-x-3">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => navigate("/")}
              className="text-gray-600"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="text-sm text-gray-600">
              Consult started: Today, {formatTime(new Date())}
            </div>
          </div>
          <Button variant="ghost" className="text-blue-600 hover:text-blue-700">
            Log in
          </Button>
        </div>
      </header>

      {/* Emergency Notice */}
      <div className="bg-red-50 border-b border-red-100 px-4 py-2">
        <div className="max-w-4xl mx-auto flex items-center justify-center space-x-2 text-sm text-red-800">
          <AlertTriangle className="h-4 w-4" />
          <span>If this is an emergency, call 911 or your local emergency number.</span>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
              {message.type === "ai" && (
                <div className="flex-shrink-0 mr-3">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=50&h=50&fit=crop&crop=face" />
                    <AvatarFallback>AI</AvatarFallback>
                  </Avatar>
                </div>
              )}
              <div className={`max-w-lg ${message.type === "user" ? "ml-auto" : ""}`}>
                <div className={`rounded-2xl px-4 py-3 ${
                  message.type === "user" 
                    ? "bg-blue-600 text-white" 
                    : "bg-white text-gray-900 shadow-sm border"
                }`}>
                  <div className="whitespace-pre-line text-sm leading-relaxed">
                    {message.content}
                  </div>
                </div>
                {message.type === "ai" && (
                  <div className="mt-1 text-xs text-gray-500 px-2">
                    AI Response • {formatTime(message.timestamp)}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="flex-shrink-0 mr-3">
                <Avatar className="h-8 w-8">
                  <AvatarImage src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=50&h=50&fit=crop&crop=face" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
              </div>
              <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                </div>
              </div>
            </div>
          )}
          
          {/* User Info Collection */}
          {currentStep === "collect_info" && !isTyping && (
            <div className="flex justify-start">
              <div className="flex-shrink-0 mr-3">
                <Avatar className="h-8 w-8">
                  <AvatarImage src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=50&h=50&fit=crop&crop=face" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
              </div>
              <Card className="max-w-lg">
                <CardContent className="p-4 space-y-4">
                  <div className="space-y-3">
                    <Input 
                      placeholder="Age (18+)" 
                      className="text-center"
                      value={userInfo.age}
                      onChange={(e) => setUserInfo({...userInfo, age: e.target.value})}
                    />
                    <div className="flex space-x-2">
                      <Button 
                        variant={userInfo.sex === "female" ? "default" : "outline"}
                        onClick={() => setUserInfo({...userInfo, sex: "female"})}
                        className="flex-1"
                      >
                        Female
                      </Button>
                      <Button 
                        variant={userInfo.sex === "male" ? "default" : "outline"}
                        onClick={() => setUserInfo({...userInfo, sex: "male"})}
                        className="flex-1"
                      >
                        Male
                      </Button>
                    </div>
                    <Button 
                      className="w-full bg-blue-600 hover:bg-blue-700"
                      disabled={!userInfo.age || !userInfo.sex}
                      onClick={() => {
                        const infoMessage = `I am ${userInfo.age} years old and ${userInfo.sex}`;
                        setInputMessage(infoMessage);
                        setTimeout(() => handleSendMessage(), 100);
                      }}
                    >
                      Submit
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="flex-1 relative">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Reply to Doctronic..."
                className="pr-12 rounded-full border-gray-300 focus:border-blue-500"
                maxLength={1500}
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">
                {inputMessage.length}/1500
              </div>
            </div>
            <Button 
              onClick={handleSendMessage}
              disabled={!inputMessage.trim()}
              className="rounded-full bg-blue-600 hover:bg-blue-700 p-3"
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="mt-2 flex items-center justify-center text-xs text-gray-500">
            <span>Doctronic is an AI doctor, not a licensed doctor, and does not practice medicine or provide medical advice.</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;