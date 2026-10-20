with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target_menu = '''        # Action Pilih Folder
        folder_text = "Pilih Folder Unduhan..." if self.current_lang == "id" else "Select Download Folder..."
        folder_action = QAction(folder_text, self)
        folder_action.triggered.connect(self.browse_folder)
        menu.addAction(folder_action)
        
        menu.exec(self.mapToGlobal(position))'''

replacement_menu = '''        # Action Pilih Folder
        folder_text = "Pilih Folder Unduhan..." if self.current_lang == "id" else "Select Download Folder..."
        folder_action = QAction(folder_text, self)
        folder_action.triggered.connect(self.browse_folder)
        menu.addAction(folder_action)
        
        menu.addSeparator()
        
        help_text = "Bantuan & Pintasan" if self.current_lang == "id" else "Help & Shortcuts"
        help_action = QAction(help_text, self)
        help_action.triggered.connect(self.show_help_dialog)
        menu.addAction(help_action)
        
        about_text = "Tentang Aplikasi" if self.current_lang == "id" else "About Application"
        about_action = QAction(about_text, self)
        about_action.triggered.connect(self.show_about_dialog)
        menu.addAction(about_action)
        
        donate_text = "Dukung / Donasi (GoPay)" if self.current_lang == "id" else "Support / Donate (GoPay)"
        donate_action = QAction(donate_text, self)
        donate_action.triggered.connect(self.show_donate_dialog)
        menu.addAction(donate_action)
        
        menu.exec(self.mapToGlobal(position))

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
        text = "Dukung terus pengembangan aplikasi ini dengan memberikan donasi seikhlasnya.\n\nGoPay: 085883879200\nAtas nama: Ajang Berbagi\n\nTerima kasih banyak atas dukungan Anda!" if self.current_lang == "id" else "Support the continuous development of this application by donating.\n\nGoPay: 085883879200\nName: Ajang Berbagi\n\nThank you very much for your support!"
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, text)'''

c = c.replace(target_menu, replacement_menu)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
