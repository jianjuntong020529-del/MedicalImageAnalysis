# -*- coding: utf-8 -*-
"""
医学影像多格式加载器（可扩展策略模式）

使用方式
--------
# 直接调用（自动识别格式）
from src.utils.image_loader import load_image
data, spacing = load_image(path)

# 注册自定义格式
from src.utils.image_loader import ImageLoaderRegistry, BaseImageReader

class MyReader(BaseImageReader):
    @classmethod
    def can_read(cls, path: str) -> bool:
        return path.endswith('.myformat')

    def read(self, path: str):
        ...  # 返回 (np.ndarray H×W×D float32, spacing tuple)

ImageLoaderRegistry.register(MyReader)

支持的内置格式
--------------
  - DICOM 目录（传入文件夹路径）
  - 单个 .dcm 文件（自动扫描同目录所有帧）
  - .nii / .nii.gz
  - .npy
  - .mha / .mhd（MetaImage，需 SimpleITK）
  - .hdr/.img（Analyze，需 nibabel）
"""

import os
import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, List, Type

# 统一返回类型
ImageData = Tuple[np.ndarray, Tuple[float, float, float]]


# ══════════════════════════════════════════════════════════════════════════════
# 基类
# ══════════════════════════════════════════════════════════════════════════════

class BaseImageReader(ABC):
    """所有格式 Reader 的基类，子类只需实现 can_read 和 read。"""

    @classmethod
    @abstractmethod
    def can_read(cls, path):
        """判断该 Reader 是否能处理给定路径（文件或目录）。"""

    @abstractmethod
    def read(self, path):
        """
        读取影像数据。
        返回 (data, spacing)：
          data    : np.ndarray, shape (H, W, D), dtype float32
          spacing : (sx, sy, sz) 体素间距，单位 mm
        """

    # 可选：Reader 的优先级（数字越小越优先）
    priority = 100


# ══════════════════════════════════════════════════════════════════════════════
# 注册表
# ══════════════════════════════════════════════════════════════════════════════

class ImageLoaderRegistry:
    """Reader 注册表，维护所有已注册的格式 Reader。"""

    _readers = []  # type: List[Type[BaseImageReader]]

    @classmethod
    def register(cls, reader_cls):
        """注册一个 Reader 类（重复注册会被忽略）。"""
        if reader_cls not in cls._readers:
            cls._readers.append(reader_cls)
            cls._readers.sort(key=lambda r: r.priority)

    @classmethod
    def find_reader(cls, path):
        """根据路径找到第一个匹配的 Reader 类，找不到则抛出 ValueError。"""
        for reader_cls in cls._readers:
            if reader_cls.can_read(path):
                return reader_cls
        raise ValueError(
            "不支持的文件格式: {}\n已注册格式: {}".format(
                path, [r.__name__ for r in cls._readers]
            )
        )

    @classmethod
    def list_readers(cls):
        return [r.__name__ for r in cls._readers]


# ══════════════════════════════════════════════════════════════════════════════
# 内置 Reader 实现
# ══════════════════════════════════════════════════════════════════════════════

class DicomDirReader(BaseImageReader):
    """DICOM 目录读取器（传入文件夹路径）。"""
    priority = 10

    @classmethod
    def can_read(cls, path):
        if not os.path.isdir(path):
            return False
        import glob
        return bool(glob.glob(os.path.join(path, "*.dcm")))

    def read(self, path):
        return _read_dicom_dir(path)


class DicomFileReader(BaseImageReader):
    """单个 .dcm 文件读取器（自动扫描同目录所有帧）。"""
    priority = 20

    @classmethod
    def can_read(cls, path):
        return os.path.isfile(path) and path.lower().endswith('.dcm')

    def read(self, path):
        return _read_dicom_dir(os.path.dirname(path))


class NiftiReader(BaseImageReader):
    """.nii / .nii.gz 读取器。"""
    priority = 30

    @classmethod
    def can_read(cls, path):
        lower = path.lower()
        return os.path.isfile(path) and (
            lower.endswith('.nii') or lower.endswith('.nii.gz')
        )

    def read(self, path):
        try:
            import nibabel as nib
        except ImportError:
            raise ImportError("需要安装 nibabel：pip install nibabel")
        img = nib.load(path)
        data = img.get_fdata().astype(np.float32)
        zooms = img.header.get_zooms()
        spacing = tuple(float(z) for z in zooms[:3]) if len(zooms) >= 3 else (1.0, 1.0, 1.0)
        return data, spacing


