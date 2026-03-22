# -*- coding: utf-8 -*-
"""
文件加载后台线程
在后台线程中执行文件 I/O 操作，避免阻塞主线程
"""

import os
import glob
import numpy as np
import pydicom
import SimpleITK as sitk
from PyQt5.QtCore import QThread, pyqtSignal
from medpy.io import load

from src.utils.logger import get_logger

logger = get_logger(__name__)


class LoadWorker(QThread):
    """
    文件加载工作线程
    支持 DICOM, NII, NPY, STL, IM0 等格式
    """
    
    # 信号定义
    progress = pyqtSignal(int, str)  # (百分比, 当前步骤描述)
    step_done = pyqtSignal(int)      # 某步完成，传步骤索引
    finished = pyqtSignal(object, dict)  # (data_array, meta)
    error = pyqtSignal(str)          # 错误信息
    
    def __init__(self, path, fmt, params=None):
        """
        初始化加载工作线程
        
        Args:
            path: 文件或文件夹路径
            fmt: 文件格式 ('DICOM', 'NII', 'NPY', 'STL', 'IM0')
            params: 额外参数（如 IM0 的尺寸参数）
        """
        super().__init__()
        self.path = path
        self.fmt = fmt
        self.params = params or {}
        self._cancelled = False
    
    def cancel(self):
        """取消加载操作"""
        self._cancelled = True
    
    def run(self):
        """执行加载操作"""
        try:
            if self.fmt == 'DICOM':
                self._load_dicom()
            elif self.fmt in ('NII', 'NRRD', 'MHA'):
                self._load_sitk()
            elif self.fmt == 'NPY':
                self._load_npy()
            elif self.fmt == 'STL':
                self._load_stl()
            elif self.fmt == 'IM0':
                self._load_im0()
        except Exception as e:
            logger.error(f"加载文件失败: {e}", exc_info=True)
            self.error.emit(str(e))
    
    def _load_dicom(self):
        """加载 DICOM 文件夹"""
        steps = ['扫描文件列表', '读取头信息', '排列切片', '加载体素', '构建体积']
        
        # 步骤 0: 扫描文件列表
        self.progress.emit(0, steps[0])
        files = glob.glob(self.path + '/**/*.dcm', recursive=True)
        if self._cancelled:
            return
        self.step_done.emit(0)
        
        # 步骤 1: 读取头信息
        self.progress.emit(20, steps[1])
        reader = sitk.ImageSeriesReader()
        names = reader.GetGDCMSeriesFileNames(self.path)
        if self._cancelled:
            return
        self.step_done.emit(1)
        
        # 步骤 2: 排列切片
        self.progress.emit(40, steps[2])
        reader.SetFileNames(names)
        if self._cancelled:
            return
        self.step_done.emit(2)
        
        # 步骤 3: 加载体素
        self.progress.emit(55, steps[3])
        image = reader.Execute()
        if self._cancelled:
            return
        self.step_done.emit(3)
        
        # 步骤 4: 构建体积
        self.progress.emit(85, steps[4])
        array = sitk.GetArrayFromImage(image)
        array = np.transpose(array, (2, 1, 0))
        self.step_done.emit(4)
        
        # 构建元数据
        meta = {
            '格式': 'DICOM',
            '层数': str(array.shape[2]),
            '尺寸': f'{array.shape[0]} × {array.shape[1]}',
            '体素间距': str(image.GetSpacing()),
            '路径': self.path,
        }
        
        self.progress.emit(100, '完成')
        self.finished.emit(array, meta)
    
    def _load_sitk(self):
        """加载 NII/NRRD/MHA 文件"""
        steps = ['解压文件', '解析文件头', '读取体素', '应用变换']
        
        # 步骤 0: 解压文件
        self.progress.emit(5, steps[0])
        image = sitk.ReadImage(self.path)
        if self._cancelled:
            return
        self.step_done.emit(0)
        
        # 步骤 1: 解析文件头
        self.progress.emit(30, steps[1])
        spacing = image.GetSpacing()
        if self._cancelled:
            return
        self.step_done.emit(1)
        
        # 步骤 2: 读取体素
        self.progress.emit(55, steps[2])
        array = sitk.GetArrayFromImage(image)
        if self._cancelled:
            return
        self.step_done.emit(2)
        
        # 步骤 3: 应用变换
        self.progress.emit(85, steps[3])
        array = np.transpose(array, (2, 1, 0))
        self.step_done.emit(3)
        
        # 构建元数据
        meta = {
            '格式': self.fmt,
            '层数': str(array.shape[2]),
            '尺寸': f'{array.shape[0]} × {array.shape[1]}',
            '体素间距': f'{spacing[0]:.2f} × {spacing[1]:.2f} × {spacing[2]:.2f} mm',
            '路径': self.path,
        }
        
        self.progress.emit(100, '完成')
        self.finished.emit(array, meta)
    
    def _load_npy(self):
        """加载 NPY 文件"""
        # NPY 是单步加载，使用不确定进度条
        self.progress.emit(10, 'np.load() 执行中...')
        
        array = np.load(self.path, allow_pickle=False)
        
        self.progress.emit(100, '完成')
        
        meta = {
            '格式': 'NPY',
            '维度': str(array.shape),
            '数据类型': str(array.dtype),
            '路径': self.path
        }
        
        self.finished.emit(array, meta)
    
    def _load_stl(self):
        """加载 STL 文件"""
        try:
            import trimesh
        except ImportError:
            self.error.emit("需要安装 trimesh 库来加载 STL 文件")
            return
        
        steps = ['读取三角面片', '计算法向量', '构建 VBO', '上传 GPU']
        
        # 步骤 0: 读取三角面片
        self.progress.emit(10, steps[0])
        mesh = trimesh.load(self.path)
        if self._cancelled:
            return
        self.step_done.emit(0)
        
        # 步骤 1: 计算法向量
        self.progress.emit(40, steps[1])
        _ = mesh.vertex_normals
        if self._cancelled:
            return
        self.step_done.emit(1)
        
        # 步骤 2: 构建 VBO
        self.progress.emit(70, steps[2])
        self.step_done.emit(2)
        
        # 步骤 3: 上传 GPU
        self.progress.emit(90, steps[3])
        self.step_done.emit(3)
        
        meta = {
            '格式': 'STL',
            '顶点数': f'{len(mesh.vertices):,}',
            '面数': f'{len(mesh.faces):,}',
            '路径': self.path
        }
        
        self.progress.emit(100, '完成')
        self.finished.emit(mesh, meta)
    
    def _load_im0(self):
        """加载 IM0 文件"""
        # IM0 需要用户指定参数，这里简化处理
        self.progress.emit(10, '读取二进制数据')
        
        # 实际实现需要根据参数读取原始二进制数据
        # 这里仅作示例
        
        self.progress.emit(100, '完成')
        
        meta = {
            '格式': 'IM0',
            '路径': self.path
        }
        
        # 注意：实际数据需要根据参数解析
        self.finished.emit(None, meta)
