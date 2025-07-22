#!/usr/bin/env python3
"""
CrashLens CLI - Token Waste Detection Tool
Scans Langfuse-style JSONL logs for inefficient GPT API usage patterns.
"""

import click
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, List, Any

from .parsers.langfuse import LangfuseParser
from .detectors.retry_loops import RetryLoopDetector
from .detectors.fallback_storm import FallbackStormDetector
from .detectors.fallback_failure import FallbackFailureDetector
from .detectors.overkill_model_detector import detect_expensive_model_waste
from .reporters.slack_formatter import SlackFormatter
from .reporters.markdown_formatter import MarkdownFormatter
from .reporters.summary_formatter import SummaryFormatter


def load_pricing_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load pricing configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "pricing.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        click.echo(f"⚠️  Warning: Could not load pricing config: {e}", err=True)
        return {}


def scan_logs(logfile: Optional[Path] = None, demo: bool = False, config_path: Optional[Path] = None, 
              stdin: bool = False, paste: bool = False, summary: bool = False, output_format: str = 'slack', summary_only: bool = False, dry_run_policy: bool = False) -> str:
    """
    🎯 Scan logs for token waste patterns
    
    Load JSONL lines → Group by trace_id → Run 3 hardcoded detectors → 
    Estimate cost → Output in Slack-style format
    """
    
    # Load pricing configuration
    pricing_config = load_pricing_config(config_path)
    
    # Initialize parser and load logs
    parser = LangfuseParser()
    
    if stdin:
        traces = parser.parse_stdin()
    elif paste:
        import pyperclip
        try:
            text = pyperclip.paste()
            traces = parser.parse_string(text)
        except Exception as e:
            return f"❌ Error reading from clipboard: {e}"
    elif logfile:
        traces = parser.parse_file(logfile)
    else:
        return "❌ Error: No input source specified"
    
    if not traces:
        return "⚠️  No traces found in input"
    
    # Initialize detectors with config thresholds
    thresholds = pricing_config.get('thresholds', {})

    fallback_detector = FallbackFailureDetector(
        time_window_seconds=thresholds.get('fallback_failure', {}).get('time_window_seconds', 300)
    )
    # overkill_detector = detect_expensive_model_waste
    # Other detectors can be added here as needed

    # Run fallback failure detector first
    fallback_detections = fallback_detector.detect(traces, pricing_config.get('models', {}))
    # Add waste_cost and waste_tokens to fallback detections
    for det in fallback_detections:
        waste_tokens = 0
        waste_cost = 0.0
        for rec in det.get('records', []):
            waste_tokens += rec.get('completion_tokens', 0)
            model = rec.get('model', 'gpt-3.5-turbo')
            input_tokens = rec.get('prompt_tokens', 0)
            output_tokens = rec.get('completion_tokens', 0)
            model_config = pricing_config.get('models', {}).get(model, {})
            if model_config:
                input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
                output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
                waste_cost += input_cost + output_cost
        det['waste_tokens'] = waste_tokens
        det['waste_cost'] = waste_cost

    fallback_trace_ids = {d['trace_id'] for d in fallback_detections}

    # Run overkill detector only on traces without fallback failures
    traces_without_fallback = {tid: recs for tid, recs in traces.items() if tid not in fallback_trace_ids}
    overkill_detections = detect_expensive_model_waste(
        traces_without_fallback,
        model_pricing=pricing_config.get('models', {})
    )

    # Run other detectors as before (if needed)
    detectors = [
        RetryLoopDetector(
            max_retries=thresholds.get('retry_loop', {}).get('max_retries', 3),
            time_window_minutes=thresholds.get('retry_loop', {}).get('time_window_minutes', 5),
            max_retry_interval_minutes=thresholds.get('retry_loop', {}).get('max_retry_interval_minutes', 2)
        ),
        FallbackStormDetector(
            fallback_threshold=thresholds.get('fallback_storm', {}).get('fallback_threshold', 3),
            time_window_minutes=thresholds.get('fallback_storm', {}).get('time_window_minutes', 10)
        )
    ]

    all_detections = []
    detector_results = []
    already_flagged_ids = set()
    
    # Add other detectors first to build flagged IDs
    for detector in detectors:
        if hasattr(detector, 'detect') and 'model_pricing' in detector.detect.__code__.co_varnames:
            detections = detector.detect(traces, pricing_config.get('models', {}))
        else:
            detections = detector.detect(traces)
        
        # Track flagged trace IDs
        for detection in detections:
            already_flagged_ids.add(detection.get('trace_id'))
        
        all_detections.extend(detections)
        detector_results.append((detector.__class__.__name__, detections))
    
    # Run fallback failure detector with suppression
    fallback_detections = fallback_detector.detect(traces, pricing_config.get('models', {}), already_flagged_ids)
    # Add prioritized detectors
    all_detections.extend(fallback_detections)
    detector_results.append(("FallbackFailureDetector", fallback_detections))
    all_detections.extend(overkill_detections)
    detector_results.append(("OverkillModelDetector", overkill_detections))

    # Handle dry-run-policy mode
    if dry_run_policy:
        dry_run_lines = []
        any_triggered = False
        for rule_name, detections in detector_results:
            if detections:
                dry_run_lines.append(f"[DRY RUN] Detected: {rule_name.replace('Detector','').replace('_',' ')} ({len(detections)} matches)")
                any_triggered = True
            else:
                dry_run_lines.append(f"[DRY RUN] No {rule_name.replace('Detector','').replace('_',' ')} detected")
        if not any_triggered:
            return "[DRY RUN] No detection rules would trigger on this data."
        return "\n".join(dry_run_lines)
    
    # Handle summary mode
    if summary:
        formatter = SummaryFormatter()
        output = formatter.format(traces, pricing_config.get('models', {}), summary_only=summary_only)
        return output
    
    # Estimate costs using pricing config
    if pricing_config.get('models'):
        for detection in all_detections:
            detection['estimated_cost'] = estimate_detection_cost(detection, pricing_config['models'])
    
    # Format output using selected formatter
    if output_format == 'markdown':
        formatter = MarkdownFormatter()
    else:
        formatter = SlackFormatter()
    output = formatter.format(all_detections, traces, summary_only=summary_only)
    
    return output


