# -*- coding: utf-8 -*-
"""
图像增强服务层 — 非破坏性 VTK Pipeline
原始数据不被修改，所有滤镜作用于渲染管线副本
"""
import vtk
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ImageEnhanceService:
    """
    维护一条可配置的 VTK 图像处理管线：
        reader → [median] → [gaussian] → [laplacian sharpen] → output
    每个滤镜可独立开关，最终输出供 viewer.SetInputData() 使用。
    """

    def __init__(self, base_model):
        self._base_model = base_model
        self._enabled = {
            'median':   False,
            'gaussian': False,
            'sharpen':  False,
        }
        self._params = {
            'median_size':   3,      # 核大小（奇数）
            'gaussian_std':  1.0,    # 标准差
            'sharpen_alpha': 0.5,    # 锐化强度 0~1
        }
        self._pipeline_dirty = True
        self._output = None          # 当前管线末端输出（vtkImageData）

    # ── 开关 ──────────────────────────────────────────────────────────────────

    def set_enabled(self, name: str, enabled: bool):
        if self._enabled.get(name) != enabled:
            self._enabled[name] = enabled
            self._pipeline_dirty = True

    def set_param(self, name: str, value):
        if self._params.get(name) != value:
            self._params[name] = value
            self._pipeline_dirty = True

    # ── 执行管线 ──────────────────────────────────────────────────────────────

    def get_output(self):
        """返回增强后的 vtkImageData；若无增强则返回原始数据。"""
        if not any(self._enabled.values()):
            return self._base_model.imageReader.GetOutput()
        if self._pipeline_dirty:
            self._rebuild()
        return self._output

    def _rebuild(self):
        src = self._base_model.imageReader.GetOutputPort()

        # ── 去噪：中值滤波 ────────────────────────────────────────────────
        if self._enabled['median']:
            sz = int(self._params['median_size'])
            sz = sz if sz % 2 == 1 else sz + 1   # 保证奇数
            f = vtk.vtkImageMedian3D()
            f.SetInputConnection(src)
            f.SetKernelSize(sz, sz, 1)            # 2D 切片内滤波，Z=1 避免跨层
            f.Update()
            src = f.GetOutputPort()
            logger.debug(f"Median filter applied, kernel={sz}")

        # ── 平滑：高斯滤波 ────────────────────────────────────────────────
        if self._enabled['gaussian']:
            std = float(self._params['gaussian_std'])
            f = vtk.vtkImageGaussianSmooth()
            f.SetInputConnection(src)
            f.SetStandardDeviations(std, std, 0)  # Z=0 不跨层
            f.SetRadiusFactors(2, 2, 0)
            f.Update()
            src = f.GetOutputPort()
            logger.debug(f"Gaussian smooth applied, std={std}")

        # ── 锐化：拉普拉斯增强 ────────────────────────────────────────────
        if self._enabled['sharpen']:
            alpha = float(self._params['sharpen_alpha'])
            # 拉普拉斯边缘
            lap = vtk.vtkImageLaplacian()
            lap.SetInputConnection(src)
            lap.SetDimensionality(2)
            lap.Update()
            # 原图 + alpha * 拉普拉斯
            wsum = vtk.vtkImageWeightedSum()
            wsum.AddInputConnection(src)
            wsum.AddInputConnection(lap.GetOutputPort())
            wsum.SetWeight(0, 1.0)
            wsum.SetWeight(1, alpha)
            wsum.Update()
            src = wsum.GetOutputPort()
            logger.debug(f"Laplacian sharpen applied, alpha={alpha}")

        # 取最终输出
        tmp = vtk.vtkImageData()
        tmp.DeepCopy(src.GetProducer().GetOutput())
        self._output = tmp
        self._pipeline_dirty = False
        logger.info("Image enhance pipeline rebuilt")
