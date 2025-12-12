# Block 2: Scraper Module

**Status**: **COMPLETE** (with ongoing improvements)  
**Last Updated**: 2025-12-12  
**Location**: `src/scraper/`

---

## Overview

Web scraping module for extracting novel content from various webnovel sites. Supports multiple scraping strategies with automatic fallback.

---

## Components

### Core Classes

1. **`GenericScraper`** (`generic_scraper.py`)
   - Main scraper class for general use
   - Works with most webnovel sites without site-specific code
   - Combines URL fetching + content scraping

2. **`BaseScraper`** (`base_scraper.py`)
   - Abstract base class for all scrapers
   - Common functionality and interface

3. **`NovelBinScraper`** (`novelbin_scraper.py`)
   - Site-specific scraper for NovelBin
   - Inherits from BaseScraper

4. **`ChapterUrlFetcher`** (`url_fetcher.py`)
   - Fetches chapter URLs using multiple strategies:
     1. JavaScript variable extraction (fastest)
     2. AJAX endpoint discovery (fast)
     3. HTML parsing (medium)
     4. Playwright with scrolling (slow but complete) ⭐ **IMPROVED**
     5. Follow "next" links (slow but reliable)
   - Failsafe fallback strategy
   - **Recent Improvements** (2025-01-27):
     -  Retry logic with exponential backoff for transient errors
     -  Rate limiting between requests (reduces blocking risk)
     -  Network idle waiting (replaces fixed delays, more reliable)
     -  Progress tracking for pagination visits
     -  Enhanced Cloudflare challenge handling

5. **`ContentScraper`** (`content_scraper.py`)
   - Scrapes chapter content and titles
   - Multiple selector patterns (failsafe)
   - Handles different site structures

### Utilities

- **`chapter_parser.py`**: Chapter number extraction, URL normalization, sorting
- **`text_cleaner.py`**: Text cleaning utilities, removes UI elements
- **`config.py`**: Scraper configuration constants

---

## Usage

```python
from scraper import GenericScraper

scraper = GenericScraper()
chapters = scraper.fetch_chapter_urls(novel_url)
content = scraper.scrape_chapter(chapter_url)
```

---

## Testing

**Test Location**: `tests/unit/`
-  `test_text_cleaner.py` - Text cleaner tests
-  `test_chapter_parser.py` - Chapter parser tests

**Playwright Integration Tests**: `ACT REFERENCES/TESTS/TEST_SCRIPTS/`
-  `test_playwright_novelfull_full.py` - Full chapter fetch test for NovelFull
-  `test_playwright_simple.py` - Basic Playwright functionality test
-  `test_playwright_quick.py` - Quick Playwright test
-  `test_playwright_novelfull.py` - NovelFull-specific Playwright test

---

## Recent Improvements (2025-01-27)

### Playwright Enhancements

Based on comparison with similar GitHub projects, the following improvements were implemented:

1. **Retry Logic with Exponential Backoff**
   - Automatically retries failed page loads (up to 3 attempts)
   - Exponential backoff: 1s, 2s, 4s delays
   - Handles transient network errors gracefully

2. **Rate Limiting**
   - Minimum 0.5s delay between requests
   - Reduces risk of being blocked by websites
   - Configurable via `_min_request_delay` attribute

3. **Network Idle Waiting**
   - Replaced fixed delays with `networkidle` waits
   - More reliable - waits for actual network activity to complete
   - Falls back to `domcontentloaded` if `networkidle` times out
   - Applied to both pagination visits and scrolling completion

4. **Progress Tracking**
   - Shows progress percentage during pagination visits
   - Format: "Loading page X/Y (Z%)"
   - Better visibility for long-running operations

5. **Enhanced Error Handling**
   - Continues on individual page errors (doesn't stop entire process)
   - Better Cloudflare challenge detection and waiting
   - Improved logging for debugging

**Reference**: See `ACT REFERENCES/PLAYWRIGHT_COMPARISON.md` for detailed comparison with other projects.

---

**See Also**:
- [Project Status](../CURRENT_STATUS_SUMMARY.md)
- [Architecture](../ARCHITECTURE.md)
- [Playwright Comparison](../../PLAYWRIGHT_COMPARISON.md)
