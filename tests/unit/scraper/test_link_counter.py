"""
Unit tests for link_counter.js module.

Tests the countChapterLinks and getChapterLinks functions.
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
def link_counter_code():
    """Load the link_counter.js module code."""
    script_path = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts" / "link_counter.js"
    return script_path.read_text(encoding="utf-8")


@pytest.fixture
def chapter_detector_code():
    """Load the chapter_detector.js module code (dependency)."""
    script_path = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts" / "chapter_detector.js"
    return script_path.read_text(encoding="utf-8")


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestLinkCounter:
    """Test cases for link_counter.js module."""
    
    def test_counts_chapter_links(self, link_counter_code, chapter_detector_code):
        """Test counting chapter links in the DOM."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <a href="/chapter-1">Chapter 1</a>
                    <a href="/chapter-2">Chapter 2</a>
                    <a href="/chapter-3">Chapter 3</a>
                    <a href="/about">About</a>
                    <a href="/contact">Contact</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {chapter_detector_code}
                {link_counter_code}
                
                return countChapterLinks(isChapterLink);
            """)
            
            assert result == 3, "Should count 3 chapter links"
            
            browser.close()
    
    def test_counts_zero_when_no_chapters(self, link_counter_code, chapter_detector_code):
        """Test counting when no chapter links exist."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <a href="/about">About</a>
                    <a href="/contact">Contact</a>
                    <a href="/home">Home</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {chapter_detector_code}
                {link_counter_code}
                
                return countChapterLinks(isChapterLink);
            """)
            
            assert result == 0, "Should count 0 chapter links"
            
            browser.close()
    
    def test_get_chapter_links_returns_array(self, link_counter_code, chapter_detector_code):
        """Test that getChapterLinks returns an array of link elements."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <a href="/chapter-1" id="ch1">Chapter 1</a>
                    <a href="/chapter-2" id="ch2">Chapter 2</a>
                    <a href="/about" id="about">About</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                {chapter_detector_code}
                {link_counter_code}
                
                var links = getChapterLinks(isChapterLink);
                return {{
                            count: links.length,
                    hasCh1: links.some(link => link.id === 'ch1'),
                    hasCh2: links.some(link => link.id === 'ch2'),
                    hasAbout: links.some(link => link.id === 'about')
                }};
            }})()
            """)
            
            assert result['count'] == 2, "Should return 2 chapter links"
            assert result['hasCh1'] == True, "Should include chapter 1"
            assert result['hasCh2'] == True, "Should include chapter 2"
            assert result['hasAbout'] == False, "Should not include about link"
            
            browser.close()
    
    def test_counts_dynamic_chapter_links(self, link_counter_code, chapter_detector_code):
        """Test counting when chapter links are added dynamically."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="container">
                        <a href="/chapter-1">Chapter 1</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Count initial links
            initial_count = page.evaluate(f"""
                {chapter_detector_code}
                {link_counter_code}
                
                return countChapterLinks(isChapterLink);
            """)
            
            # Add more links dynamically
            page.evaluate("""
                var container = document.getElementById('container');
                container.innerHTML += '<a href="/chapter-2">Chapter 2</a>';
                container.innerHTML += '<a href="/chapter-3">Chapter 3</a>';
            """)
            
            # Count again
            final_count = page.evaluate(f"""
                {chapter_detector_code}
                {link_counter_code}
                
                return countChapterLinks(isChapterLink);
            """)
            
            assert initial_count == 1, "Initial count should be 1"
            assert final_count == 3, "Final count should be 3 after adding links"
            
            browser.close()
    
    def test_handles_empty_dom(self, link_counter_code, chapter_detector_code):
        """Test counting when DOM has no links."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.set_content("<html><body></body></html>")
            
            result = page.evaluate(f"""
                {chapter_detector_code}
                {link_counter_code}
                
                return {{
                            count: countChapterLinks(isChapterLink),
                    links: getChapterLinks(isChapterLink).length
                }};
            }})()
            """)
            
            assert result['count'] == 0, "Should return 0 for empty DOM"
            assert result['links'] == 0, "Should return empty array for empty DOM"
            
            browser.close()

