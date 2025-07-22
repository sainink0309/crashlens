#!/usr/bin/env python3
"""
Test script to verify model consistency in retry loop detection
"""

import json
from datetime import datetime, timedelta
from crashlens.detectors.retry_loops import RetryLoopDetector

def create_test_logs_with_model_changes():
    """Create test logs with model changes to verify they're not flagged as retry loops"""
    base_time = datetime.now()
    logs = []
    
    # Scenario 1: Model escalation - should NOT be flagged as retry loop
    # (gpt-3.5 fails, escalates to gpt-4, then actual retries on gpt-4)
    logs.extend([
        {
            "traceId": "trace_model_change",
            "type": "generation", 
            "startTime": (base_time + timedelta(seconds=0)).isoformat() + "Z",
            "input": {"model": "gpt-3.5-turbo", "prompt": "Complex analysis task"},
            "usage": {"prompt_tokens": 50, "completion_tokens": 10},
            "cost": 0.0001
        },
        {
            "traceId": "trace_model_change",
            "type": "generation",
            "startTime": (base_time + timedelta(seconds=30)).isoformat() + "Z", 
            "input": {"model": "gpt-4", "prompt": "Complex analysis task"},
            "usage": {"prompt_tokens": 50, "completion_tokens": 200},
            "cost": 0.0050
        },
        {
            "traceId": "trace_model_change", 
            "type": "generation",
            "startTime": (base_time + timedelta(seconds=60)).isoformat() + "Z",
            "input": {"model": "gpt-4", "prompt": "Complex analysis task"},
            "usage": {"prompt_tokens": 50, "completion_tokens": 200},
            "cost": 0.0050
        },
        {
            "traceId": "trace_model_change",
            "type": "generation", 
            "startTime": (base_time + timedelta(seconds=90)).isoformat() + "Z",
            "input": {"model": "gpt-4", "prompt": "Complex analysis task"},
            "usage": {"prompt_tokens": 50, "completion_tokens": 200},
            "cost": 0.0050
        }
    ])
    
    # Scenario 2: Pure retry loop - same model throughout (should be flagged)
    logs.extend([
        {
            "traceId": "trace_pure_retry",
            "type": "generation",
            "startTime": (base_time + timedelta(minutes=10, seconds=0)).isoformat() + "Z",
            "input": {"model": "gpt-3.5-turbo", "prompt": "What is 2+2?"},
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            "cost": 0.0001
        },
        {
            "traceId": "trace_pure_retry",
            "type": "generation", 
            "startTime": (base_time + timedelta(minutes=10, seconds=30)).isoformat() + "Z",
            "input": {"model": "gpt-3.5-turbo", "prompt": "What is 2+2?"},
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            "cost": 0.0001
        },
        {
            "traceId": "trace_pure_retry",
            "type": "generation",
            "startTime": (base_time + timedelta(minutes=10, seconds=60)).isoformat() + "Z", 
            "input": {"model": "gpt-3.5-turbo", "prompt": "What is 2+2?"},
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            "cost": 0.0001
        },
        {
            "traceId": "trace_pure_retry",
            "type": "generation",
            "startTime": (base_time + timedelta(minutes=10, seconds=90)).isoformat() + "Z",
            "input": {"model": "gpt-3.5-turbo", "prompt": "What is 2+2?"},
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            "cost": 0.0001
        }
    ])
    
    return logs

def test_model_consistency():
    """Test that model consistency is enforced in retry loop detection"""
    print("🧪 Testing Model Consistency in Retry Loop Detection")
    print("=" * 60)
    
    # Create test logs
    logs = create_test_logs_with_model_changes()
    
    # Parse logs into traces format
    traces = {}
    for log in logs:
        trace_id = log["traceId"]
        if trace_id not in traces:
            traces[trace_id] = []
        
        record = {
            "traceId": log["traceId"],
            "startTime": log["startTime"],
            "prompt": log["input"]["prompt"],
            "model": log["input"]["model"],
            "prompt_tokens": log["usage"]["prompt_tokens"],
            "completion_tokens": log["usage"]["completion_tokens"],
            "cost": log["cost"]
        }
        traces[trace_id].append(record)
    
    print("📋 Test Data Summary:")
    for trace_id, records in traces.items():
        print(f"\n   {trace_id}: {len(records)} records")
        for i, record in enumerate(records):
            print(f"     {i+1}. {record['model']}: {record['prompt']}")
    
    # Test retry loop detection
    print("\n📊 Testing retry loop detection with model consistency:")
    detector = RetryLoopDetector(
        max_retries=3,  # This means >3, so 4+ records needed
        time_window_minutes=5
    )
    
    detections = detector.detect(traces)
    
    print(f"\n✅ Found {len(detections)} retry loop(s):")
    
    expected_detections = 1  # Only trace_pure_retry should be flagged
    
    for detection in detections:
        print(f"\n🔍 Detection: {detection['description']}")
        print(f"   Trace ID: {detection['trace_id']}")
        print(f"   Model: {detection['model']}")
        print(f"   Retry Count: {detection['retry_count']}")
        print(f"   Method: {detection['detection_method']}")
        print(f"   Sample Prompt: {detection['sample_prompt']}")
        print(f"   Waste Cost: ${detection['waste_cost']:.4f}")
        print(f"   Time Span: {detection['time_span']}")
    
    # Verify results
    if len(detections) == expected_detections:
        print(f"\n✅ SUCCESS: Correctly found {expected_detections} retry loop(s)")
        if detections[0]['trace_id'] == 'trace_pure_retry':
            print("✅ SUCCESS: Only flagged pure retry loop (same model throughout)")
        else:
            print("❌ FAILURE: Flagged wrong trace")
    else:
        print(f"\n❌ FAILURE: Expected {expected_detections} detections, got {len(detections)}")
        if len(detections) > expected_detections:
            print("❌ Model escalation was incorrectly flagged as retry loop")
    
    print(f"\n🎯 Summary: Model consistency check {'PASSED' if len(detections) == expected_detections else 'FAILED'}")

if __name__ == "__main__":
    test_model_consistency()
