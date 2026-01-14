#!/usr/bin/env python
"""
Debug content extraction to understand test failures.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from scraper.extractors.chapter_extractor import ChapterExtractor
from bs4 import BeautifulSoup

def debug_paragraph_extraction():
    """Debug the paragraph extraction logic."""
    extractor = ChapterExtractor('https://example.com')

    html = '''
    <div class="chapter-c">
        <p>Paragraph 1 content</p>
        <div class="text-block">Div content without p tag</div>
        <div class="wrapper">
            <p>Paragraph 2 content</p>
            <span>Span content</span>
        </div>
        <div class="empty-div"></div>
    </div>
    '''

    soup = BeautifulSoup(html, 'html.parser')
    content = extractor._extract_content(soup)

    print('HTML:')
    print(html)
    print('Extracted content:')
    print(repr(content))
    print('Content length:', len(content) if content else 0)

def debug_selector_priority():
    """Debug selector priority."""
    extractor = ChapterExtractor('https://example.com')

    html = '''
    <html><body>
        <div class="chapter-c">First content</div>
        <div class="content">Second content</div>
        <article>Third content</article>
    </body></html>
    '''

    soup = BeautifulSoup(html, 'html.parser')

    # Test with first selector that should match
    from scraper.config import CONTENT_SELECTORS
    print('CONTENT_SELECTORS:', CONTENT_SELECTORS[:5])  # First 5 selectors

    content = extractor._extract_content(soup)
    print('Extracted content:', repr(content))

if __name__ == "__main__":
    print("=== Debugging paragraph extraction ===")
    debug_paragraph_extraction()

    print("\n=== Debugging selector priority ===")
    debug_selector_priority()