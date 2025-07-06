"""
Markdown Formatter
Formats detection results in Markdown format for documentation
"""

from typing import Dict, List, Any


class MarkdownFormatter:
    """Formats detections in Markdown format"""
    
    def __init__(self):
        self.severity_colors = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
    
    def format(self, detections: List[Dict[str, Any]], traces: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format detections in Markdown output"""
        if not detections:
            return "# CrashLens Report\n\n✅ No token waste patterns detected! Your GPT usage looks efficient."
        
        output = []
        output.append("# CrashLens Token Waste Report")
        output.append("")
        
        # Summary table
        total_waste_cost = sum(d.get('waste_cost', 0) for d in detections)
        total_waste_tokens = sum(d.get('waste_tokens', 0) for d in detections)
        
        output.append("## Summary")
        output.append("")
        output.append("| Metric | Value |")
        output.append("|--------|-------|")
        output.append(f"| Total Potential Savings | ${total_waste_cost:.2f} |")
        output.append(f"| Wasted Tokens | {total_waste_tokens:,} |")
        output.append(f"| Issues Found | {len(detections)} |")
        output.append(f"| Traces Analyzed | {len(traces)} |")
        output.append("")
        
        # Group by type
        by_type = {}
        for detection in detections:
            det_type = detection['type']
            if det_type not in by_type:
                by_type[det_type] = []
            by_type[det_type].append(detection)
        
        # Format each type
        for det_type, type_detections in by_type.items():
            type_name = det_type.replace('_', ' ').title()
            output.append(f"## {type_name} ({len(type_detections)} issues)")
            output.append("")
            
            # Type summary table
            type_waste_cost = sum(d.get('waste_cost', 0) for d in type_detections)
            type_waste_tokens = sum(d.get('waste_tokens', 0) for d in type_detections)
            
            output.append("| Metric | Value |")
            output.append("|--------|-------|")
            output.append(f"| Total Waste Cost | ${type_waste_cost:.4f} |")
            output.append(f"| Total Waste Tokens | {type_waste_tokens:,} |")
            output.append("")
            
            # Individual detections
            for i, detection in enumerate(type_detections, 1):
                output.append(self._format_detection(detection, i))
                output.append("")
        
        # Monthly projection
        if total_waste_cost > 0:
            monthly_projection = total_waste_cost * 30  # Rough estimate
            output.append("## Monthly Projection")
            output.append("")
            output.append(f"Based on current patterns, potential monthly savings: **${monthly_projection:.2f}**")
            output.append("")
        
        return "\n".join(output)
    
    def _format_detection(self, detection: Dict[str, Any], index: int) -> str:
        """Format a single detection in Markdown"""
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
        
        elif detection['type'] == 'gpt4_short':
            lines.append(f"- **Prompt Length**: {detection.get('prompt_length', 0)} tokens")
            lines.append(f"- **Model Used**: {detection.get('model_used', 'unknown')}")
            lines.append(f"- **Suggested Model**: {detection.get('suggested_model', 'gpt-3.5-turbo')}")
        
        elif detection['type'] == 'fallback_storm':
            lines.append(f"- **Fallback Count**: {detection.get('fallback_count', 0)}")
            models = detection.get('models_sequence', [])
            if models:
                lines.append(f"- **Model Sequence**: {' → '.join(models)}")
            lines.append(f"- **Time Span**: {detection.get('time_span', 'unknown')}")
        
        lines.append(f"- **Trace ID**: `{detection.get('trace_id', 'unknown')}`")
        lines.append("")
        
        # Sample prompt
        if detection.get('sample_prompt'):
            lines.append("**Sample Prompt**:")
            lines.append("```")
            lines.append(detection['sample_prompt'])
            lines.append("```")
            lines.append("")
        
        return "\n".join(lines) 