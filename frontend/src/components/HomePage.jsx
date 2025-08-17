import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar";
import { Badge } from "./ui/badge";
import { ArrowRight, Menu, User } from "lucide-react";

const HomePage = () => {
  const [symptomInput, setSymptomInput] = useState("");
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (symptomInput.trim()) {
      navigate("/chat", { state: { initialMessage: symptomInput } });
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleGetStarted();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-4 md:px-8">
        <div className="flex items-center space-x-2">
          <Menu className="h-6 w-6 text-gray-600" />
        </div>
        <Button variant="ghost" className="text-blue-600 hover:text-blue-700">
          Log in
        </Button>
      </header>

      {/* Main Content */}
      <div className="flex flex-col items-center justify-center px-4 py-8 md:py-16">
        {/* Doctor Avatar Group */}
        <div className="mb-8 flex items-center">
          <div className="relative">
            <div className="flex -space-x-2">
              <Avatar className="h-12 w-12 border-2 border-white">
                <AvatarImage src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=100&h=100&fit=crop&crop=face" />
                <AvatarFallback>D1</AvatarFallback>
              </Avatar>
              <Avatar className="h-12 w-12 border-2 border-white">
                <AvatarImage src="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=100&h=100&fit=crop&crop=face" />
                <AvatarFallback>D2</AvatarFallback>
              </Avatar>
              <Avatar className="h-12 w-12 border-2 border-white">
                <AvatarImage src="https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=100&h=100&fit=crop&crop=face" />
                <AvatarFallback>D3</AvatarFallback>
              </Avatar>
            </div>
            <div className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full bg-white flex items-center justify-center shadow-sm">
              <div className="h-3 w-3 rounded-full bg-green-500"></div>
            </div>
          </div>
        </div>

        {/* Main Heading */}
        <h1 className="mb-6 text-4xl md:text-5xl font-bold text-gray-900 text-center">
          Hi, I'm Doctronic
        </h1>

        {/* Description */}
        <div className="mb-8 max-w-lg text-center space-y-4">
          <p className="text-lg text-gray-700">
            I'm your private and personal AI doctor.
          </p>
          <p className="text-gray-600">
            As an AI doctor, my service is fast and free. I've already helped people{" "}
            <span className="font-semibold text-gray-900">13,853,248</span> times!
          </p>
          <p className="text-gray-600">
            After we chat, if you want you can have a video visit with a top doctor for only $39.
          </p>
          <p className="text-gray-700 font-medium">
            What can I help you with today?
          </p>
        </div>

        {/* Input Section */}
        <div className="w-full max-w-lg space-y-4">
          <div className="relative">
            <Textarea
              value={symptomInput}
              onChange={(e) => setSymptomInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about your health"
              className="min-h-[120px] resize-none rounded-xl border-gray-300 pr-16 text-base"
              maxLength={1500}
            />
            <div className="absolute bottom-3 left-3 text-xs text-gray-400">
              {symptomInput.length} / 1500
            </div>
            <Button
              onClick={handleGetStarted}
              disabled={!symptomInput.trim()}
              className="absolute bottom-3 right-3 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              <span>Get Started</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
            <div className="h-4 w-4 flex items-center justify-center">
              <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
            </div>
            <span>HIPAA compliant & anonymous</span>
          </div>
        </div>

        {/* Bottom Stats */}
        <div className="mt-16 flex items-center space-x-2">
          <div className="flex -space-x-1">
            <Avatar className="h-6 w-6 border border-white">
              <AvatarImage src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=50&h=50&fit=crop&crop=face" />
              <AvatarFallback>D</AvatarFallback>
            </Avatar>
            <Avatar className="h-6 w-6 border border-white">
              <AvatarImage src="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=50&h=50&fit=crop&crop=face" />
              <AvatarFallback>D</AvatarFallback>
            </Avatar>
            <Avatar className="h-6 w-6 border border-white">
              <AvatarImage src="https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=50&h=50&fit=crop&crop=face" />
              <AvatarFallback>D</AvatarFallback>
            </Avatar>
          </div>
          <span className="text-sm text-gray-600">Over 13.8M+ consultations</span>
        </div>
      </div>
    </div>
  );
};

export default HomePage;