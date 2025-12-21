"""
Scraping Thread - Handles background scraping operations.
"""

import os
from typing import List, Dict

from PySide6.QtCore import QThread, Signal

from core.logger import get_logger
from scraper import GenericScraper

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
        self.should_stop = False
        self.is_paused = False
    
    def stop(self):
        """Stop the scraping operation."""
        self.should_stop = True
    
    def pause(self):
        """Pause the scraping operation."""
        self.is_paused = True
    
    def resume(self):
        """Resume the scraping operation."""
        self.is_paused = False
    
    def run(self):
        """Run the scraping operation."""
        try:
            self.status.emit("Initializing scraper...")
            scraper = GenericScraper(self.url)
            
            # Get chapter URLs
            self.status.emit("Fetching chapter URLs...")
            chapter_urls = scraper.get_chapter_urls(self.url)
            
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
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Scrape each chapter
            for idx, chapter_url in enumerate(selected_urls):
                if self.should_stop:
                    self.status.emit("Stopped by user")
                    self.finished.emit(False, "Scraping stopped")
                    return
                
                while self.is_paused and not self.should_stop:
                    self.status.emit("Paused...")
                    self.msleep(100)
                
                if self.should_stop:
                    break
                
                try:
                    self.status.emit(f"Scraping chapter {idx + 1}/{total}...")
                    content, title, error_msg = scraper.scrape_chapter(chapter_url)
                    
                    if content:
                        # Save chapter
                        chapter_num = idx + 1
                        filename = f"chapter_{chapter_num:04d}{self.file_format}"
                        filepath = os.path.join(self.output_dir, filename)
                        
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
            
            if not self.should_stop:
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
            start = self.chapter_selection.get('from', 1) - 1
            end = self.chapter_selection.get('to', len(chapter_urls))
            return chapter_urls[start:end]
        elif selection_type == 'specific':
            indices = self.chapter_selection.get('chapters', [])
            return [chapter_urls[i - 1] for i in indices if 1 <= i <= len(chapter_urls)]
        
        return chapter_urls

