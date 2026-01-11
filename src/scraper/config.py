"""
Configuration for scraper module.

Contains default settings, selectors, and patterns for web scraping.
"""

# Request settings
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 5.0  # Increased from 2.0 to reduce website impact
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 3.0  # Increased from 2.0 for more conservative backoff

# Rate limiting
RATE_LIMIT_DELAY = 3.0  # Increased from 1.0 to reduce request frequency
RATE_LIMIT_BUFFER = 1.0  # Increased from 0.5 for more conservative rate limiting

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
    # NovelFull specific selectors (most specific first)
    "div.cha-words",  # NovelFull main content container
    "div.cha-content",  # NovelFull content wrapper
    "div.chapter-c",
    "div#chapter-c",
    "div.text-left",
    "div#text-chapter",
    "div.chapter-content-wrapper",

    # General novel site selectors
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

    # Additional common selectors
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
    "div#chap-content",
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

# Pagination detection settings
PAGINATION_SUSPICIOUS_COUNTS = [20, 25, 30, 40, 50, 55, 100, 200]  # Common pagination limits
PAGINATION_CRITICAL_COUNT = 55  # Always suspect pagination at this count
PAGINATION_SMALL_COUNT_THRESHOLD = 100  # Below this is considered "small"
PAGINATION_RANGE_COVERAGE_THRESHOLD = 0.8  # Minimum coverage required for range validation
