"""
Scraping Thread - Handles background scraping operations.
"""

import os
from threading import Event
from typing import Dict, List
from urllib.parse import urlparse

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger
from scraper import GenericScraper
from utils.validation import validate_directory_path, validate_url

logger = get_logger("ui.scraper_view.scraping_thread")


class ScrapingThread(QThread):
    """Thread for running scraping operations without blocking UI."""
    
    progress = Signal(int)  # Progress percentage
    status = Signal(str)  # Status message
    finished = Signal(bool, str)  # Success, message
    file_created = Signal(str)  # File path
    
    def __init__(self, url: str, chapter_selection: dict, output_dir: str, file_format: str):
        super().__init__()
        self.url = url
        self.chapter_selection = chapter_selection
        self.output_dir = output_dir
        self.file_format = file_format
        self.should_stop = Event()  # Thread-safe stop flag
        self.pause_event = Event()  # Thread-safe pause flag
        self.pause_event.set()  # Initially, not paused
        self._is_paused = False

    @property
    def is_paused(self) -> bool:
        """Whether the scraping thread is currently paused (UI-friendly flag)."""
        # Use the event as source of truth; keep _is_paused as a backup for clarity.
        try:
            return not self.pause_event.is_set()
        except Exception:
            return self._is_paused
    
    def stop(self):
        """Stop the scraping operation."""
        self.should_stop.set()
    
    def pause(self):
        """Pause the scraping operation."""
        self.pause_event.clear()
        self._is_paused = True
    
    def resume(self):
        """Resume the scraping operation."""
        self.pause_event.set()
        self._is_paused = False
    
    def run(self):
        """Run the scraping operation."""
        try:
            # Validate and sanitize URL (SSRF hardening)
            is_valid, clean_or_err = validate_url(self.url)
            if not is_valid:
                self.finished.emit(False, f"Invalid URL: {clean_or_err}")
                return
            clean_url = clean_or_err

            # Validate output directory (prevent unsafe paths)
            is_valid_dir, safe_dir_or_err = validate_directory_path(self.output_dir, allow_create=True)
            if not is_valid_dir:
                self.finished.emit(False, f"Invalid output directory: {safe_dir_or_err}")
                return
            safe_output_dir = safe_dir_or_err

            # Normalize file format to a safe extension with leading dot
            fmt = (self.file_format or ".txt").strip().lower()
            if not fmt.startswith("."):
                fmt = "." + fmt
            if fmt not in {".txt", ".md", ".html", ".json"}:
                fmt = ".txt"
            self.file_format = fmt

            # Initialize scraper with base URL (not full TOC URL)
            parsed = urlparse(clean_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            self.status.emit("Initializing scraper...")
            scraper = GenericScraper(base_url)
            
            # Get chapter URLs
            self.status.emit("Fetching chapter URLs...")
            chapter_urls = scraper.get_chapter_urls(clean_url)
            
            if not chapter_urls:
                self.finished.emit(False, "No chapters found")
                return
            
            # Filter chapters based on selection
            selected_urls = self._filter_chapters(chapter_urls)
            total = len(selected_urls)
            
            if total == 0:
                self.finished.emit(False, "No chapters match selection criteria")
                return
            
            self.status.emit(f"Scraping {total} chapters...")
            
            # Create output directory
            os.makedirs(safe_output_dir, exist_ok=True)
            
            # Scrape each chapter
            for idx, chapter_url in enumerate(selected_urls):
                if self.should_stop.is_set():
                    self.status.emit("Stopped by user")
                    self.finished.emit(False, "Scraping stopped")
                    return
                
                # Wait if paused
                self.pause_event.wait()
                
                # Check again after waiting
                if self.should_stop.is_set():
                    break
                
                try:
                    self.status.emit(f"Scraping chapter {idx + 1}/{total}...")
                    content, _, error_msg = scraper.scrape_chapter(chapter_url)
                    
                    if content:
                        # Save chapter
                        chapter_num = idx + 1
                        filename = f"chapter_{chapter_num:04d}{self.file_format}"
                        filepath = os.path.join(safe_output_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        self.file_created.emit(filepath)
                    elif error_msg:
                        logger.warning(f"Failed to scrape chapter {idx + 1}: {error_msg}")
                    
                    progress = int((idx + 1) / total * 100)
                    self.progress.emit(progress)
                    
                except Exception as e:
                    logger.error(f"Error scraping chapter {idx + 1}: {e}")
                    self.status.emit(f"Error in chapter {idx + 1}: {str(e)}")
            
            if not self.should_stop.is_set():
                self.status.emit("Scraping completed!")
                self.finished.emit(True, f"Successfully scraped {total} chapters")
            else:
                self.finished.emit(False, "Scraping stopped")
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            self.finished.emit(False, f"Error: {str(e)}")
    
    def _filter_chapters(self, chapter_urls: List[str]) -> List[str]:
        """Filter chapters based on selection criteria."""
        selection_type = self.chapter_selection.get('type')
        
        if selection_type == 'all':
            return chapter_urls
        elif selection_type == 'range':
            # Support both legacy keys ('from'/'to') and normalized keys ('start'/'end')
            start_raw = self.chapter_selection.get('from', self.chapter_selection.get('start', 1))
            end_raw = self.chapter_selection.get('to', self.chapter_selection.get('end', len(chapter_urls)))
            start = int(start_raw) - 1 if start_raw else 0
            end = int(end_raw) if end_raw else len(chapter_urls)
            return chapter_urls[start:end]
        elif selection_type in ('specific', 'list'):
            indices = self.chapter_selection.get('chapters', self.chapter_selection.get('indices', []))
            return [chapter_urls[i - 1] for i in indices if 1 <= i <= len(chapter_urls)]
        
        return chapter_urls

