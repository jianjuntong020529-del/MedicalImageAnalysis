# -*- coding: utf-8 -*-
"""
图像增强独立窗口
工作流：上传图像 → 选择增强参数 → 应用 → 预览对比 → 导出
"""
import os
import numpy as np

import vtk
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QSizePolicy

from src.service.ImageEnhanceService import ImageEnhanceService
from src.utils.logger import get_logger

logger = get_logger(__name__)

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
        color: {_TEXT}; font-size: 11px; font-weight: 600; font-family: {_FONT};
        border: 1px solid {_BORDER}; border-radius: 6px;
        margin-top: 10px; padding-top: 6px; background: transparent;
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {_WHITE}; }}
'''
_SLIDER = f'''
    QSlider {{ background: transparent; }}
    QSlider::groove:horizontal {{ height: 4px; background: #555; border-radius: 2px; }}
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
        width: 13px; height: 13px; border-radius: 3px; border: 1px solid #555; background: #333;
    }}
    QCheckBox::indicator:checked {{ background: {_ACCENT}; border-color: {_ACCENT}; }}
'''
_BTN_PRIMARY = f'''
    QPushButton {{
        background: {_ACCENT}; color: {_WHITE}; border: none;
        border-radius: 5px; padding: 7px 18px;
        font-size: 12px; font-weight: 600; font-family: {_FONT};
    }}
    QPushButton:hover {{ background: #2563eb; }}
    QPushButton:pressed {{ background: #1d4ed8; }}
    QPushButton:disabled {{ background: #374151; color: #6b7280; }}
'''
_BTN_SECONDARY = f'''
    QPushButton {{
        background: {_CARD2}; color: {_TEXT}; border: 1px solid {_BORDER};
        border-radius: 5px; padding: 7px 18px;
        font-size: 12px; font-family: {_FONT};
    }}
    QPushButton:hover {{ background: {_HOVER}; color: {_WHITE}; }}
'''
_IMG_FRAME = f'background: #111; border: 1px solid {_BORDER}; border-radius: 6px;'


class ImageEnhanceWindow(QtWidgets.QWidget):
    """图像增强独立窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('影像增强')
        self.resize(1100, 720)
        self.setStyleSheet(f'background: {_BG};')
        self.setWindowFlags(Qt.Window)

        self._service    = None   # ImageEnhanceService，加载图像后创建
        self._orig_pixmap = None  # 原始切片 QPixmap
        self._enh_pixmap  = None  # 增强后切片 QPixmap
        self._reader      = None  # vtkDICOMImageReader / vtkNIFTIImageReader
        self._current_slice = 0
        self._max_slice     = 0

        self._init_ui()

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── 顶部标题栏 ────────────────────────────────────────────────────
        hdr = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel('影像增强工作台')
        title.setStyleSheet(
            f'font-size: 15px; font-weight: 700; color: {_WHITE};'
            f'font-family: {_FONT}; background: transparent; border: none;'
        )
        hdr.addWidget(title)
        hdr.addStretch()

        self.btn_load = QtWidgets.QPushButton('📂  上传图像')
        self.btn_load.setStyleSheet(_BTN_PRIMARY)
        self.btn_load.clicked.connect(self._on_load)
        hdr.addWidget(self.btn_load)
        root.addLayout(hdr)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f'background: {_BORDER}; border: none;')
        root.addWidget(sep)

        # ── 主体：左侧参数 + 右侧预览 ─────────────────────────────────────
        body = QtWidgets.QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body, 1)

        # ── 左侧参数面板 ──────────────────────────────────────────────────
        param_panel = QtWidgets.QWidget()
        param_panel.setFixedWidth(270)
        param_panel.setStyleSheet(f'background: {_CARD}; border-radius: 8px; border: 1px solid {_BORDER};')
        pv = QtWidgets.QVBoxLayout(param_panel)
        pv.setContentsMargins(12, 12, 12, 12)
        pv.setSpacing(6)

        pv.addWidget(self._section_label('增强参数（仅作用于当前切片）'))

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f'''
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ background: transparent; width: 4px; }}
            QScrollBar::handle:vertical {{ background: {_BORDER}; border-radius: 2px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        ''')
        inner = QtWidgets.QWidget()
        inner.setStyleSheet('background: transparent;')
        iv = QtWidgets.QVBoxLayout(inner)
        iv.setContentsMargins(0, 0, 0, 0)
        iv.setSpacing(6)

        # A. 去噪 — 中值滤波
        grp_d = QtWidgets.QGroupBox('去噪 — 中值滤波')
        grp_d.setStyleSheet(_GRP)
        vd = QtWidgets.QVBoxLayout(grp_d)
        vd.setSpacing(4); vd.setContentsMargins(8, 4, 8, 8)
        self.chk_median = QtWidgets.QCheckBox('启用')
        self.chk_median.setStyleSheet(_CHK)
        vd.addWidget(self.chk_median)
        self.sl_median, self.lbl_median = self._slider_row(vd, '核大小', 1, 7, 3)
        vd.addWidget(self._tip('消除椒盐噪声，保留边缘'))
        iv.addWidget(grp_d)

        # B. 平滑 — 高斯滤波
        grp_s = QtWidgets.QGroupBox('平滑 — 高斯滤波')
        grp_s.setStyleSheet(_GRP)
        vs = QtWidgets.QVBoxLayout(grp_s)
        vs.setSpacing(4); vs.setContentsMargins(8, 4, 8, 8)
        self.chk_gaussian = QtWidgets.QCheckBox('启用')
        self.chk_gaussian.setStyleSheet(_CHK)
        vs.addWidget(self.chk_gaussian)
        self.sl_gaussian, self.lbl_gaussian = self._slider_row(vs, '柔和度', 1, 30, 10)
        vs.addWidget(self._tip('减少伪影，平滑细节'))
        iv.addWidget(grp_s)

        # C. 锐化 — 拉普拉斯
        grp_sh = QtWidgets.QGroupBox('边缘锐化 — 拉普拉斯')
        grp_sh.setStyleSheet(_GRP)
        vsh = QtWidgets.QVBoxLayout(grp_sh)
        vsh.setSpacing(4); vsh.setContentsMargins(8, 4, 8, 8)
        self.chk_sharpen = QtWidgets.QCheckBox('启用')
        self.chk_sharpen.setStyleSheet(_CHK)
        vsh.addWidget(self.chk_sharpen)
        self.sl_sharpen, self.lbl_sharpen = self._slider_row(vsh, '锐度', 1, 20, 5)
        vsh.addWidget(self._tip('突出微小结节、骨裂纹边界'))
        iv.addWidget(grp_sh)

        # D. CLAHE — 局部对比度自适应均衡
        grp_clahe = QtWidgets.QGroupBox('局部对比度 — CLAHE')
        grp_clahe.setStyleSheet(_GRP)
        vc = QtWidgets.QVBoxLayout(grp_clahe)
        vc.setSpacing(4); vc.setContentsMargins(8, 4, 8, 8)
        self.chk_clahe = QtWidgets.QCheckBox('启用')
        self.chk_clahe.setStyleSheet(_CHK)
        vc.addWidget(self.chk_clahe)
        self.sl_clahe_clip, self.lbl_clahe_clip = self._slider_row(vc, '限幅', 1, 40, 20)
        self.sl_clahe_tile, self.lbl_clahe_tile = self._slider_row(vc, '块大小', 2, 16, 8)
        vc.addWidget(self._tip('同时显示纵隔与肺野细节'))
        iv.addWidget(grp_clahe)

        # E. Gamma 校正
        grp_gamma = QtWidgets.QGroupBox('亮度校正 — Gamma')
        grp_gamma.setStyleSheet(_GRP)
        vg = QtWidgets.QVBoxLayout(grp_gamma)
        vg.setSpacing(4); vg.setContentsMargins(8, 4, 8, 8)
        self.chk_gamma = QtWidgets.QCheckBox('启用')
        self.chk_gamma.setStyleSheet(_CHK)
        vg.addWidget(self.chk_gamma)
        self.sl_gamma, self.lbl_gamma = self._slider_row(vg, 'γ×10', 1, 30, 10)
        vg.addWidget(self._tip('γ<1 提亮暗区，γ>1 压暗高光'))
        iv.addWidget(grp_gamma)

        # F. 直方图均衡化
        grp_he = QtWidgets.QGroupBox('全局对比度 — 直方图均衡')
        grp_he.setStyleSheet(_GRP)
        vh = QtWidgets.QVBoxLayout(grp_he)
        vh.setSpacing(4); vh.setContentsMargins(8, 4, 8, 8)
        self.chk_histeq = QtWidgets.QCheckBox('启用')
        self.chk_histeq.setStyleSheet(_CHK)
        vh.addWidget(self.chk_histeq)
        vh.addWidget(self._tip('拉伸全局灰度分布，增强整体对比'))
        iv.addWidget(grp_he)

        iv.addStretch()
        scroll.setWidget(inner)
        pv.addWidget(scroll, 1)

        # 操作按钮
        self.btn_apply = QtWidgets.QPushButton('▶  应用增强')
        self.btn_apply.setStyleSheet(_BTN_PRIMARY)
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._on_apply)
        pv.addWidget(self.btn_apply)

        self.btn_reset_params = QtWidgets.QPushButton('重置参数')
        self.btn_reset_params.setStyleSheet(_BTN_SECONDARY)
        self.btn_reset_params.clicked.connect(self._on_reset_params)
        pv.addWidget(self.btn_reset_params)

        body.addWidget(param_panel)

        # ── 右侧预览区 ────────────────────────────────────────────────────
        preview = QtWidgets.QWidget()
        preview.setStyleSheet('background: transparent;')
        pv2 = QtWidgets.QVBoxLayout(preview)
        pv2.setContentsMargins(0, 0, 0, 0)
        pv2.setSpacing(8)

        slice_row = QtWidgets.QHBoxLayout()
        slice_row.addWidget(self._lbl('切片'))
        self.sl_slice = QtWidgets.QSlider(Qt.Horizontal)
        self.sl_slice.setRange(0, 0)
        self.sl_slice.setStyleSheet(_SLIDER)
        self.sl_slice.valueChanged.connect(self._on_slice_changed)
        slice_row.addWidget(self.sl_slice, 1)
        self.lbl_slice = QtWidgets.QLabel('0 / 0')
        self.lbl_slice.setFixedWidth(60)
        self.lbl_slice.setStyleSheet(f'font-size: 11px; color: {_SEC}; font-family: {_FONT};'
                                     f'background: transparent; border: none;')
        slice_row.addWidget(self.lbl_slice)
        pv2.addLayout(slice_row)

        img_row = QtWidgets.QHBoxLayout()
        img_row.setSpacing(10)
        self.lbl_orig = self._img_label('原始图像')
        self.lbl_enh  = self._img_label('增强结果')
        img_row.addWidget(self._img_card('原始图像', self.lbl_orig))
        img_row.addWidget(self._img_card('增强结果', self.lbl_enh))
        pv2.addLayout(img_row, 1)

        self.status_lbl = QtWidgets.QLabel('请先上传图像')
        self.status_lbl.setStyleSheet(
            f'font-size: 11px; color: {_SEC}; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        pv2.addWidget(self.status_lbl)

        export_row = QtWidgets.QHBoxLayout()
        export_row.addStretch()
        self.btn_export_orig = QtWidgets.QPushButton('导出原始切片')
        self.btn_export_orig.setStyleSheet(_BTN_SECONDARY)
        self.btn_export_orig.setEnabled(False)
        self.btn_export_orig.clicked.connect(lambda: self._on_export(enhanced=False))
        self.btn_export_enh = QtWidgets.QPushButton('导出增强切片')
        self.btn_export_enh.setStyleSheet(_BTN_PRIMARY)
        self.btn_export_enh.setEnabled(False)
        self.btn_export_enh.clicked.connect(lambda: self._on_export(enhanced=True))
        export_row.addWidget(self.btn_export_orig)
        export_row.addWidget(self.btn_export_enh)
        pv2.addLayout(export_row)

        body.addWidget(preview, 1)

    # ── 槽函数 ────────────────────────────────────────────────────────────────

    def _on_load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, '选择图像文件', '',
            'All Supported (*.dcm *.nii *.nii.gz *.npy *.png *.jpg *.jpeg *.bmp *.tif *.tiff);;'
            'DICOM (*.dcm);;NIfTI (*.nii *.nii.gz);;NumPy (*.npy);;'
            'Image (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)'
        )
        if not path:
            # 也支持选择 DICOM 文件夹
            folder = QFileDialog.getExistingDirectory(self, '或选择 DICOM 文件夹')
            if not folder:
                return
            path = folder

        try:
            self._load_image(path)
        except Exception as e:
            QMessageBox.critical(self, '加载失败', str(e))
            logger.error(f"Load failed: {e}", exc_info=True)

    def _load_image(self, path):
        """加载图像，初始化 reader 和 service"""
        import SimpleITK as sitk

        name_lower = path.lower() if not os.path.isdir(path) else ''

        if os.path.isdir(path):
            # DICOM 文件夹
            reader = sitk.ImageSeriesReader()
            names = reader.GetGDCMSeriesFileNames(path)
            if not names:
                raise RuntimeError(f'目录中未找到 DICOM 序列：{path}')
            reader.SetFileNames(names)
            image = reader.Execute()
            arr = sitk.GetArrayFromImage(image)   # (Z, Y, X)

        elif name_lower.endswith(('.nii', '.nii.gz')):
            image = sitk.ReadImage(path)
            arr = sitk.GetArrayFromImage(image)

        elif name_lower.endswith('.npy'):
            arr = np.load(path)

        elif name_lower.endswith('.dcm'):
            reader = sitk.ImageSeriesReader()
            folder = os.path.dirname(path)
            names = reader.GetGDCMSeriesFileNames(folder)
            reader.SetFileNames(names)
            image = reader.Execute()
            arr = sitk.GetArrayFromImage(image)

        elif name_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
            # 普通图片：读取为灰度，shape → (1, H, W) 当作单切片体积
            qimg = QtGui.QImage(path)
            if qimg.isNull():
                raise RuntimeError(f'无法读取图片：{path}')
            qimg = qimg.convertToFormat(QtGui.QImage.Format_Grayscale8)
            w, h = qimg.width(), qimg.height()
            ptr = qimg.bits()
            ptr.setsize(h * w)
            arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, w)).astype(np.float32)
            arr = arr[np.newaxis, ...]   # (1, H, W)

        else:
            raise ValueError(f'不支持的文件格式：{path}')

        self._volume = arr.astype(np.float32)
        self._max_slice = self._volume.shape[0] - 1
        self._current_slice = self._max_slice // 2

        self._service = _NumpyEnhanceService(self._volume)

        self.sl_slice.setRange(0, self._max_slice)
        self.sl_slice.setValue(self._current_slice)
        self.btn_apply.setEnabled(True)
        self.btn_export_orig.setEnabled(True)
        self._enh_pixmap = None
        self.btn_export_enh.setEnabled(False)
        self.status_lbl.setText(
            f'已加载：{os.path.basename(path)}  |  '
            f'尺寸：{self._volume.shape[-1]}×{self._volume.shape[-2]}×{self._volume.shape[0]}'
        )
        self._render_slice(self._current_slice, enhanced=False)
        logger.info(f"Image loaded: {path}, shape={self._volume.shape}")

    def _on_slice_changed(self, val):
        self._current_slice = val
        self.lbl_slice.setText(f'{val} / {self._max_slice}')
        self._render_slice(val, enhanced=False)
        # 若该切片已有增强结果则同步显示，否则清空右侧
        if self._service and val in self._service._result:
            self._render_slice(val, enhanced=True)
        else:
            self._enh_pixmap = None
            self.lbl_enh.clear()

    def _on_apply(self):
        if self._service is None:
            return
        enabled = {
            'median':   self.chk_median.isChecked(),
            'gaussian': self.chk_gaussian.isChecked(),
            'sharpen':  self.chk_sharpen.isChecked(),
            'clahe':    self.chk_clahe.isChecked(),
            'gamma':    self.chk_gamma.isChecked(),
            'histeq':   self.chk_histeq.isChecked(),
        }
        params = {
            'median_size':   self.sl_median.value() * 2 - 1,
            'gaussian_std':  self.sl_gaussian.value() / 10.0,
            'sharpen_alpha': self.sl_sharpen.value() / 10.0,
            'clahe_clip':    self.sl_clahe_clip.value() / 10.0,
            'clahe_tile':    self.sl_clahe_tile.value(),
            'gamma':         self.sl_gamma.value() / 10.0,
        }
        try:
            self._service.apply(self._current_slice, enabled, params)
            self._render_slice(self._current_slice, enhanced=True)
            self.btn_export_enh.setEnabled(True)
            self.status_lbl.setText('增强完成，可导出结果')
            logger.info(f"Enhancement applied on slice {self._current_slice}: {enabled}")
        except Exception as e:
            QMessageBox.critical(self, '增强失败', str(e))
            logger.error(f"Enhancement failed: {e}", exc_info=True)

    def _on_reset_params(self):
        for chk in (self.chk_median, self.chk_gaussian, self.chk_sharpen,
                    self.chk_clahe, self.chk_gamma, self.chk_histeq):
            chk.setChecked(False)
        self.sl_median.setValue(3)
        self.sl_gaussian.setValue(10)
        self.sl_sharpen.setValue(5)
        self.sl_clahe_clip.setValue(20)
        self.sl_clahe_tile.setValue(8)
        self.sl_gamma.setValue(10)
        self._enh_pixmap = None
        self.lbl_enh.clear()
        self.btn_export_enh.setEnabled(False)
        self.status_lbl.setText('参数已重置')

    def _on_export(self, enhanced: bool):
        pixmap = self._enh_pixmap if enhanced else self._orig_pixmap
        if pixmap is None:
            return
        tag = 'enhanced' if enhanced else 'original'
        path, _ = QFileDialog.getSaveFileName(
            self, '导出切片', f'slice_{self._current_slice}_{tag}.png',
            'PNG Image (*.png);;JPEG Image (*.jpg)'
        )
        if not path:
            return
        if pixmap.save(path):
            QMessageBox.information(self, '导出成功', f'已保存至：\n{path}')
        else:
            QMessageBox.critical(self, '导出失败', '文件写入失败')

    # ── 渲染 ──────────────────────────────────────────────────────────────────

    def _render_slice(self, idx: int, enhanced: bool):
        """将指定切片渲染为 QPixmap 并显示"""
        if self._service is None:
            return
        arr = self._service.get_slice(idx, enhanced=enhanced)
        pixmap = self._array_to_pixmap(arr)
        if enhanced:
            self._enh_pixmap = pixmap
            self._set_pixmap(self.lbl_enh, pixmap)
        else:
            self._orig_pixmap = pixmap
            self._set_pixmap(self.lbl_orig, pixmap)

    @staticmethod
    def _array_to_pixmap(arr: np.ndarray) -> QtGui.QPixmap:
        """2D float array → 归一化灰度 QPixmap"""
        mn, mx = arr.min(), arr.max()
        if mx > mn:
            norm = ((arr - mn) / (mx - mn) * 255).astype(np.uint8)
        else:
            norm = np.zeros_like(arr, dtype=np.uint8)
        h, w = norm.shape
        img = QtGui.QImage(norm.data, w, h, w, QtGui.QImage.Format_Grayscale8)
        return QtGui.QPixmap.fromImage(img.copy())

    @staticmethod
    def _set_pixmap(label: QtWidgets.QLabel, pixmap: QtGui.QPixmap):
        scaled = pixmap.scaled(
            label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._orig_pixmap:
            self._set_pixmap(self.lbl_orig, self._orig_pixmap)
        if self._enh_pixmap:
            self._set_pixmap(self.lbl_enh, self._enh_pixmap)

    # ── UI 辅助 ───────────────────────────────────────────────────────────────

    def _section_label(self, text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(
            f'font-size: 12px; font-weight: 700; color: {_WHITE};'
            f'font-family: {_FONT}; background: transparent; border: none;'
        )
        return l

    def _lbl(self, text, w=40):
        l = QtWidgets.QLabel(text)
        l.setFixedWidth(w)
        l.setStyleSheet(f'font-size: 11px; color: {_SEC}; font-family: {_FONT};'
                        f'background: transparent; border: none;')
        return l

    def _tip(self, text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet(f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
                        f'background: transparent; border: none;')
        return l

    def _slider_row(self, parent_layout, label, lo, hi, val):
        h = QtWidgets.QHBoxLayout(); h.setSpacing(6)
        h.addWidget(self._lbl(label))
        sl = QtWidgets.QSlider(Qt.Horizontal)
        sl.setRange(lo, hi); sl.setValue(val)
        sl.setStyleSheet(_SLIDER)
        lbl = QtWidgets.QLabel(str(val))
        lbl.setFixedWidth(22)
        lbl.setStyleSheet(f'font-size: 10px; color: {_SEC}; font-family: {_FONT};'
                          f'background: transparent; border: none;')
        sl.valueChanged.connect(lambda v, l=lbl: l.setText(str(v)))
        h.addWidget(sl, 1); h.addWidget(lbl)
        parent_layout.addLayout(h)
        return sl, lbl

    def _img_label(self, _):
        l = QtWidgets.QLabel()
        l.setAlignment(Qt.AlignCenter)
        l.setStyleSheet('background: transparent; border: none;')
        l.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return l

    def _img_card(self, title, img_label):
        card = QtWidgets.QWidget()
        card.setStyleSheet(f'background: {_CARD}; border-radius: 8px; border: 1px solid {_BORDER};')
        cv = QtWidgets.QVBoxLayout(card)
        cv.setContentsMargins(8, 8, 8, 8); cv.setSpacing(4)
        t = QtWidgets.QLabel(title)
        t.setStyleSheet(f'font-size: 11px; font-weight: 600; color: {_WHITE};'
                        f'font-family: {_FONT}; background: transparent; border: none;')
        cv.addWidget(t)
        frame = QtWidgets.QFrame()
        frame.setStyleSheet(_IMG_FRAME)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        fl = QtWidgets.QVBoxLayout(frame)
        fl.setContentsMargins(4, 4, 4, 4)
        fl.addWidget(img_label)
        cv.addWidget(frame, 1)
        return card


# ── 纯 NumPy 增强服务（不依赖 BaseModel）────────────────────────────────────

class _NumpyEnhanceService:
    """基于 scipy/numpy/cv2 的图像增强，只处理单张切片，毫秒级响应"""

    def __init__(self, volume: np.ndarray):
        self._orig   = volume          # (Z, Y, X) float32
        self._result: dict = {}        # {slice_idx: enhanced_2d_array}

    def apply(self, idx: int, enabled: dict, params: dict):
        import scipy.ndimage as ndi
        import cv2

        arr = self._orig[idx].copy()   # 单切片 (H, W)

        # ── 1. 去噪：中值滤波 ─────────────────────────────────────────────
        if enabled.get('median'):
            sz = int(params.get('median_size', 3))
            sz = sz if sz % 2 == 1 else sz + 1
            arr = ndi.median_filter(arr, size=sz)

        # ── 2. 平滑：高斯滤波 ─────────────────────────────────────────────
        if enabled.get('gaussian'):
            std = float(params.get('gaussian_std', 1.0))
            arr = ndi.gaussian_filter(arr, sigma=std)

        # ── 3. 锐化：拉普拉斯增强 ─────────────────────────────────────────
        if enabled.get('sharpen'):
            alpha = float(params.get('sharpen_alpha', 0.5))
            lap = ndi.laplace(arr)
            arr = arr + alpha * lap

        # ── 4. CLAHE：限制对比度自适应直方图均衡 ──────────────────────────
        if enabled.get('clahe'):
            clip  = float(params.get('clahe_clip', 2.0))
            tile  = int(params.get('clahe_tile', 8))
            # 归一化到 uint16 再做 CLAHE，保留更多灰度层次
            mn, mx = arr.min(), arr.max()
            if mx > mn:
                u16 = ((arr - mn) / (mx - mn) * 65535).astype(np.uint16)
            else:
                u16 = np.zeros_like(arr, dtype=np.uint16)
            clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tile, tile))
            u16 = clahe.apply(u16)
            arr = u16.astype(np.float32) / 65535.0 * (mx - mn) + mn

        # ── 5. Gamma 校正 ─────────────────────────────────────────────────
        if enabled.get('gamma'):
            gamma = float(params.get('gamma', 1.0))
            mn, mx = arr.min(), arr.max()
            if mx > mn:
                norm = (arr - mn) / (mx - mn)          # [0, 1]
                norm = np.power(np.clip(norm, 0, 1), gamma)
                arr  = norm * (mx - mn) + mn

        # ── 6. 直方图均衡化 ───────────────────────────────────────────────
        if enabled.get('histeq'):
            mn, mx = arr.min(), arr.max()
            if mx > mn:
                u8 = ((arr - mn) / (mx - mn) * 255).astype(np.uint8)
                u8 = cv2.equalizeHist(u8)
                arr = u8.astype(np.float32) / 255.0 * (mx - mn) + mn

        self._result[idx] = arr

    def get_slice(self, idx: int, enhanced: bool) -> np.ndarray:
        if enhanced and idx in self._result:
            return self._result[idx]
        idx = max(0, min(idx, self._orig.shape[0] - 1))
        return self._orig[idx]
