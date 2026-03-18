import numpy as np
import os
from scipy.ndimage import distance_transform_edt
from PIL import Image
import matplotlib.pyplot as plt


def generate_colored_edt(input_path, output_dir_name="edp", max_vis_dist=40):
    """
    生成彩色的欧式距离图。

    参数:
    input_path: 中心点 .npy 文件路径
    output_dir_name: 保存文件夹名称
    max_vis_dist: 可视化的最大距离阈值（像素）。
                  距离中心点超过这个值的像素将显示为黑色。
                  距离越近越红，距离越远越蓝。
    """

    # 1. 准备路径
    save_dir = os.path.join("data", output_dir_name)
    os.makedirs(save_dir, exist_ok=True)
    print(f"保存目录已创建: {save_dir}")

    # 2. 加载数据
    centerline_mask = np.load(input_path)
    D, H, W = centerline_mask.shape
    print(f"数据加载形状: {centerline_mask.shape}")

    # 3. 计算 3D 欧式距离
    print("正在计算 3D EDT...")
    # logical_not: 将1变0，0变1。因为edt计算的是到最近0点的距离。
    edt_volume = distance_transform_edt(np.logical_not(centerline_mask))

    # 4. 获取颜色映射器 (Colormap)
    # 'jet' 是经典的彩虹色：红(近) -> 黄 -> 绿 -> 蓝(远)
    cmap = plt.get_cmap('jet')

    print(f"正在生成彩色切片 (最大可视距离设为 {max_vis_dist} 像素)...")

    # 5. 遍历 H 维度 (Axis 1)
    saved_count = 0
    for h in range(H):
        # 取出距离图的切片 (Shape: D, W)
        dist_slice = edt_volume[:, h, :]

        # --- 颜色映射逻辑 ---

        # A. 创建一个掩码，标记出超过最大距离的背景区域
        bg_mask = dist_slice > max_vis_dist

        # B. 归一化距离到 [0, 1] 区间
        # 我们希望：距离0(中心) -> 1.0 (对应Jet的红色)
        #        距离max(边缘) -> 0.0 (对应Jet的蓝色)
        # 所以公式是： 1 - (dist / max)
        norm_slice = 1.0 - (dist_slice / max_vis_dist)
        norm_slice = np.clip(norm_slice, 0, 1)  # 确保不越界

        # C. 应用 Colormap
        # cmap(numpy_array) 返回的是 (D, W, 4) 的 RGBA 浮点数组 (0.0 - 1.0)
        rgba_img = cmap(norm_slice)

        # D. 将 RGBA 转为 RGB (丢弃 Alpha 通道)，并转为 0-255
        rgb_img = (rgba_img[:, :, :3] * 255).astype(np.uint8)

        # E. 将超过阈值的背景设为黑色 ([0,0,0])
        # 这一步是为了让图像更干净，否则远处全是深蓝色
        rgb_img[bg_mask] = [0, 0, 0]

        # 6. 保存图片
        # 只有当这一层可视范围内有颜色时才保存（可选）
        # 这里默认全部保存，文件名对应索引
        Image.fromarray(rgb_img).save(os.path.join(save_dir, f"{h}.png"))
        saved_count += 1

    print(f"处理完成！彩色距离图已保存至: {save_dir}")


# --- 运行示例 ---
if __name__ == "__main__":
    input_file = 'r1_s.npy'  # 您的中心点文件

    # max_vis_dist 决定了光晕的大小
    # 30-50 通常适合牙科CT，如果是全身CT可能需要更大
    try:
        generate_colored_edt(input_file, max_vis_dist=40)
    except Exception as e:
        print(f"发生错误: {e}")