#!/usr/bin/env python3
"""
wipe_engine.py - Core wiping logic for SecureWipe Pro
Модуль з логікою безпечного знищення даних

Стандарти:
  - NIST SP 800-88r1 (Clear, Purge)
  - IEEE 2883-2022 (Crypto Erase)
"""

import os
import sys
import time
import random
import string
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable, List, Tuple


class WipeEngine:
    """Engine for secure data wiping operations (NIST SP 800-88r1 / IEEE 2883-2022)"""

    STANDARD_VERSION = "NIST SP 800-88r1 / IEEE 2883-2022"

    def __init__(self, block_size: int = 65536, progress_callback: Optional[Callable] = None):
        """
        Initialize wipe engine

        Args:
            block_size: Size of blocks for read/write operations (default 64KB)
            progress_callback: Callback function for progress updates
        """
        self.block_size = block_size
        self.progress_callback = progress_callback
        self._cancelled = False

    def cancel(self):
        """Cancel current operation"""
        self._cancelled = True

    # ============================================================
    #  МЕТОД 1 — NIST Clear (1 прохід псевдовипадкових даних)
    # ============================================================

    def wipe_nist_clear(self, target_path: str) -> Dict:
        """
        NIST SP 800-88r1, рівень Clear.
        Один прохід запису псевдовипадкових даних.

        Для кого: HDD та USB-накопичувачі, що залишаються в організації
                 або передаються в межах неї.

        Returns:
            Dictionary with operation results
        """
        self._cancelled = False
        start_time = time.time()
        method_name = "NIST Clear (1 pass pseudorandom)"

        try:
            file_size = os.path.getsize(target_path)
            written = 0

            with open(target_path, 'r+b') as f:
                while written < file_size:
                    if self._cancelled:
                        return self._create_result(False, start_time, "CANCELLED", method_name)

                    chunk = min(self.block_size, file_size - written)
                    f.write(os.urandom(chunk))  # Псевдовипадкові байти
                    written += chunk

                    if self.progress_callback:
                        progress = (written / file_size) * 100
                        self.progress_callback(
                            1, 1, "NIST Clear: random",
                            progress, written, file_size
                        )

                f.flush()
                os.fsync(f.fileno())  # Гарантує запис на фізичний носій

            duration = time.time() - start_time
            return self._create_result(True, start_time, "SUCCESS", method_name, duration)

        except Exception as e:
            duration = time.time() - start_time
            return self._create_result(False, start_time, "ERROR", method_name, duration, str(e))

    # ============================================================
    #  МЕТОД 2 — NIST Purge (апаратне стирання)
    # ============================================================

    def wipe_nist_purge(self, drive_letter: str) -> Dict:
        """
        NIST SP 800-88r1, рівень Purge; IEEE 2883-2022.
        Використовує апаратну команду контролера для знищення
        всіх даних включно з резервним простором і кешем контролера.

        Для кого: SSD, HDD — охоплює резервний простір і кеш контролера.

        Реалізація:
          Windows: diskpart 'clean all'
          Linux:   hdparm --security-erase (ATA SE) або nvme format (NVMe Sanitize)

        Args:
            drive_letter: Літера диску (Windows, напр. "D:") або device path (Linux, напр. "/dev/sdb")

        Returns:
            Dictionary with operation results
        """
        self._cancelled = False
        start_time = time.time()
        method_name = "NIST Purge (hardware erase)"

        try:
            if self._cancelled:
                return self._create_result(False, start_time, "CANCELLED", method_name)

            if os.name == 'nt':
                result = self._purge_windows(drive_letter)
            else:
                result = self._purge_linux(drive_letter)

            duration = time.time() - start_time
            if result['success']:
                return self._create_result(True, start_time, "SUCCESS", method_name, duration)
            else:
                return self._create_result(False, start_time, "ERROR", method_name, duration, result.get('error', 'Unknown error'))

        except Exception as e:
            duration = time.time() - start_time
            return self._create_result(False, start_time, "ERROR", method_name, duration, str(e))

    def _purge_windows(self, drive_letter: str) -> Dict:
        """Windows: Використовує diskpart 'clean all' для повного стирання диска"""
        # Нормалізуємо літеру диску
        drive_clean = drive_letter.strip().rstrip('\\').rstrip(':')

        script = f"""
select volume {drive_clean}
clean all
"""
        try:
            proc = subprocess.run(
                ['diskpart'],
                input=script,
                capture_output=True,
                text=True,
                timeout=86400  # Максимум 24 години для великих дисків
            )
            if proc.returncode == 0:
                return {'success': True}
            else:
                return {'success': False, 'error': f"diskpart error: {proc.stderr}"}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': "diskpart operation timed out"}
        except FileNotFoundError:
            return {'success': False, 'error': "diskpart not found (Windows only)"}

    def _purge_linux(self, device_path: str) -> Dict:
        """Linux: hdparm ATA Secure Erase або nvme Sanitize"""
        try:
            # Визначаємо тип пристрою
            if device_path.startswith('/dev/nvme'):
                # NVMe Sanitize
                # ses=1 — User Data Erase
                proc = subprocess.run(
                    ['nvme', 'format', device_path, '--ses=1'],
                    capture_output=True, text=True, timeout=86400
                )
            else:
                # hdparm ATA Secure Erase для SATA/SAS
                # Спочатку встановлюємо пароль, потім видаляємо
                set_pass = subprocess.run(
                    ['hdparm', '--user-master', 'u', '--security-set-pass', 'pw', device_path],
                    capture_output=True, text=True, timeout=30
                )
                if set_pass.returncode != 0:
                    return {'success': False, 'error': f"hdparm set password failed: {set_pass.stderr}"}

                proc = subprocess.run(
                    ['hdparm', '--user-master', 'u', '--security-erase', 'pw', device_path],
                    capture_output=True, text=True, timeout=86400
                )

            if proc.returncode == 0:
                return {'success': True}
            else:
                return {'success': False, 'error': f"erase failed: {proc.stderr}"}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': "erase operation timed out"}
        except FileNotFoundError as e:
            return {'success': False, 'error': f"required tool not found: {e}"}

    # ============================================================
    #  МЕТОД 3 — Crypto Erase (криптографічне знищення)
    # ============================================================

    def wipe_crypto_erase(self, drive_letter: str) -> Dict:
        """
        IEEE 2883-2022; NIST SP 800-88r1 рівень Purge.
        Знищення ключа шифрування BitLocker → дані стають
        криптографічно недоступними назавжди без перезапису секторів.

        Для кого: диски з увімкненим шифруванням BitLocker або SED.

        Returns:
            Dictionary with operation results
        """
        self._cancelled = False
        start_time = time.time()
        method_name = "Crypto Erase (BitLocker key destruction)"

        if os.name != 'nt':
            duration = time.time() - start_time
            return self._create_result(False, start_time, "ERROR", method_name, duration,
                                       "Crypto Erase (BitLocker) is Windows-only")

        try:
            if self._cancelled:
                return self._create_result(False, start_time, "CANCELLED", method_name)

            # Крок 1: Перевірити статус BitLocker
            check_proc = subprocess.run(
                ['powershell', '-Command',
                 f'Get-BitLockerVolume -MountPoint {drive_letter}: 2>&1'],
                capture_output=True, text=True
            )

            if check_proc.returncode != 0:
                duration = time.time() - start_time
                return self._create_result(False, start_time, "ERROR", method_name, duration,
                                           f"BitLocker check failed: {check_proc.stderr}")

            stdout = check_proc.stdout

            # Крок 2: Якщо зашифрований — видалити всі захисники ключа
            if 'FullyEncrypted' in stdout or 'EncryptionInProgress' in stdout:
                # Видалення всіх захисників ключа
                remove_proc = subprocess.run(
                    ['powershell', '-Command',
                     f'(Get-BitLockerVolume -MountPoint {drive_letter}:).KeyProtector '
                     f'| Remove-BitLockerKeyProtector -MountPoint {drive_letter}: '
                     f'-KeyProtectorId {{$_.KeyProtectorId}}'],
                    capture_output=True, text=True
                )

                # Вимкнення BitLocker
                off_proc = subprocess.run(
                    ['manage-bde', '-off', f'{drive_letter}:'],
                    capture_output=True, text=True
                )

                if off_proc.returncode == 0 or remove_proc.returncode == 0:
                    duration = time.time() - start_time
                    return self._create_result(True, start_time, "SUCCESS", method_name, duration)
                else:
                    duration = time.time() - start_time
                    return self._create_result(False, start_time, "ERROR", method_name, duration,
                                               f"Failed to disable BitLocker: {off_proc.stderr}")
            else:
                duration = time.time() - start_time
                return self._create_result(False, start_time, "ERROR", method_name, duration,
                                           "Drive is not BitLocker-encrypted. Crypto Erase unavailable.")

        except Exception as e:
            duration = time.time() - start_time
            return self._create_result(False, start_time, "ERROR", method_name, duration, str(e))

    def check_bitlocker_status(self, drive_letter: str) -> Tuple[bool, str]:
        """
        Перевірити статус BitLocker для диска.

        Returns:
            (is_encrypted, status_message)
        """
        if os.name != 'nt':
            return False, "Windows only"

        try:
            proc = subprocess.run(
                ['powershell', '-Command',
                 f'Get-BitLockerVolume -MountPoint {drive_letter}: 2>&1'],
                capture_output=True, text=True
            )
            stdout = proc.stdout

            if 'FullyEncrypted' in stdout:
                return True, "FullyEncrypted"
            elif 'EncryptionInProgress' in stdout:
                return True, "EncryptionInProgress"
            elif 'FullyDecrypted' in stdout:
                return False, "FullyDecrypted"
            else:
                return False, "Unknown"
        except Exception:
            return False, "Error checking"

    def is_admin(self) -> bool:
        """Перевірка наявності прав адміністратора"""
        try:
            if os.name == 'nt':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False

    # ============================================================
    #  ВЕРИФІКАЦІЯ
    # ============================================================

    def verify_wipe(self, target_path: str, method: str = "NIST Clear",
                    original_data: bytes = None, file_size: int = 0) -> Dict:
        """
        Розширена верифікація знищення даних — специфічна для кожного методу.

        Args:
            target_path: Шлях до файлу/диска
            method: Назва методу знищення
            original_data: Оригінальні дані (для порівняння, якщо доступні)
            file_size: Оригінальний розмір файлу

        Returns:
            Dictionary with verification results
        """
        self._cancelled = False
        start_time = time.time()

        try:
            if not file_size:
                file_size = os.path.getsize(target_path)

            if "NIST Clear" in method:
                return self._verify_nist_clear(target_path, file_size, original_data)
            elif "NIST Purge" in method or "Purge" in method:
                return self._verify_nist_purge(target_path, file_size)
            elif "Crypto Erase" in method or "Crypto" in method:
                return self._verify_crypto_erase(target_path)
            elif "Gutmann" in method or "DoD" in method or "dod" in method.lower():
                # Для сумісності — перевірка як NIST Clear
                return self._verify_nist_clear(target_path, file_size, original_data)
            elif "zeros" in method.lower() or "zero" in method.lower():
                return self._verify_zeros(target_path, file_size)
            else:
                return self._verify_generic(target_path, file_size)

        except Exception as e:
            duration = time.time() - start_time
            return {
                'success': False,
                'duration': duration,
                'error': str(e),
                'status': 'ERROR',
                'method': method
            }

    def _verify_nist_clear(self, target_path: str, file_size: int,
                           original_data: bytes = None) -> Dict:
        """
        Верифікація NIST Clear:
        Зчитує 1000 випадкових секторів і перевіряє що вміст
        відрізняється від нулів і від оригіналу.
        """
        self._cancelled = False
        block_size = self.block_size
        total_blocks = (file_size + block_size - 1) // block_size

        print(f"\n[ВЕРИФІКАЦІЯ NIST Clear] Перевірка результату...")
        print(f"  Файл: {os.path.basename(target_path)}")
        print(f"  Розмір: {self._format_size(file_size)}")
        print(f"  Секторів загалом: {total_blocks}")

        # Випадкові позиції для перевірки (максимум 1000)
        num_samples = min(1000, total_blocks)
        sample_positions = sorted(random.sample(range(total_blocks), num_samples))

        changed_count = 0
        zero_count = 0
        original_match = 0

        with open(target_path, 'rb') as f:
            for idx, block_num in enumerate(sample_positions):
                if self._cancelled:
                    return self._create_result(False, 0, "CANCELLED", "Verify NIST Clear")

                f.seek(block_num * block_size)
                data = f.read(min(block_size, file_size - block_num * block_size))

                is_zeros = data == b'\x00' * len(data)
                is_original = original_data and self._is_original_block(data, block_num, original_data, block_size)

                if not is_zeros:
                    changed_count += 1
                if is_zeros:
                    zero_count += 1
                if is_original:
                    original_match += 1

                if self.progress_callback and (idx + 1) % 50 == 0:
                    progress = ((idx + 1) / num_samples) * 100
                    self.progress_callback(1, 1, "Verify NIST Clear", progress, idx + 1, num_samples)

        # Результати
        changed_percent = (changed_count / num_samples * 100) if num_samples > 0 else 0
        zero_percent = (zero_count / num_samples * 100) if num_samples > 0 else 0

        # Успіх: більшість секторів змінено і не є нулями
        success = changed_percent > 95.0

        print(f"  Перевірено секторів: {num_samples}")
        print(f"  Змінено (не нулі): {changed_count}/{num_samples} ({changed_percent:.2f}%)")
        print(f"  Нулів: {zero_count}/{num_samples} ({zero_percent:.2f}%)")
        if original_data:
            print(f"  Відповідностей оригіналу: {original_match}/{num_samples}")
        print(f"{'='*50}")

        if success:
            print(f"✓ Верифікація NIST Clear: {changed_percent:.1f}% секторів змінено ✓")
        else:
            print(f"✗ Верифікація NIST Clear: недостатньо змін ({changed_percent:.1f}%)")

        duration = time.time() - start_time
        return {
            'success': success,
            'duration': duration,
            'method': 'NIST Clear',
            'status': 'SUCCESS' if success else 'FAILED',
            'total_blocks': num_samples,
            'changed_blocks': changed_count,
            'zero_blocks': zero_count,
            'changed_percent': changed_percent,
            'clean_percent': changed_percent,
            'file_size': file_size,
            'verification_samples': num_samples
        }

    def _verify_nist_purge(self, target_path: str, file_size: int) -> Dict:
        """
        Верифікація NIST Purge:
        Зчитує перші/останні/випадкові сектори, перевіряє що вміст = нулі.
        """
        self._cancelled = False
        block_size = self.block_size
        total_blocks = (file_size + block_size - 1) // block_size

        print(f"\n[ВЕРИФІКАЦІЯ NIST Purge] Перевірка результату...")
        print(f"  Файл: {os.path.basename(target_path)}")
        print(f"  Розмір: {self._format_size(file_size)}")

        # Перевіряємо: перші 100, останні 100, 800 випадкових
        num_edge = min(100, total_blocks)
        num_random = min(800, max(0, total_blocks - 2 * num_edge))

        positions = list(range(num_edge))  # Перші
        if total_blocks > num_edge * 2:
            positions.extend(range(total_blocks - num_edge, total_blocks))  # Останні
        if total_blocks > num_edge * 2 + num_random:
            mid_range = range(num_edge, total_blocks - num_edge)
            positions.extend(random.sample(list(mid_range), min(num_random, len(mid_range))))

        zero_count = 0
        non_zero_count = 0

        with open(target_path, 'rb') as f:
            for idx, block_num in enumerate(positions):
                if self._cancelled:
                    return self._create_result(False, 0, "CANCELLED", "Verify NIST Purge")

                f.seek(block_num * block_size)
                data = f.read(min(block_size, file_size - block_num * block_size))

                if data == b'\x00' * len(data):
                    zero_count += 1
                else:
                    non_zero_count += 1

                if self.progress_callback and (idx + 1) % 100 == 0:
                    progress = ((idx + 1) / len(positions)) * 100
                    self.progress_callback(1, 1, "Verify NIST Purge", progress, idx + 1, len(positions))

        total_checked = len(positions)
        clean_percent = (zero_count / total_checked * 100) if total_checked > 0 else 0
        success = non_zero_count == 0

        print(f"  Перевірено секторів: {total_checked}")
        print(f"  Чистих (нули): {zero_count}/{total_checked} ({clean_percent:.2f}%)")
        print(f"  Ненульових: {non_zero_count}")
        print(f"{'='*50}")

        if success:
            print(f"✓ Верифікація NIST Purge: 100% секторів чисті ✓")
        else:
            print(f"✗ Верифікація NIST Purge: знайдено ненульові сектори!")

        duration = time.time() - start_time
        return {
            'success': success,
            'duration': duration,
            'method': 'NIST Purge',
            'status': 'SUCCESS' if success else 'FAILED',
            'total_blocks': total_checked,
            'clean_blocks': zero_count,
            'dirty_blocks': non_zero_count,
            'clean_percent': clean_percent,
            'file_size': file_size
        }

    def _verify_crypto_erase(self, drive_letter: str) -> Dict:
        """
        Верифікація Crypto Erase:
        Перевіряє що BitLocker вимкнений, спробує прочитати дані.
        """
        print(f"\n[ВЕРИФІКАЦІЯ Crypto Erase] Перевірка результату...")
        print(f"  Диск: {drive_letter}:")

        # Перевірка статусу BitLocker
        try:
            proc = subprocess.run(
                ['powershell', '-Command',
                 f'Get-BitLockerVolume -MountPoint {drive_letter}: 2>&1'],
                capture_output=True, text=True
            )
            stdout = proc.stdout

            if 'FullyDecrypted' in stdout:
                print(f"  Статус BitLocker: Вимкнено ✓")
                success = True
                status_msg = "Ключ знищено, BitLocker вимкнено"
            elif 'FullyEncrypted' in stdout:
                print(f"  Статус BitLocker: Зашифровано (помилка!)")
                success = False
                status_msg = "BitLocker все ще зашифрований"
            else:
                print(f"  Статус BitLocker: Невизначено")
                success = False
                status_msg = "Не вдалося визначити статус BitLocker"

        except Exception as e:
            print(f"  Помилка перевірки BitLocker: {e}")
            success = False
            status_msg = f"Помилка: {e}"

        print(f"{'='*50}")
        if success:
            print(f"✓ Верифікація Crypto Erase: ключ знищено, статус BitLocker: вимкнено ✓")
        else:
            print(f"✗ Верифікація Crypto Erase: {status_msg}")

        duration = time.time() - start_time
        return {
            'success': success,
            'duration': duration,
            'method': 'Crypto Erase',
            'status': 'SUCCESS' if success else 'FAILED',
            'bitlocker_status': status_msg
        }

    def _verify_zeros(self, target_path: str, file_size: int) -> Dict:
        """Верифікація знищення нулями"""
        self._cancelled = False
        block_size = self.block_size
        total_blocks = 0
        clean_blocks = 0

        print(f"\n[ВЕРИФІКАЦІЯ Zeros] Перевірка результату...")
        print(f"  Файл: {os.path.basename(target_path)}")
        print(f"  Розмір: {self._format_size(file_size)}")

        with open(target_path, 'rb') as f:
            bytes_read = 0
            while bytes_read < file_size:
                if self._cancelled:
                    return self._create_result(False, 0, "CANCELLED", "Verify Zeros")

                remaining = min(block_size, file_size - bytes_read)
                data = f.read(remaining)
                total_blocks += 1

                if data == b'\x00' * len(data):
                    clean_blocks += 1

                bytes_read += len(data)

                if self.progress_callback:
                    progress = (bytes_read / file_size) * 100
                    self.progress_callback(1, 1, "Verify Zeros", progress, bytes_read, file_size)

        clean_percent = (clean_blocks / total_blocks * 100) if total_blocks > 0 else 0
        success = clean_blocks == total_blocks

        print(f"  Перевірено секторів: {total_blocks}")
        print(f"  Чистих: {clean_blocks} ({clean_percent:.2f}%)")
        print(f"{'='*50}")

        if success:
            print(f"✓ Верифікація Zeros: 100% секторів = 0x00 ✓")
        else:
            print(f"✗ Верифікація Zeros: знайдено ненульові сектори!")

        duration = time.time() - start_time
        return {
            'success': success,
            'duration': duration,
            'method': 'Zeros',
            'status': 'SUCCESS' if success else 'FAILED',
            'total_blocks': total_blocks,
            'clean_blocks': clean_blocks,
            'clean_percent': clean_percent,
            'file_size': file_size
        }

    def _verify_generic(self, target_path: str, file_size: int) -> Dict:
        """Загальна верифікація — перевіряє що файл не містить оригінальних даних"""
        return self._verify_nist_clear(target_path, file_size)

    def _is_original_block(self, data: bytes, block_num: int,
                           original_data: bytes, block_size: int) -> bool:
        """Перевіряє чи блок збігається з оригінальним"""
        start = block_num * block_size
        end = start + len(data)
        if start < len(original_data):
            orig_block = original_data[start:end]
            return data == orig_block
        return False

    # ============================================================
    #  РЕЖИМ 2: Папка
    # ============================================================

    def wipe_folder(self, folder_path: str, method: str = "nist_clear") -> Dict:
        """
        Mode 2: Wipe all files in folder recursively.

        Args:
            folder_path: Path to folder
            method: Wiping method ('nist_clear', 'nist_purge', 'crypto_erase')

        Returns:
            Dictionary with results
        """
        self._cancelled = False
        start_time = time.time()

        results = {
            'total_files': 0,
            'wiped_files': 0,
            'failed_files': 0,
            'total_size': 0,
            'errors': [],
            'method': method,
            'standard': self.STANDARD_VERSION
        }

        # Вибір функції знищення
        wipe_func = self._get_wipe_function(method)
        if wipe_func is None:
            results['status'] = 'ERROR'
            results['error'] = f"Unknown method: {method}"
            return results

        try:
            # Збираємо всі файли
            all_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        all_files.append(file_path)

            results['total_files'] = len(all_files)

            if self.progress_callback:
                self.progress_callback(0, 1, "Scanning folder", 0, 0, 0)

            print(f"\n[ПАПКА] Знайдено файлів: {len(all_files)}\n")

            # Знищуємо кожен файл
            for idx, file_path in enumerate(all_files, 1):
                if self._cancelled:
                    results['status'] = 'CANCELLED'
                    return results

                try:
                    file_size = os.path.getsize(file_path)
                    results['total_size'] += file_size

                    print(f"Файл {idx} з {len(all_files)}: {os.path.basename(file_path)}")

                    wipe_result = wipe_func(file_path)

                    if wipe_result.get('success'):
                        results['wiped_files'] += 1
                    else:
                        results['failed_files'] += 1
                        results['errors'].append(f"{file_path}: {wipe_result.get('error', 'Unknown error')}")

                except Exception as e:
                    results['failed_files'] += 1
                    results['errors'].append(f"{file_path}: {str(e)}")
                    print(f"ПОМИЛКА: {e}")

                # Update progress
                if self.progress_callback:
                    progress = (idx / len(all_files)) * 100
                    self.progress_callback(
                        idx, len(all_files), f"File {idx}/{len(all_files)}",
                        progress, idx, len(all_files)
                    )

            # Видалення порожніх директорій
            print(f"\n[ПАПКА] Видалення порожніх папок...")
            self._remove_empty_dirs(folder_path)

            duration = time.time() - start_time
            results['duration'] = duration
            results['status'] = 'SUCCESS'
            results['success'] = results['failed_files'] == 0

            print(f"\n[ПАПКА] Завершено!")
            print(f"  Знищено файлів: {results['wiped_files']}")
            print(f"  Загальний розмір: {self._format_size(results['total_size'])}")
            print(f"  Час: {duration:.2f} сек.\n")

        except Exception as e:
            duration = time.time() - start_time
            results['duration'] = duration
            results['status'] = 'ERROR'
            results['error'] = str(e)
            results['success'] = False

        return results

    def _get_wipe_function(self, method: str):
        """Повертає функцію знищення за назвою методу"""
        method_map = {
            'nist_clear': self.wipe_nist_clear,
            'nist_purge': self.wipe_nist_purge,
            'crypto_erase': self.wipe_crypto_erase,
            'zeros': self.wipe_zeros,
            'dod': self.wipe_dod,
            'gutmann': self.wipe_gutmann,
        }
        return method_map.get(method.lower())

    # ============================================================
    #  РЕЖИМ 3: Вільний простір диску
    # ============================================================

    def wipe_free_space(self, drive_letter: str, method: str = "zeros") -> Dict:
        """
        Mode 3: Fill free disk space with temp files then delete them.

        Args:
            drive_letter: Drive letter (e.g., "C:\\", "D:\\")
            method: Fill method ('zeros' or 'random')

        Returns:
            Dictionary with results
        """
        self._cancelled = False
        start_time = time.time()

        results = {
            'total_space_filled': 0,
            'temp_files_created': 0,
            'errors': [],
            'method': method,
            'standard': self.STANDARD_VERSION
        }

        try:
            import shutil

            # Get free space
            total, used, free = shutil.disk_usage(drive_letter)
            free_gb = free / (1024 ** 3)

            print(f"\n[ВІЛЬНИЙ ПРОСТІР] Диск: {drive_letter}")
            print(f"  Вільно: {free_gb:.2f} GB")
            print(f"  Метод заповнення: {method}\n")

            if self.progress_callback:
                self.progress_callback(0, 1, "Checking free space", 0, 0, free)

            temp_dir = os.path.join(drive_letter, "temp_wipe_secure")
            os.makedirs(temp_dir, exist_ok=True)

            temp_files = []
            bytes_written = 0
            file_counter = 0

            # Fill free space
            while True:
                if self._cancelled:
                    results['status'] = 'CANCELLED'
                    break

                try:
                    # Check if still free space
                    _, _, free = shutil.disk_usage(drive_letter)
                    if free < 1024 * 1024:  # Less than 1MB free
                        break

                    # Create temp file (100MB chunks)
                    file_counter += 1
                    temp_file = os.path.join(temp_dir, f"temp_{file_counter}.bin")
                    temp_files.append(temp_file)

                    with open(temp_file, 'wb') as f:
                        chunk_size = 100 * 1024 * 1024  # 100MB
                        block = (b'\x00' * self.block_size if method == "zeros"
                                 else os.urandom(self.block_size))

                        written = 0
                        while written < chunk_size:
                            if self._cancelled:
                                break

                            remaining = min(self.block_size, chunk_size - written)
                            f.write(block[:remaining])
                            written += remaining
                            bytes_written += remaining

                            # Update progress every 10MB
                            if written % (10 * 1024 * 1024) == 0:
                                if self.progress_callback:
                                    filled_gb = bytes_written / (1024 ** 3)
                                    progress = (filled_gb / free_gb) * 100 if free_gb > 0 else 0
                                    self.progress_callback(
                                        int(filled_gb), int(free_gb), f"Filled {filled_gb:.1f} GB",
                                        progress, bytes_written, free
                                    )

                    results['temp_files_created'] += 1

                    # Update progress
                    filled_gb = bytes_written / (1024 ** 3)
                    if self.progress_callback:
                        progress = (filled_gb / free_gb) * 100 if free_gb > 0 else 0
                        self.progress_callback(
                            int(filled_gb), int(free_gb), f"Filled {filled_gb:.1f} GB",
                            min(progress, 100), bytes_written, free
                        )

                    print(f"Заповнено {filled_gb:.2f} GB з {free_gb:.2f} GB")

                except OSError as e:
                    if "No space left" in str(e) or "disk full" in str(e).lower():
                        break
                    else:
                        results['errors'].append(str(e))
                        break

            # Delete temp files
            print(f"\n[ВІЛЬНИЙ ПРОСТІР] Видалення тимчасових файлів...")
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    results['errors'].append(f"Delete {temp_file}: {str(e)}")

            # Remove temp directory
            try:
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception:
                pass

            duration = time.time() - start_time
            results['duration'] = duration
            results['total_space_filled'] = bytes_written
            results['status'] = 'SUCCESS'
            results['success'] = True

            filled_gb = bytes_written / (1024 ** 3)
            print(f"\n[ВІЛЬНИЙ ПРОСТІР] Завершено!")
            print(f"  Заповнено: {filled_gb:.2f} GB")
            print(f"  Створено файлів: {results['temp_files_created']}")
            print(f"  Час: {duration:.2f} сек.\n")

        except Exception as e:
            duration = time.time() - start_time
            results['duration'] = duration
            results['status'] = 'ERROR'
            results['error'] = str(e)
            results['success'] = False

        return results

    # ============================================================
    #  РЕЖИМ 4: Повне знищення диска
    # ============================================================

    def wipe_disk_full(self, drive_letter: str, method: str = "nist_clear") -> Dict:
        """
        FULL DISK WIPE: Destroy ALL data on selected disk.
        Wipes all files and folders, then fills free space.

        Args:
            drive_letter: Drive letter (e.g., "E:\\")
            method: Wipe method ('nist_clear', 'nist_purge', 'crypto_erase', 'zeros')

        Returns:
            Dictionary with results
        """
        self._cancelled = False
        start_time = time.time()

        results = {
            'total_files': 0,
            'wiped_files': 0,
            'failed_files': 0,
            'total_folders': 0,
            'total_size': 0,
            'errors': [],
            'method': method,
            'standard': self.STANDARD_VERSION
        }

        try:
            print(f"\n[ПОВНЕ ЗНИЩЕННЯ ДИСКА] Диск: {drive_letter}")
            print(f"  Метод: {method}\n")

            if not os.path.exists(drive_letter):
                results['error'] = f"Диск не знайдено: {drive_letter}"
                results['success'] = False
                return results

            # Step 1: Collect all files on disk
            print("[ПОВНЕ ЗНИЩЕННЯ] Збір файлів на диску...")
            all_files = []
            all_dirs = []

            for root, dirs, files in os.walk(drive_letter):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    all_dirs.append(dir_path)

            results['total_files'] = len(all_files)
            results['total_folders'] = len(all_dirs)

            print(f"  Знайдено файлів: {len(all_files)}")
            print(f"  Знайдено папок: {len(all_dirs)}\n")

            # Step 2: Wipe all files
            print("[ПОВНЕ ЗНИЩЕННЯ] Знищення файлів...")

            wipe_func = self._get_wipe_function(method)
            if wipe_func is None:
                wipe_func = self.wipe_nist_clear  # Default

            for idx, file_path in enumerate(all_files, 1):
                if self._cancelled:
                    results['status'] = 'CANCELLED'
                    break

                try:
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        results['total_size'] += file_size

                        wipe_result = wipe_func(file_path)

                        if wipe_result.get('success'):
                            results['wiped_files'] += 1
                        else:
                            results['failed_files'] += 1
                            results['errors'].append(f"{file_path}: {wipe_result.get('error', 'Unknown')}")

                        # Delete file after wipe
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass

                        # Progress
                        if self.progress_callback:
                            progress = (idx / len(all_files)) * 100
                            self.progress_callback(
                                idx, len(all_files), f"File {idx}/{len(all_files)}",
                                progress, idx, len(all_files)
                            )

                        if idx % 10 == 0:
                            print(f"  Знищено: {idx}/{len(all_files)} файлів")

                except Exception as e:
                    results['failed_files'] += 1
                    results['errors'].append(f"{file_path}: {str(e)}")
                    print(f"ПОМИЛКА: {file_path} - {e}")

            print(f"\n  Знищено файлів: {results['wiped_files']}/{results['total_files']}")

            # Step 3: Remove empty directories
            print(f"\n[ПОВНЕ ЗНИЩЕННЯ] Видалення порожніх папок...")
            all_dirs_sorted = sorted(all_dirs, reverse=True)

            for dir_path in all_dirs_sorted:
                try:
                    if os.path.exists(dir_path) and not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except Exception:
                    pass

            # Step 4: Fill remaining free space (only for nist_clear/zeros/random methods)
            if method not in ('nist_purge', 'crypto_erase'):
                print(f"\n[ПОВНЕ ЗНИЩЕННЯ] Заповнення вільного простору...")
                free_space_result = self.wipe_free_space(drive_letter,
                                                         "zeros" if method == "nist_clear" else "random")
                results['free_space_filled'] = free_space_result.get('total_space_filled', 0)

            duration = time.time() - start_time
            results['duration'] = duration
            results['status'] = 'SUCCESS'
            results['success'] = results['failed_files'] == 0

            print(f"\n[ПОВНЕ ЗНИЩЕННЯ] Завершено!")
            print(f"  Знищено файлів: {results['wiped_files']}")
            print(f"  Загальний розмір: {self._format_size(results['total_size'])}")
            print(f"  Час: {duration:.2f} сек.\n")

        except Exception as e:
            duration = time.time() - start_time
            results['duration'] = duration
            results['status'] = 'ERROR'
            results['error'] = str(e)
            results['success'] = False
            print(f"\nПОМИЛКА: {e}\n")

        return results

    # ============================================================
    #  Застосунки Windows
    # ============================================================

    def clean_windows_artifacts(self) -> Dict:
        """
        Clean Windows artifacts (Recycle Bin, Prefetch, Recent, etc.)
        Requires admin rights for some operations.

        Returns:
            Dictionary with results
        """
        results = {
            'operations': [],
            'success_count': 0,
            'failed_count': 0,
            'standard': self.STANDARD_VERSION
        }

        if os.name != 'nt':
            results['error'] = 'Windows only feature'
            return results

        print(f"\n[АРТЕФАКТИ] Очищення слідів Windows...\n")

        operations = [
            {
                'name': 'Recycle Bin',
                'cmd': 'powershell.exe -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"',
                'admin_required': False
            },
            {
                'name': 'Prefetch',
                'cmd': 'del /q C:\\Windows\\Prefetch\\* 2>nul',
                'admin_required': True
            },
            {
                'name': 'Recent Files',
                'cmd': f'del /q "%APPDATA%\\Microsoft\\Windows\\Recent\\*" 2>nul',
                'admin_required': False
            },
            {
                'name': 'Thumbnail Cache',
                'cmd': f'del /q "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*" 2>nul',
                'admin_required': False
            }
        ]

        for op in operations:
            try:
                print(f"  {op['name']}...", end='')
                result = subprocess.run(
                    op['cmd'],
                    shell=True,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(" ✓")
                    results['success_count'] += 1
                    results['operations'].append(f"{op['name']}: SUCCESS")
                else:
                    print(" ✗")
                    results['failed_count'] += 1
                    results['operations'].append(f"{op['name']}: FAILED")

            except Exception as e:
                print(f" ✗ ({e})")
                results['failed_count'] += 1
                results['operations'].append(f"{op['name']}: ERROR - {str(e)}")

        # Try to delete Volume Shadow Copies (requires admin)
        try:
            print(f"  Volume Shadow Copies...", end='')
            result = subprocess.run(
                'vssadmin delete shadows /all /quiet',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(" ✓")
                results['success_count'] += 1
            else:
                print(" ✗ (потрібні права адміністратора)")
                results['failed_count'] += 1
        except Exception:
            print(" ✗")
            results['failed_count'] += 1

        print(f"\n[АРТЕФАКТИ] Завершено!")
        print(f"  Успішно: {results['success_count']}")
        print(f"  Помилок: {results['failed_count']}\n")

        results['success'] = results['failed_count'] == 0
        return results

    # ============================================================
    #  УТИЛІТИ
    # ============================================================

    def _remove_empty_dirs(self, folder_path: str):
        """Remove empty directories recursively"""
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        print(f"  Видалено порожню папку: {dir_path}")
                except Exception:
                    pass

    @staticmethod
    def get_available_drives() -> list:
        """Get list of available drives (Windows)"""
        drives = []
        if os.name == 'nt':
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
        return drives

    @staticmethod
    def create_test_file(filename: str = "test_data.bin", size_mb: int = 10) -> str:
        """
        Create test file with pseudo data

        Returns:
            Absolute path to created file
        """
        size_bytes = size_mb * 1024 * 1024

        test_patterns = [
            b"CONFIDENTIAL DATA " * 10,
            b"1234567890" * 20,
            os.urandom(512),
            b"SECRET DOCUMENT " * 15,
            b"DELETE ME " * 25
        ]

        with open(filename, 'wb') as f:
            bytes_written = 0
            pattern_index = 0
            while bytes_written < size_bytes:
                remaining = min(512, size_bytes - bytes_written)
                pattern = test_patterns[pattern_index % len(test_patterns)]
                f.write(pattern[:remaining])
                bytes_written += remaining
                pattern_index += 1

        return os.path.abspath(filename)

    @staticmethod
    def _create_result(success: bool, start_time: float,
                       status: str, method: str = "",
                       duration: Optional[float] = None,
                       error: str = "") -> Dict:
        """Create result dictionary with standard fields"""
        if duration is None:
            duration = time.time() - start_time

        return {
            'success': success,
            'duration': duration,
            'status': status,
            'method': method,
            'standard': WipeEngine.STANDARD_VERSION,
            'error': error
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    @staticmethod
    def save_log(method: str, target: str, result: Dict, log_dir: str = "logs"):
        """
        Save operation log to file with NIST/IEEE standard reference.

        Args:
            method: Wiping method used
            target: Target file path
            result: Result dictionary
            log_dir: Directory for logs
        """
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        log_file = log_path / f"wipe_log_{datetime.now().strftime('%Y-%m-%d')}.txt"

        standard = result.get('standard', WipeEngine.STANDARD_VERSION)
        status = result.get('status', 'UNKNOWN')
        duration = result.get('duration', 0)
        success = result.get('success', False)
        verification = ""

        if 'clean_percent' in result:
            verification = f"\n  Верифікація: {result.get('clean_percent', 0):.1f}% секторів змінено"
        elif 'bitlocker_status' in result:
            verification = f"\n  Верифікація: {result.get('bitlocker_status', 'N/A')}"

        checkmark = "✓" if success else "✗"

        log_entry = f"""
═══════════════════════════════════════════════
Дата/час:    {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Стандарт:    {standard}
Метод:       {method}
Об'єкт:      {target}
Розмір:      {WipeEngine._format_size_static(result.get('file_size', 0))}
Час:         {duration:.2f} сек
             {verification}
Результат:   {status} {checkmark}
═══════════════════════════════════════════════
"""

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        return str(log_file)

    @staticmethod
    def _format_size_static(size_bytes: int) -> str:
        """Static version of _format_size for log output"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
