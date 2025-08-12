"""
AI Services Integration Module
Provides intelligent suggestions and insights using multiple AI APIs
"""

import os
import json
import asyncio
import random
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# AI Service Imports
import openai
from groq import Groq
import google.generativeai as genai
from huggingface_hub import InferenceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiAPIRotator:
    """Handles rotation and fallback for multiple Gemini API keys"""
    
    def __init__(self):
        """Initialize with multiple Gemini API keys"""
        self.api_keys = self._load_gemini_keys()
        self.current_key_index = 0
        self.failed_keys = set()
        
    def _load_gemini_keys(self) -> List[str]:
        """Load Gemini API keys from environment"""
        keys_str = os.getenv('GEMINI_API_KEYS', '')
        if keys_str:
            return [key.strip() for key in keys_str.split(',') if key.strip()]
        
        # Fallback to single key if no multiple keys provided
        single_key = os.getenv('GEMINI_API_KEY')
        return [single_key] if single_key else []
    
    def get_current_key(self) -> Optional[str]:
        """Get current working API key"""
        if not self.api_keys:
            return None
            
        # Try to find a working key
        attempts = 0
        while attempts < len(self.api_keys):
            current_key = self.api_keys[self.current_key_index]
            
            if current_key not in self.failed_keys:
                return current_key
                
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            attempts += 1
        
        # If all keys failed, reset and try again
        if len(self.failed_keys) >= len(self.api_keys):
            logger.warning("All Gemini API keys failed. Resetting failed keys list.")
            self.failed_keys.clear()
            return self.api_keys[0] if self.api_keys else None
            
        return None
    
    def mark_key_failed(self, api_key: str):
        """Mark an API key as failed"""
        self.failed_keys.add(api_key)
        logger.warning(f"Marked Gemini API key as failed: {api_key[:20]}...")
        
    def rotate_key(self):
        """Rotate to next API key"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"Rotated to Gemini API key index: {self.current_key_index}")

class AIServiceManager:
    def __init__(self):
        """Initialize AI service clients with API keys from environment"""
        self.groq_client = None
        self.gemini_rotator = GeminiAPIRotator()
        self.openrouter_client = None
        self.hf_client = None
        
        # Model preferences (configurable without new keys)
        self.gemini_model_preferred = os.getenv('GEMINI_CHAT_MODEL') or os.getenv('GEMINI_MODEL') or 'gemini-1.5-pro'
        self.gemini_model_fallback = os.getenv('GEMINI_CHAT_FALLBACK_MODEL') or 'gemini-1.5-flash'
        self.gemini_client = None
        
        # Initialize clients with API keys
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI service clients"""
        try:
            # Groq Client (Fast inference)
            if os.getenv('GROQ_API_KEY'):
                self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
                logger.info("Groq client initialized successfully")
            
            # Initialize Gemini with current key
            self._initialize_gemini_client()
            
            # OpenRouter Client
            if os.getenv('OPENROUTER_API_KEY'):
                self.openrouter_client = openai.OpenAI(
                    api_key=os.getenv('OPENROUTER_API_KEY'),
                    base_url="https://openrouter.ai/api/v1"
                )
                logger.info("OpenRouter client initialized successfully")
            
            # Hugging Face Client
            if os.getenv('HUGGING_FACE_API_KEY'):
                self.hf_client = InferenceClient(token=os.getenv('HUGGING_FACE_API_KEY'))
                logger.info("Hugging Face client initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing AI clients: {str(e)}")
    
    def _initialize_gemini_client(self):
        """Initialize Gemini client with current API key and preferred model"""
        try:
            current_key = self.gemini_rotator.get_current_key()
            if current_key:
                genai.configure(api_key=current_key)
                # Try preferred model, then fallback
                try:
                    self.gemini_client = genai.GenerativeModel(self.gemini_model_preferred)
                    logger.info(f"Gemini client initialized with model: {self.gemini_model_preferred}")
                except Exception as model_err:
                    logger.warning(f"Preferred Gemini model '{self.gemini_model_preferred}' failed: {model_err}. Falling back to {self.gemini_model_fallback}")
                    self.gemini_client = genai.GenerativeModel(self.gemini_model_fallback)
                logger.info(f"Gemini client initialized with key index: {self.gemini_rotator.current_key_index}")
            else:
                logger.error("No valid Gemini API key available")
                self.gemini_client = None
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {str(e)}")
            self.gemini_client = None
    
    def _retry_with_gemini_rotation(self, func, *args, **kwargs):
        """Retry function with Gemini API key rotation on failure"""
        max_retries = max(1, len(self.gemini_rotator.api_keys))
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a rate limit or quota error
                if any(keyword in error_msg for keyword in ['quota', 'rate limit', 'exceeded', 'resource_exhausted']):
                    current_key = self.gemini_rotator.get_current_key()
                    if current_key:
                        self.gemini_rotator.mark_key_failed(current_key)
                        self.gemini_rotator.rotate_key()
                        self._initialize_gemini_client()
                        
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying with next Gemini API key (attempt {attempt + 1}/{max_retries})")
                            continue
                
                # If not a rotation-worthy error or last attempt, raise the error
                if attempt == max_retries - 1:
                    raise e
        
        raise Exception("All Gemini API keys exhausted")

    async def generate_nutrition_insights(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized nutrition insights using AI"""
        try:
            # Create context from user data
            context = self._build_nutrition_context(user_data)
            
            # Use Groq for fast inference
            if self.groq_client:
                response = await self._groq_nutrition_analysis(context)
                return response
            
            # Fallback to Gemini with rotation
            elif self.gemini_client:
                response = await self._gemini_nutrition_analysis_with_rotation(context)
                return response
            
            # Default fallback
            return self._default_nutrition_insights(user_data)
            
        except Exception as e:
            logger.error(f"Error generating nutrition insights: {str(e)}")
            return self._default_nutrition_insights(user_data)

    async def _gemini_nutrition_analysis_with_rotation(self, context: str) -> Dict[str, Any]:
        """Use Gemini for nutrition analysis with API key rotation"""
        def _gemini_call():
            if not self.gemini_client:
                raise Exception("Gemini client not initialized")
                
            prompt = f"""
            As a professional nutritionist AI, analyze the following user data and provide personalized insights:
            
            {context}
            
            Please provide:
            1. Key nutritional insights
            2. Personalized recommendations
            3. Health correlations identified
            4. Actionable next steps
            
            Format your response as clear, actionable advice.
            """
            
            response = self.gemini_client.generate_content(prompt)
            return response
        
        try:
            response = self._retry_with_gemini_rotation(_gemini_call)
            
            return {
                "source": "gemini",
                "model": self.gemini_model_preferred, 
                "api_key_index": self.gemini_rotator.current_key_index,
                "insights": self._parse_gemini_response(getattr(response, 'text', str(response))),
                "recommendations": [],
                "correlations": [],
                "action_items": [],
                "confidence": 0.80
            }
            
        except Exception as e:
            logger.error(f"Gemini API error with rotation: {str(e)}")
            raise

    async def generate_goal_insights(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered goal insights and suggestions"""
        try:
            context = self._build_goal_context(goal_data)
            
            # Prefer Gemini for goal analysis
            if self.gemini_client:
                response = await self._gemini_goal_analysis_with_rotation(context)
                return response
            elif self.groq_client:
                response = await self._groq_goal_analysis(context)
                return response
            else:
                return self._default_goal_insights(goal_data)
                
        except Exception as e:
            logger.error(f"Error generating goal insights: {str(e)}")
            return self._default_goal_insights(goal_data)
    
    async def _gemini_goal_analysis_with_rotation(self, context: str) -> Dict[str, Any]:
        """Use Gemini for goal analysis with API key rotation"""
        def _gemini_goal_call():
            if not self.gemini_client:
                raise Exception("Gemini client not initialized")
                
            prompt = f"""
            As an AI goal optimization expert, analyze the user's goal data and provide intelligent insights:
            
            {context}
            
            Provide a JSON response with the following structure:
            {{
                "insights": ["insight1", "insight2", "insight3"],
                "recommendations": [
                    {{
                        "title": "recommendation title",
                        "description": "detailed description", 
                        "priority": "high|medium|low",
                        "timeline": "timeframe",
                        "success_probability": 0.85
                    }}
                ],
                "goal_adjustments": [
                    {{
                        "current_goal": "current goal",
                        "suggested_adjustment": "adjustment",
                        "reason": "why adjust"
                    }}
                ],
                "milestone_suggestions": [
                    {{
                        "milestone": "milestone name",
                        "target_date": "date",
                        "success_criteria": "criteria"
                    }}
                ]
            }}
            """
            
            response = self.gemini_client.generate_content(prompt)
            return response
        
        try:
            response = self._retry_with_gemini_rotation(_gemini_goal_call)
            
            # Try to parse JSON response
            try:
                parsed_response = json.loads(getattr(response, 'text', str(response)))
                return {
                    "source": "gemini",
                    "model": self.gemini_model_preferred,
                    "api_key_index": self.gemini_rotator.current_key_index,
                    "insights": parsed_response.get("insights", []),
                    "recommendations": parsed_response.get("recommendations", []),
                    "goal_adjustments": parsed_response.get("goal_adjustments", []),
                    "milestone_suggestions": parsed_response.get("milestone_suggestions", []),
                    "confidence": 0.85
                }
            except json.JSONDecodeError:
                return self._parse_goal_text_response(getattr(response, 'text', str(response)))
                
        except Exception as e:
            logger.error(f"Gemini goal analysis error: {str(e)}")
            raise

    async def generate_achievement_insights(self, achievement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights for achievement milestones"""
        try:
            context = self._build_achievement_context(achievement_data)
            
            if self.gemini_client:
                response = await self._gemini_achievement_analysis_with_rotation(context)
                return response
            else:
                return self._default_achievement_insights(achievement_data)
                
        except Exception as e:
            logger.error(f"Error generating achievement insights: {str(e)}")
            return self._default_achievement_insights(achievement_data)
    
    async def _gemini_achievement_analysis_with_rotation(self, context: str) -> Dict[str, Any]:
        """Use Gemini for achievement analysis with API key rotation"""
        def _gemini_achievement_call():
            if not self.gemini_client:
                raise Exception("Gemini client not initialized")
                
            prompt = f"""
            As an AI achievement specialist, analyze the user's progress and suggest meaningful achievement milestones:
            
            {context}
            
            Provide insights on:
            1. Recent achievements and their significance
            2. Upcoming milestone opportunities
            3. Motivation strategies based on progress patterns
            4. Achievement badge suggestions with descriptions
            5. Social sharing recommendations
            
            Format as actionable insights and specific achievement recommendations.
            """
            
            response = self.gemini_client.generate_content(prompt)
            return response
        
        try:
            response = self._retry_with_gemini_rotation(_gemini_achievement_call)
            
            return {
                "source": "gemini",
                "model": self.gemini_model_preferred,
                "api_key_index": self.gemini_rotator.current_key_index,
                "achievement_insights": self._parse_achievement_response(getattr(response, 'text', str(response))),
                "confidence": 0.82
            }
            
        except Exception as e:
            logger.error(f"Gemini achievement analysis error: {str(e)}")
            raise

    async def _groq_nutrition_analysis(self, context: str) -> Dict[str, Any]:
        """Use Groq for nutrition analysis"""
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional nutritionist AI. Provide personalized nutrition insights, recommendations, and correlations based on user data. Respond in JSON format with 'insights', 'recommendations', 'correlations', and 'action_items' keys."
                    },
                    {"role": "user", "content": context}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            response_text = completion.choices[0].message.content
            
            # Try to parse JSON response
            try:
                parsed_response = json.loads(response_text)
                return {
                    "source": "groq",
                    "model": "llama3-70b-8192",
                    "insights": parsed_response.get("insights", []),
                    "recommendations": parsed_response.get("recommendations", []),
                    "correlations": parsed_response.get("correlations", []),
                    "action_items": parsed_response.get("action_items", []),
                    "confidence": 0.85
                }
            except json.JSONDecodeError:
                # If not JSON, extract key insights from text
                return self._extract_insights_from_text(response_text, "groq")
                
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise

    async def _gemini_nutrition_analysis(self, context: str) -> Dict[str, Any]:
        """Use Gemini for nutrition analysis"""
        try:
            prompt = f"""
            As a professional nutritionist AI, analyze the following user data and provide personalized insights:
            
            {context}
            
            Please provide:
            1. Key nutritional insights
            2. Personalized recommendations
            3. Health correlations identified
            4. Actionable next steps
            
            Format your response as clear, actionable advice.
            """
            
            response = self.gemini_client.generate_content(prompt)
            
            return {
                "source": "gemini",
                "model": self.gemini_model_preferred,
                "insights": self._parse_gemini_response(getattr(response, 'text', str(response))),
                "recommendations": [],
                "correlations": [],
                "action_items": [],
                "confidence": 0.80
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise

    async def generate_smart_food_suggestions(self, user_profile: Dict[str, Any], current_intake: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered food suggestions based on user patterns"""
        try:
            context = self._build_food_suggestion_context(user_profile, current_intake)
            
            if self.groq_client:
                suggestions = await self._groq_food_suggestions(context)
                return suggestions
            elif self.gemini_client:
                suggestions = await self._gemini_food_suggestions(context)
                return suggestions
            else:
                return self._default_food_suggestions(user_profile, current_intake)
                
        except Exception as e:
            logger.error(f"Error generating food suggestions: {str(e)}")
            return self._default_food_suggestions(user_profile, current_intake)

    async def _groq_food_suggestions(self, context: str) -> List[Dict[str, Any]]:
        """Generate food suggestions using Groq"""
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a nutrition AI that suggests foods based on user preferences, nutritional needs, and eating patterns. Provide 4-6 specific food suggestions with reasons. Respond in JSON format with 'suggestions' array containing objects with 'name', 'calories', 'reason', 'nutrition_benefits', and 'meal_type' keys."
                    },
                    {"role": "user", "content": context}
                ],
                max_tokens=800,
                temperature=0.6
            )
            
            response_text = completion.choices[0].message.content
            
            try:
                parsed_response = json.loads(response_text)
                return parsed_response.get("suggestions", [])
            except json.JSONDecodeError:
                return self._extract_food_suggestions_from_text(response_text)
                
        except Exception as e:
            logger.error(f"Groq food suggestions error: {str(e)}")
            return []

    async def generate_health_correlations(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate health correlations and patterns using AI"""
        try:
            context = self._build_correlation_context(health_data)
            
            if self.openrouter_client:
                correlations = await self._openrouter_correlations(context)
                return correlations
            elif self.gemini_client:
                correlations = await self._gemini_correlations(context)
                return correlations
            else:
                return self._default_correlations(health_data)
                
        except Exception as e:
            logger.error(f"Error generating correlations: {str(e)}")
            return self._default_correlations(health_data)

    async def _openrouter_correlations(self, context: str) -> Dict[str, Any]:
        """Generate correlations using OpenRouter"""
        try:
            response = self.openrouter_client.chat.completions.create(
                model="anthropic/claude-3-haiku",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a health data analyst AI. Identify correlations between dietary habits, lifestyle factors, and health outcomes. Provide statistical insights and actionable recommendations."
                    },
                    {"role": "user", "content": context}
                ],
                max_tokens=600,
                temperature=0.4
            )
            
            content = response.choices[0].message.content
            
            return {
                "source": "openrouter",
                "model": "claude-3-haiku",
                "correlations": self._parse_correlation_response(content),
                "confidence": 0.82
            }
            
        except Exception as e:
            logger.error(f"OpenRouter correlations error: {str(e)}")
            return {}

    async def generate_clinical_insights(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clinical insights for healthcare providers"""
        try:
            context = self._build_clinical_context(provider_data)
            
            if self.openrouter_client:
                insights = await self._openrouter_clinical_analysis(context)
                return insights
            elif self.gemini_client:
                insights = await self._gemini_clinical_analysis(context)
                return insights
            else:
                return self._default_clinical_insights(provider_data)
                
        except Exception as e:
            logger.error(f"Error generating clinical insights: {str(e)}")
            return self._default_clinical_insights(provider_data)

    # =====================
    # Enhanced Chat Orchestration with Advanced Context
    # =====================
    async def generate_chat_response(self, message: str, history: List[Dict[str, Any]], context_type: str = "health_and_nutrition", user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a sophisticated, contextually-aware chat response with enhanced AI capabilities"""
        
        # Enhanced system prompt with advanced capabilities
        system_instruction = self._build_enhanced_system_prompt(context_type, user_context)
        
        # Build comprehensive conversation context
        conversation_context = self._build_conversation_context(history, message, user_context)
        
        # Create dynamic, context-aware user prompt
        user_prompt = self._create_dynamic_prompt(message, conversation_context, context_type, user_context)

        # Try advanced models with enhanced prompting
        response_data = await self._try_enhanced_ai_providers(system_instruction, user_prompt, conversation_context)
        
        # Post-process response for enhanced quality
        enhanced_response = self._enhance_response_quality(response_data, conversation_context, user_context)
        
        return enhanced_response

    def _build_enhanced_system_prompt(self, context_type: str, user_context: Dict[str, Any] = None) -> str:
        """Build an advanced, context-aware system prompt for superior AI responses"""
        
        base_expertise = (
            "You are an advanced AI nutrition and health specialist with deep expertise in:\n"
            "- Evidence-based nutritional science and dietetics\n"
            "- Personalized health recommendations and meal planning\n"
            "- Behavioral psychology for sustainable health habits\n"
            "- Clinical nutrition and therapeutic interventions\n"
            "- Food science, metabolism, and nutrient interactions\n\n"
        )
        
        personality_traits = (
            "Your communication style is:\n"
            "- Empathetic and encouraging, yet scientifically rigorous\n"
            "- Conversational and engaging while maintaining professionalism\n"
            "- Adaptive to user's knowledge level and emotional state\n"
            "- Proactive in asking relevant follow-up questions\n"
            "- Supportive of gradual, sustainable changes over drastic measures\n\n"
        )
        
        # Dynamic context adaptation
        contextual_focus = ""
        if user_context:
            profile_type = user_context.get('profile_type', 'general')
            health_goals = user_context.get('health_goals', [])
            dietary_restrictions = user_context.get('dietary_restrictions', [])
            
            if profile_type == 'patient':
                contextual_focus += "SPECIALIZED CONTEXT: You're assisting a patient - provide clinical-grade accuracy with compassionate guidance.\n"
            elif profile_type == 'provider':
                contextual_focus += "SPECIALIZED CONTEXT: You're assisting a healthcare provider - provide evidence-based insights suitable for clinical practice.\n"
            elif profile_type == 'family':
                contextual_focus += "SPECIALIZED CONTEXT: You're assisting a family - consider multi-generational needs and practical family dynamics.\n"
                
            if health_goals:
                contextual_focus += f"USER GOALS: {', '.join(health_goals)}\n"
            if dietary_restrictions:
                contextual_focus += f"DIETARY CONSIDERATIONS: {', '.join(dietary_restrictions)}\n"
                
        output_format = (
            "\nCRITICAL: Provide COMPREHENSIVE, DETAILED responses (aim for 400-800 words). You must respond in STRICT JSON format with enhanced structure:\n"
            "{\n"
            '  "title": "Engaging, specific title relevant to user query",\n'
            '  "summary": "Comprehensive, detailed main response (4-6 sentences minimum, naturally conversational, thorough explanation with examples and context)",\n'
            '  "key_points": ["4-6 evidence-based insights specific to user situation with detailed explanations"],\n'
            '  "action_steps": ["4-6 concrete, detailed actionable steps user can take immediately with specific instructions"],\n'
            '  "tips": ["4-5 practical, detailed tips or pro-insights with explanations"],\n'
            '  "suggestions": ["3-4 natural follow-up questions user might ask"],\n'
            '  "quick_actions": [{"type": "action_type", "label": "Button text", "action": "action_id"}],\n'
            '  "personalization": "Detailed insight showing you understand their specific context (2-3 sentences)",\n'
            '  "confidence_level": "high|medium|moderate - based on evidence quality",\n'
            '  "follow_up_priority": "high|medium|low - how important is continued conversation"\n'
            "}\n\n"
            "MANDATORY: Each response must be comprehensive and detailed. Provide thorough explanations, specific examples, step-by-step guidance, and practical context. Be conversational yet professional, specific yet accessible, evidence-based yet empathetic."
        )
        
        return base_expertise + personality_traits + contextual_focus + output_format

    def _build_conversation_context(self, history: List[Dict[str, Any]], current_message: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build comprehensive conversation context for enhanced AI responses"""
        
        # Analyze conversation patterns
        context = {
            "conversation_length": len(history) if history else 0,
            "user_engagement": "new",
            "topics_discussed": [],
            "user_preferences_detected": {},
            "conversation_tone": "neutral"
        }
        
        if history and len(history) > 0:
            # Analyze engagement level
            if len(history) >= 6:
                context["user_engagement"] = "highly_engaged"
            elif len(history) >= 3:
                context["user_engagement"] = "engaged"
            else:
                context["user_engagement"] = "exploring"
                
            # Extract topics and patterns
            all_messages = [msg.get("content", "") for msg in history[-10:]]
            context["topics_discussed"] = self._extract_conversation_topics(all_messages)
            
            # Detect user preferences and concerns
            context["user_preferences_detected"] = self._detect_user_preferences(all_messages + [current_message])
            
            # Analyze conversation tone
            context["conversation_tone"] = self._analyze_conversation_tone(all_messages + [current_message])
        
        # Add user profile context if available
        if user_context:
            context["user_profile"] = user_context
            context["personalization_available"] = True
        else:
            context["personalization_available"] = False
            
        return context

    def _create_dynamic_prompt(self, message: str, context: Dict[str, Any], context_type: str, user_context: Dict[str, Any] = None) -> str:
        """Create a dynamic, intelligent prompt based on conversation context"""
        
        # Build conversation history with intelligence
        history_summary = ""
        if context["conversation_length"] > 0:
            engagement_level = context["user_engagement"]
            topics = context["topics_discussed"]
            preferences = context["user_preferences_detected"]
            tone = context["conversation_tone"]
            
            history_summary = f"""
CONVERSATION CONTEXT:
- User engagement level: {engagement_level}
- Topics discussed: {', '.join(topics) if topics else 'None yet'}
- Detected preferences: {', '.join([f"{k}: {v}" for k, v in preferences.items()]) if preferences else 'Learning...'}
- Conversation tone: {tone}
- Context type: {context_type}
"""

        # Add personalization context
        personalization_context = ""
        if user_context:
            personalization_context = f"""
USER PROFILE CONTEXT:
- Profile type: {user_context.get('profile_type', 'general')}
- Health goals: {user_context.get('health_goals', 'Not specified')}
- Dietary restrictions: {user_context.get('dietary_restrictions', 'None mentioned')}
- Previous interactions: {user_context.get('interaction_count', 0)}
"""

        # Current message analysis
        message_analysis = f"""
CURRENT MESSAGE ANALYSIS:
- User message: "{message}"
- Intent: {self._analyze_message_intent(message)}
- Urgency: {self._assess_message_urgency(message)}
- Complexity: {self._assess_message_complexity(message)}
"""

        prompt = f"""
{history_summary}
{personalization_context}
{message_analysis}

INSTRUCTION: Generate a highly contextual, personalized response that:
1. Acknowledges the conversation history and user's journey
2. Provides specific, actionable advice based on their situation
3. Maintains conversational flow and builds rapport
4. Offers relevant follow-up suggestions that advance their health goals
5. Shows deep understanding of their context and needs

Respond in the specified JSON format with enhanced personalization and context awareness.
"""
        
        return prompt.strip()

    def _extract_conversation_topics(self, messages: List[str]) -> List[str]:
        """Extract key topics from conversation messages"""
        topics = set()
        
        # Health and nutrition keywords
        nutrition_keywords = {
            'protein', 'carbs', 'carbohydrates', 'fats', 'calories', 'vitamins', 'minerals',
            'breakfast', 'lunch', 'dinner', 'snack', 'meal', 'diet', 'nutrition',
            'weight', 'fitness', 'exercise', 'health', 'wellness', 'energy'
        }
        
        for message in messages:
            if not message:
                continue
            words = message.lower().split()
            for word in words:
                if word in nutrition_keywords:
                    topics.add(word)
                    
        return list(topics)[:8]  # Limit to most relevant topics

    def _detect_user_preferences(self, messages: List[str]) -> Dict[str, str]:
        """Detect user preferences from conversation patterns"""
        preferences = {}
        
        combined_text = ' '.join(messages).lower()
        
        # Detect dietary preferences
        if any(word in combined_text for word in ['vegetarian', 'vegan', 'plant-based']):
            preferences['diet_type'] = 'plant-based'
        elif any(word in combined_text for word in ['keto', 'low-carb', 'ketogenic']):
            preferences['diet_type'] = 'low-carb'
        elif any(word in combined_text for word in ['mediterranean', 'whole food']):
            preferences['diet_type'] = 'whole-food'
            
        # Detect health goals
        if any(word in combined_text for word in ['lose weight', 'weight loss', 'slim down']):
            preferences['primary_goal'] = 'weight_loss'
        elif any(word in combined_text for word in ['gain weight', 'build muscle', 'bulk']):
            preferences['primary_goal'] = 'muscle_building'
        elif any(word in combined_text for word in ['energy', 'tired', 'fatigue']):
            preferences['primary_goal'] = 'energy_boost'
            
        # Detect communication style preference
        if any(word in combined_text for word in ['quick', 'simple', 'easy', 'brief']):
            preferences['communication_style'] = 'concise'
        elif any(word in combined_text for word in ['detailed', 'explain', 'why', 'science']):
            preferences['communication_style'] = 'detailed'
            
        return preferences

    def _analyze_conversation_tone(self, messages: List[str]) -> str:
        """Analyze the overall tone of the conversation"""
        if not messages:
            return "neutral"
            
        combined_text = ' '.join(messages).lower()
        
        # Positive indicators
        positive_words = ['great', 'awesome', 'excellent', 'love', 'enjoy', 'excited', 'motivated']
        # Concern indicators  
        concern_words = ['worried', 'concerned', 'struggling', 'difficult', 'problem', 'issue', 'help']
        # Question indicators
        question_words = ['what', 'how', 'why', 'when', 'where', 'which', '?']
        
        positive_count = sum(1 for word in positive_words if word in combined_text)
        concern_count = sum(1 for word in concern_words if word in combined_text)
        question_count = sum(1 for word in question_words if word in combined_text)
        
        if concern_count > positive_count:
            return "concerned"
        elif positive_count > concern_count:
            return "positive"
        elif question_count > 2:
            return "inquisitive"
        else:
            return "neutral"

    def _analyze_message_intent(self, message: str) -> str:
        """Analyze the intent behind the current message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['what should i', 'recommend', 'suggest', 'advice']):
            return "seeking_recommendation"
        elif any(word in message_lower for word in ['how to', 'how do i', 'steps', 'process']):
            return "seeking_guidance"
        elif any(word in message_lower for word in ['why', 'explain', 'understand', 'reason']):
            return "seeking_explanation"
        elif any(word in message_lower for word in ['is it', 'can i', 'should i', 'safe']):
            return "seeking_validation"
        elif any(word in message_lower for word in ['problem', 'issue', 'wrong', 'concern']):
            return "reporting_issue"
        else:
            return "general_inquiry"

    def _assess_message_urgency(self, message: str) -> str:
        """Assess the urgency level of the message"""
        urgent_keywords = ['urgent', 'emergency', 'immediately', 'asap', 'serious', 'critical']
        moderate_keywords = ['soon', 'quickly', 'important', 'concerned', 'worried']
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in urgent_keywords):
            return "high"
        elif any(word in message_lower for word in moderate_keywords):
            return "moderate"
        else:
            return "low"

    def _assess_message_complexity(self, message: str) -> str:
        """Assess the complexity level of the user's question"""
        complex_keywords = ['interaction', 'metabolism', 'bioavailability', 'clinical', 'research', 'study']
        technical_keywords = ['macros', 'micronutrients', 'glycemic', 'insulin', 'hormonal']
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in complex_keywords):
            return "high"
        elif any(word in message_lower for word in technical_keywords) or len(message.split()) > 20:
            return "moderate"
        else:
            return "low"

    async def _try_enhanced_ai_providers(self, system_instruction: str, user_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Try AI providers with enhanced context and better model selection"""
        
        # Enhanced Groq with better model selection
        if self.groq_client:
            try:
                # Use more sophisticated model for complex conversations
                model = "llama3-70b-8192" if context.get("conversation_length", 0) > 3 else "llama3-8b-8192"
                temperature = 0.7 if context.get("conversation_tone") == "inquisitive" else 0.6
                
                completion = self.groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=2500,  # Increased for detailed, comprehensive responses
                    temperature=temperature,
                )
                content = completion.choices[0].message.content
                parsed = self._parse_enhanced_json(content)
                if parsed:
                    parsed.update({
                        "provider": "groq", 
                        "model": model, 
                        "confidence": 0.92,
                        "context_awareness": "high"
                    })
                    return parsed
            except Exception as e:
                logger.warning(f"Enhanced Groq chat failed, will fallback: {e}")
        
        # Enhanced Gemini with context-aware prompting
        if self.gemini_client:
            def _enhanced_gemini_chat():
                enhanced_prompt = f"""
{system_instruction}

ENHANCED CONTEXT INSTRUCTIONS:
- Conversation engagement: {context.get('user_engagement', 'new')}
- User preferences detected: {context.get('user_preferences_detected', {})}
- Conversation tone: {context.get('conversation_tone', 'neutral')}
- Personalization available: {context.get('personalization_available', False)}

{user_prompt}

CRITICAL: Respond with sophisticated, contextually-aware JSON that demonstrates deep understanding of the user's situation and conversation history. Make it feel like you truly understand their journey and needs.
"""
                return self.gemini_client.generate_content(enhanced_prompt)
                
            try:
                response = self._retry_with_gemini_rotation(_enhanced_gemini_chat)
                content = getattr(response, 'text', str(response))
                parsed = self._parse_enhanced_json(content)
                if parsed:
                    parsed.update({
                        "provider": "gemini", 
                        "model": self.gemini_model_preferred, 
                        "confidence": 0.89,
                        "context_awareness": "high"
                    })
                    return parsed
            except Exception as e:
                logger.warning(f"Enhanced Gemini chat failed, will fallback: {e}")

        # Enhanced OpenRouter with better model selection
        if self.openrouter_client:
            try:
                # Use better models for complex conversations
                model = "anthropic/claude-3-haiku" if context.get("conversation_length", 0) > 5 else "mistralai/mistral-7b-instruct"
                
                resp = self.openrouter_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=2500,
                    temperature=0.65,
                )
                content = resp.choices[0].message.content
                parsed = self._parse_enhanced_json(content)
                if parsed:
                    parsed.update({
                        "provider": "openrouter", 
                        "model": model, 
                        "confidence": 0.86,
                        "context_awareness": "moderate"
                    })
                    return parsed
            except Exception as e:
                logger.warning(f"Enhanced OpenRouter chat failed, will fallback: {e}")

        # Enhanced HuggingFace fallback
        if self.hf_client:
            try:
                enhanced_hf_prompt = f"""
{system_instruction}

Context: {context.get('user_engagement', 'new')} user with {context.get('conversation_tone', 'neutral')} tone.
{user_prompt}

Provide contextually-aware JSON response:
"""
                content = self.hf_client.text_generation(
                    enhanced_hf_prompt, 
                    max_new_tokens=2000, 
                    temperature=0.7,
                    do_sample=True
                )
                parsed = self._parse_enhanced_json(content)
                if parsed:
                    parsed.update({
                        "provider": "huggingface", 
                        "model": "enhanced-mixtral", 
                        "confidence": 0.80,
                        "context_awareness": "moderate"
                    })
                    return parsed
            except Exception as e:
                logger.warning(f"Enhanced HuggingFace chat failed: {e}")

        # Enhanced fallback response with context awareness
        return self._create_enhanced_fallback(context)

    def _enhance_response_quality(self, response_data: Dict[str, Any], context: Dict[str, Any], user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Post-process AI response to enhance quality and personalization"""
        
        if not response_data:
            return self._create_enhanced_fallback(context)
            
        # Enhance suggestions based on context
        if context.get("user_engagement") == "highly_engaged":
            response_data["suggestions"] = self._generate_advanced_suggestions(response_data, context)
        
        # Add contextual quick actions
        response_data["quick_actions"] = self._generate_contextual_quick_actions(response_data, context)
        
        # Enhance personalization
        if user_context and context.get("personalization_available"):
            response_data["personalization"] = self._generate_personalization_insight(response_data, user_context, context)
        
        # Set follow-up priority based on message urgency and complexity
        message_urgency = context.get("message_urgency", "low")
        if message_urgency == "high":
            response_data["follow_up_priority"] = "high"
        elif context.get("user_engagement") == "highly_engaged":
            response_data["follow_up_priority"] = "medium"
        else:
            response_data["follow_up_priority"] = "low"
            
        # Ensure confidence level is set
        if "confidence_level" not in response_data:
            provider_confidence = response_data.get("confidence", 0.8)
            if provider_confidence > 0.9:
                response_data["confidence_level"] = "high"
            elif provider_confidence > 0.7:
                response_data["confidence_level"] = "medium"
            else:
                response_data["confidence_level"] = "moderate"
        
        return response_data

    def _parse_enhanced_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Enhanced JSON parsing with better error handling and validation"""
        if not text:
            return None
            
        # Clean and extract JSON
        cleaned = text.strip()
        if cleaned.startswith('```'):
            # Remove code fences
            lines = cleaned.split('\n')
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith('```'):
                    in_json = not in_json
                    continue
                if in_json or (line.strip().startswith('{') or line.strip().startswith('"')):
                    json_lines.append(line)
            cleaned = '\n'.join(json_lines)
        
        # Try to find JSON object
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1:
            cleaned = cleaned[start_idx:end_idx + 1]
        
        try:
            obj = json.loads(cleaned)
            
            # Enhanced validation with defaults
            required_fields = {
                "title": "Let me help you with that",
                "summary": "I'm here to provide personalized nutrition and health guidance.",
                "key_points": [],
                "action_steps": [],
                "tips": [],
                "suggestions": [],
                "quick_actions": [],
                "personalization": "",
                "confidence_level": "medium",
                "follow_up_priority": "medium"
            }
            
            for key, default_value in required_fields.items():
                if key not in obj:
                    obj[key] = default_value
                    
            return obj
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            # Try to extract useful information from malformed response
            return self._salvage_response_data(text)

    def _salvage_response_data(self, text: str) -> Dict[str, Any]:
        """Try to salvage useful information from malformed AI responses"""
        # Extract title if present
        title_match = re.search(r'"title":\s*"([^"]*)"', text)
        title = title_match.group(1) if title_match else "Nutrition Guidance"
        
        # Extract summary if present
        summary_match = re.search(r'"summary":\s*"([^"]*)"', text)
        summary = summary_match.group(1) if summary_match else text[:200] + "..." if len(text) > 200 else text
        
        return {
            "title": title,
            "summary": summary,
            "key_points": ["I'm here to help with your nutrition questions"],
            "action_steps": ["Feel free to ask me anything about food and health"],
            "tips": ["Small, consistent changes lead to lasting results"],
            "suggestions": ["What's your main health goal?", "Tell me about your current diet"],
            "quick_actions": [{"type": "meal_suggestion", "label": "Get meal ideas", "action": "meal_suggestions"}],
            "personalization": "I'm learning about your preferences to provide better guidance.",
            "confidence_level": "moderate",
            "follow_up_priority": "medium",
            "provider": "salvaged",
            "confidence": 0.6
        }

    def _generate_advanced_suggestions(self, response: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate more sophisticated follow-up suggestions for engaged users"""
        base_suggestions = response.get("suggestions", [])
        topics = context.get("topics_discussed", [])
        preferences = context.get("user_preferences_detected", {})
        
        advanced_suggestions = []
        
        # Add topic-specific advanced questions
        if "protein" in topics:
            advanced_suggestions.append("How much protein should I eat per meal for optimal absorption?")
        if "weight" in topics and preferences.get("primary_goal") == "weight_loss":
            advanced_suggestions.append("What's the best timing for meals to support weight loss?")
        if "energy" in topics:
            advanced_suggestions.append("Which micronutrients are most important for sustained energy?")
            
        # Combine with base suggestions, prioritizing advanced ones
        all_suggestions = advanced_suggestions + base_suggestions
        return all_suggestions[:4]  # Limit to 4 suggestions

    def _generate_contextual_quick_actions(self, response: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate contextual quick actions based on conversation state"""
        actions = []
        
        user_engagement = context.get("user_engagement", "new")
        topics = context.get("topics_discussed", [])
        preferences = context.get("user_preferences_detected", {})
        
        # Add engagement-appropriate actions
        if user_engagement == "new":
            actions.append({"type": "assessment", "label": "Quick health assessment", "action": "start_assessment"})
        elif user_engagement == "engaged":
            if "meal" in topics:
                actions.append({"type": "meal_plan", "label": "Create meal plan", "action": "create_meal_plan"})
            if preferences.get("primary_goal") == "weight_loss":
                actions.append({"type": "calorie_calculator", "label": "Calculate daily calories", "action": "calc_calories"})
        elif user_engagement == "highly_engaged":
            actions.append({"type": "progress_tracker", "label": "Track progress", "action": "track_progress"})
            actions.append({"type": "expert_consultation", "label": "Book consultation", "action": "book_consultation"})
            
        # Limit to 2 most relevant actions
        return actions[:2]

    def _generate_personalization_insight(self, response: Dict[str, Any], user_context: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate a personalized insight that shows understanding of user context"""
        profile_type = user_context.get("profile_type", "general")
        health_goals = user_context.get("health_goals", [])
        interaction_count = user_context.get("interaction_count", 0)
        
        insights = []
        
        if profile_type == "patient":
            insights.append("As a patient, I'm focusing on evidence-based recommendations that align with clinical best practices.")
        elif profile_type == "provider":
            insights.append("I'm providing insights that can support your clinical practice and patient education.")
        elif profile_type == "family":
            insights.append("I understand you're managing health for multiple family members - I'll keep practical family dynamics in mind.")
            
        if health_goals:
            insights.append(f"I notice your focus on {', '.join(health_goals[:2])} - my suggestions are tailored to support these goals.")
            
        if interaction_count > 5:
            insights.append("Based on our previous conversations, I'm building a more complete picture of your preferences and needs.")
        elif interaction_count > 0:
            insights.append("I'm learning about your preferences to provide increasingly personalized guidance.")
            
        return ". ".join(insights) if insights else "I'm here to provide personalized guidance based on your unique situation."

    def _create_enhanced_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create an enhanced fallback response that's still contextually aware"""
        user_engagement = context.get("user_engagement", "new")
        conversation_tone = context.get("conversation_tone", "neutral")
        
        # Adjust response based on context
        if user_engagement == "new":
            title = "Welcome! Let's explore your nutrition journey together"
            summary = "I'm here to provide personalized nutrition and health guidance based on the latest evidence-based research."
            action_steps = [
                "Tell me about your current eating habits or health goals",
                "Share any dietary preferences or restrictions you have",
                "Ask me about any specific nutrition topics you're curious about"
            ]
        elif user_engagement == "engaged":
            title = "Let's dive deeper into your health goals"
            summary = "Based on our conversation, I'm here to provide more targeted guidance for your specific needs."
            action_steps = [
                "Let's explore specific strategies for your goals",
                "I can provide detailed meal planning or nutrition timing advice",
                "We can discuss advanced topics like nutrient timing or supplementation"
            ]
        else:  # highly_engaged
            title = "Advanced nutrition strategies tailored for you"
            summary = "I appreciate your commitment to optimizing your health. Let me provide advanced, evidence-based strategies."
            action_steps = [
                "Implement advanced nutrition periodization techniques",
                "Explore biomarker optimization through targeted nutrition",
                "Develop comprehensive lifestyle integration strategies"
            ]
            
        # Adjust tone
        if conversation_tone == "concerned":
            summary += " I understand your concerns and I'm here to provide reassuring, practical guidance."
        elif conversation_tone == "positive":
            summary += " I love your enthusiasm! Let's build on that positive momentum."
            
        return {
            "title": title,
            "summary": summary,
            "key_points": [
                "Evidence-based nutrition guidance tailored to your needs",
                "Practical strategies that fit your lifestyle",
                "Ongoing support for sustainable health improvements"
            ],
            "action_steps": action_steps,
            "tips": [
                "Small, consistent changes create lasting transformation",
                "Your unique situation requires personalized approaches",
                "I'm here to support your journey every step of the way"
            ],
            "suggestions": [
                "What's your main health priority right now?",
                "Tell me about your current meal routine",
                "What nutrition topics confuse you most?",
                "How can I help you achieve your health goals?"
            ],
            "quick_actions": [
                {"type": "assessment", "label": "Quick health assessment", "action": "start_assessment"},
                {"type": "meal_suggestion", "label": "Get meal suggestions", "action": "meal_suggestions"}
            ],
            "personalization": "I'm adapting my guidance to match your engagement level and provide increasingly valuable insights.",
            "confidence_level": "high",
            "follow_up_priority": "medium",
            "provider": "enhanced_fallback",
            "model": "context-aware",
            "confidence": 0.85,
            "context_awareness": "high"
        }

    # ========= Helper parsers =========
    def _parse_structured_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        # Trim code fences if present
        cleaned = text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.strip('`')
            # remove possible json hint
            cleaned = cleaned.replace('json', '', 1).strip()
        try:
            obj = json.loads(cleaned)
            # Basic validation
            for k in ["title", "summary", "key_points", "action_steps"]:
                if k not in obj:
                    obj.setdefault(k, []) if k.endswith('s') else obj.setdefault(k, "")
            obj.setdefault("tips", [])
            obj.setdefault("suggestions", [])
            obj.setdefault("quick_actions", [])
            return obj
        except Exception:
            return None

    def _gemini_correlations(self, context: str) -> Dict[str, Any]:
        # Existing method placeholder (not shown here)
        return {"correlations": []}

    def _gemini_clinical_analysis(self, context: str) -> Dict[str, Any]:
        return {"insights": []}

    def _openrouter_clinical_analysis(self, context: str) -> Dict[str, Any]:
        return {"insights": []}

    def _parse_goal_text_response(self, text: str) -> Dict[str, Any]:
        """Parse goal insights from text response"""
        return {
            "source": "gemini",
            "model": self.gemini_model_preferred, 
            "api_key_index": self.gemini_rotator.current_key_index,
            "insights": ["Goal analysis completed successfully"],
            "recommendations": [{"title": "Continue Progress", "description": text[:200] + "...", "priority": "medium", "timeline": "1-2 weeks", "success_probability": 0.75}],
            "goal_adjustments": [],
            "milestone_suggestions": [],
            "confidence": 0.70
        }
    
    def _parse_achievement_response(self, text: str) -> Dict[str, Any]:
        """Parse achievement insights from text response"""
        lines = text.split('\n')
        insights = []
        recommendations = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['achievement', 'milestone', 'badge']):
                insights.append(line.strip())
            elif any(keyword in line.lower() for keyword in ['suggest', 'recommend', 'try']):
                recommendations.append(line.strip())
        
        return {
            "achievements": insights[:3] if insights else ["You're making great progress!"],
            "milestone_suggestions": recommendations[:3] if recommendations else ["Keep up the great work!"],
            "motivation_tips": ["Stay consistent", "Celebrate small wins", "Track your progress"],
            "social_sharing_ideas": ["Share your latest achievement", "Inspire others with your progress"]
        }
    
    def _default_goal_insights(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide default goal insights when AI services are unavailable"""
        return {
            "source": "default",
            "insights": [
                "Your goal progress shows consistent effort",
                "Consider breaking large goals into smaller milestones",
                "Regular review and adjustment improve success rates"
            ],
            "recommendations": [
                {
                    "title": "Weekly Goal Review",
                    "description": "Set aside time each week to review progress and adjust goals as needed",
                    "priority": "high",
                    "timeline": "Weekly",
                    "success_probability": 0.80
                },
                {
                    "title": "Milestone Tracking",
                    "description": "Break larger goals into smaller, achievable milestones",
                    "priority": "medium", 
                    "timeline": "2-4 weeks",
                    "success_probability": 0.75
                }
            ],
            "goal_adjustments": [],
            "milestone_suggestions": [
                {
                    "milestone": "Complete 7 days of consistent progress",
                    "target_date": "Next week",
                    "success_criteria": "Daily goal completion"
                }
            ],
            "confidence": 0.60
        }
    
    def _default_achievement_insights(self, achievement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide default achievement insights when AI services are unavailable"""
        return {
            "source": "default",
            "achievement_insights": {
                "achievements": [
                    "You're building healthy habits consistently",
                    "Your progress shows dedication to your goals",
                    "Every small step counts toward your larger objectives"
                ],
                "milestone_suggestions": [
                    "Celebrate completing your current goal streak", 
                    "Share your progress with friends and family",
                    "Set a new personal best for goal completion"
                ],
                "motivation_tips": [
                    "Focus on progress, not perfection",
                    "Reward yourself for milestones achieved",
                    "Connect with others who share similar goals"
                ],
                "social_sharing_ideas": [
                    "Share your weekly goal completion rate",
                    "Post about a healthy habit you've maintained",
                    "Inspire others by sharing your goal journey"
                ]
            },
            "confidence": 0.60
        }

    def _groq_goal_analysis(self, context: str) -> Dict[str, Any]:
        """Use Groq for goal analysis (kept for compatibility)"""
        return {}

    def _build_nutrition_context(self, user_data: Dict[str, Any]) -> str:
        """Build context string for nutrition analysis"""
        return f"""
        User Profile Analysis Request:
        
        Demographics: Age {user_data.get('age', 'N/A')}, Gender: {user_data.get('gender', 'N/A')}
        Activity Level: {user_data.get('activity_level', 'N/A')}
        Health Goals: {user_data.get('goals', [])}
        Current Diet: {user_data.get('diet_type', 'N/A')}
        
        Recent Nutrition Data:
        - Calories: {user_data.get('avg_calories', 'N/A')}
        - Protein: {user_data.get('avg_protein', 'N/A')}g
        - Carbs: {user_data.get('avg_carbs', 'N/A')}g
        - Fat: {user_data.get('avg_fat', 'N/A')}g
        
        Health Metrics:
        - Weight: {user_data.get('weight', 'N/A')}kg
        - Energy Level: {user_data.get('energy_level', 'N/A')}/10
        - Sleep Quality: {user_data.get('sleep_quality', 'N/A')}/10
        
        Please provide personalized nutrition insights and recommendations.
        """

    def _build_food_suggestion_context(self, profile: Dict[str, Any], intake: Dict[str, Any]) -> str:
        """Build context for food suggestions"""
        return f"""
        Food Suggestion Request:
        
        User Profile:
        - Dietary Preferences: {profile.get('diet_type', 'N/A')}
        - Allergies: {profile.get('allergies', [])}
        - Favorite Foods: {profile.get('favorite_foods', [])}
        - Cooking Time Available: {profile.get('cooking_time', 'N/A')} minutes
        
        Current Daily Intake:
        - Calories consumed: {intake.get('calories', 0)}
        - Protein: {intake.get('protein', 0)}g
        - Remaining calories needed: {intake.get('calories_remaining', 'N/A')}
        
        Time of day: {intake.get('time_of_day', 'N/A')}
        
        Suggest 4-6 appropriate foods that fit their preferences and nutritional needs.
        """

    def _build_correlation_context(self, health_data: Dict[str, Any]) -> str:
        """Build context for health correlations"""
        return f"""
        Health Correlation Analysis Request:
        
        Historical Data Available:
        - {len(health_data.get('daily_logs', []))} days of food/health logs
        - Sleep patterns: {health_data.get('sleep_patterns', 'N/A')}
        - Exercise frequency: {health_data.get('exercise_frequency', 'N/A')}
        - Stress levels: {health_data.get('stress_levels', 'N/A')}
        
        Health Outcomes:
        - Energy levels trend: {health_data.get('energy_trend', 'N/A')}
        - Weight trend: {health_data.get('weight_trend', 'N/A')}
        - Mood patterns: {health_data.get('mood_patterns', 'N/A')}
        - Digestive health: {health_data.get('digestive_health', 'N/A')}
        
        Identify significant correlations between lifestyle factors and health outcomes.
        """

    def _default_nutrition_insights(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide default nutrition insights when AI services are unavailable"""
        return {
            "source": "default",
            "insights": [
                "Based on your current intake, consider balancing your macronutrients",
                "Ensure adequate hydration throughout the day",
                "Include variety in your food choices for optimal nutrient coverage"
            ],
            "recommendations": [
                "Aim for 0.8-1g protein per kg body weight",
                "Include 5-7 servings of fruits and vegetables daily",
                "Stay hydrated with 8-10 glasses of water"
            ],
            "correlations": [],
            "action_items": [
                "Track your meals consistently",
                "Monitor energy levels after meals",
                "Plan meals in advance"
            ],
            "confidence": 0.60
        }

    def _default_food_suggestions(self, profile: Dict[str, Any], intake: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Provide default food suggestions"""
        return [
            {
                "name": "Greek Yogurt with Berries",
                "calories": 150,
                "reason": "High in protein and probiotics",
                "nutrition_benefits": ["Protein", "Calcium", "Probiotics"],
                "meal_type": "snack"
            },
            {
                "name": "Mixed Green Salad with Chickpeas",
                "calories": 250,
                "reason": "Rich in fiber and plant protein",
                "nutrition_benefits": ["Fiber", "Iron", "Folate"],
                "meal_type": "lunch"
            },
            {
                "name": "Grilled Salmon with Vegetables",
                "calories": 400,
                "reason": "Omega-3 fatty acids and complete protein",
                "nutrition_benefits": ["Omega-3", "Protein", "Vitamins"],
                "meal_type": "dinner"
            }
        ]

    def _extract_insights_from_text(self, text: str, source: str) -> Dict[str, Any]:
        """Extract insights from AI text response"""
        # Simple text parsing for insights
        lines = text.split('\n')
        insights = []
        recommendations = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['insight', 'notice', 'observe']):
                insights.append(line.strip())
            elif any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'try']):
                recommendations.append(line.strip())
        
        return {
            "source": source,
            "insights": insights[:3] if insights else ["Analysis completed successfully"],
            "recommendations": recommendations[:3] if recommendations else ["Continue current healthy practices"],
            "correlations": [],
            "action_items": ["Monitor progress", "Stay consistent", "Adjust as needed"],
            "confidence": 0.75
        }

# Global AI service manager instance
ai_service_manager = AIServiceManager()

# Utility functions for easy access
async def get_nutrition_insights(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI-powered nutrition insights"""
    return await ai_service_manager.generate_nutrition_insights(user_data)

async def get_smart_food_suggestions(user_profile: Dict[str, Any], current_intake: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get AI-powered food suggestions"""
    return await ai_service_manager.generate_smart_food_suggestions(user_profile, current_intake)

async def get_health_correlations(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI-powered health correlations"""
    return await ai_service_manager.generate_health_correlations(health_data)

async def get_clinical_insights(provider_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI-powered clinical insights"""
    return await ai_service_manager.generate_clinical_insights(provider_data)

async def get_goal_insights(goal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI-powered goal insights and recommendations"""
    return await ai_service_manager.generate_goal_insights(goal_data)

async def get_achievement_insights(achievement_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI-powered achievement and milestone insights"""
    return await ai_service_manager.generate_achievement_insights(achievement_data)