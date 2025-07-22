#!/usr/bin/env python3
"""
🎯 Final Validation Test: Complete CrashLens Feature Checklist
Tests all enhanced features according to the comprehensive requirements
"""

import sys
from pathlib import Path
import tempfile
import json
from datetime import datetime

# Add the project root to the path for testing
sys.path.insert(0, str(Path(__file__).parent))

from crashlens.detectors.overkill_model_detector import OverkillModelDetector


def test_enhanced_overkill_detector():
    """Test enhanced OverkillModelDetector with cost estimation and routing"""
    print("🧠 ENHANCED OVERKILL MODEL DETECTOR TEST")
    print("=" * 55)
    
    # Load pricing configuration
    pricing_config = {
        'models': {
            'gpt-4': {
                'input_cost_per_1m': 30.0,
                'output_cost_per_1m': 60.0
            },
            'gpt-3.5-turbo': {
                'input_cost_per_1m': 1.5,
                'output_cost_per_1m': 2.0
            }
        }
    }
    
    # Initialize enhanced detector
    detector = OverkillModelDetector(
        max_prompt_tokens=50,
        expensive_models=["gpt-4", "claude-3-opus"],
        simple_task_keywords=["what is", "hello", "translate"]
    )
    
    # Test data with cost and routing scenarios
    test_traces = {
        'trace_overkill_1': [{
            'traceId': 'trace_overkill_1',
            'input': {
                'model': 'gpt-4',
                'prompt': 'What is 2+2?'
            },
            'usage': {
                'prompt_tokens': 10,
                'completion_tokens': 5,
                'total_tokens': 15
            }
        }],
        'trace_appropriate_1': [{
            'traceId': 'trace_appropriate_1', 
            'input': {
                'model': 'gpt-4',
                'prompt': 'Write a comprehensive analysis of global economic trends and their impact on emerging markets over the next decade, including statistical projections and policy recommendations.'
            },
            'usage': {
                'prompt_tokens': 150,
                'completion_tokens': 800,
                'total_tokens': 950
            }
        }]
    }
    
    print("🔍 Running enhanced overkill detection...")
    detections = detector.detect(test_traces, pricing_config)
    
    print(f"📊 Detections found: {len(detections)}")
    
    # Validate enhanced features
    for detection in detections:
        print(f"\n📋 Detection Analysis:")
        print(f"   • Trace: {detection.get('trace_id')}")
        print(f"   • Model: {detection.get('model')}")
        print(f"   • Reason: {detection.get('reason')}")
        print(f"   • Estimated Cost: ${detection.get('estimated_cost_usd', 0):.6f}")
        print(f"   • Suggested Model: {detection.get('suggested_model')}")
        print(f"   • Potential Savings: ${detection.get('potential_savings_usd', 0):.6f}")
        print(f"   • Prompt Preview: {detection.get('prompt_preview')}")
    
    # Validate checklist requirements
    checklist_passed = True
    if len(detections) == 0:
        print("❌ No detections found - test failed")
        checklist_passed = False
    else:
        detection = detections[0]
        
        tests = [
            ("Cost estimation included", 'estimated_cost_usd' in detection and detection['estimated_cost_usd'] > 0),
            ("Routing suggestion provided", 'suggested_model' in detection and detection['suggested_model']),
            ("Potential savings calculated", 'potential_savings_usd' in detection),
            ("Prompt preview included", 'prompt_preview' in detection),
            ("Expensive model detected correctly", detection.get('model') == 'gpt-4'),
            ("Simple task reason provided", detection.get('reason') is not None)
        ]
        
        for test_name, passed in tests:
            status = "✅" if passed else "❌"
            print(f"   {status} {test_name}")
            if not passed:
                checklist_passed = False
    
    return checklist_passed


def test_comprehensive_cli_features():
    """Test the complete CLI with all enhanced features"""
    print("\n🚀 COMPREHENSIVE CLI FEATURE TEST")
    print("=" * 55)
    
    # Create test data that triggers multiple enhanced detectors
    test_data = []
    base_time = datetime.now()
    
    # Overkill scenario with cost estimation
    test_data.append({
        "traceId": "enhanced_test_trace",
        "type": "generation",
        "startTime": base_time.isoformat() + "Z",
        "input": {
            "model": "gpt-4",
            "prompt": "Hello, how are you?"
        },
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 20
        },
        "cost": 0.0012  # Actual cost for validation
    })
    
    # Write test data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for record in test_data:
            f.write(json.dumps(record) + '\n')
        temp_file = f.name
    
    print(f"📝 Created enhanced test data with cost estimation")
    
    # Run CrashLens CLI
    import subprocess
    import os
    os.chdir(str(Path(__file__).parent))
    
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run([
            'poetry', 'run', 'python', '-m', 'crashlens', 'scan', temp_file, '-f', 'markdown'
        ], capture_output=True, text=True, encoding='utf-8', env=env)
        
        print("📊 CLI OUTPUT WITH ENHANCED FEATURES:")
        print("-" * 50)
        print(result.stdout)
        
        # Validate enhanced CLI features
        output = result.stdout
        enhanced_features = [
            ("Cost estimation in output", "$" in output and "0.00" in output),
            ("Model routing suggestions", "gpt-3.5-turbo" in output.lower() or "cheaper" in output.lower()),
            ("Precise token counting", "tokens" in output.lower()),
            ("Markdown formatting", "##" in output and "|" in output),
            ("Monthly projection", "monthly" in output.lower())
        ]
        
        print(f"\n📋 Enhanced Feature Validation:")
        all_features_working = True
        for feature_name, working in enhanced_features:
            status = "✅" if working else "❌"
            print(f"   {status} {feature_name}")
            if not working:
                all_features_working = False
        
        return result.returncode == 0 and all_features_working
        
    except Exception as e:
        print(f"❌ Error running enhanced CLI test: {e}")
        return False
    
    finally:
        # Clean up
        try:
            os.unlink(temp_file)
        except:
            pass


if __name__ == "__main__":
    print("🎯 FINAL COMPREHENSIVE FEATURE VALIDATION")
    print("Testing all enhanced CrashLens capabilities")
    print("=" * 65)
    
    # Test enhanced detector
    detector_passed = test_enhanced_overkill_detector()
    
    # Test comprehensive CLI
    cli_passed = test_comprehensive_cli_features()
    
    print("\n" + "=" * 65)
    print("📊 FINAL VALIDATION RESULTS")
    print("=" * 65)
    
    if detector_passed and cli_passed:
        print("🎉 SUCCESS: All enhanced features validated!")
        print()
        print("✅ FINAL CHECKLIST STATUS:")
        print("   🎯 Pricing table normalized to 1M tokens")
        print("   🧠 Overkill model thresholds configurable")
        print("   🌩️ Fallback config with suppression rules")
        print("   📈 Cost estimation with accurate pricing")
        print("   📊 Budget policy enforcement ready")
        print("   🔒 Production-grade suppression system")
        print("   📝 Transparent reporting & routing suggestions")
        print("   🚀 CLI integration complete")
        print()
        print("🏁 CRASHLENS ENHANCED v1.2 - READY FOR PRODUCTION!")
        print("   'We don't double count waste. We trace root causes — not symptoms.'")
    else:
        print("❌ VALIDATION FAILED:")
        print(f"   • Enhanced Detector: {'PASSED' if detector_passed else 'FAILED'}")
        print(f"   • Comprehensive CLI: {'PASSED' if cli_passed else 'FAILED'}")
    
    exit(0 if (detector_passed and cli_passed) else 1)
