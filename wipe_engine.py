#!/usr/bin/env python3
"""
wipe_engine.py - Core wiping logic for SecureWipe Pro
Модуль з логікою безпечного знищення даних
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable


class WipeEngine:
    """Engine for secure data wiping operations"""
    
    def __init__(self, block_size: int = 512, progress_callback: Optional[Callable] = None):
        """
        Initialize wipe engine
        
        Args:
            block_size: Size of blocks for read/write operations
            progress_callback: Callback function for progress updates
        """
        self.block_size = block_size
        self.progress_callback = progress_callback
        self._cancelled = False
    
    def cancel(self):
        """Cancel current operation"""
        self._cancelled = True
    
    def _write_with_progress(self, file_handle, data: bytes, total_size: int, 
                            current_pass: int, total_passes: int, 
                            pass_description: str) -> bool:
        """
        Write data with progress reporting
        
        Returns:
            True if completed successfully, False if cancelled
        """
        bytes_written = 0
        
        while bytes_written < total_size:
            if self._cancelled:
                return False
            
            remaining = min(self.block_size, total_size - bytes_written)
            file_handle.write(data[:remaining])
            bytes_written += remaining
            
            if self.progress_callback:
                progress = (bytes_written / total_size) * 100
                self.progress_callback(
                    current_pass, total_passes, pass_description,
                    progress, bytes_written, total_size
                )
        
        return True
    
    def wipe_zeros(self, target_path: str) -> Dict:
        """
        Method 1: Overwrite with zeros (1 pass)
        
        Returns:
            Dictionary with operation results
        """
        return self._wipe_with_pattern(target_path, [(b'\x00' * self.block_size, "0x00")])
    
    def wipe_dod(self, target_path: str) -> Dict:
        """
        Method 2: DoD 5220.22-M (3 passes)
        Pass 1: 0x00, Pass 2: 0xFF, Pass 3: random
        
        Returns:
            Dictionary with operation results
        """
        return self._wipe_with_pattern(target_path, [
            (b'\x00' * self.block_size, "0x00"),
            (b'\xFF' * self.block_size, "0xFF"),
            (None, "random")
        ])
    
    def wipe_gutmann(self, target_path: str) -> Dict:
        """
        Method 3: Gutmann simplified (7 passes)
        Pattern: 0x00, 0xFF, random, 0xAA, 0x55, random, 0x00
        
        Returns:
            Dictionary with operation results
        """
        return self._wipe_with_pattern(target_path, [
            (b'\x00' * self.block_size, "0x00"),
            (b'\xFF' * self.block_size, "0xFF"),
            (None, "random"),
            (b'\xAA' * self.block_size, "0xAA"),
            (b'\x55' * self.block_size, "0x55"),
            (None, "random"),
            (b'\x00' * self.block_size, "0x00")
        ])
    
    def _wipe_with_pattern(self, target_path: str, passes: list) -> Dict:
        """
        Internal method to wipe with given pattern
        
        Args:
            target_path: Path to target file
            passes: List of tuples (data_pattern, description)
        
        Returns:
            Dictionary with results
        """
        self._cancelled = False
        start_time = time.time()
        
        try:
            file_size = os.path.getsize(target_path)
            total_passes = len(passes)
            
            for pass_num, (data, desc) in enumerate(passes, 1):
                if self._cancelled:
                    return self._create_result(False, start_time, "CANCELLED")
                
                with open(target_path, 'r+b') as f:
                    if data is None:
                        # Random data - need to generate on the fly
                        bytes_written = 0
                        while bytes_written < file_size:
                            if self._cancelled:
                                return self._create_result(False, start_time, "CANCELLED")
                            
                            remaining = min(self.block_size, file_size - bytes_written)
                            f.write(os.urandom(remaining))
                            bytes_written += remaining
                            
                            if self.progress_callback:
                                progress = (bytes_written / file_size) * 100
                                self.progress_callback(
                                    pass_num, total_passes, desc,
                                    progress, bytes_written, file_size
                                )
                    else:
                        success = self._write_with_progress(
                            f, data, file_size, pass_num, total_passes, desc
                        )
                        if not success:
                            return self._create_result(False, start_time, "CANCELLED")
            
            duration = time.time() - start_time
            return self._create_result(True, start_time, "SUCCESS", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'success': False,
                'duration': duration,
                'error': str(e),
                'status': 'ERROR'
            }
    
    def verify_wipe(self, target_path: str, method_name: str = "", file_size: int = 0) -> Dict:
        """
        Method 4: Verify wipe result
        Check if all bytes are zeros
        
        Args:
            target_path: Path to file
            method_name: Name of wiping method used
            file_size: Original file size (for display)
        
        Returns:
            Dictionary with verification results
        """
        self._cancelled = False
        start_time = time.time()
        
        try:
            if not file_size:
                file_size = os.path.getsize(target_path)
            zeros = b'\x00' * self.block_size
            
            total_blocks = 0
            clean_blocks = 0
            dirty_blocks = 0
            non_zero_bytes = 0
            
            print(f"\n[ВЕРИФІКАЦІЯ] Перевірка результату...")
            print(f"  Файл: {os.path.basename(target_path)}")
            print(f"  Розмір: {self._format_size(file_size)}")
            print(f"  Перевірено секторів: ", end='')
            
            with open(target_path, 'rb') as f:
                bytes_read = 0
                while bytes_read < file_size:
                    if self._cancelled:
                        return self._create_result(False, start_time, "CANCELLED")
                    
                    remaining = min(self.block_size, file_size - bytes_read)
                    data = f.read(remaining)
                    total_blocks += 1
                    
                    if data == zeros[:len(data)]:
                        clean_blocks += 1
                    else:
                        dirty_blocks += 1
                        non_zero_bytes += sum(1 for b in data if b != 0x00)
                    
                    bytes_read += len(data)
                    
                    if self.progress_callback:
                        progress = (bytes_read / file_size) * 100
                        self.progress_callback(
                            1, 1, "Verifying",
                            progress, bytes_read, file_size
                        )
            
            duration = time.time() - start_time
            
            clean_percent = (clean_blocks / total_blocks * 100) if total_blocks > 0 else 0
            success = dirty_blocks == 0
            
            # Print complete summary
            print(f"{total_blocks}")
            print(f"  Чистих секторів: {clean_blocks} ({clean_percent:.2f}%)")
            print(f"  Ненульових байт знайдено: {non_zero_bytes}")
            print(f"{'='*40}")
            
            if success:
                print(f"✓ ЗНИЩЕННЯ УСПІШНЕ")
                print(f"  Метод: {method_name}")
                print(f"  Файл: {os.path.basename(target_path)}")
                print(f"  Розмір: {self._format_size(file_size)}")
                print(f"  Час виконання: {duration:.2f} сек")
                print(f"  Надійність: {clean_percent:.2f}%")
            else:
                print(f"✗ УВАГА: ЗНИЩЕННЯ НЕПОВНЕ")
                print(f"  Знайдено відновлювані дані!")
                print(f"  Ненульових байтів: {non_zero_bytes}")
                print(f"  Надійність: {clean_percent:.2f}%")
                if clean_percent < 99.9:
                    print(f"  Рекомендується повторити операцію!")
            
            print(f"{'='*40}\n")
            
            return {
                'success': success,
                'duration': duration,
                'total_blocks': total_blocks,
                'clean_blocks': clean_blocks,
                'dirty_blocks': dirty_blocks,
                'clean_percent': clean_percent,
                'non_zero_bytes': non_zero_bytes,
                'file_size': file_size,
                'method_name': method_name,
                'status': 'SUCCESS' if success else 'FAILED'
            }
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"ПОМИЛКА: {e}")
            return {
                'success': False,
                'duration': duration,
                'error': str(e),
                'status': 'ERROR'
            }
    
    def create_test_file(self, filename: str = "test_data.bin", size_mb: int = 10) -> str:
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
                remaining = min(self.block_size, size_bytes - bytes_written)
                pattern = test_patterns[pattern_index % len(test_patterns)]
                f.write(pattern[:remaining])
                bytes_written += remaining
                pattern_index += 1
        
        return os.path.abspath(filename)
    
    def _create_result(self, success: bool, start_time: float, 
                      status: str, duration: Optional[float] = None) -> Dict:
        """Create result dictionary"""
        if duration is None:
            duration = time.time() - start_time
        
        return {
            'success': success,
            'duration': duration,
            'status': status
        }
    
    @staticmethod
    def save_log(method: str, target: str, result: Dict, log_dir: str = "logs"):
        """
        Save operation log to file
        
        Args:
            method: Wiping method used
            target: Target file path
            result: Result dictionary
            log_dir: Directory for logs
        """
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        log_file = log_path / f"wipe_log_{datetime.now().strftime('%Y-%m-%d')}.txt"
        
        log_entry = f"""
{'='*60}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Method: {method}
Target: {target}
Result: {result.get('status', 'UNKNOWN')}
Duration: {result.get('duration', 0):.2f} sec
{'='*60}
"""
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        return str(log_file)    
    def wipe_folder(self, folder_path: str, method: str = "dod") -> Dict:
        """
        Mode 2: Wipe all files in folder recursively
        
        Args:
            folder_path: Path to folder
            method: Wiping method (zeros, dod, gutmann)
        
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
            'errors': []
        }
        
        try:
            # Collect all files
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
            
            # Wipe each file
            for idx, file_path in enumerate(all_files, 1):
                if self._cancelled:
                    results['status'] = 'CANCELLED'
                    return results
                
                try:
                    file_size = os.path.getsize(file_path)
                    results['total_size'] += file_size
                    
                    print(f"Файл {idx} з {len(all_files)}: {os.path.basename(file_path)}")
                    
                    # Select wipe method
                    if method == "zeros":
                        wipe_func = self.wipe_zeros
                    elif method == "gutmann":
                        wipe_func = self.wipe_gutmann
                    else:  # dod
                        wipe_func = self.wipe_dod
                    
                    # Wipe file
                    wipe_result = wipe_func(file_path)
                    
                    if wipe_result.get('success'):
                        results['wiped_files'] += 1
                    else:
                        results['failed_files'] += 1
                        
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
            
            # Remove empty directories
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
    
    def wipe_free_space(self, drive_letter: str, method: str = "zeros") -> Dict:
        """
        Mode 3: Fill free disk space with temp files then delete them
        
        Args:
            drive_letter: Drive letter (e.g., "C:\", "D:\")
            method: Fill method (zeros or random)
        
        Returns:
            Dictionary with results
        """
        self._cancelled = False
        start_time = time.time()
        
        results = {
            'total_space_filled': 0,
            'temp_files_created': 0,
            'errors': []
        }
        
        try:
            import shutil
            
            # Get free space
            total, used, free = shutil.disk_usage(drive_letter)
            free_gb = free / (1024**3)
            
            print(f"\n[ВІЛЬНИЙ ПРОСТІР] Диск: {drive_letter}")
            print(f"  Вільно: {free_gb:.2f} GB")
            print(f"  Метод: {method}\n")
            
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
                        block = b'\x00' * self.block_size if method == "zeros" else os.urandom(self.block_size)
                        
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
                                    filled_gb = bytes_written / (1024**3)
                                    progress = (filled_gb / free_gb) * 100 if free_gb > 0 else 0
                                    self.progress_callback(
                                        int(filled_gb), int(free_gb), f"Filled {filled_gb:.1f} GB",
                                        progress, bytes_written, free
                                    )
                    
                    results['temp_files_created'] += 1
                    
                    # Update progress
                    filled_gb = bytes_written / (1024**3)
                    if self.progress_callback:
                        progress = (filled_gb / free_gb) * 100 if free_gb > 0 else 0
                        self.progress_callback(
                            int(filled_gb), int(free_gb), f"Filled {filled_gb:.1f} GB",
                            min(progress, 100), bytes_written, free
                        )
                    
                    print(f"Заповнено {filled_gb:.2f} GB з {free_gb:.2f} GB")
                    
                except OSError as e:
                    # Disk full - that's what we want
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
            except:
                pass
            
            duration = time.time() - start_time
            results['duration'] = duration
            results['total_space_filled'] = bytes_written
            results['status'] = 'SUCCESS'
            results['success'] = True
            
            filled_gb = bytes_written / (1024**3)
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
    
    def clean_windows_artifacts(self) -> Dict:
        """
        Clean Windows artifacts (Recycle Bin, Prefetch, Recent, etc.)
        Requires admin rights for some operations
        
        Returns:
            Dictionary with results
        """
        import subprocess
        
        results = {
            'operations': [],
            'success_count': 0,
            'failed_count': 0
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
                'cmd': 'del /q C:\\Windows\Prefetch\* 2>nul',
                'admin_required': True
            },
            {
                'name': 'Recent Files',
                'cmd': f'del /q "%APPDATA%\Microsoft\Windows\Recent\*" 2>nul',
                'admin_required': False
            },
            {
                'name': 'Thumbnail Cache',
                'cmd': f'del /q "%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_*" 2>nul',
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
        except:
            print(" ✗")
            results['failed_count'] += 1
        
        print(f"\n[АРТЕФАКТИ] Завершено!")
        print(f"  Успішно: {results['success_count']}")
        print(f"  Помилок: {results['failed_count']}\n")
        
        results['success'] = results['failed_count'] == 0
        return results
    
    def _remove_empty_dirs(self, folder_path: str):
        """Remove empty directories recursively"""
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):  # Check if empty
                        os.rmdir(dir_path)
                        print(f"  Видалено порожню папку: {dir_path}")
                except:
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
    def _format_size(size_bytes: int) -> str:
        """Format size to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

