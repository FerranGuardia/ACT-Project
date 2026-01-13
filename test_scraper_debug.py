#!/usr/bin/env python
"""
Test the scraper directly to debug the content extraction issue.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from scraper.extractors.chapter_extractor import ChapterExtractor

def test_scraper():
    """Test the scraper directly."""
    extractor = ChapterExtractor(base_url="https://novelfull.net")

    url = "https://novelfull.net/i-alone-level-up/chapter-1.html"

    print(f"Testing scraper with URL: {url}")

    # Test _scrape_with_requests directly
    print("\n=== Testing _scrape_with_requests ===")
    content, title, error = extractor._scrape_with_requests(url, None)
    print(f"_scrape_with_requests result:")
    print(f"  Error: {error}")
    print(f"  Title: {title}")
    print(f"  Content length: {len(content) if content else 0}")

    if content:
        print(f"  Content preview: {content[:200]}...")
    else:
        print("  No content returned!")

    # Also test the full scrape method
    print("\n=== Testing full scrape method ===")
    content2, title2, error2 = extractor.scrape(url)
    print(f"Full scrape result:")
    print(f"  Error: {error2}")
    print(f"  Title: {title2}")
    print(f"  Content length: {len(content2) if content2 else 0}")

if __name__ == "__main__":
    test_scraper()