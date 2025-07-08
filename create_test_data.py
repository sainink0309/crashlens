#!/usr/bin/env python3
"""Generate large test data for performance testing"""

import json
import random
from pathlib import Path

def create_large_test_file():
    models = ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
    prompts = ['What is 2+2?', 'Summarize this', 'Fix this code', 'Generate a report', 'Translate this']
    
    with open('examples/large-test.jsonl', 'w') as f:
        for i in range(10000):
            log_entry = {
                'trace_id': f'trace_{i:06d}',
                'timestamp': '2024-01-15T10:00:00Z',
                'model': random.choice(models),
                'prompt': random.choice(prompts),
                'completion_tokens': random.randint(10, 500),
                'cost': random.uniform(0.001, 0.1),
                'status': 'success'
            }
            f.write(json.dumps(log_entry) + '\n')
    
    print('Created 10,000 log entries in examples/large-test.jsonl')

if __name__ == '__main__':
    create_large_test_file() 