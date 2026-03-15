# -*- coding: utf-8 -*-
# @Time    : 2024/10/16 11:18
#
# @Author  : Jianjun Tong
from PyQt5 import QtWidgets, QtCore, QtGui

from src.constant.ParamConstant import ParamConstant
from src.constant.QIconConstant import QIconConstant
from src.constant.WindowConstant import WindowConstant
from src.model import OrthoViewerModel
from src.model.BaseModel import BaseModel
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font
from src.widgets.ContrastWidget import Contrast


class ToolBarManager:
    def __init__(self):
        self.QMainWindow = None

    def init_toolBar(self):
        # 窗口的状态栏 添加标签、进度条、临时信息等状态信息
        self.statusBar = QtWidgets.QStatusBar(self.QMainWindow)
        self.statusBar.setObjectName("statusBar")

        # 将状态栏添加到窗口中
        self.QMainWindow.setStatusBar(self.statusBar)

        # 为窗口设置工具栏
        self.toolBar = QtWidgets.QToolBar(self.QMainWindow)
        self.toolBar.setObjectName("toolBar")
        self.toolBar.setFixedHeight(40)

        # 在工具栏中添加各种功能
        self.QMainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.action_ruler = QtWidgets.QAction(self.QMainWindow)
        self.action_ruler.setCheckable(True)
        self.action_ruler.setObjectName("action_ruler")
        self.action_ruler.setIcon(QtGui.QIcon(QIconConstant.RULER_ICON))

        self.action_paint = QtWidgets.QAction(self.QMainWindow)
        self.action_paint.setCheckable(True)
        self.action_paint.setObjectName("action_paint")
        self.action_paint.setIcon(QtGui.QIcon(QIconConstant.PAINT_ICON))


        self.action_polyline = QtWidgets.QAction(self.QMainWindow)
        self.action_polyline.setCheckable(True)
        self.action_polyline.setObjectName("action_polyline")
        self.action_polyline.setIcon(QtGui.QIcon(QIconConstant.POLYLINE_ICON))

        self.action_angle = QtWidgets.QAction(self.QMainWindow)
        self.action_angle.setCheckable(True)
        self.action_angle.setObjectName("action_angle")
        self.action_angle.setIcon(QtGui.QIcon(QIconConstant.ANGLE_ICON))

        self.action_pixel = QtWidgets.QAction(self.QMainWindow)
        self.action_pixel.setCheckable(True)
        self.action_pixel.setObjectName("action_pixel")
        self.action_pixel.setIcon(QtGui.QIcon(QIconConstant.HU_ICON))

        self.action_crosshair = QtWidgets.QAction(self.QMainWindow)
        self.action_crosshair.setCheckable(True)
        self.action_crosshair.setObjectName("action_crosshair")
        self.action_crosshair.setIcon(QtGui.QIcon(QIconConstant.CROSSHAIR_ICON))

        self.action_reset = QtWidgets.QAction(self.QMainWindow)
        self.action_reset.setObjectName("action_reset")
        self.action_reset.setIcon(QtGui.QIcon(QIconConstant.RESET_ICON))

        # 拖动图像
        self.action_dragging_image = QtWidgets.QAction(self.QMainWindow)
        self.action_dragging_image.setObjectName("action_dragging_image")
        self.action_dragging_image.setCheckable(True)
        self.action_dragging_image.setIcon(QtGui.QIcon(QIconConstant.DRAGGING_ICON))

        self.action_get_roi = QtWidgets.QAction(self.QMainWindow)
        self.action_get_roi.setObjectName("action_get_roi")
        self.action_get_roi.setCheckable(True)
        self.action_get_roi.setIcon(QtGui.QIcon(QIconConstant.GET_ROI))


        self.toolBar.addAction(self.action_ruler)
        self.toolBar.addAction(self.action_paint)
        self.toolBar.addAction(self.action_polyline)
        self.toolBar.addAction(self.action_angle)
        self.toolBar.addAction(self.action_pixel)
        self.toolBar.addAction(self.action_crosshair)
        self.toolBar.addAction(self.action_reset)
        self.toolBar.addAction(self.action_dragging_image)
        self.toolBar.addAction(self.action_get_roi)

        # 在工具栏的右侧添加间隔符
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.toolBar.addWidget(spacer)

        self.label_Subjectname = QtWidgets.QLabel(self.QMainWindow)
        self.label_Subjectname.setFixedHeight(25)
        self.label_Subjectname.setFixedWidth(110)
        self.label_Subjectname.setFont(Font.font)
        self.label_Subjectname.setText(WindowConstant.LABEL_SUBJECTNAME)
        self.toolBar.addWidget(self.label_Subjectname)

        self.lineedit_Subjectname = QtWidgets.QLineEdit(self.QMainWindow)
        # self.lineedit_Subjectname.setMaximumSize(QtCore.QSize(300, 25))
        self.lineedit_Subjectname.setFixedHeight(25)
        self.lineedit_Subjectname.setFixedWidth(300)
        self.lineedit_Subjectname.setText(WindowConstant.LINEDIET_SUBJECTNAME)
        self.toolBar.addWidget(self.lineedit_Subjectname)

        self.translateUi()

    def translateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.action_ruler.setText(_translate("MainWindow", APPVisualStyle.RULER))
        self.action_paint.setText(_translate("MainWindow", APPVisualStyle.PAINT))
        self.action_polyline.setText(_translate("MainWindow", APPVisualStyle.POLY_LINE))
        self.action_angle.setText(_translate("MainWindow", APPVisualStyle.ANGLE))
        self.action_pixel.setText(_translate("MainWindow", APPVisualStyle.HU))
        self.action_reset.setText(_translate("MainWindow", APPVisualStyle.RESET))
        self.action_crosshair.setText(_translate("MainWindow", APPVisualStyle.CROSSHAIR))
        self.action_dragging_image.setText(_translate("MainWindow", APPVisualStyle.DRAGGING))
        self.action_get_roi.setText(_translate("MainWindow", APPVisualStyle.ROI))
