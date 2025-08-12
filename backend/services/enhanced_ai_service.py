"""
Advanced AI Service with Enhanced Capabilities

This service provides:
- Multi-model AI routing with intelligent fallback
- Enhanced conversational memory and context awareness
- Sentiment analysis and emotion detection
- Smart conversation summarization
- Intent recognition and classification
- Personalized response adaptation
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import openai
import google.generativeai as genai
from groq import AsyncGroq
import requests
from textstat import flesch_reading_ease, flesch_kincaid_grade
import re
from collections import Counter
import hashlib

logger = logging.getLogger(__name__)

class ConversationAnalyzer:
    """Analyzes conversations for insights, sentiment, and patterns"""
    
    def __init__(self):
        self.emotion_keywords = {
            'joy': ['happy', 'excited', 'great', 'awesome', 'wonderful', 'fantastic', 'amazing', 'love', 'perfect'],
            'sadness': ['sad', 'depressed', 'down', 'unhappy', 'disappointed', 'upset', 'hurt', 'lonely'],
            'anger': ['angry', 'mad', 'furious', 'annoyed', 'frustrated', 'irritated', 'hate', 'disgusted'],
            'fear': ['afraid', 'scared', 'worried', 'anxious', 'nervous', 'concerned', 'panic', 'terrified'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'incredible', 'unbelievable'],
            'neutral': ['okay', 'fine', 'normal', 'regular', 'standard', 'typical']
        }
        
        self.intent_patterns = {
            'question': r'\b(what|how|when|where|who|why|which|can|could|would|should|is|are|do|does|did)\b',
            'request': r'\b(please|help|need|want|require|assist|support)\b',
            'complaint': r'\b(problem|issue|wrong|error|broken|not working|frustrated|unhappy)\b',
            'compliment': r'\b(thank|thanks|great|excellent|wonderful|amazing|perfect|love)\b',
            'goodbye': r'\b(bye|goodbye|see you|talk later|thanks for|that\'s all)\b',
            'greeting': r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b'
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment and emotion in text"""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            emotion_scores[emotion] = score
        
        # Determine primary emotion
        primary_emotion = max(emotion_scores, key=emotion_scores.get) if any(emotion_scores.values()) else 'neutral'
        confidence = emotion_scores[primary_emotion] / len(text.split()) if text.split() else 0
        
        # Calculate overall sentiment
        positive_emotions = ['joy', 'surprise']
        negative_emotions = ['sadness', 'anger', 'fear']
        
        positive_score = sum(emotion_scores[e] for e in positive_emotions)
        negative_score = sum(emotion_scores[e] for e in negative_emotions)
        
        if positive_score > negative_score:
            sentiment = 'positive'
            sentiment_score = min(positive_score / len(text.split()) * 10, 1.0) if text.split() else 0
        elif negative_score > positive_score:
            sentiment = 'negative'
            sentiment_score = min(negative_score / len(text.split()) * 10, 1.0) if text.split() else 0
        else:
            sentiment = 'neutral'
            sentiment_score = 0.5
        
        return {
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'primary_emotion': primary_emotion,
            'emotion_confidence': confidence,
            'emotion_breakdown': emotion_scores
        }
    
    def detect_intent(self, text: str) -> Dict[str, Any]:
        """Detect user intent from text"""
        text_lower = text.lower()
        detected_intents = {}
        
        for intent, pattern in self.intent_patterns.items():
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                detected_intents[intent] = matches
        
        primary_intent = max(detected_intents, key=detected_intents.get) if detected_intents else 'general'
        
        return {
            'primary_intent': primary_intent,
            'intent_confidence': detected_intents.get(primary_intent, 0) / len(text.split()) if text.split() else 0,
            'all_intents': detected_intents
        }
    
    def analyze_conversation_flow(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation flow and patterns"""
        if not messages:
            return {}
        
        user_messages = [m for m in messages if m.get('type') == 'user']
        bot_messages = [m for m in messages if m.get('type') in ['bot', 'assistant']]
        
        # Calculate conversation statistics
        total_turns = len(user_messages)
        avg_user_length = sum(len(m.get('content', '').split()) for m in user_messages) / total_turns if total_turns > 0 else 0
        
        # Analyze topic progression
        topics = []
        for msg in user_messages:
            content = msg.get('content', '')
            # Simple keyword extraction for topics
            words = re.findall(r'\b\w+\b', content.lower())
            topics.extend([w for w in words if len(w) > 4])  # Words longer than 4 chars
        
        topic_frequency = Counter(topics)
        main_topics = topic_frequency.most_common(5)
        
        # Analyze conversation engagement
        question_count = sum(1 for m in user_messages if '?' in m.get('content', ''))
        engagement_score = min((question_count + total_turns) / 10.0, 1.0)
        
        return {
            'total_turns': total_turns,
            'avg_message_length': avg_user_length,
            'main_topics': main_topics,
            'question_count': question_count,
            'engagement_score': engagement_score,
            'conversation_duration': self._calculate_duration(messages)
        }
    
    def _calculate_duration(self, messages: List[Dict]) -> float:
        """Calculate conversation duration in minutes"""
        if len(messages) < 2:
            return 0
        
        try:
            first_time = messages[0].get('timestamp')
            last_time = messages[-1].get('timestamp')
            
            if isinstance(first_time, str):
                first_time = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
            if isinstance(last_time, str):
                last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
            
            duration = (last_time - first_time).total_seconds() / 60
            return max(duration, 0)
        except:
            return 0

class EnhancedAIService:
    """Enhanced AI Service with multi-model support and advanced features"""
    
    def __init__(self):
        self.analyzer = ConversationAnalyzer()
        self.setup_clients()
        
        # Response enhancement settings
        self.personality_profiles = {
            'friendly': "Respond in a warm, friendly, and encouraging tone. Use casual language and show empathy. Provide detailed explanations with specific examples and practical tips. Aim for comprehensive responses that thoroughly address the user's needs.",
            'professional': "Respond in a professional, informative tone. Be precise and comprehensive. Provide detailed analysis, thorough explanations, and complete guidance. Include specific recommendations, step-by-step instructions, and evidence-based advice.",
            'casual': "Respond in a casual, conversational tone. Be relaxed and approachable while still being thorough and helpful. Provide detailed information in an easy-to-understand way with practical examples.",
            'enthusiastic': "Respond with enthusiasm and energy. Show excitement about helping the user. Provide comprehensive, detailed responses with lots of specific suggestions, tips, and encouragement.",
            'empathetic': "Respond with deep empathy and understanding. Be supportive and caring while providing thorough, detailed guidance. Offer comprehensive support with specific steps and considerate advice."
        }
    
    def setup_clients(self):
        """Initialize AI service clients"""
        try:
            # Groq client
            self.groq_client = AsyncGroq(api_key=os.getenv('GROQ_API_KEY'))
            
            # Gemini client
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            
            # OpenRouter setup
            self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
            
            logger.info("Enhanced AI Service clients initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AI clients: {e}")
    
    async def generate_enhanced_response(self, 
                                       message: str, 
                                       history: List[Dict], 
                                       user_context: Dict,
                                       conversation_analysis: Dict = None) -> Dict[str, Any]:
        """Generate enhanced response with multiple AI models and advanced features"""
        
        # Analyze current message
        sentiment_analysis = self.analyzer.analyze_sentiment(message)
        intent_analysis = self.analyzer.detect_intent(message)
        
        # Analyze conversation if not provided
        if not conversation_analysis:
            conversation_analysis = self.analyzer.analyze_conversation_flow(history)
        
        # Determine best AI model based on context
        best_model = self._select_best_model(message, sentiment_analysis, conversation_analysis)
        
        # Build enhanced context
        enhanced_context = self._build_enhanced_context(
            message, history, user_context, sentiment_analysis, intent_analysis, conversation_analysis
        )
        
        # Generate response with selected model
        response_data = await self._generate_with_model(best_model, enhanced_context)
        
        # Enhance response with additional features
        enhanced_response = await self._enhance_response(
            response_data, sentiment_analysis, intent_analysis, user_context
        )
        
        # Add metadata
        enhanced_response.update({
            'model_used': best_model,
            'sentiment_analysis': sentiment_analysis,
            'intent_analysis': intent_analysis,
            'conversation_analysis': conversation_analysis,
            'processing_time': datetime.utcnow().isoformat(),
            'context_quality': self._assess_context_quality(enhanced_context)
        })
        
        return enhanced_response
    
    def _select_best_model(self, message: str, sentiment: Dict, conversation: Dict) -> str:
        """Intelligently select the best AI model based on context"""
        
        # GPT-4 via OpenRouter for complex reasoning
        if any(keyword in message.lower() for keyword in ['analyze', 'compare', 'explain why', 'complex', 'detailed']):
            return 'openrouter_gpt4'
        
        # Groq for fast responses and casual chat
        if sentiment['sentiment'] == 'positive' or conversation.get('engagement_score', 0) > 0.7:
            return 'groq'
        
        # Gemini for creative and empathetic responses
        if sentiment['primary_emotion'] in ['sadness', 'fear'] or 'creative' in message.lower():
            return 'gemini'
        
        # Default to Groq for speed
        return 'groq'
    
    def _build_enhanced_context(self, message: str, history: List[Dict], user_context: Dict,
                              sentiment: Dict, intent: Dict, conversation: Dict) -> str:
        """Build enhanced context for AI models"""
        
        # Determine personality based on user sentiment and context
        personality = self._determine_personality(sentiment, user_context)
        
        context_parts = [
            f"PERSONALITY: {self.personality_profiles.get(personality, self.personality_profiles['friendly'])}",
            "",
            f"USER CONTEXT:",
            f"- Profile: {user_context.get('profile_type', 'general')}",
            f"- Interaction count: {user_context.get('interaction_count', 0)}",
            f"- Health goals: {user_context.get('health_goals', [])}",
            f"- Dietary restrictions: {user_context.get('dietary_restrictions', [])}",
            "",
            f"CURRENT MESSAGE ANALYSIS:",
            f"- Sentiment: {sentiment['sentiment']} ({sentiment['sentiment_score']:.2f})",
            f"- Primary emotion: {sentiment['primary_emotion']}",
            f"- Intent: {intent['primary_intent']}",
            "",
            f"CONVERSATION ANALYSIS:",
            f"- Total turns: {conversation.get('total_turns', 0)}",
            f"- Engagement score: {conversation.get('engagement_score', 0):.2f}",
            f"- Main topics: {[topic[0] for topic in conversation.get('main_topics', [])][:3]}",
            "",
            "RECENT CONVERSATION:"
        ]
        
        # Add recent messages for context
        recent_messages = history[-6:] if len(history) > 6 else history
        for msg in recent_messages:
            role = "User" if msg.get('type') == 'user' else "Assistant"
            content = msg.get('content', '')[:150] + '...' if len(msg.get('content', '')) > 150 else msg.get('content', '')
            context_parts.append(f"{role}: {content}")
        
        context_parts.extend([
            "",
            f"Current user message: {message}",
            "",
            "INSTRUCTIONS FOR DETAILED RESPONSE:",
            "1. Provide comprehensive, detailed responses (minimum 3-4 paragraphs)",
            "2. Include specific examples, practical tips, and actionable steps",
            "3. Explain the 'why' behind recommendations, not just the 'what'",
            "4. Address multiple aspects of the user's question thoroughly",
            "5. Provide step-by-step guidance where applicable",
            "6. Include relevant context and background information",
            "7. Offer specific meal ideas, recipes, or food suggestions when relevant",
            "8. Consider the user's sentiment and emotional state with empathy", 
            "9. Reference previous conversation topics when relevant",
            "10. Structure response with clear sections: overview, detailed explanation, specific recommendations, and next steps",
            "11. Aim for 400-800 words to ensure thoroughness",
            "12. Use bullet points, lists, and clear formatting for readability"
        ])
        
        return "\n".join(context_parts)
    
    def _determine_personality(self, sentiment: Dict, user_context: Dict) -> str:
        """Determine appropriate personality based on context"""
        
        if sentiment['primary_emotion'] in ['sadness', 'fear']:
            return 'empathetic'
        elif sentiment['sentiment'] == 'positive' and sentiment['sentiment_score'] > 0.7:
            return 'enthusiastic'
        elif user_context.get('profile_type') == 'provider':
            return 'professional'
        elif user_context.get('interaction_count', 0) > 5:
            return 'friendly'
        else:
            return 'casual'
    
    async def _generate_with_model(self, model: str, context: str) -> Dict[str, Any]:
        """Generate response with specified AI model"""
        
        try:
            if model == 'groq':
                return await self._generate_groq_response(context)
            elif model == 'gemini':
                return await self._generate_gemini_response(context)
            elif model == 'openrouter_gpt4':
                return await self._generate_openrouter_response(context)
            else:
                # Fallback to Groq
                return await self._generate_groq_response(context)
        except Exception as e:
            logger.error(f"Error with model {model}: {e}")
            # Try fallback models
            return await self._generate_fallback_response(context)
    
    async def _generate_groq_response(self, context: str) -> Dict[str, Any]:
        """Generate response using Groq"""
        try:
            response = await self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an advanced AI nutrition assistant with enhanced conversational abilities. Provide comprehensive, detailed responses with thorough explanations. Always aim for 400-800 words to ensure users receive complete, actionable guidance. Include specific examples, step-by-step instructions, and practical tips."},
                    {"role": "user", "content": context}
                ],
                max_tokens=2500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return self._parse_structured_response(content, 'groq')
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    async def _generate_gemini_response(self, context: str) -> Dict[str, Any]:
        """Generate response using Gemini"""
        try:
            system_prompt = "You are an advanced AI nutrition assistant with enhanced conversational abilities. Provide comprehensive, detailed responses with thorough explanations, specific examples, and practical guidance. Always aim for 400-800 words to ensure users receive complete, actionable information. Include step-by-step instructions, clear sections for key points, tips, and action steps."
            full_prompt = f"{system_prompt}\n\n{context}"
            
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config={
                    'temperature': 0.7,
                    'max_output_tokens': 2500,
                }
            )
            
            content = response.text if response.text else "I'm here to help with your nutrition questions!"
            return self._parse_structured_response(content, 'gemini')
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def _generate_openrouter_response(self, context: str) -> Dict[str, Any]:
        """Generate response using OpenRouter (GPT-4)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "openai/gpt-4",
                "messages": [
                    {"role": "system", "content": "You are an advanced AI nutrition assistant with enhanced conversational abilities. Provide comprehensive, detailed responses with thorough explanations, specific examples, and practical guidance. Always aim for 400-800 words to ensure users receive complete, actionable information. Include step-by-step instructions and detailed recommendations."},
                    {"role": "user", "content": context}
                ],
                "max_tokens": 2500,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return self._parse_structured_response(content, 'openrouter_gpt4')
            else:
                raise Exception(f"OpenRouter API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise
    
    async def _generate_fallback_response(self, context: str) -> Dict[str, Any]:
        """Generate fallback response when all AI models fail"""
        fallback_responses = [
            "I'm here to help you with your nutrition and health questions. What specific topic would you like to explore?",
            "I can provide guidance on healthy eating, meal planning, and nutrition. What would you like to know more about?",
            "Let me help you with your health and nutrition needs. Could you tell me more about what you're looking for?"
        ]
        
        import random
        response = random.choice(fallback_responses)
        
        return {
            'response': response,
            'title': 'How can I help you today?',
            'summary': response,
            'key_points': ['I\'m here to help with nutrition questions', 'Feel free to ask about healthy eating', 'I can provide personalized guidance'],
            'action_steps': ['Share your specific nutrition question', 'Tell me about your health goals', 'Ask about meal planning or healthy recipes'],
            'tips': ['Be specific in your questions for better help', 'I can assist with dietary restrictions', 'Feel free to ask follow-up questions'],
            'suggestions': ['What\'s a healthy breakfast?', 'How do I eat more vegetables?', 'Tell me about portion control'],
            'quick_actions': [{'label': 'Meal Planning', 'action': 'meal_planning'}, {'label': 'Nutrition Tips', 'action': 'nutrition_tips'}],
            'confidence': 0.8,
            'provider': 'fallback'
        }
    
    def _parse_structured_response(self, content: str, provider: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        
        # Extract structured elements using regex patterns
        title_match = re.search(r'(?:TITLE|Title):\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        summary_match = re.search(r'(?:SUMMARY|Summary):\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)', content, re.IGNORECASE | re.DOTALL)
        
        # Extract key points
        key_points = []
        key_points_match = re.search(r'(?:KEY POINTS?|Key Points?):\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)', content, re.IGNORECASE | re.DOTALL)
        if key_points_match:
            points_text = key_points_match.group(1)
            key_points = [point.strip().lstrip('•-*').strip() for point in points_text.split('\n') if point.strip()]
        
        # Extract action steps
        action_steps = []
        action_match = re.search(r'(?:ACTION STEPS?|Action Steps?|NEXT STEPS?):\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)', content, re.IGNORECASE | re.DOTALL)
        if action_match:
            action_text = action_match.group(1)
            action_steps = [step.strip().lstrip('•-*1234567890.').strip() for step in action_text.split('\n') if step.strip()]
        
        # Extract tips
        tips = []
        tips_match = re.search(r'(?:TIPS?|Tips?):\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)', content, re.IGNORECASE | re.DOTALL)
        if tips_match:
            tips_text = tips_match.group(1)
            tips = [tip.strip().lstrip('•-*').strip() for tip in tips_text.split('\n') if tip.strip()]
        
        # Generate suggestions based on content
        suggestions = self._generate_contextual_suggestions(content)
        
        # Generate quick actions
        quick_actions = self._generate_quick_actions(content)
        
        return {
            'response': content,
            'title': title_match.group(1).strip() if title_match else None,
            'summary': summary_match.group(1).strip() if summary_match else content[:200] + '...' if len(content) > 200 else content,
            'key_points': key_points[:5],  # Limit to 5 key points
            'action_steps': action_steps[:5],  # Limit to 5 action steps
            'tips': tips[:5],  # Limit to 5 tips
            'suggestions': suggestions,
            'quick_actions': quick_actions,
            'confidence': 0.85,
            'provider': provider
        }
    
    def _generate_contextual_suggestions(self, content: str) -> List[str]:
        """Generate contextual follow-up suggestions"""
        suggestions = []
        
        content_lower = content.lower()
        
        if 'breakfast' in content_lower:
            suggestions.extend(['What about healthy lunch ideas?', 'Tell me about protein-rich breakfasts'])
        if 'protein' in content_lower:
            suggestions.extend(['How much protein do I need daily?', 'What are plant-based protein sources?'])
        if 'weight' in content_lower:
            suggestions.extend(['Help with meal planning', 'Exercise and nutrition tips'])
        if 'vegetable' in content_lower:
            suggestions.extend(['How to make vegetables tasty?', 'Seasonal vegetable guide'])
        if 'vitamin' in content_lower or 'nutrient' in content_lower:
            suggestions.extend(['What supplements do I need?', 'Nutrient-rich food combinations'])
        
        # Default suggestions if no specific matches
        if not suggestions:
            suggestions = ['What\'s a healthy snack?', 'Help with meal prep', 'Nutrition for my age group']
        
        return suggestions[:3]  # Return max 3 suggestions
    
    def _generate_quick_actions(self, content: str) -> List[Dict[str, str]]:
        """Generate contextual quick actions"""
        content_lower = content.lower()
        actions = []
        
        if any(word in content_lower for word in ['meal', 'breakfast', 'lunch', 'dinner']):
            actions.append({'label': '🍽️ Meal Planning', 'action': 'meal_planning'})
        
        if any(word in content_lower for word in ['recipe', 'cook', 'prepare']):
            actions.append({'label': '👨‍🍳 Recipe Ideas', 'action': 'recipes'})
        
        if any(word in content_lower for word in ['exercise', 'workout', 'fitness']):
            actions.append({'label': '💪 Fitness Tips', 'action': 'fitness'})
        
        if any(word in content_lower for word in ['weight', 'lose', 'gain']):
            actions.append({'label': '⚖️ Weight Management', 'action': 'weight_management'})
        
        # Default actions
        if not actions:
            actions = [
                {'label': '📊 Nutrition Analysis', 'action': 'nutrition_analysis'},
                {'label': '🎯 Set Goals', 'action': 'set_goals'}
            ]
        
        return actions[:2]  # Return max 2 actions
    
    async def _enhance_response(self, response_data: Dict, sentiment: Dict, intent: Dict, user_context: Dict) -> Dict[str, Any]:
        """Add final enhancements to response"""
        
        # Add personalization based on user context
        if user_context.get('profile_type') == 'patient' and sentiment['primary_emotion'] in ['sadness', 'fear']:
            response_data['personalization'] = "I understand this can be challenging. Remember that small, consistent changes make the biggest difference in your health journey."
        elif user_context.get('health_goals') and 'weight_loss' in user_context['health_goals']:
            response_data['personalization'] = "Based on your weight loss goals, focus on sustainable changes that you can maintain long-term."
        elif user_context.get('interaction_count', 0) > 10:
            response_data['personalization'] = f"I notice we've had {user_context['interaction_count']} conversations - I'm here to support your ongoing health journey!"
        
        # Add confidence level based on various factors
        base_confidence = response_data.get('confidence', 0.85)
        
        # Adjust confidence based on user context richness
        if user_context.get('health_goals') or user_context.get('dietary_restrictions'):
            base_confidence += 0.05
        
        # Adjust based on conversation length
        if user_context.get('interaction_count', 0) > 5:
            base_confidence += 0.03
        
        response_data['confidence_level'] = min(base_confidence, 0.98)
        
        # Add follow-up priority
        if intent['primary_intent'] in ['complaint', 'request']:
            response_data['follow_up_priority'] = 'high'
        elif sentiment['sentiment'] == 'negative':
            response_data['follow_up_priority'] = 'medium'
        else:
            response_data['follow_up_priority'] = 'low'
        
        return response_data
    
    def _assess_context_quality(self, context: str) -> float:
        """Assess the quality of the context for analytics"""
        factors = []
        
        # Length factor
        word_count = len(context.split())
        length_score = min(word_count / 500.0, 1.0)  # Optimal around 500 words
        factors.append(length_score)
        
        # Information richness
        info_keywords = ['profile', 'context', 'sentiment', 'intent', 'history', 'goals']
        info_score = sum(1 for keyword in info_keywords if keyword in context.lower()) / len(info_keywords)
        factors.append(info_score)
        
        # Structure score
        structure_elements = ['USER CONTEXT:', 'CONVERSATION ANALYSIS:', 'INSTRUCTIONS:']
        structure_score = sum(1 for element in structure_elements if element in context) / len(structure_elements)
        factors.append(structure_score)
        
        return sum(factors) / len(factors)
    
    async def generate_conversation_summary(self, messages: List[Dict]) -> Dict[str, Any]:
        """Generate intelligent conversation summary"""
        if not messages:
            return {}
        
        analysis = self.analyzer.analyze_conversation_flow(messages)
        
        # Extract key topics and insights
        user_messages = [m for m in messages if m.get('type') == 'user']
        all_text = ' '.join([m.get('content', '') for m in user_messages])
        
        sentiment_analysis = self.analyzer.analyze_sentiment(all_text)
        
        summary = {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'conversation_duration': analysis.get('conversation_duration', 0),
            'main_topics': analysis.get('main_topics', []),
            'overall_sentiment': sentiment_analysis['sentiment'],
            'engagement_level': analysis.get('engagement_score', 0),
            'key_insights': self._extract_key_insights(messages),
            'action_items': self._extract_action_items(messages),
            'follow_up_needed': sentiment_analysis['sentiment'] == 'negative' or analysis.get('engagement_score', 0) > 0.8
        }
        
        return summary
    
    def _extract_key_insights(self, messages: List[Dict]) -> List[str]:
        """Extract key insights from conversation"""
        insights = []
        
        user_messages = [m.get('content', '') for m in messages if m.get('type') == 'user']
        bot_messages = [m.get('content', '') for m in messages if m.get('type') in ['bot', 'assistant']]
        
        # Look for health-related keywords
        health_keywords = ['weight', 'diet', 'exercise', 'nutrition', 'calories', 'protein', 'vitamins']
        mentioned_topics = []
        
        for msg in user_messages:
            for keyword in health_keywords:
                if keyword.lower() in msg.lower():
                    mentioned_topics.append(keyword)
        
        if mentioned_topics:
            insights.append(f"User discussed: {', '.join(set(mentioned_topics))}")
        
        # Check for questions asked
        questions = [msg for msg in user_messages if '?' in msg]
        if questions:
            insights.append(f"User asked {len(questions)} question(s)")
        
        return insights[:5]
    
    def _extract_action_items(self, messages: List[Dict]) -> List[str]:
        """Extract action items from conversation"""
        action_items = []
        
        # Look for action-oriented language in bot responses
        bot_messages = [m.get('content', '') for m in messages if m.get('type') in ['bot', 'assistant']]
        
        action_patterns = [
            r'try to ([^.]+)',
            r'you should ([^.]+)',
            r'consider ([^.]+)',
            r'start by ([^.]+)',
            r'make sure to ([^.]+)'
        ]
        
        for msg in bot_messages[-3:]:  # Check last 3 bot messages
            for pattern in action_patterns:
                matches = re.findall(pattern, msg.lower())
                action_items.extend([match.strip() for match in matches])
        
        return action_items[:5]

# Global instance
enhanced_ai_service = EnhancedAIService()