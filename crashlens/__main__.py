#!/usr/bin/env python3
"""
CrashLens CLI - Token Waste Detection Tool
Scans Langfuse-style JSONL logs for inefficient GPT API usage patterns.
"""

import click
import sys
from pathlib import Path
from typing import Optional

from .parsers.langfuse import LangfuseParser
from .detectors.retry_loops import RetryLoopDetector
from .detectors.short_model_detector import ShortModelDetector
from .detectors.fallback_storm import FallbackStormDetector
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
              help='Path to pricing config file')
def scan(log_file: Path, output_format: str, config: Optional[Path]):
    """Scan JSONL log file for token waste patterns"""
    
    try:
        # Initialize parser
        parser = LangfuseParser()
        traces = parser.parse_file(log_file)
        
        if not traces:
            click.echo("⚠️  No traces found in log file", err=True)
            sys.exit(1)
        
        # Initialize detectors
        detectors = [
            RetryLoopDetector(),
            ShortModelDetector(),
            FallbackStormDetector()
        ]
        
        # Run all detectors
        all_detections = []
        for detector in detectors:
            detections = detector.detect(traces)
            all_detections.extend(detections)
        
        # Format and output results
        if output_format == 'slack':
            formatter = SlackFormatter()
        else:
            formatter = MarkdownFormatter()
        
        output = formatter.format(all_detections, traces)
        click.echo(output)
        
        # Summary
        click.echo(f"\n📊 Found {len(all_detections)} waste patterns across {len(traces)} traces")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 