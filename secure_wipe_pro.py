# #!/usr/bin/env python3
# """
# Режими роботи:
# - РЕЖИМ 1: Файл (знищити один файл)
# - РЕЖИМ 2: Папка (рекурсивно знищити всі файли в папці)
# - РЕЖИМ 3: Диск (заповнити вільний простір)
# """

# import os
# import sys
# import time
# import threading
# import tkinter as tk
# from tkinter import filedialog, messagebox, simpledialog
# from datetime import datetime
# from pathlib import Path
# from typing import Optional, Callable

# # Try to import CustomTkinter
# try:
#     import customtkinter as ctk
#     from customtkinter import (
#         CTk, CTkFrame, CTkLabel, CTkButton, CTkRadioButton, CTkSegmentedButton,
#         CTkComboBox, CTkScrollableFrame
#     )
#     CTK_AVAILABLE = True
# except ImportError:
#     print("ПОМИЛКА: CustomTkinter не встановлено!")
#     print("Встановіть: pip install customtkinter")
#     sys.exit(1)

# # Імпортуємо wipe engine
# try:
#     from wipe_engine import WipeEngine, RiskLevel
# except ImportError:
#     print("ПОМИЛКА: Не знайдено wipe_engine.py!")
#     sys.exit(1)

# # Кольорова схема (Dark theme)
# COLORS = {
#     'bg_main': '#1C1C1E',
#     'bg_card': '#2C2C2E',
#     'bg_terminal': '#0D0D0D',
#     'accent_red': '#FF3B30',
#     'accent_red_hover': '#FF6961',
#     'accent_blue': '#0A84FF',
#     'accent_blue_hover': '#3A9EFF',
#     'accent_green': '#30D158',
#     'accent_green_hover': '#52DE7A',
#     'accent_orange': '#FF9F0A',
#     'accent_purple': '#BF5AF2',
#     'text_main': '#FFFFFF',
#     'text_sub': '#8E8E93',
#     'text_warning': '#FFD60A',
#     'border_color': '#3A3A3C'
# }

# # Налаштування CustomTkinter
# ctk.set_appearance_mode("dark")
# ctk.set_default_color_theme("blue")


# class SplashScreen(ctk.CTkToplevel):
#     """Splash screen при запуску програми"""

#     def __init__(self, parent):
#         super().__init__(parent)

#         self.title("")
#         self.geometry("500x350")
#         self.resizable(False, False)
#         self.configure(fg_color=COLORS['bg_main'])

#         self.overrideredirect(True)

#         self.update_idletasks()
#         x = (self.winfo_screenwidth() // 2) - (500 // 2)
#         y = (self.winfo_screenheight() // 2) - (350 // 2)
#         self.geometry(f"500x350+{x}+{y}")

#         self.grid_columnconfigure(0, weight=1)
#         self.grid_rowconfigure(0, weight=1)

#         main_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_main'], corner_radius=16)
#         main_frame.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
#         main_frame.grid_columnconfigure(0, weight=1)

#         logo_label = ctk.CTkLabel(main_frame, text="🛡️", font=ctk.CTkFont(size=72))
#         logo_label.grid(row=0, column=0, pady=(40, 10))

#         title_label = ctk.CTkLabel(
#             main_frame, text="SecureWipe Pro",
#             font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
#             text_color=COLORS['text_main']
#         )
#         title_label.grid(row=1, column=0, pady=(0, 5))

#         version_label = ctk.CTkLabel(
#             main_frame, text="v2.0 — NIST 800–88 r2 / IEEE 2883-2022",
#             font=ctk.CTkFont(family="Segoe UI", size=13),
#             text_color=COLORS['accent_blue']
#         )
#         version_label.grid(row=2, column=0, pady=(0, 5))

#         desc_label = ctk.CTkLabel(
#             main_frame,
#             text="Сучасне знищення даних\nвідповідньо до міжнародних стандартів",
#             font=ctk.CTkFont(family="Segoe UI", size=12),
#             text_color=COLORS['text_sub']
#         )
#         desc_label.grid(row=3, column=0, pady=(10, 20))

#         self.progress = ctk.CTkProgressBar(
#             main_frame, mode="indeterminate",
#             progress_color=COLORS['accent_blue']
#         )
#         self.progress.grid(row=4, column=0, padx=40, sticky="ew")
#         self.progress.start()

#         self.status_label = ctk.CTkLabel(
#             main_frame, text="Ініціалізація...",
#             font=ctk.CTkFont(family="Segoe UI", size=12),
#             text_color=COLORS['text_sub']
#         )
#         self.status_label.grid(row=5, column=0, pady=(10, 30))

#     def update_status(self, text: str):
#         self.status_label.configure(text=text)
#         self.update_idletasks()

#     def close(self):
#         self.progress.stop()
#         self.destroy()


# class TerminalWidget(ctk.CTkTextbox):
#     """Термінальний віджет для виводу логів"""

#     def __init__(self, master, **kwargs):
#         super().__init__(
#             master, fg_color=COLORS['bg_terminal'],
#             text_color="#00FF00",
#             font=ctk.CTkFont(family="Consolas", size=12), **kwargs
#         )
#         self.configure(wrap="word")

#     def write(self, text: str):
#         self.insert("end", text)
#         self.see("end")
#         self.update_idletasks()

#     def flush(self):
#         pass


# class MethodCard(ctk.CTkFrame):
#     """Картка методу знищення"""

#     def __init__(self, master, method_id: str, title: str, description: str,
#                  details: str, color: str, **kwargs):
#         super().__init__(master, fg_color=COLORS['bg_card'], corner_radius=10, **kwargs)

#         self.method_id = method_id
#         self.color = color

#         title_label = ctk.CTkLabel(
#             self, text=title,
#             font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
#             text_color=COLORS['text_main']
#         )
#         title_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

#         desc_label = ctk.CTkLabel(
#             self, text=description,
#             font=ctk.CTkFont(family="Segoe UI", size=12),
#             text_color=COLORS['text_sub'], wraplength=350
#         )
#         desc_label.grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")

#         details_label = ctk.CTkLabel(
#             self, text=details,
#             font=ctk.CTkFont(family="Consolas", size=10),
#             text_color=color
#         )
#         details_label.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="w")


# class SecureWipePro(ctk.CTk):
#     """Головне вікно SecureWipe Pro v2.0"""

#     def __init__(self):
#         super().__init__()

#         self.title("🔒 SecureWipe Pro")
#         self.geometry("1280x850")
#         self.minsize(1200, 800)
#         self.configure(fg_color=COLORS['bg_main'])

#         self.selected_method = tk.StringVar(value="nist_clear")
#         self.operation_mode = tk.StringVar(value="file")
#         self.target_path = tk.StringVar()
#         self.selected_drive = tk.StringVar()
#         self.engine = None
#         self.operation_thread = None
#         self.current_operation = None
#         self._last_progress_time = 0

#         # Рівень ризику для ризик-орієнтованого вибору методу
#         self.risk_level = tk.StringVar(value="medium")

#         self.grid_columnconfigure(0, weight=1)
#         self.grid_rowconfigure(0, weight=1)

#         self._create_widgets()
#         self._setup_drag_drop()

#         self.withdraw()
#         self.splash = SplashScreen(self)
#         self.after(2500, self._close_splash)

#     def _close_splash(self):
#         self.splash.close()
#         self.deiconify()
#         self.lift()
#         self.focus_force()

#     def _create_widgets(self):
#         # Головний контейнер з прокруткою
#         self.main_scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS['bg_main'])
#         self.main_scroll.grid(row=0, column=0, sticky="nsew")
#         self.main_scroll.grid_columnconfigure(0, weight=1)
#         self.grid_rowconfigure(0, weight=1)
#         self.grid_columnconfigure(0, weight=1)

#         main_container = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
#         main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
#         main_container.grid_columnconfigure(0, weight=1)
#         main_container.grid_columnconfigure(1, weight=1)

#         header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
#         header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
#         header_frame.grid_columnconfigure(0, weight=1)

#         title_label = ctk.CTkLabel(
#             header_frame, text="🔒 SecureWipe Pro",
#             font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
#             text_color=COLORS['text_main']
#         )
#         title_label.grid(row=0, column=0, sticky="w")

#         std_label = ctk.CTkLabel(
#             header_frame, text="NIST 800–88 r2 / IEEE 2883-2022",
#             font=ctk.CTkFont(family="Segoe UI", size=11),
#             text_color=COLORS['accent_blue']
#         )
#         std_label.grid(row=1, column=0, sticky="w", pady=(3, 0))

#         theme_btn = ctk.CTkButton(
#             header_frame, text="☀️", width=40, height=40,
#             corner_radius=20, fg_color=COLORS['bg_card'],
#             hover_color=COLORS['accent_blue']
#         )
#         theme_btn.grid(row=0, column=1, sticky="e")

#         # ── Ліва панель ──
#         left_panel = ctk.CTkScrollableFrame(
#             main_container, fg_color=COLORS['bg_card'], corner_radius=12,
#             label_text="  МЕТОДИ ЗНИЩЕННЯ  ",
#             label_font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
#             label_fg_color=COLORS['bg_card'],
#             label_text_color=COLORS['text_sub']
#         )
#         left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
#         left_panel.grid_columnconfigure(0, weight=1)

#         self._create_method_cards(left_panel)

#         # ── Права панель ──
#         right_panel = ctk.CTkScrollableFrame(
#             main_container, fg_color=COLORS['bg_card'], corner_radius=12,
#             label_text="  НАЛАШТУВАННЯ  ",
#             label_font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
#             label_fg_color=COLORS['bg_card'],
#             label_text_color=COLORS['text_sub']
#         )
#         right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
#         right_panel.grid_columnconfigure(0, weight=1)

#         self._create_status_panel(right_panel)

#         # ── Нижня панель ──
#         bottom_panel = ctk.CTkFrame(main_container, fg_color="transparent")
#         bottom_panel.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
#         bottom_panel.grid_columnconfigure(0, weight=1)
#         bottom_panel.grid_columnconfigure(1, weight=1)
#         bottom_panel.grid_columnconfigure(2, weight=1)

#         self._create_action_buttons(bottom_panel)

#         # ── Термінал ──
#         terminal_frame = ctk.CTkFrame(main_container, fg_color="transparent")
#         terminal_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 0))
#         terminal_frame.grid_columnconfigure(0, weight=1)

#         terminal_label = ctk.CTkLabel(
#             terminal_frame, text="📋 ЛОГ ОПЕРАЦІЙ",
#             font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
#             text_color=COLORS['text_sub']
#         )
#         terminal_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

#         self.terminal = TerminalWidget(terminal_frame, height=140)
#         self.terminal.grid(row=1, column=0, sticky="ew")

#         sys.stdout = self.terminal

#         print("╔══════════════════════════════════════════════╗")
#         print("║       SecureWipe Pro                     ║")
#         print("║       NIST 800–88 r2 / IEEE 2883-2022       ║")
#         print("╚══════════════════════════════════════════════╝")
#         print("Готовий до роботи.\n")

#     def _create_method_cards(self, parent):
#         methods = [
#             {
#                 'id': 'nist_clear',
#                 'title': 'NIST Clear',
#                 'desc': 'Захист від програмного відновлення',
#                 'details': '1 прохід · псевдовипадкові дані · HDD / USB',
#                 'color': COLORS['accent_blue']
#             },
#             {
#                 'id': 'nist_purge',
#                 'title': 'NIST Purge (апаратне стирання)',
#                 'desc': 'Знищення включно з резервним простором контролера',
#                 'details': 'diskpart clean all · ATA SE · NVMe Sanitize · ⚠️ Потребує права адміна',
#                 'color': COLORS['accent_red']
#             },
#             {
#                 'id': 'crypto_erase',
#                 'title': 'Crypto Erase',
#                 'desc': 'Миттєве криптографічне знищення через BitLocker',
#                 'details': 'Знищення ключа · без перезапису · ⚠️ Лише зашифровані диски',
#                 'color': COLORS['accent_purple']
#             },
#             {
#                 'id': 'verify',
#                 'title': 'Verify Only',
#                 'desc': 'Перевірка чистоти носія без знищення',
#                 'details': 'Зчитування та аналіз секторів · без змін',
#                 'color': COLORS['accent_green']
#             }
#         ]

