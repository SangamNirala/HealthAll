#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class ChatAPITester:
    def __init__(self, base_url="https://e6566380-c89f-4302-8241-fb107351c821.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:500]}...")

            self.test_results.append({
                'name': name,
                'success': success,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'response': response.text[:500] if not success else "OK"
            })

            return success, response.json() if success and response.text else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                'name': name,
                'success': False,
                'error': str(e)
            })
            return False, {}

    def test_chat_start_session(self):
        """Test POST /api/chat/start-session returns session_id and welcome_message"""
        print("\n📋 Testing Chat Start Session...")
        
        success, response = self.run_test(
            "Start Chat Session",
            "POST",
            "chat/start-session",
            200
        )
        
        if success and response:
            # Validate required fields
            required_fields = ['session_id', 'welcome_message']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✅ Response contains required fields: {required_fields}")
                session_id = response.get('session_id')
                welcome_message = response.get('welcome_message')
                print(f"   Session ID: {session_id}")
                print(f"   Welcome message length: {len(welcome_message)} chars")
                return True, session_id
            else:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False, None
        
        return False, None

    def test_chat_send_message(self, session_id):
        """Test POST /api/chat/send-message with structured response formatting"""
        print("\n📋 Testing Chat Send Message...")
        
        # Test 1: Basic message with all required fields
        message_data = {
            "session_id": session_id,
            "message": "What's a healthy breakfast for weight loss?",
            "context_type": "health_and_nutrition"
        }
        
        success, response = self.run_test(
            "Send Message - Basic",
            "POST",
            "chat/send-message",
            200,
            data=message_data
        )
        
        if success and response:
            # Validate required response fields
            required_fields = ['response', 'suggestions', 'quick_actions', 'confidence']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✅ Response contains required fields: {required_fields}")
                
                # Validate optional structured fields
                optional_fields = ['title', 'summary', 'key_points', 'action_steps', 'tips']
                present_optional = [field for field in optional_fields if field in response]
                print(f"   ✅ Optional structured fields present: {present_optional}")
                
                # Validate field types and content
                suggestions = response.get('suggestions', [])
                quick_actions = response.get('quick_actions', [])
                confidence = response.get('confidence', 0)
                key_points = response.get('key_points', [])
                action_steps = response.get('action_steps', [])
                tips = response.get('tips', [])
                
                print(f"   Response: {response.get('response', '')[:100]}...")
                print(f"   Suggestions count: {len(suggestions)}")
                print(f"   Quick actions count: {len(quick_actions)}")
                print(f"   Confidence: {confidence}")
                print(f"   Key points count: {len(key_points)}")
                print(f"   Action steps count: {len(action_steps)}")
                print(f"   Tips count: {len(tips)}")
                
                # Validate data types
                if isinstance(suggestions, list) and isinstance(quick_actions, list) and isinstance(confidence, (int, float)):
                    print(f"   ✅ Field types are correct")
                    return True
                else:
                    print(f"   ❌ Field types are incorrect")
                    return False
            else:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False
        
        return False

    def test_chat_edge_cases(self):
        """Test edge cases: missing/invalid session_id, empty responses, fallbacks"""
        print("\n📋 Testing Chat Edge Cases...")
        
        # Test 1: Missing session_id (should return validation error - this is correct behavior)
        message_without_session = {
            "message": "Hello, I need nutrition advice",
            "context_type": "health_and_nutrition"
        }
        
        success1, response1 = self.run_test(
            "Send Message - Missing Session ID (Should Fail)",
            "POST",
            "chat/send-message",
            422,  # Expecting validation error - this is correct
            data=message_without_session
        )
        
        if success1:
            print(f"   ✅ Missing session_id properly rejected with validation error")
        else:
            print(f"   ❌ Missing session_id not handled as expected")
            success1 = False
        
        # Test 2: Invalid session_id (should handle gracefully)
        message_invalid_session = {
            "session_id": "invalid_session_12345",
            "message": "Test message with invalid session",
            "context_type": "health_and_nutrition"
        }
        
        success2, response2 = self.run_test(
            "Send Message - Invalid Session ID",
            "POST",
            "chat/send-message",
            200,
            data=message_invalid_session
        )
        
        if success2 and response2:
            # Should still return valid response structure
            required_fields = ['response', 'suggestions', 'quick_actions', 'confidence']
            missing_fields = [field for field in required_fields if field not in response2]
            if not missing_fields:
                print(f"   ✅ Invalid session handled gracefully")
            else:
                print(f"   ❌ Invalid session not handled properly")
                success2 = False
        
        # Test 3: Empty suggestions/quick_actions should still be handled
        # This is tested implicitly in the above tests
        
        return success1 and success2

    def test_provider_fallback(self):
        """Test provider fallback system (Groq -> Gemini -> OpenRouter -> HF -> fallback)"""
        print("\n📋 Testing Provider Fallback System...")
        
        # Send multiple requests to test different providers
        test_messages = [
            "What are the benefits of Mediterranean diet?",
            "How much water should I drink daily?",
            "What are good protein sources for vegetarians?",
            "Tell me about intermittent fasting",
            "What vitamins are important for immune system?"
        ]
        
        all_success = True
        provider_info = []
        
        for i, message in enumerate(test_messages, 1):
            message_data = {
                "session_id": f"fallback_test_{i}_{int(datetime.now().timestamp())}",
                "message": message,
                "context_type": "health_and_nutrition"
            }
            
            success, response = self.run_test(
                f"Provider Fallback Test {i}",
                "POST",
                "chat/send-message",
                200,
                data=message_data
            )
            
            if success and response:
                # Check if response is valid even if upstream fails
                confidence = response.get('confidence', 0)
                response_text = response.get('response', '')
                
                if len(response_text) > 0 and confidence > 0:
                    print(f"   ✅ Valid response received (confidence: {confidence})")
                    provider_info.append(f"Test {i}: Success")
                else:
                    print(f"   ❌ Invalid response or zero confidence")
                    all_success = False
                    provider_info.append(f"Test {i}: Failed")
            else:
                all_success = False
                provider_info.append(f"Test {i}: Failed")
        
        print(f"   Provider fallback results: {provider_info}")
        return all_success

    def test_json_fields_persistence(self):
        """Test that JSON fields are present even when structured model parsing fails"""
        print("\n📋 Testing JSON Fields Persistence...")
        
        # Test with various message types that might challenge the AI
        challenging_messages = [
            "xyz123 random text that makes no sense",
            "!@#$%^&*()",
            "",  # Empty message
            "a" * 1000,  # Very long message
        ]
        
        all_success = True
        
        for i, message in enumerate(challenging_messages, 1):
            if message == "":
                continue  # Skip empty message as it might be rejected
                
            message_data = {
                "session_id": f"persistence_test_{i}_{int(datetime.now().timestamp())}",
                "message": message,
                "context_type": "health_and_nutrition"
            }
            
            success, response = self.run_test(
                f"JSON Fields Persistence Test {i}",
                "POST",
                "chat/send-message",
                200,
                data=message_data
            )
            
            if success and response:
                # Ensure all required fields are present
                required_fields = ['response', 'suggestions', 'quick_actions', 'confidence']
                missing_fields = [field for field in required_fields if field not in response]
                
                if not missing_fields:
                    # Check that arrays are actually arrays (not null)
                    suggestions = response.get('suggestions', [])
                    quick_actions = response.get('quick_actions', [])
                    key_points = response.get('key_points', [])
                    action_steps = response.get('action_steps', [])
                    tips = response.get('tips', [])
                    
                    if (isinstance(suggestions, list) and isinstance(quick_actions, list) and 
                        isinstance(key_points, list) and isinstance(action_steps, list) and 
                        isinstance(tips, list)):
                        print(f"   ✅ All JSON fields present and correct type")
                    else:
                        print(f"   ❌ JSON fields not proper arrays")
                        all_success = False
                else:
                    print(f"   ❌ Missing required fields: {missing_fields}")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def run_comprehensive_chat_tests(self):
        """Run all Chat API tests as specified in the review request"""
        print("🚀 Starting Comprehensive Chat API Tests")
        print("=" * 80)
        print("Testing updated Chat API flow and structured response formatting")
        print("=" * 80)
        
        # Test 1: Start Session
        print("\n1️⃣ Testing POST /api/chat/start-session")
        session_success, session_id = self.test_chat_start_session()
        
        if not session_id:
            session_id = f"fallback_session_{int(datetime.now().timestamp())}"
            print(f"   Using fallback session ID: {session_id}")
        
        # Test 2: Send Message with structured response
        print("\n2️⃣ Testing POST /api/chat/send-message")
        message_success = self.test_chat_send_message(session_id)
        
        # Test 3: Edge cases
        print("\n3️⃣ Testing Edge Cases")
        edge_cases_success = self.test_chat_edge_cases()
        
        # Test 4: Provider fallback system
        print("\n4️⃣ Testing Provider Fallback System")
        fallback_success = self.test_provider_fallback()
        
        # Test 5: JSON fields persistence
        print("\n5️⃣ Testing JSON Fields Persistence")
        persistence_success = self.test_json_fields_persistence()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE CHAT API TEST RESULTS")
        print("=" * 80)
        print(f"✅ Start Session: {'PASS' if session_success else 'FAIL'}")
        print(f"✅ Send Message Structure: {'PASS' if message_success else 'FAIL'}")
        print(f"✅ Edge Cases: {'PASS' if edge_cases_success else 'FAIL'}")
        print(f"✅ Provider Fallback: {'PASS' if fallback_success else 'FAIL'}")
        print(f"✅ JSON Fields Persistence: {'PASS' if persistence_success else 'FAIL'}")
        print(f"\n📈 Overall Success Rate: {self.tests_passed}/{self.tests_run} ({(self.tests_passed/self.tests_run*100):.1f}%)")
        
        overall_success = (session_success and message_success and edge_cases_success and 
                          fallback_success and persistence_success)
        
        if overall_success:
            print("🎉 ALL CHAT API TESTS PASSED!")
            return True
        else:
            print("❌ SOME CHAT API TESTS FAILED!")
            return False

if __name__ == "__main__":
    tester = ChatAPITester()
    success = tester.run_comprehensive_chat_tests()
    sys.exit(0 if success else 1)