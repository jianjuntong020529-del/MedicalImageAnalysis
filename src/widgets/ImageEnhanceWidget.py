# -*- coding: utf-8 -*-
"""
图像增强工具栏 Widget — 深色主题，与整体 UI 风格一致
"""
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

# ── 设计 Token ────────────────────────────────────────────────────────────────
_BG     = '#1e1e1e'
_CARD   = '#2d2d2d'
_CARD2  = '#333333'
_BORDER = '#3a3a3a'
_HOVER  = '#383838'
_ACCENT = '#3b82f6'
_TEXT   = '#e8e8e8'
_SEC    = '#9ca3af'
_WHITE  = '#ffffff'
_FONT   = '"Microsoft YaHei", "PingFang SC", sans-serif'

_GRP = f'''
    QGroupBox {{
        color: {_TEXT}; font-size: 11px; font-weight: 600;
        font-family: {_FONT};
        border: 1px solid {_BORDER}; border-radius: 6px;
        margin-top: 10px; padding-top: 6px;
        background: transparent;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 10px; padding: 0 4px;
        color: {_WHITE};
    }}
'''
_SLIDER = f'''
    QSlider {{ background: transparent; }}
    QSlider::groove:horizontal {{
        height: 4px; background: #555; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 12px; height: 12px; margin: -4px 0;
        background: {_ACCENT}; border-radius: 6px;
    }}
    QSlider::handle:horizontal:hover {{ background: #60a5fa; }}
    QSlider::sub-page:horizontal {{ background: {_ACCENT}; border-radius: 2px; }}
'''
_CHK = f'''
    QCheckBox {{ color: {_TEXT}; font-size: 11px; font-family: {_FONT}; }}
    QCheckBox::indicator {{
        width: 13px; height: 13px; border-radius: 3px;
        border: 1px solid #555; background: #333;
    }}
    QCheckBox::indicator:checked {{
        background: {_ACCENT}; border-color: {_ACCENT};
    }}
'''
_BTN_PRIMARY = f'''
    QPushButton {{
        background: {_ACCENT}; color: {_WHITE}; border: none;
        border-radius: 4px; padding: 6px 14px;
        font-size: 11px; font-weight: 600; font-family: {_FONT};
    }}
    QPushButton:hover {{ background: #2563eb; }}
    QPushButton:pressed {{ background: #1d4ed8; }}
    QPushButton:disabled {{ background: #374151; color: #6b7280; }}
'''
_BTN_SECONDARY = f'''
    QPushButton {{
        background: {_CARD2}; color: {_TEXT}; border: 1px solid {_BORDER};
        border-radius: 4px; padding: 6px 14px;
        font-size: 11px; font-family: {_FONT};
    }}
    QPushButton:hover {{ background: {_HOVER}; color: {_WHITE}; }}
'''


