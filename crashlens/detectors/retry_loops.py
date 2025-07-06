"""
Retry Loop Detector
Detects patterns of repeated API calls that suggest retry loops
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta


class RetryLoopDetector:
    """Detects retry loops in API calls"""
    
    def __init__(self, max_retries: int = 3, time_window_minutes: int = 5):
        self.max_retries = max_retries
        self.time_window = timedelta(minutes=time_window_minutes)
    
    def detect(self, traces: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detect retry loops across all traces"""
        detections = []
        
        for trace_id, records in traces.items():
            # Group records by similar prompts within time window
            prompt_groups = self._group_by_prompt(records)
            
            for prompt_hash, group in prompt_groups.items():
                if len(group) > self.max_retries:
                    # Calculate waste metrics
                    total_tokens = sum(r.get('completion_tokens', 0) for r in group)
                    total_cost = sum(r.get('cost', 0.0) for r in group)
                    
                    detection = {
                        'type': 'retry_loop',
                        'trace_id': trace_id,
                        'severity': 'high' if len(group) > 5 else 'medium',
                        'description': f"Retry loop detected: {len(group)} calls for same prompt",
                        'waste_tokens': total_tokens,
                        'waste_cost': total_cost,
                        'retry_count': len(group),
                        'time_span': self._get_time_span(group),
                        'sample_prompt': group[0].get('prompt', '')[:100] + '...' if len(group[0].get('prompt', '')) > 100 else group[0].get('prompt', ''),
                        'records': group
                    }
                    detections.append(detection)
        
        return detections
    
    def _group_by_prompt(self, records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group records by prompt similarity and time proximity"""
        groups = {}
        
        for record in records:
            prompt = record.get('prompt', '')
            timestamp = record.get('timestamp')
            
            if not prompt or not timestamp:
                continue
            
            # Simple prompt hashing (in real implementation, use more sophisticated similarity)
            prompt_hash = hash(prompt) % 10000
            
            if prompt_hash not in groups:
                groups[prompt_hash] = []
            
            # Check if this record is within time window of existing records
            record_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            should_add = True
            
            for existing_record in groups[prompt_hash]:
                existing_time = datetime.fromisoformat(existing_record['timestamp'].replace('Z', '+00:00'))
                if abs((record_time - existing_time).total_seconds()) <= self.time_window.total_seconds():
                    should_add = True
                    break
            
            if should_add:
                groups[prompt_hash].append(record)
        
        return groups
    
    def _get_time_span(self, records: List[Dict[str, Any]]) -> str:
        """Calculate time span of retry loop"""
        if len(records) < 2:
            return "0 seconds"
        
        timestamps = []
        for record in records:
            try:
                ts = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                timestamps.append(ts)
            except (KeyError, ValueError):
                continue
        
        if len(timestamps) < 2:
            return "0 seconds"
        
        span = max(timestamps) - min(timestamps)
        return f"{span.total_seconds():.1f} seconds" 