#         for i, m in enumerate(methods):
#             # Контейнер для картки з радіо-кнопкою
#             container = ctk.CTkFrame(parent, fg_color="transparent")
#             container.grid(row=i, column=0, padx=10, pady=(0, 8), sticky="ew")
#             container.grid_columnconfigure(1, weight=1)

#             # Радіо-кнопка зліва
#             rb = ctk.CTkRadioButton(
#                 container, text="", variable=self.selected_method,
#                 value=m['id'], width=20, height=20
#             )
#             rb.grid(row=0, column=0, padx=(5, 10), pady=15, sticky="w")

#             # Картка методу
#             card = MethodCard(
#                 container, method_id=m['id'], title=m['title'],
#                 description=m['desc'], details=m['details'], color=m['color']
#             )
#             card.grid(row=0, column=1, sticky="ew")

#             def make_card_clickable(card_widget, method_val):
#                 def on_click(event=None):
#                     self.selected_method.set(method_val)
#                     self._on_method_change(method_val)
#                 card_widget.bind("<Button-1>", on_click)
#                 for child in card_widget.winfo_children():
#                     child.bind("<Button-1>", on_click)

#             make_card_clickable(card, m['id'])

#     def _create_status_panel(self, parent):
#         parent.grid_columnconfigure(0, weight=1)

#         self.mode_segmented = ctk.CTkSegmentedButton(
#             parent, values=["Файл", "Папка", "Диск"],
#             font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
#             height=40, corner_radius=8,
#             fg_color=COLORS['bg_main'],
#             selected_color=COLORS['accent_blue'],
#             unselected_color=COLORS['bg_card'],
#             text_color=COLORS['text_main'],
#             unselected_hover_color=COLORS['accent_blue_hover'],
#             command=self._on_segmented_mode_change
#         )
#         self.mode_segmented.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
#         self.mode_segmented.set("Файл")

#         self.mode_desc_label = ctk.CTkLabel(
#             parent, text="Знищити один файл обраним методом",
#             font=ctk.CTkFont(family="Segoe UI", size=11),
#             text_color=COLORS['text_sub']
#         )
#         self.mode_desc_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

#         separator = ctk.CTkFrame(parent, height=2, fg_color=COLORS['border_color'])
#         separator.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")

#         # ── Секція оцінки ризику ──
#         risk_label = ctk.CTkLabel(
#             parent, text="ОЦІНКА РИЗИКУ АКТИВУ",
#             font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
#             text_color=COLORS['text_sub']
#         )
#         risk_label.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="w")

#         risk_frame = ctk.CTkFrame(parent, fg_color="transparent")
#         risk_frame.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
#         risk_frame.grid_columnconfigure((0, 1, 2), weight=1)

#         # Кнопки вибору рівня ризику
#         self.risk_low_btn = ctk.CTkButton(
#             risk_frame, text="🟢 Низький",
#             font=ctk.CTkFont(family="Segoe UI", size=11),
#             height=32, corner_radius=8,
#             fg_color=COLORS['bg_main'],
#             hover_color=COLORS['accent_green'],
#             command=lambda: self._set_risk_level("low")
#         )
#         self.risk_low_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

#         self.risk_medium_btn = ctk.CTkButton(
#             risk_frame, text="🟡 Середній",
#             font=ctk.CTkFont(family="Segoe UI", size=11),
#             height=32, corner_radius=8,
#             fg_color=COLORS['accent_orange'],
#             hover_color=COLORS['accent_orange'],
#             command=lambda: self._set_risk_level("medium")
#         )
#         self.risk_medium_btn.grid(row=0, column=1, padx=5, sticky="ew")

#         self.risk_high_btn = ctk.CTkButton(
#             risk_frame, text="🔴 Високий",
#             font=ctk.CTkFont(family="Segoe UI", size=11),
#             height=32, corner_radius=8,
#             fg_color=COLORS['bg_main'],
#             hover_color=COLORS['accent_red'],
#             command=lambda: self._set_risk_level("high")
#         )
#         self.risk_high_btn.grid(row=0, column=2, padx=(5, 0), sticky="ew")

#         # Інформація про рекомендований метод
#         self.risk_info_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_main'], corner_radius=8)
#         self.risk_info_frame.grid(row=5, column=0, padx=20, pady=(0, 15), sticky="ew")
#         self.risk_info_frame.grid_columnconfigure(0, weight=1)

#         self.risk_info_label = ctk.CTkLabel(
#             self.risk_info_frame,
#             text="Рекомендований метод: NIST Purge",
#             font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
#             text_color=COLORS['accent_orange']
#         )
#         self.risk_info_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

#         self.risk_desc_label = ctk.CTkLabel(
#             self.risk_info_frame,
#             text="Апаратне стирання для персональних даних",
#             font=ctk.CTkFont(family="Segoe UI", size=10),
#             text_color=COLORS['text_sub']
#         )
#         self.risk_desc_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

#         separator2 = ctk.CTkFrame(parent, height=2, fg_color=COLORS['border_color'])
#         separator2.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")

#         label = ctk.CTkLabel(
#             parent, text="ПАНЕЛЬ СТАТУСУ",
#             font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
#             text_color=COLORS['text_sub']
#         )
#         label.grid(row=7, column=0, padx=20, pady=(0, 15), sticky="w")

#         target_frame = ctk.CTkFrame(parent, fg_color="transparent")
#         target_frame.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")
#         target_frame.grid_columnconfigure(0, weight=1)

#         self.target_label = ctk.CTkLabel(
#             target_frame, text="Ціль:",
#             font=ctk.CTkFont(family="Segoe UI", size=12),
#             text_color=COLORS['text_sub']
#         )
#         self.target_label.grid(row=0, column=0, sticky="w")

#         input_frame = ctk.CTkFrame(target_frame, fg_color="transparent")
#         input_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
#         input_frame.grid_columnconfigure(0, weight=1)

#         self.target_entry = ctk.CTkEntry(
#             input_frame, textvariable=self.target_path,
#             placeholder_text="Перетягніть файл або натисніть 📁",
#             font=ctk.CTkFont(family="Segoe UI", size=12), height=35
#         )
#         self.target_entry.grid(row=0, column=0, sticky="ew")

#         self.browse_btn = ctk.CTkButton(
#             input_frame, text="📁", width=40, height=35,
#             corner_radius=8, fg_color=COLORS['bg_card'],
#             hover_color=COLORS['accent_blue'], command=self._browse_file
#         )
#         self.browse_btn.grid(row=0, column=1, padx=(8, 0))

#         self.disk_frame = ctk.CTkFrame(parent, fg_color="transparent")
#         self.disk_frame.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")
#         self.disk_frame.grid_columnconfigure(0, weight=1)

#         disk_label = ctk.CTkLabel(
#             self.disk_frame, text="Виберіть диск для очищення:",
#             font=ctk.CTkFont(family="Segoe UI", size=12),
#             text_color=COLORS['text_sub']
#         )
#         disk_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

#         drives = WipeEngine.get_available_drives()
#         if not drives:
#             drives = ["C:\\", "D:\\", "E:\\"]

#         drives_with_custom = drives + ["Інший диск..."]

#         self.disk_combo = ctk.CTkComboBox(
#             self.disk_frame, values=drives_with_custom,
#             variable=self.selected_drive,
#             font=ctk.CTkFont(family="Segoe UI", size=12), height=40,
#             command=self._on_disk_selected
#         )
#         self.disk_combo.grid(row=1, column=0, sticky="ew")

#         if drives:
#             self.disk_combo.set(drives[0])
#             self.selected_drive.set(drives[0])

#         self.disk_frame.grid_remove()

#         self.info_frame = ctk.CTkFrame(parent, fg_color="transparent")
#         self.info_frame.grid(row=10, column=0, padx=20, pady=(10, 5), sticky="ew")
#         self.info_frame.grid_columnconfigure(0, weight=1)

#         self.size_label = ctk.CTkLabel(
#             self.info_frame, text="Розмір: --",
#             font=ctk.CTkFont(family="Segoe UI", size=12),
#             text_color=COLORS['text_main']
#         )
#         self.size_label.grid(row=0, column=0, sticky="w")

#         self.method_label = ctk.CTkLabel(
#             self.info_frame, text="Метод: NIST Clear",
#             font=ctk.CTkFont(family="Segoe UI", size=11),
#             text_color=COLORS['accent_blue']
#         )
#         self.method_label.grid(row=1, column=0, sticky="w", pady=(3, 0))

#         self.status_label = ctk.CTkLabel(
#             self.info_frame, text="Статус: Готовий",
#             font=ctk.CTkFont(family="Segoe UI", size=12),
#             text_color=COLORS['accent_green']
#         )
#         self.status_label.grid(row=2, column=0, sticky="w", pady=(5, 0))

#         progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
#         progress_frame.grid(row=11, column=0, padx=20, pady=(10, 20), sticky="ew")
#         progress_frame.grid_columnconfigure(0, weight=1)

#         self.progress_bar = ctk.CTkProgressBar(
#             progress_frame, mode="determinate",
#             progress_color=COLORS['accent_blue'],
#             height=20, corner_radius=10
#         )
#         self.progress_bar.grid(row=0, column=0, sticky="ew")
#         self.progress_bar.set(0)

#         self.progress_label = ctk.CTkLabel(
#             progress_frame, text="0%",
#             font=ctk.CTkFont(family="Segoe UI", size=11),
#             text_color=COLORS['text_sub']
#         )
#         self.progress_label.grid(row=1, column=0, pady=(5, 0))

#         self.details_label = ctk.CTkLabel(
#             parent, text="",
#             font=ctk.CTkFont(family="Segoe UI", size=11),
#             text_color=COLORS['text_sub'], wraplength=400
#         )
#         self.details_label.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="w")

#     def _set_risk_level(self, level: str):
#         """Встановити рівень ризику та оновити рекомендації"""
#         self.risk_level.set(level)

#         # Оновити вигляд кнопок
#         self.risk_low_btn.configure(
#             fg_color=COLORS['accent_green'] if level == "low" else COLORS['bg_main']
#         )
#         self.risk_medium_btn.configure(
#             fg_color=COLORS['accent_orange'] if level == "medium" else COLORS['bg_main']
#         )
#         self.risk_high_btn.configure(
#             fg_color=COLORS['accent_red'] if level == "high" else COLORS['bg_main']
#         )

#         # Отримати рекомендований метод
#         risk_enum = RiskLevel(level)
#         is_encrypted = False
#         if self.operation_mode.get() == "disk":
#             drive = self.selected_drive.get()
#             if drive:
#                 is_encrypted, _ = WipeEngine().check_bitlocker_status(drive.rstrip('\\'))

#         recommendation = WipeEngine.get_recommended_method(risk_enum, is_encrypted)

#         # Оновити відображення рекомендації
#         risk_display = WipeEngine.get_risk_level_display(risk_enum)
#         self.risk_info_label.configure(
#             text=f"Рекомендований метод: {recommendation['method_name']}",
#             text_color=risk_display['color']
#         )
#         self.risk_desc_label.configure(text=recommendation['description'])

#         # Автоматично вибрати рекомендований метод
#         self.selected_method.set(recommendation['method_id'])
#         self._on_method_change(recommendation['method_id'])

#     def _create_action_buttons(self, parent):
#         parent.grid_columnconfigure(0, weight=1)
#         parent.grid_columnconfigure(1, weight=1)
#         parent.grid_columnconfigure(2, weight=1)

#         test_btn = ctk.CTkButton(
#             parent, text="🧪 TEST MODE",
#             font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
#             height=50, corner_radius=12,
#             fg_color=COLORS['accent_blue'],
#             hover_color=COLORS['accent_blue_hover'],
#             command=self._test_mode
#         )
#         test_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

