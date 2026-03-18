import numpy as np
import matplotlib.pyplot as plt
import os  # 导入os模块用于检查文件名
from typing import Tuple


def _get_slice_data(volume: np.ndarray, index: int, axis: int) -> np.ndarray:
    """根据轴和索引提取 2D 切片数据。"""
    if axis == 0:
        slicer = (index, slice(None), slice(None))
    elif axis == 1:
        slicer = (slice(None), index, slice(None))
    else:  # axis == 2
        slicer = (slice(None), slice(None), index)
    return volume[slicer]


def display_paired_slices_batched(
        original_file_path: str,
        gt_file_path: str,
        start_index: int,
        end_index: int,
        slices_per_figure: int = 5,  # 每张图显示的切片对数
        axis: int = 0
):
    """
    读取原始图像和 GT 掩码的 3D 数据，并在指定的轴和索引范围内，
    以每张图最多 5 对切片的方式分批显示灰度切片图。
    """
    try:
        # 1. 读取两个 .npy 文件
        original_volume = np.load(original_file_path)
        gt_volume = np.load(gt_file_path)

        print(f"原始图像形状: {original_volume.shape}")
        print(f"GT 掩码形状: {gt_volume.shape}")

        # 2. 检查数据一致性
        if original_volume.shape != gt_volume.shape:
            print("错误: 原始图像和 GT 掩码的 3D 形状不一致，无法对齐显示。")
            return

        if axis not in [0, 1, 2]:
            raise ValueError("axis 参数必须是 0 (D), 1 (H) 或 2 (W)。")

        # 调整索引范围
        max_idx = original_volume.shape[axis]
        start_index = max(0, start_index)
        end_index = min(max_idx, end_index)

        all_indices = list(range(start_index, end_index))
        num_slices_to_display = len(all_indices)

        if num_slices_to_display <= 0:
            print(f"警告: 索引范围 ({start_index} 到 {end_index}) 无效或没有切片可显示。")
            return

        # 3. 计算批次（Figure）数量
        num_figures = (num_slices_to_display + slices_per_figure - 1) // slices_per_figure

        print(f"总共要显示 {num_slices_to_display} 个切片。")
        print(f"每张图显示最多 {slices_per_figure} 对，将生成 {num_figures} 张图。")

        rows = 2  # 固定的 2 行：上为 Original，下为 GT

        # --- 检查是否需要对原始图像计算像素 ---
        # 如果文件名包含 "data.npy"，则视为原始灰度数据，不计算像素点
        # 否则视为Mask数据，需要计算像素点
        is_raw_data = "data.npy" in os.path.basename(original_file_path)

        # 4. 迭代批次（生成多张图）
        for batch_num in range(num_figures):

            # 确定当前批次的切片索引
            batch_start_idx = batch_num * slices_per_figure
            batch_end_idx = min((batch_num + 1) * slices_per_figure, num_slices_to_display)
            current_batch_indices_global = all_indices[batch_start_idx:batch_end_idx]

            cols = len(current_batch_indices_global)  # 当前图的列数

            # 宽度设为 6 * 列数，高度设为 12
            fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 12))

            # 确保 axes 是一个 2D 数组 (2 x cols) 以便统一索引 axes[row, col]
            if cols == 1:
                axes = axes.reshape(rows, cols)

            # 5. 绘制当前批次的切片
            for i, idx in enumerate(current_batch_indices_global):
                # 提取切片数据
                original_slice = _get_slice_data(original_volume, idx, axis)
                gt_slice = _get_slice_data(gt_volume, idx, axis)

                # ==========================================
                # --- 上排：显示原始图像 (Row 0) ---
                # ==========================================
                ax_orig = axes[0, i]
                ax_orig.imshow(original_slice, cmap='gray', origin='lower')
                ax_orig.set_title(f"Orig - Index {idx}", fontsize=14)

                if is_raw_data:
                    # 如果是 data.npy，保持之前的简洁模式，不显示任何标签
                    ax_orig.axis('off')
                else:
                    # 如果不是 data.npy (比如是 gt_alpha.npy)，计算并显示像素点
                    orig_pixel_count = np.count_nonzero(original_slice)

                    orig_text_color = 'red' if orig_pixel_count > 0 else 'black'
                    orig_font_weight = 'bold' if orig_pixel_count > 0 else 'normal'

                    ax_orig.set_xlabel(f"Pixels: {orig_pixel_count}", fontsize=16, color=orig_text_color,
                                       fontweight=orig_font_weight)

                    # 隐藏刻度线但保留xlabel
                    ax_orig.set_xticks([])
                    ax_orig.set_yticks([])

                # ==========================================
                # --- 下排：显示 GT 掩码 (Row 1) ---
                # ==========================================
                ax_gt = axes[1, i]
                ax_gt.imshow(gt_slice, cmap='gray', origin='lower')
                ax_gt.set_title(f"GT - Index {idx}", fontsize=14)

                # 计算 GT 像素点数量
                gt_pixel_count = np.count_nonzero(gt_slice)

                # 如果有像素点，用红色显示，否则用黑色
                gt_text_color = 'red' if gt_pixel_count > 0 else 'black'
                gt_font_weight = 'bold' if gt_pixel_count > 0 else 'normal'

                # 使用 set_xlabel 将文字放在图片正下方
                ax_gt.set_xlabel(f"Pixels: {gt_pixel_count}", fontsize=16, color=gt_text_color,
                                 fontweight=gt_font_weight)

                # 隐藏刻度但保留 Label
                ax_gt.set_xticks([])
                ax_gt.set_yticks([])

            # 6. 设置图的标题和布局
            fig.suptitle(
                f"Slices from Axis {axis} - Batch {batch_num + 1} (Indices {current_batch_indices_global[0]} to {current_batch_indices_global[-1]})",
                fontsize=18)
            plt.tight_layout(rect=[0, 0, 1, 0.96])

        # 7. 显示所有 figure
        plt.show()

    except FileNotFoundError:
        print(f"错误: 找不到文件 {original_file_path} 或 {gt_file_path}。")
    except ValueError as e:
        print(f"运行时错误: {e}")
    except Exception as e:
        print(f"发生意外错误: {e}")


if __name__ == "__main__":
    # ----------------------------------------------------------------------
    # 配置区
    # ----------------------------------------------------------------------

    # 场景 1: 上面是原始灰度数据 (data.npy)，不显示像素点
    # ORIGINAL_FILE = "data.npy"

    # 场景 2: 上面是另一个掩码数据 (gt_alpha.npy)，显示像素点
    ORIGINAL_FILE = "gt_alpha.npy"

    GT_FILE = "r1_s.npy"  # 下面的对比文件 (生成的中心线/点)

    START_INDEX = 60
    END_INDEX = 120
    SLICE_AXIS = 1  # 0=D, 1=H, 2=W

    # 每个 figure 显示 5 对切片
    SLICES_PER_FIGURE = 5

    # 运行
    display_paired_slices_batched(ORIGINAL_FILE, GT_FILE, START_INDEX, END_INDEX, SLICES_PER_FIGURE, SLICE_AXIS)