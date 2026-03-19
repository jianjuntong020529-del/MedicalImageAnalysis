# -*- coding: utf-8 -*-
"""
多切片平铺视图面板（嵌入主界面）

优化要点：
  1. 离屏渲染结果缓存（LRU），避免重复渲染同一切片
  2. 表格布局（QGridLayout），行列数可配置
  3. 去掉标题栏，工具栏紧凑
  4. 滑块 + 鼠标滚轮双重控制中心切片
  5. 边界保护：到达首/末切片时禁止继续滑动
  6. 视图方向选择（轴/矢/冠）
  7. 布局选择（1行N列 / 2行N列 / 3行N列）
"""

import vtk
import numpy as np
from collections import OrderedDict
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, pyqtSignal


# ── 离屏渲染缓存（最多缓存 200 张，key = (orientation, slice_index, ww, wl, size)）
_RENDER_CACHE: OrderedDict = OrderedDict()
_CACHE_MAX = 200


def _cache_key(orientation, idx, ww, wl, size):
    return (orientation, idx, int(ww), int(wl), size)


def _get_cached(key):
    if key in _RENDER_CACHE:
        _RENDER_CACHE.move_to_end(key)
        return _RENDER_CACHE[key]
    return None


def _put_cache(key, pixmap):
    _RENDER_CACHE[key] = pixmap
    _RENDER_CACHE.move_to_end(key)
    while len(_RENDER_CACHE) > _CACHE_MAX:
        _RENDER_CACHE.popitem(last=False)


def clear_render_cache():
    """数据重新加载时清空缓存"""
    _RENDER_CACHE.clear()


