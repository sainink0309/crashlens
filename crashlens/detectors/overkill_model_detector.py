"""
Expensive Model Short Detector
Detects inefficient use of expensive models for short/simple prompts (multi-model and single-model traces).
"""

from typing import Dict, List, Any, Optional


class OverkillModelDetector:
    """Detects wasteful use of expensive models for short/simple prompts"""
    
    def __init__(self, prompt_token_threshold: int = 50, completion_token_threshold: int = 100, min_tokens_for_gpt4: int = 100):
        self.prompt_token_threshold = prompt_token_threshold
        self.completion_token_threshold = completion_token_threshold
        self.min_tokens_for_gpt4 = min_tokens_for_gpt4
        
        self.expensive_models = {
            'gpt-4': 'gpt-3.5-turbo',
            'gpt-4-32k': 'gpt-3.5-turbo-16k',
            'gpt-4-turbo': 'gpt-3.5-turbo',
            'claude-3-opus': 'claude-3-sonnet',
            'claude-3-sonnet': 'claude-3-haiku',
            'claude-2.1': 'claude-3-haiku',
            'claude-2.0': 'claude-3-haiku'
        }
    
    def detect(self, traces: Dict[str, List[Dict[str, Any]]], model_pricing: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Detects wasteful use of expensive models for short/simple prompts.
        Only flags 'expensive_model_short' and recommends a cheaper model if appropriate.
        Handles both single-model and multi-model traces.
        """
        return detect_expensive_model_waste(
            traces, 
            self.prompt_token_threshold, 
            self.completion_token_threshold, 
            self.min_tokens_for_gpt4, 
            model_pricing
        )

def detect_expensive_model_waste(
    traces: Dict[str, List[Dict[str, Any]]],
    prompt_token_threshold: int = 50,
    completion_token_threshold: int = 100,
    min_tokens_for_gpt4: int = 100,
    model_pricing: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Detects wasteful use of expensive models for short/simple prompts.
    Only flags 'expensive_model_short' and recommends a cheaper model if appropriate.
    Handles both single-model and multi-model traces.
    """
    expensive_models = {
        'gpt-4': 'gpt-3.5-turbo',
        'gpt-4-32k': 'gpt-3.5-turbo-16k',
        'gpt-4-turbo': 'gpt-3.5-turbo',
        'claude-3-opus': 'claude-3-sonnet',
        'claude-3-sonnet': 'claude-3-haiku',
        'claude-2.1': 'claude-3-haiku',
        'claude-2.0': 'claude-3-haiku'
    }
    detections = []
    for trace_id, records in traces.items():
        for record in records:
            model = record.get('model', '').lower()
            prompt = record.get('prompt', '')
            if model in expensive_models:
                prompt_tokens = record.get('prompt_tokens', len(prompt.split()))
                if prompt_tokens < min_tokens_for_gpt4:
                    current_cost = _calculate_record_cost(record, model_pricing)
                    suggested_model = expensive_models[model]
                    cheaper_cost = _calculate_cost_with_model(record, suggested_model, model_pricing)
                    potential_savings = max(0.0, current_cost - cheaper_cost)
                    detections.append({
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
                    })
    return [d for d in detections if d is not None]

def _calculate_record_cost(record: Dict[str, Any], model_pricing: Optional[Dict[str, Any]]) -> float:
    if not model_pricing:
        return record.get('cost', 0.0)
    model = record.get('model', 'gpt-3.5-turbo')
    input_tokens = record.get('prompt_tokens', 0)
    output_tokens = record.get('completion_tokens', 0)
    if 'cost' in record and record['cost'] is not None:
        return record['cost']
    model_config = model_pricing.get(model, {})
    if model_config:
        input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
        output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
        return input_cost + output_cost
    return 0.0

def _calculate_cost_with_model(record: Dict[str, Any], new_model: str, model_pricing: Optional[Dict[str, Any]]) -> float:
    if not model_pricing:
        return 0.0
    input_tokens = record.get('prompt_tokens', 0)
    output_tokens = record.get('completion_tokens', 0)
    model_config = model_pricing.get(new_model, {})
    if model_config:
        input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
        output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
        return input_cost + output_cost
    return 0.0

# Example usage:
# issues = detect_expensive_model_waste(traces, model_pricing=...) 