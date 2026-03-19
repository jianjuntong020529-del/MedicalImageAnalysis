# -*- coding: utf-8 -*-
"""
CPR（曲面重建）核心算法

完全参照全景图生成逻辑（generate_Panormaic_MPR）实现：
  1. 三次样条拟合控制点（2D XY 平面）
  2. 等弧长采样曲线，得到 sample_points_num 个采样点
  3. 计算每个采样点的法向量
  4. 沿法向量正负方向各采 arch_width/2 个点，共 normal_samples_num 条法向量线
  5. 对每条法向量线，沿 Z 轴（所有切片）提取体素值 → shape (Z, N_curve)
  6. 对所有法向量线结果取均值 → 最终 CPR 图像 shape (Z, N_curve)
  7. 归一化到 uint8 输出
"""

import numpy as np
from scipy import interpolate


def generate_cpr(volume, control_points, sample_points_num=800, arch_width=80, normal_samples_num=40):
    """
    生成 CPR 图像（与全景图生成逻辑一致）。

    参数
    ----
    volume             : np.ndarray, shape (H, W, D) float32，项目内部格式
    control_points     : np.ndarray, shape (N, 2)，XY 平面控制点（像素坐标）
    sample_points_num  : int，样条曲线上的采样点数，默认 800
    arch_width         : int，法向量方向采样宽度（像素），默认 80
    normal_samples_num : int，法向量方向采样层数（厚度），默认 40

    返回
    ----
    cpr_mean   : np.ndarray, shape (Z, N_curve), dtype uint8，叠加模式（均值）
    cpr_volume : np.ndarray, shape (normal_samples_num, Z, N_curve), dtype uint8，
                 三维 CPR 数据，第0轴为厚度方向（法向量），滑块切换此轴
    """
    if len(control_points) < 2:
        empty = np.zeros((volume.shape[2], 10), dtype=np.uint8)
        return empty, np.zeros((normal_samples_num, volume.shape[2], 10), dtype=np.uint8)

    pts = np.array(control_points, dtype=np.float64)
    x = pts[:, 0]
    y = pts[:, 1]

    # 三次样条拟合（与全景图完全一致）
    k = min(3, len(pts) - 1)
    tck, u = interpolate.splprep([x, y], k=k, s=0)

    # 等弧长采样
    unew = np.linspace(0, 1, sample_points_num)
    out = interpolate.splev(unew, tck)
    sample_points = np.array([[int(out[0][i]), int(out[1][i])] for i in range(len(out[0]))])

    # 计算法向量（与全景图完全一致）
    dx, dy = interpolate.splev(unew, tck, der=1)
    norm = np.sqrt(dx ** 2 + dy ** 2)
    norm[norm < 1e-8] = 1.0
    nx, ny = dy / norm, -dx / norm

    # 构建法向量采样线
    scale = arch_width / 2.0
    lines = []
    for i in range(len(sample_points)):
        x0, y0 = sample_points[i, :]
        nx0, ny0 = nx[i], ny[i]
        x1, y1 = x0 + nx0 * scale, y0 + ny0 * scale
        x2, y2 = x0 - nx0 * scale, y0 - ny0 * scale
        lines.append([(x1, y1), (x2, y2)])

    # 等距采样每条法向量线
    normal_sample_points = []
    for line in lines:
        lx1, ly1 = line[0]
        lx2, ly2 = line[1]
        xs = np.linspace(lx1, lx2, normal_samples_num, endpoint=True)
        ys = np.linspace(ly1, ly2, normal_samples_num, endpoint=True)
        normal_sample_points.append(list(zip(xs, ys)))

    normal_sample_points = np.array(normal_sample_points).reshape((-1, 2))

    # 重新排序：按法向量索引分组（与全景图完全一致）
    sample_points_total = []
    for i in range(normal_samples_num):
        row = []
        for j in range(sample_points.shape[0]):
            row.append(normal_sample_points[i + j * normal_samples_num])
        sample_points_total.append(row)
    sample_points_total = np.array(sample_points_total).astype(np.int32)

    # 确保 volume 为 (Z, H, W)
    vol = _ensure_zhw(volume)
    Z, H, W = vol.shape

    # 沿 Z 轴提取体素值，取均值（与全景图完全一致）
    sysnetic_curve = []
    for i in range(normal_samples_num):
        slice_point = sample_points_total[i, :]  # (N_curve, 2)
        index_max = np.max(slice_point, axis=0)
        if index_max[0] >= W or index_max[1] >= H:
            # 边界处理
            total = []
            for z in range(Z):
                level_pixel = []
                for pt in slice_point:
                    if pt[0] >= W or pt[1] >= H or pt[0] < 0 or pt[1] < 0:
                        level_pixel.append(0)
                    else:
                        level_pixel.append(vol[z, pt[1], pt[0]])
                total.append(level_pixel)
            sysnetic_curve.append(np.array(total))
        else:
            # 快速向量化提取（与全景图 ct_cube[0:Z, slice_point[:,1], slice_point[:,0]] 一致）
            curve2line = vol[:, slice_point[:, 1], slice_point[:, 0]]  # (Z, N_curve)
            sysnetic_curve.append(curve2line)

    sysnetic_curve = np.array(sysnetic_curve)  # (normal_samples_num, Z, N_curve)

    # 沿法向量方向取均值 → (Z, N_curve)，叠加模式用
    cpr_mean = np.mean(sysnetic_curve, axis=0)

    # 归一化：对整个三维数据统一归一化，保证各层亮度一致
    lo, hi = sysnetic_curve.min(), sysnetic_curve.max()
    if hi > lo:
        cpr_volume = ((sysnetic_curve - lo) / (hi - lo) * 255).astype(np.uint8)
        cpr_mean_u8 = ((cpr_mean - cpr_mean.min()) / (cpr_mean.max() - cpr_mean.min() + 1e-8) * 255).astype(np.uint8)
    else:
        cpr_volume = np.zeros_like(sysnetic_curve, dtype=np.uint8)
        cpr_mean_u8 = np.zeros_like(cpr_mean, dtype=np.uint8)

    return cpr_mean_u8, cpr_volume  # (Z, N_curve), (normal_samples_num, Z, N_curve)


def _ensure_zhw(volume):
    """
    将体数据统一转为 (Z, H, W) 格式。
    项目内部 load_image 统一返回 (H, W, D)，直接转置为 (D, H, W) = (Z, H, W)。
    与全景图 ct_cube shape=(Z, H, W) 完全一致。
    """
    if volume.ndim != 3:
        raise ValueError("volume 必须是三维数组")
    # 项目内部格式固定为 (H, W, D)，转置为 (D, H, W) = (Z, H, W)
    return np.transpose(volume, (2, 0, 1))
