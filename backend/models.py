from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class MessageType(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"

class SexType(str, Enum):
    MALE = "male"
    FEMALE = "female"

class ConsultationStatus(str, Enum):
    ACTIVE = "active"
    COLLECTING_INFO = "collecting_info"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    REQUIRES_DOCTOR = "requires_doctor"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"

class UserInfo(BaseModel):
    age: Optional[int] = None
    sex: Optional[SexType] = None
    additional_info: Optional[Dict[str, Any]] = None

class Diagnosis(BaseModel):
    condition: str
    probability: int  # 0-100
    description: str
    symptoms: List[str]
    treatment_options: List[str]
    urgency_level: UrgencyLevel

class MessageMetadata(BaseModel):
    diagnosis: Optional[List[Diagnosis]] = None
    recommendations: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None
    user_info_collected: Optional[bool] = None
    emergency_detected: Optional[bool] = None

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consultation_id: str
    type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[MessageMetadata] = None

class Consultation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    initial_symptoms: str
    user_info: UserInfo = Field(default_factory=UserInfo)
    status: ConsultationStatus = ConsultationStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Message] = Field(default_factory=list)

# Request/Response Models
class CreateConsultationRequest(BaseModel):
    symptoms: str
    user_id: Optional[str] = None

class CreateConsultationResponse(BaseModel):
    consultation_id: str
    session_token: str
    message: str

class SendMessageRequest(BaseModel):
    content: str
    type: MessageType = MessageType.USER

class SendMessageResponse(BaseModel):
    message: Message
    ai_response: Optional[Message] = None

class UpdateUserInfoRequest(BaseModel):
    age: Optional[int] = None
    sex: Optional[SexType] = None
    additional_info: Optional[Dict[str, Any]] = None

class MedicalAnalysisRequest(BaseModel):
    symptoms: str
    user_info: UserInfo
    conversation_history: List[Message]

class MedicalAnalysisResponse(BaseModel):
    diagnosis: List[Diagnosis]
    recommendations: List[str]
    follow_up_questions: List[str]
    emergency_detected: bool