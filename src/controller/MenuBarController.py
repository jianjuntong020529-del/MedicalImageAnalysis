# -*- coding: utf-8 -*-
# @Time    : 2024/10/8 17:05
#
# @Author  : Jianjun Tong
import glob
import os

import numpy as np
import pydicom
import vtk
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from medpy.io import load, save

from src.interactor_style.SegmentationInteractorStyle import LeftButtonPressEvent_Point, LeftButtonPressEvent_labelBox, MouseMoveEvent_labelBox
from src.constant.ParamConstant import ParamConstant
from src.core.tooth_landmark_detc.Tooth_LandmarkDect_CBCT import MaxMin_normalization_Intensity
from src.core.sam_med2d.sam_med2d_funcs import multiple_box_segmentation, single_box_segmentation, point_segmentation
from src.core.sam_med2d.segment_anything import sam_model_registry
from src.interactor_style.FourViewerInteractorStyle import MouseWheelForward, MouseWheelBackWard
from src.model.AnnotationEnableModel import AnnotationEnable
from src.model.BaseModel import BaseModel
from src.model.DataAndModelType import DataAndModelType
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.ToolBarEnableModel import ToolBarEnable
from src.model.ToolBarWidgetModel import ToolBarWidget
from src.model.ToothImplantListModel import ToothImplantList
from src.model.VolumeRenderModel import VolumeRender
from src.service.AnnotationService import AnnotationService
from src.service.MenuBarService import MenuBarService
from src.ui.GenweatePanomrmaicWindow import Generate_Panormaic_Widget
from src.ui.ToothLandmarkWindow import Tooth_Landmark
from src.utils.IM0AndBIMUtils import Save_BIM, convertNsave
from src.utils.globalVariables import *
from src.widgets.MenuBarWidget import MenuBarManager