#         self.wipe_btn = ctk.CTkButton(
#             parent, text="🗑️ START WIPE",
#             font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
#             height=50, corner_radius=12,
#             fg_color=COLORS['accent_red'],
#             hover_color=COLORS['accent_red_hover'],
#             command=self._start_wipe
#         )
#         self.wipe_btn.grid(row=0, column=1, padx=(10, 10), sticky="ew")

#         if os.name == 'nt':
#             clean_btn = ctk.CTkButton(
#                 parent, text="🧹 Очистити сліди",
#                 font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
#                 height=50, corner_radius=12,
#                 fg_color=COLORS['bg_card'],
#                 hover_color=COLORS['accent_blue_hover'],
#                 command=self._clean_artifacts
#             )
#             clean_btn.grid(row=0, column=2, padx=(10, 0), sticky="ew")

#     def _on_method_change(self, method_id: str):
#         names = {
#             'nist_clear': 'NIST Clear',
#             'nist_purge': 'NIST Purge',
#             'crypto_erase': 'Crypto Erase',
#             'verify': 'Verify Only'
#         }
#         self.method_label.configure(text=f"Метод: {names.get(method_id, method_id)}")

#         if method_id == 'crypto_erase':
#             mode = self.operation_mode.get()
#             if mode == 'disk':
#                 drive = self.selected_drive.get()
#                 if drive:
#                     is_enc, status = WipeEngine().check_bitlocker_status(drive.rstrip('\\'))
#                     if not is_enc:
#                         self.status_label.configure(
#                             text="⚠️ Диск не зашифрований! Crypto Erase недоступний.",
#                             text_color=COLORS['text_warning']
#                         )
#                     else:
#                         self.status_label.configure(
#                             text=f"✓ Диск зашифровано ({status}). Crypto Erase готовий.",
#                             text_color=COLORS['accent_green']
#                         )

#         if method_id == 'nist_purge':
#             if not WipeEngine().is_admin():
#                 self.status_label.configure(
#                     text="⚠️ Потрібні права адміністратора для NIST Purge!",
#                     text_color=COLORS['text_warning']
#                 )

#     def _on_segmented_mode_change(self, mode_text):
#         mode_map = {"Файл": "file", "Папка": "folder", "Диск": "disk"}
#         mode = mode_map.get(mode_text, "file")
#         self.operation_mode.set(mode)

#         desc_map = {
#             "file": "Знищити один файл обраним методом",
#             "folder": "Рекурсивно знищити всі файли в папці",
#             "disk": "ПОВНЕ ЗНИЩЕННЯ ВСЬОГО ДИСКА (файли + папки + вільний простір)"
#         }
#         self.mode_desc_label.configure(text=desc_map.get(mode, ""))

#         if mode == "file":
#             self.target_label.configure(text="Ціль:")
#             self.target_entry.configure(placeholder_text="Перетягніть файл або натисніть 📁")
#             self.browse_btn.configure(command=self._browse_file)
#             self.disk_frame.grid_remove()
#             target_frame = self.target_entry.master
#             target_frame.grid()
#         elif mode == "folder":
#             self.target_label.configure(text="Папка:")
#             self.target_entry.configure(placeholder_text="Виберіть папку або натисніть 📁")
#             self.browse_btn.configure(command=self._browse_folder)
#             self.disk_frame.grid_remove()
#             target_frame = self.target_entry.master
#             target_frame.grid()
#         elif mode == "disk":
#             self.target_label.configure(text="Диск:")
#             target_frame = self.target_entry.master
#             target_frame.grid_remove()
#             self.disk_frame.grid()
#             self._update_disk_info()

#         self.target_path.set("")
#         self._update_file_info()

#     def _on_disk_selected(self, choice):
#         if choice == "Інший диск...":
#             custom_path = simpledialog.askstring(
#                 "Вибір диска", "Введіть шлях до диска (наприклад, E:\\):", parent=self
#             )
#             if custom_path:
#                 if not custom_path.endswith('\\'):
#                     custom_path = custom_path.rstrip('\\') + '\\'
#                 current_values = list(self.disk_combo.cget("values"))
#                 if custom_path not in current_values:
#                     current_values.insert(-1, custom_path)
#                     self.disk_combo.configure(values=current_values)
#                 self.disk_combo.set(custom_path)
#                 self.selected_drive.set(custom_path)
#                 self._update_disk_info(custom_path)
#             else:
#                 drives = WipeEngine.get_available_drives()
#                 if drives:
#                     self.disk_combo.set(drives[0])
#                     self.selected_drive.set(drives[0])
#         else:
#             self.selected_drive.set(choice)
#             self._update_disk_info(choice)

#         current_method = self.selected_method.get()
#         if current_method == 'crypto_erase':
#             self._on_method_change(current_method)

#         # Оновити рекомендацію при зміні диска
#         self._set_risk_level(self.risk_level.get())

#     def _update_disk_info(self, drive_path=None):
#         if drive_path is None:
#             drive_path = self.selected_drive.get()

#         if drive_path and os.path.exists(drive_path):
#             try:
#                 import shutil
#                 total, used, free = shutil.disk_usage(drive_path)
#                 free_gb = free / (1024 ** 3)
#                 total_gb = total / (1024 ** 3)
#                 used_gb = used / (1024 ** 3)
#                 pct = (used / total * 100) if total > 0 else 0
#                 self.size_label.configure(
#                     text=f"📊 {used_gb:.1f}/{total_gb:.1f} GB використано ({pct:.0f}%)\n"
#                          f"   Вільно: {free_gb:.2f} GB"
#                 )
#                 self.status_label.configure(
#                     text=f"Диск {drive_path} готовий до очищення",
#                     text_color=COLORS['accent_green']
#                 )
#             except Exception:
#                 self.size_label.configure(text="Помилка читання диска")
#                 self.status_label.configure(text="Помилка", text_color=COLORS['accent_red'])
#         else:
#             self.size_label.configure(text="Диск не знайдено")
#             self.status_label.configure(text="Помилка", text_color=COLORS['accent_red'])

#     def _setup_drag_drop(self):
#         self.target_entry.bind("<ButtonRelease-1>", lambda e: self._browse_target())
#         self.target_entry.bind("<Button-3>", self._paste_from_clipboard)

#     def _paste_from_clipboard(self, event):
#         try:
#             clipboard = self.clipboard_get()
#             if os.path.exists(clipboard):
#                 self.target_path.set(clipboard)
#                 self._update_file_info()
#         except Exception:
#             pass

#     def _browse_target(self):
#         mode = self.operation_mode.get()
#         if mode == "file":
#             self._browse_file()
#         elif mode == "folder":
#             self._browse_folder()

#     def _browse_file(self):
#         filename = filedialog.askopenfilename(
#             title="Виберіть файл для знищення",
#             filetypes=[("Всі файли", "*.*")]
#         )
#         if filename:
#             self.target_path.set(filename)
#             self._update_file_info()

#     def _browse_folder(self):
#         folder = filedialog.askdirectory(title="Виберіть папку для знищення")
#         if folder:
#             self.target_path.set(folder)
#             self._update_file_info()

#     def _count_files_in_folder(self, folder_path):
#         count = 0
#         total_size = 0
#         for root, dirs, files in os.walk(folder_path):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 if os.path.exists(file_path) and os.path.isfile(file_path):
#                     count += 1
#                     try:
#                         total_size += os.path.getsize(file_path)
#                     except Exception:
#                         pass
#         return count, total_size

#     def _update_file_info(self):
#         target = self.target_path.get()
#         mode = self.operation_mode.get()

#         if mode == "disk":
#             return

#         if target and os.path.exists(target):
#             if mode == "file" and os.path.isfile(target):
#                 size = os.path.getsize(target)
#                 size_str = self._format_size(size)
#                 self.size_label.configure(text=f"📄 Розмір: {size_str}")
#             elif mode == "folder" and os.path.isdir(target):
#                 file_count, total_size = self._count_files_in_folder(target)
#                 size_str = self._format_size(total_size)
#                 self.size_label.configure(text=f"📁 Файлів: {file_count} · Загалом: {size_str}")
#             else:
#                 self.size_label.configure(text="Розмір: --")
#         else:
#             self.size_label.configure(text="Розмір: --")

#     def _format_size(self, size_bytes: int) -> str:
#         for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
#             if size_bytes < 1024.0:
#                 return f"{size_bytes:.2f} {unit}"
#             size_bytes /= 1024.0
#         return f"{size_bytes:.2f} PB"

#     def _test_mode(self):
#         def worker():
#             try:
#                 self._set_status("Створення тестового файлу...", COLORS['accent_blue'])
#                 print("\n[ТЕСТОВИЙ РЕЖИМ] Створення тестового файлу...")

#                 engine = WipeEngine()
#                 test_file = engine.create_test_file("test_data.bin", size_mb=10)

#                 self.target_path.set(test_file)
#                 self.operation_mode.set("file")
#                 self._on_segmented_mode_change("Файл")
#                 self._update_file_info()

#                 print(f"✓ Тестовий файл створено: {test_file}\n")
#                 self._set_status("Тестовий файл створено", COLORS['accent_green'])

#                 messagebox.showinfo(
#                     "Успіх",
#                     f"Тестовий файл створено:\n{test_file}\n\n"
#                     f"Тепер оберіть метод знищення та натисніть START WIPE."
#                 )

#             except Exception as e:
#                 print(f"ПОМИЛКА: {e}\n")
#                 self._set_status("Помилка", COLORS['accent_red'])
#                 messagebox.showerror("Помилка", str(e))

#         thread = threading.Thread(target=worker, daemon=True)
#         thread.start()

#     def _start_wipe(self):
#         mode = self.operation_mode.get()
#         method = self.selected_method.get()

#         if mode == "disk":
#             target = self.selected_drive.get()
#             if not target:
#                 messagebox.showwarning("Увага", "Виберіть диск!")
#                 return
#             if not os.path.exists(target):
#                 messagebox.showerror("Помилка", f"Диск не знайдено: {target}")
#                 return
#         else:
#             target = self.target_path.get()
#             if not target:
#                 messagebox.showwarning("Увага", "Виберіть ціль для знищення!")
#                 return
#             if not os.path.exists(target):
#                 messagebox.showerror("Помилка", f"Шлях не існує:\n{target}")
#                 return

#         method_names = {
#             "nist_clear": "NIST Clear (1 pass pseudorandom)",
#             "nist_purge": "NIST Purge (hardware erase)",
#             "crypto_erase": "Crypto Erase (BitLocker key destruction)",
#             "verify": "Verify Only"
#         }

#         mode_names = {
#             "file": "Файл",
#             "folder": "Папка",
#             "disk": "Диск"
#         }

#         method_display = method_names.get(method, method)

#         # NIST Purge: перевірка прав адміністратора
#         if method == "nist_purge" and not WipeEngine().is_admin():
#             messagebox.showerror(
#                 "Недостатньо прав",
#                 "NIST Purge потребує прав адміністратора!\n\n"
#                 "Будь ласка, запустіть програму від імені адміністратора."
#             )
#             return

#         # NIST Purge: попередження про незворотність
#         if method == "nist_purge":
#             confirm_purge = messagebox.askyesno(
#                 "⚠️ Незворотна операція",
#                 "NIST Purge зітре ВЕСЬ ФІЗИЧНИЙ ДИСК, на якому розташований "
#                 "обраний том, включно з усіма розділами та резервними зонами.\n\n"
#                 f"Том: {target}\n"
#                 "Після стирання диск стане неформатованим — потрібно буде "
#                 "заново створити розділ і файлову систему.\n\n"
#                 "Системний диск стирати заборонено.\n\n"
#                 "Усі дані будуть НЕВІДНОВЛЮВАНІ. Продовжити?",
#                 icon='warning'
#             )
#             if not confirm_purge:
#                 return

#         # Crypto Erase: перевірка BitLocker
#         if method == "crypto_erase":
#             if os.name == 'nt':
#                 is_enc, status = WipeEngine().check_bitlocker_status(target.rstrip('\\'))
#                 if not is_enc:
#                     messagebox.showerror(
#                         "Crypto Erase недоступний",
#                         f"Диск {target} не зашифровано BitLocker.\n\n"
#                         "Crypto Erase вимагає увімкненого шифрування.\n"
#                         "Оберіть NIST Clear або NIST Purge."
#                     )
#                     return

