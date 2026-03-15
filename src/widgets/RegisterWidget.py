# -*- coding: utf-8 -*-
# @Time    : 2024/10/10 17:14
#
# @Author  : Jianjun Tong
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox

from src.constant.WindowConstant import WindowConstant
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font


class Register:
    def __init__(self):
        self.widget = None

    def init_widget(self):
        # ----------------------配准工具栏-----------------------------------------------------
        self.widget_registering = QtWidgets.QWidget(self.widget)
        self.widget_registering.hide()
        self.widget_registering.setObjectName("widget_registering")
        self.widget_registering.setMinimumSize(QtCore.QSize(350, 220))
        self.widget_registering.setMaximumSize(QtCore.QSize(400, 250))
        self.widget_registering.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)

        self.verticalLayout_registering = QtWidgets.QVBoxLayout(self.widget_registering)
        self.verticalLayout_registering.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_registering.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.verticalLayout_registering.setAlignment(Qt.AlignTop)
        self.verticalLayout_registering.setObjectName("verticalLayout_registering")

        self.label_regist = QtWidgets.QLabel(self.widget_registering)
        self.label_regist.setObjectName("label_regist")
        self.label_regist.setStyleSheet(APPVisualStyle.WIDGET_LABEL_COLOR)
        self.label_regist.setFont(Font.font)
        self.verticalLayout_registering.addWidget(self.label_regist)
        # -----------------------------------------------------------------
        self.horizontalLayout_anchor_visual = QtWidgets.QHBoxLayout()
        self.horizontalLayout_anchor_visual.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_anchor_visual.setObjectName("horizontalLayout_anchor_visual")

        self.pushButton_anchor_seg = QtWidgets.QPushButton(self.widget_registering)
        self.pushButton_anchor_seg.setObjectName("pushButton_anchor_seg")
        self.pushButton_anchor_seg.setFont(Font.font)
        self.horizontalLayout_anchor_visual.addWidget(self.pushButton_anchor_seg)

        self.pushButton_anchor_load = QtWidgets.QPushButton(self.widget_registering)
        self.pushButton_anchor_load.setObjectName("pushButton_anchor_load")
        self.pushButton_anchor_load.setFont(Font.font)
        self.anchor_load = False
        self.horizontalLayout_anchor_visual.addWidget(self.pushButton_anchor_load)

        self.verticalLayout_registering.addLayout(self.horizontalLayout_anchor_visual)

        # 配准锚点方向----------------------------------------------------------------------------------
        self.horizontalLayout_anchor_direction = QtWidgets.QHBoxLayout()
        self.horizontalLayout_anchor_direction.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_anchor_direction.setObjectName("horizontalLayout_anchor_direction")

        self.label_anchor_direction = QtWidgets.QLabel(self.widget_registering)
        self.label_anchor_direction.setObjectName("label_anchor_direction")
        self.horizontalLayout_anchor_direction.addWidget(self.label_anchor_direction)

        self.anchor_direction_cb_up = QCheckBox('Up', self.widget_registering)
        self.anchor_direction_cb_up.setCheckState(2)
        self.anchor_direction_cb_down = QCheckBox('Down', self.widget_registering)
        self.anchor_direction_cb_down.setCheckState(0)

        self.horizontalLayout_anchor_direction.addWidget(self.anchor_direction_cb_up)
        self.horizontalLayout_anchor_direction.addWidget(self.anchor_direction_cb_down)
        self.verticalLayout_registering.addLayout(self.horizontalLayout_anchor_direction)
        # --------------自动锚点选择---------------------------------------------------------------------------------------
        self.horizontalLayout_autoanchor = QtWidgets.QHBoxLayout()
        self.horizontalLayout_autoanchor.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_autoanchor.setObjectName("horizontalLayout_autoanchor")

        self.label_autoanchor = QtWidgets.QLabel(self.widget_registering)
        self.label_autoanchor.setObjectName("label_autoanchor")
        self.horizontalLayout_autoanchor.addWidget(self.label_autoanchor)

        self.autoanchor_cb1 = QCheckBox('1', self.widget_registering)
        self.autoanchor_cb2 = QCheckBox('2', self.widget_registering)
        self.autoanchor_cb3 = QCheckBox('3', self.widget_registering)
        self.autoanchor_cb4 = QCheckBox('4', self.widget_registering)
        self.autoanchor_cb5 = QCheckBox('5', self.widget_registering)
        self.autoanchor_cb6 = QCheckBox('6', self.widget_registering)
        self.autoanchor_cb7 = QCheckBox('7', self.widget_registering)
        self.autoanchor_cb8 = QCheckBox('8', self.widget_registering)

        self.autoanchor_cb1.setEnabled(False)
        self.autoanchor_cb2.setEnabled(False)
        self.autoanchor_cb3.setEnabled(False)
        self.autoanchor_cb4.setEnabled(False)
        self.autoanchor_cb5.setEnabled(False)
        self.autoanchor_cb6.setEnabled(False)
        self.autoanchor_cb7.setEnabled(False)
        self.autoanchor_cb8.setEnabled(False)

        self.horizontalLayout_autoanchor.addWidget(self.autoanchor_cb1)
        self.horizontalLayout_autoanchor.addWidget(self.autoanchor_cb2)
        self.horizontalLayout_autoanchor.addWidget(self.autoanchor_cb3)
        self.horizontalLayout_autoanchor.addWidget(self.autoanchor_cb4)
        self.horizontalLayout_autoanchor.addWidget(self.autoanchor_cb5)
        self.horizontalLayout_autoanchor.addWidget(self.autoanchor_cb6)
        self.horizontalLayout_autoanchor.addWidget(self.autoanchor_cb7)
        self.horizontalLayout_autoanchor.addWidget(self.autoanchor_cb8)
        self.verticalLayout_registering.addLayout(self.horizontalLayout_autoanchor)

        # --------------手动锚点选择--------------------------------------------------------------------------------------
        self.horizontalLayout_manualanchor = QtWidgets.QHBoxLayout()
        self.horizontalLayout_manualanchor.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_manualanchor.setObjectName("horizontalLayout_manualanchor")

        self.label_manualanchor = QtWidgets.QLabel(self.widget_registering)
        self.label_manualanchor.setObjectName("label_manualanchor")
        self.horizontalLayout_manualanchor.addWidget(self.label_manualanchor)

        self.manualanchor_cb1 = QCheckBox('1', self.widget_registering)
        self.manualanchor_cb2 = QCheckBox('2', self.widget_registering)
        self.manualanchor_cb3 = QCheckBox('3', self.widget_registering)
        self.manualanchor_cb4 = QCheckBox('4', self.widget_registering)
        self.manualanchor_cb5 = QCheckBox('5', self.widget_registering)
        self.manualanchor_cb6 = QCheckBox('6', self.widget_registering)
        self.manualanchor_cb7 = QCheckBox('7', self.widget_registering)
        self.manualanchor_cb8 = QCheckBox('8', self.widget_registering)

        self.manualanchor_cb1.setEnabled(False)
        self.manualanchor_cb2.setEnabled(False)
        self.manualanchor_cb3.setEnabled(False)
        self.manualanchor_cb4.setEnabled(False)
        self.manualanchor_cb5.setEnabled(False)
        self.manualanchor_cb6.setEnabled(False)
        self.manualanchor_cb7.setEnabled(False)
        self.manualanchor_cb8.setEnabled(False)

        self.horizontalLayout_manualanchor.addWidget(self.manualanchor_cb1)
        self.horizontalLayout_manualanchor.addWidget(self.manualanchor_cb2)
        self.horizontalLayout_manualanchor.addWidget(self.manualanchor_cb3)
        self.horizontalLayout_manualanchor.addWidget(self.manualanchor_cb4)
        self.horizontalLayout_manualanchor.addWidget(self.manualanchor_cb5)
        self.horizontalLayout_manualanchor.addWidget(self.manualanchor_cb6)
        self.horizontalLayout_manualanchor.addWidget(self.manualanchor_cb7)
        self.horizontalLayout_manualanchor.addWidget(self.manualanchor_cb8)
        self.verticalLayout_registering.addLayout(self.horizontalLayout_manualanchor)
        # --------------------------------------------------------------------------------------------------------------
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")

        self.pushButton_anchor_reg = QtWidgets.QPushButton(self.widget_registering)
        self.pushButton_anchor_reg.setObjectName("pushButton_anchor_reg")
        self.pushButton_anchor_reg.setFont(Font.font)
        self.horizontalLayout_8.addWidget(self.pushButton_anchor_reg)

        self.pushButton_reg_adjust = QtWidgets.QPushButton(self.widget_registering)
        self.pushButton_reg_adjust.setObjectName("pushButton_reg_adjust")
        self.pushButton_reg_adjust.setFont(Font.font)
        self.horizontalLayout_8.addWidget(self.pushButton_reg_adjust)
        self.verticalLayout_registering.addLayout(self.horizontalLayout_8)
        # =================微调滑条======================================================
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        # ----------------------1. X轴位移------------------------------
        self.label_regis_x_adjust = QtWidgets.QLabel(self.widget_registering)
        self.label_regis_x_adjust.setObjectName("label_regis_x_adjust")
        self.horizontalLayout_9.addWidget(self.label_regis_x_adjust)

        self.horizontalSlider_X_Axis_Move = QtWidgets.QSlider(self.widget_registering)
        self.horizontalSlider_X_Axis_Move.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_X_Axis_Move.setObjectName("horizontalSlider_X_Axis_Move")
        self.horizontalSlider_X_Axis_Move.setMaximum(10)
        self.horizontalSlider_X_Axis_Move.setMinimum(-10)
        self.horizontalSlider_X_Axis_Move.setFixedHeight(16)
        self.horizontalSlider_X_Axis_Move.setSingleStep(1)
        self.X_Axis_Move_value = 0
        self.horizontalLayout_9.addWidget(self.horizontalSlider_X_Axis_Move)
        # ----------------------2. X轴旋转------------------------------
        self.label_regis_x_rotate = QtWidgets.QLabel(self.widget_registering)
        self.label_regis_x_rotate.setObjectName("label_regis_x_rotate")
        self.horizontalLayout_9.addWidget(self.label_regis_x_rotate)

        self.horizontalSlider_X_Axis_Angle = QtWidgets.QSlider(self.widget_registering)
        self.horizontalSlider_X_Axis_Angle.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_X_Axis_Angle.setObjectName("horizontalSlider_X_Axis_Angle")
        self.horizontalSlider_X_Axis_Angle.setMaximum(10)
        self.horizontalSlider_X_Axis_Angle.setMinimum(-10)
        self.horizontalSlider_X_Axis_Angle.setFixedHeight(16)
        self.horizontalSlider_X_Axis_Angle.setSingleStep(1)
        self.X_Axis_Angle_value = 0

        self.horizontalLayout_9.addWidget(self.horizontalSlider_X_Axis_Angle)
        self.verticalLayout_registering.addLayout(self.horizontalLayout_9)
        # ----------------------2. Y轴位移------------------------------
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")

        self.label_regis_y_adjust = QtWidgets.QLabel(self.widget_registering)
        self.label_regis_y_adjust.setObjectName("label_regis_y_adjust")
        self.horizontalLayout_10.addWidget(self.label_regis_y_adjust)

        self.horizontalSlider_Y_Axis_Move = QtWidgets.QSlider(self.widget_registering)
        self.horizontalSlider_Y_Axis_Move.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_Y_Axis_Move.setMaximum(10)
        self.horizontalSlider_Y_Axis_Move.setMinimum(-10)
        self.horizontalSlider_Y_Axis_Move.setFixedHeight(16)
        self.horizontalSlider_Y_Axis_Move.setSingleStep(1)
        self.Y_Axis_Move_value = 0
        self.horizontalLayout_10.addWidget(self.horizontalSlider_Y_Axis_Move)
        # ----------------------4. Y轴旋转------------------------------
        self.label_regis_y_rotate = QtWidgets.QLabel(self.widget_registering)
        self.label_regis_y_rotate.setObjectName("label_regis_y_rotate")
        self.horizontalLayout_10.addWidget(self.label_regis_y_rotate)

        self.horizontalSlider_Y_Axis_Angle = QtWidgets.QSlider(self.widget_registering)
        self.horizontalSlider_Y_Axis_Angle.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_Y_Axis_Angle.setObjectName("horizontalSlider_Y_Axis_Angle")
        self.horizontalSlider_Y_Axis_Angle.setMaximum(10)
        self.horizontalSlider_Y_Axis_Angle.setMinimum(-10)
        self.horizontalSlider_Y_Axis_Angle.setFixedHeight(16)
        self.horizontalSlider_Y_Axis_Angle.setSingleStep(1)
        self.Y_Axis_Angle_value = 0
        self.horizontalLayout_10.addWidget(self.horizontalSlider_Y_Axis_Angle)
        self.verticalLayout_registering.addLayout(self.horizontalLayout_10)
        # ----------------------5. Z轴位移------------------------------
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")

        self.label_regis_z_adjust = QtWidgets.QLabel(self.widget_registering)
        self.label_regis_z_adjust.setObjectName("label_regis_z_adjust")
        self.horizontalLayout_11.addWidget(self.label_regis_z_adjust)

        self.horizontalSlider_Z_Axis_Move = QtWidgets.QSlider(self.widget_registering)
        self.horizontalSlider_Z_Axis_Move.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_Z_Axis_Move.setObjectName("horizontalSlider_Z_Axis_Move")
        self.horizontalSlider_Z_Axis_Move.setMaximum(10)
        self.horizontalSlider_Z_Axis_Move.setMinimum(-10)
        self.horizontalSlider_Z_Axis_Move.setFixedHeight(16)
        self.horizontalSlider_Z_Axis_Move.setSingleStep(1)
        self.Z_Axis_Move_value = 0
        self.horizontalLayout_11.addWidget(self.horizontalSlider_Z_Axis_Move)
        # ----------------------6. Z轴旋转------------------------------
        self.label_regis_z_rotate = QtWidgets.QLabel(self.widget_registering)
        self.label_regis_z_rotate.setObjectName("label_regis_z_rotate")
        self.horizontalLayout_11.addWidget(self.label_regis_z_rotate)

        self.horizontalSlider_Z_Axis_Angle = QtWidgets.QSlider(self.widget_registering)
        self.horizontalSlider_Z_Axis_Angle.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_Z_Axis_Angle.setObjectName("horizontalSlider_Z_Axis_Angle")
        self.horizontalLayout_11.addWidget(self.horizontalSlider_Z_Axis_Angle)
        self.horizontalSlider_Z_Axis_Angle.setMaximum(10)
        self.horizontalSlider_Z_Axis_Angle.setMinimum(-10)
        self.horizontalSlider_Z_Axis_Angle.setFixedHeight(16)
        self.horizontalSlider_Z_Axis_Angle.setSingleStep(1)
        self.Z_Axis_Angle_value = 0
        self.verticalLayout_registering.addLayout(self.horizontalLayout_11)

        self.translateUi()

    def translateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.label_regist.setText(_translate("MainWindow", WindowConstant.REGISTER_WIDGET_LABEL))
        self.pushButton_anchor_seg.setText(_translate("MainWindow", WindowConstant.ANCHOR_SEG_BUTTON))
        self.pushButton_anchor_load.setText(_translate("MainWindow", WindowConstant.ANCHOR_LOAD_BUTTON))
        self.label_anchor_direction.setText(_translate("MainWindow", WindowConstant.ANCHOR_DIRECTION))
        self.label_autoanchor.setText(_translate("MainWindow", WindowConstant.AUTO_ANCHOR))
        self.label_manualanchor.setText(_translate("MainWindow", WindowConstant.MANUAL_ANCHOR))
        self.pushButton_anchor_reg.setText(_translate("MainWindow", WindowConstant.ANCHOR_REG_BUTTON))
        self.pushButton_reg_adjust.setText(_translate("MainWindow", WindowConstant.REG_ADJUST_BUTTON))
        self.label_regis_x_adjust.setText(_translate("MainWindow", WindowConstant.REGIS_MOVE_X_AXIS))
        self.label_regis_x_rotate.setText(_translate("MainWindow", WindowConstant.REGIS_X_ROATE))
        self.label_regis_y_adjust.setText(_translate("MainWindow", WindowConstant.REGIS_MOVE_Y_AXIS))
        self.label_regis_y_rotate.setText(_translate("MainWindow", WindowConstant.REGIS_Y_ROATE))
        self.label_regis_z_adjust.setText(_translate("MainWindow", WindowConstant.REGIS_MOVE_Z_AXIS))
        self.label_regis_z_rotate.setText(_translate("MainWindow", WindowConstant.REGIS_Z_ROATE))
