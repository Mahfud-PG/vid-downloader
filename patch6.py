with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

lines[598] = '        except Exception as e:\n'
lines[599] = '            self.signals.finished.emit(f"Error: {str(e)[:50]}", False)\n'

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
