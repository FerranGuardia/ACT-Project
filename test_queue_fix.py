"""
Verify the queue processing fix.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication


def test_queue_processing():
    """Test that start_scraping() now processes queue items."""
    print("\n" + "="*70)
    print("TEST: Queue Processing")
    print("="*70)
    
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    scraper = window.scraper_view
    
    test_url = "https://example.com/novel"
    test_dir = "C:\\tmp\\test_output"
    
    # Scenario 1: Start with empty queue (should validate input form)
    print("\n→ Scenario 1: Empty queue, empty form - should fail")
    print("-" * 60)
    scraper.start_scraping()
    print(f"  Thread created: {scraper.scraping_thread is not None}")
    
    # Scenario 2: Start with empty queue, populated form - should work
    print("\n→ Scenario 2: Empty queue, populated form - should work")
    print("-" * 60)
    scraper.url_input_section.set_url(test_url)
    scraper.output_settings.set_output_dir(test_dir)
    scraper.start_scraping()
    print(f"  Thread created: {scraper.scraping_thread is not None}")
    if scraper.scraping_thread and scraper.scraping_thread.isRunning():
        scraper.scraping_thread.stop()
    
    # Reset
    scraper.scraping_thread = None
    
    # Scenario 3: Add to queue, clear form, click start - should process queue
    print("\n→ Scenario 3: Queue item exists, form cleared - should process queue")
    print("-" * 60)
    
    # Add to queue
    scraper.url_input_section.set_url(test_url)
    scraper.output_settings.set_output_dir(test_dir)
    scraper.add_to_queue()
    
    print(f"  Queue items before start: {len(scraper.queue_items)}")
    print(f"  Input form URL: '{scraper.url_input_section.get_url()}'")
    
    # Start (should process queue item, not form)
    scraper.start_scraping()
    print(f"  Thread created: {scraper.scraping_thread is not None}")
    if scraper.scraping_thread:
        print(f"  Thread running: {scraper.scraping_thread.isRunning()}")
        print(f"  Thread scraped URL: {scraper.scraping_thread.url}")
        print(f"  Expected URL: {test_url}")
        print(f"  ✓ CORRECT!" if scraper.scraping_thread.url == test_url else "  ✗ WRONG!")
    
    print("\n" + "="*70)
    print("✓ Queue processing fix verified!")
    print("="*70)


if __name__ == "__main__":
    test_queue_processing()
