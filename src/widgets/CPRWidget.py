# -*- coding: utf-8 -*-
"""
多曲面重建（CPR）主界面

左侧：横截面标注视图（轴状切片 + 控制点标注）
右侧：CPR 结果视图
  - 叠加模式：整张 CPR 图（Z × N_curve），支持亮度/对比度调节
  - 切片模式：滑块切换厚度方向（法向量方向）的 CPR 切片
"""

import os
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter

_BG      = "#1e1e2f"
_PANEL   = "#282838"
_TOOLBAR = "#2d2d44"
_BORDER  = "#444444"
_TEXT    = "#f0f0f0"
_DIM     = "#b0b0b0"

_BTN_STYLE = (
    "QPushButton{background:#3a3a58;color:#f0f0f0;border:none;"
    "border-radius:4px;padding:5px 10px;font-size:12px;}"
    "QPushButton:hover{background:#4a4a78;}"
    "QPushButton:checked{background:#0099ff;color:white;}"
    "QPushButton:disabled{background:#2a2a2a;color:#666;}"
)
_COMBO_STYLE = (
    "QComboBox{background:#3a3a58;border:1px solid #555;color:#f0f0f0;"
    "padding:3px 6px;border-radius:3px;font-size:12px;}"
    "QComboBox::drop-down{border:none;}"
    "QComboBox QAbstractItemView{background:#3a3a58;color:#f0f0f0;"
    "selection-background-color:#0099ff;}"
)
_SLIDER_STYLE = (
    "QSlider::groove:horizontal{height:4px;background:#444;border-radius:2px;}"
    "QSlider::handle:horizontal{width:12px;height:12px;margin:-4px 0;"
    "background:#0099ff;border-radius:6px;}"
    "QSlider::sub-page:horizontal{background:#0099ff;border-radius:2px;}"
)
_SPIN_STYLE = (
    "QSpinBox{background:#3a3a58;color:#f0f0f0;border:1px solid #555;"
    "border-radius:3px;padding:2px 4px;}"
)


