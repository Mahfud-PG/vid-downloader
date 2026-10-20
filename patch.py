with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'self.download_path = self.settings.value("download_path", os.path.join(os.path.expanduser("~"), "Downloads", "Vid Downloader"))',
    'self.download_path = self.settings.value("download_path", os.path.join(os.path.expanduser("~"), "Downloads", "Vid Downloader"))\n        self.saved_album_entries = None\n        self.last_search_entries = None'
)

c = c.replace(
    '    def on_search_finished(self, entries):\n        self.status_label.setText(self.tr("status_found", len(entries)))',
    '    def on_search_finished(self, entries):\n        self.last_search_entries = entries\n        self.status_label.setText(self.tr("status_found", len(entries)))'
)

c = c.replace(
    '''            item_data = {
                'url': url,
                'playlist_title': item.get('__playlist_title'),
                'playlist_index': item.get('__playlist_index')
            }''',
    '''            item_data = {
                'url': url,
                'title': title,
                'playlist_title': item.get('__playlist_title'),
                'playlist_index': item.get('__playlist_index'),
                '__is_ytmusic_album': item.get('__is_ytmusic_album'),
                'browseId': item.get('browseId'),
                'playlistId': item.get('playlistId')
            }'''
)

c = c.replace(
    '    def perform_search_or_resolve(self):',
    '''    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Escape:
            if getattr(self, "saved_album_entries", None) is not None:
                self.results_list.clear()
                self.on_search_finished(self.saved_album_entries)
                self.saved_album_entries = None
                self.status_label.setText(self.tr("status_found", self.results_list.count()))
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def perform_search_or_resolve(self):'''
)

c = c.replace(
    '''    def on_list_item_activated(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            url = data.get('url')
            if url:
                self.url_entry.setText(url)''',
    '''    def bg_fetch_album_tracks(self, browse_id, album_title):
        try:
            from ytmusicapi import YTMusic
            yt = YTMusic()
            album = yt.get_album(browse_id)
            tracks = album.get('tracks', [])
            entries = []
            for i, t in enumerate(tracks):
                track_title = t.get('title', 'Unknown Track')
                duration = t.get('duration_seconds')
                vid = t.get('videoId')
                if not vid: continue
                entries.append({
                    'title': f"{i+1:02d}. {track_title}",
                    'url': f"https://music.youtube.com/watch?v={vid}",
                    'duration': duration,
                    '__is_ytmusic_album': False,
                    '__playlist_title': album_title,
                    '__playlist_index': i + 1
                })
            self.signals.search_finished.emit(entries)
        except Exception as e:
            self.signals.finished.emit(f"Error fetching album: {str(e)[:50]}", False)

    def on_list_item_activated(self, item):
        from PyQt6.QtCore import Qt
        import threading
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            if data.get('__is_ytmusic_album'):
                browse_id = data.get('browseId')
                album_title = data.get('title') or item.text()
                if browse_id:
                    self.saved_album_entries = self.last_search_entries
                    self.status_label.setText(self.tr("search_searching") if self.current_lang == "id" else "Fetching album tracks...")
                    threading.Thread(target=self.bg_fetch_album_tracks, args=(browse_id, album_title), daemon=True).start()
                return

            url = data.get('url')
            if url:
                self.url_entry.setText(url)'''
)

c = c.replace(
    '''            if pl_title:
                outtmpl = os.path.join(self.download_path, pl_title, '%(title)s.%(ext)s')
            else:
                outtmpl = os.path.join(self.download_path, '%(title)s.%(ext)s')''',
    '''            if pl_title:
                outtmpl = os.path.join(self.download_path, pl_title, '%(playlist_index)02d. %(title)s.%(ext)s')
            else:
                outtmpl = os.path.join(self.download_path, '%(title)s.%(ext)s')'''
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
