#!/usr/bin/env python3
from crashlens.parsers.langfuse import LangfuseParser
from pathlib import Path

parser = LangfuseParser()
demo_file = Path('examples/demo-logs.jsonl')
traces = parser.parse_file(demo_file)

print(f'Traces found: {len(traces)}')
total_cost = 0

for trace_id, records in traces.items():
    trace_cost = 0
    print(f'\nTrace {trace_id}: {len(records)} records')
    for i, record in enumerate(records):
        cost = record.get('cost', 0)
        print(f'  Record {i}: cost={cost}, keys={list(record.keys())[:5]}...')
        trace_cost += cost
        total_cost += cost
    print(f'  Trace total: ${trace_cost:.6f}')

print(f'\nGrand total: ${total_cost:.6f}')
