# -*- coding: utf-8 -*-
# @Time    : 2024/10/15 10:00
#
# @Author  : Jianjun Tong
"""
分割编辑控制器
负责协调分割编辑界面和业务逻辑
"""
from PyQt5 import QtWidgets
from src.widgets.SegmentationEditWidget import SegmentationEditWidget


class SegmentationEditController:
    """分割编辑控制器类"""
    
    def __init__(self, parent_widget):
        """
        初始化分割编辑控制器
        
        Args:
            parent_widget: 父窗口组件
        """
        self.parent_widget = parent_widget
        self.seg_edit_widget = None
        self.seg_edit_window = None
    
    def show_segmentation_editor(self):
        """显示分割编辑窗口"""
        # 创建独立窗口
        self.seg_edit_window = QtWidgets.QDialog(self.parent_widget)
        self.seg_edit_window.setWindowTitle("NIfTI分割结果编辑")
        self.seg_edit_window.resize(1000, 800)
        
        # 创建布局
        layout = QtWidgets.QVBoxLayout(self.seg_edit_window)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加分割编辑组件
        self.seg_edit_widget = SegmentationEditWidget(self.seg_edit_window)
        layout.addWidget(self.seg_edit_widget)
        
        # 显示窗口
        self.seg_edit_window.exec_()
    
    def close_segmentation_editor(self):
        """关闭分割编辑窗口"""
        if self.seg_edit_window:
            self.seg_edit_window.close()
            self.seg_edit_window = None
            self.seg_edit_widget = None
