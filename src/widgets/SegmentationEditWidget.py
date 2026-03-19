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


# ══════════════════════════════════════════════════════════════════════════════
# 共享视图状态（缩放 + 平移，两个视图同步）
# ══════════════════════════════════════════════════════════════════════════════

class ViewState:
    """两个视图共享的缩放/平移状态"""
    def __init__(self):
        self.zoom   = 1.0
        self.offset = QPoint(0, 0)

    def reset(self):
        self.zoom   = 1.0
        self.offset = QPoint(0, 0)


# ══════════════════════════════════════════════════════════════════════════════
# 自定义图像视图控件
# ══════════════════════════════════════════════════════════════════════════════

class ImageViewLabel(QtWidgets.QWidget):
    slice_changed = QtCore.pyqtSignal(int)

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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)
        if self._pixmap is None or self._pixmap.isNull():
            return
        w, h = self.width(), self.height()
        pw, ph = self._pixmap.width(), self._pixmap.height()
        base_scale = min(w / pw, h / ph)
        scale = base_scale * self._vs.zoom
        dw = int(pw * scale)
        dh = int(ph * scale)
        x = (w - dw) // 2 + self._vs.offset.x()
        y = (h - dh) // 2 + self._vs.offset.y()
        painter.drawPixmap(x, y, dw, dh, self._pixmap)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if delta > 0 else 1 / 1.15
            self._vs.zoom = max(0.2, min(self._vs.zoom * factor, 20.0))
            self._notify_siblings()
        else:
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
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._vs.reset()
            self._notify_siblings()

    def _notify_siblings(self):
        p = self.parent()
        while p is not None:
            if hasattr(p, '_on_view_state_changed'):
                p._on_view_state_changed()
                break
            p = p.parent()

    def widget_to_image_coords(self, pos, img_w, img_h):
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
        self._label_rows = {}   # label_val -> (row_widget, checkbox)
        self._view_state = ViewState()
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
        root.addWidget(self._make_load_orig_row())
        root.addWidget(self._make_load_seg_row())
        root.addWidget(self._make_orient_row())
        root.addWidget(self._make_edit_tools_row())
        root.addLayout(self._make_main_area(), stretch=1)
        root.addWidget(self._make_params_row())
        root.addWidget(self._make_status_bar())
        self._set_edit_tools_enabled(False)
        self._set_orient_enabled(False)

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

    def _make_main_area(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(self._make_label_panel(), stretch=0)
        left_box = QtWidgets.QVBoxLayout()
        t1 = QtWidgets.QLabel("原始影像")
        t1.setAlignment(Qt.AlignCenter)
        t1.setStyleSheet(_LABEL_STYLE)
        self.lbl_orig = ImageViewLabel(self._view_state)
        self.lbl_orig.slice_changed.connect(self._on_scroll_slice)
        left_box.addWidget(t1)
        left_box.addWidget(self.lbl_orig, stretch=1)
        layout.addLayout(left_box, stretch=1)
        right_box = QtWidgets.QVBoxLayout()
        t2 = QtWidgets.QLabel("分割编辑区")
        t2.setAlignment(Qt.AlignCenter)
        t2.setStyleSheet(_LABEL_STYLE)
        self.lbl_edit = ImageViewLabel(self._view_state)
        self.lbl_edit.slice_changed.connect(self._on_scroll_slice)
        self.lbl_edit.setMouseTracking(True)
        self.lbl_edit.mousePressEvent   = self._on_mouse_press
        self.lbl_edit.mouseMoveEvent    = self._on_mouse_move
        self.lbl_edit.mouseReleaseEvent = self._on_mouse_release
        right_box.addWidget(t2)
        right_box.addWidget(self.lbl_edit, stretch=1)
        layout.addLayout(right_box, stretch=1)
        return layout

    def _on_view_state_changed(self):
        self.lbl_orig.update()
        self.lbl_edit.update()

    def _make_label_panel(self):
        """左侧标签列表面板（色块 + 显隐复选框，与三维视图风格一致）"""
        frame = QtWidgets.QFrame()
        frame.setFixedWidth(155)
        frame.setStyleSheet(
            "background: #252525; border-radius: 6px; border: 1px solid #3a3a3a;"
        )
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setSpacing(4)
        vbox.setContentsMargins(6, 6, 6, 6)

        lbl_title = QtWidgets.QLabel("标签列表")
        lbl_title.setStyleSheet("color: #5bc8f5; font-size: 13px; font-weight: bold;")
        vbox.addWidget(lbl_title)

        # 全显 / 全隐 / 清除 按钮行
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(4)

        def _mk_btn(text, color="#4a4a4a"):
            b = QtWidgets.QPushButton(text)
            b.setFixedHeight(22)
            b.setStyleSheet(
                f"QPushButton{{background:{color};color:#eee;border:none;"
                f"border-radius:3px;font-size:12px;padding:0 4px;}}"
                f"QPushButton:hover{{background:#5a5a5a;}}"
            )
            return b

        self.btn_show_all  = _mk_btn("全显")
        self.btn_hide_all  = _mk_btn("全隐")
        self.btn_clear_seg = _mk_btn("清除", "#e53935")
        self.btn_show_all.clicked.connect(self._on_show_all_labels)
        self.btn_hide_all.clicked.connect(self._on_hide_all_labels)
        self.btn_clear_seg.clicked.connect(self._on_clear_seg)
        btn_row.addWidget(self.btn_show_all)
        btn_row.addWidget(self.btn_hide_all)
        btn_row.addWidget(self.btn_clear_seg)
        vbox.addLayout(btn_row)

        # 滚动列表
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea{background:#1e1e1e;border:1px solid #3a3a3a;border-radius:3px;}"
            "QScrollBar:vertical{background:#252525;width:8px;}"
            "QScrollBar::handle:vertical{background:#3a3a3a;border-radius:4px;}"
        )
        self._label_list_container = QtWidgets.QWidget()
        self._label_list_container.setStyleSheet("background:#1e1e1e;")
        self._label_list_layout = QtWidgets.QVBoxLayout(self._label_list_container)
        self._label_list_layout.setContentsMargins(4, 4, 4, 4)
        self._label_list_layout.setSpacing(2)
        self._label_list_layout.addStretch()
        scroll.setWidget(self._label_list_container)
        vbox.addWidget(scroll, 1)

        self.lbl_current_label = QtWidgets.QLabel("编辑: 标签 1")
        self.lbl_current_label.setStyleSheet("color: #e07b2d; font-size: 11px;")
        self.lbl_current_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.lbl_current_label)

        return frame

    def _make_params_row(self):
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(_PANEL_STYLE)
        grid = QtWidgets.QGridLayout(frame)
        grid.setSpacing(8)
        grid.setContentsMargins(8, 6, 8, 6)
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
        self._view_state.reset()
        d = self.editor.orig_data.shape[2]
        mid = d // 2
        self.slider_slice.setRange(0, d - 1)
        self.slider_slice.setValue(mid)
        self.editor.current_slice = mid
        self.lbl_slice.setText(f"{mid} / {d - 1}")
        self.lbl_slice_info.setText(f"切片: {mid} / {d - 1}")
        self._refresh_orig()
        short = os.path.basename(path.rstrip("/\\"))
        self.lbl_orig_status.setText(short)
        self.lbl_orig_status.setStyleSheet(_STATUS_OK)
        shape = self.editor.orig_data.shape
        self.lbl_data_shape.setText(f"形状: {shape[0]}x{shape[1]}x{shape[2]}")
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
    # 标签列表（新版：色块 + 显隐复选框）
    # ══════════════════════════════════════════════════════════════════════════

    def _rebuild_label_list(self):
        """重建标签列表"""
        self._label_rows.clear()
        while self._label_list_layout.count() > 1:
            item = self._label_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._visible_labels = None
        labels = self.editor.get_seg_labels()
        if not labels:
            return
        for lv in labels:
            row_w = self._make_label_row(lv)
            self._label_list_layout.insertWidget(self._label_list_layout.count() - 1, row_w)
        self._select_label(labels[0])
        self._highlight_row(labels[0])

    def _make_label_row(self, lv):
        """创建单行：色块 + 标签名 + 显隐复选框"""
        color = self.editor.get_label_color(lv)
        hex_c = "#{:02x}{:02x}{:02x}".format(*color)
        row_w = QtWidgets.QWidget()
        row_w.setFixedHeight(28)
        row_w.setCursor(Qt.PointingHandCursor)
        row_w.setStyleSheet(
            "QWidget{background:transparent;border-radius:3px;}"
            "QWidget:hover{background:#2a2a2a;}"
        )
        h = QtWidgets.QHBoxLayout(row_w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(6)
        dot = QtWidgets.QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background:{hex_c};border-radius:6px;border:none;")
        h.addWidget(dot)
        lbl = QtWidgets.QLabel(f"标签 {lv}")
        lbl.setStyleSheet("color:#dddddd;font-size:12px;background:transparent;")
        h.addWidget(lbl, 1)
        cb = QtWidgets.QCheckBox()
        cb.setChecked(True)
        cb.setStyleSheet(
            "QCheckBox{color:#888;}"
            "QCheckBox::indicator{width:14px;height:14px;}"
        )
        cb.stateChanged.connect(
            lambda state, v=lv: self._on_label_visibility_changed(v, state == Qt.Checked)
        )
        h.addWidget(cb)
        row_w.mousePressEvent = lambda e, v=lv: self._on_label_row_clicked(v)
        self._label_rows[lv] = (row_w, cb)
        return row_w

    def _highlight_row(self, lv):
        for v, (row_w, _) in self._label_rows.items():
            if v == lv:
                row_w.setStyleSheet(
                    "QWidget{background:#1a3a5c;border-radius:3px;"
                    "border:1px solid #5bc8f5;}"
                )
            else:
                row_w.setStyleSheet(
                    "QWidget{background:transparent;border-radius:3px;}"
                    "QWidget:hover{background:#2a2a2a;}"
                )

    def _on_label_row_clicked(self, lv):
        """点击标签行：选中该标签，只显示该标签"""
        self._select_label(lv)
        self._highlight_row(lv)
        self._visible_labels = {lv}
        for v, (_, cb) in self._label_rows.items():
            cb.blockSignals(True)
            cb.setChecked(v == lv)
            cb.blockSignals(False)
        self._refresh_edit()

    def _on_label_visibility_changed(self, lv, visible):
        if self._visible_labels is None:
            self._visible_labels = set(self._label_rows.keys())
        if visible:
            self._visible_labels.add(lv)
        else:
            self._visible_labels.discard(lv)
        if self._visible_labels == set(self._label_rows.keys()):
            self._visible_labels = None
        self._refresh_edit()

    def _on_show_all_labels(self):
        self._visible_labels = None
        for _, (_, cb) in self._label_rows.items():
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
        self._refresh_edit()

    def _on_hide_all_labels(self):
        self._visible_labels = set()
        for _, (_, cb) in self._label_rows.items():
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
        self._refresh_edit()

    def _on_clear_seg(self):
        """清除分割叠加，需要重新导入"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认清除",
            "清除后分割叠加将消失，需要重新导入分割掩码。\n确认清除？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return
        self.editor.seg_data = None
        self.editor.history_stack = []
        self.editor.history_index = -1
        self._visible_labels = None
        self._label_rows.clear()
        while self._label_list_layout.count() > 1:
            item = self._label_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.lbl_current_label.setText("编辑: 标签 1")
        self.lbl_seg_status.setText("未加载")
        self.lbl_seg_status.setStyleSheet(_STATUS_NONE)
        self._set_edit_tools_enabled(False)
        self._set_orient_enabled(False)
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
        if self.editor.orig_data is None:
            return
        d = self.editor.orig_data.shape[2]
        new_val = max(0, min(self.editor.current_slice + step, d - 1))
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
