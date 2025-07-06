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
from .detectors.gpt4_short import GPT4ShortDetector
from .detectors.fallback_storm import FallbackStormDetector
from .reporters.slack_formatter import SlackFormatter
from .reporters.markdown_formatter import MarkdownFormatter


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


def scan_logs(logfile: Path, demo: bool = False, config_path: Optional[Path] = None) -> str:
    """
    🎯 Scan logs for token waste patterns
    
    Load JSONL lines → Group by trace_id → Run 3 hardcoded detectors → 
    Estimate cost → Output in Slack-style format
    """
    
    # Load pricing configuration
    pricing_config = load_pricing_config(config_path)
    
    # Initialize parser and load logs
    parser = LangfuseParser()
    traces = parser.parse_file(logfile)
    
    if not traces:
        return "⚠️  No traces found in log file"
    
    # Initialize detectors with config thresholds
    thresholds = pricing_config.get('thresholds', {})
    
    detectors = [
        RetryLoopDetector(
            max_retries=thresholds.get('retry_loop', {}).get('max_retries', 3),
            time_window_minutes=thresholds.get('retry_loop', {}).get('time_window_minutes', 5)
        ),
        GPT4ShortDetector(
            min_tokens_for_gpt4=thresholds.get('gpt4_short', {}).get('min_tokens_for_gpt4', 200),
            gpt4_cost_multiplier=thresholds.get('gpt4_short', {}).get('gpt4_cost_multiplier', 20.0)
        ),
        FallbackStormDetector(
            fallback_threshold=thresholds.get('fallback_storm', {}).get('fallback_threshold', 3),
            time_window_minutes=thresholds.get('fallback_storm', {}).get('time_window_minutes', 10)
        )
    ]
    
    # Run all detectors
    all_detections = []
    for detector in detectors:
        detections = detector.detect(traces)
        all_detections.extend(detections)
    
    # Estimate costs using pricing config
    if pricing_config.get('models'):
        for detection in all_detections:
            detection['estimated_cost'] = estimate_detection_cost(detection, pricing_config['models'])
    
    # Format output using Slack formatter
    formatter = SlackFormatter()
    output = formatter.format(all_detections, traces)
    
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
@click.argument('log_file', type=click.Path(exists=True, path_type=Path))
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['slack', 'markdown'], case_sensitive=False),
              default='slack', help='Output format')
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Path to pricing config file')
@click.option('--demo', is_flag=True, help='Run in demo mode with sample data')
def scan(log_file: Path, output_format: str, config: Optional[Path], demo: bool):
    """Scan JSONL log file for token waste patterns"""
    
    try:
        # Use the new scan_logs function
        output = scan_logs(log_file, demo=demo, config_path=config)
        click.echo(output)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 