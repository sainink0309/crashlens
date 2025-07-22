#!/usr/bin/env python3
"""
🧪 Overkill Model Detector Checklist Compliance Test
Tests the detector against the official checklist requirements.
"""

from datetime import datetime
from crashlens.detectors.overkill_model_detector import OverkillModelDetector

def test_overkill_checklist_compliance():
    """Test the overkill detector against official checklist"""
    print("🧪 OVERKILL MODEL DETECTOR CHECKLIST COMPLIANCE TEST")
    print("=" * 60)
    
    # Create test traces matching checklist scenarios
    test_traces = {
        # ✅ Should trigger: gpt-4, short prompt with keyword
        "overkill_simple": [
            {
                "traceId": "overkill_simple",
                "startTime": datetime.now().isoformat() + "Z",
                "prompt": "summarize this paragraph",  # Starts with "summarize"
                "model": "gpt-4",
                "usage": {"prompt_tokens": 5, "completion_tokens": 20},
                "cost": 0.045
            }
        ],
        
        # ✅ Should trigger: gpt-4, very short prompt
        "overkill_short": [
            {
                "traceId": "overkill_short",
                "startTime": datetime.now().isoformat() + "Z",
                "prompt": "translate 'hello' to Spanish",  # Starts with "translate"
                "model": "gpt-4-turbo",
                "usage": {"prompt_tokens": 8, "completion_tokens": 5},
                "cost": 0.025
            }
        ],
        
        # ❌ Should NOT trigger: gpt-4, long prompt
        "not_overkill_long": [
            {
                "traceId": "not_overkill_long",
                "startTime": datetime.now().isoformat() + "Z",
                "prompt": "generate production-ready backend for this schema with comprehensive error handling, authentication, database models, API endpoints, testing suite, and deployment configuration",  # Long prompt
                "model": "gpt-4",
                "usage": {"prompt_tokens": 50, "completion_tokens": 500},
                "cost": 0.15
            }
        ],
        
        # ❌ Should NOT trigger: gpt-3.5, short prompt
        "not_overkill_cheap": [
            {
                "traceId": "not_overkill_cheap",
                "startTime": datetime.now().isoformat() + "Z",
                "prompt": "summarize this",  # Short but cheap model
                "model": "gpt-3.5-turbo",
                "usage": {"prompt_tokens": 3, "completion_tokens": 10},
                "cost": 0.002
            }
        ],
        
        # ❌ Should NOT trigger: Complex format (suppression)
        "not_overkill_complex": [
            {
                "traceId": "not_overkill_complex",
                "startTime": datetime.now().isoformat() + "Z",
                "prompt": '{"task": "translate", "context": "business document"}',  # Complex JSON format
                "model": "gpt-4",
                "usage": {"prompt_tokens": 15, "completion_tokens": 10},
                "cost": 0.03
            }
        ],
        
        # ❌ Should NOT trigger: Failed call
        "not_overkill_failed": [
            {
                "traceId": "not_overkill_failed",
                "startTime": datetime.now().isoformat() + "Z",
                "prompt": "explain this",  # Simple but failed
                "model": "gpt-4",
                "usage": {"prompt_tokens": 3, "completion_tokens": 0},  # No completion tokens
                "error": "API rate limit exceeded",
                "cost": 0.0
            }
        ]
    }
    
    # Test the detector
    detector = OverkillModelDetector(max_prompt_tokens_for_overkill=20, max_prompt_chars=150)
    detections = detector.detect(test_traces)
    
    print("🔍 DETECTION RESULTS")
    print("-" * 40)
    
    detected_traces = {d['trace_id'] for d in detections}
    
    for detection in detections:
        print(f"✅ OVERKILL DETECTED: {detection['trace_id']}")
        print(f"   Model: {detection['model']}")
        print(f"   Tokens: {detection['prompt_tokens']}")
        print(f"   Reason: {detection['reason']}")
        print(f"   Cost: ${detection['estimated_cost_usd']:.4f}")
        print(f"   Sample: '{detection['sample_prompt']}'")
        print()
    
    print("📋 CHECKLIST VERIFICATION")
    print("-" * 40)
    
    # Expected results based on checklist
    expected_detections = {"overkill_simple", "overkill_short"}
    expected_no_detections = {"not_overkill_long", "not_overkill_cheap", "not_overkill_complex", "not_overkill_failed"}
    
    # Verify detection logic checklist
    checklist_results = []
    
    # ✅ Expensive model detection
    expensive_detected = any(d['model'] in ['gpt-4', 'gpt-4-turbo'] for d in detections)
    checklist_results.append(("Expensive model detection", expensive_detected))
    
    # ✅ Short prompt detection  
    short_prompt_detected = any(d['prompt_tokens'] <= 20 for d in detections)
    checklist_results.append(("Short prompt detection (≤20 tokens)", short_prompt_detected))
    
    # ✅ Simple task heuristics
    keyword_detected = any('summarize' in d['reason'] or 'translate' in d['reason'] for d in detections)
    checklist_results.append(("Simple task keyword detection", keyword_detected))
    
    # ✅ Span succeeded check
    succeeded_only = all(d['estimated_cost_usd'] > 0 for d in detections)
    checklist_results.append(("Only successful spans flagged", succeeded_only))
    
    # ⚠️ Suppression logic
    complex_suppressed = "not_overkill_complex" not in detected_traces
    cheap_model_suppressed = "not_overkill_cheap" not in detected_traces
    long_prompt_suppressed = "not_overkill_long" not in detected_traces
    failed_suppressed = "not_overkill_failed" not in detected_traces
    
    checklist_results.append(("Complex format suppression", complex_suppressed))
    checklist_results.append(("Cheap model suppression", cheap_model_suppressed))
    checklist_results.append(("Long prompt suppression", long_prompt_suppressed))
    checklist_results.append(("Failed call suppression", failed_suppressed))
    
    # 💡 CLI output format
    has_required_fields = all(
        all(field in d for field in ['trace_id', 'model', 'estimated_cost_usd', 'prompt_tokens', 'overkill_detected'])
        for d in detections
    )
    checklist_results.append(("Required output fields present", has_required_fields))
    
    # Print checklist results
    all_passed = True
    for check_name, passed in checklist_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    print("\n🎯 EXPECTED vs ACTUAL")
    print("-" * 40)
    print(f"Expected detections: {expected_detections}")
    print(f"Actual detections: {detected_traces}")
    print(f"Expected no detections: {expected_no_detections}")
    print(f"Actual no detections: {set(test_traces.keys()) - detected_traces}")
    
    # Final validation
    correct_positives = expected_detections == detected_traces
    correct_negatives = len(expected_no_detections & detected_traces) == 0
    
    print(f"\n✅ Correct positive detections: {correct_positives}")
    print(f"✅ Correct negative suppressions: {correct_negatives}")
    
    print("\n" + "=" * 60)
    if all_passed and correct_positives and correct_negatives:
        print("🎉 SUCCESS: Overkill Model Detector fully complies with checklist!")
    else:
        print("❌ FAILURE: Some checklist items failed")
    
    return all_passed and correct_positives and correct_negatives

if __name__ == "__main__":
    test_overkill_checklist_compliance()
