#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class DetailedChatAPITester:
    def __init__(self, base_url="https://quickchat-boost.preview.emergentagent.com/api"):
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
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
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

    def test_chat_long_response_validation(self):
        """Test Chat API for long response composition as per review request"""
        print("\n💬 DETAILED CHAT API LONG-RESPONSE VALIDATION")
        print("=" * 70)
        
        # Test 1: Start a new chat session
        print("\n1️⃣ TESTING: POST /api/chat/start-session returns a session_id")
        success1, session_response = self.run_test(
            "Start Chat Session",
            "POST",
            "chat/start-session",
            200
        )
        
        if not success1 or not session_response:
            print("❌ CRITICAL FAILURE: Cannot start chat session - aborting tests")
            return False
            
        session_id = session_response.get('session_id')
        if not session_id:
            print("❌ CRITICAL FAILURE: No session_id returned from start-session")
            return False
            
        print(f"   ✅ SUCCESS: Chat session started with ID: {session_id}")
        
        # Test 2: Send specific messages and validate responses
        print("\n2️⃣ TESTING: POST /api/chat/send-message for specific prompts")
        test_messages = [
            "What should I eat for breakfast?",
            "How can I lose weight healthily?", 
            "What are good protein sources?"
        ]
        
        all_responses_valid = True
        word_counts = []
        response_details = []
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n   📝 Testing Message {i}: '{message}'")
            
            # Send message to chat API
            message_data = {
                "session_id": session_id,
                "message": message,
                "context_type": "health_and_nutrition",
                "user_context": {
                    "profile_type": "patient",
                    "health_goals": ["weight_management", "healthy_eating"],
                    "interaction_count": i
                }
            }
            
            success, response = self.run_test(
                f"Send Chat Message {i}",
                "POST", 
                "chat/send-message",
                200,
                data=message_data
            )
            
            if success and response:
                # Detailed response analysis
                analysis = self.analyze_detailed_response(response, message, i)
                response_details.append(analysis)
                word_counts.append(analysis['word_count'])
                
                # Print detailed validation results
                print(f"   📊 DETAILED VALIDATION RESULTS:")
                print(f"      ✅ Response received: {analysis['word_count']} words")
                print(f"      ✅ Word count >= 350: {'YES' if analysis['word_count'] >= 350 else 'NO'}")
                print(f"      ✅ Word count 400-800 range: {'YES' if 400 <= analysis['word_count'] <= 800 else 'NO'}")
                print(f"      ✅ Has title: {'YES' if analysis['has_title'] else 'NO'}")
                print(f"      ✅ Has summary: {'YES' if analysis['has_summary'] else 'NO'}")
                print(f"      ✅ Has key_points: {'YES' if analysis['key_points_count'] > 0 else 'NO'} ({analysis['key_points_count']} items)")
                print(f"      ✅ Has action_steps: {'YES' if analysis['action_steps_count'] > 0 else 'NO'} ({analysis['action_steps_count']} items)")
                print(f"      ✅ Has tips: {'YES' if analysis['tips_count'] > 0 else 'NO'} ({analysis['tips_count']} items)")
                print(f"      ✅ Confidence score: {analysis['confidence']}")
                
                # Validate minimum requirements
                if analysis['word_count'] < 350:
                    print(f"      ❌ FAILURE: Response too short ({analysis['word_count']} < 350 words)")
                    all_responses_valid = False
                    
                if not analysis['has_structured_fields']:
                    print(f"      ❌ FAILURE: Missing required structured fields")
                    all_responses_valid = False
                    
            else:
                print(f"   ❌ FAILURE: Could not get response for message {i}")
                all_responses_valid = False
        
        # Test 3: Validate chat history
        print(f"\n3️⃣ TESTING: GET /api/chat/history/{session_id} validation")
        success3, history_response = self.run_test(
            "Get Chat History",
            "GET",
            f"chat/history/{session_id}",
            200
        )
        
        history_valid = True
        if success3 and history_response:
            messages = history_response.get('messages', [])
            print(f"   ✅ Chat history retrieved: {len(messages)} messages")
            
            # Validate assistant messages in history
            ai_messages = [msg for msg in messages if msg.get('type') == 'assistant']
            print(f"   📈 Assistant messages in history: {len(ai_messages)}")
            
            for i, ai_msg in enumerate(ai_messages, 1):
                content = ai_msg.get('content', '')
                content_word_count = len(content.split()) if content else 0
                structured_data = ai_msg.get('structured', {})
                
                print(f"   📝 Assistant Message {i}:")
                print(f"      Content length: {content_word_count} words")
                print(f"      Content >= 350 words: {'YES' if content_word_count >= 350 else 'NO'}")
                print(f"      Has structured metadata: {'YES' if structured_data else 'NO'}")
                
                if structured_data:
                    provider = structured_data.get('provider', 'unknown')
                    model = structured_data.get('model', 'unknown')
                    confidence = structured_data.get('confidence', 'unknown')
                    
                    print(f"      Provider: {provider}")
                    print(f"      Model: {model}")
                    print(f"      Confidence: {confidence}")
                
                if content_word_count < 350:
                    print(f"      ❌ FAILURE: Assistant message content too short")
                    history_valid = False
        else:
            print(f"   ❌ FAILURE: Could not retrieve chat history")
            history_valid = False
        
        # Generate comprehensive report
        print(f"\n📋 COMPREHENSIVE VALIDATION REPORT")
        print("=" * 70)
        
        if word_counts:
            avg_word_count = sum(word_counts) / len(word_counts)
            min_word_count = min(word_counts)
            max_word_count = max(word_counts)
            
            print(f"📊 WORD COUNT ANALYSIS:")
            print(f"   Average word count: {avg_word_count:.1f} words")
            print(f"   Minimum word count: {min_word_count} words")
            print(f"   Maximum word count: {max_word_count} words")
            print(f"   All responses >= 350 words: {'YES' if min_word_count >= 350 else 'NO'}")
            print(f"   All responses in 400-800 range: {'YES' if all(400 <= wc <= 800 for wc in word_counts) else 'NO'}")
        
        print(f"\n🔍 STRUCTURED FIELDS VALIDATION:")
        if response_details:
            all_have_title = all(r['has_title'] for r in response_details)
            all_have_summary = all(r['has_summary'] for r in response_details)
            all_have_key_points = all(r['key_points_count'] > 0 for r in response_details)
            all_have_action_steps = all(r['action_steps_count'] > 0 for r in response_details)
            all_have_tips = all(r['tips_count'] > 0 for r in response_details)
            
            print(f"   All responses have title: {'YES' if all_have_title else 'NO'}")
            print(f"   All responses have summary: {'YES' if all_have_summary else 'NO'}")
            print(f"   All responses have key_points: {'YES' if all_have_key_points else 'NO'}")
            print(f"   All responses have action_steps: {'YES' if all_have_action_steps else 'NO'}")
            print(f"   All responses have tips: {'YES' if all_have_tips else 'NO'}")
        
        print(f"\n🎯 FINAL VALIDATION RESULTS:")
        session_test_passed = success1 and session_id is not None
        message_tests_passed = all_responses_valid and len(word_counts) == 3
        history_test_passed = success3 and history_valid
        
        print(f"   ✅ Session creation test: {'PASS' if session_test_passed else 'FAIL'}")
        print(f"   ✅ Message response tests: {'PASS' if message_tests_passed else 'FAIL'}")
        print(f"   ✅ Chat history test: {'PASS' if history_test_passed else 'FAIL'}")
        
        overall_success = session_test_passed and message_tests_passed and history_test_passed
        print(f"   🏆 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        return overall_success

    def analyze_detailed_response(self, response, original_message, message_num):
        """Analyze chat response with detailed validation"""
        analysis = {
            'message_number': message_num,
            'original_message': original_message,
            'word_count': 0,
            'has_title': False,
            'has_summary': False,
            'has_structured_fields': False,
            'key_points_count': 0,
            'action_steps_count': 0,
            'tips_count': 0,
            'suggestions_count': 0,
            'confidence': response.get('confidence', 0),
            'provider': 'unknown',
            'model': 'unknown'
        }
        
        # Analyze main response text
        main_response = response.get('response', '')
        if main_response:
            analysis['word_count'] = len(main_response.split())
            
        # Check for structured fields in top-level response
        analysis['has_title'] = bool(response.get('title'))
        analysis['has_summary'] = bool(response.get('summary'))
        
        # Count structured elements
        analysis['key_points_count'] = len(response.get('key_points', []))
        analysis['action_steps_count'] = len(response.get('action_steps', []))
        analysis['tips_count'] = len(response.get('tips', []))
        analysis['suggestions_count'] = len(response.get('suggestions', []))
        
        # Check if response has required structured fields
        analysis['has_structured_fields'] = (
            analysis['has_title'] and 
            analysis['has_summary'] and
            analysis['key_points_count'] > 0 and
            analysis['action_steps_count'] > 0 and
            analysis['tips_count'] > 0
        )
        
        return analysis

    def run_detailed_validation(self):
        """Run detailed Chat API validation"""
        print("🚀 Starting Detailed Chat API Long-Response Validation...")
        print(f"   Base URL: {self.base_url}")
        print("=" * 70)

        # Test Chat API Long-Response Validation
        validation_success = self.test_chat_long_response_validation()

        print("\n" + "=" * 70)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 70)
        print(f"🎯 Chat API Long-Response Validation: {'✅ PASS' if validation_success else '❌ FAIL'}")
        print("=" * 70)
        print(f"📈 Overall Success Rate: {self.tests_passed}/{self.tests_run} ({(self.tests_passed/self.tests_run)*100:.1f}%)")

        return validation_success

if __name__ == "__main__":
    tester = DetailedChatAPITester()
    success = tester.run_detailed_validation()
    
    if success:
        print("\n🎉 All detailed chat validation tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ Some detailed chat validation tests failed. Check the results above.")
        sys.exit(1)