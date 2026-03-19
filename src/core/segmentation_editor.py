# -*- coding: utf-8 -*-
import numpy as np
import cv2


class SegmentationEditor:

    def __init__(self):
        self.orig_data    = None          # (H, W, D) float32
        self.orig_spacing = (1.0, 1.0, 1.0)

        self.seg_data    = None           # (H, W, D) int32，原始方向存储
        self.seg_affine  = None
        self.seg_header  = None

        # 分割掩码显示变换（X/Y/Z 轴翻转 + 旋转）
        # X轴翻转 = 上下翻转(flipud), Y轴翻转 = 左右翻转(fliplr), Z轴翻转 = 沿切片方向翻转(不影响当前切片显示，但影响切片索引)
        self.flip_x  = False   # X轴翻转（行方向，上下）
        self.flip_y  = False   # Y轴翻转（列方向，左右）
        self.flip_z  = False   # Z轴翻转（切片方向，影响切片索引映射）
        self.rotate_k = 0      # np.rot90 k值

        self.current_slice = 0
        self.current_label = 1
        self.brush_size    = 5
        self.brush_shape   = "circle"
        self.alpha         = 0.5

        self.history_stack = []
        self.history_index = -1

        # 标签颜色表（动态扩展）
        self._base_colors = [
            [255, 80,  80 ],
            [80,  255, 80 ],
            [80,  120, 255],
            [255, 220, 50 ],
            [255, 80,  255],
            [80,  255, 255],
            [255, 160, 80 ],
            [160, 80,  255],
        ]

    def get_label_color(self, label):
        idx = (int(label) - 1) % len(self._base_colors)
        return self._base_colors[idx]

    # ──────────────────────────────────────────────
    # 加载
    # ──────────────────────────────────────────────

    def load_original(self, path):
        from src.utils.image_loader import load_image
        self.orig_data, self.orig_spacing = load_image(path)
        self.flip_x = self.flip_y = self.flip_z = False
        self.rotate_k = 0
        print(f"原始影像: {self.orig_data.shape}, spacing={self.orig_spacing}")

    def load_segmentation(self, seg_path):
        if self.orig_data is None:
            raise Exception("请先加载原始影像")
        from src.utils.nii_utils import read_nii_gz
        seg_data, self.seg_affine, self.seg_header = read_nii_gz(seg_path)
        if seg_data.shape != self.orig_data.shape:
            raise Exception(
                f"尺寸不匹配\n原始: {self.orig_data.shape}\n分割: {seg_data.shape}"
            )
        self.seg_data = seg_data
        if self.seg_affine is None:
            from src.utils.nii_utils import make_affine_from_spacing
            self.seg_affine = make_affine_from_spacing(self.orig_spacing)
        self.history_stack = [self.seg_data.copy()]
        self.history_index = 0
        print(f"分割掩码: {self.seg_data.shape}, 标签={np.unique(self.seg_data).tolist()}")

    # ──────────────────────────────────────────────
    # 显示变换（仅作用于分割掩码切片）
    # ──────────────────────────────────────────────

    def _get_seg_slice_index(self):
        """Z轴翻转时映射切片索引"""
        d = self.seg_data.shape[2]
        if self.flip_z:
            return d - 1 - self.current_slice
        return self.current_slice

    def _apply_seg_transform(self, arr2d):
        """X轴翻转(上下) → Y轴翻转(左右) → 旋转"""
        if self.flip_x:
            arr2d = np.flipud(arr2d)
        if self.flip_y:
            arr2d = np.fliplr(arr2d)
        if self.rotate_k:
            arr2d = np.rot90(arr2d, k=self.rotate_k)
        return arr2d

    def display_to_orig_coords(self, xd, yd, disp_h, disp_w):
        """
        将显示坐标系中的点 (xd, yd) 逆变换回原始数组坐标 (x_orig, y_orig)。
        disp_h, disp_w 是变换后显示图像的尺寸（用于旋转时的坐标折算）。
        变换顺序：flip_x → flip_y → rotate_k
        逆变换顺序：逆rotate → 逆flip_y → 逆flip_x
        """
        h_orig = self.orig_data.shape[0]
        w_orig = self.orig_data.shape[1]

        x, y = xd, yd
        h, w = disp_h, disp_w

        # 逆旋转
        if self.rotate_k == 1:
            # rot90 k=1: (x,y) -> (y, h-1-x)，逆: (x,y) -> (w-1-y, x)
            x, y = w - 1 - y, x
            h, w = w, h
        elif self.rotate_k == 2:
            # rot90 k=2: 逆 = 再转两次，即 (x,y) -> (w-1-x, h-1-y)
            x, y = w - 1 - x, h - 1 - y
        elif self.rotate_k == 3:
            # rot90 k=3: (x,y) -> (h-1-y, x)，逆: (x,y) -> (y, h-1-x)
            x, y = y, h - 1 - x
            h, w = w, h

        # 逆 flip_y（左右）
        if self.flip_y:
            x = w_orig - 1 - x

        # 逆 flip_x（上下）
        if self.flip_x:
            y = h_orig - 1 - y

        x = max(0, min(int(x), w_orig - 1))
        y = max(0, min(int(y), h_orig - 1))
        return x, y

    def get_display_slice(self):
        """返回 (orig_slice, seg_slice_transformed)"""
        if self.orig_data is None:
            return None, None
        orig = self.orig_data[:, :, self.current_slice]
        seg = None
        if self.seg_data is not None:
            seg_idx = self._get_seg_slice_index()
            seg = self._apply_seg_transform(
                self.seg_data[:, :, seg_idx].copy()
            )
        return orig, seg

    def fuse_image(self, orig_slice, seg_slice, visible_labels=None, ww=None, wc=None):
        """融合原图和变换后的分割掩码，返回 uint8 RGB。
        visible_labels: None 表示显示全部，否则只显示指定标签集合。
        """
        h_o, w_o = orig_slice.shape
        s = orig_slice.astype(np.float32)
        if ww is not None and wc is not None and ww > 0:
            lo = wc - ww / 2.0
            hi = wc + ww / 2.0
            s = np.clip(s, lo, hi)
        else:
            lo, hi = s.min(), s.max()
        norm = ((s - lo) / (hi - lo + 1e-8) * 255).astype(np.uint8)
        rgb  = cv2.cvtColor(norm, cv2.COLOR_GRAY2RGB)
        if seg_slice is None:
            return rgb
        h_s, w_s = seg_slice.shape
        if (h_s, w_s) != (h_o, w_o):
            seg_slice = cv2.resize(
                seg_slice.astype(np.float32), (w_o, h_o),
                interpolation=cv2.INTER_NEAREST
            ).astype(np.int32)
        seg_color = np.zeros_like(rgb)
        for label in np.unique(seg_slice):
            if label == 0:
                continue
            if visible_labels is not None and label not in visible_labels:
                continue
            seg_color[seg_slice == label] = self.get_label_color(label)
        return cv2.addWeighted(rgb, 1 - self.alpha, seg_color, self.alpha, 0)

    def get_orig_display(self, ww=None, wc=None):
        """返回当前切片的 uint8 灰度图，支持窗位(wc)/窗宽(ww)调整"""
        if self.orig_data is None:
            return None
        s = self.orig_data[:, :, self.current_slice].astype(np.float32)
        if ww is not None and wc is not None and ww > 0:
            lo = wc - ww / 2.0
            hi = wc + ww / 2.0
        else:
            lo, hi = s.min(), s.max()
        s = np.clip(s, lo, hi)
        return ((s - lo) / (hi - lo + 1e-8) * 255).astype(np.uint8)

    def get_data_range(self):
        """返回原始数据的全局 (min, max)，用于初始化窗位窗宽"""
        if self.orig_data is None:
            return 0, 1
        return float(self.orig_data.min()), float(self.orig_data.max())

    def get_seg_labels(self):
        """返回当前分割掩码中的非零标签列表"""
        if self.seg_data is None:
            return []
        return [int(v) for v in np.unique(self.seg_data) if v != 0]

    # ──────────────────────────────────────────────
    # 编辑
    # ──────────────────────────────────────────────

    def edit_seg_mask(self, x_orig, y_orig, mode="draw"):
        if self.seg_data is None:
            return
        mask = self._make_mask(x_orig, y_orig)
        seg_idx = self._get_seg_slice_index()
        if mode == "draw":
            self.seg_data[:, :, seg_idx][mask] = self.current_label
        else:
            self.seg_data[:, :, seg_idx][mask] = 0

    def commit_stroke(self):
        if self.seg_data is None:
            return
        self.history_stack = self.history_stack[:self.history_index + 1]
        self.history_stack.append(self.seg_data.copy())
        self.history_index += 1

    def _make_mask(self, cx, cy):
        seg_idx = self._get_seg_slice_index()
        h, w = self.seg_data[:, :, seg_idx].shape
        xx, yy = np.meshgrid(np.arange(w), np.arange(h))
        if self.brush_shape == "circle":
            return (xx - cx) ** 2 + (yy - cy) ** 2 <= self.brush_size ** 2
        else:
            return (np.abs(xx - cx) <= self.brush_size) & (np.abs(yy - cy) <= self.brush_size)

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.seg_data = self.history_stack[self.history_index].copy()
            return True
        return False

    def redo(self):
        if self.history_index < len(self.history_stack) - 1:
            self.history_index += 1
            self.seg_data = self.history_stack[self.history_index].copy()
            return True
        return False

    # ──────────────────────────────────────────────
    # 保存
    # ──────────────────────────────────────────────

    def save_edited_seg(self, save_path):
        if self.seg_data is None:
            raise Exception("没有可保存的分割数据")
        from src.utils.nii_utils import save_nii_gz
        return save_nii_gz(self.seg_data, self.seg_affine, self.seg_header, save_path)
