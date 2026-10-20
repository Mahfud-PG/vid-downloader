with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(581, 599):
    if lines[i].startswith('    '):
        lines[i] = lines[i][4:]

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
