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

from src.utils import DICOMConversionParams, NPYToDICOMConverter
from src.utils.logger import get_logger

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
from src.utils.ErrorRecoveryManager import ErrorRecoveryManager, ErrorType, ErrorContext
from src.ui.GenweatePanomrmaicWindow import Generate_Panormaic_Widget
from src.ui.ToothLandmarkWindow import Tooth_Landmark
from src.ui.CoronalCanalAnnotationWindow import CoronalCanalAnnotationWindow
from src.utils.IM0AndBIMUtils import Save_BIM, convertNsave
from src.utils.globalVariables import *
from src.widgets.MenuBarWidget import MenuBarManager

logger = get_logger(__name__)

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
        self.actionAdd_NIFIT_Data.triggered.connect(self.on_actionAdd_NIFIT_Data)
        self.actionAdd_NPY_Data.triggered.connect(self.on_actionAdd_NPY_Data)

        self.action_generatePanormaic.triggered.connect(self.on_action_generatePanormaic)
        self.action_toothLandmark_annotation.triggered.connect(self.on_action_tooth_landmark_annotation)
        self.action_coronal_canal_annotation.triggered.connect(self.on_action_coronal_canal_annotation)
        self.action_implant_toolbar.triggered.connect(self.on_action_implant_toolbar)
        self.action_registration_toolbar.triggered.connect(self.on_action_registration_toolbar)
        self.action_parameters_toolbar.triggered.connect(self.on_action_parameters_toolbar)
        self.actionAdd_Load_Universal_model.triggered.connect(self.on_actionAdd_Load_Universal_model)
        self.actionAdd_Load_Lungseg_model.triggered.connect(self.on_actionAdd_Load_Lungseg_model)
        self.action_nifti_segmentation_editor.triggered.connect(self.on_action_nifti_segmentation_editor)
        self.action_volume_render_toolbar.triggered.connect(self.on_action_volume_render_toolbar)
        self.action_view_layout.triggered.connect(self.on_action_view_layout)
        self.action_multi_slice_view.triggered.connect(self.on_action_multi_slice_view)
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

    def on_actionAdd_NIFIT_Data(self):
        """
        处理 NIFTI 文件加载操作
        
        验证 DICOM 数据已加载，然后打开文件选择对话框选择 NIFTI 文件，
        并委托给 MenuBarService 进行处理
        """
        print("选择 NIFTI 文件")
        
        # 验证 DICOM 数据是否已加载
        # if getDirPath() == "" or getFileIsEmpty():
        #     self.message_warning_dialog(
        #         'NIFTI 加载错误', 
        #         '请先加载 DICOM 数据，然后再加载 NIFTI 分割文件。'
        #     )
        #     return
        
        # 打开文件选择对话框，添加适当的过滤器
        file_dialog_result = QtWidgets.QFileDialog.getOpenFileName(
            None, 
            "选择 NIFTI 分割文件", 
            "", 
            "NIFTI Files (*.nii *.nii.gz);;All Files (*)"
        )
        
        if file_dialog_result[0] == "":
            return
        
        nifti_path = file_dialog_result[0]
        
        try:
            # 验证文件存在性
            if not os.path.exists(nifti_path):
                self.message_warning_dialog(
                    'NIFTI 文件错误',
                    f'选择的文件不存在: {nifti_path}'
                )
                return
            
            # 委托给服务层处理
            self.menuBarService.on_actionAdd_NIFIT_Data(nifti_path)
            
            # 加载NIFTI文件后，恢复缩放交互功能
            self.restore_zoom_interaction()
            
        except Exception as e:
            # 错误处理和用户反馈
            error_message = f"加载 NIFTI 文件时发生错误: {str(e)}"
            self.message_warning_dialog('NIFTI 加载错误', error_message)

    def on_actionAdd_NPY_Data(self):
        """
        处理 NPY 文件加载操作
        
        打开文件选择对话框选择 .npy 文件，验证文件存在性和可读性，
        并委托给 MenuBarService 进行处理，同时处理UI状态更新和用户反馈
        """
        print("选择 NPY 文件")
        
        error_recovery_manager = None
        
        try:
            # 初始化错误恢复管理器
            error_recovery_manager = ErrorRecoveryManager()
            
            # 打开文件选择对话框，添加适当的过滤器
            file_dialog_result = QtWidgets.QFileDialog.getOpenFileName(
                None, 
                "选择 NPY 数据文件", 
                "", 
                "NumPy Files (*.npy);;All Files (*)"
            )
            
            if file_dialog_result[0] == "":
                return
            
            npy_path = file_dialog_result[0]
            
            # 验证文件存在性
            if not os.path.exists(npy_path):
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.FILE_NOT_FOUND,
                    f'选择的文件不存在: {npy_path}',
                    file_path=npy_path
                )
                error_recovery_manager.handle_error(error_context)
                
                self.message_warning_dialog(
                    'NPY 文件错误',
                    f'选择的文件不存在: {npy_path}'
                )
                return
            
            # 验证文件可读性
            if not os.access(npy_path, os.R_OK):
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.PERMISSION_ERROR,
                    f'文件无法读取，请检查文件权限: {npy_path}',
                    file_path=npy_path
                )
                error_recovery_manager.handle_error(error_context)
                
                self.message_warning_dialog(
                    'NPY 文件错误',
                    f'文件无法读取，请检查文件权限: {npy_path}'
                )
                return
            
            # 基本的 .npy 文件格式验证
            if not npy_path.lower().endswith('.npy'):
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.INVALID_DATA_FORMAT,
                    '请选择有效的 .npy 文件',
                    file_path=npy_path
                )
                error_recovery_manager.handle_error(error_context)
                
                self.message_warning_dialog(
                    'NPY 文件错误',
                    '请选择有效的 .npy 文件'
                )
                return

            #  这里实现NPY转化为DICOM的逻辑
            # 如果是重新加载NPY文件，需要先释放VTK reader对旧文件的占用
            if DataAndModelType.DATA_TYPE == 'NPY':
                logger.info("Releasing VTK reader resources before reloading NPY data")
                try:
                    # 释放reader对文件的占用
                    self.reader.SetDirectoryName("")
                    self.reader.Modified()
                    self.reader.Update()
                    # 清理viewer中的引用
                    if hasattr(self, 'menuBarService'):
                        for viewer_attr in ['viewer_XY', 'viewer_YZ', 'viewer_XZ']:
                            if hasattr(self.menuBarService, viewer_attr):
                                viewer = getattr(self.menuBarService, viewer_attr)
                                if viewer and hasattr(viewer, 'GetRenderWindow'):
                                    viewer.GetRenderWindow().Finalize()
                    # 给系统一点时间释放文件句柄
                    import time
                    time.sleep(0.2)
                except Exception as e:
                    logger.warning(f"Failed to release reader resources: {e}")
            
            self.save_npypath_temp = ParamConstant.OUTPUT_FILE_PATH + 'npy_temp/'
            if not os.path.exists(self.save_npypath_temp):
                os.mkdir(self.save_npypath_temp)
            else:
                for file in glob.glob(self.save_npypath_temp + "*.dcm"):
                    os.remove(file)
            self.save_npypath = ParamConstant.OUTPUT_FILE_PATH + 'npy/'
            if not os.path.exists(self.save_npypath):
                os.mkdir(self.save_npypath)
            else:
                for file in glob.glob(self.save_npypath_temp + "*.dcm"):
                    os.remove(file)

            # 加载NPY文件
            try:
                npy_data = np.load(npy_path)
                logger.info(f"Successfully loaded NPY file: shape={npy_data.shape}, dtype={npy_data.dtype}")
            except Exception as e:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.INVALID_DATA_FORMAT,
                    f"Failed to load NPY file: {npy_path}",
                    file_path=npy_path,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
                raise ValueError(f"Failed to load NPY file: {npy_path}") from e

            # 验证数据格式为三维数组
            if len(npy_data.shape) != 3:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.INVALID_DATA_FORMAT,
                    f"Invalid data format. Expected 3D array, got {len(npy_data.shape)}D array with shape: {npy_data.shape}",
                    file_path=npy_path
                )
                error_recovery_manager.handle_error(error_context)
                raise ValueError(
                    f"Invalid data format. Expected 3D array, got {len(npy_data.shape)}D array with shape: {npy_data.shape}")

            if npy_data.size == 0:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.INVALID_DATA_FORMAT,
                    "NPY file contains no data",
                    file_path=npy_path
                )
                error_recovery_manager.handle_error(error_context)
                raise ValueError("NPY file contains no data")

            # 创建NPY到DICOM转换器
            conversion_params = DICOMConversionParams(
                pixel_spacing=(1.0, 1.0),
                slice_thickness=1.0,
                patient_name="NPY_PATIENT",
                study_description="NPY Data Import",
                data_type= "NPY"
            )
            converter = NPYToDICOMConverter(conversion_params)

            # 转换NPY数据为DICOM格式
            try:
                dicom_files = converter.convert(npy_data, self.save_npypath_temp)
                logger.info(f"Successfully converted NPY to {len(dicom_files)} DICOM files")
            except MemoryError as e:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.MEMORY_ERROR,
                    f"Insufficient memory to convert NPY data",
                    file_path=npy_path,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
                raise RuntimeError(f"Insufficient memory to convert NPY data") from e
            except Exception as e:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.CONVERSION_ERROR,
                    f"Failed to convert NPY to DICOM format",
                    file_path=npy_path,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
                raise RuntimeError(f"Failed to convert NPY to DICOM format") from e


            dicom_files = glob.glob(self.save_npypath_temp + "*.dcm")
            dicom_files.sort()
            number_slices = len(dicom_files)
            for index in range(number_slices):
                dicom_file = pydicom.dcmread(dicom_files[index])
                convertNsave(dicom_file,ParamConstant.IMAGE_DCM, self.save_npypath, index)
                self.SliceThickness = dicom_file.SliceThickness

            # 在开始处理前清理UI状态和工具栏
            self._clear_ui_state_for_new_data()

            DataAndModelType.DATA_TYPE = 'NPY'

            setDirPath(self.save_npypath)

            self.reader.SetDirectoryName(self.save_npypath)
            self.reader.Update()
            # 更新 Data Information
            self.baseModelClass.imageReader = self.reader
            self.baseModelClass.update_data_information()

            self.menuBarService.on_actionAdd_NPY_Data(self.SliceThickness)

            
        except FileNotFoundError as e:
            error_message = f"文件未找到: {str(e)}"
            if error_recovery_manager:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.FILE_NOT_FOUND,
                    error_message,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
            self.message_warning_dialog('NPY 加载错误', error_message)
            
        except PermissionError as e:
            error_message = f"文件权限错误: {str(e)}"
            if error_recovery_manager:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.PERMISSION_ERROR,
                    error_message,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
            self.message_warning_dialog('NPY 加载错误', error_message)
            
        except ValueError as e:
            error_message = f"数据格式错误: {str(e)}"
            if error_recovery_manager:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.INVALID_DATA_FORMAT,
                    error_message,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
            self.message_warning_dialog('NPY 加载错误', error_message)
            
        except MemoryError as e:
            error_message = f"内存不足，建议关闭其他应用程序或使用较小的数据文件: {str(e)}"
            if error_recovery_manager:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.MEMORY_ERROR,
                    error_message,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
            self.message_warning_dialog('NPY 加载错误', error_message)
            
        except RuntimeError as e:
            error_message = f"运行时错误: {str(e)}"
            if error_recovery_manager:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.VTK_ERROR,
                    error_message,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
            self.message_warning_dialog('NPY 加载错误', error_message)
            
        except Exception as e:
            # 错误处理和用户反馈
            error_message = f"加载 NPY 文件时发生未知错误: {str(e)}"
            if error_recovery_manager:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.UNKNOWN_ERROR,
                    error_message,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
            self.message_warning_dialog('NPY 加载错误', error_message)
        
        finally:
            # 确保资源清理
            if error_recovery_manager:
                try:
                    error_recovery_manager.cleanup_resources()
                except Exception as cleanup_error:
                    print(f"清理资源时发生错误: {cleanup_error}")

    def _clear_ui_state_for_new_data(self):
        """
        为新数据加载清理UI状态和工具栏
        
        确保与现有DICOM和IM0数据加载功能的一致性
        """
        try:
            # 清理参数表格
            try:
                ToolBarWidget.parameters_widget.tableWidget.clearContents()
                ToolBarWidget.parameters_widget.tableWidget.setRowCount(0)
            except:
                print("clear table fail!!!")

            # 清理植体列表
            try:
                ToolBarWidget.implant_widget.ToothID_Implant_QStringList.removeRows(1,
                                                                                    ToolBarWidget.implant_widget.ToothID_Implant_QStringList.rowCount() - 1)
            except:
                print("clear tooth implant list failed")

            # 清理所有工具栏状态
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
            
            # 更新工具栏显示
            self.toolBarController.toolBar.update()

            # 清理植体相关列表
            ToothImplantList.Tooth_Implant_File_List.clear()
            ToothImplantList.Tooth_Implant_File_List = []

            ToothImplantList.Tooth_Implant_Reg_File_List.clear()
            ToothImplantList.Tooth_Implant_Reg_File_List = []
            
        except Exception as e:
            print(f"清理UI状态时发生错误: {e}")

    def _handle_npy_loading_success(self, npy_path: str):
        """
        处理NPY数据加载成功后的UI更新
        
        Args:
            npy_path: 成功加载的NPY文件路径
        """
        try:
            # 设置文件路径和状态
            setDirPath(npy_path)
            
            # 更新数据信息
            self.reader = self.baseModelClass.imageReader
            
            # 设置标注主题名称
            ParamConstant.ANNOTATION_SUBJECT_NAME = os.path.basename(npy_path).split('.')[0]
            
            # 显示成功消息
            self.message_info_dialog(
                'NPY 数据加载', 
                f'NPY 数据加载成功！\n文件: {os.path.basename(npy_path)}\n数据类型: NPY'
            )
            
            print(f"NPY 数据加载成功: {npy_path}")
            print(f"数据类型已设置为: {DataAndModelType.DATA_TYPE}")
            
        except Exception as e:
            print(f"处理NPY加载成功状态时发生错误: {e}")
            # 不抛出异常，因为主要功能已经完成



    def LoadSTL(self, filename, color=None):
        """
        加载STL文件并创建actor
        
        Args:
            filename: STL文件路径
            color: 可选的RGB颜色元组 (r, g, b)，值范围0-1
            
        Returns:
            vtk.vtkLODActor: STL模型的actor
        """
        # 如果没有加载医学影像数据，使用默认中心点
        try:
            bounds = self.baseModelClass.bounds
            self.center0 = (bounds[1] + bounds[0]) / 2.0
            self.center1 = (bounds[3] + bounds[2]) / 2.0
            self.center2 = (bounds[5] + bounds[4]) / 2.0
        except:
            # 没有医学影像数据时，使用原点
            self.center0 = 0.0
            self.center1 = 0.0
            self.center2 = 0.0
            logger.info("No medical image data loaded, using origin as center")
        
        transform = vtk.vtkTransform()
        transform.Translate(self.center0, self.center1, self.center2)

        reader = vtk.vtkSTLReader()  # 读取stl文件
        reader.SetFileName(filename)  # 文件名
        mapper = vtk.vtkPolyDataMapper()  # 将多边形数据映射到图形基元
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkLODActor()
        actor.SetMapper(mapper)
        actor.SetUserTransform(transform)
        
        # 设置颜色
        if color:
            actor.GetProperty().SetColor(color[0], color[1], color[2])
        
        return actor  # 表示渲染场景中的实体

    def on_actionAdd_STL_Data(self):
        """
        加载STL文件到体渲染窗口
        支持多选文件，统一使用黄色显示
        """
        # 获取或初始化renderer
        if not hasattr(self.viewModel.VolumeOrthorViewer, 'renderer') or self.viewModel.VolumeOrthorViewer.renderer is None:
            # 如果没有renderer，创建一个新的
            logger.info("Creating new renderer for STL display")
            renderer = vtk.vtkRenderer()
            renderer.SetBackground(0.5, 0.5, 0.5)
            self.viewModel.VolumeOrthorViewer.widget.GetRenderWindow().AddRenderer(renderer)
            self.viewModel.VolumeOrthorViewer.renderer = renderer
            
            # 设置交互样式
            style = vtk.vtkInteractorStyleTrackballCamera()
            style.SetDefaultRenderer(renderer)
            style.EnabledOn()
            self.viewModel.VolumeOrthorViewer.renderWindowInteractor.SetInteractorStyle(style)
            
            # 添加坐标轴
            axesActor = vtk.vtkAxesActor()
            axes = vtk.vtkOrientationMarkerWidget()
            axes.SetOrientationMarker(axesActor)
            axes.SetInteractor(self.viewModel.VolumeOrthorViewer.renderWindowInteractor)
            axes.EnabledOn()
            axes.SetEnabled(1)
            axes.InteractiveOff()
            
        self.renderer_volume = self.viewModel.VolumeOrthorViewer.renderer
        
        if self.actionAdd_STL_Data.isChecked():
            logger.info("选择STL文件")
            
            # 使用getOpenFileNames支持多选
            file_dialog_result = QtWidgets.QFileDialog.getOpenFileNames(
                None, 
                "选择STL文件（可多选）", 
                "", 
                "STL Files (*.stl);;All Files (*)"
            )
            
            stl_paths = file_dialog_result[0]
            
            if not stl_paths or len(stl_paths) == 0:
                logger.info("未选择文件")
                self.actionAdd_STL_Data.setChecked(False)
                return
            
            logger.info(f"选择了 {len(stl_paths)} 个STL文件")
            
            # 清除之前的STL actors
            if not hasattr(VolumeRender, 'actor_stl_list'):
                VolumeRender.actor_stl_list = []
            
            for actor in VolumeRender.actor_stl_list:
                try:
                    self.renderer_volume.RemoveActor(actor)
                except:
                    pass
            VolumeRender.actor_stl_list.clear()
            
            # 隐藏体渲染（如果存在）
            if hasattr(VolumeRender, 'volume_cbct') and VolumeRender.volume_cbct:
                try:
                    self.renderer_volume.RemoveVolume(VolumeRender.volume_cbct)
                    logger.info("隐藏体渲染")
                except:
                    logger.debug('volume_cbct removal failed')
            
            # 统一的黄色
            yellow_color = (223/255.0, 196/255.0, 45/255.0)
            
            # 加载所有选中的STL文件
            self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
            for stl_path in stl_paths:
                try:
                    logger.info(f"加载STL文件: {stl_path}")
                    actor_stl = self.LoadSTL(stl_path, color=yellow_color)
                    self.renderer_volume.AddActor(actor_stl)
                    VolumeRender.actor_stl_list.append(actor_stl)
                except Exception as e:
                    logger.error(f"加载STL文件失败 {stl_path}: {e}")
            
            # 重置相机以显示所有模型
            self.renderer_volume.ResetCamera()
            self.vtkWidget_Volume.Render()
            
            logger.info(f"成功加载 {len(VolumeRender.actor_stl_list)} 个STL模型")
            
        else:
            logger.info("恢复体渲染")
            
            # 移除所有STL actors
            if hasattr(VolumeRender, 'actor_stl_list'):
                for actor in VolumeRender.actor_stl_list:
                    try:
                        self.renderer_volume.RemoveActor(actor)
                    except:
                        pass
                VolumeRender.actor_stl_list.clear()
            
            # 恢复体渲染（如果存在）
            if hasattr(VolumeRender, 'volume_cbct') and VolumeRender.volume_cbct:
                try:
                    self.renderer_volume.AddVolume(VolumeRender.volume_cbct)
                    logger.info("恢复体渲染")
                except:
                    logger.debug('volume_cbct restoration failed')
            
            self.vtkWidget_Volume.Render()

    def valuechange1(self):
        self.menuBarService.valuechange1()

    def valuechange2(self):
        self.menuBarService.valuechange2()

    def valuechange3(self):
        self.menuBarService.valuechange3()

    def on_action_nifti_segmentation_editor(self):
        """打开NIfTI分割结果编辑窗口"""
        from src.controller.SegmentationEditController import SegmentationEditController
        self._seg_edit_controller = SegmentationEditController(self.QMainWindow)
        self._seg_edit_controller.show_segmentation_editor()

    def on_action_volume_render_toolbar(self):
        """显示/隐藏体绘制工具栏"""
        widget = ToolBarWidget.volume_render_widget
        if widget is None:
            return
        if widget.isHidden():
            widget.show()
        else:
            widget.hide()

    def on_action_view_layout(self):
        """打开/关闭视图布局控制面板"""
        if ToolBarWidget.view_layout_widget is not None:
            ToolBarWidget.view_layout_widget.show_panel()

    def on_action_multi_slice_view(self):
        """切换到多切片视图（嵌入主界面 QStackedWidget）"""
        if ToolBarWidget.multi_slice_widget is not None:
            ToolBarWidget.multi_slice_widget.show_panel()

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

    def on_action_coronal_canal_annotation(self):
        print("冠状面下颌管标注")
        if getFileIsEmpty():
            print("未导入文件，无法进行下颌管标注！")
            return
        # 创建独立的标注窗口，不传递主窗口的视图模型
        self.coronal_canal_annotation_window = CoronalCanalAnnotationWindow(self.baseModelClass, self.viewModel)
        self.coronal_canal_annotation_window.show()

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

    def restore_zoom_interaction(self):
        """
        恢复VTK窗口的缩放交互功能
        在加载NIFTI文件后调用此方法来确保用户可以正常缩放视图
        """
        try:
            print("正在恢复缩放交互功能...")
            
            # 获取所有查看器
            viewers = [
                self.viewModel.AxialOrthoViewer.viewer,      # XY视图
                self.viewModel.SagittalOrthoViewer.viewer,   # YZ视图  
                self.viewModel.CoronalOrthoViewer.viewer,    # XZ视图
            ]
            
            # 为每个查看器恢复交互功能
            for i, viewer in enumerate(viewers):
                if viewer is not None:
                    try:
                        # 获取交互器
                        interactor = viewer.GetRenderWindow().GetInteractor()
                        if interactor is not None:
                            # 确保交互器已初始化
                            if not interactor.GetInitialized():
                                interactor.Initialize()
                            
                            # 获取当前的交互器样式
                            current_style = viewer.GetInteractorStyle()
                            
                            if current_style is not None:
                                # 确保交互器样式已启用
                                current_style.EnabledOn()
                                
                                # 如果是vtkImageViewer2，确保其交互功能正常
                                if hasattr(viewer, 'SetupInteractor'):
                                    viewer.SetupInteractor(interactor)
                                
                                print(f"已恢复视图 {i+1} 的交互功能")
                            else:
                                print(f"警告: 视图 {i+1} 没有交互器样式")
                        else:
                            print(f"警告: 视图 {i+1} 没有交互器")
                    except Exception as e:
                        print(f"恢复视图 {i+1} 交互功能时出错: {e}")
            
            # 特别处理体绘制窗口的交互功能
            try:
                volume_interactor = self.viewModel.VolumeOrthorViewer.renderWindowInteractor
                if volume_interactor is not None:
                    # 确保体绘制窗口有正确的交互器样式
                    style = vtk.vtkInteractorStyleTrackballCamera()
                    style.SetDefaultRenderer(self.viewModel.VolumeOrthorViewer.renderer)
                    style.EnabledOn()
                    volume_interactor.SetInteractorStyle(style)
                    
                    if not volume_interactor.GetInitialized():
                        volume_interactor.Initialize()
                    
                    print("已恢复体绘制窗口的交互功能")
            except Exception as e:
                print(f"恢复体绘制窗口交互功能时出错: {e}")
            
            # 强制刷新所有窗口
            try:
                widgets = [
                    self.viewModel.AxialOrthoViewer.widget,
                    self.viewModel.SagittalOrthoViewer.widget,
                    self.viewModel.CoronalOrthoViewer.widget,
                    self.viewModel.VolumeOrthorViewer.widget
                ]
                
                for widget in widgets:
                    if widget is not None:
                        widget.GetRenderWindow().Render()
                        
            except Exception as e:
                print(f"刷新窗口时出错: {e}")
            
            print("缩放交互功能恢复完成")
            
        except Exception as e:
            print(f"恢复缩放交互功能时发生错误: {e}")
            # 即使出错也不应该阻止程序继续运行

