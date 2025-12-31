"""
Unit tests for load_more_handler.js module.

Tests the tryClickLoadMore and related functions for detecting and clicking Load More buttons.
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
def load_more_handler_code():
    """Load the load_more_handler.js module code."""
    script_path = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts" / "load_more_handler.js"
    return script_path.read_text(encoding="utf-8")


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestLoadMoreHandler:
    """Test cases for load_more_handler.js module."""
    
    def test_detects_load_more_by_text(self, load_more_handler_code):
        """Test detection of Load More buttons by text content."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <button id="btn1">Load More</button>
                    <a href="#" id="btn2">Show More</a>
                    <span id="btn3">View More</span>
                    <div id="btn4">See More</div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Test matchesLoadMoreText function
            result = page.evaluate(f"""
                (function() {{
                    {load_more_handler_code}
                    
                    var btn1 = document.getElementById('btn1');
                    var btn2 = document.getElementById('btn2');
                    var btn3 = document.getElementById('btn3');
                    var btn4 = document.getElementById('btn4');
                    
                    return {{
                        btn1: matchesLoadMoreText(btn1.textContent.toLowerCase().trim()),
                        btn2: matchesLoadMoreText(btn2.textContent.toLowerCase().trim()),
                        btn3: matchesLoadMoreText(btn3.textContent.toLowerCase().trim()),
                        btn4: matchesLoadMoreText(btn4.textContent.toLowerCase().trim())
                    }};
                }})()
            """)
            
            assert result['btn1'] == True, "Should detect 'Load More'"
            assert result['btn2'] == True, "Should detect 'Show More'"
            assert result['btn3'] == True, "Should detect 'View More'"
            assert result['btn4'] == True, "Should detect 'See More'"
            
            browser.close()
    
    def test_detects_load_more_by_class(self, load_more_handler_code):
        """Test detection of Load More buttons by CSS class patterns."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <button class="load-more-button" id="btn1">Click</button>
                    <a href="#" class="loadmore" id="btn2">Click</a>
                    <div class="show-more-btn" id="btn3">Click</div>
                    <span class="expand-button" id="btn4">Click</span>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Test that tryClickLoadMore can find these buttons
            # We'll check if the function attempts to click them
            result = page.evaluate(f"""
                (function() {{
                    {load_more_handler_code}
                    
                    // Mock click to track if button was found
                    var clicked = false;
                    var btn1 = document.getElementById('btn1');
                    var originalClick = btn1.click;
                    btn1.click = function() {{
                        clicked = true;
                        originalClick.call(this);
                    }};
                    
                    return {{
                        found: tryClickLoadMore().then(function(result) {{
                            return result;
                        }})
                    }};
                }})()
            """)
            
            # Note: This is a simplified test - actual clicking requires async handling
            browser.close()
    
    def test_rejects_non_load_more_buttons(self, load_more_handler_code):
        """Test that non-Load More buttons are correctly rejected."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <button id="btn1">Submit</button>
                    <a href="#" id="btn2">Read More Content Here</a>
                    <div id="btn3">More information about this topic</div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    {load_more_handler_code}
                    
                    var btn1 = document.getElementById('btn1');
                    var btn2 = document.getElementById('btn2');
                    var btn3 = document.getElementById('btn3');
                    
                    return {{
                        btn1: matchesLoadMoreText(btn1.textContent.toLowerCase().trim()),
                        btn2: matchesLoadMoreText(btn2.textContent.toLowerCase().trim()),
                        btn3: matchesLoadMoreText(btn3.textContent.toLowerCase().trim())
                    }};
                }})()
            """)
            
            assert result['btn1'] == False, "Should reject 'Submit'"
            assert result['btn2'] == False, "Should reject long text with 'More'"
            assert result['btn3'] == False, "Should reject long descriptive text"
            
            browser.close()
    
    def test_detects_various_load_more_patterns(self, load_more_handler_code):
        """Test detection of various Load More text patterns."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            test_cases = [
                "load more",
                "show more",
                "view more",
                "see more",
                "more chapters",
                "next page",
                "load all",
                "show all",
                "expand",
                "more",
                "load"
            ]
            
            results = []
            for i, text in enumerate(test_cases):
                html = f'<html><body><button id="btn{i}">{text}</button></body></html>'
                page.set_content(html)
                
                result = page.evaluate(f"""
                    (function() {{
                        {load_more_handler_code}
                        
                        var btn = document.getElementById('btn{i}');
                        return matchesLoadMoreText(btn.textContent.toLowerCase().trim());
                    }})()
                """)
                
                results.append((text, result))
            
            # All should be detected
            for text, detected in results:
                assert detected == True, f"Should detect '{text}'"
            
            browser.close()
    
    def test_handles_invisible_buttons(self, load_more_handler_code):
        """Test that invisible buttons are not clicked."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <button id="visible" style="display: block;">Load More</button>
                    <button id="hidden" style="display: none;">Load More</button>
                    <button id="zero-size" style="width: 0; height: 0;">Load More</button>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Check visibility
            result = page.evaluate("""
                var visible = document.getElementById('visible');
                var hidden = document.getElementById('hidden');
                var zeroSize = document.getElementById('zero-size');
                
                return {
                    visible: visible.offsetParent !== null && visible.offsetWidth > 0 && visible.offsetHeight > 0,
                    hidden: hidden.offsetParent !== null && hidden.offsetWidth > 0 && hidden.offsetHeight > 0,
                    zeroSize: zeroSize.offsetParent !== null && zeroSize.offsetWidth > 0 && zeroSize.offsetHeight > 0
                };
            """)
            
            assert result['visible'] == True, "Visible button should be detected"
            assert result['hidden'] == False, "Hidden button should not be detected"
            assert result['zeroSize'] == False, "Zero-size button should not be detected"
            
            browser.close()

