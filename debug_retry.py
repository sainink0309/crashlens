#!/usr/bin/env python3
"""
Debug test for retry loop detection
"""

from datetime import datetime, timedelta
from crashlens.detectors.retry_loops import RetryLoopDetector

def debug_retry_detection():
    """Debug the retry loop detection"""
    print("🔍 DEBUG: Retry Loop Detection")
    print("=" * 50)
    
    base_time = datetime.now()
    
    # Simple test case
    traces = {
        "test_retry": [
            {
                "traceId": "test_retry",
                "startTime": (base_time).isoformat() + "Z",
                "prompt": "What is 2+2?",
                "model": "gpt-3.5-turbo",
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                "cost": 0.0001
            },
            {
                "traceId": "test_retry",
                "startTime": (base_time + timedelta(seconds=30)).isoformat() + "Z",
                "prompt": "What is 2+2?",
                "model": "gpt-3.5-turbo",
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                "cost": 0.0001
            },
            {
                "traceId": "test_retry",
                "startTime": (base_time + timedelta(seconds=60)).isoformat() + "Z",
                "prompt": "What is 2+2?",
                "model": "gpt-3.5-turbo",
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                "cost": 0.0001
            },
            {
                "traceId": "test_retry",
                "startTime": (base_time + timedelta(seconds=90)).isoformat() + "Z",
                "prompt": "What is 2+2?",
                "model": "gpt-3.5-turbo",
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                "cost": 0.0001
            }
        ]
    }
    
    print(f"📊 Trace data:")
    for record in traces["test_retry"]:
        print(f"   Time: {record['startTime']}")
        print(f"   Prompt: '{record['prompt']}'")
        print(f"   Model: {record['model']}")
        print()
    
    # Test with different configurations
    configs = [
        {"max_retries": 3, "time_window_minutes": 5, "max_retry_interval_minutes": 2},
        {"max_retries": 2, "time_window_minutes": 5, "max_retry_interval_minutes": 2},
        {"max_retries": 1, "time_window_minutes": 5, "max_retry_interval_minutes": 2},
    ]
    
    for i, config in enumerate(configs):
        print(f"🧪 Test {i+1}: max_retries={config['max_retries']}, "
              f"time_window={config['time_window_minutes']}min, "
              f"retry_interval={config['max_retry_interval_minutes']}min")
        
        detector = RetryLoopDetector(**config)
        detections = detector.detect(traces)
        
        print(f"   Results: {len(detections)} detections")
        if detections:
            for detection in detections:
                print(f"   ✅ {detection['trace_id']}: {detection['retry_count']} retries")
                print(f"      Time span: {detection['time_span']}s")
                print(f"      Waste cost: ${detection['waste_cost']:.4f}")
        else:
            print("   ❌ No detections")
        print()

if __name__ == "__main__":
    debug_retry_detection()
