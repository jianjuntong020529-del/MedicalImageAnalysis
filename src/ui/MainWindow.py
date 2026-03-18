# -*- coding: utf-8 -*-
# @Time    : 2024/10/8 17:06
#
# @Author  : Jianjun Tong
import vtk
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from src.constant.QIconConstant import QIconConstant
from src.constant.WindowConstant import WindowConstant
from src.constant.ParamConstant import ParamConstant
from src.controller.AnnotationController import AnnotationController
from src.controller.ComputeParameterController import ComputeParameterController
from src.controller.ContrastController import ContrastController
from src.controller.DentalImplantController import DentalImplantController
from src.controller.MenuBarController import MenuBarController
from src.controller.RegisterController import RegisterController
from src.controller.ToolBarController import ToolBarController
from src.model.BaseModel import BaseModel
from src.model.ToolBarWidgetModel import ToolBarWidget
from src.style.AppVisualStyle import APPVisualStyle
from src.widgets.QtOrthoViewerWidget import QtOrthoViewer
from src.model.OrthoViewerModel import OrthoViewerModel

# 关闭error弹窗
error = vtk.vtkOutputWindow
error.SetGlobalWarningDisplay(0)


class Ui_MainWindow(object):
    def __init__(self):
        self.implant_path = ParamConstant.IMPLANT_PATH
        self.output_file_path = ParamConstant.OUTPUT_FILE_PATH
        self.subject_name = ParamConstant.SUBJECT_NAME

    def setupUi(self, QMainWindow):
        QMainWindow.setWindowTitle(WindowConstant.WINDOW_TITLE)

        # 设置背景颜色
        QMainWindow.setStyleSheet(APPVisualStyle.BACKGROUND_COLOR)

        # 窗口大小
        QMainWindow.resize(1286, 1073)

        # 软件图标
        QMainWindow.setWindowIcon(QtGui.QIcon(QIconConstant.WINDOW_ICON))

        self.centralwidget = QtWidgets.QWidget(QMainWindow)
        self.widget = QtWidgets.QWidget(self.centralwidget)

        # 系统整体布局
        self.system_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.system_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.system_layout.addWidget(self.widget)

        # Data
        self.baseModelClass = BaseModel()
        # 横截面
        self.AxialOrthoViewer = QtOrthoViewer(self.baseModelClass, self.widget, "Axial")
        # 矢状面
        self.SagittalOrthoViewer = QtOrthoViewer(self.baseModelClass, self.widget, "Sagittal")
        # 冠状面
        self.CoronalOrthoViewer = QtOrthoViewer(self.baseModelClass, self.widget, "Coronal")
        # 3D viewer
        self.VolumeOrthoViewer = QtOrthoViewer(self.baseModelClass, self.widget, "3D Viewer")
        # 传递视图数据
        self.OrthoViewerModel = OrthoViewerModel(self.AxialOrthoViewer, self.SagittalOrthoViewer,
                                                 self.CoronalOrthoViewer, self.VolumeOrthoViewer)

        # 四视图布局
        self.four_view_layout = QtWidgets.QVBoxLayout()
        self.four_view_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        # 横断面，矢状面窗口布局
        self.xy_yz_horizontal_layout = QtWidgets.QHBoxLayout()
        self.xy_yz_horizontal_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        self.xy_yz_horizontal_layout.addWidget(self.AxialOrthoViewer.widget)
        self.xy_yz_horizontal_layout.addWidget(self.AxialOrthoViewer.slider)
        self.xy_yz_horizontal_layout.addWidget(self.SagittalOrthoViewer.widget)
        self.xy_yz_horizontal_layout.addWidget(self.SagittalOrthoViewer.slider)

        # verticalSLider_XY的label 与 verticalSLider_YZ 的布局
        self.labelxy_labelyz_horizontal_layout = QtWidgets.QHBoxLayout()
        self.labelxy_labelyz_horizontal_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        self.labelxy_labelyz_horizontal_layout.addWidget(self.AxialOrthoViewer.slider_label)
        self.labelxy_labelyz_horizontal_layout.addWidget(self.SagittalOrthoViewer.slider_label)

        self.xy_yz_label_vertical_layout = QtWidgets.QVBoxLayout()
        self.xy_yz_label_vertical_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.xy_yz_label_vertical_layout.addLayout(self.xy_yz_horizontal_layout)
        self.xy_yz_label_vertical_layout.addLayout(self.labelxy_labelyz_horizontal_layout)
        self.four_view_layout.addLayout(self.xy_yz_label_vertical_layout)

        # 冠状面窗口 XZ 与 体绘制窗口的布局
        self.xz_volume_label_vertical_layout = QtWidgets.QVBoxLayout()
        self.xz_volume_label_vertical_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        self.xz_volume_horizontal_layout = QtWidgets.QHBoxLayout()
        self.xz_volume_horizontal_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        self.xz_volume_horizontal_layout.addWidget(self.CoronalOrthoViewer.widget)
        self.xz_volume_horizontal_layout.addWidget(self.CoronalOrthoViewer.slider)

        self.xz_volume_horizontal_layout.addWidget(self.VolumeOrthoViewer.widget)
        self.xz_volume_horizontal_layout.addWidget(self.VolumeOrthoViewer.slider)
        self.xz_volume_horizontal_layout.setStretch(0, 10)
        self.xz_volume_horizontal_layout.setStretch(1, 1)
        self.xz_volume_horizontal_layout.setStretch(2, 10)
        self.xz_volume_horizontal_layout.setStretch(3, 1)
        self.xz_volume_label_vertical_layout.addLayout(self.xz_volume_horizontal_layout)

        self.labelxz_labelvolume_horizontal_layout = QtWidgets.QHBoxLayout()
        self.labelxz_labelvolume_horizontal_layout.setSpacing(4)

        self.labelxz_labelvolume_horizontal_layout.addWidget(self.CoronalOrthoViewer.slider_label)
        self.labelxz_labelvolume_horizontal_layout.addWidget(self.VolumeOrthoViewer.slider_label)

        self.xz_volume_label_vertical_layout.addLayout(self.labelxz_labelvolume_horizontal_layout)

        self.four_view_layout.addLayout(self.xz_volume_label_vertical_layout)
        self.system_layout.addLayout(self.four_view_layout, 7)

        QMainWindow.setCentralWidget(self.centralwidget)

        # 工具栏布局
        self.tool_bar_layout = QtWidgets.QVBoxLayout()
        self.tool_bar_layout.setAlignment(Qt.AlignTop)
        self.tool_bar_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        # 状态栏
        self.toolBarController = ToolBarController(self.baseModelClass, self.OrthoViewerModel, QMainWindow)

        # 菜单栏
        self.menuBarController = MenuBarController(self.baseModelClass, self.OrthoViewerModel, self.toolBarController, QMainWindow)

        # 对比度调整栏
        self.contrast = ContrastController(self.baseModelClass, self.OrthoViewerModel, self.widget)
        self.tool_bar_layout.addWidget(self.contrast.widget_contrast)
        ToolBarWidget.contrast_widget = self.contrast

        # 植体工具栏
        self.implantController = DentalImplantController(self.baseModelClass, self.OrthoViewerModel, self.toolBarController, self.widget)
        self.tool_bar_layout.addWidget(self.implantController.widget_implant)
        ToolBarWidget.implant_widget = self.implantController

        # 配准工具栏
        self.registerController = RegisterController(self.baseModelClass, self.OrthoViewerModel, self.widget)
        self.tool_bar_layout.addWidget(self.registerController.widget_registering)
        ToolBarWidget.registering_widget = self.registerController

        # 植体参数计算
        self.computeParametersController = ComputeParameterController(self.baseModelClass, self.OrthoViewerModel, self.widget)
        self.tool_bar_layout.addWidget(self.computeParametersController.widget_parameters)
        ToolBarWidget.parameters_widget = self.computeParametersController

        # 分割标注栏
        self.annotationController = AnnotationController(self.baseModelClass, self.OrthoViewerModel, self.widget)
        self.tool_bar_layout.addWidget(self.annotationController.widget_labels)
        ToolBarWidget.annotation_widget = self.annotationController

        # 体绘制工具栏
        from src.controller.VolumeRenderController import VolumeRenderController
        self.volumeRenderController = VolumeRenderController(self.OrthoViewerModel, self.widget)
        self.tool_bar_layout.addWidget(self.volumeRenderController.widget_volume_render)
        ToolBarWidget.volume_render_widget = self.volumeRenderController

        self.system_layout.addLayout(self.tool_bar_layout, 2)

        self.translateUi(QMainWindow)
        QtCore.QMetaObject.connectSlotsByName(QMainWindow)

    def translateUi(self, QMainWindow):
        _translate = QtCore.QCoreApplication.translate
        QMainWindow.setWindowTitle(_translate("MainWindow", WindowConstant.WINDOW_TITLE))
        self.AxialOrthoViewer.slider_label.setText(_translate("MainWindow", WindowConstant.LABEL_SLICE))
        self.SagittalOrthoViewer.slider_label.setText(_translate("MainWindow", WindowConstant.LABEL_SLICE))
        self.CoronalOrthoViewer.slider_label.setText(_translate("MainWindow", WindowConstant.LABEL_SLICE))
        self.VolumeOrthoViewer.slider_label.setText(_translate("MainWindow", WindowConstant.LABEL_VOLUME))

