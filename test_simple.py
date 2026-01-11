"""
Verify the queue processing fix - simpler version.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

print("[1] Importing modules...")
from ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication

print("[2] Creating application...")
app = QApplication.instance() or QApplication([])
window = MainWindow()
scraper = window.scraper_view

print("[3] Setting up test data...")
test_url = "https://novelfull.com/test-novel"
test_dir = "C:\\tmp\\test_output"

print("[4] Adding item to queue...")
scraper.url_input_section.set_url(test_url)
scraper.output_settings.set_output_dir(test_dir)
scraper.add_to_queue()
print(f"    Queue items: {len(scraper.queue_items)}")

print("[5] Form state after add_to_queue:")
print(f"    Input form URL: '{scraper.url_input_section.get_url()}'")

print("[6] Calling start_scraping()...")
scraper.start_scraping()

print("[7] Result:")
print(f"    Thread created: {scraper.scraping_thread is not None}")
if scraper.scraping_thread:
    print(f"    Thread running: {scraper.scraping_thread.isRunning()}")
    print(f"    Thread URL: {scraper.scraping_thread.url}")
    print(f"    Expected URL: {test_url}")
    match = scraper.scraping_thread.url == test_url
    print(f"    Result: {'PASS' if match else 'FAIL'}")
    if scraper.scraping_thread.isRunning():
        scraper.scraping_thread.stop()

print("[8] Done!")
