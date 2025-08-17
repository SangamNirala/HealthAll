import React, { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar";
import { Badge } from "./ui/badge";
import { Card, CardContent } from "./ui/card";
import { ArrowUp, Menu, AlertTriangle, Loader2 } from "lucide-react";
import { useConsultation } from "../hooks/useConsultation";
import { useToast } from "../hooks/use-toast";

const ChatInterface = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { messages, sendMessage, updateUserInfo, fetchConsultation, isLoading } = useConsultation();
  const [inputMessage, setInputMessage] = useState("");
  const [currentStep, setCurrentStep] = useState("initial");
  const [userInfo, setUserInfo] = useState({ age: "", sex: "" });
  const [consultationId, setConsultationId] = useState(null);
  const [sessionToken, setSessionToken] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    if (location.state?.consultationId) {
      setConsultationId(location.state.consultationId);
      setSessionToken(location.state.sessionToken);
      
      // Fetch existing conversation
      fetchConsultation(location.state.consultationId);
    } else {
      // Redirect to home if no consultation
      navigate("/");
    }
  }, [location.state, fetchConsultation, navigate]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !consultationId || isLoading) return;

    const messageContent = inputMessage.trim();
    setInputMessage("");
    setIsTyping(true);

    try {
      await sendMessage(messageContent, consultationId);
      
      // Check if this was user info submission
      if (currentStep === "collect_info" && (messageContent.includes("years old") || messageContent.includes("male") || messageContent.includes("female"))) {
        setCurrentStep("symptom_analysis");
      }
    } catch (error) {
      toast({
        title: "Failed to send message",
        description: "There was an error sending your message. Please try again.",
        variant: "destructive"
      });
      console.error("Failed to send message:", error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleUserInfoSubmit = async () => {
    if (!userInfo.age || !userInfo.sex || !consultationId) return;

    setIsTyping(true);
    
    try {
      // Update user info in backend
      await updateUserInfo(consultationId, {
        age: parseInt(userInfo.age),
        sex: userInfo.sex
      });

      // Send message with user info
      const infoMessage = `I am ${userInfo.age} years old and ${userInfo.sex}`;
      await sendMessage(infoMessage, consultationId);
      
      setCurrentStep("symptom_analysis");
    } catch (error) {
      toast({
        title: "Failed to submit information",
        description: "There was an error submitting your information. Please try again.",
        variant: "destructive"
      });
      console.error("Failed to submit user info:", error);
    } finally {
      setIsTyping(false);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const detectUserInfoNeeded = () => {
    // Check if AI is asking for user info in recent messages
    const recentAIMessages = messages.filter(m => m.type === "ai").slice(-2);
    return recentAIMessages.some(m => 
      m.content.toLowerCase().includes("age") && 
      m.content.toLowerCase().includes("sex")
    );
  };

  const shouldShowUserInfoForm = () => {
    return detectUserInfoNeeded() && !userInfo.age && !userInfo.sex && messages.length > 0;
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
                  
                  {/* Show emergency warning if detected */}
                  {message.metadata?.emergency_detected && (
                    <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-800 text-xs">
                      🚨 Emergency symptoms detected. Please seek immediate medical attention.
                    </div>
                  )}
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
          {(isTyping || isLoading) && (
            <div className="flex justify-start">
              <div className="flex-shrink-0 mr-3">
                <Avatar className="h-8 w-8">
                  <AvatarImage src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=50&h=50&fit=crop&crop=face" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
              </div>
              <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border">
                <div className="flex items-center space-x-1">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  <span className="text-sm text-gray-600">Doctronic is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          {/* User Info Collection Form */}
          {shouldShowUserInfoForm() && !isLoading && (
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
                      type="number"
                      min="18"
                      max="120"
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
                      disabled={!userInfo.age || !userInfo.sex || isLoading}
                      onClick={handleUserInfoSubmit}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                          Submitting...
                        </>
                      ) : (
                        "Submit"
                      )}
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
                onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
                placeholder="Reply to Doctronic..."
                className="pr-12 rounded-full border-gray-300 focus:border-blue-500"
                maxLength={1500}
                disabled={isLoading}
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">
                {inputMessage.length}/1500
              </div>
            </div>
            <Button 
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="rounded-full bg-blue-600 hover:bg-blue-700 p-3"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
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