import numpy as np
from scipy.ndimage import label, center_of_mass
import os
from PIL import Image


def npy_to_centerline_with_images(input_path, output_path,min_area_threshold=3):
    """
    1. 按照 H 维度遍历，计算中心点。
    2. 将每层切片的原始Mask和结果Point保存为图片到 data/img 和 data/res 文件夹。
    3. 包含防止重心落在背景区域的修正逻辑。
    """

    # --- 1. 准备文件夹 ---
    img_save_dir = os.path.join("data", "img")
    res_save_dir = os.path.join("data", "res")

    os.makedirs(img_save_dir, exist_ok=True)
    os.makedirs(res_save_dir, exist_ok=True)
    print(f"文件夹已创建:\n -> {img_save_dir}\n -> {res_save_dir}")

    # --- 2. 加载数据 ---
    mask = np.load(input_path)
    D, H, W = mask.shape
    print(f"原始数据形状: (D={D}, H={H}, W={W})")

    # 初始化输出 3D 数组
    centerline_mask = np.zeros_like(mask, dtype=np.uint8)

    points_count = 0

    # --- 3. 遍历 H 维度 ---
    print("开始处理并保存图像...")
    for h in range(H):
        # 提取当前切片 (D, W)
        slice_img = mask[:, h, :]

        # 如果全是背景，跳过（不保存全黑图片，避免垃圾文件过多）
        # 如果您希望连全黑的层也保存，请注释掉下面两行
        if not np.any(slice_img):
            continue

        # 过滤噪点
        if np.sum(slice_img) < min_area_threshold:
            continue

        # --- A. 保存原始 Mask 切片 ---
        # 将 0/1 转为 0/255 以便肉眼观察
        img_visual = (slice_img * 255).astype(np.uint8)
        # Image.fromarray 需要 (Height, Width)，这里对应 (D, W)
        Image.fromarray(img_visual).save(os.path.join(img_save_dir, f"{h}.png"))

        # --- B. 计算中心点 (含修正逻辑) ---
        # 创建一个临时的 2D 结果层，用于保存当前层的点图
        current_res_slice = np.zeros_like(slice_img, dtype=np.uint8)

        labeled_slice, num_features = label(slice_img > 0)

        for i in range(1, num_features + 1):
            component_mask = (labeled_slice == i)


            # 计算重心
            cd_float, cw_float = center_of_mass(component_mask)
            idx_d = int(round(cd_float))
            idx_w = int(round(cw_float))

            # 边界保护
            idx_d = np.clip(idx_d, 0, D - 1)
            idx_w = np.clip(idx_w, 0, W - 1)

            # [重要] 检查点是否落在背景上（空心/弯曲情况），如果是，强制移到最近的像素
            if slice_img[idx_d, idx_w] == 0:
                coords_d, coords_w = np.where(component_mask)
                distances = (coords_d - cd_float) ** 2 + (coords_w - cw_float) ** 2
                min_idx = np.argmin(distances)
                idx_d = coords_d[min_idx]
                idx_w = coords_w[min_idx]

            # 填充 3D 结果数组
            centerline_mask[idx_d, h, idx_w] = 1

            # 填充 2D 临时切片 (用于保存图片)
            current_res_slice[idx_d, idx_w] = 1
            points_count += 1

        # --- C. 保存结果点切片 ---
        res_visual = (current_res_slice * 255).astype(np.uint8)

        # 为了让那个单像素点看得清，可以选择不做处理，或者做一个简单的膨胀(可选)
        # 这里保持原汁原味的一个像素点
        Image.fromarray(res_visual).save(os.path.join(res_save_dir, f"{h}.png"))

    # --- 4. 保存最终的 .npy 文件 ---
    np.save(output_path, centerline_mask)
    print(f"处理完成！")
    print(f"共生成 {points_count} 个中心点。")
    print(f"图片已保存至 ./data/ 目录下。")
    print(f"最终3D数据已保存至: {output_path}")


# --- 运行示例 ---
if __name__ == "__main__":
    input_npy = 'gt_alpha.npy'  # 输入
    output_npy = 'r1_s.npy'  # 输出

    try:
        npy_to_centerline_with_images(input_npy, output_npy)
    except FileNotFoundError:
        print("错误：找不到输入文件，请确认 gt_sparse.npy 是否存在。")
    except Exception as e:
        print(f"发生错误: {e}")