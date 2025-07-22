"""
Overkill Model Detector
Detects inefficient use of expensive models for short/simple prompts according to official checklist.
"""

import re
import json
from typing import Dict, List, Any, Optional


class OverkillModelDetector:
    """Detects overkill usage of expensive models for short/simple tasks"""
    
    def __init__(self, max_prompt_tokens_for_overkill: int = 20, max_prompt_chars: int = 150):
        """
        Initialize the Overkill Model Detector
        
        Args:
            max_prompt_tokens_for_overkill: Maximum tokens for short prompt detection
            max_prompt_chars: Maximum characters for very short prompt detection
        """
        self.max_prompt_tokens_for_overkill = max_prompt_tokens_for_overkill
        self.max_prompt_chars = max_prompt_chars
        
        # Expensive models that should be checked for overkill
        self.overkill_model_names = [
            "gpt-4", "gpt-4-1106-preview", "gpt-4-turbo", "gpt-4-32k",
            "claude-2", "claude-2.1", "claude-3-opus"
        ]
        
        # Keywords indicating simple tasks
        self.simple_prompt_keywords = [
            "summarize", "fix grammar", "translate", "explain"
        ]
    
    def detect(self, traces: Dict[str, List[Dict[str, Any]]], model_pricing: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Detect overkill model usage according to official checklist
        
        Args:
            traces: Dictionary of trace_id -> list of records
            model_pricing: Optional pricing configuration
            
        Returns:
            List of detection results
        """
        detections = []
        
        for trace_id, records in traces.items():
            for record in records:
                detection = self._check_overkill_pattern(trace_id, record, model_pricing)
                if detection:
                    detections.append(detection)
        
        return detections
    
    def _check_overkill_pattern(self, trace_id: str, record: Dict[str, Any], model_pricing: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if a single record represents overkill model usage"""
        
        # ✅ CHECKLIST: Span uses expensive model
        model = record.get('model', '').lower()
        if not self._is_expensive_model(model):
            return None
        
        # ✅ CHECKLIST: Span succeeded (returned output, not error)
        if not self._span_succeeded(record):
            return None
        
        prompt = record.get('prompt', '')
        
        # ✅ CHECKLIST: Check if prompt is short
        prompt_tokens = self._estimate_tokens(prompt)
        if prompt_tokens > self.max_prompt_tokens_for_overkill:
            return None
        
        # ✅ CHECKLIST: Check if task looks simple via heuristics
        simple_reason = self._check_simple_task_heuristics(prompt)
        if not simple_reason:
            return None
        
        # ⚠️ SUPPRESSION LOGIC: Do not flag complex formats
        if self._has_complex_format(prompt):
            return None
        
        # Calculate estimated cost
        estimated_cost = self._calculate_estimated_cost(record, model_pricing)
        
        # 💡 CLI OUTPUT: Return detection metadata
        return {
            'type': 'overkill_model',
            'trace_id': trace_id,
            'severity': 'medium',
            'model': model,
            'prompt_tokens': prompt_tokens,
            'prompt_length': len(prompt),
            'reason': simple_reason,
            'estimated_cost_usd': estimated_cost,
            'overkill_detected': True,
            'description': f"Overkill: {model} used for simple task ({simple_reason})",
            'waste_cost': estimated_cost * 0.7,  # Assume 70% could be saved with cheaper model
            'sample_prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
        }
    
    def _is_expensive_model(self, model: str) -> bool:
        """Check if model is considered expensive for overkill detection"""
        model_lower = model.lower()
        return any(expensive in model_lower for expensive in self.overkill_model_names)
    
    def _span_succeeded(self, record: Dict[str, Any]) -> bool:
        """Check if span succeeded (returned output, not error)"""
        # Check for completion tokens
        completion_tokens = record.get('usage', {}).get('completion_tokens', 0)
        if completion_tokens > 0:
            return True
        
        # Check for direct output fields
        if record.get('completion') or record.get('output'):
            return True
        
        # Check if there's no error indicated
        if not record.get('error') and not record.get('failed', False):
            return True
        
        return False
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using simple word splitting (approximation)"""
        if not text:
            return 0
        # Simple approximation: ~0.75 tokens per word
        word_count = len(text.split())
        return max(1, int(word_count * 0.75))
    
    def _check_simple_task_heuristics(self, prompt: str) -> Optional[str]:
        """
        Check if task looks simple via heuristics
        Returns reason string if simple, None if complex
        """
        prompt_lower = prompt.lower().strip()
        
        # ✅ CHECKLIST: Prompt starts with simple keywords
        for keyword in self.simple_prompt_keywords:
            if prompt_lower.startswith(keyword):
                return f"prompt starts with '{keyword}'"
        
        # ✅ CHECKLIST: Prompt length very short
        if len(prompt) < self.max_prompt_chars:
            return f"prompt too short ({len(prompt)} chars)"
        
        # Additional heuristics for simple tasks
        simple_patterns = [
            (r'^(what is|what are)', "simple question"),
            (r'^(how to)', "simple how-to"),
            (r'^(define|definition)', "simple definition"),
            (r'^(list|show me)', "simple listing"),
        ]
        
        for pattern, reason in simple_patterns:
            if re.match(pattern, prompt_lower):
                return reason
        
        return None
    
    def _has_complex_format(self, prompt: str) -> bool:
        """Check if prompt contains complex formats that should not be flagged"""
        # ⚠️ SUPPRESSION: Complex JSON-like structures
        if re.search(r'\{"task":|"context":|"instructions":', prompt):
            return True
        
        # ⚠️ SUPPRESSION: Multi-line structured prompts
        if prompt.count('\n') > 3:
            return True
        
        # ⚠️ SUPPRESSION: Code-like content
        if re.search(r'```|def |class |import |function', prompt):
            return True
        
        return False
    
    def _calculate_estimated_cost(self, record: Dict[str, Any], model_pricing: Optional[Dict[str, Any]]) -> float:
        """Calculate estimated cost for the record"""
        # Use existing cost if available
        if 'cost' in record and record['cost'] is not None:
            return float(record['cost'])
        
        # Calculate from pricing if available
        if model_pricing:
            model = record.get('model', '')
            model_config = model_pricing.get(model, {})
            if model_config:
                input_tokens = record.get('usage', {}).get('prompt_tokens', 0)
                output_tokens = record.get('usage', {}).get('completion_tokens', 0)
                
                input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
                output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
                return input_cost + output_cost
        
        # Fallback estimation for common models
        model = record.get('model', '').lower()
        input_tokens = record.get('usage', {}).get('prompt_tokens', 0)
        output_tokens = record.get('usage', {}).get('completion_tokens', 0)
        
        if 'gpt-4' in model:
            return (input_tokens * 0.03 + output_tokens * 0.06) / 1000
        elif 'claude-2' in model:
            return (input_tokens * 0.008 + output_tokens * 0.024) / 1000
        
        return 0.0

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