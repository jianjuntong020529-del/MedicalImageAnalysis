# -*- coding: utf-8 -*-
"""
加载动画辅助类 - 轻量级版本
提供简单的接口来集成加载动画到现有的文件加载流程
使用顶部进度条 + 右下角提示条，不阻塞主界面
"""

import os
from PyQt5.QtWidgets import QMessageBox

from src.widgets.LoadingAnimationWidget import LoadingIndicator
from src.utils.LoadingWorker import LoadWorker
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LoadingAnimationHelper:
    """
    加载动画辅助类 - 轻量级版本
    使用顶部进度条 + 右下角提示条展示加载状态
    """

    def __init__(self, parent_widget, status_bar=None):
        self.parent_widget = parent_widget
        self.status_bar = status_bar
        # 用列表持有所有活跃 worker，防止 GC 提前回收
        self._workers = []

        # 创建加载指示器
        self.loading_indicator = LoadingIndicator(parent_widget)

    def start_loading(self, path, fmt, on_success=None, on_error=None, params=None):
        """启动文件加载流程（异步，不阻塞主线程）"""
        filename = os.path.basename(path)

        # 显示加载指示器
        self.loading_indicator.start_loading(fmt, filename)

        # 创建工作线程并加入持有列表
        worker = LoadWorker(path, fmt, params)
        self._workers.append(worker)

        def _on_done(data, meta):
            self._release_worker(worker)
            self._on_success(data, meta, on_success)

        def _on_fail(msg):
            self._release_worker(worker)
            self._on_error(msg, on_error)

        worker.progress.connect(self._on_progress)
        worker.finished.connect(_on_done)
        worker.error.connect(_on_fail)

        worker.start()
        logger.info(f"开始加载 {fmt} 文件: {path}")

    def _release_worker(self, worker):
        """线程完成后等待其退出并从列表移除"""
        worker.wait()
        if worker in self._workers:
            self._workers.remove(worker)

    def _on_progress(self, percent, message):
        self.loading_indicator.update_progress(percent)

    def _on_success(self, data, meta, callback):
        self.loading_indicator.finish_success()
        logger.info(f"文件加载成功: {meta}")
        if callback:
            callback(data, meta)

    def _on_error(self, error_msg, callback):
        self.loading_indicator.finish_error(error_msg)
        logger.error(f"文件加载失败: {error_msg}")
        QMessageBox.critical(
            self.parent_widget,
            '加载失败',
            f'文件读取出错：\n{error_msg}'
        )
        if callback:
            callback(error_msg)

    def cleanup(self):
        """清理所有活跃线程"""
        for w in list(self._workers):
            w.quit()
            w.wait()
        self._workers.clear()
