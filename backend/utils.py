import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import secrets

def extract_user_info_from_text(text: str) -> Dict[str, Any]:
    """Extract age and sex information from user text"""
    result = {"age": None, "sex": None}
    
    # Extract age
    age_patterns = [
        r'i am (\d+)',
        r'(\d+) years? old',
        r'age (\d+)',
        r'(\d+)y/o',
        r'(\d+)\s*yr',
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, text.lower())
        if match:
            age = int(match.group(1))
            if 0 < age < 120:  # Reasonable age range
                result["age"] = age
                break
    
    # Extract sex
    text_lower = text.lower()
    if any(word in text_lower for word in ['female', 'woman', 'girl', 'she', 'her']):
        result["sex"] = "female"
    elif any(word in text_lower for word in ['male', 'man', 'boy', 'he', 'him']):
        result["sex"] = "male"
    
    return result

def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage"""
    return hashlib.sha256(data.encode()).hexdigest()

def clean_medical_text(text: str) -> str:
    """Clean and sanitize medical text input"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove potentially harmful characters but keep medical terminology
    text = re.sub(r'[<>{}[\]\\]', '', text)
    
    return text

def validate_age(age: int) -> bool:
    """Validate age input"""
    return 0 < age < 120

def validate_symptoms_text(text: str) -> bool:
    """Validate symptoms text input"""
    if not text or len(text.strip()) < 5:
        return False
    
    if len(text) > 2000:  # Reasonable limit
        return False
    
    return True

def format_timestamp(dt: datetime) -> str:
    """Format timestamp for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from AI response text"""
    try:
        # Look for JSON block in response
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            json_str = match.group()
            return json.loads(json_str)
        
        return None
    except json.JSONDecodeError:
        return None

def detect_emergency_symptoms(text: str) -> bool:
    """Detect emergency symptoms in text"""
    emergency_indicators = [
        # Cardiovascular
        'chest pain', 'heart attack', 'cardiac arrest', 'severe chest pressure',
        
        # Respiratory
        'can\'t breathe', 'difficulty breathing', 'shortness of breath', 'choking',
        
        # Neurological
        'stroke', 'sudden weakness', 'facial drooping', 'speech problems',
        'severe headache', 'loss of consciousness', 'seizure',
        
        # Trauma
        'severe bleeding', 'major injury', 'broken bone', 'head injury',
        
        # Allergic/Anaphylaxis
        'allergic reaction', 'swelling throat', 'difficulty swallowing',
        'severe rash', 'hives all over',
        
        # Other emergencies
        'overdose', 'poisoning', 'suicide', 'self harm',
        'severe abdominal pain', 'vomiting blood', 'rectal bleeding'
    ]
    
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in emergency_indicators)

def get_medical_disclaimer() -> str:
    """Get standard medical disclaimer text"""
    return ("This AI assistant provides general health information and is not a substitute for "
            "professional medical advice, diagnosis, or treatment. Always seek the advice of "
            "qualified health professionals for any medical concerns. In case of emergency, "
            "call 911 or your local emergency services immediately.")

def sanitize_diagnosis_data(diagnosis_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sanitize and validate diagnosis data"""
    sanitized = []
    
    for diag in diagnosis_list:
        if not isinstance(diag, dict):
            continue
            
        sanitized_diag = {
            "condition": str(diag.get("condition", "Unknown condition"))[:100],
            "probability": max(0, min(100, int(diag.get("probability", 0)))),
            "description": str(diag.get("description", ""))[:500],
            "symptoms": [str(s)[:100] for s in diag.get("symptoms", [])[:10]],
            "treatment_options": [str(t)[:200] for t in diag.get("treatment_options", [])[:10]],
            "urgency_level": diag.get("urgency_level", "medium")
        }
        
        sanitized.append(sanitized_diag)
    
    return sanitized[:5]  # Limit to 5 diagnoses

def calculate_response_confidence(diagnosis_list: List[Dict[str, Any]]) -> float:
    """Calculate overall confidence score for diagnoses"""
    if not diagnosis_list:
        return 0.0
    
    # Weight by probability and number of diagnoses
    total_prob = sum(d.get("probability", 0) for d in diagnosis_list)
    avg_prob = total_prob / len(diagnosis_list)
    
    # Confidence decreases with more diagnoses (more uncertainty)
    confidence_factor = max(0.5, 1.0 - (len(diagnosis_list) - 1) * 0.1)
    
    return min(100.0, avg_prob * confidence_factor)

def format_medical_response(analysis_data: Dict[str, Any]) -> str:
    """Format comprehensive medical response"""
    parts = []
    
    # Add main response
    if "response_text" in analysis_data:
        parts.append(analysis_data["response_text"])
    
    # Add diagnosis section
    diagnoses = analysis_data.get("diagnosis", [])
    if diagnoses:
        parts.append("\n**Possible Conditions:**")
        for diag in diagnoses:
            parts.append(f"\n**{diag.get('condition')}** ({diag.get('probability')}% probability)")
            if diag.get('description'):
                parts.append(f"• {diag['description']}")
    
    # Add recommendations
    recommendations = analysis_data.get("recommendations", [])
    if recommendations:
        parts.append("\n**Recommendations:**")
        for rec in recommendations:
            parts.append(f"✓ {rec}")
    
    # Add emergency warning
    if analysis_data.get("emergency_detected"):
        parts.append("\n🚨 **EMERGENCY DETECTED** - Seek immediate medical attention!")
    
    # Add disclaimer
    parts.append(f"\n📋 {get_medical_disclaimer()}")
    
    return "\n".join(parts)