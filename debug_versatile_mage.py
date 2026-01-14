#!/usr/bin/env python
"""
Debug Versatile Mage HTML structure to understand why content selectors don't work.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from scraper.extractors.chapter_extractor import ChapterExtractor
from bs4 import BeautifulSoup

def debug_versatile_mage():
    """Debug the Versatile Mage page structure."""
    extractor = ChapterExtractor("https://novelfull.net")

    # Use the same URL as in the test
    chapter_url = "https://novelfull.net/versatile-mage/chapter-1.html"

    print(f"Fetching: {chapter_url}")

    # Get the raw HTML
    content, title, error = extractor.scrape(chapter_url)

    if error:
        print(f"Error: {error}")
        return

    print(f"Title: {title}")
    print(f"Content length: {len(content) if content else 0}")
    print(f"Content: {repr(content)}")

    # Now let's examine the HTML structure by making a direct request
    import requests

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(chapter_url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')

        print("\n=== HTML Structure Analysis ===")

        # Check if the expected selectors exist
        from scraper.config import CONTENT_SELECTORS

        print(f"Checking CONTENT_SELECTORS: {CONTENT_SELECTORS[:5]}...")

        for selector in CONTENT_SELECTORS:
            elements = soup.select(selector)
            if elements:
                print(f"[FOUND] Selector '{selector}' found {len(elements)} elements")
                for i, elem in enumerate(elements[:2]):  # Show first 2
                    text = elem.get_text(strip=True)
                    print(f"  Element {i+1}: {len(text)} chars - {text[:100]}{'...' if len(text) > 100 else ''}")
            else:
                print(f"[MISSING] Selector '{selector}' found 0 elements")

        # Check for common content patterns
        print("\n=== Common content patterns ===")

        # Look for divs with class containing 'chapter'
        chapter_divs = soup.find_all('div', class_=lambda x: x and 'chapter' in x.lower())
        print(f"Divs with 'chapter' in class: {len(chapter_divs)}")
        for div in chapter_divs[:3]:
            text = div.get_text(strip=True)
            print(f"  {div.get('class')}: {len(text)} chars - {text[:80]}{'...' if len(text) > 80 else ''}")

        # Look for divs with class containing 'content'
        content_divs = soup.find_all('div', class_=lambda x: x and 'content' in x.lower())
        print(f"Divs with 'content' in class: {len(content_divs)}")
        for div in content_divs[:3]:
            text = div.get_text(strip=True)
            print(f"  {div.get('class')}: {len(text)} chars - {text[:80]}{'...' if len(text) > 80 else ''}")

        # Look for article tags
        articles = soup.find_all('article')
        print(f"Article tags: {len(articles)}")
        for article in articles[:2]:
            text = article.get_text(strip=True)
            print(f"  Article: {len(text)} chars - {text[:80]}{'...' if len(text) > 80 else ''}")

    except Exception as e:
        print(f"Error fetching HTML: {e}")

if __name__ == "__main__":
    debug_versatile_mage()