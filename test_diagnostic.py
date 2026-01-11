"""
Deeper diagnostics for the scraper start issue.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.logger import get_logger

logger = get_logger("diag_test")


def diagnose_start_scraping():
    """Diagnose why start_scraping doesn't create a thread."""
    print("\n" + "="*70)
    print("DIAGNOSTIC: Start Scraping Issue")
    print("="*70)
    
    from ui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication
    
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    scraper = window.scraper_view
    
    # Scenario 1: Start without any input
    print("\n→ SCENARIO 1: Calling start_scraping() with empty inputs")
    print("-" * 60)
    
    print("Input state:")
    print(f"  URL: '{scraper.url_input_section.get_url()}'")
    print(f"  Output dir: '{scraper.output_settings.get_output_dir()}'")
    
    print("\nValidation:")
    valid, error = scraper.handlers.validate_inputs(
        scraper.url_input_section,
        scraper.chapter_selection_section,
        scraper.output_settings
    )
    print(f"  Valid: {valid}")
    print(f"  Error: {error}")
    
    scraper.start_scraping()
    print(f"  Thread created: {scraper.scraping_thread is not None}")
    
    # Scenario 2: Set inputs then start
    print("\n→ SCENARIO 2: Set inputs then call start_scraping()")
    print("-" * 60)
    
    test_url = "https://example.com/novel"
    test_dir = "C:\\tmp\\test_output"
    
    scraper.url_input_section.set_url(test_url)
    scraper.output_settings.set_output_dir(test_dir)
    
    print("Input state:")
    print(f"  URL: '{scraper.url_input_section.get_url()}'")
    print(f"  Output dir: '{scraper.output_settings.get_output_dir()}'")
    
    print("\nValidation:")
    valid, error = scraper.handlers.validate_inputs(
        scraper.url_input_section,
        scraper.chapter_selection_section,
        scraper.output_settings
    )
    print(f"  Valid: {valid}")
    print(f"  Error: {error}")
    
    print("\nCalling start_scraping()...")
    scraper.start_scraping()
    
    print(f"  Thread created: {scraper.scraping_thread is not None}")
    if scraper.scraping_thread:
        print(f"  Thread running: {scraper.scraping_thread.isRunning()}")
        print(f"  Thread: {scraper.scraping_thread}")
    
    # Scenario 3: Add to queue then try start
    print("\n→ SCENARIO 3: Add to queue, then call start_scraping()")
    print("-" * 60)
    
    # Clear inputs
    scraper.url_input_section.set_url("")
    scraper.output_settings.set_output_dir("")
    
    # Add to queue
    scraper.url_input_section.set_url(test_url)
    scraper.output_settings.set_output_dir(test_dir)
    scraper.add_to_queue()
    
    print(f"Queue items: {len(scraper.queue_items)}")
    print(f"Queue list count: {scraper.queue_section.queue_list.count()}")
    
    # Now the input should be cleared after adding to queue
    print("\nInput state after add_to_queue:")
    print(f"  URL: '{scraper.url_input_section.get_url()}'")
    print(f"  Output dir: '{scraper.output_settings.get_output_dir()}'")
    
    print("\nValidation:")
    valid, error = scraper.handlers.validate_inputs(
        scraper.url_input_section,
        scraper.chapter_selection_section,
        scraper.output_settings
    )
    print(f"  Valid: {valid}")
    print(f"  Error: {error}")
    
    print("\nCalling start_scraping()...")
    scraper.start_scraping()
    
    print(f"  Thread created: {scraper.scraping_thread is not None}")
    if scraper.scraping_thread:
        print(f"  Thread running: {scraper.scraping_thread.isRunning()}")
    
    # Check controls state
    print("\n→ CONTROLS STATE CHECK")
    print("-" * 60)
    print(f"Start button: {scraper.controls_section.start_button}")
    print(f"Pause button: {scraper.controls_section.pause_button}")
    print(f"Stop button: {scraper.controls_section.stop_button}")
    
    print("\n" + "="*70)
    print("KEY FINDING:")
    print("="*70)
    print("""
When you click 'Start', the app validates the URL INPUT FIELD, not the queue!
The workflow should be:
  1. Enter URL and settings in the form
  2. Click "Add to Queue" (this should clear the form)
  3. Click "Start" or "Start Scraping" to process queue items
  
BUT: Currently, "Start" tries to start from the INPUT FIELD, not the QUEUE!
This explains why:
  - Queue items don't process
  - Progress doesn't show
  - No thread is created (validation fails after clearing inputs)
""")


if __name__ == "__main__":
    diagnose_start_scraping()
