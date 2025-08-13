#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class ClinicalDashboardTester:
    def __init__(self, base_url="https://caretrack-test.preview.emergentagent.com/api"):
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
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
                except:
                    print(f"   Response: {response.text[:300]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

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

    def test_enhanced_clinical_dashboard_endpoints(self):
        """Test Enhanced Clinical Dashboard API endpoints for Phase 4.1"""
        print("🏥 PHASE 4.1 COMPREHENSIVE BACKEND TESTING: Enhanced Clinical Dashboard API Endpoints")
        print("=" * 80)
        
        provider_id = "demo-provider-123"
        
        # Test 1: GET /api/provider/patient-queue/{provider_id}
        print("\n📝 Test 1: Patient Queue Management System")
        success1, queue_data = self.run_test(
            "GET /api/provider/patient-queue/{provider_id}",
            "GET",
            f"provider/patient-queue/{provider_id}",
            200
        )
        
        # Validate patient queue response structure
        if success1 and queue_data:
            expected_keys = ['provider_id', 'queue_stats', 'priority_queue', 'scheduled_queue']
            missing_keys = [key for key in expected_keys if key not in queue_data]
            if not missing_keys:
                print(f"   ✅ Patient queue response structure valid")
                queue_stats = queue_data.get('queue_stats', {})
                print(f"   📊 Queue Stats: {queue_stats.get('total_in_queue', 0)} total, {queue_stats.get('urgent', 0)} urgent")
            else:
                print(f"   ❌ Missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: GET /api/provider/clinical-insights/{provider_id}
        print("\n📝 Test 2: AI-Powered Clinical Decision Support")
        success2, insights_data = self.run_test(
            "GET /api/provider/clinical-insights/{provider_id}",
            "GET",
            f"provider/clinical-insights/{provider_id}",
            200
        )
        
        # Validate clinical insights response structure
        if success2 and insights_data:
            expected_keys = ['provider_id', 'ai_recommendations', 'clinical_alerts']
            missing_keys = [key for key in expected_keys if key not in insights_data]
            if not missing_keys:
                print(f"   ✅ Clinical insights response structure valid")
                ai_recommendations = insights_data.get('ai_recommendations', [])
                print(f"   🧠 AI Recommendations: {len(ai_recommendations)} available")
            else:
                print(f"   ❌ Missing keys: {missing_keys}")
                success2 = False
        
        # Test 3: GET /api/provider/treatment-outcomes/{provider_id}
        print("\n📝 Test 3: Treatment Outcome Tracking")
        success3, outcomes_data = self.run_test(
            "GET /api/provider/treatment-outcomes/{provider_id}",
            "GET",
            f"provider/treatment-outcomes/{provider_id}",
            200
        )
        
        # Test with timeframe parameter
        success3b, outcomes_data_30d = self.run_test(
            "GET /api/provider/treatment-outcomes/{provider_id} (30d timeframe)",
            "GET",
            f"provider/treatment-outcomes/{provider_id}",
            200,
            params={"timeframe": "30d"}
        )
        
        # Validate treatment outcomes response structure
        if success3 and outcomes_data:
            expected_keys = ['provider_id', 'timeframe', 'outcome_summary']
            missing_keys = [key for key in expected_keys if key not in outcomes_data]
            if not missing_keys:
                print(f"   ✅ Treatment outcomes response structure valid")
                outcome_summary = outcomes_data.get('outcome_summary', {})
                print(f"   📈 Success Rate: {outcome_summary.get('success_rate', 0)}%")
                print(f"   😊 Patient Satisfaction: {outcome_summary.get('patient_satisfaction', 0)}/5")
            else:
                print(f"   ❌ Missing keys: {missing_keys}")
                success3 = False
        
        # Test 4: GET /api/provider/population-health/{provider_id}
        print("\n📝 Test 4: Population Health Analytics")
        success4, population_data = self.run_test(
            "GET /api/provider/population-health/{provider_id}",
            "GET",
            f"provider/population-health/{provider_id}",
            200
        )
        
        # Validate population health response structure
        if success4 and population_data:
            expected_keys = ['provider_id', 'population_overview', 'demographic_breakdown']
            missing_keys = [key for key in expected_keys if key not in population_data]
            if not missing_keys:
                print(f"   ✅ Population health response structure valid")
                population_overview = population_data.get('population_overview', {})
                print(f"   👥 Total Population: {population_overview.get('total_population', 0)}")
                print(f"   🏃 Active Patients: {population_overview.get('active_patients', 0)}")
            else:
                print(f"   ❌ Missing keys: {missing_keys}")
                success4 = False
        
        # Test 5: POST /api/provider/evidence-recommendations
        print("\n📝 Test 5: AI-Powered Evidence-Based Recommendations")
        evidence_request_data = {
            "condition": "Type 2 Diabetes",
            "patient_profile": {
                "age": 45,
                "gender": "male",
                "bmi": 28.5,
                "hba1c": 8.2,
                "comorbidities": ["hypertension", "obesity"],
                "current_medications": ["metformin", "lisinopril"]
            },
            "clinical_context": {
                "presentation": "routine_followup",
                "recent_labs": {
                    "hba1c": 8.2,
                    "fasting_glucose": 165,
                    "blood_pressure": "145/92"
                },
                "treatment_goals": ["glycemic_control", "weight_reduction"]
            }
        }
        
        success5, evidence_data = self.run_test(
            "POST /api/provider/evidence-recommendations",
            "POST",
            "provider/evidence-recommendations",
            200,
            data=evidence_request_data
        )
        
        # Validate evidence recommendations response structure
        if success5 and evidence_data:
            expected_keys = ['request_id', 'condition', 'evidence_level', 'recommendations']
            missing_keys = [key for key in expected_keys if key not in evidence_data]
            if not missing_keys:
                print(f"   ✅ Evidence recommendations response structure valid")
                recommendations = evidence_data.get('recommendations', [])
                print(f"   📚 Evidence-Based Recommendations: {len(recommendations)} available")
                print(f"   🎯 Evidence Level: {evidence_data.get('evidence_level', 'Unknown')}")
            else:
                print(f"   ❌ Missing keys: {missing_keys}")
                success5 = False
        
        # Test 6: GET /api/provider/continuing-education/{provider_id}
        print("\n📝 Test 6: Professional Continuing Education Portal")
        success6, education_data = self.run_test(
            "GET /api/provider/continuing-education/{provider_id}",
            "GET",
            f"provider/continuing-education/{provider_id}",
            200
        )
        
        # Validate continuing education response structure
        if success6 and education_data:
            expected_keys = ['provider_id', 'education_summary', 'available_courses', 'cme_tracking']
            missing_keys = [key for key in expected_keys if key not in education_data]
            if not missing_keys:
                print(f"   ✅ Continuing education response structure valid")
                education_summary = education_data.get('education_summary', {})
                print(f"   🎓 CME Credits: {education_summary.get('credits_earned_this_year', 0)}/{education_summary.get('credits_required', 0)}")
                print(f"   📋 Compliance Status: {education_summary.get('compliance_status', 'Unknown')}")
            else:
                print(f"   ❌ Missing keys: {missing_keys}")
                success6 = False
        
        # Test 7: Error Handling - Invalid Provider ID
        print("\n📝 Test 7: Error Handling - Invalid Provider ID")
        success7, _ = self.run_test(
            "Patient Queue - Invalid Provider ID (Should Return 404)",
            "GET",
            "provider/patient-queue/invalid-provider-999",
            404
        )
        
        # Test 8: Real-time Data Support Verification
        print("\n📝 Test 8: Real-time Data Support Verification")
        
        # Test multiple quick requests to verify real-time capabilities
        import time
        start_time = time.time()
        
        realtime_tests = [
            (f"provider/patient-queue/{provider_id}", "Patient Queue Real-time"),
            (f"provider/clinical-insights/{provider_id}", "Clinical Insights Real-time"),
            (f"provider/treatment-outcomes/{provider_id}", "Treatment Outcomes Real-time")
        ]
        
        realtime_success = True
        for endpoint, test_name in realtime_tests:
            success, _ = self.run_test(
                test_name,
                "GET",
                endpoint,
                200
            )
            if not success:
                realtime_success = False
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"   ⏱️ Real-time test completed in {total_time:.2f} seconds")
        if total_time < 5.0:
            print(f"   ✅ Response times support real-time monitoring")
        else:
            print(f"   ⚠️ Response times may be slow for real-time monitoring")
        
        # Calculate overall success
        core_endpoints_success = success1 and success2 and success3 and success3b and success4 and success5 and success6
        error_handling_success = success7
        
        overall_success = core_endpoints_success and error_handling_success and realtime_success
        
        return overall_success, {
            'patient_queue': success1,
            'clinical_insights': success2,
            'treatment_outcomes': success3 and success3b,
            'population_health': success4,
            'evidence_recommendations': success5,
            'continuing_education': success6,
            'error_handling': success7,
            'realtime_support': realtime_success
        }

    def run_comprehensive_test(self):
        """Run comprehensive Enhanced Clinical Dashboard API test"""
        print("🚀 Starting Enhanced Clinical Dashboard API Comprehensive Test")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 80)

        overall_success, detailed_results = self.test_enhanced_clinical_dashboard_endpoints()

        # Print final results
        print("\n" + "=" * 80)
        print(f"📊 ENHANCED CLINICAL DASHBOARD API TEST RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🎯 DETAILED ENDPOINT RESULTS:")
        print(f"   ✅ Patient Queue Management: {'PASS' if detailed_results['patient_queue'] else 'FAIL'}")
        print(f"   ✅ Clinical Decision Support: {'PASS' if detailed_results['clinical_insights'] else 'FAIL'}")
        print(f"   ✅ Treatment Outcomes Tracking: {'PASS' if detailed_results['treatment_outcomes'] else 'FAIL'}")
        print(f"   ✅ Population Health Analytics: {'PASS' if detailed_results['population_health'] else 'FAIL'}")
        print(f"   ✅ Evidence-Based Recommendations: {'PASS' if detailed_results['evidence_recommendations'] else 'FAIL'}")
        print(f"   ✅ Continuing Education Portal: {'PASS' if detailed_results['continuing_education'] else 'FAIL'}")
        print(f"   ✅ Error Handling: {'PASS' if detailed_results['error_handling'] else 'FAIL'}")
        print(f"   ✅ Real-time Data Support: {'PASS' if detailed_results['realtime_support'] else 'FAIL'}")
        
        print(f"\n🏥 OVERALL ENHANCED CLINICAL DASHBOARD: {'✅ READY FOR PHASE 4.2' if overall_success else '❌ NEEDS FIXES'}")
        
        if overall_success:
            print("\n🎉 All Enhanced Clinical Dashboard API endpoints are working correctly!")
            print("✅ Ready for Phase 4.2 frontend testing")
            return 0
        else:
            print("\n⚠️ Some Enhanced Clinical Dashboard API endpoints failed.")
            print("❌ Backend issues need to be resolved before Phase 4.2 frontend testing")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result.get('success', False):
                    print(f"  - {result['name']}: {result.get('error', 'Status code mismatch')}")
            return 1

def main():
    """Main test execution"""
    tester = ClinicalDashboardTester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())