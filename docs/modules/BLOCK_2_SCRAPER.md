# Scraper Module (v1.1.1)

**Status**: ✅ Complete
**Location**: `src/scraper/`
**Version**: 1.1.1 - Universal Detector Architecture

## Overview

Handles web scraping and content extraction from novel websites using the Universal URL Detector system. The scraper has been refactored in v1.1.1 to use a unified adaptive multi-strategy approach, removing legacy dual-path complexity.

## Components

- **NovelScraper**: Main scraper for web novel sites (unified interface)
- **Universal URL Detector**: Adaptive multi-strategy URL discovery system
- **Detection Strategies**: Parallel execution of 5 optimized extraction methods:
  - JavaScript variable extraction (fastest)
  - AJAX endpoint discovery (handles lazy-loading & pagination)
  - HTML parsing (traditional but reliable)
  - Browser automation (Playwright, comprehensive)
  - API reverse engineering (advanced sites)
- **Content extractors**: Chapter content extraction with Cloudflare bypass
- **Adaptive Configuration**: Machine learning-based optimization per website
- **Session Management**: Rate limiting and session pooling

## Features

- **Parallel strategy execution** for optimal performance
- **Adaptive learning** that improves detection over time
- **Machine learning optimization** per website domain
- **Comprehensive fallback** through multiple extraction methods
- Retry logic with backoff
- Rate limiting and delays
- Progress tracking
- Error handling

## Architecture (v1.1.1)

The scraper uses a **unified Universal URL Detector** that:
1. **Parallel Strategy Execution**: Runs 5 detection strategies simultaneously for optimal performance
2. **Adaptive Learning**: Learns from successful/failed attempts per site using machine learning
3. **Intelligent Selection**: Selects optimal strategies based on historical performance and response times
4. **Comprehensive Coverage**: Handles modern web applications with lazy-loading, pagination, and anti-bot measures
5. **Session Management**: Integrated rate limiting and connection pooling for reliability

### Key Improvements in v1.1.1
- **Removed Legacy Complexity**: Eliminated confusing dual-path system and misleading "fast path" optimizations
- **Always Universal**: Single, reliable detection system instead of multiple fallbacks
- **Better Performance**: Parallel execution instead of sequential fallbacks
- **Enhanced Reliability**: Machine learning optimization per website domain

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
