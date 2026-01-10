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

URL fetching (optimized order):
1. JavaScript variable extraction (fastest)
2. AJAX endpoint discovery (fast + lazy-loading)
3. Playwright with scrolling (comprehensive)

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
