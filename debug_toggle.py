#!/usr/bin/env python3
"""
Debug test to understand the toggle behavior
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from crashlens.cli import SuppressionEngine

def debug_toggle():
    print("🐛 DEBUG: Understanding Toggle Behavior")
    print("=" * 50)
    
    # Test data
    test_data = [{'type': 'retry_loop', 'trace_id': 'debug_trace', 'waste_cost': 0.01}]
    storm_data = [{'type': 'fallback_storm', 'trace_id': 'debug_trace', 'waste_cost': 0.005}]
    
    print("🔧 Test: Suppression DISABLED")
    engine = SuppressionEngine({'fallback_storm': {'suppress_if_retry_loop': False}})
    
    print("Processing RetryLoopDetector...")
    retry_active = engine.process_detections('RetryLoopDetector', test_data)
    print(f"   Retry active: {len(retry_active)}")
    print(f"   Trace ownership: {dict(engine.trace_ownership)}")
    
    print("Processing FallbackStormDetector...")
    
    # Debug the _should_suppress_by_priority method
    current_priority = 2  # FallbackStormDetector
    owner_priority = 1    # RetryLoopDetector 
    should_suppress = engine._should_suppress_by_priority('FallbackStormDetector', current_priority, owner_priority)
    print(f"   Should suppress by priority? {should_suppress}")
    
    storm_active = engine.process_detections('FallbackStormDetector', storm_data)
    print(f"   Storm active: {len(storm_active)}")
    print(f"   Storm suppressed: {len([d for d in engine.suppressed_detections if 'Storm' in d.get('detector', '')])}")
    print(f"   Final trace ownership: {dict(engine.trace_ownership)}")
    
    print("\nSuppressed detections:")
    for detection in engine.suppressed_detections:
        print(f"   - {detection.get('detector')}: {detection.get('suppression_reason')}")
    
    print("\nActive detections:")
    for detection in engine.active_detections:
        print(f"   - {detection.get('type')} from trace {detection.get('trace_id')}")

if __name__ == "__main__":
    debug_toggle()
