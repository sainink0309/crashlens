"""
Fallback Storm Detector
Detects patterns of model fallbacks that suggest configuration issues
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta


class FallbackStormDetector:
    """Detects fallback storms in API calls"""
    
    def __init__(self, fallback_threshold: int = 3, time_window_minutes: int = 10):
        self.fallback_threshold = fallback_threshold
        self.time_window = timedelta(minutes=time_window_minutes)
    
    def detect(self, traces: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detect fallback storms across all traces"""
        detections = []
        
        for trace_id, records in traces.items():
            # Look for patterns of model changes within time window
            fallback_groups = self._find_fallback_patterns(records)
            
            for group in fallback_groups:
                if len(group) >= self.fallback_threshold:
                    # Calculate waste metrics
                    total_tokens = sum(r.get('completion_tokens', 0) for r in group)
                    total_cost = sum(r.get('cost', 0.0) for r in group)
                    
                    # Identify the fallback sequence
                    models_used = [r.get('model', 'unknown') for r in group]
                    unique_models = list(dict.fromkeys(models_used))  # Preserve order
                    
                    detection = {
                        'type': 'fallback_storm',
                        'trace_id': trace_id,
                        'severity': 'high' if len(group) > 5 else 'medium',
                        'description': f"Fallback storm detected: {len(group)} model switches",
                        'waste_tokens': total_tokens,
                        'waste_cost': total_cost,
                        'fallback_count': len(group),
                        'models_sequence': unique_models,
                        'time_span': self._get_time_span(group),
                        'sample_prompt': group[0].get('prompt', '')[:100] + '...' if len(group[0].get('prompt', '')) > 100 else group[0].get('prompt', ''),
                        'records': group
                    }
                    detections.append(detection)
        
        return detections
    
    def _find_fallback_patterns(self, records: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Find groups of records that show fallback patterns"""
        if len(records) < 2:
            return []
        
        # Sort records by timestamp
        sorted_records = sorted(records, key=lambda r: r.get('startTime', ''))
        
        fallback_groups = []
        current_group = []
        
        for i, record in enumerate(sorted_records):
            if not current_group:
                current_group = [record]
                continue
            
            # Check if this record is within time window and shows model change
            current_time = datetime.fromisoformat(record['startTime'].replace('Z', '+00:00'))
            last_record = current_group[-1]
            last_time = datetime.fromisoformat(last_record['startTime'].replace('Z', '+00:00'))
            
            time_diff = abs((current_time - last_time).total_seconds())
            current_model = record.get('model', '')
            last_model = last_record.get('model', '')
            
            # Check if within time window and model changed
            if (time_diff <= self.time_window.total_seconds() and 
                current_model != last_model and 
                self._is_similar_prompt(record, last_record)):
                
                current_group.append(record)
            else:
                # End current group if it has enough records
                if len(current_group) >= self.fallback_threshold:
                    fallback_groups.append(current_group)
                current_group = [record]
        
        # Don't forget the last group
        if len(current_group) >= self.fallback_threshold:
            fallback_groups.append(current_group)
        
        return fallback_groups
    
    def _is_similar_prompt(self, record1: Dict[str, Any], record2: Dict[str, Any]) -> bool:
        """Check if two records have similar prompts"""
        prompt1 = record1.get('prompt', '')
        prompt2 = record2.get('prompt', '')
        
        # Simple similarity check (in real implementation, use more sophisticated comparison)
        if not prompt1 or not prompt2:
            return False
        
        # Check if prompts are similar (same first 50 chars or similar length)
        return (prompt1[:50] == prompt2[:50] or 
                abs(len(prompt1) - len(prompt2)) < 20)
    
    def _get_time_span(self, records: List[Dict[str, Any]]) -> str:
        """Calculate time span of fallback storm"""
        if len(records) < 2:
            return "0 seconds"
        
        timestamps = []
        for record in records:
            try:
                ts = datetime.fromisoformat(record['startTime'].replace('Z', '+00:00'))
                timestamps.append(ts)
            except (KeyError, ValueError):
                continue
        
        if len(timestamps) < 2:
            return "0 seconds"
        
        span = max(timestamps) - min(timestamps)
        return f"{span.total_seconds():.1f} seconds" 