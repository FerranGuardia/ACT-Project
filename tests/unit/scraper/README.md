# Playwright Scripts Unit Tests

This directory contains unit tests for the modularized Playwright scripts located in `src/scraper/playwright_scripts/`.

## Test Files

Each module has a corresponding test file:

1. **`test_chapter_detector.py`** - Tests `chapter_detector.js`
   - Tests `isChapterLink()` function
   - Validates various chapter link patterns
   - Tests edge cases and error handling

2. **`test_link_counter.py`** - Tests `link_counter.js`
   - Tests `countChapterLinks()` function
   - Tests `getChapterLinks()` function
   - Tests dynamic link detection

3. **`test_load_more_handler.py`** - Tests `load_more_handler.js`
   - Tests `tryClickLoadMore()` function
   - Tests `matchesLoadMoreText()` function
   - Tests button detection strategies

4. **`test_container_finder.py`** - Tests `container_finder.js`
   - Tests `findChapterContainer()` function
   - Tests container priority logic
   - Tests fallback behavior

5. **`test_scroll_operations.py`** - Tests `scroll_operations.js`
   - Tests `scrollContainer()` function
   - Tests `scrollContainerToBottom()` function
   - Tests `scrollToLastChapter()` function
   - Tests `scrollPastLastChapter()` function

6. **`test_scroll_loop.py`** - Tests `scroll_loop.js`
   - Tests `performScrollLoop()` function
   - Tests `SCROLL_CONFIG` object
   - Tests `performFinalLoadMoreAttempts()` function
   - Tests `performFinalAggressiveScroll()` function

7. **`test_main.py`** - Tests `main.js`
   - Tests `scrollAndCountChapters()` entry point
   - Tests module integration
   - Tests end-to-end functionality

## Running the Tests

### Prerequisites

- Playwright must be installed: `pip install playwright && playwright install chromium`
- pytest must be installed: `pip install pytest`

### Run All Tests

```bash
# From project root
pytest tests/unit/scraper/

# With verbose output
pytest tests/unit/scraper/ -v

# Run specific test file
pytest tests/unit/scraper/test_chapter_detector.py

# Run specific test class
pytest tests/unit/scraper/test_chapter_detector.py::TestChapterDetector

# Run specific test method
pytest tests/unit/scraper/test_chapter_detector.py::TestChapterDetector::test_detects_standard_chapter_links
```

### Skip Tests if Playwright Not Installed

Tests automatically skip if Playwright is not installed. You'll see:
```
SKIPPED [1] tests/unit/scraper/test_chapter_detector.py: Playwright not installed
```

## Test Structure

Each test file follows this pattern:

1. **Fixtures**: Load JavaScript module code from files
2. **Test Classes**: Group related tests together
3. **Test Methods**: Individual test cases that:
   - Launch a Playwright browser
   - Create test HTML/DOM
   - Inject JavaScript modules
   - Execute functions via `page.evaluate()`
   - Assert expected results
   - Clean up browser

## Example Test

```python
def test_detects_standard_chapter_links(self, chapter_detector_code):
    """Test detection of standard chapter link patterns."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        html = """
        <html>
            <body>
                <a href="/chapter-1" id="link1">Chapter 1</a>
            </body>
        </html>
        """
        
        page.set_content(html)
        
        result = page.evaluate(f"""
            {chapter_detector_code}
            
            var link1 = document.getElementById('link1');
            return isChapterLink(link1);
        """)
        
        assert result == True
        browser.close()
```

## Test Coverage

The tests cover:

- ✅ **Functionality**: All exported functions are tested
- ✅ **Edge Cases**: Null inputs, empty arrays, invalid data
- ✅ **Pattern Matching**: Various chapter link patterns
- ✅ **Integration**: Module dependencies and interactions
- ✅ **Error Handling**: Graceful handling of errors

## Notes

- Tests run in headless browser mode for speed
- Tests use simplified configurations (reduced delays) for faster execution
- Tests are isolated - each test creates its own browser instance
- Tests clean up after themselves (browser.close())

## Troubleshooting

### Tests Fail with "Playwright not installed"

Install Playwright:
```bash
pip install playwright
playwright install chromium
```

### Tests Timeout

Some tests may timeout if Playwright is slow. Increase timeout:
```bash
pytest tests/unit/scraper/ --timeout=30
```

### Browser Launch Fails

Ensure Chromium is installed:
```bash
playwright install chromium
```

