# -*- coding: utf-8 -*-
# @Time    : 2024/10/8 17:05
#
# @Author  : Jianjun Tong
import glob
import os

import nibabel
import pydicom
import vtk
import numpy as np
from PyQt5 import QtWidgets
from medpy.io import load

from src.constant.ParamConstant import ParamConstant
from src.controller.ToolBarController import ToolBarController
from src.interactor_style.FourViewerInteractorStyle import MouseWheelForward, MouseWheelBackWard, MouseWheelForwardSeg, MouseWheelBackWardSeg
from src.model.AnnotationEnableModel import AnnotationEnable
from src.model.DataAndModelType import DataAndModelType
from src.model.VolumeRenderModel import VolumeRender
from src.model.BaseModel import BaseModel
from src.model.CameraPositionModel import CameraPosition
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.ToolBarEnableModel import ToolBarEnable
from src.service.AnnotationService import AnnotationService
from src.service.ConstantService import ContrastService
from src.service.ToolBarService import ToolBarService
from src.model.ToolBarWidgetModel import ToolBarWidget
from src.utils.IM0AndBIMUtils import convertNsave
from src.utils.globalVariables import *
from src.utils.logger import get_logger
from src.utils.NPYToDICOMConverter import NPYToDICOMConverter, DICOMConversionParams
from src.utils.TempFileManager import TempFileManager
from src.utils.ErrorRecoveryManager import ErrorRecoveryManager, ErrorType, ErrorContext

logger = get_logger(__name__)


