# -*- coding: utf-8 -*-
"""
加载动画辅助类
提供简单的接口来集成加载动画到现有的文件加载流程
"""

import os
from PyQt5.QtWidgets import QMessageBox

from src.widgets.LoadingAnimationWidget import LoadingOverlay
from src.utils.LoadingWorker import LoadWorker
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LoadingAnimationHelper:
    """
    加载动画辅助类
    封装加载动画的创建、显示和事件处理逻辑
    """
    
    # 不同格式的加载步骤定义
    STEPS_MAP = {
        'DICOM': ['扫描文件列表', '读取头信息', '排列切片', '加载体素', '构建体积'],
        'NII': ['解压文件', '解析文件头', '读取体素', '应用变换'],
        'NRRD': ['解压文件', '解析文件头', '读取体素', '应用变换'],
        'MHA': ['解压文件', '解析文件头', '读取体素', '应用变换'],
        'STL': ['读取三角面片', '计算法向量', '构建 VBO', '上传 GPU'],
        'NPY': [],  # NPY 是单步加载，不显示步骤列表
        'IM0': [],
    }
    
    def __init__(self, parent_widget, status_bar=None):
        """
        初始化加载动画辅助类
        
        Args:
            parent_widget: 父控件，用于显示遮罩层
            status_bar: 状态栏，用于显示成功消息（可选）
        """
        self.parent_widget = parent_widget
        self.status_bar = status_bar
        self._worker = None
        self._overlay = None
    
    def start_loading(self, path, fmt, on_success=None, on_error=None, params=None):
        """
        启动文件加载流程
        
        Args:
            path: 文件或文件夹路径
            fmt: 文件格式
            on_success: 成功回调函数 callback(data, meta)
            on_error: 错误回调函数 callback(error_msg)
            params: 额外参数（如 IM0 的尺寸参数）
        """
        filename = os.path.basename(path)
        
        # 创建并显示加载遮罩
        self._overlay = LoadingOverlay(self.parent_widget, fmt, filename)
        
        # 设置步骤列表
        steps = self.STEPS_MAP.get(fmt, [])
        self._overlay.set_steps(steps)
        
        # 显示遮罩
        self._overlay.show_over(self.parent_widget)
        
        # 连接取消信号
        self._overlay.cancelled.connect(self._on_cancel)
        
        # 创建并启动工作线程
        self._worker = LoadWorker(path, fmt, params)
        
        # 连接信号
        self._worker.progress.connect(self._overlay.update_progress)
        self._worker.step_done.connect(self._on_step_done)
        self._worker.finished.connect(lambda data, meta: self._on_success(data, meta, on_success))
        self._worker.error.connect(lambda msg: self._on_error(msg, on_error))
        
        # 启动线程
        self._worker.start()
        
        # 标记第一步为 active
        if steps:
            self._overlay.mark_step(0, 'active')
        
        logger.info(f"开始加载 {fmt} 文件: {path}")
    
    def _on_step_done(self, step_idx):
        """步骤完成回调"""
        if self._overlay:
            # 标记当前步骤为完成
            self._overlay.mark_step(step_idx, 'done')
            
            # 标记下一步为 active
            steps = self.STEPS_MAP.get(self._worker.fmt, [])
            if step_idx + 1 < len(steps):
                self._overlay.mark_step(step_idx + 1, 'active')
    
    def _on_success(self, data, meta, callback):
        """加载成功回调"""
        # 使用淡出动画隐藏遮罩
        if self._overlay:
            self._overlay.fade_out_and_close()
            self._overlay = None
        
        # 显示成功消息
        filename = os.path.basename(meta.get('路径', ''))
        success_msg = f'✓  {filename} 加载完成'
        
        if '尺寸' in meta:
            success_msg += f'   {meta["尺寸"]}'
        
        if self.status_bar:
            self.status_bar.showMessage(success_msg, 4000)
        
        logger.info(f"文件加载成功: {meta}")
        
        # 调用用户回调
        if callback:
            callback(data, meta)
    
    def _on_error(self, error_msg, callback):
        """加载失败回调"""
        # 使用淡出动画隐藏遮罩
        if self._overlay:
            self._overlay.fade_out_and_close()
            self._overlay = None
        
        logger.error(f"文件加载失败: {error_msg}")
        
        # 显示错误对话框
        QMessageBox.critical(
            self.parent_widget,
            '加载失败',
            f'文件读取出错：\n{error_msg}'
        )
        
        # 调用用户回调
        if callback:
            callback(error_msg)
    
    def _on_cancel(self):
        """取消加载回调"""
        if self._worker:
            self._worker.cancel()
            self._worker.quit()
            self._worker.wait()
        
        # 使用淡出动画隐藏遮罩
        if self._overlay:
            self._overlay.fade_out_and_close()
            self._overlay = None
        
        logger.info("用户取消了文件加载")
        
        QMessageBox.information(
            self.parent_widget,
            '已取消',
            '文件加载已取消。'
        )
    
    def cleanup(self):
        """清理资源"""
        if self._worker:
            self._worker.quit()
            self._worker.wait()
            self._worker = None
        
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
