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
    
    def verify_wipe(self, target_path: str) -> Dict:
        """
        Method 4: Verify wipe result
        Check if all bytes are zeros
        
        Returns:
            Dictionary with verification results
        """
        self._cancelled = False
        start_time = time.time()
        
        try:
            file_size = os.path.getsize(target_path)
            zeros = b'\x00' * self.block_size
            
            total_blocks = 0
            clean_blocks = 0
            dirty_blocks = 0
            non_zero_bytes = 0
            
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
            
            return {
                'success': success,
                'duration': duration,
                'total_blocks': total_blocks,
                'clean_blocks': clean_blocks,
                'dirty_blocks': dirty_blocks,
                'clean_percent': clean_percent,
                'non_zero_bytes': non_zero_bytes,
                'status': 'SUCCESS' if success else 'FAILED'
            }
            
        except Exception as e:
            duration = time.time() - start_time
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
