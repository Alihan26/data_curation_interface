#!/usr/bin/env python3
"""Fix indentation in scraper.py"""

with open('backend/services/scraper.py', 'r') as f:
    lines = f.readlines()

# Fix line 443 (index 442) - add 4 more spaces
if lines[442].strip().startswith('paragraphs.append'):
    lines[442] = '                    paragraphs.append(text)\n'
    print("Fixed line 443 indentation")
else:
    print("Line 443 doesn't match expected content")
    print(f"Found: {repr(lines[442])}")

with open('backend/services/scraper.py', 'w') as f:
    f.writelines(lines)

print("Done!")

