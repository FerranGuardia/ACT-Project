# Isolated Testing Directory

This directory contains tools for isolated testing of the ACT scraping pipeline without running the full application.

## Directory Structure

```
isolated_testing/
├── isolated_url_extraction_test.py  # Single novel URL testing
├── run_isolated_tests.py           # Multi-novel testing runner
├── test_config.json                # Test configuration
├── output/                         # Test results and reports
└── README.md                       # This file
```

## Quick Start

### Test a Single Novel URL

```bash
python isolated_testing/isolated_url_extraction_test.py <toc_url> [output_file]
```

Example:
```bash
python isolated_testing/isolated_url_extraction_test.py https://novelfull.net/black-tech-internet-cafe-system.html
```

### Test Multiple Novels

```bash
python isolated_testing/run_isolated_tests.py test_config.json
```

## Configuration

Edit `test_config.json` to define multiple tests:

```json
{
  "tests": [
    {
      "name": "Black Tech Internet Cafe System",
      "toc_url": "https://novelfull.net/black-tech-internet-cafe-system.html",
      "expected_chapters": 55
    },
    {
      "name": "Another Novel",
      "toc_url": "https://example.com/novel-toc.html",
      "expected_chapters": 120
    }
  ],
  "output_dir": "isolated_testing/output"
}
```

## Output Files

- `output/{novel_name}_chapter_urls.txt` - Extracted chapter URLs
- `output/test_report_*.json` - Detailed test results and timing

## Current Test Results

### Black Tech Internet Cafe System
- **URL**: https://novelfull.net/black-tech-internet-cafe-system.html
- **Status**: ✅ Working (55 chapters extracted)
- **Method**: JavaScript array parsing

## Adding New Tests

1. Add novel to `test_config.json`
2. Run the test suite
3. Check results in `output/` directory

## Troubleshooting

- Check console output for detailed logs
- Failed tests will show error messages in reports
- URLs are validated before processing
- Network timeouts are handled automatically