#                 confirm_crypto = messagebox.askyesno(
#                     "🔐 Підтвердження Crypto Erase",
#                     "Ця операція знищить ключ шифрування BitLocker.\n\n"
#                     f"Диск: {target}\n"
#                     "Після знищення ключа дані будуть криптографічно недоступні.\n\n"
#                     "⚠️ Це незворотна операція!\n"
#                     "Ви впевнені, що бажаєте продовжити?",
#                     icon='warning'
#                 )
#                 if not confirm_crypto:
#                     return

#         # Інформація про рівень ризику
#         risk_display = WipeEngine.get_risk_level_display(RiskLevel(self.risk_level.get()))

#         confirm = messagebox.askyesno(
#             "Підтвердження",
#             f"УВАГА: ДАНІ БУДУТЬ ЗНИЩЕНІ БЕЗПОВОРОТНО!\n\n"
#             f"Стандарт: NIST 800–88 r2 / IEEE 2883-2022\n"
#             f"Режим: {mode_names[mode]}\n"
#             f"Ціль: {target}\n"
#             f"Метод: {method_display}\n"
#             f"Рівень ризику: {risk_display['icon']} {risk_display['label']}\n\n"
#             f"Продовжити?",
#             icon='warning'
#         )

#         if not confirm:
#             return

#         self.wipe_btn.configure(state="disabled", text="⏳ ВИКОНУЄТЬСЯ...")
#         self._set_status("Виконання...", COLORS['accent_blue'])

#         def worker():
#             try:
#                 self.engine = WipeEngine(progress_callback=self._progress_callback)

#                 start_time = time.time()
#                 result = None

#                 if mode == "file":
#                     if method == "verify":
#                         result = self.engine.verify_wipe(target, method_display)
#                         WipeEngine.save_log("Verify only", target, result)
#                     else:
#                         file_size = os.path.getsize(target) if os.path.exists(target) else 0

#                         if method == "nist_clear":
#                             result = self.engine.wipe_nist_clear(target)
#                         elif method == "nist_purge":
#                             result = self.engine.wipe_nist_purge(target)
#                         elif method == "crypto_erase":
#                             result = self.engine.wipe_crypto_erase(target)

#                         print(f"\n{'═'*50}")
#                         print(f"[ВЕРИФІКАЦІЯ] Стандарт: {WipeEngine.STANDARD_VERSION}")
#                         print(f"  Метод: {method_display}")
#                         print(f"{'═'*50}")

#                         verify_result = self.engine.verify_wipe(
#                             target, method_display,
#                             original_data=None,
#                             file_size=file_size
#                         )
#                         WipeEngine.save_log(method_display, target, verify_result)
#                         result = verify_result

#                 elif mode == "folder":
#                     result = self.engine.wipe_folder(target, method)
#                     WipeEngine.save_log(
#                         f"Folder wipe - {method_display}", target, result
#                     )

#                 elif mode == "disk":
#                     # Crypto Erase працює з усім томом (знищення ключа BitLocker),
#                     # а не пофайлово — викликаємо його напряму
#                     if method == "crypto_erase":
#                         result = self.engine.wipe_crypto_erase(target)
#                         verify_result = self.engine._verify_crypto_erase(
#                             target.strip().rstrip('\\').rstrip(':')
#                         )
#                         result['verification'] = verify_result
#                         if 'bitlocker_status' in verify_result:
#                             result['bitlocker_status'] = verify_result['bitlocker_status']
#                         WipeEngine.save_log(
#                             f"FULL Disk Crypto Erase", target, result
#                         )
#                     # NIST Purge — апаратне стирання цілого фізичного диска через
#                     # diskpart clean all, а не пофайловий перезапис
#                     elif method == "nist_purge":
#                         result = self.engine.wipe_nist_purge(target)
#                         WipeEngine.save_log(
#                             f"FULL Disk Purge - {method_display}", target, result
#                         )
#                     else:
#                         result = self.engine.wipe_disk_full(target, method)
#                         WipeEngine.save_log(
#                             f"FULL Disk wipe - {method_display}", target, result
#                         )

#                 duration = time.time() - start_time
#                 self.after(0, lambda: self._operation_complete(result, mode, duration))

#             except Exception as e:
#                 print(f"\nПОМИЛКА: {e}\n")
#                 self.after(0, lambda: self._operation_error(str(e)))

#         self.operation_thread = threading.Thread(target=worker, daemon=True)
#         self.operation_thread.start()

#     def _progress_callback(self, current_pass: int, total_passes: int,
#                            description: str, progress: float,
#                            bytes_done: int, total_bytes: int):

#         def update():
#             self.progress_bar.set(progress / 100)
#             self.progress_label.configure(text=f"{progress:.1f}%")

#             mode = self.operation_mode.get()

#             if mode == "disk":
#                 filled_gb = bytes_done / (1024 ** 3)
#                 total_gb = total_bytes / (1024 ** 3)
#                 speed = ""
#                 current_time = time.time()
#                 if hasattr(self, '_last_progress_time'):
#                     elapsed = current_time - self._last_progress_time
#                     if elapsed > 0:
#                         speed = f" | {filled_gb / elapsed:.1f} GB/s"
#                 self.details_label.configure(
#                     text=f"Заповнено {filled_gb:.1f} GB з {total_gb:.1f} GB{speed}"
#                 )
#                 self._last_progress_time = current_time
#             else:
#                 current_time = time.time()
#                 if not hasattr(self, '_last_progress_time'):
#                     self._last_progress_time = current_time
#                 elapsed = current_time - self._last_progress_time
#                 if elapsed > 0:
#                     speed = self._format_size(bytes_done / elapsed) + "/s"
#                 else:
#                     speed = "calculating..."
#                 self.details_label.configure(
#                     text=f"Прохід {current_pass}/{total_passes} | {description} | {speed}"
#                 )

#         self.after(0, update)

#     def _operation_complete(self, result: dict, mode: str, duration: float):
#         """Завершення операції"""
#         self.wipe_btn.configure(state="normal", text="🗑️ START WIPE")
#         self.progress_bar.set(1.0)
#         self.progress_label.configure(text="100%")

#         success = result.get('success', False)

#         if success:
#             self._set_status("✓ Знищено успішно", COLORS['accent_green'])
#         else:
#             self._set_status("✗ Знищення неповне", COLORS['accent_red'])

#         # Показуємо статистику залежно від режиму
#         if mode == "file":
#             if success:
#                 self.size_label.configure(
#                     text=f"✓ Знищено: {self._format_size(result.get('file_size', 0))}"
#                 )
#             else:
#                 self.size_label.configure(text="✗ Знищення неповне")

#         elif mode == "folder":
#             wiped = result.get('wiped_files', 0)
#             total = result.get('total_files', 0)
#             size = self._format_size(result.get('total_size', 0))
#             self.size_label.configure(text=f"Знищено: {wiped}/{total} файлів · {size}")

#         elif mode == "disk":
#             filled_gb = result.get('total_space_filled', 0) / (1024 ** 3)
#             self.size_label.configure(text=f"Заповнено: {filled_gb:.2f} GB")

#         # Показуємо модальний діалог з результатами
#         self._show_result_dialog(result, mode, duration)

#     def _show_result_dialog(self, result: dict, mode: str, duration: float):
#         """Показати модальний діалог з результатом"""
#         dialog = ctk.CTkToplevel(self)
#         dialog.title("Результат операції")
#         dialog.geometry("580x520")
#         dialog.resizable(False, False)
#         dialog.configure(fg_color=COLORS['bg_main'])
#         dialog.transient(self)
#         dialog.grab_set()

#         dialog.update_idletasks()
#         x = self.winfo_x() + (self.winfo_width() // 2) - (580 // 2)
#         y = self.winfo_y() + (self.winfo_height() // 2) - (520 // 2)
#         dialog.geometry(f"580x520+{x}+{y}")

#         dialog.grid_columnconfigure(0, weight=1)
#         dialog.grid_rowconfigure(3, weight=1)

#         success = result.get('success', False)

#         if success:
#             icon_text = "✓"
#             title_text = "ОПЕРАЦІЮ ЗАВЕРШЕНО УСПІШНО"
#             bg_color = COLORS['accent_green']
#         else:
#             icon_text = "✗"
#             title_text = "УВАГА: ЗНИЩЕННЯ НЕПОВНЕ"
#             bg_color = COLORS['accent_red']

#         # Іконка
#         icon_label = ctk.CTkLabel(
#             dialog, text=icon_text,
#             font=ctk.CTkFont(size=64), text_color=bg_color
#         )
#         icon_label.grid(row=0, column=0, pady=(30, 10))

#         # Заголовок
#         title_label = ctk.CTkLabel(
#             dialog, text=title_text,
#             font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
#             text_color=bg_color
#         )
#         title_label.grid(row=1, column=0, pady=(0, 10))

#         # Стандарт
#         std_label = ctk.CTkLabel(
#             dialog,
#             text=f"Стандарт: {result.get('standard', WipeEngine.STANDARD_VERSION)}",
#             font=ctk.CTkFont(family="Segoe UI", size=10),
#             text_color=COLORS['text_sub']
#         )
#         std_label.grid(row=2, column=0, pady=(0, 10))

#         # Блок деталей
#         details_frame = ctk.CTkFrame(dialog, fg_color=COLORS['bg_card'], corner_radius=12)
#         details_frame.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="nsew")
#         details_frame.grid_columnconfigure(0, weight=1)

#         row = 0
#         method_display = result.get('method', 'N/A')

#         # === ФАЙЛ ===
#         if mode == "file":
#             details = [
#                 f"Метод: {method_display}",
#                 f"Файл: {self.target_path.get()}",
#                 f"Розмір: {self._format_size(result.get('file_size', 0))}",
#                 f"Час: {result.get('duration', duration):.2f} сек",
#             ]

#             # Специфічна інформація верифікації для кожного методу
#             msg = result.get('message', '')
#             if msg:
#                 details.append(f"Перевірка: {msg}")
#             elif 'percent' in result:
#                 pct = result.get('percent', 0)
#                 passed = result.get('passed_sectors', 0)
#                 total_s = result.get('checked_sectors', 0)
#                 method_name = result.get('method', '')

#                 if 'NIST Clear' in method_name:
#                     details.append(
#                         f"Секторів з псевдовипадковими даними: {passed}/{total_s} ({pct:.2f}%) ✓"
#                         if success else
#                         f"Секторів з низькою ентропією: {result.get('failed_sectors', 0)}/{total_s}"
#                     )
#                 elif 'NIST Purge' in method_name:
#                     details.append(
#                         f"Чистих секторів: {passed}/{total_s} ({pct:.2f}%) ✓"
#                         if success else
#                         f"Ненульових секторів: {result.get('failed_sectors', 0)}/{total_s}"
#                     )
#                 elif 'Zeros' in method_name:
#                     details.append(
#                         f"Нульових секторів: {passed}/{total_s} ({pct:.2f}%) ✓"
#                         if success else
#                         f"Ненульових секторів: {result.get('failed_sectors', 0)}/{total_s}"
#                     )

#             if 'bitlocker_status' in result:
#                 details.append(f"BitLocker: {result.get('bitlocker_status', 'N/A')}")

#         # === ПАПКА ===
#         elif mode == "folder":
#             details = [
#                 f"Метод: {method_display}",
#                 f"Папка: {self.target_path.get()}",
#                 f"Знищено файлів: {result.get('wiped_files', 0)} з {result.get('total_files', 0)}",
#                 f"Загальний розмір: {self._format_size(result.get('total_size', 0))}",
#                 f"Час: {result.get('duration', duration):.2f} сек"
#             ]

#         # === ДИСК ===
#         elif mode == "disk":
#             filled_gb = result.get('total_space_filled', 0) / (1024 ** 3)
#             details = [
#                 f"Метод: {method_display}",
#                 f"Диск: {self.selected_drive.get()}",
#                 f"Заповнено: {filled_gb:.2f} GB",
#                 f"Створено файлів: {result.get('temp_files_created', 0)}",
#                 f"Час: {result.get('duration', duration):.2f} сек"
#             ]

