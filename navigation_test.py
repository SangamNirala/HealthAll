#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class NavigationAPITester:
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
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
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

    def test_patient_navigation_endpoints(self):
        """Test Patient role navigation endpoints"""
        print("\n🧭 Testing Patient Navigation Endpoints...")
        
        test_user_id = "demo-patient-123"
        
        # Test Patient Dashboard
        success1, _ = self.run_test(
            "Patient Dashboard",
            "GET",
            f"patient/dashboard/{test_user_id}",
            200
        )
        
        # Test Patient Food Log
        success2, _ = self.run_test(
            "Patient Food Log",
            "GET",
            f"patient/food-log/{test_user_id}",
            200
        )
        
        # Test Patient Health Metrics
        success3, _ = self.run_test(
            "Patient Health Metrics",
            "GET",
            f"patient/health-metrics/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3

    def test_phase3_patient_apis(self):
        """Test Phase 3 Patient APIs that were mentioned as working"""
        print("\n🚀 Testing Phase 3 Patient APIs...")
        
        test_user_id = "demo-patient-123"
        
        # Test Patient Analytics API
        success1, analytics_data = self.run_test(
            "Patient Analytics API",
            "GET",
            f"patient/analytics/{test_user_id}",
            200
        )
        
        # Validate analytics response structure
        if success1 and analytics_data:
            expected_keys = ['nutrition_trends', 'ai_powered_insights', 'weekly_summary']
            missing_keys = [key for key in expected_keys if key not in analytics_data]
            if not missing_keys:
                print(f"   ✅ Analytics response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Analytics response missing keys: {missing_keys}")
                success1 = False
        
        # Test Patient Medications API
        success2, medications_data = self.run_test(
            "Patient Medications API",
            "GET",
            f"patient/medications/{test_user_id}",
            200
        )
        
        # Validate medications response structure
        if success2 and medications_data:
            expected_keys = ['medications', 'reminders', 'adherence_stats', 'ai_insights']
            missing_keys = [key for key in expected_keys if key not in medications_data]
            if not missing_keys:
                print(f"   ✅ Medications response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Medications response missing keys: {missing_keys}")
                success2 = False
        
        # Test Patient Health Timeline API
        success3, timeline_data = self.run_test(
            "Patient Health Timeline API",
            "GET",
            f"patient/timeline/{test_user_id}",
            200
        )
        
        # Validate timeline response structure
        if success3 and timeline_data:
            expected_keys = ['timeline_events', 'patterns', 'milestones', 'ai_insights', 'categories_summary']
            missing_keys = [key for key in expected_keys if key not in timeline_data]
            if not missing_keys:
                print(f"   ✅ Timeline response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Timeline response missing keys: {missing_keys}")
                success3 = False
        
        # Test Patient Smart Suggestions API
        success4, suggestions_data = self.run_test(
            "Patient Smart Suggestions API",
            "GET",
            f"patient/smart-suggestions/{test_user_id}",
            200
        )
        
        # Validate smart suggestions response structure
        if success4 and suggestions_data:
            expected_keys = ['quick_add_suggestions', 'meal_pattern_insights']
            missing_keys = [key for key in expected_keys if key not in suggestions_data]
            if not missing_keys:
                print(f"   ✅ Smart suggestions response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Smart suggestions response missing keys: {missing_keys}")
                success4 = False
        
        # Test Patient Symptoms Correlation API
        success5, correlation_data = self.run_test(
            "Patient Symptoms Correlation API",
            "GET",
            f"patient/symptoms-correlation/{test_user_id}",
            200
        )
        
        # Validate symptoms correlation response structure
        if success5 and correlation_data:
            expected_keys = ['correlations', 'recommendations']
            missing_keys = [key for key in expected_keys if key not in correlation_data]
            if not missing_keys:
                print(f"   ✅ Symptoms correlation response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Symptoms correlation response missing keys: {missing_keys}")
                success5 = False
        
        return success1 and success2 and success3 and success4 and success5

    def test_enhanced_food_logging_api(self):
        """Test Enhanced Food Logging API with AI pattern recognition"""
        print("\n🍎 Testing Enhanced Food Logging API...")
        
        # Test food logging with a sample food item
        sample_food_data = {
            "food_name": "Grilled Chicken Breast",
            "meal_type": "lunch",
            "quantity": 150,
            "unit": "grams"
        }
        
        success, response = self.run_test(
            "Enhanced Food Logging - Grilled Chicken",
            "POST",
            "patient/food-log",
            200,
            data=sample_food_data
        )
        
        if success and response:
            # Validate enhanced food logging response structure
            expected_keys = ['success', 'food_entry', 'daily_totals', 'ai_insights', 'pattern_recognition', 'smart_suggestions']
            missing_keys = [key for key in expected_keys if key not in response]
            
            if not missing_keys:
                print(f"   ✅ Enhanced food logging response contains all required keys")
                
                # Validate food_entry structure
                food_entry = response.get('food_entry', {})
                entry_keys = ['id', 'food_name', 'calories', 'protein', 'carbs', 'fat', 'confidence', 'ai_enhanced']
                missing_entry_keys = [key for key in entry_keys if key not in food_entry]
                
                if not missing_entry_keys:
                    print(f"   ✅ Food entry structure valid with AI enhancement")
                    
                    # Check AI enhancement indicators
                    ai_enhanced = food_entry.get('ai_enhanced', False)
                    confidence = food_entry.get('confidence', 0)
                    print(f"   ✅ AI Enhanced: {ai_enhanced}, Confidence: {confidence}")
                else:
                    print(f"   ❌ Food entry missing keys: {missing_entry_keys}")
                    success = False
            else:
                print(f"   ❌ Enhanced food logging response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_medication_actions(self):
        """Test medication action endpoints"""
        print("\n💊 Testing Medication Action Endpoints...")
        
        test_user_id = "demo-patient-123"
        
        # Test marking medication as taken
        sample_medication_take_data = {
            "medication_id": "med_001",
            "taken_at": datetime.utcnow().isoformat(),
            "notes": "Taken with breakfast as prescribed"
        }
        
        success1, take_response = self.run_test(
            "Mark Medication as Taken",
            "POST",
            f"patient/medications/{test_user_id}/take",
            200,
            data=sample_medication_take_data
        )
        
        # Test adding new medication
        sample_new_medication = {
            "name": "Vitamin D3",
            "dosage": "2000 IU",
            "frequency": "daily",
            "times": ["09:00"],
            "with_food": False,
            "condition": "Vitamin D Deficiency",
            "prescriber": "Dr. Johnson",
            "start_date": "2024-01-16",
            "end_date": None
        }
        
        success2, add_response = self.run_test(
            "Add New Medication",
            "POST",
            f"patient/medications/{test_user_id}",
            200,
            data=sample_new_medication
        )
        
        return success1 and success2

    def test_timeline_actions(self):
        """Test timeline action endpoints"""
        print("\n📅 Testing Timeline Action Endpoints...")
        
        test_user_id = "demo-patient-123"
        
        # Test adding timeline event
        sample_timeline_event = {
            "type": "exercise",
            "title": "Morning Yoga Session",
            "value": "30 minutes",
            "category": "activity",
            "details": "Completed 30-minute yoga session focusing on flexibility and mindfulness",
            "impact": "positive",
            "date": datetime.utcnow().date().isoformat()
        }
        
        success, event_response = self.run_test(
            "Add Timeline Event",
            "POST",
            f"patient/timeline/{test_user_id}/event",
            200,
            data=sample_timeline_event
        )
        
        return success

    def run_navigation_tests(self):
        """Run all navigation-focused tests"""
        print("🚀 Starting Navigation & Phase 3 Patient API Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)
        print("Focus: Testing navigation issues fix and Phase 3 Patient APIs")

        # Test Patient Navigation Endpoints
        print("\n📋 Testing Patient Navigation Endpoints...")
        nav_success = self.test_patient_navigation_endpoints()

        # Test Phase 3 Patient APIs
        print("\n📋 Testing Phase 3 Patient APIs...")
        phase3_success = self.test_phase3_patient_apis()

        # Test Enhanced Food Logging
        print("\n📋 Testing Enhanced Food Logging...")
        food_success = self.test_enhanced_food_logging_api()

        # Test Medication Actions
        print("\n📋 Testing Medication Actions...")
        med_success = self.test_medication_actions()

        # Test Timeline Actions
        print("\n📋 Testing Timeline Actions...")
        timeline_success = self.test_timeline_actions()

        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 NAVIGATION & PHASE 3 API TEST RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Summary by category
        print(f"\n📋 Category Results:")
        print(f"Patient Navigation Endpoints: {'✅ PASSED' if nav_success else '❌ FAILED'}")
        print(f"Phase 3 Patient APIs: {'✅ PASSED' if phase3_success else '❌ FAILED'}")
        print(f"Enhanced Food Logging: {'✅ PASSED' if food_success else '❌ FAILED'}")
        print(f"Medication Actions: {'✅ PASSED' if med_success else '❌ FAILED'}")
        print(f"Timeline Actions: {'✅ PASSED' if timeline_success else '❌ FAILED'}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All navigation and Phase 3 API tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the details above.")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result.get('success', False):
                    print(f"  - {result['name']}: {result.get('error', 'Status code mismatch')}")
            return 1

if __name__ == "__main__":
    tester = NavigationAPITester()
    exit_code = tester.run_navigation_tests()
    sys.exit(exit_code)