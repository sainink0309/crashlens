#!/usr/bin/env python3
"""
🧪 6. Unit Test Coverage for Production-Grade Suppression & Priority Logic
Covers overlapping detections, suppression precedence, and correct trace ownership.
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add the project root to the path for testing
sys.path.insert(0, str(Path(__file__).parent))

from crashlens.cli import SuppressionEngine, DETECTOR_PRIORITY, DETECTOR_DISPLAY_NAMES


def test_priority_suppression():
    """🔁 6. Test overlapping detections and suppression precedence"""
    print("🧪 PRODUCTION-GRADE SUPPRESSION & PRIORITY LOGIC TEST")
    print("=" * 65)
    
    base_time = datetime.now()
    
    # Create overlapping test data - same traces detected by multiple detectors
    test_detections = {
        # Retry Loop Detection (Priority 1 - Highest)
        'RetryLoopDetector': [
            {
                'type': 'retry_loop',
                'trace_id': 'overlap_trace_1',
                'severity': 'high', 
                'description': 'Retry loop with 4 identical calls',
                'waste_cost': 0.012,
                'waste_tokens': 45,
                'sample_prompt': 'What is 2+2?'
            }
        ],
        
        # Fallback Storm Detection (Priority 2) - Should be suppressed for overlap_trace_1
        'FallbackStormDetector': [
            {
                'type': 'fallback_storm',
                'trace_id': 'overlap_trace_1',  # Same trace as retry loop
                'severity': 'medium',
                'description': 'Model switching detected',
                'waste_cost': 0.008,
                'models_used': ['gpt-3.5-turbo', 'gpt-4']
            },
            {
                'type': 'fallback_storm', 
                'trace_id': 'unique_storm_trace',  # Different trace
                'severity': 'high',
                'description': 'Chaotic model switching',
                'waste_cost': 0.025,
                'models_used': ['gpt-3.5-turbo', 'gpt-4', 'claude-2']
            }
        ],
        
        # Fallback Failure Detection (Priority 3) - Should be suppressed for overlap_trace_1
        'FallbackFailureDetector': [
            {
                'type': 'fallback_failure',
                'trace_id': 'overlap_trace_1',  # Same trace as retry loop and storm
                'severity': 'medium',
                'description': 'Unnecessary fallback from gpt-3.5-turbo to gpt-4',
                'waste_cost': 0.005
            }
        ],
        
        # Overkill Model Detection (Priority 4 - Lowest) - Should be suppressed for overlap_trace_1
        'OverkillModelDetector': [
            {
                'type': 'overkill_model',
                'trace_id': 'overlap_trace_1',  # Same trace as all others
                'severity': 'low',
                'description': 'GPT-4 used for simple task',
                'waste_cost': 0.003
            },
            {
                'type': 'overkill_model',
                'trace_id': 'unique_overkill_trace',  # Different trace
                'severity': 'medium', 
                'description': 'Claude-2 used for translation',
                'waste_cost': 0.015
            }
        ]
    }
    
    # Initialize suppression engine
    suppression_config = {
        'fallback_storm': {'suppress_if_retry_loop': True},
        'fallback_failure': {'suppress_if_retry_loop': True}, 
        'overkill_model': {'suppress_if_retry_loop': True}
    }
    
    engine = SuppressionEngine(suppression_config, include_suppressed=True)
    
    print("🔢 1. DETECTOR PRIORITY VERIFICATION")
    print("-" * 40)
    for detector, priority in sorted(DETECTOR_PRIORITY.items(), key=lambda x: x[1]):
        print(f"   Priority {priority}: {DETECTOR_DISPLAY_NAMES.get(detector, detector)}")
    
    print("\n🧠 2. PROCESSING DETECTIONS IN PRIORITY ORDER")
    print("-" * 50)
    
    all_active = []
    
    # Process detectors in priority order
    for detector_name in sorted(DETECTOR_PRIORITY.keys(), key=lambda x: DETECTOR_PRIORITY[x]):
        detections = test_detections.get(detector_name, [])
        print(f"\n🔍 Processing {DETECTOR_DISPLAY_NAMES.get(detector_name, detector_name)}")
        print(f"   Raw detections: {len(detections)}")
        
        active = engine.process_detections(detector_name, detections)
        all_active.extend(active)
        
        print(f"   Active after suppression: {len(active)}")
        print(f"   Current trace ownership: {dict(engine.trace_ownership)}")
    
    print("\n🧰 3. SUPPRESSION ANALYSIS")
    print("-" * 40)
    
    summary = engine.get_suppression_summary()
    
    print(f"📊 Total traces analyzed: {summary['total_traces_analyzed']}")
    print(f"✅ Active issues: {summary['active_issues']}")
    print(f"🛑 Suppressed issues: {summary['suppressed_issues']}")
    
    print("\n📋 Suppression breakdown:")
    for reason, count in summary['suppression_breakdown'].items():
        formatted_reason = reason.replace('_', ' ').replace(':', ' by ').title()
        print(f"   • {formatted_reason}: {count} issues")
    
    print("\n🧠 Trace ownership:")
    for trace_id, owner in summary['trace_ownership'].items():
        display_name = DETECTOR_DISPLAY_NAMES.get(owner, owner)
        print(f"   • {trace_id}: owned by {display_name}")
    
    print("\n📝 DETAILED SUPPRESSED DETECTIONS")
    print("-" * 45)
    for detection in engine.suppressed_detections:
        trace_id = detection.get('trace_id')
        detector = detection.get('detector', '')
        reason = detection.get('suppression_reason', 'unknown')
        display_name = DETECTOR_DISPLAY_NAMES.get(detector, detector)
        
        print(f"   ⚠️ {display_name} suppressed for trace {trace_id}")
        print(f"      Reason: {reason.replace('_', ' ').replace(':', ' by ')}")
    
    print("\n🎯 EXPECTED vs ACTUAL RESULTS")
    print("-" * 40)
    
    # Test expectations
    expected_active_traces = {'overlap_trace_1', 'unique_storm_trace', 'unique_overkill_trace'}
    actual_active_traces = {d.get('trace_id') for d in all_active if d.get('trace_id')}
    
    expected_ownership = {
        'overlap_trace_1': 'RetryLoopDetector',  # Highest priority wins
        'unique_storm_trace': 'FallbackStormDetector',
        'unique_overkill_trace': 'OverkillModelDetector'
    }
    
    print("Trace ownership verification:")
    ownership_correct = True
    for trace_id, expected_owner in expected_ownership.items():
        actual_owner = engine.trace_ownership.get(trace_id)
        status = "✅" if actual_owner == expected_owner else "❌"
        print(f"   {status} {trace_id}: Expected {DETECTOR_DISPLAY_NAMES.get(expected_owner)}, Got {DETECTOR_DISPLAY_NAMES.get(actual_owner) if actual_owner else 'None'}")
        if actual_owner != expected_owner:
            ownership_correct = False
    
    print("\nSuppression logic verification:")
    suppression_tests = [
        ("overlap_trace_1 has only 1 active detection", len([d for d in all_active if d.get('trace_id') == 'overlap_trace_1']) == 1),
        ("overlap_trace_1 owned by RetryLoopDetector", engine.trace_ownership.get('overlap_trace_1') == 'RetryLoopDetector'),
        ("FallbackStorm suppressed for overlap_trace_1", any(d.get('trace_id') == 'overlap_trace_1' and 'FallbackStorm' in d.get('detector', '') for d in engine.suppressed_detections)),
        ("unique traces remain active", len(actual_active_traces) == 3)
    ]
    
    all_tests_passed = ownership_correct
    for test_name, passed in suppression_tests:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}")
        if not passed:
            all_tests_passed = False
    
    print("\n" + "=" * 65)
    if all_tests_passed:
        print("🎉 SUCCESS: Production-grade suppression logic working perfectly!")
        print("   ✅ Correct trace ownership")
        print("   ✅ Proper priority-based suppression") 
        print("   ✅ Transparent suppression reporting")
        print("   ✅ No double-counting of waste")
    else:
        print("❌ FAILURE: Some suppression logic tests failed")
    
    return all_tests_passed


def test_config_suppression_toggle():
    """🧪 Test Case: Toggle suppression off and ensure both detectors report correctly"""
    print("\n" + "=" * 65)
    print("🧪 CONFIGURATION SUPPRESSION TOGGLE TEST")
    print("=" * 65)
    
    # Test data with overlapping trace
    test_data = [
        {
            'type': 'retry_loop',
            'trace_id': 'toggle_test_trace',
            'waste_cost': 0.01
        }
    ]
    
    storm_data = [
        {
            'type': 'fallback_storm', 
            'trace_id': 'toggle_test_trace',
            'waste_cost': 0.005
        }
    ]
    
    print("🔧 Test 1: Suppression ENABLED (default)")
    engine1 = SuppressionEngine({'fallback_storm': {'suppress_if_retry_loop': True}})
    engine1.process_detections('RetryLoopDetector', test_data)
    storm_active1 = engine1.process_detections('FallbackStormDetector', storm_data)
    
    print(f"   Storm detections active: {len(storm_active1)}")
    print(f"   Storm detections suppressed: {len([d for d in engine1.suppressed_detections if 'Storm' in d.get('detector', '')])}")
    print(f"   Expected: 0 active, 1 suppressed")
    
    print("\n🔧 Test 2: Suppression DISABLED")
    engine2 = SuppressionEngine({'fallback_storm': {'suppress_if_retry_loop': False}})
    engine2.process_detections('RetryLoopDetector', test_data)
    
    # Debug: Check what should happen before processing
    current_priority = 2  # FallbackStormDetector  
    owner_priority = 1    # RetryLoopDetector
    should_suppress = engine2._should_suppress_by_priority('FallbackStormDetector', current_priority, owner_priority)
    print(f"   Should suppress by priority? {should_suppress}")
    print(f"   Configuration: {engine2.suppression_config}")
    
    storm_active2 = engine2.process_detections('FallbackStormDetector', storm_data)
    
    print(f"   Storm detections active: {len(storm_active2)}")
    print(f"   Storm detections suppressed: {len([d for d in engine2.suppressed_detections if 'Storm' in d.get('detector', '')])}")
    print(f"   Expected: 1 active, 0 suppressed")
    
    # Verify toggle behavior - print the actual values for debugging
    print(f"\n📊 Comparison:")
    print(f"   Test 1 (enabled): {len(storm_active1)} active")
    print(f"   Test 2 (disabled): {len(storm_active2)} active")
    print(f"   Toggle logic: Test1==0 AND Test2==1 = {len(storm_active1) == 0} AND {len(storm_active2) == 1}")
    
    toggle_test_passed = (len(storm_active1) == 0 and len(storm_active2) == 1)
    
    print(f"\n✅ Toggle test: {'PASSED' if toggle_test_passed else 'FAILED'}")
    
    return toggle_test_passed


if __name__ == "__main__":
    test1_passed = test_priority_suppression()
    test2_passed = test_config_suppression_toggle()
    
    print("\n" + "=" * 65)
    print("📊 FINAL TEST RESULTS")
    print("=" * 65)
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED: Production-grade suppression system is ready!")
        print("   🔢 Priority logic working correctly")
        print("   🧠 Trace ownership properly managed")
        print("   📜 Configuration toggles working")
        print("   📊 Transparent reporting implemented")
    else:
        print("❌ SOME TESTS FAILED: Review suppression logic")
    
    exit(0 if test1_passed and test2_passed else 1)
