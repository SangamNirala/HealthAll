import google.generativeai as genai
import os
import json
import re
from typing import List, Dict, Any, Tuple
from models import Diagnosis, UrgencyLevel, UserInfo, Message
import logging

logger = logging.getLogger(__name__)

class MedicalAI:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.medical_prompt = """You are an AI medical assistant similar to Doctronic.ai. Your role is to:

1. ALWAYS start responses with medical disclaimers
2. Analyze symptoms and provide differential diagnoses with probabilities
3. Ask relevant follow-up questions
4. Detect medical emergencies
5. Provide general health recommendations
6. NEVER give definitive diagnoses - always use probabilities and suggest seeing a real doctor

EMERGENCY SYMPTOMS TO WATCH FOR:
- Chest pain, shortness of breath
- Severe headache with neurological symptoms
- Signs of stroke (FAST protocol)
- Severe abdominal pain
- Loss of consciousness
- Severe allergic reactions

RESPONSE FORMAT:
Always respond in this JSON format:
{
  "emergency_detected": boolean,
  "response_text": "Your conversational response to the user",
  "diagnosis": [
    {
      "condition": "Name of condition",
      "probability": 0-100,
      "description": "Brief description",
      "symptoms": ["symptom1", "symptom2"],
      "treatment_options": ["option1", "option2"],
      "urgency_level": "low|medium|high|emergency"
    }
  ],
  "recommendations": ["recommendation1", "recommendation2"],
  "follow_up_questions": ["question1", "question2"]
}

MEDICAL DISCLAIMERS:
- Always remind that you are not a licensed doctor
- Emphasize that this is not medical advice
- Recommend seeing a healthcare provider for proper diagnosis
- If emergency detected, immediately advise calling 911"""

    async def analyze_symptoms(self, symptoms: str, user_info: UserInfo, conversation_history: List[Message]) -> Dict[str, Any]:
        """Analyze symptoms and return medical assessment"""
        try:
            # Build conversation context
            context = self._build_conversation_context(symptoms, user_info, conversation_history)
            
            # Create prompt
            prompt = f"{self.medical_prompt}\n\nCONVERSATION CONTEXT:\n{context}\n\nProvide medical assessment in the required JSON format."
            
            # Get AI response
            response = await self._get_ai_response(prompt)
            
            # Parse and validate response
            return self._parse_medical_response(response)
            
        except Exception as e:
            logger.error(f"Error in medical analysis: {e}")
            return self._get_fallback_response()

    async def generate_conversation_response(self, message: str, user_info: UserInfo, conversation_history: List[Message]) -> Dict[str, Any]:
        """Generate conversational response for ongoing chat"""
        try:
            context = self._build_conversation_context(message, user_info, conversation_history)
            
            prompt = f"""You are Doctronic, an AI medical assistant. Continue this medical conversation naturally.

CONTEXT:
{context}

USER'S LATEST MESSAGE: {message}

Respond conversationally as Doctronic would, asking relevant medical questions and providing guidance. 
If the user provides their age/sex information, acknowledge it and proceed with symptom analysis.
If symptoms seem severe, provide differential diagnosis with probabilities.

Respond in JSON format:
{{
  "response_text": "Your natural conversational response",
  "needs_analysis": boolean,
  "collect_user_info": boolean,
  "emergency_detected": boolean
}}"""

            response = await self._get_ai_response(prompt)
            return self._parse_conversation_response(response)
            
        except Exception as e:
            logger.error(f"Error in conversation generation: {e}")
            return {
                "response_text": "I understand. Can you tell me a bit more about your symptoms?",
                "needs_analysis": False,
                "collect_user_info": False,
                "emergency_detected": False
            }

    def _build_conversation_context(self, current_message: str, user_info: UserInfo, history: List[Message]) -> str:
        """Build conversation context for AI"""
        context_parts = []
        
        # Add user info if available
        if user_info.age or user_info.sex:
            context_parts.append(f"PATIENT INFO: Age: {user_info.age or 'Unknown'}, Sex: {user_info.sex or 'Unknown'}")
        
        # Add recent conversation history
        context_parts.append("CONVERSATION HISTORY:")
        for msg in history[-6:]:  # Last 6 messages for context
            role = "PATIENT" if msg.type == "user" else "AI"
            context_parts.append(f"{role}: {msg.content}")
        
        context_parts.append(f"CURRENT MESSAGE: {current_message}")
        
        return "\n".join(context_parts)

    async def _get_ai_response(self, prompt: str) -> str:
        """Get response from Gemini API"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def _parse_medical_response(self, response: str) -> Dict[str, Any]:
        """Parse medical analysis response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data
            else:
                return self._get_fallback_response()
        except Exception as e:
            logger.error(f"Failed to parse medical response: {e}")
            return self._get_fallback_response()

    def _parse_conversation_response(self, response: str) -> Dict[str, Any]:
        """Parse conversation response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data
            else:
                return {
                    "response_text": response,
                    "needs_analysis": False,
                    "collect_user_info": False,
                    "emergency_detected": False
                }
        except Exception as e:
            logger.error(f"Failed to parse conversation response: {e}")
            return {
                "response_text": "I understand your concern. Can you provide more details about how you're feeling?",
                "needs_analysis": False,
                "collect_user_info": False,
                "emergency_detected": False
            }

    def _get_fallback_response(self) -> Dict[str, Any]:
        """Fallback response when AI fails"""
        return {
            "emergency_detected": False,
            "response_text": "I understand your concern. Based on what you've shared, I'd recommend discussing these symptoms with a healthcare provider for a proper evaluation. In the meantime, please monitor your symptoms and seek immediate care if they worsen.",
            "diagnosis": [
                {
                    "condition": "Requires Professional Evaluation",
                    "probability": 100,
                    "description": "Your symptoms require evaluation by a licensed healthcare provider",
                    "symptoms": ["Various symptoms reported"],
                    "treatment_options": ["Consult with healthcare provider"],
                    "urgency_level": "medium"
                }
            ],
            "recommendations": [
                "Schedule appointment with healthcare provider",
                "Monitor symptoms closely",
                "Seek immediate care if symptoms worsen"
            ],
            "follow_up_questions": [
                "Are there any other symptoms you've noticed?",
                "Have you experienced this before?"
            ]
        }

    def detect_emergency_keywords(self, text: str) -> bool:
        """Quick emergency keyword detection"""
        emergency_keywords = [
            "chest pain", "can't breathe", "shortness of breath", "heart attack",
            "stroke", "unconscious", "severe headache", "vision loss",
            "severe bleeding", "allergic reaction", "swelling throat",
            "difficulty swallowing", "sudden weakness", "confusion",
            "severe abdominal pain", "vomiting blood", "suicide", "overdose"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in emergency_keywords)