# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

from src.constant.WindowConstant import WindowConstant

# ── 设计 Token（与 DataManagerWidget 保持一致）────────────────────────────────
_BG     = '#1e1e1e'
_CARD   = '#2d2d2d'
_BORDER = '#3a3a3a'
_HOVER  = '#383838'
_ACCENT = '#3b82f6'
_TEXT   = '#e8e8e8'
_SEC    = '#9ca3af'
_HINT   = '#6b7280'
_WHITE  = '#ffffff'
_FONT   = '"Microsoft YaHei", "PingFang SC", sans-serif'

_SLIDER_STYLE = f'''
    QSlider::groove:horizontal {{
        height: 4px; background: {_BORDER}; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 14px; height: 14px; margin: -5px 0;
        background: {_ACCENT}; border-radius: 7px;
        border: 2px solid #1e3a5f;
    }}
    QSlider::handle:horizontal:hover {{
        background: #60a5fa;
    }}
    QSlider::sub-page:horizontal {{
        background: {_ACCENT}; border-radius: 2px;
    }}
'''


class Contrast:
    def __init__(self):
        self.widget = None

    def init_widget(self):
        self.widget_contrast = QtWidgets.QWidget(self.widget)
        self.widget_contrast.setMinimumSize(QtCore.QSize(220, 110))
        self.widget_contrast.setMaximumSize(QtCore.QSize(400, 130))
        self.widget_contrast.setObjectName("widget_contrast")
        self.widget_contrast.setStyleSheet(
            f'background: {_CARD}; border-radius: 8px; border: 1px solid {_BORDER};'
        )

        # 阴影
        eff = QGraphicsDropShadowEffect(self.widget_contrast)
        eff.setBlurRadius(12); eff.setOffset(0, 2)
        eff.setColor(QColor(0, 0, 0, 60))
        self.widget_contrast.setGraphicsEffect(eff)

        root = QtWidgets.QVBoxLayout(self.widget_contrast)
        root.setContentsMargins(12, 8, 12, 10)
        root.setSpacing(4)

        # ── 标题 ──
        self.title = QtWidgets.QLabel(self.widget_contrast)
        self.title.setObjectName("title")
        self.title.setStyleSheet(
            f'font-size: 11px; font-weight: 700; color: {_WHITE};'
            f'letter-spacing: 1px; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        root.addWidget(self.title)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f'background: {_BORDER}; border: none;')
        root.addWidget(sep)

        # ── 窗位 ──
        self._add_slider_row(root, '窗位', 'window_level', 'window_level_slider',
                             -2000, 3000)

        # ── 窗宽 ──
        self._add_slider_row(root, '窗宽', 'window_width', 'window_width_slider',
                             -2000, 8000)

        self._translate()

    def _add_slider_row(self, parent_layout, label_text, label_attr, slider_attr,
                        minimum, maximum):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)

        lbl_key = QtWidgets.QLabel(label_text)
        lbl_key.setFixedWidth(28)
        lbl_key.setStyleSheet(
            f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        row.addWidget(lbl_key)

        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setObjectName(slider_attr)
        slider.setMaximum(maximum)
        slider.setMinimum(minimum)
        slider.setSingleStep(1)
        slider.setStyleSheet(_SLIDER_STYLE)
        row.addWidget(slider, 1)

        lbl_val = QtWidgets.QLabel('0')
        lbl_val.setFixedWidth(42)
        lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_val.setStyleSheet(
            f'font-size: 10px; font-weight: 700; color: {_WHITE};'
            f'font-family: {_FONT}; background: transparent; border: none;'
        )
        row.addWidget(lbl_val)

        parent_layout.addLayout(row)

        # 绑定到实例属性
        setattr(self, slider_attr, slider)
        setattr(self, label_attr, lbl_val)

        # 滑块值变化时同步标签
        slider.valueChanged.connect(lambda v, l=lbl_val: l.setText(str(v)))

    def _translate(self):
        self.title.setText(WindowConstant.CONTRAST_TOOL_TITLE)

