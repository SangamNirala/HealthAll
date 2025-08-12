#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class ChatAPITester:
    def __init__(self, base_url="https://chat-test-complete.preview.emergentagent.com/api"):
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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
                except:
                    print(f"   Response: {response.text[:300]}...")
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

    def test_chat_api_endpoints(self):
        """Test Chat API endpoints for detailed response analysis"""
        print("\n💬 Testing Chat API Endpoints for Response Quality...")
        
        # Test 1: Start a new chat session
        success1, session_response = self.run_test(
            "Start Chat Session",
            "POST",
            "chat/start-session",
            200
        )
        
        if not success1 or not session_response:
            print("❌ Failed to start chat session - cannot continue chat tests")
            return False
            
        session_id = session_response.get('session_id')
        if not session_id:
            print("❌ No session_id returned from start-session")
            return False
            
        print(f"   ✅ Chat session started: {session_id}")
        
        # Test messages with detailed response analysis
        test_messages = [
            "What should I eat for breakfast?",
            "How can I lose weight healthily?", 
            "What are good protein sources?"
        ]
        
        all_tests_passed = True
        response_analysis = []
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n   Testing Message {i}: '{message}'")
            
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
                # Analyze response quality
                analysis = self.analyze_chat_response(response, message, i)
                response_analysis.append(analysis)
                
                # Print detailed analysis
                print(f"   📊 Response Analysis for Message {i}:")
                print(f"      Word Count: {analysis['word_count']}")
                print(f"      Has Title: {analysis['has_title']}")
                print(f"      Has Summary: {analysis['has_summary']}")
                print(f"      Key Points Count: {analysis['key_points_count']}")
                print(f"      Action Steps Count: {analysis['action_steps_count']}")
                print(f"      Tips Count: {analysis['tips_count']}")
                print(f"      Response Quality: {analysis['quality_assessment']}")
                print(f"      AI Provider: {analysis.get('provider', 'Unknown')}")
                print(f"      Confidence: {analysis.get('confidence', 'N/A')}")
                
                # Check if response meets quality criteria
                if analysis['word_count'] < 100:
                    print(f"      ⚠️  WARNING: Response too short ({analysis['word_count']} words)")
                    all_tests_passed = False
                    
                if not analysis['has_structured_data']:
                    print(f"      ⚠️  WARNING: Missing structured response fields")
                    all_tests_passed = False
                    
            else:
                print(f"   ❌ Failed to get response for message {i}")
                all_tests_passed = False
        
        # Test 4: Get chat history
        success4, history_response = self.run_test(
            "Get Chat History",
            "GET",
            f"chat/history/{session_id}",
            200
        )
        
        if success4 and history_response:
            messages = history_response.get('messages', [])
            print(f"   ✅ Chat history retrieved: {len(messages)} messages")
            
            # Analyze conversation flow
            user_messages = [msg for msg in messages if msg.get('type') == 'user']
            ai_messages = [msg for msg in messages if msg.get('type') == 'assistant']
            
            print(f"   📈 Conversation Analysis:")
            print(f"      User Messages: {len(user_messages)}")
            print(f"      AI Messages: {len(ai_messages)}")
            
            # Check if AI responses have structured data
            structured_responses = 0
            for msg in ai_messages:
                if msg.get('structured'):
                    structured_responses += 1
                    
            print(f"      Structured AI Responses: {structured_responses}/{len(ai_messages)}")
        
        # Generate comprehensive analysis report
        self.generate_chat_analysis_report(response_analysis)
        
        return all_tests_passed and success1 and success4

    def analyze_chat_response(self, response, original_message, message_num):
        """Analyze chat response quality and structure"""
        analysis = {
            'message_number': message_num,
            'original_message': original_message,
            'word_count': 0,
            'has_title': False,
            'has_summary': False,
            'has_structured_data': False,
            'key_points_count': 0,
            'action_steps_count': 0,
            'tips_count': 0,
            'suggestions_count': 0,
            'quality_assessment': 'poor',
            'provider': response.get('provider', 'unknown'),
            'confidence': response.get('confidence', 0)
        }
        
        # Analyze main response text
        main_response = response.get('response', '')
        if main_response:
            analysis['word_count'] = len(main_response.split())
            
        # Check for structured fields
        analysis['has_title'] = bool(response.get('title'))
        analysis['has_summary'] = bool(response.get('summary'))
        
        # Count structured elements
        analysis['key_points_count'] = len(response.get('key_points', []))
        analysis['action_steps_count'] = len(response.get('action_steps', []))
        analysis['tips_count'] = len(response.get('tips', []))
        analysis['suggestions_count'] = len(response.get('suggestions', []))
        
        # Check if response has structured data
        analysis['has_structured_data'] = (
            analysis['has_title'] or 
            analysis['has_summary'] or
            analysis['key_points_count'] > 0 or
            analysis['action_steps_count'] > 0 or
            analysis['tips_count'] > 0
        )
        
        # Assess overall quality
        if analysis['word_count'] >= 400 and analysis['has_structured_data']:
            analysis['quality_assessment'] = 'excellent'
        elif analysis['word_count'] >= 200 and analysis['has_structured_data']:
            analysis['quality_assessment'] = 'good'
        elif analysis['word_count'] >= 100:
            analysis['quality_assessment'] = 'fair'
        else:
            analysis['quality_assessment'] = 'poor'
            
        return analysis

    def generate_chat_analysis_report(self, response_analysis):
        """Generate comprehensive analysis report for chat responses"""
        print(f"\n📋 COMPREHENSIVE CHAT API ANALYSIS REPORT")
        print("=" * 60)
        
        if not response_analysis:
            print("❌ No response data to analyze")
            return
            
        # Calculate averages
        total_responses = len(response_analysis)
        avg_word_count = sum(r['word_count'] for r in response_analysis) / total_responses
        structured_responses = sum(1 for r in response_analysis if r['has_structured_data'])
        
        print(f"Total Responses Analyzed: {total_responses}")
        print(f"Average Word Count: {avg_word_count:.1f} words")
        print(f"Structured Responses: {structured_responses}/{total_responses} ({(structured_responses/total_responses)*100:.1f}%)")
        
        # Quality distribution
        quality_counts = {}
        for r in response_analysis:
            quality = r['quality_assessment']
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            
        print(f"\nQuality Distribution:")
        for quality, count in quality_counts.items():
            print(f"  {quality.capitalize()}: {count} ({(count/total_responses)*100:.1f}%)")
        
        # Detailed analysis per message
        print(f"\nDetailed Response Analysis:")
        for r in response_analysis:
            print(f"  Message {r['message_number']}: '{r['original_message'][:50]}...'")
            print(f"    Word Count: {r['word_count']} | Quality: {r['quality_assessment']}")
            print(f"    Structured Elements: Title={r['has_title']}, Summary={r['has_summary']}")
            print(f"    Content Counts: Points={r['key_points_count']}, Steps={r['action_steps_count']}, Tips={r['tips_count']}")
            print(f"    Provider: {r['provider']} | Confidence: {r['confidence']}")
        
        # Identify issues
        print(f"\n🔍 ISSUE IDENTIFICATION:")
        issues_found = []
        
        short_responses = [r for r in response_analysis if r['word_count'] < 100]
        if short_responses:
            issues_found.append(f"SHORT RESPONSES: {len(short_responses)} responses under 100 words")
            
        unstructured_responses = [r for r in response_analysis if not r['has_structured_data']]
        if unstructured_responses:
            issues_found.append(f"UNSTRUCTURED RESPONSES: {len(unstructured_responses)} responses missing structured fields")
            
        poor_quality = [r for r in response_analysis if r['quality_assessment'] == 'poor']
        if poor_quality:
            issues_found.append(f"POOR QUALITY: {len(poor_quality)} responses rated as poor quality")
            
        if issues_found:
            for issue in issues_found:
                print(f"  ❌ {issue}")
        else:
            print(f"  ✅ No major issues identified")
            
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if avg_word_count < 200:
            print(f"  • Increase response length - current average ({avg_word_count:.1f}) is below target (400-800 words)")
        if structured_responses < total_responses:
            print(f"  • Ensure all responses include structured fields (title, summary, key_points, action_steps, tips)")
        if any(r['quality_assessment'] == 'poor' for r in response_analysis):
            print(f"  • Review AI prompt engineering to improve response quality")
        if any(r['provider'] == 'unknown' for r in response_analysis):
            print(f"  • Investigate AI provider selection and fallback mechanisms")

    def run_all_tests(self):
        """Run all chat API tests"""
        print("🚀 Starting Chat API Quality Tests...")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)

        # Test Chat API Endpoints
        chat_success = self.test_chat_api_endpoints()

        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Chat API Quality: {'PASS' if chat_success else 'FAIL'}")
        print("=" * 60)
        print(f"📈 Overall Success Rate: {self.tests_passed}/{self.tests_run} ({(self.tests_passed/self.tests_run)*100:.1f}%)")

        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = ChatAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All chat tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ Some chat tests failed. Check the results above.")
        sys.exit(1)