# -*- coding: utf-8 -*-
"""
冠状面下颌管标注UI组件
"""
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QVBoxLayout, QLabel, QPushButton

from src.constant.CoronalCanalConstant import CoronalCanalConstant
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font


class CoronalCanalAnnotationWidget:
    """冠状面下颌管标注UI组件"""
    
    def init_widget(self):
        """初始化UI组件"""
        # 主容器
        self.widget_canal_annotation = QtWidgets.QWidget()
        self.widget_canal_annotation.setMinimumSize(QtCore.QSize(350, 400))
        self.widget_canal_annotation.setMaximumSize(QtCore.QSize(400, 400))
        # self.widget_canal_annotation.setStyleSheet("background-color: #000000;")
        self.widget_canal_annotation.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)
        
        # 主布局
        self.canal_annotation_layout = QtWidgets.QVBoxLayout(self.widget_canal_annotation)
        self.canal_annotation_layout.setContentsMargins(11, 11, 11, 11)
        self.canal_annotation_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.canal_annotation_layout.setAlignment(Qt.AlignTop)
        
        # 标题
        self.widget_title = QtWidgets.QLabel(self.widget_canal_annotation)
        self.widget_title.setMinimumSize(QtCore.QSize(200, 20))
        self.widget_title.setMaximumSize(QtCore.QSize(240, 20))
        self.widget_title.setStyleSheet(APPVisualStyle.WIDGET_LABEL_COLOR)
        self.widget_title.setFont(Font.font_en)
        self.widget_title.setText(CoronalCanalConstant.WIDGET_TITLE)
        self.canal_annotation_layout.addWidget(self.widget_title, Qt.AlignLeft | Qt.AlignTop)
        
        # 下颌管类型选择
        self.canal_type_label = QtWidgets.QLabel(self.widget_canal_annotation)
        self.canal_type_label.setFont(Font.font_en)
        self.canal_type_label.setText(CoronalCanalConstant.CANAL_TYPE_LABEL)
        
        self.canal_type_combobox = QComboBox()
        self.canal_type_combobox.setFont(Font.font_en)
        self.canal_type_combobox.setMinimumSize(QtCore.QSize(200, 25))
        self.canal_type_combobox.setMaximumSize(QtCore.QSize(240, 25))
        
        # 添加下颌管类型选项
        for name, color in CoronalCanalConstant.CANAL_TYPES:
            pix_color = QPixmap(20, 20)
            pix_color.fill(QColor(color))
            self.canal_type_combobox.addItem(QIcon(pix_color), name)
        
        self.canal_type_combobox.setCurrentIndex(CoronalCanalConstant.DEFAULT_CANAL_TYPE)
        
        # 类型选择布局
        self.canal_type_layout = QHBoxLayout()
        self.canal_type_layout.setAlignment(Qt.AlignLeft)
        self.canal_type_layout.addWidget(self.canal_type_label)
        self.canal_type_layout.addWidget(self.canal_type_combobox)
        self.canal_annotation_layout.addLayout(self.canal_type_layout)
        
        # 操作按钮
        self.pushButton_paint = QtWidgets.QPushButton(self.widget_canal_annotation)
        self.pushButton_paint.setFont(Font.font_en)
        self.pushButton_paint.setText(CoronalCanalConstant.PAINT_BUTTON)
        self.pushButton_paint.setCheckable(True)
        self.pushButton_paint.setAutoExclusive(False)
        
        self.pushButton_clear = QtWidgets.QPushButton(self.widget_canal_annotation)
        self.pushButton_clear.setFont(Font.font_en)
        self.pushButton_clear.setText(CoronalCanalConstant.CLEAR_BUTTON)
        self.pushButton_clear.setAutoExclusive(False)
        
        self.pushButton_undo = QtWidgets.QPushButton(self.widget_canal_annotation)
        self.pushButton_undo.setFont(Font.font_en)
        self.pushButton_undo.setText(CoronalCanalConstant.UNDO_BUTTON)
        self.pushButton_undo.setAutoExclusive(False)
        
        self.pushButton_redo = QtWidgets.QPushButton(self.widget_canal_annotation)
        self.pushButton_redo.setFont(Font.font_en)
        self.pushButton_redo.setText(CoronalCanalConstant.REDO_BUTTON)
        self.pushButton_redo.setAutoExclusive(False)
        
        # 按钮布局
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setSpacing(10)
        self.button_layout.setContentsMargins(11, 11, 11, 11)
        
        self.button_left_layout = QtWidgets.QVBoxLayout()
        self.button_left_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.button_right_layout = QtWidgets.QVBoxLayout()
        self.button_right_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        
        self.button_left_layout.addWidget(self.pushButton_paint)
        self.button_left_layout.addWidget(self.pushButton_undo)
        self.button_right_layout.addWidget(self.pushButton_clear)
        self.button_right_layout.addWidget(self.pushButton_redo)
        
        self.button_layout.addLayout(self.button_left_layout)
        self.button_layout.addLayout(self.button_right_layout)
        self.canal_annotation_layout.addLayout(self.button_layout)
        
        # 标注信息显示
        self.info_label = QtWidgets.QLabel(self.widget_canal_annotation)
        self.info_label.setFont(Font.font_en)
        self.info_label.setText(CoronalCanalConstant.ANNOTATION_INFO)
        self.canal_annotation_layout.addWidget(self.info_label)
        
        # 点数量显示
        self.point_count_label = QtWidgets.QLabel(self.widget_canal_annotation)
        self.point_count_label.setFont(Font.font_en)
        self.point_count_label.setText(f"{CoronalCanalConstant.POINT_COUNT_LABEL} 0")
        self.canal_annotation_layout.addWidget(self.point_count_label)
        
        # 左侧下颌管点数
        self.left_canal_count_label = QtWidgets.QLabel(self.widget_canal_annotation)
        self.left_canal_count_label.setFont(Font.font_en)
        self.left_canal_count_label.setText("左侧下颌管: 0")
        self.canal_annotation_layout.addWidget(self.left_canal_count_label)
        
        # 右侧下颌管点数
        self.right_canal_count_label = QtWidgets.QLabel(self.widget_canal_annotation)
        self.right_canal_count_label.setFont(Font.font_en)
        self.right_canal_count_label.setText("右侧下颌管: 0")
        self.canal_annotation_layout.addWidget(self.right_canal_count_label)
        
        # 文件操作按钮
        self.pushButton_load = QtWidgets.QPushButton(self.widget_canal_annotation)
        self.pushButton_load.setFont(Font.font_en)
        self.pushButton_load.setText(CoronalCanalConstant.LOAD_BUTTON)
        self.pushButton_load.setAutoExclusive(False)
        
        self.pushButton_save = QtWidgets.QPushButton(self.widget_canal_annotation)
        self.pushButton_save.setFont(Font.font_en)
        self.pushButton_save.setText(CoronalCanalConstant.SAVE_BUTTON)
        self.pushButton_save.setAutoExclusive(False)
        
        # 文件操作按钮布局
        self.file_button_layout = QtWidgets.QHBoxLayout()
        self.file_button_layout.setSpacing(10)
        self.file_button_layout.addWidget(self.pushButton_load)
        self.file_button_layout.addWidget(self.pushButton_save)
        self.canal_annotation_layout.addLayout(self.file_button_layout)

        # 分割操作按钮
        self.pushButton_setartSeg = QtWidgets.QPushButton(self.widget_canal_annotation)
        self.pushButton_setartSeg.setFont(Font.font_en)
        self.pushButton_setartSeg.setText(CoronalCanalConstant.SEG_BUTTON)
        self.pushButton_setartSeg.setAutoExclusive(False)

        self.pushButton_loadSegResult = QtWidgets.QPushButton(self.widget_canal_annotation)
        self.pushButton_loadSegResult.setFont(Font.font_en)
        self.pushButton_loadSegResult.setText(CoronalCanalConstant.LOAD_SEG_RESULT_BUTTON)
        self.pushButton_loadSegResult.setAutoExclusive(False)

        # 分割按钮布局
        self.seg_button_layout = QtWidgets.QHBoxLayout()
        self.seg_button_layout.setSpacing(10)
        self.seg_button_layout.addWidget(self.pushButton_setartSeg)
        self.seg_button_layout.addWidget(self.pushButton_loadSegResult)
        self.canal_annotation_layout.addLayout(self.seg_button_layout)

        # 添加弹性空间
        self.canal_annotation_layout.addStretch()
        
        # 初始化状态
        self.paint_enabled = False
    
    def update_point_count_display(self, left_count: int, right_count: int, total_count: int):
        """更新点数量显示"""
        self.point_count_label.setText(f"{CoronalCanalConstant.POINT_COUNT_LABEL} {total_count}")
        self.left_canal_count_label.setText(f"左侧下颌管: {left_count}")
        self.right_canal_count_label.setText(f"右侧下颌管: {right_count}")
    
    def set_paint_enabled(self, enabled: bool):
        """设置标注状态"""
        self.paint_enabled = enabled
        self.pushButton_paint.setChecked(enabled)
        if enabled:
            self.pushButton_paint.setText("结束标注")
        else:
            self.pushButton_paint.setText(CoronalCanalConstant.PAINT_BUTTON)