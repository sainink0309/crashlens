"""
Retry Loop Detector
Detects patterns of repeated API calls that suggest retry loops using semantic similarity.
This version includes significant performance and logic improvements.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

# Attempt to import sentence-transformers and set a flag.
# This makes the dependency optional for projects that might use this module.
try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    logging.warning(
        "sentence-transformers or PyTorch not found. "
        "RetryLoopDetector will fall back to exact string matching."
    )


class RetryLoopDetector:
    """
    Detects retry loops in API call traces using semantic similarity.

    This detector identifies when the same or a very similar prompt is sent
    multiple times within a short time window for the same trace ID.
    """

    def __init__(self, max_retries: int = 3, time_window_minutes: int = 5,
                 similarity_threshold: float = 0.9):
        """
        Initializes the detector with configurable thresholds.

        Args:
            max_retries (int): The number of calls (original + retries)
                               that must be exceeded to trigger a detection.
                               A value of 3 means 4+ calls will be flagged.
            time_window_minutes (int): The maximum time in minutes between
                                       consecutive similar calls for them to be
                                       considered part of the same loop.
            similarity_threshold (float): The cosine similarity score (0.0 to 1.0)
                                          required to consider two prompts as
                                          semantically similar.
        """
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1.")
        
        self.max_retries = max_retries
        self.time_window = timedelta(minutes=time_window_minutes)
        self.similarity_threshold = similarity_threshold
        self.model: Optional[SentenceTransformer] = None

        # Initialize the model only if the library is available.
        if SEMANTIC_AVAILABLE:
            try:
                # Using a fast and effective model for semantic similarity.
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logging.info("Semantic similarity model loaded successfully.")
            except Exception as e:
                logging.error(f"Failed to load sentence transformer model: {e}")
                # Ensure model is None if loading fails.
                self.model = None
        else:
            logging.info("Running in exact-match mode for retry detection.")

    def detect(self, traces: Dict[str, List[Dict[str, Any]]], model_pricing: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Analyzes all traces and detects retry loops based on semantic similarity.

        Args:
            traces (Dict[str, List[Dict[str, Any]]]): A dictionary where keys are
                                                      trace_ids and values are lists
                                                      of log records.

        Returns:
            List[Dict[str, Any]]: A list of detection dictionaries, one for each
                                  identified retry loop.
        """
        detections = []
        for trace_id, records in traces.items():
            # Optimization: a loop cannot occur if the number of records
            # is not greater than the retry threshold.
            if len(records) <= self.max_retries:
                continue

            # Find groups of consecutive, similar prompts.
            prompt_groups = self._find_retry_groups(records)

            for group in prompt_groups:
                # A loop is detected if the number of calls in a group
                # exceeds the configured maximum.
                if len(group) > self.max_retries:
                    total_tokens = sum(r.get('completion_tokens', 0) for r in group)
                    total_cost = sum(self._calculate_record_cost(r, model_pricing) for r in group)
                    
                    # The first record in the group is a good sample.
                    sample_prompt = group[0].get('prompt', 'N/A')

                    detection = {
                        'type': 'retry_loop',
                        'trace_id': trace_id,
                        'severity': 'high' if len(group) > 5 else 'medium',
                        'description': (
                            f"Retry loop detected with {len(group)} similar calls "
                            f"for the same trace."
                        ),
                        'waste_tokens': total_tokens,
                        'waste_cost': total_cost,
                        'retry_count': len(group),
                        'time_span': f"{self._get_time_span(group):.1f} seconds",
                        'sample_prompt': sample_prompt[:150] + ('...' if len(sample_prompt) > 150 else ''),
                        'detection_method': 'semantic' if self.model else 'exact_match',
                        'records': group
                    }
                    detections.append(detection)

        return detections

    def _find_retry_groups(self, records: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Groups consecutive records that are semantically similar and within the time window.
        This is the core logic for identifying potential retry loops.

        Args:
            records (List[Dict[str, Any]]): The list of log records for a single trace.

        Returns:
            List[List[Dict[str, Any]]]: A list of groups, where each group is a list of
                                        records considered to be part of a retry sequence.
        """
        # Ensure records are sorted by time to process them chronologically.
        try:
            sorted_records = sorted(
                [r for r in records if 'startTime' in r], 
                key=lambda r: r['startTime']
            )
        except (TypeError, ValueError):
            # Handle cases with malformed timestamps.
            return []

        if not sorted_records:
            return []

        # --- Batch Embedding for Performance ---
        prompts = [r.get('prompt', '') for r in sorted_records]
        embeddings = None
        if self.model:
            try:
                # Encode all prompts in one go for massive speedup.
                embeddings = self.model.encode(prompts, convert_to_tensor=True)
            except Exception as e:
                logging.warning(f"Failed to encode prompts for a trace: {e}. Falling back to exact match for this trace.")
                self.model = None # Disable for subsequent checks in this run if it fails
        
        # --- Grouping Logic ---
        all_groups = []
        current_group = [sorted_records[0]]

        for i in range(1, len(sorted_records)):
            prev_record = sorted_records[i-1]
            curr_record = sorted_records[i]

            # Check if the two consecutive records are similar enough to be in the same group.
            are_similar = False
            if embeddings is not None:
                # Use pre-computed embeddings for similarity check.
                similarity = util.cos_sim(embeddings[i-1], embeddings[i]).item()
                are_similar = similarity >= self.similarity_threshold
            else:
                # Fallback to exact string comparison if model is unavailable.
                prev_prompt = prev_record.get('prompt')
                curr_prompt = curr_record.get('prompt')
                if prev_prompt and curr_prompt:
                    are_similar = prev_prompt == curr_prompt

            # Check the time window constraint.
            prev_time = datetime.fromisoformat(prev_record['startTime'].replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(curr_record['startTime'].replace('Z', '+00:00'))
            is_within_time_window = (curr_time - prev_time) <= self.time_window

            if are_similar and is_within_time_window:
                # If similar and within the time limit, extend the current group.
                current_group.append(curr_record)
            else:
                # If not similar or outside the time window, the current loop has ended.
                # Store the completed group and start a new one.
                all_groups.append(current_group)
                current_group = [curr_record]
        
        # Add the last group after the loop finishes.
        all_groups.append(current_group)

        return all_groups

    def _get_time_span(self, records: List[Dict[str, Any]]) -> float:
        """Calculates the total time span of a group of records in seconds."""
        if len(records) < 2:
            return 0.0
        
        # Parse timestamps, ignoring potential errors.
        timestamps = []
        for r in records:
            try:
                timestamps.append(datetime.fromisoformat(r['startTime'].replace('Z', '+00:00')))
            except (KeyError, ValueError):
                continue
        
        if len(timestamps) < 2:
            return 0.0
            
        span = max(timestamps) - min(timestamps)
        return round(span.total_seconds(), 2)

    def _calculate_record_cost(self, record: Dict[str, Any], model_pricing: Optional[Dict[str, Any]]) -> float:
        """Calculate the cost of a record using model pricing configuration"""
        if not model_pricing:
            return record.get('cost', 0.0)
        
        model = record.get('model', 'gpt-3.5-turbo')
        input_tokens = record.get('prompt_tokens', 0)
        output_tokens = record.get('completion_tokens', 0)
        
        # Use existing cost if available
        if 'cost' in record and record['cost'] is not None:
            return record['cost']
        
        # Calculate cost using pricing configuration
        model_config = model_pricing.get(model, {})
        if model_config:
            input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
            output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
            return input_cost + output_cost
        
        return 0.0 