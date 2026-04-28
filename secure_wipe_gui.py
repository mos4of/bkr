#!/usr/bin/env python3
"""
Secure Wipe Tool v1.0 - GUI Version
Програма безпечного знищення даних з графічним інтерфейсом
Для демонстрації БКР на тему «Безпечне виведення з експлуатації технічних засобів»
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path

# Імпортуємо функції з основного модуля
try:
    from secure_wipe import (
    wipe_zeros, wipe_dod, wipe_gutmann, 
    verify_wipe, save_log, create_test_file, TQDM_AVAILABLE
)
except ImportError:
    messagebox.showerror("Помилка", "Не знайдено secure_wipe.py! Переконайтеся, що файл у тій же папці.")
    sys.exit(1)


class RedirectText:
    """Клас для перенаправлення виводу в текстовий віджет"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
    
    def write(self, string):
        self.buffer += string
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()
    
    def flush(self):
        pass


class SecureWipeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Wipe Tool v1.0 - GUI")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        self.current_operation = None
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', 
                       background='#2b2b2b', 
                       foreground='#ffffff',
                       font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel',
                       background='#2b2b2b',
                       foreground='#cccccc',
                       font=('Arial', 10))
        style.configure('Action.TButton',
                       font=('Arial', 10, 'bold'),
                       padding=10)
        
        # Головний контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, 
                               text="=== SECURE WIPE TOOL v1.0 ===",
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame,
                                  text="Безпечне знищення даних на носіях",
                                  style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Вибір методу
        method_frame = ttk.LabelFrame(main_frame, text="Метод знищення", padding="10")
        method_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.method_var = tk.StringVar(value="zeros")
        
        ttk.Radiobutton(method_frame, text="Zeros (1 pass)", 
                       variable=self.method_var, value="zeros").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Radiobutton(method_frame, text="DoD 5220.22-M (3 passes)",
                       variable=self.method_var, value="dod").grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(method_frame, text="Gutmann (7 passes)",
                       variable=self.method_var, value="gutmann").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(method_frame, text="Verify only",
                       variable=self.method_var, value="verify").grid(row=1, column=0, sticky=tk.W, padx=5)
        
        # Вибір цілі
        target_frame = ttk.LabelFrame(main_frame, text="Ціль", padding="10")
        target_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.target_var = tk.StringVar()
        ttk.Entry(target_frame, textvariable=self.target_var, width=60).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(target_frame, text="Огляд...", 
                  command=self.browse_file).grid(row=0, column=1, padx=5)
        ttk.Button(target_frame, text="Тестовий файл",
                  command=self.create_test_file).grid(row=0, column=2, padx=5)
        
        # Кнопки дій
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Button(button_frame, text="▶ Запустити знищення",
                  command=self.start_wipe, style='Action.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="📥 Завантажити з GitHub",
                  command=self.clone_from_github).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="ℹ️ Про програму",
                  command=self.show_about).grid(row=0, column=2, padx=5)
        
        # Прогрес-бар
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Консоль виводу
        output_frame = ttk.LabelFrame(main_frame, text="Вивід", padding="5")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.output_text = scrolledtext.ScrolledText(output_frame, 
                                                     height=20,
                                                     bg='#1e1e1e',
                                                     fg='#00ff00',
                                                     font=('Consolas', 9))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Налаштування grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Перенаправлення stdout
        self.redirect = RedirectText(self.output_text)
        sys.stdout = self.redirect
        
        # Початкове повідомлення
        print("=== SECURE WIPE TOOL v1.0 - GUI ===")
        print("Готовий до роботи.\n")
    
    def browse_file(self):
        """Вибір файлу через діалог"""
        filename = filedialog.askopenfilename(
            title="Виберіть файл для знищення",
            filetypes=[("Всі файли", "*.*")]
        )
        if filename:
            self.target_var.set(filename)
    
    def create_test_file(self):
        """Створення тестового файлу"""
        def worker():
            try:
                self.progress.start()
                test_file = create_test_file("test_data.bin", size_mb=10)
                self.target_var.set(test_file)
                messagebox.showinfo("Успіх", f"Тестовий файл створено:\n{test_file}")
            except Exception as e:
                messagebox.showerror("Помилка", str(e))
            finally:
                self.progress.stop()
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
    
    def start_wipe(self):
        """Запуск процесу знищення"""
        target = self.target_var.get()
        
        if not target:
            messagebox.showwarning("Увага", "Виберіть ціль для знищення!")
            return
        
        if not os.path.exists(target):
            messagebox.showerror("Помилка", f"Шлях не існує:\n{target}")
            return
        
        if not os.path.isfile(target):
            messagebox.showerror("Помилка", "Це не файл!")
            return
        
        method = self.method_var.get()
        
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
            f"Продовжити?"
        )
        
        if not confirm:
            return
        
        # Запуск у окремому потоці
        def worker():
            try:
                self.progress.start()
                self.output_text.delete(1.0, tk.END)
                
                start_time = time.time()
                
                if method == "zeros":
                    duration = wipe_zeros(target)
                elif method == "dod":
                    duration = wipe_dod(target)
                elif method == "gutmann":
                    duration = wipe_gutmann(target)
                elif method == "verify":
                    result = verify_wipe(target)
                    save_log("Verify only", target,
                            "SUCCESS" if result['success'] else "FAILED",
                            result['duration'])
                    return
                
                total_duration = time.time() - start_time
                
                # Верифікація
                result = verify_wipe(target)
                
                # Логування
                save_log(method_names[method], target,
                        "SUCCESS" if result['success'] else "FAILED",
                        total_duration)
                
                if result['success']:
                    messagebox.showinfo("Успіх", "Знищення завершено успішно!")
                else:
                    messagebox.showwarning("Увага", "Верифікація виявила проблеми!")
                    
            except Exception as e:
                messagebox.showerror("Помилка", str(e))
            finally:
                self.progress.stop()
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
    
    def clone_from_github(self):
        """Завантаження з GitHub репозиторію"""
        repo_url = "https://github.com/mos4of/bkr.git"
        
        confirm = messagebox.askyesno(
            "Завантаження з GitHub",
            f"Завантажити код з репозиторію?\n\n{repo_url}\n\n"
            f"Файли будуть збережені в поточну папку."
        )
        
        if not confirm:
            return
        
        def worker():
            try:
                self.progress.start()
                self.output_text.delete(1.0, tk.END)
                
                print(f"Завантаження з {repo_url}...\n")
                
                # Використовуємо git clone
                result = subprocess.run(
                    ["git", "clone", repo_url],
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                if result.returncode == 0:
                    print("✓ Репозиторій успішно завантажено!\n")
                    print(result.stdout)
                    messagebox.showinfo("Успіх", "Репозиторій завантажено успішно!")
                else:
                    # Можливо, папка вже існує
                    if "already exists" in result.stderr:
                        print("Папка bkr вже існує. Оновлюємо...\n")
                        subprocess.run(
                            ["git", "-C", "bkr", "pull"],
                            capture_output=True,
                            text=True
                        )
                        print("✓ Репозиторій оновлено!\n")
                    else:
                        print(f"Помилка: {result.stderr}\n")
                        messagebox.showerror("Помилка", result.stderr)
                        
            except FileNotFoundError:
                # Git не встановлено, пропонуємо завантажити zip
                print("Git не знайдено. Завантажуємо ZIP-архів...\n")
                self.download_zip()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))
            finally:
                self.progress.stop()
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
    
    def download_zip(self):
        """Завантаження ZIP-архіву з GitHub"""
        try:
            import urllib.request
            import zipfile
            
            zip_url = "https://github.com/mos4of/bkr/archive/refs/heads/master.zip"
            
            print("Завантаження архіву...\n")
            
            # Завантаження
            zip_path = "bkr-master.zip"
            urllib.request.urlretrieve(zip_url, zip_path)
            
            print("Розпакування...\n")
            
            # Розпакування
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            
            # Видалення архіву
            os.remove(zip_path)
            
            print("✓ Архів завантажено та розпаковано!\n")
            messagebox.showinfo("Успіх", "Архів завантажено та розпаковано!")
            
        except Exception as e:
            print(f"Помилка завантаження: {e}\n")
            messagebox.showerror("Помилка", str(e))
    
    def show_about(self):
        """Вікно з інформацією про програму"""
        about_text = """Secure Wipe Tool v1.0 - GUI Version

Програма безпечного знищення даних на носіях
для демонстрації БКР на тему 
«Безпечне виведення з експлуатації технічних засобів»

Методи знищення:
• Zeros (1 pass) - перезаписування нулями
• DoD 5220.22-M (3 passes) - стандарт Міністерства оборони США
• Gutmann (7 passes) - спрощена схема Гутмана
• Verify only - перевірка чистоти носія

Репозиторій: https://github.com/mos4of/bkr

Розроблено для БКР 2026
"""
        messagebox.showinfo("Про програму", about_text)


def main():
    """Головна функція"""
    root = tk.Tk()
    app = SecureWipeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
