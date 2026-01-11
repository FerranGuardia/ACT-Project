# Console Event Logging - Quick Start

## TL;DR - Get Started Now

Run this to see all UI actions in your console:

```bash
python launch_ui_debug.py
```

That's it! You'll now see every click, input change, and navigation action.

---

## What You'll See

When you click buttons or interact with the UI:

```
[UI EVENT] DEBUG   | 🖱️  [CLICK] Mode Card: scraper selected
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] Navigation: Landing Page → Scraper
```

---

## Available Launchers

### 1. **Standard UI Launcher** (includes logging)
```bash
python launch_ui.py
```
✅ Verbose logging enabled by default  
✅ All UI events shown in console  
✅ Good for regular use + debugging

### 2. **Debug Launcher** (dedicated debug version)
```bash
python launch_ui_debug.py
```
✅ Same as above but with additional debug info  
✅ Better console output formatting  
✅ Command-line options available

### 3. **Windows Batch File**
```bash
launch_ui_debug.bat
```
✅ Double-click to run  
✅ Pauses at end to see output

---

## Command-Line Options

```bash
# Suppress non-critical logs
python launch_ui_debug.py --quiet

# Only show UI events (filter other logs)
python launch_ui_debug.py --filter ui

# Disable UI event logging entirely
python launch_ui_debug.py --no-ui-logging

# Show help
python launch_ui_debug.py --help
```

---

## Event Types You'll See

| Emoji | Type | Example |
|-------|------|---------|
| 🖱️ | CLICK | `Button 'Submit' pressed` |
| ⌨️ | INPUT | `Input 'email' changed` |
| 🔀 | NAVIGATION | `Landing Page → Scraper` |
| ⚙️ | PROCESS | `Scraper: completed` |
| ❌ | ERROR | `Failed to load URL` |
| 🐛 | DEBUG | Debug information |

---

## Common Debugging Scenarios

### Scenario 1: Button Click Not Working
1. Run: `python launch_ui_debug.py`
2. Click the button
3. Look for: `🖱️ [CLICK] Button 'ButtonName' pressed`
4. If you don't see it, the click handler isn't being called

### Scenario 2: Navigation Issue
1. Run: `python launch_ui_debug.py`
2. Click to navigate to a new view
3. Look for: `🔀 [NAVIGATION] CurrentView → NewView`
4. If you don't see it, check if the navigation function was called

### Scenario 3: Silent Crashes
1. Run: `python launch_ui_debug.py --quiet`
2. Look for: `❌ [ERROR]` messages
3. These will tell you exactly what failed

---

## Programmatic Usage

Log custom events in your code:

```python
from ui.event_logger import UIEventLogger

# Log a button click
UIEventLogger.log_button_click("MyButton", "activated")

# Log an error
UIEventLogger.log_error("Something went wrong", context="my_feature")

# Log navigation
UIEventLogger.log_navigation("ViewA", "ViewB")

# Disable logging if too verbose
UIEventLogger.disable()
```

---

## Still Not Working?

1. ✅ Make sure you're using `python launch_ui_debug.py` (not another launcher)
2. ✅ Check console isn't being redirected elsewhere
3. ✅ Look in `~/.act/logs/act.log` for more details
4. ✅ Try `--no-ui-logging` to see if core logs show the issue

---

## Files Modified

New files created:
- `launch_ui_debug.py` - Debug launcher script
- `launch_ui_debug.bat` - Windows batch launcher
- `src/ui/utils/event_logger.py` - Event logging module
- `UI_EVENT_LOGGING_GUIDE.md` - Full documentation

Files updated:
- `launch_ui.py` - Now includes verbose logging
- `src/core/logger.py` - Added verbose console methods
- `src/ui/main_window.py` - Added event logging to navigation
- `src/ui/landing_page_components.py` - Added event logging to card clicks
- `src/ui/landing_page_modes.py` - Pass mode_id to cards

---

**Need help?** Run `python launch_ui_debug.py --help` for all options!
