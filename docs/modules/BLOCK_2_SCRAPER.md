# Scraper Module (Legacy, 1.1-prep)

**Status**: Complete  
**Location**: `src/scraper/`  
**Version**: 1.1.0-pre  

## Overview

Legacy scraper for web novels. It uses a proven, sequential fallback approach and is the only supported scraping system for the 1.1 release.

## Components

- **NovelScraper**: Main entry point for scraping
- **UrlExtractor**: Legacy URL extraction with ordered fallbacks
- **ChapterExtractor**: Chapter content/title extraction
- **Playwright scripts**: Browser automation for difficult sites
- **Session Management**: Rate limiting and consistent headers

## Legacy URL Extraction Flow

The extractor tries these methods in order:
1. **JavaScript variable extraction** (fastest)
2. **AJAX endpoint discovery**
3. **HTML parsing**
4. **Playwright with scrolling** (fallback)

If a method yields enough chapters, it stops and returns those URLs.

## Features

- Reliable multi-step fallback (sequential)
- Pagination awareness and range validation
- Rate limiting and delay between requests
- Consistent URL normalization and ordering
- Robust chapter content parsing

## Usage

```python
from scraper import NovelScraper

scraper = NovelScraper("https://example-novel.com")
chapter_urls = scraper.get_chapter_urls(toc_url)
content, title, error = scraper.scrape_chapter(chapter_url)
```
