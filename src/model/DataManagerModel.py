# -*- coding: utf-8 -*-
"""
数据管理模型 - 管理所有已加载的数据项
"""
from dataclasses import dataclass, field
from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal


# 数据类型常量
TYPE_RAW = 0   # Volume
TYPE_SEG = 1   # Segmentation
TYPE_3D  = 2   # Model

TYPE_NAMES = {
    TYPE_RAW: "Volume",
    TYPE_SEG: "Segmentation",
    TYPE_3D:  "Model"
}

# 格式标签颜色
FMT_COLORS = {
    'DICOM': ('#3B6D11', '#EAF3DE'),
    'NII':   ('#185FA5', '#E6F1FB'),
    'NPY':   ('#185FA5', '#E6F1FB'),
    'STL':   ('#854F0B', '#FAEEDA'),
    'IM0':   ('#3B6D11', '#EAF3DE'),
}

# 数据类型默认颜色池
_COLOR_POOL = [
    '#4a90d9', '#e07b54', '#e74c3c', '#e67e22', '#9b59b6',
    '#1abc9c', '#3498db', '#f39c12', '#2ecc71', '#e91e63',
]
_color_idx = 0


def _next_color():
    global _color_idx
    c = _COLOR_POOL[_color_idx % len(_COLOR_POOL)]
    _color_idx += 1
    return c


@dataclass
class DataItem:
    """单个数据项"""
    name: str
    data_type: int      # TYPE_RAW / TYPE_SEG / TYPE_3D
    fmt: str            # DICOM / NII / NPY / STL / IM0
    path: str = ''
    color: str = field(default_factory=_next_color)
    visible: bool = True
    dim: str = '—'
    # vtk actor 引用（3D模型用）
    actor: object = None
    # vtk mapper/reader 引用（切片视图用）
    vtk_data: object = None


class DataManagerModel(QObject):
    """数据管理模型，维护三类数据列表并发出变更信号"""

    data_changed = pyqtSignal()           # 任何数据变更
    visibility_changed = pyqtSignal(str)  # 某项可见性变更，传 item.name
    item_removed = pyqtSignal(str, int)   # 数据删除，传 (name, data_type)
    color_changed = pyqtSignal(str, str)  # 颜色变更，传 (name, new_color)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[DataItem] = []

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def add_item(self, item: DataItem):
        self._items.append(item)
        self.data_changed.emit()

    def remove_item(self, name: str):
        item = self.get_item(name)
        data_type = item.data_type if item else ''
        self._items = [i for i in self._items if i.name != name]
        if item:
            self.item_removed.emit(name, data_type)
        self.data_changed.emit()

    def get_item(self, name: str) -> Optional[DataItem]:
        for i in self._items:
            if i.name == name:
                return i
        return None

    def set_visible(self, name: str, visible: bool):
        item = self.get_item(name)
        if item and item.visible != visible:
            item.visible = visible
            self.visibility_changed.emit(name)
            self.data_changed.emit()

    def set_color(self, name: str, color: str):
        item = self.get_item(name)
        if item and item.color != color:
            item.color = color
            self.color_changed.emit(name, color)
            # 不触发 data_changed，避免重建整个列表

    def toggle_visible(self, name: str):
        item = self.get_item(name)
        if item:
            self.set_visible(name, not item.visible)

    # ── 分类查询 ──────────────────────────────────────────────────────────────

    def raw_items(self) -> List[DataItem]:
        return [i for i in self._items if i.data_type == TYPE_RAW]

    def seg_items(self) -> List[DataItem]:
        return [i for i in self._items if i.data_type == TYPE_SEG]

    def items_3d(self) -> List[DataItem]:
        return [i for i in self._items if i.data_type == TYPE_3D]

    def all_items(self) -> List[DataItem]:
        return list(self._items)

    def clear(self):
        self._items.clear()
        self.data_changed.emit()


# 全局单例
_instance: Optional[DataManagerModel] = None


def get_data_manager() -> DataManagerModel:
    global _instance
    if _instance is None:
        _instance = DataManagerModel()
    return _instance
