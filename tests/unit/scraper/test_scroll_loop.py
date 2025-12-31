"""
Unit tests for scroll_loop.js module.

Tests the main scrolling loop logic and configuration.
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
def scroll_loop_code():
    """Load the scroll_loop.js module code."""
    script_path = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts" / "scroll_loop.js"
    return script_path.read_text(encoding="utf-8")


@pytest.fixture
def all_dependencies_code():
    """Load all dependency modules."""
    scripts_dir = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts"
    
    modules = [
        "chapter_detector.js",
        "link_counter.js",
        "load_more_handler.js",
        "container_finder.js",
        "scroll_operations.js",
    ]
    
    code_parts = []
    for module in modules:
        code_parts.append((scripts_dir / module).read_text(encoding="utf-8"))
    
    return "\n\n".join(code_parts)


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestScrollLoop:
    """Test cases for scroll_loop.js module."""
    
    def test_scroll_config_exists(self, scroll_loop_code):
        """Test that SCROLL_CONFIG object exists and has expected properties."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.set_content("<html><body></body></html>")
            
            result = page.evaluate(f"""
                (function() {{
                    scroll_loop_code
                    
                    return {{
                            exists: typeof SCROLL_CONFIG !== 'undefined',
                    hasMaxScrolls: 'maxScrolls' in SCROLL_CONFIG,
                    hasMaxNoChange: 'maxNoChange' in SCROLL_CONFIG,
                    hasScrollDelay: 'scrollDelay' in SCROLL_CONFIG,
                    maxScrolls: SCROLL_CONFIG.maxScrolls,
                    maxNoChange: SCROLL_CONFIG.maxNoChange
                }};
            }})()
            """)
            
            assert result['exists'] == True, "SCROLL_CONFIG should exist"
            assert result['hasMaxScrolls'] == True, "Should have maxScrolls"
            assert result['hasMaxNoChange'] == True, "Should have maxNoChange"
            assert result['hasScrollDelay'] == True, "Should have scrollDelay"
            assert result['maxScrolls'] == 1000, "maxScrolls should be 1000"
            assert result['maxNoChange'] == 30, "maxNoChange should be 30"
            
            browser.close()
    
    def test_perform_scroll_loop_with_simple_case(self, scroll_loop_code, all_dependencies_code):
        """Test performScrollLoop with a simple case (few chapters, no lazy loading)."""
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
            
            # Create a simplified version that stops early for testing
            result = page.evaluate(f"""
                {all_dependencies_code}
                {scroll_loop_code}
                
                // Override SCROLL_CONFIG for faster testing
                SCROLL_CONFIG.maxScrolls = 5;
                SCROLL_CONFIG.maxNoChange = 2;
                SCROLL_CONFIG.scrollDelay = 50;
                
                var dependencies = {{
                    countChapterLinks: function() {{
                        return countChapterLinks(isChapterLink);
                    }},
                    getChapterLinks: function() {{
                        return getChapterLinks(isChapterLink);
                    }},
                    tryClickLoadMore: async function() {{ return false; }},
                    findChapterContainer: findChapterContainer,
                    scrollContainer: function(container) {{
                        // Simplified scroll for testing
                        container.scrollTop += 100;
                        window.scrollTo(0, document.body.scrollHeight);
                    }},
                    scrollContainerToBottom: scrollContainerToBottom,
                    scrollToLastChapter: async function(links) {{
                        if (links.length > 0) {{
                            links[links.length - 1].scrollIntoView();
                        }}
                    }},
                    scrollPastLastChapter: async function(links) {{
                        // Simplified for testing
                    }}
                }};
                
                return performScrollLoop(dependencies);
            """)
            
            assert result == 3, "Should count 3 chapters"
            
            browser.close()
    
    def test_perform_final_load_more_attempts(self, scroll_loop_code, all_dependencies_code):
        """Test performFinalLoadMoreAttempts function."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="chapters">
                        <a href="/chapter-1">Chapter 1</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {all_dependencies_code}
                {scroll_loop_code}
                
                var tryClickLoadMoreCalled = 0;
                var mockTryClickLoadMore = async function() {{
                    tryClickLoadMoreCalled++;
                    return false; // Simulate no button found
                }};
                
                var countCalled = 0;
                var mockCountChapterLinks = function() {{
                    countCalled++;
                    return countChapterLinks(isChapterLink);
                }};
                
                return performFinalLoadMoreAttempts(mockTryClickLoadMore, mockCountChapterLinks).then(function(result) {{
                    return {{
                                result: result,
                        tryClickLoadMoreCalled: tryClickLoadMoreCalled,
                        countCalled: countCalled
                    }};
                }});
            """)
            
            assert result['tryClickLoadMoreCalled'] == 5, "Should attempt 5 times"
            assert result['result'] == False, "Should return false when no button found"
            
            browser.close()
    
    def test_perform_final_aggressive_scroll(self, scroll_loop_code, all_dependencies_code):
        """Test performFinalAggressiveScroll function."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="chapters" style="height: 200px; overflow-y: scroll;">
                        <div style="height: 1000px;">
                            <a href="/chapter-1">Chapter 1</a>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Override config for faster testing
            result = page.evaluate(f"""
                {all_dependencies_code}
                {scroll_loop_code}
                
                SCROLL_CONFIG.finalAggressiveScrolls = 2;
                SCROLL_CONFIG.finalAggressiveLoadMoreAttempts = 1;
                SCROLL_CONFIG.finalAggressiveWait = 50;
                
                var container = document.getElementById('chapters');
                var scrollToBottomCalled = 0;
                var tryClickLoadMoreCalled = 0;
                
                var dependencies = {{
                    scrollContainerToBottom: function(cont) {{
                        scrollToBottomCalled++;
                        scrollContainerToBottom(cont);
                    }},
                    tryClickLoadMore: async function() {{
                        tryClickLoadMoreCalled++;
                        return false;
                    }},
                    countChapterLinks: function() {{
                        return countChapterLinks(isChapterLink);
                    }},
                    getChapterLinks: function() {{
                        return getChapterLinks(isChapterLink);
                    }},
                    scrollPastLastChapter: async function(links) {{
                        // Simplified
                    }}
                }};
                
                return performFinalAggressiveScroll(container, dependencies, 1).then(function(finalCount) {{
                    return {{
                                finalCount: finalCount,
                        scrollToBottomCalled: scrollToBottomCalled,
                        tryClickLoadMoreCalled: tryClickLoadMoreCalled
                    }};
                }});
            """)
            
            assert result['scrollToBottomCalled'] == 2, "Should scroll to bottom 2 times"
            assert result['tryClickLoadMoreCalled'] == 2, "Should try load more 2 times"
            assert result['finalCount'] == 1, "Should return chapter count"
            
            browser.close()
    
    def test_scroll_loop_stops_on_max_no_change(self, scroll_loop_code, all_dependencies_code):
        """Test that scroll loop stops when maxNoChange is reached."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="chapters">
                        <a href="/chapter-1">Chapter 1</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {all_dependencies_code}
                {scroll_loop_code}
                
                // Override config for faster testing
                SCROLL_CONFIG.maxScrolls = 100;
                SCROLL_CONFIG.maxNoChange = 3;
                SCROLL_CONFIG.scrollDelay = 10;
                
                var scrollCount = 0;
                var dependencies = {{
                    countChapterLinks: function() {{
                        return 1; // Always return same count
                    }},
                    getChapterLinks: function() {{
                        return [];
                    }},
                    tryClickLoadMore: async function() {{ return false; }},
                    findChapterContainer: findChapterContainer,
                    scrollContainer: function(container) {{
                        scrollCount++;
                    }},
                    scrollContainerToBottom: function() {{}},
                    scrollToLastChapter: async function() {{}},
                    scrollPastLastChapter: async function() {{}}
                }};
                
                return performScrollLoop(dependencies).then(function(count) {{
                    return {{
                                count: count,
                        scrollCount: scrollCount
                    }};
                }});
            """)
            
            # Should stop after maxNoChange iterations
            assert result['scrollCount'] <= SCROLL_CONFIG.maxNoChange + 5, "Should stop after maxNoChange"
            assert result['count'] == 1, "Should return final count"
            
            browser.close()

