# Scraper Module

**Status**: Complete
**Location**: `src/scraper/`

## Components

- **`GenericScraper`**: Main scraper for webnovel sites
- **`ChapterUrlFetcher`**: Multi-strategy URL extraction with fallback
- **`ContentScraper`**: Chapter content extraction with selector patterns
- **`BaseScraper`**: Abstract base class
- **`NovelBinScraper`**: Site-specific implementation

## Strategies

URL fetching (fallback order):
1. JavaScript variable extraction
2. AJAX endpoint discovery  
3. HTML parsing
4. Playwright with scrolling
5. Link following

## Features

- Retry logic with exponential backoff
- Rate limiting (0.5s minimum delay)
- Network idle waiting
- Progress tracking
- Cloudflare handling

## Usage

```python
from scraper import GenericScraper
scraper = GenericScraper()
chapters = scraper.fetch_chapter_urls(url)
content = scraper.scrape_chapter(url)
```

## Testing

- `tests/unit/test_text_cleaner.py`
- `tests/unit/test_chapter_parser.py`
