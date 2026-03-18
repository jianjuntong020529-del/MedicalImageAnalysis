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

    支持格式：
      - DICOM 目录（传入文件夹路径）
      - 单个 .dcm 文件（自动扫描同目录所有帧）
      - .nii / .nii.gz
      - .npy

    Args:
        path: 文件路径或 DICOM 目录路径

    Returns:
        data   : np.ndarray, shape (H, W, D), float32
        spacing: (sx, sy, sz) 像素间距，单位 mm；无法获取时返回 (1.0, 1.0, 1.0)
    """
    if os.path.isdir(path):
        return _load_dicom_dir(path)

    ext = _get_ext(path)

    if ext == '.dcm':
        # 单个 dcm 文件 → 取其所在目录加载全部帧
        return _load_dicom_dir(os.path.dirname(path))

    if ext in ('.nii', '.gz'):
        return _load_nifti(path)

    if ext == '.npy':
        return _load_npy(path)

    raise ValueError(f"不支持的文件格式: {path}\n"
                     "支持格式: DICOM目录 / .dcm / .nii / .nii.gz / .npy")


def _get_ext(path):
    """获取文件扩展名（处理 .nii.gz 双扩展名）"""
    lower = path.lower()
    if lower.endswith('.nii.gz'):
        return '.gz'
    return os.path.splitext(lower)[1]


def _load_dicom_dir(dicom_dir):
    """
    用 pydicom 加载 DICOM 目录，按 InstanceNumber 排序后堆叠为 (H, W, D)。
    与项目现有 IM0AndBIMUtils 的读取方式保持一致。
    """
    import glob
    import pydicom

    if not dicom_dir or not os.path.isdir(dicom_dir):
        raise Exception(f"DICOM 目录不存在: {dicom_dir}")

    dcm_files = sorted(glob.glob(os.path.join(dicom_dir, "*.dcm")))
    if not dcm_files:
        raise Exception(f"目录中未找到 .dcm 文件: {dicom_dir}")

    # 读取所有切片，按 InstanceNumber 排序
    slices = []
    for f in dcm_files:
        try:
            ds = pydicom.dcmread(f)
            slices.append(ds)
        except Exception:
            continue

    if not slices:
        raise Exception("无法读取任何 DICOM 切片")

    slices.sort(key=lambda s: int(getattr(s, 'InstanceNumber', 0)))

    # 提取像素间距
    try:
        ps = slices[0].PixelSpacing          # [row_spacing, col_spacing]
        st = float(getattr(slices[0], 'SliceThickness', 1.0))
        spacing = (float(ps[1]), float(ps[0]), st)   # (x, y, z) → (W, H, D)
    except Exception:
        spacing = (1.0, 1.0, 1.0)

    # 堆叠为 (H, W, D)
    arrays = []
    for ds in slices:
        arr = ds.pixel_array.astype(np.float32)
        # 应用 RescaleSlope / RescaleIntercept（HU 值转换）
        slope = float(getattr(ds, 'RescaleSlope', 1))
        intercept = float(getattr(ds, 'RescaleIntercept', 0))
        arr = arr * slope + intercept
        arrays.append(arr)

    data = np.stack(arrays, axis=-1)   # (H, W, D)
    return data, spacing


def _load_nifti(nii_path):
    """加载 NIfTI 文件，返回 (data, spacing)"""
    try:
        import nibabel as nib
        img = nib.load(nii_path)
        data = img.get_fdata().astype(np.float32)
        zooms = img.header.get_zooms()
        spacing = tuple(float(z) for z in zooms[:3]) if len(zooms) >= 3 else (1.0, 1.0, 1.0)
        return data, spacing
    except Exception as e:
        raise Exception(f"加载 NIfTI 文件失败: {str(e)}")


def _load_npy(npy_path):
    """加载 .npy 文件，返回 (data, spacing)"""
    try:
        data = np.load(npy_path).astype(np.float32)
        if data.ndim == 2:
            data = data[:, :, np.newaxis]   # 单切片扩展为 (H, W, 1)
        return data, (1.0, 1.0, 1.0)
    except Exception as e:
        raise Exception(f"加载 npy 文件失败: {str(e)}")


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
