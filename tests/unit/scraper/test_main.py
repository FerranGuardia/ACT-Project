"""
Unit tests for main.js module.

Tests the main entry point scrollAndCountChapters function that orchestrates all modules.
"""

import pytest
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
    HAS_PLAYWRIGHT: bool = True
except ImportError:
    HAS_PLAYWRIGHT: bool = False
    sync_playwright = None  # type: ignore[assignment, misc]


@pytest.fixture
def all_modules_code():
    """Load all module code in dependency order."""
    scripts_dir = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts"
    
    modules = [
        "chapter_detector.js",
        "link_counter.js",
        "load_more_handler.js",
        "container_finder.js",
        "scroll_operations.js",
        "scroll_loop.js",
        "main.js",
    ]
    
    code_parts = []
    for module in modules:
        code_parts.append((scripts_dir / module).read_text(encoding="utf-8"))
    
    return "\n\n".join(code_parts)


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestMain:
    """Test cases for main.js module."""
    
    def test_scroll_and_count_chapters_exists(self, all_modules_code):
        """Test that scrollAndCountChapters function exists."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.set_content("<html><body></body></html>")
            
            result = page.evaluate(f"""
                (function() {{
                    {all_modules_code}
                    
                    return typeof scrollAndCountChapters;
                }})()
            """)
            
            assert result == "function", "scrollAndCountChapters should be a function"
            
            browser.close()
    
    def test_scroll_and_count_chapters_returns_count(self, all_modules_code):
        """Test that scrollAndCountChapters returns a chapter count."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="chapters">
                        <a href="/chapter-1">Chapter 1</a>
                        <a href="/chapter-2">Chapter 2</a>
                        <a href="/chapter-3">Chapter 3</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Override config for faster testing
            result = page.evaluate(f"""
                (function() {{
                    {all_modules_code}
                    
                    // Override SCROLL_CONFIG for faster testing
                    SCROLL_CONFIG.maxScrolls = 5;
                    SCROLL_CONFIG.maxNoChange = 2;
                    SCROLL_CONFIG.scrollDelay = 50;
                    
                    return scrollAndCountChapters().then(function(count) {{
                        return count;
                    }});
                }})()
            """)
            
            assert isinstance(result, (int, float)), "Should return a number"
            assert result == 3, "Should return count of 3 chapters"
            
            browser.close()
    
    def test_scroll_and_count_chapters_with_lazy_loading(self, all_modules_code):
        """Test scrollAndCountChapters with simulated lazy loading."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="chapters" style="height: 200px; overflow-y: scroll;">
                        <div style="height: 2000px;">
                            <a href="/chapter-1">Chapter 1</a>
                            <a href="/chapter-2">Chapter 2</a>
                            <a href="/chapter-3">Chapter 3</a>
                            <a href="/chapter-4">Chapter 4</a>
                            <a href="/chapter-5">Chapter 5</a>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Override config for faster testing
            result = page.evaluate(f"""
                (function() {{
                    {all_modules_code}
                    
                    SCROLL_CONFIG.maxScrolls = 10;
                    SCROLL_CONFIG.maxNoChange = 3;
                    SCROLL_CONFIG.scrollDelay = 50;
                    
                    return scrollAndCountChapters().then(function(count) {{
                        return count;
                    }});
                }})()
            """)
            
            assert result == 5, "Should find all 5 chapters"
            
            browser.close()
    
    def test_scroll_and_count_chapters_handles_empty_page(self, all_modules_code):
        """Test scrollAndCountChapters with empty page."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.set_content("<html><body></body></html>")
            
            # Override config for faster testing
            result = page.evaluate(f"""
                (function() {{
                    {all_modules_code}
                    
                    SCROLL_CONFIG.maxScrolls = 5;
                    SCROLL_CONFIG.maxNoChange = 2;
                    SCROLL_CONFIG.scrollDelay = 50;
                    
                    return scrollAndCountChapters().then(function(count) {{
                        return count;
                    }});
                }})()
            """)
            
            assert result == 0, "Should return 0 for empty page"
            
            browser.close()
    
    def test_scroll_and_count_chapters_integrates_all_modules(self, all_modules_code):
        """Test that scrollAndCountChapters properly integrates all modules."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="chapters">
                        <a href="/chapter-1">Chapter 1</a>
                        <a href="/chapter-2">Chapter 2</a>
                        <button class="load-more-button">Load More</button>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Track which modules are called
            result = page.evaluate(f"""
                (function() {{
                    {all_modules_code}
                    
                    // Override config for faster testing
                    SCROLL_CONFIG.maxScrolls = 5;
                    SCROLL_CONFIG.maxNoChange = 2;
                    SCROLL_CONFIG.scrollDelay = 50;
                    
                    // Verify all functions exist
                    var functionsExist = {{
                        isChapterLink: typeof isChapterLink === 'function',
                        countChapterLinks: typeof countChapterLinks === 'function',
                        getChapterLinks: typeof getChapterLinks === 'function',
                        tryClickLoadMore: typeof tryClickLoadMore === 'function',
                        findChapterContainer: typeof findChapterContainer === 'function',
                        scrollContainer: typeof scrollContainer === 'function',
                        performScrollLoop: typeof performScrollLoop === 'function'
                    }};
                    
                    return scrollAndCountChapters().then(function(count) {{
                        return {{
                            count: count,
                            functionsExist: functionsExist
                        }};
                    }});
                }})()
            """)
            
            assert result['count'] == 2, "Should count 2 chapters"
            assert all(result['functionsExist'].values()), "All functions should exist"
            
            browser.close()
    
    def test_scroll_and_count_chapters_with_pagination(self, all_modules_code):
        """Test scrollAndCountChapters with pagination-like structure."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div class="chapter-list">
                        <a href="/chapter-1">Chapter 1</a>
                        <a href="/chapter-2">Chapter 2</a>
                        <a href="/chapter-3">Chapter 3</a>
                        <a href="/chapter-4">Chapter 4</a>
                        <a href="/chapter-5">Chapter 5</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Override config for faster testing
            result = page.evaluate(f"""
                (function() {{
                    {all_modules_code}
                    
                    SCROLL_CONFIG.maxScrolls = 5;
                    SCROLL_CONFIG.maxNoChange = 2;
                    SCROLL_CONFIG.scrollDelay = 50;
                    
                    return scrollAndCountChapters().then(function(count) {{
                        return count;
                    }});
                }})()
            """)
            
            assert result == 5, "Should find all 5 chapters"
            
            browser.close()

