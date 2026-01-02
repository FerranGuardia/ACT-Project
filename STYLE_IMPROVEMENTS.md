# UI Style Improvements

This document tracks style improvements being made on the `ui-improvements-for-style` branch.

## Issues Identified

### 1. Hardcoded Colors
Many widgets use hardcoded color values instead of the centralized `COLORS` dictionary:

- `#888` → Should use `COLORS['text_secondary']`
- `white` → Should use `COLORS['text_primary']` or proper style function
- `#3a3a3a` → Should use `COLORS['bg_medium']` or similar
- `#2d2d2d` → Should use `COLORS['bg_dark']` or similar
- `rgb(27, 29, 35)` → Should use `COLORS['bg_dark']`

### 2. Inline Styles
Several widgets have inline styles that should be moved to `styles.py`:

- Toolbar styles in `main_window.py`
- Queue item widget styles (multiple files)
- Status label styles
- Icon label styles

### 3. Missing Style Functions
Need to add style functions for:

- Queue item widgets
- Toolbar
- Status labels
- Icon containers
- Secondary text labels

## Files to Update

### High Priority
- `src/ui/styles.py` - Add missing style functions
- `src/ui/main_window.py` - Replace toolbar inline style
- `src/ui/views/tts_view/queue_item_widget.py` - Replace hardcoded colors
- `src/ui/views/scraper_view/queue_item_widget.py` - Replace hardcoded colors
- `src/ui/views/full_auto_view/queue_item_widget.py` - Replace hardcoded colors

### Medium Priority
- All files with `setStyleSheet("color: white;")` or similar
- All files with `setStyleSheet("color: #888;")` or similar
- Progress sections with status labels

## Improvement Plan

1. ✅ Create branch `ui-improvements-for-style`
2. ✅ Add missing style functions to `styles.py`
3. ✅ Replace hardcoded colors with `COLORS` references
4. ✅ Replace inline styles with style function calls
5. ⏳ Test all views to ensure consistency
6. ✅ Document new style functions

## Completed Changes

### New Style Functions Added to `styles.py`
- `get_toolbar_style()` - Toolbar styling
- `get_queue_item_style()` - Queue item widget container
- `get_icon_container_style()` - Icon containers in queue items
- `get_status_label_style()` - Status labels
- `get_secondary_text_style()` - Secondary/muted text labels

### Files Updated
1. **src/ui/styles.py** - Added 5 new style functions
2. **src/ui/main_window.py** - Replaced toolbar inline style with `get_toolbar_style()`
3. **src/ui/views/tts_view/queue_item_widget.py** - Replaced all hardcoded colors
4. **src/ui/views/scraper_view/queue_item_widget.py** - Replaced all hardcoded colors
5. **src/ui/views/full_auto_view/queue_item_widget.py** - Replaced all hardcoded colors
6. **src/ui/views/tts_view/progress_section.py** - Replaced `"color: white;"` with `get_status_label_style()`
7. **src/ui/views/scraper_view/progress_section.py** - Replaced `"color: white;"` with `get_status_label_style()`
8. **src/ui/views/full_auto_view/current_processing_section.py** - Replaced `"color: white;"` with `get_status_label_style()`
9. **src/ui/views/merger_view.py** - Replaced `"color: white;"` with `get_status_label_style()`

### Color Replacements Made
- `#888` → `COLORS['text_secondary']` via `get_secondary_text_style()`
- `white` / `"color: white;"` → `COLORS['text_primary']` via `get_status_label_style()`
- `#3a3a3a` → `COLORS['bg_light']` via `get_icon_container_style()`
- `#2d2d2d` → `COLORS['bg_medium']` via `get_queue_item_style()`
- `rgb(27, 29, 35)` → `COLORS['bg_dark']` via `get_toolbar_style()`

## Remaining Items

- One hardcoded color in `landing_page.py`: `rgb(200, 200, 200)` - This is intentionally slightly different from `text_primary` for description text, but could be standardized if desired.
- Some hardcoded colors remain in `styles.py` itself - These are intentional as they're part of the style definitions (e.g., scrollbar arrows, hover states).

## Next Steps

1. Test the UI to ensure all styles look correct
2. Consider standardizing the landing page description color
3. Review any other widgets that might benefit from centralized styling

