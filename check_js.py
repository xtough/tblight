import re

with open('C:/SAPDevelop/tb/static/app.js', encoding='utf-8') as f:
    src = f.read()
    lines = src.splitlines()

# Find lines with 3+ backticks — these have nested template literals
for i, line in enumerate(lines, 1):
    bt = line.count('`')
    if bt >= 3:
        print(f'L{i} ({bt} backticks): {line.strip()}')
