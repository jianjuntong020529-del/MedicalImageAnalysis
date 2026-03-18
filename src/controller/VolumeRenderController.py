# -*- coding: utf-8 -*-
from src.widgets.VolumeRenderWidget import VolumeRenderWidget


class VolumeRenderController(VolumeRenderWidget):
    """体绘制工具栏控制器，继承 Widget，接收 viewModel 供后续扩展"""

    def __init__(self, viewer_model, parent=None):
        super().__init__(parent)
        self.viewModel = viewer_model
        # 暴露 widget 属性，与其他 controller 保持一致
        self.widget_volume_render = self
