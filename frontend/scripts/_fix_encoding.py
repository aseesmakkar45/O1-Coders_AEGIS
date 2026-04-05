import re

filepath = r'c:\Users\lenovo\Desktop\#JOURNEY\Hackathons\ROSETTA HACKATHON\rosetta\frontend\index.html'

with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Fix corrupted em-dashes (various encodings)
# Common mojibake patterns for em-dash (U+2014):
content = content.replace('\u00e2\u0080\u0094', '\u2014')  # UTF-8 bytes as latin-1
content = content.replace('\u00e2\u0080\u201c', '\u2014')  # another variant
content = content.replace('-\u201d', '\u2014')  # -" pattern
content = content.replace('-"', '\u2014')  # plain -"
content = content.replace('\ufffd', '-')  # replacement character

# Also fix any remaining mojibake
content = content.replace('\u00c3\u00a2\u00e2\u201a\u00ac\u201c', '-')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing encoding")
