# UI Testing Guide - ACT Application

**Date**: 2025-12-06  
**Version**: 1.0  
**Status**: Ready for Testing

---

## 🎯 Testing Objectives

This guide provides comprehensive testing procedures for the ACT (Audiobook Creator Tools) UI application. The UI has been fully implemented with backend integration and is ready for both manual and automated testing.

---

## 📋 Pre-Testing Setup

### Prerequisites
1. **Python 3.9+** installed
2. **PySide6** installed (`pip install PySide6`)
3. **pydub** installed for audio merging (`pip install pydub`)
4. **ffmpeg** installed (required by pydub for audio format conversion)
5. **Edge-TTS** dependencies (usually auto-installed)

### Launch the Application
```bash
# Option 1: Use the batch file
launch_ui.bat

# Option 2: Use Python directly
python launch_ui.py
```

### Verify Installation
- Application window should open
- Landing page should display 4 mode cards
- No error messages in console

---

## 🧪 Manual Testing Procedures

### Test 1: General UI Navigation

**Objective**: Verify basic UI navigation and layout

**Steps**:
1. Launch the application
2. Verify landing page displays 4 cards (Scraper, TTS, Merger, Full Automation)
3. Click on "Scraper" card
4. Verify Scraper view displays
5. Verify "Back to Home" button appears in toolbar
6. Click "Back to Home" button
7. Verify return to landing page
8. Repeat for TTS, Merger, and Full Automation views

**Expected Results**:
- ✅ All views navigate correctly
- ✅ Back button appears/disappears appropriately
- ✅ No crashes or errors

**Pass/Fail**: __________

---

### Test 2: Scraper View - Basic Functionality

**Objective**: Test web scraping functionality

**Prerequisites**: 
- Valid webnovel URL (e.g., from NovelBin or similar site)
- Internet connection

**Steps**:
1. Navigate to Scraper view
2. Enter a valid novel URL
3. Select "All chapters" option
4. Click "Browse" to select output directory
5. Select output format (.txt or .md)
6. Click "▶️ Start Scraping"
7. Observe progress bar and status updates
8. Wait for completion
9. Verify files appear in "Output Files" list
10. Click "📂 Open Folder" button
11. Verify folder opens in file explorer

**Expected Results**:
- ✅ URL validation works (try invalid URL first)
- ✅ Progress bar updates during scraping
- ✅ Status messages update appropriately
- ✅ Files are created in output directory
- ✅ File list updates with created files
- ✅ Open folder button works

**Error Cases to Test**:
- Invalid URL format → Should show error message
- No output directory selected → Should show validation error
- Network error → Should show appropriate error message

**Pass/Fail**: __________

---

### Test 3: Scraper View - Chapter Selection

**Objective**: Test different chapter selection options

**Steps**:
1. Navigate to Scraper view
2. Enter a valid novel URL
3. Test "Range" option:
   - Select "Range" radio button
   - Set "from" to 1, "to" to 5
   - Start scraping
   - Verify only chapters 1-5 are scraped
4. Test "Specific chapters" option:
   - Select "Specific chapters" radio button
   - Enter "1, 3, 5, 7" in input field
   - Start scraping
   - Verify only specified chapters are scraped

**Expected Results**:
- ✅ Range selection works correctly
- ✅ Specific chapter selection works correctly
- ✅ Input validation prevents invalid ranges (e.g., from > to)

**Pass/Fail**: __________

---

### Test 4: Scraper View - Pause/Stop

**Objective**: Test pause and stop functionality

**Steps**:
1. Start a scraping operation with many chapters
2. Click "⏸️ Pause" button
3. Verify scraping pauses (status shows "Paused...")
4. Click "▶️ Resume" (button text should change)
5. Verify scraping resumes
6. Click "⏹️ Stop" button
7. Verify scraping stops
8. Verify UI resets (buttons re-enabled)

**Expected Results**:
- ✅ Pause button pauses operation
- ✅ Resume button resumes operation
- ✅ Stop button stops operation immediately
- ✅ UI state resets correctly after stop

