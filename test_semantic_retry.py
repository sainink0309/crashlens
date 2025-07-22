#!/usr/bin/env python3
"""
Test script for retry loop detection (exact match only)
"""

import json
from datetime import datetime, timedelta
from crashlens.detectors.retry_loops import RetryLoopDetector

def create_test_logs():
    """Create test logs with retry patterns"""
    base_time = datetime.now()
    logs = []
    
    # Scenario 1: Exact retry loop (4 identical calls)
    for i in range(4):
        logs.append({
            "traceId": "trace_001",
            "type": "generation",
            "startTime": (base_time + timedelta(seconds=i*30)).isoformat() + "Z",
            "input": {
                "model": "gpt-4",
                "prompt": "What is 2+2?"
            },
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 3
            },
            "cost": 0.0003
        })
    
    # Scenario 2: Different prompts (should not trigger)
    different_prompts = [
        "What is 2+2?",
        "Explain quantum physics",
        "Write a haiku about coding"
    ]
    for i, prompt in enumerate(different_prompts):
        logs.append({
            "traceId": "trace_003",
            "type": "generation",
            "startTime": (base_time + timedelta(minutes=5, seconds=i*30)).isoformat() + "Z",
            "input": {
                "model": "gpt-4",
                "prompt": prompt
            },
            "usage": {
                "prompt_tokens": 8,
                "completion_tokens": 15
            },
            "cost": 0.0006
        })
    return logs

def test_retry_loop_detection():
    """Test retry loop detection (exact match only)"""
    print("🧪 Testing Retry Loop Detection (Exact Match)")
    print("=" * 50)
    
    # Create test logs
    logs = create_test_logs()
    
    # Parse logs into traces format
    traces = {}
    for log in logs:
        trace_id = log["traceId"]
        if trace_id not in traces:
            traces[trace_id] = []
        
        # Extract fields as expected by the detector
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
        print(f"   {trace_id}: {len(records)} records")
        for record in records:
            print(f"     - {record['prompt']}")
    print()
    
    # Test retry loop detection
    print("📊 Testing retry loop detection (exact match):")
    detector = RetryLoopDetector(
        max_retries=3,  # This means >3, so 4+ records needed
        time_window_minutes=5
    )
    
    detections = detector.detect(traces)
    
    print(f"✅ Found {len(detections)} retry loop(s):")
    for detection in detections:
        print(f"\n🔍 Detection: {detection['description']}")
        print(f"   Trace ID: {detection['trace_id']}")
        print(f"   Retry Count: {detection['retry_count']}")
        print(f"   Method: {detection['detection_method']}")
        print(f"   Sample Prompt: {detection['sample_prompt']}")
        print(f"   Waste Cost: ${detection['waste_cost']:.4f}")
        print(f"   Time Span: {detection['time_span']}")
        print(f"   All Prompts in Group:")
        for i, record in enumerate(detection['records']):
            print(f"     {i+1}. {record['prompt']}")
    
    if not detections:
        print("❌ No retry loops detected")
    
    print(f"\n🎯 Summary: {len(detections)} retry loop(s) detected using exact match")

if __name__ == "__main__":
    test_retry_loop_detection() 