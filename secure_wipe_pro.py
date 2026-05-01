#!/usr/bin/env python3
"""
SecureWipe Pro v1.0
Сучасний інструмент безпечного знищення даних
Для демонстрації БКР на тему «Безпечне виведення з експлуатації технічних засобів»

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
    from customtkinter import CTk, CTkFrame, CTkLabel, CTkButton, CTkRadioButton, CTkSegmentedButton, CTkComboBox
    CTK_AVAILABLE = True
except ImportError:
    print("ПОМИЛКА: CustomTkinter не встановлено!")
    print("Встановіть: pip install customtkinter")
    sys.exit(1)

# Імпортуємо wipe engine
try:
    from wipe_engine import WipeEngine
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
    'accent_green': '#30D158',
    'text_main': '#FFFFFF',
    'text_sub': '#8E8E93'
}

# Налаштування CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SplashScreen(ctk.CTkToplevel):
    """Splash screen при запуску програми"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("")
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_main'])
        
        # Видаляємо рамку вікна
        self.overrideredirect(True)
        
        # Центрування на екрані
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f"400x300+{x}+{y}")
        
        # Контент
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_main'], corner_radius=12)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Логотип (Unicode)
        logo_label = ctk.CTkLabel(
            main_frame,
            text="🔒",
            font=ctk.CTkFont(size=64)
        )
        logo_label.grid(row=0, column=0, pady=(40, 20))
        
        # Назва
        title_label = ctk.CTkLabel(
            main_frame,
            text="SecureWipe Pro",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=COLORS['text_main']
        )
        title_label.grid(row=1, column=0, pady=(0, 10))
        
        # Версія
        version_label = ctk.CTkLabel(
            main_frame,
            text="v1.0.0",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS['text_sub']
        )
        version_label.grid(row=2, column=0, pady=(0, 20))
        
        # Прогрес-бар
        self.progress = ctk.CTkProgressBar(
            main_frame,
            mode="indeterminate",
            progress_color=COLORS['accent_blue']
        )
        self.progress.grid(row=3, column=0, padx=40, sticky="ew")
        self.progress.start()
        
        # Статус
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ініціалізація...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub']
        )
        self.status_label.grid(row=4, column=0, pady=(10, 40))
    
    def update_status(self, text: str):
        """Оновлення статусу"""
        self.status_label.configure(text=text)
        self.update_idletasks()
    
    def close(self):
        """Закриття splash screen"""
        self.progress.stop()
        self.destroy()


