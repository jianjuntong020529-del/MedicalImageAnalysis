# -*- coding: utf-8 -*-
# @Time    : 2024/10/9 17:06
#
# @Author  : Jianjun Tong
from PyQt5 import QtWidgets, QtCore

from src.constant.WindowConstant import WindowConstant
from src.model.AnnotationEnableModel import AnnotationEnable
from src.model.OrthoViewerModel import OrthoViewerModel
from src.style.AppVisualStyle import APPVisualStyle
from src.widgets.ContrastWidget import Contrast


class MenuBarManager:
    def __init__(self):
        self.QMainWindow = None

    def init_menubar(self):
        self.menubar = QtWidgets.QMenuBar(self.QMainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1103, 30))
        self.menubar.setObjectName("menubar")
        self.menubar.setStyleSheet(APPVisualStyle.menubar_style)

        self.fileMenu = QtWidgets.QMenu(self.menubar)
        self.fileMenu.setObjectName("fileMenu")
        self.fileMenu.setStyleSheet(APPVisualStyle.menu_style)

        self.toolMenu = QtWidgets.QMenu(self.menubar)
        self.toolMenu.setObjectName("toolMenu")
        self.toolMenu.setStyleSheet(APPVisualStyle.menu_style)

        self.modelloadMenu = QtWidgets.QMenu(self.menubar)
        self.modelloadMenu.setObjectName("modelloadMenu")
        self.modelloadMenu.setStyleSheet(APPVisualStyle.menu_style)

        self.segmentation_menu = QtWidgets.QMenu(self.menubar)
        self.segmentation_menu.setObjectName("segmentation_menu")
        self.segmentation_menu.setStyleSheet(APPVisualStyle.menu_style)

        # 将主菜单栏添加到窗口中
        self.QMainWindow.setMenuBar(self.menubar)

        # 添加子菜单栏到主菜单栏中
        self.actionAdd_DiICOM_Data = QtWidgets.QAction(self.QMainWindow)
        self.actionAdd_DiICOM_Data.setObjectName("actionAdd_DiICOM_Data")

        self.actionAdd_IM0BIM_Data = QtWidgets.QAction(self.QMainWindow)
        self.actionAdd_IM0BIM_Data.setObjectName("actionAdd_IM0BIM_Data")

        self.actionAdd_NIFIT_Data = QtWidgets.QAction(self.QMainWindow)
        self.actionAdd_NIFIT_Data.setObjectName("actionAdd_NIFIT_Data")

        self.actionAdd_NPY_Data = QtWidgets.QAction(self.QMainWindow)
        self.actionAdd_NPY_Data.setObjectName("actionAdd_NPY_Data")

        self.actionAdd_STL_Data = QtWidgets.QAction(self.QMainWindow)
        self.actionAdd_STL_Data.setObjectName("actionAdd_STL_Data")
        self.actionAdd_STL_Data.setCheckable(True)

        self.action_generatePanormaic = QtWidgets.QAction(self.QMainWindow)
        self.action_generatePanormaic.setObjectName("action_generatePanormaic")

        self.action_toothLandmark_annotation = QtWidgets.QAction(self.QMainWindow)
        self.action_toothLandmark_annotation.setObjectName("action_toothLandmark_annotation")

        self.action_coronal_canal_annotation = QtWidgets.QAction(self.QMainWindow)
        self.action_coronal_canal_annotation.setObjectName("action_coronal_canal_annotation")

        self.action_nifti_segmentation_editor = QtWidgets.QAction(self.QMainWindow)
        self.action_nifti_segmentation_editor.setObjectName("action_nifti_segmentation_editor")

        self.action_volume_render_toolbar = QtWidgets.QAction(self.QMainWindow)
        self.action_volume_render_toolbar.setObjectName("action_volume_render_toolbar")
        self.action_volume_render_toolbar.setCheckable(True)

        self.action_view_layout = QtWidgets.QAction(self.QMainWindow)
        self.action_view_layout.setObjectName("action_view_layout")

        self.action_multi_slice_view = QtWidgets.QAction(self.QMainWindow)
        self.action_multi_slice_view.setObjectName("action_multi_slice_view")


        self.action_implant_toolbar = QtWidgets.QAction(self.QMainWindow)
        self.action_implant_toolbar.setObjectName("action_implant_toolbar")
        self.action_implant_toolbar.setCheckable(True)

        self.action_registration_toolbar = QtWidgets.QAction(self.QMainWindow)
        self.action_registration_toolbar.setObjectName("action_registration_toolbar")
        self.action_registration_toolbar.setCheckable(True)

        self.action_parameters_toolbar = QtWidgets.QAction(self.QMainWindow)
        self.action_parameters_toolbar.setObjectName("action_parameters_toolbar")
        self.action_parameters_toolbar.setCheckable(True)

        self.actionAdd_Load_Universal_model = QtWidgets.QAction(self.QMainWindow)
        self.actionAdd_Load_Universal_model.setObjectName("actionAdd_Load_Universal_model")

        self.actionAdd_Load_Lungseg_model = QtWidgets.QAction(self.QMainWindow)
        self.actionAdd_Load_Lungseg_model.setObjectName("actionAdd_Load_Lungseg_model")
        self.Flag_Load_model = False


        self.actionGroup = QtWidgets.QActionGroup(self.QMainWindow)
        self.actionGroup.setExclusive(False)

        # 创建分割菜单栏中的操作
        self.pointAction = QtWidgets.QAction(self.QMainWindow)
        self.pointAction.setObjectName("pointAction")
        self.pointAction.setCheckable(True)
        AnnotationEnable.pointAction = self.pointAction

        self.point_label = QtWidgets.QMenu(WindowConstant.POINT_TYPE, self.segmentation_menu)

        self.actionGroup = QtWidgets.QActionGroup(self.QMainWindow)
        # 添加子菜单项
        self.point_label_0 = QtWidgets.QAction(WindowConstant.POINT_LABEL_0, self.QMainWindow)
        self.point_label_0.setCheckable(True)
        self.point_label_0.setChecked(False)
        self.actionGroup.addAction(self.point_label_0)

        self.point_label_1 = QtWidgets.QAction(WindowConstant.POINT_LABEL_1, self.QMainWindow)
        self.point_label_1.setCheckable(True)
        self.point_label_1.setChecked(True)
        self.actionGroup.addAction(self.point_label_1)

        self.point_label.addAction(self.point_label_0)
        self.point_label.addAction(self.point_label_1)

        self.labelBoxAction = QtWidgets.QAction(self.QMainWindow)
        self.labelBoxAction.setObjectName("labelBoxAction")
        self.labelBoxAction.setCheckable(True)
        AnnotationEnable.labelBoxAction = self.labelBoxAction

        self.box_label = QtWidgets.QMenu(WindowConstant.BOUNDING_BOX_TYPE, self.segmentation_menu)
        self.boxlabel_actionGroup = QtWidgets.QActionGroup(self.QMainWindow)
        # 添加子菜单项
        self.box_label_single = QtWidgets.QAction(WindowConstant.BOUNDING_BOX_SINGLE, self.QMainWindow)
        self.box_label_single.setCheckable(True)
        self.box_label_single.setObjectName("Single")
        self.box_label_single.setChecked(True)
        self.boxlabel_actionGroup.addAction(self.box_label_single)

        self.box_label_multiple = QtWidgets.QAction(WindowConstant.BOUNDING_BOX_MULTIPLE, self.QMainWindow)
        self.box_label_multiple.setObjectName("Multiple")
        self.box_label_multiple.setCheckable(True)
        self.box_label_multiple.setChecked(False)
        self.boxlabel_actionGroup.addAction(self.box_label_multiple)

        self.box_label.addAction(self.box_label_single)
        self.box_label.addAction(self.box_label_multiple)

        self.segmentation_type = QtWidgets.QMenu(WindowConstant.SEGMENTATION_TYPE, self.segmentation_menu)
        self.segmentation_type_group = QtWidgets.QActionGroup(self.QMainWindow)

        self.segmentation_type_none = QtWidgets.QAction(WindowConstant.SEGMENTATION_NONE, self.QMainWindow)
        self.segmentation_type_none.setCheckable(True)
        self.segmentation_type_none.setChecked(True)
        self.segmentation_type_none.setObjectName("None")
        self.segmentation_type_group.addAction(self.segmentation_type_none)

        self.segmentation_type_sliceRange = QtWidgets.QAction(WindowConstant.SEGMENTATION_SLICE_RANGE, self.QMainWindow)
        self.segmentation_type_sliceRange.setCheckable(True)
        self.segmentation_type_sliceRange.setChecked(False)
        self.segmentation_type_sliceRange.setObjectName("Slice Range")
        self.segmentation_type_group.addAction(self.segmentation_type_sliceRange)

        self.segmentation_type.addAction(self.segmentation_type_none)
        self.segmentation_type.addAction(self.segmentation_type_sliceRange)

        self.startSegmentationAction = QtWidgets.QAction(self.QMainWindow)
        self.startSegmentationAction.setObjectName("startSegmentationAction")

        self.saveResultAction = QtWidgets.QAction(self.QMainWindow)
        self.saveResultAction.setObjectName("saveResultAction")
        self.saveResultAction.setCheckable(False)


        self.fileMenu.addAction(self.actionAdd_DiICOM_Data)
        self.fileMenu.addAction(self.actionAdd_IM0BIM_Data)
        self.fileMenu.addAction(self.actionAdd_NIFIT_Data)
        self.fileMenu.addAction(self.actionAdd_NPY_Data)
        self.fileMenu.addAction(self.actionAdd_STL_Data)

        self.toolMenu.addAction(self.action_generatePanormaic)
        self.toolMenu.addAction(self.action_toothLandmark_annotation)
        self.toolMenu.addAction(self.action_coronal_canal_annotation)
        self.toolMenu.addAction(self.action_implant_toolbar)
        self.toolMenu.addAction(self.action_registration_toolbar)
        self.toolMenu.addAction(self.action_parameters_toolbar)
        self.toolMenu.addAction(self.action_nifti_segmentation_editor)
        self.toolMenu.addAction(self.action_volume_render_toolbar)
        self.toolMenu.addAction(self.action_view_layout)

        self.modelloadMenu.addAction(self.actionAdd_Load_Universal_model)
        self.modelloadMenu.addAction(self.actionAdd_Load_Lungseg_model)

        self.segmentation_menu.addAction(self.pointAction)
        self.segmentation_menu.addMenu(self.point_label)
        self.segmentation_menu.addAction(self.labelBoxAction)
        self.segmentation_menu.addMenu(self.box_label)
        self.segmentation_menu.addMenu(self.segmentation_type)
        self.segmentation_menu.addAction(self.startSegmentationAction)
        self.segmentation_menu.addAction(self.saveResultAction)


        self.menubar.addAction(self.fileMenu.menuAction())
        self.menubar.addAction(self.toolMenu.menuAction())
        self.menubar.addAction(self.modelloadMenu.menuAction())
        self.menubar.addAction(self.segmentation_menu.menuAction())

        self.translateUi()

    def translateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.fileMenu.setTitle(_translate("MainWindow", WindowConstant.FILE_MENU))
        self.toolMenu.setTitle(_translate("MainWindow", WindowConstant.TOOL_MENU))
        self.segmentation_menu.setTitle(_translate("MainWindow", WindowConstant.SAM_MED2D_SEG))
        self.actionAdd_DiICOM_Data.setText(_translate("MainWindow", WindowConstant.ADD_DICOM))
        self.actionAdd_IM0BIM_Data.setText(_translate("MainWindow", WindowConstant.ADD_IM0))
        self.actionAdd_NIFIT_Data.setText(_translate("MainWindow", WindowConstant.ADD_NIFIT))
        self.actionAdd_NPY_Data.setText(_translate("MainWindow", WindowConstant.ADD_NPY))
        self.actionAdd_STL_Data.setText(_translate("MainWindow", WindowConstant.ADD_STL))
        self.action_generatePanormaic.setText(_translate("MainWindow", WindowConstant.ACTION_GENERATE_PANORMAIC))
        self.action_toothLandmark_annotation.setText(_translate("MainWindow", WindowConstant.ACTION_TOOTH_LANDMARK_ANNOTATION))
        self.action_coronal_canal_annotation.setText(_translate("MainWindow", WindowConstant.ACTION_CORONAL_CANAL_ANNOTATION))
        self.action_implant_toolbar.setText(_translate("MainWindow", WindowConstant.ACTION_IMPLANT_TOOLBAR))
        self.action_registration_toolbar.setText(_translate("MainWindow", WindowConstant.ACTION_REGISTRATION_TOOLBAR))
        self.action_parameters_toolbar.setText(_translate("MainWindow", WindowConstant.ACTION_PARAMETERS_TOOLBAR))
        self.pointAction.setText(_translate("MainWindow", WindowConstant.POINT))
        self.labelBoxAction.setText(_translate("MainWindow", WindowConstant.BOUNDING_BOX))
        self.startSegmentationAction.setText(_translate("MainWindow", WindowConstant.START_SEGMENTATION))
        self.saveResultAction.setText(_translate("MainWindow", WindowConstant.SAVE_SEGMENTATION_RESULTS))
        self.modelloadMenu.setTitle(_translate("MainWindow", WindowConstant.MODEL_LOAD))
        self.actionAdd_Load_Universal_model.setText(_translate("MainWindow", WindowConstant.LOAD_UNIVERSAL_MODEL))
        self.actionAdd_Load_Lungseg_model.setText(_translate("MainWindow", WindowConstant.LOAD_LUNGSEG_MODEL))
        self.action_nifti_segmentation_editor.setText(_translate("MainWindow", WindowConstant.ACTION_NIFTI_SEGMENTATION_EDITOR))
        self.action_volume_render_toolbar.setText(_translate("MainWindow", WindowConstant.ACTION_VOLUME_RENDER_TOOLBAR))
        self.action_view_layout.setText(_translate("MainWindow", WindowConstant.ACTION_VIEW_LAYOUT))

