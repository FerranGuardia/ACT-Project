# Testing Console Event Logging

This document guides you through testing the new console event logging system.

## Prerequisites

- ACT application should be ready to run
- Virtual environment should be set up (`/.venv/`)
- All dependencies installed

## Step-by-Step Testing

### Test 1: Basic Launch with Verbose Logging

**Objective**: Verify that the debug launcher starts and shows initial log messages.

**Steps**:
1. Open a terminal in the ACT directory
2. Run: `python launch_ui_debug.py`
3. Wait for the application to start

**Expected Output** (in console):
```
========================================
   ACT - Debug UI Launcher
========================================

Starting UI with VERBOSE logging...
All button clicks, input changes, and navigation will be shown in console.

... (logging initialization messages)

[UI EVENT] DEBUG   | Available events to watch for:
[UI EVENT] DEBUG   | 🖱️  [CLICK]      - Button and UI element clicks
[UI EVENT] DEBUG   | ⌨️  [INPUT]      - Text field and input changes
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] - View and page transitions
[UI EVENT] DEBUG   | ⚙️  [PROCESS]    - Background operations
[UI EVENT] DEBUG   | ❌ [ERROR]      - Errors and exceptions

✅ Application launched successfully!
📝 Watch console for all UI interactions and events
```

**Result**: ✅ PASS if you see the header and UI event logging is ACTIVE

---

### Test 2: Landing Page Navigation

**Objective**: Verify that clicking mode cards logs navigation events.

**Steps**:
1. Application should be running from Test 1
2. Look at the landing page with mode cards (Scraper, TTS, Merger, Full Auto)
3. Click on the **"Scraper"** mode card

**Expected Console Output**:
```
[UI EVENT] DEBUG   | 🖱️  [CLICK] Mode Card: scraper selected
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] Navigation: Landing Page → Scraper | reason: user clicked mode card
```

**Result**: ✅ PASS if you see both the click and navigation events

---

### Test 3: Back Button Navigation

**Objective**: Verify that back button logs navigation back to landing.

**Steps**:
1. Still on a mode view (e.g., Scraper view)
2. Click the **"Back"** button at the top left

**Expected Console Output**:
```
[UI EVENT] DEBUG   | 🖱️  [CLICK] Button 'Back' pressed
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] Navigation: Any View → Landing Page | reason: back button pressed
```

**Result**: ✅ PASS if you see the back button click and navigation event

---

### Test 4: Multiple Mode Clicks

**Objective**: Verify event logging works consistently across multiple interactions.

**Steps**:
1. Go back to landing page
2. Click on **"TTS"** card
3. Go back
4. Click on **"Merger"** card
5. Go back

**Expected Console Output** (should see 3 navigation pairs):
```
[UI EVENT] DEBUG   | 🖱️  [CLICK] Mode Card: tts selected
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] Navigation: Landing Page → TTS

[UI EVENT] DEBUG   | 🖱️  [CLICK] Button 'Back' pressed
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] Navigation: Any View → Landing Page

[UI EVENT] DEBUG   | 🖱️  [CLICK] Mode Card: merger selected
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] Navigation: Landing Page → Merger
```

**Result**: ✅ PASS if all events are logged consistently

---

### Test 5: Quiet Mode

**Objective**: Verify that --quiet flag suppresses non-critical logs.

**Steps**:
1. Close current application
2. Run: `python launch_ui_debug.py --quiet`
3. Interact with the UI (click buttons, navigate)

**Expected Output**:
- ✅ Should still see UI event logging
- ✅ Should NOT see as many debug messages
- ✅ Should be cleaner/less verbose

**Result**: ✅ PASS if UI events still appear but console is less cluttered

---

### Test 6: No UI Logging Mode

**Objective**: Verify that --no-ui-logging disables event logging.

**Steps**:
1. Close current application  
2. Run: `python launch_ui_debug.py --no-ui-logging`
3. Click buttons and navigate