#         for detail in details:
#             label = ctk.CTkLabel(
#                 details_frame, text=detail,
#                 font=ctk.CTkFont(family="Segoe UI", size=12),
#                 text_color=COLORS['text_main'], anchor="w"
#             )
#             label.grid(row=row, column=0, padx=20, pady=(12 if row == 0 else 6, 6), sticky="ew")
#             row += 1

#         # Кнопка закриття
#         close_btn = ctk.CTkButton(
#             dialog, text="OK",
#             font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
#             height=40, corner_radius=8,
#             fg_color=bg_color, hover_color=bg_color,
#             command=dialog.destroy
#         )
#         close_btn.grid(row=4, column=0, padx=30, pady=(0, 25))

#         dialog.after(15000, dialog.destroy)

#     def _operation_error(self, error_msg: str):
#         """Помилка операції"""
#         self.wipe_btn.configure(state="normal", text="🗑️ START WIPE")
#         self._set_status("Помилка", COLORS['accent_red'])
#         messagebox.showerror("Помилка", error_msg)

#     def _clean_artifacts(self):
#         """Очищення артефактів Windows"""
#         confirm = messagebox.askyesno(
#             "Очищення слідів",
#             "Очистити артефакти Windows?\n\n"
#             "Це видалить:\n"
#             "• Кошик (Recycle Bin)\n"
#             "• Prefetch файли\n"
#             "• Recent files\n"
#             "• Thumbnail cache\n"
#             "• Тіньові копії VSS (потрібні права адміна)\n\n"
#             "Продовжити?",
#             icon='warning'
#         )

#         if not confirm:
#             return

#         def worker():
#             try:
#                 self._set_status("Очищення слідів Windows...", COLORS['accent_blue'])
#                 print("\n[АРТЕФАКТИ] Очищення...\n")

#                 engine = WipeEngine()
#                 result = engine.clean_windows_artifacts()

#                 self.after(0, lambda: self._artifacts_complete(result))

#             except Exception as e:
#                 print(f"\nПОМИЛКА: {e}\n")
#                 self.after(0, lambda: self._set_status("Помилка", COLORS['accent_red']))

#         thread = threading.Thread(target=worker, daemon=True)
#         thread.start()

#     def _artifacts_complete(self, result: dict):
#         """Завершення очищення артефактів"""
#         if result.get('success'):
#             self._set_status("Артефакти очищено ✓", COLORS['accent_green'])
#             messagebox.showinfo("Успіх", "Артефакти Windows очищено!")
#         else:
#             self._set_status("Помилка очищення", COLORS['accent_red'])
#             messagebox.showwarning(
#                 "Увага",
#                 "Деякі операції не виконані.\n"
#                 "Можливо, потрібні права адміністратора."
#             )

#     def _set_status(self, text: str, color: str):
#         """Оновлення статусу"""
#         self.status_label.configure(text=f"Статус: {text}", text_color=color)


# def main():
#     """Головна функція"""
#     app = SecureWipePro()
#     app.mainloop()


# if __name__ == "__main__":
#     main()


