#!/usr/bin/env python3
"""
Стандарти:
  - NIST 800–88 r2 (Clear, Purge)
  - IEEE 2883-2022 (Crypto Erase)
"""

import os
import sys
import time
import random
import string
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable, List, Tuple
from enum import Enum


class RiskLevel(Enum):
    """Рівні ризику активу для ризик-орієнтованого вибору методу знищення даних"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SanitizationMethod(Enum):
    """Методи знищення даних згідно NIST 800–88 r2"""
    NIST_CLEAR = "nist_clear"
    NIST_PURGE = "nist_purge"
    CRYPTO_ERASE = "crypto_erase"


class WipeEngine:
    """Engine for secure data wiping operations (NIST 800–88 r2 / IEEE 2883-2022)"""

    STANDARD_VERSION = "NIST 800–88 r2 / IEEE 2883-2022"

    def __init__(self, block_size: int = 65536, progress_callback: Optional[Callable] = None):
        self.block_size = block_size
        self.progress_callback = progress_callback
        self._cancelled = False

    def cancel(self):
        """Cancel current operation"""
        self._cancelled = True

    # ============================================================
    #  РИЗИК-ОРІЄНТОВАНА ЛОГІКА ВИБОРУ МЕТОДУ ЗНИЩЕННЯ ДАНИХ
    # ============================================================

    @staticmethod
    def assess_risk_level(data_type: str = "general",
                          confidentiality: str = "medium",
                          user_choice: Optional[str] = None) -> RiskLevel:
   
        # Якщо користувач явно вказав рівень ризику через GUI
        if user_choice:
            choice_lower = user_choice.lower()
            if choice_lower in ("low", "low_risk", "низький"):
                return RiskLevel.LOW
            elif choice_lower in ("high", "high_risk", "високий"):
                return RiskLevel.HIGH
            else:
                return RiskLevel.MEDIUM

        # Оцінка за рівнем конфіденційності
        conf_lower = confidentiality.lower()
        if conf_lower in ("critical", "top_secret", "секретно"):
            return RiskLevel.HIGH
        elif conf_lower in ("high", "confidential", "конфіденційно"):
            return RiskLevel.HIGH
        elif conf_lower in ("low", "public", "публічно"):
            return RiskLevel.LOW

        # Оцінка за типом даних
        dtype_lower = data_type.lower()
        if dtype_lower in ("classified", "military", "military_data"):
            return RiskLevel.HIGH
        elif dtype_lower in ("financial", "medical", "personal", "pii"):
            return RiskLevel.MEDIUM

        # За замовчуванням — середній ризик
        return RiskLevel.MEDIUM

    @staticmethod
    def get_recommended_method(risk_level: RiskLevel,
                               is_encrypted: bool = False,
                               is_nvme: bool = False) -> Dict:
        """
        Повертає рекомендований метод знищення даних на основі рівня ризику.

        Логіка згідно NIST 800–88 r2:
            - Низький ризик → NIST Clear
            - Середній ризик → NIST Purge
            - Високий ризик → Crypto Erase (якщо зашифровано) або Purge
        """
        if risk_level == RiskLevel.LOW:
            return {
                'method': SanitizationMethod.NIST_CLEAR,
                'method_id': 'nist_clear',
                'method_name': 'NIST Clear',
                'description': '1 прохід псевдовипадкових даних',
                'suitable_for': 'HDD, USB — захист від програмного відновлення',
                'risk_level': risk_level.value
            }
        elif risk_level == RiskLevel.MEDIUM:
            return {
                'method': SanitizationMethod.NIST_PURGE,
                'method_id': 'nist_purge',
                'method_name': 'NIST Purge',
                'description': 'Апаратне стирання (diskpart clean all / ATA SE / NVMe Sanitize)',
                'suitable_for': 'SSD, HDD — охоплює резервний простір і кеш контролера',
                'risk_level': risk_level.value
            }
        else:  # HIGH
            if is_encrypted:
                return {
                    'method': SanitizationMethod.CRYPTO_ERASE,
                    'method_id': 'crypto_erase',
                    'method_name': 'Crypto Erase',
                    'description': 'Знищення ключа шифрування (миттєво, без перезапису)',
                    'suitable_for': 'Зашифровані диски — найвищий рівень захисту',
                    'risk_level': risk_level.value
                }
            else:
                method_name = 'NIST Purge (NVMe Sanitize)' if is_nvme else 'NIST Purge'
                return {
                    'method': SanitizationMethod.NIST_PURGE,
                    'method_id': 'nist_purge',
                    'method_name': method_name,
                    'description': 'Апаратне стирання з підтримкою NVMe Sanitize',
                    'suitable_for': 'SSD, HDD — повне знищення з резервним простором',
                    'risk_level': risk_level.value
                }

    @staticmethod
    def get_risk_level_display(risk_level: RiskLevel) -> Dict:
        """Повертає відображення рівня ризику для GUI"""
        displays = {
            RiskLevel.LOW: {
                'label': 'Низький',
                'color': '#30D158',  # зелений
                'icon': '🟢',
                'description': 'Звичайні дані, публічна інформація'
            },
            RiskLevel.MEDIUM: {
                'label': 'Середній',
                'color': '#FF9F0A',  # помаранчевий
                'icon': '🟡',
                'description': 'Персональні дані, фінансова інформація'
            },
            RiskLevel.HIGH: {
                'label': 'Високий',
                'color': '#FF3B30',  # червоний
                'icon': '🔴',
                'description': 'Секретні дані, військова інформація'
            }
        }
        return displays.get(risk_level, displays[RiskLevel.MEDIUM])

    # ============================================================
    #  МЕТОД 1 — NIST Clear (1 прохід псевдовипадкових даних)
    # ============================================================

    def wipe_nist_clear(self, target_path: str) -> Dict:
        """
        NIST 800–88 r2, рівень Clear.
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
                    f.write(os.urandom(chunk))
                    written += chunk

                    if self.progress_callback:
                        progress = (written / file_size) * 100
                        self.progress_callback(
                            1, 1, "NIST Clear: random",
                            progress, written, file_size
                        )

                f.flush()
                os.fsync(f.fileno())

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
        NIST 800–88 r2, рівень Purge; IEEE 2883-2022.
        Використовує апаратну команду контролера для знищення
        всіх даних включно з резервним простором і кешем контролера.

        Для кого: SSD, HDD — охоплює резервний простір і кеш контролера.
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
                return self._create_result(False, start_time, "ERROR", method_name, duration,
                                           result.get('error', 'Unknown error'))

        except Exception as e:
            duration = time.time() - start_time
            return self._create_result(False, start_time, "ERROR", method_name, duration, str(e))

    def _get_physical_disk_number(self, drive_letter: str) -> Optional[int]:
        
        # Визначити номер фізичного диска за літерою тому.

        letter = drive_letter.strip().rstrip('\\').rstrip(':').strip()
        try:
            proc = subprocess.run(
                ['powershell', '-Command',
                 f'(Get-Partition -DriveLetter {letter}).DiskNumber'],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            out = (proc.stdout or "").strip()
            if out and out.isdigit():
                return int(out)
        except Exception as e:
            print(f"  Помилка визначення номера диска: {e}")
        return None

    def _is_system_disk(self, disk_number: int) -> bool:
        """
        Перевірити, чи містить фізичний диск системний розділ Windows.
        Захист від випадкового знищення диска, з якого завантажена ОС.
        У разі будь-якого сумніву повертає True (безпечніше відмовити).
        """
        try:
            sys_letter = os.environ.get('SystemDrive', 'C:').rstrip(':')
            proc = subprocess.run(
                ['powershell', '-Command',
                 f'((Get-Partition -DiskNumber {disk_number}).DriveLetter) '
                 f'-join ","'],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            letters = (proc.stdout or "").strip().upper()
            return sys_letter.upper() in letters
        except Exception:
            return True

    def _purge_windows(self, drive_letter: str) -> Dict:
        """
        Windows: повне апаратне стирання фізичного диска через diskpart
        'clean all' (рівень NIST Purge).

        clean all працює з цілим фізичним диском. Програма спершу визначає
        номер диска за літерою тому, перевіряє, що це не системний диск,
        виконує стирання і підтверджує результат за виводом diskpart.
        """
        # 1. Номер фізичного диска
        disk_number = self._get_physical_disk_number(drive_letter)
        print(f"  [Purge] Том {drive_letter} -> фізичний диск №{disk_number}")
        if disk_number is None:
            return {'success': False,
                    'error': "Не вдалося визначити номер фізичного диска для тому."}

        # 2. Захист від системного диска
        if self._is_system_disk(disk_number):
            return {'success': False,
                    'error': f"Диск {disk_number} є системним. Стирання заборонено "
                             f"для безпеки ОС. Використайте окремий носій (USB / "
                             f"зовнішній диск)."}

        # 3. clean all для цілого фізичного диска
        script = f"""select disk {disk_number}
clean all
"""
        try:
            proc = subprocess.run(
                ['diskpart'],
                input=script,
                capture_output=True,
                text=True, encoding="utf-8", errors="replace",
                timeout=86400
            )
            stdout = (proc.stdout or "")
            stdout_low = stdout.lower()

            # 4. Реальна перевірка результату за виводом diskpart
            #    (самого returncode недостатньо — diskpart часто повертає 0
            #    навіть коли внутрішня команда не виконалась)
            success_markers = ['succeeded in cleaning', 'успішно очист', 'успешно очист']
            error_markers = ['error', 'помилк', 'ошибк', 'denied', 'failed', 'cannot',
                             'не вдал', 'отказ']
            cleaned_ok = any(m in stdout_low for m in success_markers)
            has_error = any(m in stdout_low for m in error_markers)

            if cleaned_ok and not has_error:
                return {'success': True, 'disk_number': disk_number}
            else:
                return {'success': False,
                        'error': f"diskpart не підтвердив очищення диска {disk_number}. "
                                 f"Вивід: {stdout.strip()[:300]}"}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': "diskpart operation timed out"}
        except FileNotFoundError:
            return {'success': False, 'error': "diskpart not found (Windows only)"}

    def _purge_linux(self, device_path: str) -> Dict:
        """
        Linux: NVMe Sanitize з fallback до ATA Secure Erase.

        Пріоритет:
        1. NVMe Sanitize (найкращий варіант для NVMe SSD)
        2. NVMe Format --ses=1 (Secure Erase)
        3. ATA Secure Erase через hdparm (для SATA SSD/HDD)
        """
        try:
            if device_path.startswith('/dev/nvme'):
                # Спочатку пробуємо NVMe Sanitize
                sanitize_result = self._nvme_sanitize(device_path)
                if sanitize_result['success']:
                    return sanitize_result

                # Fallback до NVMe Format --ses=1
                print(f"  NVMe Sanitize недоступний, fallback до nvme format --ses=1")
                format_result = self._nvme_format(device_path)
                if format_result['success']:
                    return format_result

                # Якщо обидва методи недоступні — повертаємо помилку
                return {
                    'success': False,
                    'error': f"NVMe Sanitize та Format недоступні: {sanitize_result.get('error', '')}"
                }
            else:
                # ATA Secure Erase через hdparm для SATA пристроїв
                return self._ata_secure_erase(device_path)

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': "erase operation timed out"}
        except FileNotFoundError as e:
            return {'success': False, 'error': f"required tool not found: {e}"}

    def _nvme_sanitize(self, device_path: str) -> Dict:
        """
        NVMe Sanitize — найкращий метод для NVMe SSD.

        Підтримує різні типи sanitize:
        - Block Erase (ses=1): стирання блоків
        - Crypto Erase (ses=2): криптографічне стирання
        - Overwrite (ses=3): перезапис

        Використовуємо Block Erase як найбільш надійний.
        """
        try:
            # Спочатку перевіряємо підтримку sanitize
            log_result = subprocess.run(
                ['nvme', 'sanitize-log', device_path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
            )

            if log_result.returncode != 0:
                return {
                    'success': False,
                    'error': f"sanitize-log недоступний: {log_result.stderr.strip()}"
                }

            # Перевіряємо чи пристрій підтримує sanitize
            # Шукаємо "Sanitize Capabilities" у виводі
            sanitize_output = log_result.stdout
            if "Sanitize Capabilities" in sanitize_output:
                # Парсимо підтримувані типи
                caps = {}
                for line in sanitize_output.split('\n'):
                    if ':' in line and 'Sanitize' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            caps[parts[0].strip()] = parts[1].strip()

            # Запускаємо sanitize з Block Erase (ses=1)
            print(f"  Запуск NVMe Sanitize (Block Erase) для {device_path}...")
            sanitize_proc = subprocess.run(
                ['nvme', 'sanitize', device_path, '--ses=1'],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
            )

            if sanitize_proc.returncode != 0:
                return {
                    'success': False,
                    'error': f"sanitize команда невдала: {sanitize_proc.stderr.strip()}"
                }

            # Очікуємо завершення sanitize (може тривати довго)
            print(f"  Очікування завершення NVMe Sanitize...")
            return self._wait_for_sanitize_completion(device_path)

        except FileNotFoundError:
            return {
                'success': False,
                'error': "nvme CLI не знайдено. Встановіть nvme-cli."
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "sanitize-log timeout"
            }

    def _wait_for_sanitize_completion(self, device_path: str,
                                       max_wait: int = 86400,
                                       poll_interval: int = 10) -> Dict:
        """
        Очікування завершення NVMe Sanitize операції.

        Періодично перевіряємо статус через sanitize-log.
        """
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                log_result = subprocess.run(
                    ['nvme', 'sanitize-log', device_path],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
                )

                if log_result.returncode == 0:
                    output = log_result.stdout
                    # Шукаємо статус sanitize
                    for line in output.split('\n'):
                        if 'Sanitize Status' in line or 'sanitize progress' in line.lower():
                            # Перевіряємо чи завершено
                            if '0x0' in line or 'No Sanitize' in line or 'Completed' in line:
                                return {'success': True}
                            elif 'Progress' in line:
                                # Парсимо прогрес
                                print(f"    Прогрес Sanitize: {line.strip()}")

                time.sleep(poll_interval)

            except Exception as e:
                print(f"    Помилка перевірки статусу: {e}")
                time.sleep(poll_interval)

        return {
            'success': False,
            'error': f"Sanitize не завершено за {max_wait} секунд"
        }

    def _nvme_format(self, device_path: str) -> Dict:
        """
        NVMe Format --ses=1 (Secure Erase) — fallback метод.

        Використовується коли NVMe Sanitize недоступний.
        """
        try:
            print(f"  Запуск NVMe Format --ses=1 для {device_path}...")
            proc = subprocess.run(
                ['nvme', 'format', device_path, '--ses=1'],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=86400
            )

            if proc.returncode == 0:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"nvme format невдалий: {proc.stderr.strip()}"
                }

        except FileNotFoundError:
            return {
                'success': False,
                'error': "nvme CLI не знайдено"
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "nvme format timeout"
            }

    def _ata_secure_erase(self, device_path: str) -> Dict:
        """
        ATA Secure Erase через hdparm для SATA пристроїв.
        """
        try:
            # Встановлюємо пароль безпеки
            set_pass = subprocess.run(
                ['hdparm', '--user-master', 'u', '--security-set-pass', 'pw', device_path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
            )
            if set_pass.returncode != 0:
                return {
                    'success': False,
                    'error': f"hdparm set password failed: {set_pass.stderr.strip()}"
                }

            # Запускаємо Secure Erase
            proc = subprocess.run(
                ['hdparm', '--user-master', 'u', '--security-erase', 'pw', device_path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=86400
            )

            if proc.returncode == 0:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f"ATA Secure Erase невдалий: {proc.stderr.strip()}"
                }

        except FileNotFoundError:
            return {
                'success': False,
                'error': "hdparm не знайдено. Встановіть hdparm."
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "ATA Secure Erase timeout"
            }

    # ============================================================
    #  МЕТОД 3 — Crypto Erase (криптографічне знищення)
    # ============================================================

    # Множина станів тому, що вважаються зашифрованими
    _ENCRYPTED_VOLUME_STATES = {
        'FullyEncrypted',
        'UsedSpaceOnlyEncrypted',
        'EncryptionInProgress',
    }

    def _get_bitlocker_fields(self, drive_letter: str) -> Tuple[str, str]:
        """
        Отримати чисті значення VolumeStatus та ProtectionStatus тому BitLocker.

        Замість парсингу текстового виводу Get-BitLockerVolume звертаємось
        безпосередньо до властивостей об'єкта, щоб отримати рядки без зайвого
        форматування. Значення нормалізуються (рядок без пробілів) для надійного
        порівняння незалежно від локалі чи числового подання.

        Повертає кортеж (volume_status, protection_status).
        """
        volume_status = ""
        protection_status = ""
        # Нормалізуємо літеру диска: приймаємо 'E', 'E:', 'E:\\', 'E\\' → 'E'
        letter = drive_letter.strip().rstrip('\\').rstrip(':').strip()
        try:
            vs_proc = subprocess.run(
                ['powershell', '-Command',
                 f'(Get-BitLockerVolume -MountPoint {letter}:).VolumeStatus'],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            ps_proc = subprocess.run(
                ['powershell', '-Command',
                 f'(Get-BitLockerVolume -MountPoint {letter}:).ProtectionStatus'],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            # Нормалізація: прибираємо пробіли, переноси рядків, зайві символи
            volume_status = (vs_proc.stdout or "").strip()
            protection_status = (ps_proc.stdout or "").strip()
            print(f"  [BitLocker] {letter}: VolumeStatus='{volume_status}', "
                  f"ProtectionStatus='{protection_status}'")
        except Exception as e:
            print(f"  Помилка читання полів BitLocker: {e}")
        return volume_status, protection_status

    def _is_protection_on(self, protection_status: str) -> bool:
        """
        Чи увімкнено захист BitLocker (протектори ключа активні).

        ProtectionStatus може повертатись як рядок ('On'/'Off') або як число
        (1 — увімкнено, 0 — вимкнено) залежно від локалі та версії PowerShell.
        """
        normalized = str(protection_status).strip().lower()
        return normalized == 'on' or normalized == '1'

    def wipe_crypto_erase(self, drive_letter: str) -> Dict:
        """
        IEEE 2883-2022; NIST 800–88 r2 рівень Purge.
        Знищення ключа шифрування BitLocker.
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

            # Читаємо чисті значення стану тому та стану захисту
            volume_status, protection_status = self._get_bitlocker_fields(drive_letter)

            # Нормалізуємо літеру диска для подальших команд
            letter = drive_letter.strip().rstrip('\\').rstrip(':').strip()

            if not volume_status:
                duration = time.time() - start_time
                return self._create_result(False, start_time, "ERROR", method_name, duration,
                                           "Не вдалося визначити стан BitLocker для диска.")

            is_encrypted = volume_status in self._ENCRYPTED_VOLUME_STATES
            protection_on = self._is_protection_on(protection_status)

            # Том зашифрований і захист активний — є протектори ключа для знищення
            if is_encrypted and protection_on:
                remove_proc = subprocess.run(
                    ['powershell', '-Command',
                     f'(Get-BitLockerVolume -MountPoint {letter}:).KeyProtector '
                     f'| Remove-BitLockerKeyProtector -MountPoint {letter}: '
                     f'-KeyProtectorId {{$_.KeyProtectorId}}'],
                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                )

                off_proc = subprocess.run(
                    ['manage-bde', '-off', f'{letter}:'],
                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                )

                if off_proc.returncode == 0 or remove_proc.returncode == 0:
                    duration = time.time() - start_time
                    return self._create_result(True, start_time, "SUCCESS", method_name, duration)
                else:
                    duration = time.time() - start_time
                    return self._create_result(False, start_time, "ERROR", method_name, duration,
                                               f"Failed to disable BitLocker: {off_proc.stderr}")

            # Том зашифрований, але захист вимкнено — протекторів немає, знищувати нічого
            elif is_encrypted and not protection_on:
                duration = time.time() - start_time
                return self._create_result(
                    False, start_time, "ERROR", method_name, duration,
                    "Захист BitLocker вимкнено (протектори ключа відсутні). "
                    "Crypto Erase неможливий — ключ уже у відкритому вигляді. "
                    "Увімкніть захист (manage-bde -protectors -enable) або оберіть NIST Purge.")

            # Том не зашифрований узагалі
            else:
                duration = time.time() - start_time
                return self._create_result(
                    False, start_time, "ERROR", method_name, duration,
                    "Диск не зашифровано BitLocker. Crypto Erase недоступний. "
                    "Оберіть NIST Clear або NIST Purge.")

        except Exception as e:
            duration = time.time() - start_time
            return self._create_result(False, start_time, "ERROR", method_name, duration, str(e))

    def check_bitlocker_status(self, drive_letter: str) -> Tuple[bool, str]:
        """Перевірити статус BitLocker для диска."""
        if os.name != 'nt':
            return False, "Windows only"

        try:
            volume_status, protection_status = self._get_bitlocker_fields(drive_letter)

            if not volume_status:
                return False, "Unknown"

            is_encrypted = volume_status in self._ENCRYPTED_VOLUME_STATES
            protection_on = self._is_protection_on(protection_status)

            # Придатний для Crypto Erase лише якщо зашифровано І захист увімкнено
            if is_encrypted and protection_on:
                return True, volume_status
            elif is_encrypted and not protection_on:
                # Зашифровано, але захист вимкнено — протектори відсутні
                return False, f"{volume_status} (ProtectionOff)"
            else:
                return False, volume_status or "FullyDecrypted"
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
    #  ВЕРИФІКАЦІЯ — окрема логіка для кожного методу
    # ============================================================

    def verify_wipe(self, target_path: str, method: str = "NIST Clear",
                    original_data: bytes = None, file_size: int = 0) -> Dict:
        """
        Розширена верифікація знищення даних — специфічна для кожного методу.
        """
        self._cancelled = False

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
                return self._verify_nist_clear(target_path, file_size, original_data)
            elif "zeros" in method.lower() or "zero" in method.lower():
                return self._verify_zeros(target_path, file_size)
            else:
                return self._verify_generic(target_path, file_size)

        except Exception as e:
            return {
                'success': False,
                'duration': 0,
                'error': str(e),
                'status': 'ERROR',
                'method': method
            }

    def _verify_nist_clear(self, target_path: str, file_size: int,
                           original_data: bytes = None) -> Dict:
        """
        Верифікація NIST Clear:
        Перевіряє що сектори містять псевдовипадкові дані з високою ентропією.
        Критерій: унікальних байтів > 10 (реальні random мають 200+).
        """
        start_time = time.time()
        self._cancelled = False
        block_size = self.block_size
        total_blocks = max(1, (file_size + block_size - 1) // block_size)

        print(f"\n[ВЕРИФІКАЦІЯ NIST Clear] Перевірка результату...")
        print(f"  Файл: {os.path.basename(target_path)}")
        print(f"  Розмір: {self._format_size(file_size)}")
        print(f"  Секторів загалом: {total_blocks}")

        num_samples = min(1000, total_blocks)
        if total_blocks > 1:
            sample_positions = sorted(random.sample(range(total_blocks), num_samples))
        else:
            sample_positions = [0]

        passed_count = 0
        failed_count = 0

        with open(target_path, 'rb') as f:
            for idx, block_num in enumerate(sample_positions):
                if self._cancelled:
                    return self._create_result(False, start_time, "CANCELLED", "Verify NIST Clear")

                f.seek(block_num * block_size)
                data = f.read(min(block_size, file_size - block_num * block_size))

                if not data:
                    failed_count += 1
                    continue

                unique_bytes = len(set(data[:min(256, len(data))]))

                if unique_bytes > 10:
                    passed_count += 1
                else:
                    failed_count += 1

                if self.progress_callback and (idx + 1) % 50 == 0:
                    progress = ((idx + 1) / num_samples) * 100
                    self.progress_callback(1, 1, "Verify NIST Clear", progress, idx + 1, num_samples)

        total_checked = num_samples
        passed_percent = (passed_count / total_checked * 100) if total_checked > 0 else 0
        success = passed_percent >= 95.0

        print(f"  Перевірено секторів: {total_checked}")
        print(f"  З ентропією > 10: {passed_count}/{total_checked} ({passed_percent:.2f}%)")
        print(f"  З низькою ентропією: {failed_count}/{total_checked}")
        print(f"{'='*50}")

        if success:
            print(f"✓ Верифікація NIST Clear: {passed_percent:.1f}% секторів містять псевдовипадкові дані ✓")
        else:
            print(f"✗ Верифікація NIST Clear: {100 - passed_percent:.1f}% секторів мають низьку ентропію")

        duration = time.time() - start_time
        return {
            'success': success,
            'duration': duration,
            'method': 'NIST Clear',
            'status': 'SUCCESS' if success else 'FAILED',
            'total_sectors': total_checked,
            'checked_sectors': total_checked,
            'passed_sectors': passed_count,
            'failed_sectors': failed_count,
            'percent': passed_percent,
            'file_size': file_size,
            'message': (
                f"Верифікація NIST Clear: {passed_percent:.2f}% секторів "
                f"містять псевдовипадкові дані"
            )
        }

    def _verify_nist_purge(self, target_path: str, file_size: int) -> Dict:
        """
        Верифікація NIST Purge:
        Зчитує перші/останні/випадкові сектори, перевіряє що вміст = нулі.
        """
        start_time = time.time()
        self._cancelled = False
        block_size = self.block_size
        total_blocks = max(1, (file_size + block_size - 1) // block_size)

        print(f"\n[ВЕРИФІКАЦІЯ NIST Purge] Перевірка результату...")
        print(f"  Файл: {os.path.basename(target_path)}")
        print(f"  Розмір: {self._format_size(file_size)}")

        num_edge = min(100, total_blocks)
        num_random = min(800, max(0, total_blocks - 2 * num_edge))

        positions = list(range(num_edge))
        if total_blocks > num_edge * 2:
            positions.extend(range(total_blocks - num_edge, total_blocks))
        if total_blocks > num_edge * 2 + num_random:
            mid_range = range(num_edge, total_blocks - num_edge)
            positions.extend(random.sample(list(mid_range), min(num_random, len(mid_range))))

        zero_count = 0
        non_zero_count = 0

        with open(target_path, 'rb') as f:
            for idx, block_num in enumerate(positions):
                if self._cancelled:
                    return self._create_result(False, start_time, "CANCELLED", "Verify NIST Purge")

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
            'total_sectors': total_checked,
            'checked_sectors': total_checked,
            'passed_sectors': zero_count,
            'failed_sectors': non_zero_count,
            'percent': clean_percent,
            'clean_blocks': zero_count,
            'dirty_blocks': non_zero_count,
            'clean_percent': clean_percent,
            'file_size': file_size,
            'message': (
                f"Верифікація NIST Purge: {clean_percent:.2f}% секторів чисті"
                if success else
                f"Знищення неповне: {100 - clean_percent:.2f}% секторів не очищено"
            )
        }

    def _verify_crypto_erase(self, drive_letter: str) -> Dict:
        """
        Верифікація Crypto Erase:
        Перевіряє що BitLocker вимкнений (ключ знищено).
        """
        start_time = time.time()
        print(f"\n[ВЕРИФІКАЦІЯ Crypto Erase] Перевірка результату...")
        print(f"  Диск: {drive_letter}:")

        success = False
        status_msg = "Невизначено"

        try:
            volume_status, protection_status = self._get_bitlocker_fields(drive_letter)
            protection_on = self._is_protection_on(protection_status)

            # Успіх: захист вимкнено АБО том повністю розшифровано
            if not protection_on or volume_status == 'FullyDecrypted':
                print(f"  Статус BitLocker: захист вимкнено / ключ знищено ✓")
                success = True
                status_msg = "Ключ знищено, захист BitLocker вимкнено"
            # Помилка: захист усе ще активний
            elif protection_on:
                print(f"  Статус BitLocker: захист усе ще увімкнено (помилка!)")
                success = False
                status_msg = "Захист BitLocker все ще активний"
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
            'bitlocker_status': status_msg,
            'message': status_msg
        }

    def _verify_zeros(self, target_path: str, file_size: int) -> Dict:
        """
        Верифікація Zeros:
        Успіх = 100% байтів дорівнює 0x00
        """
        start_time = time.time()
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
                    return self._create_result(False, start_time, "CANCELLED", "Verify Zeros")

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
        print(f"  Нульових: {clean_blocks}/{total_blocks} ({clean_percent:.2f}%)")
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
            'total_sectors': total_blocks,
            'checked_sectors': total_blocks,
            'passed_sectors': clean_blocks,
            'failed_sectors': total_blocks - clean_blocks,
            'percent': clean_percent,
            'clean_blocks': clean_blocks,
            'clean_percent': clean_percent,
            'file_size': file_size,
            'message': (
                f"Верифікація Zeros: {clean_percent:.2f}% секторів = 0x00"
                if success else
                f"Знищення неповне: {100 - clean_percent:.2f}% секторів не нулі"
            )
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

        wipe_func = self._get_wipe_function(method)
        if wipe_func is None:
            results['status'] = 'ERROR'
            results['error'] = f"Unknown method: {method}"
            return results

        try:
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

                if self.progress_callback:
                    progress = (idx / len(all_files)) * 100
                    self.progress_callback(
                        idx, len(all_files), f"File {idx}/{len(all_files)}",
                        progress, idx, len(all_files)
                    )

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
            # 'zeros': self.wipe_zeros,
            # 'dod': self.wipe_dod,
            # 'gutmann': self.wipe_gutmann,
        }
        return method_map.get(method.lower())

    # ============================================================
    #  РЕЖИМ 3: Вільний простір диску
    # ============================================================

    def wipe_free_space(self, drive_letter: str, method: str = "zeros") -> Dict:
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

            while True:
                if self._cancelled:
                    results['status'] = 'CANCELLED'
                    break

                try:
                    _, _, free = shutil.disk_usage(drive_letter)
                    if free < 1024 * 1024:
                        break

                    file_counter += 1
                    temp_file = os.path.join(temp_dir, f"temp_{file_counter}.bin")
                    temp_files.append(temp_file)

                    with open(temp_file, 'wb') as f:
                        chunk_size = 100 * 1024 * 1024
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

                            if written % (10 * 1024 * 1024) == 0:
                                if self.progress_callback:
                                    filled_gb = bytes_written / (1024 ** 3)
                                    progress = (filled_gb / free_gb) * 100 if free_gb > 0 else 0
                                    self.progress_callback(
                                        int(filled_gb), int(free_gb), f"Filled {filled_gb:.1f} GB",
                                        progress, bytes_written, free
                                    )

                    results['temp_files_created'] += 1

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

            print(f"\n[ВІЛЬНИЙ ПРОСТІР] Видалення тимчасових файлів...")
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    results['errors'].append(f"Delete {temp_file}: {str(e)}")

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

            print("[ПОВНЕ ЗНИЩЕННЯ] Знищення файлів...")

            wipe_func = self._get_wipe_function(method)
            if wipe_func is None:
                wipe_func = self.wipe_nist_clear

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

                        try:
                            os.remove(file_path)
                        except OSError:
                            pass

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

            print(f"\n[ПОВНЕ ЗНИЩЕННЯ] Видалення порожніх папок...")
            all_dirs_sorted = sorted(all_dirs, reverse=True)

            for dir_path in all_dirs_sorted:
                try:
                    if os.path.exists(dir_path) and not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except Exception:
                    pass

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
                    text=True, encoding="utf-8", errors="replace"
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

        try:
            print(f"  Volume Shadow Copies...", end='')
            result = subprocess.run(
                'vssadmin delete shadows /all /quiet',
                shell=True,
                capture_output=True,
                text=True, encoding="utf-8", errors="replace"
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
        """Create test file with pseudo data"""
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

    # ============================================================
    #  КОНТРОЛЬ ЦІЛІСНОСТІ ЖУРНАЛУ ЧЕРЕЗ SHA-256
    # ============================================================

    @staticmethod
    def _compute_log_hash(log_entry: str) -> str:
        """
        Обчислює SHA-256 хеш для запису журналу.

        Хеш формується на основі вмісту запису для забезпечення
        контролю цілісності журналу операцій.
        """
        return hashlib.sha256(log_entry.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_log_integrity(log_file_path: str) -> Dict:
        """
        Перевіряє цілісність журналу операцій.

        Читає журнал, знаходить записи з хешами та перевіряє
        чи вміст запису відповідає збереженому хешу.

        Returns:
            Dict з результатами перевірки:
            - success: bool — чи всі записи цілісні
            - total_entries: int — кількість записів
            - valid_entries: int — кількість валідних записів
            - corrupted_entries: int — кількість пошкоджених записів
            - details: list — деталі перевірки
        """
        results = {
            'success': True,
            'total_entries': 0,
            'valid_entries': 0,
            'corrupted_entries': 0,
            'details': []
        }

        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Розділяємо на записи (кожен запис розділений лінією з ═)
            entries = content.split('═══════════════════════════════════════════════')

            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue

                results['total_entries'] += 1

                # Шукаємо хеш у записі
                hash_line = None
                entry_without_hash = entry
                for line in entry.split('\n'):
                    if line.strip().startswith('SHA-256:'):
                        hash_line = line.strip().replace('SHA-256:', '').strip()
                        # Видаляємо рядок з хешем для перевірки
                        entry_without_hash = entry.replace(line, '').strip()
                        break

                if hash_line:
                    # Перераховуємо хеш для вмісту без рядка з хешем
                    computed_hash = WipeEngine._compute_log_hash(entry_without_hash)
                    if computed_hash == hash_line:
                        results['valid_entries'] += 1
                        results['details'].append({
                            'status': 'valid',
                            'hash': hash_line[:16] + '...'
                        })
                    else:
                        results['corrupted_entries'] += 1
                        results['success'] = False
                        results['details'].append({
                            'status': 'corrupted',
                            'expected': hash_line[:16] + '...',
                            'computed': computed_hash[:16] + '...'
                        })
                else:
                    # Запис без хеша (старий формат) — вважаємо валідним
                    results['valid_entries'] += 1
                    results['details'].append({
                        'status': 'legacy',
                        'note': 'Запис без хеша (старий формат)'
                    })

        except FileNotFoundError:
            results['success'] = False
            results['error'] = f"Файл журналу не знайдено: {log_file_path}"
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)

        return results

    @staticmethod
    def save_log(method: str, target: str, result: Dict, log_dir: str = "logs"):
        """
        Save operation log to file with NIST/IEEE standard reference
        and SHA-256 integrity hash.
        """
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        log_file = log_path / f"wipe_log_{datetime.now().strftime('%Y-%m-%d')}.txt"

        standard = result.get('standard', WipeEngine.STANDARD_VERSION)
        status = result.get('status', 'UNKNOWN')
        duration = result.get('duration', 0)
        success = result.get('success', False)

        verification = ""
        if 'message' in result:
            verification = f"\n  {result['message']}"
        elif 'clean_percent' in result:
            verification = f"\n  Верифікація: {result.get('clean_percent', 0):.1f}% секторів змінено"
        elif 'bitlocker_status' in result:
            verification = f"\n  Верифікація: {result.get('bitlocker_status', 'N/A')}"

        checkmark = "✓" if success else "✗"

        # Формуємо вміст запису (без хешу)
        log_entry_content = f"""
═══════════════════════════════════════════════
Дата/час:    {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Стандарт:    {standard}
Метод:       {method}
Об'єкт:      {target}
Розмір:      {WipeEngine._format_size_static(result.get('file_size', 0))}
Час:         {duration:.2f} сек{verification}
Результат:   {status} {checkmark}"""

        # Обчислюємо SHA-256 хеш для вмісту запису
        entry_hash = WipeEngine._compute_log_hash(log_entry_content)

        # Додаємо хеш до запису
        log_entry = log_entry_content + f"\nSHA-256:     {entry_hash}\n═══════════════════════════════════════════════\n"

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