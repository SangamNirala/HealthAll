"""
Advanced Conversation Management System

This service provides:
- Conversation threading and branching
- Smart context management
- Conversation analytics and insights
- Session management with persistence
- Conversation search and filtering
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import hashlib
from collections import defaultdict

logger = logging.getLogger(__name__)

class ConversationThread:
    """Represents a conversation thread with branching capabilities"""
    
    def __init__(self, thread_id: str, parent_message_id: str = None):
        self.thread_id = thread_id
        self.parent_message_id = parent_message_id
        self.messages = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata = {}
    
    def add_message(self, message: Dict[str, Any]):
        """Add message to thread"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thread to dictionary"""
        return {
            'thread_id': self.thread_id,
            'parent_message_id': self.parent_message_id,
            'messages': self.messages,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }

class ConversationManager:
    """Advanced conversation management with threading and analytics"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.conversations_collection = db.enhanced_conversations
        self.analytics_collection = db.conversation_analytics
        
        # Conversation settings
        self.max_context_messages = 20
        self.context_decay_factor = 0.1  # How much older messages matter less
        
    async def create_conversation(self, session_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create new conversation with enhanced features"""
        
        conversation = {
            'session_id': session_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'user_context': user_context,
            'threads': {},  # Thread ID -> Thread data
            'main_thread': None,
            'analytics': {
                'total_messages': 0,
                'user_messages': 0,
                'bot_messages': 0,
                'avg_response_time': 0,
                'sentiment_history': [],
                'topics_discussed': [],
                'engagement_score': 0
            },
            'tags': [],
            'status': 'active',
            'context_summary': {},
            'preferences': {
                'response_style': 'balanced',
                'verbosity': 'medium',
                'personality': 'friendly'
            }
        }
        
        # Create main thread
        main_thread = ConversationThread(f"{session_id}_main")
        conversation['threads'][main_thread.thread_id] = main_thread.to_dict()
        conversation['main_thread'] = main_thread.thread_id
        
        await self.conversations_collection.insert_one(conversation)
        return conversation
    
    async def add_message(self, session_id: str, message: Dict[str, Any], 
                         thread_id: str = None, create_branch: bool = False) -> Dict[str, Any]:
        """Add message to conversation with threading support"""
        
        conversation = await self.conversations_collection.find_one({'session_id': session_id})
        if not conversation:
            # Create conversation if it doesn't exist
            conversation = await self.create_conversation(session_id, {})
        
        # Determine target thread
        if thread_id is None:
            thread_id = conversation['main_thread']
        
        # Create new branch if requested
        if create_branch:
            branch_id = f"{session_id}_branch_{datetime.utcnow().timestamp()}"
            new_thread = ConversationThread(branch_id, thread_id)
            conversation['threads'][branch_id] = new_thread.to_dict()
            thread_id = branch_id
        
        # Add message to thread
        enhanced_message = {
            **message,
            'message_id': f"{session_id}_{datetime.utcnow().timestamp()}",
            'thread_id': thread_id,
            'timestamp': datetime.utcnow(),
            'sequence_number': len(conversation['threads'][thread_id]['messages'])
        }
        
        conversation['threads'][thread_id]['messages'].append(enhanced_message)
        conversation['threads'][thread_id]['updated_at'] = datetime.utcnow()
        
        # Update analytics
        await self._update_conversation_analytics(conversation, enhanced_message)
        
        # Update conversation
        conversation['updated_at'] = datetime.utcnow()
        await self.conversations_collection.replace_one(
            {'session_id': session_id}, 
            conversation
        )
        
        return enhanced_message
    
    async def get_conversation(self, session_id: str, thread_id: str = None) -> Dict[str, Any]:
        """Get conversation with specified thread"""
        
        conversation = await self.conversations_collection.find_one({'session_id': session_id})
        if not conversation:
            return None
        
        if thread_id is None:
            thread_id = conversation['main_thread']
        
        return {
            'session_id': session_id,
            'thread_id': thread_id,
            'messages': conversation['threads'][thread_id]['messages'],
            'analytics': conversation['analytics'],
            'context_summary': conversation.get('context_summary', {}),
            'preferences': conversation.get('preferences', {}),
            'created_at': conversation['created_at'],
            'updated_at': conversation['updated_at']
        }
    
    async def get_conversation_context(self, session_id: str, thread_id: str = None, 
                                     max_messages: int = None) -> List[Dict[str, Any]]:
        """Get conversation context with smart filtering"""
        
        conversation = await self.get_conversation(session_id, thread_id)
        if not conversation:
            return []
        
        messages = conversation['messages']
        if not messages:
            return []
        
        max_messages = max_messages or self.max_context_messages
        
        # Apply smart context filtering
        if len(messages) <= max_messages:
            return messages
        
        # Keep most recent messages and important earlier messages
        recent_messages = messages[-max_messages//2:]
        older_messages = messages[:-max_messages//2]
        
        # Score older messages for importance
        important_messages = self._score_message_importance(older_messages)
        selected_older = important_messages[:max_messages//2]
        
        # Combine and sort by timestamp
        context_messages = selected_older + recent_messages
        context_messages.sort(key=lambda x: x.get('timestamp', datetime.min))
        
        return context_messages
    
    def _score_message_importance(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score messages for importance in context"""
        
        scored_messages = []
        
        for msg in messages:
            score = 0
            content = msg.get('content', '').lower()
            
            # User questions are important
            if msg.get('type') == 'user' and '?' in content:
                score += 10
            
            # Messages mentioning health goals
            if any(keyword in content for keyword in ['goal', 'weight', 'diet', 'health']):
                score += 8
            
            # Messages with structured AI responses
            if msg.get('type') in ['bot', 'assistant'] and msg.get('structured'):
                score += 6
            
            # Messages with user personal information
            if any(keyword in content for keyword in ['i am', 'my', 'me', 'myself']):
                score += 5
            
            # Longer messages might be more informative
            score += min(len(content.split()) / 10, 3)
            
            scored_messages.append((score, msg))
        
        # Sort by score and return messages
        scored_messages.sort(key=lambda x: x[0], reverse=True)
        return [msg for score, msg in scored_messages]
    
    async def _update_conversation_analytics(self, conversation: Dict[str, Any], 
                                           new_message: Dict[str, Any]):
        """Update conversation analytics"""
        
        analytics = conversation['analytics']
        
        # Update message counts
        analytics['total_messages'] += 1
        if new_message.get('type') == 'user':
            analytics['user_messages'] += 1
        else:
            analytics['bot_messages'] += 1
        
        # Update sentiment history if available
        if 'sentiment_analysis' in new_message:
            sentiment = new_message['sentiment_analysis']
            analytics['sentiment_history'].append({
                'timestamp': new_message['timestamp'],
                'sentiment': sentiment.get('sentiment'),
                'score': sentiment.get('sentiment_score', 0)
            })
            
            # Keep only last 50 sentiment entries
            analytics['sentiment_history'] = analytics['sentiment_history'][-50:]
        
        # Extract and update topics
        if new_message.get('type') == 'user':
            content = new_message.get('content', '').lower()
            health_topics = ['nutrition', 'diet', 'exercise', 'weight', 'calories', 'protein', 'vitamins', 'health']
            
            for topic in health_topics:
                if topic in content and topic not in analytics['topics_discussed']:
                    analytics['topics_discussed'].append(topic)
        
        # Calculate engagement score
        if analytics['user_messages'] > 0:
            question_ratio = len([s for s in analytics['sentiment_history'] if '?' in str(s)]) / analytics['user_messages']
            message_frequency = analytics['total_messages'] / max((datetime.utcnow() - conversation['created_at']).total_seconds() / 3600, 1)  # messages per hour
            
            analytics['engagement_score'] = min((question_ratio * 0.4 + message_frequency * 0.6), 1.0)
    
    async def search_conversations(self, user_id: str = None, query: str = None, 
                                 tags: List[str] = None, date_range: Dict = None) -> List[Dict[str, Any]]:
        """Search conversations with advanced filtering"""
        
        filter_criteria = {}
        
        if user_id:
            filter_criteria['user_context.user_id'] = user_id
        
        if tags:
            filter_criteria['tags'] = {'$in': tags}
        
        if date_range:
            date_filter = {}
            if date_range.get('start'):
                date_filter['$gte'] = date_range['start']
            if date_range.get('end'):
                date_filter['$lte'] = date_range['end']
            if date_filter:
                filter_criteria['created_at'] = date_filter
        
        # Text search if query provided
        if query:
            filter_criteria['$text'] = {'$search': query}
        
        conversations = await self.conversations_collection.find(
            filter_criteria
        ).sort('updated_at', -1).limit(50).to_list(length=50)
        
        return conversations
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive conversation summary"""
        
        conversation = await self.conversations_collection.find_one({'session_id': session_id})
        if not conversation:
            return {}
        
        analytics = conversation['analytics']
        
        # Calculate conversation metrics
        duration = (conversation['updated_at'] - conversation['created_at']).total_seconds() / 3600  # hours
        
        # Sentiment trend
        sentiment_history = analytics.get('sentiment_history', [])
        sentiment_trend = 'stable'
        if len(sentiment_history) >= 3:
            recent_sentiment = [s['score'] for s in sentiment_history[-3:]]
            if all(recent_sentiment[i] > recent_sentiment[i-1] for i in range(1, len(recent_sentiment))):
                sentiment_trend = 'improving'
            elif all(recent_sentiment[i] < recent_sentiment[i-1] for i in range(1, len(recent_sentiment))):
                sentiment_trend = 'declining'
        
        summary = {
            'session_id': session_id,
            'total_messages': analytics['total_messages'],
            'duration_hours': round(duration, 2),
            'topics_discussed': analytics['topics_discussed'],
            'engagement_score': analytics['engagement_score'],
            'sentiment_trend': sentiment_trend,
            'last_activity': conversation['updated_at'],
            'thread_count': len(conversation['threads']),
            'status': conversation['status'],
            'key_insights': await self._generate_conversation_insights(conversation)
        }
        
        return summary
    
    async def _generate_conversation_insights(self, conversation: Dict[str, Any]) -> List[str]:
        """Generate insights about the conversation"""
        
        insights = []
        analytics = conversation['analytics']
        
        # Engagement insights
        if analytics['engagement_score'] > 0.7:
            insights.append("High engagement - user is actively participating")
        elif analytics['engagement_score'] < 0.3:
            insights.append("Low engagement - consider different approach")
        
        # Topic insights
        topics = analytics['topics_discussed']
        if len(topics) > 5:
            insights.append(f"Diverse discussion covering {len(topics)} health topics")
        elif len(topics) == 1:
            insights.append(f"Focused discussion on {topics[0]}")
        
        # Sentiment insights
        sentiment_history = analytics.get('sentiment_history', [])
        if sentiment_history:
            recent_sentiments = [s['sentiment'] for s in sentiment_history[-5:]]
            if recent_sentiments.count('positive') > recent_sentiments.count('negative'):
                insights.append("Generally positive conversation tone")
            elif recent_sentiments.count('negative') > recent_sentiments.count('positive'):
                insights.append("User may need additional support")
        
        # Message pattern insights
        if analytics['user_messages'] > analytics['bot_messages'] * 1.5:
            insights.append("User is very talkative - good for information gathering")
        elif analytics['bot_messages'] > analytics['user_messages'] * 1.5:
            insights.append("AI is providing detailed guidance - educational session")
        
        return insights[:5]  # Return top 5 insights
    
    async def update_conversation_preferences(self, session_id: str, preferences: Dict[str, Any]):
        """Update conversation preferences"""
        
        await self.conversations_collection.update_one(
            {'session_id': session_id},
            {
                '$set': {
                    'preferences': preferences,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    async def tag_conversation(self, session_id: str, tags: List[str]):
        """Add tags to conversation"""
        
        await self.conversations_collection.update_one(
            {'session_id': session_id},
            {
                '$addToSet': {'tags': {'$each': tags}},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
    
    async def archive_conversation(self, session_id: str):
        """Archive a conversation"""
        
        await self.conversations_collection.update_one(
            {'session_id': session_id},
            {
                '$set': {
                    'status': 'archived',
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    async def get_conversation_analytics(self, user_id: str = None, date_range: Dict = None) -> Dict[str, Any]:
        """Get aggregated conversation analytics"""
        
        # Build aggregation pipeline
        pipeline = []
        
        # Match stage
        match_criteria = {'status': {'$ne': 'archived'}}
        if user_id:
            match_criteria['user_context.user_id'] = user_id
        if date_range:
            date_filter = {}
            if date_range.get('start'):
                date_filter['$gte'] = date_range['start']
            if date_range.get('end'):
                date_filter['$lte'] = date_range['end']
            if date_filter:
                match_criteria['created_at'] = date_filter
        
        pipeline.append({'$match': match_criteria})
        
        # Group and aggregate
        pipeline.append({
            '$group': {
                '_id': None,
                'total_conversations': {'$sum': 1},
                'total_messages': {'$sum': '$analytics.total_messages'},
                'avg_engagement': {'$avg': '$analytics.engagement_score'},
                'all_topics': {'$push': '$analytics.topics_discussed'}
            }
        })
        
        result = await self.conversations_collection.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'avg_engagement': 0,
                'top_topics': []
            }
        
        data = result[0]
        
        # Process topics
        all_topics = []
        for topic_list in data.get('all_topics', []):
            all_topics.extend(topic_list)
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_conversations': data['total_conversations'],
            'total_messages': data['total_messages'],
            'avg_engagement': round(data['avg_engagement'], 3),
            'top_topics': top_topics
        }