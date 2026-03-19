# -*- coding: utf-8 -*-
"""
CPR（多曲面重建）控制器

职责：
  - 管理 CPRWidget 的生命周期（独立浮动窗口）
  - 响应菜单栏触发，显示/隐藏 CPR 面板
  - 可接收主窗口已加载的体数据，直接传入 CPR 面板
"""

from PyQt5 import QtWidgets, QtCore
from src.widgets.CPRWidget import CPRWidget


class CPRController(QtCore.QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget = CPRWidget()
        self.widget.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.WindowCloseButtonHint |
            QtCore.Qt.WindowMinMaxButtonsHint
        )

    def show(self):
        self.widget.show()
        self.widget.raise_()
        self.widget.activateWindow()

    def hide(self):
        self.widget.hide()

    def toggle(self):
        if self.widget.isVisible():
            self.hide()
        else:
            self.show()

    def set_volume_from_base_model(self, base_model):
        """
        从主窗口的 BaseModel 中提取体数据并传入 CPR 面板。
        如果主窗口已加载 DICOM/NIfTI 数据，可直接调用此方法。
        """
        try:
            import numpy as np
            reader = base_model.imageReader
            reader.Update()
            vtk_img = reader.GetOutput()
            from vtk.util.numpy_support import vtk_to_numpy
            dims = vtk_img.GetDimensions()   # (W, H, D)
            spacing = vtk_img.GetSpacing()
            arr = vtk_to_numpy(vtk_img.GetPointData().GetScalars())
            volume = arr.reshape(dims[2], dims[1], dims[0]).transpose(1, 2, 0).astype(np.float32)
            self.widget.set_volume(volume, spacing)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self.widget, "数据传入失败",
                "无法从主窗口获取体数据：{}\n请在 CPR 面板中手动打开数据文件。".format(e)
            )
