#!/usr/bin/env python3
"""
CrashLens CLI - Token Waste Detection Tool
Scans Langfuse-style JSONL logs for inefficient GPT API usage patterns.
"""

import click
import sys
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Set

from .parsers.langfuse import LangfuseParser
from .detectors.retry_loops import RetryLoopDetector
from .detectors.overkill_model_detector import OverkillModelDetector
from .detectors.fallback_storm import FallbackStormDetector
from .detectors.fallback_failure import FallbackFailureDetector
from .reporters.slack_formatter import SlackFormatter
from .reporters.markdown_formatter import MarkdownFormatter


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """CrashLens - Detect token waste in GPT API logs"""
    pass


def _create_record_id(record: Dict[str, Any], trace_id: str) -> str:
    """Create a unique identifier for a record"""
    return f"{trace_id}_{record.get('startTime', '')}_{record.get('prompt', '')[:50]}"


def _filter_excluded_records(traces: Dict[str, List[Dict[str, Any]]], excluded_records: Set[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Filter out records that have been flagged by higher-priority detectors"""
    filtered_traces = {}
    
    for trace_id, records in traces.items():
        filtered_records = []
        for record in records:
            record_id = _create_record_id(record, trace_id)
            if record_id not in excluded_records:
                filtered_records.append(record)
        
        if filtered_records:
            filtered_traces[trace_id] = filtered_records
    
    return filtered_traces


def _run_prioritized_detection(traces: Dict[str, List[Dict[str, Any]]], pricing_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run detectors in priority order with suppression logic"""
    
    # Get detection thresholds from config
    thresholds = pricing_config.get('thresholds', {})
    retry_config = thresholds.get('retry_loop', {})
    fallback_storm_config = thresholds.get('fallback_storm', {})
    fallback_failure_config = thresholds.get('fallback_failure', {})
    
    # Initialize detectors in priority order
    detectors = [
        RetryLoopDetector(
            max_retries=retry_config.get('max_retries', 1),
            time_window_minutes=retry_config.get('time_window_minutes', 5),
            max_retry_interval_minutes=retry_config.get('max_retry_interval_minutes', 2)
        ),
        FallbackFailureDetector(
            time_window_seconds=fallback_failure_config.get('time_window_seconds', 300)
        ),
        OverkillModelDetector(),
        FallbackStormDetector(
            min_calls=fallback_storm_config.get('fallback_threshold', 3),
            max_trace_window_minutes=fallback_storm_config.get('time_window_minutes', 10)
        )
    ]
    
    all_detections = []
    excluded_records = set()  # Track records that have been flagged by higher-priority detectors
    
    for i, detector in enumerate(detectors):
        detector_name = detector.__class__.__name__
        
        # Filter traces to exclude already flagged records
        filtered_traces = _filter_excluded_records(traces, excluded_records)
        
        # Run detector
        if hasattr(detector, 'detect') and 'model_pricing' in detector.detect.__code__.co_varnames:
            detections = detector.detect(filtered_traces, pricing_config.get('models', {}))
        else:
            detections = detector.detect(filtered_traces)
        
        # Add suppression notes and track excluded records
        for detection in detections:
            detection['suppression_notes'] = {
                'suppressed_detectors': [],
                'reason': None
            }
            
            # Add records to excluded set for lower-priority detectors
            for record in detection.get('records', []):
                record_id = _create_record_id(record, detection['trace_id'])
                excluded_records.add(record_id)
            
            # Add suppression notes based on detector priority
            if detector_name == 'RetryLoopDetector':
                detection['suppression_notes']['suppressed_detectors'] = ['OverkillModelDetector', 'FallbackFailureDetector']
                detection['suppression_notes']['reason'] = 'These records were already claimed by a higher-priority RetryLoop detection.'
            elif detector_name == 'FallbackFailureDetector':
                detection['suppression_notes']['suppressed_detectors'] = ['OverkillModelDetector']
                detection['suppression_notes']['reason'] = 'These records were already claimed by a higher-priority FallbackFailure detection.'
        
        all_detections.extend(detections)
    
    return all_detections


def _format_human_readable(detections: List[Dict[str, Any]], total_waste_cost: float) -> str:
    """Format detections for human-readable terminal output"""
    if not detections:
        return "✅ CrashLens Scan Complete. No issues found."
    
    output = []
    output.append(f"✅ CrashLens Scan Complete. {len(detections)} issues found.\n")
    
    for detection in detections:
        severity = detection.get('severity', 'medium').upper()
        detection_type = detection.get('type', 'unknown').replace('_', ' ').title()
        
        output.append(f"[ {severity} SEVERITY ] {detection_type}")
        
        if 'trace_id' in detection:
            output.append(f"  • Trace ID:          {detection['trace_id']}")
        
        output.append(f"  • Description:       {detection.get('description', 'N/A')}")
        
        if 'waste_cost' in detection:
            output.append(f"  • Potential Waste:   ${detection['waste_cost']:.6f}")
        
        # Add suppression notes if any
        suppression_notes = detection.get('suppression_notes', {})
        suppressed_detectors = suppression_notes.get('suppressed_detectors', [])
        if suppressed_detectors:
            output.append(f"  • Suppressed Alerts: {', '.join(suppressed_detectors)} (already part of a higher-priority detection)")
        
        output.append("")  # Empty line between detections
    
    return "\n".join(output)


@cli.command()
@click.argument('log_file', type=click.Path(exists=True, path_type=Path))
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['slack', 'markdown', 'json', 'human'], case_sensitive=False),
              default='slack', help='Output format')
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Path to custom pricing config file (uses built-in config by default)')
def scan(log_file: Path, output_format: str, config: Optional[Path]):
    """Scan JSONL log file for token waste patterns"""
    
    try:
        # Load pricing configuration (default to built-in config)
        pricing_config = {}
        config_path = config or Path(__file__).parent / "config" / "pricing.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                pricing_config = yaml.safe_load(f)
        except Exception as e:
            click.echo(f"⚠️  Warning: Could not load pricing config from {config_path}: {e}", err=True)
            click.echo("💡 Using default pricing for cost calculations...")
        
        # Initialize parser
        parser = LangfuseParser()
        traces = parser.parse_file(log_file)
        
        if not traces:
            click.echo("⚠️  No traces found in log file", err=True)
            sys.exit(1)
        
        # Run prioritized detection
        all_detections = _run_prioritized_detection(traces, pricing_config)
        
        # Calculate total waste cost
        total_waste_cost = sum(d.get('waste_cost', 0) for d in all_detections)
        
        # Output based on format
        if output_format == 'json':
            # Machine-readable JSON output
            json_output = []
            for detection in all_detections:
                json_detection = {
                    'type': detection.get('type'),
                    'severity': detection.get('severity'),
                    'description': detection.get('description'),
                    'waste_cost': f"{detection.get('waste_cost', 0):.6f}",
                    'suppression_notes': detection.get('suppression_notes', {})
                }
                if 'trace_id' in detection:
                    json_detection['trace_id'] = detection['trace_id']
                json_output.append(json_detection)
            
            click.echo(json.dumps(json_output, indent=2))
        elif output_format == 'human':
            # Human-readable terminal output
            output = _format_human_readable(all_detections, total_waste_cost)
            click.echo(output)
        else:
            # Default Slack/Markdown format
            if output_format == 'markdown':
                formatter = MarkdownFormatter()
            else:
                formatter = SlackFormatter()
            
            output = formatter.format(all_detections, traces)
            click.echo(output)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()