class TerminalWidget(ctk.CTkTextbox):
    """Термінальний віджет для виводу логів"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS['bg_terminal'],
            text_color="#00FF00",
            font=ctk.CTkFont(family="Consolas", size=12),
            **kwargs
        )
        self.configure(wrap="word")
    
    def write(self, text: str):
        """Запис тексту (як для stdout)"""
        self.insert("end", text)
        self.see("end")
        self.update_idletasks()
    
    def flush(self):
        """Flush method for stdout compatibility"""
        pass


class SecureWipePro(ctk.CTk):
    """Головне вікно SecureWipe Pro"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🔒 SecureWipe Pro")
        self.geometry("960x650")
        self.minsize(960, 650)
        self.configure(fg_color=COLORS['bg_main'])
        
        # Змінні стану
        self.selected_method = tk.StringVar(value="dod")
        self.operation_mode = tk.StringVar(value="file")
        self.target_path = tk.StringVar()
        self.selected_drive = tk.StringVar()
        self.engine = None
        self.operation_thread = None
        self.current_operation = None
        
        # Налаштування сітки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Створення інтерфейсу
        self._create_widgets()
        self._setup_drag_drop()
        
        # Показуємо splash screen
        self.withdraw()
        self.splash = SplashScreen(self)
        self.after(2000, self._close_splash)
    
    def _close_splash(self):
        """Закриття splash screen після затримки"""
        self.splash.close()
        self.deiconify()
        self.lift()
        self.focus_force()
    
    def _create_widgets(self):
        """Створення всіх віджетів інтерфейсу"""
        
        # Головний контейнер
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=2)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Заголовок
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔒 SecureWipe Pro",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS['text_main']
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Перемикач теми (заготовка)
        theme_btn = ctk.CTkButton(
            header_frame,
            text="☀️",
            width=40,
            height=40,
            corner_radius=20,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['accent_blue']
        )
        theme_btn.grid(row=0, column=1, sticky="e")
        
        # Ліва панель - Методи
        left_panel = ctk.CTkFrame(
            main_container,
            fg_color=COLORS['bg_card'],
            corner_radius=12
        )
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_columnconfigure(0, weight=1)
        
        self._create_method_panel(left_panel)
        
        # Права панель - Статус
        right_panel = ctk.CTkFrame(
            main_container,
            fg_color=COLORS['bg_card'],
            corner_radius=12
        )
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(2, weight=1)
        
        self._create_status_panel(right_panel)
        
        # Нижня панель - Кнопки дій
        bottom_panel = ctk.CTkFrame(main_container, fg_color="transparent")
        bottom_panel.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        bottom_panel.grid_columnconfigure(0, weight=1)
        bottom_panel.grid_columnconfigure(1, weight=1)
        bottom_panel.grid_columnconfigure(2, weight=1)
        
        self._create_action_buttons(bottom_panel)
        
        # Термінал логів
        terminal_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        terminal_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(20, 0))
        terminal_frame.grid_columnconfigure(0, weight=1)
        terminal_frame.grid_rowconfigure(1, weight=1)
        
        terminal_label = ctk.CTkLabel(
            terminal_frame,
            text="📋 ЛОГ ОПЕРАЦІЙ",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS['text_sub']
        )
        terminal_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.terminal = TerminalWidget(terminal_frame, height=150)
        self.terminal.grid(row=1, column=0, sticky="nsew")
        
        # Перенаправлення stdout
        sys.stdout = self.terminal
        
        # Початкове повідомлення
        print("=== SecureWipe Pro v1.0 ===")
        print("Готовий до роботи.\n")
    
    def _create_method_panel(self, parent):
        """Панель вибору методу"""
        parent.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        label = ctk.CTkLabel(
            parent,
            text="МЕТОДИ ЗНИЩЕННЯ",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS['text_sub']
        )
        label.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")
        
        # Методи
        methods = [
            ("zeros", "Zeros (1 pass)", "Перезаписування нулями"),
            ("dod", "DoD 3-pass", "Стандарт Міноборони США"),
            ("gutmann", "Gutmann (7 passes)", "Спрощена схема Гутмана"),
            ("verify", "Verify only", "Перевірка чистоти носія")
        ]
        
        self.method_radios = []
        for i, (value, text, desc) in enumerate(methods):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.grid(row=i+1, column=0, padx=20, pady=(0, 10), sticky="ew")
            frame.grid_columnconfigure(0, weight=1)
            
            radio = ctk.CTkRadioButton(
                frame,
                text=text,
                variable=self.selected_method,
                value=value,
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=COLORS['text_main'],
                fg_color=COLORS['accent_blue'],
                hover_color=COLORS['accent_blue']
            )
            radio.grid(row=0, column=0, sticky="w")
            
            desc_label = ctk.CTkLabel(
                frame,
                text=desc,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLORS['text_sub']
            )
            desc_label.grid(row=1, column=0, sticky="w", padx=(25, 0))
            
            self.method_radios.append(radio)
    
    def _create_status_panel(self, parent):
        """Панель статусу"""
        parent.grid_columnconfigure(0, weight=1)
        
        # Mode switcher at the top of status panel
        self.mode_segmented = ctk.CTkSegmentedButton(
            parent,
            values=["File", "Folder", "Disk"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color=COLORS['bg_main'],
            selected_color=COLORS['accent_blue'],
            unselected_color=COLORS['bg_card'],
            text_color=COLORS['text_main'],
            unselected_hover_color=COLORS['accent_blue'],
            command=self._on_segmented_mode_change
        )
        self.mode_segmented.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.mode_segmented.set("File")  # Default
        
        # Description label
        self.mode_desc_label = ctk.CTkLabel(
            parent,
            text="Знищити один файл обраним методом",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_sub']
        )
        self.mode_desc_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Separator
        separator = ctk.CTkFrame(parent, height=2, fg_color=COLORS['text_sub'])
        separator.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Заголовок
        label = ctk.CTkLabel(
            parent,
            text="ПАНЕЛЬ СТАТУСУ",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS['text_sub']
        )
        label.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Ціль або Диск
        target_frame = ctk.CTkFrame(parent, fg_color="transparent")
        target_frame.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        target_frame.grid_columnconfigure(0, weight=1)
        
        self.target_label = ctk.CTkLabel(
            target_frame,
            text="Ціль:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub']
        )
        self.target_label.grid(row=0, column=0, sticky="w")
        
        self.target_entry = ctk.CTkEntry(
            target_frame,
            textvariable=self.target_path,
            placeholder_text="Перетягніть файл або натисніть 📁",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=35
        )
        self.target_entry.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        self.browse_btn = ctk.CTkButton(
            target_frame,
            text="📁",
            width=35,
            height=35,
            corner_radius=8,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['accent_blue'],
            command=self._browse_file
        )
        self.browse_btn.grid(row=1, column=1, padx=(5, 0))
        
        # Диски (спочатку приховано)
        self.disk_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.disk_frame.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.disk_frame.grid_columnconfigure(0, weight=1)
        
        disk_label = ctk.CTkLabel(
            self.disk_frame,
            text="Виберіть диск для очищення:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub']
        )
        disk_label.grid(row=0, column=0, sticky="w")
        
        # Отримуємо список дисків
        drives = WipeEngine.get_available_drives()
        if not drives:
            drives = ["C:\\", "D:\\", "E:\\"]
        
        # Add option to enter custom path
        drives_with_custom = drives + ["Інший диск..."]
        
        self.disk_combo = ctk.CTkComboBox(
            self.disk_frame,
            values=drives_with_custom,
            variable=self.selected_drive,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=35,
            command=self._on_disk_selected
        )
        self.disk_combo.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        if drives:
            self.disk_combo.set(drives[0])
            self.selected_drive.set(drives[0])
        
        self.disk_frame.grid_remove()  # Приховуємо
        
        # Інформація про файл/папку
        self.info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.info_frame.grid(row=6, column=0, padx=20, pady=(10, 10), sticky="ew")
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        self.size_label = ctk.CTkLabel(
            self.info_frame,
            text="Розмір: --",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_main']
        )
        self.size_label.grid(row=0, column=0, sticky="w")
        
        self.status_label = ctk.CTkLabel(
            self.info_frame,
            text="Статус: Готовий",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['accent_green']
        )
        self.status_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Прогрес
        progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
        progress_frame.grid(row=7, column=0, padx=20, pady=(10, 20), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            mode="determinate",
            progress_color=COLORS['accent_blue'],
            height=20,
            corner_radius=10
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_sub']
        )
        self.progress_label.grid(row=1, column=0, pady=(5, 0))
        
        # Деталі операції
        self.details_label = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text_sub']
        )
        self.details_label.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="w")
    
    def _create_action_buttons(self, parent):
        """Кнопки дій"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_columnconfigure(2, weight=1)
        
        # Кнопка Test Mode
        test_btn = ctk.CTkButton(
            parent,
            text="🧪 TEST MODE",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color=COLORS['accent_blue'],
            hover_color='#1E90FF',
            command=self._test_mode
        )
        test_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # Кнопка Start Wipe
        self.wipe_btn = ctk.CTkButton(
            parent,
            text="🗑️ START WIPE",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color=COLORS['accent_red'],
            hover_color=COLORS['accent_red_hover'],
            command=self._start_wipe
        )
        self.wipe_btn.grid(row=0, column=1, padx=(10, 10), sticky="ew")
        
        # Кнопка Clean Artifacts (Windows only)
        if os.name == 'nt':
            clean_btn = ctk.CTkButton(
                parent,
                text="🧹 Очистити сліди",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                height=50,
                corner_radius=12,
                fg_color=COLORS['bg_card'],
                hover_color=COLORS['accent_blue'],
                command=self._clean_artifacts
            )
            clean_btn.grid(row=0, column=2, padx=(10, 0), sticky="ew")
    
    def _on_segmented_mode_change(self, mode_text):
        """Обробка зміни режиму через segmented button"""
        # Map text to mode value
        mode_map = {
            "File": "file",
            "Folder": "folder",
            "Disk": "disk"
        }
        mode = mode_map.get(mode_text, "file")
        self.operation_mode.set(mode)
        
        # Update description
        desc_map = {
            "file": "Знищити один файл обраним методом",
            "folder": "Рекурсивно знищити всі файли в папці",
            "disk": "Заповнити вільний простір диска"
        }
        self.mode_desc_label.configure(text=desc_map.get(mode, ""))
        
        if mode == "file":
            self.target_label.configure(text="Ціль:")
            self.target_entry.configure(placeholder_text="Перетягніть файл або натисніть 📁")
            self.browse_btn.configure(command=self._browse_file)
            self.disk_frame.grid_remove()
            self.target_entry.grid(row=1, column=0, sticky="ew", pady=(5, 0))
            self.browse_btn.grid(row=1, column=1, padx=(5, 0))
            
        elif mode == "folder":
            self.target_label.configure(text="Папка:")
            self.target_entry.configure(placeholder_text="Виберіть папку або натисніть 📁")
            self.browse_btn.configure(command=self._browse_folder)
            self.disk_frame.grid_remove()
            self.target_entry.grid(row=1, column=0, sticky="ew", pady=(5, 0))
            self.browse_btn.grid(row=1, column=1, padx=(5, 0))
            
        elif mode == "disk":
            self.target_label.configure(text="Диск:")
            self.target_entry.grid_remove()
            self.browse_btn.grid_remove()
            self.disk_frame.grid()
            # Show disk info
            self._update_disk_info()
            
        self.target_path.set("")
        self._update_file_info()
    
    def _on_disk_selected(self, choice):
        """Handle disk selection from combo box"""
        if choice == "Інший диск...":
            # Ask user to enter custom disk path
            custom_path = simpledialog.askstring(
                "Вибір диска",
                "Введіть шлях до диска (наприклад, E:\\):",
                parent=self
            )
            if custom_path:
                # Normalize path
                if not custom_path.endswith('\\'):
                    custom_path = custom_path.rstrip('\\') + '\\'
                
                # Add to combo box if not already there
                current_values = list(self.disk_combo.cget("values"))
                if custom_path not in current_values:
                    current_values.insert(-1, custom_path)
                    self.disk_combo.configure(values=current_values)
                self.disk_combo.set(custom_path)
                self.selected_drive.set(custom_path)
                
                # Show free space
                self._update_disk_info(custom_path)
            else:
                # Reset to first drive
                drives = WipeEngine.get_available_drives()
                if drives:
                    self.disk_combo.set(drives[0])
                    self.selected_drive.set(drives[0])
        else:
            self.selected_drive.set(choice)
            self._update_disk_info(choice)
    
    def _update_disk_info(self, drive_path=None):
        """Update disk free space info"""
        if drive_path is None:
            drive_path = self.selected_drive.get()
        
        if drive_path and os.path.exists(drive_path):
            try:
                import shutil
                total, used, free = shutil.disk_usage(drive_path)
                free_gb = free / (1024**3)
                total_gb = total / (1024**3)
                self.size_label.configure(text=f"Вільно: {free_gb:.2f} GB з {total_gb:.2f} GB")
                self.status_label.configure(text=f"Диск {drive_path} готовий до очищення")
            except Exception as e:
                self.size_label.configure(text="Помилка читання диска")
                self.status_label.configure(text="Помилка")
        else:
            self.size_label.configure(text="Диск не знайдено")
            self.status_label.configure(text="Помилка")
    
    def _setup_drag_drop(self):
        """Налаштування drag & drop"""
        self.target_entry.bind("<ButtonRelease-1>", lambda e: self._browse_target())
        # Простий drag & drop через вставку з буфера
        self.target_entry.bind("<Button-3>", self._paste_from_clipboard)
    
    def _paste_from_clipboard(self, event):
        """Вставка шляху з буфера обміну"""
        try:
            clipboard = self.clipboard_get()
            if os.path.exists(clipboard):
                self.target_path.set(clipboard)
                self._update_file_info()
        except:
            pass
    
    def _browse_target(self):
        """Вибір цілі залежно від режиму"""
        mode = self.operation_mode.get()
        if mode == "file":
            self._browse_file()
        elif mode == "folder":
            self._browse_folder()
        # For disk mode, do nothing (use combo box)
    
    def _browse_file(self):
        """Вибір файлу через діалог"""
        filename = filedialog.askopenfilename(
            title="Виберіть файл для знищення",
            filetypes=[("Всі файли", "*.*")]
        )
        if filename:
            self.target_path.set(filename)
            self._update_file_info()
    
    def _browse_folder(self):
        """Вибір папки через діалог"""
        folder = filedialog.askdirectory(
            title="Виберіть папку для знищення"
        )
        if folder:
            self.target_path.set(folder)
            self._update_file_info()
    
    def _count_files_in_folder(self, folder_path):
        """Count files in folder recursively"""
        count = 0
        total_size = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    count += 1
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        return count, total_size
    
    def _update_file_info(self):
        """Оновлення інформації про файл/папку"""
        target = self.target_path.get()
        mode = self.operation_mode.get()
        
        if mode == "disk":
            return
            
        if target and os.path.exists(target):
            if mode == "file" and os.path.isfile(target):
                size = os.path.getsize(target)
                size_str = self._format_size(size)
                self.size_label.configure(text=f"Розмір: {size_str}")
            elif mode == "folder" and os.path.isdir(target):
                # Count files in folder
                file_count, total_size = self._count_files_in_folder(target)
                size_str = self._format_size(total_size)
                self.size_label.configure(text=f"Знайдено: {file_count} файлів, {size_str}")
            else:
                self.size_label.configure(text="Розмір: --")
        else:
            self.size_label.configure(text="Розмір: --")
    
    def _format_size(self, size_bytes: int) -> str:
        """Форматування розміру"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _test_mode(self):
        """Тестовий режим"""
        def worker():
            try:
                self._set_status("Створення тестового файлу...", COLORS['accent_blue'])
                print("\n[ТЕСТОВИЙ РЕЖИМ] Створення тестового файлу...")
                
                engine = WipeEngine()
                test_file = engine.create_test_file("test_data.bin", size_mb=10)
                
                self.target_path.set(test_file)
                self.operation_mode.set("file")
                self._on_segmented_mode_change("File")
                self._update_file_info()
                
                print(f"✓ Тестовий файл створено: {test_file}\n")
                self._set_status("Тестовий файл створено", COLORS['accent_green'])
                
                messagebox.showinfo("Успіх", f"Тестовий файл створено:\n{test_file}")
                
            except Exception as e:
                print(f"ПОМИЛКА: {e}\n")
                self._set_status("Помилка", COLORS['accent_red'])
                messagebox.showerror("Помилка", str(e))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _start_wipe(self):
        """Запуск знищення"""
        mode = self.operation_mode.get()
        method = self.selected_method.get()
        
        # Визначення цілі
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
        
        # Підтвердження
        method_names = {
            "zeros": "Zeros (1 pass)",
            "dod": "DoD 5220.22-M (3 passes)",
            "gutmann": "Gutmann (7 passes)",
            "verify": "Verify only"
        }
        
        mode_names = {
            "file": "Файл",
            "folder": "Папка",
            "disk": "Диск"
        }
        
        confirm = messagebox.askyesno(
            "Підтвердження",
            f"УВАГА: ДАНІ БУДУТЬ ЗНИЩЕНІ БЕЗПОВОРОТНО!\n\n"
            f"Режим: {mode_names[mode]}\n"
            f"Ціль: {target}\n"
            f"Метод: {method_names[method]}\n\n"
            f"Продовжити?",
            icon='warning'
        )
        
        if not confirm:
            return
        
        # Запуск у окремому потоці
        self.wipe_btn.configure(state="disabled", text="⏳ ВИКОНУЄТЬСЯ...")
        self._set_status("Виконання...", COLORS['accent_blue'])
        
        def worker():
            try:
                self.engine = WipeEngine(
                    progress_callback=self._progress_callback
                )
                
                start_time = time.time()
                result = None
                
                if mode == "file":
                    # Режим 1: Один файл
                    method_display = method_names[method]
                    if method == "verify":
                        result = self.engine.verify_wipe(target, method_display)
                        WipeEngine.save_log("Verify only", target, result)
                    else:
                        file_size = os.path.getsize(target) if os.path.exists(target) else 0
                        
                        if method == "zeros":
                            result = self.engine.wipe_zeros(target)
                        elif method == "dod":
                            result = self.engine.wipe_dod(target)
                        elif method == "gutmann":
                            result = self.engine.wipe_gutmann(target)
                        
                        # Верифікація
                        print("\n[ВЕРИФІКАЦІЯ] Перевірка результату...\n")
                        verify_result = self.engine.verify_wipe(target, method_display, file_size)
                        WipeEngine.save_log(method_display, target, verify_result)
                        result = verify_result
                        
                elif mode == "folder":
                    # Режим 2: Папка
                    result = self.engine.wipe_folder(target, method)
                    WipeEngine.save_log(f"Folder wipe - {method_names[method]}", 
                                        target, result)
                    
                elif mode == "disk":
                    # Режим 3: Диск
                    result = self.engine.wipe_free_space(target, method)
                    WipeEngine.save_log(f"Disk wipe - {method}", 
                                        target, result)
                
                # Завершення
                duration = time.time() - start_time
                
                self.after(0, lambda: self._operation_complete(result, mode))
                
            except Exception as e:
                print(f"\nПОМИЛКА: {e}\n")
                self.after(0, lambda: self._operation_error(str(e)))
        
        self.operation_thread = threading.Thread(target=worker, daemon=True)
        self.operation_thread.start()
    
    def _progress_callback(self, current_pass: int, total_passes: int,
                          description: str, progress: float,
                          bytes_done: int, total_bytes: int):
        """Callback для оновлення прогресу"""
        
        def update():
            self.progress_bar.set(progress / 100)
            self.progress_label.configure(text=f"{progress:.1f}%")
            
            mode = self.operation_mode.get()
            
            if mode == "disk":
                filled_gb = bytes_done / (1024**3)
                total_gb = total_bytes / (1024**3)
                speed = ""
                if hasattr(self, '_last_progress_time'):
                    elapsed = time.time() - self._last_progress_time
                    if elapsed > 0:
                        speed = f" | {filled_gb/elapsed:.1f} GB/s"
                self.details_label.configure(
                    text=f"Заповнено {filled_gb:.1f} GB з {total_gb:.1f} GB{speed}"
                )
                self._last_progress_time = time.time()
            else:
                speed = self._format_size(bytes_done / max(1, time.time() - start_time)) + "/s"
                self.details_label.configure(
                    text=f"Pass {current_pass}/{total_passes} | {description} | {speed}"
                )
        
        start_time = time.time()
        self.after(0, update)
    
    def _operation_complete(self, result: dict, mode: str):
        """Завершення операції"""
        self.wipe_btn.configure(state="normal", text="🗑️ START WIPE")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="100%")
        
        # Показуємо статистику
        if mode == "file":
            if result.get('success'):
                self.size_label.configure(text=f"Знищено: {self._format_size(result.get('file_size', 0))}")
                self._set_status("✓ Знищено успішно", COLORS['accent_green'])
            else:
                self._set_status("✗ Знищення неповне", COLORS['accent_red'])
                
        elif mode == "folder":
            wiped = result.get('wiped_files', 0)
            total = result.get('total_files', 0)
            size = self._format_size(result.get('total_size', 0))
            self.size_label.configure(text=f"Знищено: {wiped} файлів")
            self._set_status(f"✓ Оброблено {wiped} з {total} файлів", COLORS['accent_green'])
            
        elif mode == "disk":
            filled_gb = result.get('total_space_filled', 0) / (1024**3)
            files_created = result.get('temp_files_created', 0)
            self.size_label.configure(text=f"Заповнено: {filled_gb:.2f} GB")
            self._set_status(f"✓ Диск заповнено ({filled_gb:.2f} GB)", COLORS['accent_green'])
        
        # Show modal dialog with results
        self._show_result_dialog(result, mode)
    
    def _show_result_dialog(self, result: dict, mode: str):
        """Показати модальний діалог з результатом"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Результат операції")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS['bg_main'])
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (500 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        
        # Result icon and title
        success = result.get('success', False)
        
        if success:
            icon_text = "✓"
            title_text = "ОПЕРАЦІЮ ЗАВЕРШЕНО УСПІШНО"
            bg_color = COLORS['accent_green']
        else:
            icon_text = "✗"
            title_text = "УВАГА: ЗНИЩЕННЯ НЕПОВНЕ"
            bg_color = COLORS['accent_red']
        
        # Icon
        icon_label = ctk.CTkLabel(
            dialog,
            text=icon_text,
            font=ctk.CTkFont(size=64),
            text_color=bg_color
        )
        icon_label.grid(row=0, column=0, pady=(30, 10))
        
        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=title_text,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=bg_color
        )
        title_label.grid(row=1, column=0, pady=(0, 20))
        
        # Details frame
        details_frame = ctk.CTkFrame(dialog, fg_color=COLORS['bg_card'], corner_radius=12)
        details_frame.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="ew")
        details_frame.grid_columnconfigure(0, weight=1)
        
        # Add details based on mode
        row = 0
        
        if mode == "file":
            details = [
                f"Метод: {result.get('method_name', 'N/A')}",
                f"Файл: {self.target_path.get()}",
                f"Розмір: {self._format_size(result.get('file_size', 0))}",
                f"Час: {result.get('duration', 0):.2f} сек",
                f"Надійність: {result.get('clean_percent', 0):.2f}%"
            ]
        elif mode == "folder":
            details = [
                f"Знищено файлів: {result.get('wiped_files', 0)} з {result.get('total_files', 0)}",
                f"Загальний розмір: {self._format_size(result.get('total_size', 0))}",
                f"Час: {result.get('duration', 0):.2f} сек"
            ]
        elif mode == "disk":
            filled_gb = result.get('total_space_filled', 0) / (1024**3)
            details = [
                f"Заповнено: {filled_gb:.2f} GB",
                f"Створено файлів: {result.get('temp_files_created', 0)}",
                f"Час: {result.get('duration', 0):.2f} сек"
            ]
        
        for detail in details:
            label = ctk.CTkLabel(
                details_frame,
                text=detail,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLORS['text_main']
            )
            label.grid(row=row, column=0, padx=20, pady=(10 if row == 0 else 5), sticky="w")
            row += 1
        
        # Close button
        close_btn = ctk.CTkButton(
            dialog,
            text="OK",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color=bg_color,
            hover_color=bg_color,
            command=dialog.destroy
        )
        close_btn.grid(row=3, column=0, padx=30, pady=(0, 30))
        
        # Auto-close after 10 seconds
        dialog.after(10000, dialog.destroy)
    
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
            "• Тіньові копії (потрібні права адміна)\n\n"
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
            messagebox.showwarning("Увага", "Деякі операції не виконані.\nМожливо, потрібні права адміністратора.")
    
    def _set_status(self, text: str, color: str):
        """Оновлення статусу"""
        self.status_label.configure(text=f"Статус: {text}", text_color=color)


def main():
    """Головна функція"""
    app = SecureWipePro()
    app.mainloop()


if __name__ == "__main__":
    main()
