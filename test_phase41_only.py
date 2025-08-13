#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import HealthPlatformAPITester

def main():
    """Run only Phase 4.1 Enhanced Clinical Dashboard tests"""
    print("🚀 Starting Phase 4.1 Enhanced Clinical Dashboard Re-Testing...")
    
    # Initialize tester with the correct backend URL
    tester = HealthPlatformAPITester("https://caretrack-test.preview.emergentagent.com/api")
    
    # Run only the Phase 4.1 specific test
    success = tester.test_phase41_clinical_dashboard_retesting_specific()
    
    # Print final summary
    print("\n" + "=" * 80)
    print("📊 PHASE 4.1 ENHANCED CLINICAL DASHBOARD RE-TESTING COMPLETE")
    print(f"Overall Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    if tester.tests_run > 0:
        success_rate = (tester.tests_passed / tester.tests_run) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    print("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())