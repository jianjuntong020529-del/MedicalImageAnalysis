# -*- coding: utf-8 -*-
import vtk
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font


# ── 预设组织传输函数 ──────────────────────────────────────────────────────────
# 每个预设定义 color_points: [(scalar, r, g, b), ...]
#              opacity_points: [(scalar, opacity), ...]
# 标量值单位为 HU（Hounsfield Unit），适用于 CBCT/CT 数据

TISSUE_PRESETS = {
    # ── 口腔牙齿 CBCT（默认预设）──────────────────────────────────────────────
    # 针对口腔 CBCT 数据优化：
    #   软组织（-200~200 HU）：半透明肉色
    #   牙槽骨（200~700 HU）：不透明米黄色
    #   牙釉质/硬组织（700~3000 HU）：高亮白色
    "口腔牙齿 CBCT": {
        "color": [
            (-1000, 0.0, 0.0, 0.0),    # 空气：黑色透明
            (-200,  0.8, 0.6, 0.5),    # 软组织：肉色
            (200,   0.9, 0.75, 0.55),  # 牙槽骨：米黄色
            (700,   1.0, 0.95, 0.85),  # 牙本质：象牙白
            (1500,  1.0, 1.0,  1.0),   # 牙釉质：纯白
            (3000,  1.0, 1.0,  1.0),   # 金属/高密度：纯白
        ],
        "opacity": [
            (-1000, 0.0),   # 空气：完全透明
            (-200,  0.0),   # 软组织边界：透明
            (0,     0.03),  # 软组织：微透明（可见轮廓）
            (200,   0.0),   # 软组织与骨交界：透明过渡
            (400,   0.08),  # 松质骨：轻微不透明
            (700,   0.35),  # 皮质骨/牙槽骨：半透明
            (1000,  0.65),  # 牙本质：较不透明
            (1500,  0.85),  # 牙釉质：高度不透明
            (3000,  0.95),  # 高密度硬组织：几乎不透明
        ],
    },
    # ── 骨骼（通用 CT）────────────────────────────────────────────────────────
    "骨骼": {
        "color":   [(0, 0, 0, 0), (400, 0.9, 0.7, 0.5), (1000, 1.0, 0.9, 0.7), (2000, 1.0, 1.0, 1.0)],
        "opacity": [(0, 0.0), (400, 0.0), (600, 0.15), (1000, 0.5), (2000, 0.85)],
    },
    # ── 牙齿/硬组织（高分辨率 CBCT）──────────────────────────────────────────
    "牙齿/硬组织": {
        "color":   [(0, 0, 0, 0), (700, 1.0, 0.95, 0.85), (1500, 1.0, 1.0, 1.0), (3000, 1.0, 1.0, 1.0)],
        "opacity": [(0, 0.0), (600, 0.0), (800, 0.1), (1500, 0.6), (3000, 0.9)],
    },
    # ── 软组织 ────────────────────────────────────────────────────────────────
    "软组织": {
        "color":   [(0, 0, 0, 0), (-200, 0.8, 0.4, 0.3), (200, 1.0, 0.6, 0.5), (600, 1.0, 0.8, 0.7)],
        "opacity": [(0, 0.0), (-500, 0.0), (-200, 0.05), (200, 0.2), (600, 0.4)],
    },
    # ── 肺部 ──────────────────────────────────────────────────────────────────
    "肺部": {
        "color":   [(-1000, 0, 0, 0), (-600, 0.3, 0.5, 0.8), (-400, 0.5, 0.7, 1.0), (0, 0.8, 0.8, 0.8)],
        "opacity": [(-1000, 0.0), (-800, 0.0), (-600, 0.1), (-400, 0.3), (0, 0.0)],
    },
    # ── MRI 脑部 ──────────────────────────────────────────────────────────────
    "MRI 脑部": {
        "color":   [(0, 0, 0, 0), (100, 0.5, 0.3, 0.6), (500, 0.8, 0.6, 0.9), (1000, 1.0, 0.9, 1.0)],
        "opacity": [(0, 0.0), (50, 0.0), (200, 0.1), (500, 0.4), (1000, 0.7)],
    },
    # ── 自定义（不覆盖当前传输函数）──────────────────────────────────────────
    "自定义": None,
}


