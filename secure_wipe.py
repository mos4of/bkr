#!/usr/bin/env python3
"""
Secure Wipe Tool v1.0
Програма безпечного знищення даних на носіях
Для демонстрації БКР на тему «Безпечне виведення з експлуатації технічних засобів»
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Попередження: tqdm не встановлено. Використовується простий прогрес-бар.")
    print("Для встановлення: pip install tqdm")


def format_size(size_bytes):
    """Форматування розміру в зручний вигляд"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def simple_progress_bar(current, total, prefix='', suffix='', length=40):
    """Простий прогрес-бар без tqdm"""
    percent = (current / total) * 100
    filled = int(length * current // total)
    bar = '=' * filled + '>' + '-' * (length - filled - 1)
    print(f'\r{prefix}[{bar}] {percent:.1f}% {suffix}', end='', flush=True)
    if current == total:
        print()


def wipe_zeros(target_path, block_size=512):
    """
    МЕТОД 1: Перезаписування нулями (1 прохід)
    Відкрити файл/диск і записати 0x00 по всій довжині
    """
    print(f"\n[МЕТОД 1] Перезаписування нулями (1 прохід)")
    print(f"Ціль: {target_path}")
    
    file_size = os.path.getsize(target_path)
    zeros = b'\x00' * block_size
    
    print(f"Розмір: {format_size(file_size)}")
    
    start_time = time.time()
    
    with open(target_path, 'r+b') as f:
        if TQDM_AVAILABLE:
            with tqdm(total=file_size, unit='B', unit_scale=True, 
                     desc="Pass 1/1 (0x00)", ascii=True) as pbar:
                while True:
                    pos = f.tell()
                    if pos >= file_size:
                        break
                    remaining = min(block_size, file_size - pos)
                    f.write(zeros[:remaining])
                    pbar.update(remaining)
        else:
            bytes_written = 0
            while bytes_written < file_size:
                remaining = min(block_size, file_size - bytes_written)
                f.write(zeros[:remaining])
                bytes_written += remaining
                simple_progress_bar(bytes_written, file_size, 
                                  prefix="Pass 1/1: ", suffix=f"| {format_size(bytes_written)}/s")
    
    duration = time.time() - start_time
    print(f"\nЗнищення завершено за {duration:.2f} сек.")
    return duration


def wipe_dod(target_path, block_size=512):
    """
    МЕТОД 2: Перезаписування за DoD 5220.22-M (3 проходи)
    Прохід 1: 0x00, Прохід 2: 0xFF, Прохід 3: випадкові байти
    """
    print(f"\n[МЕТОД 2] Перезаписування за DoD 5220.22-M (3 проходи)")
    print(f"Ціль: {target_path}")
    
    file_size = os.path.getsize(target_path)
    passes = [
        (b'\x00' * block_size, "0x00"),
        (b'\xFF' * block_size, "0xFF"),
        (None, "random")
    ]
    
    print(f"Розмір: {format_size(file_size)}")
    
    start_time = time.time()
    
    for pass_num, (data, desc) in enumerate(passes, 1):
        print(f"\nПрохід {pass_num}/3: запис {desc}")
        
        with open(target_path, 'r+b') as f:
            if TQDM_AVAILABLE:
                with tqdm(total=file_size, unit='B', unit_scale=True,
                         desc=f"Pass {pass_num}/3 ({desc})", ascii=True) as pbar:
                    while True:
                        pos = f.tell()
                        if pos >= file_size:
                            break
                        remaining = min(block_size, file_size - pos)
                        if data is None:
                            f.write(os.urandom(remaining))
                        else:
                            f.write(data[:remaining])
                        pbar.update(remaining)
            else:
                bytes_written = 0
                while bytes_written < file_size:
                    remaining = min(block_size, file_size - bytes_written)
                    if data is None:
                        f.write(os.urandom(remaining))
                    else:
                        f.write(data[:remaining])
                    bytes_written += remaining
                    simple_progress_bar(bytes_written, file_size,
                                      prefix=f"Pass {pass_num}/3: ", 
                                      suffix=f"| {format_size(bytes_written)}/s")
    
    duration = time.time() - start_time
    print(f"\nЗнищення завершено за {duration:.2f} сек.")
    return duration


def wipe_gutmann(target_path, block_size=512):
    """
    МЕТОД 3: Перезаписування за схемою Гутмана (спрощено, 7 проходів)
    Чергування: 0x00, 0xFF, random, 0xAA, 0x55, random, 0x00
    """
    print(f"\n[МЕТОД 3] Перезаписування за схемою Гутмана (7 проходів)")
    print(f"Ціль: {target_path}")
    
    file_size = os.path.getsize(target_path)
    passes = [
        (b'\x00' * block_size, "0x00"),
        (b'\xFF' * block_size, "0xFF"),
        (None, "random"),
        (b'\xAA' * block_size, "0xAA"),
        (b'\x55' * block_size, "0x55"),
        (None, "random"),
        (b'\x00' * block_size, "0x00")
    ]
    
    print(f"Розмір: {format_size(file_size)}")
    
    start_time = time.time()
    
    for pass_num, (data, desc) in enumerate(passes, 1):
        print(f"\nПрохід {pass_num}/7: запис {desc}")
        
        with open(target_path, 'r+b') as f:
            if TQDM_AVAILABLE:
                with tqdm(total=file_size, unit='B', unit_scale=True,
                         desc=f"Pass {pass_num}/7 ({desc})", ascii=True) as pbar:
                    while True:
                        pos = f.tell()
                        if pos >= file_size:
                            break
                        remaining = min(block_size, file_size - pos)
                        if data is None:
                            f.write(os.urandom(remaining))
                        else:
                            f.write(data[:remaining])
                        pbar.update(remaining)
            else:
                bytes_written = 0
                while bytes_written < file_size:
                    remaining = min(block_size, file_size - bytes_written)
                    if data is None:
                        f.write(os.urandom(remaining))
                    else:
                        f.write(data[:remaining])
                    bytes_written += remaining
                    simple_progress_bar(bytes_written, file_size,
                                      prefix=f"Pass {pass_num}/7: ",
                                      suffix=f"| {format_size(bytes_written)}/s")
    
    duration = time.time() - start_time
    print(f"\nЗнищення завершено за {duration:.2f} сек.")
    return duration


def verify_wipe(target_path, block_size=512):
    """
    МЕТОД 4: Верифікація після знищення
    Читати носій і перевіряти чи залишились ненульові байти
    Повертає dict з результатами
    """
    print(f"\n[ВЕРИФІКАЦІЯ] Перевірка знищення даних")
    print(f"Ціль: {target_path}")
    
    file_size = os.path.getsize(target_path)
    zeros = b'\x00' * block_size
    
    total_blocks = 0
    clean_blocks = 0
    dirty_blocks = 0
    non_zero_bytes = 0
    
    print(f"Розмір: {format_size(file_size)}")
    
    start_time = time.time()
    
    with open(target_path, 'rb') as f:
        if TQDM_AVAILABLE:
            with tqdm(total=file_size, unit='B', unit_scale=True,
                     desc="Verifying", ascii=True) as pbar:
                while True:
                    pos = f.tell()
                    if pos >= file_size:
                        break
                    remaining = min(block_size, file_size - pos)
                    data = f.read(remaining)
                    total_blocks += 1
                    
                    if data == zeros[:len(data)]:
                        clean_blocks += 1
                    else:
                        dirty_blocks += 1
                        non_zero_bytes += sum(1 for b in data if b != 0x00)
                    
                    pbar.update(len(data))
        else:
            bytes_read = 0
            while bytes_read < file_size:
                remaining = min(block_size, file_size - bytes_read)
                data = f.read(remaining)
                total_blocks += 1
                
                if data == zeros[:len(data)]:
                    clean_blocks += 1
                else:
                    dirty_blocks += 1
                    non_zero_bytes += sum(1 for b in data if b != 0x00)
                
                bytes_read += len(data)
                simple_progress_bar(bytes_read, file_size,
                                  prefix="Verify: ",
                                  suffix=f"| блоків: {total_blocks}")
    
    duration = time.time() - start_time
    
    clean_percent = (clean_blocks / total_blocks * 100) if total_blocks > 0 else 0
    dirty_percent = (dirty_blocks / total_blocks * 100) if total_blocks > 0 else 0
    
    result = {
        'success': dirty_blocks == 0,
        'total_blocks': total_blocks,
        'clean_blocks': clean_blocks,
        'dirty_blocks': dirty_blocks,
        'clean_percent': clean_percent,
        'dirty_percent': dirty_percent,
        'non_zero_bytes': non_zero_bytes,
        'duration': duration
    }
    
    print(f"\n\nРезультати верифікації:")
    print(f"  Всього блоків: {total_blocks}")
    print(f"  Чистих блоків: {clean_blocks} ({clean_percent:.2f}%)")
    print(f"  Брудних блоків: {dirty_blocks} ({dirty_percent:.2f}%)")
    print(f"  Ненульових байтів: {non_zero_bytes}")
    print(f"  Час перевірки: {duration:.2f} сек.")
    
    if result['success']:
        print(f"\n✓ Верифікація пройшла успішно! Всі дані знищено.")
    else:
        print(f"\n✗ УВАГА: Виявлено {non_zero_bytes} ненульових байтів!")
        print(f"  Знищення неповне. Рекомендується повторити операцію.")
    
    return result


def save_log(method, target, result, duration):
    """
    Логування операцій
    Зберігає лог у файл: дата, метод, назва носія, результат, час виконання
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"wipe_log_{datetime.now().strftime('%Y-%m-%d')}.txt"
    
    log_entry = f"""
{'='*60}
Дата: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Метод: {method}
Ціль: {target}
Результат: {result}
Час виконання: {duration:.2f} сек.
{'='*60}
"""
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(f"\nЛог збережено: {log_file}")
    return log_file


def create_test_file(filename="test_data.bin", size_mb=10):
    """
    Створення тестового файлу з псевдо-даними
    """
    print(f"\n[ТЕСТОВИЙ РЕЖИМ] Створення тестового файлу")
    print(f"Файл: {filename}")
    print(f"Розмір: {size_mb} МБ")
    
    size_bytes = size_mb * 1024 * 1024
    
    test_data_patterns = [
        b"CONFIDENTIAL DATA " * 10,
        b"1234567890" * 20,
        os.urandom(512),
        b"SECRET DOCUMENT " * 15,
        b"DELETE ME " * 25
    ]
    
    start_time = time.time()
    
    with open(filename, 'wb') as f:
        if TQDM_AVAILABLE:
            with tqdm(total=size_bytes, unit='B', unit_scale=True,
                     desc="Creating test file", ascii=True) as pbar:
                bytes_written = 0
                pattern_index = 0
                while bytes_written < size_bytes:
                    remaining = min(512, size_bytes - bytes_written)
                    pattern = test_data_patterns[pattern_index % len(test_data_patterns)]
                    f.write(pattern[:remaining])
                    bytes_written += remaining
                    pbar.update(remaining)
                    pattern_index += 1
        else:
            bytes_written = 0
            pattern_index = 0
            while bytes_written < size_bytes:
                remaining = min(512, size_bytes - bytes_written)
                pattern = test_data_patterns[pattern_index % len(test_data_patterns)]
                f.write(pattern[:remaining])
                bytes_written += remaining
                pattern_index += 1
                simple_progress_bar(bytes_written, size_bytes,
                                  prefix="Creating: ",
                                  suffix=f"| {format_size(bytes_written)}")
    
    duration = time.time() - start_time
    print(f"\nТестовий файл створено за {duration:.2f} сек.")
    print(f"Шлях: {os.path.abspath(filename)}")
    return os.path.abspath(filename)


def test_mode():
    """
    ТЕСТОВИЙ РЕЖИМ - безпечна демонстрація
    """
    print("\n" + "="*60)
    print("ТЕСТОВИЙ РЕЖИМ (безпечна демонстрація)")
    print("="*60)
    
    test_file = create_test_file("test_data.bin", size_mb=10)
    
    print("\nОберіть метод знищення для тестування:")
    print("[1] Zeros (1 pass)")
    print("[2] DoD 5220.22-M (3 passes)")
    print("[3] Gutmann simplified (7 passes)")
    print("[4] Verify only")
    
    choice = input("\nВаш вибір (1-4): ").strip()
    
    methods = {
        '1': ('Zeros (1 pass)', wipe_zeros),
        '2': ('DoD 5220.22-M (3 passes)', wipe_dod),
        '3': ('Gutmann simplified (7 passes)', wipe_gutmann),
        '4': ('Verify only', None)
    }
    
    if choice not in methods:
        print("Невірний вибір!")
        return
    
    method_name, method_func = methods[choice]
    
    if choice == '4':
        result = verify_wipe(test_file)
        save_log("Verify only", test_file, 
                "SUCCESS" if result['success'] else "FAILED", 
                result['duration'])
    else:
        print(f"\nУВАГА: Дані у тестовому файлі будуть знищені!")
        print(f"Ціль: {test_file}")
        confirm = input("Підтвердіть (y/n): ").strip().lower()
        
        if confirm == 'y':
            start_time = time.time()
            duration = method_func(test_file)
            total_duration = time.time() - start_time
            
            result = verify_wipe(test_file)
            
            save_log(method_name, test_file, 
                    "SUCCESS" if result['success'] else "FAILED", 
                    total_duration)
        else:
            print("Операцію скасовано.")
    
    print(f"\nТестовий файл все ще існує: {test_file}")
    delete = input("Видалити тестовий файл? (y/n): ").strip().lower()
    if delete == 'y':
        os.remove(test_file)
        print("Тестовий файл видалено.")


def main():
    """
    Головна функція - меню вибору методу
    """
    print("\n" + "="*60)
    print("=== SECURE WIPE TOOL v1.0 ===")
    print("Безпечне знищення даних на носіях")
    print("="*60)
    
    while True:
        print("\nОберіть метод знищення:")
        print("[1] Zeros (1 pass)")
        print("[2] DoD 5220.22-M (3 passes)")
        print("[3] Gutmann simplified (7 passes)")
        print("[4] Verify only")
        print("[5] Test mode (safe demo)")
        print("[0] Вихід")
        
        choice = input("\nВаш вибір (0-5): ").strip()
        
        if choice == '0':
            print("\nДо побачення!")
            break
        
        if choice == '5':
            test_mode()
            continue
        
        if choice not in ['1', '2', '3', '4']:
            print("Невірний вибір!")
            continue
        
        target = input("\nВведіть шлях до файлу/диску: ").strip()
        
        if not os.path.exists(target):
            print(f"ПОМИЛКА: Шлях не існує: {target}")
            continue
        
        if not os.path.isfile(target):
            print(f"ПОМИЛКА: Це не файл: {target}")
            print("Для демонстрації використовуйте тестовий режим [5]")
            continue
        
        methods = {
            '1': ('Zeros (1 pass)', wipe_zeros),
            '2': ('DoD 5220.22-M (3 passes)', wipe_dod),
            '3': ('Gutmann simplified (7 passes)', wipe_gutmann)
        }
        
        if choice == '4':
            result = verify_wipe(target)
            save_log("Verify only", target, 
                    "SUCCESS" if result['success'] else "FAILED", 
                    result['duration'])
            continue
        
        method_name, method_func = methods[choice]
        
        print(f"\n{'='*60}")
        print(f"УВАГА: ДАНІ БУДУТЬ ЗНИЩЕНІ БЕЗПОВОРОТНО!")
        print(f"Ціль: {target}")
        print(f"Метод: {method_name}")
        print(f"{'='*60}")
        
        confirm = input("\nПідтвердіть знищення (y/n): ").strip().lower()
        
        if confirm == 'y':
            start_time = time.time()
            duration = method_func(target)
            total_duration = time.time() - start_time
            
            result = verify_wipe(target)
            
            save_log(method_name, target, 
                    "SUCCESS" if result['success'] else "FAILED", 
                    total_duration)
        else:
            print("Операцію скасовано.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограму перервано користувачем.")
        sys.exit(0)
    except Exception as e:
        print(f"\nПОМИЛКА: {e}")
        sys.exit(1)
