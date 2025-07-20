#!/usr/bin/env python3
"""
CrashLens CLI - Token Waste Detection Tool
Scans Langfuse-style JSONL logs for inefficient GPT API usage patterns.
"""

import click
import sys
import yaml
from pathlib import Path
from typing import Optional

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


@cli.command()
@click.argument('log_file', type=click.Path(exists=True, path_type=Path))
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['slack', 'markdown'], case_sensitive=False),
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
        
        # Get detection thresholds from config
        thresholds = pricing_config.get('thresholds', {})
        retry_config = thresholds.get('retry_loop', {})
        fallback_storm_config = thresholds.get('fallback_storm', {})
        fallback_failure_config = thresholds.get('fallback_failure', {})
        
        # Initialize detectors with config thresholds
        detectors = [
            RetryLoopDetector(
                max_retries=retry_config.get('max_retries', 2),
                time_window_minutes=retry_config.get('time_window_minutes', 5),
                similarity_threshold=retry_config.get('similarity_threshold', 0.6)
            ),
            OverkillModelDetector(),
            FallbackStormDetector(
                fallback_threshold=fallback_storm_config.get('fallback_threshold', 3),
                time_window_minutes=fallback_storm_config.get('time_window_minutes', 10)
            ),
            FallbackFailureDetector(
                time_window_seconds=fallback_failure_config.get('time_window_seconds', 15),
                similarity_threshold=fallback_failure_config.get('similarity_threshold', 0.8)
            )
        ]
        
        # Run all detectors
        all_detections = []
        for detector in detectors:
            if hasattr(detector, 'detect') and 'model_pricing' in detector.detect.__code__.co_varnames:
                detections = detector.detect(traces, pricing_config.get('models', {}))
            else:
                detections = detector.detect(traces)
            all_detections.extend(detections)
        
        # Calculate total AI spend
        total_ai_spend = 0.0
        total_tokens = 0
        model_usage = {}
        
        for trace_id, records in traces.items():
            for record in records:
                model = record.get('input.model', 'unknown')
                prompt_tokens = record.get('usage.prompt_tokens', 0)
                completion_tokens = record.get('usage.completion_tokens', 0)
                
                # Track model usage
                if model not in model_usage:
                    model_usage[model] = {'calls': 0, 'tokens': 0, 'cost': 0.0}
                model_usage[model]['calls'] += 1
                model_usage[model]['tokens'] += prompt_tokens + completion_tokens
                
                # Calculate cost if pricing is available
                if pricing_config.get('models') and model in pricing_config['models']:
                    model_config = pricing_config['models'][model]
                    input_cost = (prompt_tokens / 1000) * model_config.get('input_cost_per_1k', 0)
                    output_cost = (completion_tokens / 1000) * model_config.get('output_cost_per_1k', 0)
                    cost = input_cost + output_cost
                    model_usage[model]['cost'] += cost
                    total_ai_spend += cost
                
                total_tokens += prompt_tokens + completion_tokens
        
        # Calculate total waste cost
        total_waste_cost = sum(d.get('waste_cost', 0) for d in all_detections)
        
        # Format and output results
        if output_format == 'slack':
            formatter = SlackFormatter()
        else:
            formatter = MarkdownFormatter()
        
        output = formatter.format(all_detections, traces)
        
        # Add detailed cost breakdown
        cost_breakdown = []
        cost_breakdown.append("")
        cost_breakdown.append("💰 **Cost Breakdown**")
        cost_breakdown.append("=" * 30)
        cost_breakdown.append(f"🧾 **Total AI Spend**: ${total_ai_spend:.4f}")
        cost_breakdown.append(f"🎯 **Total Tokens**: {total_tokens:,}")
        cost_breakdown.append(f"📊 **Total Traces**: {len(traces)}")
        cost_breakdown.append("")
        
        if model_usage:
            cost_breakdown.append("🤖 **Model Usage**:")
            for model, stats in model_usage.items():
                cost_breakdown.append(f"  • {model}: {stats['calls']} calls, {stats['tokens']:,} tokens, ${stats['cost']:.4f}")
            cost_breakdown.append("")
        
        if total_waste_cost > 0:
            cost_breakdown.append(f"💸 **Total Waste**: ${total_waste_cost:.4f}")
            if total_ai_spend > 0:
                waste_percentage = (total_waste_cost / total_ai_spend) * 100
                cost_breakdown.append(f"📈 **Waste Percentage**: {waste_percentage:.1f}%")
        
        output += "\n".join(cost_breakdown)
        click.echo(output)
        
        # Summary
        click.echo(f"\n📊 Found {len(all_detections)} waste patterns across {len(traces)} traces")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 