# ══════════════════════════════════════════════════════════════════════════════
# 可交互图像视图（缩放/平移/标注/滚轮切片）
# ══════════════════════════════════════════════════════════════════════════════
class AnnotationView(QtWidgets.QWidget):
    slice_changed = pyqtSignal(int)           # 滚轮切片 +1/-1（无 Ctrl）
    point_added   = pyqtSignal(float, float)  # 图像坐标 (x, y)

    def __init__(self, parent=None):
        super(AnnotationView, self).__init__(parent)
        self._pixmap     = None
        self._zoom       = 1.0
        self._offset     = QPoint(0, 0)
        self._drag_pos   = None
        self._annot_mode = False
        self.setStyleSheet("background:#000;border:2px solid #5bc8f5;border-radius:4px;")
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def set_annot_mode(self, enabled):
        self._annot_mode = enabled
        self.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)

    def reset_view(self):
        self._zoom = 1.0
        self._offset = QPoint(0, 0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)
        if self._pixmap and not self._pixmap.isNull():
            w, h = self.width(), self.height()
            pw, ph = self._pixmap.width(), self._pixmap.height()
            base = min(w / pw, h / ph)
            scale = base * self._zoom
            dw, dh = int(pw * scale), int(ph * scale)
            x = (w - dw) // 2 + self._offset.x()
            y = (h - dh) // 2 + self._offset.y()
            painter.drawPixmap(x, y, dw, dh, self._pixmap)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if event.modifiers() & Qt.ControlModifier:
            # Ctrl+滚轮：缩放
            factor = 1.15 if delta > 0 else 1.0 / 1.15
            self._zoom = max(0.1, min(self._zoom * factor, 30.0))
            self.update()
        else:
            # 普通滚轮：切片切换，步长1
            self.slice_changed.emit(1 if delta < 0 else -1)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._drag_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton and self._annot_mode:
            coords = self._to_image(event.pos())
            if coords:
                self.point_added.emit(coords[0], coords[1])

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self._offset += event.pos() - self._drag_pos
            self._drag_pos = event.pos()
            self.update()
        elif event.buttons() & Qt.LeftButton and self._annot_mode:
            coords = self._to_image(event.pos())
            if coords:
                self.point_added.emit(coords[0], coords[1])

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._drag_pos = None
            self.setCursor(Qt.CrossCursor if self._annot_mode else Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self.reset_view()

    def _to_image(self, pos):
        if not self._pixmap or self._pixmap.isNull():
            return None
        w, h = self.width(), self.height()
        pw, ph = self._pixmap.width(), self._pixmap.height()
        base = min(w / pw, h / ph)
        scale = base * self._zoom
        dw, dh = int(pw * scale), int(ph * scale)
        x0 = (w - dw) // 2 + self._offset.x()
        y0 = (h - dh) // 2 + self._offset.y()
        ax = pos.x() - x0
        ay = pos.y() - y0
        if 0 <= ax < dw and 0 <= ay < dh:
            return ax / dw * pw, ay / dh * ph
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 主 CPR 界面
# ══════════════════════════════════════════════════════════════════════════════
class CPRWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(CPRWidget, self).__init__(parent)
        self.setWindowTitle("多曲面重建（CPR）")
        self.setStyleSheet("background:%s;color:%s;" % (_BG, _TEXT))
        self.resize(1280, 800)

        self._volume        = None   # (H, W, D) float32
        self._spacing       = (1.0, 1.0, 1.0)
        self._current_z     = 0      # 左侧轴状切片索引
        self._path_points   = []     # [(x, y), ...] 2D 控制点
        self._cpr_image     = None   # (Z, N_curve) uint8，叠加模式
        self._cpr_volume    = None   # (T, Z, N_curve) uint8，切片模式
        self._cpr_slice_idx = 0      # 切片模式当前厚度层索引
        self._right_mode    = 0      # 0=叠加, 1=切片
        self._arch_width    = 80     # 记录当前生成时的厚度值，供滑块映射用
        # 叠加模式亮度/对比度（-100~100）
        self._brightness    = 0
        self._contrast      = 0

        self._init_ui()

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_toolbar())

        splitter = QtWidgets.QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle{background:%s;width:3px;}" % _BORDER)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([640, 640])
        root.addWidget(splitter, 1)

        root.addWidget(self._build_status_bar())

    def _build_toolbar(self):
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(50)
        bar.setStyleSheet("background:%s;border-bottom:1px solid %s;" % (_TOOLBAR, _BORDER))
        lay = QtWidgets.QHBoxLayout(bar)
        lay.setContentsMargins(12, 4, 12, 4)
        lay.setSpacing(6)

        self.btn_open = self._mk_btn("打开数据")
        self.btn_open.clicked.connect(self._on_open_data)
        lay.addWidget(self.btn_open)
        lay.addWidget(self._sep())

        self.btn_point = self._mk_btn("点标注", checkable=True)
        self.btn_point.clicked.connect(self._on_toggle_annot)
        self.btn_clear = self._mk_btn("清除路径")
        self.btn_clear.clicked.connect(self._on_clear_path)
        lay.addWidget(self.btn_point)
        lay.addWidget(self.btn_clear)
        lay.addWidget(self._sep())

        self.btn_save = self._mk_btn("保存标注")
        self.btn_save.clicked.connect(self._on_save_annotation)
        lay.addWidget(self.btn_save)
        lay.addWidget(self._sep())

        self.btn_gen = self._mk_btn("生成CPR")
        self.btn_gen.clicked.connect(self._on_generate_cpr)
        self.btn_gen.setEnabled(False)
        lay.addWidget(self.btn_gen)
        lay.addWidget(self._sep())

        # 采样步长
        lay.addWidget(self._mk_lbl("采样步长:"))
        self.spin_samples = QtWidgets.QSpinBox()
        self.spin_samples.setRange(100, 2000)
        self.spin_samples.setValue(800)
        self.spin_samples.setSingleStep(100)
        self.spin_samples.setFixedWidth(65)
        self.spin_samples.setStyleSheet(_SPIN_STYLE)
        lay.addWidget(self.spin_samples)
        lay.addWidget(self._sep())

        # 厚度设置（替代原"平滑"，直接设置 arch_width 像素值，上限由图像 H 决定）
        lay.addWidget(self._mk_lbl("厚度(px):"))
        self.spin_thickness = QtWidgets.QSpinBox()
        self.spin_thickness.setRange(4, 512)   # 上限在加载数据后动态更新为图像 H
        self.spin_thickness.setValue(80)
        self.spin_thickness.setSingleStep(1)
        self.spin_thickness.setFixedWidth(60)
        self.spin_thickness.setStyleSheet(_SPIN_STYLE)
        lay.addWidget(self.spin_thickness)
        lay.addWidget(self._sep())

        # 亮度（叠加模式有效）
        lay.addWidget(self._mk_lbl("亮度:"))
        self.slider_brightness = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(-100, 100)
        self.slider_brightness.setValue(0)
        self.slider_brightness.setSingleStep(1)
        self.slider_brightness.setFixedWidth(80)
        self.slider_brightness.setStyleSheet(_SLIDER_STYLE)
        self.lbl_brightness = QtWidgets.QLabel("0")
        self.lbl_brightness.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        self.lbl_brightness.setFixedWidth(28)
        self.slider_brightness.valueChanged.connect(self._on_brightness_changed)
        lay.addWidget(self.slider_brightness)
        lay.addWidget(self.lbl_brightness)

        # 对比度
        lay.addWidget(self._mk_lbl("对比度:"))
        self.slider_contrast = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(-100, 100)
        self.slider_contrast.setValue(0)
        self.slider_contrast.setSingleStep(1)
        self.slider_contrast.setFixedWidth(80)
        self.slider_contrast.setStyleSheet(_SLIDER_STYLE)
        self.lbl_contrast = QtWidgets.QLabel("0")
        self.lbl_contrast.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        self.lbl_contrast.setFixedWidth(28)
        self.slider_contrast.valueChanged.connect(self._on_contrast_changed)
        lay.addWidget(self.slider_contrast)
        lay.addWidget(self.lbl_contrast)

        lay.addStretch()

        self.btn_export = self._mk_btn("导出CPR")
        self.btn_export.clicked.connect(self._on_export_cpr)
        self.btn_export.setEnabled(False)
        lay.addWidget(self.btn_export)
        return bar

    def _build_left_panel(self):
        panel = QtWidgets.QWidget()
        panel.setStyleSheet("background:%s;" % _PANEL)
        lay = QtWidgets.QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QtWidgets.QWidget()
        hdr.setFixedHeight(36)
        hdr.setStyleSheet("background:%s;border-bottom:1px solid %s;" % (_TOOLBAR, _BORDER))
        hl = QtWidgets.QHBoxLayout(hdr)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.addWidget(self._mk_lbl("横截面标注视图", bold=True))
        hl.addStretch()
        self.lbl_left_info = QtWidgets.QLabel("切片: 0 / 0")
        self.lbl_left_info.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        hl.addWidget(self.lbl_left_info)
        lay.addWidget(hdr)

        self.left_view = AnnotationView()
        self.left_view.slice_changed.connect(self._on_left_scroll)
        self.left_view.point_added.connect(self._on_point_added)
        lay.addWidget(self.left_view, 1)

        # 底部：路径点数 + 切片滑块（步长1，宽度自适应）
        ftr = QtWidgets.QWidget()
        ftr.setFixedHeight(36)
        ftr.setStyleSheet("background:%s;border-top:1px solid %s;" % (_TOOLBAR, _BORDER))
        fl = QtWidgets.QHBoxLayout(ftr)
        fl.setContentsMargins(10, 4, 10, 4)
        fl.setSpacing(8)
        self.lbl_path_count = QtWidgets.QLabel("路径点: 0")
        self.lbl_path_count.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        fl.addWidget(self.lbl_path_count)
        self.slider_left = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_left.setRange(0, 0)
        self.slider_left.setSingleStep(1)
        self.slider_left.setPageStep(10)
        self.slider_left.setStyleSheet(_SLIDER_STYLE)
        self.slider_left.valueChanged.connect(self._on_left_slider)
        self.lbl_left_slice = QtWidgets.QLabel("0 / 0")
        self.lbl_left_slice.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        self.lbl_left_slice.setFixedWidth(55)
        fl.addWidget(self.slider_left, 1)
        fl.addWidget(self.lbl_left_slice)
        lay.addWidget(ftr)
        return panel

    def _build_right_panel(self):
        panel = QtWidgets.QWidget()
        panel.setStyleSheet("background:%s;" % _PANEL)
        lay = QtWidgets.QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QtWidgets.QWidget()
        hdr.setFixedHeight(36)
        hdr.setStyleSheet("background:%s;border-bottom:1px solid %s;" % (_TOOLBAR, _BORDER))
        hl = QtWidgets.QHBoxLayout(hdr)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.addWidget(self._mk_lbl("CPR 曲面重建", bold=True))
        hl.addStretch()
        self.combo_cpr_mode = QtWidgets.QComboBox()
        self.combo_cpr_mode.addItems(["叠加模式（全景）", "切片模式（三维）"])
        self.combo_cpr_mode.setFixedWidth(150)
        self.combo_cpr_mode.setStyleSheet(_COMBO_STYLE)
        self.combo_cpr_mode.currentIndexChanged.connect(self._on_cpr_mode_changed)
        hl.addWidget(self.combo_cpr_mode)
        lay.addWidget(hdr)

        self.right_view = AnnotationView()
        # 右侧滚轮：切片模式下切换厚度层
        self.right_view.slice_changed.connect(self._on_right_scroll)
        lay.addWidget(self.right_view, 1)

        # 底部：模式提示 + 切片滑块（步长1，宽度自适应）
        ftr = QtWidgets.QWidget()
        ftr.setFixedHeight(36)
        ftr.setStyleSheet("background:%s;border-top:1px solid %s;" % (_TOOLBAR, _BORDER))
        fl = QtWidgets.QHBoxLayout(ftr)
        fl.setContentsMargins(10, 4, 10, 4)
        fl.setSpacing(8)
        self.lbl_cpr_hint = QtWidgets.QLabel("叠加模式")
        self.lbl_cpr_hint.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        fl.addWidget(self.lbl_cpr_hint)
        self.slider_cpr = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_cpr.setRange(0, 0)
        self.slider_cpr.setSingleStep(1)
        self.slider_cpr.setPageStep(1)
        self.slider_cpr.setStyleSheet(_SLIDER_STYLE)
        self.slider_cpr.valueChanged.connect(self._on_cpr_slider)
        self.slider_cpr.setVisible(False)
        self.lbl_cpr_slice = QtWidgets.QLabel("0 / 0")
        self.lbl_cpr_slice.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        self.lbl_cpr_slice.setFixedWidth(55)
        self.lbl_cpr_slice.setVisible(False)
        fl.addWidget(self.slider_cpr, 1)
        fl.addWidget(self.lbl_cpr_slice)
        lay.addWidget(ftr)
        return panel

    def _build_status_bar(self):
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet("background:%s;border-top:1px solid %s;" % (_TOOLBAR, _BORDER))
        lay = QtWidgets.QHBoxLayout(bar)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(24)
        self.lbl_data_path = QtWidgets.QLabel("数据路径: 未加载")
        self.lbl_data_path.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        self.lbl_annot_info = QtWidgets.QLabel("标注点数: 0 | CPR状态: 未生成")
        self.lbl_annot_info.setStyleSheet("color:%s;font-size:12px;" % _DIM)
        lay.addWidget(self.lbl_data_path, 2)
        lay.addWidget(self.lbl_annot_info, 2)
        lay.addStretch()
        return bar

    # ── 数据加载 ──────────────────────────────────────────────────────────────

    def set_volume(self, volume, spacing=(1.0, 1.0, 1.0), path=""):
        self._volume = volume.astype(np.float32)
        self._spacing = spacing
        H, W, D = volume.shape
        self._current_z = D // 2
        # 厚度上限 = 图像 H（Y轴像素数）
        self.spin_thickness.setMaximum(H)
        self.spin_thickness.setValue(min(80, H))
        # 左侧滑块
        self.slider_left.setRange(0, D - 1)
        self.slider_left.setValue(D // 2)
        self.lbl_left_slice.setText("%d / %d" % (D // 2, D - 1))
        self._path_points = []
        self._cpr_image = None
        self._cpr_volume = None
        self.btn_gen.setEnabled(False)
        self.btn_export.setEnabled(False)
        if path:
            self.lbl_data_path.setText("数据路径: %s" % os.path.basename(path))
        self._refresh_left()
        self._refresh_right()

    def _on_open_data(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "打开影像文件", "",
            "所有支持格式 (*.nii *.nii.gz *.npy *.dcm *.mha *.mhd *.hdr);;"
            "NIfTI (*.nii *.nii.gz);;DICOM (*.dcm);;NumPy (*.npy);;"
            "MetaImage (*.mha *.mhd);;Analyze (*.hdr);;所有文件 (*)"
        )
        if not path:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "或选择 DICOM 目录")
        if not path:
            return
        try:
            from src.utils.image_loader import load_image
            volume, spacing = load_image(path)
            self.set_volume(volume, spacing, path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "加载失败", str(e))

    # ── 标注 ──────────────────────────────────────────────────────────────────

    def _on_toggle_annot(self, checked):
        self.left_view.set_annot_mode(checked)

    def _on_point_added(self, x, y):
        if self._volume is None:
            return
        self._path_points.append((x, y))
        n = len(self._path_points)
        self.lbl_path_count.setText("路径点: %d" % n)
        if n >= 2:
            self.btn_gen.setEnabled(True)
        self._refresh_left()
        self._update_annot_info()

    def _on_clear_path(self):
        self._path_points = []
        self._cpr_image = None
        self._cpr_volume = None
        self.btn_gen.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.lbl_path_count.setText("路径点: 0")
        self.slider_cpr.setRange(0, 0)
        self.lbl_cpr_slice.setText("0 / 0 px")
        self._refresh_left()
        self._refresh_right()
        self._update_annot_info()

    def _on_save_annotation(self):
        if not self._path_points:
            QtWidgets.QMessageBox.information(self, "提示", "没有标注点可保存")
            return
        import json
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存标注", "", "JSON (*.json)")
        if not save_path:
            return
        with open(save_path, "w") as f:
            json.dump({"path_points": self._path_points}, f)
        QtWidgets.QMessageBox.information(self, "成功", "标注已保存至 %s" % save_path)

    # ── 左侧切片控制（滚轮 + 滑块同步，步长1）────────────────────────────────

    def _on_left_scroll(self, step):
        """鼠标滚轮触发，步长1，同步滑块"""
        if self._volume is None:
            return
        D = self._volume.shape[2]
        self._current_z = max(0, min(self._current_z + step, D - 1))
        self.slider_left.blockSignals(True)
        self.slider_left.setValue(self._current_z)
        self.slider_left.blockSignals(False)
        self.lbl_left_slice.setText("%d / %d" % (self._current_z, D - 1))
        self._refresh_left()

    def _on_left_slider(self, value):
        """滑块拖动，步长1"""
        self._current_z = value
        if self._volume is not None:
            D = self._volume.shape[2]
            self.lbl_left_slice.setText("%d / %d" % (value, D - 1))
        self._refresh_left()

    # ── 右侧切片控制（滚轮 + 滑块同步，步长1）────────────────────────────────

    def _on_right_scroll(self, step):
        """切片模式下鼠标滚轮切换厚度层，步长1（像素），同步滑块"""
        if self._right_mode != 1 or self._cpr_volume is None:
            return
        cur = self.slider_cpr.value()
        nxt = max(0, min(cur + step, self._arch_width - 1))
        self.slider_cpr.blockSignals(True)
        self.slider_cpr.setValue(nxt)
        self.slider_cpr.blockSignals(False)
        self.lbl_cpr_slice.setText("%d / %d px" % (nxt, self._arch_width - 1))
        self._cpr_slice_idx = self._px_to_layer(nxt)
        self._refresh_right()

    def _on_cpr_slider(self, value):
        """滑块拖动，value 为像素厚度值，映射到层索引"""
        self.lbl_cpr_slice.setText("%d / %d px" % (value, self._arch_width - 1))
        self._cpr_slice_idx = self._px_to_layer(value)
        self._refresh_right()

    def _px_to_layer(self, px_value):
        """将像素厚度值（0~arch_width-1）映射到 _cpr_volume 的层索引（0~T-1）"""
        if self._cpr_volume is None:
            return 0
        T = self._cpr_volume.shape[0]
        if self._arch_width <= 1:
            return 0
        return int(round(px_value * (T - 1) / (self._arch_width - 1)))

    # ── 亮度/对比度 ───────────────────────────────────────────────────────────

    def _on_brightness_changed(self, value):
        self._brightness = value
        self.lbl_brightness.setText(str(value))
        self._refresh_right()

    def _on_contrast_changed(self, value):
        self._contrast = value
        self.lbl_contrast.setText(str(value))
        self._refresh_right()

    def _apply_bc(self, arr_u8):
        """对 uint8 图像应用亮度/对比度调节，返回 uint8"""
        if self._brightness == 0 and self._contrast == 0:
            return arr_u8
        img = arr_u8.astype(np.float32)
        # 对比度：以128为中心缩放
        if self._contrast != 0:
            factor = (259.0 * (self._contrast + 255)) / (255.0 * (259 - self._contrast))
            img = factor * (img - 128.0) + 128.0
        # 亮度：直接偏移
        img = img + self._brightness
        return np.clip(img, 0, 255).astype(np.uint8)

    # ── 模式切换 ──────────────────────────────────────────────────────────────

    def _on_cpr_mode_changed(self, idx):
        self._right_mode = idx
        is_slice = (idx == 1)
        self.slider_cpr.setVisible(is_slice)
        self.lbl_cpr_slice.setVisible(is_slice)
        # 亮度/对比度仅叠加模式有意义（切片模式也可用，不做限制）
        self.lbl_cpr_hint.setText("切片模式：滚轮/滑块切换厚度层" if is_slice else "叠加模式：均值投影全景图")
        self._refresh_right()

    # ── CPR 生成 ──────────────────────────────────────────────────────────────

    def _on_generate_cpr(self):
        if self._volume is None or len(self._path_points) < 2:
            QtWidgets.QMessageBox.warning(self, "提示", "请先加载数据并标注至少2个路径点")
            return
        try:
            from src.core.cpr_engine import generate_cpr
            control_pts = np.array(self._path_points, dtype=np.float64)
            arch_width = self.spin_thickness.value()  # 直接使用像素厚度值
            normal_samples_num = 40

            self._cpr_image, self._cpr_volume = generate_cpr(
                self._volume, control_pts,
                sample_points_num=self.spin_samples.value(),
                arch_width=arch_width,
                normal_samples_num=normal_samples_num,
            )

            T = self._cpr_volume.shape[0]
            self._arch_width = arch_width
            self.btn_export.setEnabled(True)

            # 切片模式滑块：范围 0 ~ arch_width-1（真实厚度像素值），步长1
            # 滑块值通过线性映射转换为层索引
            self._cpr_slice_idx = T // 2
            self.slider_cpr.setRange(0, arch_width - 1)
            self.slider_cpr.setSingleStep(1)
            self.slider_cpr.setValue(arch_width // 2)
            self.lbl_cpr_slice.setText("%d / %d px" % (arch_width // 2, arch_width - 1))

            self._update_annot_info()
            self._refresh_right()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "CPR生成失败", str(e))

    def _on_export_cpr(self):
        if self._cpr_image is None:
            return
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "导出CPR图像", "cpr_result", "PNG (*.png);;TIFF (*.tiff);;所有格式 (*)"
        )
        if not save_path:
            return
        img = self._apply_bc(self._cpr_image)
        try:
            from PIL import Image
            Image.fromarray(img).save(save_path)
        except ImportError:
            Z, N = img.shape
            qimg = QImage(img.tobytes(), N, Z, N, QImage.Format_Grayscale8)
            qimg.save(save_path)
        QtWidgets.QMessageBox.information(self, "成功", "CPR图像已导出至 %s" % save_path)

    # ── 视图刷新 ──────────────────────────────────────────────────────────────

    def _refresh_left(self):
        if self._volume is None:
            return
        H, W, D = self._volume.shape
        z = max(0, min(self._current_z, D - 1))
        sl = self._volume[:, :, z]
        lo, hi = sl.min(), sl.max()
        norm = ((sl - lo) / (hi - lo + 1e-8) * 255).astype(np.uint8)
        rgb = np.stack([norm, norm, norm], axis=2)

        # 绘制控制点（黄色方块）
        for px, py in self._path_points:
            xi, yi = int(px), int(py)
            for ddy in range(-3, 4):
                for ddx in range(-3, 4):
                    nx2, ny2 = xi + ddx, yi + ddy
                    if 0 <= ny2 < H and 0 <= nx2 < W:
                        rgb[ny2, nx2] = [255, 220, 0]

        # 绘制控制点连线
        if len(self._path_points) >= 2:
            for i in range(len(self._path_points) - 1):
                x1, y1 = int(self._path_points[i][0]), int(self._path_points[i][1])
                x2, y2 = int(self._path_points[i + 1][0]), int(self._path_points[i + 1][1])
                steps = max(abs(x2 - x1), abs(y2 - y1), 1)
                for t in range(steps + 1):
                    lx = int(x1 + (x2 - x1) * t / steps)
                    ly = int(y1 + (y2 - y1) * t / steps)
                    if 0 <= ly < H and 0 <= lx < W:
                        rgb[ly, lx] = [255, 220, 0]

        raw = np.ascontiguousarray(rgb)
        qimg = QImage(raw.data, W, H, W * 3, QImage.Format_RGB888).copy()
        self.left_view.set_pixmap(QPixmap.fromImage(qimg))
        self.lbl_left_info.setText("切片: %d / %d" % (z, D - 1))

    def _refresh_right(self):
        if self._cpr_image is None:
            self.right_view.set_pixmap(None)
            return

        if self._right_mode == 0:
            # 叠加模式：整张 CPR 图 (Z, N_curve)，应用亮度/对比度
            img = self._apply_bc(self._cpr_image)
            Z, N = img.shape
            raw = np.ascontiguousarray(img)
            qimg = QImage(raw.data, N, Z, N, QImage.Format_Grayscale8).copy()
            self.right_view.set_pixmap(QPixmap.fromImage(qimg))
        else:
            # 切片模式：_cpr_volume (T, Z, N_curve)，滑块切换 T（厚度层）
            if self._cpr_volume is None:
                return
            T, Z, N = self._cpr_volume.shape
            idx = max(0, min(self._cpr_slice_idx, T - 1))
            frame = self._cpr_volume[idx]  # (Z, N_curve)
            raw = np.ascontiguousarray(frame)
            qimg = QImage(raw.data, N, Z, N, QImage.Format_Grayscale8).copy()
            self.right_view.set_pixmap(QPixmap.fromImage(qimg))

    def _update_annot_info(self):
        n = len(self._path_points)
        if self._cpr_image is not None:
            Z, N = self._cpr_image.shape
            state = "已生成 (%dx%d)" % (N, Z)
        else:
            state = "未生成"
        self.lbl_annot_info.setText("标注点数: %d | CPR状态: %s" % (n, state))

    # ── 辅助 ──────────────────────────────────────────────────────────────────

    def _mk_btn(self, text, checkable=False):
        btn = QtWidgets.QPushButton(text)
        btn.setCheckable(checkable)
        btn.setStyleSheet(_BTN_STYLE)
        return btn

    def _mk_lbl(self, text, bold=False):
        lbl = QtWidgets.QLabel(text)
        style = "color:%s;font-size:12px;" % _TEXT
        if bold:
            style += "font-weight:bold;"
        lbl.setStyleSheet(style)
        return lbl

    def _sep(self):
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.VLine)
        sep.setStyleSheet("color:%s;" % _BORDER)
        return sep
