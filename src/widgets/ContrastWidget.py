# -*- coding: utf-8 -*-
# @Time    : 2024/10/10 15:52
#
# @Author  : Jianjun Tong
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from src.constant.WindowConstant import WindowConstant
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font



class Contrast:
    def __init__(self):
        self.widget = None

    def init_widget(self):
        self.widget_contrast = QtWidgets.QWidget(self.widget)
        self.widget_contrast.setMinimumSize(QtCore.QSize(350, 120))
        self.widget_contrast.setMaximumSize(QtCore.QSize(400, 120))
        self.widget_contrast.setObjectName("widget_contrast")
        self.widget_contrast.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)

        self.contrast_vertical_layout = QtWidgets.QVBoxLayout(self.widget_contrast)
        self.contrast_vertical_layout.setContentsMargins(11, 11, 11, 11)
        self.contrast_vertical_layout.setSpacing(5)
        self.contrast_vertical_layout.setObjectName("contrast_vertical_layout")
        # -----------------------------对比度调整栏名称---------------------------------------
        self.title = QtWidgets.QLabel(self.widget_contrast)
        self.title.setMinimumSize(QtCore.QSize(100, 20))
        self.title.setMaximumSize(QtCore.QSize(150, 20))
        self.title.setObjectName("title")
        self.title.setStyleSheet(APPVisualStyle.WIDGET_LABEL_COLOR)
        self.title.setFont(Font.font2)
        self.contrast_vertical_layout.addWidget(self.title, Qt.AlignLeft | Qt.AlignTop)

        # ----------------------------窗位线--------------------------------------------------
        self.window_level_slider = QtWidgets.QSlider(self.widget_contrast)
        self.window_level_slider.setOrientation(QtCore.Qt.Horizontal)
        self.window_level_slider.setObjectName("window_level_slider")
        self.window_level_slider.setMaximum(3000)
        self.window_level_slider.setMinimum(-2000)
        self.window_level_slider.setSingleStep(1)
        self.contrast_vertical_layout.addWidget(self.window_level_slider, Qt.AlignLeft)
        self.window_level = QtWidgets.QLabel(self.widget_contrast)
        self.window_level.setObjectName("window_level")
        self.contrast_vertical_layout.addWidget(self.window_level, Qt.AlignCenter)
        # ---------------------------窗宽线----------------------------------------------------
        self.window_width_slider = QtWidgets.QSlider(self.widget_contrast)
        self.window_width_slider.setOrientation(QtCore.Qt.Horizontal)
        self.window_width_slider.setObjectName("window_width_slider")
        self.window_width_slider.setMaximum(8000)
        self.window_width_slider.setMinimum(-2000)
        self.window_width_slider.setSingleStep(1)
        self.contrast_vertical_layout.addWidget(self.window_width_slider)
        self.window_width = QtWidgets.QLabel(self.widget_contrast)
        self.window_width.setObjectName("window_width")
        self.contrast_vertical_layout.addWidget(self.window_width, Qt.AlignCenter)


        self.translateUi()

    def translateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.title.setText(_translate("MainWindow", WindowConstant.CONTRAST_TOOL_TITLE))
        self.window_level.setText(_translate("MainWindow", WindowConstant.WINDOW_LEVEL))
        self.window_width.setText(_translate("MainWindow", WindowConstant.WINDOW_WIDTH))

