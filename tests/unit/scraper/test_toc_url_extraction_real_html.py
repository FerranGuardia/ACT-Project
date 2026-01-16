"""Fixture-based tests for TOC (table-of-contents) URL extraction.

Goal: validate the real parsing + validation logic for TOC pages without
hitting the network or Playwright.

We mock only the network fetch (`_fetch_with_retry`) and keep everything else real.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.scraper.strategies.html_parsing_strategy import HtmlParsingStrategy
from src.scraper.strategies.javascript_strategy import JavaScriptStrategy


@dataclass
class _FakeResponse:
    text: str


class _DummySessionManager:
    def get_session(self):
        raise AssertionError("Network access should not occur in these tests")

    def rate_limit(self):
        return None


@pytest.mark.asyncio
async def test_javascript_strategy_extracts_chapter_urls_from_script_array(monkeypatch: pytest.MonkeyPatch):
    strategy = JavaScriptStrategy(base_url="https://example.com", session_manager=_DummySessionManager())

    html = """<!doctype html>
<html>
  <head>
    <script>
      // Typical TOC JS payload
      var chapters = [
        "/novel/chapter-2.html",
        "/novel/chapter-1.html",
        "/about.html",
        "/novel/chapter-3.html",
        "/novel/chapter-2.html" // duplicate
      ];
    </script>
  </head>
  <body>toc</body>
</html>"""

    monkeypatch.setattr(strategy, "_fetch_with_retry", lambda *_args, **_kwargs: _FakeResponse(text=html))

    result = await strategy.detect("https://example.com/toc")

    assert result.error is None
    assert result.method == "javascript"

    # The strategy should normalize relative URLs to absolute and drop non-chapter links.
    assert set(result.urls) == {
        "https://example.com/novel/chapter-1.html",
        "https://example.com/novel/chapter-2.html",
        "https://example.com/novel/chapter-3.html",
    }

    # Coverage should reflect min/max chapter numbers found.
    assert result.coverage_range == (1, 3)

    # Should have some confidence if validation succeeded.
    assert result.confidence > 0.0
    assert result.validation_score > 0.0


@pytest.mark.asyncio
async def test_html_parsing_strategy_extracts_chapter_urls_from_anchor_tags(monkeypatch: pytest.MonkeyPatch):
    strategy = HtmlParsingStrategy(base_url="https://example.com", session_manager=_DummySessionManager())

    html = """<!doctype html>
<html>
  <body>
    <div id="toc">
      <ul class="chapter-list">
        <li><a href="/novel/chapter-1">Chapter 1 - Start</a></li>
        <li><a href="/novel/chapter-2">Chapter 2 - Continue</a></li>
        <li><a href="/novel/chapter-3">Chapter 3 - More</a></li>
        <li><a href="/novel/">Index</a></li>
        <li><a href="/contact">Contact</a></li>
      </ul>
    </div>
  </body>
</html>"""

    monkeypatch.setattr(strategy, "_fetch_with_retry", lambda *_args, **_kwargs: _FakeResponse(text=html))

    result = await strategy.detect("https://example.com/toc")

    assert result.error is None
    assert result.method == "html_parsing"

    assert result.urls == [
        "https://example.com/novel/chapter-1",
        "https://example.com/novel/chapter-2",
        "https://example.com/novel/chapter-3",
    ]

    assert result.coverage_range == (1, 3)
    assert result.confidence > 0.0
    assert result.validation_score > 0.0
