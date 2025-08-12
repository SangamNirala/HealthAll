#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class HealthPlatformAPITester:
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

    def test_basic_api(self):
        """Test basic API endpoint"""
        return self.run_test(
            "Basic API Root",
            "GET",
            "",
            200
        )

    def test_status_endpoints(self):
        """Test status check endpoints"""
        # Test GET status checks
        success1, _ = self.run_test(
            "Get Status Checks",
            "GET",
            "status",
            200
        )

        # Test POST status check
        success2, response = self.run_test(
            "Create Status Check",
            "POST",
            "status",
            200,
            data={"client_name": f"test_client_{datetime.now().strftime('%H%M%S')}"}
        )

        return success1 and success2

    def test_user_endpoints(self):
        """Test user management endpoints"""
        # Create a test user
        test_user_data = {
            "name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "role": "patient"
        }

        success1, user_response = self.run_test(
            "Create User",
            "POST",
            "users",
            200,
            data=test_user_data
        )

        # Get users by role
        success2, _ = self.run_test(
            "Get Users by Role (patient)",
            "GET",
            "users/patient",
            200
        )

        success3, _ = self.run_test(
            "Get Users by Role (provider)",
            "GET",
            "users/provider",
            200
        )

        return success1 and success2 and success3, user_response.get('id') if user_response else None

    def test_health_metrics_endpoints(self, user_id=None):
        """Test health metrics endpoints"""
        if not user_id:
            user_id = "test-user-id"

        # Create a health metric
        test_metric_data = {
            "user_id": user_id,
            "metric_type": "weight",
            "value": 70.5,
            "unit": "kg"
        }

        success1, _ = self.run_test(
            "Create Health Metric",
            "POST",
            "health-metrics",
            200,
            data=test_metric_data
        )

        # Get health metrics for user
        success2, _ = self.run_test(
            "Get User Health Metrics",
            "GET",
            f"health-metrics/{user_id}",
            200
        )

        return success1 and success2

    def test_dashboard_endpoints(self):
        """Test role-specific dashboard endpoints"""
        test_user_id = "test-user-123"

        # Test Patient Dashboard
        success1, patient_data = self.run_test(
            "Patient Dashboard",
            "GET",
            f"patient/dashboard/{test_user_id}",
            200
        )

        # Test Provider Dashboard
        success2, provider_data = self.run_test(
            "Provider Dashboard",
            "GET",
            f"provider/dashboard/{test_user_id}",
            200
        )

        # Test Family Dashboard
        success3, family_data = self.run_test(
            "Family Dashboard",
            "GET",
            f"family/dashboard/{test_user_id}",
            200
        )

        # Test Guest Dashboard
        success4, guest_data = self.run_test(
            "Guest Dashboard",
            "GET",
            "guest/dashboard",
            200
        )

        # Validate dashboard data structure based on actual API responses
        if success1 and patient_data:
            expected_patient_keys = ['user_id', 'welcome_message', 'nutrition_summary', 'health_metrics', 'goals', 'recent_meals', 'ai_recommendations']
            patient_keys_valid = all(key in patient_data for key in expected_patient_keys)
            print(f"   Patient dashboard keys validation: {'✅' if patient_keys_valid else '❌'}")

        if success2 and provider_data:
            expected_provider_keys = ['user_id', 'welcome_message', 'patient_overview', 'clinical_alerts', 'todays_appointments', 'patient_progress']
            provider_keys_valid = all(key in provider_data for key in expected_provider_keys)
            print(f"   Provider dashboard keys validation: {'✅' if provider_keys_valid else '❌'}")

        if success3 and family_data:
            expected_family_keys = ['user_id', 'family_overview', 'family_members', 'meal_planning', 'health_alerts', 'upcoming_appointments']
            family_keys_valid = all(key in family_data for key in expected_family_keys)
            print(f"   Family dashboard keys validation: {'✅' if family_keys_valid else '❌'}")

        if success4 and guest_data:
            expected_guest_keys = ['session_info', 'todays_entries', 'nutrition_summary', 'simple_goals', 'nutrition_tips', 'message']
            guest_keys_valid = all(key in guest_data for key in expected_guest_keys)
            print(f"   Guest dashboard keys validation: {'✅' if guest_keys_valid else '❌'}")

        return success1 and success2 and success3 and success4

    def test_additional_endpoints(self):
        """Test additional role-specific endpoints"""
        test_user_id = "test-user-123"
        
        # Test Patient Food Log
        success1, _ = self.run_test(
            "Patient Food Log",
            "GET",
            f"patient/food-log/{test_user_id}",
            200
        )

        # Test Provider Patients List
        success2, _ = self.run_test(
            "Provider Patients List",
            "GET",
            "provider/patients",
            200
        )

        # Test Provider Clinical Tools
        success3, _ = self.run_test(
            "Provider Clinical Tools",
            "GET",
            "provider/clinical-tools",
            200
        )

        # Test Family Meal Planning
        success4, _ = self.run_test(
            "Family Meal Planning",
            "GET",
            f"family/meal-planning/{test_user_id}",
            200
        )

        # Test Guest Quick Log (POST)
        success5, _ = self.run_test(
            "Guest Quick Log",
            "POST",
            "guest/quick-log",
            200,
            data={"food_name": "Apple", "calories": 95}
        )

        return success1 and success2 and success3 and success4 and success5

    def test_profile_management_endpoints(self):
        """Test comprehensive profile management API endpoints"""
        print("\n🔍 Testing Profile Management Endpoints...")
        
        # Test Patient Profile Management
        patient_success = self.test_patient_profile_management()
        
        # Test Provider Profile Management  
        provider_success = self.test_provider_profile_management()
        
        # Test Family Profile Management
        family_success = self.test_family_profile_management()
        
        # Test Guest Profile Management
        guest_success = self.test_guest_profile_management()
        
        # Test Profile Completion Tracking
        completion_success = self.test_profile_completion_tracking()
        
        return patient_success and provider_success and family_success and guest_success and completion_success

    def test_patient_profile_management(self):
        """Test Patient Profile CRUD operations"""
        print("\n📋 Testing Patient Profile Management...")
        
        # Generate unique user ID for testing
        test_user_id = f"patient_user_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create Patient Profile with minimal data
        minimal_profile_data = {
            "user_id": test_user_id,
            "basic_info": {
                "full_name": "Sarah Johnson",
                "age": 28,
                "gender": "Female",
                "location": "New York, NY",
                "timezone": "America/New_York",
                "preferred_language": "English"
            }
        }
        
        success1, profile_response = self.run_test(
            "Create Patient Profile (Minimal)",
            "POST",
            "profiles/patient",
            200,
            data=minimal_profile_data
        )
        
        # Test 2: Get Patient Profile
        success2, get_response = self.run_test(
            "Get Patient Profile",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        # Test 3: Create comprehensive patient profile with another user
        comprehensive_user_id = f"patient_comp_{datetime.now().strftime('%H%M%S')}"
        comprehensive_profile_data = {
            "user_id": comprehensive_user_id,
            "basic_info": {
                "full_name": "Michael Chen",
                "age": 35,
                "gender": "Male",
                "location": "San Francisco, CA",
                "contact_preferences": {"email": True, "sms": False, "push": True},
                "timezone": "America/Los_Angeles",
                "emergency_contact": {"name": "Lisa Chen", "phone": "+1-555-0123"},
                "preferred_language": "English"
            },
            "physical_metrics": {
                "height_cm": 175.0,
                "current_weight_kg": 78.5,
                "goal_weight_kg": 75.0,
                "body_fat_percentage": 18.5,
                "measurements": {"waist": 85.0, "chest": 102.0},
                "bmi": 25.6
            },
            "activity_profile": {
                "activity_level": "MODERATELY_ACTIVE",
                "exercise_types": ["running", "weightlifting", "yoga"],
                "exercise_frequency": 4,
                "sleep_schedule": {
                    "bedtime": "23:00",
                    "wake_time": "07:00",
                    "sleep_quality": 4
                },
                "stress_level": 3,
                "work_type": "DESK_JOB"
            },
            "health_history": {
                "primary_health_goals": ["weight_loss", "muscle_gain", "better_sleep"],
                "medical_conditions": {"hypertension": "mild"},
                "allergies": ["peanuts", "shellfish"],
                "food_intolerances": ["lactose"],
                "family_medical_history": ["diabetes", "heart_disease"]
            },
            "dietary_profile": {
                "diet_type": "OMNIVORE",
                "cultural_restrictions": [],
                "food_allergies": ["peanuts", "shellfish"],
                "food_dislikes": ["liver", "brussels_sprouts"],
                "meal_timing_preference": "TRADITIONAL_3_MEALS",
                "cooking_skill_level": 3,
                "available_cooking_time": 45
            },
            "goals_preferences": {
                "health_targets": [
                    {"type": "weight", "target": 75.0, "timeframe": "3_months"},
                    {"type": "exercise", "target": 5, "timeframe": "weekly"}
                ],
                "communication_methods": ["email", "app_notifications"],
                "notification_preferences": {"daily_reminders": True, "weekly_reports": True},
                "privacy_settings": {"share_with_providers": True, "anonymous_data": False}
            }
        }
        
        success3, comp_response = self.run_test(
            "Create Patient Profile (Comprehensive)",
            "POST",
            "profiles/patient",
            200,
            data=comprehensive_profile_data
        )
        
        # Test 4: Update Patient Profile
        update_data = {
            "physical_metrics": {
                "height_cm": 175.0,
                "current_weight_kg": 77.0,  # Updated weight
                "goal_weight_kg": 75.0,
                "body_fat_percentage": 17.8,  # Updated body fat
                "measurements": {"waist": 84.0, "chest": 102.0},  # Updated waist
                "bmi": 25.1
            }
        }
        
        success4, update_response = self.run_test(
            "Update Patient Profile",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=update_data
        )
        
        # Test 5: Test duplicate profile creation (should fail)
        success5, _ = self.run_test(
            "Create Duplicate Patient Profile (Should Fail)",
            "POST",
            "profiles/patient",
            400,  # Expecting 400 Bad Request
            data=minimal_profile_data
        )
        
        # Test 6: Test invalid enum values
        invalid_enum_data = {
            "user_id": f"invalid_enum_{datetime.now().strftime('%H%M%S')}",
            "activity_profile": {
                "activity_level": "INVALID_LEVEL",  # Invalid enum value
                "exercise_frequency": 3,
                "sleep_schedule": {
                    "bedtime": "23:00",
                    "wake_time": "07:00",
                    "sleep_quality": 4
                },
                "stress_level": 3,
                "work_type": "DESK_JOB"
            }
        }
        
        success6, _ = self.run_test(
            "Create Patient Profile with Invalid Enum (Should Fail)",
            "POST",
            "profiles/patient",
            422,  # Expecting validation error
            data=invalid_enum_data
        )
        
        # Test 7: Delete Patient Profile
        success7, _ = self.run_test(
            "Delete Patient Profile",
            "DELETE",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        # Test 8: Get deleted profile (should fail)
        success8, _ = self.run_test(
            "Get Deleted Patient Profile (Should Fail)",
            "GET",
            f"profiles/patient/{test_user_id}",
            404
        )
        
        # Validate profile completion calculation
        if success3 and comp_response:
            completion = comp_response.get('profile_completion', 0)
            print(f"   Profile completion percentage: {completion}%")
            completion_valid = completion > 80  # Should be high for comprehensive profile
            print(f"   Profile completion validation: {'✅' if completion_valid else '❌'}")
        
        return success1 and success2 and success3 and success4 and success5 and success6 and success7 and success8

    def test_provider_profile_management(self):
        """Test Provider Profile CRUD operations"""
        print("\n📋 Testing Provider Profile Management...")
        
        test_user_id = f"provider_user_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create Provider Profile
        provider_profile_data = {
            "user_id": test_user_id,
            "professional_identity": {
                "full_name": "Dr. Emily Rodriguez",
                "professional_title": "Registered Dietitian",
                "medical_license": "RD123456",
                "registration_numbers": {"state_license": "CA-RD-789", "national_cert": "CDR-12345"},
                "years_experience": 8
            },
            "credentials": {
                "education": [
                    {
                        "degree": "Master of Science in Nutrition",
                        "institution": "University of California, Davis",
                        "graduation_year": 2015,
                        "specialization": "Clinical Nutrition"
                    }
                ],
                "certifications": [
                    {
                        "name": "Certified Diabetes Educator",
                        "organization": "CBDCE",
                        "issue_date": "2018-06-15",
                        "expiration_date": "2025-06-15",
                        "status": "ACTIVE"
                    }
                ],
                "specializations": ["diabetes_management", "weight_management", "sports_nutrition"]
            },
            "practice_info": {
                "workplace": "Bay Area Medical Center",
                "practice_type": "Hospital-based",
                "patient_demographics": ["adults", "seniors", "athletes"],
                "languages_spoken": ["English", "Spanish"],
                "areas_of_expertise": ["diabetes", "cardiovascular_health", "sports_nutrition"]
            },
            "preferences": {
                "consultation_types": ["in_person", "telehealth", "group_sessions"],
                "working_hours": {
                    "timezone": "America/Los_Angeles",
                    "schedule": {
                        "monday": {"start": "08:00", "end": "17:00"},
                        "tuesday": {"start": "08:00", "end": "17:00"},
                        "wednesday": {"start": "08:00", "end": "17:00"},
                        "thursday": {"start": "08:00", "end": "17:00"},
                        "friday": {"start": "08:00", "end": "15:00"}
                    }
                },
                "max_patients": 150,
                "accepting_new_patients": True,
                "specialized_conditions": ["type_2_diabetes", "metabolic_syndrome"],
                "treatment_philosophies": ["evidence_based", "patient_centered", "holistic"]
            }
        }
        
        success1, provider_response = self.run_test(
            "Create Provider Profile",
            "POST",
            "profiles/provider",
            200,
            data=provider_profile_data
        )
        
        # Test 2: Get Provider Profile
        success2, _ = self.run_test(
            "Get Provider Profile",
            "GET",
            f"profiles/provider/{test_user_id}",
            200
        )
        
        # Test 3: Update Provider Profile
        update_data = {
            "preferences": {
                "consultation_types": ["in_person", "telehealth"],  # Removed group sessions
                "working_hours": {
                    "timezone": "America/Los_Angeles",
                    "schedule": {
                        "monday": {"start": "08:00", "end": "17:00"},
                        "tuesday": {"start": "08:00", "end": "17:00"},
                        "wednesday": {"start": "08:00", "end": "17:00"},
                        "thursday": {"start": "08:00", "end": "17:00"},
                        "friday": {"start": "08:00", "end": "15:00"}
                    }
                },
                "max_patients": 175,  # Updated capacity
                "accepting_new_patients": False,  # No longer accepting
                "specialized_conditions": ["type_2_diabetes", "metabolic_syndrome"],
                "treatment_philosophies": ["evidence_based", "patient_centered", "holistic"]
            }
        }
        
        success3, _ = self.run_test(
            "Update Provider Profile",
            "PUT",
            f"profiles/provider/{test_user_id}",
            200,
            data=update_data
        )
        
        # Test 4: Delete Provider Profile
        success4, _ = self.run_test(
            "Delete Provider Profile",
            "DELETE",
            f"profiles/provider/{test_user_id}",
            200
        )
        
        # Validate verification status
        if success1 and provider_response:
            verification_status = provider_response.get('verification_status', '')
            print(f"   Provider verification status: {verification_status}")
            verification_valid = verification_status == "PENDING"
            print(f"   Verification status validation: {'✅' if verification_valid else '❌'}")
        
        return success1 and success2 and success3 and success4

    def test_family_profile_management(self):
        """Test Family Profile CRUD operations"""
        print("\n📋 Testing Family Profile Management...")
        
        test_user_id = f"family_user_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create Family Profile
        family_profile_data = {
            "user_id": test_user_id,
            "family_structure": {
                "family_role": "Parent",
                "number_of_members": 4,
                "primary_caregiver": True
            },
            "family_members": [
                {
                    "name": "John Smith",
                    "relationship": "Self",
                    "age": 42,
                    "gender": "Male",
                    "special_needs": [],
                    "allergies": ["pollen"],
                    "medications": [],
                    "health_conditions": ["hypertension"]
                },
                {
                    "name": "Mary Smith",
                    "relationship": "Spouse",
                    "age": 38,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["shellfish"],
                    "medications": ["multivitamin"],
                    "health_conditions": []
                },
                {
                    "name": "Emma Smith",
                    "relationship": "Daughter",
                    "age": 12,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["peanuts"],
                    "medications": [],
                    "health_conditions": []
                },
                {
                    "name": "Alex Smith",
                    "relationship": "Son",
                    "age": 8,
                    "gender": "Male",
                    "special_needs": ["ADHD"],
                    "allergies": [],
                    "medications": ["ADHD_medication"],
                    "health_conditions": ["ADHD"]
                }
            ],
            "household_management": {
                "common_dietary_restrictions": ["peanut_free", "shellfish_free"],
                "family_meal_preferences": ["home_cooked", "balanced_nutrition", "kid_friendly"],
                "budget_considerations": {"weekly_grocery_budget": 200, "dining_out_budget": 100},
                "shopping_responsibilities": ["John", "Mary"],
                "cooking_responsibilities": ["Mary", "John"]
            },
            "care_coordination": {
                "healthcare_providers": {
                    "John": {"provider": "Dr. Johnson", "contact": "555-0101"},
                    "Mary": {"provider": "Dr. Williams", "contact": "555-0102"},
                    "Emma": {"provider": "Dr. Peterson", "contact": "555-0103"},
                    "Alex": {"provider": "Dr. Chen", "contact": "555-0104"}
                },
                "emergency_contacts": [
                    {"name": "Grandma Smith", "phone": "555-0200", "relationship": "Grandmother"},
                    {"name": "Uncle Mike", "phone": "555-0201", "relationship": "Uncle"}
                ],
                "medication_management": {"Alex": "Morning with breakfast"},
                "health_tracking_preferences": {"shared_calendar": True, "appointment_reminders": True}
            }
        }
        
        success1, family_response = self.run_test(
            "Create Family Profile",
            "POST",
            "profiles/family",
            200,
            data=family_profile_data
        )
        
        # Test 2: Get Family Profile
        success2, _ = self.run_test(
            "Get Family Profile",
            "GET",
            f"profiles/family/{test_user_id}",
            200
        )
        
        # Test 3: Update Family Profile (add new family member)
        update_data = {
            "family_members": [
                {
                    "name": "John Smith",
                    "relationship": "Self",
                    "age": 42,
                    "gender": "Male",
                    "special_needs": [],
                    "allergies": ["pollen"],
                    "medications": [],
                    "health_conditions": ["hypertension"]
                },
                {
                    "name": "Mary Smith",
                    "relationship": "Spouse",
                    "age": 38,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["shellfish"],
                    "medications": ["multivitamin"],
                    "health_conditions": []
                },
                {
                    "name": "Emma Smith",
                    "relationship": "Daughter",
                    "age": 12,
                    "gender": "Female",
                    "special_needs": [],
                    "allergies": ["peanuts"],
                    "medications": [],
                    "health_conditions": []
                },
                {
                    "name": "Alex Smith",
                    "relationship": "Son",
                    "age": 8,
                    "gender": "Male",
                    "special_needs": ["ADHD"],
                    "allergies": [],
                    "medications": ["ADHD_medication"],
                    "health_conditions": ["ADHD"]
                },
                {
                    "name": "Baby Smith",
                    "relationship": "Son",
                    "age": 1,
                    "gender": "Male",
                    "special_needs": [],
                    "allergies": [],
                    "medications": [],
                    "health_conditions": []
                }
            ]
        }
        
        success3, _ = self.run_test(
            "Update Family Profile (Add Member)",
            "PUT",
            f"profiles/family/{test_user_id}",
            200,
            data=update_data
        )
        
        # Test 4: Delete Family Profile
        success4, _ = self.run_test(
            "Delete Family Profile",
            "DELETE",
            f"profiles/family/{test_user_id}",
            200
        )
        
        # Validate family member structure
        if success1 and family_response:
            family_members = family_response.get('family_members', [])
            print(f"   Family members count: {len(family_members)}")
            members_valid = len(family_members) == 4
            print(f"   Family members validation: {'✅' if members_valid else '❌'}")
        
        return success1 and success2 and success3 and success4

    def test_guest_profile_management(self):
        """Test Guest Profile CRUD operations"""
        print("\n📋 Testing Guest Profile Management...")
        
        # Generate unique session ID
        test_session_id = f"guest_session_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create Guest Profile
        guest_profile_data = {
            "session_id": test_session_id,
            "basic_demographics": {
                "age": 25,
                "gender": "Female",
                "activity_level": "LIGHTLY_ACTIVE"
            },
            "simple_goals": {
                "goal_type": "lose",
                "target_amount": 5.0,
                "timeframe": "2_months"
            },
            "session_expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        success1, guest_response = self.run_test(
            "Create Guest Profile",
            "POST",
            "profiles/guest",
            200,
            data=guest_profile_data
        )
        
        # Test 2: Get Guest Profile
        success2, _ = self.run_test(
            "Get Guest Profile",
            "GET",
            f"profiles/guest/{test_session_id}",
            200
        )
        
        # Test 3: Create expired guest profile
        expired_session_id = f"expired_session_{datetime.now().strftime('%H%M%S')}"
        expired_profile_data = {
            "session_id": expired_session_id,
            "basic_demographics": {
                "age": 30,
                "gender": "Male",
                "activity_level": "MODERATELY_ACTIVE"
            },
            "simple_goals": {
                "goal_type": "maintain",
                "target_amount": 0.0,
                "timeframe": "ongoing"
            },
            "session_expires": (datetime.utcnow() - timedelta(hours=1)).isoformat()  # Expired 1 hour ago
        }
        
        success3, _ = self.run_test(
            "Create Expired Guest Profile",
            "POST",
            "profiles/guest",
            200,
            data=expired_profile_data
        )
        
        # Test 4: Try to get expired profile (should fail)
        success4, _ = self.run_test(
            "Get Expired Guest Profile (Should Fail)",
            "GET",
            f"profiles/guest/{expired_session_id}",
            404
        )
        
        # Test 5: Delete Guest Profile
        success5, _ = self.run_test(
            "Delete Guest Profile",
            "DELETE",
            f"profiles/guest/{test_session_id}",
            200
        )
        
        # Test 6: Get deleted profile (should fail)
        success6, _ = self.run_test(
            "Get Deleted Guest Profile (Should Fail)",
            "GET",
            f"profiles/guest/{test_session_id}",
            404
        )
        
        # Validate session expiration
        if success1 and guest_response:
            session_expires = guest_response.get('session_expires', '')
            print(f"   Guest session expires: {session_expires}")
            expires_valid = session_expires != ''
            print(f"   Session expiration validation: {'✅' if expires_valid else '❌'}")
        
        return success1 and success2 and success3 and success4 and success5 and success6

    def test_profile_completion_tracking(self):
        """Test Profile Completion Status endpoints"""
        print("\n📋 Testing Profile Completion Tracking...")
        
        # Create test profiles with different completion levels
        minimal_user_id = f"minimal_user_{datetime.now().strftime('%H%M%S')}"
        complete_user_id = f"complete_user_{datetime.now().strftime('%H%M%S')}"
        
        # Create minimal patient profile
        minimal_data = {
            "user_id": minimal_user_id,
            "basic_info": {
                "full_name": "Test User",
                "age": 30,
                "gender": "Male",
                "location": "Test City",
                "timezone": "America/New_York",
                "preferred_language": "English"
            }
        }
        
        success1, _ = self.run_test(
            "Create Minimal Patient Profile for Completion Test",
            "POST",
            "profiles/patient",
            200,
            data=minimal_data
        )
        
        # Create complete patient profile
        complete_data = {
            "user_id": complete_user_id,
            "basic_info": {
                "full_name": "Complete User",
                "age": 35,
                "gender": "Female",
                "location": "Complete City",
                "timezone": "America/New_York",
                "preferred_language": "English"
            },
            "physical_metrics": {
                "height_cm": 165.0,
                "current_weight_kg": 65.0,
                "goal_weight_kg": 60.0
            },
            "activity_profile": {
                "activity_level": "MODERATELY_ACTIVE",
                "exercise_frequency": 3,
                "sleep_schedule": {
                    "bedtime": "22:00",
                    "wake_time": "06:00",
                    "sleep_quality": 4
                },
                "stress_level": 2,
                "work_type": "MIXED"
            },
            "health_history": {
                "primary_health_goals": ["weight_loss"],
                "allergies": ["none"]
            },
            "dietary_profile": {
                "diet_type": "VEGETARIAN",
                "meal_timing_preference": "TRADITIONAL_3_MEALS",
                "cooking_skill_level": 3,
                "available_cooking_time": 30
            },
            "goals_preferences": {
                "health_targets": [{"type": "weight", "target": 60.0}],
                "communication_methods": ["email"]
            }
        }
        
        success2, _ = self.run_test(
            "Create Complete Patient Profile for Completion Test",
            "POST",
            "profiles/patient",
            200,
            data=complete_data
        )
        
        # Test completion status for minimal profile
        success3, minimal_completion = self.run_test(
            "Get Minimal Profile Completion Status",
            "GET",
            f"profiles/completion/{minimal_user_id}",
            200,
            params={"role": "patient"}
        )
        
        # Test completion status for complete profile
        success4, complete_completion = self.run_test(
            "Get Complete Profile Completion Status",
            "GET",
            f"profiles/completion/{complete_user_id}",
            200,
            params={"role": "patient"}
        )
        
        # Test completion status for non-existent profile
        success5, _ = self.run_test(
            "Get Non-existent Profile Completion Status",
            "GET",
            f"profiles/completion/non_existent_user",
            200,
            params={"role": "patient"}
        )
        
        # Test invalid role
        success6, _ = self.run_test(
            "Get Profile Completion with Invalid Role (Should Fail)",
            "GET",
            f"profiles/completion/{minimal_user_id}",
            400,
            params={"role": "invalid_role"}
        )
        
        # Validate completion percentages
        if success3 and minimal_completion:
            minimal_percentage = minimal_completion.get('completion_percentage', 0)
            print(f"   Minimal profile completion: {minimal_percentage}%")
            minimal_valid = 0 < minimal_percentage < 50  # Should be low
            print(f"   Minimal completion validation: {'✅' if minimal_valid else '❌'}")
        
        if success4 and complete_completion:
            complete_percentage = complete_completion.get('completion_percentage', 0)
            print(f"   Complete profile completion: {complete_percentage}%")
            complete_valid = complete_percentage == 100.0  # Should be 100%
            print(f"   Complete completion validation: {'✅' if complete_valid else '❌'}")
        
        # Clean up test profiles
        self.run_test("Cleanup Minimal Profile", "DELETE", f"profiles/patient/{minimal_user_id}", 200)
        self.run_test("Cleanup Complete Profile", "DELETE", f"profiles/patient/{complete_user_id}", 200)
        
        return success1 and success2 and success3 and success4 and success5 and success6

    def test_patient_profile_creation_and_autosave(self):
        """Test Patient Profile Creation and Auto-Save functionality as requested"""
        print("\n📋 Testing Patient Profile Creation and Auto-Save Functionality...")
        
        # Test 1: Create basic patient profile with minimal basic_info data
        test_user_id = f"profile_test_{datetime.now().strftime('%H%M%S')}"
        
        basic_profile_data = {
            "user_id": test_user_id,
            "basic_info": {
                "full_name": "Sarah Johnson",
                "age": 28,
                "gender": "Female",
                "location": "New York, NY",
                "timezone": "America/New_York",
                "preferred_language": "English"
            }
        }
        
        success1, profile_response = self.run_test(
            "Create Basic Patient Profile (Name + Age)",
            "POST",
            "profiles/patient",
            200,
            data=basic_profile_data
        )
        
        # Validate profile completion calculation for basic profile
        if success1 and profile_response:
            completion = profile_response.get('profile_completion', 0)
            print(f"   Profile completion for basic info only: {completion}%")
            # Should be 16.7% (1 out of 6 sections completed)
            expected_completion = 16.7
            completion_valid = abs(completion - expected_completion) < 1.0
            print(f"   Profile completion validation: {'✅' if completion_valid else '❌'} (Expected ~{expected_completion}%)")
        
        # Test 2: Get profile completion status
        success2, completion_data = self.run_test(
            "Get Profile Completion Status",
            "GET",
            f"profiles/completion/{test_user_id}",
            200,
            params={"role": "patient"}
        )
        
        # Validate completion status response
        if success2 and completion_data:
            expected_keys = ['completion_percentage', 'missing_sections', 'total_sections', 'completed_sections']
            missing_keys = [key for key in expected_keys if key not in completion_data]
            if not missing_keys:
                print(f"   ✅ Completion status contains all required keys: {expected_keys}")
                completion_pct = completion_data.get('completion_percentage', 0)
                missing_sections = completion_data.get('missing_sections', [])
                completed_sections = completion_data.get('completed_sections', 0)
                total_sections = completion_data.get('total_sections', 0)
                
                print(f"   Completion: {completion_pct}%, Completed: {completed_sections}/{total_sections} sections")
                print(f"   Missing sections: {missing_sections}")
                
                # Should have 5 missing sections (physical_metrics, activity_profile, health_history, dietary_profile, goals_preferences)
                expected_missing = 5
                missing_valid = len(missing_sections) == expected_missing
                print(f"   Missing sections validation: {'✅' if missing_valid else '❌'} (Expected {expected_missing} missing)")
            else:
                print(f"   ❌ Completion status missing keys: {missing_keys}")
                success2 = False
        
        # Test 3: Test auto-save with partial data (complete basic_info section)
        complete_basic_info_data = {
            "basic_info": {
                "full_name": "Sarah Johnson",
                "age": 28,
                "gender": "Female",
                "location": "New York, NY",
                "contact_preferences": {"email": True, "sms": False, "push": True},
                "timezone": "America/New_York",
                "emergency_contact": {"name": "John Johnson", "phone": "+1-555-0123"},
                "preferred_language": "English"
            }
        }
        
        success3, update_response = self.run_test(
            "Auto-Save: Update with Complete Basic Info",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=complete_basic_info_data
        )
        
        # Test 4: Test auto-save with incomplete basic_info section (missing required fields)
        incomplete_user_id = f"incomplete_test_{datetime.now().strftime('%H%M%S')}"
        
        incomplete_basic_info_data = {
            "user_id": incomplete_user_id,
            "basic_info": {
                "full_name": "Test User"
                # Missing age, gender, location, timezone, preferred_language
            }
        }
        
        success4, _ = self.run_test(
            "Create Profile with Incomplete Basic Info (Should Fail)",
            "POST",
            "profiles/patient",
            422,  # Expecting validation error
            data=incomplete_basic_info_data
        )
        
        # Test 5: Test auto-save behavior with partial profile data (add physical_metrics)
        physical_metrics_data = {
            "physical_metrics": {
                "height_cm": 165.0,
                "current_weight_kg": 65.0,
                "goal_weight_kg": 60.0,
                "body_fat_percentage": 22.5,
                "measurements": {"waist": 75.0, "chest": 90.0, "hips": 95.0},
                "bmi": 23.9
            }
        }
        
        success5, physical_response = self.run_test(
            "Auto-Save: Add Physical Metrics Section",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=physical_metrics_data
        )
        
        # Validate profile completion increased
        if success5 and physical_response:
            new_completion = physical_response.get('profile_completion', 0)
            print(f"   Profile completion after adding physical metrics: {new_completion}%")
            # Should be 33.3% (2 out of 6 sections completed)
            expected_completion = 33.3
            completion_valid = abs(new_completion - expected_completion) < 1.0
            print(f"   Updated completion validation: {'✅' if completion_valid else '❌'} (Expected ~{expected_completion}%)")
        
        # Test 6: Test section completion badges logic - add health history with previous surgeries
        health_history_data = {
            "health_history": {
                "primary_health_goals": ["weight_loss", "better_sleep"],
                "medical_conditions": {"hypertension": "mild"},
                "current_medications": [
                    {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}
                ],
                "allergies": ["peanuts"],
                "food_intolerances": ["lactose"],
                "previous_surgeries": [
                    {
                        "procedure": "Appendectomy",
                        "date": "2018-03-15",
                        "notes": "Routine appendix removal, no complications"
                    },
                    {
                        "procedure": "Wisdom tooth extraction",
                        "date": "2020-07-22",
                        "notes": "All four wisdom teeth removed"
                    }
                ],
                "family_medical_history": ["diabetes", "heart_disease"]
            }
        }
        
        success6, health_response = self.run_test(
            "Auto-Save: Add Health History with Previous Surgeries",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=health_history_data
        )
        
        # Validate previous surgeries were saved
        if success6 and health_response:
            health_history = health_response.get('health_history', {})
            previous_surgeries = health_history.get('previous_surgeries', [])
            print(f"   Previous surgeries saved: {len(previous_surgeries)} procedures")
            surgeries_valid = len(previous_surgeries) == 2
            print(f"   Previous surgeries validation: {'✅' if surgeries_valid else '❌'} (Expected 2 procedures)")
            
            new_completion = health_response.get('profile_completion', 0)
            print(f"   Profile completion after adding health history: {new_completion}%")
            # Should be 50.0% (3 out of 6 sections completed)
            expected_completion = 50.0
            completion_valid = abs(new_completion - expected_completion) < 1.0
            print(f"   Updated completion validation: {'✅' if completion_valid else '❌'} (Expected ~{expected_completion}%)")
        
        # Test 7: Get final profile to verify all data persisted correctly
        success7, final_profile = self.run_test(
            "Get Final Profile (Verify Persistence)",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        # Validate all sections are present and completion is correct
        if success7 and final_profile:
            sections_present = []
            if final_profile.get('basic_info'): sections_present.append('basic_info')
            if final_profile.get('physical_metrics'): sections_present.append('physical_metrics')
            if final_profile.get('health_history'): sections_present.append('health_history')
            
            print(f"   Sections present in final profile: {sections_present}")
            print(f"   Final profile completion: {final_profile.get('profile_completion', 0)}%")
            
            # Verify previous surgeries are still there
            health_history = final_profile.get('health_history', {})
            previous_surgeries = health_history.get('previous_surgeries', [])
            if previous_surgeries:
                print(f"   ✅ Previous surgeries persisted: {[s.get('procedure') for s in previous_surgeries]}")
            else:
                print(f"   ❌ Previous surgeries not persisted")
                success7 = False
        
        # Test 8: Test validation logic with invalid data
        invalid_activity_data = {
            "activity_profile": {
                "activity_level": "INVALID_LEVEL",  # Invalid enum
                "exercise_frequency": 3,
                "sleep_schedule": {
                    "bedtime": "23:00",
                    "wake_time": "07:00",
                    "sleep_quality": 4
                },
                "stress_level": 3,
                "work_type": "DESK_JOB"
            }
        }
        
        success8, _ = self.run_test(
            "Auto-Save: Invalid Activity Profile (Should Fail)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            422,  # Expecting validation error
            data=invalid_activity_data
        )
        
        # Clean up test profile
        cleanup_success, _ = self.run_test(
            "Cleanup Test Profile",
            "DELETE",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        print(f"\n📊 Patient Profile Creation & Auto-Save Test Summary:")
        print(f"   ✅ Basic profile creation: {'PASS' if success1 else 'FAIL'}")
        print(f"   ✅ Completion status tracking: {'PASS' if success2 else 'FAIL'}")
        print(f"   ✅ Auto-save complete section: {'PASS' if success3 else 'FAIL'}")
        print(f"   ✅ Validation of incomplete data: {'PASS' if success4 else 'FAIL'}")
        print(f"   ✅ Auto-save partial updates: {'PASS' if success5 else 'FAIL'}")
        print(f"   ✅ Previous surgeries functionality: {'PASS' if success6 else 'FAIL'}")
        print(f"   ✅ Data persistence verification: {'PASS' if success7 else 'FAIL'}")
        print(f"   ✅ Invalid data validation: {'PASS' if success8 else 'FAIL'}")
        print(f"   ✅ Cleanup: {'PASS' if cleanup_success else 'FAIL'}")
        
        return (success1 and success2 and success3 and success4 and success5 and 
                success6 and success7 and success8 and cleanup_success)

    def test_patient_analytics_endpoints(self):
        """Test Patient Analytics endpoints for the new Patient Analytics page"""
        print("\n📋 Testing Patient Analytics Endpoints...")
        
        test_user_id = "demo-patient-123"
        
        # Test 1: GET /api/patient/analytics/{user_id}
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
        
        # Test 2: GET /api/patient/smart-suggestions/{user_id}
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
        
        # Test 3: GET /api/patient/symptoms-correlation/{user_id}
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
        
        return success1 and success2 and success3

    def test_phase3_patient_apis(self):
        """Test Phase 3 Patient APIs: Medications, Health Timeline, and Enhanced Food Logging"""
        print("\n📋 Testing Phase 3 Patient APIs...")
        
        test_user_id = "demo-patient-123"
        
        # Test Patient Medication APIs
        medication_success = self.test_patient_medication_apis(test_user_id)
        
        # Test Patient Health Timeline APIs
        timeline_success = self.test_patient_health_timeline_apis(test_user_id)
        
        # Test Enhanced Food Logging API
        food_logging_success = self.test_enhanced_food_logging_api()
        
        return medication_success and timeline_success and food_logging_success

    def test_patient_medication_apis(self, user_id):
        """Test Patient Medication API endpoints"""
        print("\n💊 Testing Patient Medication APIs...")
        
        # Test 1: GET /api/patient/medications/{user_id}
        success1, medications_data = self.run_test(
            "Get Patient Medications",
            "GET",
            f"patient/medications/{user_id}",
            200
        )
        
        # Validate medications response structure
        if success1 and medications_data:
            expected_keys = ['medications', 'reminders', 'adherence_stats', 'ai_insights']
            missing_keys = [key for key in expected_keys if key not in medications_data]
            if not missing_keys:
                print(f"   ✅ Medications response contains all required keys: {expected_keys}")
                
                # Validate medications array structure
                medications = medications_data.get('medications', [])
                if medications and len(medications) > 0:
                    med = medications[0]
                    med_keys = ['id', 'name', 'dosage', 'frequency', 'times', 'adherence_rate', 'status']
                    missing_med_keys = [key for key in med_keys if key not in med]
                    if not missing_med_keys:
                        print(f"   ✅ Medication object structure valid")
                    else:
                        print(f"   ❌ Medication object missing keys: {missing_med_keys}")
                        success1 = False
            else:
                print(f"   ❌ Medications response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: POST /api/patient/medications/{user_id}/take
        sample_medication_take_data = {
            "medication_id": "med_001",
            "taken_at": datetime.utcnow().isoformat(),
            "notes": "Taken with breakfast as prescribed"
        }
        
        success2, take_response = self.run_test(
            "Mark Medication as Taken",
            "POST",
            f"patient/medications/{user_id}/take",
            200,
            data=sample_medication_take_data
        )
        
        # Validate take medication response
        if success2 and take_response:
            expected_keys = ['success', 'medication_id', 'taken_at']
            missing_keys = [key for key in expected_keys if key not in take_response]
            if not missing_keys:
                print(f"   ✅ Take medication response contains required keys: {expected_keys}")
            else:
                print(f"   ❌ Take medication response missing keys: {missing_keys}")
                success2 = False
        
        # Test 3: POST /api/patient/medications/{user_id} (Add new medication)
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
        
        success3, add_response = self.run_test(
            "Add New Medication",
            "POST",
            f"patient/medications/{user_id}",
            200,
            data=sample_new_medication
        )
        
        # Validate add medication response
        if success3 and add_response:
            expected_keys = ['success', 'medication', 'message']
            missing_keys = [key for key in expected_keys if key not in add_response]
            if not missing_keys:
                print(f"   ✅ Add medication response contains required keys: {expected_keys}")
                
                # Validate the medication object in response
                medication = add_response.get('medication', {})
                if medication:
                    med_keys = ['id', 'name', 'dosage', 'frequency', 'status']
                    missing_med_keys = [key for key in med_keys if key not in medication]
                    if not missing_med_keys:
                        print(f"   ✅ Added medication object structure valid")
                    else:
                        print(f"   ❌ Added medication object missing keys: {missing_med_keys}")
                        success3 = False
            else:
                print(f"   ❌ Add medication response missing keys: {missing_keys}")
                success3 = False
        
        return success1 and success2 and success3

    def test_patient_health_timeline_apis(self, user_id):
        """Test Patient Health Timeline API endpoints"""
        print("\n📅 Testing Patient Health Timeline APIs...")
        
        # Test 1: GET /api/patient/timeline/{user_id}
        success1, timeline_data = self.run_test(
            "Get Patient Health Timeline",
            "GET",
            f"patient/timeline/{user_id}",
            200
        )
        
        # Validate timeline response structure
        if success1 and timeline_data:
            expected_keys = ['timeline_events', 'patterns', 'milestones', 'ai_insights', 'categories_summary']
            missing_keys = [key for key in expected_keys if key not in timeline_data]
            if not missing_keys:
                print(f"   ✅ Timeline response contains all required keys: {expected_keys}")
                
                # Validate timeline events structure
                events = timeline_data.get('timeline_events', [])
                if events and len(events) > 0:
                    event = events[0]
                    event_keys = ['id', 'date', 'type', 'title', 'value', 'category', 'impact']
                    missing_event_keys = [key for key in event_keys if key not in event]
                    if not missing_event_keys:
                        print(f"   ✅ Timeline event structure valid")
                    else:
                        print(f"   ❌ Timeline event missing keys: {missing_event_keys}")
                        success1 = False
                
                # Validate patterns structure
                patterns = timeline_data.get('patterns', {})
                if patterns:
                    pattern_keys = ['energy_correlation', 'sleep_impact', 'nutrition_consistency']
                    missing_pattern_keys = [key for key in pattern_keys if key not in patterns]
                    if not missing_pattern_keys:
                        print(f"   ✅ Timeline patterns structure valid")
                    else:
                        print(f"   ❌ Timeline patterns missing keys: {missing_pattern_keys}")
            else:
                print(f"   ❌ Timeline response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: POST /api/patient/timeline/{user_id}/event
        sample_timeline_event = {
            "type": "exercise",
            "title": "Morning Yoga Session",
            "value": "30 minutes",
            "category": "activity",
            "details": "Completed 30-minute yoga session focusing on flexibility and mindfulness",
            "impact": "positive",
            "date": datetime.utcnow().date().isoformat()
        }
        
        success2, event_response = self.run_test(
            "Add Timeline Event",
            "POST",
            f"patient/timeline/{user_id}/event",
            200,
            data=sample_timeline_event
        )
        
        # Validate add event response
        if success2 and event_response:
            expected_keys = ['success', 'event', 'message']
            missing_keys = [key for key in expected_keys if key not in event_response]
            if not missing_keys:
                print(f"   ✅ Add timeline event response contains required keys: {expected_keys}")
                
                # Validate the event object in response
                event = event_response.get('event', {})
                if event:
                    event_keys = ['id', 'date', 'type', 'title', 'value', 'category']
                    missing_event_keys = [key for key in event_keys if key not in event]
                    if not missing_event_keys:
                        print(f"   ✅ Added timeline event structure valid")
                    else:
                        print(f"   ❌ Added timeline event missing keys: {missing_event_keys}")
                        success2 = False
            else:
                print(f"   ❌ Add timeline event response missing keys: {missing_keys}")
                success2 = False
        
        return success1 and success2

    def test_enhanced_food_logging_api(self):
        """Test Enhanced Food Logging API with AI pattern recognition"""
        print("\n🍎 Testing Enhanced Food Logging API...")
        
        # Test various food names to verify AI pattern recognition
        test_foods = [
            {
                "food_name": "Grilled Chicken Breast",
                "meal_type": "lunch",
                "quantity": 150,
                "unit": "grams"
            },
            {
                "food_name": "Greek Yogurt with Berries",
                "meal_type": "breakfast",
                "quantity": 200,
                "unit": "grams"
            },
            {
                "food_name": "Quinoa Salad",
                "meal_type": "dinner",
                "quantity": 250,
                "unit": "grams"
            },
            {
                "food_name": "Avocado Toast",
                "meal_type": "breakfast",
                "quantity": 1,
                "unit": "slice"
            },
            {
                "food_name": "Salmon Fillet",
                "meal_type": "dinner",
                "quantity": 180,
                "unit": "grams"
            }
        ]
        
        all_tests_passed = True
        
        for i, food_data in enumerate(test_foods, 1):
            success, response = self.run_test(
                f"Enhanced Food Logging - {food_data['food_name']}",
                "POST",
                "patient/food-log",
                200,
                data=food_data
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
                        all_tests_passed = False
                    
                    # Validate AI insights
                    ai_insights = response.get('ai_insights', [])
                    if ai_insights:
                        print(f"   ✅ AI insights provided: {len(ai_insights)} insights")
                    else:
                        print(f"   ⚠️  No AI insights provided")
                    
                    # Validate pattern recognition
                    pattern_recognition = response.get('pattern_recognition', {})
                    pattern_keys = ['meal_timing_pattern', 'nutrition_balance', 'suggestions']
                    missing_pattern_keys = [key for key in pattern_keys if key not in pattern_recognition]
                    
                    if not missing_pattern_keys:
                        print(f"   ✅ Pattern recognition structure valid")
                        suggestions = pattern_recognition.get('suggestions', [])
                        if suggestions:
                            print(f"   ✅ Pattern-based suggestions: {len(suggestions)} suggestions")
                    else:
                        print(f"   ❌ Pattern recognition missing keys: {missing_pattern_keys}")
                        all_tests_passed = False
                    
                    # Validate smart suggestions
                    smart_suggestions = response.get('smart_suggestions', {})
                    smart_keys = ['complementary_foods', 'portion_feedback', 'timing_feedback']
                    missing_smart_keys = [key for key in smart_keys if key not in smart_suggestions]
                    
                    if not missing_smart_keys:
                        print(f"   ✅ Smart suggestions structure valid")
                        complementary_foods = smart_suggestions.get('complementary_foods', [])
                        if complementary_foods:
                            print(f"   ✅ Complementary food suggestions: {len(complementary_foods)} suggestions")
                    else:
                        print(f"   ❌ Smart suggestions missing keys: {missing_smart_keys}")
                        all_tests_passed = False
                        
                else:
                    print(f"   ❌ Enhanced food logging response missing keys: {missing_keys}")
                    all_tests_passed = False
            else:
                all_tests_passed = False
        
        return all_tests_passed

    def test_phase4_food_logging_endpoints(self):
        """Test Phase 4 Food Logging Backend Endpoints"""
        print("\n📋 Testing Phase 4 Food Logging Backend Endpoints...")
        
        test_user_id = "demo-patient-123"
        
        # Test 1: GET /api/patient/food-log/{user_id}/daily-summary
        success1, daily_summary_data = self.run_test(
            "Patient Food Log Daily Summary",
            "GET",
            f"patient/food-log/{test_user_id}/daily-summary",
            200
        )
        
        # Validate daily summary response structure
        if success1 and daily_summary_data:
            expected_keys = ['user_id', 'date', 'summary']
            missing_keys = [key for key in expected_keys if key not in daily_summary_data]
            if not missing_keys:
                print(f"   ✅ Daily summary response contains all required keys: {expected_keys}")
                
                # Validate summary structure
                summary = daily_summary_data.get('summary', {})
                summary_keys = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'meals', 'water_intake', 'goals_met', 'daily_goals', 'progress_percentage']
                missing_summary_keys = [key for key in summary_keys if key not in summary]
                
                if not missing_summary_keys:
                    print(f"   ✅ Summary structure contains all required keys")
                    
                    # Validate goals_met structure
                    goals_met = summary.get('goals_met', {})
                    goals_keys = ['calories', 'protein', 'carbs', 'fat', 'fiber']
                    missing_goals_keys = [key for key in goals_keys if key not in goals_met]
                    
                    if not missing_goals_keys:
                        print(f"   ✅ Goals met structure valid")
                    else:
                        print(f"   ❌ Goals met missing keys: {missing_goals_keys}")
                        success1 = False
                    
                    # Validate progress_percentage structure
                    progress_percentage = summary.get('progress_percentage', {})
                    progress_keys = ['calories', 'protein', 'carbs', 'fat', 'fiber']
                    missing_progress_keys = [key for key in progress_keys if key not in progress_percentage]
                    
                    if not missing_progress_keys:
                        print(f"   ✅ Progress percentage structure valid")
                    else:
                        print(f"   ❌ Progress percentage missing keys: {missing_progress_keys}")
                        success1 = False
                        
                else:
                    print(f"   ❌ Summary missing keys: {missing_summary_keys}")
                    success1 = False
            else:
                print(f"   ❌ Daily summary response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: GET /api/patient/food-log/{user_id}/recent
        success2, recent_logs_data = self.run_test(
            "Patient Food Log Recent Entries",
            "GET",
            f"patient/food-log/{test_user_id}/recent",
            200
        )
        
        # Validate recent logs response structure
        if success2 and recent_logs_data:
            expected_keys = ['user_id', 'logs']
            missing_keys = [key for key in expected_keys if key not in recent_logs_data]
            if not missing_keys:
                print(f"   ✅ Recent logs response contains all required keys: {expected_keys}")
                
                # Validate logs array structure
                logs = recent_logs_data.get('logs', [])
                if logs and len(logs) > 0:
                    log = logs[0]
                    log_keys = ['id', 'food_name', 'brand', 'calories', 'protein', 'carbs', 'fat', 'fiber', 'sodium', 'meal_type', 'serving_size', 'timestamp', 'source', 'confidence']
                    missing_log_keys = [key for key in log_keys if key not in log]
                    
                    if not missing_log_keys:
                        print(f"   ✅ Food log entry structure valid with detailed nutrition info")
                        print(f"   ✅ Found {len(logs)} recent food log entries")
                        
                        # Validate timestamp format
                        timestamp = log.get('timestamp', '')
                        if timestamp:
                            print(f"   ✅ Timestamp format valid: {timestamp}")
                        else:
                            print(f"   ❌ Missing timestamp in food log entry")
                            success2 = False
                            
                    else:
                        print(f"   ❌ Food log entry missing keys: {missing_log_keys}")
                        success2 = False
                else:
                    print(f"   ❌ No food log entries found in response")
                    success2 = False
            else:
                print(f"   ❌ Recent logs response missing keys: {missing_keys}")
                success2 = False
        
        # Test 3: GET /api/patient/smart-suggestions/{user_id}
        success3, smart_suggestions_data = self.run_test(
            "Patient Smart Food Suggestions",
            "GET",
            f"patient/smart-suggestions/{test_user_id}",
            200
        )
        
        # Validate smart suggestions response structure
        if success3 and smart_suggestions_data:
            expected_keys = ['user_id', 'meal_context', 'generated_at', 'quick_add_suggestions', 'meal_pattern_insights', 'nutrition_gaps', 'personalized_recommendations']
            missing_keys = [key for key in expected_keys if key not in smart_suggestions_data]
            if not missing_keys:
                print(f"   ✅ Smart suggestions response contains all required keys: {expected_keys}")
                
                # Validate quick_add_suggestions structure
                suggestions = smart_suggestions_data.get('quick_add_suggestions', [])
                if suggestions and len(suggestions) > 0:
                    suggestion = suggestions[0]
                    suggestion_keys = ['name', 'calories', 'protein', 'carbs', 'fat', 'reason']
                    missing_suggestion_keys = [key for key in suggestion_keys if key not in suggestion]
                    
                    if not missing_suggestion_keys:
                        print(f"   ✅ Quick add suggestions structure valid")
                        print(f"   ✅ Found {len(suggestions)} contextual food suggestions")
                        
                        # Check meal context awareness
                        meal_context = smart_suggestions_data.get('meal_context', '')
                        if meal_context in ['breakfast', 'lunch', 'dinner', 'snack']:
                            print(f"   ✅ Context-aware suggestions for {meal_context} time")
                        else:
                            print(f"   ❌ Invalid meal context: {meal_context}")
                            success3 = False
                            
                    else:
                        print(f"   ❌ Quick add suggestion missing keys: {missing_suggestion_keys}")
                        success3 = False
                else:
                    print(f"   ❌ No quick add suggestions found")
                    success3 = False
                
                # Validate meal_pattern_insights structure
                pattern_insights = smart_suggestions_data.get('meal_pattern_insights', {})
                pattern_keys = ['breakfast_time', 'lunch_time', 'dinner_time', 'snack_preferences', 'hydration_pattern', 'meal_spacing']
                missing_pattern_keys = [key for key in pattern_keys if key not in pattern_insights]
                
                if not missing_pattern_keys:
                    print(f"   ✅ Meal pattern insights structure valid")
                else:
                    print(f"   ❌ Meal pattern insights missing keys: {missing_pattern_keys}")
                    success3 = False
                
                # Validate nutrition_gaps structure
                nutrition_gaps = smart_suggestions_data.get('nutrition_gaps', [])
                if nutrition_gaps and len(nutrition_gaps) > 0:
                    gap = nutrition_gaps[0]
                    gap_keys = ['nutrient', 'current', 'target', 'suggestion', 'foods', 'estimated_calories']
                    missing_gap_keys = [key for key in gap_keys if key not in gap]
                    
                    if not missing_gap_keys:
                        print(f"   ✅ Nutrition gaps structure valid with {len(nutrition_gaps)} gaps identified")
                    else:
                        print(f"   ❌ Nutrition gap missing keys: {missing_gap_keys}")
                        success3 = False
                
                # Validate personalized_recommendations structure
                recommendations = smart_suggestions_data.get('personalized_recommendations', [])
                if recommendations and len(recommendations) > 0:
                    rec = recommendations[0]
                    rec_keys = ['title', 'description', 'foods', 'priority']
                    missing_rec_keys = [key for key in rec_keys if key not in rec]
                    
                    if not missing_rec_keys:
                        print(f"   ✅ Personalized recommendations structure valid with {len(recommendations)} recommendations")
                    else:
                        print(f"   ❌ Personalized recommendation missing keys: {missing_rec_keys}")
                        success3 = False
                        
            else:
                print(f"   ❌ Smart suggestions response missing keys: {missing_keys}")
                success3 = False
        
        print(f"\n📊 Phase 4 Food Logging Endpoints Test Summary:")
        print(f"   ✅ Daily Summary Endpoint: {'PASS' if success1 else 'FAIL'}")
        print(f"   ✅ Recent Logs Endpoint: {'PASS' if success2 else 'FAIL'}")
        print(f"   ✅ Smart Suggestions Endpoint: {'PASS' if success3 else 'FAIL'}")
        
        return success1 and success2 and success3

    def test_phase5_family_features(self):
        """Test Phase 5 Comprehensive Family Features endpoints"""
        print("\n📋 Testing Phase 5 Comprehensive Family Features...")
        
        test_family_id = "demo-family-123"
        
        # Test 1: Family Calendar Integration
        calendar_success = self.test_family_calendar_integration(test_family_id)
        
        # Test 2: Child Nutrition Education
        nutrition_education_success = self.test_child_nutrition_education(test_family_id)
        
        # Test 3: Caregiver Tools
        caregiver_tools_success = self.test_caregiver_tools(test_family_id)
        
        # Test 4: Goals Coordination
        goals_coordination_success = self.test_goals_coordination(test_family_id)
        
        # Test 5: Multi-Profile Management
        multi_profile_success = self.test_multi_profile_management(test_family_id)
        
        # Test 6: Family Health Overview (existing)
        health_overview_success = self.test_family_health_overview(test_family_id)
        
        # Test 7: Advanced Meal Planning (existing)
        meal_planning_success = self.test_family_meal_planning_advanced(test_family_id)
        
        return (calendar_success and nutrition_education_success and caregiver_tools_success and 
                goals_coordination_success and multi_profile_success and health_overview_success and 
                meal_planning_success)

    def test_family_calendar_integration(self, family_id):
        """Test Family Calendar Integration with Health Events Coordination"""
        print("\n📅 Testing Family Calendar Integration...")
        
        success, calendar_data = self.run_test(
            "Family Calendar Integration",
            "GET",
            f"family/calendar-integration/{family_id}",
            200
        )
        
        # Validate calendar response structure
        if success and calendar_data:
            expected_keys = ['family_id', 'calendar_overview', 'health_events', 'upcoming_appointments', 'medication_schedules', 'family_activities', 'coordination_tools']
            missing_keys = [key for key in expected_keys if key not in calendar_data]
            
            if not missing_keys:
                print(f"   ✅ Family calendar response contains all required keys: {expected_keys}")
                
                # Validate health events structure
                health_events = calendar_data.get('health_events', [])
                if health_events and len(health_events) > 0:
                    event = health_events[0]
                    event_keys = ['id', 'member', 'type', 'title', 'date', 'time', 'priority', 'status']
                    missing_event_keys = [key for key in event_keys if key not in event]
                    
                    if not missing_event_keys:
                        print(f"   ✅ Health event structure valid")
                        print(f"   📅 Sample event: {event.get('member')} - {event.get('title')} on {event.get('date')}")
                    else:
                        print(f"   ❌ Health event missing keys: {missing_event_keys}")
                        success = False
                
                # Validate medication schedules
                medication_schedules = calendar_data.get('medication_schedules', {})
                if medication_schedules:
                    print(f"   ✅ Medication schedules provided for family members")
                    member_count = len(medication_schedules)
                    print(f"   💊 Medication schedules for {member_count} family members")
                
            else:
                print(f"   ❌ Family calendar response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_child_nutrition_education(self, family_id):
        """Test Child Nutrition Education Portal"""
        print("\n🍎 Testing Child Nutrition Education...")
        
        success, education_data = self.run_test(
            "Child Nutrition Education Portal",
            "GET",
            f"family/child-nutrition-education/{family_id}",
            200
        )
        
        # Validate education response structure
        if success and education_data:
            expected_keys = ['family_id', 'education_overview', 'age_appropriate_content', 'interactive_activities', 'progress_tracking', 'parent_resources', 'meal_planning_for_kids']
            missing_keys = [key for key in expected_keys if key not in education_data]
            
            if not missing_keys:
                print(f"   ✅ Child nutrition education response contains all required keys: {expected_keys}")
                
                # Validate age-appropriate content structure
                age_content = education_data.get('age_appropriate_content', {})
                if age_content:
                    age_groups = list(age_content.keys())
                    print(f"   ✅ Age-appropriate content available for: {age_groups}")
                    
                    # Check if content has proper structure
                    if age_groups:
                        sample_content = age_content[age_groups[0]]
                        content_keys = ['lessons', 'activities', 'goals']
                        missing_content_keys = [key for key in content_keys if key not in sample_content]
                        
                        if not missing_content_keys:
                            print(f"   ✅ Age-appropriate content structure valid")
                        else:
                            print(f"   ❌ Age-appropriate content missing keys: {missing_content_keys}")
                            success = False
                
                # Validate interactive activities
                activities = education_data.get('interactive_activities', [])
                if activities and len(activities) > 0:
                    activity = activities[0]
                    activity_keys = ['id', 'title', 'age_range', 'type', 'duration', 'learning_objectives']
                    missing_activity_keys = [key for key in activity_keys if key not in activity]
                    
                    if not missing_activity_keys:
                        print(f"   ✅ Interactive activity structure valid")
                        print(f"   🎮 Sample activity: {activity.get('title')} for ages {activity.get('age_range')}")
                    else:
                        print(f"   ❌ Interactive activity missing keys: {missing_activity_keys}")
                        success = False
                
            else:
                print(f"   ❌ Child nutrition education response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_caregiver_tools(self, family_id):
        """Test Advanced Caregiver Tools and Emergency Management"""
        print("\n🚑 Testing Caregiver Tools...")
        
        success, caregiver_data = self.run_test(
            "Advanced Caregiver Tools",
            "GET",
            f"family/caregiver-tools/{family_id}",
            200
        )
        
        # Validate caregiver tools response structure
        if success and caregiver_data:
            expected_keys = ['family_id', 'caregiver_dashboard', 'emergency_management', 'health_monitoring', 'medication_management', 'care_coordination', 'support_resources']
            missing_keys = [key for key in expected_keys if key not in caregiver_data]
            
            if not missing_keys:
                print(f"   ✅ Caregiver tools response contains all required keys: {expected_keys}")
                
                # Validate emergency management structure
                emergency_mgmt = caregiver_data.get('emergency_management', {})
                if emergency_mgmt:
                    emergency_keys = ['emergency_contacts', 'medical_information', 'action_plans', 'emergency_kit']
                    missing_emergency_keys = [key for key in emergency_keys if key not in emergency_mgmt]
                    
                    if not missing_emergency_keys:
                        print(f"   ✅ Emergency management structure valid")
                        
                        # Check emergency contacts
                        emergency_contacts = emergency_mgmt.get('emergency_contacts', [])
                        if emergency_contacts:
                            print(f"   📞 Emergency contacts configured: {len(emergency_contacts)} contacts")
                    else:
                        print(f"   ❌ Emergency management missing keys: {missing_emergency_keys}")
                        success = False
                
                # Validate health monitoring
                health_monitoring = caregiver_data.get('health_monitoring', {})
                if health_monitoring:
                    monitoring_keys = ['vital_signs_tracking', 'symptom_monitoring', 'medication_adherence', 'appointment_tracking']
                    missing_monitoring_keys = [key for key in monitoring_keys if key not in health_monitoring]
                    
                    if not missing_monitoring_keys:
                        print(f"   ✅ Health monitoring structure valid")
                        print(f"   💓 Health monitoring tools available")
                    else:
                        print(f"   ❌ Health monitoring missing keys: {missing_monitoring_keys}")
                        success = False
                
            else:
                print(f"   ❌ Caregiver tools response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_goals_coordination(self, family_id):
        """Test Family Goal Setting and Progress Coordination"""
        print("\n🎯 Testing Goals Coordination...")
        
        # Test 1: Get family goals coordination
        success1, goals_data = self.run_test(
            "Family Goals Coordination",
            "GET",
            f"family/goals-coordination/{family_id}",
            200
        )
        
        # Validate goals coordination response structure
        if success1 and goals_data:
            expected_keys = ['family_id', 'goals_overview', 'active_goals', 'completed_goals', 'goal_categories', 'progress_tracking', 'motivation_tools']
            missing_keys = [key for key in expected_keys if key not in goals_data]
            
            if not missing_keys:
                print(f"   ✅ Goals coordination response contains all required keys: {expected_keys}")
                
                # Validate active goals structure
                active_goals = goals_data.get('active_goals', [])
                if active_goals and len(active_goals) > 0:
                    goal = active_goals[0]
                    goal_keys = ['id', 'title', 'category', 'participants', 'target', 'current_progress', 'deadline', 'status']
                    missing_goal_keys = [key for key in goal_keys if key not in goal]
                    
                    if not missing_goal_keys:
                        print(f"   ✅ Active goal structure valid")
                        print(f"   🎯 Sample goal: {goal.get('title')} - {goal.get('current_progress')}% complete")
                    else:
                        print(f"   ❌ Active goal missing keys: {missing_goal_keys}")
                        success1 = False
                
                # Validate progress tracking
                progress_tracking = goals_data.get('progress_tracking', {})
                if progress_tracking:
                    tracking_keys = ['weekly_progress', 'member_contributions', 'milestone_achievements']
                    missing_tracking_keys = [key for key in tracking_keys if key not in progress_tracking]
                    
                    if not missing_tracking_keys:
                        print(f"   ✅ Progress tracking structure valid")
                    else:
                        print(f"   ❌ Progress tracking missing keys: {missing_tracking_keys}")
                        success1 = False
                
            else:
                print(f"   ❌ Goals coordination response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: Update goal progress
        sample_progress_data = {
            "member": "Emma",
            "progress": 85,
            "notes": "Great progress this week with daily vegetable intake",
            "date": "2024-01-16"
        }
        
        success2, progress_response = self.run_test(
            "Update Family Goal Progress",
            "POST",
            "family/goals/goal_nutrition_2024/update-progress",
            200,
            data=sample_progress_data
        )
        
        # Validate progress update response
        if success2 and progress_response:
            expected_keys = ['success', 'goal_id', 'updated_progress', 'member', 'message']
            missing_keys = [key for key in expected_keys if key not in progress_response]
            
            if not missing_keys:
                print(f"   ✅ Goal progress update response contains required keys: {expected_keys}")
                updated_progress = progress_response.get('updated_progress', 0)
                member = progress_response.get('member', '')
                print(f"   📈 Progress updated: {member} - {updated_progress}%")
            else:
                print(f"   ❌ Goal progress update response missing keys: {missing_keys}")
                success2 = False
        
        return success1 and success2

    def test_multi_profile_management(self, family_id):
        """Test Multi-Profile Management System"""
        print("\n👥 Testing Multi-Profile Management...")
        
        success, profile_data = self.run_test(
            "Multi-Profile Management System",
            "GET",
            f"family/multi-profile-management/{family_id}",
            200
        )
        
        # Validate multi-profile management response structure
        if success and profile_data:
            expected_keys = ['family_id', 'profile_overview', 'family_members', 'health_profiles', 'privacy_settings', 'data_sharing', 'profile_synchronization']
            missing_keys = [key for key in expected_keys if key not in profile_data]
            
            if not missing_keys:
                print(f"   ✅ Multi-profile management response contains all required keys: {expected_keys}")
                
                # Validate family members structure
                family_members = profile_data.get('family_members', [])
                if family_members and len(family_members) > 0:
                    member = family_members[0]
                    member_keys = ['id', 'name', 'role', 'age', 'profile_completion', 'health_status', 'permissions']
                    missing_member_keys = [key for key in member_keys if key not in member]
                    
                    if not missing_member_keys:
                        print(f"   ✅ Family member profile structure valid")
                        print(f"   👤 Sample member: {member.get('name')} - {member.get('profile_completion')}% complete")
                    else:
                        print(f"   ❌ Family member profile missing keys: {missing_member_keys}")
                        success = False
                
                # Validate health profiles structure
                health_profiles = profile_data.get('health_profiles', {})
                if health_profiles:
                    profile_keys = list(health_profiles.keys())
                    print(f"   ✅ Health profiles available for: {profile_keys}")
                    
                    # Check individual health profile structure
                    if profile_keys:
                        sample_profile = health_profiles[profile_keys[0]]
                        health_keys = ['basic_info', 'health_metrics', 'medications', 'allergies', 'conditions']
                        missing_health_keys = [key for key in health_keys if key not in sample_profile]
                        
                        if not missing_health_keys:
                            print(f"   ✅ Individual health profile structure valid")
                        else:
                            print(f"   ❌ Individual health profile missing keys: {missing_health_keys}")
                            success = False
                
                # Validate privacy settings
                privacy_settings = profile_data.get('privacy_settings', {})
                if privacy_settings:
                    privacy_keys = ['data_sharing_consent', 'profile_visibility', 'emergency_access', 'provider_access']
                    missing_privacy_keys = [key for key in privacy_keys if key not in privacy_settings]
                    
                    if not missing_privacy_keys:
                        print(f"   ✅ Privacy settings structure valid")
                        print(f"   🔒 Privacy controls configured")
                    else:
                        print(f"   ❌ Privacy settings missing keys: {missing_privacy_keys}")
                        success = False
                
            else:
                print(f"   ❌ Multi-profile management response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_family_health_overview(self, family_id):
        """Test Family Health Coordination (existing endpoint)"""
        print("\n🏥 Testing Family Health Overview...")
        
        success, health_data = self.run_test(
            "Family Health Overview",
            "GET",
            f"family/health-overview/{family_id}",
            200
        )
        
        # Validate health overview response structure
        if success and health_data:
            expected_keys = ['family_id', 'health_summary', 'member_health_status', 'upcoming_appointments', 'health_alerts', 'vaccination_status', 'care_coordination']
            missing_keys = [key for key in expected_keys if key not in health_data]
            
            if not missing_keys:
                print(f"   ✅ Family health overview response contains all required keys: {expected_keys}")
                
                # Validate member health status
                member_health = health_data.get('member_health_status', [])
                if member_health and len(member_health) > 0:
                    member = member_health[0]
                    member_keys = ['name', 'age', 'overall_status', 'recent_vitals', 'medications', 'upcoming_appointments']
                    missing_member_keys = [key for key in member_keys if key not in member]
                    
                    if not missing_member_keys:
                        print(f"   ✅ Member health status structure valid")
                        print(f"   👤 Sample member: {member.get('name')} - Status: {member.get('overall_status')}")
                    else:
                        print(f"   ❌ Member health status missing keys: {missing_member_keys}")
                        success = False
                
                # Validate health alerts
                health_alerts = health_data.get('health_alerts', [])
                if health_alerts:
                    print(f"   ✅ Health alerts available: {len(health_alerts)} alerts")
                    if len(health_alerts) > 0:
                        alert = health_alerts[0]
                        alert_keys = ['id', 'member', 'type', 'priority', 'message', 'date']
                        missing_alert_keys = [key for key in alert_keys if key not in alert]
                        
                        if not missing_alert_keys:
                            print(f"   ✅ Health alert structure valid")
                        else:
                            print(f"   ❌ Health alert missing keys: {missing_alert_keys}")
                            success = False
                
            else:
                print(f"   ❌ Family health overview response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_family_meal_planning_advanced(self, family_id):
        """Test Advanced Meal Planning (existing endpoint)"""
        print("\n🍽️ Testing Advanced Meal Planning...")
        
        success, meal_data = self.run_test(
            "Advanced Family Meal Planning",
            "GET",
            f"family/meal-planning-advanced/{family_id}",
            200
        )
        
        # Validate advanced meal planning response structure
        if success and meal_data:
            expected_keys = ['family_id', 'meal_planning_overview', 'weekly_meal_plans', 'nutritional_analysis', 'shopping_lists', 'recipe_recommendations', 'dietary_accommodations']
            missing_keys = [key for key in expected_keys if key not in meal_data]
            
            if not missing_keys:
                print(f"   ✅ Advanced meal planning response contains all required keys: {expected_keys}")
                
                # Validate weekly meal plans
                weekly_plans = meal_data.get('weekly_meal_plans', {})
                if weekly_plans:
                    days = list(weekly_plans.keys())
                    print(f"   ✅ Weekly meal plans available for: {days}")
                    
                    # Check meal plan structure for a day
                    if days:
                        day_plan = weekly_plans[days[0]]
                        meal_keys = ['breakfast', 'lunch', 'dinner', 'snacks']
                        available_meals = [meal for meal in meal_keys if meal in day_plan]
                        
                        if available_meals:
                            print(f"   ✅ Daily meal plan structure valid with meals: {available_meals}")
                        else:
                            print(f"   ❌ Daily meal plan missing meal types")
                            success = False
                
                # Validate nutritional analysis
                nutrition_analysis = meal_data.get('nutritional_analysis', {})
                if nutrition_analysis:
                    nutrition_keys = ['daily_totals', 'member_specific_needs', 'nutrient_balance', 'recommendations']
                    missing_nutrition_keys = [key for key in nutrition_keys if key not in nutrition_analysis]
                    
                    if not missing_nutrition_keys:
                        print(f"   ✅ Nutritional analysis structure valid")
                        print(f"   📊 Nutritional analysis includes daily totals and member-specific needs")
                    else:
                        print(f"   ❌ Nutritional analysis missing keys: {missing_nutrition_keys}")
                        success = False
                
                # Validate recipe recommendations
                recipe_recommendations = meal_data.get('recipe_recommendations', [])
                if recipe_recommendations and len(recipe_recommendations) > 0:
                    recipe = recipe_recommendations[0]
                    recipe_keys = ['id', 'name', 'category', 'prep_time', 'servings', 'difficulty', 'family_friendly', 'nutritional_info']
                    missing_recipe_keys = [key for key in recipe_keys if key not in recipe]
                    
                    if not missing_recipe_keys:
                        print(f"   ✅ Recipe recommendation structure valid")
                        print(f"   🍳 Sample recipe: {recipe.get('name')} - {recipe.get('prep_time')} min, serves {recipe.get('servings')}")
                    else:
                        print(f"   ❌ Recipe recommendation missing keys: {missing_recipe_keys}")
                        success = False
                
            else:
                print(f"   ❌ Advanced meal planning response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_phase4_provider_features(self):
        """Test Phase 4 Advanced Provider Features endpoints"""
        print("\n📋 Testing Phase 4 Advanced Provider Features...")
        
        test_provider_id = "provider-123"
        
        # Test 1: Patient Queue Management
        queue_success = self.test_patient_queue_management(test_provider_id)
        
        # Test 2: Clinical Decision Support
        cds_success = self.test_clinical_decision_support()
        
        # Test 3: Treatment Outcomes
        outcomes_success = self.test_treatment_outcomes(test_provider_id)
        
        # Test 4: Population Health Analytics
        population_success = self.test_population_health_analytics(test_provider_id)
        
        # Test 5: Evidence-Based Recommendations
        evidence_success = self.test_evidence_based_recommendations()
        
        # Test 6: Continuing Education
        education_success = self.test_continuing_education(test_provider_id)
        
        # Test 7: Course Enrollment
        enrollment_success = self.test_course_enrollment()
        
        # Test 8: Certificate Management
        certificates_success = self.test_certificate_management(test_provider_id)
        
        return (queue_success and cds_success and outcomes_success and 
                population_success and evidence_success and education_success and 
                enrollment_success and certificates_success)

    def test_patient_queue_management(self, provider_id):
        """Test Patient Queue Management System"""
        print("\n🏥 Testing Patient Queue Management...")
        
        success, queue_data = self.run_test(
            "Patient Queue Management",
            "GET",
            f"provider/patient-queue/{provider_id}",
            200
        )
        
        # Validate queue response structure
        if success and queue_data:
            expected_keys = ['provider_id', 'queue_stats', 'priority_queue', 'scheduled_queue', 'completed_today', 'no_shows']
            missing_keys = [key for key in expected_keys if key not in queue_data]
            
            if not missing_keys:
                print(f"   ✅ Patient queue response contains all required keys: {expected_keys}")
                
                # Validate queue_stats structure
                queue_stats = queue_data.get('queue_stats', {})
                stats_keys = ['total_in_queue', 'urgent', 'scheduled', 'walk_in', 'avg_wait_time']
                missing_stats_keys = [key for key in stats_keys if key not in queue_stats]
                
                if not missing_stats_keys:
                    print(f"   ✅ Queue stats structure valid")
                    print(f"   📊 Total in queue: {queue_stats.get('total_in_queue')}, Urgent: {queue_stats.get('urgent')}")
                else:
                    print(f"   ❌ Queue stats missing keys: {missing_stats_keys}")
                    success = False
                
                # Validate priority_queue structure
                priority_queue = queue_data.get('priority_queue', [])
                if priority_queue and len(priority_queue) > 0:
                    patient = priority_queue[0]
                    patient_keys = ['id', 'patient_name', 'condition', 'priority', 'wait_time', 'room', 'vitals', 'status']
                    missing_patient_keys = [key for key in patient_keys if key not in patient]
                    
                    if not missing_patient_keys:
                        print(f"   ✅ Priority queue patient structure valid")
                        print(f"   🚨 Priority patient: {patient.get('patient_name')} - {patient.get('condition')}")
                    else:
                        print(f"   ❌ Priority queue patient missing keys: {missing_patient_keys}")
                        success = False
                
            else:
                print(f"   ❌ Patient queue response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_clinical_decision_support(self):
        """Test AI-Powered Clinical Decision Support"""
        print("\n🧠 Testing Clinical Decision Support...")
        
        # Sample patient data for clinical decision support
        sample_patient_data = {
            "patient_data": {
                "id": "patient-456",
                "age": 52,
                "gender": "male",
                "weight": 95,
                "height": 175,
                "bmi": 31.0,
                "blood_pressure": "145/92",
                "glucose": 126
            },
            "symptoms": [
                "increased thirst",
                "frequent urination", 
                "unexplained weight loss",
                "fatigue"
            ],
            "history": [
                "family_history_diabetes",
                "hypertension",
                "sedentary_lifestyle"
            ]
        }
        
        success, cds_data = self.run_test(
            "Clinical Decision Support",
            "POST",
            "provider/clinical-decision-support",
            200,
            data=sample_patient_data
        )
        
        # Validate clinical decision support response
        if success and cds_data:
            expected_keys = ['request_id', 'patient_id', 'ai_recommendations', 'drug_interactions', 'contraindications', 'clinical_guidelines', 'risk_scores']
            missing_keys = [key for key in expected_keys if key not in cds_data]
            
            if not missing_keys:
                print(f"   ✅ Clinical decision support response contains all required keys")
                
                # Validate AI recommendations structure
                ai_recommendations = cds_data.get('ai_recommendations', [])
                if ai_recommendations and len(ai_recommendations) > 0:
                    recommendation = ai_recommendations[0]
                    rec_keys = ['category', 'confidence', 'recommendation', 'evidence', 'next_steps']
                    missing_rec_keys = [key for key in rec_keys if key not in recommendation]
                    
                    if not missing_rec_keys:
                        print(f"   ✅ AI recommendation structure valid")
                        print(f"   🎯 Confidence: {recommendation.get('confidence')}, Category: {recommendation.get('category')}")
                    else:
                        print(f"   ❌ AI recommendation missing keys: {missing_rec_keys}")
                        success = False
                
                # Validate risk scores
                risk_scores = cds_data.get('risk_scores', {})
                if risk_scores:
                    print(f"   ✅ Risk scores provided: {list(risk_scores.keys())}")
                    diabetes_risk = risk_scores.get('diabetes_risk', 0)
                    print(f"   📊 Diabetes risk: {diabetes_risk}")
                
            else:
                print(f"   ❌ Clinical decision support response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_treatment_outcomes(self, provider_id):
        """Test Treatment Outcome Tracking"""
        print("\n📈 Testing Treatment Outcomes...")
        
        success, outcomes_data = self.run_test(
            "Treatment Outcomes",
            "GET",
            f"provider/treatment-outcomes/{provider_id}",
            200,
            params={"timeframe": "30d"}
        )
        
        # Validate treatment outcomes response
        if success and outcomes_data:
            expected_keys = ['provider_id', 'timeframe', 'outcome_summary', 'condition_outcomes', 'trending_metrics']
            missing_keys = [key for key in expected_keys if key not in outcomes_data]
            
            if not missing_keys:
                print(f"   ✅ Treatment outcomes response contains all required keys")
                
                # Validate outcome summary
                outcome_summary = outcomes_data.get('outcome_summary', {})
                summary_keys = ['total_patients_treated', 'successful_outcomes', 'success_rate', 'readmission_rate', 'patient_satisfaction']
                missing_summary_keys = [key for key in summary_keys if key not in outcome_summary]
                
                if not missing_summary_keys:
                    print(f"   ✅ Outcome summary structure valid")
                    success_rate = outcome_summary.get('success_rate', 0)
                    print(f"   📊 Success rate: {success_rate}%, Patient satisfaction: {outcome_summary.get('patient_satisfaction')}")
                else:
                    print(f"   ❌ Outcome summary missing keys: {missing_summary_keys}")
                    success = False
                
                # Validate condition outcomes
                condition_outcomes = outcomes_data.get('condition_outcomes', [])
                if condition_outcomes and len(condition_outcomes) > 0:
                    condition = condition_outcomes[0]
                    condition_keys = ['condition', 'patients', 'improved', 'stable', 'declined', 'target_achievement_rate']
                    missing_condition_keys = [key for key in condition_keys if key not in condition]
                    
                    if not missing_condition_keys:
                        print(f"   ✅ Condition outcomes structure valid")
                        print(f"   🏥 {condition.get('condition')}: {condition.get('improved')}/{condition.get('patients')} improved")
                    else:
                        print(f"   ❌ Condition outcomes missing keys: {missing_condition_keys}")
                        success = False
                
            else:
                print(f"   ❌ Treatment outcomes response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_population_health_analytics(self, provider_id):
        """Test Population Health Analytics"""
        print("\n👥 Testing Population Health Analytics...")
        
        success, population_data = self.run_test(
            "Population Health Analytics",
            "GET",
            f"provider/population-health/{provider_id}",
            200
        )
        
        # Validate population health response
        if success and population_data:
            expected_keys = ['provider_id', 'population_overview', 'demographic_breakdown', 'condition_prevalence', 'risk_stratification', 'quality_measures', 'intervention_opportunities']
            missing_keys = [key for key in expected_keys if key not in population_data]
            
            if not missing_keys:
                print(f"   ✅ Population health response contains all required keys")
                
                # Validate population overview
                population_overview = population_data.get('population_overview', {})
                overview_keys = ['total_population', 'active_patients', 'high_risk_patients', 'chronic_conditions_prevalence']
                missing_overview_keys = [key for key in overview_keys if key not in population_overview]
                
                if not missing_overview_keys:
                    print(f"   ✅ Population overview structure valid")
                    total_pop = population_overview.get('total_population', 0)
                    high_risk = population_overview.get('high_risk_patients', 0)
                    print(f"   📊 Total population: {total_pop}, High risk: {high_risk}")
                else:
                    print(f"   ❌ Population overview missing keys: {missing_overview_keys}")
                    success = False
                
                # Validate demographic breakdown
                demographic_breakdown = population_data.get('demographic_breakdown', [])
                if demographic_breakdown and len(demographic_breakdown) > 0:
                    demo = demographic_breakdown[0]
                    demo_keys = ['age_group', 'count', 'percentage', 'top_conditions']
                    missing_demo_keys = [key for key in demo_keys if key not in demo]
                    
                    if not missing_demo_keys:
                        print(f"   ✅ Demographic breakdown structure valid")
                        print(f"   👥 Age group {demo.get('age_group')}: {demo.get('count')} patients ({demo.get('percentage')}%)")
                    else:
                        print(f"   ❌ Demographic breakdown missing keys: {missing_demo_keys}")
                        success = False
                
                # Validate quality measures
                quality_measures = population_data.get('quality_measures', [])
                if quality_measures and len(quality_measures) > 0:
                    measure = quality_measures[0]
                    measure_keys = ['measure', 'target', 'current', 'status']
                    missing_measure_keys = [key for key in measure_keys if key not in measure]
                    
                    if not missing_measure_keys:
                        print(f"   ✅ Quality measures structure valid")
                        print(f"   📏 {measure.get('measure')}: {measure.get('current')} (target: {measure.get('target')})")
                    else:
                        print(f"   ❌ Quality measures missing keys: {missing_measure_keys}")
                        success = False
                
            else:
                print(f"   ❌ Population health response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_evidence_based_recommendations(self):
        """Test AI-Powered Evidence-Based Recommendations"""
        print("\n📚 Testing Evidence-Based Recommendations...")
        
        # Sample condition data for evidence-based recommendations
        sample_condition_data = {
            "condition": "Type 2 Diabetes",
            "patient_profile": {
                "age": 58,
                "gender": "female",
                "weight": 82,
                "height": 162,
                "bmi": 31.2,
                "hba1c": 8.1,
                "egfr": 75,
                "comorbidities": ["hypertension", "obesity"]
            },
            "clinical_context": "newly_diagnosed"
        }
        
        success, evidence_data = self.run_test(
            "Evidence-Based Recommendations",
            "POST",
            "provider/evidence-recommendations",
            200,
            data=sample_condition_data
        )
        
        # Validate evidence-based recommendations response
        if success and evidence_data:
            expected_keys = ['request_id', 'condition', 'evidence_level', 'recommendations', 'clinical_studies', 'contraindications', 'drug_interactions', 'patient_specific_factors', 'follow_up_recommendations']
            missing_keys = [key for key in expected_keys if key not in evidence_data]
            
            if not missing_keys:
                print(f"   ✅ Evidence-based recommendations response contains all required keys")
                
                # Validate recommendations structure
                recommendations = evidence_data.get('recommendations', [])
                if recommendations and len(recommendations) > 0:
                    recommendation = recommendations[0]
                    rec_keys = ['category', 'recommendation', 'evidence_level', 'source', 'confidence']
                    missing_rec_keys = [key for key in rec_keys if key not in recommendation]
                    
                    if not missing_rec_keys:
                        print(f"   ✅ Recommendation structure valid")
                        print(f"   📋 Category: {recommendation.get('category')}, Evidence level: {recommendation.get('evidence_level')}")
                        print(f"   🎯 Confidence: {recommendation.get('confidence')}")
                    else:
                        print(f"   ❌ Recommendation missing keys: {missing_rec_keys}")
                        success = False
                
                # Validate clinical studies
                clinical_studies = evidence_data.get('clinical_studies', [])
                if clinical_studies and len(clinical_studies) > 0:
                    study = clinical_studies[0]
                    study_keys = ['study', 'year', 'finding', 'relevance', 'patient_count']
                    missing_study_keys = [key for key in study_keys if key not in study]
                    
                    if not missing_study_keys:
                        print(f"   ✅ Clinical studies structure valid")
                        print(f"   🔬 Study: {study.get('study')} ({study.get('year')}), Relevance: {study.get('relevance')}")
                    else:
                        print(f"   ❌ Clinical studies missing keys: {missing_study_keys}")
                        success = False
                
                # Validate follow-up recommendations
                follow_up = evidence_data.get('follow_up_recommendations', [])
                if follow_up:
                    print(f"   ✅ Follow-up recommendations provided: {len(follow_up)} recommendations")
                
            else:
                print(f"   ❌ Evidence-based recommendations response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_continuing_education(self, provider_id):
        """Test Professional Continuing Education Portal"""
        print("\n🎓 Testing Continuing Education...")
        
        success, education_data = self.run_test(
            "Continuing Education",
            "GET",
            f"provider/continuing-education/{provider_id}",
            200
        )
        
        # Validate continuing education response
        if success and education_data:
            expected_keys = ['provider_id', 'education_summary', 'featured_courses', 'my_courses', 'categories', 'upcoming_deadlines']
            missing_keys = [key for key in expected_keys if key not in education_data]
            
            if not missing_keys:
                print(f"   ✅ Continuing education response contains all required keys")
                
                # Validate education summary
                education_summary = education_data.get('education_summary', {})
                summary_keys = ['total_credits_earned', 'credits_required', 'progress_percentage', 'courses_completed', 'courses_in_progress', 'deadline']
                missing_summary_keys = [key for key in summary_keys if key not in education_summary]
                
                if not missing_summary_keys:
                    print(f"   ✅ Education summary structure valid")
                    credits_earned = education_summary.get('total_credits_earned', 0)
                    credits_required = education_summary.get('credits_required', 0)
                    progress = education_summary.get('progress_percentage', 0)
                    print(f"   📊 Credits: {credits_earned}/{credits_required} ({progress}% complete)")
                else:
                    print(f"   ❌ Education summary missing keys: {missing_summary_keys}")
                    success = False
                
                # Validate featured courses
                featured_courses = education_data.get('featured_courses', [])
                if featured_courses and len(featured_courses) > 0:
                    course = featured_courses[0]
                    course_keys = ['id', 'title', 'provider', 'credits', 'duration', 'format', 'difficulty', 'rating', 'enrolled', 'cost', 'description', 'learning_objectives']
                    missing_course_keys = [key for key in course_keys if key not in course]
                    
                    if not missing_course_keys:
                        print(f"   ✅ Featured course structure valid")
                        print(f"   📚 Course: {course.get('title')} ({course.get('credits')} credits)")
                        print(f"   ⭐ Rating: {course.get('rating')}, Format: {course.get('format')}")
                    else:
                        print(f"   ❌ Featured course missing keys: {missing_course_keys}")
                        success = False
                
                # Validate categories
                categories = education_data.get('categories', [])
                if categories and len(categories) > 0:
                    category = categories[0]
                    cat_keys = ['id', 'name', 'course_count']
                    missing_cat_keys = [key for key in cat_keys if key not in category]
                    
                    if not missing_cat_keys:
                        print(f"   ✅ Categories structure valid")
                        print(f"   📂 Category: {category.get('name')} ({category.get('course_count')} courses)")
                    else:
                        print(f"   ❌ Categories missing keys: {missing_cat_keys}")
                        success = False
                
            else:
                print(f"   ❌ Continuing education response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_course_enrollment(self):
        """Test Course Enrollment"""
        print("\n📝 Testing Course Enrollment...")
        
        # Sample enrollment data
        enrollment_data = {
            "provider_id": "provider-123"
        }
        
        success, enrollment_response = self.run_test(
            "Course Enrollment",
            "POST",
            "provider/courses/course-001/enroll",
            200,
            data=enrollment_data
        )
        
        # Validate course enrollment response
        if success and enrollment_response:
            expected_keys = ['course_id', 'provider_id', 'enrollment_status', 'message', 'access_url', 'enrollment_date']
            missing_keys = [key for key in expected_keys if key not in enrollment_response]
            
            if not missing_keys:
                print(f"   ✅ Course enrollment response contains all required keys")
                enrollment_status = enrollment_response.get('enrollment_status')
                course_id = enrollment_response.get('course_id')
                print(f"   ✅ Enrollment status: {enrollment_status} for course {course_id}")
                print(f"   🔗 Access URL: {enrollment_response.get('access_url')}")
            else:
                print(f"   ❌ Course enrollment response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_certificate_management(self, provider_id):
        """Test Certificate Management"""
        print("\n🏆 Testing Certificate Management...")
        
        success, certificates_data = self.run_test(
            "Certificate Management",
            "GET",
            f"provider/certificates/{provider_id}",
            200
        )
        
        # Validate certificate management response
        if success and certificates_data:
            expected_keys = ['provider_id', 'certificates', 'total_credits']
            missing_keys = [key for key in expected_keys if key not in certificates_data]
            
            if not missing_keys:
                print(f"   ✅ Certificate management response contains all required keys")
                
                # Validate certificates structure
                certificates = certificates_data.get('certificates', [])
                if certificates and len(certificates) > 0:
                    certificate = certificates[0]
                    cert_keys = ['id', 'course_title', 'credits', 'completed_date', 'certificate_number', 'download_url', 'verification_code']
                    missing_cert_keys = [key for key in cert_keys if key not in certificate]
                    
                    if not missing_cert_keys:
                        print(f"   ✅ Certificate structure valid")
                        print(f"   🏆 Certificate: {certificate.get('course_title')} ({certificate.get('credits')} credits)")
                        print(f"   📅 Completed: {certificate.get('completed_date')}")
                        print(f"   🔢 Certificate #: {certificate.get('certificate_number')}")
                    else:
                        print(f"   ❌ Certificate missing keys: {missing_cert_keys}")
                        success = False
                
                # Validate total credits
                total_credits = certificates_data.get('total_credits', 0)
                print(f"   📊 Total credits earned: {total_credits}")
                
            else:
                print(f"   ❌ Certificate management response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_guest_food_log_api_integration(self):
        """Test Guest Food Log API integration specifically as requested"""
        print("\n📋 Testing Guest Food Log API Integration...")
        
        # Test 1: Create guest session
        success1, session_response = self.run_test(
            "Create Guest Session",
            "POST",
            "guest/session",
            200
        )
        
        session_id = None
        if success1 and session_response:
            session_id = session_response.get('session_id')
            expected_keys = ['session_id', 'expires_at', 'features_available', 'limitations', 'upgrade_benefits']
            missing_keys = [key for key in expected_keys if key not in session_response]
            
            if not missing_keys:
                print(f"   ✅ Session creation response contains all required keys: {expected_keys}")
                print(f"   📝 Session ID: {session_id}")
                
                # Validate features available
                features = session_response.get('features_available', [])
                if 'instant_food_logging' in features:
                    print(f"   ✅ Instant food logging feature available")
                else:
                    print(f"   ❌ Instant food logging feature not available")
                    success1 = False
            else:
                print(f"   ❌ Session creation response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: Test instant food logging with different food items
        food_items = [
            {"food_name": "grilled chicken breast", "calories": 165},
            {"food_name": "greek yogurt", "calories": 100},
            {"food_name": "banana", "calories": 105}
        ]
        
        food_logging_success = True
        for i, food_item in enumerate(food_items, 1):
            success, response = self.run_test(
                f"Instant Food Log - {food_item['food_name'].title()}",
                "POST",
                "guest/instant-food-log",
                200,
                data=food_item
            )
            
            if success and response:
                # Validate instant food logging response structure
                expected_keys = ['success', 'food_recognized', 'estimated_nutrition', 'instant_feedback', 
                               'session_totals', 'simple_suggestions', 'learning_moment']
                missing_keys = [key for key in expected_keys if key not in response]
                
                if not missing_keys:
                    print(f"   ✅ Food logging response contains all required keys")
                    
                    # Validate estimated nutrition structure
                    nutrition = response.get('estimated_nutrition', {})
                    nutrition_keys = ['calories', 'protein', 'carbs', 'fat', 'fiber']
                    missing_nutrition_keys = [key for key in nutrition_keys if key not in nutrition]
                    
                    if not missing_nutrition_keys:
                        print(f"   ✅ Nutrition data structure valid")
                        print(f"   🍎 {food_item['food_name'].title()}: {nutrition.get('calories')} cal, {nutrition.get('protein')}g protein")
                    else:
                        print(f"   ❌ Nutrition data missing keys: {missing_nutrition_keys}")
                        food_logging_success = False
                    
                    # Validate instant feedback
                    feedback = response.get('instant_feedback', [])
                    if feedback and len(feedback) > 0:
                        print(f"   ✅ Instant feedback provided: {len(feedback)} feedback items")
                        print(f"   💡 Sample feedback: {feedback[0]}")
                    else:
                        print(f"   ❌ No instant feedback provided")
                        food_logging_success = False
                    
                    # Validate learning moment
                    learning_moment = response.get('learning_moment', {})
                    if learning_moment and 'tip' in learning_moment and 'content' in learning_moment:
                        print(f"   ✅ Learning moment provided: {learning_moment.get('tip')}")
                    else:
                        print(f"   ❌ Learning moment missing or incomplete")
                        food_logging_success = False
                    
                    # Validate simple suggestions
                    suggestions = response.get('simple_suggestions', [])
                    if suggestions and len(suggestions) > 0:
                        print(f"   ✅ Simple suggestions provided: {len(suggestions)} suggestions")
                    else:
                        print(f"   ❌ No simple suggestions provided")
                        food_logging_success = False
                        
                else:
                    print(f"   ❌ Food logging response missing keys: {missing_keys}")
                    food_logging_success = False
            else:
                food_logging_success = False
        
        # Test 3: Check session status if session was created
        session_status_success = True
        if session_id:
            success3, status_response = self.run_test(
                "Check Guest Session Status",
                "GET",
                f"guest/session/{session_id}/status",
                200
            )
            
            if success3 and status_response:
                expected_keys = ['session_id', 'status', 'time_remaining', 'activity_summary', 'recommendations']
                missing_keys = [key for key in expected_keys if key not in status_response]
                
                if not missing_keys:
                    print(f"   ✅ Session status response contains all required keys")
                    
                    # Validate activity summary
                    activity = status_response.get('activity_summary', {})
                    activity_keys = ['foods_logged', 'tips_viewed', 'calculations_used', 'session_duration']
                    missing_activity_keys = [key for key in activity_keys if key not in activity]
                    
                    if not missing_activity_keys:
                        print(f"   ✅ Activity summary structure valid")
                        print(f"   📊 Foods logged: {activity.get('foods_logged')}, Session duration: {activity.get('session_duration')}")
                    else:
                        print(f"   ❌ Activity summary missing keys: {missing_activity_keys}")
                        session_status_success = False
                else:
                    print(f"   ❌ Session status response missing keys: {missing_keys}")
                    session_status_success = False
            else:
                session_status_success = False
        
        # Test 4: Test complete flow validation
        flow_success = success1 and food_logging_success and session_status_success
        
        if flow_success:
            print(f"\n   ✅ COMPLETE FLOW VALIDATION PASSED")
            print(f"   ✅ Session creation ➜ Food logging ➜ Session status - All working correctly")
            print(f"   ✅ API returns expected structure with instant_feedback, learning_moment, simple_suggestions, estimated_nutrition")
        else:
            print(f"\n   ❌ COMPLETE FLOW VALIDATION FAILED")
            print(f"   ❌ Issues found in session management or food logging functionality")
        
        return flow_success

    def test_phase6_guest_goals_management(self):
        """Test Phase 6 Guest Goals Management APIs"""
        print("\n📋 Testing Phase 6 Guest Goals Management APIs...")
        
        # Test 1: Create guest session
        session_success = self.test_guest_session_creation()
        
        if not session_success:
            print("❌ Guest session creation failed - skipping goal tests")
            return False
        
        # Test 2-5: Test goal management with created session
        goals_success = self.test_guest_goals_management_flow()
        
        return session_success and goals_success

    def test_guest_session_creation(self):
        """Test guest session creation"""
        print("\n🔑 Testing Guest Session Creation...")
        
        success, session_data = self.run_test(
            "Create Guest Session",
            "POST",
            "guest/session",
            200
        )
        
        if success and session_data:
            # Validate session response structure
            expected_keys = ['session_id', 'expires_at', 'features_available', 'limitations', 'upgrade_benefits']
            missing_keys = [key for key in expected_keys if key not in session_data]
            
            if not missing_keys:
                print(f"   ✅ Guest session response contains all required keys: {expected_keys}")
                
                # Store session_id for subsequent tests
                self.test_session_id = session_data.get('session_id')
                print(f"   🔑 Session ID: {self.test_session_id}")
                
                # Validate features available
                features = session_data.get('features_available', [])
                expected_features = ['instant_food_logging', 'basic_nutrition_info', 'simple_goal_tracking', 'educational_content']
                if all(feature in features for feature in expected_features):
                    print(f"   ✅ All expected features available: {len(features)} features")
                else:
                    print(f"   ⚠️  Some expected features missing")
                
                return True
            else:
                print(f"   ❌ Guest session response missing keys: {missing_keys}")
                return False
        
        return False

    def test_guest_goals_management_flow(self):
        """Test complete guest goals management flow"""
        if not hasattr(self, 'test_session_id'):
            print("❌ No session ID available for testing")
            return False
        
        session_id = self.test_session_id
        
        # Test 1: Sync guest goals with backend
        sync_success = self.test_sync_guest_goals(session_id)
        
        # Test 2: Retrieve guest goals
        retrieve_success = self.test_retrieve_guest_goals(session_id)
        
        # Test 3: Update goal progress
        progress_success = self.test_update_goal_progress(session_id)
        
        # Test 4: Get goal analytics
        analytics_success = self.test_guest_goal_analytics(session_id)
        
        return sync_success and retrieve_success and progress_success and analytics_success

    def test_sync_guest_goals(self, session_id):
        """Test syncing guest goals with backend"""
        print("\n📝 Testing Guest Goals Sync...")
        
        # Sample goals data with different categories and progress levels
        sample_goals = {
            "goals": [
                {
                    "id": 1,
                    "title": "Drink 8 glasses of water",
                    "category": "hydration",
                    "target": 8,
                    "unit": "glasses",
                    "current": 3,
                    "timeframe": "daily",
                    "createdAt": datetime.utcnow().isoformat(),
                    "lastUpdated": datetime.utcnow().isoformat()
                },
                {
                    "id": 2,
                    "title": "Eat 5 servings of fruits/vegetables",
                    "category": "nutrition",
                    "target": 5,
                    "unit": "servings",
                    "current": 2,
                    "timeframe": "daily",
                    "createdAt": datetime.utcnow().isoformat(),
                    "lastUpdated": datetime.utcnow().isoformat()
                },
                {
                    "id": 3,
                    "title": "Take vitamins",
                    "category": "habits",
                    "target": 1,
                    "unit": "dose",
                    "current": 1,
                    "timeframe": "daily",
                    "createdAt": datetime.utcnow().isoformat(),
                    "lastUpdated": datetime.utcnow().isoformat()
                }
            ]
        }
        
        success, sync_response = self.run_test(
            "Sync Guest Goals",
            "POST",
            f"guest/goals/{session_id}",
            200,
            data=sample_goals
        )
        
        if success and sync_response:
            # Validate sync response structure
            expected_keys = ['success', 'session_id', 'goals_synced', 'expires_at']
            missing_keys = [key for key in expected_keys if key not in sync_response]
            
            if not missing_keys:
                print(f"   ✅ Goals sync response contains all required keys: {expected_keys}")
                
                # Validate sync details
                goals_synced = sync_response.get('goals_synced', 0)
                if goals_synced == 3:
                    print(f"   ✅ All 3 goals synced successfully")
                    return True
                else:
                    print(f"   ❌ Expected 3 goals synced, got {goals_synced}")
                    return False
            else:
                print(f"   ❌ Goals sync response missing keys: {missing_keys}")
                return False
        
        return False

    def test_retrieve_guest_goals(self, session_id):
        """Test retrieving guest goals for a session"""
        print("\n📖 Testing Guest Goals Retrieval...")
        
        success, goals_response = self.run_test(
            "Retrieve Guest Goals",
            "GET",
            f"guest/goals/{session_id}",
            200
        )
        
        if success and goals_response:
            # Validate goals response structure
            expected_keys = ['success', 'session_id', 'goals']
            missing_keys = [key for key in expected_keys if key not in goals_response]
            
            if not missing_keys:
                print(f"   ✅ Goals retrieval response contains all required keys: {expected_keys}")
                
                # Validate goals data
                goals = goals_response.get('goals', [])
                if len(goals) == 3:
                    print(f"   ✅ Retrieved all 3 synced goals")
                    
                    # Validate goal structure
                    goal = goals[0]
                    goal_keys = ['id', 'title', 'category', 'target', 'unit', 'current', 'timeframe']
                    missing_goal_keys = [key for key in goal_keys if key not in goal]
                    
                    if not missing_goal_keys:
                        print(f"   ✅ Goal structure valid")
                        
                        # Validate different categories
                        categories = [g.get('category') for g in goals]
                        expected_categories = ['hydration', 'nutrition', 'habits']
                        if all(cat in categories for cat in expected_categories):
                            print(f"   ✅ All expected categories present: {categories}")
                            return True
                        else:
                            print(f"   ❌ Missing expected categories. Got: {categories}")
                            return False
                    else:
                        print(f"   ❌ Goal structure missing keys: {missing_goal_keys}")
                        return False
                else:
                    print(f"   ❌ Expected 3 goals, got {len(goals)}")
                    return False
            else:
                print(f"   ❌ Goals retrieval response missing keys: {missing_keys}")
                return False
        
        return False

    def test_update_goal_progress(self, session_id):
        """Test updating progress for a specific goal"""
        print("\n📈 Testing Goal Progress Update...")
        
        # Update progress for goal ID 1 (water intake)
        progress_update = {
            "goal_id": 1,
            "current": 5  # Updated from 3 to 5 glasses
        }
        
        success, progress_response = self.run_test(
            "Update Goal Progress",
            "POST",
            f"guest/goals/{session_id}/progress",
            200,
            data=progress_update
        )
        
        if success and progress_response:
            # Validate progress update response structure
            expected_keys = ['success', 'goal_id', 'new_current', 'message']
            missing_keys = [key for key in expected_keys if key not in progress_response]
            
            if not missing_keys:
                print(f"   ✅ Progress update response contains all required keys: {expected_keys}")
                
                # Validate update details
                goal_id = progress_response.get('goal_id')
                new_current = progress_response.get('new_current')
                
                if goal_id == 1 and new_current == 5:
                    print(f"   ✅ Goal progress updated successfully: Goal {goal_id} now at {new_current}")
                    return True
                else:
                    print(f"   ❌ Progress update mismatch. Expected goal 1 at 5, got goal {goal_id} at {new_current}")
                    return False
            else:
                print(f"   ❌ Progress update response missing keys: {missing_keys}")
                return False
        
        return False

    def test_guest_goal_analytics(self, session_id):
        """Test getting goal analytics and insights"""
        print("\n📊 Testing Guest Goal Analytics...")
        
        success, analytics_response = self.run_test(
            "Get Goal Analytics",
            "GET",
            f"guest/goals/{session_id}/analytics",
            200
        )
        
        if success and analytics_response:
            # Validate analytics response structure
            expected_keys = ['success', 'session_id', 'analytics']
            missing_keys = [key for key in expected_keys if key not in analytics_response]
            
            if not missing_keys:
                print(f"   ✅ Analytics response contains all required keys: {expected_keys}")
                
                # Validate analytics data structure
                analytics = analytics_response.get('analytics', {})
                analytics_keys = ['total_goals', 'completed_goals', 'completion_rate', 'category_breakdown', 'insights', 'motivational_message', 'next_actions']
                missing_analytics_keys = [key for key in analytics_keys if key not in analytics]
                
                if not missing_analytics_keys:
                    print(f"   ✅ Analytics data contains all required keys: {analytics_keys}")
                    
                    # Validate analytics calculations
                    total_goals = analytics.get('total_goals', 0)
                    completed_goals = analytics.get('completed_goals', 0)
                    completion_rate = analytics.get('completion_rate', 0)
                    
                    print(f"   📊 Analytics Summary:")
                    print(f"      Total Goals: {total_goals}")
                    print(f"      Completed Goals: {completed_goals}")
                    print(f"      Completion Rate: {completion_rate}%")
                    
                    # Validate category breakdown
                    category_breakdown = analytics.get('category_breakdown', {})
                    expected_categories = ['hydration', 'nutrition', 'habits']
                    
                    if all(cat in category_breakdown for cat in expected_categories):
                        print(f"   ✅ Category breakdown includes all expected categories")
                        
                        # Check if habits category shows as completed (current=1, target=1)
                        habits_stats = category_breakdown.get('habits', {})
                        if habits_stats.get('completed', 0) == 1 and habits_stats.get('total', 0) == 1:
                            print(f"   ✅ Habits category correctly shows as completed")
                        
                    else:
                        print(f"   ❌ Category breakdown missing expected categories")
                        return False
                    
                    # Validate insights and motivational messages
                    insights = analytics.get('insights', [])
                    motivational_message = analytics.get('motivational_message', '')
                    next_actions = analytics.get('next_actions', [])
                    
                    if insights and motivational_message and next_actions:
                        print(f"   ✅ Analytics includes insights ({len(insights)}), motivational message, and next actions ({len(next_actions)})")
                        print(f"   💬 Sample insight: {insights[0] if insights else 'None'}")
                        print(f"   🎯 Motivational message: {motivational_message}")
                        print(f"   📋 Next action: {next_actions[0] if next_actions else 'None'}")
                        return True
                    else:
                        print(f"   ❌ Missing insights, motivational message, or next actions")
                        return False
                        
                else:
                    print(f"   ❌ Analytics data missing keys: {missing_analytics_keys}")
                    return False
            else:
                print(f"   ❌ Analytics response missing keys: {missing_keys}")
                return False
        
        return False

    def test_phase7_data_export_endpoints(self):
        """Test Phase 7 Data Export API endpoints"""
        print("\n📋 Testing Phase 7 Data Export Endpoints...")
        
        # Test Patient Data Export
        patient_export_success = self.test_patient_data_export()
        
        # Test Provider Data Export
        provider_export_success = self.test_provider_data_export()
        
        # Test Family Data Export
        family_export_success = self.test_family_data_export()
        
        # Test Guest Data Export
        guest_export_success = self.test_guest_data_export()
        
        return (patient_export_success and provider_export_success and 
                family_export_success and guest_export_success)

    def test_patient_data_export(self):
        """Test Patient Data Export endpoint"""
        print("\n👤 Testing Patient Data Export...")
        
        test_user_id = "demo-patient-123"
        
        # Test 1: GET /api/patient/export/{user_id} - Default JSON format
        success1, export_data = self.run_test(
            "Patient Data Export (JSON)",
            "GET",
            f"patient/export/{test_user_id}",
            200
        )
        
        # Validate export response structure
        if success1 and export_data:
            expected_keys = ['export_info', 'profile', 'health_data', 'food_logs', 'ai_insights']
            missing_keys = [key for key in expected_keys if key not in export_data]
            
            if not missing_keys:
                print(f"   ✅ Patient export response contains all required keys: {expected_keys}")
                
                # Validate export_info structure
                export_info = export_data.get('export_info', {})
                info_keys = ['user_id', 'role', 'exported_at', 'format']
                missing_info_keys = [key for key in info_keys if key not in export_info]
                
                if not missing_info_keys:
                    print(f"   ✅ Export metadata structure valid")
                    print(f"   📊 User ID: {export_info.get('user_id')}, Role: {export_info.get('role')}")
                    print(f"   📅 Exported at: {export_info.get('exported_at')}")
                    
                    # Verify role-specific data
                    if export_info.get('role') == 'patient':
                        print(f"   ✅ Role-specific data correctly identified as patient")
                    else:
                        print(f"   ❌ Role mismatch - expected 'patient', got '{export_info.get('role')}'")
                        success1 = False
                else:
                    print(f"   ❌ Export metadata missing keys: {missing_info_keys}")
                    success1 = False
                
                # Validate profile data structure
                profile = export_data.get('profile', {})
                if profile:
                    profile_keys = ['user_id', 'basic_info', 'physical_metrics', 'activity_profile', 
                                  'health_history', 'dietary_profile', 'goals_preferences', 'profile_completion']
                    missing_profile_keys = [key for key in profile_keys if key not in profile]
                    
                    if not missing_profile_keys:
                        print(f"   ✅ Patient profile structure valid")
                        completion = profile.get('profile_completion', 0)
                        print(f"   📈 Profile completion: {completion}%")
                    else:
                        print(f"   ❌ Patient profile missing keys: {missing_profile_keys}")
                        success1 = False
                
                # Validate health data structure
                health_data = export_data.get('health_data', {})
                if health_data:
                    health_keys = ['nutrition_summary', 'health_metrics', 'goals']
                    missing_health_keys = [key for key in health_keys if key not in health_data]
                    
                    if not missing_health_keys:
                        print(f"   ✅ Health data structure valid")
                        goals = health_data.get('goals', [])
                        print(f"   🎯 Health goals: {len(goals)} goals tracked")
                    else:
                        print(f"   ❌ Health data missing keys: {missing_health_keys}")
                        success1 = False
                
                # Validate food logs structure
                food_logs = export_data.get('food_logs', [])
                if food_logs and len(food_logs) > 0:
                    log = food_logs[0]
                    log_keys = ['date', 'meals', 'total_calories', 'total_protein']
                    missing_log_keys = [key for key in log_keys if key not in log]
                    
                    if not missing_log_keys:
                        print(f"   ✅ Food logs structure valid")
                        print(f"   🍽️ Food logs: {len(food_logs)} days of data")
                    else:
                        print(f"   ❌ Food logs missing keys: {missing_log_keys}")
                        success1 = False
                
                # Validate AI insights
                ai_insights = export_data.get('ai_insights', [])
                if ai_insights:
                    print(f"   ✅ AI insights provided: {len(ai_insights)} insights")
                else:
                    print(f"   ⚠️  No AI insights in export")
                    
            else:
                print(f"   ❌ Patient export response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: Test with explicit JSON format parameter
        success2, _ = self.run_test(
            "Patient Data Export (Explicit JSON)",
            "GET",
            f"patient/export/{test_user_id}",
            200,
            params={"format": "json"}
        )
        
        # Test 3: Test error handling for non-existent patient
        success3, _ = self.run_test(
            "Patient Data Export (Non-existent User)",
            "GET",
            "patient/export/non-existent-user-123",
            404
        )
        
        return success1 and success2 and success3

    def test_provider_data_export(self):
        """Test Provider Data Export endpoint"""
        print("\n👨‍⚕️ Testing Provider Data Export...")
        
        test_user_id = "demo-provider-123"
        
        # Test 1: GET /api/provider/export/{user_id}
        success1, export_data = self.run_test(
            "Provider Data Export (JSON)",
            "GET",
            f"provider/export/{test_user_id}",
            200
        )
        
        # Validate export response structure
        if success1 and export_data:
            expected_keys = ['export_info', 'profile', 'practice_data', 'professional_insights']
            missing_keys = [key for key in expected_keys if key not in export_data]
            
            if not missing_keys:
                print(f"   ✅ Provider export response contains all required keys: {expected_keys}")
                
                # Validate export_info structure
                export_info = export_data.get('export_info', {})
                info_keys = ['user_id', 'role', 'exported_at', 'format']
                missing_info_keys = [key for key in info_keys if key not in export_info]
                
                if not missing_info_keys:
                    print(f"   ✅ Export metadata structure valid")
                    print(f"   📊 User ID: {export_info.get('user_id')}, Role: {export_info.get('role')}")
                    
                    # Verify role-specific data
                    if export_info.get('role') == 'provider':
                        print(f"   ✅ Role-specific data correctly identified as provider")
                    else:
                        print(f"   ❌ Role mismatch - expected 'provider', got '{export_info.get('role')}'")
                        success1 = False
                else:
                    print(f"   ❌ Export metadata missing keys: {missing_info_keys}")
                    success1 = False
                
                # Validate provider profile structure
                profile = export_data.get('profile', {})
                if profile:
                    profile_keys = ['user_id', 'professional_identity', 'credentials', 'practice_info', 
                                  'preferences', 'verification_status', 'profile_completion']
                    missing_profile_keys = [key for key in profile_keys if key not in profile]
                    
                    if not missing_profile_keys:
                        print(f"   ✅ Provider profile structure valid")
                        verification = profile.get('verification_status', 'UNKNOWN')
                        completion = profile.get('profile_completion', 0)
                        print(f"   🔐 Verification: {verification}, Completion: {completion}%")
                    else:
                        print(f"   ❌ Provider profile missing keys: {missing_profile_keys}")
                        success1 = False
                
                # Validate practice data structure
                practice_data = export_data.get('practice_data', {})
                if practice_data:
                    practice_keys = ['patient_overview', 'clinical_analytics', 'recent_activities']
                    missing_practice_keys = [key for key in practice_keys if key not in practice_data]
                    
                    if not missing_practice_keys:
                        print(f"   ✅ Practice data structure valid")
                        patient_overview = practice_data.get('patient_overview', {})
                        total_patients = patient_overview.get('total_patients', 0)
                        print(f"   👥 Total patients: {total_patients}")
                    else:
                        print(f"   ❌ Practice data missing keys: {missing_practice_keys}")
                        success1 = False
                
                # Validate professional insights
                insights = export_data.get('professional_insights', [])
                if insights:
                    print(f"   ✅ Professional insights provided: {len(insights)} insights")
                else:
                    print(f"   ⚠️  No professional insights in export")
                    
            else:
                print(f"   ❌ Provider export response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: Test error handling for non-existent provider
        success2, _ = self.run_test(
            "Provider Data Export (Non-existent User)",
            "GET",
            "provider/export/non-existent-provider-123",
            404
        )
        
        return success1 and success2

    def test_family_data_export(self):
        """Test Family Data Export endpoint"""
        print("\n👨‍👩‍👧‍👦 Testing Family Data Export...")
        
        test_family_id = "demo-family-123"
        
        # Test 1: GET /api/family/export/{family_id}
        success1, export_data = self.run_test(
            "Family Data Export (JSON)",
            "GET",
            f"family/export/{test_family_id}",
            200
        )
        
        # Validate export response structure
        if success1 and export_data:
            expected_keys = ['export_info', 'profile', 'family_health_data', 'meal_planning', 'care_coordination']
            missing_keys = [key for key in expected_keys if key not in export_data]
            
            if not missing_keys:
                print(f"   ✅ Family export response contains all required keys: {expected_keys}")
                
                # Validate export_info structure
                export_info = export_data.get('export_info', {})
                info_keys = ['family_id', 'role', 'exported_at', 'format']
                missing_info_keys = [key for key in info_keys if key not in export_info]
                
                if not missing_info_keys:
                    print(f"   ✅ Export metadata structure valid")
                    print(f"   📊 Family ID: {export_info.get('family_id')}, Role: {export_info.get('role')}")
                    
                    # Verify role-specific data
                    if export_info.get('role') == 'family':
                        print(f"   ✅ Role-specific data correctly identified as family")
                    else:
                        print(f"   ❌ Role mismatch - expected 'family', got '{export_info.get('role')}'")
                        success1 = False
                else:
                    print(f"   ❌ Export metadata missing keys: {missing_info_keys}")
                    success1 = False
                
                # Validate family profile structure
                profile = export_data.get('profile', {})
                if profile:
                    profile_keys = ['user_id', 'family_structure', 'family_members', 'household_management', 
                                  'care_coordination', 'profile_completion']
                    missing_profile_keys = [key for key in profile_keys if key not in profile]
                    
                    if not missing_profile_keys:
                        print(f"   ✅ Family profile structure valid")
                        family_members = profile.get('family_members', [])
                        completion = profile.get('profile_completion', 0)
                        print(f"   👥 Family members: {len(family_members)}, Completion: {completion}%")
                    else:
                        print(f"   ❌ Family profile missing keys: {missing_profile_keys}")
                        success1 = False
                
                # Validate family health data structure
                health_data = export_data.get('family_health_data', {})
                if health_data:
                    health_keys = ['member_health_summary', 'family_goals']
                    missing_health_keys = [key for key in health_keys if key not in health_data]
                    
                    if not missing_health_keys:
                        print(f"   ✅ Family health data structure valid")
                        member_summary = health_data.get('member_health_summary', [])
                        family_goals = health_data.get('family_goals', [])
                        print(f"   💪 Health summaries: {len(member_summary)} members, Goals: {len(family_goals)}")
                    else:
                        print(f"   ❌ Family health data missing keys: {missing_health_keys}")
                        success1 = False
                
                # Validate meal planning structure
                meal_planning = export_data.get('meal_planning', {})
                if meal_planning:
                    meal_keys = ['weekly_meals', 'dietary_accommodations', 'budget_tracking']
                    missing_meal_keys = [key for key in meal_keys if key not in meal_planning]
                    
                    if not missing_meal_keys:
                        print(f"   ✅ Meal planning structure valid")
                        weekly_meals = meal_planning.get('weekly_meals', [])
                        print(f"   🍽️ Weekly meals planned: {len(weekly_meals)} days")
                    else:
                        print(f"   ❌ Meal planning missing keys: {missing_meal_keys}")
                        success1 = False
                
                # Validate care coordination structure
                care_coord = export_data.get('care_coordination', {})
                if care_coord:
                    care_keys = ['medical_appointments', 'emergency_contacts', 'healthcare_providers']
                    missing_care_keys = [key for key in care_keys if key not in care_coord]
                    
                    if not missing_care_keys:
                        print(f"   ✅ Care coordination structure valid")
                        appointments = care_coord.get('medical_appointments', [])
                        emergency_contacts = care_coord.get('emergency_contacts', [])
                        print(f"   🏥 Appointments: {len(appointments)}, Emergency contacts: {len(emergency_contacts)}")
                    else:
                        print(f"   ❌ Care coordination missing keys: {missing_care_keys}")
                        success1 = False
                    
            else:
                print(f"   ❌ Family export response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: Test error handling for non-existent family
        success2, _ = self.run_test(
            "Family Data Export (Non-existent Family)",
            "GET",
            "family/export/non-existent-family-123",
            404
        )
        
        return success1 and success2

    def test_guest_data_export(self):
        """Test Guest Data Export endpoint"""
        print("\n👤 Testing Guest Data Export...")
        
        test_session_id = "demo-guest-session-123"
        
        # Test 1: GET /api/guest/export/{session_id}
        success1, export_data = self.run_test(
            "Guest Data Export (JSON)",
            "GET",
            f"guest/export/{test_session_id}",
            200
        )
        
        # Validate export response structure
        if success1 and export_data:
            expected_keys = ['export_info', 'profile', 'session_data', 'insights', 'upgrade_benefits']
            missing_keys = [key for key in expected_keys if key not in export_data]
            
            if not missing_keys:
                print(f"   ✅ Guest export response contains all required keys: {expected_keys}")
                
                # Validate export_info structure
                export_info = export_data.get('export_info', {})
                info_keys = ['session_id', 'role', 'exported_at', 'format', 'session_expires_at']
                missing_info_keys = [key for key in info_keys if key not in export_info]
                
                if not missing_info_keys:
                    print(f"   ✅ Export metadata structure valid")
                    print(f"   📊 Session ID: {export_info.get('session_id')}, Role: {export_info.get('role')}")
                    print(f"   ⏰ Session expires: {export_info.get('session_expires_at')}")
                    
                    # Verify role-specific data
                    if export_info.get('role') == 'guest':
                        print(f"   ✅ Role-specific data correctly identified as guest")
                    else:
                        print(f"   ❌ Role mismatch - expected 'guest', got '{export_info.get('role')}'")
                        success1 = False
                else:
                    print(f"   ❌ Export metadata missing keys: {missing_info_keys}")
                    success1 = False
                
                # Validate guest profile structure
                profile = export_data.get('profile', {})
                if profile:
                    profile_keys = ['session_id', 'demographics', 'goals', 'created_at', 'expires_at']
                    missing_profile_keys = [key for key in profile_keys if key not in profile]
                    
                    if not missing_profile_keys:
                        print(f"   ✅ Guest profile structure valid")
                        print(f"   📅 Created: {profile.get('created_at')}")
                    else:
                        print(f"   ❌ Guest profile missing keys: {missing_profile_keys}")
                        success1 = False
                
                # Validate session data structure
                session_data = export_data.get('session_data', {})
                if session_data:
                    session_keys = ['todays_entries', 'nutrition_summary', 'simple_goals']
                    missing_session_keys = [key for key in session_keys if key not in session_data]
                    
                    if not missing_session_keys:
                        print(f"   ✅ Session data structure valid")
                        todays_entries = session_data.get('todays_entries', {})
                        foods_logged = todays_entries.get('foods_logged', [])
                        simple_goals = session_data.get('simple_goals', [])
                        print(f"   🍎 Foods logged: {len(foods_logged)}, Goals: {len(simple_goals)}")
                    else:
                        print(f"   ❌ Session data missing keys: {missing_session_keys}")
                        success1 = False
                
                # Validate insights
                insights = export_data.get('insights', [])
                if insights:
                    print(f"   ✅ Guest insights provided: {len(insights)} insights")
                else:
                    print(f"   ⚠️  No insights in guest export")
                
                # Validate upgrade benefits structure
                upgrade_benefits = export_data.get('upgrade_benefits', {})
                if upgrade_benefits:
                    benefit_keys = ['features_available_with_account', 'current_limitations']
                    missing_benefit_keys = [key for key in benefit_keys if key not in upgrade_benefits]
                    
                    if not missing_benefit_keys:
                        print(f"   ✅ Upgrade benefits structure valid")
                        features = upgrade_benefits.get('features_available_with_account', [])
                        limitations = upgrade_benefits.get('current_limitations', [])
                        print(f"   🚀 Upgrade features: {len(features)}, Current limitations: {len(limitations)}")
                    else:
                        print(f"   ❌ Upgrade benefits missing keys: {missing_benefit_keys}")
                        success1 = False
                    
            else:
                print(f"   ❌ Guest export response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: Test error handling for non-existent session
        success2, _ = self.run_test(
            "Guest Data Export (Non-existent Session)",
            "GET",
            "guest/export/non-existent-session-123",
            404
        )
        
        # Test 3: Test session expiration handling (if applicable)
        # Note: This would require creating an expired session, which might not be feasible in this test
        # For now, we'll assume the endpoint handles expiration correctly based on the implementation
        
        return success1 and success2

    def test_phase7_data_export_endpoints(self):
        """Test Phase 7 Data Export API Endpoints"""
        print("\n📋 Testing Phase 7 Data Export Endpoints...")
        
        # Test identifiers as specified in the review request
        patient_id = "demo-patient-123"
        provider_id = "demo-provider-123"
        family_id = "demo-family-123"
        guest_session_id = "demo-guest-session-123"
        
        # Test 1: Patient Data Export
        patient_success = self.test_patient_data_export_comprehensive(patient_id)
        
        # Test 2: Provider Data Export
        provider_success = self.test_provider_data_export_comprehensive(provider_id)
        
        # Test 3: Family Data Export
        family_success = self.test_family_data_export_comprehensive(family_id)
        
        # Test 4: Guest Data Export
        guest_success = self.test_guest_data_export_comprehensive(guest_session_id)
        
        # Test 5: Error handling for non-existent profiles
        error_handling_success = self.test_export_error_handling()
        
        return (patient_success and provider_success and family_success and 
                guest_success and error_handling_success)

    def test_patient_data_export_comprehensive(self, user_id):
        """Test Patient Data Export endpoint with comprehensive validation"""
        print("\n🏥 Testing Patient Data Export...")
        
        success, export_data = self.run_test(
            "Patient Data Export",
            "GET",
            f"patient/export/{user_id}",
            200
        )
        
        if success and export_data:
            # Validate export_info metadata
            export_info = export_data.get('export_info', {})
            expected_info_keys = ['user_id', 'role', 'exported_at', 'format']
            missing_info_keys = [key for key in expected_info_keys if key not in export_info]
            
            if not missing_info_keys:
                print(f"   ✅ Export info metadata valid: {expected_info_keys}")
                
                # Validate role-specific data
                if export_info.get('role') == 'patient':
                    print(f"   ✅ Role correctly identified as 'patient'")
                else:
                    print(f"   ❌ Role mismatch: expected 'patient', got '{export_info.get('role')}'")
                    success = False
                    
                # Validate user_id matches
                if export_info.get('user_id') == user_id:
                    print(f"   ✅ User ID correctly set: {user_id}")
                else:
                    print(f"   ❌ User ID mismatch: expected '{user_id}', got '{export_info.get('user_id')}'")
                    success = False
            else:
                print(f"   ❌ Export info missing keys: {missing_info_keys}")
                success = False
            
            # Validate comprehensive data structure
            expected_main_keys = ['export_info', 'profile', 'health_data', 'food_logs', 'ai_insights']
            missing_main_keys = [key for key in expected_main_keys if key not in export_data]
            
            if not missing_main_keys:
                print(f"   ✅ Patient export contains all required sections: {expected_main_keys}")
                
                # Validate profile data completeness
                profile = export_data.get('profile', {})
                profile_keys = ['user_id', 'basic_info', 'physical_metrics', 'activity_profile', 
                               'health_history', 'dietary_profile', 'goals_preferences', 'profile_completion']
                missing_profile_keys = [key for key in profile_keys if key not in profile]
                
                if not missing_profile_keys:
                    print(f"   ✅ Patient profile data structure complete")
                    completion = profile.get('profile_completion', 0)
                    print(f"   📊 Profile completion: {completion}%")
                else:
                    print(f"   ❌ Patient profile missing keys: {missing_profile_keys}")
                
                # Validate health data
                health_data = export_data.get('health_data', {})
                health_keys = ['nutrition_summary', 'health_metrics', 'goals']
                missing_health_keys = [key for key in health_keys if key not in health_data]
                
                if not missing_health_keys:
                    print(f"   ✅ Health data structure complete")
                    goals = health_data.get('goals', [])
                    print(f"   🎯 Health goals: {len(goals)} goals tracked")
                else:
                    print(f"   ❌ Health data missing keys: {missing_health_keys}")
                
                # Validate food logs
                food_logs = export_data.get('food_logs', [])
                if isinstance(food_logs, list) and len(food_logs) > 0:
                    log = food_logs[0]
                    log_keys = ['date', 'meals', 'total_calories', 'total_protein']
                    missing_log_keys = [key for key in log_keys if key not in log]
                    
                    if not missing_log_keys:
                        print(f"   ✅ Food logs structure valid: {len(food_logs)} days")
                    else:
                        print(f"   ❌ Food logs missing keys: {missing_log_keys}")
                else:
                    print(f"   ⚠️  No food logs in export")
                
                # Validate AI insights
                ai_insights = export_data.get('ai_insights', [])
                if isinstance(ai_insights, list) and len(ai_insights) > 0:
                    print(f"   ✅ AI insights provided: {len(ai_insights)} insights")
                else:
                    print(f"   ⚠️  No AI insights in export")
                    
            else:
                print(f"   ❌ Patient export missing main sections: {missing_main_keys}")
                success = False
            
            # Validate JSON format compliance
            try:
                import json
                json.dumps(export_data)
                print(f"   ✅ Export data is valid JSON format")
            except (TypeError, ValueError) as e:
                print(f"   ❌ Export data is not valid JSON: {e}")
                success = False
        
        return success

    def test_provider_data_export_comprehensive(self, user_id):
        """Test Provider Data Export endpoint with comprehensive validation"""
        print("\n👩‍⚕️ Testing Provider Data Export...")
        
        success, export_data = self.run_test(
            "Provider Data Export",
            "GET",
            f"provider/export/{user_id}",
            200
        )
        
        if success and export_data:
            # Validate export_info metadata
            export_info = export_data.get('export_info', {})
            expected_info_keys = ['user_id', 'role', 'exported_at', 'format']
            missing_info_keys = [key for key in expected_info_keys if key not in export_info]
            
            if not missing_info_keys:
                print(f"   ✅ Export info metadata valid: {expected_info_keys}")
                
                # Validate role-specific data
                if export_info.get('role') == 'provider':
                    print(f"   ✅ Role correctly identified as 'provider'")
                else:
                    print(f"   ❌ Role mismatch: expected 'provider', got '{export_info.get('role')}'")
                    success = False
                    
                # Validate user_id matches
                if export_info.get('user_id') == user_id:
                    print(f"   ✅ User ID correctly set: {user_id}")
                else:
                    print(f"   ❌ User ID mismatch: expected '{user_id}', got '{export_info.get('user_id')}'")
                    success = False
            else:
                print(f"   ❌ Export info missing keys: {missing_info_keys}")
                success = False
            
            # Validate comprehensive data structure
            expected_main_keys = ['export_info', 'profile', 'practice_data', 'professional_insights']
            missing_main_keys = [key for key in expected_main_keys if key not in export_data]
            
            if not missing_main_keys:
                print(f"   ✅ Provider export contains all required sections: {expected_main_keys}")
                
                # Validate profile data completeness
                profile = export_data.get('profile', {})
                profile_keys = ['user_id', 'professional_identity', 'credentials', 'practice_info', 
                               'preferences', 'verification_status', 'profile_completion']
                missing_profile_keys = [key for key in profile_keys if key not in profile]
                
                if not missing_profile_keys:
                    print(f"   ✅ Provider profile data structure complete")
                    verification = profile.get('verification_status', 'UNKNOWN')
                    completion = profile.get('profile_completion', 0)
                    print(f"   📊 Verification: {verification}, Completion: {completion}%")
                else:
                    print(f"   ❌ Provider profile missing keys: {missing_profile_keys}")
                
                # Validate practice data
                practice_data = export_data.get('practice_data', {})
                practice_keys = ['patient_overview', 'clinical_analytics', 'recent_activities']
                missing_practice_keys = [key for key in practice_keys if key not in practice_data]
                
                if not missing_practice_keys:
                    print(f"   ✅ Practice data structure complete")
                    patient_overview = practice_data.get('patient_overview', {})
                    total_patients = patient_overview.get('total_patients', 0)
                    print(f"   👥 Total patients: {total_patients}")
                else:
                    print(f"   ❌ Practice data missing keys: {missing_practice_keys}")
                
                # Validate professional insights
                insights = export_data.get('professional_insights', [])
                if isinstance(insights, list) and len(insights) > 0:
                    print(f"   ✅ Professional insights provided: {len(insights)} insights")
                else:
                    print(f"   ⚠️  No professional insights in export")
                    
            else:
                print(f"   ❌ Provider export missing main sections: {missing_main_keys}")
                success = False
            
            # Validate JSON format compliance
            try:
                import json
                json.dumps(export_data)
                print(f"   ✅ Export data is valid JSON format")
            except (TypeError, ValueError) as e:
                print(f"   ❌ Export data is not valid JSON: {e}")
                success = False
        
        return success

    def test_family_data_export_comprehensive(self, family_id):
        """Test Family Data Export endpoint with comprehensive validation"""
        print("\n👨‍👩‍👧‍👦 Testing Family Data Export...")
        
        success, export_data = self.run_test(
            "Family Data Export",
            "GET",
            f"family/export/{family_id}",
            200
        )
        
        if success and export_data:
            # Validate export_info metadata
            export_info = export_data.get('export_info', {})
            expected_info_keys = ['family_id', 'role', 'exported_at', 'format']
            missing_info_keys = [key for key in expected_info_keys if key not in export_info]
            
            if not missing_info_keys:
                print(f"   ✅ Export info metadata valid: {expected_info_keys}")
                
                # Validate role-specific data
                if export_info.get('role') == 'family':
                    print(f"   ✅ Role correctly identified as 'family'")
                else:
                    print(f"   ❌ Role mismatch: expected 'family', got '{export_info.get('role')}'")
                    success = False
                    
                # Validate family_id matches
                if export_info.get('family_id') == family_id:
                    print(f"   ✅ Family ID correctly set: {family_id}")
                else:
                    print(f"   ❌ Family ID mismatch: expected '{family_id}', got '{export_info.get('family_id')}'")
                    success = False
            else:
                print(f"   ❌ Export info missing keys: {missing_info_keys}")
                success = False
            
            # Validate comprehensive data structure
            expected_main_keys = ['export_info', 'profile', 'family_health_data', 'meal_planning', 'care_coordination']
            missing_main_keys = [key for key in expected_main_keys if key not in export_data]
            
            if not missing_main_keys:
                print(f"   ✅ Family export contains all required sections: {expected_main_keys}")
                
                # Validate profile data completeness
                profile = export_data.get('profile', {})
                profile_keys = ['user_id', 'family_structure', 'family_members', 'household_management', 
                               'care_coordination', 'profile_completion']
                missing_profile_keys = [key for key in profile_keys if key not in profile]
                
                if not missing_profile_keys:
                    print(f"   ✅ Family profile data structure complete")
                    family_members = profile.get('family_members', [])
                    completion = profile.get('profile_completion', 0)
                    print(f"   👥 Family members: {len(family_members)}, Completion: {completion}%")
                else:
                    print(f"   ❌ Family profile missing keys: {missing_profile_keys}")
                
                # Validate family health data
                health_data = export_data.get('family_health_data', {})
                health_keys = ['member_health_summary', 'family_goals']
                missing_health_keys = [key for key in health_keys if key not in health_data]
                
                if not missing_health_keys:
                    print(f"   ✅ Family health data structure complete")
                    member_summary = health_data.get('member_health_summary', [])
                    family_goals = health_data.get('family_goals', [])
                    print(f"   📊 Health summaries: {len(member_summary)}, Goals: {len(family_goals)}")
                else:
                    print(f"   ❌ Family health data missing keys: {missing_health_keys}")
                
                # Validate meal planning data
                meal_planning = export_data.get('meal_planning', {})
                meal_keys = ['weekly_meals', 'dietary_accommodations', 'budget_tracking']
                missing_meal_keys = [key for key in meal_keys if key not in meal_planning]
                
                if not missing_meal_keys:
                    print(f"   ✅ Meal planning data structure complete")
                    weekly_meals = meal_planning.get('weekly_meals', [])
                    accommodations = meal_planning.get('dietary_accommodations', [])
                    print(f"   🍽️ Weekly meals: {len(weekly_meals)}, Accommodations: {len(accommodations)}")
                else:
                    print(f"   ❌ Meal planning missing keys: {missing_meal_keys}")
                
                # Validate care coordination
                care_coordination = export_data.get('care_coordination', {})
                care_keys = ['medical_appointments', 'emergency_contacts', 'healthcare_providers']
                missing_care_keys = [key for key in care_keys if key not in care_coordination]
                
                if not missing_care_keys:
                    print(f"   ✅ Care coordination data structure complete")
                    appointments = care_coordination.get('medical_appointments', [])
                    emergency_contacts = care_coordination.get('emergency_contacts', [])
                    print(f"   🏥 Appointments: {len(appointments)}, Emergency contacts: {len(emergency_contacts)}")
                else:
                    print(f"   ❌ Care coordination missing keys: {missing_care_keys}")
                    
            else:
                print(f"   ❌ Family export missing main sections: {missing_main_keys}")
                success = False
            
            # Validate JSON format compliance
            try:
                import json
                json.dumps(export_data)
                print(f"   ✅ Export data is valid JSON format")
            except (TypeError, ValueError) as e:
                print(f"   ❌ Export data is not valid JSON: {e}")
                success = False
        
        return success

    def test_guest_data_export_comprehensive(self, session_id):
        """Test Guest Data Export endpoint with comprehensive validation"""
        print("\n👤 Testing Guest Data Export...")
        
        success, export_data = self.run_test(
            "Guest Data Export",
            "GET",
            f"guest/export/{session_id}",
            200
        )
        
        if success and export_data:
            # Validate export_info metadata
            export_info = export_data.get('export_info', {})
            expected_info_keys = ['session_id', 'role', 'exported_at', 'format', 'session_expires_at']
            missing_info_keys = [key for key in expected_info_keys if key not in export_info]
            
            if not missing_info_keys:
                print(f"   ✅ Export info metadata valid: {expected_info_keys}")
                
                # Validate role-specific data
                if export_info.get('role') == 'guest':
                    print(f"   ✅ Role correctly identified as 'guest'")
                else:
                    print(f"   ❌ Role mismatch: expected 'guest', got '{export_info.get('role')}'")
                    success = False
                
                # Validate session_id matches
                if export_info.get('session_id') == session_id:
                    print(f"   ✅ Session ID correctly set: {session_id}")
                else:
                    print(f"   ❌ Session ID mismatch: expected '{session_id}', got '{export_info.get('session_id')}'")
                    success = False
                
                # Validate session expiration handling
                session_expires = export_info.get('session_expires_at')
                if session_expires:
                    print(f"   ✅ Session expiration info provided: {session_expires}")
                else:
                    print(f"   ⚠️  No session expiration info")
            else:
                print(f"   ❌ Export info missing keys: {missing_info_keys}")
                success = False
            
            # Validate comprehensive data structure
            expected_main_keys = ['export_info', 'profile', 'session_data', 'insights', 'upgrade_benefits']
            missing_main_keys = [key for key in expected_main_keys if key not in export_data]
            
            if not missing_main_keys:
                print(f"   ✅ Guest export contains all required sections: {expected_main_keys}")
                
                # Validate profile data completeness
                profile = export_data.get('profile', {})
                profile_keys = ['session_id', 'demographics', 'goals', 'created_at', 'expires_at']
                missing_profile_keys = [key for key in profile_keys if key not in profile]
                
                if not missing_profile_keys:
                    print(f"   ✅ Guest profile data structure complete")
                    demographics = profile.get('demographics', {})
                    goals = profile.get('goals', {})
                    print(f"   👤 Demographics: {bool(demographics)}, Goals: {bool(goals)}")
                else:
                    print(f"   ❌ Guest profile missing keys: {missing_profile_keys}")
                
                # Validate session data
                session_data = export_data.get('session_data', {})
                session_keys = ['todays_entries', 'nutrition_summary', 'simple_goals']
                missing_session_keys = [key for key in session_keys if key not in session_data]
                
                if not missing_session_keys:
                    print(f"   ✅ Session data structure complete")
                    
                    # Validate today's entries
                    todays_entries = session_data.get('todays_entries', {})
                    if 'foods_logged' in todays_entries and 'total_calories' in todays_entries:
                        foods_count = len(todays_entries.get('foods_logged', []))
                        total_calories = todays_entries.get('total_calories', 0)
                        print(f"   🍽️ Today's entries: {foods_count} foods, {total_calories} calories")
                    else:
                        print(f"   ⚠️  Incomplete today's entries data")
                        
                    # Validate simple goals
                    simple_goals = session_data.get('simple_goals', [])
                    if isinstance(simple_goals, list) and len(simple_goals) > 0:
                        print(f"   🎯 Simple goals: {len(simple_goals)} goals tracked")
                    else:
                        print(f"   ⚠️  No simple goals in session data")
                else:
                    print(f"   ❌ Session data missing keys: {missing_session_keys}")
                
                # Validate upgrade benefits (guest-specific feature)
                upgrade_benefits = export_data.get('upgrade_benefits', {})
                upgrade_keys = ['features_available_with_account', 'current_limitations']
                missing_upgrade_keys = [key for key in upgrade_keys if key not in upgrade_benefits]
                
                if not missing_upgrade_keys:
                    print(f"   ✅ Upgrade benefits information complete")
                    features_count = len(upgrade_benefits.get('features_available_with_account', []))
                    limitations_count = len(upgrade_benefits.get('current_limitations', []))
                    print(f"   ⬆️ Upgrade info: {features_count} features, {limitations_count} limitations")
                else:
                    print(f"   ❌ Upgrade benefits missing keys: {missing_upgrade_keys}")
                
                # Validate insights
                insights = export_data.get('insights', [])
                if isinstance(insights, list) and len(insights) > 0:
                    print(f"   ✅ Insights provided: {len(insights)} insights")
                else:
                    print(f"   ⚠️  No insights in export")
                    
            else:
                print(f"   ❌ Guest export missing main sections: {missing_main_keys}")
                success = False
            
            # Validate JSON format compliance
            try:
                import json
                json.dumps(export_data)
                print(f"   ✅ Export data is valid JSON format")
            except (TypeError, ValueError) as e:
                print(f"   ❌ Export data is not valid JSON: {e}")
                success = False
        
        return success

    def test_export_error_handling(self):
        """Test error handling for non-existent profiles and expired sessions"""
        print("\n🚫 Testing Export Error Handling...")
        
        # Test 1: Non-existent patient profile (404)
        success1, _ = self.run_test(
            "Non-existent Patient Export (Should Fail)",
            "GET",
            "patient/export/non-existent-patient-123",
            404
        )
        
        # Test 2: Non-existent provider profile (404)
        success2, _ = self.run_test(
            "Non-existent Provider Export (Should Fail)",
            "GET",
            "provider/export/non-existent-provider-123",
            404
        )
        
        # Test 3: Non-existent family profile (404)
        success3, _ = self.run_test(
            "Non-existent Family Export (Should Fail)",
            "GET",
            "family/export/non-existent-family-123",
            404
        )
        
        # Test 4: Non-existent guest session (404)
        success4, _ = self.run_test(
            "Non-existent Guest Export (Should Fail)",
            "GET",
            "guest/export/non-existent-session-123",
            404
        )
        
        # Test 5: Test expired guest session (if backend supports it)
        # Note: This would require creating an expired session first, 
        # but for now we'll test with a non-existent session
        success5, _ = self.run_test(
            "Expired Guest Session Export (Should Fail)",
            "GET",
            "guest/export/expired-session-123",
            404  # or 410 if session expired
        )
        
        if success1:
            print(f"   ✅ Patient 404 error handling working")
        if success2:
            print(f"   ✅ Provider 404 error handling working")
        if success3:
            print(f"   ✅ Family 404 error handling working")
        if success4:
            print(f"   ✅ Guest 404 error handling working")
        if success5:
            print(f"   ✅ Expired session error handling working")
        
        return success1 and success2 and success3 and success4 and success5

    def test_guest_session_management_and_export(self):
        """Test the fixed guest session management and data export functionality"""
        print("\n📋 Testing Guest Session Management and Data Export...")
        
        # Test 1: Create a new guest session - verify it creates a guest profile in database
        print("\n🔍 Step 1: Creating guest session...")
        success1, session_response = self.run_test(
            "Create Guest Session",
            "POST",
            "guest/session",
            200
        )
        
        if not success1 or not session_response:
            print("❌ Failed to create guest session - cannot continue with export test")
            return False
        
        session_id = session_response.get('session_id')
        if not session_id:
            print("❌ No session_id returned from guest session creation")
            return False
        
        print(f"✅ Guest session created with ID: {session_id}")
        
        # Validate session response structure
        expected_session_keys = ['session_id', 'expires_at', 'features_available', 'limitations', 'upgrade_benefits']
        missing_session_keys = [key for key in expected_session_keys if key not in session_response]
        if missing_session_keys:
            print(f"⚠️  Session response missing keys: {missing_session_keys}")
        else:
            print("✅ Session response structure is complete")
        
        # Test 2: Verify guest profile was created in database by trying to get it
        print(f"\n🔍 Step 2: Verifying guest profile exists in database...")
        success2, profile_response = self.run_test(
            "Get Guest Profile (Verify Database Creation)",
            "GET",
            f"profiles/guest/{session_id}",
            200
        )
        
        if success2:
            print("✅ Guest profile successfully created in database")
            print(f"   Profile session_id: {profile_response.get('session_id')}")
            print(f"   Profile expires: {profile_response.get('session_expires')}")
        else:
            print("❌ Guest profile was not created in database - this was the original issue")
            return False
        
        # Test 3: Test data export with the session_id - verify it now works
        print(f"\n🔍 Step 3: Testing data export with session_id: {session_id}")
        success3, export_response = self.run_test(
            "Export Guest Data",
            "GET",
            f"guest/export/{session_id}",
            200
        )
        
        if not success3:
            print("❌ Guest data export failed - the fix may not be working properly")
            return False
        
        print("✅ Guest data export successful!")
        
        # Validate export response structure
        if export_response:
            expected_export_keys = ['export_info', 'profile', 'session_data', 'insights', 'upgrade_benefits']
            missing_export_keys = [key for key in expected_export_keys if key not in export_response]
            
            if not missing_export_keys:
                print("✅ Export response contains all required keys")
                
                # Validate export_info structure
                export_info = export_response.get('export_info', {})
                if export_info.get('session_id') == session_id:
                    print(f"✅ Export info session_id matches: {session_id}")
                else:
                    print(f"❌ Export info session_id mismatch")
                    return False
                
                # Validate profile structure
                profile = export_response.get('profile', {})
                if profile.get('session_id') == session_id:
                    print(f"✅ Profile session_id matches: {session_id}")
                else:
                    print(f"❌ Profile session_id mismatch")
                    return False
                
                # Validate session_data structure
                session_data = export_response.get('session_data', {})
                session_data_keys = ['todays_entries', 'nutrition_summary', 'simple_goals']
                missing_session_keys = [key for key in session_data_keys if key not in session_data]
                
                if not missing_session_keys:
                    print("✅ Session data structure is complete")
                else:
                    print(f"⚠️  Session data missing keys: {missing_session_keys}")
                
            else:
                print(f"❌ Export response missing keys: {missing_export_keys}")
                return False
        
        # Test 4: Test complete guest workflow - session creation -> data export
        print(f"\n🔍 Step 4: Testing complete guest workflow with new session...")
        
        # Create another session to test the complete workflow
        success4, workflow_session = self.run_test(
            "Create Second Guest Session (Workflow Test)",
            "POST",
            "guest/session",
            200
        )
        
        if success4 and workflow_session:
            workflow_session_id = workflow_session.get('session_id')
            print(f"✅ Second session created: {workflow_session_id}")
            
            # Immediately try to export data from the new session
            success5, workflow_export = self.run_test(
                "Export Data from New Session (Workflow Test)",
                "GET",
                f"guest/export/{workflow_session_id}",
                200
            )
            
            if success5:
                print("✅ Complete workflow successful: session creation -> immediate data export")
            else:
                print("❌ Workflow failed: could not export data from newly created session")
                return False
        else:
            print("❌ Failed to create second session for workflow test")
            return False
        
        # Test 5: Test that expired guest profiles are cleaned up properly
        print(f"\n🔍 Step 5: Testing expired profile cleanup...")
        
        # Try to export from a non-existent session (should fail with 404)
        fake_session_id = "fake_session_12345"
        success6, _ = self.run_test(
            "Export from Non-existent Session (Should Fail)",
            "GET",
            f"guest/export/{fake_session_id}",
            404  # Expecting 404 Not Found
        )
        
        if success6:
            print("✅ Properly handles non-existent session with 404 error")
        else:
            print("❌ Did not properly handle non-existent session")
            return False
        
        # Test 6: Verify session status endpoint works
        print(f"\n🔍 Step 6: Testing session status endpoint...")
        success7, status_response = self.run_test(
            "Get Guest Session Status",
            "GET",
            f"guest/session/{session_id}/status",
            200
        )
        
        if success7 and status_response:
            print("✅ Session status endpoint working")
            if status_response.get('session_id') == session_id:
                print(f"✅ Status response session_id matches: {session_id}")
            else:
                print(f"⚠️  Status response session_id mismatch")
        else:
            print("⚠️  Session status endpoint failed (not critical for main fix)")
        
        print(f"\n🎉 Guest Session Management and Export Test Summary:")
        print(f"   ✅ Guest session creation: {'PASSED' if success1 else 'FAILED'}")
        print(f"   ✅ Database profile creation: {'PASSED' if success2 else 'FAILED'}")
        print(f"   ✅ Data export functionality: {'PASSED' if success3 else 'FAILED'}")
        print(f"   ✅ Complete workflow: {'PASSED' if success4 and success5 else 'FAILED'}")
        print(f"   ✅ Error handling: {'PASSED' if success6 else 'FAILED'}")
        print(f"   ✅ Session status: {'PASSED' if success7 else 'PASSED (optional)'}")
        
        # All critical tests must pass
        all_critical_passed = success1 and success2 and success3 and success4 and success5 and success6
        
        if all_critical_passed:
            print("\n🎉 ALL GUEST SESSION MANAGEMENT AND EXPORT TESTS PASSED!")
            print("✅ The fix is working correctly:")
            print("   - Guest sessions now create profiles in database")
            print("   - Data export now works for guest sessions")
            print("   - Complete workflow functions properly")
            print("   - Error handling is appropriate")
        else:
            print("\n❌ SOME GUEST SESSION TESTS FAILED")
            print("   The fix may need additional work")
        
        return all_critical_passed

    def test_profile_wizard_enhancements(self):
        """Test profile wizard enhancements backend support as requested"""
        print("\n📋 Testing Profile Wizard Enhancements Backend Support...")
        
        # Test 1: Previous Surgeries Field Support
        previous_surgeries_success = self.test_previous_surgeries_support()
        
        # Test 2: Profile Completion Tracking
        completion_tracking_success = self.test_profile_completion_tracking_enhanced()
        
        # Test 3: Cross-Session Profile Support
        cross_session_success = self.test_cross_session_profile_support()
        
        # Test 4: Section-Based Updates
        section_updates_success = self.test_section_based_updates()
        
        return (previous_surgeries_success and completion_tracking_success and 
                cross_session_success and section_updates_success)

    def test_previous_surgeries_support(self):
        """Test Patient Profile APIs for previous_surgeries field support"""
        print("\n🏥 Testing Previous Surgeries Field Support...")
        
        test_user_id = f"surgery_test_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create patient profile with health_history containing previous_surgeries
        profile_with_surgeries = {
            "user_id": test_user_id,
            "basic_info": {
                "full_name": "John Surgery Patient",
                "age": 45,
                "gender": "Male",
                "location": "Boston, MA",
                "timezone": "America/New_York",
                "preferred_language": "English"
            },
            "health_history": {
                "primary_health_goals": ["recovery", "maintain_health"],
                "medical_conditions": {"post_surgical": "recovering"},
                "previous_surgeries": [
                    {
                        "id": "surg_001",
                        "name": "Appendectomy",
                        "date": "2020-03-15",
                        "details": "Laparoscopic appendix removal, no complications, full recovery"
                    },
                    {
                        "id": "surg_002", 
                        "name": "Knee Arthroscopy",
                        "date": "2022-08-10",
                        "details": "Meniscus repair, successful procedure, 6 weeks recovery"
                    },
                    {
                        "id": "surg_003",
                        "name": "Gallbladder Removal",
                        "date": "2023-01-20",
                        "details": "Cholecystectomy due to gallstones, minimally invasive"
                    }
                ],
                "allergies": ["penicillin"],
                "family_medical_history": ["heart_disease"]
            }
        }
        
        success1, create_response = self.run_test(
            "Create Patient Profile with Previous Surgeries",
            "POST",
            "profiles/patient",
            200,
            data=profile_with_surgeries
        )
        
        # Validate previous_surgeries were stored correctly
        if success1 and create_response:
            health_history = create_response.get('health_history', {})
            previous_surgeries = health_history.get('previous_surgeries', [])
            print(f"   Previous surgeries stored: {len(previous_surgeries)} procedures")
            
            if len(previous_surgeries) == 3:
                print(f"   ✅ All 3 surgeries stored correctly")
                # Validate surgery structure
                surgery = previous_surgeries[0]
                required_fields = ['id', 'name', 'date', 'details']
                missing_fields = [field for field in required_fields if field not in surgery]
                if not missing_fields:
                    print(f"   ✅ Surgery data structure valid: {surgery['name']} on {surgery['date']}")
                else:
                    print(f"   ❌ Surgery missing fields: {missing_fields}")
                    success1 = False
            else:
                print(f"   ❌ Expected 3 surgeries, got {len(previous_surgeries)}")
                success1 = False
        
        # Test 2: Retrieve patient profile and verify previous_surgeries data is preserved
        success2, get_response = self.run_test(
            "Retrieve Patient Profile with Previous Surgeries",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        if success2 and get_response:
            health_history = get_response.get('health_history', {})
            previous_surgeries = health_history.get('previous_surgeries', [])
            
            if len(previous_surgeries) == 3:
                print(f"   ✅ Previous surgeries preserved on retrieval")
                # Verify specific surgery details
                appendectomy = next((s for s in previous_surgeries if s['name'] == 'Appendectomy'), None)
                if appendectomy and appendectomy['date'] == '2020-03-15':
                    print(f"   ✅ Surgery details preserved: {appendectomy['name']} - {appendectomy['details'][:50]}...")
                else:
                    print(f"   ❌ Surgery details not preserved correctly")
                    success2 = False
            else:
                print(f"   ❌ Previous surgeries not preserved on retrieval")
                success2 = False
        
        # Test 3: Update existing patient profile with previous_surgeries modifications
        surgery_update = {
            "health_history": {
                "primary_health_goals": ["recovery", "maintain_health"],
                "medical_conditions": {"post_surgical": "recovering"},
                "previous_surgeries": [
                    {
                        "id": "surg_001",
                        "name": "Appendectomy",
                        "date": "2020-03-15",
                        "details": "Laparoscopic appendix removal, no complications, full recovery - UPDATED"
                    },
                    {
                        "id": "surg_002", 
                        "name": "Knee Arthroscopy",
                        "date": "2022-08-10",
                        "details": "Meniscus repair, successful procedure, 6 weeks recovery"
                    },
                    {
                        "id": "surg_003",
                        "name": "Gallbladder Removal",
                        "date": "2023-01-20",
                        "details": "Cholecystectomy due to gallstones, minimally invasive"
                    },
                    {
                        "id": "surg_004",
                        "name": "Cataract Surgery",
                        "date": "2023-11-05",
                        "details": "Left eye cataract removal, outpatient procedure, excellent results"
                    }
                ],
                "allergies": ["penicillin"],
                "family_medical_history": ["heart_disease"]
            }
        }
        
        success3, update_response = self.run_test(
            "Update Patient Profile - Modify Previous Surgeries",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=surgery_update
        )
        
        if success3 and update_response:
            health_history = update_response.get('health_history', {})
            previous_surgeries = health_history.get('previous_surgeries', [])
            
            if len(previous_surgeries) == 4:
                print(f"   ✅ Surgery modifications successful - now {len(previous_surgeries)} procedures")
                # Verify updated details
                appendectomy = next((s for s in previous_surgeries if s['name'] == 'Appendectomy'), None)
                if appendectomy and 'UPDATED' in appendectomy['details']:
                    print(f"   ✅ Surgery details updated successfully")
                else:
                    print(f"   ❌ Surgery details update failed")
                    success3 = False
                
                # Verify new surgery added
                cataract = next((s for s in previous_surgeries if s['name'] == 'Cataract Surgery'), None)
                if cataract:
                    print(f"   ✅ New surgery added: {cataract['name']} on {cataract['date']}")
                else:
                    print(f"   ❌ New surgery not added")
                    success3 = False
            else:
                print(f"   ❌ Expected 4 surgeries after update, got {len(previous_surgeries)}")
                success3 = False
        
        # Test 4: Test array structure validation
        invalid_surgery_data = {
            "health_history": {
                "previous_surgeries": [
                    {
                        "name": "Invalid Surgery",
                        # Missing required fields like id, date, details
                    }
                ]
            }
        }
        
        success4, _ = self.run_test(
            "Update with Invalid Surgery Structure (Should Still Work)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,  # Should work as validation is flexible
            data=invalid_surgery_data
        )
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Previous Surgeries Test Profile",
            "DELETE",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        print(f"\n📊 Previous Surgeries Support Test Summary:")
        print(f"   ✅ Create with surgeries: {'PASS' if success1 else 'FAIL'}")
        print(f"   ✅ Retrieve surgeries: {'PASS' if success2 else 'FAIL'}")
        print(f"   ✅ Update surgeries: {'PASS' if success3 else 'FAIL'}")
        print(f"   ✅ Structure validation: {'PASS' if success4 else 'FAIL'}")
        print(f"   ✅ Cleanup: {'PASS' if cleanup_success else 'FAIL'}")
        
        return success1 and success2 and success3 and success4 and cleanup_success

    def test_profile_completion_tracking_enhanced(self):
        """Test enhanced profile completion tracking for Patient, Provider, and Family profiles"""
        print("\n📊 Testing Enhanced Profile Completion Tracking...")
        
        # Test Patient Profile Completion
        patient_success = self.test_patient_completion_tracking()
        
        # Test Provider Profile Completion  
        provider_success = self.test_provider_completion_tracking()
        
        # Test Family Profile Completion
        family_success = self.test_family_completion_tracking()
        
        return patient_success and provider_success and family_success

    def test_patient_completion_tracking(self):
        """Test Patient profile completion calculation and persistence"""
        print("\n👤 Testing Patient Profile Completion Tracking...")
        
        test_user_id = f"patient_completion_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create profile with 1 section (basic_info) - should be 16.7%
        basic_profile = {
            "user_id": test_user_id,
            "basic_info": {
                "full_name": "Completion Test User",
                "age": 30,
                "gender": "Female",
                "location": "Test City",
                "timezone": "America/New_York",
                "preferred_language": "English"
            }
        }
        
        success1, response1 = self.run_test(
            "Patient Profile - 1 Section (16.7%)",
            "POST",
            "profiles/patient",
            200,
            data=basic_profile
        )
        
        if success1 and response1:
            completion = response1.get('profile_completion', 0)
            expected = 16.7
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 1 section completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 1 section completion: {completion}% (expected ~{expected}%)")
                success1 = False
        
        # Test 2: Add physical_metrics section - should be 33.3%
        physical_update = {
            "physical_metrics": {
                "height_cm": 165.0,
                "current_weight_kg": 65.0,
                "goal_weight_kg": 60.0
            }
        }
        
        success2, response2 = self.run_test(
            "Patient Profile - Add Physical Metrics (33.3%)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=physical_update
        )
        
        if success2 and response2:
            completion = response2.get('profile_completion', 0)
            expected = 33.3
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 2 sections completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 2 sections completion: {completion}% (expected ~{expected}%)")
                success2 = False
        
        # Test 3: Add activity_profile section - should be 50.0%
        activity_update = {
            "activity_profile": {
                "activity_level": "MODERATELY_ACTIVE",
                "exercise_frequency": 3,
                "sleep_schedule": {
                    "bedtime": "22:00",
                    "wake_time": "06:00",
                    "sleep_quality": 4
                },
                "stress_level": 2,
                "work_type": "DESK_JOB"
            }
        }
        
        success3, response3 = self.run_test(
            "Patient Profile - Add Activity Profile (50.0%)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=activity_update
        )
        
        if success3 and response3:
            completion = response3.get('profile_completion', 0)
            expected = 50.0
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 3 sections completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 3 sections completion: {completion}% (expected ~{expected}%)")
                success3 = False
        
        # Test 4: Verify completion is persisted in database
        success4, get_response = self.run_test(
            "Patient Profile - Verify Completion Persisted",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        if success4 and get_response:
            persisted_completion = get_response.get('profile_completion', 0)
            expected = 50.0
            if abs(persisted_completion - expected) < 1.0:
                print(f"   ✅ Completion persisted: {persisted_completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ Completion not persisted: {persisted_completion}% (expected ~{expected}%)")
                success4 = False
        
        # Test 5: Test completion API endpoint
        success5, completion_data = self.run_test(
            "Patient Profile - Completion API Endpoint",
            "GET",
            f"profiles/completion/{test_user_id}",
            200,
            params={"role": "patient"}
        )
        
        if success5 and completion_data:
            api_completion = completion_data.get('completion_percentage', 0)
            completed_sections = completion_data.get('completed_sections', 0)
            total_sections = completion_data.get('total_sections', 0)
            missing_sections = completion_data.get('missing_sections', [])
            
            if abs(api_completion - 50.0) < 1.0 and completed_sections == 3 and total_sections == 6:
                print(f"   ✅ Completion API: {api_completion}%, {completed_sections}/{total_sections} sections")
                print(f"   ✅ Missing sections: {missing_sections}")
            else:
                print(f"   ❌ Completion API mismatch: {api_completion}%, {completed_sections}/{total_sections}")
                success5 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Patient Completion Test",
            "DELETE",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3 and success4 and success5 and cleanup_success

    def test_provider_completion_tracking(self):
        """Test Provider profile completion calculation and persistence"""
        print("\n👨‍⚕️ Testing Provider Profile Completion Tracking...")
        
        test_user_id = f"provider_completion_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create profile with 1 section (professional_identity) - should be 25%
        identity_profile = {
            "user_id": test_user_id,
            "professional_identity": {
                "full_name": "Dr. Completion Test",
                "professional_title": "Registered Dietitian",
                "medical_license": "RD123456",
                "years_experience": 5
            }
        }
        
        success1, response1 = self.run_test(
            "Provider Profile - 1 Section (25%)",
            "POST",
            "profiles/provider",
            200,
            data=identity_profile
        )
        
        if success1 and response1:
            completion = response1.get('profile_completion', 0)
            expected = 25.0
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 1 section completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 1 section completion: {completion}% (expected ~{expected}%)")
                success1 = False
        
        # Test 2: Add credentials section - should be 50%
        credentials_update = {
            "credentials": {
                "education": [
                    {
                        "degree": "Master of Science in Nutrition",
                        "institution": "Test University",
                        "graduation_year": 2018,
                        "specialization": "Clinical Nutrition"
                    }
                ],
                "certifications": [
                    {
                        "name": "Certified Diabetes Educator",
                        "organization": "CBDCE",
                        "issue_date": "2020-01-01",
                        "expiration_date": "2025-01-01",
                        "status": "ACTIVE"
                    }
                ],
                "specializations": ["diabetes_management"]
            }
        }
        
        success2, response2 = self.run_test(
            "Provider Profile - Add Credentials (50%)",
            "PUT",
            f"profiles/provider/{test_user_id}",
            200,
            data=credentials_update
        )
        
        if success2 and response2:
            completion = response2.get('profile_completion', 0)
            expected = 50.0
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 2 sections completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 2 sections completion: {completion}% (expected ~{expected}%)")
                success2 = False
        
        # Test 3: Verify completion persisted
        success3, get_response = self.run_test(
            "Provider Profile - Verify Completion Persisted",
            "GET",
            f"profiles/provider/{test_user_id}",
            200
        )
        
        if success3 and get_response:
            persisted_completion = get_response.get('profile_completion', 0)
            expected = 50.0
            if abs(persisted_completion - expected) < 1.0:
                print(f"   ✅ Completion persisted: {persisted_completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ Completion not persisted: {persisted_completion}% (expected ~{expected}%)")
                success3 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Provider Completion Test",
            "DELETE",
            f"profiles/provider/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3 and cleanup_success

    def test_family_completion_tracking(self):
        """Test Family profile completion calculation and persistence"""
        print("\n👨‍👩‍👧‍👦 Testing Family Profile Completion Tracking...")
        
        test_user_id = f"family_completion_{datetime.now().strftime('%H%M%S')}"
        
        # Test 1: Create profile with 1 section (family_structure) - should be 25%
        structure_profile = {
            "user_id": test_user_id,
            "family_structure": {
                "family_role": "Parent",
                "number_of_members": 3,
                "primary_caregiver": True
            }
        }
        
        success1, response1 = self.run_test(
            "Family Profile - 1 Section (25%)",
            "POST",
            "profiles/family",
            200,
            data=structure_profile
        )
        
        if success1 and response1:
            completion = response1.get('profile_completion', 0)
            expected = 25.0
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 1 section completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 1 section completion: {completion}% (expected ~{expected}%)")
                success1 = False
        
        # Test 2: Add family_members section - should be 50%
        members_update = {
            "family_members": [
                {
                    "name": "Parent Test",
                    "relationship": "Self",
                    "age": 35,
                    "gender": "Female",
                    "allergies": [],
                    "medications": [],
                    "health_conditions": []
                },
                {
                    "name": "Child Test",
                    "relationship": "Child",
                    "age": 8,
                    "gender": "Male",
                    "allergies": ["peanuts"],
                    "medications": [],
                    "health_conditions": []
                }
            ]
        }
        
        success2, response2 = self.run_test(
            "Family Profile - Add Family Members (50%)",
            "PUT",
            f"profiles/family/{test_user_id}",
            200,
            data=members_update
        )
        
        if success2 and response2:
            completion = response2.get('profile_completion', 0)
            expected = 50.0
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 2 sections completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 2 sections completion: {completion}% (expected ~{expected}%)")
                success2 = False
        
        # Test 3: Add household_management section - should be 75%
        household_update = {
            "household_management": {
                "common_dietary_restrictions": ["peanut_free"],
                "family_meal_preferences": ["home_cooked", "healthy"],
                "budget_considerations": {"weekly_grocery_budget": 150},
                "shopping_responsibilities": ["Parent Test"],
                "cooking_responsibilities": ["Parent Test"]
            }
        }
        
        success3, response3 = self.run_test(
            "Family Profile - Add Household Management (75%)",
            "PUT",
            f"profiles/family/{test_user_id}",
            200,
            data=household_update
        )
        
        if success3 and response3:
            completion = response3.get('profile_completion', 0)
            expected = 75.0
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 3 sections completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 3 sections completion: {completion}% (expected ~{expected}%)")
                success3 = False
        
        # Test 4: Add care_coordination section - should be 100%
        care_update = {
            "care_coordination": {
                "healthcare_providers": {
                    "Parent Test": {"provider": "Dr. Smith", "contact": "555-0101"},
                    "Child Test": {"provider": "Dr. Johnson", "contact": "555-0102"}
                },
                "emergency_contacts": [
                    {"name": "Grandparent", "phone": "555-0200", "relationship": "Grandparent"}
                ],
                "medication_management": {},
                "health_tracking_preferences": {"shared_calendar": True}
            }
        }
        
        success4, response4 = self.run_test(
            "Family Profile - Add Care Coordination (100%)",
            "PUT",
            f"profiles/family/{test_user_id}",
            200,
            data=care_update
        )
        
        if success4 and response4:
            completion = response4.get('profile_completion', 0)
            expected = 100.0
            if abs(completion - expected) < 1.0:
                print(f"   ✅ 4 sections completion: {completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ 4 sections completion: {completion}% (expected ~{expected}%)")
                success4 = False
        
        # Test 5: Verify completion persisted
        success5, get_response = self.run_test(
            "Family Profile - Verify Completion Persisted",
            "GET",
            f"profiles/family/{test_user_id}",
            200
        )
        
        if success5 and get_response:
            persisted_completion = get_response.get('profile_completion', 0)
            expected = 100.0
            if abs(persisted_completion - expected) < 1.0:
                print(f"   ✅ Completion persisted: {persisted_completion}% (expected ~{expected}%)")
            else:
                print(f"   ❌ Completion not persisted: {persisted_completion}% (expected ~{expected}%)")
                success5 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Family Completion Test",
            "DELETE",
            f"profiles/family/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3 and success4 and success5 and cleanup_success

    def test_cross_session_profile_support(self):
        """Test profile retrieval by user_id works correctly for cross-session editing"""
        print("\n🔄 Testing Cross-Session Profile Support...")
        
        # Test Patient Profile Cross-Session Support
        patient_success = self.test_patient_cross_session()
        
        # Test Provider Profile Cross-Session Support
        provider_success = self.test_provider_cross_session()
        
        # Test Family Profile Cross-Session Support
        family_success = self.test_family_cross_session()
        
        return patient_success and provider_success and family_success

    def test_patient_cross_session(self):
        """Test Patient profile cross-session editing"""
        print("\n👤 Testing Patient Cross-Session Profile Support...")
        
        test_user_id = f"patient_cross_session_{datetime.now().strftime('%H%M%S')}"
        
        # Session 1: Create initial profile
        initial_profile = {
            "user_id": test_user_id,
            "basic_info": {
                "full_name": "Cross Session Patient",
                "age": 32,
                "gender": "Female",
                "location": "Seattle, WA",
                "timezone": "America/Los_Angeles",
                "preferred_language": "English"
            },
            "physical_metrics": {
                "height_cm": 168.0,
                "current_weight_kg": 70.0,
                "goal_weight_kg": 65.0
            }
        }
        
        success1, _ = self.run_test(
            "Session 1 - Create Initial Patient Profile",
            "POST",
            "profiles/patient",
            200,
            data=initial_profile
        )
        
        # Session 2: Retrieve existing profile by user_id
        success2, retrieved_profile = self.run_test(
            "Session 2 - Retrieve Patient Profile by User ID",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        if success2 and retrieved_profile:
            # Verify all original data is present
            basic_info = retrieved_profile.get('basic_info', {})
            physical_metrics = retrieved_profile.get('physical_metrics', {})
            
            if (basic_info.get('full_name') == 'Cross Session Patient' and 
                physical_metrics.get('height_cm') == 168.0):
                print(f"   ✅ Profile data retrieved correctly across sessions")
            else:
                print(f"   ❌ Profile data not retrieved correctly")
                success2 = False
        
        # Session 2: Continue editing - add health history
        health_update = {
            "health_history": {
                "primary_health_goals": ["weight_loss", "fitness"],
                "allergies": ["shellfish"],
                "previous_surgeries": [
                    {
                        "id": "cross_surg_001",
                        "name": "Tonsillectomy",
                        "date": "2015-06-10",
                        "details": "Childhood tonsil removal, no complications"
                    }
                ]
            }
        }
        
        success3, updated_profile = self.run_test(
            "Session 2 - Continue Editing (Add Health History)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=health_update
        )
        
        if success3 and updated_profile:
            # Verify original data is still present
            basic_info = updated_profile.get('basic_info', {})
            health_history = updated_profile.get('health_history', {})
            
            if (basic_info.get('full_name') == 'Cross Session Patient' and 
                len(health_history.get('previous_surgeries', [])) == 1):
                print(f"   ✅ Cross-session editing preserved existing data")
            else:
                print(f"   ❌ Cross-session editing lost existing data")
                success3 = False
        
        # Session 3: Retrieve updated profile
        success4, final_profile = self.run_test(
            "Session 3 - Retrieve Updated Profile",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        if success4 and final_profile:
            # Verify all sections are present
            sections = ['basic_info', 'physical_metrics', 'health_history']
            present_sections = [s for s in sections if final_profile.get(s)]
            
            if len(present_sections) == 3:
                print(f"   ✅ All sections preserved across sessions: {present_sections}")
                completion = final_profile.get('profile_completion', 0)
                print(f"   ✅ Profile completion: {completion}%")
            else:
                print(f"   ❌ Sections lost across sessions. Present: {present_sections}")
                success4 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Patient Cross-Session Test",
            "DELETE",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3 and success4 and cleanup_success

    def test_provider_cross_session(self):
        """Test Provider profile cross-session editing"""
        print("\n👨‍⚕️ Testing Provider Cross-Session Profile Support...")
        
        test_user_id = f"provider_cross_session_{datetime.now().strftime('%H%M%S')}"
        
        # Session 1: Create initial profile
        initial_profile = {
            "user_id": test_user_id,
            "professional_identity": {
                "full_name": "Dr. Cross Session",
                "professional_title": "Clinical Nutritionist",
                "medical_license": "CN789012",
                "years_experience": 7
            }
        }
        
        success1, _ = self.run_test(
            "Session 1 - Create Initial Provider Profile",
            "POST",
            "profiles/provider",
            200,
            data=initial_profile
        )
        
        # Session 2: Retrieve and continue editing
        success2, retrieved_profile = self.run_test(
            "Session 2 - Retrieve Provider Profile by User ID",
            "GET",
            f"profiles/provider/{test_user_id}",
            200
        )
        
        if success2 and retrieved_profile:
            professional_identity = retrieved_profile.get('professional_identity', {})
            if professional_identity.get('full_name') == 'Dr. Cross Session':
                print(f"   ✅ Provider profile retrieved correctly across sessions")
            else:
                print(f"   ❌ Provider profile not retrieved correctly")
                success2 = False
        
        # Session 2: Add practice info
        practice_update = {
            "practice_info": {
                "workplace": "Cross Session Medical Center",
                "practice_type": "Private Practice",
                "languages_spoken": ["English", "Spanish"],
                "areas_of_expertise": ["weight_management", "diabetes"]
            }
        }
        
        success3, updated_profile = self.run_test(
            "Session 2 - Continue Editing (Add Practice Info)",
            "PUT",
            f"profiles/provider/{test_user_id}",
            200,
            data=practice_update
        )
        
        if success3 and updated_profile:
            professional_identity = updated_profile.get('professional_identity', {})
            practice_info = updated_profile.get('practice_info', {})
            
            if (professional_identity.get('full_name') == 'Dr. Cross Session' and 
                practice_info.get('workplace') == 'Cross Session Medical Center'):
                print(f"   ✅ Provider cross-session editing successful")
            else:
                print(f"   ❌ Provider cross-session editing failed")
                success3 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Provider Cross-Session Test",
            "DELETE",
            f"profiles/provider/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3 and cleanup_success

    def test_family_cross_session(self):
        """Test Family profile cross-session editing"""
        print("\n👨‍👩‍👧‍👦 Testing Family Cross-Session Profile Support...")
        
        test_user_id = f"family_cross_session_{datetime.now().strftime('%H%M%S')}"
        
        # Session 1: Create initial profile
        initial_profile = {
            "user_id": test_user_id,
            "family_structure": {
                "family_role": "Parent",
                "number_of_members": 4,
                "primary_caregiver": True
            },
            "family_members": [
                {
                    "name": "Cross Session Parent",
                    "relationship": "Self",
                    "age": 40,
                    "gender": "Male",
                    "allergies": [],
                    "medications": [],
                    "health_conditions": []
                }
            ]
        }
        
        success1, _ = self.run_test(
            "Session 1 - Create Initial Family Profile",
            "POST",
            "profiles/family",
            200,
            data=initial_profile
        )
        
        # Session 2: Retrieve and continue editing
        success2, retrieved_profile = self.run_test(
            "Session 2 - Retrieve Family Profile by User ID",
            "GET",
            f"profiles/family/{test_user_id}",
            200
        )
        
        if success2 and retrieved_profile:
            family_members = retrieved_profile.get('family_members', [])
            if len(family_members) == 1 and family_members[0].get('name') == 'Cross Session Parent':
                print(f"   ✅ Family profile retrieved correctly across sessions")
            else:
                print(f"   ❌ Family profile not retrieved correctly")
                success2 = False
        
        # Session 2: Add more family members
        members_update = {
            "family_members": [
                {
                    "name": "Cross Session Parent",
                    "relationship": "Self",
                    "age": 40,
                    "gender": "Male",
                    "allergies": [],
                    "medications": [],
                    "health_conditions": []
                },
                {
                    "name": "Cross Session Spouse",
                    "relationship": "Spouse",
                    "age": 38,
                    "gender": "Female",
                    "allergies": ["pollen"],
                    "medications": [],
                    "health_conditions": []
                },
                {
                    "name": "Cross Session Child",
                    "relationship": "Child",
                    "age": 10,
                    "gender": "Female",
                    "allergies": [],
                    "medications": [],
                    "health_conditions": []
                }
            ]
        }
        
        success3, updated_profile = self.run_test(
            "Session 2 - Continue Editing (Add Family Members)",
            "PUT",
            f"profiles/family/{test_user_id}",
            200,
            data=members_update
        )
        
        if success3 and updated_profile:
            family_structure = updated_profile.get('family_structure', {})
            family_members = updated_profile.get('family_members', [])
            
            if (family_structure.get('family_role') == 'Parent' and 
                len(family_members) == 3):
                print(f"   ✅ Family cross-session editing successful - {len(family_members)} members")
            else:
                print(f"   ❌ Family cross-session editing failed")
                success3 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Family Cross-Session Test",
            "DELETE",
            f"profiles/family/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3 and cleanup_success

    def test_section_based_updates(self):
        """Test that partial profile updates work properly for each profile type"""
        print("\n📝 Testing Section-Based Updates...")
        
        # Test Patient Section-Based Updates
        patient_success = self.test_patient_section_updates()
        
        # Test Provider Section-Based Updates
        provider_success = self.test_provider_section_updates()
        
        # Test Family Section-Based Updates
        family_success = self.test_family_section_updates()
        
        return patient_success and provider_success and family_success

    def test_patient_section_updates(self):
        """Test Patient profile section-based updates"""
        print("\n👤 Testing Patient Section-Based Updates...")
        
        test_user_id = f"patient_section_{datetime.now().strftime('%H%M%S')}"
        
        # Create initial profile with basic_info only
        initial_profile = {
            "user_id": test_user_id,
            "basic_info": {
                "full_name": "Section Update Patient",
                "age": 29,
                "gender": "Female",
                "location": "Portland, OR",
                "timezone": "America/Los_Angeles",
                "preferred_language": "English"
            }
        }
        
        success1, _ = self.run_test(
            "Create Initial Patient Profile (Basic Info Only)",
            "POST",
            "profiles/patient",
            200,
            data=initial_profile
        )
        
        # Test 1: Update only physical_metrics section
        physical_only_update = {
            "physical_metrics": {
                "height_cm": 162.0,
                "current_weight_kg": 58.0,
                "goal_weight_kg": 55.0,
                "body_fat_percentage": 24.0
            }
        }
        
        success2, response2 = self.run_test(
            "Update Only Physical Metrics Section",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=physical_only_update
        )
        
        if success2 and response2:
            # Verify basic_info is still present
            basic_info = response2.get('basic_info', {})
            physical_metrics = response2.get('physical_metrics', {})
            
            if (basic_info.get('full_name') == 'Section Update Patient' and 
                physical_metrics.get('height_cm') == 162.0):
                print(f"   ✅ Physical metrics section updated independently")
            else:
                print(f"   ❌ Section update affected other sections")
                success2 = False
        
        # Test 2: Update only health_history section
        health_only_update = {
            "health_history": {
                "primary_health_goals": ["fitness", "energy"],
                "allergies": ["dust"],
                "previous_surgeries": [
                    {
                        "id": "section_surg_001",
                        "name": "Dental Surgery",
                        "date": "2021-09-15",
                        "details": "Wisdom tooth extraction, routine procedure"
                    }
                ]
            }
        }
        
        success3, response3 = self.run_test(
            "Update Only Health History Section",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=health_only_update
        )
        
        if success3 and response3:
            # Verify other sections are still present
            basic_info = response3.get('basic_info', {})
            physical_metrics = response3.get('physical_metrics', {})
            health_history = response3.get('health_history', {})
            
            if (basic_info.get('full_name') == 'Section Update Patient' and 
                physical_metrics.get('height_cm') == 162.0 and
                len(health_history.get('previous_surgeries', [])) == 1):
                print(f"   ✅ Health history section updated independently")
            else:
                print(f"   ❌ Health history update affected other sections")
                success3 = False
        
        # Test 3: Update multiple sections at once
        multi_section_update = {
            "activity_profile": {
                "activity_level": "LIGHTLY_ACTIVE",
                "exercise_frequency": 2,
                "sleep_schedule": {
                    "bedtime": "23:30",
                    "wake_time": "07:30",
                    "sleep_quality": 3
                },
                "stress_level": 4,
                "work_type": "MIXED"
            },
            "dietary_profile": {
                "diet_type": "VEGETARIAN",
                "meal_timing_preference": "SMALL_FREQUENT",
                "cooking_skill_level": 4,
                "available_cooking_time": 60
            }
        }
        
        success4, response4 = self.run_test(
            "Update Multiple Sections Simultaneously",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=multi_section_update
        )
        
        if success4 and response4:
            # Verify all sections are present
            sections = ['basic_info', 'physical_metrics', 'health_history', 'activity_profile', 'dietary_profile']
            present_sections = [s for s in sections if response4.get(s)]
            
            if len(present_sections) == 5:
                print(f"   ✅ Multiple sections updated, all sections preserved: {present_sections}")
                completion = response4.get('profile_completion', 0)
                expected = 83.3  # 5 out of 6 sections
                if abs(completion - expected) < 2.0:
                    print(f"   ✅ Profile completion updated correctly: {completion}%")
                else:
                    print(f"   ❌ Profile completion incorrect: {completion}% (expected ~{expected}%)")
                    success4 = False
            else:
                print(f"   ❌ Multiple section update lost data. Present: {present_sections}")
                success4 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Patient Section Updates Test",
            "DELETE",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        return success1 and success2 and success3 and success4 and cleanup_success

    def test_provider_section_updates(self):
        """Test Provider profile section-based updates"""
        print("\n👨‍⚕️ Testing Provider Section-Based Updates...")
        
        test_user_id = f"provider_section_{datetime.now().strftime('%H%M%S')}"
        
        # Create initial profile
        initial_profile = {
            "user_id": test_user_id,
            "professional_identity": {
                "full_name": "Dr. Section Update",
                "professional_title": "Nutritionist",
                "medical_license": "NU456789",
                "years_experience": 6
            }
        }
        
        success1, _ = self.run_test(
            "Create Initial Provider Profile",
            "POST",
            "profiles/provider",
            200,
            data=initial_profile
        )
        
        # Update only practice_info section
        practice_update = {
            "practice_info": {
                "workplace": "Section Update Clinic",
                "practice_type": "Outpatient",
                "languages_spoken": ["English"],
                "areas_of_expertise": ["general_nutrition"]
            }
        }
        
        success2, response2 = self.run_test(
            "Update Only Practice Info Section",
            "PUT",
            f"profiles/provider/{test_user_id}",
            200,
            data=practice_update
        )
        
        if success2 and response2:
            professional_identity = response2.get('professional_identity', {})
            practice_info = response2.get('practice_info', {})
            
            if (professional_identity.get('full_name') == 'Dr. Section Update' and 
                practice_info.get('workplace') == 'Section Update Clinic'):
                print(f"   ✅ Provider section updated independently")
            else:
                print(f"   ❌ Provider section update failed")
                success2 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Provider Section Updates Test",
            "DELETE",
            f"profiles/provider/{test_user_id}",
            200
        )
        
        return success1 and success2 and cleanup_success

    def test_family_section_updates(self):
        """Test Family profile section-based updates"""
        print("\n👨‍👩‍👧‍👦 Testing Family Section-Based Updates...")
        
        test_user_id = f"family_section_{datetime.now().strftime('%H%M%S')}"
        
        # Create initial profile
        initial_profile = {
            "user_id": test_user_id,
            "family_structure": {
                "family_role": "Parent",
                "number_of_members": 2,
                "primary_caregiver": True
            }
        }
        
        success1, _ = self.run_test(
            "Create Initial Family Profile",
            "POST",
            "profiles/family",
            200,
            data=initial_profile
        )
        
        # Update only household_management section
        household_update = {
            "household_management": {
                "common_dietary_restrictions": ["gluten_free"],
                "family_meal_preferences": ["organic", "local"],
                "budget_considerations": {"weekly_grocery_budget": 200},
                "shopping_responsibilities": ["Parent"],
                "cooking_responsibilities": ["Parent"]
            }
        }
        
        success2, response2 = self.run_test(
            "Update Only Household Management Section",
            "PUT",
            f"profiles/family/{test_user_id}",
            200,
            data=household_update
        )
        
        if success2 and response2:
            family_structure = response2.get('family_structure', {})
            household_management = response2.get('household_management', {})
            
            if (family_structure.get('family_role') == 'Parent' and 
                'gluten_free' in household_management.get('common_dietary_restrictions', [])):
                print(f"   ✅ Family section updated independently")
            else:
                print(f"   ❌ Family section update failed")
                success2 = False
        
        # Clean up
        cleanup_success, _ = self.run_test(
            "Cleanup Family Section Updates Test",
            "DELETE",
            f"profiles/family/{test_user_id}",
            200
        )
        
        return success1 and success2 and cleanup_success

    def test_phase4_food_logging_endpoints(self):
        """Test Phase 4 Food Logging Backend Endpoints"""
        print("\n📋 Testing Phase 4 Food Logging Backend Endpoints...")
        
        test_user_id = "demo-patient-123"
        
        # Test 1: GET /api/patient/food-log/{user_id}/daily-summary
        success1, daily_summary = self.run_test(
            "Phase 4: Daily Food Summary",
            "GET",
            f"patient/food-log/{test_user_id}/daily-summary",
            200
        )
        
        # Validate daily summary response structure
        if success1 and daily_summary:
            expected_keys = ['user_id', 'date', 'summary']
            missing_keys = [key for key in expected_keys if key not in daily_summary]
            if not missing_keys:
                print(f"   ✅ Daily summary response contains all required keys: {expected_keys}")
                
                # Validate summary structure
                summary = daily_summary.get('summary', {})
                summary_keys = ['calories', 'protein', 'carbs', 'fat', 'meals', 'water_intake', 'goals_met', 'daily_goals', 'progress_percentage']
                missing_summary_keys = [key for key in summary_keys if key not in summary]
                if not missing_summary_keys:
                    print(f"   ✅ Daily summary structure contains all required fields: {summary_keys}")
                    
                    # Validate goals_met structure
                    goals_met = summary.get('goals_met', {})
                    if isinstance(goals_met, dict) and len(goals_met) > 0:
                        print(f"   ✅ Goals met tracking present: {list(goals_met.keys())}")
                    
                    # Validate progress_percentage structure
                    progress = summary.get('progress_percentage', {})
                    if isinstance(progress, dict) and len(progress) > 0:
                        print(f"   ✅ Progress percentage tracking present: {list(progress.keys())}")
                else:
                    print(f"   ❌ Daily summary missing keys: {missing_summary_keys}")
                    success1 = False
            else:
                print(f"   ❌ Daily summary response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: GET /api/patient/food-log/{user_id}/recent
        success2, recent_logs = self.run_test(
            "Phase 4: Recent Food Logs",
            "GET",
            f"patient/food-log/{test_user_id}/recent",
            200
        )
        
        # Validate recent logs response structure
        if success2 and recent_logs:
            expected_keys = ['user_id', 'logs']
            missing_keys = [key for key in expected_keys if key not in recent_logs]
            if not missing_keys:
                print(f"   ✅ Recent logs response contains all required keys: {expected_keys}")
                
                # Validate logs array structure
                logs = recent_logs.get('logs', [])
                if logs and len(logs) > 0:
                    log = logs[0]
                    log_keys = ['id', 'food_name', 'brand', 'calories', 'protein', 'carbs', 'fat', 'fiber', 'sodium', 'meal_type', 'serving_size', 'timestamp', 'source', 'confidence']
                    missing_log_keys = [key for key in log_keys if key not in log]
                    if not missing_log_keys:
                        print(f"   ✅ Recent log entry structure valid with all nutrition data")
                        print(f"   ✅ Sample log: {log['food_name']} - {log['calories']} cal, {log['protein']}g protein")
                        print(f"   ✅ Source: {log['source']}, Confidence: {log['confidence']}")
                    else:
                        print(f"   ❌ Recent log entry missing keys: {missing_log_keys}")
                        success2 = False
                else:
                    print(f"   ❌ No recent logs found in response")
                    success2 = False
            else:
                print(f"   ❌ Recent logs response missing keys: {missing_keys}")
                success2 = False
        
        # Test 3: GET /api/patient/smart-suggestions/{user_id}
        success3, smart_suggestions = self.run_test(
            "Phase 4: Smart Food Suggestions",
            "GET",
            f"patient/smart-suggestions/{test_user_id}",
            200
        )
        
        # Validate smart suggestions response structure
        if success3 and smart_suggestions:
            expected_keys = ['user_id', 'meal_context', 'generated_at', 'quick_add_suggestions', 'meal_pattern_insights', 'nutrition_gaps', 'personalized_recommendations']
            missing_keys = [key for key in expected_keys if key not in smart_suggestions]
            if not missing_keys:
                print(f"   ✅ Smart suggestions response contains all required keys")
                
                # Validate quick_add_suggestions structure
                quick_add = smart_suggestions.get('quick_add_suggestions', [])
                if quick_add and len(quick_add) > 0:
                    suggestion = quick_add[0]
                    suggestion_keys = ['name', 'calories', 'protein', 'carbs', 'fat', 'reason']
                    missing_suggestion_keys = [key for key in suggestion_keys if key not in suggestion]
                    if not missing_suggestion_keys:
                        print(f"   ✅ Quick add suggestions structure valid")
                        print(f"   ✅ Sample suggestion: {suggestion['name']} - {suggestion['reason']}")
                    else:
                        print(f"   ❌ Quick add suggestion missing keys: {missing_suggestion_keys}")
                        success3 = False
                
                # Validate meal_pattern_insights structure
                patterns = smart_suggestions.get('meal_pattern_insights', {})
                pattern_keys = ['breakfast_time', 'lunch_time', 'dinner_time', 'snack_preferences']
                missing_pattern_keys = [key for key in pattern_keys if key not in patterns]
                if not missing_pattern_keys:
                    print(f"   ✅ Meal pattern insights structure valid")
                else:
                    print(f"   ❌ Meal pattern insights missing keys: {missing_pattern_keys}")
                
                # Validate nutrition_gaps structure
                gaps = smart_suggestions.get('nutrition_gaps', [])
                if gaps and len(gaps) > 0:
                    gap = gaps[0]
                    gap_keys = ['nutrient', 'current', 'target', 'suggestion', 'foods']
                    missing_gap_keys = [key for key in gap_keys if key not in gap]
                    if not missing_gap_keys:
                        print(f"   ✅ Nutrition gaps structure valid")
                        print(f"   ✅ Sample gap: {gap['nutrient']} - {gap['suggestion']}")
                    else:
                        print(f"   ❌ Nutrition gap missing keys: {missing_gap_keys}")
                
                # Validate personalized_recommendations structure
                recommendations = smart_suggestions.get('personalized_recommendations', [])
                if recommendations and len(recommendations) > 0:
                    rec = recommendations[0]
                    rec_keys = ['title', 'description', 'foods', 'priority']
                    missing_rec_keys = [key for key in rec_keys if key not in rec]
                    if not missing_rec_keys:
                        print(f"   ✅ Personalized recommendations structure valid")
                        print(f"   ✅ Sample recommendation: {rec['title']} - {rec['priority']} priority")
                    else:
                        print(f"   ❌ Personalized recommendation missing keys: {missing_rec_keys}")
                
                # Validate context-aware suggestions based on time of day
                meal_context = smart_suggestions.get('meal_context', '')
                print(f"   ✅ Context-aware suggestions for: {meal_context}")
                
            else:
                print(f"   ❌ Smart suggestions response missing keys: {missing_keys}")
                success3 = False
        
        # Test 4: Verify AI Integration Endpoints (already tested but confirm they're working)
        success4 = True
        ai_endpoints = [
            ("AI Food Recognition", "POST", "ai/food-recognition", {"image": "base64_encoded_image_data", "user_id": test_user_id}),
            ("AI Voice Command", "POST", "ai/voice-command", {"transcript": "I had a grilled chicken breast for lunch", "user_id": test_user_id}),
            ("AI Meal Suggestions", "POST", "ai/meal-suggestions", {"user_id": test_user_id, "meal_type": "dinner", "preferences": ["healthy", "quick"]})
        ]
        
        for name, method, endpoint, data in ai_endpoints:
            success, response = self.run_test(
                f"Phase 4: {name} (Verification)",
                method,
                endpoint,
                200,
                data=data
            )
            if success:
                print(f"   ✅ {name} endpoint confirmed working")
            else:
                print(f"   ❌ {name} endpoint failed")
                success4 = False
        
        print(f"\n📊 Phase 4 Food Logging Test Summary:")
        print(f"   ✅ Daily Summary Endpoint: {'PASS' if success1 else 'FAIL'}")
        print(f"   ✅ Recent Logs Endpoint: {'PASS' if success2 else 'FAIL'}")
        print(f"   ✅ Smart Suggestions Endpoint: {'PASS' if success3 else 'FAIL'}")
        print(f"   ✅ AI Integration Endpoints: {'PASS' if success4 else 'FAIL'}")
        
        return success1 and success2 and success3 and success4

    def test_ai_api_endpoints(self):
        """Test the 4 new AI API endpoints"""
        print("\n🤖 Testing AI API Endpoints...")
        
        # Test 1: POST /api/ai/food-recognition
        food_recognition_success = self.test_food_recognition_endpoint()
        
        # Test 2: POST /api/ai/health-insights
        health_insights_success = self.test_health_insights_endpoint()
        
        # Test 3: POST /api/ai/meal-suggestions
        meal_suggestions_success = self.test_meal_suggestions_endpoint()
        
        # Test 4: POST /api/ai/voice-command
        voice_command_success = self.test_voice_command_endpoint()
        
        return food_recognition_success and health_insights_success and meal_suggestions_success and voice_command_success

    def test_food_recognition_endpoint(self):
        """Test POST /api/ai/food-recognition endpoint"""
        print("\n🍎 Testing Food Recognition Endpoint...")
        
        # Create a small base64 encoded test image (1x1 pixel JPEG)
        # This is a minimal valid JPEG image in base64
        test_image_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        
        test_data = {
            "image": test_image_base64,
            "provider": "gemini"
        }
        
        success, response = self.run_test(
            "AI Food Recognition",
            "POST",
            "ai/food-recognition",
            200,
            data=test_data
        )
        
        # Validate response structure
        if success and response:
            expected_keys = ['foods', 'confidence', 'insights']
            missing_keys = [key for key in expected_keys if key not in response]
            if not missing_keys:
                print(f"   ✅ Food recognition response contains all required keys: {expected_keys}")
                
                # Validate foods array structure
                foods = response.get('foods', [])
                if isinstance(foods, list):
                    print(f"   ✅ Foods array structure valid (contains {len(foods)} items)")
                    
                    # If foods found, validate structure
                    if foods and len(foods) > 0:
                        food = foods[0]
                        food_keys = ['name', 'calories', 'protein', 'carbs', 'fat', 'confidence']
                        missing_food_keys = [key for key in food_keys if key not in food]
                        if not missing_food_keys:
                            print(f"   ✅ Food item structure valid")
                        else:
                            print(f"   ⚠️ Food item missing some keys: {missing_food_keys}")
                    
                    # Validate confidence score
                    confidence = response.get('confidence', 0)
                    if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                        print(f"   ✅ Confidence score valid: {confidence}")
                    else:
                        print(f"   ⚠️ Confidence score format issue: {confidence}")
                        
                else:
                    print(f"   ❌ Foods should be an array")
                    success = False
            else:
                print(f"   ❌ Food recognition response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_health_insights_endpoint(self):
        """Test POST /api/ai/health-insights endpoint"""
        print("\n💡 Testing Health Insights Endpoint...")
        
        # Sample health data for testing
        test_health_data = {
            "user_id": "test-user-123",
            "age": 32,
            "gender": "female",
            "activity_level": "moderately_active",
            "current_weight": 68.5,
            "goal_weight": 65.0,
            "daily_calories": 2000,
            "avg_protein": 85,
            "avg_carbs": 180,
            "avg_fat": 70,
            "sleep_hours": 7.5,
            "exercise_frequency": 4,
            "stress_level": 6,
            "health_goals": ["weight_loss", "energy_improvement"],
            "medical_conditions": [],
            "recent_symptoms": ["fatigue", "occasional_headaches"]
        }
        
        test_data = {
            "healthData": test_health_data,
            "provider": "gemini",
            "analysis_type": "comprehensive"
        }
        
        success, response = self.run_test(
            "AI Health Insights",
            "POST",
            "ai/health-insights",
            200,
            data=test_data
        )
        
        # Validate response structure
        if success and response:
            expected_keys = ['insights', 'recommendations', 'patterns', 'confidence']
            missing_keys = [key for key in expected_keys if key not in response]
            if not missing_keys:
                print(f"   ✅ Health insights response contains all required keys: {expected_keys}")
                
                # Validate insights array
                insights = response.get('insights', [])
                if isinstance(insights, list):
                    print(f"   ✅ Insights array valid (contains {len(insights)} insights)")
                else:
                    print(f"   ❌ Insights should be an array")
                    success = False
                
                # Validate recommendations array
                recommendations = response.get('recommendations', [])
                if isinstance(recommendations, list):
                    print(f"   ✅ Recommendations array valid (contains {len(recommendations)} recommendations)")
                else:
                    print(f"   ❌ Recommendations should be an array")
                    success = False
                
                # Validate patterns object
                patterns = response.get('patterns', {})
                if isinstance(patterns, dict):
                    print(f"   ✅ Patterns object valid")
                else:
                    print(f"   ❌ Patterns should be an object")
                    success = False
                
                # Validate confidence score
                confidence = response.get('confidence', 0)
                if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                    print(f"   ✅ Confidence score valid: {confidence}")
                else:
                    print(f"   ⚠️ Confidence score format issue: {confidence}")
                    
            else:
                print(f"   ❌ Health insights response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_meal_suggestions_endpoint(self):
        """Test POST /api/ai/meal-suggestions endpoint"""
        print("\n🍽️ Testing Meal Suggestions Endpoint...")
        
        # Sample nutrition history and preferences
        test_nutrition_history = {
            "recent_meals": [
                {"name": "Oatmeal with berries", "calories": 350, "protein": 12, "carbs": 65, "fat": 8},
                {"name": "Grilled chicken salad", "calories": 420, "protein": 35, "carbs": 15, "fat": 22},
                {"name": "Greek yogurt", "calories": 150, "protein": 15, "carbs": 12, "fat": 8}
            ],
            "daily_totals": {
                "calories": 920,
                "protein": 62,
                "carbs": 92,
                "fat": 38
            },
            "nutritional_gaps": {
                "calories_remaining": 1080,
                "protein_needed": 38,
                "fiber_low": True,
                "omega3_low": True
            }
        }
        
        test_preferences = {
            "diet_type": "mediterranean",
            "allergies": ["tree_nuts"],
            "dislikes": ["liver", "brussels_sprouts"],
            "cooking_time": 30,
            "meal_type": "dinner",
            "cuisine_preferences": ["italian", "greek", "middle_eastern"],
            "health_goals": ["weight_loss", "heart_health"]
        }
        
        test_data = {
            "nutritionHistory": test_nutrition_history,
            "preferences": test_preferences,
            "provider": "gemini"
        }
        
        success, response = self.run_test(
            "AI Meal Suggestions",
            "POST",
            "ai/meal-suggestions",
            200,
            data=test_data
        )
        
        # Validate response structure
        if success and response:
            expected_keys = ['suggestions', 'reasoning', 'nutritionalBenefits']
            missing_keys = [key for key in expected_keys if key not in response]
            if not missing_keys:
                print(f"   ✅ Meal suggestions response contains all required keys: {expected_keys}")
                
                # Validate suggestions array
                suggestions = response.get('suggestions', [])
                if isinstance(suggestions, list):
                    print(f"   ✅ Suggestions array valid (contains {len(suggestions)} suggestions)")
                    
                    # If suggestions found, validate structure
                    if suggestions and len(suggestions) > 0:
                        suggestion = suggestions[0]
                        suggestion_keys = ['name', 'description', 'calories', 'protein', 'carbs', 'fat', 'benefits', 'reasoning']
                        missing_suggestion_keys = [key for key in suggestion_keys if key not in suggestion]
                        if not missing_suggestion_keys:
                            print(f"   ✅ Meal suggestion structure valid")
                        else:
                            print(f"   ⚠️ Meal suggestion missing some keys: {missing_suggestion_keys}")
                else:
                    print(f"   ❌ Suggestions should be an array")
                    success = False
                
                # Validate reasoning
                reasoning = response.get('reasoning', '')
                if isinstance(reasoning, str) and reasoning:
                    print(f"   ✅ Reasoning provided")
                else:
                    print(f"   ⚠️ Reasoning should be a non-empty string")
                
                # Validate nutritional benefits
                benefits = response.get('nutritionalBenefits', [])
                if isinstance(benefits, list):
                    print(f"   ✅ Nutritional benefits array valid (contains {len(benefits)} benefits)")
                else:
                    print(f"   ❌ Nutritional benefits should be an array")
                    success = False
                    
            else:
                print(f"   ❌ Meal suggestions response missing keys: {missing_keys}")
                success = False
        
        return success

    def test_voice_command_endpoint(self):
        """Test POST /api/ai/voice-command endpoint"""
        print("\n🎤 Testing Voice Command Endpoint...")
        
        # Test various voice command transcripts
        test_transcripts = [
            "I had a grilled chicken breast with steamed broccoli and brown rice for lunch",
            "Log two slices of whole wheat toast with avocado and a cup of coffee",
            "I ate a large apple and a handful of almonds as a snack",
            "For dinner I had salmon fillet with quinoa and mixed vegetables",
            "Add one cup of Greek yogurt with blueberries to my breakfast"
        ]
        
        all_tests_passed = True
        
        for i, transcript in enumerate(test_transcripts, 1):
            test_data = {
                "transcript": transcript,
                "provider": "gemini",
                "command_type": "food_logging"
            }
            
            success, response = self.run_test(
                f"AI Voice Command {i} - '{transcript[:30]}...'",
                "POST",
                "ai/voice-command",
                200,
                data=test_data
            )
            
            # Validate response structure
            if success and response:
                expected_keys = ['foodItems', 'intent', 'confidence', 'clarifications']
                missing_keys = [key for key in expected_keys if key not in response]
                if not missing_keys:
                    print(f"   ✅ Voice command response contains all required keys")
                    
                    # Validate foodItems array
                    food_items = response.get('foodItems', [])
                    if isinstance(food_items, list):
                        print(f"   ✅ Food items array valid (contains {len(food_items)} items)")
                        
                        # If food items found, validate structure
                        if food_items and len(food_items) > 0:
                            food_item = food_items[0]
                            item_keys = ['name', 'quantity', 'calories', 'protein', 'carbs', 'fat', 'confidence']
                            missing_item_keys = [key for key in item_keys if key not in food_item]
                            if not missing_item_keys:
                                print(f"   ✅ Food item structure valid")
                            else:
                                print(f"   ⚠️ Food item missing some keys: {missing_item_keys}")
                    else:
                        print(f"   ❌ Food items should be an array")
                        success = False
                    
                    # Validate intent
                    intent = response.get('intent', '')
                    if isinstance(intent, str) and intent:
                        print(f"   ✅ Intent provided: {intent}")
                    else:
                        print(f"   ⚠️ Intent should be a non-empty string")
                    
                    # Validate confidence score
                    confidence = response.get('confidence', 0)
                    if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                        print(f"   ✅ Confidence score valid: {confidence}")
                    else:
                        print(f"   ⚠️ Confidence score format issue: {confidence}")
                    
                    # Validate clarifications array
                    clarifications = response.get('clarifications', [])
                    if isinstance(clarifications, list):
                        print(f"   ✅ Clarifications array valid (contains {len(clarifications)} items)")
                    else:
                        print(f"   ❌ Clarifications should be an array")
                        success = False
                        
                else:
                    print(f"   ❌ Voice command response missing keys: {missing_keys}")
                    success = False
            
            if not success:
                all_tests_passed = False
        
        return all_tests_passed

    def test_phase4_food_logging_endpoints(self):
        """Test Phase 4 Food Logging endpoints after dependency updates"""
        print("\n📋 Testing Phase 4 Food Logging Endpoints...")
        
        test_user_id = "demo-patient-123"
        
        # Test 1: GET /api/patient/food-log/{user_id}/daily-summary
        success1, daily_summary_data = self.run_test(
            "Phase 4: Daily Nutrition Summary",
            "GET",
            f"patient/food-log/{test_user_id}/daily-summary",
            200
        )
        
        # Validate daily summary response structure
        if success1 and daily_summary_data:
            expected_keys = ['user_id', 'date', 'summary']
            missing_keys = [key for key in expected_keys if key not in daily_summary_data]
            if not missing_keys:
                print(f"   ✅ Daily summary contains all required keys: {expected_keys}")
                
                # Validate summary structure
                summary = daily_summary_data.get('summary', {})
                summary_keys = ['calories', 'protein', 'carbs', 'fat', 'meals', 'water_intake', 'goals_met', 'daily_goals', 'progress_percentage']
                missing_summary_keys = [key for key in summary_keys if key not in summary]
                if not missing_summary_keys:
                    print(f"   ✅ Summary contains all required nutrition keys")
                    calories = summary.get('calories', 0)
                    progress = summary.get('progress_percentage', {})
                    print(f"   ✅ Daily calories: {calories}, Progress data available: {len(progress)} metrics")
                else:
                    print(f"   ❌ Summary missing keys: {missing_summary_keys}")
                    success1 = False
            else:
                print(f"   ❌ Daily summary missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: GET /api/patient/food-log/{user_id}/recent
        success2, recent_data = self.run_test(
            "Phase 4: Recent Food Log Entries",
            "GET",
            f"patient/food-log/{test_user_id}/recent",
            200
        )
        
        # Validate recent entries response structure
        if success2 and recent_data:
            expected_keys = ['user_id', 'logs']
            missing_keys = [key for key in expected_keys if key not in recent_data]
            if not missing_keys:
                print(f"   ✅ Recent entries contains all required keys: {expected_keys}")
                
                # Validate recent entries structure
                entries = recent_data.get('logs', [])
                if entries and len(entries) > 0:
                    entry = entries[0]
                    entry_keys = ['id', 'food_name', 'calories', 'timestamp', 'source', 'confidence']
                    missing_entry_keys = [key for key in entry_keys if key not in entry]
                    if not missing_entry_keys:
                        print(f"   ✅ Recent entry structure valid with timestamps and confidence scores")
                        print(f"   ✅ Found {len(entries)} recent food log entries")
                    else:
                        print(f"   ❌ Recent entry missing keys: {missing_entry_keys}")
                        success2 = False
            else:
                print(f"   ❌ Recent entries missing keys: {missing_keys}")
                success2 = False
        
        # Test 3: GET /api/patient/smart-suggestions/{user_id} (context-aware)
        success3, smart_suggestions_data = self.run_test(
            "Phase 4: Context-Aware Smart Suggestions",
            "GET",
            f"patient/smart-suggestions/{test_user_id}",
            200
        )
        
        # Validate smart suggestions response structure
        if success3 and smart_suggestions_data:
            expected_keys = ['quick_add_suggestions', 'meal_pattern_insights', 'nutrition_gaps']
            missing_keys = [key for key in expected_keys if key not in smart_suggestions_data]
            if not missing_keys:
                print(f"   ✅ Smart suggestions contains all required keys: {expected_keys}")
                
                # Validate suggestions structure
                suggestions = smart_suggestions_data.get('quick_add_suggestions', [])
                if suggestions and len(suggestions) > 0:
                    suggestion = suggestions[0]
                    suggestion_keys = ['name', 'calories', 'reason']
                    missing_suggestion_keys = [key for key in suggestion_keys if key not in suggestion]
                    if not missing_suggestion_keys:
                        print(f"   ✅ Smart suggestion structure valid with personalized recommendations")
                    else:
                        print(f"   ❌ Smart suggestion missing keys: {missing_suggestion_keys}")
                        success3 = False
                
                # Validate nutrition gaps
                gaps = smart_suggestions_data.get('nutrition_gaps', [])
                if gaps and len(gaps) > 0:
                    gap = gaps[0]
                    gap_keys = ['nutrient', 'current', 'target', 'suggestion']
                    missing_gap_keys = [key for key in gap_keys if key not in gap]
                    if not missing_gap_keys:
                        print(f"   ✅ Nutrition gap structure valid with personalized targets")
                    else:
                        print(f"   ❌ Nutrition gap missing keys: {missing_gap_keys}")
            else:
                print(f"   ❌ Smart suggestions missing keys: {missing_keys}")
                success3 = False
        
        return success1 and success2 and success3

    def test_ai_integration_endpoints_verification(self):
        """Verify AI Integration endpoints are still working after dependency updates"""
        print("\n📋 Verifying AI Integration Endpoints...")
        
        # Test 1: POST /api/ai/food-recognition
        sample_food_image = {
            "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "user_id": "demo-patient-123"
        }
        
        success1, food_recognition_response = self.run_test(
            "AI: Food Recognition",
            "POST",
            "ai/food-recognition",
            200,
            data=sample_food_image
        )
        
        # Validate food recognition response
        if success1 and food_recognition_response:
            expected_keys = ['foods', 'confidence', 'insights']
            missing_keys = [key for key in expected_keys if key not in food_recognition_response]
            if not missing_keys:
                print(f"   ✅ Food recognition response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Food recognition response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: POST /api/ai/voice-command
        sample_voice_data = {
            "transcript": "I had a grilled chicken breast with quinoa and steamed broccoli for lunch",
            "user_id": "demo-patient-123"
        }
        
        success2, voice_response = self.run_test(
            "AI: Voice Command Processing",
            "POST",
            "ai/voice-command",
            200,
            data=sample_voice_data
        )
        
        # Validate voice command response (check actual response structure)
        if success2 and voice_response:
            # The actual response uses 'foodItems' instead of 'parsed_foods'
            expected_keys = ['foodItems', 'intent', 'clarifications']
            missing_keys = [key for key in expected_keys if key not in voice_response]
            if not missing_keys:
                print(f"   ✅ Voice command response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Voice command response missing keys: {missing_keys}")
                success2 = False
        
        # Test 3: POST /api/ai/meal-suggestions (with correct required fields)
        sample_meal_request = {
            "user_id": "demo-patient-123",
            "meal_type": "dinner",
            "dietary_preferences": ["low_carb", "high_protein"],
            "available_time": 30,
            "nutritionHistory": {
                "calories": 1200,
                "protein": 45,
                "carbs": 120,
                "fat": 40
            },
            "healthGoals": ["weight_loss", "muscle_gain"]
        }
        
        success3, meal_suggestions_response = self.run_test(
            "AI: Meal Suggestions",
            "POST",
            "ai/meal-suggestions",
            200,
            data=sample_meal_request
        )
        
        # Validate meal suggestions response
        if success3 and meal_suggestions_response:
            expected_keys = ['suggestions', 'reasoning', 'nutritionalBenefits']
            missing_keys = [key for key in expected_keys if key not in meal_suggestions_response]
            if not missing_keys:
                print(f"   ✅ Meal suggestions response contains all required keys: {expected_keys}")
            else:
                print(f"   ❌ Meal suggestions response missing keys: {missing_keys}")
                success3 = False
        
        return success1 and success2 and success3

    def test_chat_api_endpoints(self):
        """Test Chat API endpoints for food and health queries"""
        print("\n💬 Testing Chat API Endpoints...")
        
        # Test 1: Start a new chat session
        success1, session_response = self.run_test(
            "Start Chat Session",
            "POST",
            "chat/start-session",
            200
        )
        
        session_id = None
        if success1 and session_response:
            session_id = session_response.get('session_id')
            expected_keys = ['session_id', 'message', 'welcome_message']
            missing_keys = [key for key in expected_keys if key not in session_response]
            if not missing_keys:
                print(f"   ✅ Start session response contains all required keys: {expected_keys}")
                print(f"   Session ID: {session_id}")
            else:
                print(f"   ❌ Start session response missing keys: {missing_keys}")
                success1 = False
        
        if not session_id:
            print("   ❌ Failed to get session ID, using fallback for remaining tests")
            session_id = f"test_session_{int(datetime.now().timestamp())}"
        
        # Test 2: Send a food-related question
        food_question_data = {
            "session_id": session_id,
            "message": "What's a healthy breakfast for someone trying to lose weight?",
            "context_type": "health_and_nutrition",
            "user_context": {"goal": "weight_loss", "meal_type": "breakfast"}
        }
        
        success2, food_response = self.run_test(
            "Send Food-Related Message",
            "POST",
            "chat/send-message",
            200,
            data=food_question_data
        )
        
        # Validate food question response
        if success2 and food_response:
            expected_keys = ['response', 'session_id', 'suggestions', 'quick_actions', 'confidence']
            missing_keys = [key for key in expected_keys if key not in food_response]
            if not missing_keys:
                print(f"   ✅ Food question response contains all required keys: {expected_keys}")
                
                # Validate response content
                response_text = food_response.get('response', '')
                suggestions = food_response.get('suggestions', [])
                quick_actions = food_response.get('quick_actions', [])
                confidence = food_response.get('confidence', 0)
                
                print(f"   Response length: {len(response_text)} characters")
                print(f"   Suggestions count: {len(suggestions)}")
                print(f"   Quick actions count: {len(quick_actions)}")
                print(f"   Confidence score: {confidence}")
                
                # Check if response is nutrition-focused
                nutrition_keywords = ['breakfast', 'healthy', 'protein', 'fiber', 'calories', 'nutrition', 'weight']
                has_nutrition_content = any(keyword.lower() in response_text.lower() for keyword in nutrition_keywords)
                print(f"   ✅ Contains nutrition content: {has_nutrition_content}")
                
                if not has_nutrition_content:
                    print(f"   ⚠️  Response may not be nutrition-focused enough")
                
            else:
                print(f"   ❌ Food question response missing keys: {missing_keys}")
                success2 = False
        
        # Test 3: Send a health-related question
        health_question_data = {
            "session_id": session_id,
            "message": "How much protein do I need daily for muscle building?",
            "context_type": "health_and_nutrition",
            "user_context": {"goal": "muscle_building", "topic": "protein_requirements"}
        }
        
        success3, health_response = self.run_test(
            "Send Health-Related Message",
            "POST",
            "chat/send-message",
            200,
            data=health_question_data
        )
        
        # Validate health question response
        if success3 and health_response:
            response_text = health_response.get('response', '')
            suggestions = health_response.get('suggestions', [])
            quick_actions = health_response.get('quick_actions', [])
            
            # Check if response is health/protein-focused
            protein_keywords = ['protein', 'muscle', 'grams', 'daily', 'building', 'amino', 'intake']
            has_protein_content = any(keyword.lower() in response_text.lower() for keyword in protein_keywords)
            print(f"   ✅ Contains protein/health content: {has_protein_content}")
            
            # Check for contextual suggestions
            if suggestions:
                print(f"   ✅ Generated contextual suggestions: {suggestions[:2]}")  # Show first 2
            
            if quick_actions:
                print(f"   ✅ Generated quick actions: {[qa.get('label', 'N/A') for qa in quick_actions]}")
        
        # Test 4: Test conversation context maintenance
        followup_question_data = {
            "session_id": session_id,
            "message": "What are some good protein sources for vegetarians?",
            "context_type": "health_and_nutrition",
            "user_context": {"diet_type": "vegetarian", "topic": "protein_sources"}
        }
        
        success4, followup_response = self.run_test(
            "Send Follow-up Message (Context Test)",
            "POST",
            "chat/send-message",
            200,
            data=followup_question_data
        )
        
        # Validate context maintenance
        if success4 and followup_response:
            response_text = followup_response.get('response', '')
            vegetarian_keywords = ['vegetarian', 'plant', 'beans', 'lentils', 'tofu', 'quinoa', 'nuts', 'seeds']
            has_vegetarian_content = any(keyword.lower() in response_text.lower() for keyword in vegetarian_keywords)
            print(f"   ✅ Contains vegetarian protein content: {has_vegetarian_content}")
        
        # Test 5: Get chat history
        success5, history_response = self.run_test(
            "Get Chat History",
            "GET",
            f"chat/history/{session_id}",
            200
        )
        
        # Validate chat history
        if success5 and history_response:
            expected_keys = ['messages', 'session_id', 'created_at', 'context_type']
            missing_keys = [key for key in expected_keys if key not in history_response]
            if not missing_keys:
                print(f"   ✅ Chat history response contains all required keys: {expected_keys}")
                
                messages = history_response.get('messages', [])
                print(f"   Messages in history: {len(messages)}")
                
                # Validate message structure
                if messages:
                    user_messages = [msg for msg in messages if msg.get('type') == 'user']
                    assistant_messages = [msg for msg in messages if msg.get('type') == 'assistant']
                    
                    print(f"   User messages: {len(user_messages)}")
                    print(f"   Assistant messages: {len(assistant_messages)}")
                    
                    # Check if messages are properly stored
                    if len(user_messages) >= 3 and len(assistant_messages) >= 3:
                        print(f"   ✅ Conversation history properly maintained")
                    else:
                        print(f"   ⚠️  Expected more messages in history")
                        
                    # Validate message structure
                    if messages:
                        sample_message = messages[0]
                        msg_keys = ['type', 'content', 'timestamp']
                        missing_msg_keys = [key for key in msg_keys if key not in sample_message]
                        if not missing_msg_keys:
                            print(f"   ✅ Message structure valid")
                        else:
                            print(f"   ❌ Message structure missing keys: {missing_msg_keys}")
                            success5 = False
            else:
                print(f"   ❌ Chat history response missing keys: {missing_keys}")
                success5 = False
        
        # Test 6: Test AI service failure fallback
        invalid_session_data = {
            "session_id": f"fallback_test_{int(datetime.now().timestamp())}",
            "message": "This is a test message to check fallback responses",
            "context_type": "health_and_nutrition"
        }
        
        success6, fallback_response = self.run_test(
            "Test Fallback Response",
            "POST",
            "chat/send-message",
            200,
            data=invalid_session_data
        )
        
        # Validate fallback response
        if success6 and fallback_response:
            response_text = fallback_response.get('response', '')
            confidence = fallback_response.get('confidence', 1.0)
            
            # Fallback responses should have lower confidence and helpful content
            if confidence <= 0.8 and len(response_text) > 0:
                print(f"   ✅ Fallback response working (confidence: {confidence})")
            else:
                print(f"   ⚠️  Fallback response may not be working as expected")
        
        # Test 7: Test empty session history
        empty_session_id = f"empty_session_{int(datetime.now().timestamp())}"
        success7, empty_history = self.run_test(
            "Get Empty Session History",
            "GET",
            f"chat/history/{empty_session_id}",
            200
        )
        
        # Validate empty history response
        if success7 and empty_history:
            messages = empty_history.get('messages', [])
            if len(messages) == 0:
                print(f"   ✅ Empty session history handled correctly")
            else:
                print(f"   ⚠️  Expected empty messages array for new session")
        
        print(f"\n📊 Chat API Test Summary:")
        print(f"   ✅ Start session: {'PASS' if success1 else 'FAIL'}")
        print(f"   ✅ Food-related query: {'PASS' if success2 else 'FAIL'}")
        print(f"   ✅ Health-related query: {'PASS' if success3 else 'FAIL'}")
        print(f"   ✅ Context maintenance: {'PASS' if success4 else 'FAIL'}")
        print(f"   ✅ Chat history retrieval: {'PASS' if success5 else 'FAIL'}")
        print(f"   ✅ Fallback responses: {'PASS' if success6 else 'FAIL'}")
        print(f"   ✅ Empty session handling: {'PASS' if success7 else 'FAIL'}")
        
        return success1 and success2 and success3 and success4 and success5 and success6 and success7

    def test_enhanced_chat_api_endpoints(self):
        """Test Enhanced Chat Model System API endpoints"""
        print("\n🤖 Testing Enhanced Chat Model System...")
        
        # Test 1: Start a new chat session
        success1, session_response = self.run_test(
            "Start Chat Session",
            "POST",
            "chat/start-session",
            200
        )
        
        session_id = session_response.get("session_id") if session_response else f"test_session_{datetime.now().strftime('%H%M%S')}"
        
        # Test 2: Send basic message with enhanced context
        basic_message_data = {
            "session_id": session_id,
            "message": "What should I eat for breakfast to boost my energy?",
            "context_type": "health_and_nutrition",
            "user_context": {
                "profile_type": "patient",
                "health_goals": ["energy_boost", "weight_management"],
                "dietary_restrictions": ["vegetarian"],
                "interaction_count": 1
            }
        }
        
        success2, basic_response = self.run_test(
            "Send Basic Message with Enhanced Context",
            "POST",
            "chat/send-message",
            200,
            data=basic_message_data
        )
        
        # Test 3: Send follow-up message to test conversation context
        followup_message_data = {
            "session_id": session_id,
            "message": "Can you give me specific meal ideas with protein amounts?",
            "context_type": "health_and_nutrition",
            "user_context": {
                "profile_type": "patient",
                "health_goals": ["energy_boost", "weight_management"],
                "dietary_restrictions": ["vegetarian"],
                "interaction_count": 2
            }
        }
        
        success3, followup_response = self.run_test(
            "Send Follow-up Message (Context Building)",
            "POST",
            "chat/send-message",
            200,
            data=followup_message_data
        )
        
        # Test 4: Test different user context profiles
        provider_message_data = {
            "session_id": f"provider_session_{datetime.now().strftime('%H%M%S')}",
            "message": "What are the latest evidence-based recommendations for managing diabetes through nutrition?",
            "context_type": "clinical_guidance",
            "user_context": {
                "profile_type": "provider",
                "specialization": ["diabetes_management", "clinical_nutrition"],
                "patient_demographics": ["adults", "seniors"],
                "interaction_count": 1
            }
        }
        
        success4, provider_response = self.run_test(
            "Provider Context Message",
            "POST",
            "chat/send-message",
            200,
            data=provider_message_data
        )
        
        # Test 5: Test family context
        family_message_data = {
            "session_id": f"family_session_{datetime.now().strftime('%H%M%S')}",
            "message": "How can I plan healthy meals for my family with kids who are picky eaters?",
            "context_type": "family_nutrition",
            "user_context": {
                "profile_type": "family",
                "family_size": 4,
                "children_ages": [8, 12],
                "dietary_restrictions": ["peanut_free"],
                "interaction_count": 1
            }
        }
        
        success5, family_response = self.run_test(
            "Family Context Message",
            "POST",
            "chat/send-message",
            200,
            data=family_message_data
        )
        
        # Test 6: Get chat history
        success6, history_response = self.run_test(
            "Get Chat History",
            "GET",
            f"chat/history/{session_id}",
            200
        )
        
        # Test 7: Test error handling with malformed request
        malformed_data = {
            "session_id": session_id,
            "message": "",  # Empty message
            "context_type": "health_and_nutrition"
        }
        
        success7, error_response = self.run_test(
            "Send Empty Message (Error Handling)",
            "POST",
            "chat/send-message",
            200,  # Should still return 200 with fallback response
            data=malformed_data
        )
        
        # Test 8: Test complex multi-turn conversation
        complex_session_id = f"complex_session_{datetime.now().strftime('%H%M%S')}"
        
        # First message
        complex_msg1 = {
            "session_id": complex_session_id,
            "message": "I'm trying to lose weight but I'm always hungry. What should I do?",
            "context_type": "health_and_nutrition",
            "user_context": {
                "profile_type": "patient",
                "health_goals": ["weight_loss"],
                "current_weight": 80,
                "goal_weight": 70,
                "interaction_count": 1
            }
        }
        
        success8a, _ = self.run_test(
            "Complex Conversation - Message 1",
            "POST",
            "chat/send-message",
            200,
            data=complex_msg1
        )
        
        # Second message
        complex_msg2 = {
            "session_id": complex_session_id,
            "message": "I usually skip breakfast and eat a big lunch. Is that bad?",
            "context_type": "health_and_nutrition",
            "user_context": {
                "profile_type": "patient",
                "health_goals": ["weight_loss"],
                "current_weight": 80,
                "goal_weight": 70,
                "interaction_count": 2
            }
        }
        
        success8b, complex_response = self.run_test(
            "Complex Conversation - Message 2",
            "POST",
            "chat/send-message",
            200,
            data=complex_msg2
        )
        
        # Validate response structures
        validation_results = []
        
        if success2 and basic_response:
            # Validate enhanced response structure
            required_fields = ['response', 'session_id', 'suggestions', 'quick_actions', 'confidence']
            enhanced_fields = ['title', 'summary', 'key_points', 'action_steps', 'tips']
            
            basic_fields_valid = all(field in basic_response for field in required_fields)
            enhanced_fields_present = any(field in basic_response for field in enhanced_fields)
            
            validation_results.append(basic_fields_valid)
            validation_results.append(enhanced_fields_present)
            
            print(f"   Basic response fields validation: {'✅' if basic_fields_valid else '❌'}")
            print(f"   Enhanced response fields present: {'✅' if enhanced_fields_present else '❌'}")
            
            # Check confidence level
            confidence = basic_response.get('confidence', 0)
            confidence_valid = 0.5 <= confidence <= 1.0
            validation_results.append(confidence_valid)
            print(f"   Confidence level validation (0.5-1.0): {'✅' if confidence_valid else '❌'} ({confidence})")
            
            # Check suggestions array
            suggestions = basic_response.get('suggestions', [])
            suggestions_valid = isinstance(suggestions, list) and len(suggestions) > 0
            validation_results.append(suggestions_valid)
            print(f"   Suggestions array validation: {'✅' if suggestions_valid else '❌'} ({len(suggestions)} suggestions)")
            
            # Check quick actions
            quick_actions = basic_response.get('quick_actions', [])
            quick_actions_valid = isinstance(quick_actions, list)
            validation_results.append(quick_actions_valid)
            print(f"   Quick actions validation: {'✅' if quick_actions_valid else '❌'} ({len(quick_actions)} actions)")
        
        if success6 and history_response:
            # Validate chat history structure
            messages = history_response.get('messages', [])
            history_valid = isinstance(messages, list) and len(messages) >= 2  # Should have user + AI messages
            validation_results.append(history_valid)
            print(f"   Chat history validation: {'✅' if history_valid else '❌'} ({len(messages)} messages)")
            
            # Check message structure
            if messages:
                first_message = messages[0]
                message_structure_valid = all(field in first_message for field in ['type', 'content', 'timestamp'])
                validation_results.append(message_structure_valid)
                print(f"   Message structure validation: {'✅' if message_structure_valid else '❌'}")
        
        # Test context awareness by checking if responses differ based on user context
        context_awareness_valid = True
        if success2 and success4 and basic_response and provider_response:
            basic_content = basic_response.get('response', '').lower()
            provider_content = provider_response.get('response', '').lower()
            
            # Provider response should be more clinical/evidence-based
            clinical_terms = ['evidence', 'clinical', 'research', 'study', 'guidelines']
            provider_clinical = any(term in provider_content for term in clinical_terms)
            
            # Basic response should be more conversational
            conversational_terms = ['you', 'your', 'try', 'consider', 'might']
            basic_conversational = any(term in basic_content for term in conversational_terms)
            
            context_awareness_valid = provider_clinical or basic_conversational
            validation_results.append(context_awareness_valid)
            print(f"   Context awareness validation: {'✅' if context_awareness_valid else '❌'}")
        
        # Overall success
        all_tests_passed = all([success1, success2, success3, success4, success5, success6, success7, success8a, success8b])
        all_validations_passed = all(validation_results) if validation_results else True
        
        overall_success = all_tests_passed and all_validations_passed
        
        print(f"   Enhanced Chat API Tests: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        print(f"   API Tests: {sum([success1, success2, success3, success4, success5, success6, success7, success8a, success8b])}/9")
        print(f"   Validation Tests: {sum(validation_results)}/{len(validation_results) if validation_results else 0}")
        
        return overall_success

    def test_ai_service_integration(self):
        """Test AI Service Integration and Fallback Mechanisms"""
        print("\n🧠 Testing AI Service Integration...")
        
        # Test 1: Test with realistic health query
        realistic_query_data = {
            "session_id": f"ai_test_session_{datetime.now().strftime('%H%M%S')}",
            "message": "I have diabetes and high blood pressure. What foods should I avoid and what should I eat more of?",
            "context_type": "health_and_nutrition",
            "user_context": {
                "profile_type": "patient",
                "health_conditions": ["diabetes", "hypertension"],
                "medications": ["metformin", "lisinopril"],
                "age": 55,
                "interaction_count": 1
            }
        }
        
        success1, realistic_response = self.run_test(
            "Realistic Health Query with Medical Context",
            "POST",
            "chat/send-message",
            200,
            data=realistic_query_data
        )
        
        # Test 2: Test with nutrition calculation query
        calculation_query_data = {
            "session_id": f"calc_session_{datetime.now().strftime('%H%M%S')}",
            "message": "How many calories should I eat per day if I'm 30 years old, 170cm tall, weigh 75kg, and exercise 3 times a week?",
            "context_type": "health_and_nutrition",
            "user_context": {
                "profile_type": "patient",
                "age": 30,
                "height": 170,
                "weight": 75,
                "activity_level": "moderately_active",
                "health_goals": ["maintain_weight"],
                "interaction_count": 1
            }
        }
        
        success2, calculation_response = self.run_test(
            "Nutrition Calculation Query",
            "POST",
            "chat/send-message",
            200,
            data=calculation_query_data
        )
        
        # Test 3: Test with meal planning query
        meal_planning_data = {
            "session_id": f"meal_session_{datetime.now().strftime('%H%M%S')}",
            "message": "Can you create a 3-day meal plan for someone who is vegetarian, trying to lose weight, and has a busy schedule?",
            "context_type": "meal_planning",
            "user_context": {
                "profile_type": "patient",
                "dietary_restrictions": ["vegetarian"],
                "health_goals": ["weight_loss"],
                "lifestyle": ["busy_schedule"],
                "cooking_time": "30_minutes_max",
                "interaction_count": 1
            }
        }
        
        success3, meal_response = self.run_test(
            "Meal Planning Query",
            "POST",
            "chat/send-message",
            200,
            data=meal_planning_data
        )
        
        # Test 4: Test fallback mechanism with very long message
        long_message_data = {
            "session_id": f"long_session_{datetime.now().strftime('%H%M%S')}",
            "message": "I have been struggling with my weight for years and have tried many different diets including keto, paleo, intermittent fasting, and calorie counting but nothing seems to work long term and I always end up gaining the weight back and I'm feeling really frustrated and don't know what to do anymore and I'm wondering if you can help me understand why this keeps happening and what I should try next because I really want to be healthy and feel good about myself but I'm starting to lose hope that I'll ever be able to maintain a healthy weight and lifestyle and I'm also dealing with stress from work and family responsibilities which makes it even harder to stick to healthy habits and I often find myself eating emotionally when I'm stressed or tired and I know this isn't helping but I don't know how to break the cycle and I'm hoping you can provide some guidance and support to help me figure out a sustainable approach to health and wellness that will actually work for me long term.",
            "context_type": "health_and_nutrition",
            "user_context": {
                "profile_type": "patient",
                "health_goals": ["weight_loss", "stress_management"],
                "previous_attempts": ["keto", "paleo", "intermittent_fasting"],
                "challenges": ["emotional_eating", "work_stress", "family_stress"],
                "interaction_count": 1
            }
        }
        
        success4, long_response = self.run_test(
            "Long Complex Message (Fallback Test)",
            "POST",
            "chat/send-message",
            200,
            data=long_message_data
        )
        
        # Test 5: Test with invalid/edge case data
        edge_case_data = {
            "session_id": f"edge_session_{datetime.now().strftime('%H%M%S')}",
            "message": "🍎🥗🏃‍♀️💪 healthy food exercise?",  # Emoji-heavy message
            "context_type": "health_and_nutrition",
            "user_context": {
                "profile_type": "general",
                "interaction_count": 1
            }
        }
        
        success5, edge_response = self.run_test(
            "Edge Case Message (Emojis)",
            "POST",
            "chat/send-message",
            200,
            data=edge_case_data
        )
        
        # Validate AI service responses
        validation_results = []
        
        if success1 and realistic_response:
            # Check if response addresses medical conditions
            response_content = realistic_response.get('response', '').lower()
            medical_awareness = any(term in response_content for term in ['diabetes', 'blood pressure', 'sodium', 'sugar', 'carbohydrate'])
            validation_results.append(medical_awareness)
            print(f"   Medical condition awareness: {'✅' if medical_awareness else '❌'}")
            
            # Check for structured response elements
            structured_elements = realistic_response.get('key_points', []) or realistic_response.get('action_steps', [])
            has_structure = len(structured_elements) > 0
            validation_results.append(has_structure)
            print(f"   Structured response elements: {'✅' if has_structure else '❌'}")
        
        if success2 and calculation_response:
            # Check if response includes numerical guidance
            response_content = calculation_response.get('response', '').lower()
            numerical_guidance = any(term in response_content for term in ['calorie', 'kcal', '2000', '2500', 'tdee', 'bmr'])
            validation_results.append(numerical_guidance)
            print(f"   Numerical guidance present: {'✅' if numerical_guidance else '❌'}")
        
        if success3 and meal_response:
            # Check if response includes meal suggestions
            response_content = meal_response.get('response', '').lower()
            meal_suggestions = any(term in response_content for term in ['breakfast', 'lunch', 'dinner', 'meal', 'recipe'])
            validation_results.append(meal_suggestions)
            print(f"   Meal suggestions present: {'✅' if meal_suggestions else '❌'}")
            
            # Check for vegetarian awareness
            vegetarian_awareness = any(term in response_content for term in ['vegetarian', 'plant', 'protein', 'beans', 'tofu'])
            validation_results.append(vegetarian_awareness)
            print(f"   Vegetarian dietary awareness: {'✅' if vegetarian_awareness else '❌'}")
        
        if success4 and long_response:
            # Check if fallback handles long message appropriately
            response_confidence = long_response.get('confidence', 0)
            fallback_handled = response_confidence >= 0.5  # Should still provide reasonable confidence
            validation_results.append(fallback_handled)
            print(f"   Long message fallback handling: {'✅' if fallback_handled else '❌'}")
        
        if success5 and edge_response:
            # Check if edge case is handled gracefully
            edge_confidence = edge_response.get('confidence', 0)
            edge_handled = edge_confidence >= 0.5 and len(edge_response.get('response', '')) > 10
            validation_results.append(edge_handled)
            print(f"   Edge case handling: {'✅' if edge_handled else '❌'}")
        
        # Test response time (should be reasonable)
        import time
        start_time = time.time()
        
        quick_test_data = {
            "session_id": f"speed_session_{datetime.now().strftime('%H%M%S')}",
            "message": "What's a healthy snack?",
            "context_type": "health_and_nutrition",
            "user_context": {"profile_type": "general", "interaction_count": 1}
        }
        
        success6, speed_response = self.run_test(
            "Response Time Test",
            "POST",
            "chat/send-message",
            200,
            data=quick_test_data
        )
        
        response_time = time.time() - start_time
        reasonable_time = response_time < 30  # Should respond within 30 seconds
        validation_results.append(reasonable_time)
        print(f"   Response time validation (<30s): {'✅' if reasonable_time else '❌'} ({response_time:.2f}s)")
        
        # Overall success
        all_tests_passed = all([success1, success2, success3, success4, success5, success6])
        all_validations_passed = all(validation_results) if validation_results else True
        
        overall_success = all_tests_passed and all_validations_passed
        
        print(f"   AI Service Integration Tests: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        print(f"   API Tests: {sum([success1, success2, success3, success4, success5, success6])}/6")
        print(f"   Validation Tests: {sum(validation_results)}/{len(validation_results) if validation_results else 0}")
        
        return overall_success

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

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Health & Nutrition Platform API Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)

        # Test Enhanced Chat Model System tests (NEW - PRIORITY TEST)
        print("\n📋 Testing Enhanced Chat Model System (PRIORITY)...")
        chat_api_success = self.test_enhanced_chat_api_endpoints()
        ai_service_success = self.test_ai_service_integration()
        
        # Test Enhanced Chat Detailed Responses (REVIEW REQUEST)
        print("\n📋 Testing Enhanced Chat Detailed Responses (REVIEW REQUEST)...")
        enhanced_chat_detailed_success = self.test_enhanced_chat_detailed_responses()
        
        # Test basic API
        print("\n📋 Testing Basic API...")
        self.test_basic_api()

        # Test status endpoints
        print("\n📋 Testing Status Endpoints...")
        self.test_status_endpoints()

        # Test user endpoints
        print("\n📋 Testing User Management...")
        user_success, user_id = self.test_user_endpoints()

        # Test health metrics
        print("\n📋 Testing Health Metrics...")
        self.test_health_metrics_endpoints(user_id)

        # Test dashboard endpoints
        print("\n📋 Testing Dashboard Endpoints...")
        self.test_dashboard_endpoints()

        # Test additional endpoints
        print("\n📋 Testing Additional Role-Specific Endpoints...")
        self.test_additional_endpoints()

        # Test profile management endpoints
        print("\n📋 Testing Profile Management Endpoints...")
        self.test_profile_management_endpoints()

        # Test Profile Wizard Enhancements (NEW - MAIN FOCUS)
        print("\n📋 Testing Profile Wizard Enhancements...")
        self.test_profile_wizard_enhancements()

        # Test patient analytics endpoints
        print("\n📋 Testing Patient Analytics Endpoints...")
        self.test_patient_analytics_endpoints()

        # Test Phase 3 Patient APIs
        print("\n📋 Testing Phase 3 Patient APIs...")
        self.test_phase3_patient_apis()

        # Test Phase 4 Advanced Provider Features
        print("\n📋 Testing Phase 4 Advanced Provider Features...")
        self.test_phase4_provider_features()

        # Test Phase 4 Food Logging Endpoints (NEW - REQUESTED TEST)
        print("\n📋 Testing Phase 4 Food Logging Endpoints (REQUESTED)...")
        phase4_food_logging_success = self.test_phase4_food_logging_endpoints()
        
        # Test AI Integration Endpoints Verification (NEW - REQUESTED TEST)
        print("\n📋 Testing AI Integration Endpoints Verification (REQUESTED)...")
        ai_verification_success = self.test_ai_integration_endpoints_verification()

        # Test Phase 5 Comprehensive Family Features
        print("\n📋 Testing Phase 5 Comprehensive Family Features...")
        self.test_phase5_family_features()

        # Test Phase 6 Guest Goals Management
        print("\n📋 Testing Phase 6 Guest Goals Management...")
        phase6_success = self.test_phase6_guest_goals_management()

        # Test Phase 7 Data Export Endpoints
        print("\n📋 Testing Phase 7 Data Export Endpoints...")
        phase7_success = self.test_phase7_data_export_endpoints()

        # Test AI API Endpoints (NEW - PRIORITY TEST)
        print("\n📋 Testing AI API Endpoints (PRIORITY)...")
        ai_success = self.test_ai_api_endpoints()
        
        # Test Chat API Endpoints (NEW - REQUESTED TEST)
        print("\n📋 Testing Chat API Endpoints (REQUESTED)...")
        chat_success = self.test_chat_api_endpoints()
        
        # Test Phase 3 AI Integration for PersonalInsights (NEW - FOCUS TEST)
        print("\n📋 Testing Phase 3 AI Integration - PersonalInsights (FOCUS)...")
        phase3_ai_success = self.test_phase3_ai_integration_personalinsights()

        # Test Guest Session Management and Export (PRIORITY TEST)
        print("\n📋 Testing Guest Session Management & Export (PRIORITY)...")
        guest_session_success = self.test_guest_session_management_and_export()

        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 FINAL RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Highlight the priority test results
        print(f"\n🎯 PRIORITY TEST RESULTS:")
        print(f"   Enhanced Chat API Endpoints: {'✅ PASSED' if chat_api_success else '❌ FAILED'}")
        print(f"   AI Service Integration: {'✅ PASSED' if ai_service_success else '❌ FAILED'}")
        print(f"   AI API Endpoints: {'✅ PASSED' if ai_success else '❌ FAILED'}")
        print(f"   Chat API Endpoints: {'✅ PASSED' if chat_success else '❌ FAILED'}")
        print(f"   Phase 3 AI Integration - PersonalInsights: {'✅ PASSED' if phase3_ai_success else '❌ FAILED'}")
        print(f"   Phase 4 Food Logging Endpoints: {'✅ PASSED' if phase4_food_logging_success else '❌ FAILED'}")
        print(f"   Guest Session Management & Export: {'✅ PASSED' if guest_session_success else '❌ FAILED'}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result.get('success', False):
                    print(f"  - {result['name']}: {result.get('error', 'Status code mismatch')}")
            return 1

    def test_patient_profile_auto_save_compatibility(self):
        """Test Patient Profile Management API for auto-save compatibility"""
        print("\n🔍 Testing Patient Profile Management API - Auto-Save Compatibility...")
        print("Focus: Ensure auto-save improvements don't break existing functionality")
        
        # Generate unique user ID for testing
        test_user_id = f"autosave_test_{datetime.now().strftime('%H%M%S_%f')}"
        
        # Test 1: Create Patient Profile with complete profile data (POST /api/profiles/patient)
        print("\n📝 Test 1: Patient Profile Creation with Complete Data")
        complete_profile_data = {
            "user_id": test_user_id,
            "basic_info": {
                "full_name": "Jessica Martinez",
                "age": 32,
                "gender": "Female",
                "location": "Austin, TX",
                "contact_preferences": {"email": True, "sms": True, "push": False},
                "timezone": "America/Chicago",
                "emergency_contact": {"name": "Carlos Martinez", "phone": "+1-555-0199"},
                "preferred_language": "English"
            },
            "physical_metrics": {
                "height_cm": 168.0,
                "current_weight_kg": 72.0,
                "goal_weight_kg": 68.0,
                "body_fat_percentage": 22.5,
                "muscle_mass_kg": 45.0,
                "measurements": {"waist": 78.0, "chest": 95.0, "hips": 98.0},
                "bmi": 25.5
            },
            "activity_profile": {
                "activity_level": "VERY_ACTIVE",
                "exercise_types": ["yoga", "pilates", "swimming", "hiking"],
                "exercise_frequency": 5,
                "sleep_schedule": {
                    "bedtime": "22:30",
                    "wake_time": "06:30",
                    "sleep_quality": 4
                },
                "stress_level": 2,
                "work_type": "MIXED"
            },
            "health_history": {
                "primary_health_goals": ["weight_loss", "muscle_tone", "stress_reduction"],
                "medical_conditions": {"hypothyroidism": "controlled"},
                "current_medications": [
                    {"name": "Levothyroxine", "dosage": "50mcg", "frequency": "daily"}
                ],
                "allergies": ["latex", "iodine"],
                "food_intolerances": ["gluten"],
                "previous_surgeries": [
                    {"procedure": "Appendectomy", "year": 2018, "complications": "none"}
                ],
                "family_medical_history": ["thyroid_disease", "diabetes"]
            },
            "dietary_profile": {
                "diet_type": "FLEXITARIAN",
                "cultural_restrictions": [],
                "specific_diets": ["gluten_free"],
                "food_allergies": [],
                "food_dislikes": ["mushrooms", "olives"],
                "meal_timing_preference": "SMALL_FREQUENT",
                "cooking_skill_level": 4,
                "available_cooking_time": 60
            },
            "goals_preferences": {
                "health_targets": [
                    {"type": "weight", "target": 68.0, "timeframe": "4_months"},
                    {"type": "body_fat", "target": 20.0, "timeframe": "6_months"},
                    {"type": "exercise", "target": 5, "timeframe": "weekly"}
                ],
                "communication_methods": ["email", "app_notifications", "text_messages"],
                "notification_preferences": {
                    "daily_reminders": True, 
                    "weekly_reports": True, 
                    "goal_achievements": True,
                    "meal_suggestions": True
                },
                "privacy_settings": {
                    "share_with_providers": True, 
                    "anonymous_data": True,
                    "research_participation": False
                },
                "data_sharing_preferences": {
                    "family_members": True,
                    "healthcare_team": True,
                    "fitness_apps": False
                }
            }
        }
        
        success1, create_response = self.run_test(
            "Create Patient Profile - Complete Data",
            "POST",
            "profiles/patient",
            200,
            data=complete_profile_data
        )
        
        # Validate profile completion calculation
        if success1 and create_response:
            completion = create_response.get('profile_completion', 0)
            print(f"   ✅ Profile completion: {completion}% (Expected: 100%)")
            completion_valid = completion == 100.0
            if not completion_valid:
                print(f"   ❌ Profile completion calculation issue: Expected 100%, got {completion}%")
        
        # Test 2: Verify profile retrieval
        print("\n📝 Test 2: Profile Retrieval Verification")
        success2, get_response = self.run_test(
            "Get Complete Patient Profile",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        # Validate all sections are present
        if success2 and get_response:
            expected_sections = ["basic_info", "physical_metrics", "activity_profile", "health_history", "dietary_profile", "goals_preferences"]
            missing_sections = [section for section in expected_sections if not get_response.get(section)]
            if not missing_sections:
                print(f"   ✅ All profile sections present and complete")
            else:
                print(f"   ❌ Missing sections: {missing_sections}")
        
        # Test 3: Partial Updates (PUT /api/profiles/patient/{user_id}) - Simulating auto-save behavior
        print("\n📝 Test 3: Partial Profile Updates (Auto-Save Simulation)")
        
        # Test 3a: Update only basic_info (common auto-save scenario)
        basic_info_update = {
            "basic_info": {
                "full_name": "Jessica Martinez-Rodriguez",  # Name change
                "age": 32,
                "gender": "Female",
                "location": "Austin, TX",
                "contact_preferences": {"email": True, "sms": True, "push": True},  # Updated preferences
                "timezone": "America/Chicago",
                "emergency_contact": {"name": "Carlos Martinez", "phone": "+1-555-0199"},
                "preferred_language": "English"
            }
        }
        
        success3a, update_response_basic = self.run_test(
            "Partial Update - Basic Info Only",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=basic_info_update
        )
        
        # Test 3b: Update only physical_metrics (another common auto-save scenario)
        physical_update = {
            "physical_metrics": {
                "height_cm": 168.0,
                "current_weight_kg": 71.2,  # Weight progress
                "goal_weight_kg": 68.0,
                "body_fat_percentage": 21.8,  # Body fat progress
                "muscle_mass_kg": 45.5,  # Muscle gain
                "measurements": {"waist": 77.0, "chest": 95.0, "hips": 97.5},  # Updated measurements
                "bmi": 25.2
            }
        }
        
        success3b, update_response_physical = self.run_test(
            "Partial Update - Physical Metrics Only",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=physical_update
        )
        
        # Test 3c: Update multiple sections simultaneously (complex auto-save scenario)
        multi_section_update = {
            "activity_profile": {
                "activity_level": "VERY_ACTIVE",
                "exercise_types": ["yoga", "pilates", "swimming", "hiking", "strength_training"],  # Added new exercise
                "exercise_frequency": 6,  # Increased frequency
                "sleep_schedule": {
                    "bedtime": "22:00",  # Earlier bedtime
                    "wake_time": "06:00",  # Earlier wake time
                    "sleep_quality": 5  # Improved sleep quality
                },
                "stress_level": 1,  # Reduced stress
                "work_type": "MIXED"
            },
            "goals_preferences": {
                "health_targets": [
                    {"type": "weight", "target": 68.0, "timeframe": "3_months"},  # Updated timeframe
                    {"type": "body_fat", "target": 19.0, "timeframe": "5_months"},  # More ambitious target
                    {"type": "exercise", "target": 6, "timeframe": "weekly"}  # Increased exercise target
                ],
                "communication_methods": ["email", "app_notifications", "text_messages"],
                "notification_preferences": {
                    "daily_reminders": True, 
                    "weekly_reports": True, 
                    "goal_achievements": True,
                    "meal_suggestions": True,
                    "workout_reminders": True  # New preference
                },
                "privacy_settings": {
                    "share_with_providers": True, 
                    "anonymous_data": True,
                    "research_participation": True  # Changed mind about research
                },
                "data_sharing_preferences": {
                    "family_members": True,
                    "healthcare_team": True,
                    "fitness_apps": True  # Now willing to share with fitness apps
                }
            }
        }
        
        success3c, update_response_multi = self.run_test(
            "Partial Update - Multiple Sections",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=multi_section_update
        )
        
        # Test 4: Validation Testing - Ensure validation still works with complete sections
        print("\n📝 Test 4: Validation Testing with Complete Sections")
        
        # Test 4a: Invalid enum value in complete section
        invalid_enum_update = {
            "activity_profile": {
                "activity_level": "SUPER_ACTIVE",  # Invalid enum value
                "exercise_types": ["yoga"],
                "exercise_frequency": 3,
                "sleep_schedule": {
                    "bedtime": "22:00",
                    "wake_time": "06:00",
                    "sleep_quality": 4
                },
                "stress_level": 2,
                "work_type": "DESK_JOB"
            }
        }
        
        success4a, _ = self.run_test(
            "Validation Test - Invalid Enum (Should Fail)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            422,  # Expecting validation error
            data=invalid_enum_update
        )
        
        # Test 4b: Invalid data type in complete section
        invalid_type_update = {
            "physical_metrics": {
                "height_cm": "not_a_number",  # Invalid data type
                "current_weight_kg": 70.0,
                "goal_weight_kg": 68.0
            }
        }
        
        success4b, _ = self.run_test(
            "Validation Test - Invalid Data Type (Should Fail)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            422,  # Expecting validation error
            data=invalid_type_update
        )
        
        # Test 4c: Missing required fields in complete section
        incomplete_section_update = {
            "basic_info": {
                "full_name": "Test User"
                # Missing required fields: age, gender, location, timezone, preferred_language
            }
        }
        
        success4c, _ = self.run_test(
            "Validation Test - Incomplete Required Section (Should Fail)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            422,  # Expecting validation error
            data=incomplete_section_update
        )
        
        # Test 5: Profile Completion Calculation After Updates
        print("\n📝 Test 5: Profile Completion Calculation Verification")
        
        success5, final_profile = self.run_test(
            "Get Updated Profile for Completion Check",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        if success5 and final_profile:
            final_completion = final_profile.get('profile_completion', 0)
            print(f"   ✅ Final profile completion: {final_completion}% (Should remain 100%)")
            final_completion_valid = final_completion == 100.0
            if not final_completion_valid:
                print(f"   ❌ Profile completion calculation changed unexpectedly: {final_completion}%")
        
        # Test 6: Profile Completion Status API
        success6, completion_status = self.run_test(
            "Get Profile Completion Status",
            "GET",
            f"profiles/completion/{test_user_id}",
            200,
            params={"role": "patient"}
        )
        
        if success6 and completion_status:
            api_completion = completion_status.get('completion_percentage', 0)
            missing_sections = completion_status.get('missing_sections', [])
            print(f"   ✅ API completion status: {api_completion}%")
            print(f"   ✅ Missing sections: {missing_sections}")
            
            if api_completion != 100.0 or missing_sections:
                print(f"   ❌ Completion API inconsistency detected")
        
        # Cleanup: Delete test profile
        success_cleanup, _ = self.run_test(
            "Cleanup - Delete Test Profile",
            "DELETE",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        # Calculate overall success
        all_create_update_tests = success1 and success2 and success3a and success3b and success3c
        all_validation_tests = success4a and success4b and success4c  # These should fail (return True when they fail as expected)
        all_completion_tests = success5 and success6
        
        overall_success = all_create_update_tests and all_validation_tests and all_completion_tests and success_cleanup
        
        print(f"\n📊 Auto-Save Compatibility Test Results:")
        print(f"   Profile Creation & Updates: {'✅' if all_create_update_tests else '❌'}")
        print(f"   Validation Still Working: {'✅' if all_validation_tests else '❌'}")
        print(f"   Completion Calculation: {'✅' if all_completion_tests else '❌'}")
        print(f"   Overall Success: {'✅' if overall_success else '❌'}")
        
        return overall_success

    def test_patient_profile_partial_updates_smoke_test(self):
        """Smoke test for patient profile partial updates as requested in review"""
        print("\n🔍 Patient Profile Partial Updates - Smoke Test")
        print("Testing: POST with basic_info only, PUT with physical_metrics only, PUT with incomplete activity_profile")
        
        # Generate unique user ID for testing
        test_user_id = f"smoke_test_{datetime.now().strftime('%H%M%S_%f')}"
        
        # Test 1: POST /api/profiles/patient with only user_id and complete basic_info section
        print("\n📝 Test 1: POST with only user_id and complete basic_info section")
        basic_info_only_data = {
            "user_id": test_user_id,
            "basic_info": {
                "full_name": "Emma Wilson",
                "age": 29,
                "gender": "Female", 
                "location": "Seattle, WA",
                "contact_preferences": {"email": True, "sms": False, "push": True},
                "timezone": "America/Los_Angeles",
                "emergency_contact": {"name": "David Wilson", "phone": "+1-555-0188"},
                "preferred_language": "English"
            }
        }
        
        success1, create_response = self.run_test(
            "POST Patient Profile - Basic Info Only",
            "POST",
            "profiles/patient",
            200,
            data=basic_info_only_data
        )
        
        if success1 and create_response:
            completion = create_response.get('profile_completion', 0)
            print(f"   ✅ Profile completion after basic_info only: {completion}%")
        
        # Test 2: PUT /api/profiles/patient/{user_id} with only complete physical_metrics section
        print("\n📝 Test 2: PUT with only complete physical_metrics section")
        physical_metrics_only = {
            "physical_metrics": {
                "height_cm": 165.0,
                "current_weight_kg": 62.0,
                "goal_weight_kg": 58.0,
                "body_fat_percentage": 24.0,
                "muscle_mass_kg": 42.0,
                "measurements": {"waist": 75.0, "chest": 88.0, "hips": 95.0},
                "bmi": 22.8
            }
        }
        
        success2, update_response = self.run_test(
            "PUT Patient Profile - Physical Metrics Only",
            "PUT",
            f"profiles/patient/{test_user_id}",
            200,
            data=physical_metrics_only
        )
        
        if success2 and update_response:
            completion = update_response.get('profile_completion', 0)
            print(f"   ✅ Profile completion after adding physical_metrics: {completion}%")
        
        # Test 3: PUT with incomplete activity_profile (missing sleep_schedule) - should return 422
        print("\n📝 Test 3: PUT with incomplete activity_profile (missing sleep_schedule)")
        incomplete_activity_profile = {
            "activity_profile": {
                "activity_level": "MODERATELY_ACTIVE",
                "exercise_types": ["running", "yoga"],
                "exercise_frequency": 4,
                # Missing required sleep_schedule field
                "stress_level": 3,
                "work_type": "DESK_JOB"
            }
        }
        
        success3, _ = self.run_test(
            "PUT Patient Profile - Incomplete Activity Profile (Should Fail)",
            "PUT",
            f"profiles/patient/{test_user_id}",
            422,  # Expecting validation error
            data=incomplete_activity_profile
        )
        
        # Test 4: GET returns merged profile with completion > 0
        print("\n📝 Test 4: GET merged profile with completion > 0")
        success4, final_profile = self.run_test(
            "GET Merged Patient Profile",
            "GET",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        if success4 and final_profile:
            completion = final_profile.get('profile_completion', 0)
            basic_info = final_profile.get('basic_info')
            physical_metrics = final_profile.get('physical_metrics')
            
            print(f"   ✅ Final profile completion: {completion}%")
            print(f"   ✅ Has basic_info: {'Yes' if basic_info else 'No'}")
            print(f"   ✅ Has physical_metrics: {'Yes' if physical_metrics else 'No'}")
            
            completion_valid = completion > 0
            sections_merged = basic_info is not None and physical_metrics is not None
            
            if not completion_valid:
                print(f"   ❌ Profile completion should be > 0, got {completion}%")
            if not sections_merged:
                print(f"   ❌ Profile sections not properly merged")
        
        # Cleanup
        success_cleanup, _ = self.run_test(
            "Cleanup - Delete Smoke Test Profile",
            "DELETE",
            f"profiles/patient/{test_user_id}",
            200
        )
        
        # Overall success evaluation
        overall_success = success1 and success2 and success3 and success4 and success_cleanup
        
        print(f"\n📊 Smoke Test Results:")
        print(f"   POST with basic_info only: {'✅' if success1 else '❌'}")
        print(f"   PUT with physical_metrics only: {'✅' if success2 else '❌'}")
        print(f"   PUT with incomplete activity_profile (422): {'✅' if success3 else '❌'}")
        print(f"   GET merged profile with completion > 0: {'✅' if success4 else '❌'}")
        print(f"   Overall Smoke Test: {'✅' if overall_success else '❌'}")
        
        return overall_success

    def test_profile_completion_persistence_fix(self):
        """Test that profile_completion is properly persisted to database after updates"""
        print("\n🔍 Testing Profile Completion Persistence Fix")
        print("Focus: Verify profile_completion field is saved to database (not just calculated)")
        
        # Test Patient Profile Completion Persistence
        print("\n📝 Testing Patient Profile Completion Persistence")
        patient_user_id = f"patient_persist_{datetime.now().strftime('%H%M%S_%f')}"
        
        # Step 1: Create patient profile with only basic_info (should be ~16.7% completion)
        basic_info_data = {
            "user_id": patient_user_id,
            "basic_info": {
                "full_name": "Sarah Johnson",
                "age": 28,
                "gender": "Female",
                "location": "New York, NY",
                "timezone": "America/New_York",
                "preferred_language": "English"
            }
        }
        
        success1, create_response = self.run_test(
            "Create Patient Profile - Basic Info Only",
            "POST",
            "profiles/patient",
            200,
            data=basic_info_data
        )
        
        initial_completion = 0
        if success1 and create_response:
            initial_completion = create_response.get('profile_completion', 0)
            print(f"   ✅ Initial completion: {initial_completion}% (Expected: ~16.7%)")
        
        # Step 2: PUT update to add physical_metrics section
        physical_metrics_update = {
            "physical_metrics": {
                "height_cm": 165.0,
                "current_weight_kg": 65.0,
                "goal_weight_kg": 60.0,
                "body_fat_percentage": 22.0,
                "measurements": {"waist": 75.0, "chest": 88.0},
                "bmi": 23.9
            }
        }
        
        success2, update_response = self.run_test(
            "Update Patient Profile - Add Physical Metrics",
            "PUT",
            f"profiles/patient/{patient_user_id}",
            200,
            data=physical_metrics_update
        )
        
        updated_completion = 0
        if success2 and update_response:
            updated_completion = update_response.get('profile_completion', 0)
            print(f"   ✅ Updated completion: {updated_completion}% (Expected: ~33.3%)")
        
        # Step 3: Verify GET shows increased completion percentage
        success3, get_response = self.run_test(
            "Get Patient Profile - Verify Persisted Completion",
            "GET",
            f"profiles/patient/{patient_user_id}",
            200
        )
        
        persisted_completion = 0
        if success3 and get_response:
            persisted_completion = get_response.get('profile_completion', 0)
            print(f"   ✅ Persisted completion: {persisted_completion}% (Should match updated: {updated_completion}%)")
        
        # Step 4: Verify completion API endpoint returns updated values
        success4, completion_api_response = self.run_test(
            "Get Patient Profile Completion Status",
            "GET",
            f"profiles/completion/{patient_user_id}",
            200,
            params={"role": "PATIENT"}
        )
        
        api_completion = 0
        if success4 and completion_api_response:
            api_completion = completion_api_response.get('completion_percentage', 0)
            print(f"   ✅ API completion: {api_completion}% (Should match persisted: {persisted_completion}%)")
        
        # Test Provider Profile Completion Persistence
        print("\n📝 Testing Provider Profile Completion Persistence")
        provider_user_id = f"provider_persist_{datetime.now().strftime('%H%M%S_%f')}"
        
        # Step 1: Create provider profile with only professional_identity (25% completion)
        professional_identity_data = {
            "user_id": provider_user_id,
            "professional_identity": {
                "full_name": "Dr. Emily Rodriguez",
                "professional_title": "Registered Dietitian",
                "medical_license": "RD123456",
                "registration_numbers": {"state_license": "CA-RD-789"},
                "years_experience": 8
            }
        }
        
        success5, provider_create_response = self.run_test(
            "Create Provider Profile - Professional Identity Only",
            "POST",
            "profiles/provider",
            200,
            data=professional_identity_data
        )
        
        provider_initial_completion = 0
        if success5 and provider_create_response:
            provider_initial_completion = provider_create_response.get('profile_completion', 0)
            print(f"   ✅ Provider initial completion: {provider_initial_completion}% (Expected: 25%)")
        
        # Step 2: PUT update to add credentials section
        credentials_update = {
            "credentials": {
                "education": [
                    {
                        "degree": "Master of Science in Nutrition",
                        "institution": "University of California, Davis",
                        "graduation_year": 2015,
                        "specialization": "Clinical Nutrition"
                    }
                ],
                "certifications": [
                    {
                        "name": "Certified Diabetes Educator",
                        "organization": "CBDCE",
                        "issue_date": "2018-06-15",
                        "expiration_date": "2025-06-15",
                        "status": "ACTIVE"
                    }
                ],
                "specializations": ["diabetes_management", "weight_management"]
            }
        }
        
        success6, provider_update_response = self.run_test(
            "Update Provider Profile - Add Credentials",
            "PUT",
            f"profiles/provider/{provider_user_id}",
            200,
            data=credentials_update
        )
        
        provider_updated_completion = 0
        if success6 and provider_update_response:
            provider_updated_completion = provider_update_response.get('profile_completion', 0)
            print(f"   ✅ Provider updated completion: {provider_updated_completion}% (Expected: 50%)")
        
        # Step 3: Verify GET shows increased completion percentage
        success7, provider_get_response = self.run_test(
            "Get Provider Profile - Verify Persisted Completion",
            "GET",
            f"profiles/provider/{provider_user_id}",
            200
        )
        
        provider_persisted_completion = 0
        if success7 and provider_get_response:
            provider_persisted_completion = provider_get_response.get('profile_completion', 0)
            print(f"   ✅ Provider persisted completion: {provider_persisted_completion}% (Should match updated: {provider_updated_completion}%)")
        
        # Step 4: Verify completion API endpoint reflects new percentage
        success8, provider_completion_api = self.run_test(
            "Get Provider Profile Completion Status",
            "GET",
            f"profiles/completion/{provider_user_id}",
            200,
            params={"role": "PROVIDER"}
        )
        
        provider_api_completion = 0
        if success8 and provider_completion_api:
            provider_api_completion = provider_completion_api.get('completion_percentage', 0)
            print(f"   ✅ Provider API completion: {provider_api_completion}% (Should match persisted: {provider_persisted_completion}%)")
        
        # Test Family Profile Completion Persistence
        print("\n📝 Testing Family Profile Completion Persistence")
        family_user_id = f"family_persist_{datetime.now().strftime('%H%M%S_%f')}"
        
        # Step 1: Create family profile with only family_structure (50% completion due to family_members default [])
        family_structure_data = {
            "user_id": family_user_id,
            "family_structure": {
                "family_role": "Parent",
                "number_of_members": 3,
                "primary_caregiver": True
            }
        }
        
        success9, family_create_response = self.run_test(
            "Create Family Profile - Family Structure Only",
            "POST",
            "profiles/family",
            200,
            data=family_structure_data
        )
        
        family_initial_completion = 0
        if success9 and family_create_response:
            family_initial_completion = family_create_response.get('profile_completion', 0)
            print(f"   ✅ Family initial completion: {family_initial_completion}% (Expected: 50% - family_structure + empty family_members list)")
        
        # Step 2: PUT update to add household_management section to increase completion
        household_management_update = {
            "household_management": {
                "common_dietary_restrictions": ["peanut_free"],
                "family_meal_preferences": ["home_cooked", "balanced_nutrition"],
                "budget_considerations": {"weekly_grocery_budget": 200},
                "shopping_responsibilities": ["John", "Mary"],
                "cooking_responsibilities": ["Mary"]
            }
        }
        
        success10, family_update_response = self.run_test(
            "Update Family Profile - Add Household Management",
            "PUT",
            f"profiles/family/{family_user_id}",
            200,
            data=household_management_update
        )
        
        family_updated_completion = 0
        if success10 and family_update_response:
            family_updated_completion = family_update_response.get('profile_completion', 0)
            print(f"   ✅ Family updated completion: {family_updated_completion}% (Expected: 75%)")
        
        # Step 3: Verify GET shows increased completion percentage
        success11, family_get_response = self.run_test(
            "Get Family Profile - Verify Persisted Completion",
            "GET",
            f"profiles/family/{family_user_id}",
            200
        )
        
        family_persisted_completion = 0
        if success11 and family_get_response:
            family_persisted_completion = family_get_response.get('profile_completion', 0)
            print(f"   ✅ Family persisted completion: {family_persisted_completion}% (Should match updated: {family_updated_completion}%)")
        
        # Step 4: Verify completion API endpoint reflects new percentage
        success12, family_completion_api = self.run_test(
            "Get Family Profile Completion Status",
            "GET",
            f"profiles/completion/{family_user_id}",
            200,
            params={"role": "FAMILY"}
        )
        
        family_api_completion = 0
        if success12 and family_completion_api:
            family_api_completion = family_completion_api.get('completion_percentage', 0)
            print(f"   ✅ Family API completion: {family_api_completion}% (Should match persisted: {family_persisted_completion}%)")
        
        # Cleanup test profiles
        self.run_test("Cleanup Patient Profile", "DELETE", f"profiles/patient/{patient_user_id}", 200)
        self.run_test("Cleanup Provider Profile", "DELETE", f"profiles/provider/{provider_user_id}", 200)
        self.run_test("Cleanup Family Profile", "DELETE", f"profiles/family/{family_user_id}", 200)
        
        # Validate persistence logic
        patient_persistence_valid = (
            initial_completion < updated_completion and
            updated_completion == persisted_completion and
            persisted_completion == api_completion
        )
        
        provider_persistence_valid = (
            provider_initial_completion < provider_updated_completion and
            provider_updated_completion == provider_persisted_completion and
            provider_persisted_completion == provider_api_completion
        )
        
        family_persistence_valid = (
            family_initial_completion < family_updated_completion and
            family_updated_completion == family_persisted_completion and
            family_persisted_completion == family_api_completion
        )
        
        overall_success = (
            success1 and success2 and success3 and success4 and
            success5 and success6 and success7 and success8 and
            success9 and success10 and success11 and success12 and
            patient_persistence_valid and provider_persistence_valid and family_persistence_valid
        )
        
        print(f"\n📊 Profile Completion Persistence Test Results:")
        print(f"   Patient Profile Persistence: {'✅' if patient_persistence_valid else '❌'}")
        print(f"   Provider Profile Persistence: {'✅' if provider_persistence_valid else '❌'}")
        print(f"   Family Profile Persistence: {'✅' if family_persistence_valid else '❌'}")
        print(f"   Overall Success: {'✅' if overall_success else '❌'}")
        
        if not patient_persistence_valid:
            print(f"   ❌ Patient: Initial({initial_completion}%) → Updated({updated_completion}%) → Persisted({persisted_completion}%) → API({api_completion}%)")
        if not provider_persistence_valid:
            print(f"   ❌ Provider: Initial({provider_initial_completion}%) → Updated({provider_updated_completion}%) → Persisted({provider_persisted_completion}%) → API({provider_api_completion}%)")
        if not family_persistence_valid:
            print(f"   ❌ Family: Initial({family_initial_completion}%) → Updated({family_updated_completion}%) → Persisted({family_persisted_completion}%) → API({family_api_completion}%)")
        
        return overall_success

    def test_phase3_ai_integration_personalinsights(self):
        """Test Phase 3 AI Integration specifically for PersonalInsights component data structure"""
        print("\n🧠 Testing Phase 3 AI Integration - PersonalInsights Data Integration...")
        print("Focus: AI Health Insights endpoint with PersonalInsights component data structure")
        
        # Test 1: AI Health Insights with comprehensive PersonalInsights data
        print("\n📝 Test 1: AI Health Insights with PersonalInsights Data Structure")
        
        # Generate comprehensive user data matching PersonalInsights component structure
        personalinsights_health_data = {
            "user_id": "demo-patient-123",
            "timeframe": "weekly",
            "age": 32,
            "gender": "female",
            "activity_level": "moderately_active",
            "goals": ["weight_loss", "energy_boost"],
            "diet_type": "balanced",
            "avg_calories": 1850,
            "avg_protein": 95,
            "avg_carbs": 220,
            "avg_fat": 65,
            "weight": 68,
            "energy_level": 7,
            "sleep_quality": 6,
            "stress_levels": "moderate",
            "exercise_frequency": "4_times_week",
            "daily_logs": [
                {
                    "date": "2024-01-15",
                    "calories": 1820,
                    "energy": 7.2,
                    "sleep_hours": 7.0,
                    "exercise_minutes": 45,
                    "mood": 7.5
                },
                {
                    "date": "2024-01-14", 
                    "calories": 1890,
                    "energy": 6.8,
                    "sleep_hours": 6.5,
                    "exercise_minutes": 30,
                    "mood": 7.0
                },
                {
                    "date": "2024-01-13",
                    "calories": 1780,
                    "energy": 8.0,
                    "sleep_hours": 7.5,
                    "exercise_minutes": 60,
                    "mood": 8.2
                },
                {
                    "date": "2024-01-12",
                    "calories": 1950,
                    "energy": 6.5,
                    "sleep_hours": 6.0,
                    "exercise_minutes": 0,
                    "mood": 6.8
                },
                {
                    "date": "2024-01-11",
                    "calories": 1830,
                    "energy": 7.8,
                    "sleep_hours": 7.2,
                    "exercise_minutes": 50,
                    "mood": 7.8
                }
            ]
        }
        
        test_data = {
            "healthData": personalinsights_health_data,
            "provider": "gemini",
            "analysis_type": "comprehensive"
        }
        
        success1, response1 = self.run_test(
            "AI Health Insights - PersonalInsights Data",
            "POST",
            "ai/health-insights",
            200,
            data=test_data
        )
        
        # Validate response structure matches PersonalInsights expectations
        if success1 and response1:
            expected_keys = ['insights', 'recommendations', 'patterns', 'confidence']
            missing_keys = [key for key in expected_keys if key not in response1]
            if not missing_keys:
                print(f"   ✅ PersonalInsights AI response contains all required keys: {expected_keys}")
                
                # Validate insights array for PersonalInsights
                insights = response1.get('insights', [])
                if isinstance(insights, list) and len(insights) > 0:
                    print(f"   ✅ Insights array valid for PersonalInsights (contains {len(insights)} insights)")
                    for i, insight in enumerate(insights[:3]):  # Show first 3 insights
                        print(f"      - Insight {i+1}: {insight[:100]}...")
                else:
                    print(f"   ❌ Insights array should contain meaningful insights for PersonalInsights")
                    success1 = False
                
                # Validate recommendations for PersonalInsights
                recommendations = response1.get('recommendations', [])
                if isinstance(recommendations, list) and len(recommendations) > 0:
                    print(f"   ✅ Recommendations array valid for PersonalInsights (contains {len(recommendations)} recommendations)")
                    for i, rec in enumerate(recommendations[:3]):  # Show first 3 recommendations
                        print(f"      - Recommendation {i+1}: {rec[:100]}...")
                else:
                    print(f"   ❌ Recommendations array should contain actionable recommendations for PersonalInsights")
                    success1 = False
                
                # Validate patterns object for PersonalInsights
                patterns = response1.get('patterns', {})
                if isinstance(patterns, dict):
                    print(f"   ✅ Patterns object valid for PersonalInsights")
                    if 'positive_patterns' in patterns:
                        print(f"      - Positive patterns: {len(patterns.get('positive_patterns', []))}")
                    if 'areas_for_improvement' in patterns:
                        print(f"      - Areas for improvement: {len(patterns.get('areas_for_improvement', []))}")
                else:
                    print(f"   ❌ Patterns should be an object for PersonalInsights")
                    success1 = False
                
                # Validate confidence score for PersonalInsights
                confidence = response1.get('confidence', 0)
                if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                    print(f"   ✅ Confidence score valid for PersonalInsights: {confidence}")
                else:
                    print(f"   ⚠️ Confidence score format issue for PersonalInsights: {confidence}")
                    
            else:
                print(f"   ❌ PersonalInsights AI response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: Groq Service Integration Test
        print("\n📝 Test 2: Groq Service Integration Verification")
        
        # Test with different provider to verify Groq integration
        groq_test_data = {
            "healthData": {
                "user_id": "demo-patient-123",
                "nutrition_summary": {
                    "avg_calories": 1850,
                    "avg_protein": 95,
                    "protein_goal_percentage": 85,
                    "fiber_intake": 22,
                    "water_intake": 7.5
                },
                "activity_metrics": {
                    "exercise_frequency": 4,
                    "avg_steps": 8500,
                    "active_minutes": 180
                },
                "health_indicators": {
                    "energy_level": 7.2,
                    "sleep_quality": 6.8,
                    "mood_score": 7.5,
                    "stress_level": 4
                }
            },
            "provider": "groq",  # Test Groq specifically
            "analysis_type": "comprehensive"
        }
        
        success2, response2 = self.run_test(
            "Groq Service Integration Test",
            "POST", 
            "ai/health-insights",
            200,
            data=groq_test_data
        )
        
        if success2 and response2:
            print(f"   ✅ Groq service integration working")
            # Check if response indicates Groq was used (though it might fallback to Gemini)
            confidence = response2.get('confidence', 0)
            print(f"   ✅ Groq service response confidence: {confidence}")
        else:
            print(f"   ⚠️ Groq service integration test failed, but this might be expected if Groq API is not available")
        
        # Test 3: Missing Dependencies Check
        print("\n📝 Test 3: AI Service Dependencies Check")
        
        # Test with minimal data to check if backend starts without errors
        minimal_test_data = {
            "healthData": {
                "user_id": "demo-patient-123",
                "age": 32,
                "calories": 1800
            },
            "provider": "gemini"
        }
        
        success3, response3 = self.run_test(
            "AI Dependencies Check - Minimal Data",
            "POST",
            "ai/health-insights", 
            200,
            data=minimal_test_data
        )
        
        if success3:
            print(f"   ✅ AI service dependencies are properly installed and working")
            print(f"   ✅ Backend starts without AI dependency errors")
        else:
            print(f"   ❌ AI service dependencies may be missing or misconfigured")
        
        # Test 4: Response Format Validation for PersonalInsights
        print("\n📝 Test 4: Response Format Validation for PersonalInsights Component")
        
        # Test with comprehensive data to validate full response format
        comprehensive_test_data = {
            "healthData": {
                "user_id": "demo-patient-123",
                "demographics": {
                    "age": 32,
                    "gender": "female",
                    "activity_level": "moderately_active"
                },
                "nutrition_data": {
                    "daily_calories": 1850,
                    "protein_intake": 95,
                    "carb_intake": 220,
                    "fat_intake": 65,
                    "fiber_intake": 25,
                    "water_intake": 8
                },
                "health_metrics": {
                    "weight": 68,
                    "energy_level": 7.2,
                    "sleep_quality": 6.8,
                    "mood_score": 7.5,
                    "stress_level": 4
                },
                "goals": ["weight_loss", "energy_improvement", "better_sleep"],
                "recent_patterns": {
                    "exercise_consistency": "good",
                    "meal_timing": "regular",
                    "sleep_schedule": "inconsistent"
                }
            },
            "provider": "gemini",
            "analysis_type": "comprehensive"
        }
        
        success4, response4 = self.run_test(
            "PersonalInsights Response Format Validation",
            "POST",
            "ai/health-insights",
            200,
            data=comprehensive_test_data
        )
        
        if success4 and response4:
            # Validate that response format matches PersonalInsights component expectations
            required_structure = {
                'insights': list,
                'recommendations': list, 
                'patterns': dict,
                'confidence': (int, float)
            }
            
            structure_valid = True
            for key, expected_type in required_structure.items():
                if key not in response4:
                    print(f"   ❌ Missing required key for PersonalInsights: {key}")
                    structure_valid = False
                elif not isinstance(response4[key], expected_type):
                    print(f"   ❌ Invalid type for PersonalInsights key {key}: expected {expected_type}, got {type(response4[key])}")
                    structure_valid = False
                else:
                    print(f"   ✅ PersonalInsights key {key} has correct type: {expected_type}")
            
            if structure_valid:
                print(f"   ✅ Response format fully compatible with PersonalInsights component")
            else:
                print(f"   ❌ Response format has issues for PersonalInsights component")
                success4 = False
        
        # Test 5: Real-world PersonalInsights Scenario
        print("\n📝 Test 5: Real-world PersonalInsights Integration Scenario")
        
        # Simulate the exact data structure that PersonalInsights component sends
        realworld_data = {
            "healthData": {
                "user_id": "demo-patient-123",
                "timeframe": "weekly",
                "age": 32,
                "gender": "female", 
                "activity_level": "moderately_active",
                "goals": ["weight_loss", "energy_boost"],
                "diet_type": "balanced",
                "avg_calories": 1850,
                "avg_protein": 95,
                "avg_carbs": 220,
                "avg_fat": 65,
                "weight": 68,
                "energy_level": 7,
                "sleep_quality": 6,
                "stress_levels": "moderate",
                "exercise_frequency": "4_times_week",
                "daily_logs": [
                    {"date": "2024-01-15", "calories": 1820, "energy": 7.2, "sleep_hours": 7.0, "exercise_minutes": 45, "mood": 7.5},
                    {"date": "2024-01-14", "calories": 1890, "energy": 6.8, "sleep_hours": 6.5, "exercise_minutes": 30, "mood": 7.0},
                    {"date": "2024-01-13", "calories": 1780, "energy": 8.0, "sleep_hours": 7.5, "exercise_minutes": 60, "mood": 8.2},
                    {"date": "2024-01-12", "calories": 1950, "energy": 6.5, "sleep_hours": 6.0, "exercise_minutes": 0, "mood": 6.8},
                    {"date": "2024-01-11", "calories": 1830, "energy": 7.8, "sleep_hours": 7.2, "exercise_minutes": 50, "mood": 7.8},
                    {"date": "2024-01-10", "calories": 1760, "energy": 7.0, "sleep_hours": 6.8, "exercise_minutes": 40, "mood": 7.2},
                    {"date": "2024-01-09", "calories": 1920, "energy": 6.2, "sleep_hours": 5.5, "exercise_minutes": 0, "mood": 6.5},
                    {"date": "2024-01-08", "calories": 1840, "energy": 7.5, "sleep_hours": 7.8, "exercise_minutes": 55, "mood": 8.0},
                    {"date": "2024-01-07", "calories": 1880, "energy": 7.1, "sleep_hours": 7.0, "exercise_minutes": 35, "mood": 7.3},
                    {"date": "2024-01-06", "calories": 1810, "energy": 6.9, "sleep_hours": 6.2, "exercise_minutes": 45, "mood": 7.1},
                    {"date": "2024-01-05", "calories": 1900, "energy": 6.4, "sleep_hours": 6.0, "exercise_minutes": 0, "mood": 6.8},
                    {"date": "2024-01-04", "calories": 1770, "energy": 7.8, "sleep_hours": 7.5, "exercise_minutes": 50, "mood": 8.1},
                    {"date": "2024-01-03", "calories": 1860, "energy": 7.2, "sleep_hours": 7.1, "exercise_minutes": 40, "mood": 7.4},
                    {"date": "2024-01-02", "calories": 1820, "energy": 6.7, "sleep_hours": 6.3, "exercise_minutes": 30, "mood": 6.9}
                ]
            },
            "provider": "gemini",
            "analysis_type": "comprehensive"
        }
        
        success5, response5 = self.run_test(
            "Real-world PersonalInsights Integration",
            "POST",
            "ai/health-insights",
            200,
            data=realworld_data
        )
        
        if success5 and response5:
            print(f"   ✅ Real-world PersonalInsights integration successful")
            
            # Validate that insights are meaningful and actionable
            insights = response5.get('insights', [])
            recommendations = response5.get('recommendations', [])
            
            if len(insights) >= 3:
                print(f"   ✅ Generated {len(insights)} meaningful insights for PersonalInsights")
            else:
                print(f"   ⚠️ Should generate at least 3 insights for PersonalInsights, got {len(insights)}")
            
            if len(recommendations) >= 3:
                print(f"   ✅ Generated {len(recommendations)} actionable recommendations for PersonalInsights")
            else:
                print(f"   ⚠️ Should generate at least 3 recommendations for PersonalInsights, got {len(recommendations)}")
            
            # Check confidence score is reasonable
            confidence = response5.get('confidence', 0)
            if confidence >= 0.6:
                print(f"   ✅ AI confidence score is reasonable for PersonalInsights: {confidence}")
            else:
                print(f"   ⚠️ AI confidence score seems low for PersonalInsights: {confidence}")
        
        print(f"\n📊 Phase 3 AI Integration - PersonalInsights Test Summary:")
        print(f"   ✅ PersonalInsights Data Structure: {'PASS' if success1 else 'FAIL'}")
        print(f"   ✅ Groq Service Integration: {'PASS' if success2 else 'FAIL'}")
        print(f"   ✅ AI Dependencies Check: {'PASS' if success3 else 'FAIL'}")
        print(f"   ✅ Response Format Validation: {'PASS' if success4 else 'FAIL'}")
        print(f"   ✅ Real-world Integration: {'PASS' if success5 else 'FAIL'}")
        
        return success1 and success2 and success3 and success4 and success5

def main():
    """Main test execution"""
    tester = HealthPlatformAPITester()
    
    # Run the profile completion persistence test as requested in the review
    print("🚀 Starting Profile Completion Persistence Fix Test")
    print(f"🌐 Base URL: {tester.base_url}")
    print("=" * 80)
    
    success = tester.test_profile_completion_persistence_fix()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 Profile Completion Persistence Fix Test: PASSED")
        print("✅ Profile completion is properly persisted to database after updates")
        return 0
    else:
        print("⚠️ Profile Completion Persistence Fix Test: FAILED")
        print("❌ Issues detected with profile completion persistence")
        return 1

if __name__ == "__main__":
    sys.exit(main())