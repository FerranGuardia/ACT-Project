#!/usr/bin/env python
from pathlib import Path
import json

queue_file = Path.home() / '.act' / 'queue.json'
print(f'Queue file: {queue_file}')
print(f'Exists: {queue_file.exists()}')

if queue_file.exists():
    try:
        with open(queue_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f'Queue contains {len(data)} items:')
        for i, item in enumerate(data):
            title = item.get('title', 'No title')
            url = item.get('url', 'No URL')
            status = item.get('status', 'Unknown')
            progress = item.get('progress', 0)
            print(f'  {i+1}. {title}')
            print(f'     URL: {url}')
            print(f'     Status: {status}')
            print(f'     Progress: {progress}%')
            if 'black-tech-internet-cafe-system' in url.lower():
                print('     *** THIS IS THE NOVEL IN QUESTION ***')
            print()
    except Exception as e:
        print(f'Error reading queue file: {e}')
else:
    print('Queue file does not exist')