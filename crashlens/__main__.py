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
from .reporters.summary_formatter import SummaryFormatter


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
@click.argument('log_file', type=click.Path(exists=True, path_type=Path), required=False)
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['slack', 'markdown', 'json', 'human'], case_sensitive=False),
              default='slack', help='Output format')
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Path to custom pricing config file (uses built-in config by default)')
@click.option('--demo', is_flag=True, help='🎬 Run analysis on built-in demo data (no file required)')
@click.option('--stdin', is_flag=True, help='📥 Read JSONL data from standard input')
@click.option('--paste', is_flag=True, help='📋 Interactive mode: paste JSONL data directly')
@click.option('--summary', is_flag=True, help='📊 Show cost summary with model and route breakdown')
@click.option('--summary-only', is_flag=True, help='📋 Summary without trace IDs (safe for sharing)')
def scan(log_file: Optional[Path], output_format: str, config: Optional[Path], demo: bool, stdin: bool, 
         paste: bool, summary: bool, summary_only: bool):
    """Scan JSONL log file for token waste patterns
    
    Examples:
      crashlens scan logs.jsonl              # Scan a specific file
      crashlens scan --demo                  # Use built-in demo data
      cat logs.jsonl | crashlens scan --stdin  # Read from pipe
      crashlens scan --paste                 # Interactive paste mode
    """
    
    # Validate input options
    input_count = sum([bool(log_file), demo, stdin, paste])
    if input_count == 0:
        click.echo("❌ Error: Must specify input source: file path, --demo, --stdin, or --paste")
        click.echo("💡 Try: crashlens scan --help")
        sys.exit(1)
    elif input_count > 1:
        click.echo("❌ Error: Cannot use multiple input sources simultaneously")
        click.echo("💡 Choose one: file path, --demo, --stdin, or --paste")
        sys.exit(1)
    
    # Validate summary options
    if summary and summary_only:
        click.echo("❌ Error: Cannot use --summary and --summary-only together")
        click.echo("💡 Choose one: --summary OR --summary-only")
        sys.exit(1)
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
        
        # Initialize parser and handle different input sources
        parser = LangfuseParser()
        traces = {}
        
        try:
            if demo:
                # Use built-in demo data
                demo_file = Path(__file__).parent.parent / "examples" / "demo-logs.jsonl"
                if not demo_file.exists():
                    click.echo("❌ Error: Demo file not found. Please check installation.")
                    sys.exit(1)
                click.echo("🎬 Running analysis on built-in demo data...")
                traces = parser.parse_file(demo_file)
            
            elif stdin:
                # Read from standard input
                click.echo("📥 Reading JSONL data from standard input...")
                try:
                    traces = parser.parse_stdin()
                except KeyboardInterrupt:
                    click.echo("\n⚠️  Input cancelled by user")
                    sys.exit(1)
            
            elif paste:
                # Interactive paste mode
                click.echo("Interactive paste mode - Enter JSONL data")
                click.echo("Paste your JSONL lines below, then press Ctrl+D (Unix) or Ctrl+Z+Enter (Windows) when done:")
                click.echo("---")
                try:
                    lines = []
                    while True:
                        try:
                            line = input()
                            if line.strip():  # Only add non-empty lines
                                lines.append(line)
                        except EOFError:
                            # User pressed Ctrl+D or Ctrl+Z+Enter
                            break
                        except KeyboardInterrupt:
                            click.echo("\nInput cancelled by user")
                            sys.exit(1)
                    
                    if not lines:
                        click.echo("No data provided")
                        sys.exit(1)
                    
                    click.echo(f"Processing {len(lines)} lines...")
                    # Join lines and parse as string
                    jsonl_text = '\n'.join(lines)
                    traces = parser.parse_string(jsonl_text)
                    
                except Exception as e:
                    click.echo(f"Error processing pasted data: {e}", err=True)
                    sys.exit(1)
            
            elif log_file:
                # Read from specified file
                traces = parser.parse_file(log_file)
            
        except Exception as e:
            click.echo(f"❌ Error reading input: {e}", err=True)
            sys.exit(1)
        
        if not traces:
            source = "demo data" if demo else "standard input" if stdin else "pasted data" if paste else "log file"
            click.echo(f"⚠️  No traces found in {source}", err=True)
            sys.exit(1)
        
        # Run prioritized detection
        all_detections = _run_prioritized_detection(traces, pricing_config)
        
        # Calculate total waste cost
        total_waste_cost = sum(d.get('waste_cost', 0) for d in all_detections)
        
        # Handle summary modes
        if summary or summary_only:
            # Use SummaryFormatter for cost breakdown
            summary_formatter = SummaryFormatter()
            output = summary_formatter.format(traces, pricing_config.get('models', {}), summary_only)
            
            # Add detection summary if we have detections
            if all_detections:
                output += "\n\n🚨 **Waste Detection Summary**\n"
                output += f"📊 **Issues Found**: {len(all_detections)}\n"
                output += f"💰 **Total Potential Savings**: ${total_waste_cost:.6f}\n"
                
                # Group detections by type
                detections_by_type = {}
                for detection in all_detections:
                    detector_type = detection.get('type', 'unknown')
                    if detector_type not in detections_by_type:
                        detections_by_type[detector_type] = []
                    detections_by_type[detector_type].append(detection)
                
                # Show detection breakdown
                for detector_type, detections in detections_by_type.items():
                    display_name = detector_type.replace('_', ' ').title()
                    waste_cost = sum(d.get('waste_cost', 0) for d in detections)
                    output += f"  • {display_name}: {len(detections)} issues, ${waste_cost:.6f} potential savings\n"
            
            click.echo(output)
            return
        
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
            
            output = formatter.format(all_detections, traces, pricing_config.get('models', {}))
            click.echo(output)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()