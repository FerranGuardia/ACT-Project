"""
Unit tests for scroll_operations.js module.

Tests scroll operation helper functions for containers and windows.
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
def scroll_operations_code():
    """Load the scroll_operations.js module code."""
    script_path = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts" / "scroll_operations.js"
    return script_path.read_text(encoding="utf-8")


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestScrollOperations:
    """Test cases for scroll_operations.js module."""
    
    def test_scrolls_container_by_amount(self, scroll_operations_code):
        """Test scrolling a container by a specified amount."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="container" style="height: 200px; overflow-y: scroll;">
                        <div style="height: 1000px;">
                            <a href="/chapter-1">Chapter 1</a>
                            <a href="/chapter-2">Chapter 2</a>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {scroll_operations_code}
                
                var container = document.getElementById('container');
                var initialScroll = container.scrollTop;
                scrollContainer(container, 200);
                var finalScroll = container.scrollTop;
                
                return {{
                            scrolled: finalScroll > initialScroll,
                    scrollAmount: finalScroll - initialScroll
                }};
            }})()
            """)
            
            assert result['scrolled'] == True, "Container should be scrolled"
            assert result['scrollAmount'] >= 200, "Should scroll by at least 200px"
            
            browser.close()
    
    def test_scrolls_container_to_bottom(self, scroll_operations_code):
        """Test scrolling container to its maximum height."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="container" style="height: 200px; overflow-y: scroll;">
                        <div style="height: 1000px;">
                            <a href="/chapter-1">Chapter 1</a>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {scroll_operations_code}
                
                var container = document.getElementById('container');
                scrollContainerToBottom(container);
                
                return {{
                            scrollTop: container.scrollTop,
                    scrollHeight: container.scrollHeight,
                    clientHeight: container.clientHeight,
                    isAtBottom: container.scrollTop >= (container.scrollHeight - container.clientHeight - 10)
                }};
            }})()
            """)
            
            assert result['isAtBottom'] == True, "Container should be scrolled to bottom"
            
            browser.close()
    
    def test_scrolls_to_last_chapter(self, scroll_operations_code):
        """Test scrolling the last chapter link into view."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body style="height: 200px; overflow-y: scroll;">
                    <div style="height: 2000px;">
                        <a href="/chapter-1" id="ch1" style="display: block; margin-top: 100px;">Chapter 1</a>
                        <a href="/chapter-2" id="ch2" style="display: block; margin-top: 500px;">Chapter 2</a>
                        <a href="/chapter-3" id="ch3" style="display: block; margin-top: 1500px;">Chapter 3</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {scroll_operations_code}
                
                var ch1 = document.getElementById('ch1');
                var ch2 = document.getElementById('ch2');
                var ch3 = document.getElementById('ch3');
                var chapterLinks = [ch1, ch2, ch3];
                
                return new Promise(function(resolve) {{
                    scrollToLastChapter(chapterLinks, 100).then(function() {{
                        var lastLinkRect = ch3.getBoundingClientRect();
                        resolve({{
                            isVisible: lastLinkRect.top >= 0 && lastLinkRect.bottom <= window.innerHeight,
                            scrollY: window.scrollY
                        }});
                    }});
                }});
            """)
            
            # The last chapter should be scrolled into view
            assert result['scrollY'] > 0, "Page should be scrolled"
            
            browser.close()
    
    def test_scrolls_past_last_chapter(self, scroll_operations_code):
        """Test scrolling past the last chapter link."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body style="height: 200px; overflow-y: scroll;">
                    <div style="height: 2000px;">
                        <a href="/chapter-1" id="ch1" style="display: block; margin-top: 1000px; height: 100px;">Chapter 1</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {scroll_operations_code}
                
                var ch1 = document.getElementById('ch1');
                var chapterLinks = [ch1];
                var initialScrollY = window.scrollY;
                
                return new Promise(function(resolve) {{
                    scrollPastLastChapter(chapterLinks, 2, 100).then(function() {{
                        resolve({{
                            scrolled: window.scrollY > initialScrollY,
                            scrollAmount: window.scrollY - initialScrollY
                        }});
                    }});
                }});
            """)
            
            assert result['scrolled'] == True, "Should scroll past last chapter"
            assert result['scrollAmount'] > 0, "Should scroll by some amount"
            
            browser.close()
    
    def test_handles_empty_chapter_links_array(self, scroll_operations_code):
        """Test handling when chapter links array is empty."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.set_content("<html><body></body></html>")
            
            # Should not throw error
            result = page.evaluate(f"""
                {scroll_operations_code}
                
                return new Promise(function(resolve) {{
                    scrollToLastChapter([], 100).then(function() {{
                        resolve({{success: true}});
                    }});
                }});
            """)
            
            assert result['success'] == True, "Should handle empty array gracefully"
            
            browser.close()
    
    def test_scrolls_window_when_container_is_body(self, scroll_operations_code):
        """Test that window scrolling occurs even when container is body."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body style="height: 200px; overflow-y: scroll;">
                    <div style="height: 2000px;">
                        <a href="/chapter-1">Chapter 1</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {scroll_operations_code}
                
                var initialScrollY = window.scrollY;
                scrollContainer(document.body, 200);
                var finalScrollY = window.scrollY;
                
                return {{
                            scrolled: finalScrollY > initialScrollY,
                    scrollAmount: finalScrollY - initialScrollY
                }};
            }})()
            """)
            
            assert result['scrolled'] == True, "Window should be scrolled"
            
            browser.close()

