#!/usr/bin/env python
"""
Debug selector priority issue.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from scraper.extractors.chapter_extractor import ChapterExtractor
from bs4 import BeautifulSoup
from unittest.mock import patch

# Debug selector priority
extractor = ChapterExtractor('https://example.com')

html = '''<html><body>
    <div class="chapter-c">This is the first content that should be extracted</div>
    <div class="content">This is the second content that should not be extracted</div>
    <article>This is the third content that should not be extracted</article>
</body></html>'''

soup = BeautifulSoup(html, 'html.parser')

# Test with first selector that should match
from scraper.config import CONTENT_SELECTORS
print('CONTENT_SELECTORS:', CONTENT_SELECTORS[:5])

mock_selectors = ["div.chapter-c", "div.content", "article"]
print('Mock selectors:', mock_selectors)

with patch('src.scraper.extractors.chapter_extractor.CONTENT_SELECTORS', mock_selectors):
    # Check if patching worked
    from src.scraper.extractors.chapter_extractor import CONTENT_SELECTORS as patched_selectors
    print('Patched selectors:', patched_selectors)

    # Test each selector individually
    for selector in mock_selectors:
        element = soup.select_one(selector)
        print(f'Selector "{selector}" found element:', element is not None)
        if element:
            print(f'  Element text: {repr(element.get_text(strip=True))}')

    content = extractor._extract_content(soup)
    print('Extracted content:', repr(content))