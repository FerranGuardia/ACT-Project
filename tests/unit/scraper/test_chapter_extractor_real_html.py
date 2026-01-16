"""Real-HTML tests for ChapterExtractor.

These tests exercise the actual parsing + filtering logic using static HTML.
They intentionally avoid network and excessive mocking.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.scraper.extractors.chapter_extractor import ChapterExtractor


@dataclass
class _FakeResponse:
    status_code: int
    content: bytes
    url: str
    headers: dict[str, str] | None = None
    history: list[object] | None = None
    text: str | None = None

    def __post_init__(self) -> None:
        if self.headers is None:
            self.headers = {}
        if self.history is None:
            self.history = []
        if self.text is None:
            # Used only in some error paths (e.g., 403 preview)
            self.text = self.content.decode("utf-8", errors="ignore")


class _FakeSession:
    def __init__(self, response: _FakeResponse):
        self._response = response
        self.calls: list[tuple[str, float, bool]] = []

    def get(self, url: str, timeout: float, allow_redirects: bool = True):
        self.calls.append((url, timeout, allow_redirects))
        return self._response


def _make_extractor(base_url: str = "https://example.com") -> ChapterExtractor:
    # delay=0 to keep tests fast and deterministic
    return ChapterExtractor(base_url=base_url, timeout=1, delay=0.0)


def test_scrape_with_requests_extracts_title_and_content_from_real_html():
    extractor = _make_extractor()

    html = """<!DOCTYPE html>
<html>
  <head><title>Chapter 12: The Beginning - Some Novel</title></head>
  <body>
    <h1 class="chapter-title">Chapter 12: The Beginning</h1>
    <div class="chapter-content">
      <p>This is the first paragraph of the chapter content, long enough to keep.</p>
      <p>Next Chapter » click here to continue reading</p>
      <p>This is the second paragraph of the chapter content, also long enough to keep.</p>
      <div>This is the second paragraph of the chapter content, also long enough to keep.</div>
    </div>
  </body>
</html>"""

    chapter_url = "https://example.com/novel/chapter-12"
    response = _FakeResponse(
        status_code=200,
        content=html.encode("utf-8"),
        url=chapter_url,
        headers={"Content-Encoding": ""},
        history=[],
    )

    extractor._session = _FakeSession(response)

    content, title, error = extractor._scrape_with_requests(chapter_url)

    assert error is None
    assert title == "The Beginning"

    assert "first paragraph" in content
    assert "second paragraph" in content

    # Navigation should be filtered/cleaned out
    assert "Next Chapter" not in content

    # Duplicate content should not show twice
    assert content.count("second paragraph") == 1


def test_extract_title_falls_back_to_url_chapter_number_when_no_title_in_html():
    extractor = _make_extractor()

    html = """<!DOCTYPE html>
<html>
  <head><title>Untitled</title></head>
  <body>
    <div class="chapter-content"><p>This is a paragraph with enough characters to extract.</p></div>
  </body>
</html>"""

    chapter_url = "https://example.com/story/chapter-45"
    response = _FakeResponse(
        status_code=200,
        content=html.encode("utf-8"),
        url=chapter_url,
        headers={"Content-Encoding": ""},
        history=[],
    )

    extractor._session = _FakeSession(response)

    content, title, error = extractor._scrape_with_requests(chapter_url)

    assert error is None
    assert title == "Chapter 45"
    assert "enough characters" in content


def test_extract_content_prefers_leaf_div_text_when_no_p_tags_present():
    extractor = _make_extractor()

    html = """<!DOCTYPE html>
<html>
  <body>
    <h1>Chapter 1: Div-only content</h1>
    <div class="chapter-content">
      <div>This is a div that contains the actual chapter content and is long enough.</div>
      <div>Previous Chapter - should not be included because it looks like navigation</div>
    </div>
  </body>
</html>"""

    chapter_url = "https://example.com/chapter/1"
    response = _FakeResponse(
        status_code=200,
        content=html.encode("utf-8"),
        url=chapter_url,
        headers={"Content-Encoding": ""},
        history=[],
    )

    extractor._session = _FakeSession(response)

    content, title, error = extractor._scrape_with_requests(chapter_url)

    assert error is None
    assert title == "Div-only content"
    assert "actual chapter content" in content
    assert "Previous Chapter" not in content


def test_scrape_with_requests_blocks_cross_site_redirect_targets(monkeypatch: pytest.MonkeyPatch):
    extractor = _make_extractor(base_url="https://example.com")

    # Make redirect validation deterministic (avoid DNS resolution in validate_url).
    from src.scraper.extractors import \
        chapter_extractor as chapter_extractor_module

    def _always_valid(url: str):
        return True, url

    monkeypatch.setattr(chapter_extractor_module, "validate_url", _always_valid)

    html = """<!DOCTYPE html><html><body>
      <div class=\"chapter-content\"><p>This is a paragraph with enough characters to extract.</p></div>
    </body></html>"""

    chapter_url = "https://example.com/chapter/1"

    response = _FakeResponse(
        status_code=200,
        content=html.encode("utf-8"),
        url="https://evil.example/redirected",
        headers={"Content-Encoding": ""},
        history=[object()],
    )

    extractor._session = _FakeSession(response)

    content, title, error = extractor._scrape_with_requests(chapter_url)

    assert content is None
    assert title is None
    assert error == "Blocked redirect to a different site"


def test_scrape_with_requests_ignores_non_http_redirect_url_values():
    extractor = _make_extractor(base_url="https://example.com")

    html = """<!DOCTYPE html><html><body>
      <div class=\"chapter-content\"><p>This is a paragraph with enough characters to extract.</p></div>
    </body></html>"""

    chapter_url = "https://example.com/chapter/1"

    response = _FakeResponse(
        status_code=200,
        content=html.encode("utf-8"),
        url="javascript:alert(1)",
        headers={"Content-Encoding": ""},
        history=[object()],
    )

    extractor._session = _FakeSession(response)

    content, title, error = extractor._scrape_with_requests(chapter_url)

    assert error is None
    assert title == "Chapter 1"
    assert content is not None
