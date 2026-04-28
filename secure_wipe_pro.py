#!/usr/bin/env python3
"""
SecureWipe Pro v1.0
Сучасний інструмент безпечного знищення даних
Для демонстрації БКР на тему «Безпечне виведення з експлуатації технічних засобів»
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

# Try to import CustomTkinter
try:
    import customtkinter as ctk
    from customtkinter import CTk, CTkFrame, CTkLabel, CTkButton, CTkRadioButton
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
        self.geometry("900x650")
        self.minsize(900, 650)
        self.configure(fg_color=COLORS['bg_main'])
        
        # Змінні стану
        self.selected_method = tk.StringVar(value="dod")
        self.target_path = tk.StringVar()
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
        main_container.grid_columnconfigure(1, weight=1)
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
            ("zeros", "🔵 Zeros (1 pass)", "Перезаписування нулями"),
            ("dod", "🟡 DoD 3-pass", "Стандарт Міноборони США"),
            ("gutmann", "🟢 Gutmann (7 passes)", "Спрощена схема Гутмана"),
            ("verify", "🟣 Verify only", "Перевірка чистоти носія")
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
        
        # Заповнювач
        spacer = ctk.CTkFrame(parent, fg_color="transparent")
        spacer.grid(row=5, column=0, sticky="ew")
    
    def _create_status_panel(self, parent):
        """Панель статусу"""
        parent.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        label = ctk.CTkLabel(
            parent,
            text="ПАНЕЛЬ СТАТУСУ",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS['text_sub']
        )
        label.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")
        
        # Ціль
        target_frame = ctk.CTkFrame(parent, fg_color="transparent")
        target_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        target_frame.grid_columnconfigure(0, weight=1)
        
        target_label = ctk.CTkLabel(
            target_frame,
            text="Ціль:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS['text_sub']
        )
        target_label.grid(row=0, column=0, sticky="w")
        
        self.target_entry = ctk.CTkEntry(
            target_frame,
            textvariable=self.target_path,
            placeholder_text="Перетягніть файл або натисніть 📁",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=35
        )
        self.target_entry.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        browse_btn = ctk.CTkButton(
            target_frame,
            text="📁",
            width=35,
            height=35,
            corner_radius=8,
            fg_color=COLORS['bg_card'],
            hover_color=COLORS['accent_blue'],
            command=self._browse_file
        )
        browse_btn.grid(row=1, column=1, padx=(5, 0))
        
        # Інформація про файл
        self.info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.info_frame.grid(row=2, column=0, padx=20, pady=(10, 10), sticky="ew")
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
        progress_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
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
        self.details_label.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="w")
    
    def _create_action_buttons(self, parent):
        """Кнопки дій"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        
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
        self.wipe_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")
    
    def _setup_drag_drop(self):
        """Налаштування drag & drop"""
        self.target_entry.bind("<ButtonRelease-1>", lambda e: self._browse_file())
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
    
    def _browse_file(self):
        """Вибір файлу через діалог"""
        filename = filedialog.askopenfilename(
            title="Виберіть файл для знищення",
            filetypes=[("Всі файли", "*.*")]
        )
        if filename:
            self.target_path.set(filename)
            self._update_file_info()
    
    def _update_file_info(self):
        """Оновлення інформації про файл"""
        target = self.target_path.get()
        if target and os.path.exists(target):
            size = os.path.getsize(target)
            size_str = self._format_size(size)
            self.size_label.configure(text=f"Розмір: {size_str}")
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
        target = self.target_path.get()
        
        if not target:
            messagebox.showwarning("Увага", "Виберіть ціль для знищення!")
            return
        
        if not os.path.exists(target):
            messagebox.showerror("Помилка", f"Шлях не існує:\n{target}")
            return
        
        if not os.path.isfile(target):
            messagebox.showerror("Помилка", "Це не файл!")
            return
        
        method = self.selected_method.get()
        
        # Підтвердження
        method_names = {
            "zeros": "Zeros (1 pass)",
            "dod": "DoD 5220.22-M (3 passes)",
            "gutmann": "Gutmann (7 passes)",
            "verify": "Verify only"
        }
        
        confirm = messagebox.askyesno(
            "Підтвердження",
            f"УВАГА: ДАНІ БУДУТЬ ЗНИЩЕНІ БЕЗПОВОРОТНО!\n\n"
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
                
                if method == "verify":
                    result = self.engine.verify_wipe(target)
                    WipeEngine.save_log("Verify only", target, result)
                else:
                    # Виконуємо знищення
                    if method == "zeros":
                        result = self.engine.wipe_zeros(target)
                    elif method == "dod":
                        result = self.engine.wipe_dod(target)
                    elif method == "gutmann":
                        result = self.engine.wipe_gutmann(target)
                    
                    # Верифікація
                    print("\n[ВЕРИФІКАЦІЯ] Перевірка результату...\n")
                    verify_result = self.engine.verify_wipe(target)
                    
                    # Логування
                    WipeEngine.save_log(method_names[method], target, verify_result)
                    
                    result = verify_result
                
                # Завершення
                duration = time.time() - start_time
                
                self.after(0, lambda: self._operation_complete(result))
                
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
            
            speed = self._format_size(bytes_done / max(1, time.time() - start_time)) + "/s"
            self.details_label.configure(
                text=f"Pass {current_pass}/{total_passes} | {description} | {speed}"
            )
        
        start_time = time.time()
        self.after(0, update)
    
    def _operation_complete(self, result: dict):
        """Завершення операції"""
        self.wipe_btn.configure(state="normal", text="🗑️ START WIPE")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="100%")
        
        if result.get('success'):
            self._set_status("Знищення завершено успішно ✓", COLORS['accent_green'])
            messagebox.showinfo("Успіх", "Операцію завершено успішно!")
        else:
            self._set_status("Помилка або неповне знищення", COLORS['accent_red'])
            messagebox.showwarning("Увага", "Верифікація виявила проблеми!")
    
    def _operation_error(self, error_msg: str):
        """Помилка операції"""
        self.wipe_btn.configure(state="normal", text="🗑️ START WIPE")
        self._set_status("Помилка", COLORS['accent_red'])
        messagebox.showerror("Помилка", error_msg)
    
    def _set_status(self, text: str, color: str):
        """Оновлення статусу"""
        self.status_label.configure(text=f"Статус: {text}", text_color=color)


def main():
    """Головна функція"""
    app = SecureWipePro()
    app.mainloop()


if __name__ == "__main__":
    main()
