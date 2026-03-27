# -*- coding: utf-8 -*-
"""
数据管理面板 - 深色专业风，医学影像软件侧边栏
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QTableWidget, QTableWidgetItem,
    QHeaderView, QGraphicsDropShadowEffect, QCheckBox, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QBrush, QFont

from src.model.DataManagerModel import (
    DataManagerModel, DataItem, TYPE_RAW, TYPE_SEG, TYPE_3D, FMT_COLORS
)

# ── 设计 Token ────────────────────────────────────────────────────────────────

_BG         = '#1e1e1e'
_CARD       = '#2d2d2d'
_CARD2      = '#333333'
_BORDER     = '#3a3a3a'
_HOVER      = '#383838'
_SEL        = '#254b7c'
_ACCENT     = '#3b82f6'
_TEXT       = '#e8e8e8'
_TEXT_SEC   = '#9ca3af'
_TEXT_HINT  = '#6b7280'
_WHITE      = '#ffffff'
_FONT       = '"Microsoft YaHei", "PingFang SC", sans-serif'

# ── 样式块 ────────────────────────────────────────────────────────────────────

_BTN_ICON = f'''
    QPushButton {{
        background: transparent; border: none;
        color: {_TEXT_SEC}; font-size: 13px; border-radius: 4px; padding: 2px 4px;
    }}
    QPushButton:hover {{ color: {_WHITE}; background: {_HOVER}; }}
    QPushButton:pressed {{ color: #ef4444; background: #3a1a1a; }}
'''

_BTN_COLLAPSE = f'''
    QPushButton {{
        background: transparent; border: 1px solid {_BORDER};
        color: {_TEXT_SEC}; font-size: 11px; border-radius: 4px; padding: 2px 6px;
    }}
    QPushButton:hover {{ color: {_WHITE}; border-color: #555; background: {_HOVER}; }}
'''

_BTN_DELETE_HDR = f'''
    QPushButton {{
        background: transparent; border: 1px solid #5a2020;
        color: #f87171; font-size: 11px; border-radius: 4px; padding: 2px 6px;
    }}
    QPushButton:hover {{ background: #3a1a1a; border-color: #ef4444; color: #fca5a5; }}
'''

_TABLE_STYLE = f'''
    QTableWidget {{
        background: {_CARD}; color: {_TEXT};
        gridline-color: {_BORDER}; border: none;
        font-size: 12px; font-family: {_FONT};
    }}
    QTableWidget::item {{
        padding: 5px 8px; border: none;
        border-bottom: 1px solid {_BORDER};
    }}
    QTableWidget::item:selected {{ background: {_SEL}; color: {_WHITE}; }}
    QHeaderView::section {{
        background: {_CARD}; color: {_TEXT_HINT};
        border: none; padding: 4px 8px;
        font-size: 11px; font-family: {_FONT};
    }}
'''

_SCROLL_STYLE = f'''
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: transparent; width: 4px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {_BORDER}; border-radius: 2px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: #555; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
'''


def _card_style(bg=_CARD, radius=8):
    return (
        f'background: {bg}; border-radius: {radius}px;'
        f'border: 1px solid {_BORDER};'
    )


def _drop_shadow(widget, blur=16, dy=2, alpha=60):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, dy)
    eff.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(eff)


# ── 颜色圆点 ──────────────────────────────────────────────────────────────────

class ColorDot(QWidget):
    color_picked = pyqtSignal(str)  # 用户选择了新颜色，传 hex 字符串

    def __init__(self, color: str, size=10, clickable=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)
        self._clickable = clickable
        if clickable:
            self.setCursor(Qt.PointingHandCursor)
            self.setToolTip('点击更改颜色')

    def set_color(self, c: str):
        self._color = QColor(c)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(self._color))
        if self._clickable:
            p.setPen(QColor('#888888'))
        else:
            p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, self.width() - 1, self.height() - 1)

    def mousePressEvent(self, e):
        if self._clickable and e.button() == Qt.LeftButton:
            from PyQt5.QtWidgets import QApplication
            # 临时清除全局样式，避免深色主题污染颜色选择器
            app = QApplication.instance()
            saved_style = app.styleSheet()
            app.setStyleSheet('')
            color = QColorDialog.getColor(self._color, None, '选择颜色')
            app.setStyleSheet(saved_style)
            if color.isValid():
                self._color = color
                self.update()
                self.color_picked.emit(color.name())
            e.accept()  # 阻止事件冒泡到父级 DataItemRow，避免触发 item_activated
            return
        super().mousePressEvent(e)


# ── 格式徽章 ──────────────────────────────────────────────────────────────────

class FmtBadge(QLabel):
    _MAP = {
        'DICOM': ('#86efac', '#14532d'),
        'NII':   ('#93c5fd', '#1e3a5f'),
        'NPY':   ('#93c5fd', '#1e3a5f'),
        'STL':   ('#fcd34d', '#451a03'),
        'IM0':   ('#86efac', '#14532d'),
    }

    def __init__(self, fmt: str, parent=None):
        super().__init__(fmt, parent)
        fg, bg = self._MAP.get(fmt, (_TEXT_SEC, _CARD2))
        self.setStyleSheet(
            f'font-size: 10px; font-weight: 600; font-family: {_FONT};'
            f'padding: 1px 6px; border-radius: 4px;'
            f'color: {fg}; background: {bg};'
        )
        self.setFixedHeight(16)


# ── 数量气泡 ──────────────────────────────────────────────────────────────────

class CountBubble(QLabel):
    def __init__(self, parent=None):
        super().__init__('0', parent)
        self.setFixedSize(20, 20)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f'font-size: 10px; font-weight: 700; font-family: {_FONT};'
            f'color: {_WHITE}; background: {_ACCENT};'
            f'border-radius: 10px;'
        )

    def set_count(self, n: int):
        self.setText(str(n))


# ── 单条数据行 ────────────────────────────────────────────────────────────────

class DataItemRow(QWidget):
    clicked = pyqtSignal(str)
    check_changed = pyqtSignal(str, bool)  # (name, checked) 复选框变化
    delete_requested = pyqtSignal(str)
    color_changed = pyqtSignal(str, str)   # (name, hex_color) 颜色变化

    def __init__(self, item: DataItem, parent=None):
        super().__init__(parent)
        self.item_name = item.name
        self.item_type = item.data_type
        self._selected = False
        self.setFixedHeight(30)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet('background: transparent; border-radius: 6px;')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 4, 0)
        layout.setSpacing(5)

        # 复选框（控制显示/隐藏）— 原始图像不提供复选框（排他性显示，通过点击切换）
        self.chk = QCheckBox()
        self.chk.setChecked(item.visible)
        self.chk.setFixedSize(16, 16)
        self.chk.setStyleSheet(f'''
            QCheckBox::indicator {{
                width: 13px; height: 13px;
                border-radius: 3px; border: 1px solid #555; background: #333;
            }}
            QCheckBox::indicator:checked {{
                background: {_ACCENT}; border-color: {_ACCENT};
            }}
        ''')
        self.chk.stateChanged.connect(self._on_check)
        layout.addWidget(self.chk)
        if item.data_type == TYPE_RAW:
            self.chk.hide()

        # 颜色圆点（SEG/3D 可点击选色）
        clickable = item.data_type in (TYPE_SEG, TYPE_3D)
        self.dot = ColorDot(item.color, 10, clickable=clickable)
        self.dot.color_picked.connect(lambda c: self.color_changed.emit(self.item_name, c))
        layout.addWidget(self.dot)

        # 文件名
        self.name_lbl = QLabel(item.name)
        self.name_lbl.setStyleSheet(
            f'font-size: 12px; color: {_TEXT}; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        self.name_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name_lbl, 1)

        # 格式徽章
        self.badge = FmtBadge(item.fmt)
        layout.addWidget(self.badge)

        # 删除按钮
        del_btn = QPushButton('✕')
        del_btn.setFixedSize(18, 18)
        del_btn.setToolTip('删除')
        del_btn.setStyleSheet(
            f'QPushButton {{ background: transparent; border: none;'
            f'color: {_TEXT_HINT}; font-size: 10px; border-radius: 3px; }}'
            f'QPushButton:hover {{ color: #ef4444; background: #3a1a1a; }}'
        )
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.item_name))
        layout.addWidget(del_btn)

    def _on_check(self, state):
        checked = (state == Qt.Checked)
        self._update_name_color(checked)
        self.check_changed.emit(self.item_name, checked)

    def _update_name_color(self, visible=None):
        if visible is None:
            visible = self.chk.isChecked()
        c = _TEXT if visible else _TEXT_HINT
        w = '600' if self._selected else '400'
        self.name_lbl.setStyleSheet(
            f'font-size: 12px; color: {c}; font-weight: {w};'
            f'font-family: {_FONT}; background: transparent; border: none;'
        )

    def set_selected(self, sel: bool):
        self._selected = sel
        bg = _SEL if sel else 'transparent'
        self.setStyleSheet(f'background: {bg}; border-radius: 6px;')
        self._update_name_color()

    def set_checked(self, checked: bool):
        self.chk.blockSignals(True)
        self.chk.setChecked(checked)
        self.chk.blockSignals(False)
        self._update_name_color(checked)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.item_name)
        super().mousePressEvent(e)

    def enterEvent(self, _):
        if not self._selected:
            self.setStyleSheet(f'background: {_HOVER}; border-radius: 6px;')

    def leaveEvent(self, _):
        if not self._selected:
            self.setStyleSheet('background: transparent; border-radius: 6px;')


# ── 分组标题行 ────────────────────────────────────────────────────────────────

class SectionHeader(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, title: str, extra_widget=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self._expanded = True
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f'background: {_CARD}; border-radius: 6px;')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(7)

        self.arrow = QLabel('▾')
        self.arrow.setFixedWidth(12)
        self.arrow.setStyleSheet(
            f'color: {_TEXT_SEC}; font-size: 12px;'
            f'background: transparent; border: none;'
        )
        layout.addWidget(self.arrow)

        lbl = QLabel(title)
        lbl.setStyleSheet(
            f'font-size: 12px; font-weight: 600; color: {_TEXT};'
            f'font-family: {_FONT}; background: transparent; border: none;'
        )
        layout.addWidget(lbl, 1)

        if extra_widget is not None:
            layout.addWidget(extra_widget)

        self.bubble = CountBubble()
        layout.addWidget(self.bubble)

    def set_count(self, n: int):
        self.bubble.set_count(n)

    def mousePressEvent(self, e):
        # 如果点击的是子控件（如按钮），不触发折叠
        if self.childAt(e.pos()) is not None:
            super().mousePressEvent(e)
            return
        self._expanded = not self._expanded
        self.arrow.setText('▾' if self._expanded else '▸')
        self.toggled.emit(self._expanded)

    def enterEvent(self, _):
        self.setStyleSheet(f'background: {_HOVER}; border-radius: 6px;')

    def leaveEvent(self, _):
        self.setStyleSheet(f'background: {_CARD}; border-radius: 6px;')


# ── 属性面板 ──────────────────────────────────────────────────────────────────

class PropertiesPanel(QFrame):
    _DEFAULT = [
        ('文件名', ''), ('患者姓名', ''), ('数据类型', ''),
        ('格式', ''), ('矩阵尺寸', ''), ('体素间距', ''),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f'QFrame {{ background: {_CARD}; border-radius: 8px;'
            f'border: 1px solid {_BORDER}; }}'
        )
        _drop_shadow(self, blur=12, dy=2, alpha=50)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(10, 8, 10, 8)
        self._root.setSpacing(0)

        hdr = QHBoxLayout()
        t = QLabel('属性')
        t.setStyleSheet(
            f'font-size: 11px; font-weight: 700; color: {_WHITE};'
            f'letter-spacing: 1px; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        hdr.addWidget(t)
        hdr.addStretch()
        self._root.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f'background: {_BORDER}; border: none; margin-bottom: 4px;')
        self._root.addWidget(sep)

        # 行容器
        self._rows_widget = QWidget()
        self._rows_widget.setStyleSheet('background: transparent;')
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 2, 0, 0)
        self._rows_layout.setSpacing(0)
        self._root.addWidget(self._rows_widget)

        self.clear()

    def _set_rows(self, rows: list):
        # 清空旧行
        lo = self._rows_layout
        while lo.count():
            item = lo.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        _key_style = (
            f'font-size: 10px; color: {_TEXT_SEC}; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        _val_style_filled = (
            f'font-size: 10px; font-weight: 700; color: {_WHITE};'
            f'font-family: {_FONT}; background: transparent; border: none;'
        )
        _val_style_empty = (
            f'font-size: 10px; font-weight: 700; color: {_TEXT_HINT};'
            f'font-family: {_FONT}; background: transparent; border: none;'
        )

        for i, (k, v) in enumerate(rows):
            row = QWidget()
            row.setFixedHeight(22)
            row.setStyleSheet(
                f'background: {"#2a2a2a" if i % 2 == 0 else "transparent"};'
                f'border-radius: 3px;'
            )
            rl = QHBoxLayout(row)
            rl.setContentsMargins(4, 0, 4, 0)
            rl.setSpacing(4)

            key_lbl = QLabel(k)
            key_lbl.setStyleSheet(_key_style)
            key_lbl.setFixedWidth(54)

            val_str = str(v) if v and v != '—' else '—'
            val_lbl = QLabel(val_str)
            val_lbl.setStyleSheet(_val_style_filled if (v and v != '—') else _val_style_empty)
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_lbl.setWordWrap(False)
            # 超长文本截断显示，鼠标悬停显示完整内容
            val_lbl.setToolTip(val_str)

            rl.addWidget(key_lbl)
            rl.addWidget(val_lbl, 1)
            lo.addWidget(row)

    def update_item(self, item: DataItem, seg_items=None):
        tm = {TYPE_RAW: 'Volume', TYPE_SEG: 'Segmentation', TYPE_3D: 'Model'}
        rows = [
            ('文件名',   item.filename),
            ('患者姓名', item.patient_name),
            ('数据类型', tm.get(item.data_type, '—')),
            ('格式',     item.fmt),
            ('矩阵尺寸', item.dim),
            ('体素间距', item.spacing),
        ]
        if item.data_type == TYPE_RAW and seg_items:
            rows.append(('叠加分割', ', '.join(s.name for s in seg_items)))
        elif item.data_type == TYPE_3D:
            rows.append(('显示', '体绘制窗口'))
        self._set_rows(rows)

    def clear(self):
        self._set_rows(self._DEFAULT)


# ── 主面板 ────────────────────────────────────────────────────────────────────

class DataManagerPanel(QWidget):
    add_data_requested = pyqtSignal()
    # 点击行触发叠加/显示：(item_name, data_type, path)
    item_activated = pyqtSignal(str, int, str)
    # 复选框切换：(item_name, data_type, checked)
    visibility_changed = pyqtSignal(str, int, bool)
    # 数据删除：(item_name, data_type)
    item_deleted = pyqtSignal(str, int)
    # 颜色变更：(item_name, data_type, hex_color)
    color_changed = pyqtSignal(str, int, str)
    # 三维数据全局颜色变更：(hex_color,)
    global_3d_color_changed = pyqtSignal(str)

    def __init__(self, model: DataManagerModel, parent=None):
        super().__init__(parent)
        self.model = model
        self._selected_name = ''
        self._row_widgets: dict = {}

        self.setMinimumWidth(220)
        self.setMaximumWidth(300)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setStyleSheet(f'background: {_BG};')

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── 加载数据按钮 ──
        btn_add = QPushButton('＋  加载数据')
        btn_add.setFixedHeight(34)
        btn_add.setStyleSheet(f'''
            QPushButton {{
                background: {_ACCENT}; color: {_WHITE}; border: none;
                border-radius: 6px; font-size: 13px; font-weight: 700;
                font-family: {_FONT};
            }}
            QPushButton:hover {{ background: #2563eb; }}
            QPushButton:pressed {{ background: #1d4ed8; }}
        ''')
        btn_add.clicked.connect(self.add_data_requested)
        root.addWidget(btn_add)

        # ── 标题栏 ──
        hdr = QFrame()
        hdr.setFixedHeight(36)
        hdr.setStyleSheet(_card_style(_CARD, 8))
        _drop_shadow(hdr, blur=8, dy=1, alpha=40)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(12, 0, 8, 0)
        hl.setSpacing(6)

        title = QLabel('数据管理器')
        title.setStyleSheet(
            f'font-size: 12px; font-weight: 700; color: {_WHITE};'
            f'font-family: {_FONT}; background: transparent; border: none;'
        )
        hl.addWidget(title, 1)

        btn_collapse = QPushButton('折叠')
        btn_collapse.setFixedHeight(22)
        btn_collapse.setStyleSheet(_BTN_COLLAPSE)
        btn_collapse.clicked.connect(self._collapse_all)
        hl.addWidget(btn_collapse)

        btn_del = QPushButton('删除')
        btn_del.setFixedHeight(22)
        btn_del.setStyleSheet(_BTN_DELETE_HDR)
        btn_del.clicked.connect(self._delete_selected)
        hl.addWidget(btn_del)

        root.addWidget(hdr)

        # ── 列表卡片 ──
        list_card = QFrame()
        list_card.setStyleSheet(_card_style(_CARD, 8))
        _drop_shadow(list_card, blur=10, dy=2, alpha=50)
        lc_layout = QVBoxLayout(list_card)
        lc_layout.setContentsMargins(6, 6, 6, 6)
        lc_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(_SCROLL_STYLE)

        self._tree_widget = QWidget()
        self._tree_widget.setStyleSheet('background: transparent;')
        self._tree_layout = QVBoxLayout(self._tree_widget)
        self._tree_layout.setContentsMargins(0, 0, 0, 0)
        self._tree_layout.setSpacing(3)
        self._tree_layout.setAlignment(Qt.AlignTop)

        self._sec_raw, self._body_raw = self._make_section('原始图像')
        self._sec_seg, self._body_seg = self._make_section('分割图像')

        # 三维数据分组：标题栏带全局颜色按钮
        self._btn_3d_global_color = QPushButton('🎨')
        self._btn_3d_global_color.setFixedSize(22, 22)
        self._btn_3d_global_color.setToolTip('更改所有三维数据颜色')
        self._btn_3d_global_color.setStyleSheet(f'''
            QPushButton {{
                background: transparent; border: 1px solid {_BORDER};
                color: {_TEXT_SEC}; font-size: 12px; border-radius: 4px;
            }}
            QPushButton:hover {{ background: {_HOVER}; color: {_WHITE}; border-color: #555; }}
        ''')
        self._btn_3d_global_color.clicked.connect(self._on_global_3d_color)
        self._sec_3d, self._body_3d = self._make_section('三维数据', self._btn_3d_global_color)

        scroll.setWidget(self._tree_widget)
        lc_layout.addWidget(scroll)
        root.addWidget(list_card, 1)

        # ── 属性面板 ──
        self.props = PropertiesPanel()
        root.addWidget(self.props)

        self.model.data_changed.connect(self._rebuild)
        self.model.visibility_changed.connect(self._on_model_visibility_changed)
        self.model.item_removed.connect(self.item_deleted)
        self.model.color_changed.connect(self._on_model_color_changed)

    def _make_section(self, title: str, extra_widget=None):
        hdr = SectionHeader(title, extra_widget=extra_widget)
        body = QWidget()
        body.setStyleSheet('background: transparent;')
        bl = QVBoxLayout(body)
        bl.setContentsMargins(6, 2, 0, 4)
        bl.setSpacing(1)
        hdr.toggled.connect(lambda exp, b=body: b.setVisible(exp))
        self._tree_layout.addWidget(hdr)
        self._tree_layout.addWidget(body)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f'background: {_BORDER}; border: none;')
        self._tree_layout.addWidget(sep)
        return hdr, body

    def _rebuild(self):
        self._row_widgets.clear()

        def _fill(body: QWidget, items):
            lo = body.layout()
            while lo.count():
                w = lo.takeAt(0).widget()
                if w:
                    w.deleteLater()
            for item in items:
                row = DataItemRow(item)
                row.clicked.connect(self._on_row_clicked)
                row.check_changed.connect(self._on_row_check)
                row.delete_requested.connect(self._on_row_delete)
                row.color_changed.connect(self._on_row_color)
                lo.addWidget(row)
                self._row_widgets[item.name] = row
                if item.name == self._selected_name:
                    row.set_selected(True)

        _fill(self._body_raw, self.model.raw_items())
        _fill(self._body_seg, self.model.seg_items())
        _fill(self._body_3d,  self.model.items_3d())
        self._sec_raw.set_count(len(self.model.raw_items()))
        self._sec_seg.set_count(len(self.model.seg_items()))
        self._sec_3d.set_count(len(self.model.items_3d()))

        if self._selected_name:
            item = self.model.get_item(self._selected_name)
            if item:
                self.props.update_item(item, self.model.seg_items())
            else:
                self._selected_name = ''
                self.props.clear()

    def _on_row_clicked(self, name: str):
        # 更新选中高亮
        if self._selected_name and self._selected_name in self._row_widgets:
            self._row_widgets[self._selected_name].set_selected(False)
        self._selected_name = name
        if name in self._row_widgets:
            self._row_widgets[name].set_selected(True)

        item = self.model.get_item(name)
        if item:
            self.props.update_item(item, self.model.seg_items())
            # 点击任意行都触发激活（叠加/显示），由 Controller 决定如何响应
            self.item_activated.emit(name, item.data_type, item.path)

    def _on_row_check(self, name: str, checked: bool):
        """复选框变化 → 更新模型 + 发出信号"""
        item = self.model.get_item(name)
        if item:
            self.model.set_visible(name, checked)
            self.visibility_changed.emit(name, item.data_type, checked)

    def _on_row_delete(self, name: str):
        item = self.model.get_item(name)
        data_type = item.data_type if item else ''
        self.model.remove_item(name)
        if self._selected_name == name:
            self._selected_name = ''
            self.props.clear()


    def _on_row_color(self, name: str, color: str):
        """颜色圆点选色 → 更新模型 + 发出信号"""
        item = self.model.get_item(name)
        if item:
            self.model.set_color(name, color)
            self.color_changed.emit(name, item.data_type, color)

    def _on_model_visibility_changed(self, name: int):
        item = self.model.get_item(name)
        if item and name in self._row_widgets:
            self._row_widgets[name].set_checked(item.visible)

    def _on_model_color_changed(self, name: int, color: str):
        """模型颜色变更 → 只刷新对应行的颜色圆点"""
        if name in self._row_widgets:
            self._row_widgets[name].dot.set_color(color)

    def _collapse_all(self):
        for b in (self._body_raw, self._body_seg, self._body_3d):
            b.setVisible(False)

    def _on_global_3d_color(self):
        """全局颜色按钮：统一更改所有三维数据的颜色"""
        from PyQt5.QtWidgets import QApplication, QColorDialog
        from PyQt5.QtGui import QColor
        app = QApplication.instance()
        saved = app.styleSheet()
        app.setStyleSheet('')
        color = QColorDialog.getColor(QColor('#dfC42d'), None, '选择三维数据全局颜色')
        app.setStyleSheet(saved)
        if not color.isValid():
            return
        hex_color = color.name()
        # 更新所有 3D DataItem 的颜色
        for item in self.model.items_3d():
            self.model.set_color(item.name, hex_color)
            # 刷新行内颜色圆点
            if item.name in self._row_widgets:
                self._row_widgets[item.name].dot.set_color(hex_color)
        # 发出全局颜色信号，由 Controller 统一更新 VTK actor
        self.global_3d_color_changed.emit(hex_color)

    def _delete_selected(self):
        """删除所有复选框勾选的数据项"""
        checked_names = [
            name for name, row in self._row_widgets.items()
            if row.chk.isChecked()
        ]
        for name in checked_names:
            self._on_row_delete(name)
