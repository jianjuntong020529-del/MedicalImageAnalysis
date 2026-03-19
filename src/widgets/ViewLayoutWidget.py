# -*- coding: utf-8 -*-
"""
视图布局控制面板 Widget
提供多种视图布局切换按钮，控制主界面四个视图窗口的显示方式。
支持布局：
  - 四视图（2×2）
  - 仅轴状面（Axial）
  - 仅矢状面（Sagittal）
  - 仅冠状面（Coronal）
  - 仅3D体绘制
  - 三视图（轴+矢+冠，不含3D）
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, pyqtSignal


# ── 布局常量 ──────────────────────────────────────────────────────────────────
LAYOUT_FOUR      = "four"       # 四视图 2×2
LAYOUT_AXIAL     = "axial"      # 仅轴状面
LAYOUT_SAGITTAL  = "sagittal"   # 仅矢状面
LAYOUT_CORONAL   = "coronal"    # 仅冠状面
LAYOUT_VOLUME    = "volume"     # 仅3D体绘制
LAYOUT_THREE     = "three"      # 三视图（轴+矢+冠）
LAYOUT_MULTISLICE = "multislice" # 多切片平铺视图


class ViewLayoutWidget(QtWidgets.QWidget):
    """
    视图布局控制面板。
    发出 layout_changed 信号，携带布局名称字符串，由 Controller 响应。
    """

    # 布局切换信号，参数为布局名称常量
    layout_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 当前激活的布局名称
        self._current_layout = LAYOUT_FOUR
        self._init_ui()

    # ══════════════════════════════════════════════════════════════════════════
    # UI 初始化
    # ══════════════════════════════════════════════════════════════════════════

    def _init_ui(self):
        self.setWindowTitle("视图布局")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedSize(320, 270)
        self.setStyleSheet(self._window_style())

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── 标题 ──────────────────────────────────────────────────────────────
        title = QtWidgets.QLabel("视图布局")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #5bc8f5; font-size: 14px; font-weight: bold; "
            "border-bottom: 1px solid #444; padding-bottom: 6px;"
        )
        root.addWidget(title)

        # ── 布局按钮网格 ──────────────────────────────────────────────────────
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(8)

        # 每个按钮：(布局常量, 显示文字, 图标pixmap, 行, 列)
        btn_defs = [
            (LAYOUT_FOUR,      "四视图",    self._icon_four(),     0, 0),
            (LAYOUT_AXIAL,     "轴状面",    self._icon_single(),   0, 1),
            (LAYOUT_SAGITTAL,  "矢状面",    self._icon_single(),   0, 2),
            (LAYOUT_CORONAL,   "冠状面",    self._icon_single(),   1, 0),
            (LAYOUT_VOLUME,    "3D 体绘制", self._icon_single(),   1, 1),
            (LAYOUT_THREE,     "三视图",    self._icon_three(),    1, 2),
            (LAYOUT_MULTISLICE,"多切片视图", self._icon_multi(),   2, 0),
        ]

        # 保存按钮引用，用于高亮当前选中
        self._buttons = {}

        for layout_name, label, icon_pixmap, row, col in btn_defs:
            btn = self._make_layout_btn(layout_name, label, icon_pixmap)
            grid.addWidget(btn, row, col)
            self._buttons[layout_name] = btn

        root.addLayout(grid)

        # ── 当前布局提示 ──────────────────────────────────────────────────────
        self.lbl_current = QtWidgets.QLabel("当前：四视图")
        self.lbl_current.setAlignment(Qt.AlignCenter)
        self.lbl_current.setStyleSheet("color: #aaa; font-size: 11px;")
        root.addWidget(self.lbl_current)

        # 默认高亮四视图按钮
        self._highlight(LAYOUT_FOUR)

    # ══════════════════════════════════════════════════════════════════════════
    # 按钮工厂
    # ══════════════════════════════════════════════════════════════════════════

    def _make_layout_btn(self, layout_name: str, label: str, icon_pixmap: QtGui.QPixmap) -> QtWidgets.QPushButton:
        """创建单个布局切换按钮"""
        btn = QtWidgets.QPushButton()
        btn.setFixedSize(82, 64)
        btn.setToolTip(label)
        btn.setCursor(Qt.PointingHandCursor)

        # 图标 + 文字垂直排列
        btn_layout = QtWidgets.QVBoxLayout(btn)
        btn_layout.setContentsMargins(4, 6, 4, 4)
        btn_layout.setSpacing(3)

        icon_lbl = QtWidgets.QLabel()
        icon_lbl.setPixmap(icon_pixmap)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")

        text_lbl = QtWidgets.QLabel(label)
        text_lbl.setAlignment(Qt.AlignCenter)
        text_lbl.setStyleSheet("background: transparent; color: #ccc; font-size: 11px;")

        btn_layout.addWidget(icon_lbl)
        btn_layout.addWidget(text_lbl)

        btn.setStyleSheet(self._btn_normal_style())
        btn.clicked.connect(lambda _, n=layout_name, t=label: self._on_btn_clicked(n, t))
        return btn

    # ══════════════════════════════════════════════════════════════════════════
    # 事件
    # ══════════════════════════════════════════════════════════════════════════

    def _on_btn_clicked(self, layout_name: str, label: str):
        """按钮点击：更新高亮、发出信号"""
        self._current_layout = layout_name
        self._highlight(layout_name)
        self.lbl_current.setText(f"当前：{label}")
        self.layout_changed.emit(layout_name)

    def _highlight(self, layout_name: str):
        """高亮选中按钮，其余恢复普通样式"""
        for name, btn in self._buttons.items():
            if name == layout_name:
                btn.setStyleSheet(self._btn_active_style())
            else:
                btn.setStyleSheet(self._btn_normal_style())

    # ══════════════════════════════════════════════════════════════════════════
    # 图标绘制（用 QPainter 绘制简单示意图，无需外部图片）
    # ══════════════════════════════════════════════════════════════════════════

    def _icon_four(self) -> QtGui.QPixmap:
        """绘制 2×2 四格示意图标"""
        pm = QtGui.QPixmap(40, 32)
        pm.fill(Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor("#5bc8f5"), 1.5)
        p.setPen(pen)
        p.setBrush(QtGui.QColor("#2a4a6a"))
        # 四个格子
        for rx, ry in [(1, 1), (21, 1), (1, 17), (21, 17)]:
            p.drawRoundedRect(rx, ry, 17, 13, 2, 2)
        p.end()
        return pm

    def _icon_single(self) -> QtGui.QPixmap:
        """绘制单格示意图标"""
        pm = QtGui.QPixmap(40, 32)
        pm.fill(Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor("#5bc8f5"), 1.5)
        p.setPen(pen)
        p.setBrush(QtGui.QColor("#2a4a6a"))
        p.drawRoundedRect(2, 2, 36, 28, 3, 3)
        p.end()
        return pm

    def _icon_three(self) -> QtGui.QPixmap:
        """绘制三格（上一大 + 下两小）示意图标"""
        pm = QtGui.QPixmap(40, 32)
        pm.fill(Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor("#5bc8f5"), 1.5)
        p.setPen(pen)
        p.setBrush(QtGui.QColor("#2a4a6a"))
        # 上方大格
        p.drawRoundedRect(1, 1, 38, 14, 2, 2)
        # 下方两小格
        p.drawRoundedRect(1, 17, 17, 13, 2, 2)
        p.drawRoundedRect(21, 17, 17, 13, 2, 2)
        p.end()
        return pm

    def _icon_multi(self) -> QtGui.QPixmap:
        """绘制多切片横排示意图标（5个小格横排）"""
        pm = QtGui.QPixmap(40, 32)
        pm.fill(Qt.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor("#5bc8f5"), 1.5)
        p.setPen(pen)
        # 中间格（中心切片）高亮填充
        p.setBrush(QtGui.QColor("#2a4a6a"))
        for i in range(5):
            x = i * 8 + 1
            if i == 2:  # 中心切片
                p.setBrush(QtGui.QColor("#1a5a8a"))
            else:
                p.setBrush(QtGui.QColor("#2a4a6a"))
            p.drawRoundedRect(x, 4, 6, 24, 1, 1)
        p.end()
        return pm

    # ══════════════════════════════════════════════════════════════════════════
    # 样式
    # ══════════════════════════════════════════════════════════════════════════

    def _window_style(self) -> str:
        return """
            QWidget {
                background-color: #2b2b2b;
                border-radius: 6px;
            }
        """

    def _btn_normal_style(self) -> str:
        return """
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #5bc8f5;
            }
        """

    def _btn_active_style(self) -> str:
        return """
            QPushButton {
                background-color: #1a3a5c;
                border: 2px solid #5bc8f5;
                border-radius: 5px;
            }
        """
