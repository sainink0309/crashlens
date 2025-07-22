#!/usr/bin/env python3
"""
Test the updated fallback failure detector
"""

from datetime import datetime, timedelta
from crashlens.detectors.fallback_failure import FallbackFailureDetector

def test_updated_fallback_detector():
    """Test the updated fallback failure detector"""
    print("🧪 Testing Updated Fallback Failure Detection")
    print("=" * 50)
    
    base_time = datetime.now()
    
    # Test Case 1: Valid fallback failure (should be detected)
    valid_fallback_trace = [
        {
            "traceId": "fallback_001",
            "startTime": (base_time).isoformat() + "Z",
            "prompt": "Translate 'hello' to Spanish",
            "model": "gpt-3.5-turbo",
            "usage": {"prompt_tokens": 8, "completion_tokens": 5},
            "cost": 0.0002
        },
        {
            "traceId": "fallback_001", 
            "startTime": (base_time + timedelta(minutes=2)).isoformat() + "Z",
            "prompt": "Translate 'hello' to Spanish",  # Same prompt
            "model": "gpt-4",  # More expensive model
            "usage": {"prompt_tokens": 8, "completion_tokens": 5},
            "cost": 0.0008
        }
    ]
    
    # Test Case 2: Should be suppressed (already flagged by retry loop)
    retry_flagged_trace = [
        {
            "traceId": "retry_001",
            "startTime": (base_time + timedelta(minutes=5)).isoformat() + "Z",
            "prompt": "What is 2+2?",
            "model": "gpt-3.5-turbo",
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            "cost": 0.0001
        },
        {
            "traceId": "retry_001",
            "startTime": (base_time + timedelta(minutes=6)).isoformat() + "Z", 
            "prompt": "What is 2+2?",
            "model": "gpt-4",
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            "cost": 0.0003
        }
    ]
    
    traces = {
        "fallback_001": valid_fallback_trace,
        "retry_001": retry_flagged_trace
    }
    
    print("📋 Test Cases:")
    print("   1. Valid Fallback: gpt-3.5-turbo → gpt-4 (same prompt)")
    print("   2. Retry Flagged: Should be suppressed if retry_001 is flagged")
    print()
    
    # Test without suppression
    detector = FallbackFailureDetector(time_window_seconds=300)
    detections_no_suppression = detector.detect(traces)
    
    print(f"🔍 Detections without suppression: {len(detections_no_suppression)}")
    for detection in detections_no_suppression:
        print(f"   ✅ {detection['trace_id']}: {detection['model_tiers']}")
    
    # Test with suppression
    already_flagged = {"retry_001"}  # Simulate retry_001 being flagged
    detections_with_suppression = detector.detect(traces, already_flagged_ids=already_flagged)
    
    print(f"🔍 Detections with suppression: {len(detections_with_suppression)}")
    for detection in detections_with_suppression:
        print(f"   ✅ {detection['trace_id']}: {detection['model_tiers']}")
        print(f"      Description: {detection['description']}")
        print(f"      Waste Cost: ${detection['waste_cost']:.4f}")
        print(f"      Time Between Calls: {detection['time_between_calls']}")
    
    print()
    print("🎯 Expected Results:")
    print("   ✅ Without suppression: 2 detections")
    print("   ✅ With suppression: 1 detection (retry_001 suppressed)")
    
    success = (len(detections_no_suppression) == 2 and 
               len(detections_with_suppression) == 1 and
               detections_with_suppression[0]['trace_id'] == 'fallback_001')
    
    if success:
        print("🎉 SUCCESS: Updated fallback failure detection working correctly!")
    else:
        print("❌ FAILURE: Unexpected results")
    
    return success

if __name__ == "__main__":
    test_updated_fallback_detector()
