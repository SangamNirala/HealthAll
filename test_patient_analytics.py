#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class PatientAnalyticsAPITester:
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

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
                    return success, response_data
                except:
                    print(f"   Response: {response.text[:200]}...")
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:500]}...")
                return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_patient_analytics_endpoints(self):
        """Test Patient Analytics endpoints for the new Patient Analytics page"""
        print("\n📋 Testing Patient Analytics Endpoints...")
        
        test_user_id = "demo-patient-123"
        
        # Test 1: GET /api (root endpoint)
        print("\n📝 Test 1: Basic API Root Endpoint")
        success_root, root_data = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        
        # Validate root response has message
        if success_root and root_data:
            if 'message' in root_data:
                print(f"   ✅ Root endpoint contains 'message' key")
            else:
                print(f"   ❌ Root endpoint missing 'message' key")
                success_root = False
        
        # Test 2: GET /api/patient/analytics/{user_id}
        print(f"\n📝 Test 2: Patient Analytics for user_id={test_user_id}")
        success1, analytics_data = self.run_test(
            "Patient Analytics",
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
        
        # Test 3: GET /api/patient/smart-suggestions/{user_id}
        print(f"\n📝 Test 3: Patient Smart Suggestions for user_id={test_user_id}")
        success2, suggestions_data = self.run_test(
            "Patient Smart Suggestions",
            "GET",
            f"patient/smart-suggestions/{test_user_id}",
            200
        )
        
        # Validate smart suggestions response structure
        if success2 and suggestions_data:
            expected_keys = ['quick_add_suggestions', 'meal_pattern_insights']
            missing_keys = [key for key in expected_keys if key not in suggestions_data]
            if not missing_keys:
                print(f"   ✅ Smart suggestions response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Smart suggestions response missing keys: {missing_keys}")
                success2 = False
        
        # Test 4: GET /api/patient/symptoms-correlation/{user_id}
        print(f"\n📝 Test 4: Patient Symptoms Correlation for user_id={test_user_id}")
        success3, correlation_data = self.run_test(
            "Patient Symptoms Correlation",
            "GET",
            f"patient/symptoms-correlation/{test_user_id}",
            200
        )
        
        # Validate symptoms correlation response structure
        if success3 and correlation_data:
            expected_keys = ['correlations', 'recommendations']
            missing_keys = [key for key in expected_keys if key not in correlation_data]
            if not missing_keys:
                print(f"   ✅ Symptoms correlation response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Symptoms correlation response missing keys: {missing_keys}")
                success3 = False
        
        return success_root, success1, success2, success3

    def run_tests(self):
        """Run Patient Analytics API tests"""
        print("🚀 Starting Patient Analytics API Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)

        # Test patient analytics endpoints
        success_root, success1, success2, success3 = self.test_patient_analytics_endpoints()

        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 PATIENT ANALYTICS TEST RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 Individual Test Results:")
        print(f"   GET /api (root): {'✅' if success_root else '❌'}")
        print(f"   GET /api/patient/analytics/demo-patient-123: {'✅' if success1 else '❌'}")
        print(f"   GET /api/patient/smart-suggestions/demo-patient-123: {'✅' if success2 else '❌'}")
        print(f"   GET /api/patient/symptoms-correlation/demo-patient-123: {'✅' if success3 else '❌'}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All Patient Analytics tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the details above.")
            return 1

if __name__ == "__main__":
    tester = PatientAnalyticsAPITester()
    exit_code = tester.run_tests()
    sys.exit(exit_code)