# Playwright Scripts Module

This directory contains modularized JavaScript files for Playwright-based chapter URL extraction.

## Module Structure

The scripts are split into focused modules, each under 400 lines of code:

### Core Modules

1. **`chapter_detector.js`** (~70 lines)
   - `isChapterLink(link)` - Detects if a link element is a chapter link
   - Uses flexible patterns matching Python `_is_chapter_url()` logic
   - Supports multiple webnovel site patterns

2. **`link_counter.js`** (~30 lines)
   - `countChapterLinks(isChapterLinkFn)` - Counts chapter links in DOM
   - `getChapterLinks(isChapterLinkFn)` - Gets all chapter link elements

3. **`load_more_handler.js`** (~112 lines)
   - `tryClickLoadMore()` - Attempts to find and click "Load More" buttons
   - `matchesLoadMoreText(text)` - Checks if text matches load more patterns
   - `tryClickLoadMoreAggressive()` - Performs multiple aggressive attempts

4. **`container_finder.js`** (~37 lines)
   - `findChapterContainer()` - Finds the best container for scrolling
   - Prioritizes chapter-specific containers, falls back to general content containers

5. **`scroll_operations.js`** (~89 lines)
   - `scrollContainer(container, scrollAmount)` - Scrolls container by amount
   - `scrollContainerToBottom(container)` - Scrolls container to bottom
   - `scrollToLastChapter(chapterLinks, waitTime)` - Scrolls to last chapter
   - `scrollPastLastChapter(chapterLinks, multiplier, waitTime)` - Scrolls past last chapter

6. **`scroll_loop.js`** (~202 lines)
   - `performScrollLoop(dependencies)` - Main scrolling loop orchestration
   - `performFinalLoadMoreAttempts()` - Final aggressive load more attempts
   - `performFinalAggressiveScroll()` - Final aggressive scroll phase
   - Contains `SCROLL_CONFIG` configuration object

7. **`main.js`** (~47 lines)
   - `scrollAndCountChapters()` - Main entry point
   - Orchestrates all modules
   - Called by Playwright's `page.evaluate()`

## Module Loading Order

Modules are loaded in dependency order by the Python loader (`url_extractor_playwright.py`):

1. `chapter_detector.js` (no dependencies)
2. `link_counter.js` (depends on `chapter_detector.js`)
3. `load_more_handler.js` (no dependencies)
4. `container_finder.js` (no dependencies)
5. `scroll_operations.js` (no dependencies)
6. `scroll_loop.js` (depends on all above modules)
7. `main.js` (depends on all above modules)

## Usage

The Python loader (`_load_playwright_scroll_script()`) automatically bundles all modules together and wraps them in an async function for Playwright execution:

```python
from src.scraper.extractors.url_extractor_playwright import PlaywrightExtractor

extractor = PlaywrightExtractor(...)
script = extractor._load_playwright_scroll_script()
result = page.evaluate(script)  # Returns chapter count
```

## Benefits of Modularization

1. **Maintainability**: Each module has a single, clear responsibility
2. **Testability**: Individual modules can be tested in isolation
3. **Readability**: Smaller files are easier to understand and navigate
4. **Reusability**: Modules can be reused or modified independently
5. **Code Size**: All modules are under 400 lines, making them manageable

## Testing

Each module can be tested independently:

- **Unit Tests**: Test individual functions with mock DOM elements
- **Integration Tests**: Test modules together in a real browser context
- **E2E Tests**: Test the complete bundled script with Playwright

See `tests/unit/scraper/test_playwright_scripts/` for test examples.





