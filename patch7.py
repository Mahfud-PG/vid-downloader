with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''    def on_search_finished(self, entries):
        self.last_search_entries = entries'''
replacement = '''    def on_search_finished(self, entries):
        self.results_list.clear()
        self.last_search_entries = entries'''
c = c.replace(target, replacement)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
