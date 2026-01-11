# Scraper Module

**Status**: ✅ Complete
**Location**: `src/scraper/`

## Overview

Handles web scraping and content extraction from novel websites.

## Components

- **GenericScraper**: Main scraper for web novel sites
- **URL extractors**: Multi-strategy URL discovery with fallback
- **Content extractors**: Chapter content extraction
- **Base classes**: Abstract scraper implementations

## Features

- Retry logic with backoff
- Rate limiting and delays
- Progress tracking
- Error handling

## Usage

```python
from scraper import GenericScraper

scraper = GenericScraper()
chapters = scraper.fetch_chapter_urls(url)
content = scraper.scrape_chapter(url)
```

## Testing

- Unit tests for scraper components
- Integration tests for scraping workflows
