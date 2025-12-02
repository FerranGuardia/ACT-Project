"""
Configuration for scraper module.

Contains default settings, selectors, and patterns for web scraping.
"""

# Request settings
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 2.0
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0  # seconds

# Rate limiting
RATE_LIMIT_DELAY = 1.0
RATE_LIMIT_BUFFER = 0.5

# Playwright settings
PLAYWRIGHT_TIMEOUT = 30000
PLAYWRIGHT_HEADLESS = True
PLAYWRIGHT_MAX_SCROLLS = 2000

# Content selectors (common patterns across webnovel sites)
TITLE_SELECTORS = [
    "h1.chapter-title",
    "h1#chapter-title",
    "h2.chapter-title",
    ".chapter-title",
    "#chapter-title",
    "h1",
    "h2",
]

CONTENT_SELECTORS = [
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
]

# Chapter URL patterns
CHAPTER_URL_PATTERN = r"chapter[_-]?(\d+)"
NOVEL_ID_PATTERNS = [
    r"/novel/(\d+)",
    r"/book/(\d+)",
    r"/b/([^/]+)",
    r"novelId=(\d+)",
    r'data-novel-id="(\d+)"',
]

