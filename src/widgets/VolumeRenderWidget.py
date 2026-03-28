# -*- coding: utf-8 -*-
import vtk
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

# ── 设计 Token（与 DataManagerWidget / ContrastWidget 保持一致）──────────────
_BG     = '#1e1e1e'
_CARD   = '#2d2d2d'
_CARD2  = '#333333'
_BORDER = '#3a3a3a'
_HOVER  = '#383838'
_ACCENT = '#3b82f6'
_TEXT   = '#e8e8e8'
_SEC    = '#000000'
_HINT   = '#000000'
_WHITE  = '#ffffff'
_GRAY_TRACK = '#555555'
_FONT   = '"Microsoft YaHei", "PingFang SC", sans-serif'

_GRP_STYLE = f'''
    QGroupBox {{
        color: {_SEC}; font-size: 11px; font-weight: 600;
        font-family: {_FONT};
        border: 1px solid {_BORDER}; border-radius: 6px;
        margin-top: 10px; padding-top: 6px;
        background: transparent;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 10px; padding: 0 4px;
        color: {_SEC};
    }}
'''


_SPIN_STYLE = f'''
    QSpinBox {{
        background: {_CARD2}; color: {_TEXT}; border: 1px solid {_BORDER};
        border-radius: 3px; padding: 2px 4px; font-size: 11px;
        font-family: {_FONT};
    }}
    QSpinBox:focus {{ border-color: {_ACCENT}; }}
'''
_SLIDER_STYLE = f'''
    QSlider {{background: transparent;}}
    QSlider::groove:horizontal {{
        height: 4px; 
        background: {_GRAY_TRACK}; 
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 12px; 
        height: 12px; 
        margin: -4px 0;
        background: {_ACCENT}; 
        border-radius: 6px;
    }}
    QSlider::handle:horizontal:hover {{ 
        background: #60a5fa; 
    }}
    /* 已填充部分（左侧）保持高亮颜色 */
    QSlider::sub-page:horizontal {{ 
        background: {_ACCENT}; 
        border-radius: 2px; 
    }}
    /* 未填充部分（右侧）明确指定为灰色 */
    QSlider::add-page:horizontal {{ 
        background: {_GRAY_TRACK}; 
        border-radius: 2px; 
    }}
'''
_BTN_PRIMARY = f'''
    QPushButton {{
        background: {_ACCENT}; color: {_WHITE}; border: none;
        border-radius: 4px; padding: 5px 12px;
        font-size: 11px; font-weight: 600; font-family: {_FONT};
    }}
    QPushButton:hover {{ background: #2563eb; }}
    QPushButton:pressed {{ background: #1d4ed8; }}
'''
_BTN_SECONDARY = f'''
    QPushButton {{
        background: {_CARD2}; color: {_TEXT}; border: 1px solid {_BORDER};
        border-radius: 4px; padding: 5px 12px;
        font-size: 11px; font-family: {_FONT};
    }}
    QPushButton:hover {{ background: {_HOVER}; color: {_WHITE}; }}
'''
_CHK_STYLE = f'''
    QCheckBox {{ color: #000000; font-size: 11px; font-family: {_FONT}; background: transparent; }}
    QCheckBox::indicator {{
        width: 13px; height: 13px; border-radius: 3px;
        border: 1px solid #555; background: #333;
    }}
    QCheckBox::indicator:checked {{
        background: {_ACCENT}; border-color: {_ACCENT};
    }}
'''

# ── 口腔 CBCT 默认关键点（范围格式）────────────────────────────────────────
# 格式: (hu_start, hu_end, opacity, r, g, b)
# 若 hu_start == hu_end 表示单点；否则 [hu_start, hu_end] 区间保持恒定属性
_DEFAULT_POINTS = [
    (-1000, -200,  0.00,  0.00, 0.00, 0.00),   # 空气区间：黑色完全透明
    (-200,   0,    0.03,  0.80, 0.60, 0.50),   # 软组织区间：肉色微透明
    (0,      200,  0.00,  0.90, 0.75, 0.55),   # 骨交界过渡：米黄透明
    (200,    700,  0.08,  0.90, 0.75, 0.55),   # 松质骨区间：米黄轻微不透明
    (700,    1000, 0.35,  1.00, 0.95, 0.85),   # 皮质骨区间：象牙白半透明
    (1000,   1500, 0.65,  1.00, 0.95, 0.85),   # 牙本质区间：象牙白较不透明
    (1500,   3000, 0.85,  1.00, 1.00, 1.00),   # 牙釉质/高密度：纯白高度不透明
]

