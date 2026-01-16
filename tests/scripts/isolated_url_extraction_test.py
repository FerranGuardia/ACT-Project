#!/usr/bin/env python3
"""
Isolated URL extraction testing script.

This script tests the chapter URL extraction pipeline for a given novel TOC URL.
It uses the ScrapeService to extract all chapter URLs and saves them to a text file.

Usage:
    python tests/scripts/isolated_url_extraction_test.py <toc_url> [output_file]

Example:
    python tests/scripts/isolated_url_extraction_test.py https://novelfull.net/black-tech-internet-cafe-system.html
"""

import sys
import os
from pathlib import Path
from typing import List, Optional
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.logger import get_logger, ACTLogger
from services.scrape_service import ScrapeService
from utils.validation import validate_url

logger = get_logger("isolated_url_test")


class IsolatedUrlExtractionTester:
    """Isolated tester for URL extraction pipeline."""

    def __init__(self):
        self.scrape_service = ScrapeService()
        self.logger = get_logger("isolated_tester")

    def test_url_extraction(self, toc_url: str, output_file: Optional[str] = None) -> bool:
        """
        Test chapter URL extraction for a given TOC URL.

        Args:
            toc_url: URL of the table of contents page
            output_file: Optional output file path for chapter URLs

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting isolated URL extraction test for: {toc_url}")

            # Validate URL first
            is_valid, clean_url = validate_url(toc_url)
            if not is_valid:
                self.logger.error(f"Invalid URL: {clean_url}")
                return False

            toc_url = clean_url
            self.logger.info(f"Validated URL: {toc_url}")

            # Extract chapter URLs
            self.logger.info("Extracting chapter URLs...")
            chapter_urls = self.scrape_service.get_chapter_urls(toc_url)

            if not chapter_urls:
                self.logger.error("No chapter URLs extracted!")
                return False

            self.logger.info(f"Successfully extracted {len(chapter_urls)} chapter URLs")

            # Print summary
            print(f"\n=== URL EXTRACTION RESULTS ===")
            print(f"TOC URL: {toc_url}")
            print(f"Total chapters found: {len(chapter_urls)}")
            print(f"First 5 URLs:")
            for i, url in enumerate(chapter_urls[:5], 1):
                print(f"  {i}. {url}")
            if len(chapter_urls) > 5:
                print(f"  ... and {len(chapter_urls) - 5} more")
            print(f"Last 3 URLs:")
            for i, url in enumerate(chapter_urls[-3:], len(chapter_urls)-2):
                print(f"  {i}. {url}")

            # Save to file if requested
            if output_file:
                self._save_urls_to_file(chapter_urls, output_file)
            else:
                # Default filename based on URL
                default_filename = self._generate_default_filename(toc_url)
                self._save_urls_to_file(chapter_urls, default_filename)

            return True

        except Exception as e:
            self.logger.exception(f"Error during URL extraction test: {e}")
            print(f"\nERROR: {e}")
            return False

    def _save_urls_to_file(self, urls: List[str], filename: str) -> None:
        """Save chapter URLs to a text file."""
        try:
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Chapter URLs extracted from TOC\n")
                f.write(f"# Total chapters: {len(urls)}\n")
                f.write("# \n")
                for i, url in enumerate(urls, 1):
                    f.write(f"{i:4d}. {url}\n")

            self.logger.info(f"Saved {len(urls)} chapter URLs to: {output_path}")
            print(f"\n[SUCCESS] Saved chapter URLs to: {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to save URLs to file: {e}")
            print(f"\n[ERROR] Failed to save URLs to file: {e}")

    def _generate_default_filename(self, toc_url: str) -> str:
        """Generate a default filename based on the TOC URL."""
        # Extract novel name from URL
        from urllib.parse import urlparse
        parsed = urlparse(toc_url)
        path_parts = parsed.path.strip('/').split('/')

        if path_parts:
            novel_name = path_parts[-1].replace('.html', '').replace('-', '_')
        else:
            novel_name = "unknown_novel"

        return f"isolated_test_output/{novel_name}_chapter_urls.txt"


def main():
    """Main entry point for isolated testing."""
    if len(sys.argv) < 2:
        print("Usage: python isolated_url_extraction_test.py <toc_url> [output_file]")
        print("\nExample:")
        print("  python isolated_url_extraction_test.py https://novelfull.net/black-tech-internet-cafe-system.html")
        print("  python isolated_url_extraction_test.py https://novelfull.net/black-tech-internet-cafe-system.html custom_output.txt")
        return 1

    toc_url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Initialize logger
    _ = ACTLogger()

    # Create tester and run test
    tester = IsolatedUrlExtractionTester()
    success = tester.test_url_extraction(toc_url, output_file)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())