class MenuBarController(MenuBarManager):
    def __init__(self, baseModelClass: BaseModel, viewer_model: OrthoViewerModel, toolBarController, QMainWindow):
        super(MenuBarController, self).__init__()

        self.baseModelClass = baseModelClass
        self.viewModel = viewer_model
        self.toolBarController = toolBarController
        self.QMainWindow = QMainWindow

        self.init_menubar()

        self.annotationService = AnnotationService(self.baseModelClass, self.viewModel)

        self.reader = baseModelClass.imageReader

        # XY 窗口
        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider

        # YZ 窗口
        self.verticalSlider_YZ = self.viewModel.SagittalOrthoViewer.slider

        # XZ 窗口
        self.verticalSlider_XZ = self.viewModel.CoronalOrthoViewer.slider

        self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
        self.iren_Volume = self.viewModel.VolumeOrthorViewer.renderWindowInteractor

        self.temp_actor = None

        self.menuBarService = MenuBarService(self.baseModelClass, self.viewModel)

        self.verticalSlider_XY.valueChanged.connect(self.valuechange1)
        self.verticalSlider_YZ.valueChanged.connect(self.valuechange2)
        self.verticalSlider_XZ.valueChanged.connect(self.valuechange3)

        self.actionAdd_DiICOM_Data.triggered.connect(self.on_actionAdd_DICOM_Data)
        self.actionAdd_IM0BIM_Data.triggered.connect(self.on_actionAdd_IM0BIM_Data)
        self.actionAdd_STL_Data.triggered.connect(self.on_actionAdd_STL_Data)
        self.actionAdd_Npy_Data.triggered,connect(self.on_actionAdd_Npy_Data)

        self.action_generatePanormaic.triggered.connect(self.on_action_generatePanormaic)
        self.action_toothLandmark_annotation.triggered.connect(self.on_action_tooth_landmark_annotation)
        self.action_implant_toolbar.triggered.connect(self.on_action_implant_toolbar)
        self.action_registration_toolbar.triggered.connect(self.on_action_registration_toolbar)
        self.action_parameters_toolbar.triggered.connect(self.on_action_parameters_toolbar)
        self.actionAdd_Load_Universal_model.triggered.connect(self.on_actionAdd_Load_Universal_model)
        self.actionAdd_Load_Lungseg_model.triggered.connect(self.on_actionAdd_Load_Lungseg_model)
        self.pointAction.triggered.connect(self.on_action_point)
        self.point_label_0.triggered.connect(self.select_point_label)
        self.point_label_1.triggered.connect(self.select_point_label)
        self.labelBoxAction.triggered.connect(self.on_action_labelBox)
        self.box_label_single.triggered.connect(self.select_box_label)
        self.box_label_multiple.triggered.connect(self.select_box_label)
        self.segmentation_type_none.triggered.connect(self.select_slice_range)
        self.segmentation_type_sliceRange.triggered.connect(self.select_slice_range)
        self.startSegmentationAction.triggered.connect(self.on_action_startSegmentation)
        self.saveResultAction.triggered.connect(self.on_action_saveResult)

    def on_action_implant_toolbar(self):
        print("打开植体工具栏")
        if ToolBarWidget.implant_widget.widget_implant.isHidden():
            ToolBarWidget.implant_widget.widget_implant.show()
        else:
            ToolBarWidget.implant_widget.widget_implant.hide()

    def on_action_registration_toolbar(self):
        print("打开配准工具栏")
        if ToolBarWidget.registering_widget.widget_registering.isHidden():
            ToolBarWidget.registering_widget.widget_registering.show()
        else:
            ToolBarWidget.registering_widget.widget_registering.hide()

    def on_action_parameters_toolbar(self):
        print("计算加工参数")
        if ToolBarWidget.parameters_widget.widget_parameters.isHidden():
            ToolBarWidget.parameters_widget.widget_parameters.show()
        else:
            ToolBarWidget.parameters_widget.widget_parameters.hide()

    def on_actionAdd_DICOM_Data(self):
        print("选择DICOM文件")
        old_path = getDirPath()
        path = QtWidgets.QFileDialog.getExistingDirectory(None, "选取文件夹")
        print("Selected path:", path)
        if path == "":
            if old_path == 'F:\CBCT_Register_version_12_7\testdata\\40':
                setFileIsEmpty(True)
                return
            else:
                path = old_path

        # 获取目录下的所有文件名
        files = os.listdir(path)

        # 检查是否存在DICOM文件
        dcm_files_exist = any(file.endswith(".dcm") for file in files)

        if not dcm_files_exist:
            print("该目录下没有DICOM文件数据")
            return

        DataAndModelType.DATA_TYPE = 'DICOM'

        try:
            ToolBarWidget.parameters_widget.tableWidget.clearContents()
            ToolBarWidget.parameters_widget.tableWidget.setRowCount(0)
        except:
            print("clear table fail!!!")

        try:
            ToolBarWidget.implant_widget.ToothID_Implant_QStringList.removeRows(1,
                                                                                ToolBarWidget.implant_widget.ToothID_Implant_QStringList.rowCount() - 1)
        except:
            print("clear tooth implant list failed")

        if ToolBarEnable.ruler_enable:
            self.toolBarController.toolBarService.clear_ruler()
            self.toolBarController.action_ruler.setChecked(False)
        if ToolBarEnable.paint_enable:
            self.toolBarController.toolBarService.clear_paint()
            self.toolBarController.action_paint.setChecked(False)
        if ToolBarEnable.pixel_enable:
            self.toolBarController.toolBarService.clear_pixel()
            self.toolBarController.action_pixel.setChecked(False)
        if ToolBarEnable.polyline_enable:
            self.toolBarController.toolBarService.clear_polyline()
            self.toolBarController.action_polyline.setChecked(False)
        if ToolBarEnable.crosshair_enable:
            self.toolBarController.toolBarService.clear_crosshair()
            self.toolBarController.action_crosshair.setChecked(False)
        if ToolBarEnable.angle_enable:
            self.toolBarController.toolBarService.clear_angle()
            self.toolBarController.action_angle.setChecked(False)
        if ToolBarEnable.roi_enable:
            self.toolBarController.toolBarService.clear_get_roi()
            self.toolBarController.action_get_roi.setChecked(False)
        if ToolBarEnable.dragging_enable:
            self.QMainWindow.setCursor(Qt.ArrowCursor)
            self.toolBarController.toolBarService.clear_dragging_image()
            self.toolBarController.action_dragging_image.setChecked(False)
        if self.pointAction.isChecked():
            self.toolBarController.toolBarService.disable_point_action()
        if self.labelBoxAction.isChecked():
            self.toolBarController.toolBarService.disable_label_box_action()
        self.toolBarController.toolBar.update()

        ToothImplantList.Tooth_Implant_File_List.clear()
        ToothImplantList.Tooth_Implant_File_List = []

        ToothImplantList.Tooth_Implant_Reg_File_List.clear()
        ToothImplantList.Tooth_Implant_Reg_File_List = []

        setDirPath(path)
        self.reader.SetDirectoryName(path)
        self.reader.Update()
        # 更新 Data Information
        self.baseModelClass.imageReader = self.reader
        self.baseModelClass.update_data_information()

        ParamConstant.ANNOTATION_SUBJECT_NAME = getDirPath().split('/')[-1]

        self.menuBarService.on_actionAdd_DICOM_Data()

    def on_actionAdd_IM0BIM_Data(self):
        print("选择IM0BIM文件")
        old_path = getDirPath()
        path = QtWidgets.QFileDialog.getOpenFileName(None, "选取文件", "", "*.IM0;;*.BIM")
        if path == "":
            if old_path == 'F:\CBCT_Register_version_12_7\testdata\\40':
                setFileIsEmpty(True)
                return
            else:
                path = old_path
        path = path[0]
        self.IM0path = path
        print(path)
        subname = path.split('/')[-1]
        subname = subname.split('.')[0]
        print(subname)
        # ----------------------IM0转化为DICOM-----------------------------------------------
        self.save_dicompath_temp = ParamConstant.OUTPUT_FILE_PATH + subname + '_temp/'
        if not os.path.exists(self.save_dicompath_temp):
            os.mkdir(self.save_dicompath_temp)
        else:
            for file in glob.glob(self.save_dicompath_temp + '*.dcm'):
                os.remove(file)
        os.system('mipg2dicom ' + path + ' ' + self.save_dicompath_temp)
        # ---------------------------------------------------------------------------------
        self.save_dicompath = ParamConstant.OUTPUT_FILE_PATH + subname + '/'
        if not os.path.exists(self.save_dicompath):
            os.mkdir(self.save_dicompath)
        else:
            for file in glob.glob(self.save_dicompath + '*.dcm'):
                os.remove(file)
        # --------------------------------------
        dicom_files = glob.glob(self.save_dicompath_temp + '*.dcm')
        dicom_files.sort()
        number_slices = len(dicom_files)
        for slice_ in range(number_slices):
            dicom_file = pydicom.dcmread(dicom_files[slice_])
            convertNsave(dicom_file, ParamConstant.IMAGE_DCM, self.save_dicompath, slice_)
            self.SliceThickness = dicom_file.SliceThickness
        # ---------------------------------------------------------------------------------

        # 获取目录下的所有文件名
        files = os.listdir(self.save_dicompath)
        # 检查是否存在DCM文件
        dcm_files_exist = any(file.endswith(".dcm") for file in files)

        if not dcm_files_exist:
            print("该目录下没有DCM文件数据")
            return

        DataAndModelType.DATA_TYPE = 'IM0'

        try:
            ToolBarWidget.parameters_widget.tableWidget.clearContents()
            ToolBarWidget.parameters_widget.tableWidget.setRowCount(0)
        except:
            print("clear table fail!!!")

        try:
            ToolBarWidget.implant_widget.ToothID_Implant_QStringList.removeRows(1,ToolBarWidget.implant_widget.ToothID_Implant_QStringList.rowCount() - 1)
        except:
            print("clear tooth implant list failed")

        if ToolBarEnable.ruler_enable:
            self.toolBarController.toolBarService.clear_ruler()
            self.toolBarController.action_ruler.setChecked(False)
        if ToolBarEnable.paint_enable:
            self.toolBarController.toolBarService.clear_paint()
            self.toolBarController.action_paint.setChecked(False)
        if ToolBarEnable.pixel_enable:
            self.toolBarController.toolBarService.clear_pixel()
            self.toolBarController.action_pixel.setChecked(False)
        if ToolBarEnable.polyline_enable:
            self.toolBarController.toolBarService.clear_polyline()
            self.toolBarController.action_polyline.setChecked(False)
        if ToolBarEnable.crosshair_enable:
            self.toolBarController.toolBarService.clear_crosshair()
            self.toolBarController.action_crosshair.setChecked(False)
        if ToolBarEnable.angle_enable:
            self.toolBarController.toolBarService.clear_angle()
            self.toolBarController.action_angle.setChecked(False)
        if ToolBarEnable.roi_enable:
            self.toolBarController.toolBarService.clear_get_roi()
            self.toolBarController.action_get_roi.setChecked(False)
        if ToolBarEnable.dragging_enable:
            self.QMainWindow.setCursor(Qt.ArrowCursor)
            self.toolBarController.toolBarService.clear_dragging_image()
            self.toolBarController.action_dragging_image.setChecked(False)
        if self.pointAction.isChecked():
            self.toolBarController.toolBarService.disable_point_action()
        if self.labelBoxAction.isChecked():
            self.toolBarController.toolBarService.disable_label_box_action()
        self.toolBarController.toolBar.update()

        ToothImplantList.Tooth_Implant_File_List.clear()
        ToothImplantList.Tooth_Implant_File_List = []

        ToothImplantList.Tooth_Implant_Reg_File_List.clear()
        ToothImplantList.Tooth_Implant_Reg_File_List = []

        setDirPath(self.save_dicompath)

        self.reader.SetDirectoryName(self.save_dicompath)
        self.reader.Update()
        # 更新 Data Information
        self.baseModelClass.imageReader = self.reader
        self.baseModelClass.update_data_information()

        self.menuBarService.on_actionAdd_IM0_Data(self.SliceThickness)

    def on_actionAdd_Npy_Data(self):
        print("选择npy文件")
        old_path = getDirPath()
        path = QtWidgets.QFileDialog.getOpenFileName(None, "选取文件", "", "*.npy")
        if path == "":
            if old_path == 'F:\CBCT_Register_version_12_7\testdata\\40':
                setFileIsEmpty(True)
                return
            else:
                path = old_path
        path = path[0]
        self.IM0path = path
        print(path)
        subname = path.split('/')[-1]
        subname = subname.split('.')[0]
        print(subname)
        # # ----------------------IM0转化为DICOM-----------------------------------------------
        # self.save_dicompath_temp = ParamConstant.OUTPUT_FILE_PATH + subname + '_temp/'
        # if not os.path.exists(self.save_dicompath_temp):
        #     os.mkdir(self.save_dicompath_temp)
        # else:
        #     for file in glob.glob(self.save_dicompath_temp + '*.dcm'):
        #         os.remove(file)
        # os.system('mipg2dicom ' + path + ' ' + self.save_dicompath_temp)
        # # ---------------------------------------------------------------------------------
        # self.save_dicompath = ParamConstant.OUTPUT_FILE_PATH + subname + '/'
        # if not os.path.exists(self.save_dicompath):
        #     os.mkdir(self.save_dicompath)
        # else:
        #     for file in glob.glob(self.save_dicompath + '*.dcm'):
        #         os.remove(file)
        # # --------------------------------------
        # dicom_files = glob.glob(self.save_dicompath_temp + '*.dcm')
        # dicom_files.sort()
        # number_slices = len(dicom_files)
        # for slice_ in range(number_slices):
        #     dicom_file = pydicom.dcmread(dicom_files[slice_])
        #     convertNsave(dicom_file, ParamConstant.IMAGE_DCM, self.save_dicompath, slice_)
        #     self.SliceThickness = dicom_file.SliceThickness
        # # ---------------------------------------------------------------------------------
        #
        # # 获取目录下的所有文件名
        # files = os.listdir(self.save_dicompath)
        # # 检查是否存在DCM文件
        # dcm_files_exist = any(file.endswith(".dcm") for file in files)
        #
        # if not dcm_files_exist:
        #     print("该目录下没有DCM文件数据")
        #     return
        #
        # DataAndModelType.DATA_TYPE = 'IM0'
        #
        # try:
        #     ToolBarWidget.parameters_widget.tableWidget.clearContents()
        #     ToolBarWidget.parameters_widget.tableWidget.setRowCount(0)
        # except:
        #     print("clear table fail!!!")
        #
        # try:
        #     ToolBarWidget.implant_widget.ToothID_Implant_QStringList.removeRows(1,
        #                                                                         ToolBarWidget.implant_widget.ToothID_Implant_QStringList.rowCount() - 1)
        # except:
        #     print("clear tooth implant list failed")
        #
        # if ToolBarEnable.ruler_enable:
        #     self.toolBarController.toolBarService.clear_ruler()
        #     self.toolBarController.action_ruler.setChecked(False)
        # if ToolBarEnable.paint_enable:
        #     self.toolBarController.toolBarService.clear_paint()
        #     self.toolBarController.action_paint.setChecked(False)
        # if ToolBarEnable.pixel_enable:
        #     self.toolBarController.toolBarService.clear_pixel()
        #     self.toolBarController.action_pixel.setChecked(False)
        # if ToolBarEnable.polyline_enable:
        #     self.toolBarController.toolBarService.clear_polyline()
        #     self.toolBarController.action_polyline.setChecked(False)
        # if ToolBarEnable.crosshair_enable:
        #     self.toolBarController.toolBarService.clear_crosshair()
        #     self.toolBarController.action_crosshair.setChecked(False)
        # if ToolBarEnable.angle_enable:
        #     self.toolBarController.toolBarService.clear_angle()
        #     self.toolBarController.action_angle.setChecked(False)
        # if ToolBarEnable.roi_enable:
        #     self.toolBarController.toolBarService.clear_get_roi()
        #     self.toolBarController.action_get_roi.setChecked(False)
        # if ToolBarEnable.dragging_enable:
        #     self.QMainWindow.setCursor(Qt.ArrowCursor)
        #     self.toolBarController.toolBarService.clear_dragging_image()
        #     self.toolBarController.action_dragging_image.setChecked(False)
        # if self.pointAction.isChecked():
        #     self.toolBarController.toolBarService.disable_point_action()
        # if self.labelBoxAction.isChecked():
        #     self.toolBarController.toolBarService.disable_label_box_action()
        # self.toolBarController.toolBar.update()
        #
        # ToothImplantList.Tooth_Implant_File_List.clear()
        # ToothImplantList.Tooth_Implant_File_List = []
        #
        # ToothImplantList.Tooth_Implant_Reg_File_List.clear()
        # ToothImplantList.Tooth_Implant_Reg_File_List = []
        #
        # setDirPath(self.save_dicompath)
        #
        # self.reader.SetDirectoryName(self.save_dicompath)
        # self.reader.Update()
        # # 更新 Data Information
        # self.baseModelClass.imageReader = self.reader
        # self.baseModelClass.update_data_information()
        #
        # self.menuBarService.on_actionAdd_IM0_Data(self.SliceThickness)

    def LoadSTL(self, filename):
        bounds = self.baseModelClass.bounds
        self.center0 = (bounds[1] + bounds[0]) / 2.0
        self.center1 = (bounds[3] + bounds[2]) / 2.0
        self.center2 = (bounds[5] + bounds[4]) / 2.0
        transform = vtk.vtkTransform()
        transform.Translate(self.center0, self.center1, self.center2)

        reader = vtk.vtkSTLReader()  # 读取stl文件
        reader.SetFileName(filename)  # 文件名
        mapper = vtk.vtkPolyDataMapper()  # 将多边形数据映射到图形基元
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkLODActor()
        actor.SetMapper(mapper)
        actor.SetUserTransform(transform)
        return actor  # 表示渲染场景中的实体

    def on_actionAdd_STL_Data(self):
        self.renderer_volume = self.viewModel.VolumeOrthorViewer.renderer
        if self.actionAdd_STL_Data.isChecked():
            print("选择STL文件")
            path = QtWidgets.QFileDialog.getOpenFileName(None, "选择STL文件", filter="*.stl")
            if path == "":
                return
            try:
                self.renderer_volume.RemoveActor(VolumeRender.actor_stl)
            except:
                print('actor_stl is not found!!!')
            try:
                self.renderer_volume.RemoveActor(VolumeRender.volume_cbct)
            except:
                print('volume_cbct is not found!!!')
            print(path)
            self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
            actor_stl = self.LoadSTL(path[0])
            self.renderer_volume.AddActor(actor_stl)
            self.vtkWidget_Volume.Render()
            VolumeRender.actor_stl = actor_stl
        else:
            print("恢复体渲染")
            try:
                self.renderer_volume.RemoveActor(VolumeRender.actor_stl)
            except:
                print('actor_stl is not found!!!')
            try:
                self.renderer_volume.AddActor(VolumeRender.volume_cbct)
            except:
                print('volume_cbct is not found!!!')

    def valuechange1(self):
        self.menuBarService.valuechange1()

    def valuechange2(self):
        self.menuBarService.valuechange2()

    def valuechange3(self):
        self.menuBarService.valuechange3()

    def on_action_generatePanormaic(self):
        print("全景图生成功能")
        if getFileIsEmpty():
            print("未导入文件，无法进行牙弓线标注！")
            return
        self.panormaic_window = Generate_Panormaic_Widget(self.baseModelClass)
        self.panormaic_window.show()

    def on_action_tooth_landmark_annotation(self):
        print("牙齿标记标注")
        if getFileIsEmpty():
            print("未导入文件，无法进行牙齿标注！")
            return
        self.tooth_landmark_window = Tooth_Landmark(self.baseModelClass, self.viewModel)
        self.tooth_landmark_window.show()

    def on_action_point(self):
        if getFileIsEmpty():
            print("文件未导入")
            return
        self.update_axial_viewer()
        if self.pointAction.isChecked():
            ToolBarWidget.annotation_widget.widget_labels.show()
            if ToolBarEnable.ruler_enable:
                self.toolBarController.toolBarService.clear_ruler()
                self.toolBarController.action_ruler.setChecked(False)
            if ToolBarEnable.paint_enable:
                self.toolBarController.toolBarService.clear_paint()
                self.toolBarController.action_paint.setChecked(False)
            if ToolBarEnable.pixel_enable:
                self.toolBarController.toolBarService.clear_pixel()
                self.toolBarController.action_pixel.setChecked(False)
            if ToolBarEnable.polyline_enable:
                self.toolBarController.toolBarService.clear_polyline()
                self.toolBarController.action_polyline.setChecked(False)
            if ToolBarEnable.crosshair_enable:
                self.toolBarController.toolBarService.clear_crosshair()
                self.toolBarController.action_crosshair.setChecked(False)
            if ToolBarEnable.angle_enable:
                self.toolBarController.toolBarService.clear_angle()
                self.toolBarController.action_angle.setChecked(False)
            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarController.toolBarService.clear_dragging_image()
                self.toolBarController.action_dragging_image.setChecked(False)

            self.annotationService.label_clear()
            self.labelBoxAction.setChecked(False)
            AnnotationEnable.labelBoxAction = self.labelBoxAction
            AnnotationEnable.pointAction = self.pointAction
            try:
                for i in getSingleBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")
            try:
                for i in getLastBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
                self.viewer_XY.Render()
            except:
                print("clear the Last box actor failed!!")
            try:
                for actor in getMultipleBoundingBoxActor():
                    for i in actor:
                        print("getMultipleBoundingBoxActor:", i)
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                clearMultipleBoundingBoxActor()
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")
            try:
                self.viewer_XY_InteractorStyle.RemoveObservers("LeftButtonPressEvent")
            except:
                print("LeftButtonPressEvent is not found")
            try:
                self.viewer_XY_InteractorStyle.RemoveObservers("MouseMoveEvent")
            except:
                print("MouseMoveEvent is not found")

            self.viewer_XY_InteractorStyle.RemoveObservers("MouseWheelForwardEvent")
            self.viewer_XY_InteractorStyle.RemoveObservers("MouseWheelBackwardEvent")

            wheelforward = MouseWheelForward(self.viewer_XY, self.label_XY, self.verticalSlider_XY,
                                             self.type_XY)
            wheelbackward = MouseWheelBackWard(self.viewer_XY, self.label_XY, self.verticalSlider_XY,
                                               self.type_XY)
            self.viewer_XY_InteractorStyle.AddObserver("MouseWheelForwardEvent", wheelforward)
            self.viewer_XY_InteractorStyle.AddObserver("MouseWheelBackwardEvent", wheelbackward)
            clearMultipleUndoStack()
            clearMultipleRedoStack()

            print("开始标注 point")
            picker = vtk.vtkPointPicker()
            picker.PickFromListOn()
            left_press = LeftButtonPressEvent_Point(picker, self.baseModelClass, self.viewModel)
            self.viewer_XY_InteractorStyle.AddObserver("LeftButtonPressEvent", left_press)
            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
        else:
            AnnotationEnable.labelBoxAction = self.labelBoxAction
            AnnotationEnable.pointAction = self.pointAction
            print("结束标注 point")
            self.annotationService.label_clear()
            ToolBarWidget.annotation_widget.widget_labels.hide()
            self.viewer_XY_InteractorStyle.RemoveObservers("LeftButtonPressEvent")

    def select_point_label(self):
        if self.point_label_0.isChecked():
            setSelectPointLabel1(False)
            print("select point label 0")
        else:
            setSelectPointLabel1(True)
            print("select point label 1")

    def select_box_label(self):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        if self.box_label_single.isChecked():
            setSelectSingleBoxLabel(True)
            clearMultipleUndoStack()
            clearMultipleRedoStack()
            setMultipleBoundingBoxDict({})
            try:
                for i in getSingleBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
            except:
                print('Close viewer_XY actor_paint Failed!!!')
            try:
                for i in getLastBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
            except:
                print('Close viewer_XY actor_paint Failed!!!')
            try:
                for actor in getMultipleBoundingBoxActor():
                    for i in actor:
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                clearMultipleBoundingBoxActor()
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")
            print("select box label single")
        else:
            setSelectSingleBoxLabel(False)
            print("select box label multiple")
            clearSingleUndoStack()
            clearPointsRedoStack()
            setSingleBoundingBoxDict({})
            try:
                for i in getSingleBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")

    def on_action_labelBox(self):
        if getFileIsEmpty():
            print("文件未导入")
            return
        self.update_axial_viewer()
        if self.labelBoxAction.isChecked():
            print("开始标注 labelBox")
            # 关闭其他工具的使用
            ToolBarWidget.annotation_widget.widget_labels.show()
            if ToolBarEnable.ruler_enable:
                self.toolBarController.toolBarService.clear_ruler()
                self.toolBarController.action_ruler.setChecked(False)
            if ToolBarEnable.paint_enable:
                self.toolBarController.toolBarService.clear_paint()
                self.toolBarController.action_paint.setChecked(False)
            if ToolBarEnable.pixel_enable:
                self.toolBarController.toolBarService.clear_pixel()
                self.toolBarController.action_pixel.setChecked(False)
            if ToolBarEnable.polyline_enable:
                self.toolBarController.toolBarService.clear_polyline()
                self.toolBarController.action_polyline.setChecked(False)
            if ToolBarEnable.crosshair_enable:
                self.toolBarController.toolBarService.clear_crosshair()
                self.toolBarController.action_crosshair.setChecked(False)
            if ToolBarEnable.angle_enable:
                self.toolBarController.toolBarService.clear_angle()
                self.toolBarController.action_angle.setChecked(False)
            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarController.toolBarService.clear_dragging_image()
                self.toolBarController.action_dragging_image.setChecked(False)

            self.annotationService.label_clear()
            self.pointAction.setChecked(False)
            AnnotationEnable.labelBoxAction = self.labelBoxAction
            AnnotationEnable.pointAction = self.pointAction
            try:
                for i in getPointsActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
                self.viewer_XY.Render()
            except:
                print('Close viewer_XY point actor Failed!!!')
            clearPointsActor()
            clearPointsUndoStack()
            clearPointsRedoStack()
            self.viewer_XY_InteractorStyle.RemoveObservers("LeftButtonPressEvent")
            self.viewer_XY_InteractorStyle.RemoveObservers("MouseWheelForwardEvent")
            self.viewer_XY_InteractorStyle.RemoveObservers("MouseWheelBackwardEvent")
            self.wheelforward = MouseWheelForward(self.viewer_XY, self.label_XY, self.verticalSlider_XY,
                                                  self.type_XY)
            self.wheelbackward = MouseWheelBackWard(self.viewer_XY, self.label_XY, self.verticalSlider_XY,
                                                    self.type_XY)
            self.viewer_XY_InteractorStyle.AddObserver("MouseWheelForwardEvent", self.wheelforward)
            self.viewer_XY_InteractorStyle.AddObserver("MouseWheelBackwardEvent", self.wheelbackward)
            self.picker = vtk.vtkPointPicker()
            self.picker.PickFromListOn()
            self.left_press_labelBox = LeftButtonPressEvent_labelBox(self.picker, self.baseModelClass, self.viewModel)
            self.mouse_move_labelBox = MouseMoveEvent_labelBox(self.picker, self.baseModelClass, self.viewModel)
            self.viewer_XY_InteractorStyle.AddObserver("LeftButtonPressEvent", self.left_press_labelBox)
            self.viewer_XY_InteractorStyle.AddObserver("MouseMoveEvent", self.mouse_move_labelBox)
            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
        else:
            print("结束标注 labelBox")
            ToolBarWidget.annotation_widget.widget_labels.hide()
            self.annotationService.label_clear()
            try:
                for i in getLastBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")
            try:
                for i in getSingleBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")
            try:
                for actor in getMultipleBoundingBoxActor():
                    for i in actor:
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                clearMultipleBoundingBoxActor()
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")
            self.viewer_XY_InteractorStyle.RemoveObservers("LeftButtonPressEvent")
            self.viewer_XY_InteractorStyle.RemoveObservers("MouseMoveEvent")
            clearMultipleUndoStack()
            clearMultipleRedoStack()
            AnnotationEnable.labelBoxAction = self.labelBoxAction
            AnnotationEnable.pointAction = self.pointAction

    def on_action_startSegmentation(self):
        if getFileIsEmpty():
            print("文件未导入")
            return
        if not self.Flag_Load_model:
            print("Model has not been loaded!!")
            self.message_warning_dialog('Model Load', "Model has not been loaded!!")
            return
        self.dicomdata, self.header = load(getDirPath())
        # -------------创建分割目标矩阵--------------------------------------------
        self.segmentation_Result = np.zeros_like(self.dicomdata)
        # ----------------------------------------------
        Meanv = np.mean(self.dicomdata)
        Std = np.std(self.dicomdata)
        Minv = np.min(self.dicomdata)
        Maxv = np.max(self.dicomdata)
        normal_val_min = np.max([Minv, Meanv - 2 * Std])
        normal_val_max = np.min([Maxv, Meanv + 2 * Std])
        if DataAndModelType.MODEL_TYPE == 'Universal':
            dicomdata = np.uint8(MaxMin_normalization_Intensity(self.dicomdata, Minv, Maxv) * 255)
        else:
            dicomdata = np.uint8(MaxMin_normalization_Intensity(self.dicomdata, normal_val_min, normal_val_max) * 255)
        if self.pointAction.isChecked():
            points_dict = getPointsDict()
            index_list = [str(point[2]) for point in getPointsUndoStack()]
            for index in list(points_dict.keys()):
                if index not in index_list:
                    del points_dict[index]
            print(points_dict)
            if self.segmentation_type_sliceRange.isChecked():
                keys = sorted(int(k) for k in points_dict.keys())
                print("keys:", keys)
                for i in range(keys[0] + 1, keys[-1]):
                    if str(i) not in points_dict:
                        points_dict[str(i)] = {'points': points_dict[str(i - 1)]["points"],
                                               'label': points_dict[str(i - 1)]["label"],
                                               'image_name': f'_image_{i}.png'}
            print(points_dict)
            for index, data in points_dict.items():
                if DataAndModelType.DATA_TYPE == "DICOM":
                    index_z = self.dicomdata.shape[2] - int(index) - 1
                else:
                    index_z = int(index)
                select_layer_image = dicomdata[:, :, index_z]
                select_layer_image_transpose = np.transpose(select_layer_image)
                input_points = []
                input_labels = data["label"]
                for point in data["points"]:
                    index_y = self.dicomdata.shape[1] - point[1] - 1
                    input_points.append([point[0], index_y])
                temp = point_segmentation(self.model, input_points, input_labels, select_layer_image_transpose)

                self.segmentation_Result[:, :, index_z] = np.transpose(temp)
        if self.labelBoxAction.isChecked():
            if getSelectSingleBoxLabel():
                index_list = [str(point[4]) for point in getSingleUndoStack()]
                bounding_box_dict = getSingleBoundingBoxDict()
                for index in list(bounding_box_dict.keys()):
                    if index not in index_list:
                        del bounding_box_dict[index]
                print(bounding_box_dict)
                if self.segmentation_type_sliceRange.isChecked():
                    keys = sorted(int(k) for k in bounding_box_dict.keys())
                    print("keys:", keys)
                    for i in range(keys[0] + 1, keys[-1]):
                        if str(i) not in bounding_box_dict:
                            bounding_box_dict[str(i)] = {'bounding_box': bounding_box_dict[str(i - 1)]["bounding_box"],
                                                         'image_name': f'_image_{i}.png'}
                print(bounding_box_dict)
                for index, data in bounding_box_dict.items():
                    if DataAndModelType.DATA_TYPE == "DICOM":
                        index_z = self.dicomdata.shape[2] - int(index) - 1
                    else:
                        index_z = int(index)
                    select_layer_image = dicomdata[:, :, index_z]
                    select_layer_image_transpose = np.transpose(select_layer_image)
                    start_x = data["bounding_box"][0]
                    start_y = self.dicomdata.shape[1] - data["bounding_box"][1] - 1
                    end_x = data["bounding_box"][2]
                    end_y = self.dicomdata.shape[1] - data["bounding_box"][3] - 1
                    input_box = [start_x, start_y, end_x, end_y]
                    temp = single_box_segmentation(self.model, input_box, select_layer_image_transpose)
                    self.segmentation_Result[:, :, index_z] = np.transpose(temp)

            else:
                index_list = [str(point[4]) for point in getMultipleUndoStack()]
                bounding_box_dict = getMultipleBoundingBoxDict()
                for index in list(bounding_box_dict.keys()):
                    if index not in index_list:
                        del bounding_box_dict[index]
                print(bounding_box_dict)
                if self.segmentation_type_sliceRange.isChecked():
                    keys = sorted(int(k) for k in bounding_box_dict.keys())
                    print("keys:", keys)
                    for i in range(keys[0] + 1, keys[-1]):
                        if str(i) not in bounding_box_dict:
                            bounding_box_dict[str(i)] = {'bounding_box': bounding_box_dict[str(i - 1)]["bounding_box"],
                                                         'image_name': f'_image_{i}.png'}
                print(bounding_box_dict)
                for index, data in bounding_box_dict.items():
                    if DataAndModelType.DATA_TYPE == "DICOM":
                        index_z = self.dicomdata.shape[2] - int(index) - 1
                    else:
                        index_z = int(index)
                    select_layer_image = dicomdata[:, :, index_z]
                    select_layer_image_transpose = np.transpose(select_layer_image)
                    input_box = []
                    for box in data["bounding_box"]:
                        start_x = box[0]
                        start_y = self.dicomdata.shape[1] - box[1] - 1
                        end_x = box[2]
                        end_y = self.dicomdata.shape[1] - box[3] - 1
                        input_point = [start_x, start_y, end_x, end_y]
                        input_box.append(input_point)
                    temp = multiple_box_segmentation(self.model, input_box, select_layer_image_transpose, ParamConstant.args)
                    self.segmentation_Result[:, :, index_z] = np.transpose(temp)

    def on_action_saveResult(self):
        Segmentation_Result = self.segmentation_Result
        if DataAndModelType.DATA_TYPE == 'IM0':
            Segmentation_Result = np.transpose(Segmentation_Result, (1, 0, 2))
            Save_BIM(np.int32(Segmentation_Result),
                     ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_seg.BIM', input_file=self.IM0path)
        else:
            save(np.int32(Segmentation_Result),
                 ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_seg.nii.gz', hdr=self.header)
        self.message_info_dialog('Save Result', 'Segmentation result saved successfully!')

    def update_axial_viewer(self):
        self.annotationService = AnnotationService(self.baseModelClass, self.viewModel)
        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.type_XY = self.viewModel.AxialOrthoViewer.type
        self.viewer_XY_InteractorStyle = self.viewer_XY.GetInteractorStyle()
        self.label_XY = self.viewModel.AxialOrthoViewer.slider_label

    def select_slice_range(self):
        if self.segmentation_type_sliceRange.isChecked():
            self.segmentation_type_none.setChecked(False)
            self.segmentation_type_sliceRange.setChecked(True)
        else:
            self.segmentation_type_none.setChecked(True)
            self.segmentation_type_sliceRange.setChecked(False)

    def on_actionAdd_Load_Universal_model(self):
        print('Load Universal_model!')
        # path = QtWidgets.QFileDialog.getOpenFileName(None, "选取文件", "", "*.pth;")
        # -----------------------------------------------------
        if self.Flag_Load_model:
            del self.model
        else:
            self.Flag_Load_model = True
        # -----------------------------------------------------
        ParamConstant.args.sam_checkpoint = ParamConstant.universal_model
        self.model = sam_model_registry["vit_b"](ParamConstant.args).to(ParamConstant.device)
        self.message_info_dialog('Load model', 'Load Universal_model Successfully!')
        DataAndModelType.MODEL_TYPE = 'Universal'
        print('Load Universal_model Successfully!')

    def on_actionAdd_Load_Lungseg_model(self):
        print('Load Lungseg_model!')
        # path = QtWidgets.QFileDialog.getOpenFileName(None, "选取文件", "", "*.pth;")
        # -----------------------------------------------------
        if self.Flag_Load_model:
            del self.model
        else:
            self.Flag_Load_model = True
        # -----------------------------------------------------
        ParamConstant.args.sam_checkpoint = ParamConstant.lung_seg_model
        self.model = sam_model_registry["vit_b"](ParamConstant.args).to(ParamConstant.device)
        self.message_info_dialog('Load model', 'Load Lungseg_model Successfully!')
        DataAndModelType.MODEL_TYPE = 'MRI_Lungseg'
        print('Load Lungseg_model Successfully!')


    # 提示消息框
    @staticmethod
    def message_info_dialog(title, text):
        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, title, text)
        msg_box.exec_()

    # 警告提示框
    @staticmethod
    def message_warning_dialog(title, text):
        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, title, text)
        msg_box.exec_()