#!/usr/bin/env python3
"""
Режими роботи:
- РЕЖИМ 1: Файл (знищити один файл)
- РЕЖИМ 2: Папка (рекурсивно знищити всі файли в папці)
- РЕЖИМ 3: Диск (заповнити вільний простір)
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

# Try to import CustomTkinter
try:
    import customtkinter as ctk
    from customtkinter import (
        CTk, CTkFrame, CTkLabel, CTkButton, CTkRadioButton, CTkSegmentedButton,
        CTkComboBox, CTkScrollableFrame
    )
    CTK_AVAILABLE = True
except ImportError:
    print("ПОМИЛКА: CustomTkinter не встановлено!")
    print("Встановіть: pip install customtkinter")
    sys.exit(1)

# Імпортуємо wipe engine
try:
    from wipe_engine import WipeEngine, RiskLevel
except ImportError:
    print("ПОМИЛКА: Не знайдено wipe_engine.py!")
    sys.exit(1)

# Кольорова схема (Dark theme)
COLORS = {
    'bg_main': '#1C1C1E',
    'bg_card': '#2C2C2E',
    'bg_terminal': '#0D0D0D',
    'accent_red': '#FF3B30',
    'accent_red_hover': '#FF6961',
    'accent_blue': '#0A84FF',
    'accent_blue_hover': '#3A9EFF',
    'accent_green': '#30D158',
    'accent_green_hover': '#52DE7A',
    'accent_orange': '#FF9F0A',
    'accent_purple': '#BF5AF2',
    'text_main': '#FFFFFF',
    'text_sub': '#8E8E93',
    'text_warning': '#FFD60A',
    'border_color': '#3A3A3C'
}

# Налаштування CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SplashScreen(ctk.CTkToplevel):
    """Splash screen при запуску програми"""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("")
        self.geometry("500x350")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_main'])

        self.overrideredirect(True)

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (350 // 2)
        self.geometry(f"500x350+{x}+{y}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_main'], corner_radius=16)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        main_frame.grid_columnconfigure(0, weight=1)

        logo_label = ctk.CTkLabel(main_frame, text="🛡️", font=ctk.CTkFont(size=72))
        logo_label.grid(row=0, column=0, pady=(40, 10))

        title_label = ctk.CTkLabel(
            main_frame, text="SecureWipe Pro",
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            text_color=COLORS['text_main']
        )
        title_label.grid(row=1, column=0, pady=(0, 5))

        version_label = ctk.CTkLabel(
            main_frame, text="v2.0 — NIST 800–88 r2 / IEEE 2883-2022",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS['accent_blue']
        )
        version_label.grid(row=2, column=0, pady=(0, 5))

        desc_label = ctk.CTkLabel(
            main_frame,
            text="Сучасне знищення даних\nвідповідньо до міжнародних стандартів",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub']
        )
        desc_label.grid(row=3, column=0, pady=(10, 20))

        self.progress = ctk.CTkProgressBar(
            main_frame, mode="indeterminate",
            progress_color=COLORS['accent_blue']
        )
        self.progress.grid(row=4, column=0, padx=40, sticky="ew")
        self.progress.start()

        self.status_label = ctk.CTkLabel(
            main_frame, text="Ініціалізація...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub']
        )
        self.status_label.grid(row=5, column=0, pady=(10, 30))

    def update_status(self, text: str):
        self.status_label.configure(text=text)
        self.update_idletasks()

    def close(self):
        self.progress.stop()
        self.destroy()


class TerminalWidget(ctk.CTkTextbox):
    """Термінальний віджет для виводу логів"""

    def __init__(self, master, **kwargs):
        super().__init__(
            master, fg_color=COLORS['bg_terminal'],
            text_color="#00FF00",
            font=ctk.CTkFont(family="Consolas", size=12), **kwargs
        )
        self.configure(wrap="word")

    def write(self, text: str):
        self.insert("end", text)
        self.see("end")
        self.update_idletasks()

    def flush(self):
        pass


class MethodCard(ctk.CTkFrame):
    """Картка методу знищення"""

    def __init__(self, master, method_id: str, title: str, description: str,
                 details: str, color: str, **kwargs):
        super().__init__(master, fg_color=COLORS['bg_card'], corner_radius=10, **kwargs)

        self.method_id = method_id
        self.color = color

        title_label = ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLORS['text_main']
        )
        title_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        desc_label = ctk.CTkLabel(
            self, text=description,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub'], wraplength=350
        )
        desc_label.grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")

        details_label = ctk.CTkLabel(
            self, text=details,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=color
        )
        details_label.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="w")


class SecureWipePro(ctk.CTk):
    """Головне вікно SecureWipe Pro v2.0"""

    def __init__(self):
        super().__init__()

        self.title("🔒 SecureWipe Pro")
        self.geometry("1280x850")
        self.minsize(1200, 800)
        self.configure(fg_color=COLORS['bg_main'])

        self.selected_method = tk.StringVar(value="nist_clear")
        self.operation_mode = tk.StringVar(value="file")
        self.target_path = tk.StringVar()
        self.selected_drive = tk.StringVar()
        self.engine = None
        self.operation_thread = None
        self.current_operation = None
        self._last_progress_time = 0

        # Рівень ризику для ризик-орієнтованого вибору методу
        self.risk_level = tk.StringVar(value="medium")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self._setup_drag_drop()

        self.withdraw()
        self.splash = SplashScreen(self)
        self.after(2500, self._close_splash)

    def _close_splash(self):
        self.splash.close()
        self.deiconify()
        self.lift()
        self.focus_force()

    def _create_widgets(self):
        # Головний контейнер з прокруткою
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS['bg_main'])
        self.main_scroll.grid(row=0, column=0, sticky="nsew")
        self.main_scroll.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_container = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame, text="🔒 SecureWipe Pro",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS['text_main']
        )
        title_label.grid(row=0, column=0, sticky="w")

        std_label = ctk.CTkLabel(
            header_frame, text="NIST 800–88 r2 / IEEE 2883-2022",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['accent_blue']
        )
        std_label.grid(row=1, column=0, sticky="w", pady=(3, 0))

        theme_btn = ctk.CTkButton(
            header_frame, text="☀️", width=40, height=40,
            corner_radius=20, fg_color=COLORS['bg_card'],
            hover_color=COLORS['accent_blue']
        )
        theme_btn.grid(row=0, column=1, sticky="e")

        # ── Ліва панель ──
        left_panel = ctk.CTkScrollableFrame(
            main_container, fg_color=COLORS['bg_card'], corner_radius=12,
            label_text="  МЕТОДИ ЗНИЩЕННЯ  ",
            label_font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            label_fg_color=COLORS['bg_card'],
            label_text_color=COLORS['text_sub']
        )
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_columnconfigure(0, weight=1)

        self._create_method_cards(left_panel)

        # ── Права панель ──
        right_panel = ctk.CTkScrollableFrame(
            main_container, fg_color=COLORS['bg_card'], corner_radius=12,
            label_text="  НАЛАШТУВАННЯ  ",
            label_font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            label_fg_color=COLORS['bg_card'],
            label_text_color=COLORS['text_sub']
        )
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        right_panel.grid_columnconfigure(0, weight=1)

        self._create_status_panel(right_panel)

        # ── Нижня панель ──
        bottom_panel = ctk.CTkFrame(main_container, fg_color="transparent")
        bottom_panel.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        bottom_panel.grid_columnconfigure(0, weight=1)
        bottom_panel.grid_columnconfigure(1, weight=1)
        bottom_panel.grid_columnconfigure(2, weight=1)

        self._create_action_buttons(bottom_panel)

        # ── Термінал ──
        terminal_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        terminal_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        terminal_frame.grid_columnconfigure(0, weight=1)

        terminal_label = ctk.CTkLabel(
            terminal_frame, text="📋 ЛОГ ОПЕРАЦІЙ",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS['text_sub']
        )
        terminal_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.terminal = TerminalWidget(terminal_frame, height=140)
        self.terminal.grid(row=1, column=0, sticky="ew")

        sys.stdout = self.terminal

        print("╔══════════════════════════════════════════════╗")
        print("║       SecureWipe Pro                     ║")
        print("║       NIST 800–88 r2 / IEEE 2883-2022       ║")
        print("╚══════════════════════════════════════════════╝")
        print("Готовий до роботи.\n")

    def _create_method_cards(self, parent):
        methods = [
            {
                'id': 'nist_clear',
                'title': 'NIST Clear',
                'desc': 'Захист від програмного відновлення',
                'details': '1 прохід · псевдовипадкові дані · HDD / USB',
                'color': COLORS['accent_blue']
            },
            {
                'id': 'nist_purge',
                'title': 'NIST Purge (апаратне стирання)',
                'desc': 'Знищення включно з резервним простором контролера',
                'details': 'diskpart clean all · ATA SE · NVMe Sanitize · ⚠️ Потребує права адміна',
                'color': COLORS['accent_red']
            },
            {
                'id': 'crypto_erase',
                'title': 'Crypto Erase',
                'desc': 'Миттєве криптографічне знищення через BitLocker',
                'details': 'Знищення ключа · без перезапису · ⚠️ Лише зашифровані диски',
                'color': COLORS['accent_purple']
            },
            {
                'id': 'verify',
                'title': 'Verify Only',
                'desc': 'Перевірка чистоти носія без знищення',
                'details': 'Зчитування та аналіз секторів · без змін',
                'color': COLORS['accent_green']
            }
        ]

        for i, m in enumerate(methods):
            # Контейнер для картки з радіо-кнопкою
            container = ctk.CTkFrame(parent, fg_color="transparent")
            container.grid(row=i, column=0, padx=10, pady=(0, 8), sticky="ew")
            container.grid_columnconfigure(1, weight=1)

            # Радіо-кнопка зліва
            rb = ctk.CTkRadioButton(
                container, text="", variable=self.selected_method,
                value=m['id'], width=20, height=20
            )
            rb.grid(row=0, column=0, padx=(5, 10), pady=15, sticky="w")

            # Картка методу
            card = MethodCard(
                container, method_id=m['id'], title=m['title'],
                description=m['desc'], details=m['details'], color=m['color']
            )
            card.grid(row=0, column=1, sticky="ew")

            def make_card_clickable(card_widget, method_val):
                def on_click(event=None):
                    self.selected_method.set(method_val)
                    self._on_method_change(method_val)
                card_widget.bind("<Button-1>", on_click)
                for child in card_widget.winfo_children():
                    child.bind("<Button-1>", on_click)

            make_card_clickable(card, m['id'])

    def _create_status_panel(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        self.mode_segmented = ctk.CTkSegmentedButton(
            parent, values=["Файл", "Папка", "Диск"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40, corner_radius=8,
            fg_color=COLORS['bg_main'],
            selected_color=COLORS['accent_blue'],
            unselected_color=COLORS['bg_card'],
            text_color=COLORS['text_main'],
            unselected_hover_color=COLORS['accent_blue_hover'],
            command=self._on_segmented_mode_change
        )
        self.mode_segmented.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.mode_segmented.set("Файл")

        self.mode_desc_label = ctk.CTkLabel(
            parent, text="Знищити один файл обраним методом",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_sub']
        )
        self.mode_desc_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        separator = ctk.CTkFrame(parent, height=2, fg_color=COLORS['border_color'])
        separator.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")

        # ── Секція оцінки ризику ──
        risk_label = ctk.CTkLabel(
            parent, text="ОЦІНКА РИЗИКУ АКТИВУ",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS['text_sub']
        )
        risk_label.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="w")

        risk_frame = ctk.CTkFrame(parent, fg_color="transparent")
        risk_frame.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        risk_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Кнопки вибору рівня ризику
        self.risk_low_btn = ctk.CTkButton(
            risk_frame, text="🟢 Низький",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            height=32, corner_radius=8,
            fg_color=COLORS['bg_main'],
            hover_color=COLORS['accent_green'],
            command=lambda: self._set_risk_level("low")
        )
        self.risk_low_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.risk_medium_btn = ctk.CTkButton(
            risk_frame, text="🟡 Середній",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            height=32, corner_radius=8,
            fg_color=COLORS['accent_orange'],
            hover_color=COLORS['accent_orange'],
            command=lambda: self._set_risk_level("medium")
        )
        self.risk_medium_btn.grid(row=0, column=1, padx=5, sticky="ew")

        self.risk_high_btn = ctk.CTkButton(
            risk_frame, text="🔴 Високий",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            height=32, corner_radius=8,
            fg_color=COLORS['bg_main'],
            hover_color=COLORS['accent_red'],
            command=lambda: self._set_risk_level("high")
        )
        self.risk_high_btn.grid(row=0, column=2, padx=(5, 0), sticky="ew")

        # Інформація про рекомендований метод
        self.risk_info_frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_main'], corner_radius=8)
        self.risk_info_frame.grid(row=5, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.risk_info_frame.grid_columnconfigure(0, weight=1)

        self.risk_info_label = ctk.CTkLabel(
            self.risk_info_frame,
            text="Рекомендований метод: NIST Purge",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS['accent_orange']
        )
        self.risk_info_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        self.risk_desc_label = ctk.CTkLabel(
            self.risk_info_frame,
            text="Апаратне стирання для персональних даних",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS['text_sub']
        )
        self.risk_desc_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        separator2 = ctk.CTkFrame(parent, height=2, fg_color=COLORS['border_color'])
        separator2.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")

        label = ctk.CTkLabel(
            parent, text="ПАНЕЛЬ СТАТУСУ",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS['text_sub']
        )
        label.grid(row=7, column=0, padx=20, pady=(0, 15), sticky="w")

        target_frame = ctk.CTkFrame(parent, fg_color="transparent")
        target_frame.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")
        target_frame.grid_columnconfigure(0, weight=1)

        self.target_label = ctk.CTkLabel(
            target_frame, text="Ціль:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub']
        )
        self.target_label.grid(row=0, column=0, sticky="w")

        input_frame = ctk.CTkFrame(target_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        input_frame.grid_columnconfigure(0, weight=1)

        self.target_entry = ctk.CTkEntry(
            input_frame, textvariable=self.target_path,
            placeholder_text="Перетягніть файл або натисніть 📁",
            font=ctk.CTkFont(family="Segoe UI", size=12), height=35
        )
        self.target_entry.grid(row=0, column=0, sticky="ew")

        self.browse_btn = ctk.CTkButton(
            input_frame, text="📁", width=40, height=35,
            corner_radius=8, fg_color=COLORS['bg_card'],
            hover_color=COLORS['accent_blue'], command=self._browse_file
        )
        self.browse_btn.grid(row=0, column=1, padx=(8, 0))

        self.disk_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.disk_frame.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.disk_frame.grid_columnconfigure(0, weight=1)

        disk_label = ctk.CTkLabel(
            self.disk_frame, text="Виберіть диск для очищення:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub']
        )
        disk_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        drives = WipeEngine.get_available_drives()
        if not drives:
            drives = ["C:\\", "D:\\", "E:\\"]

        drives_with_custom = drives + ["Інший диск..."]

        self.disk_combo = ctk.CTkComboBox(
            self.disk_frame, values=drives_with_custom,
            variable=self.selected_drive,
            font=ctk.CTkFont(family="Segoe UI", size=12), height=40,
            command=self._on_disk_selected
        )
        self.disk_combo.grid(row=1, column=0, sticky="ew")

        if drives:
            self.disk_combo.set(drives[0])
            self.selected_drive.set(drives[0])

        self.disk_frame.grid_remove()

        self.info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.info_frame.grid(row=10, column=0, padx=20, pady=(10, 5), sticky="ew")
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.size_label = ctk.CTkLabel(
            self.info_frame, text="Розмір: --",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_main']
        )
        self.size_label.grid(row=0, column=0, sticky="w")

        self.method_label = ctk.CTkLabel(
            self.info_frame, text="Метод: NIST Clear",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['accent_blue']
        )
        self.method_label.grid(row=1, column=0, sticky="w", pady=(3, 0))

        self.status_label = ctk.CTkLabel(
            self.info_frame, text="Статус: Готовий",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['accent_green']
        )
        self.status_label.grid(row=2, column=0, sticky="w", pady=(5, 0))

        progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
        progress_frame.grid(row=11, column=0, padx=20, pady=(10, 20), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame, mode="determinate",
            progress_color=COLORS['accent_blue'],
            height=20, corner_radius=10
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_frame, text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_sub']
        )
        self.progress_label.grid(row=1, column=0, pady=(5, 0))

        self.details_label = ctk.CTkLabel(
            parent, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_sub'], wraplength=400
        )
        self.details_label.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="w")

    def _set_risk_level(self, level: str):
        """Встановити рівень ризику та оновити рекомендації"""
        self.risk_level.set(level)

        # Оновити вигляд кнопок
        self.risk_low_btn.configure(
            fg_color=COLORS['accent_green'] if level == "low" else COLORS['bg_main']
        )
        self.risk_medium_btn.configure(
            fg_color=COLORS['accent_orange'] if level == "medium" else COLORS['bg_main']
        )
        self.risk_high_btn.configure(
            fg_color=COLORS['accent_red'] if level == "high" else COLORS['bg_main']
        )

        # Отримати рекомендований метод
        risk_enum = RiskLevel(level)
        is_encrypted = False
        if self.operation_mode.get() == "disk":
            drive = self.selected_drive.get()
            if drive:
                is_encrypted, _ = WipeEngine().check_bitlocker_status(drive.rstrip('\\'))

        recommendation = WipeEngine.get_recommended_method(risk_enum, is_encrypted)

        # Оновити відображення рекомендації
        risk_display = WipeEngine.get_risk_level_display(risk_enum)
        self.risk_info_label.configure(
            text=f"Рекомендований метод: {recommendation['method_name']}",
            text_color=risk_display['color']
        )
        self.risk_desc_label.configure(text=recommendation['description'])

        # Автоматично вибрати рекомендований метод
        self.selected_method.set(recommendation['method_id'])
        self._on_method_change(recommendation['method_id'])

    def _create_action_buttons(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_columnconfigure(2, weight=1)

        test_btn = ctk.CTkButton(
            parent, text="🧪 TEST MODE",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=50, corner_radius=12,
            fg_color=COLORS['accent_blue'],
            hover_color=COLORS['accent_blue_hover'],
            command=self._test_mode
        )
        test_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.wipe_btn = ctk.CTkButton(
            parent, text="🗑️ START WIPE",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=50, corner_radius=12,
            fg_color=COLORS['accent_red'],
            hover_color=COLORS['accent_red_hover'],
            command=self._start_wipe
        )
        self.wipe_btn.grid(row=0, column=1, padx=(10, 10), sticky="ew")

        if os.name == 'nt':
            clean_btn = ctk.CTkButton(
                parent, text="🧹 Очистити сліди",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                height=50, corner_radius=12,
                fg_color=COLORS['bg_card'],
                hover_color=COLORS['accent_blue_hover'],
                command=self._clean_artifacts
            )
            clean_btn.grid(row=0, column=2, padx=(10, 0), sticky="ew")

    def _on_method_change(self, method_id: str):
        names = {
            'nist_clear': 'NIST Clear',
            'nist_purge': 'NIST Purge',
            'crypto_erase': 'Crypto Erase',
            'verify': 'Verify Only'
        }
        self.method_label.configure(text=f"Метод: {names.get(method_id, method_id)}")

        if method_id == 'crypto_erase':
            mode = self.operation_mode.get()
            if mode == 'disk':
                drive = self.selected_drive.get()
                if drive:
                    is_enc, status = WipeEngine().check_bitlocker_status(drive.rstrip('\\'))
                    if not is_enc:
                        self.status_label.configure(
                            text="⚠️ Диск не зашифрований! Crypto Erase недоступний.",
                            text_color=COLORS['text_warning']
                        )
                    else:
                        self.status_label.configure(
                            text=f"✓ Диск зашифровано ({status}). Crypto Erase готовий.",
                            text_color=COLORS['accent_green']
                        )

        if method_id == 'nist_purge':
            if not WipeEngine().is_admin():
                self.status_label.configure(
                    text="⚠️ Потрібні права адміністратора для NIST Purge!",
                    text_color=COLORS['text_warning']
                )

    def _on_segmented_mode_change(self, mode_text):
        mode_map = {"Файл": "file", "Папка": "folder", "Диск": "disk"}
        mode = mode_map.get(mode_text, "file")
        self.operation_mode.set(mode)

        desc_map = {
            "file": "Знищити один файл обраним методом",
            "folder": "Рекурсивно знищити всі файли в папці",
            "disk": "ПОВНЕ ЗНИЩЕННЯ ВСЬОГО ДИСКА (файли + папки + вільний простір)"
        }
        self.mode_desc_label.configure(text=desc_map.get(mode, ""))

        if mode == "file":
            self.target_label.configure(text="Ціль:")
            self.target_entry.configure(placeholder_text="Перетягніть файл або натисніть 📁")
            self.browse_btn.configure(command=self._browse_file)
            self.disk_frame.grid_remove()
            target_frame = self.target_entry.master
            target_frame.grid()
        elif mode == "folder":
            self.target_label.configure(text="Папка:")
            self.target_entry.configure(placeholder_text="Виберіть папку або натисніть 📁")
            self.browse_btn.configure(command=self._browse_folder)
            self.disk_frame.grid_remove()
            target_frame = self.target_entry.master
            target_frame.grid()
        elif mode == "disk":
            self.target_label.configure(text="Диск:")
            target_frame = self.target_entry.master
            target_frame.grid_remove()
            self.disk_frame.grid()
            self._update_disk_info()

        self.target_path.set("")
        self._update_file_info()

    def _on_disk_selected(self, choice):
        if choice == "Інший диск...":
            custom_path = simpledialog.askstring(
                "Вибір диска", "Введіть шлях до диска (наприклад, E:\\):", parent=self
            )
            if custom_path:
                if not custom_path.endswith('\\'):
                    custom_path = custom_path.rstrip('\\') + '\\'
                current_values = list(self.disk_combo.cget("values"))
                if custom_path not in current_values:
                    current_values.insert(-1, custom_path)
                    self.disk_combo.configure(values=current_values)
                self.disk_combo.set(custom_path)
                self.selected_drive.set(custom_path)
                self._update_disk_info(custom_path)
            else:
                drives = WipeEngine.get_available_drives()
                if drives:
                    self.disk_combo.set(drives[0])
                    self.selected_drive.set(drives[0])
        else:
            self.selected_drive.set(choice)
            self._update_disk_info(choice)

        current_method = self.selected_method.get()
        if current_method == 'crypto_erase':
            self._on_method_change(current_method)

        # Оновити рекомендацію при зміні диска
        self._set_risk_level(self.risk_level.get())

    def _update_disk_info(self, drive_path=None):
        if drive_path is None:
            drive_path = self.selected_drive.get()

        if drive_path and os.path.exists(drive_path):
            try:
                import shutil
                total, used, free = shutil.disk_usage(drive_path)
                free_gb = free / (1024 ** 3)
                total_gb = total / (1024 ** 3)
                used_gb = used / (1024 ** 3)
                pct = (used / total * 100) if total > 0 else 0
                self.size_label.configure(
                    text=f"📊 {used_gb:.1f}/{total_gb:.1f} GB використано ({pct:.0f}%)\n"
                         f"   Вільно: {free_gb:.2f} GB"
                )
                self.status_label.configure(
                    text=f"Диск {drive_path} готовий до очищення",
                    text_color=COLORS['accent_green']
                )
            except Exception:
                self.size_label.configure(text="Помилка читання диска")
                self.status_label.configure(text="Помилка", text_color=COLORS['accent_red'])
        else:
            self.size_label.configure(text="Диск не знайдено")
            self.status_label.configure(text="Помилка", text_color=COLORS['accent_red'])

    def _setup_drag_drop(self):
        self.target_entry.bind("<ButtonRelease-1>", lambda e: self._browse_target())
        self.target_entry.bind("<Button-3>", self._paste_from_clipboard)

    def _paste_from_clipboard(self, event):
        try:
            clipboard = self.clipboard_get()
            if os.path.exists(clipboard):
                self.target_path.set(clipboard)
                self._update_file_info()
        except Exception:
            pass

    def _browse_target(self):
        mode = self.operation_mode.get()
        if mode == "file":
            self._browse_file()
        elif mode == "folder":
            self._browse_folder()

    def _browse_file(self):
        filename = filedialog.askopenfilename(
            title="Виберіть файл для знищення",
            filetypes=[("Всі файли", "*.*")]
        )
        if filename:
            self.target_path.set(filename)
            self._update_file_info()

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Виберіть папку для знищення")
        if folder:
            self.target_path.set(folder)
            self._update_file_info()

    def _count_files_in_folder(self, folder_path):
        count = 0
        total_size = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    count += 1
                    try:
                        total_size += os.path.getsize(file_path)
                    except Exception:
                        pass
        return count, total_size

    def _update_file_info(self):
        target = self.target_path.get()
        mode = self.operation_mode.get()

        if mode == "disk":
            return

        if target and os.path.exists(target):
            if mode == "file" and os.path.isfile(target):
                size = os.path.getsize(target)
                size_str = self._format_size(size)
                self.size_label.configure(text=f"📄 Розмір: {size_str}")
            elif mode == "folder" and os.path.isdir(target):
                file_count, total_size = self._count_files_in_folder(target)
                size_str = self._format_size(total_size)
                self.size_label.configure(text=f"📁 Файлів: {file_count} · Загалом: {size_str}")
            else:
                self.size_label.configure(text="Розмір: --")
        else:
            self.size_label.configure(text="Розмір: --")

    def _format_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _test_mode(self):
        def worker():
            try:
                self._set_status("Створення тестового файлу...", COLORS['accent_blue'])
                print("\n[ТЕСТОВИЙ РЕЖИМ] Створення тестового файлу...")

                engine = WipeEngine()
                test_file = engine.create_test_file("test_data.bin", size_mb=10)

                self.target_path.set(test_file)
                self.operation_mode.set("file")
                self._on_segmented_mode_change("Файл")
                self._update_file_info()

                print(f"✓ Тестовий файл створено: {test_file}\n")
                self._set_status("Тестовий файл створено", COLORS['accent_green'])

                messagebox.showinfo(
                    "Успіх",
                    f"Тестовий файл створено:\n{test_file}\n\n"
                    f"Тепер оберіть метод знищення та натисніть START WIPE."
                )

            except Exception as e:
                print(f"ПОМИЛКА: {e}\n")
                self._set_status("Помилка", COLORS['accent_red'])
                messagebox.showerror("Помилка", str(e))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _start_wipe(self):
        mode = self.operation_mode.get()
        method = self.selected_method.get()

        if mode == "disk":
            target = self.selected_drive.get()
            if not target:
                messagebox.showwarning("Увага", "Виберіть диск!")
                return
            if not os.path.exists(target):
                messagebox.showerror("Помилка", f"Диск не знайдено: {target}")
                return
        else:
            target = self.target_path.get()
            if not target:
                messagebox.showwarning("Увага", "Виберіть ціль для знищення!")
                return
            if not os.path.exists(target):
                messagebox.showerror("Помилка", f"Шлях не існує:\n{target}")
                return

        method_names = {
            "nist_clear": "NIST Clear (1 pass pseudorandom)",
            "nist_purge": "NIST Purge (hardware erase)",
            "crypto_erase": "Crypto Erase (BitLocker key destruction)",
            "verify": "Verify Only"
        }

        mode_names = {
            "file": "Файл",
            "folder": "Папка",
            "disk": "Диск"
        }

        method_display = method_names.get(method, method)

        # NIST Purge: перевірка прав адміністратора
        if method == "nist_purge" and not WipeEngine().is_admin():
            messagebox.showerror(
                "Недостатньо прав",
                "NIST Purge потребує прав адміністратора!\n\n"
                "Будь ласка, запустіть програму від імені адміністратора."
            )
            return

        # NIST Purge: попередження про незворотність
        if method == "nist_purge":
            confirm_purge = messagebox.askyesno(
                "⚠️ Незворотна операція",
                "NIST Purge перезапише ВЕСЬ диск, включно з резервними зонами.\n\n"
                f"Диск: {target}\n"
                "Усі дані будуть НЕВІДНОНОВЛЮВАНІ.\n\n"
                "Ви впевнені, що бажаєте продовжити?",
                icon='warning'
            )
            if not confirm_purge:
                return

        # Crypto Erase: перевірка BitLocker
        if method == "crypto_erase":
            if os.name == 'nt':
                is_enc, status = WipeEngine().check_bitlocker_status(target.rstrip('\\'))
                if not is_enc:
                    messagebox.showerror(
                        "Crypto Erase недоступний",
                        f"Диск {target} не зашифровано BitLocker.\n\n"
                        "Crypto Erase вимагає увімкненого шифрування.\n"
                        "Оберіть NIST Clear або NIST Purge."
                    )
                    return

                confirm_crypto = messagebox.askyesno(
                    "🔐 Підтвердження Crypto Erase",
                    "Ця операція знищить ключ шифрування BitLocker.\n\n"
                    f"Диск: {target}\n"
                    "Після знищення ключа дані будуть криптографічно недоступні.\n\n"
                    "⚠️ Це незворотна операція!\n"
                    "Ви впевнені, що бажаєте продовжити?",
                    icon='warning'
                )
                if not confirm_crypto:
                    return

        # Інформація про рівень ризику
        risk_display = WipeEngine.get_risk_level_display(RiskLevel(self.risk_level.get()))

        confirm = messagebox.askyesno(
            "Підтвердження",
            f"УВАГА: ДАНІ БУДУТЬ ЗНИЩЕНІ БЕЗПОВОРОТНО!\n\n"
            f"Стандарт: NIST 800–88 r2 / IEEE 2883-2022\n"
            f"Режим: {mode_names[mode]}\n"
            f"Ціль: {target}\n"
            f"Метод: {method_display}\n"
            f"Рівень ризику: {risk_display['icon']} {risk_display['label']}\n\n"
            f"Продовжити?",
            icon='warning'
        )

        if not confirm:
            return

        self.wipe_btn.configure(state="disabled", text="⏳ ВИКОНУЄТЬСЯ...")
        self._set_status("Виконання...", COLORS['accent_blue'])

        def worker():
            try:
                self.engine = WipeEngine(progress_callback=self._progress_callback)

                start_time = time.time()
                start_iso = datetime.now().isoformat(timespec='seconds')
                result = None

                if mode == "file":
                    if method == "verify":
                        result = self.engine.verify_wipe(target, method_display)
                        WipeEngine.save_log("Verify only", target, result)
                    else:
                        file_size = os.path.getsize(target) if os.path.exists(target) else 0

                        if method == "nist_clear":
                            result = self.engine.wipe_nist_clear(target)
                        elif method == "nist_purge":
                            result = self.engine.wipe_nist_purge(target)
                        elif method == "crypto_erase":
                            result = self.engine.wipe_crypto_erase(target)

                        print(f"\n{'═'*50}")
                        print(f"[ВЕРИФІКАЦІЯ] Стандарт: {WipeEngine.STANDARD_VERSION}")
                        print(f"  Метод: {method_display}")
                        print(f"{'═'*50}")

                        verify_result = self.engine.verify_wipe(
                            target, method_display,
                            original_data=None,
                            file_size=file_size
                        )
                        WipeEngine.save_log(method_display, target, verify_result)
                        result = verify_result

                elif mode == "folder":
                    result = self.engine.wipe_folder(target, method)
                    WipeEngine.save_log(
                        f"Folder wipe - {method_display}", target, result
                    )

                elif mode == "disk":
                    # Crypto Erase працює з усім томом (знищення ключа BitLocker),
                    # а не пофайлово — викликаємо його напряму
                    if method == "crypto_erase":
                        result = self.engine.wipe_crypto_erase(target)
                        verify_result = self.engine._verify_crypto_erase(
                            target.strip().rstrip('\\').rstrip(':')
                        )
                        result['verification'] = verify_result
                        if 'bitlocker_status' in verify_result:
                            result['bitlocker_status'] = verify_result['bitlocker_status']
                        WipeEngine.save_log(
                            f"FULL Disk Crypto Erase", target, result
                        )
                    else:
                        result = self.engine.wipe_disk_full(target, method)
                        WipeEngine.save_log(
                            f"FULL Disk wipe - {method_display}", target, result
                        )

                duration = time.time() - start_time
                end_iso = datetime.now().isoformat(timespec='seconds')

                # Зберігаємо дані для можливої генерації сертифіката
                self._last_cert_data = {
                    "sanitization_method": (result or {}).get("method", method_display),
                    "timestamps": {"start_time": start_iso, "end_time": end_iso},
                    "verification_result": {
                        "status": (result or {}).get("verification", {}).get("status")
                                  or (result or {}).get("status", ""),
                        "bad_blocks_found": 0,
                        "verification_method": (result or {}).get("verification", {}).get("details", ""),
                    },
                    "object_path": target,
                    "standard": (result or {}).get("standard", WipeEngine.STANDARD_VERSION),
                }
                self.after(0, lambda: self._operation_complete(result, mode, duration))

            except Exception as e:
                print(f"\nПОМИЛКА: {e}\n")
                self.after(0, lambda: self._operation_error(str(e)))

        self.operation_thread = threading.Thread(target=worker, daemon=True)
        self.operation_thread.start()

    def _progress_callback(self, current_pass: int, total_passes: int,
                           description: str, progress: float,
                           bytes_done: int, total_bytes: int):

        def update():
            self.progress_bar.set(progress / 100)
            self.progress_label.configure(text=f"{progress:.1f}%")

            mode = self.operation_mode.get()

            if mode == "disk":
                filled_gb = bytes_done / (1024 ** 3)
                total_gb = total_bytes / (1024 ** 3)
                speed = ""
                current_time = time.time()
                if hasattr(self, '_last_progress_time'):
                    elapsed = current_time - self._last_progress_time
                    if elapsed > 0:
                        speed = f" | {filled_gb / elapsed:.1f} GB/s"
                self.details_label.configure(
                    text=f"Заповнено {filled_gb:.1f} GB з {total_gb:.1f} GB{speed}"
                )
                self._last_progress_time = current_time
            else:
                current_time = time.time()
                if not hasattr(self, '_last_progress_time'):
                    self._last_progress_time = current_time
                elapsed = current_time - self._last_progress_time
                if elapsed > 0:
                    speed = self._format_size(bytes_done / elapsed) + "/s"
                else:
                    speed = "calculating..."
                self.details_label.configure(
                    text=f"Прохід {current_pass}/{total_passes} | {description} | {speed}"
                )

        self.after(0, update)

    def _operation_complete(self, result: dict, mode: str, duration: float):
        """Завершення операції"""
        self.wipe_btn.configure(state="normal", text="🗑️ START WIPE")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="100%")

        success = result.get('success', False)

        if success:
            self._set_status("✓ Знищено успішно", COLORS['accent_green'])
        else:
            self._set_status("✗ Знищення неповне", COLORS['accent_red'])

        # Показуємо статистику залежно від режиму
        if mode == "file":
            if success:
                self.size_label.configure(
                    text=f"✓ Знищено: {self._format_size(result.get('file_size', 0))}"
                )
            else:
                self.size_label.configure(text="✗ Знищення неповне")

        elif mode == "folder":
            wiped = result.get('wiped_files', 0)
            total = result.get('total_files', 0)
            size = self._format_size(result.get('total_size', 0))
            self.size_label.configure(text=f"Знищено: {wiped}/{total} файлів · {size}")

        elif mode == "disk":
            filled_gb = result.get('total_space_filled', 0) / (1024 ** 3)
            self.size_label.configure(text=f"Заповнено: {filled_gb:.2f} GB")

        # Показуємо модальний діалог з результатами
        self._show_result_dialog(result, mode, duration)

    def _show_result_dialog(self, result: dict, mode: str, duration: float):
        """Показати модальний діалог з результатом"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Результат операції")
        dialog.geometry("580x520")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS['bg_main'])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (580 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (520 // 2)
        dialog.geometry(f"580x520+{x}+{y}")

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(3, weight=1)

        success = result.get('success', False)

        if success:
            icon_text = "✓"
            title_text = "ОПЕРАЦІЮ ЗАВЕРШЕНО УСПІШНО"
            bg_color = COLORS['accent_green']
        else:
            icon_text = "✗"
            title_text = "УВАГА: ЗНИЩЕННЯ НЕПОВНЕ"
            bg_color = COLORS['accent_red']

        # Іконка
        icon_label = ctk.CTkLabel(
            dialog, text=icon_text,
            font=ctk.CTkFont(size=64), text_color=bg_color
        )
        icon_label.grid(row=0, column=0, pady=(30, 10))

        # Заголовок
        title_label = ctk.CTkLabel(
            dialog, text=title_text,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=bg_color
        )
        title_label.grid(row=1, column=0, pady=(0, 10))

        # Стандарт
        std_label = ctk.CTkLabel(
            dialog,
            text=f"Стандарт: {result.get('standard', WipeEngine.STANDARD_VERSION)}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS['text_sub']
        )
        std_label.grid(row=2, column=0, pady=(0, 10))

        # Блок деталей
        details_frame = ctk.CTkFrame(dialog, fg_color=COLORS['bg_card'], corner_radius=12)
        details_frame.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="nsew")
        details_frame.grid_columnconfigure(0, weight=1)

        row = 0
        method_display = result.get('method', 'N/A')

        # === ФАЙЛ ===
        if mode == "file":
            details = [
                f"Метод: {method_display}",
                f"Файл: {self.target_path.get()}",
                f"Розмір: {self._format_size(result.get('file_size', 0))}",
                f"Час: {result.get('duration', duration):.2f} сек",
            ]

            # Специфічна інформація верифікації для кожного методу
            msg = result.get('message', '')
            if msg:
                details.append(f"Перевірка: {msg}")
            elif 'percent' in result:
                pct = result.get('percent', 0)
                passed = result.get('passed_sectors', 0)
                total_s = result.get('checked_sectors', 0)
                method_name = result.get('method', '')

                if 'NIST Clear' in method_name:
                    details.append(
                        f"Секторів з псевдовипадковими даними: {passed}/{total_s} ({pct:.2f}%) ✓"
                        if success else
                        f"Секторів з низькою ентропією: {result.get('failed_sectors', 0)}/{total_s}"
                    )
                elif 'NIST Purge' in method_name:
                    details.append(
                        f"Чистих секторів: {passed}/{total_s} ({pct:.2f}%) ✓"
                        if success else
                        f"Ненульових секторів: {result.get('failed_sectors', 0)}/{total_s}"
                    )
                elif 'Zeros' in method_name:
                    details.append(
                        f"Нульових секторів: {passed}/{total_s} ({pct:.2f}%) ✓"
                        if success else
                        f"Ненульових секторів: {result.get('failed_sectors', 0)}/{total_s}"
                    )

            if 'bitlocker_status' in result:
                details.append(f"BitLocker: {result.get('bitlocker_status', 'N/A')}")

        # === ПАПКА ===
        elif mode == "folder":
            details = [
                f"Метод: {method_display}",
                f"Папка: {self.target_path.get()}",
                f"Знищено файлів: {result.get('wiped_files', 0)} з {result.get('total_files', 0)}",
                f"Загальний розмір: {self._format_size(result.get('total_size', 0))}",
                f"Час: {result.get('duration', duration):.2f} сек"
            ]

        # === ДИСК ===
        elif mode == "disk":
            filled_gb = result.get('total_space_filled', 0) / (1024 ** 3)
            details = [
                f"Метод: {method_display}",
                f"Диск: {self.selected_drive.get()}",
                f"Заповнено: {filled_gb:.2f} GB",
                f"Створено файлів: {result.get('temp_files_created', 0)}",
                f"Час: {result.get('duration', duration):.2f} сек"
            ]

        for detail in details:
            label = ctk.CTkLabel(
                details_frame, text=detail,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLORS['text_main'], anchor="w"
            )
            label.grid(row=row, column=0, padx=20, pady=(12 if row == 0 else 6, 6), sticky="ew")
            row += 1

        # Кнопки: для успішних операцій додаємо генерацію сертифіката
        if success and mode in ("file", "folder", "disk"):
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.grid(row=4, column=0, padx=30, pady=(0, 25))

            cert_btn = ctk.CTkButton(
                btn_frame, text="📄 Згенерувати сертифікат",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                height=40, corner_radius=8,
                fg_color=COLORS['accent_blue'], hover_color=COLORS['accent_blue'],
                command=lambda: self._generate_certificate_dialog(dialog)
            )
            cert_btn.pack(side="left", padx=(0, 10))

            close_btn = ctk.CTkButton(
                btn_frame, text="OK",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                height=40, width=100, corner_radius=8,
                fg_color=bg_color, hover_color=bg_color,
                command=dialog.destroy
            )
            close_btn.pack(side="left")
            # Не закриваємо автоматично, щоб користувач устиг згенерувати сертифікат
        else:
            close_btn = ctk.CTkButton(
                dialog, text="OK",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                height=40, corner_radius=8,
                fg_color=bg_color, hover_color=bg_color,
                command=dialog.destroy
            )
            close_btn.grid(row=4, column=0, padx=30, pady=(0, 25))
            dialog.after(15000, dialog.destroy)

    def _generate_certificate_dialog(self, parent_dialog=None):
        """Згенерувати PDF-сертифікат знищення для останньої операції."""
        cert_data = getattr(self, "_last_cert_data", None)
        if not cert_data:
            messagebox.showwarning(
                "Сертифікат",
                "Немає даних останньої операції для формування сертифіката."
            )
            return

        default_name = datetime.now().strftime("certificate_%Y%m%d_%H%M%S.pdf")
        path = filedialog.asksaveasfilename(
            title="Зберегти сертифікат знищення",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF документ", "*.pdf")]
        )
        if not path:
            return

        try:
            from certificate_generator import generate_certificate
        except ImportError:
            messagebox.showerror(
                "Сертифікат",
                "Не знайдено модуль certificate_generator.py або бібліотеку reportlab.\n"
                "Встановіть reportlab командою: pip install reportlab"
            )
            return

        res = generate_certificate(cert_data, path)
        if res.get("success"):
            messagebox.showinfo(
                "Сертифікат",
                f"Сертифікат успішно збережено:\n{res['path']}\n\n"
                "Поля виробника, моделі, оператора та верифікатора залишені "
                "для заповнення вручну перед підписанням."
            )
        else:
            messagebox.showerror(
                "Сертифікат",
                f"Не вдалося створити сертифікат:\n{res.get('error', 'невідома помилка')}"
            )

    def _operation_error(self, error_msg: str):
        """Помилка операції"""
        self.wipe_btn.configure(state="normal", text="🗑️ START WIPE")
        self._set_status("Помилка", COLORS['accent_red'])
        messagebox.showerror("Помилка", error_msg)

    def _clean_artifacts(self):
        """Очищення артефактів Windows"""
        confirm = messagebox.askyesno(
            "Очищення слідів",
            "Очистити артефакти Windows?\n\n"
            "Це видалить:\n"
            "• Кошик (Recycle Bin)\n"
            "• Prefetch файли\n"
            "• Recent files\n"
            "• Thumbnail cache\n"
            "• Тіньові копії VSS (потрібні права адміна)\n\n"
            "Продовжити?",
            icon='warning'
        )

        if not confirm:
            return

        def worker():
            try:
                self._set_status("Очищення слідів Windows...", COLORS['accent_blue'])
                print("\n[АРТЕФАКТИ] Очищення...\n")

                engine = WipeEngine()
                result = engine.clean_windows_artifacts()

                self.after(0, lambda: self._artifacts_complete(result))

            except Exception as e:
                print(f"\nПОМИЛКА: {e}\n")
                self.after(0, lambda: self._set_status("Помилка", COLORS['accent_red']))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _artifacts_complete(self, result: dict):
        """Завершення очищення артефактів"""
        if result.get('success'):
            self._set_status("Артефакти очищено ✓", COLORS['accent_green'])
            messagebox.showinfo("Успіх", "Артефакти Windows очищено!")
        else:
            self._set_status("Помилка очищення", COLORS['accent_red'])
            messagebox.showwarning(
                "Увага",
                "Деякі операції не виконані.\n"
                "Можливо, потрібні права адміністратора."
            )

    def _set_status(self, text: str, color: str):
        """Оновлення статусу"""
        self.status_label.configure(text=f"Статус: {text}", text_color=color)


def main():
    """Головна функція"""
    app = SecureWipePro()
    app.mainloop()


if __name__ == "__main__":
    main()