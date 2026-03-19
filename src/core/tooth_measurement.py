# -*- coding: utf-8 -*-
"""
口腔牙齿分割结果定量测量核心计算模块

支持从 NIfTI 分割掩码（label 1~32 对应 FDI 牙位）自动计算：
  - 牙体总长度、牙冠长度、牙根长度
  - 近远中宽度、颊舌向厚度
  - 牙根倾斜角度
  - 牙齿 3D 体积
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple


# ── FDI 牙位编号（全口 32 颗）────────────────────────────────────────────────
FDI_LABELS = [
    11, 12, 13, 14, 15, 16, 17, 18,  # 右上
    21, 22, 23, 24, 25, 26, 27, 28,  # 左上
    31, 32, 33, 34, 35, 36, 37, 38,  # 左下
    41, 42, 43, 44, 45, 46, 47, 48,  # 右下
]

# label 值 1~32 → FDI 编号映射
LABEL_TO_FDI: Dict[int, int] = {i + 1: fdi for i, fdi in enumerate(FDI_LABELS)}
FDI_TO_LABEL: Dict[int, int] = {v: k for k, v in LABEL_TO_FDI.items()}


@dataclass
class ToothMetrics:
    """单颗牙的测量结果"""
    fdi: int                          # FDI 牙位编号
    label: int                        # 分割掩码中的 label 值

    # 长度指标（mm）
    total_length: float = 0.0         # 牙体总长度
    crown_length: float = 0.0         # 牙冠长度
    root_length: float = 0.0          # 牙根长度

    # 宽度/厚度（mm）
    md_width: float = 0.0             # 近远中宽度（Mesial-Distal）
    bl_thickness: float = 0.0         # 颊舌向厚度（Buccal-Lingual）

    # 角度（°）
    angulation: float = 0.0           # 牙根倾斜角度

    # 体积（mm³）
    volume: float = 0.0               # 牙齿 3D 体积

    # 关键点（像素坐标，用于可视化）
    cusp_point: Optional[Tuple] = None    # 牙尖点
    apex_point: Optional[Tuple] = None   # 根尖点
    cej_point: Optional[Tuple] = None    # 釉牙骨质界（CEJ）

    # 异常标志
    warnings: List[str] = field(default_factory=list)


class ToothMeasurementEngine:
    """
    牙齿测量引擎
    输入：3D 分割掩码 numpy 数组 + 物理间距
    输出：每颗牙的 ToothMetrics 字典
    """

    # 异常阈值（临床参考值）
    WARN_ROOT_LENGTH_MIN = 10.0    # 牙根长度 < 10mm 提示吸收
    WARN_BONE_HEIGHT_MIN = 8.0     # 牙槽骨高度 < 8mm 提示骨量不足
    WARN_ANGULATION_MAX = 15.0     # 倾斜角 > 15° 提示明显倾斜

    def __init__(self, seg_data: np.ndarray, spacing: Tuple[float, float, float]):
        """
        参数
        ----
        seg_data : 3D numpy 数组，shape=(H, W, D)，值为 0（背景）或 1~32（牙位）
        spacing  : (sx, sy, sz) 物理间距，单位 mm
        """
        self.seg_data = seg_data.astype(np.int32)
        self.spacing = spacing  # (sx, sy, sz)
        self._results: Dict[int, ToothMetrics] = {}

    # ══════════════════════════════════════════════════════════════════════════
    # 公开接口
    # ══════════════════════════════════════════════════════════════════════════

    def run(self) -> Dict[int, ToothMetrics]:
        """
        遍历全口 32 颗牙，计算所有指标。
        返回 {fdi: ToothMetrics} 字典，只包含实际存在的牙齿。
        """
        self._results.clear()
        for label_val, fdi in LABEL_TO_FDI.items():
            mask = (self.seg_data == label_val)
            if not np.any(mask):
                continue  # 该牙不存在，跳过
            metrics = self._measure_one_tooth(fdi, label_val, mask)
            self._results[fdi] = metrics
        return self._results

    def get_results(self) -> Dict[int, ToothMetrics]:
        return self._results

    # ══════════════════════════════════════════════════════════════════════════
    # 单颗牙测量
    # ══════════════════════════════════════════════════════════════════════════

    def _measure_one_tooth(self, fdi: int, label: int, mask: np.ndarray) -> ToothMetrics:
        """对单颗牙掩码计算全部指标"""
        m = ToothMetrics(fdi=fdi, label=label)
        sx, sy, sz = self.spacing

        # ── 获取体素坐标 ──────────────────────────────────────────────────────
        coords = np.argwhere(mask)  # shape=(N, 3)，每行 (row, col, slice) = (y, x, z)
        if len(coords) == 0:
            return m

        # ── 3D 体积 ───────────────────────────────────────────────────────────
        voxel_vol = sx * sy * sz
        m.volume = float(len(coords)) * voxel_vol

        # ── 在冠状位（XZ 平面）投影，用于长度/角度测量 ────────────────────────
        # 冠状位：X 轴（左右）= col，Z 轴（上下）= slice
        proj_xz = self._project_to_xz(mask)
        cusp_xz, apex_xz, cej_xz = self._find_landmarks_xz(proj_xz)

        if cusp_xz is not None and apex_xz is not None:
            # 牙体总长度（冠状位）
            m.total_length = self._dist_2d(cusp_xz, apex_xz, sx, sz)
            m.cusp_point = cusp_xz
            m.apex_point = apex_xz

            # 牙根倾斜角度（与垂直轴夹角）
            m.angulation = self._calc_angulation(cusp_xz, apex_xz)

        if cej_xz is not None:
            m.cej_point = cej_xz
            if cusp_xz is not None:
                m.crown_length = self._dist_2d(cusp_xz, cej_xz, sx, sz)
            if apex_xz is not None:
                m.root_length = self._dist_2d(cej_xz, apex_xz, sx, sz)
        else:
            # CEJ 无法自动检测时，用 1/3 估算
            m.crown_length = m.total_length * 0.4
            m.root_length = m.total_length * 0.6

        # ── 在轴位（XY 平面）投影，用于宽度/厚度测量 ─────────────────────────
        # 取牙冠中部切片（Z 方向上 1/4 处）
        z_coords = coords[:, 2]
        z_crown = int(np.percentile(z_coords, 75))  # 牙冠区域（Z 较大端）
        axial_slice = mask[:, :, z_crown]

        if np.any(axial_slice):
            pts = np.argwhere(axial_slice)  # (row=y, col=x)
            # 近远中宽度：X 方向（col）最大跨度
            m.md_width = float(pts[:, 1].max() - pts[:, 1].min()) * sx
            # 颊舌向厚度：Y 方向（row）最大跨度
            m.bl_thickness = float(pts[:, 0].max() - pts[:, 0].min()) * sy

        # ── 异常检测 ──────────────────────────────────────────────────────────
        if m.root_length > 0 and m.root_length < self.WARN_ROOT_LENGTH_MIN:
            m.warnings.append(f"牙根长度 {m.root_length:.1f}mm < {self.WARN_ROOT_LENGTH_MIN}mm，提示牙根可能吸收")
        if abs(m.angulation) > self.WARN_ANGULATION_MAX:
            m.warnings.append(f"倾斜角 {m.angulation:.1f}° > {self.WARN_ANGULATION_MAX}°，提示牙齿倾斜明显")

        return m

    # ══════════════════════════════════════════════════════════════════════════
    # 辅助：投影与关键点检测
    # ══════════════════════════════════════════════════════════════════════════

    def _project_to_xz(self, mask: np.ndarray) -> np.ndarray:
        """
        将 3D 掩码投影到冠状位（XZ 平面）。
        mask shape: (H=row/y, W=col/x, D=slice/z)
        返回 2D 数组 shape: (D, W) = (z, x)，值为该列是否有体素
        """
        return np.any(mask, axis=0).T  # (W, D).T → (D, W) = (z, x)

    def _find_landmarks_xz(self, proj: np.ndarray):
        """
        在冠状位投影上找牙尖、根尖、CEJ。
        proj shape: (nz, nx)，行=Z（上下），列=X（左右）
        返回 (cusp, apex, cej)，坐标为 (x, z) 像素
        """
        pts = np.argwhere(proj)  # (row=z, col=x)
        if len(pts) == 0:
            return None, None, None

        # 牙尖：Z 最小（图像上方）
        cusp_idx = np.argmin(pts[:, 0])
        cusp = (int(pts[cusp_idx, 1]), int(pts[cusp_idx, 0]))  # (x, z)

        # 根尖：Z 最大（图像下方）
        apex_idx = np.argmax(pts[:, 0])
        apex = (int(pts[apex_idx, 1]), int(pts[apex_idx, 0]))  # (x, z)

        # CEJ：沿 Z 轴找轮廓宽度最小处（牙颈部最细）
        cej = self._find_cej_xz(proj, cusp[1], apex[1])

        return cusp, apex, cej

    def _find_cej_xz(self, proj: np.ndarray, z_cusp: int, z_apex: int) -> Optional[Tuple]:
        """
        在冠状位投影上，沿 Z 轴扫描每一行的宽度，
        找到宽度最小的行作为 CEJ 位置。
        只在牙尖到根尖的中间 60% 范围内搜索（避免端点噪声）。
        """
        nz = proj.shape[0]
        z_start = z_cusp + int((z_apex - z_cusp) * 0.2)
        z_end   = z_cusp + int((z_apex - z_cusp) * 0.8)
        z_start = max(0, min(z_start, nz - 1))
        z_end   = max(0, min(z_end, nz - 1))

        min_width = np.inf
        cej_z = (z_start + z_end) // 2  # 默认取中间
        for z in range(z_start, z_end + 1):
            row = proj[z, :]
            xs = np.where(row)[0]
            if len(xs) == 0:
                continue
            w = int(xs[-1]) - int(xs[0])
            if w < min_width:
                min_width = w
                cej_z = z

        # CEJ 的 X 坐标取该行中心
        row = proj[cej_z, :]
        xs = np.where(row)[0]
        if len(xs) == 0:
            return None
        cej_x = int((xs[0] + xs[-1]) / 2)
        return (cej_x, cej_z)

    # ══════════════════════════════════════════════════════════════════════════
    # 辅助：几何计算
    # ══════════════════════════════════════════════════════════════════════════

    def _dist_2d(self, p1: Tuple, p2: Tuple, s1: float, s2: float) -> float:
        """2D 欧式距离，p=(x,z)，s1=X间距，s2=Z间距"""
        dx = (p1[0] - p2[0]) * s1
        dz = (p1[1] - p2[1]) * s2
        return float(np.sqrt(dx ** 2 + dz ** 2))

    def _calc_angulation(self, cusp: Tuple, apex: Tuple) -> float:
        """
        计算牙体长轴与垂直轴（Z 轴）的夹角（°）。
        cusp/apex = (x, z) 像素坐标
        """
        dx = apex[0] - cusp[0]
        dz = apex[1] - cusp[1]
        if dz == 0:
            return 90.0
        angle = np.degrees(np.arctan2(abs(dx), abs(dz)))
        return float(angle)


# ══════════════════════════════════════════════════════════════════════════════
# 便捷函数：从 nibabel 图像对象直接测量
# ══════════════════════════════════════════════════════════════════════════════

def measure_from_nifti(nii_path: str) -> Tuple[Dict[int, ToothMetrics], Tuple]:
    """
    从 NIfTI 文件路径直接计算全口牙测量结果。
    返回 (results_dict, spacing)
    """
    try:
        import nibabel as nib
    except ImportError:
        raise ImportError("需要安装 nibabel：pip install nibabel")

    img = nib.load(nii_path)
    data = np.asarray(img.get_fdata(), dtype=np.int32)
    spacing = tuple(float(s) for s in img.header.get_zooms()[:3])

    engine = ToothMeasurementEngine(data, spacing)
    results = engine.run()
    return results, spacing
