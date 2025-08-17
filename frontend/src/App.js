import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "./components/ui/toaster";
import { ConsultationProvider } from "./context/ConsultationContext";
import HomePage from "./components/HomePage";
import ChatInterface from "./components/ChatInterface";

function App() {
  return (
    <div className="App">
      <ConsultationProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/chat" element={<ChatInterface />} />
          </Routes>
          <Toaster />
        </BrowserRouter>
      </ConsultationProvider>
    </div>
  );
}

export default App;