# ── 离屏渲染核心函数（模块级，避免重复创建 VTK 对象）─────────────────────────
def render_slice_offscreen(image_data, orientation: str, slice_index: int,
                           ww: float, wl: float, size: int = 200) -> QtGui.QPixmap:
    """
    离屏渲染单张切片，返回 QPixmap。
    先查缓存，命中则直接返回，否则渲染后存入缓存。
    使用 vtkImageExtractComponents + vtkImageShiftScale 纯 CPU 路径，
    完全不创建任何可见窗口，避免弹出 VTK 渲染窗口。
    """
    key = _cache_key(orientation, slice_index, ww, wl, size)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    # ── 提取指定切片的 2D 数据 ────────────────────────────────────────────────
    dims = image_data.GetDimensions()  # (nx, ny, nz)

    # 使用 vtkImageReslice 提取切片，输出始终为标准 XY 平面（W×H×1）
    reslice = vtk.vtkImageReslice()
    reslice.SetInputData(image_data)
    reslice.SetOutputDimensionality(2)
    reslice.SetInterpolationModeToLinear()

    spacing = image_data.GetSpacing()
    origin  = image_data.GetOrigin()

    if orientation == "XY":
        # 轴状面：Z=slice_index 层
        # vtkImageViewer2 XY 默认：X→右，Y→上，与四视图一致，无需翻转
        z = max(0, min(dims[2] - 1, slice_index))
        reslice.SetResliceAxesDirectionCosines(
            1, 0, 0,   # 输出 X → 数据 X（右）
            0, -1, 0,   # 输出 Y → 数据 Y（上）
            0, 0, 1    # 法线 → 数据 Z
        )
        reslice.SetResliceAxesOrigin(
            origin[0], origin[1],
            origin[2] + z * spacing[2]
        )
        reslice.SetOutputSpacing(spacing[0], spacing[1], 1)
        reslice.SetOutputExtent(0, dims[0]-1, 0, dims[1]-1, 0, 0)

    elif orientation == "YZ":
        # 矢状面：X=slice_index 层
        # QtOrthoViewerWidget 里矢状面没有额外 transform，
        # vtkImageViewer2 YZ 默认：Y→右，Z→上
        # 对应：输出 X → 数据 Y，输出 Y → 数据 Z
        x = max(0, min(dims[0] - 1, slice_index))
        reslice.SetResliceAxesDirectionCosines(
            0, 1, 0,   # 输出 X → 数据 Y（右）
            0, 0, 1,   # 输出 Y → 数据 Z（上）
            1, 0, 0    # 法线 → 数据 X
        )
        reslice.SetResliceAxesOrigin(
            origin[0] + x * spacing[0],
            origin[1],
            origin[2]
        )
        reslice.SetOutputSpacing(spacing[1], spacing[2], 1)
        reslice.SetOutputExtent(0, dims[1]-1, 0, dims[2]-1, 0, 0)

    else:  # XZ 冠状面
        # 冠状面：Y=slice_index 层
        y = max(0, min(dims[1] - 1, slice_index))
        reslice.SetResliceAxesDirectionCosines(
            1,  0,  0,   # 输出 X → 数据 X
            0,  0, 1,   # 输出 Y → 数据 Z
            0,  1,  0    # 法线 → 数据 Y
        )
        reslice.SetResliceAxesOrigin(
            origin[0],
            origin[1] + y * spacing[1],
            origin[2] + (dims[2] - 1) * spacing[2]
        )
        reslice.SetOutputSpacing(spacing[0], spacing[2], 1)
        reslice.SetOutputExtent(0, dims[0]-1, 0, dims[2]-1, 0, 0)

    reslice.Update()
    slice_data = reslice.GetOutput()

    # ── 窗位窗宽映射到 0-255 ──────────────────────────────────────────────────
    shift_scale = vtk.vtkImageShiftScale()
    shift_scale.SetInputData(slice_data)
    half = ww / 2.0
    lo = wl - half
    scale = 255.0 / ww if ww > 0 else 1.0
    shift_scale.SetShift(-lo)
    shift_scale.SetScale(scale)
    shift_scale.SetOutputScalarTypeToUnsignedChar()
    shift_scale.ClampOverflowOn()
    shift_scale.Update()
    mapped = shift_scale.GetOutput()

    # ── 转为 numpy，再转 QPixmap ──────────────────────────────────────────────
    out_dims = mapped.GetDimensions()  # (W, H, 1)
    arr_flat = np.frombuffer(mapped.GetPointData().GetScalars(), dtype=np.uint8)

    # vtkImageReslice 输出已按方向余弦排列，直接 reshape 为 (H, W)
    W, H = out_dims[0], out_dims[1]
    arr = arr_flat.reshape(H, W)
    arr = arr.copy()

    # 灰度 → RGB
    arr_rgb = np.stack([arr, arr, arr], axis=2)
    h, w = arr_rgb.shape[:2]

    qimg = QtGui.QImage(arr_rgb.data, w, h, w * 3, QtGui.QImage.Format_RGB888)
    pixmap = QtGui.QPixmap.fromImage(qimg.copy())

    # 缩放到目标尺寸
    if w != size or h != size:
        pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    del reslice, shift_scale, slice_data, mapped

    _put_cache(key, pixmap)
    return pixmap


