import React, { createContext, useContext, useState } from 'react';

const ConsultationContext = createContext();

export const useConsultationContext = () => {
  const context = useContext(ConsultationContext);
  if (!context) {
    throw new Error('useConsultationContext must be used within a ConsultationProvider');
  }
  return context;
};

export const ConsultationProvider = ({ children }) => {
  const [currentConsultation, setCurrentConsultation] = useState(null);
  const [userInfo, setUserInfo] = useState({
    age: null,
    sex: null
  });

  const updateConsultation = (consultation) => {
    setCurrentConsultation(consultation);
  };

  const updateUserInfo = (info) => {
    setUserInfo(prev => ({ ...prev, ...info }));
  };

  const clearConsultation = () => {
    setCurrentConsultation(null);
    setUserInfo({ age: null, sex: null });
  };

  const value = {
    currentConsultation,
    userInfo,
    updateConsultation,
    updateUserInfo,
    clearConsultation
  };

  return (
    <ConsultationContext.Provider value={value}>
      {children}
    </ConsultationContext.Provider>
  );
};