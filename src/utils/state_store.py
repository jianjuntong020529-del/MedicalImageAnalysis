from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, List, Tuple, Optional


@dataclass
class FileState:
    """文件加载及计数等全局元数据。"""

    dirpath: str = ""
    count: int = 1
    state: bool = False
    file_is_empty: bool = True


@dataclass
class SliceState:
    """三个正交视图的切片索引，保证联动。"""

    slice_xy: int = 0
    slice_yz: int = 0
    slice_xz: int = 0


@dataclass
class MeasurementState:
    """标尺/折线绘制过程中的临时参数。"""

    startPoint: Tuple[Any, Any] = ()
    endPoint: Tuple[Any, Any] = ()
    start_poly_point: Tuple[Any, Any] = ()
    end_poly_point: Tuple[Any, Any] = ()
    state_poly: bool = False
    state2: bool = False
    long: int = 0
    width: int = 0
    fourPoints: List[Any] = field(default_factory=list)


@dataclass
class PaintState:
    """涂抹流程涉及的演员列表与撤销/重做栈。"""

    actors: List[Any] = field(default_factory=list)
    undo_stack: List[Any] = field(default_factory=list)
    redo_stack: List[Any] = field(default_factory=list)
    color_index_list: List[int] = field(default_factory=list)
    actors_paint: List[Any] = field(default_factory=list)
    left_button_down: bool = False


@dataclass
class AnnotationState:
    """标注部件使用的所有框选/关键点状态。"""

    select_point_label_1: bool = True
    select_single_box_label: bool = True
    point_position: List[Any] = field(default_factory=list)
    single_bounding_box: List[Any] = field(default_factory=list)
    multiple_bounding_box: List[Any] = field(default_factory=list)
    multiple_bounding_box_original: List[Any] = field(default_factory=list)
    box_points_original: List[Any] = field(default_factory=list)
    single_bounding_box_actor: List[Any] = field(default_factory=list)
    multiple_bounding_box_actor: List[Any] = field(default_factory=list)
    last_bounding_box_actor: List[Any] = field(default_factory=list)
    points_actor: List[Any] = field(default_factory=list)
    points_undo_stack: List[Any] = field(default_factory=list)
    points_redo_stack: List[Any] = field(default_factory=list)
    points_dict: dict = field(default_factory=dict)
    single_undo_stack: List[Any] = field(default_factory=list)
    single_redo_stack: List[Any] = field(default_factory=list)
    single_boundingBox_dict: dict = field(default_factory=dict)
    multiple_undo_stack: List[Any] = field(default_factory=list)
    multiple_redo_stack: List[Any] = field(default_factory=list)
    multiple_boundingBox_dict: dict = field(default_factory=dict)
    control_roi_point: dict = field(default_factory=dict)


@dataclass
class ImplantState:
    """植体规划相关的状态机标志与临时缓存。"""

    is_put_implant: bool = False
    is_generate_implant: bool = False
    is_adjust: bool = False
    anchor_point_is_complete: bool = False
    dental_arch_curve_points: List[Any] = field(default_factory=list)
    dental_arch_thickness: str = "80"
    dicom_points: List[Any] = field(default_factory=list)
    control_points: List[Any] = field(default_factory=list)
    paint_points: List[Any] = field(default_factory=list)
    sample_points: List[Any] = field(default_factory=list)


@dataclass
class ClickState:
    """用于判定各方向鼠标点击区域的辅助标志。"""

    left_down_is_clicked: bool = False
    left_mid_is_clicked: bool = False
    left_up_is_clicked: bool = False
    down_mid_is_clicked: bool = False
    up_mid_is_clicked: bool = False
    right_down_is_clicked: bool = False
    right_mid_is_clicked: bool = False
    right_up_is_clicked: bool = False
    mid_is_clicked: bool = False


class StateStore:
    """UI 共享状态的线程安全容器。

    按业务分区（文件、切片、标注等）集中管理，既方便定位归属也便于自动补全。
    每个分区是 dataclass，天然带默认值与类型提示。
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self.file = FileState()
        self.slice = SliceState()
        self.measurement = MeasurementState()
        self.paint = PaintState()
        self.annotation = AnnotationState()
        self.implant = ImplantState()
        self.click = ClickState()

    @contextmanager
    def locked(self):
        """带锁暴露底层 store 的上下文管理器。"""
        self._lock.acquire()
        try:
            yield self
        finally:
            self._lock.release()

    def get(self, section: str, attr: str):
        """从指定分区原子地读取字段。"""
        with self._lock:
            return getattr(getattr(self, section), attr)

    def set(self, section: str, attr: str, value):
        """向指定分区原子地写入字段。"""
        with self._lock:
            setattr(getattr(self, section), attr, value)

    def append(self, section: str, attr: str, value):
        """线程安全地向列表型字段追加元素。"""
        with self._lock:
            getattr(getattr(self, section), attr).append(value)

    def append_unique(self, section: str, attr: str, value):
        """仅在不存在时追加，适用于 ID 去重等场景。"""
        with self._lock:
            target = getattr(getattr(self, section), attr)
            if value not in target:
                target.append(value)

    def clear_collection(self, section: str, attr: str):
        """清空集合但保持原对象引用，避免引用失效。"""
        with self._lock:
            target = getattr(getattr(self, section), attr)
            if hasattr(target, "clear"):
                target.clear()
            elif isinstance(target, list):
                target[:] = []
            elif isinstance(target, dict):
                target.clear()

    def increment(self, section: str, attr: str, delta: int = 1):
        """安全地自增/自减数值字段。"""
        with self._lock:
            current = getattr(getattr(self, section), attr)
            setattr(getattr(self, section), attr, current + delta)


_STATE_STORE: Optional[StateStore] = None


def get_state_store() -> StateStore:
    global _STATE_STORE
    if _STATE_STORE is None:
        # 惰性初始化可减少导入成本并规避顺序依赖。
        _STATE_STORE = StateStore()
    return _STATE_STORE

