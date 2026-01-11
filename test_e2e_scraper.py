"""
End-to-end test for scraper functionality to diagnose UI/backend disconnection.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.logger import get_logger

logger = get_logger("e2e_test")


def test_ui_connections():
    """Test that UI signal/slot connections are properly set up."""
    print("\n" + "="*60)
    print("TEST 1: UI Signal/Slot Connections")
    print("="*60)
    
    from ui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication
    
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    
    scraper = window.scraper_view
    
    # Check if buttons are connected
    print("\n✓ Checking UI components...")
    
    # Get the buttons
    start_button = scraper.controls_section.start_button
    print(f"  Start button exists: {start_button is not None}")
    
    add_queue_button = scraper.controls_section.add_queue_button
    print(f"  Add Queue button exists: {add_queue_button is not None}")
    
    print("\n✓ Handlers attached:")
    print(f"  scraper.handlers: {scraper.handlers}")
    print(f"  scraper._connect_handlers: {hasattr(scraper, '_connect_handlers')}")
    
    return True


def test_add_to_queue():
    """Test adding an item to the queue."""
    print("\n" + "="*60)
    print("TEST 2: Add Item to Queue")
    print("="*60)
    
    from ui.main_window import MainWindow
    from ui.ui_constants import StatusMessages
    from PySide6.QtWidgets import QApplication
    
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    
    scraper = window.scraper_view
    
    print(f"\nInitial queue items: {len(scraper.queue_items)}")
    
    # Set up test data
    test_url = "https://example.com/novel"
    test_dir = "C:\\tmp\\test_output"
    
    scraper.url_input_section.set_url(test_url)
    scraper.output_settings.set_output_dir(test_dir)
    scraper.chapter_selection_section.all_chapters_radio.setChecked(True)
    
    print(f"\nSet URL: {scraper.url_input_section.get_url()}")
    print(f"Set output dir: {scraper.output_settings.get_output_dir()}")
    
    # Add to queue
    print("\n→ Calling add_to_queue()...")
    scraper.add_to_queue()
    
    print(f"Queue items after add: {len(scraper.queue_items)}")
    print(f"Queue section list count: {scraper.queue_section.queue_list.count()}")
    
    if len(scraper.queue_items) > 0:
        print(f"✓ Queue item added: {scraper.queue_items[0]}")
    else:
        print("✗ FAILED: No item in queue!")
        return False
    
    if scraper.queue_section.queue_list.count() > 0:
        print(f"✓ Queue list widget updated")
    else:
        print("✗ FAILED: Queue list widget not updated!")
        return False
    
    return True


def test_scraping_thread():
    """Test that scraping thread can be created and signals work."""
    print("\n" + "="*60)
    print("TEST 3: Scraping Thread Creation")
    print("="*60)
    
    from ui.views.scraper_view.scraping_thread import ScrapingThread
    from PySide6.QtWidgets import QApplication
    
    app = QApplication.instance() or QApplication([])
    
    test_url = "https://example.com/novel"
    test_output_dir = "C:\\tmp\\test_output"
    chapter_selection = {"type": "all"}
    file_format = "txt"
    
    print(f"\nCreating thread with:")
    print(f"  URL: {test_url}")
    print(f"  Output: {test_output_dir}")
    
    thread = ScrapingThread(test_url, chapter_selection, test_output_dir, file_format)
    
    print(f"✓ Thread created: {thread}")
    print(f"✓ Thread isRunning: {thread.isRunning()}")
    
    # Check if signals exist
    print(f"\n✓ Signals available:")
    print(f"  progress: {hasattr(thread, 'progress')}")
    print(f"  status: {hasattr(thread, 'status')}")
    print(f"  finished: {hasattr(thread, 'finished')}")
    print(f"  file_created: {hasattr(thread, 'file_created')}")
    
    return True


def test_signal_connections_functional():
    """Test that signals actually emit and are received."""
    print("\n" + "="*60)
    print("TEST 4: Signal Emission and Reception")
    print("="*60)
    
    from ui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    
    scraper = window.scraper_view
    
    # Track signal emissions
    signals_received = {
        "progress": [],
        "status": [],
        "file_created": []
    }
    
    def on_progress(value):
        print(f"  ✓ Progress signal received: {value}")
        signals_received["progress"].append(value)
    
    def on_status(message):
        print(f"  ✓ Status signal received: {message}")
        signals_received["status"].append(message)
    
    def on_file_created(filepath):
        print(f"  ✓ File created signal received: {filepath}")
        signals_received["file_created"].append(filepath)
    
    # Connect test signals
    print("\n→ Connecting test signal handlers...")
    
    # We'll test by manually creating a thread and emitting signals
    from ui.views.scraper_view.scraping_thread import ScrapingThread
    
    thread = ScrapingThread(
        "https://example.com",
        {"type": "all"},
        "C:\\tmp\\test",
        "txt"
    )
    
    thread.progress.connect(on_progress)
    thread.status.connect(on_status)
    thread.file_created.connect(on_file_created)
    
    print("✓ Test handlers connected to thread signals")
    
    # Emit test signals manually
    print("\n→ Emitting test signals...")
    thread.progress.emit(50)
    thread.status.emit("Test status message")
    thread.file_created.emit("/test/file.txt")
    
    # Process events to allow signals to be delivered
    app.processEvents()
    
    print(f"\nSignals received:")
    print(f"  Progress: {signals_received['progress']}")
    print(f"  Status: {signals_received['status']}")
    print(f"  File created: {signals_received['file_created']}")
    
    if signals_received['progress'] and signals_received['status']:
        print("\n✓ Signals working correctly")
        return True
    else:
        print("\n✗ Signals NOT working!")
        return False


def test_full_scraper_workflow():
    """Test complete scraper workflow from UI to backend."""
    print("\n" + "="*60)
    print("TEST 5: Full Scraper Workflow")
    print("="*60)
    
    from ui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer, Qt
    
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    
    scraper = window.scraper_view
    
    print("\n→ Step 1: Add item to queue")
    scraper.url_input_section.set_url("https://example.com/novel")
    scraper.output_settings.set_output_dir("C:\\tmp\\test_output")
    scraper.chapter_selection_section.all_chapters_radio.setChecked(True)
    
    scraper.add_to_queue()
    print(f"  Queue items: {len(scraper.queue_items)}")
    
    if len(scraper.queue_items) == 0:
        print("  ✗ FAILED: Queue is empty!")
        return False
    
    print("\n→ Step 2: Check UI state before start")
    print(f"  Controls section: {scraper.controls_section}")
    print(f"  Progress bar value: {scraper.progress_section.progress_bar.value()}")
    print(f"  Status label: {scraper.progress_section.status_label.text()}")
    
    print("\n→ Step 3: Try to start scraping")
    print(f"  Calling start_scraping()...")
    
    # This will likely fail due to validation, but let's see what happens
    try:
        scraper.start_scraping()
        print(f"  ✓ start_scraping() called without error")
        
        # Check thread state
        if scraper.scraping_thread:
            print(f"  ✓ Thread created: {scraper.scraping_thread}")
            print(f"  ✓ Thread running: {scraper.scraping_thread.isRunning()}")
        else:
            print(f"  ✗ No thread created!")
            
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n→ Step 4: Check UI updates")
    # Process pending events
    app.processEvents()
    
    print(f"  Progress bar value: {scraper.progress_section.progress_bar.value()}")
    print(f"  Status label: {scraper.progress_section.status_label.text()}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("ACT - END-TO-END SCRAPER TEST")
    print("="*70)
    
    tests = [
        ("UI Connections", test_ui_connections),
        ("Add to Queue", test_add_to_queue),
        ("Scraping Thread", test_scraping_thread),
        ("Signal Connections", test_signal_connections_functional),
        ("Full Workflow", test_full_scraper_workflow),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n→ Running: {test_name}")
            result = test_func()
            results[test_name] = "PASS" if result else "FAIL"
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = "CRASH"
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        symbol = "✓" if result == "PASS" else "✗"
        print(f"{symbol} {test_name}: {result}")
    
    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")
    
    return all(r == "PASS" for r in results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
