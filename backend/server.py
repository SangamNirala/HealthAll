from fastapi import FastAPI, APIRouter, HTTPException, Body, File, UploadFile, Form, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum
import json
import requests
import base64
import random
import httpx

# Import AI services
from ai_services import get_nutrition_insights, get_smart_food_suggestions, get_health_correlations, get_clinical_insights, get_goal_insights, get_achievement_insights, AIServiceManager

# Import Supabase
from supabase import create_client, Client


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')
STORAGE_BUCKET = os.environ.get('STORAGE_BUCKET', 'symptom-files')

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

# ... many other route and model definitions above ...

# Enhanced Chat API Models
class EnhancedChatMessageRequest(BaseModel):
    session_id: str
    content: str
    type: str = "text"  # text, voice, image, multimodal
    user_context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class EnhancedChatResponse(BaseModel):
    session_id: str
    message_id: str = None
    response: str
    structured_data: Dict[str, Any] = {}
    suggestions: List[str] = []
    quick_actions: List[Dict[str, str]] = []
    conversation_insights: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

# Chat API Models
class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    context_type: str = "health_and_nutrition"
    user_context: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    response: str
    session_id: str
    suggestions: List[str] = []
    quick_actions: List[Dict[str, Any]] = []
    confidence: float = 0.8
    # Structured formatting fields for better UX (optional)
    title: Optional[str] = None
    summary: Optional[str] = None
    key_points: List[str] = []
    action_steps: List[str] = []
    tips: List[str] = []
    sources: List[str] = []

# Chat API Endpoints
@api_router.post("/chat/send-message")
async def send_chat_message(request: ChatMessageRequest):
    """Send message to AI chat assistant for food and health queries"""
    try:
        # Store chat session in database
        chat_session = await db.chat_sessions.find_one({"session_id": request.session_id})
        
        if not chat_session:
            # Create new session
            chat_session = {
                "session_id": request.session_id,
                "created_at": datetime.utcnow(),
                "messages": [],
                "context_type": request.context_type
            }
            await db.chat_sessions.insert_one(chat_session)
        
        # Add user message to history
        user_message = {
            "type": "user",
            "content": request.message,
            "timestamp": datetime.utcnow()
        }
        
        await db.chat_sessions.update_one(
            {"session_id": request.session_id},
            {"$push": {"messages": user_message}}
        )
        
        # Get recent message history for context
        # Reload to get updated history including just-pushed message
        refreshed_session = await db.chat_sessions.find_one({"session_id": request.session_id})
        recent_messages = (refreshed_session or {}).get("messages", [])[-10:]
        
        # Use AI Service Manager to generate a structured response with enhanced context awareness
        ai_service = AIServiceManager()
        
        # Build user context from request and stored data
        user_context = request.user_context.copy() if request.user_context else {}
        user_context.update({
            "session_id": request.session_id,
            "interaction_count": len(recent_messages) // 2,  # Approximate user message count
            "context_type": request.context_type
        })
        
        structured = await ai_service.generate_chat_response(
            message=request.message,
            history=recent_messages,
            context_type=request.context_type,
            user_context=user_context
        )

        # Build plain text response for backward compatibility
        plain_text = structured.get("summary") or structured.get("title") or "Here are some suggestions for you."

        # Build suggestions and quick actions
        suggestions = structured.get("suggestions", [])[:3]
        quick_actions = structured.get("quick_actions", [])[:2]

        # Store AI response with structure
        ai_message = {
            "type": "assistant",
            "content": plain_text,
            "timestamp": datetime.utcnow(),
            "suggestions": suggestions,
            "quick_actions": quick_actions,
            "structured": {
                "title": structured.get("title"),
                "summary": structured.get("summary"),
                "key_points": structured.get("key_points", []),
                "action_steps": structured.get("action_steps", []),
                "tips": structured.get("tips", []),
                "sources": structured.get("sources", []),
                "provider": structured.get("provider"),
                "model": structured.get("model"),
                "confidence": structured.get("confidence"),
            }
        }
        
        await db.chat_sessions.update_one(
            {"session_id": request.session_id},
            {"$push": {"messages": ai_message}}
        )

        return ChatResponse(
            response=plain_text,
            session_id=request.session_id,
            suggestions=suggestions,
            quick_actions=quick_actions,
            confidence=float(structured.get("confidence", 0.85)),
            title=structured.get("title"),
            summary=structured.get("summary"),
            key_points=structured.get("key_points", []),
            action_steps=structured.get("action_steps", []),
            tips=structured.get("tips", []),
            sources=structured.get("sources", []),
        )

    except Exception as e:
        logging.getLogger(__name__).error(f"Chat error: {str(e)}")
        # Return a helpful fallback response
        fallback_responses = [
            "I'm here to help with your nutrition and health questions! Could you tell me more about what you'd like to know?",
            "I can assist you with food recommendations, nutrition advice, and health tips. What specific topic interests you?",
            "Feel free to ask me about healthy eating, meal planning, or any nutrition-related questions you have!"
        ]
        
        import random as _random
        fallback_response = _random.choice(fallback_responses)
        
        return ChatResponse(
            response=fallback_response,
            session_id=request.session_id,
            suggestions=["What's a healthy breakfast?", "How do I eat more vegetables?", "Tell me about portion control"],
            quick_actions=[],
            confidence=0.5
        )

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        chat_session = await db.chat_sessions.find_one({"session_id": session_id})
        
        if not chat_session:
            return {"messages": [], "session_id": session_id}
        
        return {
            "messages": chat_session.get("messages", []),
            "session_id": session_id,
            "created_at": chat_session.get("created_at"),
            "context_type": chat_session.get("context_type", "health_and_nutrition")
        }
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@api_router.post("/chat/start-session")
async def start_chat_session():
    """Start a new chat session"""
    try:
        session_id = f"chat_{int(datetime.utcnow().timestamp())}_{random.randint(1000, 9999)}"
        
        chat_session = {
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "messages": [],
            "context_type": "health_and_nutrition"
        }
        
        await db.chat_sessions.insert_one(chat_session)
        
        return {
            "session_id": session_id,
            "message": "Chat session started successfully",
            "welcome_message": "Hi! I'm your AI nutrition assistant. I can help you with food questions, health tips, and recommendations. What would you like to know?"
        }
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error starting chat session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start chat session: {str(e)}")

# Include the router in the main app (after all endpoints are defined)
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable CORS (if not already configured elsewhere)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)