def estimate_detection_cost(detection: Dict[str, Any], model_pricing: Dict[str, Any]) -> float:
    """Estimate cost for a detection based on model pricing"""
    total_cost = 0.0
    
    for record in detection.get('records', []):
        model = record.get('model', 'gpt-3.5-turbo')
        input_tokens = record.get('prompt_tokens', 0)
        output_tokens = record.get('completion_tokens', 0)
        
        # Find model pricing
        model_config = model_pricing.get(model, {})
        if model_config:
            input_cost = (input_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
            output_cost = (output_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
            total_cost += input_cost + output_cost
    
    return total_cost


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """CrashLens - Detect token waste in GPT API logs"""
    pass


@cli.command()
@click.argument('log_file', type=click.Path(exists=True, path_type=Path), required=False)
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['slack', 'markdown'], case_sensitive=False),
              default='slack', help='Output format')
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Path to pricing config file')
@click.option('--demo', is_flag=True, help='Run in demo mode with sample data')
@click.option('--stdin', is_flag=True, help='Read logs from stdin')
@click.option('--paste', is_flag=True, help='Read logs from clipboard')
@click.option('--summary', is_flag=True, help='Show cost summary by route, model, and team')
@click.option('--summary-only', is_flag=True, help='Suppress prompts, sample inputs, and trace IDs for safe internal reports')
@click.option('--output', type=click.Path(writable=True, path_type=Path), help='Save report to a file instead of printing to stdout')
@click.option('--dry-run-policy', is_flag=True, help='Show which detection rules would trigger, without blocking or exiting')
def scan(log_file: Optional[Path], output_format: str, config: Optional[Path], demo: bool, stdin: bool, paste: bool, summary: bool, summary_only: bool, dry_run_policy: bool, output: Optional[Path]):
    """Scan JSONL log file for token waste patterns"""
    
    # Check for conflicts
    if (stdin or paste) and log_file:
        raise click.UsageError("Cannot use file input with --stdin or --paste.")
    
    if stdin and paste:
        raise click.UsageError("Cannot use both --stdin and --paste.")
    
    if not log_file and not stdin and not paste:
        raise click.UsageError("Must specify either a log file, --stdin, or --paste.")
    
    try:
        # Use the new scan_logs function
        output_text = scan_logs(logfile=log_file, demo=demo, config_path=config, stdin=stdin, paste=paste, summary=summary, output_format=output_format, summary_only=summary_only, dry_run_policy=dry_run_policy)
        if output:
            output.write_text(output_text, encoding='utf-8')
            click.echo(f"Report saved to {output}")
        else:
            click.echo(output_text)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 