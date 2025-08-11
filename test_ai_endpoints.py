#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class AIEndpointTester:
    def __init__(self, base_url="https://33398250-a329-4e3b-8d5b-cfb1de4b4a42.preview.emergentagent.com/api"):
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
                            print(f"   🍎 Sample food: {food.get('name')} - {food.get('calories')} cal")
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
                    if insights:
                        print(f"   💡 Sample insight: {insights[0]}")
                else:
                    print(f"   ❌ Insights should be an array")
                    success = False
                
                # Validate recommendations array
                recommendations = response.get('recommendations', [])
                if isinstance(recommendations, list):
                    print(f"   ✅ Recommendations array valid (contains {len(recommendations)} recommendations)")
                    if recommendations:
                        print(f"   📋 Sample recommendation: {recommendations[0]}")
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
                            print(f"   🍽️ Sample meal: {suggestion.get('name')} - {suggestion.get('calories')} cal")
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
            "I ate a large apple and a handful of almonds as a snack"
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
                                print(f"   🎤 Parsed: {food_item.get('name')} - {food_item.get('quantity')}")
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

    def test_all_ai_endpoints(self):
        """Test all 4 AI API endpoints"""
        print("🚀 Starting AI API Endpoints Test")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test 1: POST /api/ai/food-recognition
        food_recognition_success = self.test_food_recognition_endpoint()
        
        # Test 2: POST /api/ai/health-insights
        health_insights_success = self.test_health_insights_endpoint()
        
        # Test 3: POST /api/ai/meal-suggestions
        meal_suggestions_success = self.test_meal_suggestions_endpoint()
        
        # Test 4: POST /api/ai/voice-command
        voice_command_success = self.test_voice_command_endpoint()
        
        # Print summary
        print(f"\n📊 AI API Endpoints Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Component-wise results
        components = [
            ("Food Recognition", food_recognition_success),
            ("Health Insights", health_insights_success),
            ("Meal Suggestions", meal_suggestions_success),
            ("Voice Command", voice_command_success)
        ]
        
        print(f"\n📋 AI Endpoint Results:")
        for component, success in components:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {component}: {status}")
        
        overall_success = all(success for _, success in components)
        print(f"\n🎯 Overall Result: {'✅ ALL AI ENDPOINTS WORKING' if overall_success else '❌ SOME AI ENDPOINTS FAILED'}")
        
        return overall_success

if __name__ == "__main__":
    tester = AIEndpointTester()
    success = tester.test_all_ai_endpoints()
    sys.exit(0 if success else 1)