#!/usr/bin/env python
"""
Inspect NovelFull chapter page structure to understand why content extraction is failing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import requests
from bs4 import BeautifulSoup
from core.logger import get_logger

logger = get_logger("inspect_novelfull")

def inspect_chapter_page():
    """Inspect a NovelFull chapter page to understand its structure."""
    url = "https://novelfull.net/i-alone-level-up/chapter-1.html"

    logger.info(f"Inspecting chapter page: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for potential content containers
        print("=== POTENTIAL CONTENT CONTAINERS ===")

        # Check for common selectors
        selectors_to_check = [
            "div.cha-words",
            "div.cha-content",
            "div.chapter-c",
            "div#chapter-c",
            "div.text-left",
            "div#text-chapter",
            "div.chapter-content-wrapper",
            "div.chapter-content",
            "div#chapter-content",
            "div.chapter-body",
            "div#chapter-body",
            "div.content",
            "div#content",
            "div.text-content",
            "article",
            "div.read-content",
            "div.chapter-text",
            "div#novel-content",
            "div.novel-content",
            "div.entry-content",
            "div.post-content",
            "div.story-content",
            "div#story-content",
            "div.chapter-inner",
            "div.reading-content",
            "div#reading-content",
            "div.text",
            "div#text",
            "div.chap-content",
            "div#chap-content"
        ]

        found_selectors = []
        for selector in selectors_to_check:
            elements = soup.select(selector)
            if elements:
                print(f"[FOUND] Found {len(elements)} elements with selector: {selector}")
                for i, elem in enumerate(elements[:3]):  # Show first 3
                    text_length = len(elem.get_text(strip=True))
                    print(f"  Element {i+1}: {text_length} chars of text")
                    if text_length > 100:
                        print(f"    Preview: {elem.get_text(strip=True)[:200]}...")
                found_selectors.append(selector)

        print("\n=== DIV ELEMENTS WITH CLASSES ===")
        divs_with_classes = soup.find_all('div', class_=True)
        for div in divs_with_classes[:20]:  # Show first 20
            classes = div.get('class', [])
            text_length = len(div.get_text(strip=True))
            if text_length > 500:  # Only show substantial content
                print(f"div.{'.'.join(classes)}: {text_length} chars")

        print("\n=== ARTICLES AND MAIN CONTENT ===")
        articles = soup.find_all('article')
        print(f"Found {len(articles)} <article> tags")

        mains = soup.find_all('main')
        print(f"Found {len(mains)} <main> tags")

        # Look for divs with specific class patterns
        print("\n=== DIVS WITH CONTENT-RELATED CLASSES ===")
        content_divs = soup.find_all('div', class_=lambda x: x and any(word in x.lower() for word in ['content', 'chapter', 'text', 'read', 'story']))
        for div in content_divs[:10]:
            classes = div.get('class', [])
            text_length = len(div.get_text(strip=True))
            print(f"div.{'.'.join(classes)}: {text_length} chars")

        # Check the title
        print("\n=== TITLE CHECK ===")
        title_elem = soup.find('title')
        if title_elem:
            print(f"Page title: {title_elem.get_text()}")

        h1s = soup.find_all('h1')
        print(f"Found {len(h1s)} H1 tags:")
        for h1 in h1s:
            print(f"  H1: {h1.get_text(strip=True)}")

    except Exception as e:
        logger.error(f"Error inspecting page: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_chapter_page()