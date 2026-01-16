# Isolated URL Extraction Testing

This directory contains tools for isolated testing of the URL extraction pipeline without running the full ACT application.

## Quick Start

### Test a Single Novel URL

To test URL extraction for a single novel:

```bash
python tests/scripts/isolated_url_extraction_test.py <toc_url> [output_file]
```

Example:
```bash
python tests/scripts/isolated_url_extraction_test.py https://novelfull.net/black-tech-internet-cafe-system.html
```

This will:
- Extract all chapter URLs from the table of contents page
- Save them to a text file in `isolated_test_output/`
- Display a summary of the results

### Test Multiple Novels

To test multiple novels and get a comprehensive report:

```bash
cd tests/scripts
python run_isolated_tests.py test_config.json
```

## Configuration

Create a `test_config.json` file to define multiple tests:

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
  "output_dir": "isolated_test_output"
}
```

## Output Files

### Individual Test Results

For each novel tested, you'll get:
- `isolated_test_output/{novel_name}_chapter_urls.txt` - All extracted chapter URLs
- JSON report with detailed results and timing information

### Summary Report

The test runner generates a comprehensive JSON report with:
- Success/failure counts
- Chapter counts vs expected counts
- Timing information
- Error details for failed tests

## Troubleshooting

### Common Issues

1. **Unicode Encoding Errors**: Fixed in the scripts - they now use ASCII-safe characters.

2. **Network Timeouts**: The scraper has built-in retry logic and timeout handling.

3. **Invalid URLs**: URLs are validated before processing.

### Debug Logging

The scripts use the ACT logging system. To see detailed logs, check the console output or ACT log files.

## Current Test Results

### Black Tech Internet Cafe System
- **URL**: https://novelfull.net/black-tech-internet-cafe-system.html
- **Status**: ✅ Working
- **Chapters Found**: 55
- **Detection Method**: JavaScript array parsing (most reliable)

The URL extraction is working correctly for this novel. The scraper successfully identifies all 55 chapters using the JavaScript variable extraction method.

## Adding New Test Cases

To add a new novel to test:

1. Find the table of contents URL for the novel
2. Add it to `test_config.json`:
   ```json
   {
     "name": "New Novel Title",
     "toc_url": "https://example.com/novel-toc.html",
     "expected_chapters": null  // Set to expected count if known
   }
   ```
3. Run the test suite

## Integration with Full Pipeline

Once URL extraction works, you can proceed to test:
1. Chapter content scraping
2. Text processing and cleaning
3. Audio generation

The isolated testing helps identify exactly where in the pipeline issues occur.