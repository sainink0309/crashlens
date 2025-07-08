"""
Expensive Model Short Prompt Detector
Detects inefficient use of expensive models (GPT-4, Claude 3 Opus, etc.) for short/simple prompts
"""

from typing import Dict, List, Any


class GPT4ShortDetector:
    """Detects inefficient usage of expensive models for short prompts"""
    
    def __init__(self, min_tokens_for_gpt4: int = 100, gpt4_cost_multiplier: float = 20.0):
        self.min_tokens_for_gpt4 = min_tokens_for_gpt4
        self.gpt4_cost_multiplier = gpt4_cost_multiplier
        
        # Define expensive models and their cheaper alternatives
        self.expensive_models = {
            'gpt-4': 'gpt-3.5-turbo',
            'gpt-4-32k': 'gpt-3.5-turbo-16k',
            'gpt-4-turbo': 'gpt-3.5-turbo',
            'claude-3-opus': 'claude-3-sonnet',
            'claude-3-sonnet': 'claude-3-haiku',
            'claude-2.1': 'claude-3-haiku',
            'claude-2.0': 'claude-3-haiku'
        }
    
    def detect(self, traces: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detect inefficient expensive model usage across all traces"""
        detections = []
        
        for trace_id, records in traces.items():
            for record in records:
                model = record.get('model', '').lower()
                prompt = record.get('prompt', '')
                
                # Check if this is an expensive model usage
                if model in self.expensive_models:
                    prompt_tokens = len(prompt.split())  # Simple token estimation
                    
                    if prompt_tokens < self.min_tokens_for_gpt4:
                        # Calculate potential savings
                        current_cost = record.get('cost', 0.0)
                        suggested_model = self.expensive_models[model]
                        
                        # Estimate cost with cheaper model (rough approximation)
                        estimated_cheaper_cost = current_cost / self.gpt4_cost_multiplier
                        potential_savings = current_cost - estimated_cheaper_cost
                        
                        detection = {
                            'type': 'expensive_model_short',
                            'trace_id': trace_id,
                            'severity': 'medium',
                            'description': f"{model.upper()} used for short prompt ({prompt_tokens} tokens)",
                            'waste_tokens': record.get('completion_tokens', 0),
                            'waste_cost': potential_savings,
                            'prompt_length': prompt_tokens,
                            'model_used': model,
                            'suggested_model': suggested_model,
                            'sample_prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                            'records': [record]
                        }
                        detections.append(detection)
        
        return detections 