**Pass/Fail**: __________

---

### Test 5: TTS View - File Selection

**Objective**: Test file selection and management

**Steps**:
1. Navigate to TTS view
2. Click "➕ Add Files" button
3. Select multiple text files (.txt or .md)
4. Verify files appear in list
5. Click "➕ Add Folder" button
6. Select a folder containing text files
7. Verify all text files from folder are added
8. Select a file in the list
9. Click "Remove Selected" button
10. Verify file is removed from list

**Expected Results**:
- ✅ Add Files dialog works
- ✅ Add Folder recursively finds text files
- ✅ File list displays correctly
- ✅ Remove button removes selected files

**Pass/Fail**: __________

---

### Test 6: TTS View - Voice Settings

**Objective**: Test voice selection and preview

**Steps**:
1. Navigate to TTS view
2. Verify voice dropdown is populated with voices
3. Select different voices from dropdown
4. Adjust Rate slider (50-200%)
5. Verify rate label updates
6. Adjust Pitch slider (-50 to 50)
7. Verify pitch label updates
8. Adjust Volume slider (0-100%)
9. Verify volume label updates
10. Click "🔊 Preview" button
11. Verify preview audio plays (may need audio player)

**Expected Results**:
- ✅ Voice dropdown populated with available voices
- ✅ Sliders update labels correctly
- ✅ Preview button generates and plays preview audio

**Pass/Fail**: __________

---

### Test 7: TTS View - Conversion

**Objective**: Test text-to-speech conversion

**Prerequisites**: 
- Text files added to list
- Output directory selected

**Steps**:
1. Add text files to TTS view
2. Select output directory
3. Select output format (.mp3, .wav, or .ogg)
4. Adjust voice settings if desired
5. Click "▶️ Start Conversion"
6. Observe progress bar and status updates
7. Wait for completion
8. Verify audio files are created in output directory

**Expected Results**:
- ✅ Conversion starts successfully
- ✅ Progress bar updates during conversion
- ✅ Status messages update appropriately
- ✅ Audio files are created correctly
- ✅ Files are in selected format

**Error Cases to Test**:
- No files added → Should show validation error
- No output directory → Should show validation error
- Invalid text file → Should handle gracefully

**Pass/Fail**: __________

---

### Test 8: Merger View - File Management

**Objective**: Test audio file list management

**Steps**:
1. Navigate to Merger view
2. Click "➕ Add Files" button
3. Select multiple audio files (.mp3, .wav, .ogg)
4. Verify files appear in list with indices
5. Click "↑" button on a file item
6. Verify file moves up in list
7. Click "↓" button on a file item
8. Verify file moves down in list
9. Click "✖️" button on a file item
10. Verify file is removed
11. Click "Auto-sort by filename" button
12. Verify files are sorted alphabetically

**Expected Results**:
- ✅ Files can be added via dialog
- ✅ Files can be reordered (up/down)
- ✅ Files can be removed
- ✅ Auto-sort works correctly

**Pass/Fail**: __________

---

### Test 9: Merger View - Audio Merging

**Objective**: Test audio file merging

**Prerequisites**:
- Multiple audio files added
- pydub and ffmpeg installed

**Steps**:
1. Add multiple audio files to Merger view
2. Click "Browse" to select output file
3. Set silence duration (0-10 seconds)
4. Click "▶️ Start Merging"
5. Observe progress bar and status updates
6. Wait for completion
7. Verify merged audio file is created
8. Play merged file to verify quality

**Expected Results**:
- ✅ Merging starts successfully
- ✅ Progress bar updates during merging
- ✅ Merged file is created correctly
- ✅ Silence is inserted between files (if duration > 0)
- ✅ Audio quality is maintained

**Error Cases to Test**:
- No files added → Should show validation error
- No output file selected → Should show validation error
- pydub not installed → Should show helpful error message

**Pass/Fail**: __________

---

### Test 10: Full Auto View - Queue Management

