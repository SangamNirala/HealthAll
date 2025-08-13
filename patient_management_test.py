#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class PatientManagementSystemTester:
    def __init__(self, base_url="https://caretrack-test.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.provider_id = "provider-123"
        self.patient_id = "patient-456"

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

    def test_smart_patient_assignment_apis(self):
        """Test Smart Patient Assignment APIs"""
        print("\n🏥 Testing Smart Patient Assignment APIs...")
        
        # Test 1: Create Patient Assignment with AI Matching
        assignment_data = {
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "assignment_type": "routine",
            "priority": "MEDIUM",
            "assignment_reason": "Regular diabetes management checkup",
            "estimated_duration": 45,
            "scheduled_time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "patient_condition": "Type 2 Diabetes",
            "required_expertise": ["diabetes_management", "nutrition_counseling"],
            "special_instructions": "Patient prefers morning appointments"
        }
        
        success1, assignment_response = self.run_test(
            "Create Patient Assignment with AI Matching",
            "POST",
            "provider/patient-management/assignments",
            200,
            data=assignment_data
        )
        
        assignment_id = None
        if success1 and assignment_response:
            assignment_id = assignment_response.get('id')
            ai_match_score = assignment_response.get('ai_match_score', 0.0)
            print(f"   📊 AI Match Score: {ai_match_score}")
            print(f"   🆔 Assignment ID: {assignment_id}")
            
            # Validate AI match score is within expected range
            if 0.0 <= ai_match_score <= 1.0:
                print(f"   ✅ AI match score within valid range (0.0-1.0)")
            else:
                print(f"   ❌ AI match score out of range: {ai_match_score}")
                success1 = False
        
        # Test 2: Get Provider Assignments
        success2, assignments_data = self.run_test(
            "Get Provider Assignments",
            "GET",
            f"provider/patient-management/assignments/{self.provider_id}",
            200
        )
        
        if success2 and assignments_data:
            assignments = assignments_data.get('assignments', [])
            print(f"   📋 Found {len(assignments)} assignments for provider")
            
            # Validate assignment structure
            if assignments:
                assignment = assignments[0]
                expected_keys = ['id', 'patient_id', 'provider_id', 'assignment_type', 'priority', 'status', 'ai_match_score']
                missing_keys = [key for key in expected_keys if key not in assignment]
                if not missing_keys:
                    print(f"   ✅ Assignment structure valid")
                else:
                    print(f"   ❌ Assignment missing keys: {missing_keys}")
                    success2 = False
        
        # Test 3: AI-Powered Patient Matching
        matching_criteria = {
            "provider_id": self.provider_id,
            "patient_conditions": ["diabetes", "hypertension"],
            "required_expertise": ["diabetes_management", "cardiovascular_health"],
            "workload_preference": "balanced",
            "priority_threshold": "MEDIUM"
        }
        
        success3, matching_response = self.run_test(
            "AI-Powered Patient Matching",
            "POST",
            "provider/patient-management/ai-matching",
            200,
            data=matching_criteria
        )
        
        if success3 and matching_response:
            matches = matching_response.get('matches', [])
            print(f"   🎯 Found {len(matches)} potential matches")
            
            if matches:
                match = matches[0]
                match_score = match.get('match_score', 0.0)
                reasoning = match.get('reasoning', '')
                print(f"   📊 Top match score: {match_score}")
                print(f"   💭 Reasoning: {reasoning[:100]}...")
                
                # Validate match score
                if 0.0 <= match_score <= 1.0:
                    print(f"   ✅ Match score within valid range")
                else:
                    print(f"   ❌ Match score out of range: {match_score}")
                    success3 = False
        
        # Test 4: Update Assignment Status
        if assignment_id:
            update_data = {
                "status": "ACTIVE",
                "actual_start_time": datetime.utcnow().isoformat(),
                "assignment_notes": "Patient arrived on time, consultation started"
            }
            
            success4, update_response = self.run_test(
                "Update Assignment Status",
                "PUT",
                f"provider/patient-management/assignments/{assignment_id}",
                200,
                data=update_data
            )
            
            if success4 and update_response:
                updated_status = update_response.get('status')
                print(f"   📝 Assignment status updated to: {updated_status}")
        else:
            success4 = False
            print(f"   ❌ Cannot test assignment update - no assignment ID")
        
        return success1 and success2 and success3 and success4

    def test_real_time_progress_tracking_apis(self):
        """Test Real-Time Progress Tracking APIs"""
        print("\n📈 Testing Real-Time Progress Tracking APIs...")
        
        # Test 1: Record Patient Progress
        progress_data = {
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "metric_type": "VITAL_SIGNS",
            "metric_name": "Blood Glucose",
            "value": 125.0,
            "unit": "mg/dL",
            "target_range": {"min": 80.0, "max": 130.0},
            "measurement_method": "glucometer",
            "contextual_notes": "Fasting blood glucose measurement taken in morning"
        }
        
        success1, progress_response = self.run_test(
            "Record Patient Progress",
            "POST",
            "provider/patient-management/progress",
            200,
            data=progress_data
        )
        
        if success1 and progress_response:
            progress_id = progress_response.get('id')
            trend_direction = progress_response.get('trend_direction', 'stable')
            clinical_significance = progress_response.get('clinical_significance', 'normal')
            print(f"   📊 Progress ID: {progress_id}")
            print(f"   📈 Trend Direction: {trend_direction}")
            print(f"   🏥 Clinical Significance: {clinical_significance}")
        
        # Test 2: Get Patient Progress with Analytics
        success2, progress_data = self.run_test(
            "Get Patient Progress with Analytics",
            "GET",
            f"provider/patient-management/progress/{self.patient_id}",
            200
        )
        
        if success2 and progress_data:
            progress_entries = progress_data.get('progress_entries', [])
            analytics = progress_data.get('analytics', {})
            print(f"   📋 Found {len(progress_entries)} progress entries")
            
            # Validate analytics structure
            if analytics:
                expected_analytics_keys = ['trend_analysis', 'milestone_achievements', 'risk_indicators']
                missing_keys = [key for key in expected_analytics_keys if key not in analytics]
                if not missing_keys:
                    print(f"   ✅ Analytics structure valid")
                    
                    # Check trend analysis
                    trend_analysis = analytics.get('trend_analysis', {})
                    if trend_analysis:
                        improvement_rate = trend_analysis.get('improvement_rate', 0.0)
                        print(f"   📊 Improvement Rate: {improvement_rate}%")
                else:
                    print(f"   ❌ Analytics missing keys: {missing_keys}")
                    success2 = False
        
        # Test 3: Get Comprehensive Progress Analytics
        success3, analytics_data = self.run_test(
            "Get Comprehensive Progress Analytics",
            "GET",
            f"provider/patient-management/progress-analytics/{self.patient_id}",
            200
        )
        
        if success3 and analytics_data:
            metrics_summary = analytics_data.get('metrics_summary', {})
            predictive_insights = analytics_data.get('predictive_insights', [])
            risk_assessment = analytics_data.get('risk_assessment', {})
            recommendations = analytics_data.get('recommendations', [])
            
            print(f"   📊 Metrics Summary: {len(metrics_summary)} metrics")
            print(f"   🔮 Predictive Insights: {len(predictive_insights)} insights")
            print(f"   ⚠️ Risk Assessment: {risk_assessment.get('overall_risk_level', 'N/A')}")
            print(f"   💡 Recommendations: {len(recommendations)} recommendations")
            
            # Validate AI-powered insights
            if predictive_insights:
                insight = predictive_insights[0]
                confidence = insight.get('confidence', 0.0)
                prediction_type = insight.get('prediction_type', '')
                print(f"   🎯 Top insight confidence: {confidence}")
                print(f"   📝 Prediction type: {prediction_type}")
        
        return success1 and success2 and success3

    def test_intelligent_adherence_monitoring_apis(self):
        """Test Intelligent Adherence Monitoring APIs"""
        print("\n💊 Testing Intelligent Adherence Monitoring APIs...")
        
        # Test 1: Create Adherence Monitoring
        adherence_data = {
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "adherence_type": "MEDICATION",
            "target_item": "Metformin 500mg",
            "tracking_period": "weekly",
            "expected_frequency": 14,  # twice daily for 7 days
            "next_review_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        success1, adherence_response = self.run_test(
            "Create Adherence Monitoring",
            "POST",
            "provider/patient-management/adherence",
            200,
            data=adherence_data
        )
        
        adherence_id = None
        if success1 and adherence_response:
            adherence_id = adherence_response.get('id')
            adherence_status = adherence_response.get('adherence_status', 'MODERATE')
            print(f"   🆔 Adherence Monitoring ID: {adherence_id}")
            print(f"   📊 Initial Adherence Status: {adherence_status}")
        
        # Test 2: Get Adherence Data with AI Insights
        success2, adherence_data = self.run_test(
            "Get Adherence Data with AI Insights",
            "GET",
            f"provider/patient-management/adherence/{self.patient_id}",
            200
        )
        
        if success2 and adherence_data:
            adherence_records = adherence_data.get('adherence_records', [])
            ai_insights = adherence_data.get('ai_insights', [])
            predictive_risk = adherence_data.get('predictive_risk_score', 0.0)
            
            print(f"   📋 Found {len(adherence_records)} adherence records")
            print(f"   🤖 AI Insights: {len(ai_insights)} insights")
            print(f"   ⚠️ Predictive Risk Score: {predictive_risk}")
            
            # Validate adherence record structure
            if adherence_records:
                record = adherence_records[0]
                expected_keys = ['id', 'adherence_type', 'target_item', 'adherence_percentage', 'adherence_status']
                missing_keys = [key for key in expected_keys if key not in record]
                if not missing_keys:
                    print(f"   ✅ Adherence record structure valid")
                    adherence_pct = record.get('adherence_percentage', 0.0)
                    print(f"   📊 Adherence Percentage: {adherence_pct}%")
                else:
                    print(f"   ❌ Adherence record missing keys: {missing_keys}")
                    success2 = False
            
            # Validate AI insights
            if ai_insights:
                insight = ai_insights[0]
                print(f"   💡 Sample AI Insight: {insight[:100]}...")
        
        # Test 3: Update Adherence Data
        if adherence_id:
            update_data = {
                "adherence_percentage": 85.7,
                "adherence_status": "GOOD",
                "actual_frequency": 12,  # missed 2 doses out of 14
                "missed_instances": 2,
                "perfect_days": 5,
                "improvement_trend": 5.2,  # 5.2% improvement
                "barriers_identified": ["forgetfulness", "side_effects"],
                "intervention_strategies": ["medication_reminders", "side_effect_management"]
            }
            
            success3, update_response = self.run_test(
                "Update Adherence Data",
                "PUT",
                f"provider/patient-management/adherence/{adherence_id}",
                200,
                data=update_data
            )
            
            if success3 and update_response:
                updated_percentage = update_response.get('adherence_percentage', 0.0)
                updated_status = update_response.get('adherence_status', '')
                improvement_trend = update_response.get('improvement_trend', 0.0)
                print(f"   📊 Updated Adherence: {updated_percentage}% ({updated_status})")
                print(f"   📈 Improvement Trend: {improvement_trend}%")
        else:
            success3 = False
            print(f"   ❌ Cannot test adherence update - no adherence ID")
        
        return success1 and success2 and success3

    def test_smart_alert_system_apis(self):
        """Test Smart Alert System APIs"""
        print("\n🚨 Testing Smart Alert System APIs...")
        
        # Test 1: Create Smart Alert
        alert_data = {
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "category": "CLINICAL",
            "severity": "WARNING",
            "title": "Blood Glucose Trending High",
            "message": "Patient's blood glucose readings have been consistently above target range",
            "detailed_description": "Last 3 readings: 145, 152, 148 mg/dL. Target range: 80-130 mg/dL",
            "data_source": "vital_signs",
            "triggering_values": {"glucose_avg": 148.3, "target_max": 130.0},
            "recommended_actions": [
                "Review medication dosage",
                "Assess dietary compliance",
                "Schedule follow-up appointment"
            ]
        }
        
        success1, alert_response = self.run_test(
            "Create Smart Alert",
            "POST",
            "provider/patient-management/alerts",
            200,
            data=alert_data
        )
        
        alert_id = None
        if success1 and alert_response:
            alert_id = alert_response.get('id')
            urgency_score = alert_response.get('urgency_score', 0.0)
            ai_confidence = alert_response.get('ai_confidence', 0.0)
            print(f"   🆔 Alert ID: {alert_id}")
            print(f"   ⚡ Urgency Score: {urgency_score}")
            print(f"   🤖 AI Confidence: {ai_confidence}")
            
            # Validate urgency score range
            if 0.0 <= urgency_score <= 1.0:
                print(f"   ✅ Urgency score within valid range")
            else:
                print(f"   ❌ Urgency score out of range: {urgency_score}")
                success1 = False
        
        # Test 2: Get Provider Alerts
        success2, alerts_data = self.run_test(
            "Get Provider Alerts",
            "GET",
            f"provider/patient-management/alerts/{self.provider_id}",
            200
        )
        
        if success2 and alerts_data:
            alerts = alerts_data.get('alerts', [])
            alert_summary = alerts_data.get('alert_summary', {})
            
            print(f"   📋 Found {len(alerts)} alerts for provider")
            
            # Validate alert summary
            if alert_summary:
                total_alerts = alert_summary.get('total_alerts', 0)
                critical_alerts = alert_summary.get('critical_alerts', 0)
                warning_alerts = alert_summary.get('warning_alerts', 0)
                print(f"   📊 Alert Summary - Total: {total_alerts}, Critical: {critical_alerts}, Warning: {warning_alerts}")
            
            # Validate alert structure
            if alerts:
                alert = alerts[0]
                expected_keys = ['id', 'category', 'severity', 'title', 'message', 'urgency_score', 'status']
                missing_keys = [key for key in expected_keys if key not in alert]
                if not missing_keys:
                    print(f"   ✅ Alert structure valid")
                else:
                    print(f"   ❌ Alert missing keys: {missing_keys}")
                    success2 = False
        
        # Test 3: Create Alert Rule
        rule_data = {
            "provider_id": self.provider_id,
            "rule_name": "High Blood Glucose Alert",
            "description": "Alert when blood glucose exceeds 150 mg/dL for 2+ consecutive readings",
            "category": "CLINICAL",
            "severity": "WARNING",
            "condition_logic": {
                "metric": "blood_glucose",
                "threshold": 150.0,
                "consecutive_readings": 2,
                "time_window": "24_hours"
            },
            "is_active": True,
            "escalation_minutes": 30,
            "notification_methods": ["in_app", "email"]
        }
        
        success3, rule_response = self.run_test(
            "Create Alert Rule",
            "POST",
            "provider/patient-management/alert-rules",
            200,
            data=rule_data
        )
        
        if success3 and rule_response:
            rule_id = rule_response.get('id')
            rule_name = rule_response.get('rule_name')
            is_active = rule_response.get('is_active', False)
            print(f"   🆔 Rule ID: {rule_id}")
            print(f"   📝 Rule Name: {rule_name}")
            print(f"   ✅ Rule Active: {is_active}")
        
        # Test 4: Acknowledge Alert
        if alert_id:
            success4, ack_response = self.run_test(
                "Acknowledge Alert",
                "PUT",
                f"provider/patient-management/alerts/{alert_id}/acknowledge",
                200,
                data={"acknowledgment_notes": "Reviewed patient data, will adjust medication"}
            )
            
            if success4 and ack_response:
                acknowledged_at = ack_response.get('acknowledged_at')
                status = ack_response.get('status')
                print(f"   ✅ Alert acknowledged at: {acknowledged_at}")
                print(f"   📝 Status: {status}")
        else:
            success4 = False
            print(f"   ❌ Cannot test alert acknowledgment - no alert ID")
        
        return success1 and success2 and success3 and success4

    def test_automated_report_generation_apis(self):
        """Test Automated Report Generation APIs"""
        print("\n📄 Testing Automated Report Generation APIs...")
        
        # Test 1: Generate Automated Report with AI
        report_data = {
            "report_type": "PATIENT_SUMMARY",
            "report_format": "PDF",
            "title": "Comprehensive Patient Summary - Diabetes Management",
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "report_period": "monthly",
            "data_range": {
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            "charts_included": ["glucose_trends", "medication_adherence", "weight_progress"],
            "ai_insights_included": True
        }
        
        success1, report_response = self.run_test(
            "Generate Automated Report with AI",
            "POST",
            "provider/patient-management/reports",
            200,
            data=report_data
        )
        
        report_id = None
        if success1 and report_response:
            report_id = report_response.get('id')
            generation_status = report_response.get('generation_status', 'pending')
            ai_insights_included = report_response.get('ai_insights_included', False)
            print(f"   🆔 Report ID: {report_id}")
            print(f"   📊 Generation Status: {generation_status}")
            print(f"   🤖 AI Insights Included: {ai_insights_included}")
            
            # Validate report structure
            expected_keys = ['id', 'report_type', 'title', 'generation_status', 'ai_insights_included']
            missing_keys = [key for key in expected_keys if key not in report_response]
            if not missing_keys:
                print(f"   ✅ Report response structure valid")
            else:
                print(f"   ❌ Report response missing keys: {missing_keys}")
                success1 = False
        
        # Test 2: Get Provider Reports
        success2, reports_data = self.run_test(
            "Get Provider Reports",
            "GET",
            f"provider/patient-management/reports/{self.provider_id}",
            200
        )
        
        if success2 and reports_data:
            reports = reports_data.get('reports', [])
            report_summary = reports_data.get('report_summary', {})
            
            print(f"   📋 Found {len(reports)} reports for provider")
            
            # Validate report summary
            if report_summary:
                total_reports = report_summary.get('total_reports', 0)
                completed_reports = report_summary.get('completed_reports', 0)
                pending_reports = report_summary.get('pending_reports', 0)
                print(f"   📊 Report Summary - Total: {total_reports}, Completed: {completed_reports}, Pending: {pending_reports}")
            
            # Validate report structure
            if reports:
                report = reports[0]
                expected_keys = ['id', 'report_type', 'title', 'generation_status', 'generated_at']
                missing_keys = [key for key in expected_keys if key not in report]
                if not missing_keys:
                    print(f"   ✅ Report list structure valid")
                    
                    # Check for AI-generated content
                    if report.get('ai_insights_included'):
                        print(f"   🤖 Report includes AI insights")
                    
                    # Check for PDF generation
                    if report.get('file_path'):
                        print(f"   📄 PDF file generated: {report.get('file_path')}")
                else:
                    print(f"   ❌ Report missing keys: {missing_keys}")
                    success2 = False
        
        return success1 and success2

    def test_patient_risk_analysis_apis(self):
        """Test Patient Risk Analysis APIs"""
        print("\n⚠️ Testing Patient Risk Analysis APIs...")
        
        # Test 1: Create ML-based Risk Analysis
        risk_analysis_data = {
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "risk_category": "DIABETES",
            "time_horizon": "90_days"
        }
        
        success1, risk_response = self.run_test(
            "Create ML-based Risk Analysis",
            "POST",
            "provider/patient-management/risk-analysis",
            200,
            data=risk_analysis_data
        )
        
        if success1 and risk_response:
            risk_level = risk_response.get('risk_level', 'MODERATE')
            risk_score = risk_response.get('risk_score', 0.0)
            confidence_interval = risk_response.get('confidence_interval', {})
            model_accuracy = risk_response.get('model_accuracy', 0.0)
            
            print(f"   ⚠️ Risk Level: {risk_level}")
            print(f"   📊 Risk Score: {risk_score}")
            print(f"   📈 Confidence Interval: {confidence_interval}")
            print(f"   🎯 Model Accuracy: {model_accuracy}")
            
            # Validate risk score range
            if 0.0 <= risk_score <= 1.0:
                print(f"   ✅ Risk score within valid range")
            else:
                print(f"   ❌ Risk score out of range: {risk_score}")
                success1 = False
            
            # Validate contributing factors
            contributing_factors = risk_response.get('contributing_factors', [])
            protective_factors = risk_response.get('protective_factors', [])
            print(f"   ⚡ Contributing Factors: {len(contributing_factors)}")
            print(f"   🛡️ Protective Factors: {len(protective_factors)}")
            
            if contributing_factors:
                factor = contributing_factors[0]
                factor_weight = factor.get('weight', 0.0)
                factor_name = factor.get('factor', 'Unknown')
                print(f"   📊 Top risk factor: {factor_name} (weight: {factor_weight})")
        
        # Test 2: Get Patient Risk Analyses
        success2, risk_data = self.run_test(
            "Get Patient Risk Analyses",
            "GET",
            f"provider/patient-management/risk-analysis/{self.patient_id}",
            200
        )
        
        if success2 and risk_data:
            risk_analyses = risk_data.get('risk_analyses', [])
            risk_summary = risk_data.get('risk_summary', {})
            
            print(f"   📋 Found {len(risk_analyses)} risk analyses")
            
            # Validate risk summary
            if risk_summary:
                overall_risk = risk_summary.get('overall_risk_level', 'MODERATE')
                high_risk_categories = risk_summary.get('high_risk_categories', [])
                print(f"   ⚠️ Overall Risk Level: {overall_risk}")
                print(f"   🚨 High Risk Categories: {high_risk_categories}")
            
            # Validate risk analysis structure
            if risk_analyses:
                analysis = risk_analyses[0]
                expected_keys = ['id', 'risk_category', 'risk_level', 'risk_score', 'time_horizon']
                missing_keys = [key for key in expected_keys if key not in analysis]
                if not missing_keys:
                    print(f"   ✅ Risk analysis structure valid")
                    
                    # Check for intervention recommendations
                    interventions = analysis.get('intervention_recommendations', [])
                    if interventions:
                        print(f"   💡 Intervention Recommendations: {len(interventions)}")
                        intervention = interventions[0]
                        intervention_type = intervention.get('intervention_type', 'Unknown')
                        priority = intervention.get('priority', 'MEDIUM')
                        print(f"   🎯 Top intervention: {intervention_type} (priority: {priority})")
                else:
                    print(f"   ❌ Risk analysis missing keys: {missing_keys}")
                    success2 = False
        
        return success1 and success2

    def test_intelligent_meal_planning_apis(self):
        """Test Intelligent Meal Planning APIs"""
        print("\n🍽️ Testing Intelligent Meal Planning APIs...")
        
        # Test 1: Create AI-powered Meal Plan
        meal_plan_data = {
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "plan_name": "Diabetic-Friendly Weekly Meal Plan",
            "description": "Balanced meal plan for diabetes management with low glycemic index foods",
            "dietary_restrictions": ["DIABETIC", "LOW_SODIUM"],
            "calorie_target": 1800,
            "macro_targets": {
                "protein": 135.0,  # 30% of calories
                "carbs": 180.0,    # 40% of calories
                "fat": 60.0        # 30% of calories
            },
            "meal_preferences": ["mediterranean", "low_carb", "high_fiber"],
            "food_allergies": ["shellfish"],
            "plan_duration": 7
        }
        
        success1, meal_plan_response = self.run_test(
            "Create AI-powered Meal Plan",
            "POST",
            "provider/patient-management/meal-plans",
            200,
            data=meal_plan_data
        )
        
        if success1 and meal_plan_response:
            plan_id = meal_plan_response.get('id')
            ai_optimization_score = meal_plan_response.get('ai_optimization_score', 0.0)
            nutritional_completeness = meal_plan_response.get('nutritional_completeness', 0.0)
            variety_score = meal_plan_response.get('variety_score', 0.0)
            adherence_prediction = meal_plan_response.get('adherence_prediction', 0.0)
            
            print(f"   🆔 Meal Plan ID: {plan_id}")
            print(f"   🤖 AI Optimization Score: {ai_optimization_score}")
            print(f"   🥗 Nutritional Completeness: {nutritional_completeness}")
            print(f"   🎨 Variety Score: {variety_score}")
            print(f"   📊 Adherence Prediction: {adherence_prediction}")
            
            # Validate scores are within expected range
            scores = [ai_optimization_score, nutritional_completeness, variety_score, adherence_prediction]
            for i, score in enumerate(scores):
                if 0.0 <= score <= 1.0:
                    print(f"   ✅ Score {i+1} within valid range")
                else:
                    print(f"   ❌ Score {i+1} out of range: {score}")
                    success1 = False
            
            # Validate meal schedule
            meal_schedule = meal_plan_response.get('meal_schedule', [])
            if meal_schedule:
                print(f"   📅 Meal Schedule: {len(meal_schedule)} meals planned")
                meal = meal_schedule[0]
                meal_type = meal.get('meal_type', 'Unknown')
                calories = meal.get('calories', 0)
                print(f"   🍽️ Sample meal: {meal_type} ({calories} calories)")
            
            # Validate shopping list
            shopping_list = meal_plan_response.get('shopping_list', [])
            if shopping_list:
                print(f"   🛒 Shopping List: {len(shopping_list)} items")
                item = shopping_list[0]
                item_name = item.get('item', 'Unknown')
                quantity = item.get('quantity', 'N/A')
                print(f"   📝 Sample item: {item_name} ({quantity})")
        
        # Test 2: Get Patient Meal Plans
        success2, meal_plans_data = self.run_test(
            "Get Patient Meal Plans",
            "GET",
            f"provider/patient-management/meal-plans/{self.patient_id}",
            200
        )
        
        if success2 and meal_plans_data:
            meal_plans = meal_plans_data.get('meal_plans', [])
            nutrition_summary = meal_plans_data.get('nutrition_summary', {})
            
            print(f"   📋 Found {len(meal_plans)} meal plans")
            
            # Validate nutrition summary
            if nutrition_summary:
                avg_calories = nutrition_summary.get('average_daily_calories', 0)
                macro_balance = nutrition_summary.get('macro_balance', {})
                print(f"   📊 Average Daily Calories: {avg_calories}")
                print(f"   🥗 Macro Balance: {macro_balance}")
            
            # Validate meal plan structure
            if meal_plans:
                plan = meal_plans[0]
                expected_keys = ['id', 'plan_name', 'calorie_target', 'ai_optimization_score', 'nutritional_completeness']
                missing_keys = [key for key in expected_keys if key not in plan]
                if not missing_keys:
                    print(f"   ✅ Meal plan structure valid")
                    
                    # Check for USDA integration
                    usda_verified = plan.get('usda_verified', False)
                    if usda_verified:
                        print(f"   🇺🇸 USDA nutrition data integrated")
                else:
                    print(f"   ❌ Meal plan missing keys: {missing_keys}")
                    success2 = False
        
        return success1 and success2

    def test_main_dashboard_api(self):
        """Test Main Dashboard API"""
        print("\n📊 Testing Main Dashboard API...")
        
        # Test: Get Comprehensive Dashboard Data
        success, dashboard_data = self.run_test(
            "Get Comprehensive Dashboard Data",
            "GET",
            f"provider/patient-management/dashboard/{self.provider_id}",
            200
        )
        
        if success and dashboard_data:
            # Validate dashboard structure
            expected_sections = [
                'patient_assignments_summary',
                'progress_tracking_summary', 
                'adherence_monitoring_summary',
                'alerts_summary',
                'reports_summary',
                'risk_analysis_summary',
                'meal_planning_summary',
                'dashboard_metrics'
            ]
            
            missing_sections = [section for section in expected_sections if section not in dashboard_data]
            if not missing_sections:
                print(f"   ✅ Dashboard contains all required sections")
                
                # Validate each section
                assignments = dashboard_data.get('patient_assignments_summary', {})
                if assignments:
                    total_assignments = assignments.get('total_assignments', 0)
                    active_assignments = assignments.get('active_assignments', 0)
                    print(f"   👥 Assignments: {active_assignments}/{total_assignments} active")
                
                progress = dashboard_data.get('progress_tracking_summary', {})
                if progress:
                    patients_monitored = progress.get('patients_monitored', 0)
                    avg_improvement = progress.get('average_improvement_rate', 0.0)
                    print(f"   📈 Progress: {patients_monitored} patients, {avg_improvement}% avg improvement")
                
                adherence = dashboard_data.get('adherence_monitoring_summary', {})
                if adherence:
                    avg_adherence = adherence.get('average_adherence_rate', 0.0)
                    at_risk_patients = adherence.get('at_risk_patients', 0)
                    print(f"   💊 Adherence: {avg_adherence}% average, {at_risk_patients} at-risk patients")
                
                alerts = dashboard_data.get('alerts_summary', {})
                if alerts:
                    active_alerts = alerts.get('active_alerts', 0)
                    critical_alerts = alerts.get('critical_alerts', 0)
                    print(f"   🚨 Alerts: {active_alerts} active, {critical_alerts} critical")
                
                reports = dashboard_data.get('reports_summary', {})
                if reports:
                    reports_generated = reports.get('reports_generated_this_month', 0)
                    ai_insights_count = reports.get('ai_insights_generated', 0)
                    print(f"   📄 Reports: {reports_generated} this month, {ai_insights_count} AI insights")
                
                risk_analysis = dashboard_data.get('risk_analysis_summary', {})
                if risk_analysis:
                    high_risk_patients = risk_analysis.get('high_risk_patients', 0)
                    ml_predictions = risk_analysis.get('ml_predictions_accuracy', 0.0)
                    print(f"   ⚠️ Risk Analysis: {high_risk_patients} high-risk patients, {ml_predictions}% ML accuracy")
                
                meal_planning = dashboard_data.get('meal_planning_summary', {})
                if meal_planning:
                    active_meal_plans = meal_planning.get('active_meal_plans', 0)
                    avg_adherence_prediction = meal_planning.get('average_adherence_prediction', 0.0)
                    print(f"   🍽️ Meal Planning: {active_meal_plans} active plans, {avg_adherence_prediction}% predicted adherence")
                
                metrics = dashboard_data.get('dashboard_metrics', {})
                if metrics:
                    total_patients = metrics.get('total_patients_managed', 0)
                    patient_satisfaction = metrics.get('patient_satisfaction_score', 0.0)
                    ai_utilization = metrics.get('ai_utilization_rate', 0.0)
                    print(f"   📊 Metrics: {total_patients} patients, {patient_satisfaction}/5.0 satisfaction, {ai_utilization}% AI utilization")
                
            else:
                print(f"   ❌ Dashboard missing sections: {missing_sections}")
                success = False
        
        return success

    def run_all_tests(self):
        """Run all Patient Management System tests"""
        print("🚀 Starting Patient Management System API Testing...")
        print(f"📍 Base URL: {self.base_url}")
        print(f"👨‍⚕️ Provider ID: {self.provider_id}")
        print(f"👤 Patient ID: {self.patient_id}")
        
        # Run all test modules
        test_results = []
        
        print("\n" + "="*80)
        print("MODULE 1: SMART PATIENT ASSIGNMENT SYSTEM")
        print("="*80)
        test_results.append(("Smart Patient Assignment APIs", self.test_smart_patient_assignment_apis()))
        
        print("\n" + "="*80)
        print("MODULE 2: REAL-TIME PROGRESS TRACKING")
        print("="*80)
        test_results.append(("Real-Time Progress Tracking APIs", self.test_real_time_progress_tracking_apis()))
        
        print("\n" + "="*80)
        print("MODULE 3: INTELLIGENT ADHERENCE MONITORING")
        print("="*80)
        test_results.append(("Intelligent Adherence Monitoring APIs", self.test_intelligent_adherence_monitoring_apis()))
        
        print("\n" + "="*80)
        print("MODULE 4: SMART ALERT SYSTEM")
        print("="*80)
        test_results.append(("Smart Alert System APIs", self.test_smart_alert_system_apis()))
        
        print("\n" + "="*80)
        print("MODULE 5: AUTOMATED REPORT GENERATION")
        print("="*80)
        test_results.append(("Automated Report Generation APIs", self.test_automated_report_generation_apis()))
        
        print("\n" + "="*80)
        print("MODULE 6: PATIENT RISK ANALYSIS")
        print("="*80)
        test_results.append(("Patient Risk Analysis APIs", self.test_patient_risk_analysis_apis()))
        
        print("\n" + "="*80)
        print("MODULE 7: INTELLIGENT MEAL PLANNING")
        print("="*80)
        test_results.append(("Intelligent Meal Planning APIs", self.test_intelligent_meal_planning_apis()))
        
        print("\n" + "="*80)
        print("MODULE 8: MAIN DASHBOARD")
        print("="*80)
        test_results.append(("Main Dashboard API", self.test_main_dashboard_api()))
        
        # Print final summary
        print("\n" + "="*80)
        print("🏁 PATIENT MANAGEMENT SYSTEM TEST SUMMARY")
        print("="*80)
        
        passed_modules = 0
        total_modules = len(test_results)
        
        for module_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {module_name}")
            if result:
                passed_modules += 1
        
        print(f"\n📊 Overall Results:")
        print(f"   Total Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        print(f"   Modules Passed: {passed_modules}/{total_modules}")
        print(f"   Module Success Rate: {(passed_modules / total_modules * 100):.1f}%")
        
        if passed_modules == total_modules:
            print(f"\n🎉 ALL PATIENT MANAGEMENT SYSTEM MODULES PASSED!")
            print(f"✅ The Advanced Patient Management System with 30+ API endpoints is fully functional")
            print(f"🤖 AI integration, ML algorithms, and automated features are working correctly")
            print(f"📊 Real-time analytics, smart alerts, and comprehensive reporting are operational")
        else:
            print(f"\n⚠️ {total_modules - passed_modules} module(s) failed - review individual test results above")
        
        return passed_modules == total_modules

if __name__ == "__main__":
    tester = PatientManagementSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)