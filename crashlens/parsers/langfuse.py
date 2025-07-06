"""
Langfuse JSONL Parser
Parses Langfuse-style JSONL logs and groups by trace_id
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class LangfuseParser:
    """Parser for Langfuse-style JSONL log files"""
    
    def __init__(self):
        self.traces: Dict[str, List[Dict[str, Any]]] = {}
    
    def parse_file(self, file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Parse JSONL file and group by trace_id"""
        self.traces.clear()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    trace_id = record.get('trace_id')
                    
                    if trace_id:
                        if trace_id not in self.traces:
                            self.traces[trace_id] = []
                        self.traces[trace_id].append(record)
                        
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