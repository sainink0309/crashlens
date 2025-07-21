"""
Markdown Formatter
Formats detection results in Markdown format for documentation
"""

from typing import Dict, List, Any
from datetime import datetime
from ..utils.pii_scrubber import PIIScrubber


class MarkdownFormatter:
    """Formats detections in Markdown format"""
    
    def __init__(self):
        self.severity_colors = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        self.pii_scrubber = PIIScrubber()
    
    def format(self, detections: List[Dict[str, Any]], traces: Dict[str, List[Dict[str, Any]]], summary_only: bool = False) -> str:
        """Format detections in Markdown output"""
        if not detections:
            return "🔒 CrashLens runs 100% locally. No data leaves your system.\n\n**No token waste patterns detected! Your GPT usage looks efficient.**"
        
        output = []
        output.append("🔒 CrashLens runs 100% locally. No data leaves your system.\n")
        if summary_only:
            output.append("> **Summary-only mode:** Prompts, sample inputs, and trace IDs are suppressed for safe internal sharing.\n")
        output.append("# CrashLens Token Waste Report")
        output.append("")
        
        # Add analysis metadata
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output.append(f"**Analysis Date:** {current_time}  \n")
        output.append(f"**Traces Analyzed:** {len(traces):,}  \n")
        output.append("")
        
        # Scrub PII from detections
        scrubbed_detections = [self.pii_scrubber.scrub_detection(detection) for detection in detections]
        
        # Aggregate detections by type
        aggregated = self._aggregate_detections(scrubbed_detections)
        
        # Summary table
        total_waste_cost = sum(d.get('waste_cost', 0) for d in scrubbed_detections)
        total_waste_tokens = sum(d.get('waste_tokens', 0) for d in scrubbed_detections)
        total_ai_spend = self._calculate_total_ai_spend(traces)
        
        # Sanity check: savings shouldn't exceed total spend
        total_waste_cost = min(total_waste_cost, total_ai_spend)
        
        output.append("## Summary")
        output.append("")
        output.append("| Metric | Value |")
        output.append("|--------|-------|")
        output.append(f"| Total AI Spend | ${total_ai_spend:.2f} |")
        output.append(f"| Total Potential Savings | ${total_waste_cost:.4f} |")
        output.append(f"| Wasted Tokens | {total_waste_tokens:,} |")
        output.append(f"| Issues Found | {len(scrubbed_detections)} |")
        output.append(f"| Traces Analyzed | {len(traces)} |")
        output.append("")
        
        # Format aggregated detections
        for det_type, group_data in aggregated.items():
            type_name = group_data['type'].replace('_', ' ').title()
            output.append(f"## {type_name} ({group_data['count']} issues)")
            output.append("")
            
            # Type summary table
            output.append("| Metric | Value |")
            output.append("|--------|-------|")
            output.append(f"| Total Waste Cost | ${group_data['total_waste_cost']:.4f} |")
            output.append(f"| Total Waste Tokens | {group_data['total_waste_tokens']:,} |")
            output.append("")
            
            # Aggregated details
            output.append(self._format_aggregated_detection(group_data, summary_only))
            output.append("")
        
        # Monthly projection
        if total_waste_cost > 0:
            monthly_projection = total_waste_cost * 30  # Rough estimate
            output.append("## Monthly Projection")
            output.append("")
            output.append(f"Based on current patterns, potential monthly savings: **${monthly_projection:.2f}**")
            output.append("")
        
        return "\n".join(output)
    
    def _aggregate_detections(self, detections: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Aggregate detections by type and model"""
        aggregated = {}
        
        for detection in detections:
            det_type = detection['type']
            model_used = detection.get('model_used', 'unknown')
            suggested_model = detection.get('suggested_model', 'unknown')
            
            # Create a key that groups by type and model combination
            if det_type == 'expensive_model_short':
                key = f"{det_type}_{model_used}_{suggested_model}"
            else:
                key = det_type
            
            if key not in aggregated:
                aggregated[key] = {
                    'type': det_type,
                    'count': 0,
                    'total_waste_cost': 0.0,
                    'total_waste_tokens': 0,
                    'sample_prompts': [],
                    'model_used': model_used,
                    'suggested_model': suggested_model,
                    'severity': detection.get('severity', 'medium'),
                    'detections': []
                }
            
            group = aggregated[key]
            group['count'] += 1
            group['total_waste_cost'] += detection.get('waste_cost', 0)
            group['total_waste_tokens'] += detection.get('waste_tokens', 0)
            group['detections'].append(detection)
            
            # Collect sample prompts (up to 3 unique ones)
            sample_prompt = detection.get('sample_prompt', '')
            if sample_prompt and sample_prompt not in group['sample_prompts'] and len(group['sample_prompts']) < 3:
                group['sample_prompts'].append(sample_prompt)
        
        return aggregated
    
    def _format_aggregated_detection(self, group_data: Dict[str, Any], summary_only: bool = False) -> str:
        """Format an aggregated detection group in Markdown"""
        lines = []
        
        # Main description
        if group_data['type'] == 'expensive_model_short':
            model_used = group_data['model_used'].upper()
            suggested_model = group_data['suggested_model']
            lines.append(f"**Issue**: {group_data['count']} traces used {model_used} instead of {suggested_model}")
        elif group_data['type'] == 'retry_loop':
            lines.append(f"**Issue**: {group_data['count']} traces with excessive retries")
        elif group_data['type'] == 'fallback_storm':
            lines.append(f"**Issue**: {group_data['count']} traces with model fallback storms")
        elif group_data['type'] == 'fallback_failure':
            lines.append(f"**Issue**: {group_data['count']} traces with unnecessary fallback calls")
        else:
            lines.append(f"**Issue**: {group_data['count']} traces affected")
        lines.append("")
        
        # Sample prompts (suppress in summary_only)
        if group_data['sample_prompts'] and not summary_only:
            lines.append("**Sample Prompts**:")
            for i, prompt in enumerate(group_data['sample_prompts'], 1):
                lines.append(f"{i}. `{prompt[:50]}{'...' if len(prompt) > 50 else ''}`")
            lines.append("")
        
        # Suggested fix
        if group_data['type'] == 'expensive_model_short':
            lines.append(f"**Suggested Fix**: Route short prompts to `{group_data['suggested_model']}`")
        elif group_data['type'] == 'retry_loop':
            lines.append("**Suggested Fix**: Implement exponential backoff and circuit breakers")
        elif group_data['type'] == 'fallback_storm':
            lines.append("**Suggested Fix**: Optimize model selection logic")
        elif group_data['type'] == 'fallback_failure':
            lines.append("**Suggested Fix**: Remove redundant fallback calls after successful cheaper model calls")
        
        return "\n".join(lines)

    def _format_detection(self, detection: Dict[str, Any], index: int, summary_only: bool = False) -> str:
        """Format a single detection in Markdown (kept for backward compatibility)"""
        severity_emoji = self.severity_colors.get(detection['severity'], '⚪')
        
        lines = []
        lines.append(f"### {severity_emoji} Issue #{index}")
        lines.append("")
        lines.append(f"**Description**: {detection['description']}")
        lines.append("")
        
        # Key metrics
        if detection.get('waste_cost', 0) > 0:
            lines.append(f"- **Waste Cost**: ${detection['waste_cost']:.4f}")
        
        if detection.get('waste_tokens', 0) > 0:
            lines.append(f"- **Waste Tokens**: {detection['waste_tokens']:,}")
        
        # Type-specific details
        if detection['type'] == 'retry_loop':
            lines.append(f"- **Retry Count**: {detection.get('retry_count', 0)}")
            lines.append(f"- **Time Span**: {detection.get('time_span', 'unknown')}")
        
        elif detection['type'] in ['gpt4_short', 'expensive_model_short', 'expensive_model_overkill']:
            lines.append(f"- **Completion Length**: {detection.get('completion_length', 0)} tokens")
            lines.append(f"- **Model Used**: {detection.get('model_used', 'unknown')}")
            lines.append(f"- **Suggested Model**: {detection.get('suggested_model', 'gpt-3.5-turbo')}")
        
        elif detection['type'] == 'fallback_storm':
            lines.append(f"- **Fallback Count**: {detection.get('fallback_count', 0)}")
            models = detection.get('models_sequence', [])
            if models:
                lines.append(f"- **Model Sequence**: {' → '.join(models)}")
            lines.append(f"- **Time Span**: {detection.get('time_span', 'unknown')}")
        
        elif detection['type'] == 'fallback_failure':
            lines.append(f"- **Primary Model**: {detection.get('primary_model', 'unknown')}")
            lines.append(f"- **Fallback Model**: {detection.get('fallback_model', 'unknown')}")
            lines.append(f"- **Time Between Calls**: {detection.get('time_between_calls', 'unknown')}")
            if not summary_only:
                lines.append(f"- **Primary Prompt**: `{detection.get('primary_prompt', '')[:50]}{'...' if len(detection.get('primary_prompt', '')) > 50 else ''}`")
        
        # Trace ID (suppress in summary_only)
        if not summary_only:
            lines.append(f"- **Trace ID**: `{detection.get('trace_id', 'unknown')}`")
            lines.append("")
        
        # Sample prompt (suppress in summary_only)
        if detection.get('sample_prompt') and not summary_only:
            lines.append("**Sample Prompt**:")
            lines.append("```")
            lines.append(detection['sample_prompt'])
            lines.append("```")
            lines.append("")
        
        return "\n".join(lines) 

    def _calculate_total_ai_spend(self, traces: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate the total cost of all traces using the pricing config"""
        from ..cli import load_pricing_config
        pricing_config = load_pricing_config()
        model_pricing = pricing_config.get('models', {})
        total = 0.0
        for records in traces.values():
            for record in records:
                model = record.get('model', 'gpt-3.5-turbo')
                input_tokens = record.get('prompt_tokens', 0)
                output_tokens = record.get('completion_tokens', 0)
                model_config = model_pricing.get(model, {})
                if model_config:
                    input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
                    output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
                    total += input_cost + output_cost
        return total 