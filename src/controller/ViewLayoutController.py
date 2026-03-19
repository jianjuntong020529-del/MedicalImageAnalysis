# -*- coding: utf-8 -*-
"""
视图布局控制器
接收 ViewLayoutWidget 发出的 layout_changed 信号，
操控 MainWindow 中四个视图区域的显示与隐藏，实现布局切换。
多切片视图通过切换 QStackedWidget 页面实现嵌入主界面。
"""

from src.widgets.ViewLayoutWidget import (
    ViewLayoutWidget,
    LAYOUT_FOUR, LAYOUT_AXIAL, LAYOUT_SAGITTAL,
    LAYOUT_CORONAL, LAYOUT_VOLUME, LAYOUT_THREE, LAYOUT_MULTISLICE,
)


class ViewLayoutController:
    """
    视图布局控制器。

    参数
    ----
    viewer_model   : OrthoViewerModel
    four_view_refs : dict，各视图 Qt 控件引用
    view_stack     : QStackedWidget（index 0=四视图页, index 1=多切片页）
    parent         : QWidget
    """

    def __init__(self, viewer_model, four_view_refs: dict,
                 view_stack=None, parent=None):
        self.viewModel = viewer_model
        self._refs = four_view_refs
        self._view_stack = view_stack   # QStackedWidget 引用

        # 创建浮动面板
        self.panel = ViewLayoutWidget(parent)
        self.panel.layout_changed.connect(self._apply_layout)

    # ══════════════════════════════════════════════════════════════════════════
    # 公开方法
    # ══════════════════════════════════════════════════════════════════════════

    def show_panel(self):
        """显示/隐藏布局面板"""
        if self.panel.isVisible():
            self.panel.hide()
        else:
            self.panel.show()

    # ══════════════════════════════════════════════════════════════════════════
    # 布局应用
    # ══════════════════════════════════════════════════════════════════════════

    def _apply_layout(self, layout_name: str):
        """根据布局名称切换视图"""

        # 多切片视图：切换到 stack 第1页并刷新
        if layout_name == LAYOUT_MULTISLICE:
            if self._view_stack is not None:
                self._view_stack.setCurrentIndex(1)
                # 触发多切片面板刷新
                from src.model.ToolBarWidgetModel import ToolBarWidget
                if ToolBarWidget.multi_slice_widget is not None:
                    ToolBarWidget.multi_slice_widget.show_panel()
            return

        # 其他布局：切换回 stack 第0页（四视图页）
        if self._view_stack is not None:
            self._view_stack.setCurrentIndex(0)

        # 各视图控件组
        axial_w    = self._get_view_widgets("axial")
        sagittal_w = self._get_view_widgets("sagittal")
        coronal_w  = self._get_view_widgets("coronal")
        volume_w   = self._get_view_widgets("volume")

        # 布局可见性映射
        visibility_map = {
            LAYOUT_FOUR:     (True,  True,  True,  True),
            LAYOUT_AXIAL:    (True,  False, False, False),
            LAYOUT_SAGITTAL: (False, True,  False, False),
            LAYOUT_CORONAL:  (False, False, True,  False),
            LAYOUT_VOLUME:   (False, False, False, True),
            LAYOUT_THREE:    (True,  True,  True,  False),
        }
        vis = visibility_map.get(layout_name, (True, True, True, True))

        self._set_view_visible(axial_w,    vis[0])
        self._set_view_visible(sagittal_w, vis[1])
        self._set_view_visible(coronal_w,  vis[2])
        self._set_view_visible(volume_w,   vis[3])

    # ══════════════════════════════════════════════════════════════════════════
    # 辅助
    # ══════════════════════════════════════════════════════════════════════════

    def _get_view_widgets(self, prefix: str) -> list:
        keys = [f"{prefix}_widget", f"{prefix}_slider", f"{prefix}_label"]
        return [self._refs[k] for k in keys if k in self._refs and self._refs[k] is not None]

    @staticmethod
    def _set_view_visible(widgets: list, visible: bool):
        for w in widgets:
            w.show() if visible else w.hide()
