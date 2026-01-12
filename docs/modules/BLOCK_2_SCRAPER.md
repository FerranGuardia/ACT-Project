# Scraper Module

**Status**: ✅ Complete
**Location**: `src/scraper/`

## Overview

Handles web scraping and content extraction from novel websites using an adaptive multi-strategy approach.

## Components

- **NovelScraper**: Main scraper for web novel sites
- **Universal URL Detector**: Adaptive multi-strategy URL discovery system
- **Detection Strategies**: Parallel execution of 5 different extraction methods:
  - JavaScript variable extraction
  - AJAX endpoint discovery
  - HTML parsing
  - Browser automation (Playwright)
  - API reverse engineering
- **Content extractors**: Chapter content extraction
- **Adaptive Configuration**: Machine learning-based optimization per website

## Features

- **Parallel strategy execution** for optimal performance
- **Adaptive learning** that improves detection over time
- **Machine learning optimization** per website domain
- **Comprehensive fallback** through multiple extraction methods
- Retry logic with backoff
- Rate limiting and delays
- Progress tracking
- Error handling

## Architecture

The scraper uses a **unified Universal URL Detector** that:
1. Runs multiple detection strategies in parallel
2. Learns from successful/failed attempts per site
3. Selects optimal strategies based on historical performance
4. Provides comprehensive coverage for modern web applications

## Usage

```python
from scraper import NovelScraper

scraper = NovelScraper("https://example-novel.com")
chapter_urls = scraper.get_chapter_urls(toc_url)
content, title, error = scraper.scrape_chapter(chapter_url)
```

## Testing

- Unit tests for scraper components
- Integration tests for scraping workflows
