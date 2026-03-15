# -*- coding: utf-8 -*-
# @Time    : 2024/10/10 16:05
#
# @Author  : Jianjun Tong
import math

import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox

from src.constant.ParamConstant import ParamConstant
from src.constant.WindowConstant import WindowConstant
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font
from src.widgets.AngleRotationAndMoveSlider import ImplantAdjustSlider


class ImplantWidget:
    def __init__(self):
        self.widget = None

    def init_widget(self):
        # -------------------------植体工具栏--------------------------------------------------------------
        self.widget_implant = QtWidgets.QWidget(self.widget)
        self.widget_implant.hide()
        self.widget_implant.setMinimumSize(QtCore.QSize(350, 350))
        self.widget_implant.setMaximumSize(QtCore.QSize(400, 400))
        self.widget_implant.setObjectName("widget_implant")
        self.widget_implant.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)

        self.verticalLayout_implant = QtWidgets.QVBoxLayout(self.widget_implant)
        self.verticalLayout_implant.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_implant.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.verticalLayout_implant.setObjectName("verticalLayout_implant")

        self.label_implant = QtWidgets.QLabel(self.widget_implant)
        self.label_implant.setObjectName("label_implant")
        self.label_implant.setStyleSheet(APPVisualStyle.WIDGET_LABEL_COLOR)
        self.label_implant.setFont(Font.font2)

        self.verticalLayout_implant.addWidget(self.label_implant)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.label_ToothID = QtWidgets.QLabel(self.widget_implant)
        self.label_ToothID.setObjectName("label_ToothID")
        self.horizontalLayout.addWidget(self.label_ToothID)

        self.label_ToothImplant = QtWidgets.QLabel(self.widget_implant)
        self.label_ToothImplant.setObjectName("label_ToothImplant")
        self.horizontalLayout.addWidget(self.label_ToothImplant)

        self.verticalLayout_implant.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        # 牙齿序列和植体型号----------------------------------------------------------------------------------------
        # -----------------------------------------------------------------------
        self.ToothID_QComboBox = QtWidgets.QComboBox(self.widget_implant)
        self.ToothID_itmes = ParamConstant.TOOTH_ID
        self.ToothID_QComboBox.setObjectName("ToothID_QComboBox")
        self.ToothID_QComboBox.addItems(self.ToothID_itmes)  # 设置多个项目
        self.ToothID_QComboBox.setItemData(0, QtCore.QVariant(0), Qt.UserRole - 1)
        self.ToothID_QComboBox.setItemData(9, QtCore.QVariant(0), Qt.UserRole - 1)
        self.ToothID_QComboBox.setItemData(18, QtCore.QVariant(0), Qt.UserRole - 1)
        self.ToothID_QComboBox.setItemData(27, QtCore.QVariant(0), Qt.UserRole - 1)
        self.horizontalLayout_2.addWidget(self.ToothID_QComboBox)

        # -------------------------------------------------------------------------------------
        self.ToothImplant_QComboBox = QtWidgets.QComboBox(self.widget_implant)
        self.ToothImplant_itmes = ParamConstant.TOOTH_IMPLANT
        self.ToothImplant_QComboBox.addItems(self.ToothImplant_itmes)  # 设置多个项目
        self.ToothImplant_QComboBox.setObjectName("ToothImplant_QComboBox")
        self.horizontalLayout_2.addWidget(self.ToothImplant_QComboBox)
        self.verticalLayout_implant.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        # 植体上下----------------------------------------------------------------------------------
        self.horizontalLayout_implant_direction = QtWidgets.QHBoxLayout()
        self.horizontalLayout_implant_direction.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_implant_direction.setObjectName("horizontalLayout_implant_direction")

        self.label_implant_direction = QtWidgets.QLabel(self.widget_implant)
        self.label_implant_direction.setObjectName("label_implant_direction")
        self.horizontalLayout_implant_direction.addWidget(self.label_implant_direction)

        self.implant_direction_cb_up = QCheckBox('Up', self.widget_implant)
        self.implant_direction_cb_up.setCheckState(2)
        self.implant_direction_cb_down = QCheckBox('Down', self.widget_implant)
        self.implant_direction_cb_down.setCheckState(0)

        self.horizontalLayout_implant_direction.addWidget(self.implant_direction_cb_up)
        self.horizontalLayout_implant_direction.addWidget(self.implant_direction_cb_down)
        self.verticalLayout_implant.addLayout(self.horizontalLayout_implant_direction)

        # 植体放置----------------------------------------------------------------------------------------------
        self.pushButton_implant = QtWidgets.QPushButton(self.widget_implant)
        self.pushButton_implant.setObjectName("pushButton_implant")
        self.pushButton_implant.setFont(Font.font2)
        self.horizontalLayout_3.addWidget(self.pushButton_implant)
        self.implant_place_flag = False
        self.implant_circle_radius = 5
        self.implant_circle_height = 50

        # 十字线正交----------------------------------------------------------------------------------------------
        self.pushButton_crosshair_axis_orthogonal = QtWidgets.QPushButton(self.widget_implant)
        self.pushButton_crosshair_axis_orthogonal.setObjectName("pushButton_crosshair_axis_orthogonal")
        self.pushButton_crosshair_axis_orthogonal.setFont(Font.font2)
        self.pushButton_crosshair_axis_orthogonal.setCheckable(True)
        self.pushButton_crosshair_axis_orthogonal.setAutoExclusive(False)
        self.horizontalLayout_3.addWidget(self.pushButton_crosshair_axis_orthogonal)
        self.verticalLayout_implant.addLayout(self.horizontalLayout_3)
        self.cross_hairaxis_orthogonal_enable = False

        # 微调按钮
        self.pushButton_adjust_imp = QtWidgets.QPushButton(self.widget_implant)
        self.pushButton_adjust_imp.setObjectName("pushButton_adjust_imp")
        self.pushButton_adjust_imp.setFont(Font.font2)
        self.horizontalLayout_3.addWidget(self.pushButton_adjust_imp)

        # Implant Angle Rotation XY-------------------------------------------------------------------
        self.implantSlider_A_XY = ImplantAdjustSlider(self,max_value=90,min_value=-90)
        self.horizontalLayout_angle_XY = self.implantSlider_A_XY.horizontal_layout
        self.label_regis_XY_adjust = self.implantSlider_A_XY.label
        self.horizontalSlider_implant_angle_XY = self.implantSlider_A_XY.horizontal_slider
        self.verticalLayout_implant.addLayout(self.horizontalLayout_angle_XY)

        # Implant Angle Rotation YZ-------------------------------------------------------------------
        self.implantSlider_A_YZ = ImplantAdjustSlider(self,max_value=90,min_value=-90)
        self.horizontalLayout_angle_YZ = self.implantSlider_A_YZ.horizontal_layout
        self.label_regis_YZ_adjust = self.implantSlider_A_YZ.label
        self.horizontalSlider_implant_angle_YZ = self.implantSlider_A_YZ.horizontal_slider
        self.verticalLayout_implant.addLayout(self.horizontalLayout_angle_YZ)

        # Implant Angle Rotation XZ-------------------------------------------------------------------
        self.implantSlider_A_XZ = ImplantAdjustSlider(self,max_value=90,min_value=-90)
        self.horizontalLayout_angle_XZ = self.implantSlider_A_XZ.horizontal_layout
        self.label_regis_XZ_adjust = self.implantSlider_A_XZ.label
        self.horizontalSlider_implant_angle_XZ = self.implantSlider_A_XZ.horizontal_slider
        self.verticalLayout_implant.addLayout(self.horizontalLayout_angle_XZ)

        # --------------X轴位移------------------------------------
        # Implant Move on X axis----------------------------------------------------------------------------------------
        self.implantSlider_M_Xaxis = ImplantAdjustSlider(self,max_value=100,min_value=-100)
        self.horizontalLayout_move_Xaxis = self.implantSlider_M_Xaxis.horizontal_layout
        self.label_regis_move_Xaxis = self.implantSlider_M_Xaxis.label
        self.horizontalSlider_implant_move_Xaxis = self.implantSlider_M_Xaxis.horizontal_slider
        self.verticalLayout_implant.addLayout(self.horizontalLayout_move_Xaxis)

        # --------------Y轴位移------------------------------------------------------------------------------------------
        # Implant Move on Y axis-------------------------------------------------------------------
        self.implantSlider_M_Yaxis = ImplantAdjustSlider(self,max_value=100,min_value=-100)
        self.horizontalLayout_move_Yaxis = self.implantSlider_M_Yaxis.horizontal_layout
        self.label_regis_move_Yaxis = self.implantSlider_M_Yaxis.label
        self.horizontalSlider_implant_move_Yaxis = self.implantSlider_M_Yaxis.horizontal_slider
        self.verticalLayout_implant.addLayout(self.horizontalLayout_move_Yaxis)

        # --------------Z轴位移------------------------------------------------------------------------------------------
        # Implant Move on Z axis-------------------------------------------------------------------
        self.implantSlider_M_Zaxis = ImplantAdjustSlider(self, max_value=100, min_value=-100)
        self.horizontalLayout_move_Zaxis = self.implantSlider_M_Zaxis.horizontal_layout
        self.label_regis_move_Zaxis = self.implantSlider_M_Zaxis.label
        self.horizontalSlider_implant_move_Zaxis = self.implantSlider_M_Zaxis.horizontal_slider
        self.verticalLayout_implant.addLayout(self.horizontalLayout_move_Zaxis)

        # ----------------显示列表----------------------------------------------------------------------------
        self.ToothID_Implant_QStringList = QtCore.QStringListModel(self.widget_implant)
        self.ToothID_Implant_QListView = QtWidgets.QListView(self.widget_implant)
        self.ToothID_Implant_QListView.setObjectName("ToothID_Implant_QListView")
        self.ToothID_Implant_QListView.setModel(self.ToothID_Implant_QStringList)
        self.ToothID_Implant_QListView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ToothID_Implant_QStringList.insertRows(self.ToothID_Implant_QStringList.rowCount(), 1)
        index = self.ToothID_Implant_QStringList.index(self.ToothID_Implant_QStringList.rowCount() - 1)
        self.ToothID_Implant_QStringList.setData(index, WindowConstant.TOOTH_IMPLANT_LIST)
        self.verticalLayout_implant.addWidget(self.ToothID_Implant_QListView)


        self.translateUi()

    def translateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.label_implant.setText(_translate("MainWindow", WindowConstant.IMPLANT_WIDGET_LABEL))
        self.label_ToothID.setText(_translate("MainWindow", WindowConstant.TOOTH_ID_LABEL))
        self.label_ToothImplant.setText(_translate("MainWindow", WindowConstant.IMPLANT_LABEL))
        self.label_implant_direction.setText(_translate("MainWindow", WindowConstant.IMPLANT_DIRECTION))
        self.pushButton_implant.setText(_translate("MainWindow", WindowConstant.PUT_IMPLANT_BUTTON))
        self.pushButton_crosshair_axis_orthogonal.setText(_translate("MainWindow", WindowConstant.CROSSHAIR_AXIS_ORTHOGONAL))
        self.label_regis_XY_adjust.setText(_translate("MainWindow",WindowConstant.REGIS_XY_ADJUST ))
        self.label_regis_YZ_adjust.setText(_translate("MainWindow", WindowConstant.REGIS_YZ_ADJUST))
        self.label_regis_XZ_adjust.setText(_translate("MainWindow", WindowConstant.REGIS_XZ_ADJUST))
        self.label_regis_move_Xaxis.setText(_translate("MainWindow", WindowConstant.REGIS_MOVE_X_AXIS))
        self.label_regis_move_Yaxis.setText(_translate("MainWindow", WindowConstant.REGIS_MOVE_Y_AXIS))
        self.label_regis_move_Zaxis.setText(_translate("MainWindow", WindowConstant.REGIS_MOVE_Z_AXIS))
        self.pushButton_adjust_imp.setText(_translate("MainWindow", WindowConstant.ADJUST_IMPLANT_BUTTON))