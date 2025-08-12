"""
Enhanced Chat Service Integration

This service integrates all enhanced chat capabilities:
- Multi-modal input processing (text, voice, images)
- Advanced conversation management
- Real-time analytics
- Smart response generation
- Context-aware suggestions
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from .enhanced_ai_service import enhanced_ai_service
from .conversation_manager import ConversationManager
import base64
import tempfile

logger = logging.getLogger(__name__)

class EnhancedChatService:
    """Main service orchestrating all enhanced chat features"""
    
    def __init__(self, db):
        self.db = db
        self.conversation_manager = ConversationManager(db)
        self.ai_service = enhanced_ai_service
        
        # Voice processing settings
        self.supported_audio_formats = ['wav', 'mp3', 'm4a', 'webm']
        self.max_audio_duration = 300  # 5 minutes
        
        # Image processing settings  
        self.supported_image_formats = ['jpg', 'jpeg', 'png', 'webp']
        self.max_image_size = 10 * 1024 * 1024  # 10MB
    
    async def process_message(self, session_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming message with enhanced capabilities"""
        
        try:
            # Extract message details
            message_type = message_data.get('type', 'text')
            content = message_data.get('content', '')
            user_context = message_data.get('user_context', {})
            
            # Get conversation context
            conversation_context = await self.conversation_manager.get_conversation_context(
                session_id, max_messages=15
            )
            
            # Process different message types
            processed_content = await self._process_message_content(message_data)
            
            # Add user message to conversation
            user_message = {
                'type': 'user',
                'content': processed_content['text'],
                'original_type': message_type,
                'metadata': processed_content.get('metadata', {}),
                'timestamp': datetime.utcnow()
            }
            
            await self.conversation_manager.add_message(session_id, user_message)
            
            # Generate enhanced AI response
            ai_response = await self.ai_service.generate_enhanced_response(
                message=processed_content['text'],
                history=conversation_context,
                user_context=user_context,
                conversation_analysis=None  # Will be calculated automatically
            )
            
            # Add AI response to conversation
            ai_message = {
                'type': 'assistant',
                'content': ai_response['response'],
                'structured_data': {
                    'title': ai_response.get('title'),
                    'summary': ai_response.get('summary'),
                    'key_points': ai_response.get('key_points', []),
                    'action_steps': ai_response.get('action_steps', []),
                    'tips': ai_response.get('tips', []),
                    'suggestions': ai_response.get('suggestions', []),
                    'quick_actions': ai_response.get('quick_actions', [])
                },
                'metadata': {
                    'model_used': ai_response.get('model_used'),
                    'confidence': ai_response.get('confidence', 0.85),
                    'processing_time': ai_response.get('processing_time'),
                    'sentiment_analysis': ai_response.get('sentiment_analysis'),
                    'intent_analysis': ai_response.get('intent_analysis')
                },
                'timestamp': datetime.utcnow()
            }
            
            await self.conversation_manager.add_message(session_id, ai_message)
            
            # Generate enhanced suggestions
            enhanced_suggestions = await self._generate_enhanced_suggestions(
                session_id, processed_content['text'], ai_response
            )
            
            # Prepare response
            response = {
                'session_id': session_id,
                'message_id': ai_message.get('message_id'),
                'response': ai_response['response'],
                'structured_data': ai_message['structured_data'],
                'suggestions': enhanced_suggestions['contextual_suggestions'],
                'quick_actions': enhanced_suggestions['quick_actions'],
                'conversation_insights': enhanced_suggestions['insights'],
                'metadata': ai_message['metadata']
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing enhanced message: {e}")
            return await self._generate_fallback_response(session_id, str(e))
    
    async def _process_message_content(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process different types of message content"""
        
        message_type = message_data.get('type', 'text')
        
        if message_type == 'text':
            return {
                'text': message_data.get('content', ''),
                'metadata': {}
            }
        
        elif message_type == 'voice':
            return await self._process_voice_message(message_data)
        
        elif message_type == 'image':
            return await self._process_image_message(message_data)
        
        elif message_type == 'multimodal':
            return await self._process_multimodal_message(message_data)
        
        else:
            return {
                'text': message_data.get('content', ''),
                'metadata': {'warning': f'Unsupported message type: {message_type}'}
            }
    
    async def _process_voice_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice message using speech-to-text"""
        
        try:
            # For now, return the text content if provided (Web Speech API handles STT on frontend)
            text = message_data.get('content', message_data.get('transcript', ''))
            
            metadata = {
                'original_type': 'voice',
                'confidence': message_data.get('confidence', 0.9),
                'language': message_data.get('language', 'en'),
                'duration': message_data.get('duration', 0)
            }
            
            # If no text provided, indicate processing needed
            if not text:
                text = "[Voice message - transcription needed]"
                metadata['needs_transcription'] = True
            
            return {
                'text': text,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            return {
                'text': "[Voice message - transcription failed]",
                'metadata': {'error': str(e)}
            }
    
    async def _process_image_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image message with visual analysis"""
        
        try:
            image_data = message_data.get('image_data')
            caption = message_data.get('caption', '')
            
            if not image_data:
                return {
                    'text': caption or "[Image message - no image data]",
                    'metadata': {'error': 'No image data provided'}
                }
            
            # Use existing Gemini vision for image analysis (from your current implementation)
            # This would integrate with your existing food recognition endpoint
            analysis_result = await self._analyze_image_with_gemini(image_data)
            
            # Combine caption and analysis
            text_content = []
            if caption:
                text_content.append(f"User caption: {caption}")
            
            if analysis_result.get('description'):
                text_content.append(f"Image analysis: {analysis_result['description']}")
            
            combined_text = '\n'.join(text_content) or "[Image processed]"
            
            return {
                'text': combined_text,
                'metadata': {
                    'original_type': 'image',
                    'analysis': analysis_result,
                    'has_caption': bool(caption)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing image message: {e}")
            return {
                'text': caption or "[Image processing failed]",
                'metadata': {'error': str(e)}
            }
    
    async def _process_multimodal_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with multiple content types"""
        
        try:
            text_parts = []
            metadata = {'original_type': 'multimodal', 'components': []}
            
            # Process text component
            if message_data.get('text'):
                text_parts.append(message_data['text'])
                metadata['components'].append('text')
            
            # Process voice component
            if message_data.get('voice'):
                voice_result = await self._process_voice_message({'content': message_data['voice']})
                text_parts.append(f"Voice: {voice_result['text']}")
                metadata['components'].append('voice')
                metadata['voice_metadata'] = voice_result['metadata']
            
            # Process image component
            if message_data.get('image'):
                image_result = await self._process_image_message({'image_data': message_data['image']})
                text_parts.append(f"Image: {image_result['text']}")
                metadata['components'].append('image')
                metadata['image_metadata'] = image_result['metadata']
            
            combined_text = '\n'.join(text_parts) or "[Multimodal message]"
            
            return {
                'text': combined_text,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing multimodal message: {e}")
            return {
                'text': message_data.get('text', '[Multimodal processing failed]'),
                'metadata': {'error': str(e)}
            }
    
    async def _analyze_image_with_gemini(self, image_data: str) -> Dict[str, Any]:
        """Analyze image using Gemini Vision (integrate with existing food recognition)"""
        
        try:
            # This would integrate with your existing food recognition service
            # For now, return a placeholder
            return {
                'description': 'Image analysis would be performed here using existing Gemini Vision integration',
                'confidence': 0.8,
                'detected_objects': [],
                'food_items': []
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                'description': 'Image analysis failed',
                'error': str(e)
            }
    
    async def _generate_enhanced_suggestions(self, session_id: str, user_message: str, 
                                           ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced contextual suggestions"""
        
        try:
            # Get conversation summary for context
            conversation_summary = await self.conversation_manager.get_conversation_summary(session_id)
            
            # Base suggestions from AI response
            base_suggestions = ai_response.get('suggestions', [])
            base_quick_actions = ai_response.get('quick_actions', [])
            
            # Generate contextual suggestions based on conversation history
            contextual_suggestions = await self._generate_contextual_suggestions(
                session_id, user_message, conversation_summary
            )
            
            # Generate insights about the conversation
            insights = await self._generate_conversation_insights(conversation_summary, ai_response)
            
            # Combine and deduplicate suggestions
            all_suggestions = list(set(base_suggestions + contextual_suggestions))[:5]
            
            # Enhanced quick actions
            enhanced_quick_actions = await self._generate_enhanced_quick_actions(
                base_quick_actions, conversation_summary
            )
            
            return {
                'contextual_suggestions': all_suggestions,
                'quick_actions': enhanced_quick_actions,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced suggestions: {e}")
            return {
                'contextual_suggestions': ai_response.get('suggestions', []),
                'quick_actions': ai_response.get('quick_actions', []),
                'insights': {}
            }
    
    async def _generate_contextual_suggestions(self, session_id: str, current_message: str,
                                             conversation_summary: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on conversation context"""
        
        suggestions = []
        topics = conversation_summary.get('topics_discussed', [])
        
        # Topic-based suggestions
        if 'nutrition' in topics and 'exercise' not in topics:
            suggestions.append("How does exercise complement my nutrition plan?")
        
        if 'weight' in topics:
            suggestions.append("What's a healthy rate of weight change?")
        
        if 'diet' in topics and len(topics) > 2:
            suggestions.append("Can you create a personalized meal plan?")
        
        # Engagement-based suggestions
        engagement = conversation_summary.get('engagement_score', 0)
        if engagement > 0.7:
            suggestions.append("What should I track daily for best results?")
        elif engagement < 0.3:
            suggestions.append("What's one simple change I can make today?")
        
        # Time-based suggestions
        hour = datetime.now().hour
        if 6 <= hour <= 10:
            suggestions.append("What's a quick healthy breakfast idea?")
        elif 11 <= hour <= 14:
            suggestions.append("Healthy lunch options for energy?")
        elif 17 <= hour <= 20:
            suggestions.append("Light dinner ideas for tonight?")
        
        return suggestions[:3]
    
    async def _generate_enhanced_quick_actions(self, base_actions: List[Dict], 
                                             conversation_summary: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate enhanced quick actions with context"""
        
        enhanced_actions = list(base_actions) if base_actions else []
        
        # Add context-aware actions
        topics = conversation_summary.get('topics_discussed', [])
        
        if 'weight' in topics:
            enhanced_actions.append({
                'label': '📊 Track Progress',
                'action': 'track_progress',
                'description': 'Set up progress tracking'
            })
        
        if 'nutrition' in topics:
            enhanced_actions.append({
                'label': '🍽️ Meal Ideas',
                'action': 'meal_suggestions',
                'description': 'Get personalized meal suggestions'
            })
        
        if conversation_summary.get('engagement_score', 0) > 0.5:
            enhanced_actions.append({
                'label': '🎯 Set Goals',
                'action': 'goal_setting',
                'description': 'Define your health goals'
            })
        
        # Limit to 3 actions to avoid overwhelming
        return enhanced_actions[:3]
    
    async def _generate_conversation_insights(self, conversation_summary: Dict[str, Any],
                                            ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights about the current conversation"""
        
        insights = {}
        
        # Conversation quality
        engagement = conversation_summary.get('engagement_score', 0)
        if engagement > 0.7:
            insights['engagement'] = 'high'
            insights['engagement_note'] = 'Great conversation flow! Keep exploring your interests.'
        elif engagement > 0.4:
            insights['engagement'] = 'medium'
            insights['engagement_note'] = 'Good interaction. Feel free to ask more detailed questions.'
        else:
            insights['engagement'] = 'low'
            insights['engagement_note'] = 'I\'m here to help! Try asking specific questions about your health goals.'
        
        # Topic coverage
        topics_count = len(conversation_summary.get('topics_discussed', []))
        if topics_count > 5:
            insights['topic_diversity'] = 'high'
            insights['topic_note'] = 'We\'ve covered many areas. Would you like to focus on one topic?'
        elif topics_count > 2:
            insights['topic_diversity'] = 'medium'
            insights['topic_note'] = 'Good topic exploration. Let\'s dive deeper into what interests you most.'
        else:
            insights['topic_diversity'] = 'low'
            insights['topic_note'] = 'Feel free to explore different health and nutrition topics.'
        
        # Sentiment trend
        sentiment_analysis = ai_response.get('sentiment_analysis', {})
        if sentiment_analysis.get('sentiment') == 'positive':
            insights['mood'] = 'positive'
            insights['mood_note'] = 'You seem engaged and positive about your health journey!'
        elif sentiment_analysis.get('sentiment') == 'negative':
            insights['mood'] = 'needs_support'
            insights['mood_note'] = 'I\'m here to support you. Remember, small steps lead to big changes.'
        
        return insights
    
    async def _generate_fallback_response(self, session_id: str, error_message: str) -> Dict[str, Any]:
        """Generate fallback response when processing fails"""
        
        fallback_responses = [
            "I'm here to help with your health and nutrition questions. What would you like to explore?",
            "I can assist you with meal planning, nutrition advice, and healthy lifestyle tips. How can I support you today?",
            "Let's focus on your health goals. What specific area would you like guidance on?"
        ]
        
        import random
        response_text = random.choice(fallback_responses)
        
        return {
            'session_id': session_id,
            'response': response_text,
            'structured_data': {
                'title': 'How can I help you?',
                'summary': response_text,
                'key_points': ['I\'m here to support your health journey', 'Ask specific questions for better guidance'],
                'action_steps': ['Share your health goals', 'Ask about nutrition or meal planning'],
                'tips': ['Be specific in your questions', 'I can help with dietary advice']
            },
            'suggestions': ['What\'s a healthy breakfast?', 'Help with meal planning', 'Nutrition for my goals'],
            'quick_actions': [
                {'label': '🍽️ Meal Planning', 'action': 'meal_planning'},
                {'label': '🎯 Health Goals', 'action': 'goal_setting'}
            ],
            'conversation_insights': {
                'status': 'recovery',
                'note': 'Encountered a technical issue, but I\'m ready to help!'
            },
            'metadata': {
                'model_used': 'fallback',
                'confidence': 0.7,
                'error_recovery': True
            }
        }
    
    async def get_conversation_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get detailed conversation analytics"""
        
        try:
            # Get conversation summary
            summary = await self.conversation_manager.get_conversation_summary(session_id)
            
            # Get full conversation for detailed analysis
            conversation = await self.conversation_manager.get_conversation(session_id)
            
            if not conversation:
                return {'error': 'Conversation not found'}
            
            # Generate comprehensive analytics
            analytics = {
                'session_id': session_id,
                'summary': summary,
                'message_analysis': await self._analyze_message_patterns(conversation['messages']),
                'engagement_metrics': await self._calculate_engagement_metrics(conversation['messages']),
                'topic_analysis': await self._analyze_conversation_topics(conversation['messages']),
                'sentiment_journey': await self._track_sentiment_journey(conversation['messages']),
                'recommendations': await self._generate_conversation_recommendations(summary)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating conversation analytics: {e}")
            return {'error': str(e)}
    
    async def _analyze_message_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in message exchange"""
        
        if not messages:
            return {}
        
        user_messages = [m for m in messages if m.get('type') == 'user']
        bot_messages = [m for m in messages if m.get('type') in ['bot', 'assistant']]
        
        # Calculate patterns
        avg_user_length = sum(len(m.get('content', '').split()) for m in user_messages) / len(user_messages) if user_messages else 0
        avg_bot_length = sum(len(m.get('content', '').split()) for m in bot_messages) / len(bot_messages) if bot_messages else 0
        
        # Response time analysis (simplified)
        response_times = []
        for i in range(1, len(messages)):
            if messages[i-1].get('type') == 'user' and messages[i].get('type') in ['bot', 'assistant']:
                # In a real implementation, you'd calculate actual response times
                response_times.append(2.5)  # Placeholder
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'total_exchanges': len(user_messages),
            'avg_user_message_length': round(avg_user_length, 1),
            'avg_bot_message_length': round(avg_bot_length, 1),
            'avg_response_time_seconds': round(avg_response_time, 1),
            'question_count': sum(1 for m in user_messages if '?' in m.get('content', '')),
            'conversation_balance': 'user_heavy' if len(user_messages) > len(bot_messages) * 1.2 else 'balanced'
        }
    
    async def _calculate_engagement_metrics(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detailed engagement metrics"""
        
        if not messages:
            return {'engagement_score': 0}
        
        user_messages = [m for m in messages if m.get('type') == 'user']
        
        # Engagement factors
        factors = []
        
        # Message frequency
        if len(messages) > 1:
            duration = (messages[-1]['timestamp'] - messages[0]['timestamp']).total_seconds() / 60  # minutes
            message_frequency = len(user_messages) / max(duration, 1)
            factors.append(min(message_frequency / 2, 1.0))  # Normalize
        
        # Question engagement
        questions = sum(1 for m in user_messages if '?' in m.get('content', ''))
        question_ratio = questions / len(user_messages) if user_messages else 0
        factors.append(min(question_ratio * 2, 1.0))
        
        # Message length engagement
        avg_length = sum(len(m.get('content', '').split()) for m in user_messages) / len(user_messages) if user_messages else 0
        length_score = min(avg_length / 20, 1.0)  # 20 words as optimal
        factors.append(length_score)
        
        overall_score = sum(factors) / len(factors) if factors else 0
        
        return {
            'engagement_score': round(overall_score, 3),
            'message_frequency': round(factors[0] if factors else 0, 3),
            'question_engagement': round(factors[1] if len(factors) > 1 else 0, 3),
            'message_depth': round(factors[2] if len(factors) > 2 else 0, 3),
            'overall_rating': 'high' if overall_score > 0.7 else 'medium' if overall_score > 0.4 else 'low'
        }
    
    async def _analyze_conversation_topics(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze topics discussed in conversation"""
        
        user_messages = [m for m in messages if m.get('type') == 'user']
        all_text = ' '.join([m.get('content', '') for m in user_messages]).lower()
        
        # Health and nutrition topic categories
        topic_categories = {
            'nutrition': ['nutrition', 'nutrients', 'vitamin', 'mineral', 'protein', 'carbs', 'fat'],
            'weight_management': ['weight', 'lose', 'gain', 'scale', 'pounds', 'kg'],
            'meal_planning': ['meal', 'breakfast', 'lunch', 'dinner', 'snack', 'recipe'],
            'exercise': ['exercise', 'workout', 'fitness', 'gym', 'running', 'walking'],
            'health_conditions': ['diabetes', 'heart', 'blood pressure', 'cholesterol', 'condition'],
            'dietary_restrictions': ['vegetarian', 'vegan', 'gluten', 'dairy', 'allergy', 'intolerance']
        }
        
        topic_scores = {}
        for category, keywords in topic_categories.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > 0:
                topic_scores[category] = score
        
        # Sort by relevance
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'primary_topics': sorted_topics[:3],
            'topic_diversity': len(topic_scores),
            'focus_area': sorted_topics[0][0] if sorted_topics else 'general',
            'topic_coverage': list(topic_scores.keys())
        }
    
    async def _track_sentiment_journey(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Track sentiment changes throughout conversation"""
        
        user_messages = [m for m in messages if m.get('type') == 'user']
        sentiment_timeline = []
        
        for i, message in enumerate(user_messages):
            # Simple sentiment analysis (in real implementation, use the analyzer)
            content = message.get('content', '').lower()
            
            positive_words = ['good', 'great', 'thanks', 'helpful', 'love', 'perfect', 'awesome']
            negative_words = ['bad', 'wrong', 'problem', 'difficult', 'hard', 'frustrated', 'confused']
            
            positive_count = sum(1 for word in positive_words if word in content)
            negative_count = sum(1 for word in negative_words if word in content)
            
            if positive_count > negative_count:
                sentiment = 'positive'
                score = min(positive_count / len(content.split()), 1.0)
            elif negative_count > positive_count:
                sentiment = 'negative'
                score = min(negative_count / len(content.split()), 1.0)
            else:
                sentiment = 'neutral'
                score = 0.5
            
            sentiment_timeline.append({
                'message_index': i,
                'sentiment': sentiment,
                'score': score,
                'timestamp': message.get('timestamp', datetime.utcnow())
            })
        
        # Analyze trend
        if len(sentiment_timeline) >= 3:
            recent_scores = [s['score'] for s in sentiment_timeline[-3:]]
            if all(recent_scores[i] >= recent_scores[i-1] for i in range(1, len(recent_scores))):
                trend = 'improving'
            elif all(recent_scores[i] <= recent_scores[i-1] for i in range(1, len(recent_scores))):
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'sentiment_timeline': sentiment_timeline,
            'overall_trend': trend,
            'current_sentiment': sentiment_timeline[-1]['sentiment'] if sentiment_timeline else 'neutral',
            'average_sentiment_score': sum(s['score'] for s in sentiment_timeline) / len(sentiment_timeline) if sentiment_timeline else 0.5
        }
    
    async def _generate_conversation_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving conversation"""
        
        recommendations = []
        
        engagement = summary.get('engagement_score', 0)
        if engagement < 0.4:
            recommendations.append("Try asking more specific questions about your health goals")
            recommendations.append("Share details about your current diet or exercise routine")
        
        if engagement > 0.8:
            recommendations.append("Great engagement! Consider exploring advanced topics")
            recommendations.append("You might benefit from setting specific, measurable goals")
        
        topics_count = len(summary.get('topics_discussed', []))
        if topics_count < 2:
            recommendations.append("Try exploring different aspects of health and nutrition")
        elif topics_count > 6:
            recommendations.append("Consider focusing on 1-2 key areas for better results")
        
        # Duration-based recommendations
        duration = summary.get('duration_hours', 0)
        if duration > 1:
            recommendations.append("Long conversation! Consider saving key insights")
            recommendations.append("Take breaks to implement discussed strategies")
        
        return recommendations[:4]  # Limit to 4 recommendations

# Global instance
enhanced_chat_service = None

def get_enhanced_chat_service(db):
    """Get global enhanced chat service instance"""
    global enhanced_chat_service
    if enhanced_chat_service is None:
        enhanced_chat_service = EnhancedChatService(db)
    return enhanced_chat_service