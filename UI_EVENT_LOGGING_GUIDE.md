# UI Event Logging Guide

This guide explains how to enable and use comprehensive UI event logging for debugging.

## Overview

The ACT application now includes a **UI Event Logger** that tracks and displays all user interactions in the console:

- 🖱️ **Button clicks** and UI element interactions
- ⌨️ **Input field changes** and text entries
- 🔀 **Navigation events** between views
- ⚙️ **Background processes** and operations
- ❌ **Error messages** and exceptions
- 🐛 **Debug information** for troubleshooting

## Quick Start

### Option 1: Use the Debug Launcher (Easiest)

Run the dedicated debug launcher script:

```bash
python launch_ui_debug.py
```

This automatically enables:
- ✅ Verbose console logging
- ✅ All UI event tracking
- ✅ DEBUG level messages to console

### Option 2: Run Standard Launcher with Verbose Logging

The standard launcher now includes verbose logging by default:

```bash
python launch_ui.py
```

Or on Windows:

```bash
launch_ui.bat
```

## Console Output Examples

When you interact with the UI, you'll see messages like:

```
[UI EVENT] DEBUG   | 🖱️  [CLICK] Button 'Back' pressed | Widget: back_button
[UI EVENT] DEBUG   | 🖱️  [CLICK] Mode Card: scraper selected | Widget: GenreCard
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] Navigation: Landing Page → Scraper | Widget: main_window
[UI EVENT] DEBUG   | ⚙️  [PROCESS] Scraper: started | Widget: scraper_view | urls=1
[UI EVENT] DEBUG   | ⌨️  [INPUT] Input 'url' changed to: 'https://example.com...'
```

## Advanced Usage

### Launch with Options

The debug launcher supports several options:

```bash
# Default: Full verbose logging
python launch_ui_debug.py

# Suppress non-critical logs
python launch_ui_debug.py --quiet

# Filter logs by category (e.g., only show UI events)
python launch_ui_debug.py --filter ui

# Disable UI event logging (show only regular logs)
python launch_ui_debug.py --no-ui-logging
```

### Programmatic Control

You can enable/disable logging programmatically in your code:

```python
from ui.event_logger import UIEventLogger

# Enable logging
UIEventLogger.enable()

# Log a custom event
UIEventLogger.log_event(
    category=UIEventLogger.CLICK,
    message="Custom button clicked",
    widget_name="MyButton",
    details={"state": "active"}
)

# Disable logging
UIEventLogger.disable()
```

### Log Different Event Types

```python
from ui.event_logger import UIEventLogger

# Log a button click
UIEventLogger.log_button_click("Submit", "pressed")

# Log input change
UIEventLogger.log_input_change("email", "user@example.com")

# Log navigation
UIEventLogger.log_navigation("HomePage", "SettingsPage", "user clicked menu")

# Log background process
UIEventLogger.log_process(
    "FileScraper",
    "completed",
    details={"files": 42, "duration": "2.5s"}
)

# Log error
UIEventLogger.log_error("Failed to load URL", context="scraper_view")
```

### Using Decorators

Add logging to functions with decorators:

```python
from ui.event_logger import log_button_click, log_input_change, log_navigation

@log_button_click
def on_submit():
    """Automatically logs button click."""
    pass

@log_input_change("username")
def on_username_changed(text):
    """Automatically logs input changes."""
    pass

@log_navigation("MainPage")
def show_settings():
    """Automatically logs navigation."""
    pass
```

### Using Mixins

Add logging capabilities to your widgets:

```python
from ui.event_logger import EventLoggingMixin
from PySide6.QtWidgets import QPushButton

class MyButton(EventLoggingMixin, QPushButton):
    def on_click(self):
        self.log_click("pressed")
        
    def on_value_change(self, value):
        self.log_change(value, field_type="number")
```

## Configuration

### Modify Core Logger Level

If you want to change the core logging level:

```python
from core.logger import ACTLogger

# Enable verbose console logging
ACTLogger.enable_verbose_console()

# Disable verbose logging (back to INFO level)
ACTLogger.disable_verbose_console()

# Set specific level
ACTLogger.set_level("DEBUG")
```

## Log File Locations

All logs are also saved to files:

- **Main Log**: `~/.act/logs/act.log`
- **Error Log**: `~/.act/logs/act_errors.log`

These files contain DEBUG level information even when console logging is at INFO level.

## Debugging Workflow

### Finding Issues

1. **Run with debug launcher**:
   ```bash
   python launch_ui_debug.py
   ```

2. **Perform the action** that's causing issues

3. **Watch the console** for the relevant event:
   ```
   🖱️  [CLICK] Mode Card: scraper selected
   🔀 [NAVIGATION] Navigation: Landing Page → Scraper
   ```

4. **Look for error messages**:
   ```
   ❌ [ERROR] Failed to initialize view [scraper_view]
   ```

5. **Check log files** for more details:
   ```bash
   cat ~/.act/logs/act.log
   ```

### Performance Monitoring

Track which processes are running:

```
⚙️  [PROCESS] Scraper: started
⚙️  [PROCESS] Scraper: fetching URLs
⚙️  [PROCESS] Scraper: completed
```

## Troubleshooting

### Not Seeing Any Events?

1. Make sure you're using `python launch_ui_debug.py`
2. Check that `UIEventLogger.is_enabled()` returns `True`
3. Verify console output is not being redirected

### Too Much Output?

Use the `--quiet` flag:
```bash
python launch_ui_debug.py --quiet
```

Or disable UI logging but keep core logging:
```bash
python launch_ui_debug.py --no-ui-logging
```

### Missing Console Handler?

The logger automatically creates a console handler if it doesn't exist. If you modify logging config, ensure the console handler has DEBUG level:

```python
from core.logger import ACTLogger
ACTLogger.enable_verbose_console()
```

## Adding Logging to New Features

When creating new UI components:

1. **Import the logger**:
   ```python
   from ui.event_logger import UIEventLogger
   ```

2. **Log key interactions**:
   ```python
   def on_button_click(self):
       UIEventLogger.log_button_click("MyButton", "clicked")
       # Your code here
   ```

3. **Log navigation**:
   ```python
   def navigate_to_view(self, view_name):
       UIEventLogger.log_navigation("CurrentView", view_name)
       # Navigation code
   ```

4. **Log errors**:
   ```python
   try:
       # Your code
   except Exception as e:
       UIEventLogger.log_error(str(e), context="my_feature")
       raise
   ```

## Performance Note

UI event logging adds minimal overhead (~1-2% CPU increase) but can produce significant console output. For production use, consider disabling with:

```python
UIEventLogger.disable()
```

Or use the `--no-ui-logging` flag when launching.

---

**Questions or Issues?** Check the console output first - it usually shows exactly what's happening!
