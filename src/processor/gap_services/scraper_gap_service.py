"""
Scraper-specific gap detection service.

Handles gap detection for text file operations in the scraper view.
Only checks for missing text files and provides functionality to fill gaps
through scraping operations.
"""

from typing import List, Optional, Dict, Any
from core.logger import get_logger
from core.activity_console import get_activity_console, ActivityCategory
from ..gap_detector import GapDetector

logger = get_logger("processor.gap_services.scraper_gap")


class ScraperGapService:
    """
    Gap detection service specifically for scraper view operations.

    This service only checks for missing text files (.txt) and provides
    functionality to fill gaps by re-scraping missing chapters.
    """

    def __init__(self, project_manager, file_manager, scrape_service=None):
        """
        Initialize scraper gap service.

        Args:
            project_manager: ProjectManager instance
            file_manager: FileManager instance
            scrape_service: Optional ScrapeService for gap filling
        """
        self.project_manager = project_manager
        self.file_manager = file_manager
        self.scrape_service = scrape_service
        self.gap_detector = GapDetector(project_manager, file_manager)

    def detect_text_gaps(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None
    ) -> List[int]:
        """
        Detect missing text files in the specified chapter range.

        Args:
            start_from: Starting chapter number (1-indexed)
            end_chapter: Ending chapter number (None = check all chapters)

        Returns:
            List of chapter numbers with missing text files
        """
        logger.debug(f"Detecting text file gaps from chapter {start_from} to {end_chapter or 'end'}")

        missing_chapters = self.gap_detector.detect_missing_chapters(
            start_from=start_from,
            end_chapter=end_chapter,
            check_audio=False,  # Only text files in scraper view
            check_text=True
        )

        if missing_chapters:
            activity_console = get_activity_console()
            activity_console.log_gap_found(missing_chapters, "scraper_gap_detection")

            logger.info(
                f"🔍 Scraper gap detection: Found {len(missing_chapters)} missing text files "
                f"in range {start_from}-{end_chapter or 'all'}"
            )
        else:
            logger.debug(f"✓ No text file gaps detected in range {start_from}-{end_chapter or 'all'}")

        return missing_chapters

    def get_gap_report(
        self,
        start_from: int = 1,
        end_chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get detailed gap detection report for text files.

        Args:
            start_from: Starting chapter number
            end_chapter: Ending chapter number

        Returns:
            Dictionary with gap detection results
        """
        gap_report = self.gap_detector.detect_and_report_gaps(
            start_from=start_from,
            end_chapter=end_chapter,
            check_audio=False,
            check_text=True
        )

        return {
            'missing_text_files': gap_report['missing_chapters'],
            'total_checked': gap_report['total_checked'],
            'range_start': gap_report['range_start'],
            'range_end': gap_report['range_end'],
            'gaps_found': gap_report['gaps_found'],
            'gap_type': 'text_files_only'
        }

    def can_fill_gaps(self) -> bool:
        """
        Check if this service can automatically fill detected gaps.

        Returns:
            True if gaps can be filled automatically, False otherwise
        """
        return self.scrape_service is not None

    def fill_gaps(
        self,
        missing_chapters: List[int],
        toc_url: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Attempt to fill detected gaps by re-scraping missing chapters.

        Args:
            missing_chapters: List of chapter numbers to fill
            toc_url: Table of contents URL for scraping
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with filling results
        """
        if not self.can_fill_gaps():
            return {
                'success': False,
                'error': 'No scrape service available for gap filling',
                'filled_chapters': [],
                'failed_chapters': missing_chapters
            }

        logger.info(f"Attempting to fill {len(missing_chapters)} text gaps via scraping")

        filled_chapters = []
        failed_chapters = []

        try:
            # Get all chapter URLs
            all_urls = self.scrape_service.get_chapter_urls(toc_url)

            # Create mapping of chapter number to URL
            chapter_manager = self.project_manager.get_chapter_manager()
            if not chapter_manager:
                return {
                    'success': False,
                    'error': 'Chapter manager not available',
                    'filled_chapters': [],
                    'failed_chapters': missing_chapters
                }

            all_chapters = chapter_manager.get_all_chapters()
            url_mapping = {}

            for chapter in all_chapters:
                if chapter.number in missing_chapters:
                    # Find corresponding URL (this is a simplified mapping)
                    # In practice, you'd need better URL-chapter mapping
                    url_index = chapter.number - 1  # Assuming 1-indexed chapters
                    if 0 <= url_index < len(all_urls):
                        url_mapping[chapter.number] = all_urls[url_index]

            # Scrape missing chapters
            for chapter_num in missing_chapters:
                if chapter_num in url_mapping:
                    try:
                        title, content, _ = self.scrape_service.scrape_chapter(url_mapping[chapter_num])

                        if content:
                            # Save to text file
                            self.file_manager.save_text_file(chapter_num, content)
                            filled_chapters.append(chapter_num)

                            if progress_callback:
                                progress_callback(len(filled_chapters), len(missing_chapters))
                        else:
                            failed_chapters.append(chapter_num)

                    except Exception as e:
                        logger.error(f"Failed to scrape chapter {chapter_num}: {e}")
                        failed_chapters.append(chapter_num)
                else:
                    failed_chapters.append(chapter_num)

        except Exception as e:
            logger.error(f"Error during gap filling: {e}")
            return {
                'success': False,
                'error': str(e),
                'filled_chapters': filled_chapters,
                'failed_chapters': failed_chapters + (missing_chapters[len(filled_chapters):] if len(filled_chapters) < len(missing_chapters) else [])
            }

        success = len(failed_chapters) == 0
        return {
            'success': success,
            'filled_chapters': filled_chapters,
            'failed_chapters': failed_chapters,
            'total_attempted': len(missing_chapters)
        }


__all__ = ["ScraperGapService"]