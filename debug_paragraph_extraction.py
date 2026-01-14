#!/usr/bin/env python
"""
Debug paragraph extraction logic.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from bs4 import BeautifulSoup

html = '''<html><body>
    <div class="chapter-c">This is the first content that should be extracted</div>
</body></html>'''

soup = BeautifulSoup(html, 'html.parser')
content_elem = soup.select_one('div.chapter-c')

print('Content element:', content_elem)
print('Content element text:', repr(content_elem.get_text(strip=True)))
print('Content element text length:', len(content_elem.get_text(strip=True)))

# Check paragraphs
paragraphs = content_elem.find_all('p', recursive=True)
print('Paragraphs found:', len(paragraphs))

# Check divs without p
all_divs = content_elem.find_all('div', recursive=True)
print('All divs found:', len(all_divs))
divs_without_p = []
for div in all_divs:
    if not div.find('p'):
        divs_without_p.append(div)

print('Divs without p found:', len(divs_without_p))
for div in divs_without_p:
    text = div.get_text(strip=True)
    print(f'  Div text: {repr(text)}, length: {len(text)}')

# Simulate the extraction logic
all_elements = paragraphs + divs_without_p
print('All elements to process:', len(all_elements))

text_parts = []
seen_text = set()

for elem in all_elements:
    text_raw = elem.get_text(strip=True)
    text = str(text_raw) if text_raw is not None else ""
    print(f'Processing element: {elem.name}, text: {repr(text)}, length: {len(text)}')

    if text and len(text) > 20:
        print(f'  Text passes length filter (>20)')
        text_parts.append(text)
    else:
        print(f'  Text FAILS length filter (>20)')

print('Final text_parts:', text_parts)