# ── 预设（供下拉框使用）──────────────────────────────────────────────────────
TISSUE_PRESETS = {
    "默认": {
        "color":[
            (-1000,  0.00,   0.00, 0.00, 0.00),   # 空气：黑色透明
            (-200,   0.00,   0.80, 0.60, 0.50),   # 软组织边界：肉色透明
            (0,      0.03,   0.80, 0.60, 0.50),   # 软组织：肉色微透明
            (200,    0.00,   0.90, 0.75, 0.55),   # 骨交界：米黄透明过渡
            (400,    0.08,   0.90, 0.75, 0.55),   # 松质骨：米黄轻微不透明
            (700,    0.35,   1.00, 0.95, 0.85),   # 皮质骨：象牙白半透明
            (1000,   0.65,   1.00, 0.95, 0.85),   # 牙本质：象牙白较不透明
            (1500,   0.85,   1.00, 1.00, 1.00),   # 牙釉质：纯白高度不透明
            (3000,   0.95,   1.00, 1.00, 1.00),   # 高密度：纯白几乎不透明
        ],
    },
    "口腔CBCT": {
        "color": [(0, 0.0, 0.0, 0.0),(1000,  1.0, 0.5, 0.3),(1500,  1.0, 0.5, 0.3),(2000,  1.0, 0.7,  0.4),(4000,  1.0, 1.0,  1.0),],
        "opacity": [(0,     0.0),(900,   0.0),(1500,  0.3),(2000,  0.5),(4000,  0.9),],
    },
    "骨骼": {
        "color":   [(0, 0, 0, 0), (400, 0.9, 0.7, 0.5), (1000, 1.0, 0.9, 0.7), (2000, 1.0, 1.0, 1.0)],
        "opacity": [(0, 0.0), (400, 0.0), (600, 0.15), (1000, 0.5), (2000, 0.85)],
    },
    "牙齿/硬组织": {
        "color":   [(0, 0, 0, 0), (700, 1.0, 0.95, 0.85), (1500, 1.0, 1.0, 1.0), (3000, 1.0, 1.0, 1.0)],
        "opacity": [(0, 0.0), (600, 0.0), (800, 0.1), (1500, 0.6), (3000, 0.9)],
    },
    "软组织": {
        "color":   [(0, 0, 0, 0), (-200, 0.8, 0.4, 0.3), (200, 1.0, 0.6, 0.5), (600, 1.0, 0.8, 0.7)],
        "opacity": [(0, 0.0), (-500, 0.0), (-200, 0.05), (200, 0.2), (600, 0.4)],
    },
    "肺部": {
        "color":   [(-1000, 0, 0, 0), (-600, 0.3, 0.5, 0.8), (-400, 0.5, 0.7, 1.0), (0, 0.8, 0.8, 0.8)],
        "opacity": [(-1000, 0.0), (-800, 0.0), (-600, 0.1), (-400, 0.3), (0, 0.0)],
    },
    "自定义": None,
}


# ── 颜色选择按钮 ──────────────────────────────────────────────────────────────

class ColorButton(QtWidgets.QPushButton):
    color_changed = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, r=1.0, g=1.0, b=1.0, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 20)
        self._color = QtGui.QColor(int(r*255), int(g*255), int(b*255))
        self.clicked.connect(self._pick)
        self._refresh()

    def _pick(self):
        from PyQt5.QtWidgets import QApplication, QColorDialog
        app = QApplication.instance()
        saved = app.styleSheet()
        app.setStyleSheet('')
        c = QColorDialog.getColor(self._color, None, '选择颜色')
        app.setStyleSheet(saved)
        if c.isValid():
            self._color = c
            self._refresh()
            self.color_changed.emit(c)

    def _refresh(self):
        self.setStyleSheet(
            f'background: {self._color.name()}; border: 1px solid {_BORDER};'
            f'border-radius: 3px;'
        )

    def set_rgb(self, r, g, b):
        self._color = QtGui.QColor(int(r*255), int(g*255), int(b*255))
        self._refresh()

    def rgb_f(self):
        return self._color.redF(), self._color.greenF(), self._color.blueF()


