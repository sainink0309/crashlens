"""
Summary Formatter
Aggregates total costs by route, model, and team from traces
"""

from typing import Dict, List, Any
from datetime import datetime
from ..utils.pii_scrubber import PIIScrubber
from collections import defaultdict


class SummaryFormatter:
    """Formats cost summaries by route, model, and team"""
    
    def __init__(self):
        self.pii_scrubber = PIIScrubber()
    
    def format(self, traces: Dict[str, List[Dict[str, Any]]], model_pricing: Dict[str, Any], summary_only: bool = False) -> str:
        """Format cost summary from traces using compact FinOps format"""
        if not traces:
            return "🔒 CrashLens runs 100% locally. No data leaves your system.\nℹ️  No traces found for summary"
        
        output = []
        output.append("🔒 CrashLens runs 100% locally. No data leaves your system.")
        if summary_only:
            output.append("📝 Summary-only mode: Trace IDs are suppressed for safe internal sharing.")
        
        # Calculate totals first
        total_cost = 0.0
        total_tokens = 0
        model_costs = defaultdict(float)
        
        # Process all traces for totals
        for trace_id, records in traces.items():
            for record in records:
                cost = self._calculate_record_cost(record, model_pricing)
                total_cost += cost
                
                # Get tokens from multiple possible locations
                usage = record.get('usage', {})
                prompt_tokens = (usage.get('prompt_tokens', 0) or 
                               record.get('prompt_tokens', 0) or 0)
                completion_tokens = (usage.get('completion_tokens', 0) or 
                                   record.get('completion_tokens', 0) or 0)
                total_tokens += prompt_tokens + completion_tokens
                
                # Track model costs
                model = record.get('input', {}).get('model', record.get('model', 'unknown'))
                model_costs[model] += cost
        
        # Generate compact header (similar to Slack format)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cost_str = f"${total_cost:.4f}" if total_cost < 0.01 else f"${total_cost:.2f}"
        
        # Only show tokens if we have a meaningful count, otherwise suppress the field
        if total_tokens > 0:
            output.append(f"📊 CrashLens Summary – {timestamp} | Traces: {len(traces)} | Cost: {cost_str} | Tokens: {total_tokens:,}")
        else:
            output.append(f"📊 CrashLens Summary – {timestamp} | Traces: {len(traces)} | Cost: {cost_str}")
        output.append("")
        
        # Model breakdown - compact format
        if model_costs:
            sorted_models = sorted(model_costs.items(), key=lambda x: x[1], reverse=True)
            model_parts = []
            for model, cost in sorted_models:
                cost_str = f"${cost:.4f}" if cost < 0.01 else f"${cost:.2f}"
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                model_parts.append(f"{model}: {cost_str} ({percentage:.0f}%)")
            
            output.append(f"🤖 Model Breakdown: {' | '.join(model_parts)}")
        
        # Top expensive traces
        self._add_top_traces_summary(output, traces, summary_only)
        
        return "\n".join(output)

    def _add_top_traces_summary(self, output: List[str], traces: Dict[str, List[Dict[str, Any]]], summary_only: bool):
        """Add compact top traces section"""
        trace_costs = {}
        
        for trace_id, records in traces.items():
            trace_cost = sum(record.get('cost', 0.0) for record in records)
            if trace_cost > 0:
                trace_costs[trace_id] = trace_cost
        
        if trace_costs:
            sorted_traces = sorted(trace_costs.items(), key=lambda x: x[1], reverse=True)[:5]  # Top 5 for summary
            trace_lines = []
            
            for i, (trace_id, cost) in enumerate(sorted_traces, 1):
                cost_str = f"${cost:.4f}" if cost < 0.01 else f"${cost:.2f}"
                if summary_only:
                    trace_lines.append(f"#{i}: {cost_str}")
                else:
                    # Get model from first record
                    first_record = traces[trace_id][0] if traces[trace_id] else {}
                    model = first_record.get('input', {}).get('model', first_record.get('model', 'unknown'))
                    trace_lines.append(f"#{i}: {trace_id[:8]}... → {model} → {cost_str}")
            
            output.append("")
            output.append(f"🏆 Top {len(trace_lines)} Traces: " + " | ".join(trace_lines))
    
    def _calculate_record_cost(self, record: Dict[str, Any], model_pricing: Dict[str, Any]) -> float:
        """Calculate cost for a single record"""
        model = record.get('model', 'gpt-3.5-turbo')
        input_tokens = record.get('prompt_tokens', 0)
        output_tokens = record.get('completion_tokens', 0)
        
        # Use provided cost if available, otherwise calculate from pricing
        if 'cost' in record and record['cost'] is not None:
            return record['cost']
        
        # Calculate from pricing config
        model_config = model_pricing.get(model, {})
        if model_config:
            input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
            output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
            return input_cost + output_cost
        
        return 0.0 