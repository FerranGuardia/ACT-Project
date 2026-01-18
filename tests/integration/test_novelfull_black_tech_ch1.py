import re
import unittest

from scraper.novel_scraper import NovelScraper


class TestNovelFullBlackTechChapterOne(unittest.TestCase):
    def test_chapter_one_scrape_has_no_notes_noise(self):
        toc_url = "https://novelfull.net/black-tech-internet-cafe-system.html"
        scraper = NovelScraper(base_url="https://novelfull.net")

        chapter_urls = scraper.get_chapter_urls(toc_url)
        self.assertTrue(chapter_urls, "No chapter URLs returned from TOC")

        chapter_url = chapter_urls[0]
        content, title, error = scraper.scrape_chapter(chapter_url)

        self.assertIsNone(error, f"Scrape error: {error}")
        self.assertIsNotNone(content, "Scrape returned no content")
        self.assertGreater(len(content), 500, "Content unexpectedly short")

        tokens = re.findall(r"\b\w+\b", content.lower())
        notes_count = sum(1 for token in tokens if token == "notes")
        notes_ratio = notes_count / max(len(tokens), 1)
        self.assertLess(
            notes_ratio,
            0.02,
            f"Notes token ratio too high ({notes_ratio:.2%})",
        )

        notes_spam = re.search(r"(?:\b\w\b\s+notes\s+){8,}\b\w\b", content.lower())
        self.assertIsNone(notes_spam, "Detected repeated 'notes' between single letters")

        single_letter_ratio = len([t for t in tokens if len(t) == 1]) / max(len(tokens), 1)
        self.assertLess(
            single_letter_ratio,
            0.2,
            f"Single-letter token ratio too high ({single_letter_ratio:.2%})",
        )


if __name__ == "__main__":
    unittest.main()