class MenuBarService:
    def __init__(self, baseModelClass: BaseModel, viewer_model: OrthoViewerModel):

        self.baseModelClass = baseModelClass
        self.viewModel = viewer_model

        self.reader = self.baseModelClass.imageReader


        self.contrastService = ContrastService(self.baseModelClass, self.viewModel)
        self.toolBarService = ToolBarService(self.baseModelClass, self.viewModel)
        self.annotationService = AnnotationService(self.baseModelClass, self.viewModel)


        # XY 窗口
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.vtkWidget_XY = self.viewModel.AxialOrthoViewer.widget
        self.label_XY = self.viewModel.AxialOrthoViewer.slider_label
        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider
        self.id_XY = self.viewModel.AxialOrthoViewer.type

        # YZ 窗口
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.vtkWidget_YZ = self.viewModel.SagittalOrthoViewer.widget
        self.label_YZ = self.viewModel.SagittalOrthoViewer.slider_label
        self.verticalSlider_YZ = self.viewModel.SagittalOrthoViewer.slider
        self.id_YZ = self.viewModel.SagittalOrthoViewer.type

        # XZ 窗口
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        self.vtkWidget_XZ = self.viewModel.CoronalOrthoViewer.widget
        self.label_XZ = self.viewModel.CoronalOrthoViewer.slider_label
        self.verticalSlider_XZ = self.viewModel.CoronalOrthoViewer.slider
        self.id_XZ = self.viewModel.CoronalOrthoViewer.type

        self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
        self.iren_Volume = self.viewModel.VolumeOrthorViewer.renderWindowInteractor



    def on_actionAdd_DICOM_Data(self):
        setFileIsEmpty(False)
        setIsPutImplant(False)
        setIsGenerateImplant(False)
        setAnchorPointIsComplete(False)
        setIsAdjust(False)

        self.spacing = self.baseModelClass.spacing
        if self.spacing[2] == 0:
            newspacing = (self.spacing[0], self.spacing[1], 1)
            self.baseModelClass.imageReader.GetOutput().SetSpacing(newspacing)
            self.baseModelClass.imageReader.Update()
            self.baseModelClass.update_data_information()

        self.clear_mousewheel_forward_backward_event([self.viewer_XY,self.viewer_YZ,self.viewer_XZ])


        # 更新横断面
        focalPoint_XY, position_XY = self.update_viewer(self.viewModel.AxialOrthoViewer, self.vtkWidget_XY, self.label_XY,
                                                                  self.verticalSlider_XY, self.id_XY)
        # 更新矢状面
        focalPoint_YZ, position_YZ = self.update_viewer(self.viewModel.SagittalOrthoViewer, self.vtkWidget_YZ, self.label_YZ,
                                                                  self.verticalSlider_YZ, self.id_YZ)
        # 更新冠状面
        focalPoint_XZ, position_XZ = self.update_viewer(self.viewModel.CoronalOrthoViewer, self.vtkWidget_XZ, self.label_XZ,
                                                                  self.verticalSlider_XZ, self.id_XZ)

        CameraPosition.position_XY = position_XY
        CameraPosition.position_YZ = position_YZ
        CameraPosition.position_XZ = position_XZ
        CameraPosition.focalPoint_XY = focalPoint_XY
        CameraPosition.focalPoint_YZ = focalPoint_YZ
        CameraPosition.focalPoint_XZ = focalPoint_XZ


        # 调整图像对比度
        self.contrastService.adjust_window_width_and_level()

        # 更新体绘制窗口
        self.update_volume_viewer()

    def on_actionAdd_IM0_Data(self, slice_thickness):
        setFileIsEmpty(False)
        setIsPutImplant(False)
        setIsGenerateImplant(False)
        setAnchorPointIsComplete(False)
        setIsAdjust(False)

        self.spacing = self.baseModelClass.spacing
        if self.spacing[2] == 0:
            newspacing = (self.spacing[0], self.spacing[1], slice_thickness)
            self.baseModelClass.imageReader.GetOutput().SetSpacing(newspacing)
            self.baseModelClass.imageReader.Update()
            self.baseModelClass.update_data_information()

        self.clear_mousewheel_forward_backward_event([self.viewer_XY,self.viewer_YZ,self.viewer_XZ])

        # 更新横断面
        focalPoint_XY, position_XY = self.update_viewer(self.viewModel.AxialOrthoViewer, self.vtkWidget_XY, self.label_XY,
                                                                  self.verticalSlider_XY, self.id_XY)
        # 更新矢状面
        focalPoint_YZ, position_YZ = self.update_viewer(self.viewModel.SagittalOrthoViewer, self.vtkWidget_YZ, self.label_YZ,
                                                                  self.verticalSlider_YZ, self.id_YZ)
        # 更新冠状面
        focalPoint_XZ, position_XZ = self.update_viewer(self.viewModel.CoronalOrthoViewer, self.vtkWidget_XZ, self.label_XZ,
                                                                  self.verticalSlider_XZ, self.id_XZ)

        CameraPosition.position_XY = position_XY
        CameraPosition.position_YZ = position_YZ
        CameraPosition.position_XZ = position_XZ
        CameraPosition.focalPoint_XY = focalPoint_XY
        CameraPosition.focalPoint_YZ = focalPoint_YZ
        CameraPosition.focalPoint_XZ = focalPoint_XZ

        # 调整图像对比度
        self.contrastService.adjust_window_width_and_level()

        # ------------更新体绘制窗口数据-----------------------------------------
        try:
            self.update_volume_viewer()
        except Exception:
            logger.exception('Create Volume error')

    def on_actionAdd_NIFIT_Data(self, path, slice_index=None):
        """
        加载NIFTI分割结果并与DICOM图像进行叠加显示
        采用重建查看器的方式，创建新的DICOM和分割查看器
        
        Args:
            path: NIFTI文件路径
            slice_index: 可选的切片索引，如果为None则使用默认切片
            
        Raises:
            FileNotFoundError: 当NIFTI文件不存在时
            ValueError: 当文件格式无效或坐标系统不兼容时
            RuntimeError: 当VTK操作失败时
        """
        try:
            logger.info(f"Loading NIFTI segmentation file: {path}")

            # 验证文件存在性
            if not os.path.exists(path):
                error_msg = f"NIFTI file does not exist: {path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            # 验证文件扩展名
            if not (path.endswith('.nii') or path.endswith('.nii.gz')):
                error_msg = f"Invalid NIFTI file format: {path}. Expected .nii or .nii.gz"
                logger.error(error_msg)
                raise ValueError(error_msg)

            if DataAndModelType.DATA_TYPE is None:
                # 类型为空则只需要导入nii文件，将该问卷转换为DICOM图像
                self.load_nii(path)
            else:
                # 使用重建查看器的方式创建DICOM和分割视图
                self.imageblend_seg_mask(path,slice_index)
            
            logger.info("NIFTI segmentation loaded and overlaid successfully")
            
        except FileNotFoundError:
            # Re-raise file not found errors
            raise
        except ValueError:
            # Re-raise validation errors
            raise
        except RuntimeError:
            # Re-raise VTK errors
            raise
        except Exception as e:
            # Catch any unexpected errors
            error_msg = f"Unexpected error loading NIFTI segmentation: {e}"
            logger.exception(error_msg)
            raise RuntimeError(error_msg) from e

    def load_nii(self, path):

        # 初始化错误恢复管理器
        error_recovery_manager = ErrorRecoveryManager()

        self.save_niipath_temp = ParamConstant.OUTPUT_FILE_PATH + 'nii_temp/'
        if not os.path.exists(self.save_niipath_temp):
            os.mkdir(self.save_niipath_temp)
        else:
            for file in glob.glob(self.save_niipath_temp + "*.dcm"):
                os.remove(file)


        self.save_niipath = ParamConstant.OUTPUT_FILE_PATH + 'nii/'
        if not os.path.exists(self.save_niipath):
            os.mkdir(self.save_niipath)
        else:
            for file in glob.glob(self.save_niipath_temp + "*.dcm"):
                os.remove(file)

        # 加载NII文件
        try:
            nii_img = nibabel.load(path)
            # 获取numpy数组数据
            nii_data_raw = nii_img.get_fdata()
            logger.info(f"Successfully loaded NII file: shape={nii_data_raw.shape}, dtype={nii_data_raw.dtype}")
            logger.info(f"Original data range: [{np.min(nii_data_raw)}, {np.max(nii_data_raw)}]")
            
            # 将所有非零标签值统一设置为1（二值化）
            nii_data_binary = np.where(nii_data_raw > 0, 1, 0).astype(np.uint8)
            logger.info(f"Binarized segmentation: all non-zero labels set to 1")
            logger.info(f"Binarized data range: [{np.min(nii_data_binary)}, {np.max(nii_data_binary)}]")
            
            # 对于NIfTI数据，只做简单的轴转置来匹配DICOM的切片顺序
            # 将Z轴移到第一维（切片维度）
            # 原始: (X, Y, Z) -> 转换后: (Z, X, Y)
            nii_data = np.transpose(nii_data_binary, (2, 0, 1))
            
            logger.info(f"Reoriented NIfTI data shape: {nii_data.shape}")
            logger.info(f"Final data range: [{np.min(nii_data)}, {np.max(nii_data)}]")
            
        except Exception as e:
            error_context = error_recovery_manager.create_error_context(
                ErrorType.INVALID_DATA_FORMAT,
                f"Failed to load NII file: {path}",
                file_path=path,
                exception=e
            )
            error_recovery_manager.handle_error(error_context)
            raise ValueError(f"Failed to load NII file: {path}") from e

        # 验证数据格式为三维数组
        if len(nii_data.shape) != 3:
            error_context = error_recovery_manager.create_error_context(
                ErrorType.INVALID_DATA_FORMAT,
                f"Invalid data format. Expected 3D array, got {len(nii_data.shape)}D array with shape: {nii_data.shape}",
                file_path=path
            )
            error_recovery_manager.handle_error(error_context)
            raise ValueError(
                f"Invalid data format. Expected 3D array, got {len(nii_data.shape)}D array with shape: {nii_data.shape}")

        if nii_data.size == 0:
            error_context = error_recovery_manager.create_error_context(
                ErrorType.INVALID_DATA_FORMAT,
                "NII file contains no data",
                file_path=path
            )
            error_recovery_manager.handle_error(error_context)
            raise ValueError("NII file contains no data")

        # 创建NII到DICOM转换器
        conversion_params = DICOMConversionParams(
            pixel_spacing=(1.0, 1.0),
            slice_thickness=1.0,
            patient_name="NII_PATIENT",
            study_description="NII Data Import",
            data_type="NPY"
        )
        converter = NPYToDICOMConverter(conversion_params)

        # 转换NII数据为DICOM格式
        try:
            dicom_files = converter.convert(nii_data, self.save_niipath_temp)
            logger.info(f"Successfully converted NII to {len(dicom_files)} DICOM files")
        except MemoryError as e:
            error_context = error_recovery_manager.create_error_context(
                ErrorType.MEMORY_ERROR,
                f"Insufficient memory to convert NII data",
                file_path=path,
                exception=e
            )
            error_recovery_manager.handle_error(error_context)
            raise RuntimeError(f"Insufficient memory to convert NII data") from e
        except Exception as e:
            error_context = error_recovery_manager.create_error_context(
                ErrorType.CONVERSION_ERROR,
                f"Failed to convert NII to DICOM format",
                file_path=path,
                exception=e
            )
            error_recovery_manager.handle_error(error_context)
            raise RuntimeError(f"Failed to convert NII to DICOM format") from e

        dicom_files = glob.glob(self.save_niipath_temp + "*.dcm")
        dicom_files.sort()
        number_slices = len(dicom_files)
        for index in range(number_slices):
            dicom_file = pydicom.dcmread(dicom_files[index])
            convertNsave(dicom_file, ParamConstant.IMAGE_DCM, self.save_niipath, index)
            self.SliceThickness = dicom_file.SliceThickness


        # DataAndModelType.DATA_TYPE = 'NII'

        setDirPath(self.save_niipath)

        self.reader.SetDirectoryName(self.save_niipath)
        self.reader.Update()
        # 更新 Data Information
        self.baseModelClass.imageReader = self.reader
        self.baseModelClass.update_data_information()

        # XY 窗口
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.vtkWidget_XY = self.viewModel.AxialOrthoViewer.widget
        self.label_XY = self.viewModel.AxialOrthoViewer.slider_label
        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider
        self.id_XY = self.viewModel.AxialOrthoViewer.type

        # YZ 窗口
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.vtkWidget_YZ = self.viewModel.SagittalOrthoViewer.widget
        self.label_YZ = self.viewModel.SagittalOrthoViewer.slider_label
        self.verticalSlider_YZ = self.viewModel.SagittalOrthoViewer.slider
        self.id_YZ = self.viewModel.SagittalOrthoViewer.type

        # XZ 窗口
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        self.vtkWidget_XZ = self.viewModel.CoronalOrthoViewer.widget
        self.label_XZ = self.viewModel.CoronalOrthoViewer.slider_label
        self.verticalSlider_XZ = self.viewModel.CoronalOrthoViewer.slider
        self.id_XZ = self.viewModel.CoronalOrthoViewer.type

        self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
        self.iren_Volume = self.viewModel.VolumeOrthorViewer.renderWindowInteractor

        # 重置系统状态
        setFileIsEmpty(False)
        setIsPutImplant(False)
        setIsGenerateImplant(False)
        setAnchorPointIsComplete(False)
        setIsAdjust(False)

        # 检查和调整spacing
        self.spacing = self.baseModelClass.spacing
        if self.spacing[2] == 0:
            newspacing = (self.spacing[0], self.spacing[1], 1.0)
            self.baseModelClass.imageReader.GetOutput().SetSpacing(newspacing)
            self.baseModelClass.imageReader.Update()
            self.baseModelClass.update_data_information()
            logger.info(f"Adjusted spacing from {self.spacing} to {newspacing}")

        # 清理鼠标滚轮事件
        self.clear_mousewheel_forward_backward_event([self.viewer_XY, self.viewer_YZ, self.viewer_XZ])

        # 更新三个正交视图
        try:
            # 更新横断面 (XY)
            focalPoint_XY, position_XY = self.update_viewer(
                self.viewModel.AxialOrthoViewer, self.vtkWidget_XY, self.label_XY,
                self.verticalSlider_XY, self.id_XY
            )

            # 更新矢状面 (YZ)
            focalPoint_YZ, position_YZ = self.update_viewer(
                self.viewModel.SagittalOrthoViewer, self.vtkWidget_YZ, self.label_YZ,
                self.verticalSlider_YZ, self.id_YZ
            )

            # 更新冠状面 (XZ)
            focalPoint_XZ, position_XZ = self.update_viewer(
                self.viewModel.CoronalOrthoViewer, self.vtkWidget_XZ, self.label_XZ,
                self.verticalSlider_XZ, self.id_XZ
            )

            # 更新相机位置
            CameraPosition.position_XY = position_XY
            CameraPosition.position_YZ = position_YZ
            CameraPosition.position_XZ = position_XZ
            CameraPosition.focalPoint_XY = focalPoint_XY
            CameraPosition.focalPoint_YZ = focalPoint_YZ
            CameraPosition.focalPoint_XZ = focalPoint_XZ

            logger.info("Successfully updated all orthogonal views")

        except Exception as e:
            error_context = error_recovery_manager.create_error_context(
                ErrorType.VTK_ERROR,
                f"Failed to update orthogonal views",
                file_path=path,
                exception=e
            )
            error_recovery_manager.handle_error(error_context)
            raise RuntimeError(f"Failed to update orthogonal views") from e

        # 调整图像对比度
        try:
            self.contrastService.adjust_window_width_and_level()
            logger.info("Successfully adjusted image contrast")
        except Exception as e:
            logger.warning(f"Failed to adjust image contrast: {e}")
            # 对比度调整失败不应该阻止整个流程

        # 更新体绘制窗口
        try:
            self.update_volume_viewer()
            logger.info("Successfully updated volume viewer")
        except Exception as e:
            logger.warning(f"Failed to update volume viewer: {e}")
            # 体绘制更新失败不应该阻止整个流程

        logger.info("NII data loading and visualization completed successfully")

    def imageblend_seg_mask(self,path, slice_index=None):
        """
        创建DICOM和分割图像的混合显示
        重建DICOM查看器和分割查看器，实现叠加显示

        Args:
            path: .nii文件路劲
            slice_index: 可选的切片索引
        """
        try:
            logger.debug("Creating blended DICOM and segmentation viewers")

            # 读取NIFTI分割文件
            self.reader_seg = vtk.vtkNIFTIImageReader()
            self.reader_seg.SetFileName(path)

            try:
                self.reader_seg.Update()
            except Exception as e:
                error_msg = f"VTK NIFTI reader failed to read file: {path}"
                logger.error(f"{error_msg}. Error: {e}")
                raise RuntimeError(error_msg) from e

            # 获取DICOM和分割图像数据
            dicom_image = self.reader.GetOutput()
            seg_image = self.reader_seg.GetOutput()

            # 验证图像数据有效性
            if seg_image is None or seg_image.GetNumberOfPoints() == 0:
                error_msg = f"NIFTI file contains no valid image data: {path}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 记录图像信息用于调试
            seg_dims = seg_image.GetDimensions()
            seg_origin = seg_image.GetOrigin()
            seg_spacing = seg_image.GetSpacing()
            dicom_dims = dicom_image.GetDimensions()
            dicom_origin = dicom_image.GetOrigin()
            dicom_spacing = dicom_image.GetSpacing()

            logger.debug(f"NIFTI dimensions: {seg_dims}, origin: {seg_origin}, spacing: {seg_spacing}")
            logger.debug(f"DICOM dimensions: {dicom_dims}, origin: {dicom_origin}, spacing: {dicom_spacing}")

            # 验证坐标系统兼容性
            if seg_dims != dicom_dims:
                logger.warning(f"Dimension mismatch - NIFTI: {seg_dims}, DICOM: {dicom_dims}")
                logger.warning("Proceeding with alignment, but results may not be accurate")

            # 对分割图像进行翻转以匹配DICOM坐标系
            try:
                flip1 = vtk.vtkImageFlip()
                flip1.SetInputData(seg_image)
                flip1.SetFilteredAxis(2)
                flip1.Update()

                flip2 = vtk.vtkImageFlip()
                flip2.SetInputData(flip1.GetOutput())
                flip2.SetFilteredAxis(1)
                flip2.Update()
            except Exception as e:
                error_msg = "Failed to apply coordinate flipping transformations"
                logger.error(f"{error_msg}. Error: {e}")
                raise RuntimeError(error_msg) from e

            # 确保分割结果与DICOM的几何信息一致
            try:
                change_info = vtk.vtkImageChangeInformation()
                change_info.SetInputConnection(flip2.GetOutputPort())
                change_info.SetOutputOrigin(dicom_image.GetOrigin())
                change_info.SetOutputSpacing(dicom_image.GetSpacing())
                change_info.Update()

                self.seg_image_aligned = change_info.GetOutput()
            except Exception as e:
                error_msg = "Failed to align NIFTI coordinate system with DICOM"
                logger.error(f"{error_msg}. Error: {e}")
                raise RuntimeError(error_msg) from e

            # 验证对齐结果
            aligned_origin = self.seg_image_aligned.GetOrigin()
            aligned_spacing = self.seg_image_aligned.GetSpacing()
            logger.debug(f"Aligned origin: {aligned_origin}, spacing: {aligned_spacing}")

            # 获取分割图像的实际数据范围
            data_min, data_max = self.seg_image_aligned.GetScalarRange()
            logger.info(f"Segmentation image scalar range: {data_min} - {data_max}")

            # 创建颜色查找表
            try:
                self.color_table = vtk.vtkLookupTable()
                self.color_table.SetNumberOfColors(256)
                self.color_table.SetTableRange(data_min, data_max)
                self.color_table.SetTableValue(0, 0.0, 0.0, 1.0, 0.0)  # 背景透明
                for i in range(1, 256):
                    self.color_table.SetTableValue(i, 1, 0, 0, 1.0)  # 红色不透明
                self.color_table.Build()
            except Exception as e:
                error_msg = "Failed to create color lookup table"
                logger.error(f"{error_msg}. Error: {e}")
                raise RuntimeError(error_msg) from e

            self.rwi_XY = self.viewer_XY.GetRenderWindow().GetInteractor();
            self.rwi_YZ = self.viewer_YZ.GetRenderWindow().GetInteractor();
            self.rwi_XZ = self.viewer_XZ.GetRenderWindow().GetInteractor();

            # 创建新的DICOM查看器
            position_XY,focalPoint_XY,self.viewer_dicom_xy = self.create_dicom_viewer(
                self.viewModel.AxialOrthoViewer, self.vtkWidget_XY, self.label_XY,
                self.verticalSlider_XY, self.id_XY, slice_index
            )
            position_YZ,focalPoint_YZ,self.viewer_dicom_yz = self.create_dicom_viewer(
                self.viewModel.SagittalOrthoViewer, self.vtkWidget_YZ, self.label_YZ,
                self.verticalSlider_YZ, self.id_YZ, slice_index
            )
            position_XZ,focalPoint_XZ,self.viewer_dicom_xz = self.create_dicom_viewer(
                self.viewModel.CoronalOrthoViewer, self.vtkWidget_XZ, self.label_XZ,
                self.verticalSlider_XZ, self.id_XZ, slice_index
            )

            CameraPosition.position_XY = position_XY
            CameraPosition.position_YZ = position_YZ
            CameraPosition.position_XZ = position_XZ
            CameraPosition.focalPoint_XY = focalPoint_XY
            CameraPosition.focalPoint_YZ = focalPoint_YZ
            CameraPosition.focalPoint_XZ = focalPoint_XZ


            # 创建分割查看器
            self.viewer_seg_xy = self.create_seg_viewer(
                self.viewModel.AxialOrthoViewer, self.vtkWidget_XY, self.label_XY,
                self.verticalSlider_XY, self.id_XY, slice_index
            )
            self.viewer_seg_yz = self.create_seg_viewer(
                self.viewModel.SagittalOrthoViewer, self.vtkWidget_YZ, self.label_YZ,
                self.verticalSlider_YZ, self.id_YZ, slice_index
            )
            self.viewer_seg_xz = self.create_seg_viewer(
                self.viewModel.CoronalOrthoViewer, self.vtkWidget_XZ, self.label_XZ,
                self.verticalSlider_XZ, self.id_XZ, slice_index
            )


            logger.info("Successfully created blended DICOM and segmentation viewers")

        except Exception as e:
            error_msg = f"Failed to create blended viewers: {e}"
            logger.exception(error_msg)
            raise RuntimeError(error_msg) from e


    def create_dicom_viewer(self, ortho_viewer, vtkWidget, label, verticalSlider, id, slice_index):
        """
        创建DICOM图像查看器

        """
        try:
            bounds = self.baseModelClass.bounds
            center0 = (bounds[1] + bounds[0]) / 2.0
            center1 = (bounds[3] + bounds[2]) / 2.0
            center2 = (bounds[5] + bounds[4]) / 2.0

            viewer_dicom = vtk.vtkImageViewer2()
            viewer_dicom.SetInputData(self.reader.GetOutput())
            viewer_dicom.SetRenderWindow(vtkWidget.GetRenderWindow())
            viewer_dicom.SetupInteractor(vtkWidget)
            
            # 设置交互器样式以支持缩放功能
            interactor = viewer_dicom.GetRenderWindow().GetInteractor()
            if interactor is not None:
                # 使用vtkInteractorStyleImage来支持图像交互（包括缩放）
                style = vtk.vtkInteractorStyleImage()
                style.SetInteractionModeToImageSlicing()
                interactor.SetInteractorStyle(style)
                
                # 确保交互器已初始化
                if not interactor.GetInitialized():
                    interactor.Initialize()
            
            maxSlice = ortho_viewer.viewer.GetSliceMax()
            value = int(maxSlice / 2.0)

            if id == "XY":
                viewer_dicom.SetSliceOrientationToXY()
                if slice_index is None:
                    viewer_dicom.SetSlice(value)
                    verticalSlider.setValue(value)
                else:
                    value = slice_index
                    viewer_dicom.SetSlice(value)
                    verticalSlider.setValue(value)
            elif id == "YZ":
                viewer_dicom.SetSlice(value)
                verticalSlider.setValue(value)

                viewer_dicom.SetSliceOrientationToYZ()
                transform_YZ = vtk.vtkTransform()
                transform_YZ.Translate(center0, center1, center2)
                transform_YZ.RotateX(180)
                transform_YZ.RotateZ(180)
                transform_YZ.Translate(-center0, -center1, -center2)
                viewer_dicom.GetImageActor().SetUserTransform(transform_YZ)

            elif id == "XZ":
                viewer_dicom.SetSlice(value)
                verticalSlider.setValue(value)

                viewer_dicom.SetSliceOrientationToXZ()
                transform_XZ = vtk.vtkTransform()
                transform_XZ.Translate(center0, center1, center2)
                transform_XZ.RotateY(180)
                transform_XZ.RotateZ(180)
                transform_XZ.Translate(-center0, -center1, -center2)
                viewer_dicom.GetImageActor().SetUserTransform(transform_XZ)


            viewer_dicom.SetColorWindow(ToolBarWidget.contrast_widget.window_width_slider.value())
            viewer_dicom.SetColorLevel(ToolBarWidget.contrast_widget.window_level_slider.value())

            camera = viewer_dicom.GetRenderer().GetActiveCamera()
            camera.ParallelProjectionOn()
            camera.SetParallelScale(80)
            focalPoint = camera.GetFocalPoint()
            position = camera.GetPosition()

            verticalSlider.setMaximum(maxSlice)
            verticalSlider.setMinimum(0)
            verticalSlider.setSingleStep(1)

            label.setText("Slice %d/%d" % (verticalSlider.value(), maxSlice))

            viewer_dicom.Render()
            ortho_viewer.viewer = viewer_dicom

            return focalPoint, position, viewer_dicom

        except Exception as e:
            error_msg = f"Failed to create {id} DICOM viewer: {e}"
            logger.exception(error_msg)
            raise RuntimeError(error_msg) from e


    def create_seg_viewer(self, ortho_viewer, vtkWidget, label, verticalSlider, id, slice_index):
        """
        创建分割图像查看器
        关键：不要调用 SetupInteractor，因为 DICOM viewer 已经设置了
        """
        try:
            bounds = self.baseModelClass.bounds
            center0 = (bounds[1] + bounds[0]) / 2.0
            center1 = (bounds[3] + bounds[2]) / 2.0
            center2 = (bounds[5] + bounds[4]) / 2.0

            viewerLayer = vtk.vtkImageViewer2()
            viewerLayer.SetInputData(self.seg_image_aligned)
            viewerLayer.SetRenderWindow(ortho_viewer.viewer.GetRenderWindow())

            viewer_dicom = ortho_viewer.viewer

            if id == "XY":
                rwi = self.rwi_XY
                viewerLayer.SetSliceOrientationToXY()
                if slice_index is None:
                    viewerLayer.SetSlice(viewer_dicom.GetSlice())
                else:
                    viewerLayer.SetSlice(slice_index)

            elif id == "YZ":
                rwi = self.rwi_YZ
                viewerLayer.SetSliceOrientationToYZ()
                transform_YZ = vtk.vtkTransform()
                transform_YZ.Translate(center0, center1, center2)
                transform_YZ.RotateX(180)
                transform_YZ.RotateZ(180)
                transform_YZ.Translate(-center0, -center1, -center2)
                viewerLayer.GetImageActor().SetUserTransform(transform_YZ)
                viewerLayer.SetSlice(viewer_dicom.GetSlice())

            else:  # XZ
                rwi = self.rwi_XZ
                viewerLayer.SetSliceOrientationToXZ()
                transform_XZ = vtk.vtkTransform()
                transform_XZ.Translate(center0, center1, center2)
                transform_XZ.RotateY(180)
                transform_XZ.RotateZ(180)
                transform_XZ.Translate(-center0, -center1, -center2)
                viewerLayer.GetImageActor().SetUserTransform(transform_XZ)
                viewerLayer.SetSlice(viewer_dicom.GetSlice())


            # 创建事件处理器
            wheelforward = MouseWheelForwardSeg(viewer_dicom, viewerLayer, label, verticalSlider, id)
            wheelbackward = MouseWheelBackWardSeg(viewer_dicom, viewerLayer, label, verticalSlider, id)


            viewerLayer.GetImageActor().SetInterpolate(False)
            viewerLayer.GetImageActor().GetProperty().SetLookupTable(self.color_table)
            viewerLayer.GetImageActor().GetProperty().SetDiffuse(0.0)
            viewerLayer.GetImageActor().SetPickable(False)

            viewer_dicom.SetupInteractor(rwi)

            # 将分割图层添加到 DICOM viewer 的 renderer 中
            viewer_dicom.GetRenderer().AddActor(viewerLayer.GetImageActor())

            # 获取 DICOM viewer 的 interactor style 并添加事件
            viewer_dicom_interactor = viewer_dicom.GetInteractorStyle()
            if viewer_dicom_interactor:
                forward_tag = viewer_dicom_interactor.AddObserver("MouseWheelForwardEvent", wheelforward)
                backward_tag = viewer_dicom_interactor.AddObserver("MouseWheelBackwardEvent", wheelbackward)
                logger.info(f"Added mouse wheel observers for {id}: forward={forward_tag}, backward={backward_tag}")
            else:
                logger.warning(f"Failed to get interactor style for DICOM viewer {id}")

            viewerLayer.Render()
            viewer_dicom.Render()

            return viewerLayer

        except Exception as e:
            error_msg = f"Failed to create {id} segmentation viewer: {e}"
            logger.exception(error_msg)
            raise RuntimeError(error_msg) from e

    def on_actionAdd_NPY_Data(self, slice_thickness):
        """
        加载和处理NPY数据

        Args:
            slice_thickness: 切片厚度

        Raises:
            FileNotFoundError: 当NPY文件不存在时
            ValueError: 当数据格式无效时
            RuntimeError: 当VTK操作失败时
            OSError: 当文件操作失败时
        """
        error_recovery_manager = None

        try:

            # 初始化错误恢复管理器
            error_recovery_manager = ErrorRecoveryManager()

            # 重置系统状态
            setFileIsEmpty(False)
            setIsPutImplant(False)
            setIsGenerateImplant(False)
            setAnchorPointIsComplete(False)
            setIsAdjust(False)

            # 检查和调整spacing
            self.spacing = self.baseModelClass.spacing
            if self.spacing[2] == 0:
                newspacing = (self.spacing[0], self.spacing[1], 1.0)
                self.baseModelClass.imageReader.GetOutput().SetSpacing(newspacing)
                self.baseModelClass.imageReader.Update()
                self.baseModelClass.update_data_information()
                logger.info(f"Adjusted spacing from {self.spacing} to {newspacing}")

            # 清理鼠标滚轮事件
            self.clear_mousewheel_forward_backward_event([self.viewer_XY, self.viewer_YZ, self.viewer_XZ])

            # 更新三个正交视图
            try:
                # 更新横断面 (XY)
                focalPoint_XY, position_XY = self.update_viewer(
                    self.viewModel.AxialOrthoViewer, self.vtkWidget_XY, self.label_XY,
                    self.verticalSlider_XY, self.id_XY
                )

                # 更新矢状面 (YZ)
                focalPoint_YZ, position_YZ = self.update_viewer(
                    self.viewModel.SagittalOrthoViewer, self.vtkWidget_YZ, self.label_YZ,
                    self.verticalSlider_YZ, self.id_YZ
                )

                # 更新冠状面 (XZ)
                focalPoint_XZ, position_XZ = self.update_viewer(
                    self.viewModel.CoronalOrthoViewer, self.vtkWidget_XZ, self.label_XZ,
                    self.verticalSlider_XZ, self.id_XZ
                )

                # 更新相机位置
                CameraPosition.position_XY = position_XY
                CameraPosition.position_YZ = position_YZ
                CameraPosition.position_XZ = position_XZ
                CameraPosition.focalPoint_XY = focalPoint_XY
                CameraPosition.focalPoint_YZ = focalPoint_YZ
                CameraPosition.focalPoint_XZ = focalPoint_XZ

                logger.info("Successfully updated all orthogonal views")

            except Exception as e:
                error_context = error_recovery_manager.create_error_context(
                    ErrorType.VTK_ERROR,
                    f"Failed to update orthogonal views",
                    file_path=slice_thickness,
                    exception=e
                )
                error_recovery_manager.handle_error(error_context)
                raise RuntimeError(f"Failed to update orthogonal views") from e

            # 调整图像对比度
            try:
                self.contrastService.adjust_window_width_and_level()
                logger.info("Successfully adjusted image contrast")
            except Exception as e:
                logger.warning(f"Failed to adjust image contrast: {e}")
                # 对比度调整失败不应该阻止整个流程

            # 更新体绘制窗口
            try:
                self.update_volume_viewer()
                logger.info("Successfully updated volume viewer")
            except Exception as e:
                logger.warning(f"Failed to update volume viewer: {e}")
                # 体绘制更新失败不应该阻止整个流程

            logger.info("NPY data loading and visualization completed successfully")

        except FileNotFoundError:
            # 重新抛出文件未找到错误
            if error_recovery_manager:
                error_recovery_manager.cleanup_resources()
            raise

        except ValueError:
            # 重新抛出验证错误
            if error_recovery_manager:
                error_recovery_manager.cleanup_resources()
            raise

        except RuntimeError:
            # 重新抛出VTK错误
            if error_recovery_manager:
                error_recovery_manager.cleanup_resources()
            raise

        except Exception as e:
            # 捕获任何意外错误
            error_msg = f"Unexpected error during NPY data processing: {e}"
            logger.exception(error_msg)

            if error_recovery_manager:
                try:
                    error_context = error_recovery_manager.create_error_context(
                        ErrorType.UNKNOWN_ERROR,
                        error_msg,
                        file_path=slice_thickness,
                        exception=e
                    )
                    error_recovery_manager.handle_error(error_context)
                    error_recovery_manager.cleanup_resources()
                except Exception as recovery_error:
                    logger.error(f"Error recovery failed: {recovery_error}")

            raise RuntimeError(error_msg) from e

    def update_viewer(self, ortho_viewer, vtkWidget, label, verticalSlider, id):
        bounds = self.baseModelClass.bounds
        logger.debug("data bounds: %s", bounds)
        self.center0 = (bounds[1] + bounds[0]) / 2.0
        self.center1 = (bounds[3] + bounds[2]) / 2.0
        self.center2 = (bounds[5] + bounds[4]) / 2.0

        viewer = vtk.vtkResliceImageViewer()
        viewer.SetInputData(self.reader.GetOutput())
        viewer.SetupInteractor(vtkWidget)
        viewer.SetRenderWindow(vtkWidget.GetRenderWindow())

        if id == "XY":
            viewer.SetSliceOrientationToXY()
        elif id == "YZ":
            viewer.SetSliceOrientationToYZ()
            # Apply transformations for both DICOM and NPY data to ensure consistent visualization
            if DataAndModelType.DATA_TYPE in ["DICOM", "NPY"]:
                transform_YZ = vtk.vtkTransform()
                transform_YZ.Translate(self.center0, self.center1, self.center2)
                transform_YZ.RotateX(180)
                transform_YZ.RotateZ(180)
                transform_YZ.Translate(-self.center0, -self.center1, -self.center2)
                viewer.GetImageActor().SetUserTransform(transform_YZ)
        elif id == "XZ":
            viewer.SetSliceOrientationToXZ()
            # Apply transformations for both DICOM and NPY data to ensure consistent visualization
            if DataAndModelType.DATA_TYPE in ["DICOM", "NPY"]:
                transform_XZ = vtk.vtkTransform()
                transform_XZ.Translate(self.center0, self.center1, self.center2)
                transform_XZ.RotateY(180)
                transform_XZ.RotateZ(180)
                transform_XZ.Translate(-self.center0, -self.center1, -self.center2)
                viewer.GetImageActor().SetUserTransform(transform_XZ)

        viewer.SliceScrollOnMouseWheelOff()
        viewer.UpdateDisplayExtent()
        viewer.Render()

        camera = viewer.GetRenderer().GetActiveCamera()
        camera.ParallelProjectionOn()
        camera.SetParallelScale(80)
        focalPoint = camera.GetFocalPoint()
        position = camera.GetPosition()

        wheelforward = MouseWheelForward(viewer, label, verticalSlider, id)
        wheelbackward = MouseWheelBackWard(viewer, label, verticalSlider, id)
        viewer_InteractorStyle = viewer.GetInteractorStyle()
        viewer_InteractorStyle.AddObserver("MouseWheelForwardEvent", wheelforward)
        viewer_InteractorStyle.AddObserver("MouseWheelBackwardEvent", wheelbackward)

        value = viewer.GetSlice()
        maxSlice = viewer.GetSliceMax()
        verticalSlider.setMaximum(maxSlice)
        verticalSlider.setMinimum(0)
        verticalSlider.setSingleStep(1)
        verticalSlider.setValue(value)
        label.setText("Slice %d/%d" % (verticalSlider.value(), maxSlice))
        viewer.Render()

        ortho_viewer.viewer = viewer

        return focalPoint, position

    def clear_mousewheel_forward_backward_event(self, viewer_list):
        try:
            for viewer in viewer_list:
                viewer_InteractorStyle = viewer.GetInteractorStyle()
                viewer_InteractorStyle.RemoveObservers("MouseWheelForwardEvent")
                viewer_InteractorStyle.RemoveObservers("MouseWheelBackwardEvent")
        except Exception:
            logger.debug("mouse wheel event not exist", exc_info=True)

    def update_volume_viewer(self):
        # 创建体绘制映射器
        volumeMapper = vtk.vtkGPUVolumeRayCastMapper()  # 提高渲染性能
        volumeMapper.SetInputConnection(self.baseModelClass.imageReader.GetOutputPort())

        # 获取数据的标量范围以适应不同数据类型
        scalar_range = self.baseModelClass.scalerRange
        data_min, data_max = scalar_range
        logger.debug(f"Volume viewer scalar range: {data_min} - {data_max}")

        # 设置体绘制颜色 - 根据数据范围自适应
        color_transfer_function = vtk.vtkColorTransferFunction()

        if DataAndModelType.DATA_TYPE == "NPY" or DataAndModelType.DATA_TYPE is None:
            # NPY数据可能有不同的标量范围，使用相对值
            range_span = data_max - data_min
            color_transfer_function.AddRGBPoint(data_min, 0.0, 0.0, 0.0)
            color_transfer_function.AddRGBPoint(data_min + 0.25 * range_span, 1.0, 0.5, 0.3)
            color_transfer_function.AddRGBPoint(data_min + 0.5 * range_span, 1.0, 0.5, 0.3)
            color_transfer_function.AddRGBPoint(data_min + 0.75 * range_span, 1.0, 0.7, 0.4)
            color_transfer_function.AddRGBPoint(data_max, 1.0, 1.0, 1.0)
        else:
            # DICOM数据使用固定值
            color_transfer_function.AddRGBPoint(0, 0.0, 0.0, 0.0)
            color_transfer_function.AddRGBPoint(1000, 1.0, 0.5, 0.3)
            color_transfer_function.AddRGBPoint(1500, 1.0, 0.5, 0.3)
            color_transfer_function.AddRGBPoint(2000, 1.0, 0.7, 0.4)
            color_transfer_function.AddRGBPoint(4000, 1.0, 1.0, 1.0)  # 4095

        # 设置体绘制不透明度 - 根据数据范围自适应
        opacity_transfer_function = vtk.vtkPiecewiseFunction()

        if DataAndModelType.DATA_TYPE == "NPY" or DataAndModelType.DATA_TYPE is None:
            # NPY数据使用相对透明度设置
            range_span = data_max - data_min
            opacity_transfer_function.AddPoint(data_min, 0.0)
            opacity_transfer_function.AddPoint(data_min + 0.2 * range_span, 0.0)
            opacity_transfer_function.AddPoint(data_min + 0.5 * range_span, 0.3)
            opacity_transfer_function.AddPoint(data_min + 0.75 * range_span, 0.6)
            opacity_transfer_function.AddPoint(data_max, 0.9)
        else:
            # DICOM数据使用固定值
            opacity_transfer_function.AddPoint(0, 0.0)
            opacity_transfer_function.AddPoint(900, 0.0)
            opacity_transfer_function.AddPoint(1500, 0.3)
            opacity_transfer_function.AddPoint(2000, 0.6)
            opacity_transfer_function.AddPoint(4000, 0.9)  # 4095

        # 添加体绘制光照效果
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(color_transfer_function)
        volumeProperty.SetScalarOpacity(opacity_transfer_function)
        volumeProperty.ShadeOn()
        volumeProperty.SetAmbient(0.5)
        volumeProperty.SetDiffuse(0.7)
        volumeProperty.SetSpecular(0.5)

        # 创建体绘制对象
        volume_cbct = vtk.vtkVolume()
        volume_cbct.SetMapper(volumeMapper)
        volume_cbct.SetProperty(volumeProperty)
        # 添加体绘制到渲染器
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(0.5, 0.5, 0.5)
        renderer.AddVolume(volume_cbct)
        renderer.ResetCamera()
        self.vtkWidget_Volume.GetRenderWindow().AddRenderer(renderer)

        VolumeRender.volume_cbct = volume_cbct

        style = vtk.vtkInteractorStyleTrackballCamera()  # 交互器样式的一种，该样式下，用户是通过控制相机对物体作旋转、放大、缩小等操作
        style.SetDefaultRenderer(renderer)
        style.EnabledOn()
        self.iren_Volume.SetInteractorStyle(style)
        # ==================添加一个三维坐标指示=======================================
        axesActor = vtk.vtkAxesActor()
        axes = vtk.vtkOrientationMarkerWidget()
        axes.SetOrientationMarker(axesActor)
        axes.SetInteractor(self.iren_Volume)
        axes.EnabledOn()
        axes.SetEnabled(1)
        axes.InteractiveOff()
        renderer.ResetCamera()
        self.vtkWidget_Volume.Render()

        self.viewModel.VolumeOrthorViewer.renderer = renderer

        self.iren_Volume.Initialize()

    def valuechange1(self):
        viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        if not ToolBarEnable.crosshair_enable:
            value_XY = self.verticalSlider_XY.value()
            if AnnotationEnable.pointAction.isChecked():
                try:
                    for i in getPointsActor():
                        viewer_XY.GetRenderer().RemoveActor(i)
                    viewer_XY.Render()
                except Exception:
                    logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
                viewer_XY.SetSlice(value_XY)
                if getPointsUndoStack() != []:
                    for point in getPointsUndoStack():
                        logger.debug("point undo stack entry: %s", point)
                        if point[2] == value_XY:
                            self.annotationService.point_paints(point)
            if AnnotationEnable.labelBoxAction.isChecked():
                logger.debug("Processing bounding box redraw")
                if getSelectSingleBoxLabel():
                    try:
                        for i in getSingleBoundingBoxActor():
                            viewer_XY.GetRenderer().RemoveActor(i)
                        viewer_XY.Render()
                    except Exception:
                        logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
                    value = value_XY
                    viewer_XY.SetSlice(value)
                    if getSingleUndoStack():
                        for data in getSingleUndoStack():
                            if data[4] == value_XY:
                                logger.debug("single redo triggered")
                                actor_list = self.annotationService.drwa_single_bounding_box(data)
                                setSingleBoundingBoxActor(actor_list)
                    viewer_XY.UpdateDisplayExtent()
                    viewer_XY.Render()
                else:
                    try:
                        for i in getSingleBoundingBoxActor():
                            viewer_XY.GetRenderer().RemoveActor(i)
                    except Exception:
                        logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
                    try:
                        for i in getLastBoundingBoxActor():
                            viewer_XY.GetRenderer().RemoveActor(i)
                    except Exception:
                        logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
                    try:
                        for actor in getMultipleBoundingBoxActor():
                            for i in actor:
                                viewer_XY.GetRenderer().RemoveActor(i)
                        clearMultipleBoundingBoxActor()
                        viewer_XY.Render()
                    except Exception:
                        logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
                    value = value_XY
                    viewer_XY.SetSlice(value)
                    if getMultipleUndoStack():
                        for data in getMultipleUndoStack():
                            if data[4] == value_XY:
                                logger.debug("multiple redo triggered")
                                actor_list = self.annotationService.drwa_single_bounding_box(data)
                                setMultipleBoundingBoxActor(actor_list)
                    viewer_XY.UpdateDisplayExtent()
                    viewer_XY.Render()
            else:
                viewer_XY.SetSlice(value_XY)
            viewer_XY.UpdateDisplayExtent()
            viewer_XY.Render()

            # 确保分割查看器同步更新
            if hasattr(self, 'viewer_seg_xy') and self.viewer_seg_xy:
                self.viewer_seg_xy.SetSlice(value_XY)
                self.viewer_seg_xy.UpdateDisplayExtent()
                self.viewer_seg_xy.Render()
            self.label_XY.setText("Slice %d/%d" % (viewer_XY.GetSlice(), viewer_XY.GetSliceMax()))
            

        else:
            center = list(viewer_XY.GetResliceCursor().GetCenter())
            value_XY = self.verticalSlider_XY.value()
            value_YZ = self.verticalSlider_YZ.value()
            value_XZ = self.verticalSlider_XZ.value()
            origin = self.baseModelClass.origin
            spacing = self.baseModelClass.spacing
            center[2] = value_XY * spacing[2] - origin[2]
            viewer_XY.GetResliceCursor().SetCenter(center)
            viewer_XY.GetResliceCursor().Update()
            viewer_XY.GetResliceCursorWidget().Render()
            viewer_YZ.GetResliceCursorWidget().Render()
            viewer_XZ.GetResliceCursorWidget().Render()
            self.label_XY.setText("Slice %d/%d" % (value_XY, viewer_XY.GetSliceMax()))
            self.label_YZ.setText("Slice %d/%d" % (value_YZ, viewer_YZ.GetSliceMax()))
            self.label_XZ.setText("Slice %d/%d" % (value_XZ, viewer_XZ.GetSliceMax()))
            self.vtkWidget_XY.GetRenderWindow().Render()
            self.vtkWidget_YZ.GetRenderWindow().Render()
            self.vtkWidget_XZ.GetRenderWindow().Render()

    def valuechange2(self):
        viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        if not ToolBarEnable.crosshair_enable:
            logger.debug("ResliceImageView Change YZ")
            value = self.verticalSlider_YZ.value()
            viewer_YZ.SetSlice(value)
            viewer_YZ.UpdateDisplayExtent()
            viewer_YZ.Render()
            # 确保分割查看器同步更新
            if hasattr(self, 'viewer_seg_yz') and self.viewer_seg_yz:
                self.viewer_seg_yz.SetSlice(value)
                self.viewer_seg_yz.UpdateDisplayExtent()
                self.viewer_seg_yz.Render()
            self.label_YZ.setText("Slice %d/%d" % (viewer_YZ.GetSlice(), viewer_YZ.GetSliceMax()))
        else:
            center = list(viewer_XY.GetResliceCursor().GetCenter())
            value_XY = self.verticalSlider_XY.value()
            value_YZ = self.verticalSlider_YZ.value()
            value_XZ = self.verticalSlider_XZ.value()
            origin = self.baseModelClass.origin
            spacing = self.baseModelClass.spacing
            center[0] = value_YZ * spacing[0] - origin[0]
            viewer_XY.GetResliceCursor().SetCenter(center)
            viewer_XY.GetResliceCursor().Update()
            viewer_XY.GetResliceCursorWidget().Render()
            viewer_YZ.GetResliceCursorWidget().Render()
            viewer_XZ.GetResliceCursorWidget().Render()
            self.label_XY.setText("Slice %d/%d" % (value_XY, viewer_XY.GetSliceMax()))
            self.label_YZ.setText("Slice %d/%d" % (value_YZ, viewer_YZ.GetSliceMax()))
            self.label_XZ.setText("Slice %d/%d" % (value_XZ, viewer_XZ.GetSliceMax()))
            self.vtkWidget_XY.GetRenderWindow().Render()
            self.vtkWidget_YZ.GetRenderWindow().Render()
            self.vtkWidget_XZ.GetRenderWindow().Render()

    def valuechange3(self):
        viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        if not ToolBarEnable.crosshair_enable:
            logger.debug("ResliceImageView Change XZ")
            value = self.verticalSlider_XZ.value()
            viewer_XZ.SetSlice(value)
            viewer_XZ.UpdateDisplayExtent()
            viewer_XZ.Render()
            # 确保分割查看器同步更新
            if hasattr(self, 'viewer_seg_xz') and self.viewer_seg_xz:
                self.viewer_seg_xz.SetSlice(value)
                self.viewer_seg_xz.UpdateDisplayExtent()
                self.viewer_seg_xz.Render()
            self.label_XZ.setText("Slice %d/%d" % (viewer_XZ.GetSlice(), viewer_XZ.GetSliceMax()))
        else:
            center = list(viewer_XY.GetResliceCursor().GetCenter())
            value_XY = self.verticalSlider_XY.value()
            value_YZ = self.verticalSlider_YZ.value()
            value_XZ = self.verticalSlider_XZ.value()
            origin = self.baseModelClass.origin
            spacing = self.baseModelClass.spacing
            center[1] = value_XZ * spacing[1] - origin[1]
            viewer_XY.GetResliceCursor().SetCenter(center)
            viewer_XY.GetResliceCursor().Update()
            viewer_XY.GetResliceCursorWidget().Render()
            viewer_YZ.GetResliceCursorWidget().Render()
            viewer_XZ.GetResliceCursorWidget().Render()
            self.label_XY.setText("Slice %d/%d" % (value_XY, viewer_XY.GetSliceMax()))
            self.label_YZ.setText("Slice %d/%d" % (value_YZ, viewer_YZ.GetSliceMax()))
            self.label_XZ.setText("Slice %d/%d" % (value_XZ, viewer_XZ.GetSliceMax()))
            self.vtkWidget_XY.GetRenderWindow().Render()
            self.vtkWidget_YZ.GetRenderWindow().Render()
            self.vtkWidget_XZ.GetRenderWindow().Render()

