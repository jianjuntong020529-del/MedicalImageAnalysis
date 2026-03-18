# -*- coding: utf-8 -*-
import os
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QPoint, QRectF
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen

from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font


# ── 样式常量 ──────────────────────────────────────────────────────────────────

_BTN_PRIMARY = """
    QPushButton {
        background: #2d7dd2; color: white; border: none;
        border-radius: 4px; padding: 4px 12px; font-size: 12px;
    }
    QPushButton:hover { background: #3a8ee0; }
    QPushButton:pressed { background: #1f5fa0; }
    QPushButton:disabled { background: #555; color: #999; }
"""
_BTN_TOGGLE = """
    QPushButton {
        background: #3c3c3c; color: #ccc; border: 1px solid #555;
        border-radius: 4px; padding: 4px 10px; font-size: 12px;
    }
    QPushButton:hover { background: #4a4a4a; }
    QPushButton:checked { background: #2d7dd2; color: white; border: 1px solid #2d7dd2; }
    QPushButton:disabled { background: #2a2a2a; color: #666; border-color: #444; }
"""
_BTN_TOOL = """
    QPushButton {
        background: #3c3c3c; color: #ddd; border: 1px solid #555;
        border-radius: 4px; padding: 4px 10px; font-size: 12px;
    }
    QPushButton:hover { background: #4a4a4a; }
    QPushButton:checked { background: #e07b2d; color: white; border: 1px solid #e07b2d; }
    QPushButton:disabled { background: #2a2a2a; color: #666; border-color: #444; }
"""
_BTN_SAVE = """
    QPushButton {
        background: #27ae60; color: white; border: none;
        border-radius: 4px; padding: 4px 14px; font-size: 12px;
    }
    QPushButton:hover { background: #2ecc71; }
    QPushButton:pressed { background: #1e8449; }
    QPushButton:disabled { background: #555; color: #999; }
"""
_LABEL_STYLE = "color: #ccc; font-size: 12px;"
_LABEL_TITLE = "color: #5bc8f5; font-size: 13px; font-weight: bold;"
_PANEL_STYLE = "background: #2a2a2a; border-radius: 6px; padding: 4px;"
_STATUS_OK    = "color: #4fc; font-size: 11px;"
_STATUS_NONE  = "color: #888; font-size: 11px;"
_SPIN_STYLE = """
    QSpinBox { background: #3c3c3c; color: #ddd; border: 1px solid #555;
               border-radius: 3px; padding: 2px 4px; }
    QSpinBox::up-button, QSpinBox::down-button { width: 16px; }
"""
_COMBO_STYLE = """
    QComboBox { background: #3c3c3c; color: #ddd; border: 1px solid #555;
                border-radius: 3px; padding: 2px 6px; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { background: #3c3c3c; color: #ddd; selection-background-color: #2d7dd2; }
"""
_SLIDER_STYLE = """
    QSlider::groove:horizontal { height: 4px; background: #444; border-radius: 2px; }
    QSlider::handle:horizontal { width: 14px; height: 14px; margin: -5px 0;
        background: #2d7dd2; border-radius: 7px; }
    QSlider::sub-page:horizontal { background: #2d7dd2; border-radius: 2px; }
"""
_LIST_STYLE = """
    QListWidget { background: #1e1e1e; color: #ddd; border: 1px solid #444;
                  border-radius: 4px; font-size: 12px; }
    QListWidget::item { padding: 4px 8px; }
    QListWidget::item:selected { background: #2d7dd2; color: white; }
    QListWidget::item:hover { background: #333; }
"""


# ══════════════════════════════════════════════════════════════════════════════
# 共享视图状态（缩放 + 平移，两个视图同步）
# ══════════════════════════════════════════════════════════════════════════════

class ViewState:
    """两个视图共享的缩放/平移状态"""
    def __init__(self):
        self.zoom   = 1.0          # 缩放倍数
        self.offset = QPoint(0, 0) # 平移偏移（像素）

    def reset(self):
        self.zoom   = 1.0
        self.offset = QPoint(0, 0)


# ══════════════════════════════════════════════════════════════════════════════
# 自定义图像视图控件
# ══════════════════════════════════════════════════════════════════════════════

