"""
Tests for CrashLens detection rules
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from crashlens.detectors.retry_loops import RetryLoopDetector
from crashlens.detectors.fallback_storm import FallbackStormDetector


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
                    "startTime": "2024-01-15T10:00:00Z",
                    "model": "gpt-4",
                    "prompt": "What is 2+2?",
                    "completion_tokens": 5,
                    "cost": 0.0003
                },
                {
                    "startTime": "2024-01-15T10:00:01Z",
                    "model": "gpt-4",
                    "prompt": "What is 2+2?",
                    "completion_tokens": 5,
                    "cost": 0.0003
                },
                {
                    "startTime": "2024-01-15T10:00:02Z", 
                    "model": "gpt-4",
                    "prompt": "What is 2+2?",
                    "completion_tokens": 5,
                    "cost": 0.0003
                },
                {
                    "startTime": "2024-01-15T10:00:03Z", 
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
        self.assertEqual(detections[0]['retry_count'], 4)
        self.assertEqual(detections[0]['detection_method'], 'exact_match')


class TestExpensiveModelShortDetector(unittest.TestCase):
    """Test GPT-4 short prompt detection (expensive_model_short only)"""
    
    def setUp(self):
        from crashlens.detectors.overkill_model_detector import detect_expensive_model_waste
        self.detector = detect_expensive_model_waste
    
    def test_detect_expensive_model_short(self):
        """Test detection of short GPT-4 prompts as expensive_model_short"""
        traces = {
            "trace_001": [
                {
                    "startTime": "2024-01-15T10:00:00Z",
                    "model": "gpt-4",
                    "prompt": "What is 2+2?",
                    "prompt_tokens": 5,
                    "completion_tokens": 5,
                    "cost": 0.0003
                }
            ]
        }
        
        detections = self.detector(traces)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]['type'], 'expensive_model_short')
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
                    "startTime": "2024-01-15T10:00:00Z",
                    "model": "gpt-4",
                    "prompt": "Fix this code",
                    "completion_tokens": 10,
                    "cost": 0.0006
                },
                {
                    "startTime": "2024-01-15T10:00:05Z",
                    "model": "gpt-3.5-turbo",
                    "prompt": "Fix this code",
                    "completion_tokens": 10,
                    "cost": 0.0002
                },
                {
                    "startTime": "2024-01-15T10:00:10Z",
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