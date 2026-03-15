"""
视图数据传递时的数据模型
"""
from src.widgets import QtOrthoViewerWidget


class OrthoViewerModel:
    def __init__(self, AxialOrthoViewer:QtOrthoViewerWidget, SagittalOrthoViewer:QtOrthoViewerWidget, CoronalOrthoViewer:QtOrthoViewerWidget, VolumeOrthorViewer:QtOrthoViewerWidget):
        print("OrthorViewerModel")
        # 横截面
        self.AxialOrthoViewer = AxialOrthoViewer
        # 矢状面
        self.SagittalOrthoViewer = SagittalOrthoViewer
        # 冠状面
        self.CoronalOrthoViewer = CoronalOrthoViewer
        # 体渲染窗口
        self.VolumeOrthorViewer = VolumeOrthorViewer
