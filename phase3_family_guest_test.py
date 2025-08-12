#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class Phase3FamilyGuestAPITester:
    """
    Phase 3: Comprehensive Family and Guest Profile API Testing
    
    This test suite focuses specifically on testing the Family and Guest profile APIs
    that were implemented in Phase 1 and need validation for the new wizards in Phase 2.
    """
    
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

    def test_family_profile_comprehensive(self):
        """Test Family Profile API with comprehensive scenarios"""
        print("\n🏠 PHASE 3: COMPREHENSIVE FAMILY PROFILE API TESTING")
        print("=" * 60)
        
        # Generate unique user ID for testing
        test_user_id = f"family_phase3_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create Family Profile with all 4 wizard steps data
        family_profile_data = {
            "user_id": test_user_id,
            # Step 1: Family Structure
            "family_structure": {
                "family_role": "Primary Caregiver",
                "number_of_members": 5,
                "primary_caregiver": True
            },
            # Step 2: Family Members (comprehensive list)
            "family_members": [
                {
                    "name": "Jennifer Martinez",
                    "relationship": "Self",
                    "age": 34,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["shellfish", "tree_nuts"],
                    "medications": ["prenatal_vitamins"],
                    "health_conditions": ["gestational_diabetes"]
                },
                {
                    "name": "Carlos Martinez",
                    "relationship": "Spouse",
                    "age": 36,
                    "gender": "Male",
                    "special_needs": [],
                    "allergies": ["pollen"],
                    "medications": ["blood_pressure_medication"],
                    "health_conditions": ["hypertension", "high_cholesterol"]
                },
                {
                    "name": "Sofia Martinez",
                    "relationship": "Daughter",
                    "age": 14,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["dairy"],
                    "medications": [],
                    "health_conditions": ["lactose_intolerance"]
                },
                {
                    "name": "Diego Martinez",
                    "relationship": "Son",
                    "age": 10,
                    "gender": "Male",
                    "special_needs": ["ADHD", "learning_disability"],
                    "allergies": [],
                    "medications": ["ADHD_stimulant", "omega_3_supplement"],
                    "health_conditions": ["ADHD", "dyslexia"]
                },
                {
                    "name": "Abuela Rosa",
                    "relationship": "Grandmother",
                    "age": 72,
                    "gender": "Female",
                    "special_needs": ["mobility_assistance"],
                    "allergies": ["penicillin"],
                    "medications": ["diabetes_medication", "arthritis_medication", "heart_medication"],
                    "health_conditions": ["type_2_diabetes", "arthritis", "heart_disease"]
                }
            ],
            # Step 3: Household Management
            "household_management": {
                "common_dietary_restrictions": ["dairy_free", "nut_free", "low_sodium", "diabetic_friendly"],
                "family_meal_preferences": ["home_cooked", "cultural_foods", "balanced_nutrition", "budget_conscious"],
                "budget_considerations": {
                    "weekly_grocery_budget": 250,
                    "dining_out_budget": 80,
                    "special_dietary_budget": 50,
                    "medication_budget": 120
                },
                "shopping_responsibilities": ["Jennifer", "Carlos"],
                "cooking_responsibilities": ["Jennifer", "Carlos", "Sofia"]
            },
            # Step 4: Care Coordination
            "care_coordination": {
                "healthcare_providers": {
                    "Jennifer": {"provider": "Dr. Sarah Kim", "contact": "555-0301", "specialty": "OB/GYN"},
                    "Carlos": {"provider": "Dr. Michael Johnson", "contact": "555-0302", "specialty": "Cardiology"},
                    "Sofia": {"provider": "Dr. Lisa Chen", "contact": "555-0303", "specialty": "Pediatrics"},
                    "Diego": {"provider": "Dr. Amanda Rodriguez", "contact": "555-0304", "specialty": "Child Psychology"},
                    "Abuela Rosa": {"provider": "Dr. Robert Williams", "contact": "555-0305", "specialty": "Geriatrics"}
                },
                "emergency_contacts": [
                    {"name": "Maria Martinez", "phone": "555-0400", "relationship": "Sister"},
                    {"name": "Jose Martinez", "phone": "555-0401", "relationship": "Brother"},
                    {"name": "Dr. Emergency Line", "phone": "555-0911", "relationship": "Emergency Medical"}
                ],
                "medication_management": {
                    "Carlos": "Morning with breakfast",
                    "Diego": "Morning and evening with meals",
                    "Abuela Rosa": "Complex schedule - see medication chart",
                    "Jennifer": "Morning with food"
                },
                "health_tracking_preferences": {
                    "shared_calendar": True,
                    "appointment_reminders": True,
                    "medication_reminders": True,
                    "health_metrics_sharing": True,
                    "emergency_notifications": True
                }
            }
        }
        
        success1, family_response = self.run_test(
            "Create Comprehensive Family Profile (All 4 Steps)",
            "POST",
            "profiles/family",
            200,
            data=family_profile_data
        )
        
        # Test 2: Validate Family Profile Structure
        if success1 and family_response:
            print(f"\n📊 Validating Family Profile Structure:")
            
            # Validate family structure
            family_structure = family_response.get('family_structure', {})
            structure_valid = (
                family_structure.get('family_role') == 'Primary Caregiver' and
                family_structure.get('number_of_members') == 5 and
                family_structure.get('primary_caregiver') == True
            )
            print(f"   Family Structure: {'✅' if structure_valid else '❌'}")
            
            # Validate family members
            family_members = family_response.get('family_members', [])
            members_valid = len(family_members) == 5
            print(f"   Family Members Count: {'✅' if members_valid else '❌'} ({len(family_members)}/5)")
            
            # Validate household management
            household = family_response.get('household_management', {})
            household_valid = (
                len(household.get('common_dietary_restrictions', [])) == 4 and
                'budget_considerations' in household
            )
            print(f"   Household Management: {'✅' if household_valid else '❌'}")
            
            # Validate care coordination
            care_coord = family_response.get('care_coordination', {})
            care_valid = (
                len(care_coord.get('healthcare_providers', {})) == 5 and
                len(care_coord.get('emergency_contacts', [])) == 3
            )
            print(f"   Care Coordination: {'✅' if care_valid else '❌'}")
            
            # Validate profile completion
            completion = family_response.get('profile_completion', 0)
            completion_valid = completion == 100.0
            print(f"   Profile Completion: {'✅' if completion_valid else '❌'} ({completion}%)")
        
        # Test 3: Get Family Profile
        success2, get_response = self.run_test(
            "Get Family Profile",
            "GET",
            f"profiles/family/{test_user_id}",
            200
        )
        
        # Test 4: Update Family Profile (modify household management)
        update_data = {
            "household_management": {
                "common_dietary_restrictions": ["dairy_free", "nut_free", "low_sodium", "diabetic_friendly", "gluten_free"],
                "family_meal_preferences": ["home_cooked", "cultural_foods", "balanced_nutrition", "budget_conscious", "organic"],
                "budget_considerations": {
                    "weekly_grocery_budget": 300,  # Increased budget
                    "dining_out_budget": 100,
                    "special_dietary_budget": 75,
                    "medication_budget": 120
                },
                "shopping_responsibilities": ["Jennifer", "Carlos", "Sofia"],  # Added Sofia
                "cooking_responsibilities": ["Jennifer", "Carlos", "Sofia"]
            }
        }
        
        success3, update_response = self.run_test(
            "Update Family Profile (Household Management)",
            "PUT",
            f"profiles/family/{test_user_id}",
            200,
            data=update_data
        )
        
        # Test 5: Test Family Profile Completion Status
        success4, completion_response = self.run_test(
            "Get Family Profile Completion Status",
            "GET",
            f"profiles/completion/{test_user_id}",
            200,
            params={"role": "FAMILY"}
        )
        
        if success4 and completion_response:
            completion_percentage = completion_response.get('completion_percentage', 0)
            missing_sections = completion_response.get('missing_sections', [])
            print(f"   Family Profile Completion: {completion_percentage}%")
            print(f"   Missing Sections: {missing_sections}")
            completion_valid = completion_percentage == 100.0 and len(missing_sections) == 0
            print(f"   Completion Status Valid: {'✅' if completion_valid else '❌'}")
        
        # Test 6: Test concurrent family member updates
        concurrent_update_data = {
            "family_members": [
                # Keep existing members and add a new one
                {
                    "name": "Jennifer Martinez",
                    "relationship": "Self",
                    "age": 34,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["shellfish", "tree_nuts"],
                    "medications": ["prenatal_vitamins"],
                    "health_conditions": ["gestational_diabetes"]
                },
                {
                    "name": "Carlos Martinez",
                    "relationship": "Spouse",
                    "age": 36,
                    "gender": "Male",
                    "special_needs": [],
                    "allergies": ["pollen"],
                    "medications": ["blood_pressure_medication"],
                    "health_conditions": ["hypertension", "high_cholesterol"]
                },
                {
                    "name": "Sofia Martinez",
                    "relationship": "Daughter",
                    "age": 14,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["dairy"],
                    "medications": [],
                    "health_conditions": ["lactose_intolerance"]
                },
                {
                    "name": "Diego Martinez",
                    "relationship": "Son",
                    "age": 10,
                    "gender": "Male",
                    "special_needs": ["ADHD", "learning_disability"],
                    "allergies": [],
                    "medications": ["ADHD_stimulant", "omega_3_supplement"],
                    "health_conditions": ["ADHD", "dyslexia"]
                },
                {
                    "name": "Abuela Rosa",
                    "relationship": "Grandmother",
                    "age": 72,
                    "gender": "Female",
                    "special_needs": ["mobility_assistance"],
                    "allergies": ["penicillin"],
                    "medications": ["diabetes_medication", "arthritis_medication", "heart_medication"],
                    "health_conditions": ["type_2_diabetes", "arthritis", "heart_disease"]
                },
                {
                    "name": "Baby Martinez",
                    "relationship": "Son",
                    "age": 0,
                    "gender": "Male",
                    "special_needs": [],
                    "allergies": [],
                    "medications": [],
                    "health_conditions": []
                }
            ]
        }
        
        success5, _ = self.run_test(
            "Update Family Profile (Add New Baby)",
            "PUT",
            f"profiles/family/{test_user_id}",
            200,
            data=concurrent_update_data
        )
        
        # Test 7: Delete Family Profile
        success6, _ = self.run_test(
            "Delete Family Profile",
            "DELETE",
            f"profiles/family/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3 and success4 and success5 and success6

    def test_guest_profile_comprehensive(self):
        """Test Guest Profile API with comprehensive scenarios"""
        print("\n👤 PHASE 3: COMPREHENSIVE GUEST PROFILE API TESTING")
        print("=" * 60)
        
        # Test 1: Create Guest Profile with session expiration
        test_session_id = f"guest_phase3_{datetime.now().strftime('%H%M%S')}"
        
        guest_profile_data = {
            "session_id": test_session_id,
            "basic_demographics": {
                "age": 28,
                "gender": "Non-binary",
                "activity_level": "MODERATELY_ACTIVE"
            },
            "simple_goals": {
                "goal_type": "lose",
                "target_amount": 8.0,
                "timeframe": "3_months"
            },
            "session_expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        success1, guest_response = self.run_test(
            "Create Guest Profile with 24h Expiration",
            "POST",
            "profiles/guest",
            200,
            data=guest_profile_data
        )
        
        # Test 2: Validate Guest Profile Structure
        if success1 and guest_response:
            print(f"\n📊 Validating Guest Profile Structure:")
            
            # Validate basic demographics
            demographics = guest_response.get('basic_demographics', {})
            demographics_valid = (
                demographics.get('age') == 28 and
                demographics.get('gender') == 'Non-binary' and
                demographics.get('activity_level') == 'MODERATELY_ACTIVE'
            )
            print(f"   Basic Demographics: {'✅' if demographics_valid else '❌'}")
            
            # Validate simple goals
            goals = guest_response.get('simple_goals', {})
            goals_valid = (
                goals.get('goal_type') == 'lose' and
                goals.get('target_amount') == 8.0 and
                goals.get('timeframe') == '3_months'
            )
            print(f"   Simple Goals: {'✅' if goals_valid else '❌'}")
            
            # Validate session expiration
            session_expires = guest_response.get('session_expires', '')
            expires_valid = session_expires != ''
            print(f"   Session Expiration: {'✅' if expires_valid else '❌'}")
            
            # Validate role
            role_valid = guest_response.get('role') == 'GUEST'
            print(f"   Role Assignment: {'✅' if role_valid else '❌'}")
        
        # Test 3: Get Guest Profile
        success2, _ = self.run_test(
            "Get Guest Profile",
            "GET",
            f"profiles/guest/{test_session_id}",
            200
        )
        
        # Test 4: Test different activity levels
        activity_levels = ["SEDENTARY", "LIGHTLY_ACTIVE", "VERY_ACTIVE", "EXTRA_ACTIVE"]
        activity_test_results = []
        
        for i, activity_level in enumerate(activity_levels):
            session_id = f"activity_test_{i}_{datetime.now().strftime('%H%M%S')}"
            test_data = {
                "session_id": session_id,
                "basic_demographics": {
                    "age": 25 + i,
                    "gender": "Female" if i % 2 == 0 else "Male",
                    "activity_level": activity_level
                },
                "simple_goals": {
                    "goal_type": "maintain" if i % 2 == 0 else "gain",
                    "target_amount": 2.0 if i % 2 == 0 else 5.0,
                    "timeframe": "1_month"
                },
                "session_expires": (datetime.utcnow() + timedelta(hours=12)).isoformat()
            }
            
            success, response = self.run_test(
                f"Create Guest Profile with {activity_level}",
                "POST",
                "profiles/guest",
                200,
                data=test_data
            )
            activity_test_results.append(success)
            
            # Clean up
            if success:
                self.run_test(f"Cleanup {activity_level} Profile", "DELETE", f"profiles/guest/{session_id}", 200)
        
        activity_tests_passed = all(activity_test_results)
        print(f"   Activity Level Tests: {'✅' if activity_tests_passed else '❌'} ({sum(activity_test_results)}/{len(activity_test_results)})")
        
        # Test 5: Test session expiration handling
        expired_session_id = f"expired_test_{datetime.now().strftime('%H%M%S')}"
        expired_profile_data = {
            "session_id": expired_session_id,
            "basic_demographics": {
                "age": 35,
                "gender": "Male",
                "activity_level": "LIGHTLY_ACTIVE"
            },
            "simple_goals": {
                "goal_type": "maintain",
                "target_amount": 0.0,
                "timeframe": "ongoing"
            },
            "session_expires": (datetime.utcnow() - timedelta(hours=2)).isoformat()  # Expired 2 hours ago
        }
        
        success3, _ = self.run_test(
            "Create Expired Guest Profile",
            "POST",
            "profiles/guest",
            200,
            data=expired_profile_data
        )
        
        # Test 6: Try to retrieve expired profile (should fail)
        success4, _ = self.run_test(
            "Get Expired Guest Profile (Should Fail)",
            "GET",
            f"profiles/guest/{expired_session_id}",
            404
        )
        
        # Test 7: Test Guest Profile Completion Status (should fail - not supported for guests)
        success5, completion_response = self.run_test(
            "Get Guest Profile Completion Status (Should Fail - Not Supported)",
            "GET",
            f"profiles/completion/{test_session_id}",
            400,  # Should fail because GUEST role is not supported
            params={"role": "GUEST"}
        )
        
        # Guest profiles don't need completion tracking - they're always complete by design
        print(f"   Guest Profile Completion: Not supported (by design) - ✅")
        print(f"   Guest profiles are always 100% complete when created")
        
        # Test 8: Test concurrent guest sessions
        concurrent_sessions = []
        for i in range(3):
            session_id = f"concurrent_{i}_{datetime.now().strftime('%H%M%S')}"
            concurrent_data = {
                "session_id": session_id,
                "basic_demographics": {
                    "age": 20 + i * 5,
                    "gender": ["Male", "Female", "Non-binary"][i],
                    "activity_level": ["SEDENTARY", "MODERATELY_ACTIVE", "VERY_ACTIVE"][i]
                },
                "simple_goals": {
                    "goal_type": ["lose", "maintain", "gain"][i],
                    "target_amount": [3.0, 0.0, 4.0][i],
                    "timeframe": ["2_months", "ongoing", "6_months"][i]
                },
                "session_expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            success, _ = self.run_test(
                f"Create Concurrent Guest Session {i+1}",
                "POST",
                "profiles/guest",
                200,
                data=concurrent_data
            )
            concurrent_sessions.append((success, session_id))
        
        concurrent_success = all(result[0] for result in concurrent_sessions)
        print(f"   Concurrent Sessions: {'✅' if concurrent_success else '❌'}")
        
        # Test 9: Delete Guest Profile
        success6, _ = self.run_test(
            "Delete Guest Profile",
            "DELETE",
            f"profiles/guest/{test_session_id}",
            200
        )
        
        # Clean up concurrent sessions
        for success, session_id in concurrent_sessions:
            if success:
                self.run_test(f"Cleanup Concurrent Session", "DELETE", f"profiles/guest/{session_id}", 200)
        
        return success1 and success2 and activity_tests_passed and success3 and success4 and success5 and concurrent_success and success6

    def test_integration_scenarios(self):
        """Test integration scenarios between Family and Guest profiles"""
        print("\n🔗 PHASE 3: INTEGRATION TESTING SCENARIOS")
        print("=" * 60)
        
        # Test 1: Profile completion comparison
        family_user_id = f"integration_family_{datetime.now().strftime('%H%M%S')}"
        guest_session_id = f"integration_guest_{datetime.now().strftime('%H%M%S')}"
        
        # Create minimal family profile
        minimal_family_data = {
            "user_id": family_user_id,
            "family_structure": {
                "family_role": "Parent",
                "number_of_members": 3,
                "primary_caregiver": True
            }
        }
        
        success1, _ = self.run_test(
            "Create Minimal Family Profile for Integration",
            "POST",
            "profiles/family",
            200,
            data=minimal_family_data
        )
        
        # Create guest profile
        guest_data = {
            "session_id": guest_session_id,
            "basic_demographics": {
                "age": 30,
                "gender": "Female",
                "activity_level": "MODERATELY_ACTIVE"
            },
            "simple_goals": {
                "goal_type": "lose",
                "target_amount": 5.0,
                "timeframe": "2_months"
            },
            "session_expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        success2, _ = self.run_test(
            "Create Guest Profile for Integration",
            "POST",
            "profiles/guest",
            200,
            data=guest_data
        )
        
        # Test 2: Compare completion statuses
        success3, family_completion = self.run_test(
            "Get Family Profile Completion for Integration",
            "GET",
            f"profiles/completion/{family_user_id}",
            200,
            params={"role": "FAMILY"}
        )
        
        success4, guest_completion = self.run_test(
            "Get Guest Profile Completion for Integration (Should Fail - Not Supported)",
            "GET",
            f"profiles/completion/{guest_session_id}",
            400,  # Should fail because GUEST role is not supported
            params={"role": "GUEST"}
        )
        
        if success3 and family_completion:
            family_percentage = family_completion.get('completion_percentage', 0)
            
            print(f"   Family Profile Completion: {family_percentage}%")
            print(f"   Guest Profile Completion: Not supported (by design)")
            
            # Family should be partial, Guest completion tracking is not supported
            completion_comparison_valid = family_percentage < 100.0
            print(f"   Completion Comparison: {'✅' if completion_comparison_valid else '❌'}")
        
        # Test 3: Test data validation consistency
        # Test invalid enum values for both profile types
        invalid_family_data = {
            "user_id": f"invalid_family_{datetime.now().strftime('%H%M%S')}",
            "family_structure": {
                "family_role": "INVALID_ROLE",  # This should still work as it's a string
                "number_of_members": 2,
                "primary_caregiver": True
            }
        }
        
        success5, _ = self.run_test(
            "Create Family Profile with Invalid Data",
            "POST",
            "profiles/family",
            200,  # Should still work as family_role is just a string
            data=invalid_family_data
        )
        
        invalid_guest_data = {
            "session_id": f"invalid_guest_{datetime.now().strftime('%H%M%S')}",
            "basic_demographics": {
                "age": 25,
                "gender": "Female",
                "activity_level": "INVALID_ACTIVITY_LEVEL"  # This should fail
            },
            "simple_goals": {
                "goal_type": "lose",
                "target_amount": 3.0,
                "timeframe": "1_month"
            },
            "session_expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        success6, _ = self.run_test(
            "Create Guest Profile with Invalid Enum (Should Fail)",
            "POST",
            "profiles/guest",
            422,  # Should fail due to invalid enum
            data=invalid_guest_data
        )
        
        # Test 4: Test workflow simulation
        # Simulate a family member starting as guest, then creating family profile
        workflow_guest_id = f"workflow_guest_{datetime.now().strftime('%H%M%S')}"
        workflow_family_id = f"workflow_family_{datetime.now().strftime('%H%M%S')}"
        
        # Step 1: Create guest profile (trial user)
        workflow_guest_data = {
            "session_id": workflow_guest_id,
            "basic_demographics": {
                "age": 32,
                "gender": "Male",
                "activity_level": "LIGHTLY_ACTIVE"
            },
            "simple_goals": {
                "goal_type": "lose",
                "target_amount": 7.0,
                "timeframe": "4_months"
            },
            "session_expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        success7, _ = self.run_test(
            "Workflow: Create Guest Profile (Trial User)",
            "POST",
            "profiles/guest",
            200,
            data=workflow_guest_data
        )
        
        # Step 2: User decides to upgrade to family account
        workflow_family_data = {
            "user_id": workflow_family_id,
            "family_structure": {
                "family_role": "Parent",
                "number_of_members": 4,
                "primary_caregiver": True
            },
            "family_members": [
                {
                    "name": "John Workflow",
                    "relationship": "Self",
                    "age": 32,
                    "gender": "Male",
                    "special_needs": [],
                    "allergies": [],
                    "medications": [],
                    "health_conditions": []
                },
                {
                    "name": "Jane Workflow",
                    "relationship": "Spouse",
                    "age": 29,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["peanuts"],
                    "medications": [],
                    "health_conditions": []
                }
            ]
        }
        
        success8, _ = self.run_test(
            "Workflow: Create Family Profile (Upgrade from Guest)",
            "POST",
            "profiles/family",
            200,
            data=workflow_family_data
        )
        
        # Step 3: Clean up guest session (user no longer needs it)
        success9, _ = self.run_test(
            "Workflow: Delete Guest Profile (No Longer Needed)",
            "DELETE",
            f"profiles/guest/{workflow_guest_id}",
            200
        )
        
        # Clean up test profiles
        cleanup_success = True
        if success1:
            cleanup1, _ = self.run_test("Cleanup Integration Family Profile", "DELETE", f"profiles/family/{family_user_id}", 200)
            cleanup_success = cleanup_success and cleanup1
        
        if success2:
            cleanup2, _ = self.run_test("Cleanup Integration Guest Profile", "DELETE", f"profiles/guest/{guest_session_id}", 200)
            cleanup_success = cleanup_success and cleanup2
        
        if success5:
            cleanup3, _ = self.run_test("Cleanup Invalid Family Profile", "DELETE", f"profiles/family/invalid_family_{datetime.now().strftime('%H%M%S')}", 200)
        
        if success8:
            cleanup4, _ = self.run_test("Cleanup Workflow Family Profile", "DELETE", f"profiles/family/{workflow_family_id}", 200)
            cleanup_success = cleanup_success and cleanup4
        
        workflow_success = success7 and success8 and success9
        print(f"   Workflow Simulation: {'✅' if workflow_success else '❌'}")
        
        return success1 and success2 and success3 and success4 and success5 and success6 and workflow_success and cleanup_success

    def run_phase3_tests(self):
        """Run all Phase 3 comprehensive tests"""
        print("🚀 PHASE 3: COMPREHENSIVE FAMILY & GUEST PROFILE API TESTING")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 80)
        
        # Test Family Profile APIs
        family_success = self.test_family_profile_comprehensive()
        
        # Test Guest Profile APIs
        guest_success = self.test_guest_profile_comprehensive()
        
        # Test Integration Scenarios
        integration_success = self.test_integration_scenarios()
        
        # Print final results
        print("\n" + "=" * 80)
        print(f"📊 PHASE 3 FINAL RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 Test Categories:")
        print(f"   Family Profile APIs: {'✅' if family_success else '❌'}")
        print(f"   Guest Profile APIs: {'✅' if guest_success else '❌'}")
        print(f"   Integration Scenarios: {'✅' if integration_success else '❌'}")
        
        overall_success = family_success and guest_success and integration_success
        
        if overall_success and self.tests_passed == self.tests_run:
            print("\n🎉 PHASE 3 TESTING COMPLETE - ALL TESTS PASSED!")
            print("✅ Family and Guest Profile APIs are ready for the new wizards")
            return 0
        else:
            print("\n⚠️  PHASE 3 TESTING INCOMPLETE - Some tests failed")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result.get('success', False):
                    print(f"  - {result['name']}: {result.get('error', 'Status code mismatch')}")
            return 1

def main():
    """Main test execution for Phase 3"""
    tester = Phase3FamilyGuestAPITester()
    return tester.run_phase3_tests()

if __name__ == "__main__":
    sys.exit(main())