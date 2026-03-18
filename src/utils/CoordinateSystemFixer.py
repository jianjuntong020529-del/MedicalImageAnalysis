#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标系统修复工具

用于修复NPY到NII转换中的坐标系统问题，确保叠加图正确显示
"""

import numpy as np
import nibabel as nib
import vtk
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class CoordinateSystemFixer:
    """
    坐标系统修复器
    
    用于处理NPY数据到NII格式转换时的坐标系统对齐问题
    """
    
    def __init__(self):
        """初始化坐标系统修复器"""
        self.dicom_orientation = None
        self.nii_orientation = None
        
    def analyze_dicom_orientation(self, dicom_reader):
        """
        分析DICOM数据的方向信息
        
        Args:
            dicom_reader: VTK DICOM读取器
            
        Returns:
            dict: 包含方向信息的字典
        """
        try:
            if dicom_reader is None:
                logger.warning("DICOM reader is None")
                return None
                
            # 获取DICOM图像数据
            dicom_image = dicom_reader.GetOutput()
            if dicom_image is None:
                logger.warning("DICOM image data is None")
                return None
            
            # 获取基本信息
            dimensions = dicom_image.GetDimensions()
            spacing = dicom_image.GetSpacing()
            origin = dicom_image.GetOrigin()
            
            orientation_info = {
                'dimensions': dimensions,
                'spacing': spacing,
                'origin': origin,
                'bounds': dicom_image.GetBounds()
            }
            
            logger.info(f"DICOM orientation analysis: {orientation_info}")
            self.dicom_orientation = orientation_info
            
            return orientation_info
            
        except Exception as e:
            logger.error(f"Failed to analyze DICOM orientation: {e}")
            return None
    
    def fix_npy_to_nii_conversion(self, npy_data, dicom_orientation_info=None):
        """
        修复NPY到NII转换中的坐标系统问题
        
        Args:
            npy_data (numpy.ndarray): 原始NPY数据
            dicom_orientation_info (dict): DICOM方向信息
            
        Returns:
            tuple: (修复后的数据, 仿射矩阵)
        """
        try:
            logger.info(f"开始修复NPY数据坐标系统，原始形状: {npy_data.shape}")
            
            # 二值化处理
            binary_data = np.where(npy_data > 0, 1, 0).astype(np.uint8)
            
            # 根据用户反馈调整转换策略
            # 问题：XY窗口显示XZ内容，YZ窗口显示XY内容，XZ窗口显示YZ内容
            # 这表明轴的映射关系需要重新调整
            
            # 1. 检查数据形状，确定可能的轴顺序
            shape = binary_data.shape
            logger.info(f"数据形状分析: 轴0={shape[0]}, 轴1={shape[1]}, 轴2={shape[2]}")
            
            # 2. 新的修复策略：根据视图错乱情况调整轴映射
            # 原始NPY: (170, 352, 370) 可能对应 (Z, Y, X)
            # 需要重新映射以匹配正确的视图显示
            
            # 尝试不同的轴重排列来修复视图错乱
            # 策略：(Z, Y, X) -> (Z, X, Y) 然后进行适当的翻转
            fixed_data = np.transpose(binary_data, (0, 2, 1))  # (Z,Y,X) -> (Z,X,Y)
            
            # 根据视图错乱的描述，可能需要进一步的轴交换
            # 如果XY显示XZ内容，说明可能需要交换某些轴
            # 尝试: (Z,X,Y) -> (Y,Z,X) 或其他组合
            fixed_data = np.transpose(fixed_data, (2, 0, 1))  # (Z,X,Y) -> (Y,Z,X)
            
            logger.info(f"应用新修复策略: 转置(0,2,1) -> 转置(2,0,1)")
            logger.info(f"修复后形状: {fixed_data.shape}")
            
            # 3. 创建适当的仿射矩阵
            # 使用标准的医学图像坐标系
            affine = np.array([
                [1.0,  0.0,  0.0,  0.0],   # X轴
                [0.0,  1.0,  0.0,  0.0],   # Y轴  
                [0.0,  0.0,  1.0,  0.0],   # Z轴
                [0.0,  0.0,  0.0,  1.0]
            ])
            
            # 4. 如果有DICOM方向信息，进行进一步调整
            if dicom_orientation_info:
                spacing = dicom_orientation_info.get('spacing', (1.0, 1.0, 1.0))
                # 调整仿射矩阵的体素大小
                affine[0, 0] = spacing[0]
                affine[1, 1] = spacing[1]
                affine[2, 2] = spacing[2]
                
                logger.info(f"根据DICOM信息调整体素大小: {spacing}")
            
            logger.info(f"生成的仿射矩阵:\n{affine}")
            
            return fixed_data, affine
            
        except Exception as e:
            logger.error(f"修复坐标系统失败: {e}")
            # 返回原始数据和单位矩阵作为备选
            return npy_data, np.eye(4)
            
            # 4. 如果有DICOM方向信息，进行进一步调整
            if dicom_orientation_info:
                spacing = dicom_orientation_info.get('spacing', (1.0, 1.0, 1.0))
                # 调整仿射矩阵的体素大小
                affine[0, 0] = -spacing[0]
                affine[1, 1] = -spacing[1]
                affine[2, 2] = spacing[2]
                
                logger.info(f"根据DICOM信息调整体素大小: {spacing}")
            
            logger.info(f"生成的仿射矩阵:\n{affine}")
            
            return fixed_data, affine
            
        except Exception as e:
            logger.error(f"修复坐标系统失败: {e}")
            # 返回原始数据和单位矩阵作为备选
            return npy_data, np.eye(4)
    
    def create_test_versions(self, npy_data, output_dir):
        """
        创建多个测试版本用于验证
        
        Args:
            npy_data (numpy.ndarray): 原始NPY数据
            output_dir (str): 输出目录
            
        Returns:
            list: 创建的文件路径列表
        """
        import os
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # 二值化
            binary_data = np.where(npy_data > 0, 1, 0).astype(np.uint8)
            
            # 定义测试策略
            test_strategies = {
                "原始": (binary_data, np.eye(4)),
                "转置ZXY": (np.transpose(binary_data, (0, 2, 1)), np.eye(4)),
                "翻转Y": (np.flip(binary_data, axis=1), np.eye(4)),
                "翻转Z": (np.flip(binary_data, axis=2), np.eye(4)),
                "转置_翻转Y": (np.flip(np.transpose(binary_data, (0, 2, 1)), axis=2), np.eye(4)),
                "推荐修复": self.fix_npy_to_nii_conversion(npy_data)
            }
            
            created_files = []
            
            for name, (data, affine) in test_strategies.items():
                filename = os.path.join(output_dir, f"test_{name}.nii.gz")
                
                # 创建NII图像
                nii_img = nib.Nifti1Image(data, affine)
                nib.save(nii_img, filename)
                
                created_files.append(filename)
                logger.info(f"创建测试版本: {filename}")
            
            return created_files
            
        except Exception as e:
            logger.error(f"创建测试版本失败: {e}")
            return []
    
    def validate_alignment(self, nii_path, dicom_reader):
        """
        验证NII文件与DICOM数据的对齐情况
        
        Args:
            nii_path (str): NII文件路径
            dicom_reader: DICOM读取器
            
        Returns:
            dict: 验证结果
        """
        try:
            # 加载NII数据
            nii_img = nib.load(nii_path)
            nii_data = nii_img.get_fdata()
            
            # 获取DICOM数据
            dicom_image = dicom_reader.GetOutput()
            dicom_dims = dicom_image.GetDimensions()
            
            # 比较维度
            nii_dims = nii_data.shape
            
            validation_result = {
                'nii_dimensions': nii_dims,
                'dicom_dimensions': dicom_dims,
                'dimensions_match': nii_dims == dicom_dims,
                'nii_nonzero_count': np.count_nonzero(nii_data),
                'nii_value_range': [float(np.min(nii_data)), float(np.max(nii_data))]
            }
            
            logger.info(f"对齐验证结果: {validation_result}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"验证对齐失败: {e}")
            return {'error': str(e)}


def create_fixed_nii_from_npy(npy_path, output_path, dicom_reader=None):
    """
    从NPY文件创建修复后的NII文件
    
    Args:
        npy_path (str): NPY文件路径
        output_path (str): 输出NII文件路径
        dicom_reader: 可选的DICOM读取器用于获取方向信息
        
    Returns:
        str: 创建的NII文件路径
    """
    try:
        # 创建修复器
        fixer = CoordinateSystemFixer()
        
        # 分析DICOM方向（如果提供）
        dicom_info = None
        if dicom_reader:
            dicom_info = fixer.analyze_dicom_orientation(dicom_reader)
        
        # 加载NPY数据
        npy_data = np.load(npy_path)
        logger.info(f"加载NPY数据: {npy_path}, 形状: {npy_data.shape}")
        
        # 修复坐标系统
        fixed_data, affine = fixer.fix_npy_to_nii_conversion(npy_data, dicom_info)
        
        # 创建NII图像
        nii_img = nib.Nifti1Image(fixed_data, affine)
        
        # 保存文件
        nib.save(nii_img, output_path)
        logger.info(f"保存修复后的NII文件: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"创建修复后的NII文件失败: {e}")
        raise


if __name__ == "__main__":
    # 测试代码
    npy_path = "src/utils/gt_alpha.npy"
    output_path = "output/gt_alpha_fixed.nii.gz"
    
    try:
        result_path = create_fixed_nii_from_npy(npy_path, output_path)
        print(f"成功创建修复后的NII文件: {result_path}")
    except Exception as e:
        print(f"创建失败: {e}")