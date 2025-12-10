# Robustness Test Suite

Personal test suite for testing the full pipeline with multiple URLs from different websites to assess software robustness.

## Overview

This test suite runs the complete ACT pipeline (URL → Scraping → TTS → Audio Files) on multiple novels from different websites to verify:
- Compatibility with different website structures
- Robustness of the scraper across various sites
- TTS conversion reliability
- Overall pipeline stability

## Structure

```
tests/robustness_tests/
├── test_config.json      # Test configuration with URLs and settings
├── run_tests.py          # Main test runner script
├── run_tests.bat         # Windows batch file to launch tests
├── README.md             # This file
├── output/               # Test outputs (created automatically)
│   ├── novel_1/          # Isolated output for each test
│   └── novel_2/
└── summary/              # Summary reports (created automatically)
    └── test_summary_YYYYMMDD_HHMMSS.md
```

## Usage

### Quick Start

**Windows (from anywhere):**
```powershell
cd C:\Users\Nitropc\Desktop\ACT\tests\robustness_tests
.\run_tests.bat
```

**Windows (from project root `C:\Users\Nitropc\Desktop\ACT`):**
```powershell
cd tests\robustness_tests
.\run_tests.bat
```

**Windows (direct path from project root):**
```powershell
.\tests\robustness_tests\run_tests.bat
```

**Manual (from project root):**
```bash
cd tests/robustness_tests
python run_tests.py
```

**Manual (direct path from project root):**
```bash
python tests/robustness_tests/run_tests.py
```

### Configuration

Edit `test_config.json` to add, remove, or modify test URLs:

```json
{
  "tests": [
    {
      "url": "https://example.com/novel",
      "title": "Novel Title",
      "website": "example.com",
      "chapters": 2,
      "voice": "en-US-AndrewNeural",
      "provider": "edge_tts"
    }
  ],
  "settings": {
    "output_dir": "output",
    "summary_dir": "summary",
    "continue_on_error": true,
    "clear_project_data_after_test": true
  }
}
```

### Test Configuration Fields

- **url**: Novel URL to test (TOC URL)
- **title**: Display name for the novel
- **website**: Website name (for reporting)
- **chapters**: Number of chapters to test (1-2 recommended for quick testing)
- **voice**: TTS voice to use (optional, defaults to config)
- **provider**: TTS provider (optional, defaults to edge_tts)

## Current Test URLs

The suite currently tests 5 different websites:

1. **Royal Road** - The Mine Lord: A Dwarven Survival Base-Builder
2. **novelbin.me** - The Archmage's Restaurant
3. **novelfull.net** - Bringing culture to a different world
4. **fanmtl.com** - Apocalypse: System of lotteries
5. **empirenovel.com** - Black Tech Internet Cafe System

## Output

### Test Outputs

Each test creates an isolated output directory in `output/{sanitized_title}/` containing:
- Text files (scraped chapters)
- Audio files (TTS converted chapters)
- Project data files

### Summary Report

After all tests complete, a markdown summary report is generated in `summary/test_summary_YYYYMMDD_HHMMSS.md` containing:

- **Overall Statistics**: Total tests, success rate, duration
- **What Worked**: List of successful tests with details
- **What Didn't Work**: List of failed tests with error summaries
- **Detailed Results**: Full details for each test including errors and warnings

## Features

- **Isolated Outputs**: Each test gets its own output directory
- **Error Isolation**: Tests continue even if one fails (configurable)
- **Comprehensive Reporting**: Markdown summary with statistics
- **Easy Configuration**: JSON-based config for easy URL management
- **Quick Testing**: Only 1-2 chapters per URL for fast execution

## Notes

- Tests are designed to be quick (1-2 chapters per URL)
- Output files are kept for inspection
- Project data is cleared after each test (configurable)
- All tests run sequentially with small delays between them

## Adding New Tests

To add a new test URL:

1. Open `test_config.json`
2. Add a new entry to the `tests` array:
   ```json
   {
     "url": "https://new-site.com/novel",
     "title": "Novel Title",
     "website": "new-site.com",
     "chapters": 2,
     "voice": "en-US-AndrewNeural",
     "provider": "edge_tts"
   }
   ```
3. Run `run_tests.bat` or `python run_tests.py`

## Troubleshooting

- **Import errors**: Ensure ACT project structure is correct and `src/` directory exists
- **Network errors**: Some tests may fail due to network issues or site changes
- **TTS errors**: Check that Edge TTS or pyttsx3 is properly configured
- **Output directory**: Ensure write permissions for `output/` and `summary/` directories

