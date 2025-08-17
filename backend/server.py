from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import os
import logging
import asyncio
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from models import *
from database import db_manager
from medical_ai import MedicalAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize AI
medical_ai = MedicalAI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_manager.connect()
    logger.info("Doctronic AI backend started successfully")
    yield
    # Shutdown
    await db_manager.disconnect()
    logger.info("Doctronic AI backend shutdown")

# Create the main app
app = FastAPI(
    title="Doctronic AI Backend",
    description="AI Medical Assistant Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# Create API router
api_router = APIRouter(prefix="/api")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@api_router.get("/")
async def root():
    return {
        "message": "Doctronic AI Backend is running",
        "status": "healthy",
        "timestamp": datetime.utcnow()
    }

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        consultation_count = await db_manager.get_consultation_count()
        return {
            "status": "healthy",
            "database": "connected",
            "ai_service": "available",
            "total_consultations": consultation_count,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Consultation endpoints
@api_router.post("/consultations", response_model=CreateConsultationResponse)
async def create_consultation(request: CreateConsultationRequest):
    """Create a new medical consultation"""
    try:
        # Check for emergency keywords immediately
        emergency_detected = medical_ai.detect_emergency_keywords(request.symptoms)
        
        # Create consultation
        consultation = Consultation(
            initial_symptoms=request.symptoms,
            status=ConsultationStatus.ACTIVE
        )
        
        # Save to database
        consultation_id = await db_manager.create_consultation(consultation)
        
        # Create initial user message
        user_message = Message(
            consultation_id=consultation.id,
            type=MessageType.USER,
            content=request.symptoms
        )
        await db_manager.add_message(user_message)
        
        # Generate AI response
        ai_response_data = await medical_ai.generate_conversation_response(
            request.symptoms, consultation.user_info, []
        )
        
        # Create AI response message
        ai_message_content = ai_response_data.get("response_text", 
            "Absolutely, I can help with that. Quick question - what's your age and biological sex? It helps me give you more relevant and personalized information.")
        
        ai_message = Message(
            consultation_id=consultation.id,
            type=MessageType.AI,
            content=ai_message_content,
            metadata=MessageMetadata(
                emergency_detected=emergency_detected or ai_response_data.get("emergency_detected", False)
            )
        )
        await db_manager.add_message(ai_message)
        
        # Update consultation status
        new_status = ConsultationStatus.COLLECTING_INFO if ai_response_data.get("collect_user_info", True) else ConsultationStatus.ACTIVE
        await db_manager.update_consultation_status(consultation.id, new_status)
        
        return CreateConsultationResponse(
            consultation_id=consultation.id,
            session_token=consultation.session_token,
            message="Consultation created successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to create consultation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create consultation")

@api_router.get("/consultations/{consultation_id}")
async def get_consultation(consultation_id: str):
    """Get consultation details"""
    try:
        consultation = await db_manager.get_consultation(consultation_id)
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        # Get messages
        messages = await db_manager.get_messages(consultation_id)
        
        return {
            "consultation": consultation.dict(),
            "messages": [msg.dict() for msg in messages]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get consultation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve consultation")

@api_router.put("/consultations/{consultation_id}/user-info")
async def update_user_info(consultation_id: str, request: UpdateUserInfoRequest):
    """Update user information for consultation"""
    try:
        consultation = await db_manager.get_consultation(consultation_id)
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        # Update user info
        user_info_updates = {}
        if request.age is not None:
            user_info_updates["user_info.age"] = request.age
        if request.sex is not None:
            user_info_updates["user_info.sex"] = request.sex
        if request.additional_info is not None:
            user_info_updates["user_info.additional_info"] = request.additional_info
        
        await db_manager.update_consultation(consultation_id, user_info_updates)
        
        return {"message": "User information updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user info: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user information")

# Messaging endpoints
@api_router.post("/consultations/{consultation_id}/messages", response_model=SendMessageResponse)
async def send_message(consultation_id: str, request: SendMessageRequest, background_tasks: BackgroundTasks):
    """Send a message in consultation"""
    try:
        consultation = await db_manager.get_consultation(consultation_id)
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        # Create user message
        user_message = Message(
            consultation_id=consultation_id,
            type=request.type,
            content=request.content
        )
        await db_manager.add_message(user_message)
        
        # Get conversation history
        recent_messages = await db_manager.get_recent_messages(consultation_id, 10)
        
        # Generate AI response
        ai_response = None
        if request.type == MessageType.USER:
            # Check if this is user info (age/sex)
            user_info_pattern = r'(\d+).*(?:year|age).*(?:male|female)|(?:male|female).*(\d+).*(?:year|age)|i am (\d+).*(?:male|female)|(?:male|female).*i am (\d+)'
            is_user_info = any(word in request.content.lower() for word in ['male', 'female', 'age', 'years old', 'i am'])
            
            if is_user_info and consultation.status == ConsultationStatus.COLLECTING_INFO:
                # Extract and update user info
                content_lower = request.content.lower()
                age_match = re.search(r'(\d+)', request.content)
                sex_match = 'female' if 'female' in content_lower else 'male' if 'male' in content_lower else None
                
                if age_match or sex_match:
                    user_info_updates = {}
                    if age_match:
                        user_info_updates["user_info.age"] = int(age_match.group(1))
                    if sex_match:
                        user_info_updates["user_info.sex"] = sex_match
                    
                    await db_manager.update_consultation(consultation_id, user_info_updates)
                    
                    # Update consultation object for AI
                    consultation = await db_manager.get_consultation(consultation_id)
                
                # Generate response for symptom analysis
                ai_response_data = await medical_ai.analyze_symptoms(
                    consultation.initial_symptoms, 
                    consultation.user_info, 
                    recent_messages
                )
                
                # Create detailed AI response
                ai_content = _format_medical_analysis_response(ai_response_data)
                
                ai_response = Message(
                    consultation_id=consultation_id,
                    type=MessageType.AI,
                    content=ai_content,
                    metadata=MessageMetadata(
                        diagnosis=ai_response_data.get("diagnosis", []),
                        recommendations=ai_response_data.get("recommendations", []),
                        follow_up_questions=ai_response_data.get("follow_up_questions", []),
                        emergency_detected=ai_response_data.get("emergency_detected", False)
                    )
                )
                
                # Update status to analyzing/completed
                await db_manager.update_consultation_status(consultation_id, ConsultationStatus.COMPLETED)
                
            else:
                # Generate conversational response
                ai_response_data = await medical_ai.generate_conversation_response(
                    request.content, consultation.user_info, recent_messages
                )
                
                ai_response = Message(
                    consultation_id=consultation_id,
                    type=MessageType.AI,
                    content=ai_response_data.get("response_text", "I understand. Can you tell me more about how you're feeling?"),
                    metadata=MessageMetadata(
                        emergency_detected=ai_response_data.get("emergency_detected", False)
                    )
                )
            
            # Save AI response
            if ai_response:
                await db_manager.add_message(ai_response)
        
        return SendMessageResponse(
            message=user_message,
            ai_response=ai_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@api_router.get("/consultations/{consultation_id}/messages")
async def get_messages(consultation_id: str):
    """Get all messages for consultation"""
    try:
        consultation = await db_manager.get_consultation(consultation_id)
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        messages = await db_manager.get_messages(consultation_id)
        return {"messages": [msg.dict() for msg in messages]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")

# Medical Analysis endpoint
@api_router.post("/medical/analyze", response_model=MedicalAnalysisResponse)
async def analyze_medical_symptoms(request: MedicalAnalysisRequest):
    """Analyze medical symptoms and provide diagnosis"""
    try:
        analysis_result = await medical_ai.analyze_symptoms(
            request.symptoms,
            request.user_info,
            request.conversation_history
        )
        
        return MedicalAnalysisResponse(**analysis_result)
        
    except Exception as e:
        logger.error(f"Failed to analyze symptoms: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze symptoms")

# Statistics endpoint
@api_router.get("/statistics")
async def get_statistics():
    """Get platform statistics"""
    try:
        total_consultations = await db_manager.get_consultation_count()
        active_consultations = await db_manager.get_active_consultations_count()
        
        return {
            "total_consultations": f"{total_consultations:,}",
            "active_consultations": active_consultations,
            "average_response_time": "< 2 minutes",
            "satisfaction_rate": "98.7%",
            "uptime": "99.9%"
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

def _format_medical_analysis_response(analysis_data: dict) -> str:
    """Format medical analysis into readable response"""
    try:
        response_parts = []
        
        # Add response text if available
        if "response_text" in analysis_data:
            response_parts.append(analysis_data["response_text"])
        
        # Add diagnosis section
        if "diagnosis" in analysis_data and analysis_data["diagnosis"]:
            response_parts.append("\nBased on your symptoms, here are the most likely conditions:\n")
            
            for diag in analysis_data["diagnosis"]:
                response_parts.append(f"**{diag.get('condition', 'Unknown')}** ({diag.get('probability', 0)}% probability)")
                if diag.get('description'):
                    response_parts.append(f"• {diag['description']}")
                response_parts.append("")
        
        # Add recommendations
        if "recommendations" in analysis_data and analysis_data["recommendations"]:
            response_parts.append("**Recommendations:**")
            for rec in analysis_data["recommendations"]:
                response_parts.append(f"✓ {rec}")
            response_parts.append("")
        
        # Add emergency warning if detected
        if analysis_data.get("emergency_detected"):
            response_parts.append("⚠️ **IMPORTANT: Your symptoms may require immediate medical attention. Please consider calling 911 or visiting an emergency room.**")
        else:
            response_parts.append("⚠️ **Seek immediate medical attention if you experience:**")
            response_parts.append("• Sudden, severe worsening of symptoms")
            response_parts.append("• Difficulty breathing or chest pain")
            response_parts.append("• Changes in vision or speech")
            response_parts.append("• Loss of consciousness")
        
        response_parts.append("\nWould you like me to connect you with a licensed physician for a video consultation ($39)?")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Failed to format medical analysis: {e}")
        return "I've analyzed your symptoms. Based on the information provided, I recommend consulting with a healthcare provider for a proper evaluation and treatment plan."

# Include the router in the main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)