# ── 单张切片卡片 ──────────────────────────────────────────────────────────────
class SliceCard(QtWidgets.QFrame):
    """单张切片卡片，显示图像 + 切片号，点击跳转"""
    slice_clicked = pyqtSignal(int)
    zoom_requested = pyqtSignal(object)  # 传递自身，供父级放大

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slice_index = 0
        self._setup()

    def _setup(self):
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self._style_normal())
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(2)

        # 图像区（用 QFrame 包裹，方便叠加放大按钮）
        img_container = QtWidgets.QFrame(self)
        img_container.setStyleSheet("background:transparent;border:none;")
        img_lay = QtWidgets.QVBoxLayout(img_container)
        img_lay.setContentsMargins(0, 0, 0, 0)

        self.img = QtWidgets.QLabel()
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setStyleSheet("background:#111;border-radius:2px;")
        img_lay.addWidget(self.img)

        # 放大按钮（绝对定位在左上角）
        self.btn_zoom = QtWidgets.QPushButton("⛶", img_container)
        self.btn_zoom.setFixedSize(20, 20)
        self.btn_zoom.setStyleSheet(
            "QPushButton{background:rgba(0,0,0,140);color:#aaa;border:none;"
            "border-radius:3px;font-size:11px;}"
            "QPushButton:hover{background:rgba(91,200,245,180);color:#fff;}"
        )
        self.btn_zoom.move(4, 4)
        self.btn_zoom.raise_()
        self.btn_zoom.clicked.connect(lambda: self.zoom_requested.emit(self))

        lay.addWidget(img_container, 1)

        self.lbl = QtWidgets.QLabel()
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet("color:#888;font-size:10px;background:transparent;")
        self.lbl.setFixedHeight(16)
        lay.addWidget(self.lbl)

    def update_content(self, pixmap: QtGui.QPixmap, idx: int, is_center: bool):
        """更新图像和标签"""
        self._slice_index = idx
        iw = self.img.width() or 160
        ih = self.img.height() or 160
        self.img.setPixmap(
            pixmap.scaled(iw, ih, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.lbl.setText(f"#{idx}")
        self.setStyleSheet(self._style_center() if is_center else self._style_normal())

    def set_out_of_range(self, idx: int):
        """超出范围时显示占位"""
        self._slice_index = idx
        self.img.clear()
        self.img.setText("—")
        self.img.setStyleSheet("background:#111;border-radius:2px;color:#333;font-size:18px;")
        self.lbl.setText(f"#{idx}")
        self.setStyleSheet(self._style_normal())

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.slice_clicked.emit(self._slice_index)
        super().mousePressEvent(e)

    def _style_normal(self):
        return ("QFrame{background:#1c1c1c;border:1px solid #3a3a3a;border-radius:4px;}"
                "QFrame:hover{border:1px solid #5bc8f5;}")

    def _style_center(self):
        return "QFrame{background:#162840;border:2px solid #5bc8f5;border-radius:4px;}"


# ── 主面板 ────────────────────────────────────────────────────────────────────
class MultiSliceViewWidget(QtWidgets.QWidget):
    """
    多切片平铺视图面板。
    jump_to_slice(orientation, slice_index) 信号供 Controller 同步主界面滑块。
    """
    jump_to_slice = pyqtSignal(str, int)

    # 布局预设：(行数, 列数描述)
    LAYOUT_ROWS_PRESETS = [
        (1, "1 行"),
        (2, "2 行"),
        (3, "3 行"),
        (4, "4 行"),
    ]

    LAYOUT_COLS_PRESETS = [
        (1, "1 列"),
        (2, "2 列"),
        (3, "3 列"),
        (4, "4 列"),
    ]

    def __init__(self, base_model, viewer_model, half_count: int = 2, parent=None):
        super().__init__(parent)
        self._base_model = base_model
        self._viewer_model = viewer_model
        self._orientation = "XY"   # 当前方向
        self._rows = 1             # 当前行数
        self._cols = 1             # 当前列数
        self._center = 0           # 当前中心切片索引
        self._min_s = 0
        self._max_s = 0
        self._cards: list = []
        self._card_size = 180      # 卡片图像区尺寸（正方形）
        self._zoomed_card = None   # 当前放大的卡片（None 表示未放大）

        self.setStyleSheet("background:#222;")
        self._init_ui()

    # ══════════════════════════════════════════════════════════════════════════
    # UI 初始化
    # ══════════════════════════════════════════════════════════════════════════

    def _init_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(6)

        # ── 工具栏（浅色背景，字体稍大）──────────────────────────────────────
        toolbar_widget = QtWidgets.QWidget()
        toolbar_widget.setStyleSheet(
            "background:#3a3a3a;border-radius:4px;padding:2px;"
        )
        bar = QtWidgets.QHBoxLayout(toolbar_widget)
        bar.setContentsMargins(8, 4, 8, 4)
        bar.setSpacing(8)

        # 视图方向
        bar.addWidget(self._mk_lbl("视图："))
        self.combo_dir = QtWidgets.QComboBox()
        self.combo_dir.addItems(["轴状面", "矢状面", "冠状面"])
        self.combo_dir.setFixedWidth(90)
        self.combo_dir.setStyleSheet(self._combo_style())
        self.combo_dir.currentIndexChanged.connect(self._on_dir_changed)
        bar.addWidget(self.combo_dir)

        # 布局行数
        bar.addWidget(self._mk_lbl("布局："))
        self.combo_rows_layout = QtWidgets.QComboBox()
        for rows, desc in self.LAYOUT_ROWS_PRESETS:
            self.combo_rows_layout.addItem(desc, rows)
        self.combo_rows_layout.setFixedWidth(65)
        self.combo_rows_layout.setStyleSheet(self._combo_style())
        self.combo_rows_layout.currentIndexChanged.connect(self._on_layout_changed)
        bar.addWidget(self.combo_rows_layout)

        # 每行列数
        bar.addWidget(self._mk_lbl("列数："))
        self.combo_cols_layout = QtWidgets.QComboBox()
        for rows, desc in self.LAYOUT_COLS_PRESETS:
            self.combo_cols_layout.addItem(desc, rows)
        self.combo_cols_layout.setFixedWidth(65)
        self.combo_cols_layout.setStyleSheet(self._combo_style())
        self.combo_cols_layout.currentIndexChanged.connect(self._on_cols_changed)
        bar.addWidget(self.combo_cols_layout)

        bar.addStretch()

        # 当前切片信息
        self.lbl_info = QtWidgets.QLabel("切片: 0 / 0")
        self.lbl_info.setStyleSheet("color:#ddd;font-size:13px;")
        bar.addWidget(self.lbl_info)

        root.addWidget(toolbar_widget)

        # ── 卡片网格区域 ──────────────────────────────────────────────────────
        self.grid_widget = QtWidgets.QWidget()
        self.grid_widget.setStyleSheet("background:#222;")
        self.grid_layout = QtWidgets.QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.grid_widget, 1)

        # ── 底部：滑块控制中心切片 ────────────────────────────────────────────
        slider_bar = QtWidgets.QHBoxLayout()
        slider_bar.setSpacing(6)

        # 向前按钮
        self.btn_prev = QtWidgets.QPushButton("◀")
        self.btn_prev.setFixedSize(28, 22)
        self.btn_prev.setStyleSheet(self._nav_btn_style())
        self.btn_prev.clicked.connect(self._go_prev)
        slider_bar.addWidget(self.btn_prev)

        # 切片滑块
        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider.setStyleSheet(self._slider_style())
        self.slider.valueChanged.connect(self._on_slider_changed)
        slider_bar.addWidget(self.slider, 1)

        # 向后按钮
        self.btn_next = QtWidgets.QPushButton("▶")
        self.btn_next.setFixedSize(28, 22)
        self.btn_next.setStyleSheet(self._nav_btn_style())
        self.btn_next.clicked.connect(self._go_next)
        slider_bar.addWidget(self.btn_next)

        root.addLayout(slider_bar)

        # 初始化卡片
        self._rebuild_grid()

    # ══════════════════════════════════════════════════════════════════════════
    # 卡片网格重建
    # ══════════════════════════════════════════════════════════════════════════

    def _rebuild_grid(self):
        """根据 _rows / _cols 重建卡片网格，自适应面板宽高"""
        # 退出放大模式
        self._zoomed_card = None

        # 清空旧卡片
        for card in self._cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        total = self._rows * self._cols

        # ── 计算卡片尺寸，同时受宽度和高度约束 ──────────────────────────────
        # 工具栏约 36px，底部滑块约 36px，间距约 20px
        TOOLBAR_H = 36 + 36 + 20
        GAP = 4  # grid spacing

        panel_w = max(self.width() - 20, self._cols * 80)
        panel_h = max(self.height() - TOOLBAR_H, self._rows * 80)

        # 按宽度计算
        card_w_by_w = max(80, (panel_w - GAP * (self._cols - 1)) // self._cols)
        # 按高度计算（卡片高 = 宽 + 20，所以先算可用高度对应的宽）
        card_w_by_h = max(80, (panel_h - GAP * (self._rows - 1)) // self._rows - 20)

        # 取两者较小值，保证不超出任何方向
        card_w = min(card_w_by_w, card_w_by_h)
        card_h = card_w + 20  # 图像区 + 标签行

        for i in range(total):
            row = i // self._cols
            col = i % self._cols
            card = SliceCard(self.grid_widget)
            card.setFixedSize(card_w, card_h)
            card.img.setFixedSize(card_w - 6, card_h - 22)
            card.slice_clicked.connect(self._on_card_clicked)
            card.zoom_requested.connect(self._on_zoom_requested)
            self.grid_layout.addWidget(card, row, col)
            self._cards.append(card)

    # ══════════════════════════════════════════════════════════════════════════
    # 公开方法
    # ══════════════════════════════════════════════════════════════════════════

    def refresh(self):
        """刷新所有卡片图像（使用缓存加速）"""
        image_data = self._base_model.imageReader.GetOutput()
        if image_data is None or image_data.GetNumberOfPoints() == 0:
            self.lbl_info.setText("无数据")
            return

        # 获取切片范围
        self._update_slice_range(image_data)

        # 同步滑块范围（阻断信号避免递归）
        self.slider.blockSignals(True)
        self.slider.setRange(self._min_s, self._max_s)
        self.slider.setValue(self._center)
        self.slider.blockSignals(False)

        # 更新导航按钮状态
        self.btn_prev.setEnabled(self._center > self._min_s)
        self.btn_next.setEnabled(self._center < self._max_s)

        # 放大模式：只刷新放大的卡片
        if self._zoomed_card is not None:
            self._refresh_zoomed(self._zoomed_card)
            self.lbl_info.setText(
                f"切片: {self._center} / {self._max_s}  [{self._min_s}–{self._max_s}]"
            )
            return

        ww, wl = self._get_window_params()
        total = self._rows * self._cols

        # 以 center 为起点，从左到右顺序排列（不再以 center 为中间）
        # 第一张 = center - (total//2)，保证 center 在中间列
        half = total // 2
        start = self._center - half

        for i, card in enumerate(self._cards):
            idx = start + i
            is_center = (idx == self._center)

            if idx < self._min_s or idx > self._max_s:
                card.set_out_of_range(idx)
                continue

            pixmap = render_slice_offscreen(
                image_data, self._orientation, idx, ww, wl,
                size=max(card.img.width(), 128)
            )
            card.update_content(pixmap, idx, is_center)

        self.lbl_info.setText(
            f"切片: {self._center} / {self._max_s}  [{self._min_s}–{self._max_s}]"
        )

    def set_center_slice(self, idx: int):
        """外部设置中心切片（Controller 调用）"""
        self._center = max(self._min_s, min(self._max_s, idx))
        self.refresh()

    # ══════════════════════════════════════════════════════════════════════════
    # 放大 / 还原
    # ══════════════════════════════════════════════════════════════════════════

    def _on_zoom_requested(self, card: 'SliceCard'):
        """点击放大按钮：放大该卡片 / 还原布局"""
        if self._zoomed_card is card:
            # 再次点击同一张 → 还原
            self._exit_zoom()
        else:
            self._enter_zoom(card)

    def _enter_zoom(self, card: 'SliceCard'):
        """进入放大模式：隐藏其他卡片，将目标卡片撑满网格区"""
        self._zoomed_card = card
        for c in self._cards:
            if c is not card:
                c.hide()
        # 撑满整个 grid_widget
        card.setMaximumSize(16777215, 16777215)  # 解除固定尺寸限制
        card.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        card.img.setMaximumSize(16777215, 16777215)
        card.img.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        # 更新放大按钮图标为"还原"
        card.btn_zoom.setText("✕")
        card.btn_zoom.setToolTip("还原布局")
        # 延迟一帧，等 Qt 完成布局计算后再渲染，确保图像尺寸正确
        QtCore.QTimer.singleShot(0, lambda: self._refresh_zoomed(card))

    def _exit_zoom(self):
        """退出放大模式，恢复所有卡片"""
        if self._zoomed_card is None:
            return
        card = self._zoomed_card
        self._zoomed_card = None
        card.btn_zoom.setText("⛶")
        card.btn_zoom.setToolTip("")
        # 恢复固定尺寸（与 _rebuild_grid 保持一致的计算逻辑）
        TOOLBAR_H = 36 + 36 + 20
        GAP = 4
        panel_w = max(self.width() - 20, self._cols * 80)
        panel_h = max(self.height() - TOOLBAR_H, self._rows * 80)
        card_w_by_w = max(80, (panel_w - GAP * (self._cols - 1)) // self._cols)
        card_w_by_h = max(80, (panel_h - GAP * (self._rows - 1)) // self._rows - 20)
        card_w = min(card_w_by_w, card_w_by_h)
        card_h = card_w + 20
        for c in self._cards:
            c.setFixedSize(card_w, card_h)
            c.img.setFixedSize(card_w - 6, card_h - 22)
            c.show()
        self.refresh()

    def _refresh_zoomed(self, card: 'SliceCard'):
        """放大模式下刷新单张卡片图像"""
        image_data = self._base_model.imageReader.GetOutput()
        if image_data is None or image_data.GetNumberOfPoints() == 0:
            return
        ww, wl = self._get_window_params()
        # 用面板尺寸作为渲染尺寸
        sz = min(self.grid_widget.width(), self.grid_widget.height()) or 400
        pixmap = render_slice_offscreen(
            image_data, self._orientation, card._slice_index, ww, wl, size=sz
        )
        card.img.setPixmap(
            pixmap.scaled(
                card.img.width() or sz,
                card.img.height() or sz,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 事件处理
    # ══════════════════════════════════════════════════════════════════════════

    def _on_dir_changed(self, index: int):
        self._orientation = ["XY", "YZ", "XZ"][index]
        # 方向变化时清空缓存（不同方向的切片不能复用）
        clear_render_cache()
        self._center = 0
        self.refresh()

    def _on_layout_changed(self, index: int):
        self._rows = self.combo_rows_layout.itemData(index)
        self._rebuild_grid()
        self.refresh()

    def _on_cols_changed(self, index: int):
        self._cols = self.combo_cols_layout.itemData(index)
        self._rebuild_grid()
        self.refresh()

    def _on_slider_changed(self, value: int):
        """滑块拖动，更新中心切片"""
        self._center = value
        self.refresh()
        # 同步主界面
        self.jump_to_slice.emit(self._orientation, self._center)

    def _on_card_clicked(self, idx: int):
        """点击卡片，跳转到该切片"""
        self._center = idx
        self.slider.blockSignals(True)
        self.slider.setValue(idx)
        self.slider.blockSignals(False)
        self.refresh()
        self.jump_to_slice.emit(self._orientation, idx)

    def _go_prev(self):
        """向前一张（边界保护）"""
        if self._center > self._min_s:
            self._center -= 1
            self.slider.blockSignals(True)
            self.slider.setValue(self._center)
            self.slider.blockSignals(False)
            self.refresh()
            self.jump_to_slice.emit(self._orientation, self._center)

    def _go_next(self):
        """向后一张（边界保护）"""
        if self._center < self._max_s:
            self._center += 1
            self.slider.blockSignals(True)
            self.slider.setValue(self._center)
            self.slider.blockSignals(False)
            self.refresh()
            self.jump_to_slice.emit(self._orientation, self._center)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        """鼠标滚轮控制中心切片，边界保护"""
        delta = -1 if event.angleDelta().y() > 0 else 1
        new_center = self._center + delta
        # 边界保护
        new_center = max(self._min_s, min(self._max_s, new_center))
        if new_center != self._center:
            self._center = new_center
            self.slider.blockSignals(True)
            self.slider.setValue(self._center)
            self.slider.blockSignals(False)
            self.refresh()
            self.jump_to_slice.emit(self._orientation, self._center)
        event.accept()

    def resizeEvent(self, event):
        """窗口大小变化时重建卡片以自适应"""
        super().resizeEvent(event)
        self._rebuild_grid()

    # ══════════════════════════════════════════════════════════════════════════
    # 辅助
    # ══════════════════════════════════════════════════════════════════════════

    def _update_slice_range(self, image_data):
        """更新切片范围（直接从维度计算，不使用 vtkImageViewer2 避免弹窗）"""
        dims = image_data.GetDimensions()  # (nx, ny, nz)
        if self._orientation == "XY":
            self._min_s = 0
            self._max_s = dims[2] - 1
        elif self._orientation == "YZ":
            self._min_s = 0
            self._max_s = dims[0] - 1
        else:  # XZ
            self._min_s = 0
            self._max_s = dims[1] - 1
        # 修正 center 在范围内
        self._center = max(self._min_s, min(self._max_s, self._center))

    def _get_current_slice(self) -> int:
        try:
            if self._orientation == "XY":
                return self._viewer_model.AxialOrthoViewer.viewer.GetSlice()
            elif self._orientation == "YZ":
                return self._viewer_model.SagittalOrthoViewer.viewer.GetSlice()
            else:
                return self._viewer_model.CoronalOrthoViewer.viewer.GetSlice()
        except Exception:
            return 0

    def _get_window_params(self) -> tuple:
        try:
            from src.model.ToolBarWidgetModel import ToolBarWidget
            ww = float(ToolBarWidget.contrast_widget.window_width_slider.value())
            wl = float(ToolBarWidget.contrast_widget.window_level_slider.value())
            return ww, wl
        except Exception:
            return 2000.0, 1000.0

    def _mk_lbl(self, text: str) -> QtWidgets.QLabel:
        l = QtWidgets.QLabel(text)
        l.setStyleSheet("color:#ddd;font-size:13px;")
        return l

    # ── 样式 ──────────────────────────────────────────────────────────────────

    def _combo_style(self):
        return ("QComboBox{background:#4a4a4a;color:#eee;border:1px solid #5a5a5a;"
                "border-radius:3px;padding:2px 6px;font-size:13px;}"
                "QComboBox::drop-down{border:none;}"
                "QComboBox QAbstractItemView{background:#4a4a4a;color:#eee;"
                "selection-background-color:#2d7dd2;font-size:13px;}")

    def _spin_style(self):
        return ("QSpinBox{background:#4a4a4a;color:#eee;border:1px solid #5a5a5a;"
                "border-radius:3px;padding:2px 4px;font-size:13px;}")

    def _slider_style(self):
        return ("QSlider::groove:horizontal{height:4px;background:#3a3a3a;border-radius:2px;}"
                "QSlider::handle:horizontal{width:14px;height:14px;margin:-5px 0;"
                "background:#5bc8f5;border-radius:7px;}"
                "QSlider::sub-page:horizontal{background:#2d7dd2;border-radius:2px;}")

    def _nav_btn_style(self):
        return ("QPushButton{background:#333;color:#aaa;border:1px solid #4a4a4a;"
                "border-radius:3px;font-size:10px;}"
                "QPushButton:hover{background:#444;color:#5bc8f5;}"
                "QPushButton:disabled{color:#444;border-color:#333;}")