class ImageViewLabel(QtWidgets.QWidget):
    """
    支持：
    - 滚轮切换切片（发出 slice_changed 信号）
    - Ctrl + 滚轮 缩放
    - 中键/右键拖拽平移
    - 与另一个视图共享 ViewState（同步缩放/平移）
    """
    slice_changed = QtCore.pyqtSignal(int)   # 切片变化信号

    def __init__(self, view_state: ViewState, parent=None):
        super().__init__(parent)
        self._vs       = view_state
        self._pixmap   = None
        self._drag_pos = None
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setStyleSheet("border: 1px solid #444; background: #111; border-radius:4px;")
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)

    def set_pixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def pixmap(self):
        return self._pixmap

    # ── 绘制 ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)
        if self._pixmap is None or self._pixmap.isNull():
            return

        w, h = self.width(), self.height()
        pw, ph = self._pixmap.width(), self._pixmap.height()

        # 基础缩放（保持比例填满控件）
        base_scale = min(w / pw, h / ph)
        scale = base_scale * self._vs.zoom

        dw = int(pw * scale)
        dh = int(ph * scale)

        # 居中 + 平移偏移
        x = (w - dw) // 2 + self._vs.offset.x()
        y = (h - dh) // 2 + self._vs.offset.y()

        painter.drawPixmap(x, y, dw, dh, self._pixmap)

    # ── 事件 ──────────────────────────────────────────────────────────────────

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if event.modifiers() & Qt.ControlModifier:
            # Ctrl + 滚轮：缩放
            factor = 1.15 if delta > 0 else 1 / 1.15
            self._vs.zoom = max(0.2, min(self._vs.zoom * factor, 20.0))
            self._notify_siblings()
        else:
            # 普通滚轮：切换切片
            step = 1 if delta < 0 else -1
            self.slice_changed.emit(step)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._drag_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.pos() - self._drag_pos
            self._vs.offset += delta
            self._drag_pos = event.pos()
            self._notify_siblings()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._drag_pos = None
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        # 双击重置缩放/平移
        if event.button() == Qt.MiddleButton or event.button() == Qt.RightButton:
            self._vs.reset()
            self._notify_siblings()

    def _notify_siblings(self):
        """通知父控件刷新所有视图"""
        p = self.parent()
        while p is not None:
            if hasattr(p, '_on_view_state_changed'):
                p._on_view_state_changed()
                break
            p = p.parent()

    # ── 坐标转换（供绘制坐标映射使用）──────────────────────────────────────

    def widget_to_image_coords(self, pos, img_w, img_h):
        """将控件坐标转换为图像像素坐标，返回 (x, y) 或 None（超出范围）"""
        if self._pixmap is None:
            return None
        w, h = self.width(), self.height()
        pw, ph = self._pixmap.width(), self._pixmap.height()
        base_scale = min(w / pw, h / ph)
        scale = base_scale * self._vs.zoom
        dw = int(pw * scale)
        dh = int(ph * scale)
        x0 = (w - dw) // 2 + self._vs.offset.x()
        y0 = (h - dh) // 2 + self._vs.offset.y()
        ax = pos.x() - x0
        ay = pos.y() - y0
        if not (0 <= ax < dw and 0 <= ay < dh):
            return None
        xi = ax / dw * img_w
        yi = ay / dh * img_h
        return xi, yi


class SegmentationEditWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_drawing    = False
        self.edit_mode     = "draw"
        self._stroke_dirty = False
        self._visible_labels = None

        self._view_state = ViewState()   # 两视图共享缩放/平移

        from src.core.segmentation_editor import SegmentationEditor
        self.editor = SegmentationEditor()

        self._init_ui()

    # ══════════════════════════════════════════════════════════════════════════
    # UI 构建
    # ══════════════════════════════════════════════════════════════════════════

    def _init_ui(self):
        self.setMinimumSize(QtCore.QSize(1100, 820))
        self.setStyleSheet("background: #1a1a1a;")

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(10, 8, 10, 8)

        # 标题
        # title = QtWidgets.QLabel("NIfTI 分割结果编辑")
        # title.setStyleSheet(_LABEL_TITLE + " font-size:15px;")
        # root.addWidget(title)

        # 行1：加载原始影像
        root.addWidget(self._make_load_orig_row())
        # 行2：加载分割掩码
        root.addWidget(self._make_load_seg_row())
        # 行3：翻转/旋转方向控制
        root.addWidget(self._make_orient_row())
        # 行4：编辑工具栏
        root.addWidget(self._make_edit_tools_row())

        # 主体：左侧标签列表 + 中间原图 + 右侧编辑区
        root.addLayout(self._make_main_area(), stretch=1)

        # 底部参数行
        root.addWidget(self._make_params_row())
        # 状态栏
        root.addWidget(self._make_status_bar())

        self._set_edit_tools_enabled(False)
        self._set_orient_enabled(False)

    # ── 行1：加载原始影像 ──────────────────────────────────────────────────────

    def _make_load_orig_row(self):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(_PANEL_STYLE)
        row = QtWidgets.QHBoxLayout(frame)
        row.setSpacing(8)
        row.setContentsMargins(6, 4, 6, 4)

        lbl = QtWidgets.QLabel("原始影像:")
        lbl.setStyleSheet(_LABEL_STYLE + " font-weight:bold;")

        self.btn_load_orig = QtWidgets.QPushButton("加载原始影像")
        self.btn_load_orig.setFixedSize(120, 28)
        self.btn_load_orig.setStyleSheet(_BTN_PRIMARY)
        self.btn_load_orig.clicked.connect(self.on_load_original)

        self.lbl_orig_status = QtWidgets.QLabel("未加载")
        self.lbl_orig_status.setStyleSheet(_STATUS_NONE)

        row.addWidget(lbl)
        row.addWidget(self.btn_load_orig)
        row.addWidget(self.lbl_orig_status)
        row.addStretch()
        return frame

    # ── 行2：加载分割掩码 ──────────────────────────────────────────────────────

    def _make_load_seg_row(self):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(_PANEL_STYLE)
        row = QtWidgets.QHBoxLayout(frame)
        row.setSpacing(8)
        row.setContentsMargins(6, 4, 6, 4)

        lbl = QtWidgets.QLabel("分割掩码:")
        lbl.setStyleSheet(_LABEL_STYLE + " font-weight:bold;")

        self.btn_load_seg = QtWidgets.QPushButton("加载分割掩码")
        self.btn_load_seg.setFixedSize(120, 28)
        self.btn_load_seg.setStyleSheet(_BTN_PRIMARY)
        self.btn_load_seg.setEnabled(False)
        self.btn_load_seg.clicked.connect(self.on_load_segmentation)

        self.lbl_seg_status = QtWidgets.QLabel("未加载")
        self.lbl_seg_status.setStyleSheet(_STATUS_NONE)

        row.addWidget(lbl)
        row.addWidget(self.btn_load_seg)
        row.addWidget(self.lbl_seg_status)
        row.addStretch()
        return frame

    # ── 行3：翻转/旋转方向控制（独立一行）────────────────────────────────────

    def _make_orient_row(self):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(_PANEL_STYLE)
        row = QtWidgets.QHBoxLayout(frame)
        row.setSpacing(8)
        row.setContentsMargins(6, 4, 6, 4)

        lbl = QtWidgets.QLabel("掩码方向:")
        lbl.setStyleSheet(_LABEL_STYLE)

        self.btn_flip_x = QtWidgets.QPushButton("X轴翻转")
        self.btn_flip_x.setCheckable(True)
        self.btn_flip_x.setFixedSize(80, 26)
        self.btn_flip_x.setStyleSheet(_BTN_TOGGLE)
        self.btn_flip_x.setToolTip("沿X轴翻转（上下方向）")
        self.btn_flip_x.clicked.connect(self._on_flip_x)

        self.btn_flip_y = QtWidgets.QPushButton("Y轴翻转")
        self.btn_flip_y.setCheckable(True)
        self.btn_flip_y.setFixedSize(80, 26)
        self.btn_flip_y.setStyleSheet(_BTN_TOGGLE)
        self.btn_flip_y.setToolTip("沿Y轴翻转（左右方向）")
        self.btn_flip_y.clicked.connect(self._on_flip_y)

        self.btn_flip_z = QtWidgets.QPushButton("Z轴翻转")
        self.btn_flip_z.setCheckable(True)
        self.btn_flip_z.setFixedSize(80, 26)
        self.btn_flip_z.setStyleSheet(_BTN_TOGGLE)
        self.btn_flip_z.setToolTip("沿Z轴翻转（切片顺序反转）")
        self.btn_flip_z.clicked.connect(self._on_flip_z)

        lbl_rot = QtWidgets.QLabel("旋转:")
        lbl_rot.setStyleSheet(_LABEL_STYLE)
        self.combo_rotate = QtWidgets.QComboBox()
        self.combo_rotate.addItems(["0°", "90°", "180°", "270°"])
        self.combo_rotate.setFixedWidth(75)
        self.combo_rotate.setStyleSheet(_COMBO_STYLE)
        self.combo_rotate.currentIndexChanged.connect(self._on_rotate_change)

        self._orient_widgets = [self.btn_flip_x, self.btn_flip_y, self.btn_flip_z, self.combo_rotate]

        row.addWidget(lbl)
        row.addWidget(self.btn_flip_x)
        row.addWidget(self.btn_flip_y)
        row.addWidget(self.btn_flip_z)
        row.addWidget(lbl_rot)
        row.addWidget(self.combo_rotate)
        row.addStretch()
        return frame

    # ── 行4：编辑工具栏（独立一行）───────────────────────────────────────────

    def _make_edit_tools_row(self):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(_PANEL_STYLE)
        row = QtWidgets.QHBoxLayout(frame)
        row.setSpacing(8)
        row.setContentsMargins(6, 4, 6, 4)

        self.btn_draw = QtWidgets.QPushButton("画笔")
        self.btn_draw.setCheckable(True)
        self.btn_draw.setChecked(True)
        self.btn_draw.setFixedSize(70, 28)
        self.btn_draw.setStyleSheet(_BTN_TOOL)
        self.btn_draw.clicked.connect(lambda: self._set_edit_mode("draw"))

        self.btn_erase = QtWidgets.QPushButton("橡皮擦")
        self.btn_erase.setCheckable(True)
        self.btn_erase.setFixedSize(70, 28)
        self.btn_erase.setStyleSheet(_BTN_TOOL)
        self.btn_erase.clicked.connect(lambda: self._set_edit_mode("erase"))

        lbl_shape = QtWidgets.QLabel("形状:")
        lbl_shape.setStyleSheet(_LABEL_STYLE)
        self.combo_shape = QtWidgets.QComboBox()
        self.combo_shape.addItems(["圆形", "矩形"])
        self.combo_shape.setFixedWidth(70)
        self.combo_shape.setStyleSheet(_COMBO_STYLE)
        self.combo_shape.currentIndexChanged.connect(self._on_shape_change)

        lbl_brush = QtWidgets.QLabel("画笔大小:")
        lbl_brush.setStyleSheet(_LABEL_STYLE)
        self.spin_brush = QtWidgets.QSpinBox()
        self.spin_brush.setRange(1, 100)
        self.spin_brush.setValue(5)
        self.spin_brush.setFixedWidth(60)
        self.spin_brush.setStyleSheet(_SPIN_STYLE)
        self.spin_brush.valueChanged.connect(lambda v: setattr(self.editor, 'brush_size', v))

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.VLine)
        sep.setStyleSheet("color: #555;")

        self.btn_undo = QtWidgets.QPushButton("↩ 撤销")
        self.btn_undo.setFixedSize(70, 28)
        self.btn_undo.setStyleSheet(_BTN_TOOL)
        self.btn_undo.clicked.connect(self.on_undo)

        self.btn_redo = QtWidgets.QPushButton("↪ 重做")
        self.btn_redo.setFixedSize(70, 28)
        self.btn_redo.setStyleSheet(_BTN_TOOL)
        self.btn_redo.clicked.connect(self.on_redo)

        self.btn_save = QtWidgets.QPushButton("💾 保存结果")
        self.btn_save.setFixedSize(100, 28)
        self.btn_save.setStyleSheet(_BTN_SAVE)
        self.btn_save.clicked.connect(self.on_save)

        self._edit_tool_widgets = [
            self.btn_draw, self.btn_erase, self.combo_shape,
            self.spin_brush, self.btn_undo, self.btn_redo, self.btn_save,
        ]

        row.addWidget(self.btn_draw)
        row.addWidget(self.btn_erase)
        row.addWidget(lbl_shape)
        row.addWidget(self.combo_shape)
        row.addWidget(lbl_brush)
        row.addWidget(self.spin_brush)
        row.addWidget(sep)
        row.addWidget(self.btn_undo)
        row.addWidget(self.btn_redo)
        row.addStretch()
        row.addWidget(self.btn_save)
        return frame

    # ── 主体区域：标签列表 + 原图 + 编辑区 ───────────────────────────────────

    def _make_main_area(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(8)

        layout.addWidget(self._make_label_panel(), stretch=0)

        # 中间：原始影像
        left_box = QtWidgets.QVBoxLayout()
        t1 = QtWidgets.QLabel("原始影像")
        t1.setAlignment(Qt.AlignCenter)
        t1.setStyleSheet(_LABEL_STYLE)
        self.lbl_orig = ImageViewLabel(self._view_state)
        self.lbl_orig.slice_changed.connect(self._on_scroll_slice)
        left_box.addWidget(t1)
        left_box.addWidget(self.lbl_orig, stretch=1)
        layout.addLayout(left_box, stretch=1)

        # 右侧：分割编辑区
        right_box = QtWidgets.QVBoxLayout()
        t2 = QtWidgets.QLabel("分割编辑区")
        t2.setAlignment(Qt.AlignCenter)
        t2.setStyleSheet(_LABEL_STYLE)
        self.lbl_edit = ImageViewLabel(self._view_state)
        self.lbl_edit.slice_changed.connect(self._on_scroll_slice)
        self.lbl_edit.setMouseTracking(True)
        # 绘制事件挂载到 lbl_edit 的鼠标事件
        self.lbl_edit.mousePressEvent   = self._on_mouse_press
        self.lbl_edit.mouseMoveEvent    = self._on_mouse_move
        self.lbl_edit.mouseReleaseEvent = self._on_mouse_release
        right_box.addWidget(t2)
        right_box.addWidget(self.lbl_edit, stretch=1)
        layout.addLayout(right_box, stretch=1)

        return layout

    def _on_view_state_changed(self):
        """缩放/平移变化时同步刷新两个视图"""
        self.lbl_orig.update()
        self.lbl_edit.update()

    def _make_label_panel(self):
        """左侧标签列表面板"""
        frame = QtWidgets.QFrame()
        frame.setFixedWidth(150)
        frame.setStyleSheet("background: #222; border-radius: 6px; border: 1px solid #444;")
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setSpacing(4)
        vbox.setContentsMargins(6, 6, 6, 6)

        # 标题行：标签列表 + 全显示按钮
        title_row = QtWidgets.QHBoxLayout()
        lbl_title = QtWidgets.QLabel("标签列表")
        lbl_title.setStyleSheet(_LABEL_TITLE)
        self.btn_show_all = QtWidgets.QPushButton("👁 全显")
        self.btn_show_all.setFixedSize(54, 22)
        self.btn_show_all.setStyleSheet("""
            QPushButton { background:#333; color:#aaa; border:1px solid #555;
                          border-radius:3px; font-size:11px; }
            QPushButton:hover { background:#444; color:#fff; }
            QPushButton:checked { background:#2d7dd2; color:white; border-color:#2d7dd2; }
        """)
        self.btn_show_all.setCheckable(True)
        self.btn_show_all.setChecked(True)
        self.btn_show_all.clicked.connect(self._on_show_all_clicked)
        title_row.addWidget(lbl_title)
        title_row.addStretch()
        title_row.addWidget(self.btn_show_all)
        vbox.addLayout(title_row)

        self.label_list = QtWidgets.QListWidget()
        self.label_list.setStyleSheet(_LIST_STYLE)
        self.label_list.itemClicked.connect(self._on_label_item_clicked)
        vbox.addWidget(self.label_list, stretch=1)

        self.lbl_current_label = QtWidgets.QLabel("编辑: 标签 1")
        self.lbl_current_label.setStyleSheet("color: #e07b2d; font-size: 11px;")
        self.lbl_current_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.lbl_current_label)

        return frame

    # ── 底部参数行 ────────────────────────────────────────────────────────────

    def _make_params_row(self):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(_PANEL_STYLE)
        grid = QtWidgets.QGridLayout(frame)
        grid.setSpacing(8)
        grid.setContentsMargins(8, 6, 8, 6)

        # 切片滑块
        grid.addWidget(self._lbl("当前切片:"), 0, 0)
        self.slider_slice = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_slice.setMinimum(0)
        self.slider_slice.setMaximum(0)
        self.slider_slice.setStyleSheet(_SLIDER_STYLE)
        self.slider_slice.valueChanged.connect(self._on_slice_change)
        grid.addWidget(self.slider_slice, 0, 1, 1, 3)
        self.lbl_slice = QtWidgets.QLabel("0 / 0")
        self.lbl_slice.setStyleSheet(_LABEL_STYLE)
        self.lbl_slice.setMinimumWidth(70)
        grid.addWidget(self.lbl_slice, 0, 4)

        # 叠加透明度
        grid.addWidget(self._lbl("叠加透明度:"), 1, 0)
        self.slider_alpha = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_alpha.setRange(0, 100)
        self.slider_alpha.setValue(50)
        self.slider_alpha.setStyleSheet(_SLIDER_STYLE)
        self.slider_alpha.valueChanged.connect(self._on_alpha_change)
        grid.addWidget(self.slider_alpha, 1, 1, 1, 3)
        self.lbl_alpha = QtWidgets.QLabel("50%")
        self.lbl_alpha.setStyleSheet(_LABEL_STYLE)
        grid.addWidget(self.lbl_alpha, 1, 4)

        # 窗宽（WW）
        grid.addWidget(self._lbl("窗宽 WW:"), 2, 0)
        self.slider_ww = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_ww.setRange(1, 10000)
        self.slider_ww.setValue(2000)
        self.slider_ww.setStyleSheet(_SLIDER_STYLE)
        self.slider_ww.valueChanged.connect(self._on_ww_wc_change)
        grid.addWidget(self.slider_ww, 2, 1, 1, 3)
        self.lbl_ww = QtWidgets.QLabel("2000")
        self.lbl_ww.setStyleSheet(_LABEL_STYLE)
        self.lbl_ww.setMinimumWidth(70)
        grid.addWidget(self.lbl_ww, 2, 4)

        # 窗位（WC）
        grid.addWidget(self._lbl("窗位 WC:"), 3, 0)
        self.slider_wc = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_wc.setRange(-5000, 5000)
        self.slider_wc.setValue(0)
        self.slider_wc.setStyleSheet(_SLIDER_STYLE)
        self.slider_wc.valueChanged.connect(self._on_ww_wc_change)
        grid.addWidget(self.slider_wc, 3, 1, 1, 3)
        self.lbl_wc = QtWidgets.QLabel("0")
        self.lbl_wc.setStyleSheet(_LABEL_STYLE)
        self.lbl_wc.setMinimumWidth(70)
        grid.addWidget(self.lbl_wc, 3, 4)

        return frame

    # ── 状态栏（鼠标坐标 + 切片信息）────────────────────────────────────────

    def _make_status_bar(self):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet("background: #1e1e1e; border-radius: 4px; border: 1px solid #333;")
        row = QtWidgets.QHBoxLayout(frame)
        row.setContentsMargins(12, 6, 12, 6)
        row.setSpacing(24)

        self.lbl_mouse_pos = QtWidgets.QLabel("鼠标: (-, -)")
        self.lbl_mouse_pos.setStyleSheet("color: #aaa; font-size: 13px;")

        self.lbl_pixel_val = QtWidgets.QLabel("像素值: -")
        self.lbl_pixel_val.setStyleSheet("color: #aaa; font-size: 13px;")

        self.lbl_seg_label_at = QtWidgets.QLabel("标签: -")
        self.lbl_seg_label_at.setStyleSheet("color: #aaa; font-size: 13px;")

        self.lbl_data_shape = QtWidgets.QLabel("形状: -")
        self.lbl_data_shape.setStyleSheet("color: #aaa; font-size: 13px;")

        self.lbl_slice_info = QtWidgets.QLabel("切片: - / -")
        self.lbl_slice_info.setStyleSheet("color: #aaa; font-size: 13px;")

        row.addWidget(self.lbl_mouse_pos)
        row.addWidget(self.lbl_pixel_val)
        row.addWidget(self.lbl_seg_label_at)
        row.addWidget(self.lbl_data_shape)
        row.addStretch()
        row.addWidget(self.lbl_slice_info)
        return frame

    def _lbl(self, text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(_LABEL_STYLE)
        return l

    # ══════════════════════════════════════════════════════════════════════════
    # 加载事件
    # ══════════════════════════════════════════════════════════════════════════

    def on_load_original(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "加载原始影像", "",
            "所有支持格式 (*.dcm *.nii *.nii.gz *.npy);;"
            "DICOM (*.dcm);;NIfTI (*.nii *.nii.gz);;NumPy (*.npy)"
        )
        if not path:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "或选择 DICOM 目录")
        if not path:
            return
        try:
            self.editor.load_original(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "加载失败", str(e))
            return

        self._view_state.reset()   # 重置缩放/平移

        d = self.editor.orig_data.shape[2]
        mid = d // 2
        self.slider_slice.setRange(0, d - 1)
        self.slider_slice.setValue(mid)
        self.editor.current_slice = mid
        self.lbl_slice.setText(f"{mid} / {d - 1}")
        self.lbl_slice_info.setText(f"切片: {mid} / {d - 1}")

        self._refresh_orig()

        # 只显示文件路径
        short = os.path.basename(path.rstrip("/\\"))
        self.lbl_orig_status.setText(short)
        self.lbl_orig_status.setStyleSheet(_STATUS_OK)
        # 形状信息放到状态栏
        shape = self.editor.orig_data.shape
        self.lbl_data_shape.setText(f"形状: {shape[0]}×{shape[1]}×{shape[2]}")

        # 初始化窗位窗宽到数据范围
        dmin, dmax = self.editor.get_data_range()
        ww_init = int(dmax - dmin)
        wc_init = int((dmax + dmin) / 2)
        self.slider_ww.setRange(1, max(ww_init * 2, 100))
        self.slider_ww.setValue(ww_init)
        self.slider_wc.setRange(int(dmin - ww_init), int(dmax + ww_init))
        self.slider_wc.setValue(wc_init)
        self.lbl_ww.setText(str(ww_init))
        self.lbl_wc.setText(str(wc_init))

        self.btn_load_seg.setEnabled(True)

    def on_load_segmentation(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "加载分割掩码", "", "NIfTI (*.nii.gz *.nii)"
        )
        if not path:
            return
        try:
            self.editor.load_segmentation(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "加载失败", str(e))
            return

        self._refresh_edit()
        self._set_edit_tools_enabled(True)
        self._set_orient_enabled(True)
        self._rebuild_label_list()

        short = os.path.basename(path)
        self.lbl_seg_status.setText(short)
        self.lbl_seg_status.setStyleSheet(_STATUS_OK)

    # ══════════════════════════════════════════════════════════════════════════
    # 标签列表
    # ══════════════════════════════════════════════════════════════════════════

    def _rebuild_label_list(self):
        """根据分割数据重建标签列表"""
        self.label_list.clear()
        self._visible_labels = None   # 全显示
        self.btn_show_all.setChecked(True)
        labels = self.editor.get_seg_labels()
        if not labels:
            return

        for lv in labels:
            color = self.editor.get_label_color(lv)
            item = QtWidgets.QListWidgetItem(f"👁  标签 {lv}")
            item.setData(Qt.UserRole, lv)
            item.setData(Qt.UserRole + 1, True)
            item.setForeground(QColor(*color))
            self.label_list.addItem(item)

        self.label_list.setCurrentRow(0)
        self._select_label(labels[0])

    def _on_show_all_clicked(self):
        """
        全显按钮切换逻辑：
        - 当前全显 → 点击后关闭所有标签显示（隐藏分割叠加）
        - 当前隐藏 → 点击后恢复全显
        """
        if self._visible_labels is None:
            # 当前全显 → 关闭所有标签
            self._visible_labels = set()
            self.btn_show_all.setChecked(False)
            for i in range(self.label_list.count()):
                it = self.label_list.item(i)
                lv = it.data(Qt.UserRole)
                it.setText(f"🚫  标签 {lv}")
                it.setData(Qt.UserRole + 1, False)
        else:
            # 当前部分/全隐藏 → 恢复全显
            self._visible_labels = None
            self.btn_show_all.setChecked(True)
            for i in range(self.label_list.count()):
                it = self.label_list.item(i)
                lv = it.data(Qt.UserRole)
                it.setText(f"👁  标签 {lv}")
                it.setData(Qt.UserRole + 1, True)
        self._refresh_edit()

    def _on_label_item_clicked(self, item):
        lv = item.data(Qt.UserRole)
        self._select_label(lv)

        # 切换为只显示该标签
        self._visible_labels = {lv}
        self.btn_show_all.setChecked(False)
        for i in range(self.label_list.count()):
            it = self.label_list.item(i)
            ilv = it.data(Qt.UserRole)
            if ilv == lv:
                it.setText(f"�  标签 {lv}")
                it.setData(Qt.UserRole + 1, True)
            else:
                it.setText(f"🚫  标签 {ilv}")
                it.setData(Qt.UserRole + 1, False)
        self._refresh_edit()

    def _select_label(self, lv):
        self.editor.current_label = lv
        self.lbl_current_label.setText(f"编辑: 标签 {lv}")
        color = self.editor.get_label_color(lv)
        self.lbl_current_label.setStyleSheet(
            f"color: rgb({color[0]},{color[1]},{color[2]}); font-size: 11px; font-weight:bold;"
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 方向调整
    # ══════════════════════════════════════════════════════════════════════════

    def _on_flip_x(self, checked):
        self.editor.flip_x = checked
        self._refresh_edit()

    def _on_flip_y(self, checked):
        self.editor.flip_y = checked
        self._refresh_edit()

    def _on_flip_z(self, checked):
        self.editor.flip_z = checked
        self._refresh_edit()

    def _on_rotate_change(self, idx):
        self.editor.rotate_k = idx
        self._refresh_edit()

    # ══════════════════════════════════════════════════════════════════════════
    # 显示刷新
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_orig(self):
        ww = self.slider_ww.value() if hasattr(self, 'slider_ww') else None
        wc = self.slider_wc.value() if hasattr(self, 'slider_wc') else None
        arr = self.editor.get_orig_display(ww=ww, wc=wc)
        if arr is None:
            return
        self.lbl_orig.set_pixmap(self._to_pixmap_gray(arr))

    def _refresh_edit(self):
        ww = self.slider_ww.value() if hasattr(self, 'slider_ww') else None
        wc = self.slider_wc.value() if hasattr(self, 'slider_wc') else None
        orig, seg = self.editor.get_display_slice()
        if orig is None:
            return
        fused = self.editor.fuse_image(orig, seg, visible_labels=self._visible_labels, ww=ww, wc=wc)
        self.lbl_edit.set_pixmap(self._to_pixmap_rgb(fused))

    def _refresh_all(self):
        self._refresh_orig()
        self._refresh_edit()

    # ══════════════════════════════════════════════════════════════════════════
    # 参数事件
    # ══════════════════════════════════════════════════════════════════════════

    def _on_slice_change(self, value):
        self.editor.current_slice = value
        if self.editor.orig_data is not None:
            d = self.editor.orig_data.shape[2]
            self.lbl_slice.setText(f"{value} / {d - 1}")
            self.lbl_slice_info.setText(f"切片: {value} / {d - 1}")
        self._refresh_all()

    def _on_alpha_change(self, value):
        self.editor.alpha = value / 100.0
        self.lbl_alpha.setText(f"{value}%")
        self._refresh_edit()

    def _on_ww_wc_change(self):
        ww = self.slider_ww.value()
        wc = self.slider_wc.value()
        self.lbl_ww.setText(str(ww))
        self.lbl_wc.setText(str(wc))
        self._refresh_all()

    def _on_shape_change(self, idx):
        self.editor.brush_shape = "circle" if idx == 0 else "rect"

    def on_undo(self):
        if self.editor.undo():
            self._refresh_edit()

    def on_redo(self):
        if self.editor.redo():
            self._refresh_edit()

    def on_save(self):
        if self.editor.seg_data is None:
            QtWidgets.QMessageBox.warning(self, "提示", "请先加载分割掩码！")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存分割结果", "", "NIfTI (*.nii.gz)"
        )
        if not path:
            return
        try:
            self.editor.save_edited_seg(path)
            QtWidgets.QMessageBox.information(self, "成功", "保存成功！")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "保存失败", str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # 鼠标绘制 + 状态栏实时更新
    # ══════════════════════════════════════════════════════════════════════════

    def _on_scroll_slice(self, step):
        """滚轮切片：step=+1 下一片，step=-1 上一片，同步滑块"""
        if self.editor.orig_data is None:
            return
        d = self.editor.orig_data.shape[2]
        new_val = max(0, min(self.editor.current_slice + step, d - 1))
        # 通过滑块触发，避免重复刷新
        self.slider_slice.setValue(new_val)

    def _on_mouse_press(self, event):
        if self.editor.seg_data is None:
            return
        if event.button() == Qt.LeftButton:
            self.is_drawing = True
            self._stroke_dirty = False
            self._do_paint(event.pos())

    def _on_mouse_move(self, event):
        self._update_status_bar(event.pos())
        if not self.is_drawing or self.editor.seg_data is None:
            return
        if event.buttons() & Qt.LeftButton:
            self._do_paint(event.pos())

    def _on_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_drawing and self._stroke_dirty:
                self.editor.commit_stroke()
            self.is_drawing = False

    def _do_paint(self, pos):
        if self.editor.orig_data is None:
            return
        h_orig = self.editor.orig_data.shape[0]
        w_orig = self.editor.orig_data.shape[1]

        if self.editor.rotate_k in (1, 3):
            disp_h, disp_w = w_orig, h_orig
        else:
            disp_h, disp_w = h_orig, w_orig

        result = self.lbl_edit.widget_to_image_coords(pos, disp_w, disp_h)
        if result is None:
            return
        xd, yd = result
        x_orig, y_orig = self.editor.display_to_orig_coords(xd, yd, disp_h, disp_w)
        self.editor.edit_seg_mask(x_orig, y_orig, self.edit_mode)
        self._stroke_dirty = True
        self._refresh_edit()

    def _update_status_bar(self, pos):
        if self.editor.orig_data is None:
            return
        h_orig = self.editor.orig_data.shape[0]
        w_orig = self.editor.orig_data.shape[1]

        if self.editor.rotate_k in (1, 3):
            disp_h, disp_w = w_orig, h_orig
        else:
            disp_h, disp_w = h_orig, w_orig

        result = self.lbl_edit.widget_to_image_coords(pos, disp_w, disp_h)
        if result is None:
            self.lbl_mouse_pos.setText("鼠标: (-, -)")
            self.lbl_pixel_val.setText("像素值: -")
            self.lbl_seg_label_at.setText("标签: -")
            return

        xd, yd = result
        x, y = self.editor.display_to_orig_coords(xd, yd, disp_h, disp_w)
        self.lbl_mouse_pos.setText(f"鼠标: ({x}, {y})")
        pv = self.editor.orig_data[y, x, self.editor.current_slice]
        self.lbl_pixel_val.setText(f"像素值: {pv:.1f}")
        if self.editor.seg_data is not None:
            seg_idx = self.editor._get_seg_slice_index()
            sv = self.editor.seg_data[y, x, seg_idx]
            self.lbl_seg_label_at.setText(f"标签: {int(sv)}")

    # ══════════════════════════════════════════════════════════════════════════
    # 辅助
    # ══════════════════════════════════════════════════════════════════════════

    def _set_edit_mode(self, mode):
        self.edit_mode = mode
        self.btn_draw.setChecked(mode == "draw")
        self.btn_erase.setChecked(mode == "erase")

    def _set_edit_tools_enabled(self, enabled):
        for w in self._edit_tool_widgets:
            w.setEnabled(enabled)

    def _set_orient_enabled(self, enabled):
        for w in self._orient_widgets:
            w.setEnabled(enabled)

    def _to_pixmap_gray(self, arr):
        h, w = arr.shape
        img = np.ascontiguousarray(arr)
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
        return QPixmap.fromImage(qimg.copy())

    def _to_pixmap_rgb(self, arr):
        rgb = np.ascontiguousarray(arr.astype(np.uint8))
        h, w, _ = rgb.shape
        qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())
