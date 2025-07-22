#!/usr/bin/env python3
"""
Test script for --paste mode functionality
"""

import subprocess
import sys
from pathlib import Path

def test_paste_mode():
    """Test the paste mode by providing input via stdin to the paste command"""
    
    # Sample JSONL data for testing
    test_data = '''{"traceId": "paste_test_001", "type": "generation", "startTime": "2024-06-01T10:00:00Z", "input": {"model": "gpt-4", "prompt": "Hello world"}, "usage": {"prompt_tokens": 3, "completion_tokens": 2}}
{"traceId": "paste_test_002", "type": "generation", "startTime": "2024-06-01T10:00:05Z", "input": {"model": "gpt-3.5-turbo", "prompt": "What is AI?"}, "usage": {"prompt_tokens": 4, "completion_tokens": 20}}'''
    
    print("🧪 Testing --paste mode functionality...")
    print("📋 Test data:")
    print(test_data)
    print("\n" + "="*50)
    
    try:
        # Run the command with paste mode (use json format to avoid emoji issues)
        process = subprocess.Popen(
            ["poetry", "run", "python", "-m", "crashlens", "scan", "--paste", "--summary-only"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent
        )
        
        # Send test data followed by EOF
        stdout, stderr = process.communicate(input=test_data)
        
        print("📤 STDOUT:")
        print(stdout)
        
        if stderr:
            print("📤 STDERR:")
            print(stderr)
        
        print(f"📤 Exit code: {process.returncode}")
        
        return process.returncode == 0
        
    except Exception as e:
        print(f"❌ Error testing paste mode: {e}")
        return False

if __name__ == "__main__":
    success = test_paste_mode()
    print(f"\n🏁 Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
