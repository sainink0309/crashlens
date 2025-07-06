"""
GPT-4 Short Prompt Detector
Detects inefficient use of GPT-4 for short/simple prompts that could use GPT-3.5
"""

from typing import Dict, List, Any


class GPT4ShortDetector:
    """Detects inefficient GPT-4 usage for short prompts"""
    
    def __init__(self, min_tokens_for_gpt4: int = 100, gpt4_cost_multiplier: float = 20.0):
        self.min_tokens_for_gpt4 = min_tokens_for_gpt4
        self.gpt4_cost_multiplier = gpt4_cost_multiplier
    
    def detect(self, traces: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detect inefficient GPT-4 usage across all traces"""
        detections = []
        
        for trace_id, records in traces.items():
            for record in records:
                model = record.get('model', '').lower()
                prompt = record.get('prompt', '')
                
                # Check if this is GPT-4 usage
                if 'gpt-4' in model:
                    prompt_tokens = len(prompt.split())  # Simple token estimation
                    
                    if prompt_tokens < self.min_tokens_for_gpt4:
                        # Calculate potential savings
                        current_cost = record.get('cost', 0.0)
                        estimated_gpt35_cost = current_cost / self.gpt4_cost_multiplier
                        potential_savings = current_cost - estimated_gpt35_cost
                        
                        detection = {
                            'type': 'gpt4_short',
                            'trace_id': trace_id,
                            'severity': 'medium',
                            'description': f"GPT-4 used for short prompt ({prompt_tokens} tokens)",
                            'waste_tokens': record.get('completion_tokens', 0),
                            'waste_cost': potential_savings,
                            'prompt_length': prompt_tokens,
                            'model_used': model,
                            'suggested_model': 'gpt-3.5-turbo',
                            'sample_prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                            'records': [record]
                        }
                        detections.append(detection)
        
        return detections 