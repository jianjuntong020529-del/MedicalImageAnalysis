# -*- coding: utf-8 -*-
# @Time    : 2024/10/15 10:00
#
# @Author  : Jianjun Tong
"""
医学影像文件读写工具函数
支持 DICOM目录、nii/nii.gz、npy 格式的原始影像加载
支持 nii/nii.gz 格式的分割掩码读写
"""
import os
import numpy as np


# ─────────────────────────────────────────────────────────────
# 原始影像加载（多格式）
# ─────────────────────────────────────────────────────────────

def load_image_auto(path):
    """
    自动识别格式并加载原始影像，统一返回 (data, spacing) 元组。

    委托给 image_loader.load_image，支持格式可通过注册表扩展。
    当前内置支持：DICOM目录 / .dcm / .nii / .nii.gz / .npy / .mha / .mhd / .hdr

    Args:
        path: 文件路径或 DICOM 目录路径

    Returns:
        data   : np.ndarray, shape (H, W, D), float32
        spacing: (sx, sy, sz) 像素间距，单位 mm；无法获取时返回 (1.0, 1.0, 1.0)
    """
    from src.utils.image_loader import load_image
    return load_image(path)




# ─────────────────────────────────────────────────────────────
# 分割掩码读写（NIfTI）
# ─────────────────────────────────────────────────────────────

def read_nii_gz(nii_path):
    """
    读取 nii/nii.gz 分割掩码文件。

    Returns:
        data   : np.ndarray int32, shape (H, W, D)
        affine : 4×4 仿射矩阵
        header : NIfTI header 对象
    """
    try:
        import nibabel as nib
        img = nib.load(nii_path)
        data = img.get_fdata().astype(np.int32)
        return data, img.affine, img.header
    except Exception as e:
        raise Exception(f"读取分割掩码失败: {str(e)}")


def save_nii_gz(data, affine, header, save_path):
    """
    保存分割掩码为 nii.gz，保留原始空间参数。

    Args:
        data     : np.ndarray, 分割掩码
        affine   : 仿射矩阵（来自原始 NIfTI 或由 DICOM spacing 构造）
        header   : NIfTI header（可为 None，此时自动创建）
        save_path: 保存路径
    """
    try:
        import nibabel as nib
        img = nib.Nifti1Image(data.astype(np.int32), affine=affine, header=header)
        nib.save(img, save_path)
        return True
    except Exception as e:
        raise Exception(f"保存分割掩码失败: {str(e)}")


def make_affine_from_spacing(spacing):
    """
    根据像素间距构造简单仿射矩阵（原点为 0，无旋转）。
    用于 DICOM / npy 等没有仿射矩阵的格式。

    Args:
        spacing: (sx, sy, sz)

    Returns:
        4×4 np.ndarray
    """
    sx, sy, sz = spacing
    affine = np.diag([sx, sy, sz, 1.0])
    return affine
