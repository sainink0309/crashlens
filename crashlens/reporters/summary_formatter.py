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
        """Format cost summary from traces"""
        if not traces:
            return "🔒 CrashLens runs 100% locally. No data leaves your system.\nℹ️  No traces found for summary"
        
        output = []
        output.append("🔒 CrashLens runs 100% locally. No data leaves your system.")
        if summary_only:
            output.append("📝 Summary-only mode: Trace IDs are suppressed for safe internal sharing.")
        output.append("📊 **CrashLens Cost Summary**")
        output.append("=" * 50)
        
        # Add analysis metadata
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output.append(f"📅 **Analysis Date**: {current_time}")
        output.append(f"🔍 **Traces Analyzed**: {len(traces):,}")
        output.append("")
        
        # Scrub PII from traces
        scrubbed_traces = self.pii_scrubber.scrub_traces(traces)
        
        # Aggregate data
        route_costs = defaultdict(float)
        model_costs = defaultdict(float)
        team_costs = defaultdict(float)
        total_cost = 0.0
        total_tokens = 0
        
        # Process all traces
        for trace_id, records in scrubbed_traces.items():
            for record in records:
                # Calculate cost for this record
                cost = self._calculate_record_cost(record, model_pricing)
                tokens = record.get('completion_tokens', 0) + record.get('prompt_tokens', 0)
                
                # Extract metadata
                route = record.get('route', 'unknown')
                model = record.get('model', 'unknown')
                team = record.get('metadata', {}).get('team', 'unknown')
                
                # Aggregate by categories
                route_costs[route] += cost
                model_costs[model] += cost
                team_costs[team] += cost
                total_cost += cost
                total_tokens += tokens
        
        # Summary stats
        output.append(f"💰 **Total Cost**: ${total_cost:.4f}")
        output.append(f"🎯 **Total Tokens**: {total_tokens:,}")
        output.append(f"📈 **Total Traces**: {len(scrubbed_traces)}")
        output.append("")
        
        # Route breakdown
        if len(route_costs) > 1 or 'unknown' not in route_costs:
            output.append("🛣️  **Cost by Route**")
            for route, cost in sorted(route_costs.items(), key=lambda x: x[1], reverse=True):
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                output.append(f"  {route}: ${cost:.4f} ({percentage:.1f}%)")
            output.append("")
        
        # Model breakdown
        output.append("🤖 **Cost by Model**")
        for model, cost in sorted(model_costs.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            output.append(f"  {model}: ${cost:.4f} ({percentage:.1f}%)")
        output.append("")
        
        # Team breakdown (if available)
        if len(team_costs) > 1 or 'unknown' not in team_costs:
            output.append("👥 **Cost by Team**")
            for team, cost in sorted(team_costs.items(), key=lambda x: x[1], reverse=True):
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                output.append(f"  {team}: ${cost:.4f} ({percentage:.1f}%)")
            output.append("")
        
        # Top expensive traces (suppress trace IDs in summary_only)
        trace_costs = {}
        for trace_id, records in scrubbed_traces.items():
            trace_cost = sum(self._calculate_record_cost(record, model_pricing) for record in records)
            trace_costs[trace_id] = trace_cost
        
        if trace_costs:
            output.append("🏆 **Top 5 Most Expensive Traces**")
            for i, (trace_id, cost) in enumerate(sorted(trace_costs.items(), key=lambda x: x[1], reverse=True)[:5], 1):
                if summary_only:
                    output.append(f"  Trace #{i}: ${cost:.4f}")
                else:
                    output.append(f"  {trace_id}: ${cost:.4f}")
        
        return "\n".join(output)
    
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