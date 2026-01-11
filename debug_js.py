import sys
sys.path.insert(0, 'src')
from scraper.strategies.javascript_strategy import JavaScriptStrategy
from unittest.mock import Mock

# Create strategy instance
mock_session_manager = Mock()
strategy = JavaScriptStrategy('https://example.com', mock_session_manager)

html_content = """
<script>
var chapters = ["/chapter-1", "/chapter-2"];
let chapterList = ["/chapter-3", "/chapter-4"];
const data = {"urls": ["/chapter-5", "/chapter-6"]};
JSON.parse('{"chapters": ["/chapter-7", "/chapter-8"]}');
</script>
"""

print('HTML content:')
print(repr(html_content))

urls = strategy._extract_from_javascript(html_content)
print(f'Extracted URLs: {urls}')

# Test individual patterns
import re

# Pattern 1: Direct array assignments
array_patterns = [
    r'chapters\s*[:=]\s*\[([^\]]+)\]',
    r'chapterList\s*[:=]\s*\[([^\]]+)\]',
    r'chapterUrls\s*[:=]\s*\[([^\]]+)\]',
    r'chaptersArray\s*[:=]\s*\[([^\]]+)\]',
    r'chapter_data\s*[:=]\s*\[([^\]]+)\]',
    r'window\.chapters\s*[:=]\s*\[([^\]]+)\]',
    r'var\s+chapters\s*[:=]\s*\[([^\]]+)\]',
    r'let\s+chapters\s*[:=]\s*\[([^\]]+)\]',
    r'const\s+chapters\s*[:=]\s*\[([^\]]+)\]',
]

print("\nTesting array patterns:")
for i, pattern in enumerate(array_patterns):
    matches = list(re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL))
    print(f"Pattern {i}: {pattern}")
    print(f"  Matches: {len(matches)}")
    for match in matches:
        print(f"  Match: {match.group(1)}")

# Test object patterns
object_patterns = [
    r'chapters\s*[:=]\s*\{[^}]*["\']?urls?["\']?\s*:\s*\[([^\]]+)\]',
    r'chapterList\s*[:=]\s*\{[^}]*["\']?data["\']?\s*:\s*\[([^\]]+)\]',
    r'data\s*[:=]\s*\{[^}]*["\']?urls?["\']?\s*:\s*\[([^\]]+)\]',
]

print("\nTesting object patterns:")
for i, pattern in enumerate(object_patterns):
    matches = list(re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL))
    print(f"Pattern {i}: {pattern}")
    print(f"  Matches: {len(matches)}")
    for match in matches:
        print(f"  Match: {match.group(1)}")

# Test JSON patterns
json_patterns = [
    r'JSON\.parse\(\s*[\'"](.*?)[\'"]\s*\)',
    r'JSON\.parse\(\s*`(.*?)`\s*\)',
]

print("\nTesting JSON patterns:")
for i, pattern in enumerate(json_patterns):
    matches = list(re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL))
    print(f"Pattern {i}: {pattern}")
    print(f"  Matches: {len(matches)}")
    for match in matches:
        print(f"  Match: {match.group(1)}")
        # Test parsing the JSON content
        json_str = match.group(1)
        print(f"  JSON string: {json_str}")
        # Check if it has chapter keywords
        chapter_keywords = ['chapter', 'chapters', 'chapterlist', 'urls']
        has_chapter = any(keyword in json_str.lower() for keyword in chapter_keywords)
        print(f"  Has chapter keywords: {has_chapter}")
        if has_chapter:
            try:
                import json
                data = json.loads(json_str)
                print(f"  Parsed data: {data}")
            except:
                print(f"  Failed to parse JSON")

# Test chapter URL validation
print("\nTesting chapter URL validation:")
test_urls = ["/chapter-1", "/chapter-2", "/chapter-3", "/chapter-4", "/chapter-5", "/chapter-6", "/chapter-7", "/chapter-8"]
for url in test_urls:
    is_likely = strategy._is_likely_chapter_url(url)
    print(f"  {url}: {is_likely}")