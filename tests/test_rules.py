"""
Tests for CrashLens detection rules
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from detectors.retry_loops import RetryLoopDetector
from detectors.gpt4_short import GPT4ShortDetector
from detectors.fallback_storm import FallbackStormDetector


class TestRetryLoopDetector(unittest.TestCase):
    """Test retry loop detection"""
    
    def setUp(self):
        self.detector = RetryLoopDetector()
    
    def test_detect_retry_loop(self):
        """Test detection of retry loops"""
        # Mock traces with retry pattern
        traces = {
            "trace_001": [
                {
                    "trace_id": "trace_001",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "model": "gpt-4",
                    "prompt": "What is 2+2?",
                    "completion_tokens": 5,
                    "cost": 0.0003
                },
                {
                    "trace_id": "trace_001", 
                    "timestamp": "2024-01-15T10:00:01Z",
                    "model": "gpt-4",
                    "prompt": "What is 2+2?",
                    "completion_tokens": 5,
                    "cost": 0.0003
                },
                {
                    "trace_id": "trace_001",
                    "timestamp": "2024-01-15T10:00:02Z", 
                    "model": "gpt-4",
                    "prompt": "What is 2+2?",
                    "completion_tokens": 5,
                    "cost": 0.0003
                }
            ]
        }
        
        detections = self.detector.detect(traces)
        
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]['type'], 'retry_loop')
        self.assertEqual(detections[0]['retry_count'], 3)


class TestGPT4ShortDetector(unittest.TestCase):
    """Test GPT-4 short prompt detection"""
    
    def setUp(self):
        self.detector = GPT4ShortDetector()
    
    def test_detect_gpt4_short(self):
        """Test detection of short GPT-4 prompts"""
        traces = {
            "trace_001": [
                {
                    "trace_id": "trace_001",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "model": "gpt-4",
                    "prompt": "What is 2+2?",
                    "completion_tokens": 5,
                    "cost": 0.0003
                }
            ]
        }
        
        detections = self.detector.detect(traces)
        
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]['type'], 'gpt4_short')
        self.assertEqual(detections[0]['model_used'], 'gpt-4')


class TestFallbackStormDetector(unittest.TestCase):
    """Test fallback storm detection"""
    
    def setUp(self):
        self.detector = FallbackStormDetector()
    
    def test_detect_fallback_storm(self):
        """Test detection of fallback storms"""
        traces = {
            "trace_001": [
                {
                    "trace_id": "trace_001",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "model": "gpt-4",
                    "prompt": "Fix this code",
                    "completion_tokens": 10,
                    "cost": 0.0006
                },
                {
                    "trace_id": "trace_001",
                    "timestamp": "2024-01-15T10:00:05Z",
                    "model": "gpt-3.5-turbo",
                    "prompt": "Fix this code",
                    "completion_tokens": 10,
                    "cost": 0.0002
                },
                {
                    "trace_id": "trace_001",
                    "timestamp": "2024-01-15T10:00:10Z",
                    "model": "gpt-3.5-turbo-16k",
                    "prompt": "Fix this code",
                    "completion_tokens": 10,
                    "cost": 0.0004
                }
            ]
        }
        
        detections = self.detector.detect(traces)
        
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]['type'], 'fallback_storm')
        self.assertEqual(detections[0]['fallback_count'], 3)


if __name__ == '__main__':
    unittest.main() 