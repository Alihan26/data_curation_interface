#!/usr/bin/env python3
"""Fix all indentation issues in scraper.py"""

with open('backend/services/scraper.py', 'r') as f:
    lines = f.readlines()

fixes = []

# Fix line 511 (index 510)
if 510 < len(lines) and lines[510].strip().startswith('items.append'):
    lines[510] = '                        items.append(item_text)\n'
    fixes.append("Fixed line 511")

with open('backend/services/scraper.py', 'w') as f:
    f.writelines(lines)

print(f"Applied {len(fixes)} fixes:")
for fix in fixes:
    print(f"  - {fix}")