class VolumeRenderWidget(QtWidgets.QWidget):
    """体绘制组织显示调整工具栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._volume = None       # vtkVolume 引用
        self._renderer = None     # vtkRenderer 引用
        self._vtk_widget = None   # QVTKRenderWindowInteractor 引用
        self._building = False    # 防止初始化时触发回调

        self._init_ui()
        self.hide()

    # ══════════════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════════════

    def _init_ui(self):
        self.setMinimumWidth(280)
        self.setMaximumWidth(340)
        self.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(8, 8, 8, 8)

        # 标题
        title = QtWidgets.QLabel("体绘制工具栏")
        title.setFont(Font.font2)
        title.setStyleSheet("color: #5bc8f5; font-size: 13px; font-weight: bold;")
        root.addWidget(title)

        # ── 预设选择 ──────────────────────────────────────────────────────────
        grp_preset = QtWidgets.QGroupBox("组织预设")
        grp_preset.setStyleSheet(self._grp_style())
        vbox_preset = QtWidgets.QVBoxLayout(grp_preset)
        vbox_preset.setSpacing(4)

        self.combo_preset = QtWidgets.QComboBox()
        self.combo_preset.addItems(list(TISSUE_PRESETS.keys()))
        self.combo_preset.setStyleSheet(self._combo_style())
        self.combo_preset.currentTextChanged.connect(self._on_preset_changed)
        vbox_preset.addWidget(self.combo_preset)

        self.btn_apply = QtWidgets.QPushButton("应用预设")
        self.btn_apply.setStyleSheet(self._btn_primary_style())
        self.btn_apply.clicked.connect(self._apply_preset)
        vbox_preset.addWidget(self.btn_apply)

        root.addWidget(grp_preset)

        # ── 光照参数 ──────────────────────────────────────────────────────────
        grp_light = QtWidgets.QGroupBox("光照参数")
        grp_light.setStyleSheet(self._grp_style())
        grid_light = QtWidgets.QGridLayout(grp_light)
        grid_light.setSpacing(6)

        self.slider_ambient, self.lbl_ambient = self._make_slider(0, 100, 50, "环境光")
        self.slider_diffuse, self.lbl_diffuse = self._make_slider(0, 100, 70, "漫反射")
        self.slider_specular, self.lbl_specular = self._make_slider(0, 100, 50, "镜面反射")

        for row, (name, sl, lbl) in enumerate([
            ("环境光", self.slider_ambient, self.lbl_ambient),
            ("漫反射", self.slider_diffuse, self.lbl_diffuse),
            ("镜面反射", self.slider_specular, self.lbl_specular),
        ]):
            grid_light.addWidget(self._lbl(name), row, 0)
            grid_light.addWidget(sl, row, 1)
            grid_light.addWidget(lbl, row, 2)

        self.chk_shade = QtWidgets.QCheckBox("启用阴影")
        self.chk_shade.setChecked(True)
        self.chk_shade.setStyleSheet("color: #ccc; font-size: 12px;")
        grid_light.addWidget(self.chk_shade, 3, 0, 1, 3)

        self.slider_ambient.valueChanged.connect(self._on_light_changed)
        self.slider_diffuse.valueChanged.connect(self._on_light_changed)
        self.slider_specular.valueChanged.connect(self._on_light_changed)
        self.chk_shade.stateChanged.connect(self._on_light_changed)

        root.addWidget(grp_light)

        # ── 整体不透明度缩放 ──────────────────────────────────────────────────
        grp_opacity = QtWidgets.QGroupBox("整体不透明度")
        grp_opacity.setStyleSheet(self._grp_style())
        h_op = QtWidgets.QHBoxLayout(grp_opacity)
        h_op.setSpacing(6)
        self.slider_opacity_scale, self.lbl_opacity_scale = self._make_slider(0, 100, 100, "")
        self.slider_opacity_scale.valueChanged.connect(self._on_opacity_scale_changed)
        h_op.addWidget(self.slider_opacity_scale)
        h_op.addWidget(self.lbl_opacity_scale)
        root.addWidget(grp_opacity)

        # ── 背景颜色 ──────────────────────────────────────────────────────────
        grp_bg = QtWidgets.QGroupBox("背景颜色")
        grp_bg.setStyleSheet(self._grp_style())
        h_bg = QtWidgets.QHBoxLayout(grp_bg)
        h_bg.setSpacing(6)

        for name, val, attr in [("R", 128, "spin_bg_r"), ("G", 128, "spin_bg_g"), ("B", 128, "spin_bg_b")]:
            h_bg.addWidget(self._lbl(name))
            spin = QtWidgets.QSpinBox()
            spin.setRange(0, 255)
            spin.setValue(val)
            spin.setFixedWidth(55)
            spin.setStyleSheet(self._spin_style())
            spin.valueChanged.connect(self._on_bg_changed)
            setattr(self, attr, spin)
            h_bg.addWidget(spin)

        root.addWidget(grp_bg)

        # ── 重置按钮 ──────────────────────────────────────────────────────────
        self.btn_reset = QtWidgets.QPushButton("重置")
        self.btn_reset.setStyleSheet(self._btn_secondary_style())
        self.btn_reset.clicked.connect(self._reset)
        root.addWidget(self.btn_reset)

        root.addStretch()

    # ══════════════════════════════════════════════════════════════════════════
    # 绑定 VTK 对象
    # ══════════════════════════════════════════════════════════════════════════

    def bind_vtk(self, volume, renderer, vtk_widget):
        """在数据加载后调用，绑定 VTK 体绘制对象"""
        self._volume   = volume
        self._renderer = renderer
        self._vtk_widget = vtk_widget
        # 应用当前预设
        self._apply_preset()

    # ══════════════════════════════════════════════════════════════════════════
    # 事件处理
    # ══════════════════════════════════════════════════════════════════════════

    def _on_preset_changed(self, name):
        pass   # 只在点击"应用"时才生效

    def _apply_preset(self):
        if self._volume is None:
            return
        name = self.combo_preset.currentText()
        preset = TISSUE_PRESETS.get(name)
        if preset is None:
            return   # 自定义：不覆盖

        prop = self._volume.GetProperty()

        ctf = vtk.vtkColorTransferFunction()
        for pt in preset["color"]:
            ctf.AddRGBPoint(*pt)

        otf = vtk.vtkPiecewiseFunction()
        for pt in preset["opacity"]:
            otf.AddPoint(*pt)

        prop.SetColor(ctf)
        prop.SetScalarOpacity(otf)
        self._render()

    def _on_light_changed(self):
        if self._volume is None:
            return
        prop = self._volume.GetProperty()
        prop.SetAmbient(self.slider_ambient.value() / 100.0)
        prop.SetDiffuse(self.slider_diffuse.value() / 100.0)
        prop.SetSpecular(self.slider_specular.value() / 100.0)
        if self.chk_shade.isChecked():
            prop.ShadeOn()
        else:
            prop.ShadeOff()
        self._render()

    def _on_opacity_scale_changed(self, value):
        if self._volume is None:
            return
        self.lbl_opacity_scale.setText(f"{value}%")
        self._volume.GetProperty().SetScalarOpacityUnitDistance(
            max(0.1, (100 - value) / 10.0)
        )
        self._render()

    def _on_bg_changed(self):
        if self._renderer is None:
            return
        r = self.spin_bg_r.value() / 255.0
        g = self.spin_bg_g.value() / 255.0
        b = self.spin_bg_b.value() / 255.0
        self._renderer.SetBackground(r, g, b)
        self._render()

    def _reset(self):
        self.combo_preset.setCurrentIndex(0)
        self.slider_ambient.setValue(50)
        self.slider_diffuse.setValue(70)
        self.slider_specular.setValue(50)
        self.slider_opacity_scale.setValue(100)
        self.chk_shade.setChecked(True)
        self.spin_bg_r.setValue(128)
        self.spin_bg_g.setValue(128)
        self.spin_bg_b.setValue(128)
        self._apply_preset()

    # ══════════════════════════════════════════════════════════════════════════
    # 辅助
    # ══════════════════════════════════════════════════════════════════════════

    def _render(self):
        if self._vtk_widget is not None:
            self._vtk_widget.Render()

    def _make_slider(self, lo, hi, val, _name):
        sl = QtWidgets.QSlider(Qt.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)
        sl.setStyleSheet("""
            QSlider::groove:horizontal { height:4px; background:#444; border-radius:2px; }
            QSlider::handle:horizontal { width:12px; height:12px; margin:-4px 0;
                background:#2d7dd2; border-radius:6px; }
            QSlider::sub-page:horizontal { background:#2d7dd2; border-radius:2px; }
        """)
        lbl = QtWidgets.QLabel(f"{val}")
        lbl.setFixedWidth(36)
        lbl.setStyleSheet("color:#ccc; font-size:11px;")
        sl.valueChanged.connect(lambda v, l=lbl: l.setText(str(v)))
        return sl, lbl

    def _lbl(self, text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet("color:#ccc; font-size:12px;")
        return l

    def _grp_style(self):
        return """
            QGroupBox { color:#aaa; font-size:12px; border:1px solid #444;
                        border-radius:4px; margin-top:8px; padding-top:4px; }
            QGroupBox::title { subcontrol-origin:margin; left:8px; }
        """

    def _combo_style(self):
        return """
            QComboBox { background:#3c3c3c; color:#ddd; border:1px solid #555;
                        border-radius:3px; padding:2px 6px; font-size:12px; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView { background:#3c3c3c; color:#ddd;
                selection-background-color:#2d7dd2; }
        """

    def _spin_style(self):
        return """
            QSpinBox { background:#3c3c3c; color:#ddd; border:1px solid #555;
                       border-radius:3px; padding:2px 4px; font-size:12px; }
        """

    def _btn_primary_style(self):
        return """
            QPushButton { background:#2d7dd2; color:white; border:none;
                          border-radius:4px; padding:4px 12px; font-size:12px; }
            QPushButton:hover { background:#3a8ee0; }
            QPushButton:pressed { background:#1f5fa0; }
        """

    def _btn_secondary_style(self):
        return """
            QPushButton { background:#3c3c3c; color:#ccc; border:1px solid #555;
                          border-radius:4px; padding:4px 12px; font-size:12px; }
            QPushButton:hover { background:#4a4a4a; }
        """
