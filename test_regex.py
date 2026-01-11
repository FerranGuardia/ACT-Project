import re

html = '''JSON.parse('{"chapters": ['/chapter-7', '/chapter-8']}');'''
pattern1 = r'JSON\.parse\(\s*[\'"]([^\'"]*(?:chapters?|chapters?_list)[^\'"]*)[\'"]\s*\)'
pattern2 = r'JSON\.parse\(\s*[\'"](.*?)[\'"]\s*\)'

print(f"HTML: {html}")
print(f"Pattern1: {pattern1}")
print(f"Pattern2: {pattern2}")

matches1 = list(re.finditer(pattern1, html, re.IGNORECASE | re.DOTALL))
print(f'Matches1: {len(matches1)}')
for match in matches1:
    print(f'Match1: {match.group(1)}')

matches2 = list(re.finditer(pattern2, html, re.IGNORECASE | re.DOTALL))
print(f'Matches2: {len(matches2)}')
for match in matches2:
    print(f'Match2: {match.group(1)}')