**Expected Output**:
- ❌ Should NOT see `[UI EVENT]` messages
- ✅ Should still see regular logs (startup, initialization)
- ✅ Console message: "UI event logging is DISABLED"

**Result**: ✅ PASS if UI event logging is disabled but app still works

---

### Test 7: Standard Launcher (Default Mode)

**Objective**: Verify that the standard launch_ui.py also has verbose logging enabled.

**Steps**:
1. Close current application
2. Run: `python launch_ui.py`
3. Click a mode card

**Expected Output**:
```
... initialization logs ...
[UI EVENT] DEBUG   | 🖱️  [CLICK] Mode Card: scraper selected
[UI EVENT] DEBUG   | 🔀 [NAVIGATION] Navigation: Landing Page → Scraper
```

**Result**: ✅ PASS if you see UI event logging enabled

---

### Test 8: Windows Batch Launcher

**Objective**: Verify the Windows batch file works.

**Steps**:
1. Close current application
2. Navigate to ACT directory in File Explorer
3. Double-click `launch_ui_debug.bat`
4. Wait for window to open
5. Interact with UI

**Expected**:
- ✅ Console window should open
- ✅ Should see logging output
- ✅ Should see UI events when you click

**Result**: ✅ PASS if batch file works correctly

---

## Testing Checklist

Use this checklist to verify everything works:

- [ ] Debug launcher starts successfully
- [ ] Shows verbose logging header message
- [ ] Mode card clicks are logged
- [ ] Navigation events are logged
- [ ] Back button clicks are logged
- [ ] Quiet mode works (--quiet flag)
- [ ] No UI logging mode works (--no-ui-logging flag)
- [ ] Standard launcher (launch_ui.py) has logging
- [ ] Windows batch file (launch_ui_debug.bat) works
- [ ] Multiple interactions show consistent logging
- [ ] No syntax errors or crash on startup

---

## Troubleshooting

### Issue: No UI events appearing in console

**Solution**:
1. Verify you're using `python launch_ui_debug.py` (not another launcher)
2. Check that the console isn't redirected to a file
3. Try: `python launch_ui_debug.py --quiet` (to ensure logger is initialized)
4. Check `~/.act/logs/act.log` to see if events are logged to file

### Issue: Too much output/console is cluttered

**Solution**:
```bash
python launch_ui_debug.py --quiet
```

### Issue: Application crashes on startup

**Solution**:
1. Check Python syntax: `python -m py_compile launch_ui_debug.py`
2. Check imports: `python -c "from ui.event_logger import UIEventLogger"`
3. Try standard launcher: `python launch_ui.py`

### Issue: Events not showing for a specific button

**Solution**:
1. Make sure button click is being handled (might be slow)
2. Check that the handler actually calls the function
3. Add manual logging to the handler function

---

## Test Results Template

Copy and fill this out:

```
Test Date: _____________
Tester: __________________

Test 1 - Basic Launch:           [ ] PASS  [ ] FAIL
Test 2 - Mode Card Navigation:   [ ] PASS  [ ] FAIL
Test 3 - Back Button:            [ ] PASS  [ ] FAIL
Test 4 - Multiple Clicks:        [ ] PASS  [ ] FAIL
Test 5 - Quiet Mode:             [ ] PASS  [ ] FAIL
Test 6 - No UI Logging:          [ ] PASS  [ ] FAIL
Test 7 - Standard Launcher:      [ ] PASS  [ ] FAIL
Test 8 - Batch File:             [ ] PASS  [ ] FAIL

Total Passed: _____ / 8

Notes/Issues:
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________
```

---

## Next Steps

Once testing is complete:

1. ✅ Verify all tests pass
2. ✅ Add logging to more UI components as needed
3. ✅ Use for debugging any UI issues
4. ✅ Reference `UI_EVENT_LOGGING_GUIDE.md` for advanced usage

**Questions?** Check the console output - it usually shows exactly what's happening!
