import os
import sys
import threading
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QProgressBar, QFileDialog, QMessageBox, QGroupBox,
                             QDialog, QListWidget, QListWidgetItem, QMenu)
from PyQt6.QtCore import pyqtSignal, QObject, Qt, QEvent, QUrl, QSettings
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import yt_dlp
import imageio_ffmpeg

def get_ffmpeg_path():
    return imageio_ffmpeg.get_ffmpeg_exe()

class WorkerSignals(QObject):
    progress = pyqtSignal(float, str)
    finished = pyqtSignal(str, bool)
    search_finished = pyqtSignal(list)
    play_ready = pyqtSignal(str)

class PlayerSignals(QObject):
    stream_ready = pyqtSignal(str)
    fetch_error = pyqtSignal(str)

class CustomPlayerDialog(QDialog):
    def __init__(self, youtube_urls, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vid Downloader - Player")
        self.resize(800, 600)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.youtube_urls = youtube_urls if isinstance(youtube_urls, list) else [youtube_urls]
        self.current_idx = 0
        self.current_temp_file = None
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)
        
        self.loading_label = QLabel("Memuat video...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: white; font-size: 18px; background-color: black;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.video_widget)
        self.setLayout(layout)
        
        self.audio_output.setVolume(0.5)
        
        self.is_stalled = False
        self.is_repeat_all = False
        self.ab_loop_active = False
        self.loop_start = 0
        self.loop_end = 0
        
        self.player.errorOccurred.connect(self.handle_error)
        self.player.mediaStatusChanged.connect(self.handle_status)
        self.player.positionChanged.connect(self.handle_position)
        
        self.signals = PlayerSignals()
        self.signals.stream_ready.connect(self.on_stream_ready)
        self.signals.fetch_error.connect(self.on_fetch_error)
        
        self.play_current_index()

    def play_current_index(self):
        if self.current_idx >= len(self.youtube_urls):
            if self.is_repeat_all and len(self.youtube_urls) > 0:
                self.current_idx = 0
            else:
                self.accept()
                return
        elif self.current_idx < 0:
            if self.is_repeat_all and len(self.youtube_urls) > 0:
                self.current_idx = len(self.youtube_urls) - 1
            else:
                self.current_idx = 0
                
        self.cleanup_temp_file()
        
        self.ab_loop_active = False
        self.loop_start = 0
        self.loop_end = 0
        
        self.video_widget.hide()
        self.loading_label.show()
        url = self.youtube_urls[self.current_idx]
        title = f"Memuat ({self.current_idx + 1}/{len(self.youtube_urls)})..."
        self.setWindowTitle(title)
        self.loading_label.setText(title)
        
        threading.Thread(target=self.bg_fetch, args=(url,), daemon=True).start()

    def bg_fetch(self, url):
        ydl_opts = {
            'quiet': True,
            'extractor_args': {'youtube': ['player_client=android,web']}
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                extractor = info.get('extractor_key', '').lower()
                import tempfile
                temp_dir = tempfile.gettempdir()
                video_id = info.get('id', 'temp')
                
                if extractor == 'tiktok':
                    temp_file = os.path.join(temp_dir, f"tiktok_vid_downloader_{video_id}.mp4")
                    if not os.path.exists(temp_file):
                        dl_opts = {'format': 'best', 'quiet': True, 'outtmpl': temp_file}
                        with yt_dlp.YoutubeDL(dl_opts) as ydl_dl:
                            ydl_dl.download([url])
                else:
                    temp_file = os.path.join(temp_dir, f"yt_vid_downloader_{video_id}.mp4")
                    if not os.path.exists(temp_file):
                        dl_opts = {
                            'format': 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst',
                            'quiet': True,
                            'outtmpl': temp_file,
                            'extractor_args': {'youtube': ['player_client=android,web']},
                            'ffmpeg_location': imageio_ffmpeg.get_ffmpeg_exe()
                        }
                        with yt_dlp.YoutubeDL(dl_opts) as ydl_dl:
                            ydl_dl.download([url])
                            
            self.signals.stream_ready.emit(temp_file)
        except Exception as e:
            self.signals.fetch_error.emit(str(e))

    def on_stream_ready(self, stream_url):
        self.current_temp_file = stream_url
        self.loading_label.hide()
        self.video_widget.show()
        self.setWindowTitle(f"Vid Downloader - Player ({self.current_idx + 1}/{len(self.youtube_urls)})")
        
        self.player.setSource(QUrl.fromLocalFile(stream_url))
        self.is_stalled = False
        self.player.play()
        
    def on_fetch_error(self, error):
        reply = QMessageBox.warning(self, "Error", f"Gagal memuat video: {error[:50]}\nLanjut ke video berikutnya?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.current_idx += 1
            self.play_current_index()
        else:
            self.accept()

    def handle_error(self, error, error_string):
        self.is_stalled = True
        QMessageBox.warning(self, "Error Player", error_string)
        self.current_idx += 1
        self.play_current_index()

    def handle_status(self, status):
        if status in (QMediaPlayer.MediaStatus.StalledMedia, QMediaPlayer.MediaStatus.InvalidMedia):
            self.is_stalled = True
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.current_idx += 1
            self.play_current_index()
        else:
            self.is_stalled = False

    def handle_position(self, position):
        if self.ab_loop_active and self.loop_end > 0:
            if position >= self.loop_end:
                self.player.setPosition(self.loop_start)

    def keyPressEvent(self, event):
        if self.is_stalled and event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Right, Qt.Key.Key_Left, Qt.Key.Key_S, Qt.Key.Key_D, Qt.Key.Key_F, Qt.Key.Key_R, Qt.Key.Key_BracketLeft, Qt.Key.Key_BracketRight, Qt.Key.Key_Backslash, Qt.Key.Key_G, Qt.Key.Key_A):
            return
            
        try:
            if event.key() == Qt.Key.Key_Space:
                if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.player.pause()
                else:
                    self.player.play()
            elif event.key() == Qt.Key.Key_Up:
                vol = self.audio_output.volume()
                self.audio_output.setVolume(min(1.0, vol + 0.1))
            elif event.key() == Qt.Key.Key_Down:
                vol = self.audio_output.volume()
                self.audio_output.setVolume(max(0.0, vol - 0.1))
            elif event.key() == Qt.Key.Key_Right:
                pos = self.player.position()
                self.player.setPosition(pos + 5000)
            elif event.key() == Qt.Key.Key_Left:
                pos = self.player.position()
                self.player.setPosition(max(0, pos - 5000))
            elif event.key() == Qt.Key.Key_G:
                if not self.is_stalled:
                    self.player.stop()
                self.current_idx += 1
                self.play_current_index()
            elif event.key() == Qt.Key.Key_A:
                if not self.is_stalled:
                    self.player.stop()
                self.current_idx -= 1
                self.play_current_index()
            elif event.key() == Qt.Key.Key_S:
                self.player.setPlaybackRate(0.5)
            elif event.key() == Qt.Key.Key_D:
                self.player.setPlaybackRate(1.0)
            elif event.key() == Qt.Key.Key_F:
                self.player.setPlaybackRate(2.0)
            elif event.key() == Qt.Key.Key_BracketLeft:
                self.loop_start = self.player.position()
                self.ab_loop_active = False 
                self.setWindowTitle(f"Vid Downloader - Player [Loop A: {self.loop_start}ms]")
            elif event.key() == Qt.Key.Key_BracketRight:
                if self.loop_start >= 0:
                    self.loop_end = self.player.position()
                    if self.loop_end > self.loop_start:
                        self.ab_loop_active = True
                        self.setWindowTitle(f"Vid Downloader - Player [Loop A-B Aktif]")
                        self.player.setPosition(self.loop_start)
            elif event.key() == Qt.Key.Key_Backslash:
                self.ab_loop_active = False
                self.setWindowTitle(f"Vid Downloader - Player (Loop A-B Batal)")
            elif event.key() == Qt.Key.Key_R:
                self.is_repeat_all = not self.is_repeat_all
                status = "Aktif" if self.is_repeat_all else "Mati"
                self.setWindowTitle(f"Vid Downloader - Player (Repeat Playlist: {status})")
            elif event.key() == Qt.Key.Key_Escape:
                if not self.is_stalled:
                    self.player.stop()
                self.accept()
            else:
                super().keyPressEvent(event)
        except Exception:
            pass

    def cleanup_temp_file(self):
        try:
            if self.current_temp_file and os.path.exists(self.current_temp_file):
                self.player.setSource(QUrl())
                os.remove(self.current_temp_file)
                self.current_temp_file = None
        except Exception:
            pass

    def accept(self):
        try:
            if not self.is_stalled:
                self.player.stop()
        except Exception:
            pass
        self.cleanup_temp_file()
        super().accept()

    def closeEvent(self, event):
        try:
            if not self.is_stalled:
                self.player.stop()
        except Exception:
            pass
        self.cleanup_temp_file()
        super().closeEvent(event)

class VidDownloaderApp(QWidget):
    LANG = {
        "id": {
            "title": "Vid Downloader",
            "search_hint": "Masukkan Judul Video atau Link, lalu tekan Enter:",
            "search_btn": "Cari / Tampilkan",
            "search_searching": "Mencari...",
            "status_found": "Ditemukan {} hasil.",
            "download_btn": "Download ({} - {})",
            "menu_copy_link": "Salin Link",
            "menu_settings": "Pengaturan",
            "menu_folder": "Ubah Folder Penyimpanan...",
            "menu_theme": "Tema",
            "menu_lang": "Bahasa",
            "menu_format": "Format Download",
            "menu_quality": "Kualitas Video",
            "audio_quality": "Kualitas Audio",
            "success": "Sukses",
            "success_msg": "Unduhan selesai dan berhasil disimpan!",
            "error": "Error",
            "downloading": "Mengunduh... {:.1f}% ({:.1f} MB/s)",
            "download_done": "Unduhan selesai! Sedang memproses..."
        },
        "en": {
            "title": "Vid Downloader",
            "search_hint": "Paste Video Link or Title, then press Enter:",
            "search_btn": "Search / View",
            "search_searching": "Searching...",
            "status_found": "Found {} results.",
            "download_btn": "Download ({} - {})",
            "menu_copy_link": "Copy Link",
            "menu_settings": "Settings",
            "menu_folder": "Change Download Folder...",
            "menu_theme": "Theme",
            "menu_lang": "Language",
            "menu_format": "Download Format",
            "menu_quality": "Video Quality",
            "audio_quality": "Audio Quality",
            "success": "Success",
            "success_msg": "Download finished and saved successfully!",
            "error": "Error",
            "downloading": "Downloading... {:.1f}% ({:.1f} MB/s)",
            "download_done": "Download finished! Processing..."
        }
    }

    def tr(self, key, *args):
        text = self.LANG.get(self.current_lang, self.LANG["id"]).get(key, key)
        if args:
            return text.format(*args)
        return text

    def __init__(self):
        super().__init__()
        
        self.settings = QSettings("VidDownloader", "App")
        self.current_lang = self.settings.value("lang", "id")
        self.current_theme = self.settings.value("theme", "Terang")
        self.current_format = self.settings.value("format", "Video (MP4)")
        self.current_quality = self.settings.value("quality", "1080p")
        
        self.video_qualities = ["1080p", "720p", "480p", "Terbaik"]
        self.audio_qualities = ["320kbps", "128kbps"]
        
        # fallback fix if they somehow saved an audio quality while video was selected
        if self.current_format == "Video (MP4)" and self.current_quality not in self.video_qualities:
            self.current_quality = "1080p"
        elif self.current_format == "Audio (MP3)" and self.current_quality not in self.audio_qualities:
            self.current_quality = "320kbps"
            
        self.setWindowTitle(self.tr("title"))
        self.resize(650, 550)
        
        self.signals = WorkerSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.finished.connect(self.download_finished)
        self.signals.search_finished.connect(self.on_search_finished)
        
        default_download_path = os.path.join(os.path.expanduser("~"), "Downloads", "vid downloader")
        self.download_path = self.settings.value("download_path", default_download_path)
        
        if not os.path.exists(self.download_path):
            try:
                os.makedirs(self.download_path)
            except Exception:
                self.download_path = default_download_path
                if not os.path.exists(self.download_path):
                    os.makedirs(self.download_path)

        self.apply_theme(self.current_theme)

        self.setup_ui()
        self.auto_paste_clipboard()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self.auto_paste_clipboard()
        super().changeEvent(event)

    def auto_paste_clipboard(self):
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text().strip()
            if text.startswith("http://") or text.startswith("https://"):
                # Avoid overriding if user has already typed something else that is not empty
                current_text = self.url_entry.text().strip()
                if not current_text or current_text == text:
                    self.url_entry.setText(text)
        except Exception:
            pass

    def apply_theme(self, theme_name):
        from PyQt6.QtGui import QPalette, QColor
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        self.current_theme = theme_name
        self.settings.setValue("theme", theme_name)
        
        if theme_name == "Gelap":
            p = QPalette()
            p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            p.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            p.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            p.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            p.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            p.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            p.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            app.setPalette(p)
        elif theme_name == "Biru Malam":
            p = QPalette()
            p.setColor(QPalette.ColorRole.Window, QColor(20, 25, 35))
            p.setColor(QPalette.ColorRole.WindowText, QColor(200, 210, 220))
            p.setColor(QPalette.ColorRole.Base, QColor(10, 15, 20))
            p.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 25, 35))
            p.setColor(QPalette.ColorRole.ToolTipBase, QColor(200, 210, 220))
            p.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            p.setColor(QPalette.ColorRole.Text, QColor(200, 210, 220))
            p.setColor(QPalette.ColorRole.Button, QColor(30, 40, 55))
            p.setColor(QPalette.ColorRole.ButtonText, QColor(200, 210, 220))
            p.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            p.setColor(QPalette.ColorRole.Link, QColor(60, 150, 255))
            p.setColor(QPalette.ColorRole.Highlight, QColor(60, 150, 255))
            p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
            app.setPalette(p)
        elif theme_name == "Matrix":
            p = QPalette()
            p.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.black)
            p.setColor(QPalette.ColorRole.WindowText, QColor(0, 255, 0))
            p.setColor(QPalette.ColorRole.Base, QColor(5, 5, 5))
            p.setColor(QPalette.ColorRole.AlternateBase, Qt.GlobalColor.black)
            p.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
            p.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 255, 0))
            p.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))
            p.setColor(QPalette.ColorRole.Button, QColor(10, 20, 10))
            p.setColor(QPalette.ColorRole.ButtonText, QColor(0, 255, 0))
            p.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            p.setColor(QPalette.ColorRole.Link, QColor(0, 200, 0))
            p.setColor(QPalette.ColorRole.Highlight, QColor(0, 150, 0))
            p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            app.setPalette(p)
        else: # Terang (Default)
            app.setPalette(app.style().standardPalette())

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel(self.tr("title"))
        font = title_label.font()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        self.url_label = QLabel(self.tr("search_hint"))
        main_layout.addWidget(self.url_label)
        
        url_layout = QHBoxLayout()
        self.url_entry = QLineEdit()
        self.url_entry.returnPressed.connect(self.perform_search_or_resolve)
        self.url_entry.installEventFilter(self)
        url_layout.addWidget(self.url_entry)

        self.search_button = QPushButton(self.tr("search_btn"))
        self.search_button.clicked.connect(self.perform_search_or_resolve)
        url_layout.addWidget(self.search_button)
        main_layout.addLayout(url_layout)

        from PyQt6.QtWidgets import QAbstractItemView
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.results_list.itemActivated.connect(self.on_list_item_activated)
        self.results_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.results_list)

        self.download_button = QPushButton(self.tr("download_btn", self.current_format, self.current_quality))
        font = self.download_button.font()
        font.setPointSize(12)
        font.setBold(True)
        self.download_button.setFont(font)
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()
        self.setLayout(main_layout)

        QWidget.setTabOrder(self.url_entry, self.search_button)
        QWidget.setTabOrder(self.search_button, self.results_list)
        QWidget.setTabOrder(self.results_list, self.download_button)

    def eventFilter(self, source, event):
        # Quick jump to results list or format menu using Down arrow
        if source == self.url_entry and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                if self.results_list.count() > 0:
                    self.results_list.setFocus()
                    self.results_list.setCurrentRow(0)
                else:
                    self.url_entry.setFocus()
                return True
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
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

    def perform_search_or_resolve(self):
        query = self.url_entry.text().strip()
        if not query:
            return

        self.status_label.setText(self.tr("search_searching"))
        self.results_list.clear()
        
        threading.Thread(target=self.bg_search, args=(query,), daemon=True).start()

    def bg_search(self, query):
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
                    if query.startswith("http://") or query.startswith("https://"):
                        info = ydl.extract_info(query, download=False)
                        if 'entries' in info:
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
                        entries = info.get('entries', [])
                
            # Download thumbnails concurrently
            import urllib.request
            from concurrent.futures import ThreadPoolExecutor
            
            def fetch_thumb(item):
                if item and item.get('thumbnail'):
                    try:
                        req = urllib.request.Request(item['thumbnail'], headers={'User-Agent': 'Mozilla/5.0'})
                        resp = urllib.request.urlopen(req, timeout=3)
                        item['thumb_bytes'] = resp.read()
                    except:
                        pass
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(fetch_thumb, entries)
            
            self.signals.search_finished.emit(entries)
        except Exception as e:
            self.signals.finished.emit(f"Error: {str(e)[:50]}", False)

    def on_search_finished(self, entries):
        self.results_list.clear()
        self.last_search_entries = entries
        self.status_label.setText(self.tr("status_found", len(entries)))
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QIcon, QPixmap
        self.results_list.setIconSize(QSize(120, 90))
        
        for item in entries:
            if not item: continue
            title = item.get('title', 'Unknown Title')
            url = item.get('webpage_url') or item.get('original_url') or item.get('url', '')
            duration = item.get('duration')
            dur_str = f" ({int(duration)//60}:{int(duration)%60:02d})" if duration else ""
            
            list_item = QListWidgetItem(f"{title}{dur_str}")
            
            item_data = {
                'url': url,
                'title': title,
                'playlist_title': item.get('__playlist_title'),
                'playlist_index': item.get('__playlist_index'),
                '__is_ytmusic_album': item.get('__is_ytmusic_album'),
                'browseId': item.get('browseId'),
                'playlistId': item.get('playlistId')
            }
            list_item.setData(Qt.ItemDataRole.UserRole, item_data)
            
            thumb_bytes = item.get('thumb_bytes')
            if thumb_bytes:
                pixmap = QPixmap()
                pixmap.loadFromData(thumb_bytes)
                if not pixmap.isNull():
                    list_item.setIcon(QIcon(pixmap.scaled(120, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            
            self.results_list.addItem(list_item)
            
        if self.results_list.count() > 0:
            self.results_list.setFocus()
            self.results_list.setCurrentRow(0)

    def show_context_menu(self, position):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu = QMenu(self)
        
        # Opsi Salin Link (hanya muncul jika ada item yang dipilih)
        selected_items = self.results_list.selectedItems()
        if selected_items:
            copy_action = QAction(self.tr("menu_copy_link"), self)
            copy_action.triggered.connect(self.copy_link)
            menu.addAction(copy_action)
            menu.addSeparator()

        settings_menu = menu.addMenu(self.tr("menu_settings"))
        
        folder_action = QAction(self.tr("menu_folder"), self)
        folder_action.triggered.connect(self.browse_folder)
        settings_menu.addAction(folder_action)
        settings_menu.addSeparator()
        
        tema_menu = settings_menu.addMenu(self.tr("menu_theme"))
        for t_name in ["Terang", "Gelap", "Biru Malam", "Matrix"]:
            action = QAction(t_name, self)
            action.setCheckable(True)
            if self.current_theme == t_name:
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=t_name: self.apply_theme(name))
            tema_menu.addAction(action)
            
        lang_menu = settings_menu.addMenu(self.tr("menu_lang"))
        for l_code, l_name in [("id", "Indonesia"), ("en", "English")]:
            action = QAction(l_name, self)
            action.setCheckable(True)
            if self.current_lang == l_code:
                action.setChecked(True)
            action.triggered.connect(lambda checked, code=l_code: self.change_lang(code))
            lang_menu.addAction(action)
            
        menu.addSeparator()
        
        format_menu = menu.addMenu(self.tr("menu_format"))
        for f_name in ["Video (MP4)", "Audio (MP3)"]:
            action = QAction(f_name, self)
            action.setCheckable(True)
            if self.current_format == f_name:
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=f_name: self.change_format(name))
            format_menu.addAction(action)
            
        qualities = self.video_qualities if self.current_format == "Video (MP4)" else self.audio_qualities
        q_label = self.tr("menu_quality") if self.current_format == "Video (MP4)" else self.tr("audio_quality")
        quality_menu = menu.addMenu(q_label)
        for q_name in qualities:
            action = QAction(q_name, self)
            action.setCheckable(True)
            if self.current_quality == q_name:
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=q_name: self.change_quality(name))
            quality_menu.addAction(action)

        menu.addSeparator()
        info_menu_title = "Info & Bantuan" if self.current_lang == "id" else "Info & Help"
        info_menu = menu.addMenu(info_menu_title)

        help_text = "Bantuan & Pintasan" if self.current_lang == "id" else "Help & Shortcuts"
        help_action = QAction(help_text, self)
        help_action.triggered.connect(self.show_help_dialog)
        info_menu.addAction(help_action)
        
        about_text = "Tentang Aplikasi" if self.current_lang == "id" else "About Application"
        about_action = QAction(about_text, self)
        about_action.triggered.connect(self.show_about_dialog)
        info_menu.addAction(about_action)
        
        donate_text = "Dukung / Donasi (GoPay)" if self.current_lang == "id" else "Support / Donate (GoPay)"
        donate_action = QAction(donate_text, self)
        donate_action.triggered.connect(self.show_donate_dialog)
        info_menu.addAction(donate_action)

        menu.exec(self.results_list.mapToGlobal(position))

    def show_help_dialog(self):
        title = "Bantuan & Pintasan" if self.current_lang == "id" else "Help & Shortcuts"
        text = "FITUR UTAMA:\n- Pencarian Video: Ketik kata kunci biasa.\n- Pencarian Album: Ketik awalan 'album: ' (contoh: album: slank) untuk mengunduh 1 album utuh.\n- Tempel Link: Tempel (Paste) link YouTube, Playlist, atau TikTok untuk langsung diproses.\n- Unduh Massal: Tahan tombol Shift atau Ctrl di daftar lagu untuk memilih lebih dari satu.\n\nPINTASAN KEYBOARD (SHORTCUTS):\n- Panah Bawah (dari kotak teks): Pindah ke daftar hasil.\n- Enter (di daftar hasil): Putar lagu/video untuk percobaan.\n- Spasi: Putar/Jeda (Play/Pause) saat memutar lagu.\n- Panah Atas/Bawah (saat memutar): Naik/turunkan volume.\n- Panah Kanan/Kiri (saat memutar): Maju/mundur 5 detik.\n- Esc (di dalam album): Kembali ke daftar album sebelumnya." if self.current_lang == "id" else "MAIN FEATURES:\n- Video Search: Type normal keywords.\n- Album Search: Type 'album: ' prefix (e.g., album: slank) to download full albums.\n- Paste Link: Paste YouTube, Playlist, or TikTok links to process directly.\n- Bulk Download: Hold Shift or Ctrl in the list to select multiple items.\n\nKEYBOARD SHORTCUTS:\n- Down Arrow (from text box): Jump to results list.\n- Enter (on results list): Play media for preview.\n- Spacebar: Play/Pause during playback.\n- Up/Down Arrow (during playback): Increase/decrease volume.\n- Right/Left Arrow (during playback): Fast forward/rewind 5 seconds.\n- Esc (inside album): Go back to previous album list."
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, text)

    def show_about_dialog(self):
        title = "Tentang Aplikasi" if self.current_lang == "id" else "About Application"
        text = "Vid Downloader\n\nAplikasi super ringan dan aksesibel (ramah pembaca layar) untuk mencari, memutar, dan mengunduh video serta audio dari YouTube dan platform lainnya.\n\nPembuat: Ajang Berbagi" if self.current_lang == "id" else "Vid Downloader\n\nA super lightweight and accessible application to search, play, and download video and audio from YouTube and other platforms.\n\nCreator: Ajang Berbagi"
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, text)

    def show_donate_dialog(self):
        title = "Donasi" if self.current_lang == "id" else "Donate"
        text = "Dukung terus pengembangan aplikasi ini dengan memberikan donasi seikhlasnya.\n\nGoPay: 085883879200\nAtas nama: Mahfud PG\n\nTerima kasih banyak atas dukungan Anda!" if self.current_lang == "id" else "Support the continuous development of this application by donating.\n\nGoPay: 085883879200\nName: Mahfud PG\n\nThank you very much for your support!"
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, text)

    def change_lang(self, code):
        self.current_lang = code
        self.settings.setValue("lang", code)
        self.setWindowTitle(self.tr("title"))
        self.url_label.setText(self.tr("search_hint"))
        self.search_button.setText(self.tr("search_btn"))
        self.download_button.setText(self.tr("download_btn", self.current_format, self.current_quality))
        if self.status_label.text() == "Mencari..." or self.status_label.text() == "Searching...":
            self.status_label.setText(self.tr("search_searching"))

    def change_format(self, fmt):
        self.current_format = fmt
        self.settings.setValue("format", fmt)
        if fmt == "Video (MP4)":
            self.current_quality = "1080p"
        else:
            self.current_quality = "320kbps"
        self.settings.setValue("quality", self.current_quality)
        self.download_button.setText(self.tr("download_btn", self.current_format, self.current_quality))
        
    def change_quality(self, qlt):
        self.current_quality = qlt
        self.settings.setValue("quality", qlt)
        self.download_button.setText(self.tr("download_btn", self.current_format, self.current_quality))

    def copy_link(self):
        selected_items = self.results_list.selectedItems()
        if not selected_items: return
        urls = []
        for item in selected_items:
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict):
                urls.append(data.get('url', ''))
            else:
                urls.append(data)
        
        urls = [u for u in urls if u]
        if urls:
            QApplication.clipboard().setText("\n".join(urls))
            self.status_label.setText("Tersalin!" if self.current_lang == "id" else "Copied!")


    def bg_fetch_album_tracks(self, browse_id, album_title):
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
        import threading
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict) and data.get('__is_ytmusic_album'):
            browse_id = data.get('browseId')
            album_title = data.get('title') or item.text()
            if browse_id:
                self.saved_album_entries = self.last_search_entries
                self.status_label.setText(self.tr("search_searching") if self.current_lang == "id" else "Fetching album tracks...")
                threading.Thread(target=self.bg_fetch_album_tracks, args=(browse_id, album_title), daemon=True).start()
            return
            
        selected_items = self.results_list.selectedItems()
        urls_to_play = []
        if len(selected_items) > 1 and item in selected_items:
            for s_item in selected_items:
                s_data = s_item.data(Qt.ItemDataRole.UserRole)
                url = s_data['url'] if isinstance(s_data, dict) else s_data
                if url: urls_to_play.append(url)
        else:
            url = data['url'] if isinstance(data, dict) else data
            if url: urls_to_play.append(url)
            
        if not urls_to_play: return
        
        self.player_dialog = CustomPlayerDialog(urls_to_play, self)
        self.player_dialog.exec()

    def update_progress(self, percentage, message):
        if self.progress_bar.isHidden():
            self.progress_bar.show()
        self.progress_bar.setValue(int(percentage))
        self.status_label.setText(message)

    def download_finished(self, message, success):
        self.progress_bar.hide()
        self.status_label.setText(self.tr("status_ready"))
        self.download_button.setEnabled(True)
        title = self.tr("success") if success else self.tr("error")
        if success and "Sukses" in message:
            message = self.tr("success_msg")
            QMessageBox.information(self, title, message)
            # Fokus kembali ke input setelah sukses, siap untuk pencarian berikutnya
            self.url_entry.setFocus()
            self.url_entry.selectAll()
        else:
            QMessageBox.warning(self, title, message)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Menghindari error pembagian dengan 0 atau tipe data
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                
                if total > 0:
                    percentage = (downloaded / total) * 100
                    speed_mbps = speed / 1024 / 1024 if speed else 0
                    msg = self.tr("downloading", percentage, speed_mbps)
                    self.signals.progress.emit(percentage, msg)
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.signals.progress.emit(100.0, self.tr("download_done"))

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Folder", self.download_path)
        if folder:
            self.download_path = folder
            self.settings.setValue("download_path", self.download_path)

    def start_download(self):
        selected_items = self.results_list.selectedItems()
        items_data = []
        if not selected_items:
            # Fallback to text box if nothing is selected in list
            url = self.url_entry.text().strip()
            if not url:
                self.url_entry.setFocus()
                return
            items_data.append({'url': url, 'playlist_title': None, 'playlist_index': None})
        else:
            for item in selected_items:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, dict):
                    items_data.append(data)
                else:
                    items_data.append({'url': data, 'playlist_title': None, 'playlist_index': None})

        self.status_label.setText("...")
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        format_choice = self.current_format

        threading.Thread(target=self.download_process, args=(items_data, format_choice, self.current_quality), daemon=True).start()

    def download_process(self, items_data, format_choice, quality_choice):
        ffmpeg_loc = get_ffmpeg_path()
        base_ydl_opts = {
            'progress_hooks': [self.progress_hook],
            'ffmpeg_location': ffmpeg_loc,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': ['player_client=android,web']},
        }

        if format_choice == "Audio (MP3)":
            bitrate = "320" if "320" in quality_choice else "128"
            base_ydl_opts.update({
                'format': 'bestaudio/best',
                'writethumbnail': True,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': bitrate,
                    },
                    {
                        'key': 'EmbedThumbnail',
                        'already_have_thumbnail': False
                    }
                ],
            })
        else: # Video (MP4)
            if "1080p" in quality_choice:
                base_ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
            elif "720p" in quality_choice:
                base_ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
            elif "480p" in quality_choice:
                base_ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
            else:
                base_ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            base_ydl_opts['merge_output_format'] = 'mp4'

        try:
            for idx, data in enumerate(items_data):
                url = data['url']
                pl_title = data.get('playlist_title')
                pl_idx = data.get('playlist_index')
                is_album = data.get('__is_ytmusic_album')
                
                is_multi = len(items_data) > 1
                
                if is_album:
                    # Jika download langsung album utuh, biarkan yt-dlp yang atur folder & nomor
                    current_dl_path = self.download_path
                    album_folder_name = data.get('title')
                    if album_folder_name:
                        import re
                        clean_pl_title = re.sub(r'[\\/*?:"<>|]', "", album_folder_name).strip()
                        filename_tmpl = f"{clean_pl_title}/%(playlist_index)02d. %(title)s.%(ext)s"
                    else:
                        filename_tmpl = "%(playlist_title)s/%(playlist_index)02d. %(title)s.%(ext)s"
                else:
                    if pl_title:
                        import re
                        clean_pl_title = re.sub(r'[\\/*?:"<>|]', "", pl_title).strip()
                        current_dl_path = os.path.join(self.download_path, clean_pl_title)
                    else:
                        current_dl_path = self.download_path
                        
                    if pl_idx is not None:
                        filename_tmpl = f"{pl_idx:02d} - %(title)s.%(ext)s"
                    elif is_multi:
                        filename_tmpl = f"{(idx+1):02d} - %(title)s.%(ext)s"
                    else:
                        filename_tmpl = "%(title)s.%(ext)s"
                    
                os.makedirs(current_dl_path, exist_ok=True)
                
                ydl_opts = base_ydl_opts.copy()
                ydl_opts['outtmpl'] = os.path.join(current_dl_path, filename_tmpl)
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    
            self.signals.finished.emit("Sukses", True)
        except Exception as e:
            self.signals.finished.emit(f"Error: {str(e)[:100]}", False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
    window = VidDownloaderApp()
    window.show()
    sys.exit(app.exec())
