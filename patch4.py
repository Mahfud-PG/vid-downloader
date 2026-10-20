with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''                        if 'entries' in info:
                            entries = info['entries']
                            pl_title = info.get('title')
                            for i, e in enumerate(entries):
                                if e:
                                    e['__playlist_title'] = pl_title
                                    e['__playlist_index'] = i + 1
                            else:
                                entries = [info]
                        else:
                        info = ydl.extract_info(f"ytsearch10:{query}", download=False)
                        entries = info.get('entries', [])'''

replacement = '''                        if 'entries' in info:
                            entries = info['entries']
                            pl_title = info.get('title')
                            for i, e in enumerate(entries):
                                if e:
                                    e['__playlist_title'] = pl_title
                                    e['__playlist_index'] = i + 1
                        else:
                            entries = [info]
                    else:
                        info = ydl.extract_info(f"ytsearch10:{query}", download=False)
                        entries = info.get('entries', [])'''

c = c.replace(target, replacement)
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
