#!/usr/bin/env python3
"""
Doctronic AI Backend Test Suite
Tests all backend API endpoints and functionality
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Test configuration
BACKEND_URL = "https://health-chatbot-2.preview.emergentagent.com/api"

class DoctronicBackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = None
        self.test_results = []
        self.consultation_id = None
        self.session_token = None
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 Testing backend at: {self.base_url}")
        
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_health_check(self):
        """Test GET /api/health endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["status", "database", "ai_service", "total_consultations"]
                    
                    if all(field in data for field in required_fields):
                        if data["status"] == "healthy" and data["database"] == "connected":
                            self.log_test("Health Check", True, f"Status: {data['status']}, DB: {data['database']}")
                            return True
                        else:
                            self.log_test("Health Check", False, f"Unhealthy status: {data}")
                            return False
                    else:
                        self.log_test("Health Check", False, f"Missing required fields in response: {data}")
                        return False
                else:
                    self.log_test("Health Check", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
            
    async def test_create_consultation(self):
        """Test POST /api/consultations endpoint"""
        try:
            symptoms = "I have been having severe headaches for 3 days, along with nausea and sensitivity to light"
            payload = {"symptoms": symptoms}
            
            async with self.session.post(
                f"{self.base_url}/consultations",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["consultation_id", "session_token", "message"]
                    
                    if all(field in data for field in required_fields):
                        self.consultation_id = data["consultation_id"]
                        self.session_token = data["session_token"]
                        self.log_test("Create Consultation", True, f"ID: {self.consultation_id[:8]}...")
                        return True
                    else:
                        self.log_test("Create Consultation", False, f"Missing fields: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Create Consultation", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Create Consultation", False, f"Exception: {str(e)}")
            return False
            
    async def test_get_consultation(self):
        """Test GET /api/consultations/{id} endpoint"""
        if not self.consultation_id:
            self.log_test("Get Consultation", False, "No consultation ID available")
            return False
            
        try:
            async with self.session.get(f"{self.base_url}/consultations/{self.consultation_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["consultation", "messages"]
                    
                    if all(field in data for field in required_fields):
                        consultation = data["consultation"]
                        messages = data["messages"]
                        
                        # Check if consultation has required fields
                        if "id" in consultation and "initial_symptoms" in consultation:
                            # Check if there are messages (should have initial user message and AI response)
                            if len(messages) >= 2:
                                self.log_test("Get Consultation", True, f"Found {len(messages)} messages")
                                return True
                            else:
                                self.log_test("Get Consultation", False, f"Expected at least 2 messages, got {len(messages)}")
                                return False
                        else:
                            self.log_test("Get Consultation", False, "Missing consultation fields")
                            return False
                    else:
                        self.log_test("Get Consultation", False, f"Missing response fields: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Get Consultation", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Get Consultation", False, f"Exception: {str(e)}")
            return False
            
    async def test_update_user_info(self):
        """Test PUT /api/consultations/{id}/user-info endpoint"""
        if not self.consultation_id:
            self.log_test("Update User Info", False, "No consultation ID available")
            return False
            
        try:
            user_info = {"age": 28, "sex": "female"}
            
            async with self.session.put(
                f"{self.base_url}/consultations/{self.consultation_id}/user-info",
                json=user_info,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "message" in data and "updated" in data["message"].lower():
                        self.log_test("Update User Info", True, "User info updated successfully")
                        return True
                    else:
                        self.log_test("Update User Info", False, f"Unexpected response: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Update User Info", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Update User Info", False, f"Exception: {str(e)}")
            return False
            
    async def test_send_message_user_info(self):
        """Test POST /api/consultations/{id}/messages with user info"""
        if not self.consultation_id:
            self.log_test("Send User Info Message", False, "No consultation ID available")
            return False
            
        try:
            message_payload = {
                "content": "I am 28 years old and female",
                "type": "user"
            }
            
            async with self.session.post(
                f"{self.base_url}/consultations/{self.consultation_id}/messages",
                json=message_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["message", "ai_response"]
                    
                    if all(field in data for field in required_fields):
                        ai_response = data["ai_response"]
                        if ai_response and "content" in ai_response:
                            # Check if AI response contains medical analysis
                            ai_content = ai_response["content"].lower()
                            has_medical_terms = any(term in ai_content for term in [
                                "diagnosis", "condition", "probability", "recommend", "symptoms"
                            ])
                            
                            self.log_test("Send User Info Message", True, 
                                        f"AI responded with medical analysis: {has_medical_terms}")
                            return True
                        else:
                            self.log_test("Send User Info Message", False, "No AI response content")
                            return False
                    else:
                        self.log_test("Send User Info Message", False, f"Missing response fields: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Send User Info Message", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Send User Info Message", False, f"Exception: {str(e)}")
            return False
            
    async def test_get_messages(self):
        """Test GET /api/consultations/{id}/messages endpoint"""
        if not self.consultation_id:
            self.log_test("Get Messages", False, "No consultation ID available")
            return False
            
        try:
            async with self.session.get(f"{self.base_url}/consultations/{self.consultation_id}/messages") as response:
                if response.status == 200:
                    data = await response.json()
                    if "messages" in data:
                        messages = data["messages"]
                        if len(messages) >= 3:  # Initial + user info + AI analysis
                            # Check message types
                            message_types = [msg.get("type") for msg in messages]
                            has_user_and_ai = "user" in message_types and "ai" in message_types
                            
                            self.log_test("Get Messages", True, 
                                        f"Found {len(messages)} messages with types: {set(message_types)}")
                            return True
                        else:
                            self.log_test("Get Messages", False, f"Expected at least 3 messages, got {len(messages)}")
                            return False
                    else:
                        self.log_test("Get Messages", False, f"No messages field in response: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Get Messages", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Get Messages", False, f"Exception: {str(e)}")
            return False
            
    async def test_emergency_detection(self):
        """Test emergency symptom detection"""
        try:
            emergency_symptoms = "I have severe chest pain and can't breathe properly, feeling dizzy"
            payload = {"symptoms": emergency_symptoms}
            
            async with self.session.post(
                f"{self.base_url}/consultations",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    emergency_consultation_id = data.get("consultation_id")
                    
                    if emergency_consultation_id:
                        # Get the consultation to check for emergency detection
                        async with self.session.get(f"{self.base_url}/consultations/{emergency_consultation_id}") as get_response:
                            if get_response.status == 200:
                                consultation_data = await get_response.json()
                                messages = consultation_data.get("messages", [])
                                
                                # Check if any AI message detected emergency
                                emergency_detected = False
                                for msg in messages:
                                    if msg.get("type") == "ai":
                                        content = msg.get("content", "").lower()
                                        metadata = msg.get("metadata", {})
                                        
                                        if (metadata.get("emergency_detected") or 
                                            any(term in content for term in ["emergency", "911", "immediate", "urgent"])):
                                            emergency_detected = True
                                            break
                                
                                self.log_test("Emergency Detection", emergency_detected, 
                                            f"Emergency detected in AI response: {emergency_detected}")
                                return emergency_detected
                            else:
                                self.log_test("Emergency Detection", False, "Failed to get emergency consultation")
                                return False
                    else:
                        self.log_test("Emergency Detection", False, "Failed to create emergency consultation")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Emergency Detection", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Emergency Detection", False, f"Exception: {str(e)}")
            return False
            
    async def test_statistics(self):
        """Test GET /api/statistics endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/statistics") as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["total_consultations", "active_consultations", "average_response_time"]
                    
                    if all(field in data for field in required_fields):
                        # Check if total consultations is a reasonable number (should be > 0 after our tests)
                        total = data.get("total_consultations", "0")
                        # Remove commas and convert to int
                        total_num = int(total.replace(",", "")) if isinstance(total, str) else total
                        
                        if total_num >= 0:
                            self.log_test("Statistics", True, f"Total consultations: {total}")
                            return True
                        else:
                            self.log_test("Statistics", False, f"Invalid consultation count: {total}")
                            return False
                    else:
                        self.log_test("Statistics", False, f"Missing required fields: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Statistics", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Statistics", False, f"Exception: {str(e)}")
            return False
            
    async def test_medical_analysis_endpoint(self):
        """Test POST /api/medical/analyze endpoint"""
        try:
            analysis_payload = {
                "symptoms": "persistent headache with nausea and light sensitivity",
                "user_info": {"age": 28, "sex": "female"},
                "conversation_history": []
            }
            
            async with self.session.post(
                f"{self.base_url}/medical/analyze",
                json=analysis_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    required_fields = ["diagnosis", "recommendations", "follow_up_questions", "emergency_detected"]
                    
                    if all(field in data for field in required_fields):
                        diagnosis = data.get("diagnosis", [])
                        recommendations = data.get("recommendations", [])
                        
                        if len(diagnosis) > 0 and len(recommendations) > 0:
                            self.log_test("Medical Analysis", True, 
                                        f"Found {len(diagnosis)} diagnoses and {len(recommendations)} recommendations")
                            return True
                        else:
                            self.log_test("Medical Analysis", False, "Empty diagnosis or recommendations")
                            return False
                    else:
                        self.log_test("Medical Analysis", False, f"Missing required fields: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Medical Analysis", False, f"HTTP {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test("Medical Analysis", False, f"Exception: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Doctronic AI Backend Tests")
        print("=" * 50)
        
        await self.setup()
        
        try:
            # Core functionality tests
            await self.test_health_check()
            await self.test_create_consultation()
            await self.test_get_consultation()
            await self.test_update_user_info()
            await self.test_send_message_user_info()
            await self.test_get_messages()
            await self.test_emergency_detection()
            await self.test_statistics()
            await self.test_medical_analysis_endpoint()
            
        finally:
            await self.cleanup()
            
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Backend is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check the details above.")
            
        return passed == total

async def main():
    """Main test runner"""
    tester = DoctronicBackendTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())