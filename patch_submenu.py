with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''        menu.addSeparator()
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
        menu.addAction(donate_action)'''

replacement = '''        menu.addSeparator()
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
        info_menu.addAction(donate_action)'''

c = c.replace(target, replacement)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)