class NpyReader(BaseImageReader):
    """.npy 读取器。"""
    priority = 40

    @classmethod
    def can_read(cls, path):
        return os.path.isfile(path) and path.lower().endswith('.npy')

    def read(self, path):
        data = np.load(path).astype(np.float32)
        if data.ndim == 2:
            data = data[:, :, np.newaxis]
        elif data.ndim != 3:
            raise ValueError("npy 数据维度应为 2 或 3，实际为 {}".format(data.ndim))
        return data, (1.0, 1.0, 1.0)


class MetaImageReader(BaseImageReader):
    """.mha / .mhd 读取器（需要 SimpleITK）。"""
    priority = 50

    @classmethod
    def can_read(cls, path):
        lower = path.lower()
        return os.path.isfile(path) and (lower.endswith('.mha') or lower.endswith('.mhd'))

    def read(self, path):
        try:
            import SimpleITK as sitk
        except ImportError:
            raise ImportError("需要安装 SimpleITK：pip install SimpleITK")
        img = sitk.ReadImage(path)
        data = sitk.GetArrayFromImage(img)  # (D, H, W)
        data = np.transpose(data, (1, 2, 0)).astype(np.float32)  # → (H, W, D)
        spacing = tuple(float(s) for s in img.GetSpacing())
        return data, spacing


class AnalyzeReader(BaseImageReader):
    """.hdr/.img Analyze 格式读取器（需要 nibabel）。"""
    priority = 60

    @classmethod
    def can_read(cls, path):
        lower = path.lower()
        return os.path.isfile(path) and (lower.endswith('.hdr') or lower.endswith('.img'))

    def read(self, path):
        try:
            import nibabel as nib
        except ImportError:
            raise ImportError("需要安装 nibabel：pip install nibabel")
        img = nib.load(path)
        data = img.get_fdata().astype(np.float32)
        zooms = img.header.get_zooms()
        spacing = tuple(float(z) for z in zooms[:3]) if len(zooms) >= 3 else (1.0, 1.0, 1.0)
        return data, spacing


# ── 自动注册所有内置 Reader ────────────────────────────────────────────────────
for _cls in [DicomDirReader, DicomFileReader, NiftiReader, NpyReader, MetaImageReader, AnalyzeReader]:
    ImageLoaderRegistry.register(_cls)


# ══════════════════════════════════════════════════════════════════════════════
# 公开入口
# ══════════════════════════════════════════════════════════════════════════════

def load_image(path):
    """
    自动识别格式并加载影像，统一返回 (data, spacing)。
    path : 文件路径或 DICOM 目录路径
    """
    reader_cls = ImageLoaderRegistry.find_reader(path)
    return reader_cls().read(path)


def _read_dicom_dir(dicom_dir):
    import glob
    try:
        import pydicom
    except ImportError:
        raise ImportError("需要安装 pydicom：pip install pydicom")

    if not dicom_dir or not os.path.isdir(dicom_dir):
        raise FileNotFoundError("DICOM 目录不存在: {}".format(dicom_dir))

    dcm_files = sorted(glob.glob(os.path.join(dicom_dir, "*.dcm")))
    if not dcm_files:
        raise FileNotFoundError("目录中未找到 .dcm 文件: {}".format(dicom_dir))

    slices = []
    for f in dcm_files:
        try:
            slices.append(pydicom.dcmread(f))
        except Exception:
            continue

    if not slices:
        raise ValueError("无法读取任何 DICOM 切片")

    slices.sort(key=lambda s: int(getattr(s, 'InstanceNumber', 0)))

    # 提取像素间距
    try:
        ps = slices[0].PixelSpacing
        st = float(getattr(slices[0], 'SliceThickness', 1.0))
        spacing = (float(ps[1]), float(ps[0]), st)
    except Exception:
        spacing = (1.0, 1.0, 1.0)

    # 堆叠为 (H, W, D)，应用 HU 转换
    arrays = []
    for ds in slices:
        arr = ds.pixel_array.astype(np.float32)
        slope = float(getattr(ds, 'RescaleSlope', 1))
        intercept = float(getattr(ds, 'RescaleIntercept', 0))
        arrays.append(arr * slope + intercept)

    return np.stack(arrays, axis=-1), spacing
