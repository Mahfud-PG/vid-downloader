import re
with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''    def bg_search(self, query):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'extractor_args': {'youtube': ['player_client=android,web']}
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if query.startswith("http://") or query.startswith("https://"):'''

replacement = '''    def bg_search(self, query):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'extractor_args': {'youtube': ['player_client=android,web']}
        }
        try:
            if query.lower().startswith("album:"):
                try:
                    from ytmusicapi import YTMusic
                except ImportError:
                    self.signals.finished.emit("Error: ytmusicapi belum diinstall.", False)
                    return
                yt = YTMusic()
                clean_query = query[6:].strip()
                results = yt.search(clean_query, filter='albums')
                entries = []
                for res in results:
                    title = res.get('title', 'Unknown Album')
                    artists = ", ".join([a['name'] for a in res.get('artists', [])])
                    year = res.get('year', '')
                    display_title = f"{title} ({year}) - {artists}" if year else f"{title} - {artists}"
                    thumbs = res.get('thumbnails', [])
                    thumb_url = thumbs[-1]['url'] if thumbs else None
                    entries.append({
                        'title': display_title,
                        '__is_ytmusic_album': True,
                        'browseId': res.get('browseId'),
                        'playlistId': res.get('playlistId'),
                        'thumbnail': thumb_url,
                        'webpage_url': f"https://music.youtube.com/playlist?list={res.get('playlistId')}"
                    })
            else:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    if query.startswith("http://") or query.startswith("https://"):'''

c = c.replace(target, replacement)

target2 = '''                    else:
                        entries = [info]
                else:
                    info = ydl.extract_info(f"ytsearch10:{query}", download=False)
                    entries = info.get('entries', [])
                
                # Download thumbnails concurrently'''

replacement2 = '''                        else:
                            entries = [info]
                    else:
                        info = ydl.extract_info(f"ytsearch10:{query}", download=False)
                        entries = info.get('entries', [])
                
                # Download thumbnails concurrently'''

c = c.replace(target2, replacement2)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
