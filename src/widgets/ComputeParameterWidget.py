# -*- coding: utf-8 -*-
# @Time    : 2024/10/10 17:21
#
# @Author  : Jianjun Tong
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView

from src.constant.WindowConstant import WindowConstant
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font


class ComputeParameter:
    def __init__(self):
        self.widget = None

    def init_widget(self):
        self.widget_parameters = QtWidgets.QWidget(self.widget)
        self.widget_parameters.setObjectName("widget_parameters")
        self.widget_parameters.setMinimumSize(QtCore.QSize(350, 170))
        self.widget_parameters.setMaximumSize(QtCore.QSize(400, 170))
        self.widget_parameters.hide()
        self.widget_parameters.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)

        self.verticalLayout_parameters = QtWidgets.QVBoxLayout(self.widget_parameters)
        self.verticalLayout_parameters.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_parameters.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.verticalLayout_parameters.setAlignment(Qt.AlignTop)
        self.verticalLayout_parameters.setObjectName("verticalLayout_parameters")

        self.hboxlayout_button = QtWidgets.QHBoxLayout(self.widget_parameters)
        self.hboxlayout_button.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        self.pushButton_compute_process_parameters = QtWidgets.QPushButton(self.widget_parameters)
        self.pushButton_compute_process_parameters.setObjectName("pushButton_compute_process_parameters")
        self.pushButton_compute_process_parameters.setFont(Font.font)

        self.pushButton_clear_implant_actor = QtWidgets.QPushButton(self.widget_parameters)
        self.pushButton_clear_implant_actor.setObjectName("pushButton_clear_implant_actor")
        self.pushButton_clear_implant_actor.setFont(Font.font)

        self.hboxlayout_button.addWidget(self.pushButton_clear_implant_actor)
        self.hboxlayout_button.addWidget(self.pushButton_compute_process_parameters)

        self.tableWidget = QtWidgets.QTableWidget(self.widget_parameters)
        self.tableWidget.setColumnCount(5)
        font = self.tableWidget.horizontalHeader().font()
        font.setBold(True)
        self.tableWidget.horizontalHeader().setFont(font)
        self.tableWidget.setHorizontalHeaderLabels(WindowConstant.TABLE_HEADERS)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalLayout_parameters.addLayout(self.hboxlayout_button)
        self.verticalLayout_parameters.addWidget(self.tableWidget)
        self.translateUi()

    def translateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.pushButton_compute_process_parameters.setText(_translate("MainWindow", WindowConstant.COMPUTE_PARAMETERS))
        self.pushButton_clear_implant_actor.setText(_translate("QMainWindow", WindowConstant.CLEAR_IMPLANT_ACTOR))

