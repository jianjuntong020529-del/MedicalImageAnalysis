#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将npy格式文件转换为nii格式文件的脚本
"""

import argparse
import numpy as np
import nibabel as nib
import os


def npy_to_nii(input_path, output_path, transpose_axes=None, flip_axes=None):
    """
    将npy文件转换为nii文件
    
    参数:
        input_path: 输入的npy文件路径
        output_path: 输出的nii文件路径
        transpose_axes: 轴转换顺序，例如 (1, 2, 0) 表示将第0轴移到最后
        flip_axes: 需要翻转的轴，例如 [0, 1] 表示翻转第0轴和第1轴
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    
    # 检查输入文件扩展名
    if not input_path.endswith('.npy'):
        raise ValueError(f"输入文件必须是.npy格式: {input_path}")
    
    # 加载npy文件
    print(f"正在加载文件: {input_path}")
    data = np.load(input_path)
    print(f"原始数据形状: {data.shape}, 数据类型: {data.dtype}")
    
    # 转换轴顺序：将矢状面标注转换为横截面显示
    if transpose_axes is None:
        # 默认转换：假设原始数据是 (sagittal, height, width) 格式
        # 转换为 (height, width, sagittal) 以在横截面正确显示
        transpose_axes = (1, 2, 0)
    
    data_transposed = np.transpose(data, transpose_axes)
    print(f"转换后数据形状: {data_transposed.shape} (轴顺序: {transpose_axes})")
    
    # 翻转指定的轴以修正矢状面和冠状面视图
    if flip_axes is not None and len(flip_axes) > 0:
        for axis in flip_axes:
            data_transposed = np.flip(data_transposed, axis=axis)
        print(f"已翻转轴: {flip_axes}")
    
    # 创建NIfTI图像对象
    # 使用单位矩阵作为仿射变换矩阵（可根据实际需求调整）
    affine = np.eye(4)
    nii_img = nib.Nifti1Image(data_transposed, affine)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")
    
    # 保存为nii文件
    print(f"正在保存文件: {output_path}")
    nib.save(nii_img, output_path)
    print("转换完成!")


def main():
    parser = argparse.ArgumentParser(
        description='将npy格式文件转换为nii格式文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
使用示例:
  python npy_to_nii.py src/utils/gt_alpha.npy output/gt_data.nii.gz
  python npy_to_nii.py src/utils/gt_alpha.npy output/gt_data.nii.gz --transpose 1,2,0
  python npy_to_nii.py src/utils/gt_alpha.npy output/gt_data.nii.gz --transpose 1,2,0 --flip 0
  python npy_to_nii.py src/utils/gt_alpha.npy output/gt_data.nii.gz --transpose 1,2,0 --flip 0,2
  
说明:
  --transpose 参数用于指定轴转换顺序
    默认 1,2,0 表示将矢状面标注转换为横截面显示
    即：(sagittal, height, width) -> (height, width, sagittal)
  
  --flip 参数用于翻转指定的轴，以修正矢状面和冠状面视图
    例如：--flip 0 表示翻转第0轴
          --flip 0,2 表示翻转第0轴和第2轴
        """
    )
    
    parser.add_argument('input', type=str, help='输入的npy文件路径')
    parser.add_argument('output', type=str, help='输出的nii文件路径')
    parser.add_argument('--transpose', type=str, default='1,2,0',
                        help='轴转换顺序，用逗号分隔，默认为"1,2,0"（矢状面转横截面）')
    parser.add_argument('--flip', type=str, default='',
                        help='需要翻转的轴，用逗号分隔，例如"0,1"表示翻转第0轴和第1轴')
    
    args = parser.parse_args()
    
    # 解析转置参数
    transpose_axes = tuple(map(int, args.transpose.split(',')))
    
    # 解析翻转参数
    flip_axes = []
    if args.flip:
        flip_axes = [int(x) for x in args.flip.split(',')]
    
    try:
        npy_to_nii(args.input, args.output, transpose_axes, flip_axes)
    except Exception as e:
        print(f"错误: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
