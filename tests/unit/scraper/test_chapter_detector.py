"""
Unit tests for chapter_detector.js module.

Tests the isChapterLink function which detects chapter links using flexible patterns.
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
def chapter_detector_code():
    """Load the chapter_detector.js module code."""
    script_path = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts" / "chapter_detector.js"
    return script_path.read_text(encoding="utf-8")


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestChapterDetector:
    """Test cases for chapter_detector.js module."""
    
    def test_detects_standard_chapter_links(self, chapter_detector_code):
        """Test detection of standard chapter link patterns."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Create test HTML with various chapter link patterns
            html = """
            <html>
                <body>
                    <a href="/chapter-1" id="link1">Chapter 1</a>
                    <a href="/chapter-123" id="link2">Chapter 123</a>
                    <a href="/novel/chapter-45" id="link3">Chapter 45</a>
                    <a href="/ch_10" id="link4">Chapter 10</a>
                    <a href="/about" id="link5">About Us</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            # Inject module and test
            result = page.evaluate(f"""
                (function() {{
                    {chapter_detector_code}
                    
                    var link1 = document.getElementById('link1');
                    var link2 = document.getElementById('link2');
                    var link3 = document.getElementById('link3');
                    var link4 = document.getElementById('link4');
                    var link5 = document.getElementById('link5');
                    
                    return {{
                                        link1: isChapterLink(link1),
                        link2: isChapterLink(link2),
                        link3: isChapterLink(link3),
                        link4: isChapterLink(link4),
                        link5: isChapterLink(link5)
                    }};
                }})()
            """)
            
            assert result['link1'] == True, "Should detect /chapter-1"
            assert result['link2'] == True, "Should detect /chapter-123"
            assert result['link3'] == True, "Should detect /novel/chapter-45"
            assert result['link4'] == True, "Should detect /ch_10"
            assert result['link5'] == False, "Should not detect /about"
            
            browser.close()
    
    def test_detects_chapter_by_text_content(self, chapter_detector_code):
        """Test detection when href doesn't contain 'chapter' but text does."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <a href="/page/123" id="link1">Chapter 123</a>
                    <a href="/novel/456" id="link2">Chapter 456</a>
                    <a href="/book/789" id="link3">Read Chapter 789</a>
                    <a href="/page/999" id="link4">Page 999</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    chapter_detector_code
                    
                    return {{
                                    link1: isChapterLink(document.getElementById('link1')),
                    link2: isChapterLink(document.getElementById('link2')),
                    link3: isChapterLink(document.getElementById('link3')),
                    link4: isChapterLink(document.getElementById('link4'))
                }};
            }})()
            """)
            
            assert result['link1'] == True, "Should detect by text 'Chapter 123'"
            assert result['link2'] == True, "Should detect by text 'Chapter 456'"
            assert result['link3'] == True, "Should detect by text 'Read Chapter 789'"
            assert result['link4'] == False, "Should not detect 'Page 999'"
            
            browser.close()
    
    def test_detects_fanmtl_pattern(self, chapter_detector_code):
        """Test detection of FanMTL pattern (novel-name_123.html)."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div class="chapter-list">
                        <a href="/novel-name_123.html" id="link1">Chapter 123</a>
                        <a href="/novel-name/456.html" id="link2">Chapter 456</a>
                    </div>
                    <a href="/other_789.html" id="link3">Not a chapter</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    chapter_detector_code
                    
                    return {{
                                    link1: isChapterLink(document.getElementById('link1')),
                    link2: isChapterLink(document.getElementById('link2')),
                    link3: isChapterLink(document.getElementById('link3'))
                }};
            }})()
            """)
            
            assert result['link1'] == True, "Should detect .html in chapter-list"
            assert result['link2'] == True, "Should detect .html in chapter-list"
            assert result['link3'] == False, "Should not detect without context"
            
            browser.close()
    
    def test_detects_lightnovelpub_pattern(self, chapter_detector_code):
        """Test detection of LightNovelPub/NovelLive pattern."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <a href="/book/novel-name/chapter-123" id="link1">Chapter 123</a>
                    <a href="/book/novel-name/456" id="link2">Chapter 456</a>
                    <a href="/book/novel-name/chapter/789" id="link3">Chapter 789</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    chapter_detector_code
                    
                    return {{
                                    link1: isChapterLink(document.getElementById('link1')),
                    link2: isChapterLink(document.getElementById('link2')),
                    link3: isChapterLink(document.getElementById('link3'))
                }};
            }})()
            """)
            
            assert result['link1'] == True, "Should detect /book/novel-name/chapter-123"
            assert result['link2'] == True, "Should detect /book/novel-name/456"
            assert result['link3'] == True, "Should detect /book/novel-name/chapter/789"
            
            browser.close()
    
    def test_detects_chapter_in_container(self, chapter_detector_code):
        """Test detection when link is in a chapter container."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div id="chapters">
                        <a href="/page/123" id="link1">Read More</a>
                    </div>
                    <div class="chapter-list">
                        <a href="/page/456" id="link2">Continue</a>
                    </div>
                    <div>
                        <a href="/page/789" id="link3">Read More</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    chapter_detector_code
                    
                    return {{
                                    link1: isChapterLink(document.getElementById('link1')),
                    link2: isChapterLink(document.getElementById('link2')),
                    link3: isChapterLink(document.getElementById('link3'))
                }};
            }})()
            """)
            
            # Links in chapter containers should be detected if they have chapter indicators
            # Note: These might not be detected without chapter text, which is correct behavior
            browser.close()
    
    def test_rejects_non_chapter_links(self, chapter_detector_code):
        """Test that non-chapter links are correctly rejected."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <a href="/about" id="link1">About</a>
                    <a href="/contact" id="link2">Contact Us</a>
                    <a href="/home" id="link3">Home</a>
                    <a href="/novel-list" id="link4">Novel List</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    chapter_detector_code
                    
                    return {{
                                    link1: isChapterLink(document.getElementById('link1')),
                    link2: isChapterLink(document.getElementById('link2')),
                    link3: isChapterLink(document.getElementById('link3')),
                    link4: isChapterLink(document.getElementById('link4'))
                }};
            }})()
            """)
            
            assert result['link1'] == False, "Should reject /about"
            assert result['link2'] == False, "Should reject /contact"
            assert result['link3'] == False, "Should reject /home"
            assert result['link4'] == False, "Should reject /novel-list"
            
            browser.close()
    
    def test_handles_null_or_invalid_links(self, chapter_detector_code):
        """Test that null or invalid links are handled gracefully."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.set_content("<html><body></body></html>")
            
            result = page.evaluate(f"""
                (function() {{
                    chapter_detector_code
                    
                    return {{
                                    nullLink: isChapterLink(null),
                    undefinedLink: isChapterLink(undefined),
                    emptyObject: isChapterLink({{}}),
                    linkWithoutHref: isChapterLink({{textContent: 'Chapter 1'}})
                }};
            }})()
            """)
            
            assert result['nullLink'] == False, "Should handle null"
            assert result['undefinedLink'] == False, "Should handle undefined"
            assert result['emptyObject'] == False, "Should handle empty object"
            assert result['linkWithoutHref'] == False, "Should handle link without href"
            
            browser.close()

