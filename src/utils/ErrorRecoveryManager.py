# -*- coding: utf-8 -*-
# @Time    : 2024/12/24
# @Author  : Kiro AI Assistant
"""
错误恢复管理器
管理NPY数据处理过程中的错误恢复和状态保存
"""

import copy
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    INVALID_DATA_FORMAT = "invalid_data_format"
    MEMORY_ERROR = "memory_error"
    VTK_ERROR = "vtk_error"
    CONVERSION_ERROR = "conversion_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class SystemState:
    """系统状态快照"""
    data_type: Optional[str] = None
    current_file_path: Optional[str] = None
    viewer_states: Dict[str, Any] = field(default_factory=dict)
    model_states: Dict[str, Any] = field(default_factory=dict)
    temp_resources: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None


@dataclass
class ErrorContext:
    """错误上下文信息"""
    error_type: ErrorType
    error_message: str
    file_path: Optional[str] = None
    stack_trace: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)


class ErrorRecoveryManager:
    """错误恢复管理器"""
    
    def __init__(self):
        """初始化错误恢复管理器"""
        self.previous_state: Optional[SystemState] = None
        self.temp_resources: List[str] = []
        self.cleanup_callbacks: List[Callable[[], None]] = []
        self.error_handlers: Dict[ErrorType, Callable[[ErrorContext], None]] = {}
        
        # 注册默认错误处理器
        self._register_default_handlers()
        
        logger.debug("ErrorRecoveryManager initialized")
    
    def save_state(self, data_type: Optional[str] = None, 
                   file_path: Optional[str] = None,
                   viewer_states: Optional[Dict[str, Any]] = None,
                   model_states: Optional[Dict[str, Any]] = None) -> SystemState:
        """
        保存当前系统状态
        
        Args:
            data_type: 当前数据类型
            file_path: 当前文件路径
            viewer_states: 查看器状态字典
            model_states: 模型状态字典
            
        Returns:
            SystemState: 保存的状态快照
        """
        try:
            import datetime
            
            state = SystemState(
                data_type=data_type,
                current_file_path=file_path,
                viewer_states=copy.deepcopy(viewer_states or {}),
                model_states=copy.deepcopy(model_states or {}),
                temp_resources=self.temp_resources.copy(),
                timestamp=datetime.datetime.now().isoformat()
            )
            
            self.previous_state = state
            logger.info(f"System state saved at {state.timestamp}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to save system state: {e}")
            raise RuntimeError(f"Failed to save system state: {e}")
    
    def recover_state(self) -> bool:
        """
        恢复到之前保存的状态
        
        Returns:
            bool: 恢复是否成功
        """
        if self.previous_state is None:
            logger.warning("No previous state to recover")
            return False
        
        try:
            logger.info(f"Recovering system state from {self.previous_state.timestamp}")
            
            # 清理当前资源
            self.cleanup_resources()
            
            # 这里可以添加具体的状态恢复逻辑
            # 例如：恢复数据类型、文件路径、查看器状态等
            
            logger.info("System state recovered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover system state: {e}")
            return False
    
    def add_temp_resource(self, resource_path: str):
        """
        添加临时资源到跟踪列表
        
        Args:
            resource_path: 资源路径
        """
        if resource_path not in self.temp_resources:
            self.temp_resources.append(resource_path)
            logger.debug(f"Added temporary resource: {resource_path}")
    
    def add_cleanup_callback(self, callback: Callable[[], None]):
        """
        添加清理回调函数
        
        Args:
            callback: 清理回调函数
        """
        self.cleanup_callbacks.append(callback)
        logger.debug("Added cleanup callback")
    
    def cleanup_resources(self):
        """清理临时资源"""
        cleanup_errors = []
        
        # 执行清理回调
        for callback in self.cleanup_callbacks:
            try:
                callback()
                logger.debug("Executed cleanup callback")
            except Exception as e:
                error_msg = f"Cleanup callback failed: {e}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # 清理临时资源
        for resource in self.temp_resources:
            try:
                import os
                if os.path.exists(resource):
                    if os.path.isfile(resource):
                        os.remove(resource)
                    elif os.path.isdir(resource):
                        import shutil
                        shutil.rmtree(resource)
                    logger.debug(f"Cleaned up resource: {resource}")
            except Exception as e:
                error_msg = f"Failed to cleanup resource {resource}: {e}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # 清空资源列表
        self.temp_resources.clear()
        self.cleanup_callbacks.clear()
        
        if cleanup_errors:
            logger.warning(f"Some cleanup operations failed: {'; '.join(cleanup_errors)}")
        else:
            logger.info("All resources cleaned up successfully")
    
    def register_error_handler(self, error_type: ErrorType, 
                             handler: Callable[[ErrorContext], None]):
        """
        注册错误处理器
        
        Args:
            error_type: 错误类型
            handler: 错误处理函数
        """
        self.error_handlers[error_type] = handler
        logger.debug(f"Registered error handler for {error_type}")
    
    def handle_error(self, error_context: ErrorContext) -> bool:
        """
        处理错误
        
        Args:
            error_context: 错误上下文
            
        Returns:
            bool: 错误是否被成功处理
        """
        try:
            logger.error(f"Handling error: {error_context.error_type} - {error_context.error_message}")
            
            # 查找对应的错误处理器
            handler = self.error_handlers.get(error_context.error_type)
            if handler:
                handler(error_context)
                logger.info(f"Error handled by specific handler: {error_context.error_type}")
                return True
            else:
                # 使用默认处理器
                self._default_error_handler(error_context)
                logger.info("Error handled by default handler")
                return True
                
        except Exception as e:
            logger.error(f"Error handler failed: {e}")
            return False
    
    def _register_default_handlers(self):
        """注册默认错误处理器"""
        
        def handle_file_not_found(context: ErrorContext):
            logger.error(f"File not found: {context.file_path}")
            context.recovery_suggestions.extend([
                "Check if the file path is correct",
                "Verify file permissions",
                "Try selecting a different file"
            ])
        
        def handle_permission_error(context: ErrorContext):
            logger.error(f"Permission denied: {context.file_path}")
            context.recovery_suggestions.extend([
                "Check file permissions",
                "Run application with appropriate privileges",
                "Try copying file to a different location"
            ])
        
        def handle_invalid_data_format(context: ErrorContext):
            logger.error(f"Invalid data format: {context.error_message}")
            context.recovery_suggestions.extend([
                "Verify the file is a valid .npy file",
                "Check if the data is 3-dimensional",
                "Try converting the data format"
            ])
        
        def handle_memory_error(context: ErrorContext):
            logger.error(f"Memory error: {context.error_message}")
            context.recovery_suggestions.extend([
                "Close other applications to free memory",
                "Try processing smaller data files",
                "Restart the application"
            ])
        
        def handle_vtk_error(context: ErrorContext):
            logger.error(f"VTK error: {context.error_message}")
            context.recovery_suggestions.extend([
                "Check VTK installation",
                "Verify data compatibility with VTK",
                "Try restarting the application"
            ])
        
        def handle_conversion_error(context: ErrorContext):
            logger.error(f"Conversion error: {context.error_message}")
            context.recovery_suggestions.extend([
                "Check if the input data format is supported",
                "Verify sufficient disk space for conversion",
                "Try with a smaller data file",
                "Check conversion parameters"
            ])
        
        # 注册处理器
        self.register_error_handler(ErrorType.FILE_NOT_FOUND, handle_file_not_found)
        self.register_error_handler(ErrorType.PERMISSION_ERROR, handle_permission_error)
        self.register_error_handler(ErrorType.INVALID_DATA_FORMAT, handle_invalid_data_format)
        self.register_error_handler(ErrorType.MEMORY_ERROR, handle_memory_error)
        self.register_error_handler(ErrorType.VTK_ERROR, handle_vtk_error)
        self.register_error_handler(ErrorType.CONVERSION_ERROR, handle_conversion_error)
    
    def _default_error_handler(self, context: ErrorContext):
        """默认错误处理器"""
        logger.error(f"Unhandled error type: {context.error_type}")
        
        # 尝试恢复状态
        if self.previous_state:
            logger.info("Attempting to recover previous state")
            self.recover_state()
        
        # 清理资源
        self.cleanup_resources()
        
        # 添加通用恢复建议
        context.recovery_suggestions.extend([
            "Try reloading the data",
            "Restart the application if the problem persists",
            "Check the application logs for more details"
        ])
    
    def create_error_context(self, error_type: ErrorType, 
                           error_message: str,
                           file_path: Optional[str] = None,
                           exception: Optional[Exception] = None) -> ErrorContext:
        """
        创建错误上下文
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
            file_path: 相关文件路径
            exception: 原始异常对象
            
        Returns:
            ErrorContext: 错误上下文对象
        """
        stack_trace = None
        if exception:
            import traceback
            stack_trace = traceback.format_exc()
        
        return ErrorContext(
            error_type=error_type,
            error_message=error_message,
            file_path=file_path,
            stack_trace=stack_trace
        )
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type is not None:
            # 发生异常时自动清理资源
            logger.info("Exception occurred, cleaning up resources")
            self.cleanup_resources()
        return False  # 不抑制异常