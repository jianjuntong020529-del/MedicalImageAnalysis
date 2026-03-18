import numpy as np
import os
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt


def dist_transform_object(mask):
    """
    参考代码中的距离变换函数。
    计算背景(0)到最近前景(1)的欧式距离。
    """
    # 1-mask 反转了前景背景：原来的中心点(1)变成0，背景(0)变成1
    # edt计算的是非零点到最近零点的距离 -> 即计算背景到中心点的距离
    dt = ndimage.distance_transform_edt(1 - mask)
    return dt


def MaxMin_normalization(I):
    """
    参考代码中的归一化函数。
    将数据线性归一化到 [0, 1] 区间。
    """
    Maxval = np.max(I)
    Minval = np.min(I)

    # 防止除以0的错误（如果切片全黑或全白）
    if Maxval == Minval:
        return np.zeros_like(I, dtype=np.float32)

    II = (I - Minval) / (Maxval - Minval)
    return II

def generate_edt_reference_style(input_path, output_dir_name="edp"):
    """
    使用参考代码的方法生成欧式距离图并保存。
    """

    # --- 准备路径 ---
    save_dir = os.path.join("data", output_dir_name)
    os.makedirs(save_dir, exist_ok=True)
    print(f"保存目录: {save_dir}")

    # --- 加载数据 ---
    if not os.path.exists(input_path):
        print(f"错误: 找不到文件 {input_path}")
        return

    mask = np.load(input_path)
    D, H, W = mask.shape
    print(f"原始数据形状: {mask.shape}")
    print("正在计算 2D EDT 并保存...")

    saved_count = 0

    # --- 按照 H 维度 (Axis 1) 遍历 ---
    for h in range(H):
        # 1. 取出当前切片 (D, W)
        # 注意：这里我们把切片视为一张 2D 图像进行处理
        slice_mask = mask[:, h, :]

        if not np.any(slice_mask):
            continue

        # 2. 二值化处理 (参考代码逻辑: > 0.5)
        # 确保输入是 0 和 1
        binary_slice = (slice_mask > 0).astype(np.float32)

        # 3. 计算欧式距离 (调用参考函数)
        # 结果中：中心点位置为0，越远值越大
        dt_slice = dist_transform_object(binary_slice)

        # 4. 归一化 (调用参考函数)
        # 结果范围变为 [0, 1]
        # 注意：这样做的效果是，无论该层管子离边缘多远，最远的地方总是红色(1.0)，
        # 这最大限度地拉伸了每一层的对比度。
        dt_norm = MaxMin_normalization(dt_slice)

        # 5. 保存图片
        save_path = os.path.join(save_dir, f"{h}.png")

        # 使用 jet colormap (蓝-青-黄-红)
        # 0.0 (中心点) -> 蓝色
        # 1.0 (该层最远点) -> 红色
        plt.imsave(save_path, dt_norm)

        saved_count += 1

    print(f"处理完成！共保存 {saved_count} 张图片。")

# def generate_euclidean_distance_map(input_path, output_dir_name="edp"):
#     """
#     读取中心点npy数据，生成欧式距离图(EDT)，并保存切片图像。
#     为了可视化方便，生成的图像中：中心点最亮(白色)，越远越暗(黑色)。
#     """
#
#     # 1. 准备路径
#     save_dir = os.path.join("data", output_dir_name)
#     os.makedirs(save_dir, exist_ok=True)
#     print(f"保存目录已创建: {save_dir}")
#
#     # 2. 加载中心点数据
#     # mask: 1表示中心点，0表示背景
#     centerline_mask = np.load(input_path)
#     D, H, W = centerline_mask.shape
#     print(f"数据加载成功，形状: {centerline_mask.shape}")
#
#     # 3. 计算 3D 欧式距离变换 (EDT)
#     # distance_transform_edt 计算的是"非零元素"到"最近零元素"的距离。
#     # 我们想要计算"背景"到"中心点(1)"的距离。
#     # 所以我们需要反转输入：让中心点变为0，背景变为1。
#     print("正在计算 3D 欧式距离变换 (这可能需要几秒钟)...")
#
#     # logical_not 将 0->True(1), 1->False(0)
#     # sampling参数用于设定体素间距，如果体素是各向同性的(1,1,1)则不需要设置，
#     # 如果是非各向同性(比如层厚比较厚)，可以设置 sampling=[thick, 1, 1]
#     edt_volume = distance_transform_edt(np.logical_not(centerline_mask))
#
#     # 4. 归一化处理 (用于可视化)
#     # 我们希望中心点是白色(255)，最远处是黑色(0)
#     # 公式：Image = 255 * (1 - distance / max_distance)
#     max_dist = np.max(edt_volume)
#     print(f"最大距离为: {max_dist:.2f} 像素")
#
#     if max_dist == 0:
#         print("警告：图像中没有任何中心点，输出将为全黑。")
#         normalized_volume = np.zeros_like(edt_volume)
#     else:
#         # 线性归一化并反转颜色
#         normalized_volume = 255 * (1 - (edt_volume / max_dist))
#         # 转换为 uint8
#         normalized_volume = normalized_volume.astype(np.uint8)
#
#     # 5. 按 H 维度切片并保存图片
#     print("正在保存切片图像...")
#     saved_count = 0
#
#     for h in range(H):
#         # 取出切片 (D, W)
#         slice_img = normalized_volume[:, h, :]
#
#         # 原始的 centerline_mask 切片，用于判断这一层有没有点
#         # 如果您只想保存有点的层周围，可以加上判断。
#         # 这里默认保存所有层，或者您可以恢复之前的 if not np.any... 判断
#
#         # 可选：如果这一层全是黑色（意味着距离非常远或者没有意义），可以选择跳过
#         # if np.mean(slice_img) < 1: continue
#
#         # 保存图片，文件名以索引命名
#         file_name = f"{h}.png"
#         save_path = os.path.join(save_dir, file_name)
#
#         Image.fromarray(slice_img).save(save_path)
#         saved_count += 1
#
#     # 也可以选择把计算好的距离图保存为 .npy 供后续训练使用
#     # output_npy_path = input_path.replace(".npy", "_edt.npy")
#     # np.save(output_npy_path, edt_volume)
#     # print(f"3D 距离数据已保存为: {output_npy_path}")
#
#     print(f"处理完成！共保存 {saved_count} 张距离图切片至 data/{output_dir_name}")


# --- 运行示例 ---
if __name__ == "__main__":
    # 使用上一步生成的修正后的中心点文件
    input_npy_file = './src/utils/r1_s.npy'

    try:
        generate_edt_reference_style(input_npy_file)
    except FileNotFoundError:
        print(f"错误：找不到文件 {input_npy_file}")
    except Exception as e:
        print(f"发生错误: {e}")