# ── 主 Widget ─────────────────────────────────────────────────────────────────

class VolumeRenderWidget(QtWidgets.QWidget):
    """体绘制工具栏 — 深色主题 + 关键点精细控制"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._volume     = None
        self._renderer   = None
        self._vtk_widget = None
        self._block      = False   # 批量更新时屏蔽信号

        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        self.setStyleSheet(f'background: {_BG};')

        self._init_ui()
        self.hide()

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = QtWidgets.QLabel('体绘制控制面板')
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

        # ── 预设选择 ──────────────────────────────────────────────────────
        grp_preset = QtWidgets.QGroupBox('组织预设')
        grp_preset.setStyleSheet(_GRP_STYLE)
        h_preset = QtWidgets.QHBoxLayout(grp_preset)
        h_preset.setSpacing(6)

        self.combo_preset = QtWidgets.QComboBox()
        self.combo_preset.addItems(list(TISSUE_PRESETS.keys()))
        self.combo_preset.setStyleSheet(f'''
            QComboBox {{
                background: {_CARD2}; color: {_TEXT}; border: 1px solid {_BORDER};
                border-radius: 4px; padding: 3px 6px; font-size: 11px;
                font-family: {_FONT};
            }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox QAbstractItemView {{
                background: {_CARD2}; color: {_TEXT};
                selection-background-color: {_ACCENT};
            }}
        ''')
        h_preset.addWidget(self.combo_preset, 1)

        btn_apply = QtWidgets.QPushButton('应用')
        btn_apply.setStyleSheet(_BTN_PRIMARY)
        btn_apply.setFixedWidth(52)
        btn_apply.clicked.connect(self._apply_preset)
        h_preset.addWidget(btn_apply)
        root.addWidget(grp_preset)

        # ── 传输函数关键点 ────────────────────────────────────────────────
        grp_tf = QtWidgets.QGroupBox('传输函数关键点')
        grp_tf.setStyleSheet(_GRP_STYLE)
        tf_layout = QtWidgets.QVBoxLayout(grp_tf)
        tf_layout.setSpacing(4)
        tf_layout.setContentsMargins(6, 4, 6, 6)

        # 表头
        hdr = QtWidgets.QHBoxLayout()
        hdr.setSpacing(4)
        for txt, w in [('起始HU', 58), ('结束HU', 58), ('透明度', None), ('颜色', 32)]:
            l = QtWidgets.QLabel(txt)
            l.setStyleSheet(f'font-size: 10px; color: {_HINT}; font-family: {_FONT};'
                            f'background: transparent; border: none;')
            if w:
                l.setFixedWidth(w)
            else:
                l.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            hdr.addWidget(l)
        tf_layout.addLayout(hdr)

        # 滚动区域容纳关键点行
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f'''
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {_BORDER}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        ''')

        self._tf_container = QtWidgets.QWidget()
        self._tf_container.setStyleSheet('background: transparent;')
        self._tf_vbox = QtWidgets.QVBoxLayout(self._tf_container)
        self._tf_vbox.setSpacing(3)
        self._tf_vbox.setContentsMargins(0, 0, 0, 0)
        self._tf_vbox.setAlignment(Qt.AlignTop)
        scroll.setWidget(self._tf_container)
        scroll.setFixedHeight(220)
        tf_layout.addWidget(scroll)

        # 添加/删除行按钮
        h_tf_btns = QtWidgets.QHBoxLayout()
        h_tf_btns.setSpacing(6)
        btn_add_pt = QtWidgets.QPushButton('＋ 添加点')
        btn_add_pt.setStyleSheet(_BTN_SECONDARY)
        btn_add_pt.clicked.connect(self._add_point_row)
        btn_del_pt = QtWidgets.QPushButton('－ 删除末行')
        btn_del_pt.setStyleSheet(_BTN_SECONDARY)
        btn_del_pt.clicked.connect(self._del_point_row)
        h_tf_btns.addWidget(btn_add_pt)
        h_tf_btns.addWidget(btn_del_pt)
        tf_layout.addLayout(h_tf_btns)
        root.addWidget(grp_tf)

        self._point_rows = []   # list of (spin_start, spin_end, slider_op, lbl_op, btn_clr, row_w)

        # 用默认关键点初始化
        for hu_s, hu_e, op, r, g, b in _DEFAULT_POINTS:
            self._add_point_row(hu_start=hu_s, hu_end=hu_e, op=op, r=r, g=g, b=b)

        # ── 光照参数 ──────────────────────────────────────────────────────
        grp_light = QtWidgets.QGroupBox('光照参数')
        grp_light.setStyleSheet(_GRP_STYLE)
        grid = QtWidgets.QGridLayout(grp_light)
        grid.setSpacing(6)
        grid.setContentsMargins(8, 4, 8, 8)

        self.sl_ambient,  self.lbl_ambient  = self._make_slider(0, 100, 50)
        self.sl_diffuse,  self.lbl_diffuse  = self._make_slider(0, 100, 70)
        self.sl_specular, self.lbl_specular = self._make_slider(0, 100, 50)

        for row, (name, sl, lb) in enumerate([
            ('环境光',   self.sl_ambient,  self.lbl_ambient),
            ('漫反射',   self.sl_diffuse,  self.lbl_diffuse),
            ('镜面反射', self.sl_specular, self.lbl_specular),
        ]):
            grid.addWidget(self._lbl(name), row, 0)
            grid.addWidget(sl, row, 1)
            grid.addWidget(lb, row, 2)

        self.chk_shade = QtWidgets.QCheckBox('启用阴影')
        self.chk_shade.setChecked(False)
        self.chk_shade.setStyleSheet(_CHK_STYLE)
        grid.addWidget(self.chk_shade, 3, 0, 1, 3)

        self.sl_ambient.valueChanged.connect(self._on_light_changed)
        self.sl_diffuse.valueChanged.connect(self._on_light_changed)
        self.sl_specular.valueChanged.connect(self._on_light_changed)
        self.chk_shade.stateChanged.connect(self._on_light_changed)
        root.addWidget(grp_light)

        # ── 整体不透明度 ──────────────────────────────────────────────────
        grp_op = QtWidgets.QGroupBox('整体不透明度')
        grp_op.setStyleSheet(_GRP_STYLE)
        h_op = QtWidgets.QHBoxLayout(grp_op)
        h_op.setSpacing(6)
        h_op.setContentsMargins(8, 4, 8, 8)
        self.sl_global_op, self.lbl_global_op = self._make_slider(1, 200, 100)
        self.sl_global_op.valueChanged.connect(self._on_tf_changed)
        h_op.addWidget(self.sl_global_op, 1)
        h_op.addWidget(self.lbl_global_op)
        root.addWidget(grp_op)

        # ── 背景颜色 ──────────────────────────────────────────────────────
        grp_bg = QtWidgets.QGroupBox('背景颜色 (RGB 0-255)')
        grp_bg.setStyleSheet(_GRP_STYLE)
        h_bg = QtWidgets.QHBoxLayout(grp_bg)
        h_bg.setSpacing(6)
        h_bg.setContentsMargins(10, 15, 10, 10)
        for attr, val, tag in [('spin_bg_r', 128, 'R'), ('spin_bg_g', 128, 'G'), ('spin_bg_b', 128, 'B')]:
            lbl_tag = QtWidgets.QLabel(tag)
            lbl_tag.setStyleSheet(
                f'font-size: 11px; color: {_SEC}; font-family: {_FONT};'
                f'background: transparent; border: none;'
            )
            lbl_tag.setFixedWidth(14)
            h_bg.addWidget(lbl_tag)
            sp = QtWidgets.QSpinBox()
            sp.setRange(0, 255); sp.setValue(val)
            sp.setStyleSheet(_SPIN_STYLE)
            sp.valueChanged.connect(self._on_bg_changed)
            setattr(self, attr, sp)
            h_bg.addWidget(sp, 1)
        root.addWidget(grp_bg)

        # ── 底部按钮 ──────────────────────────────────────────────────────
        h_btns = QtWidgets.QHBoxLayout()
        h_btns.setSpacing(6)
        btn_reset = QtWidgets.QPushButton('重置默认')
        btn_reset.setStyleSheet(_BTN_SECONDARY)
        btn_reset.clicked.connect(self._reset)
        btn_refresh = QtWidgets.QPushButton('刷新视图')
        btn_refresh.setStyleSheet(_BTN_PRIMARY)
        btn_refresh.clicked.connect(self._render)
        h_btns.addWidget(btn_reset)
        h_btns.addWidget(btn_refresh)
        root.addLayout(h_btns)
        root.addStretch()

    # ── 关键点行管理 ──────────────────────────────────────────────────────────

    def _add_point_row(self, hu_start=0, hu_end=0, op=0.0, r=1.0, g=1.0, b=1.0):
        row_w = QtWidgets.QWidget()
        row_w.setStyleSheet('background: transparent;')
        row_h = QtWidgets.QHBoxLayout(row_w)
        row_h.setContentsMargins(0, 0, 0, 0)
        row_h.setSpacing(4)

        spin_start = QtWidgets.QSpinBox()
        spin_start.setRange(-2000, 10000)
        spin_start.setValue(int(hu_start))
        spin_start.setFixedWidth(58)
        spin_start.setStyleSheet(_SPIN_STYLE)

        spin_end = QtWidgets.QSpinBox()
        spin_end.setRange(-2000, 10000)
        spin_end.setValue(int(hu_end))
        spin_end.setFixedWidth(58)
        spin_end.setStyleSheet(_SPIN_STYLE)

        slider_op = QtWidgets.QSlider(Qt.Horizontal)
        slider_op.setRange(0, 100)
        slider_op.setValue(int(op * 100))
        slider_op.setStyleSheet(_SLIDER_STYLE)

        lbl_op = QtWidgets.QLabel(f'{int(op*100)}%')
        lbl_op.setFixedWidth(30)
        lbl_op.setStyleSheet(f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
                             f'background: transparent; border: none;')
        slider_op.valueChanged.connect(lambda v, l=lbl_op: l.setText(f'{v}%'))

        btn_clr = ColorButton(r, g, b)

        row_h.addWidget(spin_start)
        row_h.addWidget(spin_end)
        row_h.addWidget(slider_op, 1)
        row_h.addWidget(lbl_op)
        row_h.addWidget(btn_clr)

        spin_start.valueChanged.connect(self._on_tf_changed)
        spin_end.valueChanged.connect(self._on_tf_changed)
        slider_op.valueChanged.connect(self._on_tf_changed)
        btn_clr.color_changed.connect(self._on_tf_changed)

        self._tf_vbox.addWidget(row_w)
        self._point_rows.append((spin_start, spin_end, slider_op, lbl_op, btn_clr, row_w))

    def _del_point_row(self):
        if len(self._point_rows) <= 2:
            return
        *_, row_w = self._point_rows.pop()
        self._tf_vbox.removeWidget(row_w)
        row_w.deleteLater()
        self._on_tf_changed()

    # ── VTK 绑定 ──────────────────────────────────────────────────────────────

    def bind_vtk(self, volume, renderer, vtk_widget):
        self._volume     = volume
        self._renderer   = renderer
        self._vtk_widget = vtk_widget
        self._apply_tf()
        self._on_light_changed()

    # ── 事件处理 ──────────────────────────────────────────────────────────────

    def _on_tf_changed(self, *_):
        if self._block or self._volume is None:
            return
        self._apply_tf()
        self._render()

    def _apply_tf(self):
        if self._volume is None:
            return
        scale = self.sl_global_op.value() / 100.0
        ctf = vtk.vtkColorTransferFunction()
        otf = vtk.vtkPiecewiseFunction()
        for spin_start, spin_end, slider_op, _, btn_clr, _ in self._point_rows:
            hu_s = spin_start.value()
            hu_e = spin_end.value()
            op   = min(1.0, (slider_op.value() / 100.0) * scale)
            r, g, b = btn_clr.rgb_f()
            ctf.AddRGBPoint(hu_s, r, g, b)
            otf.AddPoint(hu_s, op)
            if hu_e != hu_s:
                ctf.AddRGBPoint(hu_e, r, g, b)
                otf.AddPoint(hu_e, op)
        prop = self._volume.GetProperty()
        prop.SetColor(ctf)
        prop.SetScalarOpacity(otf)

    def _apply_preset(self):
        name = self.combo_preset.currentText()
        preset = TISSUE_PRESETS.get(name)
        if preset is None:
            return
        self._block = True
        for *_, row_w in self._point_rows:
            self._tf_vbox.removeWidget(row_w)
            row_w.deleteLater()
        self._point_rows.clear()
        color_map = {int(pt[0]): (pt[1], pt[2], pt[3]) for pt in preset['color']}
        for hu, op in preset['opacity']:
            hu = int(hu)
            if hu in color_map:
                r, g, b = color_map[hu]
            else:
                keys = sorted(color_map.keys())
                closest = min(keys, key=lambda k: abs(k - hu))
                r, g, b = color_map[closest]
            # 预设为单点，hu_start == hu_end
            self._add_point_row(hu_start=hu, hu_end=hu, op=op, r=r, g=g, b=b)
        self._block = False
        self._apply_tf()
        self._render()

    def _on_light_changed(self, *_):
        if self._volume is None:
            return
        prop = self._volume.GetProperty()
        prop.SetAmbient(self.sl_ambient.value() / 100.0)
        prop.SetDiffuse(self.sl_diffuse.value() / 100.0)
        prop.SetSpecular(self.sl_specular.value() / 100.0)
        if self.chk_shade.isChecked():
            prop.ShadeOff()
        else:
            prop.ShadeOn()
        self._render()

    def _on_bg_changed(self, *_):
        if self._renderer is None:
            return
        self._renderer.SetBackground(
            self.spin_bg_r.value() / 255.0,
            self.spin_bg_g.value() / 255.0,
            self.spin_bg_b.value() / 255.0,
        )
        self._render()

    def _reset(self):
        self._block = True
        for *_, row_w in self._point_rows:
            self._tf_vbox.removeWidget(row_w)
            row_w.deleteLater()
        self._point_rows.clear()
        for hu_s, hu_e, op, r, g, b in _DEFAULT_POINTS:
            self._add_point_row(hu_start=hu_s, hu_end=hu_e, op=op, r=r, g=g, b=b)
        self.sl_ambient.setValue(50)
        self.sl_diffuse.setValue(70)
        self.sl_specular.setValue(50)
        self.sl_global_op.setValue(100)
        self.chk_shade.setChecked(False)
        self.spin_bg_r.setValue(128)
        self.spin_bg_g.setValue(128)
        self.spin_bg_b.setValue(128)
        self._block = False
        self._apply_tf()
        self._on_light_changed()
        self._on_bg_changed()

    def _render(self):
        if self._vtk_widget is not None:
            self._vtk_widget.Render()

    # ── 辅助 ──────────────────────────────────────────────────────────────────

    def _lbl(self, text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(
            f'font-size: 11px; color: {_SEC}; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        l.setFixedWidth(46)
        return l

    def _make_slider(self, lo, hi, val):
        sl = QtWidgets.QSlider(Qt.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)
        sl.setStyleSheet(_SLIDER_STYLE)
        lbl = QtWidgets.QLabel(str(val))
        lbl.setFixedWidth(28)
        lbl.setStyleSheet(
            f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        sl.valueChanged.connect(lambda v, l=lbl: l.setText(str(v)))
        return sl, lbl
