# -*- coding: utf-8 -*-
"""
加载数据对话框 - 仿 3D Slicer "Add Data into the Scene" 风格
支持选择文件/文件夹，自动识别类型，用户可手动修改
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QCheckBox, QFileDialog, QAbstractItemView, QFrame, QSizePolicy,
    QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from src.model.DataManagerModel import TYPE_RAW, TYPE_SEG, TYPE_3D

# ── 样式 ──────────────────────────────────────────────────────────────────────

_BG     = '#1e1e1e'
_CARD   = '#2d2d2d'
_BORDER = '#3a3a3a'
_HOVER  = '#383838'
_ACCENT = '#3b82f6'
_TEXT   = '#e8e8e8'
_DIM    = '#9ca3af'
_WHITE  = '#ffffff'
_FONT   = '"Microsoft YaHei", "PingFang SC", sans-serif'

_DIALOG_STYLE = f'''
    QDialog {{ background: {_BG}; font-family: {_FONT}; }}
    QLabel  {{ color: {_TEXT}; font-size: 12px; background: transparent; }}
    QTableWidget {{
        background: {_CARD}; color: {_TEXT};
        gridline-color: {_BORDER}; border: 1px solid {_BORDER};
        border-radius: 6px; font-size: 12px; font-family: {_FONT};
    }}
    QTableWidget::item {{ padding: 4px 8px; border: none; }}
    QTableWidget::item:selected {{ background: #254b7c; color: {_WHITE}; }}
    QHeaderView::section {{
        background: #252525; color: {_DIM};
        border: none; border-bottom: 1px solid {_BORDER};
        padding: 6px 8px; font-size: 11px; font-weight: 600;
    }}
    QComboBox {{
        background: #333; color: {_TEXT}; border: 1px solid {_BORDER};
        border-radius: 4px; padding: 2px 4px; font-size: 12px;
    }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox QAbstractItemView {{
        background: #333; color: {_TEXT};
        selection-background-color: {_ACCENT};
    }}
    QCheckBox {{ color: {_TEXT}; font-size: 12px; }}
    QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 3px;
        border: 1px solid #555; background: #333; }}
    QCheckBox::indicator:checked {{ background: {_ACCENT}; border-color: {_ACCENT}; }}
    QScrollBar:vertical {{
        background: transparent; width: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: #555; border-radius: 2px; min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
'''

_BTN_PRIMARY = f'''
    QPushButton {{
        background: {_ACCENT}; color: {_WHITE}; border: none;
        border-radius: 5px; padding: 6px 20px; font-size: 12px; font-weight: 600;
    }}
    QPushButton:hover {{ background: #2563eb; }}
    QPushButton:pressed {{ background: #1d4ed8; }}
    QPushButton:disabled {{ background: #374151; color: #6b7280; }}
'''

_BTN_SECONDARY = f'''
    QPushButton {{
        background: #333; color: {_TEXT}; border: 1px solid {_BORDER};
        border-radius: 5px; padding: 6px 16px; font-size: 12px;
    }}
    QPushButton:hover {{ background: {_HOVER}; color: {_WHITE}; }}
    QPushButton:pressed {{ background: #444; }}
'''

# ── 类型自动识别 ──────────────────────────────────────────────────────────────

# 扩展名 → (fmt, 默认类型)
_EXT_MAP = {
    '.dcm':    ('DICOM', TYPE_RAW),
    '.nii':    ('NII',   TYPE_SEG),
    '.gz':     ('NII',   TYPE_SEG),   # .nii.gz
    '.npy':    ('NPY',   TYPE_RAW),
    '.stl':    ('STL',   TYPE_3D),
    '.vtk':    ('STL',   TYPE_3D),
    '.im0':    ('IM0',   TYPE_RAW),
    '.bim':    ('IM0',   TYPE_RAW),
}

_SEG_KEYWORDS = ['seg', 'segmentation', 'mask', 'label']

_TYPE_LABELS = {
    TYPE_RAW: 'Volume',
    TYPE_SEG: 'Segmentation',
    TYPE_3D:  'Model',
}
_TYPE_OPTIONS = [TYPE_RAW, TYPE_SEG, TYPE_3D]


# def _guess_type(path: str):
    # """根据文件名/扩展名自动猜测格式和类型"""
    # name = os.path.basename(path).lower()

    # # 双扩展名 .nii.gz
    # if name.endswith('.nii.gz') || name.endswith('.nii'):
    #     fmt = 'NII'
    #     # 含分割关键词 → 分割图像，否则原始图像
    #     data_type = TYPE_SEG if any(k in name for k in _SEG_KEYWORDS) else TYPE_RAW
    #     return fmt, data_type

    # ext = os.path.splitext(name)[1]
    # fmt, data_type = _EXT_MAP.get(ext, ('未知', TYPE_RAW))

    # # 关键词修正
    # if fmt in ('NII', 'NPY', 'DICOM'):
    #     if any(k in name for k in _SEG_KEYWORDS):
    #         data_type = TYPE_SEG

    # return fmt, data_type

def _guess_type(path):
    name = path.lower()

    if name.endswith(('.nii', '.nii.gz')):
        return 'NII', TYPE_SEG

    elif name.endswith('.dcm') or os.path.isdir(path):
        return 'DICOM', TYPE_RAW

    elif name.endswith('.npy'):
        return 'NPY', TYPE_RAW

    elif name.endswith(('.stl', '.vtk')):
        return 'STL', TYPE_3D

    elif name.endswith(('.im0', '.bim')):
        return 'IM0', TYPE_RAW

    else:
        return 'UNKNOWN', TYPE_RAW

def _collect_files_from_dir(dir_path: str):
    """从目录中收集所有支持的文件（DICOM 目录只取一个代表条目）"""
    supported_exts = set(_EXT_MAP.keys()) | {'.gz'}
    entries = []
    dcm_dir_added = False

    for fname in sorted(os.listdir(dir_path)):
        fpath = os.path.join(dir_path, fname)
        if not os.path.isfile(fpath):
            continue
        ext = os.path.splitext(fname)[1].lower()
        if fname.lower().endswith('.nii.gz'):
            entries.append(fpath)
        elif ext == '.dcm':
            if not dcm_dir_added:
                # DICOM 目录用文件夹路径代表
                entries.append(dir_path + '/')
                dcm_dir_added = True
        elif ext in supported_exts:
            entries.append(fpath)

    return entries


# ── 对话框 ────────────────────────────────────────────────────────────────────

class AddDataDialog(QDialog):
    """
    加载数据对话框
    返回值：list of (path, fmt, data_type) 或空列表
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('加载数据')
        self.setMinimumSize(700, 460)
        self.setStyleSheet(_DIALOG_STYLE)
        self._entries = []   # list of [path, fmt, data_type, enabled]
        self._combos  = []   # QComboBox per row
        self._checks  = []   # QCheckBox per row
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # ── 顶部标题 ──
        title = QLabel('加载数据到场景')
        title.setStyleSheet(
            f'font-size: 15px; font-weight: 700; color: {_WHITE};'
        )
        root.addWidget(title)

        # ── 选择按钮行 ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_file = QPushButton('＋ 选择文件')
        btn_file.setStyleSheet(_BTN_SECONDARY)
        btn_file.clicked.connect(self._pick_files)
        btn_row.addWidget(btn_file)

        btn_dir = QPushButton('📁 选择文件夹')
        btn_dir.setStyleSheet(_BTN_SECONDARY)
        btn_dir.clicked.connect(self._pick_dir)
        btn_row.addWidget(btn_dir)

        btn_row.addStretch()

        self.lbl_count = QLabel('已选 0 个文件')
        self.lbl_count.setStyleSheet(f'color: {_DIM}; font-size: 11px;')
        btn_row.addWidget(self.lbl_count)

        root.addLayout(btn_row)

        # ── 文件列表表格 ──
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['', '文件路径', '数据类型'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 36)
        self.table.setColumnWidth(2, 130)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        root.addWidget(self.table, 1)

        # ── 底部按钮行 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'background: {_BORDER}; max-height: 1px; border: none;')
        root.addWidget(sep)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        btn_reset = QPushButton('重置')
        btn_reset.setStyleSheet(_BTN_SECONDARY)
        btn_reset.clicked.connect(self._reset)
        bottom.addWidget(btn_reset)

        bottom.addStretch()

        btn_cancel = QPushButton('取消')
        btn_cancel.setStyleSheet(_BTN_SECONDARY)
        btn_cancel.clicked.connect(self.reject)
        bottom.addWidget(btn_cancel)

        self.btn_ok = QPushButton('确认加载')
        self.btn_ok.setStyleSheet(_BTN_PRIMARY)
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept)
        bottom.addWidget(self.btn_ok)

        root.addLayout(bottom)

    # ── 文件选择 ──────────────────────────────────────────────────────────────

    def _pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, '选择文件', '',
            'All Supported (*.dcm *.nii *.nii.gz *.npy *.stl *.vtk *.IM0 *.BIM);;'
            'DICOM (*.dcm);;NIfTI (*.nii *.nii.gz);;NumPy (*.npy);;'
            'STL (*.stl *.vtk);;IM0/BIM (*.IM0 *.BIM);;All Files (*)'
        )
        if paths:
            self._add_paths(paths)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if d:
            paths = _collect_files_from_dir(d)
            if not paths:
                QMessageBox.information(self, '提示', '所选文件夹中未找到支持的文件。')
                return
            self._add_paths(paths)

    def _add_paths(self, paths):
        existing = {e[0] for e in self._entries}
        for p in paths:
            if p not in existing:
                fmt, data_type = _guess_type(p)
                self._entries.append([p, fmt, data_type, True])
        self._rebuild_table()

    # ── 表格构建 ──────────────────────────────────────────────────────────────

    def _rebuild_table(self):
        self._combos.clear()
        self._checks.clear()
        self.table.setRowCount(0)

        for i, (path, fmt, data_type, enabled) in enumerate(self._entries):
            self.table.insertRow(i)
            self.table.setRowHeight(i, 34)

            # 列0：勾选框
            chk = QCheckBox()
            chk.setChecked(enabled)
            chk.stateChanged.connect(lambda state, idx=i: self._on_check(idx, state))
            cell0 = QWidget()
            lay0 = QHBoxLayout(cell0)
            lay0.setContentsMargins(8, 0, 0, 0)
            lay0.addWidget(chk)
            cell0.setStyleSheet('background: transparent;')
            self.table.setCellWidget(i, 0, cell0)
            self._checks.append(chk)

            # 列1：路径
            display = path if not path.endswith('/') else f'[目录] {path.rstrip("/")}'
            path_item = QTableWidgetItem(display)
            path_item.setForeground(QColor(_TEXT))
            path_item.setToolTip(path)
            # 格式小标签颜色
            fmt_colors = {
                'DICOM': '#86efac', 'NII': '#93c5fd',
                'NPY': '#93c5fd', 'STL': '#fcd34d', 'IM0': '#86efac',
            }
            path_item.setForeground(QColor(fmt_colors.get(fmt, _DIM)))
            self.table.setItem(i, 1, path_item)

            # 列2：类型下拉
            combo = QComboBox()
            for t in _TYPE_OPTIONS:
                combo.addItem(_TYPE_LABELS[t], t)
            combo.setCurrentIndex(_TYPE_OPTIONS.index(data_type))
            combo.currentIndexChanged.connect(lambda idx, row=i: self._on_type_change(row, idx))
            self.table.setCellWidget(i, 2, combo)
            self._combos.append(combo)

        self._update_count()

    def _on_check(self, row: int, state: int):
        self._entries[row][3] = (state == Qt.Checked)
        self._update_count()

    def _on_type_change(self, row: int, idx: int):
        self._entries[row][2] = _TYPE_OPTIONS[idx]

    def _update_count(self):
        n = sum(1 for e in self._entries if e[3])
        self.lbl_count.setText(f'已选 {n} 个文件')
        self.btn_ok.setEnabled(n > 0)

    def _reset(self):
        self._entries.clear()
        self._combos.clear()
        self._checks.clear()
        self.table.setRowCount(0)
        self._update_count()

    # ── 结果获取 ──────────────────────────────────────────────────────────────

    def get_selected(self):
        """返回 list of (path, fmt, data_type)，仅勾选项"""
        return [
            (e[0], e[1], e[2])
            for e in self._entries if e[3]
        ]
