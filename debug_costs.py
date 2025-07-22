#!/usr/bin/env python3
import json

# Check demo data costs
total = 0
with open('examples/demo-logs.jsonl', 'r') as f:
    for line in f:
        if line.strip():
            record = json.loads(line)
            cost = record.get('cost', 0)
            total += cost
            print(f'{record.get("traceId")}: ${cost}')

print(f'Total calculated: ${total:.6f}')
