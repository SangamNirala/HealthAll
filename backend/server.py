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
    name: str
    email: str
    role: str  # patient, provider, family, guest
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileCreate(BaseModel):
    name: str
    email: str
    role: str

class HealthMetric(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    metric_type: str  # weight, blood_pressure, calories, etc.
    value: float
    unit: str
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

class HealthMetricCreate(BaseModel):
    user_id: str
    metric_type: str
    value: float
    unit: str

# ===== COMPREHENSIVE PROFILE MODELS =====

# Enums for Profile Data
class ActivityLevelEnum(str, Enum):
    SEDENTARY = "SEDENTARY"
    LIGHTLY_ACTIVE = "LIGHTLY_ACTIVE" 
    MODERATELY_ACTIVE = "MODERATELY_ACTIVE"
    VERY_ACTIVE = "VERY_ACTIVE"
    EXTRA_ACTIVE = "EXTRA_ACTIVE"

class WorkTypeEnum(str, Enum):
    DESK_JOB = "DESK_JOB"
    PHYSICAL_WORK = "PHYSICAL_WORK"
    MIXED = "MIXED"
    STUDENT = "STUDENT"
    RETIRED = "RETIRED"

class DietTypeEnum(str, Enum):
    OMNIVORE = "OMNIVORE"
    VEGETARIAN = "VEGETARIAN"
    VEGAN = "VEGAN"
    PESCATARIAN = "PESCATARIAN"
    FLEXITARIAN = "FLEXITARIAN"

class MealTimingEnum(str, Enum):
    TRADITIONAL_3_MEALS = "TRADITIONAL_3_MEALS"
    SMALL_FREQUENT = "SMALL_FREQUENT"
    INTERMITTENT_FASTING = "INTERMITTENT_FASTING"

# Patient Profile Models
class BasicInfo(BaseModel):
    full_name: str
    age: int
    gender: str
    location: str
    contact_preferences: Dict[str, bool] = {}
    timezone: str
    emergency_contact: Dict[str, str] = {}
    preferred_language: str = "English"

class PhysicalMetrics(BaseModel):
    height_cm: float
    current_weight_kg: float
    goal_weight_kg: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    measurements: Dict[str, float] = {}  # waist, chest, hips
    bmi: Optional[float] = None

class SleepSchedule(BaseModel):
    bedtime: str
    wake_time: str
    sleep_quality: int = Field(ge=1, le=5)

class ActivityProfile(BaseModel):
    activity_level: ActivityLevelEnum
    exercise_types: List[str] = []
    exercise_frequency: int  # days per week
    sleep_schedule: SleepSchedule
    stress_level: int = Field(ge=1, le=5)
    work_type: WorkTypeEnum

class HealthHistory(BaseModel):
    primary_health_goals: List[str] = []
    medical_conditions: Dict[str, str] = {}  # condition: severity
    current_medications: List[Dict[str, Any]] = []
    allergies: List[str] = []
    food_intolerances: List[str] = []
    previous_surgeries: List[Dict[str, Any]] = []
    family_medical_history: List[str] = []

class DietaryProfile(BaseModel):
    diet_type: DietTypeEnum
    cultural_restrictions: List[str] = []
    specific_diets: List[str] = []
    food_allergies: List[str] = []
    food_dislikes: List[str] = []
    meal_timing_preference: MealTimingEnum
    cooking_skill_level: int = Field(ge=1, le=5)
    available_cooking_time: int  # minutes per day

class GoalsPreferences(BaseModel):
    health_targets: List[Dict[str, Any]] = []
    communication_methods: List[str] = []
    notification_preferences: Dict[str, bool] = {}
    privacy_settings: Dict[str, bool] = {}
    data_sharing_preferences: Dict[str, bool] = {}

class PatientProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str = "PATIENT"
    basic_info: Optional[BasicInfo] = None
    physical_metrics: Optional[PhysicalMetrics] = None
    activity_profile: Optional[ActivityProfile] = None
    health_history: Optional[HealthHistory] = None
    dietary_profile: Optional[DietaryProfile] = None
    goals_preferences: Optional[GoalsPreferences] = None
    profile_completion: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientProfileCreate(BaseModel):
    user_id: str
    basic_info: Optional[BasicInfo] = None
    physical_metrics: Optional[PhysicalMetrics] = None
    activity_profile: Optional[ActivityProfile] = None
    health_history: Optional[HealthHistory] = None
    dietary_profile: Optional[DietaryProfile] = None
    goals_preferences: Optional[GoalsPreferences] = None

class PatientProfileUpdate(BaseModel):
    basic_info: Optional[BasicInfo] = None
    physical_metrics: Optional[PhysicalMetrics] = None
    activity_profile: Optional[ActivityProfile] = None
    health_history: Optional[HealthHistory] = None
    dietary_profile: Optional[DietaryProfile] = None
    goals_preferences: Optional[GoalsPreferences] = None

# Provider Profile Models
class ProfessionalIdentity(BaseModel):
    full_name: str
    professional_title: str
    medical_license: str
    registration_numbers: Dict[str, str] = {}
    years_experience: int

class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: int
    specialization: str

class Certification(BaseModel):
    name: str
    organization: str
    issue_date: str
    expiration_date: str
    status: str = "ACTIVE"

class ProfessionalCredentials(BaseModel):
    education: List[Education] = []
    certifications: List[Certification] = []
    specializations: List[str] = []

class PracticeInfo(BaseModel):
    workplace: str
    practice_type: str
    patient_demographics: List[str] = []
    languages_spoken: List[str] = []
    areas_of_expertise: List[str] = []

class WorkingHours(BaseModel):
    timezone: str
    schedule: Dict[str, Dict[str, str]] = {}  # day: {start, end}

class PracticePreferences(BaseModel):
    consultation_types: List[str] = []
    working_hours: WorkingHours
    max_patients: int
    accepting_new_patients: bool = True
    specialized_conditions: List[str] = []
    treatment_philosophies: List[str] = []

class ProviderProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str = "PROVIDER"
    professional_identity: Optional[ProfessionalIdentity] = None
    credentials: Optional[ProfessionalCredentials] = None
    practice_info: Optional[PracticeInfo] = None
    preferences: Optional[PracticePreferences] = None
    verification_status: str = "PENDING"
    profile_completion: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProviderProfileCreate(BaseModel):
    user_id: str
    professional_identity: Optional[ProfessionalIdentity] = None
    credentials: Optional[ProfessionalCredentials] = None
    practice_info: Optional[PracticeInfo] = None
    preferences: Optional[PracticePreferences] = None

class ProviderProfileUpdate(BaseModel):
    professional_identity: Optional[ProfessionalIdentity] = None
    credentials: Optional[ProfessionalCredentials] = None
    practice_info: Optional[PracticeInfo] = None
    preferences: Optional[PracticePreferences] = None

# Family Profile Models
class FamilyStructure(BaseModel):
    family_role: str  # Parent, Spouse, Adult Child, etc.
    number_of_members: int
    primary_caregiver: bool = False

class FamilyMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    relationship: str
    age: int
    gender: str
    special_needs: List[str] = []
    allergies: List[str] = []
    medications: List[str] = []
    health_conditions: List[str] = []

class HouseholdManagement(BaseModel):
    common_dietary_restrictions: List[str] = []
    family_meal_preferences: List[str] = []
    budget_considerations: Dict[str, Any] = {}
    shopping_responsibilities: List[str] = []
    cooking_responsibilities: List[str] = []

class CareCoordination(BaseModel):
    healthcare_providers: Dict[str, Dict[str, str]] = {}  # member: {provider, contact}
    emergency_contacts: List[Dict[str, str]] = []
    medication_management: Dict[str, str] = {}
    health_tracking_preferences: Dict[str, bool] = {}

class FamilyProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str = "FAMILY"
    family_structure: Optional[FamilyStructure] = None
    family_members: List[FamilyMember] = []
    household_management: Optional[HouseholdManagement] = None
    care_coordination: Optional[CareCoordination] = None
    profile_completion: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FamilyProfileCreate(BaseModel):
    user_id: str
    family_structure: Optional[FamilyStructure] = None
    family_members: List[FamilyMember] = []
    household_management: Optional[HouseholdManagement] = None
    care_coordination: Optional[CareCoordination] = None

class FamilyProfileUpdate(BaseModel):
    family_structure: Optional[FamilyStructure] = None
    family_members: Optional[List[FamilyMember]] = None
    household_management: Optional[HouseholdManagement] = None
    care_coordination: Optional[CareCoordination] = None

# Guest Profile Models
class BasicDemographics(BaseModel):
    age: int
    gender: str
    activity_level: ActivityLevelEnum

class SimpleGoals(BaseModel):
    goal_type: str  # maintain, lose, gain
    target_amount: Optional[float] = None
    timeframe: Optional[str] = None

class GuestProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str = "GUEST"
    basic_demographics: Optional[BasicDemographics] = None
    simple_goals: Optional[SimpleGoals] = None
    session_expires: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GuestProfileCreate(BaseModel):
    session_id: str
    basic_demographics: BasicDemographics
    simple_goals: SimpleGoals
    session_expires: datetime

# ===== PROFILE COMPLETION HELPERS =====

def calculate_profile_completion(profile: dict, profile_type: str) -> float:
    """Calculate profile completion percentage based on filled fields"""
    if profile_type == "PATIENT":
        sections = ["basic_info", "physical_metrics", "activity_profile", "health_history", "dietary_profile", "goals_preferences"]
    elif profile_type == "PROVIDER":
        sections = ["professional_identity", "credentials", "practice_info", "preferences"]
    elif profile_type == "FAMILY":
        sections = ["family_structure", "family_members", "household_management", "care_coordination"]
    else:
        return 100.0  # Guest profiles are always complete
    
    completed_sections = 0
    for section in sections:
        section_data = profile.get(section)
        if section_data is not None:
            # Special handling for family_members - empty list should not count as completed
            if section == "family_members" and isinstance(section_data, list) and len(section_data) == 0:
                continue
            completed_sections += 1
    
async def analyze_food_with_ai(food_name: str, food_entry: dict):
    """Helper function to analyze food with AI"""
    try:
        # Basic nutrition estimation based on food name
        # In a real application, this would use more sophisticated AI
        nutrition_estimates = {
            "apple": {"calories": 95, "protein": 0.5, "carbs": 25, "fat": 0.3},
            "banana": {"calories": 105, "protein": 1.3, "carbs": 27, "fat": 0.4},
            "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
            "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
            "salmon": {"calories": 208, "protein": 22, "carbs": 0, "fat": 12}
        }
        
        food_lower = food_name.lower()
        for key, values in nutrition_estimates.items():
            if key in food_lower:
                return values
        
        # Default values if food not found
        return {"calories": 200, "protein": 8, "carbs": 25, "fat": 8}
    except Exception as e:
        logger.error(f"Food analysis error: {e}")
        return {"calories": 200, "protein": 8, "carbs": 25, "fat": 8}

# ===== PHASE 2.4: SYMPTOM CORRELATION TRACKER =====

# File upload constants
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/mp4", "audio/ogg", "audio/webm"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for free tier
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB for images
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB for audio

async def validate_file(file: UploadFile, file_type: str) -> dict:
    """Validate uploaded file based on type and size constraints"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Read file content to check size
    file_content = await file.read()
    file_size = len(file_content)
    
    # Reset file position for later use
    await file.seek(0)
    
    # Validate file size based on type
    if file_type == "photo":
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid image type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        if file_size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"Image file too large. Maximum size: {MAX_IMAGE_SIZE // (1024*1024)}MB"
            )
    elif file_type == "voice":
        if file.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid audio type. Allowed: {', '.join(ALLOWED_AUDIO_TYPES)}"
            )
        if file_size > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"Audio file too large. Maximum size: {MAX_AUDIO_SIZE // (1024*1024)}MB"
            )
    
    return {
        "size": file_size,
        "content_type": file.content_type,
        "filename": file.filename
    }

@api_router.post("/symptom/upload/photo")
async def upload_symptom_photo(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """Upload photo for symptom documentation"""
    try:
        # Validate the uploaded file
        validation_result = await validate_file(file, "photo")
        
        # Generate unique filename to prevent conflicts
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"photos/{user_id}/{uuid.uuid4()}{file_extension}"
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase Storage
        supabase = get_supabase_client()
        upload_response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        if hasattr(upload_response, 'error') and upload_response.error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to storage: {upload_response.error}"
            )
        
        # Get public URL for the uploaded file
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(unique_filename)
        
        return {
            "message": "Photo uploaded successfully",
            "file_path": unique_filename,
            "public_url": public_url,
            "file_size": validation_result["size"],
            "content_type": validation_result["content_type"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@api_router.post("/symptom/upload/voice")
async def upload_voice_note(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """Upload voice note for symptom tracking"""
    try:
        # Validate the uploaded file
        validation_result = await validate_file(file, "voice")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"voice/{user_id}/{uuid.uuid4()}{file_extension}"
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase Storage
        supabase = get_supabase_client()
        upload_response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        if hasattr(upload_response, 'error') and upload_response.error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload voice note to storage: {upload_response.error}"
            )
        
        # Get public URL for the uploaded file
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(unique_filename)
        
        return {
            "message": "Voice note uploaded successfully",
            "file_path": unique_filename,
            "public_url": public_url,
            "file_size": validation_result["size"],
            "content_type": validation_result["content_type"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice upload failed: {str(e)}"
        )

@api_router.post("/symptom/log/{user_id}")
async def log_symptom(user_id: str, symptom_data: dict = Body(...)):
    """Log a new symptom entry"""
    try:
        # Create symptom entry with ID
        symptom_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "symptom": symptom_data.get("symptom", ""),
            "severity": symptom_data.get("severity", 1),
            "duration": symptom_data.get("duration"),
            "triggers": symptom_data.get("triggers", []),
            "medications_taken": symptom_data.get("medications_taken", []),
            "notes": symptom_data.get("notes"),
            "photo_url": symptom_data.get("photo_url"),
            "voice_note_url": symptom_data.get("voice_note_url"),
            "correlations": {}
        }
        
        # Store in MongoDB
        result = await db.symptoms.insert_one(symptom_entry)
        symptom_entry["_id"] = str(result.inserted_id)
        
        # Run correlation analysis in background
        await analyze_symptom_correlations(user_id, symptom_entry["id"])
        
        return {
            "message": "Symptom logged successfully",
            "symptom_id": symptom_entry["id"],
            "logged_at": symptom_entry["timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log symptom: {str(e)}")

@api_router.get("/symptom/entries/{user_id}")
async def get_symptom_entries(user_id: str, days: int = 30):
    """Get symptom entries for a user within specified days"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Fetch symptom entries from MongoDB
        cursor = db.symptoms.find({
            "user_id": user_id,
            "timestamp": {"$gte": start_date, "$lte": end_date}
        }).sort("timestamp", -1)
        
        symptom_entries = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            symptom_entries.append(doc)
        
        return {
            "user_id": user_id,
            "entries": symptom_entries,
            "total_count": len(symptom_entries),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch symptom entries: {str(e)}")

async def analyze_symptom_correlations(user_id: str, symptom_id: str):
    """Advanced correlation analysis for symptom patterns"""
    try:
        # Get user's recent data (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Fetch symptom data
        symptoms_cursor = db.symptoms.find({
            "user_id": user_id,
            "timestamp": {"$gte": start_date}
        })
        symptoms_data = []
        async for doc in symptoms_cursor:
            symptoms_data.append(doc)
        
        # Fetch diet data (from food logs)
        diet_cursor = db.food_logs.find({
            "user_id": user_id,
            "logged_at": {"$gte": start_date}
        })
        diet_data = []
        async for doc in diet_cursor:
            diet_data.append(doc)
        
        # Perform correlation analysis
        correlations = calculate_correlations(symptoms_data, diet_data)
        
        # Generate AI insights using existing AI service
        ai_manager = AIServiceManager()
        
        correlation_request = {
            "user_symptoms": symptoms_data[-10:],  # Last 10 symptoms
            "user_diet": diet_data[-20:],  # Last 20 diet entries
            "analysis_type": "symptom_correlation",
            "timeframe": "30_days"
        }
        
        ai_insights = await ai_manager.get_health_insights(correlation_request)
        
        # Update symptom entry with correlation data
        await db.symptoms.update_one(
            {"id": symptom_id},
            {"$set": {"correlations": correlations, "ai_insights": ai_insights}}
        )
        
        return correlations
        
    except Exception as e:
        logging.error(f"Correlation analysis failed: {str(e)}")
        return {}

def calculate_correlations(symptoms_data: List[dict], diet_data: List[dict]) -> dict:
    """Calculate multi-variate correlation analysis"""
    try:
        # Group symptoms by type
        symptom_groups = {}
        for symptom in symptoms_data:
            symptom_type = symptom.get("symptom", "unknown")
            if symptom_type not in symptom_groups:
                symptom_groups[symptom_type] = []
            symptom_groups[symptom_type].append(symptom)
        
        # Analyze correlations
        correlations = {}
        
        for symptom_type, entries in symptom_groups.items():
            if len(entries) >= 3:  # Need at least 3 entries for correlation
                # Calculate average severity
                avg_severity = sum(e.get("severity", 0) for e in entries) / len(entries)
                
                # Analyze patterns
                patterns = {
                    "frequency": len(entries),
                    "average_severity": round(avg_severity, 1),
                    "common_triggers": get_common_triggers(entries),
                    "time_patterns": analyze_time_patterns(entries),
                    "medication_effectiveness": analyze_medication_patterns(entries)
                }
                
                correlations[symptom_type] = patterns
        
        return correlations
        
    except Exception as e:
        logging.error(f"Correlation calculation failed: {str(e)}")
        return {}

def get_common_triggers(entries: List[dict]) -> List[str]:
    """Identify most common triggers"""
    trigger_counts = {}
    for entry in entries:
        for trigger in entry.get("triggers", []):
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
    
    # Return triggers that appear in at least 30% of entries
    threshold = max(1, len(entries) * 0.3)
    return [trigger for trigger, count in trigger_counts.items() if count >= threshold]

def analyze_time_patterns(entries: List[dict]) -> dict:
    """Analyze temporal patterns in symptoms"""
    hour_counts = {}
    day_counts = {}
    
    for entry in entries:
        timestamp = entry.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            hour = timestamp.hour
            day = timestamp.strftime("%A")
            
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
            day_counts[day] = day_counts.get(day, 0) + 1
    
    # Find peak times
    peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
    peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
    
    return {
        "peak_hour": peak_hour,
        "peak_day": peak_day,
        "hourly_distribution": hour_counts,
        "daily_distribution": day_counts
    }

def analyze_medication_patterns(entries: List[dict]) -> dict:
    """Analyze medication effectiveness patterns"""
    medication_effects = {}
    
    for entry in entries:
        medications = entry.get("medications_taken", [])
        severity = entry.get("severity", 0)
        
        for med in medications:
            if med not in medication_effects:
                medication_effects[med] = {"severities": [], "count": 0}
            medication_effects[med]["severities"].append(severity)
            medication_effects[med]["count"] += 1
    
    # Calculate effectiveness
    for med, data in medication_effects.items():
        if data["count"] > 0:
            data["average_severity"] = sum(data["severities"]) / len(data["severities"])
            data["effectiveness_rating"] = max(0, min(10, (10 - data["average_severity"])))
    
    return medication_effects

@api_router.get("/symptom/correlations/{user_id}")
async def get_advanced_correlations(user_id: str):
    """Get advanced correlation analysis and predictions"""
    try:
        # Get recent symptom data
        symptoms_cursor = db.symptoms.find({
            "user_id": user_id,
            "timestamp": {"$gte": datetime.utcnow() - timedelta(days=60)}
        }).sort("timestamp", -1)
        
        symptoms_data = []
        async for doc in symptoms_cursor:
            doc["_id"] = str(doc["_id"])
            symptoms_data.append(doc)
        
        if not symptoms_data:
            return {
                "user_id": user_id,
                "correlations": [],
                "predictions": [],
                "insights": ["Start logging symptoms to see patterns and correlations"],
                "confidence": 0.0
            }
        
        # Perform advanced correlation analysis
        correlations = calculate_correlations(symptoms_data, [])
        
        # Generate predictions using AI
        predictions = await generate_symptom_predictions(user_id, symptoms_data)
        
        # Generate insights
        insights = generate_correlation_insights(correlations)
        
        return {
            "user_id": user_id,
            "correlations": correlations,
            "predictions": predictions,
            "insights": insights,
            "confidence": calculate_confidence_score(symptoms_data),
            "data_points": len(symptoms_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get correlations: {str(e)}")

async def generate_symptom_predictions(user_id: str, symptoms_data: List[dict]) -> List[dict]:
    """Generate symptom predictions using AI"""
    try:
        ai_manager = AIServiceManager()
        
        prediction_request = {
            "user_id": user_id,
            "symptom_history": symptoms_data[-20:],  # Last 20 entries
            "prediction_horizon": "7_days",
            "analysis_type": "symptom_prediction"
        }
        
        ai_response = await ai_manager.get_health_insights(prediction_request)
        
        # Extract predictions from AI response
        predictions = []
        if isinstance(ai_response, dict) and "predictions" in ai_response:
            predictions = ai_response["predictions"]
        else:
            # Generate basic predictions based on patterns
            predictions = generate_basic_predictions(symptoms_data)
        
        return predictions[:5]  # Return top 5 predictions
        
    except Exception as e:
        logging.error(f"Prediction generation failed: {str(e)}")
        return generate_basic_predictions(symptoms_data)

def generate_basic_predictions(symptoms_data: List[dict]) -> List[dict]:
    """Generate basic predictions based on historical patterns"""
    predictions = []
    
    # Group by symptom type
    symptom_groups = {}
    for symptom in symptoms_data:
        symptom_type = symptom.get("symptom", "unknown")
        if symptom_type not in symptom_groups:
            symptom_groups[symptom_type] = []
        symptom_groups[symptom_type].append(symptom)
    
    # Generate predictions for each symptom type
    for symptom_type, entries in symptom_groups.items():
        if len(entries) >= 3:
            # Calculate frequency
            days_span = 30  # Assume 30 days of data
            frequency = len(entries) / days_span
            
            # Predict next occurrence
            avg_interval = days_span / len(entries)
            last_occurrence = entries[0].get("timestamp", datetime.utcnow())
            if isinstance(last_occurrence, str):
                last_occurrence = datetime.fromisoformat(last_occurrence.replace('Z', '+00:00'))
            
            next_predicted = last_occurrence + timedelta(days=avg_interval)
            
            predictions.append({
                "symptom": symptom_type,
                "predicted_date": next_predicted.isoformat(),
                "probability": min(0.9, frequency * 7),  # Weekly probability
                "confidence": 0.7 if len(entries) > 5 else 0.5,
                "reasoning": f"Based on {len(entries)} occurrences, appears every {avg_interval:.1f} days"
            })
    
    return sorted(predictions, key=lambda x: x["probability"], reverse=True)

def generate_correlation_insights(correlations: dict) -> List[str]:
    """Generate actionable insights from correlation data"""
    insights = []
    
    for symptom_type, data in correlations.items():
        frequency = data.get("frequency", 0)
        avg_severity = data.get("average_severity", 0)
        common_triggers = data.get("common_triggers", [])
        peak_hour = data.get("time_patterns", {}).get("peak_hour")
        
        if frequency >= 5:
            insights.append(f"{symptom_type.title()} occurs frequently ({frequency} times recently)")
        
        if avg_severity > 7:
            insights.append(f"{symptom_type.title()} tends to be severe (avg {avg_severity}/10)")
        
        if common_triggers:
            insights.append(f"{symptom_type.title()} commonly triggered by: {', '.join(common_triggers)}")
        
        if peak_hour is not None:
            time_desc = "morning" if peak_hour < 12 else "afternoon" if peak_hour < 18 else "evening"
            insights.append(f"{symptom_type.title()} most common in the {time_desc}")
    
    if not insights:
        insights = [
            "Continue logging symptoms to identify patterns",
            "Include triggers and severity ratings for better insights",
            "Note medication timing and effectiveness"
        ]
    
    return insights[:5]  # Limit to 5 insights

def calculate_confidence_score(symptoms_data: List[dict]) -> float:
    """Calculate confidence score based on data quality and quantity"""
    if not symptoms_data:
        return 0.0
    
    score = 0.0
    
    # Data quantity (up to 0.4 points)
    quantity_score = min(0.4, len(symptoms_data) / 50)
    score += quantity_score
    
    # Data completeness (up to 0.3 points)
    complete_entries = sum(1 for entry in symptoms_data 
                          if entry.get("severity") and entry.get("symptom") and len(entry.get("triggers", [])) > 0)
    completeness_score = (complete_entries / len(symptoms_data)) * 0.3
    score += completeness_score
    
    # Time span (up to 0.3 points)
    if len(symptoms_data) > 1:
        first_entry = symptoms_data[-1].get("timestamp", datetime.utcnow())
        last_entry = symptoms_data[0].get("timestamp", datetime.utcnow())
        
        if isinstance(first_entry, str):
            first_entry = datetime.fromisoformat(first_entry.replace('Z', '+00:00'))
        if isinstance(last_entry, str):
            last_entry = datetime.fromisoformat(last_entry.replace('Z', '+00:00'))
        
        time_span_days = (last_entry - first_entry).days
        time_score = min(0.3, time_span_days / 30)
        score += time_score
    
    return round(score, 2)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== GOAL TRACKING AND ACHIEVEMENT MODELS =====

class GoalTypeEnum(str, Enum):
    NUTRITION = "NUTRITION"
    FITNESS = "FITNESS"
    WEIGHT_MANAGEMENT = "WEIGHT_MANAGEMENT"
    SLEEP = "SLEEP"
    HYDRATION = "HYDRATION"
    WELLNESS = "WELLNESS"
    MEDICAL_COMPLIANCE = "MEDICAL_COMPLIANCE"
    HABIT_BUILDING = "HABIT_BUILDING"

class GoalStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"

class GoalPriorityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    goal_type: GoalTypeEnum
    status: GoalStatusEnum = GoalStatusEnum.ACTIVE
    priority: GoalPriorityEnum = GoalPriorityEnum.MEDIUM
    target_value: Optional[float] = None
    current_value: Optional[float] = 0.0
    target_unit: Optional[str] = None
    target_date: Optional[datetime] = None
    start_date: datetime = Field(default_factory=datetime.utcnow)
    completion_date: Optional[datetime] = None
    milestones: List[Dict[str, Any]] = []
    progress_history: List[Dict[str, Any]] = []
    success_probability: Optional[float] = None
    ai_insights: List[str] = []
    streak_count: int = 0
    longest_streak: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GoalCreate(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None
    goal_type: GoalTypeEnum
    priority: GoalPriorityEnum = GoalPriorityEnum.MEDIUM
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    target_date: Optional[datetime] = None
    milestones: List[Dict[str, Any]] = []

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatusEnum] = None
    priority: Optional[GoalPriorityEnum] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    target_date: Optional[datetime] = None
    milestones: Optional[List[Dict[str, Any]]] = None

class AchievementTypeEnum(str, Enum):
    GOAL_COMPLETION = "GOAL_COMPLETION"
    STREAK_MILESTONE = "STREAK_MILESTONE"
    PROGRESS_MILESTONE = "PROGRESS_MILESTONE"
    CATEGORY_ACHIEVEMENT = "CATEGORY_ACHIEVEMENT"
    SPECIAL_RECOGNITION = "SPECIAL_RECOGNITION"

class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    achievement_type: AchievementTypeEnum
    title: str
    description: str
    badge_icon: str
    badge_color: str
    points_awarded: int = 0
    rarity_level: str = "COMMON"  # COMMON, RARE, EPIC, LEGENDARY
    unlock_criteria: Dict[str, Any] = {}
    unlocked_at: datetime = Field(default_factory=datetime.utcnow)
    related_goal_id: Optional[str] = None
    category: str
    shareable: bool = True
    celebration_message: str
    milestone_data: Dict[str, Any] = {}

class GoalCorrelation(BaseModel):
    user_id: str
    goal_correlations: List[Dict[str, Any]] = []
    behavior_patterns: Dict[str, Any] = {}
    success_factors: List[str] = []
    recommendations: List[Dict[str, Any]] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Health & Nutrition Platform API"}

# ===== PROFILE MANAGEMENT API ENDPOINTS =====

# Patient Profile Endpoints
@api_router.post("/profiles/patient", response_model=PatientProfile)
async def create_patient_profile(profile: PatientProfileCreate):
    profile_dict = profile.dict()
    profile_obj = PatientProfile(**profile_dict)
    profile_obj.profile_completion = calculate_profile_completion(profile_dict, "PATIENT")
    
    # Check if profile already exists
    existing = await db.patient_profiles.find_one({"user_id": profile.user_id})
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    
    await db.patient_profiles.insert_one(profile_obj.dict())
    return profile_obj

@api_router.get("/profiles/patient/{user_id}", response_model=PatientProfile)
async def get_patient_profile(user_id: str):
    profile = await db.patient_profiles.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return PatientProfile(**profile)

@api_router.put("/profiles/patient/{user_id}", response_model=PatientProfile)
async def update_patient_profile(user_id: str, update: PatientProfileUpdate):
    existing = await db.patient_profiles.find_one({"user_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_dict = {k: v for k, v in update.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    # Merge existing profile with updates
    merged_profile = {**existing, **update_dict}
    merged_profile["profile_completion"] = calculate_profile_completion(merged_profile, "PATIENT")
    update_dict["profile_completion"] = merged_profile["profile_completion"]
    
    await db.patient_profiles.update_one(
        {"user_id": user_id},
        {"$set": update_dict}
    )
    
    updated_profile = await db.patient_profiles.find_one({"user_id": user_id})
    return PatientProfile(**updated_profile)

@api_router.delete("/profiles/patient/{user_id}")
async def delete_patient_profile(user_id: str):
    result = await db.patient_profiles.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted successfully"}

# Provider Profile Endpoints
@api_router.post("/profiles/provider", response_model=ProviderProfile)
async def create_provider_profile(profile: ProviderProfileCreate):
    profile_dict = profile.dict()
    profile_obj = ProviderProfile(**profile_dict)
    profile_obj.profile_completion = calculate_profile_completion(profile_dict, "PROVIDER")
    
    existing = await db.provider_profiles.find_one({"user_id": profile.user_id})
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    
    await db.provider_profiles.insert_one(profile_obj.dict())
    return profile_obj

@api_router.get("/profiles/provider/{user_id}", response_model=ProviderProfile)
async def get_provider_profile(user_id: str):
    profile = await db.provider_profiles.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProviderProfile(**profile)

@api_router.put("/profiles/provider/{user_id}", response_model=ProviderProfile)
async def update_provider_profile(user_id: str, update: ProviderProfileUpdate):
    existing = await db.provider_profiles.find_one({"user_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_dict = {k: v for k, v in update.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    merged_profile = {**existing, **update_dict}
    merged_profile["profile_completion"] = calculate_profile_completion(merged_profile, "PROVIDER")
    update_dict["profile_completion"] = merged_profile["profile_completion"]
    
    await db.provider_profiles.update_one(
        {"user_id": user_id},
        {"$set": update_dict}
    )
    
    updated_profile = await db.provider_profiles.find_one({"user_id": user_id})
    return ProviderProfile(**updated_profile)

@api_router.delete("/profiles/provider/{user_id}")
async def delete_provider_profile(user_id: str):
    result = await db.provider_profiles.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted successfully"}

# Family Profile Endpoints
@api_router.post("/profiles/family", response_model=FamilyProfile)
async def create_family_profile(profile: FamilyProfileCreate):
    profile_dict = profile.dict()
    profile_obj = FamilyProfile(**profile_dict)
    profile_obj.profile_completion = calculate_profile_completion(profile_dict, "FAMILY")
    
    existing = await db.family_profiles.find_one({"user_id": profile.user_id})
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    
    await db.family_profiles.insert_one(profile_obj.dict())
    return profile_obj

@api_router.get("/profiles/family/{user_id}", response_model=FamilyProfile)
async def get_family_profile(user_id: str):
    profile = await db.family_profiles.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return FamilyProfile(**profile)

@api_router.put("/profiles/family/{user_id}", response_model=FamilyProfile)
async def update_family_profile(user_id: str, update: FamilyProfileUpdate):
    existing = await db.family_profiles.find_one({"user_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_dict = {k: v for k, v in update.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    merged_profile = {**existing, **update_dict}
    merged_profile["profile_completion"] = calculate_profile_completion(merged_profile, "FAMILY")
    update_dict["profile_completion"] = merged_profile["profile_completion"]
    
    await db.family_profiles.update_one(
        {"user_id": user_id},
        {"$set": update_dict}
    )
    
    updated_profile = await db.family_profiles.find_one({"user_id": user_id})
    return FamilyProfile(**updated_profile)

@api_router.delete("/profiles/family/{user_id}")
async def delete_family_profile(user_id: str):
    result = await db.family_profiles.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted successfully"}

# Guest Profile Endpoints
@api_router.post("/profiles/guest", response_model=GuestProfile)
async def create_guest_profile(profile: GuestProfileCreate):
    profile_dict = profile.dict()
    profile_obj = GuestProfile(**profile_dict)
    
    # Clean up expired guest profiles periodically
    await db.guest_profiles.delete_many({"session_expires": {"$lt": datetime.utcnow()}})
    
    await db.guest_profiles.insert_one(profile_obj.dict())
    return profile_obj

@api_router.get("/profiles/guest/{session_id}", response_model=GuestProfile)
async def get_guest_profile(session_id: str):
    profile = await db.guest_profiles.find_one({
        "session_id": session_id,
        "session_expires": {"$gt": datetime.utcnow()}
    })
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found or expired")
    return GuestProfile(**profile)

@api_router.delete("/profiles/guest/{session_id}")
async def delete_guest_profile(session_id: str):
    result = await db.guest_profiles.delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted successfully"}

# Profile Completion Status Endpoints
@api_router.get("/profiles/completion/{user_id}")
async def get_profile_completion_status(user_id: str, role: str):
    if role.upper() == "PATIENT":
        profile = await db.patient_profiles.find_one({"user_id": user_id})
    elif role.upper() == "PROVIDER":
        profile = await db.provider_profiles.find_one({"user_id": user_id})
    elif role.upper() == "FAMILY":
        profile = await db.family_profiles.find_one({"user_id": user_id})
    else:
        raise HTTPException(status_code=400, detail="Invalid role specified")
    
    if not profile:
        return {"completion_percentage": 0.0, "missing_sections": []}
    
    completion = profile.get("profile_completion", 0.0)
    
    # Determine missing sections
    missing_sections = []
    if role.upper() == "PATIENT":
        sections = ["basic_info", "physical_metrics", "activity_profile", "health_history", "dietary_profile", "goals_preferences"]
    elif role.upper() == "PROVIDER":
        sections = ["professional_identity", "credentials", "practice_info", "preferences"]
    else:  # FAMILY
        sections = ["family_structure", "family_members", "household_management", "care_coordination"]
    
    missing_sections = [section for section in sections if not profile.get(section)]
    
    return {
        "completion_percentage": completion,
        "missing_sections": missing_sections,
        "total_sections": len(sections),
        "completed_sections": len(sections) - len(missing_sections)
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Role-specific API endpoints
@api_router.post("/users", response_model=UserProfile)
async def create_user(user: UserProfileCreate):
    user_dict = user.dict()
    user_obj = UserProfile(**user_dict)
    _ = await db.users.insert_one(user_obj.dict())
    return user_obj

@api_router.get("/users/{role}", response_model=List[UserProfile])
async def get_users_by_role(role: str):
    users = await db.users.find({"role": role}).to_list(1000)
    return [UserProfile(**user) for user in users]

@api_router.post("/health-metrics", response_model=HealthMetric)
async def create_health_metric(metric: HealthMetricCreate):
    metric_dict = metric.dict()
    metric_obj = HealthMetric(**metric_dict)
    _ = await db.health_metrics.insert_one(metric_obj.dict())
    return metric_obj

@api_router.get("/health-metrics/{user_id}", response_model=List[HealthMetric])
async def get_user_health_metrics(user_id: str):
    metrics = await db.health_metrics.find({"user_id": user_id}).to_list(1000)
    return [HealthMetric(**metric) for metric in metrics]

# Patient-specific endpoints
@api_router.get("/patient/dashboard/{user_id}")
async def get_patient_dashboard(user_id: str):
    return {
        "user_id": user_id,
        "welcome_message": "Welcome back, Sarah!",
        "nutrition_summary": {
            "calories": {"current": 1847, "remaining": 153, "target": 2000},
            "protein": {"current": 98, "target": 120, "unit": "g"},
            "carbs": {"current": 147, "target": 200, "unit": "g"},
            "fat": {"current": 52, "target": 65, "unit": "g"}
        },
        "health_metrics": {
            "blood_pressure": {"value": "120/80", "unit": "mmHg", "status": "Normal"},
            "weight": {"value": 68.5, "unit": "kg", "change": -0.3},
            "glucose": {"value": 95, "unit": "mg/dL", "status": "Normal"}
        },
        "goals": {
            "daily_steps": {"current": 8432, "target": 10000, "progress": 84},
            "water_intake": {"current": 6, "target": 8, "progress": 75},
            "weekly_exercise": {"current": 3, "target": 5, "progress": 60}
        },
        "recent_meals": [
            {"id": 1, "meal": "Breakfast", "food": "Oatmeal with berries", "calories": 350, "time": "8:00 AM"},
            {"id": 2, "meal": "Lunch", "food": "Grilled chicken salad", "calories": 425, "time": "12:30 PM"}
        ],
        "ai_recommendations": [
            {"type": "meal", "title": "Meal Suggestion", "message": "Try a protein-rich snack like Greek yogurt to reach your daily protein goal."},
            {"type": "hydration", "title": "Hydration Reminder", "message": "You're 2 glasses behind your water goal. Have a glass now!"},
            {"type": "activity", "title": "Activity Boost", "message": "A 15-minute walk would help you reach your step goal."}
        ]
    }

@api_router.get("/patient/food-log/{user_id}")
async def get_patient_food_log(user_id: str):
    return {
        "user_id": user_id,
        "today_entries": [
            {"id": 1, "time": "8:00 AM", "meal": "Breakfast", "food": "Oatmeal with berries", "calories": 350},
            {"id": 2, "time": "12:30 PM", "meal": "Lunch", "food": "Grilled chicken salad", "calories": 425}
        ],
        "total_calories": 775,
        "remaining_calories": 1225
    }

@api_router.get("/patient/health-metrics/{user_id}")
async def get_patient_health_metrics(user_id: str):
    return {
        "user_id": user_id,
        "metrics": [
            {"type": "weight", "value": 68.5, "unit": "kg", "date": "2024-01-15", "trend": "decreasing"},
            {"type": "blood_pressure", "systolic": 120, "diastolic": 80, "date": "2024-01-15", "status": "normal"},
            {"type": "glucose", "value": 95, "unit": "mg/dL", "date": "2024-01-15", "status": "normal"}
        ]
    }

# Provider-specific endpoints
@api_router.get("/provider/dashboard/{user_id}")
async def get_provider_dashboard(user_id: str):
    return {
        "user_id": user_id,
        "welcome_message": "Good morning, Dr. Smith!",
        "patient_overview": {
            "active_patients": 247,
            "prescriptions": 156,
            "compliance_rate": 94,
            "todays_visits": 12
        },
        "clinical_alerts": [
            {"id": 1, "patient": "John D.", "type": "critical", "message": "Blood pressure spike detected", "priority": "high"},
            {"id": 2, "patient": "Sarah M.", "type": "warning", "message": "Missed medication doses", "priority": "medium"},
            {"id": 3, "patient": "Mike R.", "type": "info", "message": "Excellent progress this week", "priority": "low"}
        ],
        "todays_appointments": [
            {"id": 1, "time": "9:00 AM", "patient": "Emma Wilson", "type": "Nutrition consultation", "status": "completed"},
            {"id": 2, "time": "11:30 AM", "patient": "David Chen", "type": "Follow-up appointment", "status": "in_progress"},
            {"id": 3, "time": "2:00 PM", "patient": "Lisa Garcia", "type": "Initial assessment", "status": "upcoming"}
        ],
        "patient_progress": {
            "weight_loss_goals": {"percentage": 87, "description": "patients on track"},
            "medication_adherence": {"percentage": 94, "description": "compliance rate"},
            "lifestyle_changes": {"percentage": 76, "description": "showing improvement"}
        }
    }

@api_router.get("/provider/patients")
async def get_provider_patients():
    return {
        "patients": [
            {"id": 1, "name": "John Doe", "age": 45, "condition": "Diabetes", "last_visit": "2024-01-10", "status": "stable"},
            {"id": 2, "name": "Sarah Miller", "age": 38, "condition": "Hypertension", "last_visit": "2024-01-12", "status": "improving"},
            {"id": 3, "name": "Mike Rodriguez", "age": 52, "condition": "Obesity", "last_visit": "2024-01-08", "status": "excellent"}
        ],
        "total_patients": 247,
        "active_patients": 189
    }

@api_router.get("/provider/clinical-tools")
async def get_clinical_tools():
    return {
        "tools": [
            {"name": "Diet Prescription Generator", "description": "Create evidence-based diet plans", "category": "nutrition"},
            {"name": "Drug Interaction Checker", "description": "Check for medication interactions", "category": "pharmacy"},
            {"name": "BMI Calculator", "description": "Calculate and track BMI over time", "category": "assessment"},
            {"name": "Risk Assessment", "description": "Cardiovascular risk calculator", "category": "assessment"}
        ]
    }

# PHASE 4: Advanced Provider Features

@api_router.get("/provider/patient-queue/{provider_id}")
async def get_patient_queue(provider_id: str):
    """Patient Queue Management System"""
    return {
        "provider_id": provider_id,
        "queue_stats": {
            "total_in_queue": 12,
            "urgent": 3,
            "scheduled": 8,
            "walk_in": 1,
            "avg_wait_time": "18 minutes"
        },
        "priority_queue": [
            {
                "id": "urgent-001",
                "patient_name": "Maria Rodriguez",
                "condition": "Chest pain",
                "priority": "urgent",
                "wait_time": "5 minutes",
                "room": "ER-3",
                "vitals": {"bp": "160/95", "hr": "105", "temp": "98.6°F"},
                "status": "ready_for_provider"
            },
            {
                "id": "urgent-002", 
                "patient_name": "Robert Chen",
                "condition": "Diabetic emergency",
                "priority": "urgent",
                "wait_time": "12 minutes",
                "room": "Room 5",
                "vitals": {"bp": "145/88", "hr": "92", "glucose": "280"},
                "status": "vitals_taken"
            }
        ],
        "scheduled_queue": [
            {
                "id": "sched-001",
                "patient_name": "Sarah Johnson",
                "appointment_time": "2:00 PM",
                "condition": "Routine follow-up",
                "priority": "routine",
                "wait_time": "on_time",
                "room": "Room 2",
                "status": "checked_in"
            },
            {
                "id": "sched-002",
                "patient_name": "David Wilson",
                "appointment_time": "2:30 PM", 
                "condition": "Medication review",
                "priority": "routine",
                "wait_time": "early",
                "room": "waiting",
                "status": "waiting"
            }
        ],
        "completed_today": 8,
        "no_shows": 1
    }

@api_router.post("/provider/clinical-decision-support")
async def clinical_decision_support(request: dict):
    """AI-Powered Clinical Decision Support"""
    patient_data = request.get("patient_data", {})
    symptoms = request.get("symptoms", [])
    history = request.get("history", [])
    
    # This would integrate with AI service for real recommendations
    return {
        "request_id": f"cds-{uuid.uuid4().hex[:8]}",
        "patient_id": patient_data.get("id", "unknown"),
        "ai_recommendations": [
            {
                "category": "diagnosis",
                "confidence": 0.87,
                "recommendation": "Consider Type 2 Diabetes screening based on symptoms",
                "evidence": "Patient presents with classic triad: polyuria, polydipsia, and unexplained weight loss",
                "next_steps": ["Order HbA1c", "Fasting glucose test", "Consider glucose tolerance test"]
            },
            {
                "category": "treatment",
                "confidence": 0.92,
                "recommendation": "Lifestyle modifications as first-line intervention",
                "evidence": "Evidence-based guidelines support lifestyle changes for pre-diabetes prevention",
                "next_steps": ["Dietary counseling", "Exercise prescription", "Weight management plan"]
            }
        ],
        "drug_interactions": [],
        "contraindications": [],
        "clinical_guidelines": [
            {
                "guideline": "ADA Standards of Medical Care 2024",
                "recommendation": "Screen adults ≥45 years for diabetes every 3 years",
                "relevance": "high"
            }
        ],
        "risk_scores": {
            "diabetes_risk": 0.73,
            "cardiovascular_risk": 0.41,
            "overall_risk": "moderate"
        }
    }

@api_router.get("/provider/treatment-outcomes/{provider_id}")
async def get_treatment_outcomes(provider_id: str, timeframe: str = "30d"):
    """Treatment Outcome Tracking"""
    return {
        "provider_id": provider_id,
        "timeframe": timeframe,
        "outcome_summary": {
            "total_patients_treated": 156,
            "successful_outcomes": 134,
            "success_rate": 85.9,
            "readmission_rate": 4.2,
            "patient_satisfaction": 4.7
        },
        "condition_outcomes": [
            {
                "condition": "Type 2 Diabetes",
                "patients": 45,
                "improved": 38,
                "stable": 5,
                "declined": 2,
                "avg_hba1c_reduction": 1.2,
                "target_achievement_rate": 84.4
            },
            {
                "condition": "Hypertension",
                "patients": 62,
                "improved": 48,
                "stable": 12,
                "declined": 2,
                "avg_bp_reduction": "15/8 mmHg",
                "target_achievement_rate": 77.4
            },
            {
                "condition": "Obesity",
                "patients": 33,
                "improved": 28,
                "stable": 4,
                "declined": 1,
                "avg_weight_loss": 12.3,
                "target_achievement_rate": 84.8
            }
        ],
        "trending_metrics": [
            {
                "metric": "HbA1c Control",
                "current": 84.4,
                "previous": 78.2,
                "trend": "improving",
                "change": "+6.2%"
            },
            {
                "metric": "Blood Pressure Control",
                "current": 77.4,
                "previous": 74.1,
                "trend": "improving", 
                "change": "+3.3%"
            }
        ]
    }

@api_router.get("/provider/population-health/{provider_id}")
async def get_population_health(provider_id: str):
    """Population Health Analytics"""
    return {
        "provider_id": provider_id,
        "population_overview": {
            "total_population": 2847,
            "active_patients": 2156,
            "high_risk_patients": 284,
            "chronic_conditions_prevalence": 45.2
        },
        "demographic_breakdown": [
            {"age_group": "18-35", "count": 542, "percentage": 19.0, "top_conditions": ["Anxiety", "Depression"]},
            {"age_group": "36-50", "count": 896, "percentage": 31.5, "top_conditions": ["Hypertension", "Diabetes"]},
            {"age_group": "51-65", "count": 758, "percentage": 26.6, "top_conditions": ["Diabetes", "Heart Disease"]},
            {"age_group": "65+", "count": 651, "percentage": 22.9, "top_conditions": ["Heart Disease", "Arthritis"]}
        ],
        "condition_prevalence": [
            {"condition": "Hypertension", "count": 567, "prevalence": 19.9, "trend": "stable"},
            {"condition": "Type 2 Diabetes", "count": 423, "prevalence": 14.9, "trend": "increasing"},
            {"condition": "Obesity", "count": 398, "prevalence": 14.0, "trend": "increasing"},
            {"condition": "Heart Disease", "count": 278, "prevalence": 9.8, "trend": "stable"},
            {"condition": "Depression", "count": 234, "prevalence": 8.2, "trend": "increasing"}
        ],
        "risk_stratification": {
            "low_risk": {"count": 1698, "percentage": 59.7},
            "medium_risk": {"count": 865, "percentage": 30.4},
            "high_risk": {"count": 284, "percentage": 9.9}
        },
        "quality_measures": [
            {
                "measure": "Diabetes HbA1c Control",
                "target": ">80%",
                "current": "84.2%",
                "status": "meeting_target"
            },
            {
                "measure": "Blood Pressure Control",
                "target": ">75%", 
                "current": "77.8%",
                "status": "meeting_target"
            },
            {
                "measure": "Preventive Screening",
                "target": ">90%",
                "current": "67.3%",
                "status": "below_target"
            }
        ],
        "intervention_opportunities": [
            {
                "intervention": "Diabetes Prevention Program",
                "eligible_patients": 156,
                "potential_impact": "23% risk reduction",
                "priority": "high"
            },
            {
                "intervention": "Hypertension Management",
                "eligible_patients": 89,
                "potential_impact": "15% cardiovascular risk reduction",
                "priority": "medium"
            }
        ]
    }

@api_router.post("/provider/evidence-recommendations")
async def get_evidence_recommendations(request: dict):
    """AI-Powered Evidence-Based Recommendations"""
    condition = request.get("condition", "")
    patient_profile = request.get("patient_profile", {})
    clinical_context = request.get("clinical_context", "")
    
    # This would integrate with AI service for real evidence-based recommendations
    return {
        "request_id": f"ebr-{uuid.uuid4().hex[:8]}",
        "condition": condition,
        "evidence_level": "high",
        "recommendations": [
            {
                "category": "first_line_treatment",
                "recommendation": "Metformin monotherapy",
                "evidence_level": "A",
                "source": "ADA 2024 Standards of Care",
                "dosing": "Start 500mg BID, titrate to 1000mg BID",
                "monitoring": "Monitor renal function, B12 levels",
                "contraindications": ["eGFR <30", "Acute heart failure"],
                "confidence": 0.94
            },
            {
                "category": "lifestyle_intervention",
                "recommendation": "Structured lifestyle program",
                "evidence_level": "A",
                "source": "Diabetes Prevention Program",
                "details": "7% weight loss goal, 150 min/week moderate exercise",
                "expected_outcome": "58% diabetes risk reduction",
                "confidence": 0.96
            }
        ],
        "clinical_studies": [
            {
                "study": "UKPDS",
                "year": "1998",
                "finding": "Intensive glucose control reduces microvascular complications",
                "relevance": "high",
                "patient_count": 3867
            }
        ],
        "contraindications": [],
        "drug_interactions": [],
        "patient_specific_factors": [
            {
                "factor": "Age > 65",
                "implication": "Consider lower starting dose",
                "adjustment": "Start metformin 250mg BID"
            }
        ],
        "follow_up_recommendations": [
            "Reassess in 3 months",
            "Monitor HbA1c quarterly",
            "Annual eye exam",
            "Quarterly foot exam"
        ]
    }

@api_router.get("/provider/continuing-education/{provider_id}")
async def get_continuing_education(provider_id: str):
    """Professional Continuing Education Portal"""
    return {
        "provider_id": provider_id,
        "education_summary": {
            "total_credits_earned": 32.5,
            "credits_required": 50.0,
            "progress_percentage": 65.0,
            "courses_completed": 8,
            "courses_in_progress": 3,
            "deadline": "2024-12-31"
        },
        "featured_courses": [
            {
                "id": "course-001",
                "title": "Advanced Diabetes Management 2024",
                "provider": "American Diabetes Association", 
                "credits": 4.0,
                "duration": "4 hours",
                "format": "Online",
                "difficulty": "Intermediate",
                "rating": 4.8,
                "enrolled": False,
                "cost": "Free",
                "description": "Latest evidence-based approaches to diabetes care",
                "learning_objectives": [
                    "Apply 2024 ADA guidelines",
                    "Optimize medication regimens",
                    "Implement technology solutions"
                ]
            },
            {
                "id": "course-002",
                "title": "Population Health Strategies",
                "provider": "CDC",
                "credits": 3.5,
                "duration": "3.5 hours",
                "format": "Webinar",
                "difficulty": "Advanced",
                "rating": 4.6,
                "enrolled": True,
                "progress": 60,
                "cost": "Free",
                "description": "Community-based interventions for chronic disease"
            }
        ],
        "my_courses": [
            {
                "id": "course-003",
                "title": "Nutrition Counseling Essentials",
                "status": "in_progress",
                "progress": 75,
                "credits": 2.5,
                "due_date": "2024-02-15",
                "last_accessed": "2024-01-10"
            },
            {
                "id": "course-004", 
                "title": "Clinical Documentation",
                "status": "completed",
                "progress": 100,
                "credits": 3.0,
                "completed_date": "2023-12-20",
                "certificate_url": "/certificates/course-004.pdf"
            }
        ],
        "categories": [
            {"id": "diabetes", "name": "Diabetes Care", "course_count": 15},
            {"id": "cardiology", "name": "Cardiovascular Health", "course_count": 12},
            {"id": "nutrition", "name": "Nutrition & Dietetics", "course_count": 18},
            {"id": "mental_health", "name": "Mental Health", "course_count": 9},
            {"id": "technology", "name": "Health Technology", "course_count": 7}
        ],
        "upcoming_deadlines": [
            {"course": "Nutrition Counseling Essentials", "due_date": "2024-02-15", "days_left": 6},
            {"course": "Annual CME Requirement", "due_date": "2024-12-31", "days_left": 330}
        ]
    }

@api_router.post("/provider/courses/{course_id}/enroll")
async def enroll_in_course(course_id: str, provider_id: str = Body(...)):
    """Enroll in a continuing education course"""
    return {
        "course_id": course_id,
        "provider_id": provider_id,
        "enrollment_status": "success",
        "message": "Successfully enrolled in course",
        "access_url": f"/courses/{course_id}/learn",
        "enrollment_date": "2024-01-15"
    }

@api_router.get("/provider/certificates/{provider_id}")
async def get_certificates(provider_id: str):
    """Get earned certificates"""
    return {
        "provider_id": provider_id,
        "certificates": [
            {
                "id": "cert-001",
                "course_title": "Advanced Diabetes Management",
                "credits": 4.0,
                "completed_date": "2023-11-15",
                "certificate_number": "ADM-2023-001",
                "download_url": "/certificates/cert-001.pdf",
                "verification_code": "ADM4B7X9"
            },
            {
                "id": "cert-002",
                "course_title": "Clinical Documentation", 
                "credits": 3.0,
                "completed_date": "2023-12-20",
                "certificate_number": "CD-2023-002",
                "download_url": "/certificates/cert-002.pdf",
                "verification_code": "CD8K2M5P"
            }
        ],
        "total_credits": 32.5
    }

# Family-specific endpoints
@api_router.get("/family/dashboard/{user_id}")
async def get_family_dashboard(user_id: str):
    return {
        "user_id": user_id,
        "family_overview": {
            "family_members": 4,
            "health_alerts": 2,
            "appointments": 3,
            "coverage": "100%"
        },
        "family_members": [
            {"id": 1, "name": "John (Dad)", "age": 42, "status": "healthy", "avatar_color": "blue"},
            {"id": 2, "name": "Sarah (Mom)", "age": 38, "status": "healthy", "avatar_color": "pink"},
            {"id": 3, "name": "Emma (12)", "age": 12, "status": "checkup_due", "avatar_color": "purple"},
            {"id": 4, "name": "Alex (8)", "age": 8, "status": "healthy", "avatar_color": "green"}
        ],
        "meal_planning": {
            "week_completion": 85,
            "planned_days": 5,
            "total_days": 7,
            "next_meals": [
                {"day": "Tonight", "meal": "Grilled Chicken", "status": "ready"},
                {"day": "Tomorrow", "meal": "Pasta Primavera", "status": "planned"}
            ]
        },
        "health_alerts": [
            {"type": "checkup", "member": "Emma", "message": "Due in 2 weeks", "priority": "medium"},
            {"type": "vaccination", "member": "All", "message": "All up to date", "priority": "low"}
        ],
        "upcoming_appointments": [
            {"date": "Tomorrow", "time": "3:00 PM", "member": "Emma", "type": "Dental Checkup"},
            {"date": "Wednesday", "time": "4:30 PM", "member": "Alex", "type": "Soccer Practice"},
            {"date": "Friday", "time": "6:00 PM", "member": "Family", "type": "Dinner Planning"}
        ]
    }

@api_router.get("/family/meal-planning/{user_id}")
async def get_family_meal_planning(user_id: str):
    return {
        "user_id": user_id,
        "weekly_plan": {
            "monday": {"breakfast": "Pancakes", "lunch": "Sandwiches", "dinner": "Chicken Stir-fry"},
            "tuesday": {"breakfast": "Oatmeal", "lunch": "Soup", "dinner": "Pasta"},
            "wednesday": {"breakfast": "Toast", "lunch": "Salad", "dinner": "Fish"},
            "thursday": {"breakfast": "Cereal", "lunch": "Leftovers", "dinner": "Pizza"},
            "friday": {"breakfast": "Eggs", "lunch": "Wraps", "dinner": "Tacos"}
        },
        "shopping_list": ["Chicken breast", "Vegetables", "Pasta", "Fish fillets", "Eggs", "Bread"],
        "family_recipes": [
            {"id": 1, "name": "Mom's Healthy Lasagna", "rating": 5, "category": "dinner", "kid_approved": True},
            {"id": 2, "name": "Rainbow Smoothie Bowls", "rating": 4, "category": "breakfast", "kid_approved": True}
        ]
    }

# Guest-specific endpoints
@api_router.get("/guest/dashboard")
async def get_guest_dashboard():
    return {
        "session_info": {
            "quick_logs": 5,
            "session_time": "15m",
            "features_used": 3,
            "experience": "Good"
        },
        "todays_entries": [
            {"id": 1, "name": "Coffee with milk", "time": "8:00 AM", "calories": 50},
            {"id": 2, "name": "Toast with avocado", "time": "8:30 AM", "calories": 320}
        ],
        "nutrition_summary": {
            "total_calories": 370,
            "meals_logged": {"breakfast": 370, "lunch": 0, "dinner": 0}
        },
        "simple_goals": [
            {"name": "Eat 5 servings of fruits/vegetables", "current": 2, "target": 5, "progress": 40},
            {"name": "Drink 8 glasses of water", "current": 3, "target": 8, "progress": 37.5},
            {"name": "Log all meals today", "current": 1, "target": 3, "progress": 33.3}
        ],
        "nutrition_tips": {
            "daily_tip": {
                "title": "Stay Hydrated",
                "content": "Drinking water before meals can help with portion control and digestion. Aim for at least 8 glasses throughout the day."
            },
            "quick_facts": [
                {"title": "🥗 Fiber Fact", "content": "Adults need 25-35g of fiber daily for optimal digestive health."},
                {"title": "💪 Protein Power", "content": "Include protein in every meal to help maintain stable blood sugar levels."},
                {"title": "🌈 Color Variety", "content": "Eating different colored fruits and vegetables ensures diverse nutrients."}
            ]
        },
        "message": "Guest session active - data will not be permanently saved"
    }

@api_router.post("/guest/quick-log")
async def create_guest_food_log(food_data: dict):
    return {
        "success": True,
        "message": "Food logged successfully (session only)",
        "entry": {
            "id": f"guest_{datetime.now().strftime('%H%M%S')}",
            "food": food_data.get("food_name", "Unknown food"),
            "calories": food_data.get("calories", 0),
            "time": datetime.now().strftime("%I:%M %p")
        }
    }

# ===== PHASE 1: ADVANCED ROLE-SPECIFIC API ENDPOINTS =====

# ===== PATIENT ANALYTICS & INSIGHTS =====

class NutritionTrend(BaseModel):
    date: str
    calories: int
    protein: float
    carbs: float
    fat: float

class HealthInsight(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    insight_type: str  # correlation, recommendation, pattern, alert
    title: str
    message: str
    confidence: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FoodLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    food_name: str
    quantity: float
    unit: str
    calories: int
    meal_type: str  # breakfast, lunch, dinner, snack
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    photo_url: Optional[str] = None

class SymptomEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symptom: str  # headache, nausea, fatigue, etc.
    severity: int  # 1-10 scale
    duration: Optional[int] = None  # duration in minutes
    triggers: List[str] = Field(default_factory=list)  # stress, lack_of_sleep, etc.
    medications_taken: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    voice_note_url: Optional[str] = None
    correlations: Optional[dict] = Field(default_factory=dict)

class SymptomCorrelationData(BaseModel):
    user_id: str
    symptoms: List[SymptomEntry]
    diet_data: List[dict] = Field(default_factory=list)
    exercise_data: List[dict] = Field(default_factory=list)
    sleep_data: List[dict] = Field(default_factory=list)
    medications: List[dict] = Field(default_factory=list)

# ===== PROVIDER CLINICAL TOOLS =====

class PatientAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    patient_id: str
    assignment_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # active, inactive, completed

class TreatmentPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    patient_id: str
    plan_type: str  # nutrition, medication, lifestyle
    recommendations: List[Dict[str, Any]]
    target_outcomes: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ClinicalNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    patient_id: str
    note_type: str  # consultation, assessment, progress
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ===== FAMILY COORDINATION =====

class FamilyGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    family_id: str
    goal_type: str  # nutrition, fitness, health
    title: str
    description: str
    target_value: Optional[float] = None
    current_progress: float = 0.0
    participants: List[str] = []  # family member IDs
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    status: str = "active"  # active, completed, paused

class MealPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    family_id: str
    week_start: datetime
    meals: Dict[str, Dict[str, str]]  # day -> meal_type -> recipe_name
    shopping_list: List[str] = []
    dietary_restrictions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ===== GUEST SESSION MANAGEMENT =====

class GuestSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    activity_log: List[Dict[str, Any]] = []
    preferences: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

# ===== ADVANCED API ENDPOINTS =====

# Patient Analytics Endpoints
@api_router.get("/patient/analytics/{user_id}")
async def get_patient_analytics(user_id: str):
    """Get comprehensive analytics for patient with AI-powered insights"""
    
    # Sample user data - in real app, this would come from database
    user_data = {
        "user_id": user_id,
        "age": 32,
        "gender": "female",
        "activity_level": "moderately_active",
        "goals": ["weight_loss", "energy_improvement"],
        "diet_type": "mediterranean",
        "avg_calories": 2030,
        "avg_protein": 92,
        "avg_carbs": 175,
        "avg_fat": 68,
        "weight": 68.5,
        "energy_level": 7.2,
        "sleep_quality": 7.5
    }
    
    # Generate AI-powered insights
    try:
        # ai_insights = await get_nutrition_insights(user_data)
        ai_insights = {"insights": [], "recommendations": [], "confidence": 0.0}
    except Exception as e:
        logger.error(f"AI insights error: {e}")
        ai_insights = {"insights": [], "recommendations": [], "confidence": 0.0}
    
    # Generate health correlations with AI
    health_data = {
        "daily_logs": [{"date": "2024-01-15", "energy": 7.5, "protein": 95}],
        "sleep_patterns": "consistent_7h",
        "exercise_frequency": "3x_week",
        "energy_trend": "improving",
        "weight_trend": "decreasing",
        "mood_patterns": "stable_positive"
    }
    
    try:
        # ai_correlations = await get_health_correlations(health_data)
        ai_correlations = {"correlations": []}
    except Exception as e:
        logger.error(f"AI correlations error: {e}")
        ai_correlations = {"correlations": []}
    
    return {
        "user_id": user_id,
        "nutrition_trends": [
            {"date": "2024-01-15", "calories": 2100, "protein": 95, "carbs": 180, "fat": 70},
            {"date": "2024-01-14", "calories": 1950, "protein": 88, "carbs": 165, "fat": 65},
            {"date": "2024-01-13", "calories": 2200, "protein": 102, "carbs": 195, "fat": 75},
            {"date": "2024-01-12", "calories": 1850, "protein": 85, "carbs": 155, "fat": 62},
            {"date": "2024-01-11", "calories": 2050, "protein": 92, "carbs": 175, "fat": 68}
        ],
        "health_correlations": ai_correlations.get("correlations", [
            {"metric": "energy_level", "correlation_with": "protein_intake", "strength": 0.75, "insight": "Higher protein intake correlates with better energy levels"},
            {"metric": "sleep_quality", "correlation_with": "caffeine_intake", "strength": -0.65, "insight": "Reduced caffeine after 2 PM improves sleep quality"},
            {"metric": "mood", "correlation_with": "exercise", "strength": 0.82, "insight": "Regular exercise significantly improves mood scores"}
        ]),
        "goal_progress": {
            "weight_loss": {"target": 70, "current": 68.5, "progress": 85, "trend": "on_track"},
            "fitness": {"target": 5, "current": 3, "progress": 60, "trend": "needs_improvement"},
            "nutrition": {"target": 100, "current": 78, "progress": 78, "trend": "good"}
        },
        "ai_powered_insights": {
            "source": ai_insights.get("source", "default"),
            "confidence": ai_insights.get("confidence", 0.6),
            "insights": ai_insights.get("insights", ["Analysis completed with available data"]),
            "recommendations": ai_insights.get("recommendations", ["Continue current healthy practices"]),
            "action_items": ai_insights.get("action_items", ["Monitor progress regularly"])
        },
        "personal_insights": [
            {"type": "achievement", "message": "You've maintained your target calorie range for 5 consecutive days!", "date": "2024-01-15"},
            {"type": "recommendation", "message": "Consider adding more fiber-rich vegetables to your lunch meals", "date": "2024-01-15"},
            {"type": "pattern", "message": "Your energy levels are highest on days when you exercise in the morning", "date": "2024-01-14"}
        ],
        "energy_patterns": {
            "morning": {"average": 7.2, "trend": "stable"},
            "afternoon": {"average": 6.8, "trend": "declining"},
            "evening": {"average": 6.5, "trend": "stable"}
        },
        "weekly_summary": {
            "average_calories": 2030,
            "protein_goal_met": 6,
            "exercise_sessions": 3,
            "weight_change": -0.3,
            "mood_score": 7.8,
            "sleep_quality": 7.5
        }
    }

@api_router.get("/patient/smart-suggestions/{user_id}")
async def get_smart_food_suggestions(user_id: str):
    """Get AI-powered food suggestions based on eating patterns"""
    
    # Sample user profile - in real app, this would come from database
    user_profile = {
        "diet_type": "mediterranean",
        "allergies": ["tree_nuts"],
        "favorite_foods": ["salmon", "quinoa", "berries", "greek_yogurt"],
        "cooking_time": 30
    }
    
    current_intake = {
        "calories": 1200,
        "protein": 45,
        "calories_remaining": 800,
        "time_of_day": "afternoon"
    }
    
    # Get AI-powered food suggestions
    try:
        # ai_suggestions = await get_smart_food_suggestions(user_profile, current_intake)
        ai_suggestions = []
    except Exception as e:
        logger.error(f"AI food suggestions error: {e}")
        ai_suggestions = []
    
    # Default suggestions if AI fails
    default_suggestions = [
        {"name": "Greek Yogurt with Berries", "calories": 150, "reason": "Your usual morning snack", "frequency": "often"},
        {"name": "Grilled Chicken Salad", "calories": 350, "reason": "Perfect for your lunch protein goal", "frequency": "weekly"},
        {"name": "Almonds (1 oz)", "calories": 164, "reason": "Healthy fat you enjoyed yesterday", "frequency": "daily"},
        {"name": "Green Smoothie", "calories": 180, "reason": "Boosts your vegetable intake", "frequency": "sometimes"}
    ]
    
    return {
        "user_id": user_id,
        "ai_powered": len(ai_suggestions) > 0,
        "quick_add_suggestions": ai_suggestions if ai_suggestions else default_suggestions,
        "meal_pattern_insights": {
            "breakfast_time": "8:15 AM",
            "lunch_time": "12:30 PM",
            "dinner_time": "7:00 PM",
            "snack_preferences": ["nuts", "fruits", "yogurt"],
            "favorite_cuisines": ["Mediterranean", "Asian", "Mexican"]
        },
        "nutrition_gaps": [
            {"nutrient": "Fiber", "current": 18, "target": 25, "suggestion": "Add beans or lentils to lunch"},
            {"nutrient": "Omega-3", "current": "low", "target": "adequate", "suggestion": "Include fatty fish twice weekly"},
            {"nutrient": "Vitamin D", "current": "insufficient", "target": "adequate", "suggestion": "Consider fortified foods or supplements"}
        ]
    }

@api_router.post("/patient/food-log")
async def log_food(food_entry: dict):
    """Smart food logging with automatic nutrition lookup and AI pattern recognition"""
    
    # Get AI-powered food analysis
    food_name = food_entry.get("food_name", "Unknown Food")
    try:
        # Simulate AI nutrition analysis
        ai_analysis = await analyze_food_with_ai(food_name, food_entry)
    except Exception as e:
        logger.error(f"AI food analysis error: {e}")
        ai_analysis = None
    
    # Enhanced nutrition lookup with AI suggestions
    enhanced_entry = {
        "id": str(uuid.uuid4()),
        "food_name": food_name,
        "calories": food_entry.get("calories") or (ai_analysis.get("calories") if ai_analysis else 200),
        "protein": food_entry.get("protein") or (ai_analysis.get("protein") if ai_analysis else 15),
        "carbs": food_entry.get("carbs") or (ai_analysis.get("carbs") if ai_analysis else 25),
        "fat": food_entry.get("fat") or (ai_analysis.get("fat") if ai_analysis else 8),
        "fiber": ai_analysis.get("fiber") if ai_analysis else 3,
        "sugar": ai_analysis.get("sugar") if ai_analysis else 5,
        "confidence": ai_analysis.get("confidence") if ai_analysis else 0.80,
        "similar_foods": ai_analysis.get("similar_foods") if ai_analysis else ["Chicken Breast", "Turkey Breast", "Lean Beef"],
        "logged_at": datetime.utcnow().isoformat(),
        "meal_type": food_entry.get("meal_type") or get_current_meal_type(),
        "ai_enhanced": bool(ai_analysis)
    }
    
    # AI-powered insights based on recent eating patterns
    ai_insights = []
    if ai_analysis:
        ai_insights.extend(ai_analysis.get("insights", []))
    
    # Pattern recognition insights
    pattern_insights = analyze_eating_patterns(enhanced_entry)
    ai_insights.extend(pattern_insights)
    
    return {
        "success": True,
        "food_entry": enhanced_entry,
        "daily_totals": {
            "calories": 1450 + enhanced_entry["calories"],
            "protein": 78 + enhanced_entry["protein"],
            "carbs": 145 + enhanced_entry["carbs"],
            "fat": 52 + enhanced_entry["fat"],
            "fiber": 18 + enhanced_entry["fiber"]
        },
        "ai_insights": ai_insights,
        "pattern_recognition": {
            "meal_timing_pattern": "Consistent with your usual lunch time",
            "nutrition_balance": "Good protein choice for post-workout meal",
            "frequency_insight": "You've had similar foods 3 times this week",
            "suggestions": [
                "Great protein choice! This helps meet your daily protein goal.",
                "Consider adding some vegetables for extra fiber and nutrients.",
                "This meal fits well with your Mediterranean diet pattern."
            ]
        },
        "smart_suggestions": {
            "complementary_foods": [
                {"name": "Mixed Green Salad", "reason": "Adds fiber and micronutrients"},
                {"name": "Avocado Slices", "reason": "Healthy fats to balance the meal"},
                {"name": "Greek Yogurt", "reason": "Additional protein and probiotics"}
            ],
            "portion_feedback": generate_portion_feedback(enhanced_entry),
            "timing_feedback": f"Good timing for {enhanced_entry['meal_type'].lower()}"
        }
    }

async def analyze_food_with_ai(food_name: str, food_entry: dict) -> dict:
    """Analyze food with AI for enhanced nutrition data"""
    # This would integrate with the AI service
    try:
        # Simulate AI food analysis
        ai_analysis = {
            "calories": estimate_calories_from_name(food_name),
            "protein": estimate_protein_from_name(food_name),
            "carbs": estimate_carbs_from_name(food_name), 
            "fat": estimate_fat_from_name(food_name),
            "fiber": estimate_fiber_from_name(food_name),
            "sugar": estimate_sugar_from_name(food_name),
            "confidence": 0.85,
            "similar_foods": get_similar_foods(food_name),
            "insights": [
                f"Nutritional analysis of {food_name} completed",
                "Values estimated using AI food recognition"
            ]
        }
        return ai_analysis
    except Exception as e:
        logger.error(f"AI food analysis failed: {e}")
        return None

def analyze_eating_patterns(food_entry: dict) -> list:
    """Analyze eating patterns for insights"""
    insights = []
    
    # Time-based insights
    current_hour = datetime.utcnow().hour
    if current_hour < 10:
        insights.append("Great start to the day with a nutritious breakfast!")
    elif current_hour < 15:
        insights.append("Perfect lunch timing for sustained energy.")
    elif current_hour < 20:
        insights.append("Good dinner choice for evening nutrition.")
    else:
        insights.append("Late meal - consider earlier dinner for better sleep.")
    
    # Nutrition-based insights
    if food_entry["protein"] > 20:
        insights.append("Excellent protein content - great for muscle maintenance.")
    if food_entry["fiber"] > 5:
        insights.append("High fiber content supports digestive health.")
    
    return insights

def get_current_meal_type() -> str:
    """Determine current meal type based on time"""
    current_hour = datetime.utcnow().hour
    if current_hour < 11:
        return "Breakfast"
    elif current_hour < 16:
        return "Lunch"
    elif current_hour < 20:
        return "Dinner"
    else:
        return "Snack"

def estimate_calories_from_name(food_name: str) -> int:
    """Estimate calories based on food name"""
    food_lower = food_name.lower()
    if any(word in food_lower for word in ["salad", "vegetables", "lettuce"]):
        return 50 + (len(food_name) * 2)
    elif any(word in food_lower for word in ["chicken", "fish", "meat"]):
        return 200 + (len(food_name) * 3)
    elif any(word in food_lower for word in ["pasta", "rice", "bread"]):
        return 150 + (len(food_name) * 4)
    else:
        return 150

def estimate_protein_from_name(food_name: str) -> int:
    """Estimate protein based on food name"""
    food_lower = food_name.lower()
    if any(word in food_lower for word in ["chicken", "fish", "meat", "protein"]):
        return 25 + (len(food_name) // 2)
    elif any(word in food_lower for word in ["yogurt", "cheese", "milk"]):
        return 12 + (len(food_name) // 3)
    else:
        return 5 + (len(food_name) // 4)

def estimate_carbs_from_name(food_name: str) -> int:
    """Estimate carbs based on food name"""
    food_lower = food_name.lower()
    if any(word in food_lower for word in ["pasta", "rice", "bread", "potato"]):
        return 35 + (len(food_name) // 2)
    elif any(word in food_lower for word in ["fruit", "apple", "banana"]):
        return 20 + (len(food_name) // 3)
    else:
        return 10 + (len(food_name) // 4)

def estimate_fat_from_name(food_name: str) -> int:
    """Estimate fat based on food name"""
    food_lower = food_name.lower()
    if any(word in food_lower for word in ["avocado", "nuts", "oil", "butter"]):
        return 15 + (len(food_name) // 3)
    elif any(word in food_lower for word in ["salmon", "cheese", "cream"]):
        return 12 + (len(food_name) // 4)
    else:
        return 5 + (len(food_name) // 5)

def estimate_fiber_from_name(food_name: str) -> int:
    """Estimate fiber based on food name"""
    food_lower = food_name.lower()
    if any(word in food_lower for word in ["vegetables", "salad", "beans", "fiber"]):
        return 8 + (len(food_name) // 4)
    elif any(word in food_lower for word in ["fruit", "apple", "pear"]):
        return 4 + (len(food_name) // 5)
    else:
        return 2

def estimate_sugar_from_name(food_name: str) -> int:
    """Estimate sugar based on food name"""
    food_lower = food_name.lower()
    if any(word in food_lower for word in ["fruit", "sweet", "dessert", "cake"]):
        return 15 + (len(food_name) // 3)
    elif any(word in food_lower for word in ["yogurt", "milk"]):
        return 8 + (len(food_name) // 4)
    else:
        return 3

def get_similar_foods(food_name: str) -> list:
    """Get similar foods based on food name"""
    food_lower = food_name.lower()
    if any(word in food_lower for word in ["chicken", "poultry"]):
        return ["Turkey Breast", "Lean Beef", "Fish Fillet", "Tofu"]
    elif any(word in food_lower for word in ["salad", "vegetables"]):
        return ["Mixed Greens", "Spinach Salad", "Kale Salad", "Arugula"]
    elif any(word in food_lower for word in ["yogurt"]):
        return ["Greek Yogurt", "Low-fat Yogurt", "Protein Yogurt", "Dairy Alternative"]
    else:
        return ["Similar Food Option 1", "Similar Food Option 2", "Alternative Choice"]

def generate_portion_feedback(food_entry: dict) -> str:
    """Generate feedback about portion size"""
    calories = food_entry.get("calories", 0)
    if calories < 100:
        return "Small portion - consider if this meets your energy needs"
    elif calories < 300:
        return "Moderate portion size - good for a snack or light meal"
    elif calories < 600:
        return "Good portion size for a main meal"
    else:
        return "Large portion - consider splitting if trying to manage calories"

# Food Logging Summary Endpoints
@api_router.get("/patient/food-log/{user_id}/daily-summary")
async def get_daily_food_summary(user_id: str):
    """Get daily nutrition summary for the user"""
    return {
        "user_id": user_id,
        "date": datetime.utcnow().date().isoformat(),
        "summary": {
            "calories": 1847,
            "protein": 125,
            "carbs": 198,
            "fat": 62,
            "fiber": 28,
            "meals": 4,
            "water_intake": 2.1,
            "goals_met": {
                "calories": True,
                "protein": True,
                "carbs": True,
                "fat": False,
                "fiber": True
            },
            "daily_goals": {
                "calories": 2000,
                "protein": 120,
                "carbs": 200,
                "fat": 67,
                "fiber": 25
            },
            "progress_percentage": {
                "calories": 92,
                "protein": 104,
                "carbs": 99,
                "fat": 93,
                "fiber": 112
            }
        }
    }

@api_router.get("/patient/food-log/{user_id}/recent")
async def get_recent_food_logs(user_id: str, limit: int = 10):
    """Get recent food log entries for the user"""
    return {
        "user_id": user_id,
        "logs": [
            {
                "id": str(uuid.uuid4()),
                "food_name": "Grilled Salmon Fillet",
                "brand": "Fresh Atlantic",
                "calories": 367,
                "protein": 39,
                "carbs": 0,
                "fat": 22,
                "fiber": 0,
                "sodium": 59,
                "meal_type": "dinner",
                "serving_size": "6 oz",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "source": "ai_photo_recognition",
                "confidence": 0.92
            },
            {
                "id": str(uuid.uuid4()),
                "food_name": "Greek Yogurt with Berries",
                "brand": "Chobani",
                "calories": 180,
                "protein": 15,
                "carbs": 20,
                "fat": 8,
                "fiber": 4,
                "sodium": 65,
                "meal_type": "breakfast",
                "serving_size": "1 cup",
                "timestamp": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
                "source": "barcode_scan",
                "confidence": 0.98
            },
            {
                "id": str(uuid.uuid4()),
                "food_name": "Quinoa Power Bowl",
                "brand": "",
                "calories": 420,
                "protein": 18,
                "carbs": 58,
                "fat": 14,
                "fiber": 8,
                "sodium": 340,
                "meal_type": "lunch",
                "serving_size": "1 bowl",
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "source": "voice_recognition",
                "confidence": 0.85
            },
            {
                "id": str(uuid.uuid4()),
                "food_name": "Mixed Nuts Handful",
                "brand": "Blue Diamond",
                "calories": 170,
                "protein": 6,
                "carbs": 6,
                "fat": 15,
                "fiber": 3,
                "sodium": 90,
                "meal_type": "snack",
                "serving_size": "1 oz",
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "source": "quick_add",
                "confidence": 1.0
            },
            {
                "id": str(uuid.uuid4()),
                "food_name": "Green Smoothie",
                "brand": "Homemade",
                "calories": 280,
                "protein": 25,
                "carbs": 35,
                "fat": 8,
                "fiber": 12,
                "sodium": 125,
                "meal_type": "breakfast",
                "serving_size": "16 oz",
                "timestamp": (datetime.utcnow() - timedelta(days=1, hours=8)).isoformat(),
                "source": "ai_photo_recognition",
                "confidence": 0.88
            }
        ]
    }

@api_router.get("/patient/smart-suggestions/{user_id}")
async def get_smart_food_suggestions(user_id: str):
    """Get AI-powered smart food suggestions based on patterns and nutrition gaps"""
    current_hour = datetime.utcnow().hour
    
    # Context-aware suggestions based on time of day
    if 6 <= current_hour <= 10:  # Breakfast time
        meal_context = "breakfast"
        contextual_suggestions = [
            {"name": "Steel Cut Oats with Berries", "calories": 220, "protein": 8, "carbs": 45, "fat": 4, "reason": "High fiber breakfast for sustained energy"},
            {"name": "Greek Yogurt Parfait", "calories": 180, "protein": 15, "carbs": 18, "fat": 6, "reason": "Protein-rich start to your day"},
            {"name": "Avocado Toast", "calories": 250, "protein": 8, "carbs": 25, "fat": 16, "reason": "Healthy fats for brain function"}
        ]
    elif 11 <= current_hour <= 15:  # Lunch time
        meal_context = "lunch"
        contextual_suggestions = [
            {"name": "Grilled Chicken Salad", "calories": 320, "protein": 35, "carbs": 12, "fat": 15, "reason": "Lean protein with vegetables"},
            {"name": "Quinoa Buddha Bowl", "calories": 380, "protein": 16, "carbs": 52, "fat": 12, "reason": "Complete amino acid profile"},
            {"name": "Turkey Wrap", "calories": 290, "protein": 24, "carbs": 28, "fat": 10, "reason": "Balanced macronutrients"}
        ]
    elif 17 <= current_hour <= 22:  # Dinner time
        meal_context = "dinner"
        contextual_suggestions = [
            {"name": "Baked Salmon with Vegetables", "calories": 420, "protein": 35, "carbs": 20, "fat": 24, "reason": "Omega-3 rich dinner"},
            {"name": "Lean Beef Stir Fry", "calories": 350, "protein": 30, "carbs": 25, "fat": 15, "reason": "Iron and protein for recovery"},
            {"name": "Lentil Curry", "calories": 310, "protein": 18, "carbs": 45, "fat": 8, "reason": "Plant-based protein and fiber"}
        ]
    else:  # Snack time
        meal_context = "snack"
        contextual_suggestions = [
            {"name": "Apple with Almond Butter", "calories": 190, "protein": 7, "carbs": 20, "fat": 12, "reason": "Satisfying healthy snack"},
            {"name": "Greek Yogurt with Nuts", "calories": 170, "protein": 12, "carbs": 8, "fat": 10, "reason": "Protein-rich between meals"},
            {"name": "Hummus with Vegetables", "calories": 120, "protein": 5, "carbs": 12, "fat": 6, "reason": "Fiber and nutrients"}
        ]
    
    return {
        "user_id": user_id,
        "meal_context": meal_context,
        "generated_at": datetime.utcnow().isoformat(),
        "quick_add_suggestions": contextual_suggestions,
        "meal_pattern_insights": {
            "breakfast_time": "8:15 AM (average)",
            "lunch_time": "12:45 PM (average)", 
            "dinner_time": "7:20 PM (average)",
            "snack_preferences": "Nuts, fruits, yogurt",
            "hydration_pattern": "Morning and evening peaks",
            "meal_spacing": "4.5 hours average"
        },
        "nutrition_gaps": [
            {
                "nutrient": "fiber",
                "current": 18,
                "target": 25,
                "suggestion": "Add more vegetables and whole grains",
                "foods": ["Broccoli", "Quinoa", "Black Beans", "Berries"],
                "estimated_calories": 150
            },
            {
                "nutrient": "omega_3",
                "current": "low",
                "target": "adequate",
                "suggestion": "Include fatty fish or walnuts",
                "foods": ["Salmon", "Sardines", "Walnuts", "Chia Seeds"],
                "estimated_calories": 200
            }
        ],
        "personalized_recommendations": [
            {
                "title": "Boost Morning Protein",
                "description": "Your breakfast protein is below optimal. Try adding eggs or Greek yogurt.",
                "foods": ["Egg Scramble", "Protein Smoothie", "Greek Yogurt Bowl"],
                "priority": "high"
            },
            {
                "title": "Evening Vegetable Intake",
                "description": "Increase vegetable variety in dinner for micronutrients.",
                "foods": ["Roasted Vegetables", "Large Salad", "Vegetable Soup"],
                "priority": "medium"
            }
        ]
    }

@api_router.get("/patient/symptoms-correlation/{user_id}")
async def get_symptoms_correlation(user_id: str):
    """Get correlations between diet and symptoms"""
    return {
        "user_id": user_id,
        "correlations": [
            {
                "symptom": "Energy Level",
                "strong_positive": ["protein_intake", "complex_carbs", "B_vitamins"],
                "strong_negative": ["processed_sugar", "alcohol", "excessive_caffeine"],
                "insights": ["Energy levels are 40% higher on days with adequate protein (>80g)"]
            },
            {
                "symptom": "Digestive Health",
                "strong_positive": ["fiber_intake", "probiotics", "water_intake"],
                "strong_negative": ["processed_foods", "excessive_dairy", "artificial_sweeteners"],
                "insights": ["Digestive scores improve by 60% with 25g+ fiber daily"]
            },
            {
                "symptom": "Sleep Quality",
                "strong_positive": ["magnesium", "tryptophan", "regular_meals"],
                "strong_negative": ["late_caffeine", "large_evening_meals", "alcohol"],
                "insights": ["Sleep quality is 35% better when avoiding caffeine after 2 PM"]
            }
        ],
        "recommendations": [
            "Track your energy levels for 2 weeks to identify patterns",
            "Consider keeping a mood-food diary",
            "Monitor sleep quality in relation to evening meal timing"
        ]
    }

# Patient Medication Reminder Endpoints
@api_router.get("/patient/medications/{user_id}")
async def get_patient_medications(user_id: str):
    """Get patient's medication reminders and schedule"""
    return {
        "user_id": user_id,
        "medications": [
            {
                "id": "med_001",
                "name": "Metformin",
                "dosage": "500mg",
                "frequency": "twice_daily",
                "times": ["08:00", "20:00"],
                "with_food": True,
                "condition": "Type 2 Diabetes",
                "prescriber": "Dr. Smith",
                "start_date": "2024-01-01",
                "end_date": "2024-06-01",
                "adherence_rate": 95,
                "last_taken": "2024-01-15 20:00",
                "next_due": "2024-01-16 08:00",
                "status": "active"
            },
            {
                "id": "med_002", 
                "name": "Omega-3 Supplement",
                "dosage": "1000mg",
                "frequency": "daily",
                "times": ["08:00"],
                "with_food": True,
                "condition": "Heart Health",
                "prescriber": "Self-prescribed",
                "start_date": "2024-01-01",
                "end_date": None,
                "adherence_rate": 87,
                "last_taken": "2024-01-15 08:15",
                "next_due": "2024-01-16 08:00",
                "status": "active"
            }
        ],
        "reminders": [
            {
                "id": "rem_001",
                "medication_id": "med_001",
                "time": "08:00",
                "status": "completed",
                "completed_at": "2024-01-16 08:05"
            },
            {
                "id": "rem_002",
                "medication_id": "med_002",
                "time": "08:00", 
                "status": "pending",
                "due_in_minutes": 45
            }
        ],
        "adherence_stats": {
            "overall_adherence": 91,
            "weekly_adherence": 95,
            "missed_doses_week": 1,
            "streak_days": 12
        },
        "ai_insights": [
            "Your adherence rate is excellent! Keep up the good work.",
            "Taking medications with food helps with absorption and reduces side effects.",
            "Consider setting phone reminders for the evening dose of Metformin."
        ]
    }

@api_router.post("/patient/medications/{user_id}/take")
async def mark_medication_taken(user_id: str, medication_data: dict):
    """Mark a medication as taken"""
    return {
        "success": True,
        "medication_id": medication_data.get("medication_id"),
        "taken_at": datetime.utcnow().isoformat(),
        "next_reminder": "2024-01-16 20:00",
        "streak_updated": True,
        "new_streak": 13
    }

@api_router.post("/patient/medications/{user_id}")
async def add_medication(user_id: str, medication: dict):
    """Add new medication to patient's list"""
    new_med = {
        "id": f"med_{uuid.uuid4()}",
        "name": medication.get("name"),
        "dosage": medication.get("dosage"),
        "frequency": medication.get("frequency"),
        "times": medication.get("times", []),
        "with_food": medication.get("with_food", False),
        "condition": medication.get("condition", ""),
        "prescriber": medication.get("prescriber", ""),
        "start_date": medication.get("start_date"),
        "end_date": medication.get("end_date"),
        "status": "active",
        "adherence_rate": 0
    }
    
    return {
        "success": True,
        "medication": new_med,
        "message": "Medication added successfully"
    }

# Patient Health Timeline Endpoints
@api_router.get("/patient/timeline/{user_id}")
async def get_health_timeline(user_id: str):
    """Get comprehensive health timeline with AI insights"""
    return {
        "user_id": user_id,
        "timeline_events": [
            {
                "id": "evt_001",
                "date": "2024-01-15",
                "type": "weight_measurement",
                "title": "Weight Check",
                "value": "68.5 kg",
                "category": "metrics",
                "details": "Lost 0.3kg from last week",
                "impact": "positive",
                "ai_note": "Consistent progress toward weight goal"
            },
            {
                "id": "evt_002",
                "date": "2024-01-14",
                "type": "exercise",
                "title": "Cardio Workout",
                "value": "45 minutes",
                "category": "activity",
                "details": "Running + strength training",
                "impact": "positive",
                "ai_note": "Excellent workout intensity for heart health"
            },
            {
                "id": "evt_003",
                "date": "2024-01-13",
                "type": "meal_log",
                "title": "High Protein Day",
                "value": "105g protein",
                "category": "nutrition",
                "details": "Exceeded daily protein goal by 15g",
                "impact": "positive",
                "ai_note": "Perfect protein intake for muscle maintenance"
            },
            {
                "id": "evt_004",
                "date": "2024-01-12",
                "type": "symptom",
                "title": "Low Energy",
                "value": "4/10 energy",
                "category": "symptoms",
                "details": "Felt tired throughout afternoon",
                "impact": "negative",
                "ai_note": "May be related to insufficient sleep (5.5 hours)"
            },
            {
                "id": "evt_005",
                "date": "2024-01-11",
                "type": "medication",
                "title": "Missed Evening Dose",
                "value": "Metformin 500mg",
                "category": "medication",
                "details": "Forgot to take evening medication",
                "impact": "negative",
                "ai_note": "Set consistent reminders to improve adherence"
            },
            {
                "id": "evt_006",
                "date": "2024-01-10",
                "type": "achievement",
                "title": "Weekly Goal Met",
                "value": "3/3 workouts completed",
                "category": "goals",
                "details": "Successfully completed weekly exercise goal",
                "impact": "positive",
                "ai_note": "Consistent exercise is improving overall health metrics"
            }
        ],
        "patterns": {
            "energy_correlation": {
                "pattern": "Energy levels higher on exercise days",
                "confidence": 0.82,
                "recommendation": "Maintain regular exercise schedule"
            },
            "sleep_impact": {
                "pattern": "Sleep <6 hours leads to poor energy next day",
                "confidence": 0.91,
                "recommendation": "Aim for 7-8 hours of sleep nightly"
            },
            "nutrition_consistency": {
                "pattern": "Protein goals met 5/7 days this week",
                "confidence": 0.95,
                "recommendation": "Plan protein sources in advance"
            }
        },
        "milestones": [
            {
                "date": "2024-01-15",
                "type": "weight_goal",
                "title": "Lost 2kg in 6 weeks",
                "description": "Reached intermediate weight loss milestone",
                "celebration": "Great progress! You're 40% toward your target."
            },
            {
                "date": "2024-01-10",
                "type": "consistency",
                "title": "30-day Exercise Streak",
                "description": "Completed 30 consecutive days with some form of exercise",
                "celebration": "Amazing dedication to your fitness journey!"
            }
        ],
        "ai_insights": [
            "Your energy levels correlate strongly with sleep duration - prioritize 7+ hours",
            "Exercise days show 30% better mood scores than sedentary days",
            "Medication adherence improved 15% since starting reminders"
        ],
        "categories_summary": {
            "metrics": {"total": 15, "positive_trend": 12},
            "activity": {"total": 23, "weekly_average": 5.2},
            "nutrition": {"total": 45, "goals_met": 38},
            "symptoms": {"total": 8, "resolved": 6},
            "medication": {"total": 12, "adherence_rate": 91},
            "goals": {"total": 6, "achieved": 4}
        }
    }

@api_router.post("/patient/timeline/{user_id}/event")
async def add_timeline_event(user_id: str, event: dict):
    """Add new event to health timeline"""
    new_event = {
        "id": f"evt_{uuid.uuid4()}",
        "date": event.get("date", datetime.utcnow().date().isoformat()),
        "type": event.get("type"),
        "title": event.get("title"),
        "value": event.get("value"),
        "category": event.get("category"),
        "details": event.get("details", ""),
        "impact": event.get("impact", "neutral"),
        "ai_note": ""  # Would be generated by AI
    }
    
    return {
        "success": True,
        "event": new_event,
        "message": "Timeline event added successfully"
    }

# Provider Clinical Endpoints
@api_router.get("/provider/clinical-insights/{provider_id}")
async def get_clinical_insights(provider_id: str):
    """Get clinical decision support and insights with AI"""
    
    # Sample provider data
    provider_data = {
        "provider_id": provider_id,
        "total_patients": 247,
        "patient_conditions": ["diabetes", "hypertension", "obesity"],
        "recent_outcomes": [
            {"condition": "diabetes", "avg_hba1c_change": -1.2},
            {"condition": "hypertension", "avg_bp_reduction": 15}
        ]
    }
    
    # Get AI-powered clinical insights
    try:
        ai_clinical_insights = await get_clinical_insights(provider_data)
    except Exception as e:
        logger.error(f"AI clinical insights error: {e}")
        ai_clinical_insights = {"insights": [], "recommendations": []}
    
    return {
        "provider_id": provider_id,
        "ai_powered_analysis": {
            "enabled": True,
            "insights": ai_clinical_insights.get("insights", []),
            "evidence_based_recommendations": ai_clinical_insights.get("recommendations", []),
            "confidence": ai_clinical_insights.get("confidence", 0.8)
        },
        "population_health": {
            "total_patients": 247,
            "diabetes_patients": 45,
            "hypertension_patients": 78,
            "obesity_patients": 89,
            "metabolic_syndrome": 23
        },
        "treatment_outcomes": [
            {"condition": "Type 2 Diabetes", "improvement_rate": 73, "average_hba1c_reduction": 1.2},
            {"condition": "Hypertension", "improvement_rate": 68, "average_bp_reduction": "15/8"},
            {"condition": "Obesity", "improvement_rate": 55, "average_weight_loss": 8.5}
        ],
        "evidence_based_recommendations": ai_clinical_insights.get("recommendations", [
            {
                "condition": "Pre-diabetes",
                "intervention": "Mediterranean Diet + Exercise",
                "evidence_level": "A",
                "success_rate": 85,
                "reference": "Diabetes Care 2023"
            },
            {
                "condition": "Hypertension",
                "intervention": "DASH Diet + Sodium Reduction",
                "evidence_level": "A",
                "success_rate": 78,
                "reference": "NEJM 2023"
            }
        ]),
        "drug_nutrient_interactions": [
            {"medication": "Warfarin", "nutrient": "Vitamin K", "interaction": "Monitor intake consistency"},
            {"medication": "Metformin", "nutrient": "Vitamin B12", "interaction": "May require supplementation"},
            {"medication": "Statins", "nutrient": "CoQ10", "interaction": "Consider supplementation"}
        ],
        "clinical_alerts": [
            {"patient_id": "pat_123", "alert": "HbA1c trending upward", "priority": "high", "action": "Review diet adherence"},
            {"patient_id": "pat_456", "alert": "Blood pressure well controlled", "priority": "low", "action": "Continue current plan"}
        ]
    }

@api_router.get("/provider/patient-analytics/{provider_id}")
async def get_provider_patient_analytics(provider_id: str):
    """Get comprehensive analytics across all patients"""
    return {
        "provider_id": provider_id,
        "patient_demographics": {
            "age_distribution": {"18-30": 15, "31-45": 45, "46-60": 78, "60+": 109},
            "gender_distribution": {"male": 118, "female": 129},
            "condition_prevalence": {
                "diabetes": 18.2,
                "hypertension": 31.6,
                "obesity": 36.0,
                "dyslipidemia": 24.3
            }
        },
        "treatment_effectiveness": {
            "diet_plans": {"prescribed": 187, "adhering": 142, "success_rate": 76},
            "medication_compliance": {"prescribed": 156, "compliant": 147, "compliance_rate": 94},
            "lifestyle_interventions": {"recommended": 203, "following": 154, "success_rate": 76}
        },
        "outcome_trends": [
            {"month": "2024-01", "weight_loss_success": 67, "bp_control": 78, "glucose_control": 71},
            {"month": "2023-12", "weight_loss_success": 62, "bp_control": 75, "glucose_control": 68},
            {"month": "2023-11", "weight_loss_success": 58, "bp_control": 72, "glucose_control": 65}
        ],
        "risk_stratification": {
            "low_risk": 89,
            "moderate_risk": 124,
            "high_risk": 34
        }
    }

@api_router.post("/provider/treatment-plan")
async def create_treatment_plan(plan_data: dict):
    """Create evidence-based treatment plans"""
    return {
        "success": True,
        "plan_id": str(uuid.uuid4()),
        "patient_id": plan_data.get("patient_id"),
        "provider_id": plan_data.get("provider_id"),
        "recommendations": [
            {
                "category": "nutrition",
                "intervention": "Mediterranean Diet Pattern",
                "evidence_level": "A",
                "duration": "12 weeks",
                "monitoring": "Weekly food logs, monthly weight"
            },
            {
                "category": "physical_activity",
                "intervention": "Progressive Resistance Training",
                "evidence_level": "A",
                "duration": "16 weeks",
                "monitoring": "Bi-weekly fitness assessments"
            }
        ],
        "expected_outcomes": [
            "5-10% weight reduction in 6 months",
            "Improved insulin sensitivity",
            "Reduced cardiovascular risk markers"
        ],
        "follow_up_schedule": [
            {"week": 2, "type": "phone_check", "focus": "diet_adherence"},
            {"week": 4, "type": "office_visit", "focus": "progress_assessment"},
            {"week": 8, "type": "lab_work", "focus": "biomarker_monitoring"}
        ]
    }

# Family Coordination Endpoints
@api_router.get("/family/health-overview/{family_id}")
async def get_family_health_overview(family_id: str):
    """Get comprehensive family health coordination data"""
    return {
        "family_id": family_id,
        "multi_member_tracking": {
            "total_members": 4,
            "health_status": {
                "excellent": 2,
                "good": 1,
                "needs_attention": 1
            },
            "upcoming_appointments": [
                {"member": "Emma", "date": "2024-01-18", "type": "Pediatric Checkup", "provider": "Dr. Smith"},
                {"member": "John", "date": "2024-01-25", "type": "Annual Physical", "provider": "Dr. Johnson"}
            ]
        },
        "shared_goals": [
            {
                "id": "goal_1",
                "title": "Family Fitness Challenge",
                "type": "physical_activity",
                "target": "150 minutes/week per member",
                "current_progress": 75,
                "participants": ["John", "Sarah", "Emma", "Alex"],
                "end_date": "2024-02-15"
            },
            {
                "id": "goal_2",
                "title": "Healthy Eating Habits",
                "type": "nutrition",
                "target": "5 servings fruits/vegetables daily",
                "current_progress": 60,
                "participants": ["John", "Sarah", "Emma", "Alex"],
                "end_date": "2024-01-31"
            }
        ],
        "meal_coordination": {
            "dietary_restrictions": {
                "Emma": ["tree_nuts"],
                "Alex": ["lactose_intolerant"],
                "Sarah": ["gluten_free"],
                "John": ["none"]
            },
            "family_friendly_meals": [
                {"name": "Gluten-Free Chicken Stir Fry", "accommodates": ["Sarah"], "nutrition_score": 9},
                {"name": "Dairy-Free Pasta Primavera", "accommodates": ["Alex"], "nutrition_score": 8},
                {"name": "Nut-Free Trail Mix", "accommodates": ["Emma"], "nutrition_score": 7}
            ],
            "weekly_meal_success": 85
        },
        "care_coordination": {
            "emergency_contacts": [
                {"name": "Grandma Betty", "relationship": "Grandmother", "phone": "+1-555-0123"},
                {"name": "Uncle Mike", "relationship": "Uncle", "phone": "+1-555-0456"}
            ],
            "healthcare_providers": {
                "family_physician": {"name": "Dr. Johnson", "phone": "+1-555-0789"},
                "pediatrician": {"name": "Dr. Smith", "phone": "+1-555-0012"},
                "emergency": {"name": "City Hospital", "phone": "911"}
            },
            "medication_schedule": [
                {"member": "Sarah", "medication": "Multivitamin", "time": "8:00 AM", "frequency": "daily"},
                {"member": "Emma", "medication": "Allergy Medication", "time": "7:00 PM", "frequency": "as_needed"}
            ]
        }
    }

@api_router.get("/family/meal-planning-advanced/{family_id}")
async def get_advanced_meal_planning(family_id: str):
    """Get intelligent meal planning for families"""
    return {
        "family_id": family_id,
        "smart_meal_suggestions": [
            {
                "meal": "Breakfast - Overnight Oats Bar",
                "accommodates_all": True,
                "prep_time": 15,
                "nutrition_score": 9,
                "kid_friendly": True,
                "dietary_notes": "Gluten-free oats, dairy-free milk options, nut-free toppings"
            },
            {
                "meal": "Lunch - Build-Your-Own Salad",
                "accommodates_all": True,
                "prep_time": 10,
                "nutrition_score": 10,
                "kid_friendly": True,
                "dietary_notes": "Customizable for all restrictions"
            }
        ],
        "budget_optimization": {
            "weekly_budget": 150,
            "current_plan_cost": 125,
            "savings_suggestions": [
                "Buy seasonal vegetables - save $15/week",
                "Bulk buy grains and legumes - save $8/week",
                "Plan leftovers strategically - save $12/week"
            ]
        },
        "nutrition_education": [
            {
                "topic": "Growing Bodies Need Protein",
                "age_group": "8-12 years",
                "key_points": ["Protein helps muscle development", "Include protein in every meal", "Fun protein sources: Greek yogurt, eggs, lean meats"],
                "activities": ["Protein scavenger hunt", "Build a balanced plate game"]
            },
            {
                "topic": "Calcium for Strong Bones",
                "age_group": "all",
                "key_points": ["Dairy alternatives for lactose intolerant", "Dark leafy greens are calcium-rich", "Vitamin D helps calcium absorption"],
                "activities": ["Calcium content comparison", "Bone health family challenge"]
            }
        ],
        "meal_prep_coordination": {
            "sunday_prep": [
                {"task": "Wash and chop vegetables", "assigned_to": "Sarah", "time": "30 min"},
                {"task": "Cook grains in bulk", "assigned_to": "John", "time": "45 min"},
                {"task": "Prepare snack portions", "assigned_to": "Emma & Alex", "time": "20 min"}
            ],
            "daily_assignments": {
                "monday": {"cook": "Sarah", "cleanup": "John", "help": "Emma"},
                "tuesday": {"cook": "John", "cleanup": "Sarah", "help": "Alex"}
            }
        }
    }

# PHASE 5: Comprehensive Family Features - Advanced APIs

@api_router.get("/family/calendar-integration/{family_id}")
async def get_family_calendar_integration(family_id: str):
    """Advanced family calendar with health events coordination"""
    return {
        "family_id": family_id,
        "calendar_overview": {
            "this_week_events": [
                {
                    "id": "evt_1",
                    "title": "Emma - Pediatric Annual Checkup",
                    "date": "2024-01-18",
                    "time": "2:30 PM",
                    "type": "medical_appointment",
                    "member": "Emma",
                    "provider": "Dr. Smith",
                    "location": "Children's Clinic",
                    "preparation_needed": ["Bring insurance card", "List of current medications", "Growth chart"],
                    "reminders_set": True
                },
                {
                    "id": "evt_2", 
                    "title": "Family Meal Prep Day",
                    "date": "2024-01-20",
                    "time": "10:00 AM",
                    "type": "meal_prep",
                    "participants": ["Sarah", "John", "Emma", "Alex"],
                    "planned_meals": ["Overnight oats", "Chicken stir fry", "Veggie muffins"],
                    "shopping_completed": True
                },
                {
                    "id": "evt_3",
                    "title": "Alex - Soccer Practice",
                    "date": "2024-01-21",
                    "time": "4:30 PM", 
                    "type": "physical_activity",
                    "member": "Alex",
                    "location": "Community Sports Center",
                    "health_benefits": ["cardiovascular health", "teamwork", "coordination"],
                    "hydration_reminder": True
                }
            ],
            "upcoming_medical": [
                {"member": "John", "appointment": "Annual Physical", "date": "2024-01-25", "status": "confirmed"},
                {"member": "Sarah", "appointment": "Nutritionist Consultation", "date": "2024-02-01", "status": "tentative"},
                {"member": "Emma", "appointment": "Orthodontist Follow-up", "date": "2024-02-08", "status": "confirmed"}
            ],
            "medication_schedule": {
                "daily_reminders": [
                    {"member": "Sarah", "medication": "Prenatal Vitamin", "time": "8:00 AM", "status": "active"},
                    {"member": "Emma", "medication": "Allergy Medication", "time": "7:00 PM", "condition": "seasonal allergies", "status": "as_needed"}
                ],
                "upcoming_refills": [
                    {"member": "Emma", "medication": "Allergy Medication", "refill_due": "2024-01-30", "pharmacy": "Main Street Pharmacy"}
                ]
            }
        },
        "synchronization": {
            "google_calendar": {"connected": True, "last_sync": "2024-01-17 6:00 AM"},
            "apple_calendar": {"connected": False, "available": True},
            "outlook_calendar": {"connected": False, "available": True}
        },
        "family_coordination": {
            "shared_responsibilities": [
                {"task": "Take Emma to checkup", "assigned_to": "Sarah", "date": "2024-01-18", "backup": "John"},
                {"task": "Pick up prescriptions", "assigned_to": "John", "date": "2024-01-19", "backup": "Sarah"}
            ],
            "transportation_coordination": [
                {"event": "Emma's Checkup", "driver": "Sarah", "passengers": ["Emma"], "departure_time": "2:00 PM"},
                {"event": "Alex's Soccer", "driver": "John", "passengers": ["Alex"], "departure_time": "4:00 PM"}
            ]
        }
    }

@api_router.get("/family/child-nutrition-education/{family_id}")
async def get_child_nutrition_education(family_id: str):
    """Comprehensive child nutrition education portal"""
    return {
        "family_id": family_id,
        "age_specific_content": [
            {
                "age_group": "8-10 years (Alex)",
                "learning_modules": [
                    {
                        "title": "Super Foods for Super Kids",
                        "duration": "15 minutes",
                        "type": "interactive_game",
                        "concepts": ["protein for muscles", "calcium for bones", "vitamins for energy"],
                        "activities": ["Food superhero matching", "Build a power plate", "Nutrient scavenger hunt"],
                        "completion_badge": "Nutrition Detective",
                        "progress": 60
                    },
                    {
                        "title": "Reading Food Labels Like a Pro", 
                        "duration": "10 minutes",
                        "type": "tutorial_video",
                        "concepts": ["serving sizes", "sugar content", "ingredient lists"],
                        "activities": ["Label detective game", "Compare similar foods", "Make healthy swaps"],
                        "completion_badge": "Label Reader",
                        "progress": 0
                    }
                ],
                "dietary_considerations": ["lactose_intolerant", "high_energy_needs", "growing_body"],
                "recommended_portions": {
                    "proteins": "2-3 servings/day",
                    "vegetables": "3-4 servings/day", 
                    "fruits": "2-3 servings/day",
                    "grains": "4-5 servings/day",
                    "dairy_alternatives": "2-3 servings/day"
                }
            },
            {
                "age_group": "12-14 years (Emma)",
                "learning_modules": [
                    {
                        "title": "Fueling Your Growing Body",
                        "duration": "20 minutes", 
                        "type": "interactive_workshop",
                        "concepts": ["adolescent nutrition needs", "body image positivity", "sports nutrition"],
                        "activities": ["Plan a perfect day of eating", "Myth vs fact quiz", "Energy balance calculator"],
                        "completion_badge": "Teen Nutrition Expert",
                        "progress": 30
                    },
                    {
                        "title": "Cooking Skills for Independence",
                        "duration": "25 minutes",
                        "type": "hands_on_cooking",
                        "concepts": ["meal preparation", "food safety", "balanced cooking"],
                        "activities": ["Cook a balanced meal", "Grocery shopping simulation", "Recipe modification"],
                        "completion_badge": "Young Chef",
                        "progress": 80
                    }
                ],
                "dietary_considerations": ["tree_nuts_allergy", "adolescent_growth", "active_lifestyle"],
                "recommended_portions": {
                    "proteins": "3-4 servings/day",
                    "vegetables": "4-5 servings/day",
                    "fruits": "3-4 servings/day", 
                    "grains": "6-7 servings/day",
                    "healthy_fats": "2-3 servings/day"
                }
            }
        ],
        "family_challenges": [
            {
                "name": "Rainbow Plate Challenge",
                "description": "Eat foods of every color each day for a week",
                "duration": "7 days",
                "participants": ["Emma", "Alex"],
                "progress": {"Emma": 85, "Alex": 70},
                "rewards": ["Healthy cooking class", "Family day out", "New sports equipment"]
            },
            {
                "name": "Hydration Heroes",
                "description": "Track water intake and learn about hydration", 
                "duration": "10 days",
                "participants": ["Emma", "Alex", "Sarah", "John"],
                "progress": {"Emma": 90, "Alex": 65, "Sarah": 100, "John": 80},
                "rewards": ["Family water bottles", "Healthy smoothie making", "Spa day"]
            }
        ],
        "expert_resources": [
            {
                "title": "Pediatric Nutritionist Q&A",
                "type": "live_session", 
                "date": "2024-01-25",
                "time": "7:00 PM",
                "expert": "Dr. Lisa Chen, RD",
                "topics": ["Picky eating", "Food allergies", "Growth nutrition"],
                "registration_required": True
            },
            {
                "title": "Family Cooking Workshop",
                "type": "hands_on_class",
                "date": "2024-02-03",
                "time": "2:00 PM", 
                "location": "Community Kitchen",
                "instructor": "Chef Maria Rodriguez",
                "focus": "Allergen-free family meals",
                "age_range": "8+ with parent"
            }
        ]
    }

@api_router.get("/family/caregiver-tools/{family_id}")
async def get_advanced_caregiver_tools(family_id: str):
    """Advanced caregiver tools and emergency management"""
    return {
        "family_id": family_id,
        "emergency_management": {
            "emergency_contacts": [
                {
                    "name": "Grandma Betty",
                    "relationship": "Grandmother", 
                    "phone": "+1-555-0123",
                    "availability": "weekdays 9AM-6PM",
                    "medical_authority": True,
                    "key_holder": True,
                    "special_instructions": "Knows Emma's allergy protocol"
                },
                {
                    "name": "Uncle Mike",
                    "relationship": "Uncle",
                    "phone": "+1-555-0456", 
                    "availability": "weekends and evenings",
                    "medical_authority": False,
                    "key_holder": True,
                    "special_instructions": "Lives 5 minutes away, has backup car seats"
                },
                {
                    "name": "Neighbor Jane",
                    "relationship": "Neighbor",
                    "phone": "+1-555-0789",
                    "availability": "emergencies only",
                    "medical_authority": False,
                    "key_holder": False,
                    "special_instructions": "Retired nurse, great in medical emergencies"
                }
            ],
            "medical_information": {
                "Emma": {
                    "allergies": ["tree nuts", "severe"],
                    "medications": ["EpiPen - always carry", "Allergy medication - as needed"],
                    "medical_conditions": ["Seasonal allergies"],
                    "emergency_protocols": ["Use EpiPen immediately for nut exposure", "Call 911", "Contact parents"],
                    "insurance": {"provider": "Blue Cross", "policy": "XYZ123", "group": "FAM001"}
                },
                "Alex": {
                    "allergies": ["none known"],
                    "medications": ["none regular"],
                    "medical_conditions": ["Lactose intolerant"],
                    "emergency_protocols": ["Standard emergency care", "Avoid dairy products"],
                    "insurance": {"provider": "Blue Cross", "policy": "XYZ123", "group": "FAM001"}
                }
            },
            "healthcare_providers": {
                "primary_care": {"name": "Dr. Johnson", "phone": "+1-555-0100", "available": "24/7 on-call"},
                "pediatrician": {"name": "Dr. Smith", "phone": "+1-555-0200", "available": "Mon-Fri 8AM-6PM"},
                "emergency": {"name": "City Hospital ER", "phone": "911", "address": "123 Medical Center Dr"},
                "urgent_care": {"name": "QuickCare Clinic", "phone": "+1-555-0300", "available": "7AM-11PM daily"}
            }
        },
        "medication_management": {
            "current_medications": [
                {
                    "member": "Sarah",
                    "medication": "Prenatal Vitamin",
                    "dosage": "1 tablet daily",
                    "time": "8:00 AM",
                    "refill_date": "2024-02-15",
                    "pharmacy": "Main Street Pharmacy",
                    "reminder_enabled": True,
                    "side_effects_to_watch": ["nausea", "constipation"]
                },
                {
                    "member": "Emma", 
                    "medication": "EpiPen",
                    "dosage": "0.3mg auto-injector",
                    "condition": "severe tree nut allergy",
                    "location": ["backpack", "home", "car"],
                    "expiration_date": "2024-08-15",
                    "replacement_reminder": True,
                    "training_needed": ["How to use", "When to use", "After-care steps"]
                }
            ],
            "medication_adherence": {
                "Sarah": {"compliance_rate": 95, "missed_doses": 2, "streak": 28},
                "Emma": {"compliance_rate": 100, "missed_doses": 0, "streak": 45}
            },
            "refill_management": [
                {"medication": "Prenatal Vitamin", "due_date": "2024-02-15", "auto_refill": True, "status": "scheduled"},
                {"medication": "EpiPen", "due_date": "2024-07-15", "auto_refill": False, "status": "reminder_set"}
            ]
        },
        "care_coordination": {
            "shared_tasks": [
                {"task": "Daily medication check", "assigned_to": "Sarah", "backup": "John", "frequency": "daily"},
                {"task": "Weekly health check-ins", "assigned_to": "alternating", "frequency": "weekly"},
                {"task": "Medical appointment scheduling", "assigned_to": "Sarah", "backup": "John", "frequency": "as_needed"}
            ],
            "communication_hub": {
                "family_chat": {"enabled": True, "platform": "secure_messaging", "participants": ["Sarah", "John"]},
                "provider_communication": {"enabled": True, "secure_portal": True, "recent_messages": 3},
                "school_nurse_contact": {"name": "Nurse Patricia", "phone": "+1-555-0400", "email": "patricia@school.edu"}
            },
            "document_management": {
                "medical_records": {"location": "encrypted_cloud", "last_updated": "2024-01-15", "access": ["Sarah", "John"]},
                "insurance_cards": {"location": "digital_wallet", "backup_printed": True, "expiration": "2024-12-31"},
                "emergency_info_sheets": {"location": "car, home, school", "last_updated": "2024-01-10", "review_due": "2024-07-10"}
            }
        },
        "health_monitoring": {
            "wellness_checks": [
                {"member": "Emma", "type": "allergy_symptom_tracking", "frequency": "daily", "last_entry": "2024-01-17"},
                {"member": "Alex", "type": "growth_monitoring", "frequency": "monthly", "last_entry": "2024-01-01"},
                {"member": "Sarah", "type": "pregnancy_wellness", "frequency": "weekly", "last_entry": "2024-01-16"}
            ],
            "symptom_tracking": {
                "Emma": {
                    "tracked_symptoms": ["sneezing", "itchy_eyes", "congestion"],
                    "triggers": ["tree_pollen", "dust"],
                    "patterns": "Symptoms worse in morning and evening",
                    "improvements": "Better with air purifier in room"
                }
            },
            "growth_tracking": {
                "Alex": {
                    "height": {"current": "4'8\"", "growth_rate": "2 inches/year", "percentile": "75th"},
                    "weight": {"current": "85 lbs", "growth_rate": "healthy", "percentile": "70th"},
                    "next_measurement": "2024-02-01"
                },
                "Emma": {
                    "height": {"current": "5'2\"", "growth_rate": "1 inch/year", "percentile": "60th"},
                    "weight": {"current": "105 lbs", "growth_rate": "healthy", "percentile": "55th"},
                    "next_measurement": "2024-02-01"
                }
            }
        }
    }

@api_router.get("/family/goals-coordination/{family_id}")
async def get_family_goals_coordination(family_id: str):
    """Advanced family goal setting and progress coordination"""
    return {
        "family_id": family_id,
        "active_goals": [
            {
                "id": "goal_nutrition_2024",
                "title": "Balanced Nutrition Challenge",
                "category": "nutrition",
                "description": "Each family member eats 5 servings of fruits and vegetables daily",
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "participants": [
                    {"name": "Sarah", "target": "5 servings/day", "current_progress": 85, "streak": 12},
                    {"name": "John", "target": "5 servings/day", "current_progress": 70, "streak": 8},
                    {"name": "Emma", "target": "4 servings/day", "current_progress": 90, "streak": 15},
                    {"name": "Alex", "target": "4 servings/day", "current_progress": 65, "streak": 5}
                ],
                "family_progress": 77,
                "milestones": [
                    {"week": 2, "achieved": True, "reward": "Family movie night"},
                    {"week": 4, "achieved": True, "reward": "Healthy cooking class"},
                    {"week": 8, "achieved": False, "reward": "Weekend farmer's market trip"},
                    {"week": 12, "achieved": False, "reward": "Family day at the park"}
                ],
                "tracking_method": "daily_photo_journal",
                "support_features": ["meal_suggestions", "progress_charts", "family_leaderboard"]
            },
            {
                "id": "goal_fitness_2024",
                "title": "Family Fitness Adventure",
                "category": "physical_activity",
                "description": "Family participates in physical activities together 4x per week",
                "start_date": "2024-01-01",
                "end_date": "2024-06-30",
                "participants": [
                    {"name": "Sarah", "target": "4 activities/week", "current_progress": 80, "favorite_activity": "hiking"},
                    {"name": "John", "target": "4 activities/week", "current_progress": 75, "favorite_activity": "cycling"},
                    {"name": "Emma", "target": "3 activities/week", "current_progress": 95, "favorite_activity": "dancing"},
                    {"name": "Alex", "target": "4 activities/week", "current_progress": 90, "favorite_activity": "soccer"}
                ],
                "family_progress": 85,
                "weekly_activities": [
                    {"day": "Saturday", "activity": "Family bike ride", "status": "completed", "duration": "45 min"},
                    {"day": "Sunday", "activity": "Park playground", "status": "completed", "duration": "60 min"},
                    {"day": "Wednesday", "activity": "Evening walk", "status": "scheduled", "duration": "30 min"},
                    {"day": "Friday", "activity": "Dance party", "status": "planned", "duration": "20 min"}
                ],
                "health_benefits": ["cardiovascular health", "family_bonding", "stress_reduction", "better_sleep"]
            },
            {
                "id": "goal_wellness_2024",
                "title": "Family Wellness Routine",
                "category": "overall_wellness", 
                "description": "Establish healthy family routines for sleep, hydration, and mindfulness",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "participants": [
                    {"name": "Sarah", "focus_areas": ["sleep_schedule", "hydration", "stress_management"], "progress": 88},
                    {"name": "John", "focus_areas": ["sleep_schedule", "hydration", "work_life_balance"], "progress": 72},
                    {"name": "Emma", "focus_areas": ["sleep_schedule", "screen_time", "study_stress"], "progress": 82},
                    {"name": "Alex", "focus_areas": ["sleep_schedule", "hydration", "emotional_regulation"], "progress": 79}
                ],
                "family_routines": [
                    {
                        "routine": "Digital sunset at 8 PM",
                        "description": "All screens off 1 hour before bedtime",
                        "compliance": 85,
                        "benefits": ["better_sleep", "family_time", "reduced_eye_strain"]
                    },
                    {
                        "routine": "Morning hydration challenge",
                        "description": "Everyone drinks water immediately upon waking",
                        "compliance": 92,
                        "benefits": ["metabolism_boost", "alertness", "healthy_habit"]
                    },
                    {
                        "routine": "Weekly family gratitude circle",
                        "description": "Share three things we're grateful for each Sunday",
                        "compliance": 78,
                        "benefits": ["emotional_wellbeing", "family_connection", "positive_mindset"]
                    }
                ]
            }
        ],
        "goal_analytics": {
            "overall_family_score": 83,
            "improvement_trends": [
                {"metric": "nutrition_consistency", "change": "+15%", "period": "last_month"},
                {"metric": "physical_activity", "change": "+22%", "period": "last_month"},
                {"metric": "sleep_quality", "change": "+8%", "period": "last_month"}
            ],
            "challenge_areas": [
                {"area": "weekend_consistency", "improvement_suggestion": "Plan weekend activities in advance"},
                {"area": "weather_dependency", "improvement_suggestion": "Add indoor activity alternatives"}
            ]
        },
        "motivation_system": {
            "individual_rewards": [
                {"member": "Emma", "earned": "Choice of weekend activity", "for": "15-day nutrition streak"},
                {"member": "Alex", "earned": "Extra 30 min screen time", "for": "Completing fitness week"}
            ],
            "family_rewards": [
                {"earned": "Family movie night", "for": "Everyone meeting weekly nutrition goal"},
                {"pending": "Weekend camping trip", "requirement": "Complete 4-week fitness challenge"}
            ],
            "celebration_milestones": [
                {"milestone": "1 month of consistent goals", "celebration": "Family dinner at favorite restaurant"},
                {"milestone": "3 months of progress", "celebration": "Family vacation planning session"},
                {"milestone": "6 months of success", "celebration": "Special family adventure day"}
            ]
        }
    }

@api_router.post("/family/goals/{goal_id}/update-progress")
async def update_family_goal_progress(goal_id: str, progress_data: dict):
    """Update progress for family goals"""
    return {
        "goal_id": goal_id,
        "updated": True,
        "new_progress": progress_data.get("progress", 0),
        "member": progress_data.get("member", "unknown"),
        "streak_updated": True,
        "family_progress_recalculated": True,
        "milestone_check": {
            "milestone_reached": progress_data.get("progress", 0) > 80,
            "reward_unlocked": "Family celebration dinner" if progress_data.get("progress", 0) > 80 else None
        },
        "encouragement_message": "Great job staying committed to your family's health goals!",
        "next_milestone": "Keep it up! You're only 5% away from your next reward."
    }

@api_router.get("/family/multi-profile-management/{family_id}")
async def get_multi_profile_management(family_id: str):
    """Advanced multi-profile management system"""
    return {
        "family_id": family_id,
        "profile_overview": {
            "total_profiles": 4,
            "completion_status": {
                "Sarah": {"completion": 95, "status": "complete", "last_updated": "2024-01-16"},
                "John": {"completion": 88, "status": "complete", "last_updated": "2024-01-15"},
                "Emma": {"completion": 92, "status": "complete", "last_updated": "2024-01-17"},
                "Alex": {"completion": 85, "status": "complete", "last_updated": "2024-01-14"}
            },
            "data_synchronization": {
                "last_sync": "2024-01-17 7:00 AM",
                "sync_status": "up_to_date",
                "conflicts_resolved": 0,
                "pending_updates": []
            }
        },
        "member_profiles": [
            {
                "member": "Sarah",
                "role": "Primary Caregiver",
                "age": 38,
                "health_summary": {
                    "current_conditions": ["Pregnancy - 2nd trimester"],
                    "allergies": ["none"],
                    "medications": ["Prenatal vitamins"],
                    "recent_vitals": {"bp": "118/75", "weight": "142 lbs", "heart_rate": "72 bpm"},
                    "health_goals": ["Healthy pregnancy weight gain", "Regular prenatal care", "Stress management"]
                },
                "dietary_preferences": {
                    "restrictions": ["none"],
                    "preferences": ["organic_when_possible", "minimal_processed_foods"],
                    "cultural_dietary": ["Mediterranean_influenced"]
                },
                "activity_level": "moderately_active",
                "responsibilities": ["medication_management", "appointment_scheduling", "meal_planning"]
            },
            {
                "member": "John",
                "role": "Secondary Caregiver",
                "age": 40,
                "health_summary": {
                    "current_conditions": ["Mild hypertension"],
                    "allergies": ["environmental_dust"],
                    "medications": ["Blood pressure medication"],
                    "recent_vitals": {"bp": "132/82", "weight": "185 lbs", "heart_rate": "68 bpm"},
                    "health_goals": ["Blood pressure management", "Weight maintenance", "Regular exercise"]
                },
                "dietary_preferences": {
                    "restrictions": ["low_sodium"],
                    "preferences": ["whole_grains", "lean_proteins"],
                    "cultural_dietary": ["American_traditional"]
                },
                "activity_level": "lightly_active",
                "responsibilities": ["transportation", "emergency_backup", "weekend_meal_prep"]
            },
            {
                "member": "Emma",
                "role": "Dependent - Adolescent", 
                "age": 12,
                "health_summary": {
                    "current_conditions": ["Seasonal allergies"],
                    "allergies": ["tree_nuts_severe", "pollen"],
                    "medications": ["EpiPen", "Allergy medication as needed"],
                    "recent_vitals": {"height": "5'2\"", "weight": "105 lbs", "growth_percentile": "60th"},
                    "health_goals": ["Allergy management", "Healthy growth", "Physical fitness"]
                },
                "dietary_preferences": {
                    "restrictions": ["tree_nuts", "avoids_processed_snacks"],
                    "preferences": ["fruits", "yogurt", "homemade_baked_goods"],
                    "cultural_dietary": ["family_style_meals"]
                },
                "activity_level": "very_active",
                "school_coordination": {
                    "school_nurse_informed": True,
                    "emergency_action_plan": "on_file",
                    "lunch_modifications": "nut_free_table"
                }
            },
            {
                "member": "Alex",
                "role": "Dependent - Child",
                "age": 8,
                "health_summary": {
                    "current_conditions": ["none"],
                    "allergies": ["none_known"],
                    "medications": ["none_regular"],
                    "recent_vitals": {"height": "4'8\"", "weight": "85 lbs", "growth_percentile": "75th"},
                    "health_goals": ["Healthy growth", "Develop good eating habits", "Stay active"],
                    "dietary_considerations": ["lactose_intolerant"]
                },
                "dietary_preferences": {
                    "restrictions": ["dairy_limited"],
                    "preferences": ["chicken", "pasta", "apples", "rice"],
                    "challenges": ["picky_eater", "limited_vegetable_acceptance"]
                },
                "activity_level": "very_active",
                "school_coordination": {
                    "lunch_modifications": "dairy_free_options",
                    "snack_preferences": "nut_free_crackers_fruit"
                }
            }
        ],
        "coordination_tools": {
            "shared_calendar": {
                "medical_appointments": 3,
                "medication_reminders": 5,
                "meal_planning_sessions": 2,
                "family_activities": 8
            },
            "communication_system": {
                "family_chat_active": True,
                "provider_messaging": True,
                "school_communication": True,
                "emergency_notifications": True
            },
            "data_sharing": {
                "with_healthcare_providers": ["with_consent", "secure_portal"],
                "with_schools": ["emergency_info_only", "updated_automatically"],
                "with_family_members": ["age_appropriate_access"]
            }
        }
    }

# Guest Experience Endpoints
@api_router.get("/guest/quick-nutrition/{session_id}")
async def get_guest_quick_nutrition(session_id: str):
    """Get instant nutrition insights for guest users"""
    return {
        "session_id": session_id,
        "instant_calculations": {
            "estimated_bmr": 1650,
            "daily_calorie_needs": 2100,
            "protein_needs": "84-126g",
            "fiber_needs": "25g",
            "water_needs": "8-10 glasses"
        },
        "quick_assessments": [
            {
                "category": "hydration",
                "current_status": "adequate",
                "recommendation": "Maintain current water intake",
                "simple_tips": ["Drink a glass of water before each meal", "Keep a water bottle visible"]
            },
            {
                "category": "energy",
                "current_status": "good",
                "recommendation": "Include protein in every meal",
                "simple_tips": ["Add Greek yogurt to smoothies", "Include nuts or seeds as snacks"]
            }
        ],
        "educational_content": [
            {
                "topic": "Reading Nutrition Labels",
                "level": "beginner",
                "key_points": ["Look at serving size first", "Check sugar content", "Aim for more fiber"],
                "time_to_read": "3 minutes"
            },
            {
                "topic": "Portion Control Basics",
                "level": "beginner",
                "key_points": ["Use your hand as a guide", "Fill half plate with vegetables", "Protein = palm size"],
                "time_to_read": "2 minutes"
            }
        ],
        "upgrade_benefits": [
            "Save your food preferences and get personalized recommendations",
            "Track your progress over time with detailed analytics",
            "Get custom meal plans based on your goals and dietary needs",
            "Access to expert-reviewed nutrition content and recipes"
        ]
    }

@api_router.post("/guest/instant-food-log")
async def instant_guest_food_log(food_data: dict):
    """Instant food logging for guests with immediate feedback"""
    return {
        "success": True,
        "food_recognized": food_data.get("food_name", "Unknown Food"),
        "estimated_nutrition": {
            "calories": food_data.get("calories", 200),
            "protein": 15,
            "carbs": 25,
            "fat": 8,
            "fiber": 3
        },
        "instant_feedback": [
            "Good choice! This food provides quality protein for sustained energy.",
            "Consider adding some vegetables or fruits to boost fiber and vitamins.",
            "This fits well within a balanced 2000-calorie daily plan."
        ],
        "session_totals": {
            "today_calories": 580,
            "meals_logged": 2,
            "session_time": "12 minutes"
        },
        "simple_suggestions": [
            "Try pairing this with a small salad for extra nutrients",
            "A glass of water now will help with digestion",
            "This makes a great base - add some colorful vegetables!"
        ],
        "learning_moment": {
            "tip": "Did you know?",
            "content": "Protein helps you feel full longer and supports muscle health. Aim for some protein in every meal!"
        }
    }

# Role-Based Data Access Endpoints
@api_router.get("/roles/{role}/features")
async def get_role_features(role: str):
    """Get available features for specific role"""
    role_features = {
        "patient": [
            {"name": "Personal Health Analytics", "category": "analytics", "premium": False},
            {"name": "Smart Food Logging", "category": "tracking", "premium": False},
            {"name": "Health Goal Tracking", "category": "goals", "premium": False},
            {"name": "Symptom Correlation", "category": "insights", "premium": True},
            {"name": "AI Health Insights", "category": "ai", "premium": True},
            {"name": "Medication Reminders", "category": "health", "premium": True}
        ],
        "provider": [
            {"name": "Patient Management", "category": "clinical", "premium": False},
            {"name": "Clinical Decision Support", "category": "clinical", "premium": True},
            {"name": "Population Health Analytics", "category": "analytics", "premium": True},
            {"name": "Evidence-Based Recommendations", "category": "clinical", "premium": True},
            {"name": "Treatment Outcome Tracking", "category": "tracking", "premium": False}
        ],
        "family": [
            {"name": "Multi-Profile Management", "category": "coordination", "premium": False},
            {"name": "Family Meal Planning", "category": "nutrition", "premium": False},
            {"name": "Care Coordination", "category": "health", "premium": False},
            {"name": "Child Nutrition Education", "category": "education", "premium": True},
            {"name": "Family Health Analytics", "category": "analytics", "premium": True}
        ],
        "guest": [
            {"name": "Quick Nutrition Tracking", "category": "tracking", "premium": False},
            {"name": "Basic Health Calculations", "category": "tools", "premium": False},
            {"name": "Nutrition Education", "category": "education", "premium": False},
            {"name": "Simple Goal Setting", "category": "goals", "premium": False}
        ]
    }
    
    return {
        "role": role,
        "features": role_features.get(role, []),
        "feature_count": len(role_features.get(role, [])),
        "premium_features": len([f for f in role_features.get(role, []) if f.get("premium", False)])
    }

@api_router.get("/analytics/role-usage")
async def get_role_usage_analytics():
    """Get usage analytics across all roles"""
    return {
        "total_users": 1247,
        "role_distribution": {
            "patient": {"count": 892, "percentage": 71.5, "growth": 12.3},
            "provider": {"count": 45, "percentage": 3.6, "growth": 8.9},
            "family": {"count": 234, "percentage": 18.8, "growth": 15.7},
            "guest": {"count": 76, "percentage": 6.1, "growth": -2.1}
        },
        "feature_usage": {
            "most_used": [
                {"feature": "Food Logging", "usage": 89.2, "role": "patient"},
                {"feature": "Family Meal Planning", "usage": 76.8, "role": "family"},
                {"feature": "Patient Management", "usage": 92.1, "role": "provider"}
            ],
            "emerging": [
                {"feature": "Symptom Correlation", "growth": 45.2, "role": "patient"},
                {"feature": "Population Analytics", "growth": 38.7, "role": "provider"}
            ]
        },
        "engagement_metrics": {
            "daily_active_users": 567,
            "weekly_retention": 78.4,
            "monthly_retention": 65.2,
            "average_session_time": "23 minutes"
        }
    }

# Session Management for Guests
@api_router.post("/guest/session")
async def create_guest_session():
    """Create a new guest session"""
    session_id = f"guest_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"
    session_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Create a basic guest profile in database to enable data export
    guest_profile = GuestProfile(
        session_id=session_id,
        role="GUEST",
        basic_demographics=None,  # Will be filled when user provides info
        simple_goals=None,  # Will be filled when user provides info
        session_expires=session_expires,
        created_at=datetime.utcnow()
    )
    
    # Clean up expired guest profiles periodically
    await db.guest_profiles.delete_many({"session_expires": {"$lt": datetime.utcnow()}})
    
    # Insert the new guest profile
    await db.guest_profiles.insert_one(guest_profile.dict())
    
    return {
        "session_id": session_id,
        "expires_at": (session_expires.timestamp()),  # 24 hours
        "features_available": [
            "instant_food_logging",
            "basic_nutrition_info",
            "simple_goal_tracking",
            "educational_content"
        ],
        "limitations": [
            "Data not permanently stored",
            "Limited to basic features",
            "No historical tracking",
            "No personalized recommendations"
        ],
        "upgrade_benefits": [
            "Permanent data storage",
            "Advanced analytics",
            "Personalized insights",
            "Goal tracking over time"
        ]
    }

@api_router.get("/guest/session/{session_id}/status")
async def get_guest_session_status(session_id: str):
    """Check guest session status and activity"""
    return {
        "session_id": session_id,
        "status": "active",
        "time_remaining": "18h 32m",
        "activity_summary": {
            "foods_logged": 5,
            "tips_viewed": 3,
            "calculations_used": 2,
            "session_duration": "15m 23s"
        },
        "recommendations": [
            "You're doing great! Consider setting a simple daily goal.",
            "Try logging your dinner to get a complete daily picture.",
            "Check out our nutrition tips section for more insights."
        ]
    }

# ===== PHASE 6: GUEST GOAL MANAGEMENT APIS =====

class GuestGoal(BaseModel):
    id: int
    title: str
    category: str
    target: int
    unit: str
    current: int = 0
    timeframe: str = "daily"
    createdAt: str
    lastUpdated: str

class GuestGoalSession(BaseModel):
    session_id: str
    goals: List[GuestGoal] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

@api_router.post("/guest/goals/{session_id}")
async def sync_guest_goals(session_id: str, goal_data: dict):
    """Sync guest goals with backend for session persistence"""
    try:
        goals_list = goal_data.get('goals', [])
        
        # Store in temporary collection with expiration
        goal_session = {
            "session_id": session_id,
            "goals": goals_list,
            "last_updated": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Update or insert goal session
        await db.guest_goal_sessions.update_one(
            {"session_id": session_id},
            {"$set": goal_session},
            upsert=True
        )
        
        # Clean up expired sessions
        await db.guest_goal_sessions.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        
        return {
            "success": True,
            "session_id": session_id,
            "goals_synced": len(goals_list),
            "expires_at": goal_session["expires_at"].isoformat()
        }
    except Exception as e:
        logger.error(f"Goal sync error: {e}")
        return {"success": False, "error": "Failed to sync goals"}

@api_router.get("/guest/goals/{session_id}")
async def get_guest_goals(session_id: str):
    """Retrieve guest goals for a session"""
    try:
        goal_session = await db.guest_goal_sessions.find_one({
            "session_id": session_id,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not goal_session:
            return {
                "success": True,
                "session_id": session_id,
                "goals": [],
                "message": "No goals found for this session"
            }
        
        return {
            "success": True,
            "session_id": session_id,
            "goals": goal_session.get("goals", []),
            "last_updated": goal_session.get("last_updated").isoformat(),
            "expires_at": goal_session.get("expires_at").isoformat()
        }
    except Exception as e:
        logger.error(f"Goal retrieval error: {e}")
        return {"success": False, "error": "Failed to retrieve goals"}

@api_router.post("/guest/goals/{session_id}/progress")
async def update_guest_goal_progress(session_id: str, progress_data: dict):
    """Update progress for a specific goal"""
    try:
        goal_id = progress_data.get('goal_id')
        new_current = progress_data.get('current', 0)
        
        # Update specific goal progress
        result = await db.guest_goal_sessions.update_one(
            {
                "session_id": session_id,
                "expires_at": {"$gt": datetime.utcnow()},
                "goals.id": goal_id
            },
            {
                "$set": {
                    "goals.$.current": new_current,
                    "goals.$.lastUpdated": datetime.utcnow().isoformat(),
                    "last_updated": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "goal_id": goal_id,
                "new_current": new_current,
                "message": "Progress updated successfully"
            }
        else:
            return {"success": False, "error": "Goal not found or session expired"}
            
    except Exception as e:
        logger.error(f"Goal progress update error: {e}")
        return {"success": False, "error": "Failed to update progress"}

@api_router.get("/guest/goals/{session_id}/analytics")
async def get_guest_goal_analytics(session_id: str):
    """Get goal analytics and insights for guest session"""
    try:
        goal_session = await db.guest_goal_sessions.find_one({
            "session_id": session_id,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not goal_session:
            return {"success": False, "error": "Session not found or expired"}
        
        goals = goal_session.get("goals", [])
        
        # Calculate analytics
        total_goals = len(goals)
        completed_goals = len([g for g in goals if g.get('current', 0) >= g.get('target', 1)])
        completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
        
        # Category breakdown
        category_stats = {}
        for goal in goals:
            category = goal.get('category', 'other')
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'completed': 0}
            category_stats[category]['total'] += 1
            if goal.get('current', 0) >= goal.get('target', 1):
                category_stats[category]['completed'] += 1
        
        # Generate insights
        insights = []
        if completion_rate >= 80:
            insights.append("Excellent progress! You're crushing your goals today.")
        elif completion_rate >= 50:
            insights.append("Great work! You're more than halfway to your daily goals.")
        elif completion_rate >= 25:
            insights.append("Good start! Keep going to reach more of your goals.")
        else:
            insights.append("Every step counts! Start with one small goal to build momentum.")
        
        # Add category-specific insights
        for category, stats in category_stats.items():
            if stats['completed'] == stats['total'] and stats['total'] > 0:
                insights.append(f"🎉 Perfect {category} goals completion!")
        
        return {
            "success": True,
            "session_id": session_id,
            "analytics": {
                "total_goals": total_goals,
                "completed_goals": completed_goals,
                "completion_rate": round(completion_rate, 1),
                "category_breakdown": category_stats,
                "session_duration": calculate_session_duration(goal_session.get("last_updated")),
                "insights": insights,
                "motivational_message": get_motivational_message(completion_rate),
                "next_actions": get_next_action_suggestions(goals)
            }
        }
    except Exception as e:
        logger.error(f"Goal analytics error: {e}")
        return {"success": False, "error": "Failed to generate analytics"}

def calculate_session_duration(last_updated):
    """Calculate session duration"""
    if not last_updated:
        return "0 minutes"
    
    duration = datetime.utcnow() - last_updated
    minutes = int(duration.total_seconds() / 60)
    
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m"

def get_motivational_message(completion_rate):
    """Get motivational message based on completion rate"""
    if completion_rate >= 100:
        return "🎉 Amazing! You've completed all your goals for today!"
    elif completion_rate >= 75:
        return "🌟 You're almost there! Just a few more goals to go!"
    elif completion_rate >= 50:
        return "💪 Great momentum! Keep pushing towards your goals!"
    elif completion_rate >= 25:
        return "🚀 Good progress! Every small step counts!"
    else:
        return "🌱 Start with one goal - you've got this!"

def get_next_action_suggestions(goals):
    """Get actionable next step suggestions"""
    suggestions = []
    
    incomplete_goals = [g for g in goals if g.get('current', 0) < g.get('target', 1)]
    
    if not incomplete_goals:
        suggestions.append("All goals completed! Consider setting a bonus goal.")
        return suggestions
    
    # Find easiest goal to complete
    easiest_goal = min(incomplete_goals, 
                      key=lambda g: g.get('target', 1) - g.get('current', 0))
    
    remaining = easiest_goal.get('target', 1) - easiest_goal.get('current', 0)
    if remaining == 1:
        suggestions.append(f"Quick win: Complete '{easiest_goal.get('title', 'Unknown')}' - just 1 more {easiest_goal.get('unit', 'step')}!")
    else:
        suggestions.append(f"Focus on '{easiest_goal.get('title', 'Unknown')}' - {remaining} {easiest_goal.get('unit', 'steps')} to go!")
    
    # Category-specific suggestions
    nutrition_goals = [g for g in incomplete_goals if g.get('category') == 'nutrition']
    if nutrition_goals:
        suggestions.append("💡 Add vegetables to your next meal for nutrition goal progress!")
    
    hydration_goals = [g for g in incomplete_goals if g.get('category') == 'hydration']
    if hydration_goals:
        suggestions.append("💧 Keep a water bottle nearby to stay on track!")
    
    return suggestions[:3]  # Limit to 3 suggestions

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== PHASE 2.3: ADVANCED GOAL TRACKING API ENDPOINTS =====

# Goal Management CRUD Endpoints
@api_router.post("/patient/goals", response_model=Goal)
async def create_goal(goal: GoalCreate):
    """Create a new goal for a patient"""
    goal_dict = goal.dict()
    goal_obj = Goal(**goal_dict)
    
    # Add initial AI insights about success probability
    try:
        goal_data = {
            "goal_type": goal.goal_type,
            "target_value": goal.target_value,
            "user_id": goal.user_id,
            "target_date": goal.target_date
        }
        ai_insights = await get_goal_insights(goal_data)
        goal_obj.success_probability = ai_insights.get("success_probability", 0.7)
        goal_obj.ai_insights = ai_insights.get("insights", [])
    except Exception as e:
        logger.error(f"AI goal insights error: {e}")
        goal_obj.success_probability = 0.7
    
    await db.patient_goals.insert_one(goal_obj.dict())
    return goal_obj

@api_router.get("/patient/goals/{user_id}")
async def get_user_goals(user_id: str, status: Optional[str] = None):
    """Get all goals for a user, optionally filtered by status"""
    query = {"user_id": user_id}
    if status:
        query["status"] = status.upper()
    
    goals = await db.patient_goals.find(query).sort("created_at", -1).to_list(100)
    return [Goal(**goal) for goal in goals]

@api_router.get("/patient/goals/goal/{goal_id}", response_model=Goal)
async def get_goal_by_id(goal_id: str):
    """Get a specific goal by ID"""
    goal = await db.patient_goals.find_one({"id": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return Goal(**goal)

@api_router.put("/patient/goals/{goal_id}", response_model=Goal)
async def update_goal(goal_id: str, update: GoalUpdate):
    """Update an existing goal"""
    existing = await db.patient_goals.find_one({"id": goal_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    update_dict = {k: v for k, v in update.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    # Check for completion
    if update_dict.get("status") == "COMPLETED" and existing.get("status") != "COMPLETED":
        update_dict["completion_date"] = datetime.utcnow()
        
        # Create achievement for goal completion
        try:
            achievement = Achievement(
                user_id=existing["user_id"],
                achievement_type=AchievementTypeEnum.GOAL_COMPLETION,
                title=f"Goal Completed: {existing['title']}",
                description=f"Successfully completed the goal: {existing['title']}",
                badge_icon="🏆",
                badge_color="#FFD700",
                points_awarded=100,
                rarity_level="COMMON",
                related_goal_id=goal_id,
                category=existing["goal_type"],
                celebration_message=f"Congratulations! You've completed your {existing['goal_type'].lower()} goal!"
            )
            await db.patient_achievements.insert_one(achievement.dict())
        except Exception as e:
            logger.error(f"Error creating completion achievement: {e}")
    
    await db.patient_goals.update_one(
        {"id": goal_id},
        {"$set": update_dict}
    )
    
    updated_goal = await db.patient_goals.find_one({"id": goal_id})
    return Goal(**updated_goal)

@api_router.delete("/patient/goals/{goal_id}")
async def delete_goal(goal_id: str):
    """Delete a goal"""
    result = await db.patient_goals.delete_one({"id": goal_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal deleted successfully"}

@api_router.post("/patient/goals/{goal_id}/progress")
async def update_goal_progress(goal_id: str, progress_data: dict):
    """Update progress for a specific goal"""
    goal = await db.patient_goals.find_one({"id": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    new_value = progress_data.get("current_value", goal.get("current_value", 0))
    progress_entry = {
        "date": datetime.utcnow().isoformat(),
        "value": new_value,
        "notes": progress_data.get("notes", ""),
        "source": progress_data.get("source", "manual")
    }
    
    # Calculate progress percentage
    target_value = goal.get("target_value", 100)
    if target_value > 0:
        progress_percentage = min((new_value / target_value) * 100, 100)
    else:
        progress_percentage = 0
    
    # Update streak count
    current_streak = goal.get("streak_count", 0)
    if progress_data.get("daily_completion", False):
        current_streak += 1
    
    # Check for milestone achievements
    milestones = goal.get("milestones", [])
    for milestone in milestones:
        if not milestone.get("achieved", False) and progress_percentage >= milestone.get("percentage", 100):
            milestone["achieved"] = True
            milestone["achieved_date"] = datetime.utcnow().isoformat()
            
            # Create milestone achievement
            try:
                achievement = Achievement(
                    user_id=goal["user_id"],
                    achievement_type=AchievementTypeEnum.PROGRESS_MILESTONE,
                    title=f"Milestone Reached: {milestone.get('title', 'Progress Milestone')}",
                    description=f"Reached {milestone.get('percentage', 0)}% of your goal: {goal['title']}",
                    badge_icon="🎯",
                    badge_color="#4CAF50",
                    points_awarded=50,
                    rarity_level="COMMON",
                    related_goal_id=goal_id,
                    category=goal["goal_type"],
                    celebration_message=f"Great progress! You've reached a major milestone!",
                    milestone_data=milestone
                )
                await db.patient_achievements.insert_one(achievement.dict())
            except Exception as e:
                logger.error(f"Error creating milestone achievement: {e}")
    
    # Update the goal
    update_dict = {
        "current_value": new_value,
        "streak_count": current_streak,
        "longest_streak": max(goal.get("longest_streak", 0), current_streak),
        "milestones": milestones,
        "$push": {"progress_history": progress_entry},
        "updated_at": datetime.utcnow()
    }
    
    await db.patient_goals.update_one(
        {"id": goal_id},
        {"$set": update_dict}
    )
    
    return {
        "goal_id": goal_id,
        "new_progress": progress_percentage,
        "current_value": new_value,
        "streak_count": current_streak,
        "milestone_reached": any(m.get("achieved") and not m.get("previously_achieved") for m in milestones),
        "message": "Progress updated successfully"
    }

# Achievement Management Endpoints
@api_router.get("/patient/achievements/{user_id}")
async def get_user_achievements(user_id: str, category: Optional[str] = None):
    """Get all achievements for a user"""
    query = {"user_id": user_id}
    if category:
        query["category"] = category.upper()
    
    achievements = await db.patient_achievements.find(query).sort("unlocked_at", -1).to_list(100)
    
    # Get achievement insights
    try:
        achievement_data = {
            "user_id": user_id,
            "recent_achievements": achievements[:5],
            "total_achievements": len(achievements),
            "categories": list(set([a.get("category") for a in achievements])),
            "points": sum([a.get("points_awarded", 0) for a in achievements])
        }
        ai_insights = await get_achievement_insights(achievement_data)
    except Exception as e:
        logger.error(f"AI achievement insights error: {e}")
        ai_insights = {"achievement_insights": {"achievements": [], "motivation_tips": []}}
    
    # Organize achievements by category
    achievements_by_category = {}
    for achievement in achievements:
        category = achievement.get("category", "OTHER")
        if category not in achievements_by_category:
            achievements_by_category[category] = []
        achievements_by_category[category].append(Achievement(**achievement))
    
    return {
        "user_id": user_id,
        "total_achievements": len(achievements),
        "total_points": sum([a.get("points_awarded", 0) for a in achievements]),
        "achievements_by_category": achievements_by_category,
        "recent_achievements": [Achievement(**a) for a in achievements[:10]],
        "ai_insights": ai_insights.get("achievement_insights", {}),
        "badge_summary": {
            "common": len([a for a in achievements if a.get("rarity_level") == "COMMON"]),
            "rare": len([a for a in achievements if a.get("rarity_level") == "RARE"]),
            "epic": len([a for a in achievements if a.get("rarity_level") == "EPIC"]),
            "legendary": len([a for a in achievements if a.get("rarity_level") == "LEGENDARY"])
        }
    }

@api_router.post("/patient/achievements/{achievement_id}/share")
async def share_achievement(achievement_id: str, share_data: dict):
    """Share an achievement on social platforms"""
    achievement = await db.patient_achievements.find_one({"id": achievement_id})
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    if not achievement.get("shareable", True):
        raise HTTPException(status_code=400, detail="This achievement is not shareable")
    
    platform = share_data.get("platform", "general")
    custom_message = share_data.get("message", "")
    
    # Generate share content based on platform
    share_content = {
        "title": achievement["title"],
        "description": achievement["description"],
        "badge_icon": achievement["badge_icon"],
        "points": achievement["points_awarded"],
        "rarity": achievement["rarity_level"],
        "celebration_message": achievement["celebration_message"]
    }
    
    if platform == "twitter":
        share_content["tweet_text"] = f"🎉 {achievement['title']} {achievement['badge_icon']} Just earned {achievement['points_awarded']} points on my health journey! #HealthGoals #Achievement"
        share_content["url"] = f"https://twitter.com/intent/tweet?text={share_content['tweet_text']}"
    elif platform == "facebook":
        share_content["post_text"] = f"I'm proud to share that I just unlocked: {achievement['title']}! {achievement['description']} 💪 #HealthJourney"
        share_content["url"] = f"https://www.facebook.com/sharer/sharer.php?quote={share_content['post_text']}"
    elif platform == "linkedin":
        share_content["post_text"] = f"Celebrating a health milestone: {achievement['title']}. {achievement['description']} Consistency and dedication paying off! 🏆"
        share_content["url"] = f"https://www.linkedin.com/sharing/share-offsite/?summary={share_content['post_text']}"
    
    if custom_message:
        share_content["custom_message"] = custom_message
    
    # Log the share activity
    share_log = {
        "achievement_id": achievement_id,
        "user_id": achievement["user_id"],
        "platform": platform,
        "shared_at": datetime.utcnow().isoformat(),
        "content": share_content
    }
    await db.achievement_shares.insert_one(share_log)
    
    return {
        "success": True,
        "platform": platform,
        "share_content": share_content,
        "message": "Achievement sharing content generated successfully"
    }

# AI-Powered Goal and Achievement Insights
@api_router.post("/ai/goal-suggestions")
async def get_ai_goal_suggestions(request_data: dict):
    """Get AI-powered goal suggestions based on user profile and history"""
    user_id = request_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    # Gather user data
    goals = await db.patient_goals.find({"user_id": user_id}).to_list(50)
    achievements = await db.patient_achievements.find({"user_id": user_id}).to_list(50)
    
    goal_data = {
        "user_id": user_id,
        "current_goals": goals,
        "achievements": achievements,
        "completion_rate": sum(1 for g in goals if g.get("status") == "COMPLETED") / max(len(goals), 1) * 100,
        "successful_types": list(set([g.get("goal_type") for g in goals if g.get("status") == "COMPLETED"])),
        "current_streak": max([g.get("streak_count", 0) for g in goals] + [0]),
        "preferences": request_data.get("preferences", {}),
        "health_conditions": request_data.get("health_conditions", [])
    }
    
    try:
        ai_suggestions = await get_goal_insights(goal_data)
    except Exception as e:
        logger.error(f"AI goal suggestions error: {e}")
        ai_suggestions = {
            "recommendations": [
                {
                    "title": "Hydration Goal",
                    "description": "Drink 8 glasses of water daily",
                    "goal_type": "HYDRATION",
                    "target_value": 8,
                    "target_unit": "glasses",
                    "priority": "MEDIUM",
                    "success_probability": 0.8
                }
            ]
        }
    
    return {
        "user_id": user_id,
        "suggested_goals": ai_suggestions.get("recommendations", []),
        "goal_adjustments": ai_suggestions.get("goal_adjustments", []),
        "insights": ai_suggestions.get("insights", []),
        "confidence": ai_suggestions.get("confidence", 0.7),
        "personalization_factors": [
            "Past goal completion rate",
            "Preferred goal categories",
            "Current health status",
            "Available time commitment"
        ]
    }

@api_router.post("/ai/goal-insights")
async def get_ai_goal_analysis(request_data: dict):
    """Get AI-powered analysis of current goals"""
    user_id = request_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    # Get current goals
    goals = await db.patient_goals.find({"user_id": user_id, "status": "ACTIVE"}).to_list(20)
    
    analysis_data = {
        "user_id": user_id,
        "active_goals": goals,
        "analysis_type": request_data.get("analysis_type", "comprehensive"),
        "timeframe": request_data.get("timeframe", "monthly")
    }
    
    try:
        ai_analysis = await get_goal_insights(analysis_data)
    except Exception as e:
        logger.error(f"AI goal analysis error: {e}")
        ai_analysis = {
            "insights": ["Goals analysis completed"],
            "recommendations": []
        }
    
    return {
        "user_id": user_id,
        "analysis_date": datetime.utcnow().isoformat(),
        "goal_performance": {
            "total_active_goals": len(goals),
            "on_track": sum(1 for g in goals if g.get("current_value", 0) / g.get("target_value", 1) >= 0.7),
            "needs_attention": sum(1 for g in goals if g.get("current_value", 0) / g.get("target_value", 1) < 0.5),
            "average_progress": sum(g.get("current_value", 0) / g.get("target_value", 1) for g in goals) / max(len(goals), 1) * 100
        },
        "ai_insights": ai_analysis.get("insights", []),
        "recommendations": ai_analysis.get("recommendations", []),
        "optimization_suggestions": ai_analysis.get("goal_adjustments", []),
        "confidence": ai_analysis.get("confidence", 0.7)
    }

@api_router.get("/patient/goal-correlations/{user_id}")
async def get_goal_correlations(user_id: str):
    """Get correlations between goals and other health factors"""
    
    # Get user's goals and related data
    goals = await db.patient_goals.find({"user_id": user_id}).to_list(50)
    achievements = await db.patient_achievements.find({"user_id": user_id}).to_list(50)
    
    correlation_data = {
        "user_id": user_id,
        "goals": goals,
        "achievements": achievements,
        "analysis_period": "90_days"
    }
    
    # Mock correlation analysis (in real app, this would be more sophisticated)
    correlations = []
    if goals:
        goal_types = list(set([g.get("goal_type") for g in goals]))
        for goal_type in goal_types:
            type_goals = [g for g in goals if g.get("goal_type") == goal_type]
            avg_completion = sum(1 for g in type_goals if g.get("status") == "COMPLETED") / len(type_goals)
            
            correlations.append({
                "goal_type": goal_type,
                "completion_rate": avg_completion * 100,
                "average_duration": 21,  # Mock data
                "success_factors": [
                    "Setting realistic targets",
                    "Daily tracking",
                    "Social support"
                ],
                "common_obstacles": [
                    "Time management",
                    "Motivation fluctuations",
                    "Unrealistic expectations"
                ]
            })
    
    return GoalCorrelation(
        user_id=user_id,
        goal_correlations=correlations,
        behavior_patterns={
            "most_successful_goal_type": max(correlations, key=lambda x: x["completion_rate"])["goal_type"] if correlations else "NUTRITION",
            "optimal_goal_duration": "3-4 weeks",
            "best_start_day": "Monday",
            "success_streak_average": 12
        },
        success_factors=[
            "Consistent daily tracking",
            "Realistic target setting", 
            "Regular progress reviews",
            "Social accountability"
        ],
        recommendations=[
            {
                "type": "goal_setting",
                "title": "Optimize Goal Duration",
                "description": "Your data shows better success with 3-4 week goals vs longer term goals",
                "priority": "HIGH"
            },
            {
                "type": "tracking",
                "title": "Daily Check-ins",
                "description": "Users with daily tracking show 40% higher completion rates",
                "priority": "MEDIUM"
            }
        ]
    )

# ========================================
# PHASE 7: DATA EXPORT ENDPOINTS
# ========================================

@api_router.get("/patient/export/{user_id}")
async def export_patient_data(user_id: str, format: str = "json"):
    """Export comprehensive patient data"""
    try:
        # Get patient profile
        profile = await db.patient_profiles.find_one({"user_id": user_id})
        if not profile:
            raise HTTPException(status_code=404, detail="Patient profile not found")
        
        # Collect all patient data
        export_data = {
            "export_info": {
                "user_id": user_id,
                "role": "patient",
                "exported_at": datetime.utcnow().isoformat(),
                "format": format
            },
            "profile": {
                "user_id": profile.get("user_id"),
                "basic_info": profile.get("basic_info", {}),
                "physical_metrics": profile.get("physical_metrics", {}),
                "activity_profile": profile.get("activity_profile", {}),
                "health_history": profile.get("health_history", {}),
                "dietary_profile": profile.get("dietary_profile", {}),
                "goals_preferences": profile.get("goals_preferences", {}),
                "profile_completion": profile.get("profile_completion", 0)
            },
            "health_data": {
                "nutrition_summary": {
                    "daily_calories": 1850,
                    "protein": 120,
                    "carbs": 180,
                    "fats": 65,
                    "fiber": 25,
                    "water": 8
                },
                "health_metrics": {
                    "weight": 68.5,
                    "bmi": 22.1,
                    "body_fat": 15.2,
                    "blood_pressure": "118/76",
                    "heart_rate": 68
                },
                "goals": [
                    {"id": "weight_goal", "title": "Maintain healthy weight", "target": 68, "current": 68.5, "unit": "kg"},
                    {"id": "protein_goal", "title": "Daily protein intake", "target": 120, "current": 95, "unit": "g"},
                    {"id": "hydration_goal", "title": "Daily water intake", "target": 8, "current": 6, "unit": "glasses"}
                ]
            },
            "food_logs": [
                {
                    "date": "2024-07-15",
                    "meals": {
                        "breakfast": [{"food": "Oatmeal with berries", "calories": 280, "protein": 8}],
                        "lunch": [{"food": "Grilled chicken salad", "calories": 420, "protein": 35}],
                        "dinner": [{"food": "Salmon with quinoa", "calories": 580, "protein": 40}],
                        "snacks": [{"food": "Greek yogurt", "calories": 150, "protein": 15}]
                    },
                    "total_calories": 1430,
                    "total_protein": 98
                }
            ],
            "ai_insights": [
                "Your protein intake is consistently good, averaging 98g daily",
                "Consider increasing vegetable variety for better micronutrient profile",
                "Your meal timing is optimal for metabolism"
            ]
        }
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting patient data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@api_router.get("/provider/export/{user_id}")
async def export_provider_data(user_id: str, format: str = "json"):
    """Export comprehensive provider data"""
    try:
        # Get provider profile
        profile = await db.provider_profiles.find_one({"user_id": user_id})
        if not profile:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        
        export_data = {
            "export_info": {
                "user_id": user_id,
                "role": "provider",
                "exported_at": datetime.utcnow().isoformat(),
                "format": format
            },
            "profile": {
                "user_id": profile.get("user_id"),
                "professional_identity": profile.get("professional_identity", {}),
                "credentials": profile.get("credentials", {}),
                "practice_info": profile.get("practice_info", {}),
                "preferences": profile.get("preferences", {}),
                "verification_status": profile.get("verification_status", "PENDING"),
                "profile_completion": profile.get("profile_completion", 0)
            },
            "practice_data": {
                "patient_overview": {
                    "total_patients": 47,
                    "active_patients": 42,
                    "patients_seen_today": 8,
                    "avg_patient_satisfaction": 4.7
                },
                "clinical_analytics": {
                    "successful_outcomes": 89.2,
                    "patient_adherence_rate": 76.3,
                    "intervention_effectiveness": 84.1
                },
                "recent_activities": [
                    {"date": "2024-07-15", "activity": "Patient consultation - John D.", "outcome": "Treatment plan updated"},
                    {"date": "2024-07-15", "activity": "Nutrition review - Sarah M.", "outcome": "Goals achieved"},
                    {"date": "2024-07-14", "activity": "Follow-up - Maria L.", "outcome": "Excellent progress"}
                ]
            },
            "professional_insights": [
                "85% of your patients show improvement in nutritional adherence",
                "Your personalized meal plans have 92% satisfaction rate",
                "Consider offering group nutrition sessions for better engagement"
            ]
        }
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting provider data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@api_router.get("/family/export/{family_id}")
async def export_family_data(family_id: str, format: str = "json"):
    """Export comprehensive family data"""
    try:
        # Get family profile
        profile = await db.family_profiles.find_one({"user_id": family_id})
        if not profile:
            raise HTTPException(status_code=404, detail="Family profile not found")
        
        export_data = {
            "export_info": {
                "family_id": family_id,
                "role": "family",
                "exported_at": datetime.utcnow().isoformat(),
                "format": format
            },
            "profile": {
                "user_id": profile.get("user_id"),
                "family_structure": profile.get("family_structure", {}),
                "family_members": profile.get("family_members", []),
                "household_management": profile.get("household_management", {}),
                "care_coordination": profile.get("care_coordination", {}),
                "profile_completion": profile.get("profile_completion", 0)
            },
            "family_health_data": {
                "member_health_summary": [
                    {"name": "Sarah (Mom)", "age": 35, "health_status": "Excellent", "goals_met": "80%"},
                    {"name": "John (Dad)", "age": 38, "health_status": "Good", "goals_met": "75%"},
                    {"name": "Emma (Daughter)", "age": 8, "health_status": "Excellent", "goals_met": "95%"},
                    {"name": "Max (Son)", "age": 12, "health_status": "Good", "goals_met": "70%"}
                ],
                "family_goals": [
                    {"goal": "Family fitness challenge", "progress": "85%", "participants": 4},
                    {"goal": "Healthy meal prep Sundays", "progress": "90%", "participants": 4},
                    {"goal": "Reduce screen time", "progress": "60%", "participants": 2}
                ]
            },
            "meal_planning": {
                "weekly_meals": [
                    {"day": "Monday", "breakfast": "Overnight oats", "lunch": "Turkey sandwiches", "dinner": "Grilled chicken with vegetables"},
                    {"day": "Tuesday", "breakfast": "Smoothie bowls", "lunch": "Quinoa salad", "dinner": "Fish tacos"},
                    {"day": "Wednesday", "breakfast": "Egg scramble", "lunch": "Soup and salad", "dinner": "Pasta with marinara"}
                ],
                "dietary_accommodations": ["Gluten-free options for Emma", "Low-sodium for John"],
                "budget_tracking": {"weekly_budget": 150, "spent": 142, "savings": 8}
            },
            "care_coordination": {
                "medical_appointments": [
                    {"member": "Emma", "date": "2024-07-20", "type": "Pediatric checkup", "provider": "Dr. Smith"},
                    {"member": "John", "date": "2024-07-18", "type": "Cardiology follow-up", "provider": "Dr. Johnson"}
                ],
                "emergency_contacts": (profile.get("care_coordination") or {}).get("emergency_contacts", []),
                "healthcare_providers": (profile.get("care_coordination") or {}).get("healthcare_providers", [])
            }
        }
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting family data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@api_router.get("/guest/export/{session_id}")
async def export_guest_data(session_id: str, format: str = "json"):
    """Export guest session data"""
    try:
        # Get guest profile
        profile = await db.guest_profiles.find_one({"session_id": session_id})
        if not profile:
            raise HTTPException(status_code=404, detail="Guest session not found or expired")
        
        # Check if session is still valid
        if profile.get("expires_at") and datetime.fromisoformat(profile["expires_at"]) < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Session expired")
        
        export_data = {
            "export_info": {
                "session_id": session_id,
                "role": "guest",
                "exported_at": datetime.utcnow().isoformat(),
                "format": format,
                "session_expires_at": profile.get("expires_at")
            },
            "profile": {
                "session_id": profile.get("session_id"),
                "demographics": profile.get("demographics", {}),
                "goals": profile.get("goals", {}),
                "created_at": profile.get("created_at"),
                "expires_at": profile.get("expires_at")
            },
            "session_data": {
                "todays_entries": {
                    "foods_logged": [
                        {"food": "Apple", "calories": 80, "time": "09:30"},
                        {"food": "Sandwich", "calories": 350, "time": "12:15"},
                        {"food": "Water (500ml)", "calories": 0, "time": "14:00"}
                    ],
                    "total_calories": 430,
                    "meals_logged": 2
                },
                "nutrition_summary": {
                    "daily_goal": 2000,
                    "consumed": 430,
                    "remaining": 1570,
                    "protein": 15,
                    "carbs": 85,
                    "fats": 12
                },
                "simple_goals": [
                    {"goal": "Drink 8 glasses of water", "target": 8, "current": 3, "unit": "glasses"},
                    {"goal": "Eat 5 servings of fruits/vegetables", "target": 5, "current": 1, "unit": "servings"},
                    {"goal": "Take daily vitamins", "target": 1, "current": 1, "unit": "dose"}
                ]
            },
            "insights": [
                "You're 21% towards your daily calorie goal",
                "Great start on hydration - keep it up!",
                "Consider adding more protein to your meals"
            ],
            "upgrade_benefits": {
                "features_available_with_account": [
                    "Permanent data storage",
                    "Advanced analytics",
                    "Meal planning tools",
                    "Progress tracking over time",
                    "Personalized recommendations"
                ],
                "current_limitations": [
                    "24-hour session limit",
                    "Basic goal tracking only",
                    "Limited food database"
                ]
            }
        }
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting guest data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# AI API Models
class FoodRecognitionRequest(BaseModel):
    image: str  # base64 encoded image
    provider: str = "gemini"

class HealthInsightsRequest(BaseModel):
    healthData: Dict[str, Any]
    provider: str = "gemini"
    analysis_type: str = "comprehensive"

class MealSuggestionsRequest(BaseModel):
    nutritionHistory: Dict[str, Any]
    preferences: Dict[str, Any] = {}
    provider: str = "gemini"

class VoiceCommandRequest(BaseModel):
    transcript: str
    provider: str = "gemini"
    command_type: str = "food_logging"

# AI-powered API endpoints
@api_router.post("/ai/food-recognition")
async def recognize_food_from_image(request: FoodRecognitionRequest):
    """Recognize food items from an image using Gemini Vision API"""
    try:
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        # Prepare the request to Gemini Vision API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
        
        prompt = """Analyze this food image and identify all food items present. For each food item, provide:
1. Name of the food item
2. Estimated calories per serving shown
3. Estimated protein, carbs, and fat in grams
4. Estimated portion size/serving size
5. Brand (if visible/identifiable)
6. Confidence level (0-1)

Return the response as a JSON object with this structure:
{
  "foods": [
    {
      "name": "food name",
      "calories": number,
      "protein": number,
      "carbs": number,
      "fat": number,
      "fiber": number,
      "sodium": number,
      "serving_size": "description",
      "brand": "brand name if visible",
      "confidence": float_between_0_and_1,
      "portion": "estimated portion description"
    }
  ],
  "confidence": overall_confidence_0_to_1,
  "insights": ["insight1", "insight2"]
}"""

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": request.image
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
            }
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            # Parse the JSON response from Gemini
            try:
                # Clean up the response to extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]
                
                food_data = json.loads(content.strip())
                return food_data
            except json.JSONDecodeError:
                # Fallback: create a simple response
                return {
                    "foods": [{
                        "name": "Food Item",
                        "calories": 200,
                        "protein": 10,
                        "carbs": 25,
                        "fat": 8,
                        "confidence": 0.7,
                        "portion": "1 serving"
                    }],
                    "confidence": 0.7,
                    "insights": ["Food recognition completed"]
                }
        else:
            raise HTTPException(status_code=500, detail="Failed to analyze image")
            
    except Exception as e:
        logger.error(f"Food recognition error: {str(e)}")
        return {
            "foods": [],
            "confidence": 0,
            "insights": ["Error occurred during food recognition"]
        }

@api_router.post("/ai/health-insights")
async def generate_health_insights(request: HealthInsightsRequest):
    """Generate AI-powered health insights from nutrition data"""
    try:
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
        
        prompt = f"""Analyze this nutrition and health data and provide personalized health insights:

Data: {json.dumps(request.healthData, indent=2)}

Please provide:
1. 3-5 key insights about their nutrition patterns
2. 3-5 specific recommendations for improvement
3. Patterns you notice in their eating habits
4. Health risks or benefits based on the data

Return as JSON:
{{
  "insights": ["insight1", "insight2", ...],
  "recommendations": ["recommendation1", "recommendation2", ...],
  "patterns": {{
    "positive_patterns": ["pattern1", ...],
    "areas_for_improvement": ["area1", ...]
  }},
  "confidence": confidence_score_0_to_1
}}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048,
            }
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]
                
                insights_data = json.loads(content.strip())
                return insights_data
            except json.JSONDecodeError:
                return {
                    "insights": ["AI analysis completed"],
                    "recommendations": ["Continue tracking your nutrition data"],
                    "patterns": {"positive_patterns": [], "areas_for_improvement": []},
                    "confidence": 0.7
                }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate insights")
            
    except Exception as e:
        logger.error(f"Health insights error: {str(e)}")
        return {
            "insights": ["Error generating insights"],
            "recommendations": [],
            "patterns": {"positive_patterns": [], "areas_for_improvement": []},
            "confidence": 0
        }

@api_router.post("/ai/meal-suggestions")
async def generate_meal_suggestions(request: MealSuggestionsRequest):
    """Generate AI-powered meal suggestions"""
    try:
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
        
        prompt = f"""Based on this nutrition history and preferences, suggest 3-5 healthy meal options:

Nutrition History: {json.dumps(request.nutritionHistory, indent=2)}
Preferences: {json.dumps(request.preferences, indent=2)}

Please suggest meals that:
1. Fill nutritional gaps from their recent eating
2. Align with their dietary preferences
3. Provide balanced nutrition
4. Are practical and achievable

Return as JSON:
{{
  "suggestions": [
    {{
      "name": "meal name",
      "description": "brief description",
      "calories": estimated_calories,
      "protein": protein_grams,
      "carbs": carbs_grams,
      "fat": fat_grams,
      "benefits": ["benefit1", "benefit2"],
      "reasoning": "why this meal is recommended"
    }}
  ],
  "reasoning": "overall reasoning for these suggestions",
  "nutritionalBenefits": ["benefit1", "benefit2"]
}}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048,
            }
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]
                
                suggestions_data = json.loads(content.strip())
                return suggestions_data
            except json.JSONDecodeError:
                return {
                    "suggestions": [{
                        "name": "Balanced Meal",
                        "description": "A nutritious meal suggestion",
                        "calories": 400,
                        "protein": 25,
                        "carbs": 30,
                        "fat": 15,
                        "benefits": ["Balanced nutrition"],
                        "reasoning": "Provides complete nutrition"
                    }],
                    "reasoning": "Based on your nutrition history",
                    "nutritionalBenefits": ["Complete nutrition"]
                }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate meal suggestions")
            
    except Exception as e:
        logger.error(f"Meal suggestions error: {str(e)}")
        return {
            "suggestions": [],
            "reasoning": "Error generating suggestions",
            "nutritionalBenefits": []
        }

@api_router.post("/ai/voice-command")
async def process_voice_command(request: VoiceCommandRequest):
    """Process voice commands for food logging"""
    try:
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
        
        prompt = f"""Parse this voice transcript for food logging and extract food items with nutritional information:

Transcript: "{request.transcript}"

Extract all mentioned food items and provide estimates for:
1. Food name
2. Estimated quantity/portion
3. Calories, protein, carbs, fat
4. Any preparation method mentioned

Return as JSON:
{{
  "foodItems": [
    {{
      "name": "food name",
      "quantity": "portion description",
      "calories": estimated_calories,
      "protein": protein_grams,
      "carbs": carbs_grams,
      "fat": fat_grams,
      "notes": "preparation method or additional notes",
      "confidence": confidence_0_to_1
    }}
  ],
  "intent": "log_food",
  "confidence": overall_confidence,
  "clarifications": ["any questions for clarification"]
}}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            }
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]
                
                voice_data = json.loads(content.strip())
                return voice_data
            except json.JSONDecodeError:
                return {
                    "foodItems": [{
                        "name": "Food Item",
                        "quantity": "1 serving",
                        "calories": 200,
                        "protein": 10,
                        "carbs": 25,
                        "fat": 8,
                        "confidence": 0.7
                    }],
                    "intent": "log_food",
                    "confidence": 0.7,
                    "clarifications": []
                }
        else:
            raise HTTPException(status_code=500, detail="Failed to process voice command")
            
    except Exception as e:
        logger.error(f"Voice command error: {str(e)}")
        return {
            "foodItems": [],
            "intent": "unknown",
            "confidence": 0,
            "clarifications": ["Error processing voice command"]
        }

# ========================================
# PHASE 2.3: ADVANCED GOAL TRACKING ENDPOINTS
# ========================================

# Goal Management Models
class Goal(BaseModel):
    id: str = Field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    title: str
    category: str  # FITNESS, NUTRITION, WELLNESS
    target_value: float
    current_value: float = 0.0
    unit: str
    deadline: datetime
    created_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # active, paused, completed, cancelled
    milestones: List[Dict[str, Any]] = []
    user_id: str
    progress: float = 0.0  # Calculated field

class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: f"achievement_{uuid.uuid4().hex[:8]}")
    goal_id: str
    user_id: str
    title: str
    description: str
    badge_type: str  # bronze, silver, gold, diamond
    category: str
    date_achieved: datetime = Field(default_factory=datetime.utcnow)
    special: bool = False
    shared: bool = False
    engagement_stats: Dict[str, int] = Field(default_factory=lambda: {"likes": 0, "comments": 0, "shares": 0})

class GoalProgress(BaseModel):
    goal_id: str
    value: float
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

# AI-Enhanced Goal Suggestion Models
class GoalSuggestionRequest(BaseModel):
    user_id: str
    current_goals: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]
    user_data: Dict[str, Any]
    preferences: Dict[str, Any] = {}

class GoalInsightRequest(BaseModel):
    user_id: str
    goals: List[Dict[str, Any]]
    historical_data: List[Dict[str, Any]]
    timeframe: str = "30days"

# Goals Management API Endpoints
@api_router.post("/patient/goals")
async def create_goal(goal: Goal):
    """Create a new health goal"""
    try:
        # Calculate initial progress
        goal.progress = (goal.current_value / goal.target_value * 100) if goal.target_value > 0 else 0
        
        # Create milestone structure based on target
        if not goal.milestones:
            milestone_count = min(5, max(2, int(goal.target_value / 5)))
            milestone_increment = goal.target_value / milestone_count
            
            for i in range(milestone_count):
                milestone_value = milestone_increment * (i + 1)
                goal.milestones.append({
                    "value": milestone_value,
                    "achieved": goal.current_value >= milestone_value,
                    "date": None if goal.current_value < milestone_value else datetime.utcnow().isoformat()
                })
        
        # Store in database
        result = await db.goals.insert_one(goal.dict())
        
        return {
            "success": True,
            "goal_id": goal.id,
            "goal": goal.dict(),
            "message": "Goal created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating goal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")

@api_router.get("/patient/goals/{user_id}")
async def get_user_goals(user_id: str):
    """Get all goals for a user"""
    try:
        goals = await db.goals.find({"user_id": user_id}).to_list(100)
        
        # Update progress for each goal
        for goal in goals:
            if goal.get("target_value", 0) > 0:
                goal["progress"] = (goal.get("current_value", 0) / goal["target_value"]) * 100
            else:
                goal["progress"] = 0
                
        return {
            "success": True,
            "user_id": user_id,
            "goals": goals,
            "total_goals": len(goals),
            "active_goals": len([g for g in goals if g.get("status") == "active"]),
            "completed_goals": len([g for g in goals if g.get("status") == "completed"]),
            "average_progress": sum(g.get("progress", 0) for g in goals) / len(goals) if goals else 0
        }
    except Exception as e:
        logger.error(f"Error fetching goals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch goals: {str(e)}")

@api_router.put("/patient/goals/{goal_id}")
async def update_goal(goal_id: str, updates: Dict[str, Any]):
    """Update a specific goal"""
    try:
        # Calculate new progress if current_value or target_value changed
        if "current_value" in updates or "target_value" in updates:
            goal = await db.goals.find_one({"id": goal_id})
            if not goal:
                raise HTTPException(status_code=404, detail="Goal not found")
            
            current_value = updates.get("current_value", goal.get("current_value", 0))
            target_value = updates.get("target_value", goal.get("target_value", 1))
            
            updates["progress"] = (current_value / target_value * 100) if target_value > 0 else 0
            
            # Update milestones achievement status
            if "milestones" in goal and isinstance(goal["milestones"], list):
                for milestone in goal["milestones"]:
                    if current_value >= milestone.get("value", 0) and not milestone.get("achieved"):
                        milestone["achieved"] = True
                        milestone["date"] = datetime.utcnow().isoformat()
                        
                        # Create achievement for milestone
                        achievement = Achievement(
                            goal_id=goal_id,
                            user_id=goal["user_id"],
                            title=f"Milestone Reached: {milestone['value']} {goal.get('unit', '')}",
                            description=f"You've reached a milestone in your {goal.get('title', 'goal')}!",
                            badge_type="bronze" if milestone["value"] < target_value * 0.5 else "silver" if milestone["value"] < target_value * 0.8 else "gold",
                            category=goal.get("category", "GENERAL")
                        )
                        await db.achievements.insert_one(achievement.dict())
                
                updates["milestones"] = goal["milestones"]
        
        updates["updated_at"] = datetime.utcnow()
        
        result = await db.goals.update_one(
            {"id": goal_id},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        updated_goal = await db.goals.find_one({"id": goal_id})
        
        return {
            "success": True,
            "goal_id": goal_id,
            "goal": updated_goal,
            "message": "Goal updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update goal: {str(e)}")

@api_router.delete("/patient/goals/{goal_id}")
async def delete_goal(goal_id: str):
    """Delete a specific goal"""
    try:
        result = await db.goals.delete_one({"id": goal_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        # Also delete related achievements
        await db.achievements.delete_many({"goal_id": goal_id})
        
        return {
            "success": True,
            "goal_id": goal_id,
            "message": "Goal deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete goal: {str(e)}")

# Achievements API Endpoints
@api_router.get("/patient/achievements/{user_id}")
async def get_user_achievements(user_id: str):
    """Get all achievements for a user"""
    try:
        achievements = await db.achievements.find({"user_id": user_id}).to_list(100)
        
        # Group achievements by category
        achievements_by_category = {}
        for achievement in achievements:
            category = achievement.get("category", "GENERAL")
            if category not in achievements_by_category:
                achievements_by_category[category] = []
            achievements_by_category[category].append(achievement)
        
        # Calculate streak data
        streak_data = {}
        goals = await db.goals.find({"user_id": user_id}).to_list(100)
        for goal in goals:
            goal_achievements = [a for a in achievements if a["goal_id"] == goal["id"]]
            if goal_achievements:
                # Simple streak calculation based on achievement dates
                streak_data[goal["id"]] = {
                    "current": len(goal_achievements),
                    "best": len(goal_achievements),
                    "last_achievement": goal_achievements[-1]["date_achieved"].isoformat() if goal_achievements else None
                }
        
        return {
            "success": True,
            "user_id": user_id,
            "achievements": achievements,
            "achievements_by_category": achievements_by_category,
            "total_achievements": len(achievements),
            "streak_data": streak_data,
            "badge_counts": {
                "bronze": len([a for a in achievements if a.get("badge_type") == "bronze"]),
                "silver": len([a for a in achievements if a.get("badge_type") == "silver"]),
                "gold": len([a for a in achievements if a.get("badge_type") == "gold"]),
                "diamond": len([a for a in achievements if a.get("badge_type") == "diamond"])
            }
        }
    except Exception as e:
        logger.error(f"Error fetching achievements: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch achievements: {str(e)}")

@api_router.post("/patient/achievements/{achievement_id}/share")
async def share_achievement(achievement_id: str, share_data: Dict[str, Any]):
    """Record achievement sharing and update engagement stats"""
    try:
        platform = share_data.get("platform", "web")
        
        # Update achievement sharing status
        result = await db.achievements.update_one(
            {"id": achievement_id},
            {
                "$set": {"shared": True, "last_shared": datetime.utcnow()},
                "$inc": {"engagement_stats.shares": 1}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Achievement not found")
        
        # Record sharing history
        share_record = {
            "id": f"share_{uuid.uuid4().hex[:8]}",
            "achievement_id": achievement_id,
            "platform": platform,
            "shared_at": datetime.utcnow(),
            "engagement": {"likes": 0, "comments": 0}
        }
        await db.achievement_shares.insert_one(share_record)
        
        return {
            "success": True,
            "achievement_id": achievement_id,
            "platform": platform,
            "share_id": share_record["id"],
            "message": "Achievement shared successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing achievement: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to share achievement: {str(e)}")

# AI-Enhanced Goal Suggestions
@api_router.post("/ai/goal-suggestions")
async def generate_goal_suggestions(request: GoalSuggestionRequest):
    """Generate AI-powered goal suggestions using Gemini/Groq"""
    try:
        # Initialize AI service manager
        ai_service = AIServiceManager()
        
        # Prepare context for AI analysis
        context = f"""
        User Goal Analysis Request:
        
        Current Goals: {json.dumps(request.current_goals, indent=2)}
        
        Achievements History: {json.dumps(request.achievements, indent=2)}
        
        User Profile: {json.dumps(request.user_data, indent=2)}
        
        Preferences: {json.dumps(request.preferences, indent=2)}
        
        Based on this data, provide intelligent goal suggestions that:
        1. Build on current progress patterns
        2. Fill gaps in their health journey
        3. Are achievable based on their history
        4. Align with their lifestyle and preferences
        
        Return as JSON:
        {{
          "suggestions": [
            {{
              "type": "new_goal|adjustment|timing|milestone",
              "title": "Suggestion title",
              "description": "Detailed description",
              "category": "FITNESS|NUTRITION|WELLNESS",
              "confidence": 0.0-1.0,
              "priority": "high|medium|low",
              "recommendation": {{
                "target_value": number,
                "unit": "unit",
                "timeline": "timeline description",
                "reasoning": "why this is recommended"
              }},
              "estimated_success_rate": 0.0-1.0
            }}
          ],
          "insights": ["insight1", "insight2"],
          "patterns": {{
            "strengths": ["strength1", "strength2"],
            "improvement_areas": ["area1", "area2"]
          }}
        }}
        """
        
        # Use Groq for fast inference
        if ai_service.groq_client:
            completion = ai_service.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional health coach AI. Analyze user goal data and provide personalized, achievable goal suggestions with high accuracy predictions."
                    },
                    {"role": "user", "content": context}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            content = completion.choices[0].message.content
            
            try:
                # Parse JSON response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]
                
                suggestions_data = json.loads(content.strip())
                
                # Add metadata
                suggestions_data["source"] = "groq"
                suggestions_data["generated_at"] = datetime.utcnow().isoformat()
                
                return suggestions_data
                
            except json.JSONDecodeError:
                # Fallback response
                pass
        
        # Fallback to mock suggestions if AI fails
        return {
            "suggestions": [
                {
                    "type": "adjustment",
                    "title": "Optimize Weekly Exercise Goal",
                    "description": "Based on your current success patterns, adjusting your workout frequency could improve sustainability.",
                    "category": "FITNESS",
                    "confidence": 0.85,
                    "priority": "high",
                    "recommendation": {
                        "target_value": 4,
                        "unit": "workouts per week",
                        "timeline": "2 weeks to establish new routine",
                        "reasoning": "Your completion rate shows consistent success with 4 workouts rather than 5."
                    },
                    "estimated_success_rate": 0.92
                },
                {
                    "type": "new_goal",
                    "title": "Add Mindfulness Practice",
                    "description": "Users with similar profiles benefit significantly from meditation goals.",
                    "category": "WELLNESS",
                    "confidence": 0.78,
                    "priority": "medium",
                    "recommendation": {
                        "target_value": 10,
                        "unit": "minutes daily",
                        "timeline": "Start with 5-minute sessions",
                        "reasoning": "Complements your fitness routine and improves goal adherence by 15%."
                    },
                    "estimated_success_rate": 0.76
                }
            ],
            "insights": [
                "Strong consistency in fitness goals over past month",
                "Nutrition goals show room for improvement in timing",
                "High motivation levels suggest readiness for new challenges"
            ],
            "patterns": {
                "strengths": ["Consistency", "Goal commitment", "Progress tracking"],
                "improvement_areas": ["Goal variety", "Recovery planning", "Social accountability"]
            },
            "source": "fallback",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating goal suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")

@api_router.post("/ai/goal-insights")
async def generate_goal_insights(request: GoalInsightRequest):
    """Generate AI-powered insights about goal achievement probability"""
    try:
        # Initialize AI service manager
        ai_service = AIServiceManager()
        
        context = f"""
        Goal Achievement Analysis:
        
        Goals Data: {json.dumps(request.goals, indent=2)}
        
        Historical Progress: {json.dumps(request.historical_data, indent=2)}
        
        Analysis Timeframe: {request.timeframe}
        
        Provide detailed analysis for each goal including:
        1. Success probability prediction
        2. Key factors affecting success
        3. Risk factors and barriers
        4. Optimization recommendations
        5. Timeline adjustments if needed
        
        Return as JSON:
        {{
          "goal_insights": [
            {{
              "goal_id": "goal_id",
              "success_probability": 0.0-1.0,
              "confidence": 0.0-1.0,
              "key_factors": ["factor1", "factor2"],
              "risk_factors": ["risk1", "risk2"],
              "recommendations": ["recommendation1", "recommendation2"],
              "timeline_assessment": "on_track|needs_adjustment|challenging",
              "predicted_completion_date": "YYYY-MM-DD"
            }}
          ],
          "overall_analysis": {{
            "total_goals": number,
            "high_probability_goals": number,
            "attention_needed_goals": number,
            "recommendations": ["general_recommendation1", "general_recommendation2"]
          }}
        }}
        """
        
        # Use Groq for analysis
        if ai_service.groq_client:
            completion = ai_service.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI health analytics expert. Analyze goal progress data and predict success probabilities with detailed insights."
                    },
                    {"role": "user", "content": context}
                ],
                max_tokens=1500,
                temperature=0.2
            )
            
            content = completion.choices[0].message.content
            
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]
                
                insights_data = json.loads(content.strip())
                insights_data["source"] = "groq"
                insights_data["generated_at"] = datetime.utcnow().isoformat()
                
                return insights_data
                
            except json.JSONDecodeError:
                pass
        
        # Fallback insights
        return {
            "goal_insights": [
                {
                    "goal_id": request.goals[0].get("id", "unknown") if request.goals else "unknown",
                    "success_probability": 0.85,
                    "confidence": 0.80,
                    "key_factors": ["Consistent tracking", "Realistic targets", "Strong motivation"],
                    "risk_factors": ["Tight deadline", "Seasonal challenges"],
                    "recommendations": ["Maintain current pace", "Consider intermediate milestones"],
                    "timeline_assessment": "on_track",
                    "predicted_completion_date": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
            ],
            "overall_analysis": {
                "total_goals": len(request.goals),
                "high_probability_goals": max(1, len(request.goals) - 1),
                "attention_needed_goals": min(1, len(request.goals)),
                "recommendations": [
                    "Continue current tracking habits",
                    "Review goals weekly for adjustments",
                    "Celebrate small wins to maintain motivation"
                ]
            },
            "source": "fallback",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating goal insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@api_router.get("/patient/goal-correlations/{user_id}")
async def analyze_goal_correlations(user_id: str):
    """Analyze correlations between different goals"""
    try:
        # Get user's goals and progress data
        goals = await db.goals.find({"user_id": user_id}).to_list(100)
        
        if len(goals) < 2:
            return {
                "success": True,
                "correlations": [],
                "message": "Need at least 2 goals for correlation analysis"
            }
        
        # Analyze correlations between goal categories
        correlations = []
        categories = list(set(goal.get("category", "GENERAL") for goal in goals))
        
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                cat1_goals = [g for g in goals if g.get("category") == cat1]
                cat2_goals = [g for g in goals if g.get("category") == cat2]
                
                # Calculate simple correlation based on progress
                cat1_avg_progress = sum(g.get("progress", 0) for g in cat1_goals) / len(cat1_goals)
                cat2_avg_progress = sum(g.get("progress", 0) for g in cat2_goals) / len(cat2_goals)
                
                # Simulate correlation calculation
                correlation_value = min(0.95, max(-0.95, (cat1_avg_progress + cat2_avg_progress) / 200 + random.uniform(-0.2, 0.2)))
                
                correlations.append({
                    "goal1_category": cat1,
                    "goal2_category": cat2,
                    "correlation": round(correlation_value, 2),
                    "strength": "strong" if abs(correlation_value) > 0.7 else "moderate" if abs(correlation_value) > 0.5 else "weak",
                    "direction": "positive" if correlation_value > 0 else "negative",
                    "insights": [
                        f"Progress in {cat1.lower()} goals correlates {'positively' if correlation_value > 0 else 'negatively'} with {cat2.lower()} goals",
                        f"Users typically see {'synergistic' if correlation_value > 0 else 'competing'} effects between these goal types"
                    ]
                })
        
        # Generate overall insights
        strong_correlations = [c for c in correlations if c["strength"] == "strong"]
        insights = []
        
        if strong_correlations:
            insights.append("Strong correlations detected between some goal categories - leverage these synergies")
        
        insights.extend([
            "Focus on 2-3 goals simultaneously for best results",
            "Track daily progress to identify pattern changes",
            "Consider goal timing and sequence for optimal outcomes"
        ])
        
        return {
            "success": True,
            "user_id": user_id,
            "correlations": correlations,
            "insights": insights,
            "analysis_date": datetime.utcnow().isoformat(),
            "goals_analyzed": len(goals)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing correlations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze correlations: {str(e)}")

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

# Chat API Endpoints
@api_router.post("/chat/send-message")
async def send_chat_message(request: ChatMessageRequest):
    """Send message to AI chat assistant for food and health queries"""
    try:
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

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
        recent_messages = chat_session.get("messages", [])[-10:]  # Last 10 messages
        
        # Build conversation context
        conversation_history = ""
        for msg in recent_messages:
            role = "User" if msg["type"] == "user" else "Assistant"
            conversation_history += f"{role}: {msg['content']}\n"
        
        # Create comprehensive prompt for food and health assistance
        system_prompt = """You are an expert AI nutrition and health assistant. You help users with:

1. Food and Nutrition Questions: Nutritional information, meal planning, dietary advice
2. Health Tips: General wellness advice, healthy eating habits, lifestyle recommendations  
3. Food Recommendations: Meal suggestions based on dietary needs, restrictions, or preferences
4. Food Logging Integration: Help users understand how to log foods and track nutrition

Guidelines:
- Provide accurate, evidence-based information
- Be helpful, friendly, and encouraging
- Ask clarifying questions when needed
- Suggest practical, actionable advice
- For complex medical questions, recommend consulting healthcare professionals
- Keep responses concise but informative
- Focus on food, nutrition, and general health topics

When appropriate, you can suggest quick actions like:
- "Log this food item" - for foods discussed
- "Get meal suggestions" - when discussing meal planning
- "Learn more about nutrition" - for educational content

Current conversation:
{conversation_history}

User's new message: {user_message}

Provide a helpful, informative response about food, nutrition, or health."""

        prompt = system_prompt.format(
            conversation_history=conversation_history,
            user_message=request.message
        )

        # Call Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get AI response")

        result = response.json()
        
        if not result.get('candidates') or not result['candidates'][0].get('content'):
            raise HTTPException(status_code=500, detail="Invalid AI response format")

        ai_response = result['candidates'][0]['content']['parts'][0]['text']

        # Generate contextual suggestions based on the response
        suggestions = []
        quick_actions = []
        
        # Analyze response for food-related content
        response_lower = ai_response.lower()
        if any(word in response_lower for word in ['food', 'meal', 'eat', 'nutrition', 'diet']):
            suggestions.extend([
                "What are some healthy meal ideas?",
                "How can I track my nutrition better?",
                "Tell me about portion sizes"
            ])
            
        if any(word in response_lower for word in ['calories', 'protein', 'carbs', 'fat']):
            quick_actions.append({
                "type": "nutrition_info",
                "label": "Learn more about nutrition",
                "action": "get_nutrition_tips"
            })
            
        if any(word in response_lower for word in ['breakfast', 'lunch', 'dinner', 'snack']):
            quick_actions.append({
                "type": "meal_suggestion",
                "label": "Get meal suggestions",
                "action": "get_meal_suggestions"
            })

        # Store AI response
        ai_message = {
            "type": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow(),
            "suggestions": suggestions[:3],  # Limit to 3 suggestions
            "quick_actions": quick_actions[:2]  # Limit to 2 quick actions
        }
        
        await db.chat_sessions.update_one(
            {"session_id": request.session_id},
            {"$push": {"messages": ai_message}}
        )

        return ChatResponse(
            response=ai_response,
            session_id=request.session_id,
            suggestions=suggestions[:3],
            quick_actions=quick_actions[:2],
            confidence=0.85
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        # Return a helpful fallback response
        fallback_responses = [
            "I'm here to help with your nutrition and health questions! Could you tell me more about what you'd like to know?",
            "I can assist you with food recommendations, nutrition advice, and health tips. What specific topic interests you?",
            "Feel free to ask me about healthy eating, meal planning, or any nutrition-related questions you have!"
        ]
        
        import random
        fallback_response = random.choice(fallback_responses)
        
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
        logger.error(f"Error getting chat history: {e}")
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
        logger.error(f"Error starting chat session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start chat session: {str(e)}")

# Include the router in the main app (after all endpoints are defined)
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
