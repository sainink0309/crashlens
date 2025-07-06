"""
Slack-style Formatter
Formats detection results in emoji-rich text format for stdout
"""

from typing import Dict, List, Any


class SlackFormatter:
    """Formats detections in Slack-style emoji text"""
    
    def __init__(self):
        self.severity_emojis = {
            'high': '🔴',
            'medium': '🟡', 
            'low': '🟢'
        }
        
        self.type_emojis = {
            'retry_loop': '🔄',
            'gpt4_short': '💎',
            'fallback_storm': '⚡'
        }
    
    def format(self, detections: List[Dict[str, Any]], traces: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format detections in Slack-style output"""
        if not detections:
            return "✅ No token waste patterns detected! Your GPT usage looks efficient."
        
        output = []
        output.append("🚨 **CrashLens Token Waste Report**")
        output.append("=" * 50)
        
        # Group by type
        by_type = {}
        for detection in detections:
            det_type = detection['type']
            if det_type not in by_type:
                by_type[det_type] = []
            by_type[det_type].append(detection)
        
        # Summary stats
        total_waste_cost = sum(d.get('waste_cost', 0) for d in detections)
        total_waste_tokens = sum(d.get('waste_tokens', 0) for d in detections)
        
        output.append(f"💰 **Total Potential Savings**: ${total_waste_cost:.2f}")
        output.append(f"🎯 **Wasted Tokens**: {total_waste_tokens:,}")
        output.append(f"📊 **Issues Found**: {len(detections)}")
        output.append("")
        
        # Format each type
        for det_type, type_detections in by_type.items():
            type_emoji = self.type_emojis.get(det_type, '❓')
            type_name = det_type.replace('_', ' ').title()
            
            output.append(f"{type_emoji} **{type_name}** ({len(type_detections)} issues)")
            
            for detection in type_detections:
                severity_emoji = self.severity_emojis.get(detection['severity'], '⚪')
                output.append(self._format_detection(detection, severity_emoji))
            
            output.append("")
        
        # Monthly projection
        if total_waste_cost > 0:
            monthly_projection = total_waste_cost * 30  # Rough estimate
            output.append(f"📈 **Monthly Projection**: ${monthly_projection:.2f} potential savings")
        
        return "\n".join(output)
    
    def _format_detection(self, detection: Dict[str, Any], severity_emoji: str) -> str:
        """Format a single detection"""
        lines = []
        
        # Main description
        lines.append(f"  {severity_emoji} {detection['description']}")
        
        # Cost and token info
        if detection.get('waste_cost', 0) > 0:
            lines.append(f"     💰 Waste: ${detection['waste_cost']:.4f}")
        
        if detection.get('waste_tokens', 0) > 0:
            lines.append(f"     🎯 Tokens: {detection['waste_tokens']:,}")
        
        # Type-specific details
        if detection['type'] == 'retry_loop':
            lines.append(f"     🔄 Retries: {detection.get('retry_count', 0)}")
            lines.append(f"     ⏱️  Time: {detection.get('time_span', 'unknown')}")
        
        elif detection['type'] == 'gpt4_short':
            lines.append(f"     📝 Prompt length: {detection.get('prompt_length', 0)} tokens")
            lines.append(f"     🤖 Model: {detection.get('model_used', 'unknown')}")
            lines.append(f"     💡 Suggested: {detection.get('suggested_model', 'gpt-3.5-turbo')}")
        
        elif detection['type'] == 'fallback_storm':
            lines.append(f"     ⚡ Fallbacks: {detection.get('fallback_count', 0)}")
            models = detection.get('models_sequence', [])
            if models:
                lines.append(f"     🔄 Models: {' → '.join(models)}")
            lines.append(f"     ⏱️  Time: {detection.get('time_span', 'unknown')}")
        
        # Sample prompt
        if detection.get('sample_prompt'):
            lines.append(f"     📄 Sample: {detection['sample_prompt']}")
        
        # Trace ID
        lines.append(f"     🔗 Trace: {detection.get('trace_id', 'unknown')}")
        
        return "\n".join(lines) 