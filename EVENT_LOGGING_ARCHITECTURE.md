# Event Logging Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          ACT Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐      ┌──────────────────┐                 │
│  │   Main Window    │      │  Landing Page    │                 │
│  │   - Navigation   │──────│   - Mode Cards   │                 │
│  │   - Back Button  │      │   - Selections   │                 │
│  └────────┬─────────┘      └────────┬─────────┘                 │
│           │                         │                            │
│           └────────────┬────────────┘                            │
│                        │                                         │
│                        ▼                                         │
│  ┌─────────────────────────────────────────────┐                │
│  │     UIEventLogger (event_logger.py)         │                │
│  │  - Logs all UI interactions                 │                │
│  │  - Categorizes events (CLICK, INPUT, etc)   │                │
│  │  - Formats with emoji icons                 │                │
│  │  - Can be enabled/disabled                  │                │
│  └─────────────────┬──────────────────────────┘                │
│                    │                                            │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────┐                │
│  │      ACTLogger (core/logger.py)             │                │
│  │  - Console Handler (DEBUG when verbose)     │                │
│  │  - File Handler (DEBUG always)              │                │
│  │  - Error File Handler                       │                │
│  └─────────────────┬──────────────────────────┘                │
│                    │                                            │
│        ┌───────────┴───────────┬────────────┐                   │
│        ▼                       ▼            ▼                   │
│   ┌─────────┐          ┌──────────────┐  ┌──────────┐           │
│   │ Console │          │ Log File     │  │ Error    │           │
│   │ (STDOUT)│          │ ~/.act/logs/ │  │ Log File │           │
│   │[UI EVT] │          │ act.log      │  │ act_err  │           │
│   └─────────┘          └──────────────┘  └──────────┘           │
│        │                                                         │
└────────┼─────────────────────────────────────────────────────────┘
         │
         ▼
    👤 User (Developer)
       - Sees all UI events in real-time
       - Debugs issues by watching interactions
```

## Data Flow

```
User Interaction
    │
    ├─→ Button Click ──→ Event Handler
    ├─→ Input Change ──→ Event Handler  
    ├─→ Navigation ────→ Event Handler
    ├─→ Process ───────→ Background Task
    └─→ Error ─────────→ Exception Handler
         │
         ▼
    UIEventLogger.log_*()
         │
         ├─→ Format message with emoji
         ├─→ Add context (widget name, details)
         └─→ Send to console logger
              │
              ▼
         Console Output with [UI EVENT] tag
         │
         ▼
    Developer sees in terminal:
    [UI EVENT] DEBUG | 🖱️ [CLICK] Button 'X' pressed
```

## Launch Paths

```
┌────────────────────────────────────────────────────────────────┐
│                    Launch Options                              │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  python launch_ui.py                                           │
│      │                                                          │
│      ├─→ Imports ACTLogger                                     │
│      ├─→ Calls enable_verbose_console()                        │
│      └─→ Verbose logging ENABLED by default                    │
│                                                                 │
│  python launch_ui_debug.py [options]                           │
│      │                                                          │
│      ├─→ Shows debug header                                    │
│      ├─→ Enables verbose console logging                       │
│      ├─→ Supports --quiet flag                                 │
│      ├─→ Supports --filter option                              │
│      ├─→ Supports --no-ui-logging flag                         │
│      └─→ Better for dedicated debugging                        │
│                                                                 │
│  launch_ui_debug.bat (Windows)                                 │
│      │                                                          │
│      └─→ Calls python launch_ui_debug.py                       │
│          (No additional options by default)                     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

## Event Logging Flow

```
┌──────────────┐
│ User Action  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│ View Handler (e.g., click)   │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ UIEventLogger.log_button_click()     │
│                                      │
│  1. Create message with emoji        │
│  2. Add widget context               │
│  3. Send to console logger           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Console (if enabled)                 │
│                                      │
│ [UI EVENT] DEBUG | 🖱️ [CLICK] ...   │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Log File (always)                    │
│                                      │
│ ~/.act/logs/act.log                  │
└──────────────────────────────────────┘
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    event_logger.py                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  UIEventLogger (Main Class)                                 │
│  ├─ enable() / disable()                                    │
│  ├─ log_event(category, message, widget, details)           │
│  ├─ log_button_click()                                      │
│  ├─ log_input_change()                                      │
│  ├─ log_navigation()                                        │
│  ├─ log_process()                                           │
│  ├─ log_error()                                             │
│  └─ _get_console_logger()                                   │
│                                                              │
│  Decorators:                                                │
│  ├─ @log_button_click                                       │
│  ├─ @log_input_change(field_name)                           │
│  └─ @log_navigation(from_view)                              │
│                                                              │
│  EventLoggingMixin (For Custom Widgets)                     │
│  ├─ log_ui_event()                                          │
│  ├─ log_click()                                             │
│  └─ log_change()                                            │
│                                                              │
│  Helper Function:                                           │
│  └─ connect_with_logging(signal, slot, name)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Console Output Examples

```
┌─────────────────────────────────────────────────────────────┐
│ Console Output (Real Examples)                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Application startup:                                        │
│ 🟢 UI Event Logging ENABLED                                │
│                                                              │
│ Mode card selection:                                        │
│ 🖱️  [CLICK] Mode Card: scraper selected                     │
│ 🔀 [NAVIGATION] Navigation: Landing Page → Scraper          │
│                                                              │
│ Back button press:                                          │
│ 🖱️  [CLICK] Button 'Back' pressed                           │
│ 🔀 [NAVIGATION] Navigation: Any View → Landing Page         │
│                                                              │
│ Input field change:                                         │
│ ⌨️  [INPUT] Input 'url' changed to: 'https://example.com'  │
│                                                              │
│ Background process:                                         │
│ ⚙️  [PROCESS] Scraper: started                              │
│ ⚙️  [PROCESS] Scraper: completed | duration=2.5s            │
│                                                              │
│ Error event:                                                │
│ ❌ [ERROR] Failed to load URL [scraper_view]               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Hierarchy

```
Level 1: ACTLogger (Core Logger)
├─ Root Logger: "act"
├─ Level: DEBUG
└─ Handlers:
   ├─ Console Handler
   │  ├─ Level: DEBUG (when verbose)
   │  ├─ Level: INFO (normal)
   │  └─ Format: "[timestamp] [logger] [level] - [message]"
   ├─ File Handler
   │  ├─ Level: DEBUG (always)
   │  ├─ File: ~/.act/logs/act.log
   │  └─ Rotation: 10MB per file
   └─ Error Handler
      ├─ Level: ERROR
      ├─ File: ~/.act/logs/act_errors.log
      └─ Rotation: 5MB per file

Level 2: UIEventLogger (UI Events)
├─ Logger: "act.ui.events"
├─ Level: DEBUG
└─ Console Handler (separate from core)
   ├─ Always DEBUG level
   ├─ Format: "[UI EVENT] [level] | [message]"
   └─ Propagate: False (independent)
```

---

This architecture ensures:
✅ Real-time visibility of UI interactions  
✅ Comprehensive logging for debugging  
✅ Easy enable/disable without code changes  
✅ Minimal performance impact  
✅ Organized and categorized events  
✅ Persistence to log files for review  
