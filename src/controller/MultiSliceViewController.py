# -*- coding: utf-8 -*-
"""
多切片视图控制器
管理 MultiSliceViewWidget，响应跳转信号，同步主界面切片滑块。
"""

from src.widgets.MultiSliceViewWidget import MultiSliceViewWidget


class MultiSliceViewController:
    """
    参数
    ----
    base_model   : BaseModel
    viewer_model : OrthoViewerModel
    parent       : QWidget（主窗口，作为面板的父控件）
    """

    def __init__(self, base_model, viewer_model, parent=None):
        self._viewer_model = viewer_model

        # 创建多切片视图面板（嵌入主界面，默认隐藏）
        self.widget = MultiSliceViewWidget(base_model, viewer_model, half_count=2, parent=parent)
        self.widget.hide()

        # 连接跳转信号
        self.widget.jump_to_slice.connect(self._on_jump_to_slice)

    # ══════════════════════════════════════════════════════════════════════════
    # 公开方法
    # ══════════════════════════════════════════════════════════════════════════

    def show_panel(self):
        """显示面板并刷新内容，同步主界面当前切片作为中心"""
        # 从主界面同步当前切片索引
        try:
            orientation = self.widget._orientation
            if orientation == "XY":
                center = self._viewer_model.AxialOrthoViewer.viewer.GetSlice()
            elif orientation == "YZ":
                center = self._viewer_model.SagittalOrthoViewer.viewer.GetSlice()
            else:
                center = self._viewer_model.CoronalOrthoViewer.viewer.GetSlice()
            self.widget._center = center
        except Exception:
            pass
        self.widget.refresh()
        self.widget.show()

    def hide_panel(self):
        self.widget.hide()

    def toggle_panel(self):
        """切换显示/隐藏"""
        if self.widget.isVisible():
            self.hide_panel()
        else:
            self.show_panel()

    def refresh(self):
        """若面板可见则刷新"""
        if self.widget.isVisible():
            self.widget.refresh()

    # ══════════════════════════════════════════════════════════════════════════
    # 信号处理
    # ══════════════════════════════════════════════════════════════════════════

    def _on_jump_to_slice(self, orientation: str, slice_index: int):
        """
        响应卡片点击或滚轮，更新主界面对应方向的滑块。
        滑块 valueChanged 会自动触发主界面视图刷新。
        """
        try:
            if orientation == "XY":
                slider = self._viewer_model.AxialOrthoViewer.slider
                viewer = self._viewer_model.AxialOrthoViewer.viewer
            elif orientation == "YZ":
                slider = self._viewer_model.SagittalOrthoViewer.slider
                viewer = self._viewer_model.SagittalOrthoViewer.viewer
            else:
                slider = self._viewer_model.CoronalOrthoViewer.slider
                viewer = self._viewer_model.CoronalOrthoViewer.viewer

            # 限制在有效范围内
            safe = max(viewer.GetSliceMin(), min(viewer.GetSliceMax(), slice_index))
            slider.setValue(safe)

            # 刷新多切片面板
            self.widget.refresh()

        except Exception as e:
            print(f"[MultiSliceViewController] 跳转失败: {e}")
