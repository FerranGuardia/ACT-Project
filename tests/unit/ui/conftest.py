"""
Pytest configuration for UI tests.

This conftest.py ensures UI tests run sequentially (no parallel execution)
due to Qt/PySide6 threading constraints.
"""

import pytest


# Automatically mark all tests in this directory as UI tests
def pytest_collection_modifyitems(config, items):
    """Automatically mark UI tests and configure execution."""
    for item in items:
        # Mark as UI test
        item.add_marker(pytest.mark.ui)

        # Add serial marker to disable parallel execution
        item.add_marker(pytest.mark.serial)

        # Skip UI tests if Qt is not available
        try:
            import PySide6.QtWidgets
            import PySide6.QtCore
        except ImportError:
            item.add_marker(pytest.mark.skip(reason="PySide6/Qt not available"))


@pytest.fixture(scope="session")
def qt_application():
    """Create QApplication instance for UI tests (session-scoped)."""
    try:
        import sys
        from PySide6.QtCore import QThread
        from PySide6.QtWidgets import QApplication

        # Check if QApplication already exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        yield app

        # Cleanup: Wait for all threads to finish before destroying QApplication
        # Guard for Qt versions that lack allThreads
        all_threads_fn = getattr(QThread, "allThreads", None)
        if callable(all_threads_fn):
            threads = all_threads_fn()
            for thread in threads:
                if thread != QThread.currentThread() and thread.isRunning():
                    thread.quit()
                    thread.wait(1000)  # Wait up to 1 second for thread to finish

        # Process any pending events
        app.processEvents()

    except ImportError:
        pytest.skip("PySide6 not available")