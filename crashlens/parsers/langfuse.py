"""
Langfuse JSONL Parser
Parses Langfuse-style JSONL logs and groups by trace_id
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class LangfuseParser:
    """Parser for Langfuse-style JSONL log files (newer style)"""
    
    def __init__(self):
        self.traces: Dict[str, List[Dict[str, Any]]] = {}
    
    def parse_file(self, file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Parse JSONL file and group by traceId"""
        self.traces.clear()
        with open(file_path, 'r', encoding='utf-8') as f:
            return self._parse_lines(f)
    
    def parse_string(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse JSONL string and group by traceId"""
        self.traces.clear()
        lines = text.splitlines()
        return self._parse_lines(lines)
    
    def parse_stdin(self) -> Dict[str, List[Dict[str, Any]]]:
        """Parse JSONL from stdin and group by traceId"""
        self.traces.clear()
        import sys
        return self._parse_lines(sys.stdin)

    def _extract_fields(self, record: dict) -> dict:
        # Only process if type == 'generation'
        if record.get('type') != 'generation':
            return None
        # Required fields (with fallback for missing nested fields)
        return {
            'traceId': record.get('traceId'),
            'type': record.get('type'),
            'startTime': record.get('startTime'),
            'endTime': record.get('endTime'),
            'level': record.get('level'),
            'input.model': record.get('input', {}).get('model'),
            'input.prompt': record.get('input', {}).get('prompt'),
            'usage.prompt_tokens': record.get('usage', {}).get('prompt_tokens'),
            'usage.completion_tokens': record.get('usage', {}).get('completion_tokens'),
            'metadata.fallback_attempted': record.get('metadata', {}).get('fallback_attempted'),
            'metadata.fallback_reason': record.get('metadata', {}).get('fallback_reason'), # optional
            'name': record.get('name'), # optional
            'metadata.source': record.get('metadata', {}).get('source'), # optional
        }

    def _parse_lines(self, lines) -> Dict[str, List[Dict[str, Any]]]:
        """Parse lines and group by traceId (newer style)"""
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                trace_id = record.get('traceId')
                parsed = self._extract_fields(record)
                if trace_id and parsed:
                    if trace_id not in self.traces:
                        self.traces[trace_id] = []
                    self.traces[trace_id].append(parsed)
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Invalid JSON on line {line_num}: {e}")
                continue
        return self.traces
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary statistics for a trace"""
        if trace_id not in self.traces:
            return {}
        
        trace_records = self.traces[trace_id]
        
        # Extract key metrics
        total_tokens = 0
        total_cost = 0.0
        model_usage = {}
        
        for record in trace_records:
            # Extract token usage
            if 'completion_tokens' in record:
                total_tokens += record.get('completion_tokens', 0)
            
            # Extract cost if available
            if 'cost' in record:
                total_cost += record.get('cost', 0.0)
            
            # Track model usage
            model = record.get('model', 'unknown')
            if model not in model_usage:
                model_usage[model] = 0
            model_usage[model] += 1
        
        return {
            'trace_id': trace_id,
            'total_records': len(trace_records),
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'model_usage': model_usage,
            'records': trace_records
        } 