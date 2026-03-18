from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.ToolBarWidgetModel import ToolBarWidget
import vtk

class ContrastService:
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel):
        self.baseModelClass = baseModelClass
        self.viewModel = viewModel

    def LevelAndWidth(self):
        scalarRange = self.baseModelClass.scalerRange
        window = (scalarRange[1] - scalarRange[0])
        # 窗位应该设置在数据范围的中心点，这样可以正确显示整个灰度范围
        level = (scalarRange[0] + scalarRange[1]) / 2.0
        return window, level

    def adjust_window_width_and_level(self):
        window, level = self.LevelAndWidth()
        print(window, level)
        ToolBarWidget.contrast_widget.window_width_slider.setValue(window)
        ToolBarWidget.contrast_widget.window_level_slider.setValue(level)

    def widthSliderValueChange(self):
        self.viewerXY = self.viewModel.AxialOrthoViewer.viewer
        self.viewerYZ = self.viewModel.SagittalOrthoViewer.viewer
        self.viewerXZ = self.viewModel.CoronalOrthoViewer.viewer

        ToolBarWidget.contrast_widget.window_level_slider.setToolTip(str(ToolBarWidget.contrast_widget.window_level_slider.value()))
        ToolBarWidget.contrast_widget.window_width_slider.setToolTip(str(ToolBarWidget.contrast_widget.window_width_slider.value()))

        viewers = [self.viewerXY, self.viewerYZ, self.viewerXZ]
        for viewer in viewers:
            viewer.SetColorLevel(ToolBarWidget.contrast_widget.window_level_slider.value())
            viewer.SetColorWindow(ToolBarWidget.contrast_widget.window_width_slider.value())
            # 检查是否为 vtkImageViewer2 类型，如果是则跳过 GetResliceCursorWidget 调用
            if not isinstance(viewer, vtk.vtkImageViewer2) and hasattr(viewer, 'GetResliceCursorWidget'):
                viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().SetWindowLevel(
                    ToolBarWidget.contrast_widget.window_width_slider.value(), ToolBarWidget.contrast_widget.window_level_slider.value())
            viewer.Render()

    def levelSliderValueChange(self):
        self.viewerXY = self.viewModel.AxialOrthoViewer.viewer
        self.viewerYZ = self.viewModel.SagittalOrthoViewer.viewer
        self.viewerXZ = self.viewModel.CoronalOrthoViewer.viewer

        ToolBarWidget.contrast_widget.window_level_slider.setToolTip(str(ToolBarWidget.contrast_widget.window_level_slider.value()))
        ToolBarWidget.contrast_widget.window_width_slider.setToolTip(str(ToolBarWidget.contrast_widget.window_width_slider.value()))

        viewers = [self.viewerXY, self.viewerYZ, self.viewerXZ]
        for viewer in viewers:
            viewer.SetColorLevel(ToolBarWidget.contrast_widget.window_level_slider.value())
            viewer.SetColorWindow(ToolBarWidget.contrast_widget.window_width_slider.value())
            # 检查是否为 vtkImageViewer2 类型，如果是则跳过 GetResliceCursorWidget 调用
            if not isinstance(viewer, vtk.vtkImageViewer2) and hasattr(viewer, 'GetResliceCursorWidget'):
                viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().SetWindowLevel(
                    ToolBarWidget.contrast_widget.window_width_slider.value(), ToolBarWidget.contrast_widget.window_level_slider.value())
            viewer.Render()


