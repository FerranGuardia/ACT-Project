import re

# Test JSON patterns
html = 'JSON.parse(\'{"chapters": ["/chapters/1", "/chapters/2"]}\')'
json_patterns = [
    r'JSON\.parse\(\s*[\'"]([^\'"]*chapters?[^\'"]*)[\'"]\s*\)',
    r'JSON\.parse\(\s*`([^`]*(?:chapters?|chapters?_list)[^`]*)`\s*\)',
]

print("Testing JSON patterns on:", repr(html))

for i, pattern in enumerate(json_patterns):
    print(f"\nTesting pattern {i}: {pattern}")
    matches = list(re.finditer(pattern, html, re.IGNORECASE | re.DOTALL))
    print(f'  Matches: {len(matches)}')
    for match in matches:
        print(f'  Full match: {repr(match.group(0))}')
        print(f'  Group 1: {repr(match.group(1))}')