class ImageEnhanceWidget(QtWidgets.QWidget):
    """图像增强工具栏，发出 apply_requested 信号通知 Controller 执行管线"""

    # 信号：(enabled_dict, params_dict)
    apply_requested  = QtCore.pyqtSignal(dict, dict)
    reset_requested  = QtCore.pyqtSignal()
    export_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)
        self.setStyleSheet(f'background: {_BG};')
        self._init_ui()
        self.hide()

    def _init_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = QtWidgets.QLabel('影像增强')
        title.setStyleSheet(
            f'font-size: 12px; font-weight: 700; color: {_WHITE};'
            f'letter-spacing: 1px; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        root.addWidget(title)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f'background: {_BORDER}; border: none;')
        root.addWidget(sep)

        # ── A. 去噪（中值滤波）────────────────────────────────────────────
        grp_denoise = QtWidgets.QGroupBox('去噪处理')
        grp_denoise.setStyleSheet(_GRP)
        vb = QtWidgets.QVBoxLayout(grp_denoise)
        vb.setSpacing(6); vb.setContentsMargins(8, 4, 8, 8)

        self.chk_median = QtWidgets.QCheckBox('启用中值滤波')
        self.chk_median.setStyleSheet(_CHK)
        vb.addWidget(self.chk_median)

        h = QtWidgets.QHBoxLayout(); h.setSpacing(6)
        h.addWidget(self._lbl('核大小'))
        self.sl_median, self.lbl_median = self._make_slider(1, 7, 3, step=2)
        h.addWidget(self.sl_median, 1)
        h.addWidget(self.lbl_median)
        vb.addLayout(h)

        tip = QtWidgets.QLabel('适用：消除低剂量 CT 颗粒感')
        tip.setStyleSheet(f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
                          f'background: transparent; border: none;')
        vb.addWidget(tip)
        root.addWidget(grp_denoise)

        # ── B. 平滑（高斯滤波）────────────────────────────────────────────
        grp_smooth = QtWidgets.QGroupBox('平滑处理')
        grp_smooth.setStyleSheet(_GRP)
        vb2 = QtWidgets.QVBoxLayout(grp_smooth)
        vb2.setSpacing(6); vb2.setContentsMargins(8, 4, 8, 8)

        self.chk_gaussian = QtWidgets.QCheckBox('启用高斯平滑')
        self.chk_gaussian.setStyleSheet(_CHK)
        vb2.addWidget(self.chk_gaussian)

        h2 = QtWidgets.QHBoxLayout(); h2.setSpacing(6)
        h2.addWidget(self._lbl('柔和度'))
        self.sl_gaussian, self.lbl_gaussian = self._make_slider(1, 30, 10)
        h2.addWidget(self.sl_gaussian, 1)
        h2.addWidget(self.lbl_gaussian)
        vb2.addLayout(h2)

        tip2 = QtWidgets.QLabel('适用：减少伪影，平滑 3D 表面')
        tip2.setStyleSheet(f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
                           f'background: transparent; border: none;')
        vb2.addWidget(tip2)
        root.addWidget(grp_smooth)

        # ── C. 锐化（拉普拉斯）────────────────────────────────────────────
        grp_sharp = QtWidgets.QGroupBox('边缘锐化')
        grp_sharp.setStyleSheet(_GRP)
        vb3 = QtWidgets.QVBoxLayout(grp_sharp)
        vb3.setSpacing(6); vb3.setContentsMargins(8, 4, 8, 8)

        self.chk_sharpen = QtWidgets.QCheckBox('启用拉普拉斯锐化')
        self.chk_sharpen.setStyleSheet(_CHK)
        vb3.addWidget(self.chk_sharpen)

        h3 = QtWidgets.QHBoxLayout(); h3.setSpacing(6)
        h3.addWidget(self._lbl('锐度'))
        self.sl_sharpen, self.lbl_sharpen = self._make_slider(1, 20, 5)
        h3.addWidget(self.sl_sharpen, 1)
        h3.addWidget(self.lbl_sharpen)
        vb3.addLayout(h3)

        tip3 = QtWidgets.QLabel('适用：突出微小结节、骨裂纹边界')
        tip3.setStyleSheet(f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
                           f'background: transparent; border: none;')
        vb3.addWidget(tip3)
        root.addWidget(grp_sharp)

        # ── 操作按钮 ──────────────────────────────────────────────────────
        h_btns = QtWidgets.QHBoxLayout(); h_btns.setSpacing(6)
        self.btn_apply = QtWidgets.QPushButton('应用增强')
        self.btn_apply.setStyleSheet(_BTN_PRIMARY)
        self.btn_apply.clicked.connect(self._on_apply)

        self.btn_reset = QtWidgets.QPushButton('重置')
        self.btn_reset.setStyleSheet(_BTN_SECONDARY)
        self.btn_reset.clicked.connect(self._on_reset)

        h_btns.addWidget(self.btn_apply, 1)
        h_btns.addWidget(self.btn_reset)
        root.addLayout(h_btns)

        self.btn_export = QtWidgets.QPushButton('导出当前切片')
        self.btn_export.setStyleSheet(_BTN_SECONDARY)
        self.btn_export.clicked.connect(self.export_requested)
        root.addWidget(self.btn_export)

        root.addStretch()

    # ── 信号发射 ──────────────────────────────────────────────────────────────

    def _on_apply(self):
        enabled = {
            'median':   self.chk_median.isChecked(),
            'gaussian': self.chk_gaussian.isChecked(),
            'sharpen':  self.chk_sharpen.isChecked(),
        }
        params = {
            'median_size':   self.sl_median.value() * 2 - 1,   # 1→1, 2→3, 3→5...
            'gaussian_std':  self.sl_gaussian.value() / 10.0,
            'sharpen_alpha': self.sl_sharpen.value() / 10.0,
        }
        self.apply_requested.emit(enabled, params)

    def _on_reset(self):
        for chk in (self.chk_median, self.chk_gaussian, self.chk_sharpen):
            chk.setChecked(False)
        self.sl_median.setValue(3)
        self.sl_gaussian.setValue(10)
        self.sl_sharpen.setValue(5)
        self.reset_requested.emit()

    # ── 辅助 ──────────────────────────────────────────────────────────────────

    def _lbl(self, text):
        l = QtWidgets.QLabel(text)
        l.setFixedWidth(40)
        l.setStyleSheet(f'font-size: 11px; color: {_SEC}; font-family: {_FONT};'
                        f'background: transparent; border: none;')
        return l

    def _make_slider(self, lo, hi, val, step=1):
        sl = QtWidgets.QSlider(Qt.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)
        sl.setSingleStep(step)
        sl.setStyleSheet(_SLIDER)
        lbl = QtWidgets.QLabel(str(val))
        lbl.setFixedWidth(24)
        lbl.setStyleSheet(f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
                          f'background: transparent; border: none;')
        sl.valueChanged.connect(lambda v, l=lbl: l.setText(str(v)))
        return sl, lbl