**Objective**: Test queue system

**Steps**:
1. Navigate to Full Auto view
2. Click "➕ Add to Queue" button
3. Enter a valid novel URL
4. Enter a title (or leave blank for auto-title)
5. Click OK
6. Verify item appears in queue
7. Add multiple items to queue
8. Use "↑" and "↓" buttons to reorder items
9. Click "✖️ Remove" on an item
10. Verify item is removed
11. Click "🗑️ Clear Queue" button
12. Verify all items are removed

**Expected Results**:
- ✅ Add to queue dialog works
- ✅ Queue items display correctly
- ✅ Reordering works
- ✅ Removal works
- ✅ Clear queue works

**Error Cases to Test**:
- Invalid URL → Should show validation error
- Empty URL → Should show validation error

**Pass/Fail**: __________

---

### Test 11: Full Auto View - Processing

**Objective**: Test full automation pipeline

**Prerequisites**:
- Valid novel URL in queue
- Internet connection

**Steps**:
1. Add a novel URL to queue
2. Click "▶️ Start Processing"
3. Observe "Currently Processing" section
4. Verify progress bar updates
5. Verify status messages update
6. Test pause/resume functionality
7. Wait for completion
8. Verify queue item status changes to "Completed"
9. Verify next item in queue auto-starts (if available)

**Expected Results**:
- ✅ Processing starts successfully
- ✅ Progress tracking works
- ✅ Status updates are accurate
- ✅ Pause/resume works
- ✅ Queue status updates correctly
- ✅ Auto-start next item works

**Error Cases to Test**:
- Invalid URL → Should show error and mark as "Failed"
- Network error → Should handle gracefully
- Stop all → Should stop current processing

**Pass/Fail**: __________

---

## 🐛 Known Issues & Limitations

### Current Limitations
1. **Styling**: No custom styling yet (default Qt appearance)
2. **Error Recovery**: Limited error recovery mechanisms
3. **Progress Accuracy**: Progress may not be 100% accurate for all operations
4. **Voice Preview**: Requires system audio player

### Dependencies
- **pydub**: Required for audio merging (optional, shows error if missing)
- **ffmpeg**: Required by pydub for format conversion
- **Edge-TTS**: Required for TTS functionality

---

## 📊 Test Results Template

### Test Session Report

**Date**: __________  
**Tester**: __________  
**Version**: 1.0  
**Environment**: __________

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | General UI Navigation | ⬜ Pass / ⬜ Fail | |
| 2 | Scraper - Basic | ⬜ Pass / ⬜ Fail | |
| 3 | Scraper - Chapter Selection | ⬜ Pass / ⬜ Fail | |
| 4 | Scraper - Pause/Stop | ⬜ Pass / ⬜ Fail | |
| 5 | TTS - File Selection | ⬜ Pass / ⬜ Fail | |
| 6 | TTS - Voice Settings | ⬜ Pass / ⬜ Fail | |
| 7 | TTS - Conversion | ⬜ Pass / ⬜ Fail | |
| 8 | Merger - File Management | ⬜ Pass / ⬜ Fail | |
| 9 | Merger - Audio Merging | ⬜ Pass / ⬜ Fail | |
| 10 | Full Auto - Queue | ⬜ Pass / ⬜ Fail | |
| 11 | Full Auto - Processing | ⬜ Pass / ⬜ Fail | |

**Overall Status**: ⬜ Ready for Production / ⬜ Needs Fixes

**Issues Found**:
1. __________
2. __________
3. __________

---

## 🔄 Next Steps After Testing

1. **Document Issues**: Record all bugs and issues found
2. **Prioritize Fixes**: Categorize issues by severity
3. **Create Fixes**: Address critical issues first
4. **Re-test**: Verify fixes work correctly
5. **Automated Tests**: Create unit and integration tests
6. **Styling**: Add custom styling and theming
7. **Performance**: Optimize for large operations

---

**Last Updated**: 2025-12-06  
**Status**: Ready for Testing

