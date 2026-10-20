with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''                    self.format_menu.setFocus()'''
replacement = '''                    self.url_entry.setFocus()'''
c = c.replace(target, replacement)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
