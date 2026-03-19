# -*- coding: utf-8 -*-
"""
口腔牙齿分割结果定量测量面板（完整版）

Tab 布局：
  [ 测量结果 ] [ 三视图 ] [ 三维视图 ]

左侧：通用牙位标签列表（带颜色色块 + 显隐复选框）
右侧：Tab 内容区
  - 测量结果：表格 + 异常提示 + 详情
  - 三视图：轴/矢/冠 原始+分割叠加，点标签高亮
  - 三维视图：STL 多文件加载，FDI 颜色，显隐控制
"""

import os
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, pyqtSignal

# ── 样式常量 ──────────────────────────────────────────────────────────────────
_BG       = "#1e1e1e"
_PANEL    = "#252525"
_TOOLBAR  = "#2d2d2d"
_BORDER   = "#3a3a3a"
_ACCENT   = "#5bc8f5"
_TEXT     = "#dddddd"
_TEXT_DIM = "#888888"
_WARN     = "#f5a623"
_OK       = "#7ed321"
_HEADER_STYLE = f"color:{_ACCENT};font-size:13px;font-weight:bold;"

# ── FDI 颜色表（参考临床牙科标注配色）────────────────────────────────────────
# 右上(11-18)暖红，左上(21-28)暖橙，左下(31-38)冷蓝，右下(41-48)冷绿
FDI_COLORS = {
    11: "#FF6B6B", 12: "#FF8E8E", 13: "#FF5252", 14: "#E53935",
    15: "#EF5350", 16: "#F44336", 17: "#D32F2F", 18: "#C62828",
    21: "#FFA726", 22: "#FFB74D", 23: "#FF9800", 24: "#FB8C00",
    25: "#F57C00", 26: "#EF6C00", 27: "#E65100", 28: "#BF360C",
    31: "#42A5F5", 32: "#64B5F6", 33: "#2196F3", 34: "#1E88E5",
    35: "#1976D2", 36: "#1565C0", 37: "#0D47A1", 38: "#0A3D91",
    41: "#66BB6A", 42: "#81C784", 43: "#4CAF50", 44: "#43A047",
    45: "#388E3C", 46: "#2E7D32", 47: "#1B5E20", 48: "#145214",
}

def fdi_color(fdi: int) -> QtGui.QColor:
    """返回 FDI 牙位对应的 QColor"""
    hex_c = FDI_COLORS.get(fdi, "#888888")
    return QtGui.QColor(hex_c)

def fdi_color_vtk(fdi: int):
    """返回 VTK 用的 (r,g,b) 0~1 浮点元组"""
    c = fdi_color(fdi)
    return c.redF(), c.greenF(), c.blueF()


