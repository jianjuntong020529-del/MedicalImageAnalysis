# -*- coding: utf-8 -*-
# @Time    : 2024/10/15 19:17
#
# @Author  : Jianjun Tong
from PyQt5 import QtWidgets, QtCore


class ImplantAdjustSlider:
    def __init__(self,widget,max_value,min_value):
        self.widget = widget
        self.horizontal_layout = QtWidgets.QHBoxLayout()
        self.horizontal_layout.setSpacing(6)

        self.label = QtWidgets.QLabel(self.widget.widget_implant)

        self.horizontal_slider = QtWidgets.QSlider(self.widget.widget_implant)
        self.horizontal_slider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontal_slider.setMaximum(max_value)
        self.horizontal_slider.setMinimum(min_value)
        self.horizontal_slider.setMinimumSize(QtCore.QSize(350, 16))
        self.horizontal_slider.setMaximumSize(QtCore.QSize(350, 16))
        self.horizontal_slider.setSingleStep(1)

        self.horizontal_layout.addWidget(self.label)
        self.horizontal_layout.addWidget(self.horizontal_slider)
