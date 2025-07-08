"""
Short Model Detector
Detects inefficient use of expensive models (GPT-4, Claude 3 Opus, etc.) for short/simple prompts
"""

from typing import Dict, List, Any


class ShortModelDetector:
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
    
    def detect(self, traces: Dict[str, List[Dict[str, Any]]], model_pricing: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Detect inefficient expensive model usage across all traces"""
        detections = []
        
        for trace_id, records in traces.items():
            for record in records:
                model = record.get('model', '').lower()
                prompt = record.get('prompt', '')
                
                # Check if this is an expensive model usage
                if model in self.expensive_models:
                    # Use actual prompt_tokens if available, otherwise estimate
                    prompt_tokens = record.get('prompt_tokens', len(prompt.split()))
                    
                    if prompt_tokens < self.min_tokens_for_gpt4:
                        # Calculate potential savings using actual pricing
                        current_cost = self._calculate_record_cost(record, model_pricing)
                        suggested_model = self.expensive_models[model]
                        
                        # Calculate cost with cheaper model
                        cheaper_cost = self._calculate_cost_with_model(record, suggested_model, model_pricing)
                        # Clamp savings to zero if negative
                        potential_savings = max(0.0, current_cost - cheaper_cost)
                        
                        detection = {
                            'type': 'expensive_model_short',
                            'trace_id': trace_id,
                            'severity': 'medium',
                            'description': f"{model.upper()} used for short prompt ({prompt_tokens} tokens)",
                            'waste_tokens': record.get('completion_tokens', 0),
                            'waste_cost': potential_savings,  # Cost difference between models, never negative
                            'prompt_length': prompt_tokens,
                            'model_used': model,
                            'suggested_model': suggested_model,
                            'sample_prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                            'records': [record]
                        }
                        detections.append(detection)
        
        return detections
    
    def _calculate_record_cost(self, record: Dict[str, Any], model_pricing: Dict[str, Any]) -> float:
        """Calculate cost for a single record using actual pricing"""
        if not model_pricing:
            return record.get('cost', 0.0)
        
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
    
    def _calculate_cost_with_model(self, record: Dict[str, Any], new_model: str, model_pricing: Dict[str, Any]) -> float:
        """Calculate what the cost would be with a different model"""
        if not model_pricing:
            return 0.0
        
        input_tokens = record.get('prompt_tokens', 0)
        output_tokens = record.get('completion_tokens', 0)
        
        # Calculate from pricing config for the new model
        model_config = model_pricing.get(new_model, {})
        if model_config:
            input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
            output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
            return input_cost + output_cost
        
        return 0.0 