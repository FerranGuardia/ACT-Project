# Scraper Test UI

A standalone test interface for manually testing the scraper module.

## Purpose

This UI allows you to test the scraper functionality without running automated tests. It's useful for:
- Testing with real URLs
- Debugging scraper issues
- Verifying scraper behavior
- Manual testing before committing

## How to Run

1. Make sure you're in the ACT project root directory
2. Run the script:
   ```bash
   python test_scraper_ui.py
   ```

## Features

### Tab 1: Configuration
- **Base URL**: The base URL of the webnovel site (e.g., `https://novelbin.me`)
- **TOC URL**: The table of contents URL (e.g., `https://novelbin.me/novel-book/novel-name#tab-chapters-title`)

### Tab 2: Test Scraping
- **Test Options**:
  - Get Chapter Count (Reference) - Uses Playwright to get the reference count
  - Fetch Chapter URLs - Tests all URL fetching methods
  - Scrape Chapter Content - Tests content scraping on the first chapter
- **Results**: Shows test results in a text area

### Tab 3: Logs
- Shows application logs
- Can be cleared with the "Clear Logs" button

## Example Usage

1. Open the UI
2. Go to Configuration tab
3. Enter:
   - Base URL: `https://novelbin.me`
   - TOC URL: `https://novelbin.me/novel-book/the-archmages-restaurant#tab-chapters-title`
4. Go to Test Scraping tab
5. Select which tests you want to run
6. Click "▶ Start Test"
7. View results in the Results area and logs in the Logs tab

## Notes

- This is a standalone test tool, not part of the git workflow
- It uses the scraper modules from `src/scraper/`
- All tests run in a separate thread so the UI stays responsive
- You can stop tests at any time with the "⏹ Stop" button

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- All scraper dependencies (requests, beautifulsoup4, playwright, etc.)

