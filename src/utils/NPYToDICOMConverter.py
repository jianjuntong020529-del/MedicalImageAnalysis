# -*- coding: utf-8 -*-
# @Time    : 2024/12/24
"""
NPY到DICOM转换器
将NumPy数组格式的医学影像数据转换为DICOM格式
"""

import os
import tempfile
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid
import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DICOMConversionParams:
    """DICOM转换参数"""
    pixel_spacing: Tuple[float, float] = (1.0, 1.0)
    slice_thickness: float = 1.0
    bits_allocated: int = 16
    bits_stored: int = 16
    high_bit: int = 15
    pixel_representation: int = 1  # 有符号
    photometric_interpretation: str = "MONOCHROME2"
    samples_per_pixel: int = 1
    patient_name: str = "NPY_PATIENT"
    patient_id: str = "NPY_001"
    study_description: str = "NPY Data Import"
    series_description: str = "NPY Series"
    data_type: str = None


class NPYToDICOMConverter:
    """NPY到DICOM转换器"""
    
    def __init__(self, conversion_params: Optional[DICOMConversionParams] = None):
        """
        初始化转换器
        
        Args:
            conversion_params: DICOM转换参数，如果为None则使用默认参数
        """
        self.params = conversion_params or DICOMConversionParams()
        self.study_instance_uid = generate_uid()
        self.series_instance_uid = generate_uid()
        
    def convert(self, npy_data: np.ndarray, output_dir: str) -> List[str]:
        """
        转换NPY数据为DICOM文件序列
        
        Args:
            npy_data: 三维numpy数组 (height, width, depth)
            output_dir: 输出目录路径
            
        Returns:
            List[str]: 生成的DICOM文件路径列表
            
        Raises:
            ValueError: 当数据格式不正确时
            OSError: 当文件操作失败时
        """
        try:
            logger.info(f"Starting NPY to DICOM conversion, output dir: {output_dir}")
            
            # 验证数据格式
            if not self._validate_data_format(npy_data):
                raise ValueError(f"Invalid data format. Expected 3D array, got shape: {npy_data.shape}")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 数据归一化处理
            normalized_data = self._normalize_data(npy_data)

            # 生成DICOM文件列表
            dicom_files = []
            depth = None
            if self.params.data_type == "NPY":
                depth = normalized_data.shape[0]
            elif self.params.data_type == "NII":
                depth = normalized_data.shape[2]
            
            for slice_index in range(depth):
                slice_data = None
                if self.params.data_type == "NPY":
                    slice_data = normalized_data[slice_index, :, :]
                elif self.params.data_type == "NII":
                    slice_data = normalized_data[:, :, slice_index]
                dicom_filename = f"slice_{slice_index:04d}.dcm"
                dicom_path = os.path.join(output_dir, dicom_filename)
                
                # 创建DICOM文件
                self._create_dicom_file(slice_data, slice_index, dicom_path)
                dicom_files.append(dicom_path)
                
            logger.info(f"Successfully converted {len(dicom_files)} slices to DICOM format")
            return dicom_files
            
        except Exception as e:
            logger.error(f"Failed to convert NPY to DICOM: {e}")
            raise
    
    def _validate_data_format(self, data: np.ndarray) -> bool:
        """
        验证数据格式
        
        Args:
            data: 输入数据
            
        Returns:
            bool: 数据格式是否有效
        """
        if not isinstance(data, np.ndarray):
            logger.error("Input data is not a numpy array")
            return False
            
        if len(data.shape) != 3:
            logger.error(f"Expected 3D array, got {len(data.shape)}D array")
            return False
            
        if data.size == 0:
            logger.error("Input data is empty")
            return False
            
        logger.debug(f"Data validation passed: shape={data.shape}, dtype={data.dtype}")
        return True
    
    def _normalize_data(self, data: np.ndarray) -> np.ndarray:
        """
        数据归一化处理
        
        对于CT数据，高密度区域（如牙齿、骨骼）应该显示为白色
        在MONOCHROME2模式下，高像素值=白色，低像素值=黑色
        因此需要将高HU值映射到高像素值
        
        Args:
            data: 输入数据
            
        Returns:
            np.ndarray: 归一化后的数据
        """
        try:
            # 获取数据范围
            data_min = float(np.min(data))
            data_max = float(np.max(data))
            
            logger.debug(f"Original data range: [{data_min}, {data_max}]")

            return data.astype(np.uint16)

        except Exception as e:
            logger.error(f"Data normalization failed: {e}")
            raise ValueError(f"Failed to normalize data: {e}")
    
    def _create_dicom_header(self, slice_index: int) -> Dataset:
        """
        创建DICOM文件头
        
        Args:
            slice_index: 切片索引
            
        Returns:
            Dataset: DICOM数据集
        """
        # 创建基础数据集
        ds = Dataset()
        
        # 患者信息
        ds.PatientName = self.params.patient_name
        ds.PatientID = self.params.patient_id
        ds.PatientBirthDate = ""
        ds.PatientSex = ""
        
        # 研究信息
        ds.StudyInstanceUID = self.study_instance_uid
        ds.StudyDate = datetime.datetime.now().strftime("%Y%m%d")
        ds.StudyTime = datetime.datetime.now().strftime("%H%M%S")
        ds.StudyDescription = self.params.study_description
        ds.StudyID = "1"
        
        # 序列信息
        ds.SeriesInstanceUID = self.series_instance_uid
        ds.SeriesNumber = 1
        ds.SeriesDescription = self.params.series_description
        ds.Modality = "CT"  # 默认使用CT模态
        
        # 图像信息
        ds.SOPInstanceUID = generate_uid()
        ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
        ds.InstanceNumber = slice_index + 1
        ds.SliceLocation = slice_index * self.params.slice_thickness
        
        # 像素数据属性
        ds.SamplesPerPixel = self.params.samples_per_pixel
        ds.PhotometricInterpretation = self.params.photometric_interpretation
        ds.BitsAllocated = self.params.bits_allocated
        ds.BitsStored = self.params.bits_stored
        ds.HighBit = self.params.high_bit
        ds.PixelRepresentation = self.params.pixel_representation
        
        # 空间信息
        ds.PixelSpacing = list(self.params.pixel_spacing)
        ds.SliceThickness = self.params.slice_thickness
        
        return ds
    
    def _create_dicom_file(self, slice_data: np.ndarray, slice_index: int, output_path: str):
        """
        创建单个DICOM文件
        
        Args:
            slice_data: 二维切片数据
            slice_index: 切片索引
            output_path: 输出文件路径
        """
        try:
            # 创建DICOM头
            ds = self._create_dicom_header(slice_index)
            
            # 设置图像尺寸
            ds.Rows = slice_data.shape[0]
            ds.Columns = slice_data.shape[1]
            
            # 设置像素数据
            ds.PixelData = slice_data.tobytes()
            
            # 创建文件数据集
            file_meta = Dataset()
            file_meta.MediaStorageSOPClassUID = ds.SOPClassUID
            file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
            file_meta.ImplementationClassUID = generate_uid()
            file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"  # Implicit VR Little Endian
            
            # 创建文件数据集
            file_ds = FileDataset(output_path, ds, file_meta=file_meta, preamble=b"\0" * 128)
            
            # 保存文件
            file_ds.save_as(output_path, write_like_original=False)
            
            logger.debug(f"Created DICOM file: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to create DICOM file {output_path}: {e}")
            raise OSError(f"Failed to create DICOM file: {e}")