# ══════════════════════════════════════════════════════════════════════════════
# 左侧通用标签列表（带颜色色块 + 显隐复选框）
# ══════════════════════════════════════════════════════════════════════════════
class LabelListWidget(QtWidgets.QWidget):
    """
    左侧牙位标签列表，每行：[色块] [FDI编号] [显隐复选框]
    信号：
      label_selected(fdi)         — 点击选中某颗牙
      label_visibility_changed(fdi, visible) — 复选框切换
    """
    label_selected          = pyqtSignal(int)
    label_visibility_changed = pyqtSignal(int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(170)
        self.setStyleSheet(f"background:{_PANEL};")
        self._fdi_rows = {}   # fdi -> (row_widget, checkbox)
        self._init_ui()

    def _init_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)

        lbl = QtWidgets.QLabel("牙位列表")
        lbl.setStyleSheet(_HEADER_STYLE)
        lay.addWidget(lbl)

        # 滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{_BG};border:1px solid {_BORDER};border-radius:3px;}}"
            f"QScrollBar:vertical{{background:{_PANEL};width:8px;}}"
            f"QScrollBar::handle:vertical{{background:{_BORDER};border-radius:4px;}}"
        )
        self._list_container = QtWidgets.QWidget()
        self._list_container.setStyleSheet(f"background:{_BG};")
        self._list_layout = QtWidgets.QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_container)
        lay.addWidget(scroll, 1)

        self.lbl_count = QtWidgets.QLabel("共 0 颗牙")
        self.lbl_count.setStyleSheet(f"color:{_TEXT_DIM};font-size:12px;")
        lay.addWidget(self.lbl_count)

    def populate(self, fdi_list: list, has_warn: dict = None):
        """填充牙位列表，has_warn: {fdi: bool}"""
        # 清空旧行
        self._fdi_rows.clear()
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        has_warn = has_warn or {}
        for fdi in sorted(fdi_list):
            row = self._make_row(fdi, has_warn.get(fdi, False))
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

        self.lbl_count.setText(f"共 {len(fdi_list)} 颗牙")

    def _make_row(self, fdi: int, warn: bool) -> QtWidgets.QWidget:
        """创建单行：色块 + 标签 + 复选框"""
        row_w = QtWidgets.QWidget()
        row_w.setFixedHeight(28)
        row_w.setCursor(Qt.PointingHandCursor)
        row_w.setStyleSheet(
            f"QWidget{{background:transparent;border-radius:3px;}}"
            f"QWidget:hover{{background:#2a2a2a;}}"
        )
        h = QtWidgets.QHBoxLayout(row_w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(6)

        # 色块
        color_dot = QtWidgets.QLabel()
        color_dot.setFixedSize(12, 12)
        c = fdi_color(fdi)
        color_dot.setStyleSheet(
            f"background:{c.name()};border-radius:6px;border:none;"
        )
        h.addWidget(color_dot)

        # 标签文字
        warn_prefix = "⚠ " if warn else ""
        lbl = QtWidgets.QLabel(f"{warn_prefix}FDI {fdi}")
        lbl.setStyleSheet(
            f"color:{'#f5a623' if warn else _TEXT};font-size:12px;background:transparent;"
        )
        h.addWidget(lbl, 1)

        # 显隐复选框（眼睛图标用 ✓）
        cb = QtWidgets.QCheckBox()
        cb.setChecked(True)
        cb.setStyleSheet(
            f"QCheckBox{{color:{_TEXT_DIM};font-size:11px;}}"
            f"QCheckBox::indicator{{width:14px;height:14px;}}"
        )
        cb.stateChanged.connect(lambda state, f=fdi: self.label_visibility_changed.emit(f, state == Qt.Checked))
        h.addWidget(cb)

        # 点击行选中
        row_w.mousePressEvent = lambda e, f=fdi: self.label_selected.emit(f)

        self._fdi_rows[fdi] = (row_w, cb)
        return row_w

    def highlight(self, fdi: int):
        """高亮选中行"""
        for f, (row_w, _) in self._fdi_rows.items():
            if f == fdi:
                row_w.setStyleSheet(
                    f"QWidget{{background:#1a3a5c;border-radius:3px;border:1px solid {_ACCENT};}}"
                )
            else:
                row_w.setStyleSheet(
                    f"QWidget{{background:transparent;border-radius:3px;}}"
                    f"QWidget:hover{{background:#2a2a2a;}}"
                )

    def clear(self):
        self._fdi_rows.clear()
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.lbl_count.setText("共 0 颗牙")


# ══════════════════════════════════════════════════════════════════════════════
# Tab1：测量结果面板
# ══════════════════════════════════════════════════════════════════════════════
class MeasurementResultTab(QtWidgets.QWidget):
    """测量结果表格 + 异常提示 + 详情"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = {}
        self._init_ui()

    def _init_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)

        # 表格区（比例2）
        lay.addWidget(self._build_table(), 2)

        # 下方：异常提示 + 详情（比例1）
        bottom = QtWidgets.QSplitter(Qt.Horizontal)
        bottom.setStyleSheet(f"QSplitter::handle{{background:{_BORDER};}}")
        bottom.addWidget(self._build_warning_panel())
        bottom.addWidget(self._build_detail_panel())
        bottom.setSizes([500, 500])
        lay.addWidget(bottom, 1)

    def _build_table(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(f"background:{_PANEL};border-radius:4px;")
        lay = QtWidgets.QVBoxLayout(frame)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(4)

        lay.addWidget(self._mk_header("测量结果总表"))

        headers = ["牙位", "牙体长度(mm)", "牙冠长度(mm)", "牙根长度(mm)",
                   "近远中宽(mm)", "颊舌厚(mm)", "倾斜角(°)", "体积(mm³)", "状态"]
        self.table = QtWidgets.QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setStyleSheet(
            f"QTableWidget{{background:{_BG};color:{_TEXT};gridline-color:{_BORDER};"
            f"border:1px solid {_BORDER};border-radius:3px;font-size:12px;}}"
            f"QHeaderView::section{{background:{_TOOLBAR};color:{_ACCENT};"
            f"border:1px solid {_BORDER};padding:4px;font-size:12px;}}"
            f"QTableWidget::item{{padding:3px 6px;}}"
            f"QTableWidget::item:selected{{background:#1a3a5c;}}"
            f"QTableWidget{{alternate-background-color:#222;}}"
        )
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        lay.addWidget(self.table, 1)
        return frame

    def _build_warning_panel(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(f"background:{_PANEL};border-radius:4px;")
        lay = QtWidgets.QVBoxLayout(frame)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(4)
        lay.addWidget(self._mk_header("⚠ 异常诊断提示", color=_WARN))
        self.warning_text = QtWidgets.QTextEdit()
        self.warning_text.setReadOnly(True)
        self.warning_text.setStyleSheet(
            f"background:{_BG};color:{_WARN};border:1px solid {_BORDER};"
            f"border-radius:3px;font-size:12px;"
        )
        self.warning_text.setPlaceholderText("测量完成后显示异常提示...")
        lay.addWidget(self.warning_text, 1)
        return frame

    def _build_detail_panel(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(f"background:{_PANEL};border-radius:4px;")
        lay = QtWidgets.QVBoxLayout(frame)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(4)
        self.lbl_detail_title = QtWidgets.QLabel("选中牙位详情")
        self.lbl_detail_title.setStyleSheet(_HEADER_STYLE)
        lay.addWidget(self.lbl_detail_title)
        self.detail_text = QtWidgets.QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet(
            f"background:{_BG};color:{_TEXT};border:1px solid {_BORDER};"
            f"border-radius:3px;font-size:12px;"
        )
        self.detail_text.setPlaceholderText("点击左侧牙位或表格行查看详情...")
        lay.addWidget(self.detail_text, 1)
        return frame

    # ── 公开方法 ──────────────────────────────────────────────────────────────

    def populate(self, results: dict):
        self._results = results
        self.table.setRowCount(0)
        for fdi in sorted(results.keys()):
            m = results[fdi]
            row = self.table.rowCount()
            self.table.insertRow(row)
            has_warn = len(m.warnings) > 0
            values = [
                str(fdi),
                f"{m.total_length:.1f}", f"{m.crown_length:.1f}", f"{m.root_length:.1f}",
                f"{m.md_width:.1f}", f"{m.bl_thickness:.1f}",
                f"{m.angulation:.1f}°", f"{m.volume:.0f}",
                "⚠ 异常" if has_warn else "✓ 正常",
            ]
            for col, val in enumerate(values):
                item = QtWidgets.QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, fdi)
                # 用 FDI 颜色标记牙位列
                if col == 0:
                    item.setForeground(fdi_color(fdi))
                elif has_warn:
                    item.setForeground(QtGui.QColor(_WARN))
                elif col == len(values) - 1:
                    item.setForeground(QtGui.QColor(_OK))
                self.table.setItem(row, col, item)

        # 汇总异常
        all_w = [f"FDI {fdi}：{w}" for fdi in sorted(results) for w in results[fdi].warnings]
        if all_w:
            self.warning_text.setHtml("<br>".join(f"• {w}" for w in all_w))
        else:
            self.warning_text.setPlainText("✓ 未发现明显异常")

    def show_fdi(self, fdi: int):
        """高亮并显示指定牙位详情"""
        self._sync_table(fdi)
        self._show_detail(fdi)

    def clear(self):
        self._results = {}
        self.table.setRowCount(0)
        self.warning_text.clear()
        self.detail_text.clear()
        self.lbl_detail_title.setText("选中牙位详情")

    # ── 内部 ──────────────────────────────────────────────────────────────────

    def _on_table_selection_changed(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item:
            fdi = item.data(Qt.UserRole)
            if fdi:
                self._show_detail(fdi)

    def _sync_table(self, fdi: int):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == fdi:
                self.table.blockSignals(True)
                self.table.selectRow(row)
                self.table.blockSignals(False)
                break

    def _show_detail(self, fdi: int):
        if fdi not in self._results:
            return
        m = self._results[fdi]
        self.lbl_detail_title.setText(f"FDI {fdi} 详情")
        c = fdi_color(fdi).name()
        lines = [
            f"<b style='color:{c}'>FDI {fdi} 测量详情</b>",
            f"<hr style='border-color:{_BORDER};'>",
            f"牙体总长度：<b>{m.total_length:.2f} mm</b>",
            f"牙冠长度：<b>{m.crown_length:.2f} mm</b>",
            f"牙根长度：<b>{m.root_length:.2f} mm</b>",
            f"冠根比：<b>{(m.crown_length/m.root_length):.2f}</b>" if m.root_length > 0 else "冠根比：N/A",
            f"近远中宽度：<b>{m.md_width:.2f} mm</b>",
            f"颊舌向厚度：<b>{m.bl_thickness:.2f} mm</b>",
            f"倾斜角度：<b>{m.angulation:.1f}°</b>",
            f"牙齿体积：<b>{m.volume:.1f} mm³</b>",
        ]
        if m.warnings:
            lines += [f"<hr style='border-color:{_BORDER};'>",
                      f"<b style='color:{_WARN}'>⚠ 异常提示</b>"]
            lines += [f"<span style='color:{_WARN}'>• {w}</span>" for w in m.warnings]
        self.detail_text.setHtml(
            f"<div style='color:{_TEXT};font-size:12px;line-height:1.8;'>"
            + "<br>".join(lines) + "</div>"
        )

    def _mk_header(self, text, color=_ACCENT):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(f"color:{color};font-size:13px;font-weight:bold;")
        return l


# ══════════════════════════════════════════════════════════════════════════════
# Tab2：三视图（原始 + 分割叠加）
# ══════════════════════════════════════════════════════════════════════════════
class TriViewTab(QtWidgets.QWidget):
    """
    轴状面 / 矢状面 / 冠状面 三视图，
    原始 DICOM 灰度 + NIfTI 分割掩码彩色叠加。
    点击标签只显示对应 label，其余透明。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image_data = None    # vtkImageData（原始）
        self._seg_data   = None    # numpy 3D 分割掩码
        self._spacing    = (1, 1, 1)
        self._active_fdi = None    # 当前高亮的 FDI（None=全显）
        self._slices     = [0, 0, 0]  # [axial_z, sagittal_x, coronal_y]
        self._init_ui()

    def _init_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)

        # 工具栏
        bar = QtWidgets.QWidget()
        bar.setStyleSheet(f"background:{_TOOLBAR};border-radius:4px;")
        bar_lay = QtWidgets.QHBoxLayout(bar)
        bar_lay.setContentsMargins(8, 4, 8, 4)
        bar_lay.setSpacing(8)
        bar_lay.addWidget(self._mk_lbl("显示："))
        self.combo_show = QtWidgets.QComboBox()
        self.combo_show.addItems(["全部牙齿", "仅选中牙位"])
        self.combo_show.setStyleSheet(self._combo_style())
        self.combo_show.currentIndexChanged.connect(self._refresh_views)
        bar_lay.addWidget(self.combo_show)
        bar_lay.addStretch()
        self.lbl_hint = QtWidgets.QLabel("请先加载 DICOM 和分割文件")
        self.lbl_hint.setStyleSheet(f"color:{_TEXT_DIM};font-size:12px;")
        bar_lay.addWidget(self.lbl_hint)
        lay.addWidget(bar)

        # 三个视图并排
        views_w = QtWidgets.QWidget()
        views_lay = QtWidgets.QHBoxLayout(views_w)
        views_lay.setContentsMargins(0, 0, 0, 0)
        views_lay.setSpacing(4)

        self._view_labels = []
        self._sliders = []
        for title in ["轴状面 (Axial)", "矢状面 (Sagittal)", "冠状面 (Coronal)"]:
            vw, lbl, slider = self._make_view_panel(title)
            views_lay.addWidget(vw, 1)
            self._view_labels.append(lbl)
            self._sliders.append(slider)

        lay.addWidget(views_w, 1)

    def _make_view_panel(self, title: str):
        """创建单个视图面板：标题 + 图像 + 滑块"""
        panel = QtWidgets.QFrame()
        panel.setStyleSheet(f"background:{_PANEL};border-radius:4px;")
        lay = QtWidgets.QVBoxLayout(panel)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        t = QtWidgets.QLabel(title)
        t.setStyleSheet(f"color:{_ACCENT};font-size:12px;font-weight:bold;")
        t.setAlignment(Qt.AlignCenter)
        lay.addWidget(t)

        img_lbl = QtWidgets.QLabel()
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet(f"background:#111;border-radius:2px;")
        img_lbl.setMinimumSize(200, 200)
        lay.addWidget(img_lbl, 1)

        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setStyleSheet(
            f"QSlider::groove:horizontal{{height:4px;background:{_BORDER};border-radius:2px;}}"
            f"QSlider::handle:horizontal{{width:12px;height:12px;margin:-4px 0;"
            f"background:{_ACCENT};border-radius:6px;}}"
            f"QSlider::sub-page:horizontal{{background:#2d7dd2;border-radius:2px;}}"
        )
        lay.addWidget(slider)

        return panel, img_lbl, slider

    # ── 公开方法 ──────────────────────────────────────────────────────────────

    def set_data(self, image_data, seg_data: np.ndarray, spacing: tuple):
        """设置原始图像和分割数据"""
        self._image_data = image_data
        self._seg_data   = seg_data
        self._spacing    = spacing
        dims = seg_data.shape  # (H, W, D)

        # 断开旧连接，重新绑定滑块
        for slider in self._sliders:
            try:
                slider.valueChanged.disconnect()
            except Exception:
                pass

        # 初始化滑块范围，中间切片
        ranges = [dims[2], dims[0], dims[1]]  # axial=z, sagittal=x, coronal=y
        for i, (slider, r) in enumerate(zip(self._sliders, ranges)):
            slider.blockSignals(True)
            slider.setRange(0, max(0, r - 1))
            slider.setValue(r // 2)
            slider.blockSignals(False)
            self._slices[i] = r // 2
            slider.valueChanged.connect(lambda v, idx=i: self._on_slider(idx, v))

        self.lbl_hint.setText(f"数据已加载  尺寸: {dims[0]}×{dims[1]}×{dims[2]}")
        # 延迟一帧等布局完成后再渲染
        QtCore.QTimer.singleShot(50, self._refresh_views)

    def set_active_fdi(self, fdi):
        """设置当前高亮牙位（None=全显）"""
        self._active_fdi = fdi
        if self.combo_show.currentIndex() == 1:
            self._refresh_views()

    def clear(self):
        self._image_data = None
        self._seg_data   = None
        self._active_fdi = None
        for lbl in self._view_labels:
            lbl.clear()
            lbl.setText("无数据")

    # ── 内部渲染 ──────────────────────────────────────────────────────────────

    def _on_slider(self, idx: int, value: int):
        self._slices[idx] = value
        self._render_view(idx)

    def _refresh_views(self):
        for i in range(3):
            self._render_view(i)

    def _render_view(self, idx: int):
        """渲染单个视图（纯 numpy，无 VTK 弹窗）"""
        if self._seg_data is None:
            return

        orientations = ["XY", "YZ", "XZ"]
        orient = orientations[idx]
        s = self._slices[idx]

        lbl_widget = self._view_labels[idx]
        w = lbl_widget.width()
        h = lbl_widget.height()
        # Tab 未显示时 width/height 可能为 0，用固定默认值
        if w < 10:
            w = 300
        if h < 10:
            h = 300
        sz = min(w, h)

        # 分割彩色叠加层（始终渲染）
        overlay_img = self._make_overlay(orient, s, sz)

        if self._image_data is not None:
            # 有原始图像：灰度底图 + 彩色叠加
            try:
                from src.widgets.MultiSliceViewWidget import render_slice_offscreen
                from src.model.ToolBarWidgetModel import ToolBarWidget
                try:
                    ww = float(ToolBarWidget.contrast_widget.window_width_slider.value())
                    wl = float(ToolBarWidget.contrast_widget.window_level_slider.value())
                except Exception:
                    ww, wl = 2000.0, 1000.0

                base_pixmap = render_slice_offscreen(self._image_data, orient, s, ww, wl, size=sz)
                base_img = base_pixmap.toImage().convertToFormat(QtGui.QImage.Format_RGB888)

                result = QtGui.QImage(base_img.size(), QtGui.QImage.Format_RGB888)
                painter = QtGui.QPainter(result)
                painter.drawImage(0, 0, base_img)
                painter.setOpacity(0.45)
                painter.drawImage(0, 0, overlay_img)
                painter.end()
                final_pixmap = QtGui.QPixmap.fromImage(result)
            except Exception:
                final_pixmap = QtGui.QPixmap.fromImage(overlay_img)
        else:
            # 无原始图像：黑色背景 + 彩色分割
            bg = QtGui.QImage(sz, sz, QtGui.QImage.Format_RGB888)
            bg.fill(QtGui.QColor("#111111"))
            painter = QtGui.QPainter(bg)
            painter.drawImage(0, 0, overlay_img)
            painter.end()
            final_pixmap = QtGui.QPixmap.fromImage(bg)

        lbl_widget.setPixmap(
            final_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _make_overlay(self, orient: str, s: int, sz: int) -> QtGui.QImage:
        """生成分割掩码的彩色叠加图像，返回 sz×sz 的 QImage"""
        seg = self._seg_data
        dims = seg.shape  # (H=row/y, W=col/x, D=slice/z)

        # 提取对应切片
        if orient == "XY":
            z = max(0, min(dims[2] - 1, s))
            arr = seg[:, :, z]               # (H, W)
        elif orient == "YZ":
            x = max(0, min(dims[0] - 1, s))
            arr = seg[x, :, :].T             # (D, W_y) → (z, y)
        else:  # XZ
            y = max(0, min(dims[1] - 1, s))
            arr = seg[:, y, :].T             # (D, H_x) → (z, x)

        H, W = arr.shape
        rgb = np.zeros((H, W, 3), dtype=np.uint8)

        # 确定要显示的 label 集合
        only_fdi = self._active_fdi if (self.combo_show.currentIndex() == 1 and self._active_fdi) else None

        from src.core.tooth_measurement import LABEL_TO_FDI
        for label_val, fdi in LABEL_TO_FDI.items():
            if only_fdi is not None and fdi != only_fdi:
                continue
            mask = (arr == label_val)
            if not np.any(mask):
                continue
            c = fdi_color(fdi)
            rgb[mask, 0] = c.red()
            rgb[mask, 1] = c.green()
            rgb[mask, 2] = c.blue()

        # numpy → QImage（必须 copy 防止内存被 GC）
        raw = rgb.tobytes()
        img = QtGui.QImage(raw, W, H, W * 3, QtGui.QImage.Format_RGB888).copy()

        # 缩放到目标尺寸
        pixmap = QtGui.QPixmap.fromImage(img)
        pixmap = pixmap.scaled(sz, sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pixmap.toImage()

    def _mk_lbl(self, text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(f"color:{_TEXT};font-size:13px;")
        return l

    def _combo_style(self):
        return (f"QComboBox{{background:#4a4a4a;color:#eee;border:1px solid #5a5a5a;"
                f"border-radius:3px;padding:2px 6px;font-size:13px;}}"
                f"QComboBox::drop-down{{border:none;}}"
                f"QComboBox QAbstractItemView{{background:#4a4a4a;color:#eee;"
                f"selection-background-color:#2d7dd2;}}")


# ══════════════════════════════════════════════════════════════════════════════
# Tab3：三维视图（STL 多文件 + FDI 颜色 + 显隐控制）
# ══════════════════════════════════════════════════════════════════════════════
class ThreeDViewTab(QtWidgets.QWidget):
    """
    三维牙齿分割结果展示。
    支持导入多个 STL 文件，每个文件对应一个 FDI 牙位，
    用 FDI 颜色渲染，左侧列表控制显隐。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._actors = {}    # fdi -> vtkActor
        self._renderer = None
        self._render_window = None
        self._interactor = None
        self._vtk_initialized = False
        self._init_ui()

    def showEvent(self, event):
        """Tab 第一次显示时初始化 VTK interactor"""
        super().showEvent(event)
        if not self._vtk_initialized:
            try:
                # QVTKRenderWindowInteractor 本身就是 interactor widget，直接调用 Initialize
                if hasattr(self._vtk_widget, 'Initialize'):
                    self._vtk_widget.Initialize()
                    self._vtk_widget.Start()
                self._vtk_initialized = True
                # 初始化后设置坐标轴指示器
                if getattr(self, '_axes_marker_pending', False) and self._renderer:
                    try:
                        import vtk
                        marker = vtk.vtkOrientationMarkerWidget()
                        marker.SetOrientationMarker(self._axes_actor)
                        marker.SetInteractor(self._vtk_widget)
                        marker.SetEnabled(1)
                        marker.InteractiveOff()
                        self._axes_marker = marker
                        self._axes_marker_pending = False
                    except Exception:
                        pass
                if self._render_window:
                    self._render_window.Render()
            except Exception as e:
                print(f"VTK 初始化失败: {e}")

    def _init_ui(self):
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)

        # 左侧：STL 文件列表 + 加载按钮
        left = QtWidgets.QWidget()
        left.setFixedWidth(200)
        left.setStyleSheet(f"background:{_PANEL};border-radius:4px;")
        left_lay = QtWidgets.QVBoxLayout(left)
        left_lay.setContentsMargins(6, 6, 6, 6)
        left_lay.setSpacing(6)

        # 加载按钮
        self.btn_load_stl = QtWidgets.QPushButton("📂 导入 STL 文件")
        self.btn_load_stl.setStyleSheet(
            f"QPushButton{{background:{_ACCENT};color:#111;border:none;"
            f"border-radius:4px;padding:4px 8px;font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{background:#7dd8f8;}}"
        )
        self.btn_load_stl.clicked.connect(self._on_load_stl)
        left_lay.addWidget(self.btn_load_stl)

        # 全选/全隐按钮行
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_show_all = self._mk_small_btn("全显")
        self.btn_hide_all = self._mk_small_btn("全隐")
        self.btn_clear_all = self._mk_small_btn("清除", "#e53935")
        self.btn_show_all.clicked.connect(lambda: self._set_all_visibility(True))
        self.btn_hide_all.clicked.connect(lambda: self._set_all_visibility(False))
        self.btn_clear_all.clicked.connect(self._clear_all)
        btn_row.addWidget(self.btn_show_all)
        btn_row.addWidget(self.btn_hide_all)
        btn_row.addWidget(self.btn_clear_all)
        left_lay.addLayout(btn_row)

        # STL 文件列表（带颜色 + 显隐复选框）
        lbl = QtWidgets.QLabel("已加载模型")
        lbl.setStyleSheet(_HEADER_STYLE)
        left_lay.addWidget(lbl)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{_BG};border:1px solid {_BORDER};border-radius:3px;}}"
        )
        self._stl_list_container = QtWidgets.QWidget()
        self._stl_list_container.setStyleSheet(f"background:{_BG};")
        self._stl_list_layout = QtWidgets.QVBoxLayout(self._stl_list_container)
        self._stl_list_layout.setContentsMargins(4, 4, 4, 4)
        self._stl_list_layout.setSpacing(2)
        self._stl_list_layout.addStretch()
        scroll.setWidget(self._stl_list_container)
        left_lay.addWidget(scroll, 1)

        self.lbl_stl_count = QtWidgets.QLabel("共 0 个模型")
        self.lbl_stl_count.setStyleSheet(f"color:{_TEXT_DIM};font-size:12px;")
        left_lay.addWidget(self.lbl_stl_count)

        lay.addWidget(left)

        # 右侧：VTK 渲染窗口
        self._vtk_widget = self._create_vtk_widget()
        lay.addWidget(self._vtk_widget, 1)

    def _create_vtk_widget(self) -> QtWidgets.QWidget:
        """创建 VTK 渲染窗口（不在此处 Initialize，等 showEvent）"""
        try:
            import vtk
            from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

            vtk_w = QVTKRenderWindowInteractor()
            self._renderer = vtk.vtkRenderer()
            self._renderer.SetBackground(0.08, 0.08, 0.08)

            rw = vtk_w.GetRenderWindow()
            rw.AddRenderer(self._renderer)
            self._render_window = rw

            style = vtk.vtkInteractorStyleTrackballCamera()
            vtk_w.SetInteractorStyle(style)

            # 坐标轴指示器（延迟到 showEvent 后设置，避免 Initialize 前调用）
            self._axes_actor = vtk.vtkAxesActor()
            self._axes_marker_pending = True  # 标记需要在 Initialize 后设置

            # 不在这里调用 Initialize()，等 showEvent
            return vtk_w

        except Exception as e:
            placeholder = QtWidgets.QLabel(f"VTK 渲染不可用\n{e}")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet(f"background:#111;color:{_TEXT_DIM};font-size:13px;")
            return placeholder

    # ── 公开方法 ──────────────────────────────────────────────────────────────

    def highlight_fdi(self, fdi: int):
        """高亮指定 FDI 的 actor（其余半透明）"""
        if not self._actors:
            return
        for f, actor in self._actors.items():
            if f == fdi:
                actor.GetProperty().SetOpacity(1.0)
                actor.GetProperty().SetAmbient(0.4)
            else:
                actor.GetProperty().SetOpacity(0.15)
        self._render()

    def reset_highlight(self):
        for actor in self._actors.values():
            actor.GetProperty().SetOpacity(1.0)
            actor.GetProperty().SetAmbient(0.1)
        self._render()

    def clear(self):
        self._clear_all()

    # ── 内部方法 ──────────────────────────────────────────────────────────────

    def _on_load_stl(self):
        """打开文件对话框，支持多选 STL"""
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "选择 STL 文件（可多选）", "",
            "STL Files (*.stl);;All Files (*)"
        )
        if not paths:
            return

        for path in paths:
            fdi = self._guess_fdi_from_filename(path)
            self._load_one_stl(path, fdi)

        if self._renderer:
            self._renderer.ResetCamera()
        self._render()
        self.lbl_stl_count.setText(f"共 {len(self._actors)} 个模型")

    def _guess_fdi_from_filename(self, path: str) -> int:
        """
        从文件名猜测 FDI 编号。
        例如 tooth_11.stl / FDI_21.stl / 36.stl 等。
        找不到则弹对话框让用户选择。
        """
        import re
        name = os.path.basename(path)
        # 匹配两位数字 11-48
        matches = re.findall(r'\b([1-4][1-8])\b', name)
        for m in matches:
            fdi = int(m)
            if fdi in FDI_COLORS:
                return fdi

        # 弹对话框
        from src.core.tooth_measurement import FDI_LABELS
        items = [str(f) for f in FDI_LABELS]
        item, ok = QtWidgets.QInputDialog.getItem(
            self, f"选择牙位 - {os.path.basename(path)}",
            "请选择该 STL 对应的 FDI 牙位编号：",
            items, 0, False
        )
        if ok and item:
            return int(item)
        return 0  # 未知

    def _load_one_stl(self, path: str, fdi: int):
        """加载单个 STL 并添加到渲染器"""
        if self._renderer is None:
            return
        try:
            import vtk
            reader = vtk.vtkSTLReader()
            reader.SetFileName(path)
            reader.Update()

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            # 设置 FDI 颜色
            r, g, b = fdi_color_vtk(fdi) if fdi in FDI_COLORS else (0.7, 0.7, 0.7)
            actor.GetProperty().SetColor(r, g, b)
            actor.GetProperty().SetAmbient(0.1)
            actor.GetProperty().SetDiffuse(0.8)
            actor.GetProperty().SetSpecular(0.3)

            # 若已有同 FDI 的 actor，先移除
            if fdi in self._actors:
                self._renderer.RemoveActor(self._actors[fdi])

            self._renderer.AddActor(actor)
            self._actors[fdi] = actor

            # 添加列表行
            self._add_stl_row(fdi, os.path.basename(path))

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "加载失败", f"无法加载 {path}：\n{e}")

    def _add_stl_row(self, fdi: int, filename: str):
        """在列表中添加一行"""
        # 移除旧行（如果存在）
        for i in range(self._stl_list_layout.count() - 1):
            item = self._stl_list_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if w.property("fdi") == fdi:
                    self._stl_list_layout.removeWidget(w)
                    w.deleteLater()
                    break

        row_w = QtWidgets.QWidget()
        row_w.setProperty("fdi", fdi)
        row_w.setFixedHeight(28)
        row_w.setStyleSheet(f"background:transparent;border-radius:3px;")
        h = QtWidgets.QHBoxLayout(row_w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(6)

        # 色块
        dot = QtWidgets.QLabel()
        dot.setFixedSize(12, 12)
        c = fdi_color(fdi) if fdi in FDI_COLORS else QtGui.QColor("#888")
        dot.setStyleSheet(f"background:{c.name()};border-radius:6px;")
        h.addWidget(dot)

        # 标签
        name = f"FDI {fdi}" if fdi else os.path.splitext(filename)[0]
        lbl = QtWidgets.QLabel(name)
        lbl.setStyleSheet(f"color:{_TEXT};font-size:12px;background:transparent;")
        lbl.setToolTip(filename)
        h.addWidget(lbl, 1)

        # 显隐复选框
        cb = QtWidgets.QCheckBox()
        cb.setChecked(True)
        cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;}}")
        cb.stateChanged.connect(lambda state, f=fdi: self._set_visibility(f, state == Qt.Checked))
        h.addWidget(cb)

        self._stl_list_layout.insertWidget(self._stl_list_layout.count() - 1, row_w)

    def _set_visibility(self, fdi: int, visible: bool):
        if fdi in self._actors:
            self._actors[fdi].SetVisibility(visible)
            self._render()

    def _set_all_visibility(self, visible: bool):
        for actor in self._actors.values():
            actor.SetVisibility(visible)
        # 同步复选框
        for i in range(self._stl_list_layout.count() - 1):
            item = self._stl_list_layout.itemAt(i)
            if item and item.widget():
                cb = item.widget().findChild(QtWidgets.QCheckBox)
                if cb:
                    cb.blockSignals(True)
                    cb.setChecked(visible)
                    cb.blockSignals(False)
        self._render()

    def _clear_all(self):
        if self._renderer:
            for actor in self._actors.values():
                self._renderer.RemoveActor(actor)
        self._actors.clear()
        while self._stl_list_layout.count() > 1:
            item = self._stl_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.lbl_stl_count.setText("共 0 个模型")
        self._render()

    def _render(self):
        if self._render_window:
            try:
                self._render_window.Render()
            except Exception:
                pass

    def _mk_small_btn(self, text, color="#4a4a4a"):
        btn = QtWidgets.QPushButton(text)
        btn.setFixedHeight(22)
        btn.setStyleSheet(
            f"QPushButton{{background:{color};color:#eee;border:none;"
            f"border-radius:3px;font-size:12px;padding:0 6px;}}"
            f"QPushButton:hover{{background:#5a5a5a;}}"
        )
        return btn


# ══════════════════════════════════════════════════════════════════════════════
# 主类：ToothMeasurementWidget
# ══════════════════════════════════════════════════════════════════════════════
class ToothMeasurementWidget(QtWidgets.QWidget):
    """
    口腔牙齿分割结果定量测量主面板（独立浮动窗口）

    布局：
      顶部工具栏
      ├─ 左侧 LabelListWidget（牙位列表）
      └─ 右侧 QTabWidget
           ├─ Tab1 MeasurementResultTab（测量结果）
           ├─ Tab2 TriViewTab（三视图）
           └─ Tab3 ThreeDViewTab（三维视图）

    对外信号：
      load_nii_requested   — 请求加载 NIfTI 分割文件
      measure_requested    — 请求执行测量
      export_pdf_requested — 请求导出 PDF
      tooth_selected(int)  — 用户选中某颗牙（FDI 编号）

    对外方法：
      set_file_path(path)  — 显示已加载文件路径
      clear()              — 清空所有数据
      set_status(msg, color) — 更新状态栏文字
      populate_results(results) — 填充测量结果
      show_tooth_detail(fdi)    — 高亮指定牙位
    """

    load_nii_requested   = pyqtSignal()
    measure_requested    = pyqtSignal()
    export_pdf_requested = pyqtSignal()
    tooth_selected       = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("口腔牙齿分割结果定量测量")
        self.setStyleSheet(f"background:{_BG};color:{_TEXT};")
        self._init_ui()

    def _init_ui(self):
        main_lay = QtWidgets.QVBoxLayout(self)
        main_lay.setContentsMargins(8, 8, 8, 8)
        main_lay.setSpacing(6)

        # ── 顶部工具栏 ────────────────────────────────────────────────────────
        main_lay.addWidget(self._build_toolbar())

        # ── 主体区域：左侧标签列表 + 右侧 Tab ─────────────────────────────────
        body = QtWidgets.QSplitter(Qt.Horizontal)
        body.setStyleSheet(f"QSplitter::handle{{background:{_BORDER};width:3px;}}")

        # 左侧标签列表
        self.label_list = LabelListWidget()
        self.label_list.label_selected.connect(self._on_label_selected)
        self.label_list.label_visibility_changed.connect(self._on_label_visibility)
        body.addWidget(self.label_list)

        # 右侧 Tab
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setStyleSheet(
            f"QTabWidget::pane{{background:{_PANEL};border:1px solid {_BORDER};border-radius:4px;}}"
            f"QTabBar::tab{{background:{_TOOLBAR};color:{_TEXT_DIM};padding:6px 16px;"
            f"border:1px solid {_BORDER};border-bottom:none;border-radius:3px 3px 0 0;margin-right:2px;}}"
            f"QTabBar::tab:selected{{background:{_PANEL};color:{_ACCENT};border-bottom:2px solid {_ACCENT};}}"
            f"QTabBar::tab:hover{{color:{_TEXT};}}"
        )

        self.result_tab  = MeasurementResultTab()
        self.triview_tab = TriViewTab()
        self.threed_tab  = ThreeDViewTab()

        self.tab_widget.addTab(self.result_tab,  "📊 测量结果")
        self.tab_widget.addTab(self.triview_tab, "🔬 三视图")
        self.tab_widget.addTab(self.threed_tab,  "🦷 三维视图")

        body.addWidget(self.tab_widget)
        body.setSizes([170, 900])
        main_lay.addWidget(body, 1)

        # ── 底部状态栏 ────────────────────────────────────────────────────────
        status_bar = QtWidgets.QWidget()
        status_bar.setFixedHeight(28)
        status_bar.setStyleSheet(f"background:{_TOOLBAR};border-radius:3px;")
        sb_lay = QtWidgets.QHBoxLayout(status_bar)
        sb_lay.setContentsMargins(8, 2, 8, 2)
        sb_lay.setSpacing(8)

        self.lbl_file = QtWidgets.QLabel("未加载文件")
        self.lbl_file.setStyleSheet(f"color:{_TEXT_DIM};font-size:12px;")
        sb_lay.addWidget(self.lbl_file, 1)

        self.lbl_status = QtWidgets.QLabel("就绪")
        self.lbl_status.setStyleSheet(f"color:{_OK};font-size:12px;")
        sb_lay.addWidget(self.lbl_status)

        main_lay.addWidget(status_bar)

    def _build_toolbar(self) -> QtWidgets.QWidget:
        """构建顶部工具栏"""
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"background:{_TOOLBAR};border-radius:4px;")
        lay = QtWidgets.QHBoxLayout(bar)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(8)

        # 标题
        title = QtWidgets.QLabel("🦷 口腔牙齿分割结果定量测量")
        title.setStyleSheet(f"color:{_ACCENT};font-size:14px;font-weight:bold;")
        lay.addWidget(title)
        lay.addStretch()

        # 加载分割文件按钮
        self.btn_load = self._mk_btn("📂 加载分割文件", _ACCENT, "#111")
        self.btn_load.clicked.connect(self.load_nii_requested)
        lay.addWidget(self.btn_load)

        # 开始测量按钮
        self.btn_measure = self._mk_btn("▶ 开始测量", "#4caf50", "#fff")
        self.btn_measure.clicked.connect(self.measure_requested)
        lay.addWidget(self.btn_measure)

        # 导出 PDF 按钮
        self.btn_export = self._mk_btn("📄 导出报告", "#ff9800", "#fff")
        self.btn_export.clicked.connect(self.export_pdf_requested)
        lay.addWidget(self.btn_export)

        return bar

    # ══════════════════════════════════════════════════════════════════════════
    # 公开方法（供 Controller 调用）
    # ══════════════════════════════════════════════════════════════════════════

    def set_file_path(self, path: str):
        """显示已加载的文件路径"""
        self.lbl_file.setText(f"文件：{os.path.basename(path)}")
        self.lbl_file.setToolTip(path)

    def clear(self):
        """清空所有数据（加载新文件时调用）"""
        self.label_list.clear()
        self.result_tab.clear()
        self.triview_tab.clear()
        self.lbl_file.setText("未加载文件")
        self.lbl_status.setText("就绪")
        self.lbl_status.setStyleSheet(f"color:{_OK};font-size:12px;")

    def set_status(self, msg: str, color: str = _OK):
        """更新底部状态栏"""
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet(f"color:{color};font-size:12px;")

    def populate_results(self, results: dict):
        """
        填充测量结果到所有 Tab。
        results: {fdi: ToothMetrics}
        """
        fdi_list = sorted(results.keys())
        has_warn = {fdi: len(results[fdi].warnings) > 0 for fdi in fdi_list}

        # 左侧标签列表
        self.label_list.populate(fdi_list, has_warn)

        # Tab1 测量结果表格
        self.result_tab.populate(results)

        # 状态栏
        warn_count = sum(1 for v in has_warn.values() if v)
        msg = f"测量完成，共 {len(fdi_list)} 颗牙"
        if warn_count:
            msg += f"，{warn_count} 颗有异常"
            self.set_status(msg, _WARN)
        else:
            self.set_status(msg, _OK)

    def show_tooth_detail(self, fdi: int):
        """高亮指定牙位（同步三个 Tab）"""
        self.label_list.highlight(fdi)
        self.result_tab.show_fdi(fdi)
        self.triview_tab.set_active_fdi(fdi)
        self.threed_tab.highlight_fdi(fdi)

    # ══════════════════════════════════════════════════════════════════════════
    # 内部信号处理
    # ══════════════════════════════════════════════════════════════════════════

    def _on_label_selected(self, fdi: int):
        """左侧标签列表点击 → 同步所有 Tab"""
        self.show_tooth_detail(fdi)
        self.tooth_selected.emit(fdi)

    def _on_label_visibility(self, fdi: int, visible: bool):
        """标签显隐复选框 → 同步三维视图"""
        if fdi in self.threed_tab._actors:
            self.threed_tab._actors[fdi].SetVisibility(visible)
            self.threed_tab._render()

    # ══════════════════════════════════════════════════════════════════════════
    # 辅助
    # ══════════════════════════════════════════════════════════════════════════

    def _mk_btn(self, text: str, bg: str, fg: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(text)
        btn.setFixedHeight(30)
        btn.setStyleSheet(
            f"QPushButton{{background:{bg};color:{fg};border:none;"
            f"border-radius:4px;padding:0 12px;font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{opacity:0.85;}}"
            f"QPushButton:disabled{{background:#555;color:#888;}}"
        )
        return btn
