import { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const useConsultation = () => {
  const [consultation, setConsultation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const createConsultation = async (symptoms) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API}/consultations`, {
        symptoms: symptoms
      });
      
      const consultationData = response.data;
      setConsultation({
        id: consultationData.consultation_id,
        sessionToken: consultationData.session_token
      });
      
      // Fetch initial messages
      await fetchMessages(consultationData.consultation_id);
      
      return consultationData;
    } catch (err) {
      console.error('Failed to create consultation:', err);
      setError('Failed to start consultation');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (content, consultationId) => {
    if (!consultationId) {
      throw new Error('No consultation ID provided');
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API}/consultations/${consultationId}/messages`, {
        content: content,
        type: 'user'
      });

      const data = response.data;
      
      // Add user message
      setMessages(prev => [...prev, data.message]);
      
      // Add AI response if available
      if (data.ai_response) {
        setMessages(prev => [...prev, data.ai_response]);
      }

      return data;
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMessages = async (consultationId) => {
    if (!consultationId) return;

    try {
      const response = await axios.get(`${API}/consultations/${consultationId}/messages`);
      setMessages(response.data.messages || []);
    } catch (err) {
      console.error('Failed to fetch messages:', err);
      setError('Failed to load conversation');
    }
  };

  const updateUserInfo = async (consultationId, userInfo) => {
    if (!consultationId) return;

    try {
      await axios.put(`${API}/consultations/${consultationId}/user-info`, userInfo);
    } catch (err) {
      console.error('Failed to update user info:', err);
      setError('Failed to update user information');
    }
  };

  const fetchConsultation = async (consultationId) => {
    if (!consultationId) return;

    try {
      const response = await axios.get(`${API}/consultations/${consultationId}`);
      setConsultation(response.data.consultation);
      setMessages(response.data.messages || []);
    } catch (err) {
      console.error('Failed to fetch consultation:', err);
      setError('Failed to load consultation');
    }
  };

  return {
    consultation,
    messages,
    isLoading,
    error,
    createConsultation,
    sendMessage,
    fetchMessages,
    updateUserInfo,
    fetchConsultation,
    setMessages
  };
};