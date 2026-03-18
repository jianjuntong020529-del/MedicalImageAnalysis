# -*- coding: utf-8 -*-
# @Time    : 2024/12/24
# @Author  : Kiro AI Assistant
"""
临时文件管理器
管理NPY数据转换过程中生成的临时DICOM文件
"""

import os
import shutil
import tempfile
import uuid
from typing import Optional
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TempFileManager:
    """临时文件管理器"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化临时文件管理器
        
        Args:
            base_dir: 基础目录，如果为None则使用系统临时目录
        """
        self.base_dir = base_dir or tempfile.gettempdir()
        self.current_temp_dir: Optional[str] = None
        self._created_dirs = []  # 跟踪创建的目录
        
        logger.debug(f"TempFileManager initialized with base_dir: {self.base_dir}")
    
    def create_temp_dir(self, prefix: str = "npy_dicom_") -> str:
        """
        创建临时目录
        
        Args:
            prefix: 目录名前缀
            
        Returns:
            str: 创建的临时目录路径
            
        Raises:
            OSError: 当目录创建失败时
        """
        try:
            # 生成唯一的目录名
            unique_id = str(uuid.uuid4())[:8]
            dir_name = f"{prefix}{unique_id}"
            temp_dir_path = os.path.join(self.base_dir, dir_name)
            
            # 创建目录
            os.makedirs(temp_dir_path, exist_ok=True)
            
            # 更新当前临时目录
            self.current_temp_dir = temp_dir_path
            self._created_dirs.append(temp_dir_path)
            
            logger.info(f"Created temporary directory: {temp_dir_path}")
            return temp_dir_path
            
        except Exception as e:
            logger.error(f"Failed to create temporary directory: {e}")
            raise OSError(f"Failed to create temporary directory: {e}")
    
    def cleanup_current(self, ignore_errors=False):
        """
        清理当前临时目录
        
        Args:
            ignore_errors: 如果为True，忽略清理错误（用于Windows文件锁定情况）
        """
        if self.current_temp_dir and os.path.exists(self.current_temp_dir):
            try:
                shutil.rmtree(self.current_temp_dir, ignore_errors=ignore_errors)
                logger.info(f"Cleaned up temporary directory: {self.current_temp_dir}")
                
                # 从跟踪列表中移除
                if self.current_temp_dir in self._created_dirs:
                    self._created_dirs.remove(self.current_temp_dir)
                    
                self.current_temp_dir = None
                
            except Exception as e:
                if ignore_errors:
                    logger.warning(f"Failed to cleanup directory {self.current_temp_dir}: {e}")
                    # 标记为待清理，但不抛出异常
                    self.current_temp_dir = None
                else:
                    logger.error(f"Failed to cleanup temporary directory {self.current_temp_dir}: {e}")
                    raise OSError(f"Failed to cleanup temporary directory: {e}")
    
    def cleanup_all(self, ignore_errors=False):
        """
        清理所有创建的临时目录
        
        Args:
            ignore_errors: 如果为True，忽略清理错误（用于Windows文件锁定情况）
        """
        cleanup_errors = []
        
        for temp_dir in self._created_dirs.copy():
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=ignore_errors)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                self._created_dirs.remove(temp_dir)
                
            except Exception as e:
                error_msg = f"Failed to cleanup directory {temp_dir}: {e}"
                if ignore_errors:
                    logger.warning(error_msg)
                else:
                    logger.error(error_msg)
                    cleanup_errors.append(error_msg)
        
        # 重置当前目录
        self.current_temp_dir = None
        
        if cleanup_errors and not ignore_errors:
            raise OSError(f"Some cleanup operations failed: {'; '.join(cleanup_errors)}")
        
        if not cleanup_errors:
            logger.info("All temporary directories cleaned up successfully")
        else:
            logger.warning(f"Cleanup completed with {len(cleanup_errors)} warnings")
    
    def get_current_temp_dir(self) -> Optional[str]:
        """
        获取当前临时目录路径
        
        Returns:
            Optional[str]: 当前临时目录路径，如果没有则返回None
        """
        return self.current_temp_dir
    
    def is_temp_dir_exists(self) -> bool:
        """
        检查当前临时目录是否存在
        
        Returns:
            bool: 临时目录是否存在
        """
        return (self.current_temp_dir is not None and 
                os.path.exists(self.current_temp_dir) and 
                os.path.isdir(self.current_temp_dir))
    
    def get_temp_file_count(self) -> int:
        """
        获取当前临时目录中的文件数量
        
        Returns:
            int: 文件数量，如果目录不存在返回0
        """
        if not self.is_temp_dir_exists():
            return 0
        
        try:
            return len([f for f in os.listdir(self.current_temp_dir) 
                       if os.path.isfile(os.path.join(self.current_temp_dir, f))])
        except Exception as e:
            logger.error(f"Failed to count files in temporary directory: {e}")
            return 0
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动清理资源"""
        try:
            # 在Windows上，VTK可能仍持有文件句柄，使用ignore_errors避免异常
            self.cleanup_all(ignore_errors=True)
        except Exception as e:
            logger.error(f"Error during context manager cleanup: {e}")
            # 不重新抛出异常，避免掩盖原始异常
    
    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            # 在析构函数中使用ignore_errors，避免抛出异常
            self.cleanup_all(ignore_errors=True)
        except Exception:
            # 在析构函数中不应该抛出异常
            pass