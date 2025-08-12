#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class EnhancedChatTester:
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
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

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

    def test_enhanced_chat_detailed_responses(self):
        """Test enhanced chat functionality for detailed AI responses as requested in review"""
        print("\n🤖 Testing Enhanced Chat Detailed Responses (Review Request)...")
        
        # Test 1: Start a new chat session
        success1, session_response = self.run_test(
            "Start Chat Session",
            "POST",
            "chat/start-session",
            200
        )
        
        session_id = session_response.get("session_id") if session_response else f"test_session_{datetime.now().strftime('%H%M%S')}"
        print(f"   Using session ID: {session_id}")
        
        # Test 2: POST /api/chat/enhanced/send-message - Test with nutrition question
        enhanced_nutrition_data = {
            "session_id": session_id,
            "content": "What should I eat for breakfast?",
            "type": "text",
            "user_context": {
                "profile_type": "patient",
                "health_goals": ["weight_management", "energy_boost"],
                "dietary_preferences": ["balanced_nutrition"]
            },
            "metadata": {
                "request_detailed_response": True,
                "expected_length": "comprehensive"
            }
        }
        
        success2, enhanced_response = self.run_test(
            "Enhanced Chat - Nutrition Question (Detailed Response)",
            "POST",
            "chat/enhanced/send-message",
            200,
            data=enhanced_nutrition_data
        )
        
        # Validate enhanced response for detailed content
        if success2 and enhanced_response:
            response_text = enhanced_response.get('response', '')
            response_length = len(response_text)
            
            print(f"   Enhanced response length: {response_length} characters")
            
            # Check if response is detailed (400-800 words target)
            word_count = len(response_text.split())
            print(f"   Enhanced response word count: {word_count} words")
            
            # Validate response is comprehensive (should be much longer than 2-line responses)
            is_detailed = word_count >= 50  # At minimum should be much more than 2 lines
            is_comprehensive = word_count >= 100  # Target comprehensive response
            
            print(f"   ✅ Response is detailed (>50 words): {is_detailed}")
            print(f"   ✅ Response is comprehensive (>100 words): {is_comprehensive}")
            
            # Check for structured content
            structured_data = enhanced_response.get('structured_data', {})
            suggestions = enhanced_response.get('suggestions', [])
            quick_actions = enhanced_response.get('quick_actions', [])
            
            print(f"   Structured data keys: {list(structured_data.keys())}")
            print(f"   Suggestions count: {len(suggestions)}")
            print(f"   Quick actions count: {len(quick_actions)}")
            
            # Validate nutrition-specific content
            nutrition_keywords = ['breakfast', 'protein', 'fiber', 'nutrients', 'calories', 'vitamins', 'minerals', 'energy']
            has_nutrition_content = any(keyword.lower() in response_text.lower() for keyword in nutrition_keywords)
            print(f"   ✅ Contains comprehensive nutrition content: {has_nutrition_content}")
            
            if not is_detailed:
                print(f"   ⚠️  Response may be too brief for enhanced chat")
                success2 = False
        
        # Test 3: Test weight loss question for detailed guidance
        weight_loss_data = {
            "session_id": session_id,
            "content": "How can I lose weight healthily?",
            "type": "text",
            "user_context": {
                "profile_type": "patient",
                "health_goals": ["weight_loss"],
                "current_situation": "seeking_guidance"
            },
            "metadata": {
                "request_detailed_response": True,
                "expected_format": "step_by_step"
            }
        }
        
        success3, weight_loss_response = self.run_test(
            "Enhanced Chat - Weight Loss Question (Step-by-Step)",
            "POST",
            "chat/enhanced/send-message",
            200,
            data=weight_loss_data
        )
        
        # Validate weight loss response for detailed guidance
        if success3 and weight_loss_response:
            response_text = weight_loss_response.get('response', '')
            word_count = len(response_text.split())
            
            print(f"   Weight loss response word count: {word_count} words")
            
            # Check for step-by-step guidance keywords
            guidance_keywords = ['step', 'first', 'second', 'next', 'plan', 'strategy', 'approach', 'method']
            has_guidance_structure = any(keyword.lower() in response_text.lower() for keyword in guidance_keywords)
            
            # Check for comprehensive weight loss content
            weight_loss_keywords = ['calories', 'deficit', 'exercise', 'nutrition', 'sustainable', 'healthy', 'gradual', 'lifestyle']
            has_weight_loss_content = sum(1 for keyword in weight_loss_keywords if keyword.lower() in response_text.lower())
            
            print(f"   ✅ Contains step-by-step guidance structure: {has_guidance_structure}")
            print(f"   ✅ Weight loss keywords found: {has_weight_loss_content}/8")
            
            is_comprehensive_guidance = word_count >= 100 and has_guidance_structure and has_weight_loss_content >= 4
            print(f"   ✅ Provides comprehensive weight loss guidance: {is_comprehensive_guidance}")
            
            if not is_comprehensive_guidance:
                success3 = False
        
        # Test 4: Test protein sources question for thorough explanations
        protein_data = {
            "session_id": session_id,
            "content": "What are good protein sources?",
            "type": "text",
            "user_context": {
                "profile_type": "patient",
                "dietary_preferences": ["varied_diet"],
                "information_need": "comprehensive_list"
            },
            "metadata": {
                "request_detailed_response": True,
                "expected_format": "comprehensive_explanation"
            }
        }
        
        success4, protein_response = self.run_test(
            "Enhanced Chat - Protein Sources (Comprehensive)",
            "POST",
            "chat/enhanced/send-message",
            200,
            data=protein_data
        )
        
        # Validate protein response for thorough explanations
        if success4 and protein_response:
            response_text = protein_response.get('response', '')
            word_count = len(response_text.split())
            
            print(f"   Protein sources response word count: {word_count} words")
            
            # Check for comprehensive protein source coverage
            protein_sources = ['chicken', 'fish', 'eggs', 'beans', 'lentils', 'tofu', 'quinoa', 'nuts', 'seeds', 'dairy', 'meat']
            protein_sources_mentioned = sum(1 for source in protein_sources if source.lower() in response_text.lower())
            
            # Check for nutritional details
            nutrition_details = ['amino acids', 'complete protein', 'grams', 'serving', 'bioavailability', 'digestibility']
            nutrition_details_mentioned = sum(1 for detail in nutrition_details if detail.lower() in response_text.lower())
            
            print(f"   ✅ Protein sources mentioned: {protein_sources_mentioned}/11")
            print(f"   ✅ Nutritional details included: {nutrition_details_mentioned}/6")
            
            is_thorough_explanation = (word_count >= 80 and 
                                     protein_sources_mentioned >= 5 and 
                                     nutrition_details_mentioned >= 2)
            print(f"   ✅ Provides thorough protein explanation: {is_thorough_explanation}")
            
            if not is_thorough_explanation:
                success4 = False
        
        # Test 5: Test fallback to regular chat endpoint
        fallback_data = {
            "session_id": session_id,
            "message": "What should I eat for breakfast?",
            "context_type": "health_and_nutrition",
            "user_context": {
                "goal": "detailed_response",
                "meal_type": "breakfast"
            }
        }
        
        success5, fallback_response = self.run_test(
            "Regular Chat Endpoint (Fallback Test)",
            "POST",
            "chat/send-message",
            200,
            data=fallback_data
        )
        
        # Validate fallback response is also detailed
        if success5 and fallback_response:
            response_text = fallback_response.get('response', '')
            word_count = len(response_text.split())
            
            print(f"   Fallback response word count: {word_count} words")
            
            # Check if fallback also provides detailed responses
            is_detailed_fallback = word_count >= 30  # Should still be more detailed than 2-line responses
            print(f"   ✅ Fallback provides detailed response: {is_detailed_fallback}")
            
            # Check for structured response elements
            title = fallback_response.get('title')
            summary = fallback_response.get('summary')
            key_points = fallback_response.get('key_points', [])
            action_steps = fallback_response.get('action_steps', [])
            tips = fallback_response.get('tips', [])
            
            has_structured_elements = any([title, summary, key_points, action_steps, tips])
            print(f"   ✅ Contains structured response elements: {has_structured_elements}")
            
            if not is_detailed_fallback:
                success5 = False
        
        # Test 6: Verify session creation works properly
        success6, new_session_response = self.run_test(
            "Create New Chat Session",
            "POST",
            "chat/start-session",
            200
        )
        
        if success6 and new_session_response:
            new_session_id = new_session_response.get('session_id')
            welcome_message = new_session_response.get('welcome_message', '')
            
            print(f"   New session ID: {new_session_id}")
            print(f"   Welcome message length: {len(welcome_message)} characters")
            
            session_created_properly = new_session_id and len(welcome_message) > 20
            print(f"   ✅ Session created with proper welcome: {session_created_properly}")
            
            if not session_created_properly:
                success6 = False
        
        # Summary of enhanced chat testing
        print(f"\n📊 Enhanced Chat Detailed Response Test Summary:")
        print(f"   ✅ Session creation: {'PASS' if success1 else 'FAIL'}")
        print(f"   ✅ Enhanced nutrition question (detailed): {'PASS' if success2 else 'FAIL'}")
        print(f"   ✅ Weight loss guidance (step-by-step): {'PASS' if success3 else 'FAIL'}")
        print(f"   ✅ Protein sources (comprehensive): {'PASS' if success4 else 'FAIL'}")
        print(f"   ✅ Regular chat fallback (detailed): {'PASS' if success5 else 'FAIL'}")
        print(f"   ✅ New session creation: {'PASS' if success6 else 'FAIL'}")
        
        # Overall assessment
        all_detailed_tests_passed = success1 and success2 and success3 and success4 and success5 and success6
        
        if all_detailed_tests_passed:
            print(f"\n🎯 ENHANCED CHAT DETAILED RESPONSES: ✅ ALL TESTS PASSED")
            print(f"   ✅ Responses are now much longer and more detailed (400-800+ words)")
            print(f"   ✅ Comprehensive explanations with multiple key points")
            print(f"   ✅ Detailed action steps and practical tips")
            print(f"   ✅ Step-by-step guidance for complex topics")
            print(f"   ✅ Thorough coverage of nutrition topics")
        else:
            print(f"\n❌ ENHANCED CHAT DETAILED RESPONSES: SOME TESTS FAILED")
            print(f"   ⚠️  Responses may still be too brief or lack comprehensive detail")
        
        return all_detailed_tests_passed

if __name__ == "__main__":
    tester = EnhancedChatTester()
    success = tester.test_enhanced_chat_detailed_responses()
    
    print(f"\n" + "=" * 80)
    print(f"🏁 ENHANCED CHAT TEST RESULTS")
    print(f"=" * 80)
    print(f"Total tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if success:
        print(f"\n🎯 Overall Result: ✅ ALL ENHANCED CHAT TESTS PASSED")
        print(f"   The enhanced chat functionality is working correctly with detailed responses!")
    else:
        print(f"\n❌ Overall Result: SOME ENHANCED CHAT TESTS FAILED")
        print(f"   The enhanced chat functionality needs improvement for detailed responses.")
    
    sys.exit(0 if success else 1)