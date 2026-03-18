# -*- coding: utf-8 -*-
"""
冠状面下颌管标注窗口
"""
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

from src.constant.CoronalCanalConstant import CoronalCanalConstant
from src.controller.CoronalCanalAnnotationController import CoronalCanalAnnotationController
from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.ToolBarWidgetModel import ToolBarWidget
from src.style.AppVisualStyle import APPVisualStyle
from src.widgets.ContrastWidget import Contrast
from src.widgets.QtCoronalViewerWidget import CoronalViewer


class CoronalCanalAnnotationWindow(QWidget):
    """冠状面下颌管标注窗口"""
    
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel):
        super().__init__()
        
        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        
        # 获取图像信息
        self.origin = self.baseModelClass.origin
        self.spacing = self.baseModelClass.spacing
        self.dimensions = self.baseModelClass.imageDimensions

        # 设置窗口属性
        self.resize(1240, 920)
        self.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)
        self.setWindowTitle(CoronalCanalConstant.WINDOW_TITLE)

        # 创建独立的冠状面视图
        self.coronalViewer = CoronalViewer(self.baseModelClass)

        # 初始化UI
        self._init_ui()
        
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        
        # 视图布局
        self.view_layout = QtWidgets.QVBoxLayout()
        self.view_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        
        # 视图和滑块布局
        self.viewer_slider_layout = QtWidgets.QHBoxLayout()
        self.viewer_slider_layout.setSpacing(6)
        self.viewer_slider_layout.addWidget(self.coronalViewer.widget)
        self.viewer_slider_layout.addWidget(self.coronalViewer.slider)
        
        # 添加到视图布局
        self.view_layout.addLayout(self.viewer_slider_layout)
        self.view_layout.addWidget(self.coronalViewer.slider_label)
        
        # 将视图布局添加到主布局
        self.main_layout.addLayout(self.view_layout, 7)
        
        # 工具栏布局
        self.toolbar_layout = QtWidgets.QVBoxLayout()
        self.toolbar_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.toolbar_layout.setAlignment(Qt.AlignTop)
        
        # 对比度调整控件
        self.contrast_widget = Contrast()
        self.contrast_widget.init_widget()
        self.toolbar_layout.addWidget(self.contrast_widget.widget_contrast)
        
        # 同步主窗口的对比度设置
        if ToolBarWidget.contrast_widget:
            self.contrast_widget.window_width_slider.setValue(
                ToolBarWidget.contrast_widget.window_width_slider.value()
            )
            self.contrast_widget.window_level_slider.setValue(
                ToolBarWidget.contrast_widget.window_level_slider.value()
            )
        
        # 冠状面下颌管标注控制器 - 传入独立的冠状面视图
        self.canal_annotation = CoronalCanalAnnotationController(
            self.baseModelClass,
            self.coronalViewer,  # 使用独立的冠状面视图
            self.contrast_widget
        )
        
        # 添加标注控件到工具栏
        self.toolbar_layout.addWidget(self.canal_annotation.widget_canal_annotation)
        
        # 将工具栏布局添加到主布局
        self.main_layout.addLayout(self.toolbar_layout, 2)

        self.setLayout(self.main_layout)