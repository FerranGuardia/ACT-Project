"""
Unit tests for container_finder.js module.

Tests the findChapterContainer function which finds the appropriate container for scrolling.
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
def container_finder_code():
    """Load the container_finder.js module code."""
    script_path = Path(__file__).parent.parent.parent.parent / "src" / "scraper" / "playwright_scripts" / "container_finder.js"
    return script_path.read_text(encoding="utf-8")


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestContainerFinder:
    """Test cases for container_finder.js module."""
    
    def test_finds_chapter_specific_container(self, container_finder_code):
        """Test finding chapter-specific containers."""
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
                (function() {{
                    {container_finder_code}
                    
                    var container = findChapterContainer();
                    return container.id;
                }})()
            """)
            
            assert result == "chapters", "Should find #chapters container"
            
            browser.close()
    
    def test_finds_chapter_list_class(self, container_finder_code):
        """Test finding container by .chapter-list class."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div class="chapter-list">
                        <a href="/chapter-1">Chapter 1</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    {container_finder_code}
                    
                    var container = findChapterContainer();
                    return container.className;
                }})()
            """)
            
            assert "chapter-list" in result, "Should find .chapter-list container"
            
            browser.close()
    
    def test_falls_back_to_general_content_container(self, container_finder_code):
        """Test fallback to general content containers."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <main>
                        <a href="/chapter-1">Chapter 1</a>
                    </main>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    {container_finder_code}
                    
                    var container = findChapterContainer();
                    return container.tagName.toLowerCase();
                }})()
            """)
            
            assert result == "main", "Should fall back to <main> container"
            
            browser.close()
    
    def test_falls_back_to_body(self, container_finder_code):
        """Test final fallback to document.body."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <a href="/chapter-1">Chapter 1</a>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    {container_finder_code}
                    
                    var container = findChapterContainer();
                    return container === document.body;
                }})()
            """)
            
            assert result == True, "Should fall back to document.body"
            
            browser.close()
    
    def test_prioritizes_chapter_containers_over_general(self, container_finder_code):
        """Test that chapter-specific containers are prioritized over general ones."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <main>
                        <div id="chapters">
                            <a href="/chapter-1">Chapter 1</a>
                        </div>
                    </main>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    {container_finder_code}
                    
                    var container = findChapterContainer();
                    return container.id;
                }})()
            """)
            
            assert result == "chapters", "Should prioritize #chapters over <main>"
            
            browser.close()
    
    def test_handles_multiple_chapter_containers(self, container_finder_code):
        """Test behavior when multiple chapter containers exist."""
        with sync_playwright() as p:  # type: ignore[attr-defined]
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            html = """
            <html>
                <body>
                    <div class="chapter-list">
                        <a href="/chapter-1">Chapter 1</a>
                    </div>
                    <div id="chapters">
                        <a href="/chapter-2">Chapter 2</a>
                    </div>
                </body>
            </html>
            """
            
            page.set_content(html)
            
            result = page.evaluate(f"""
                (function() {{
                    {container_finder_code}
                    
                    var container = findChapterContainer();
                    // querySelector returns first match, so it should be .chapter-list
                    return container.className || container.id;
                }})()
            """)
            
            # Should find one of them (querySelector returns first match)
            assert "chapter" in result.lower() or result == "chapters", "Should find a chapter container"
            
            browser.close()

