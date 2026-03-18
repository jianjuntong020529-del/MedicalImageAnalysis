# -*- coding: utf-8 -*-
"""
独立的冠状面视图组件
"""
import vtk
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src.interactor_style.FourViewerInteractorStyle import MouseWheelForward, MouseWheelBackWard
from src.model.BaseModel import BaseModel
from src.model.ToolBarWidgetModel import ToolBarWidget
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font


class CoronalViewer:
    """独立的冠状面视图组件"""
    
    def __init__(self, baseModelClass: BaseModel):
        super(CoronalViewer, self).__init__()
        # Reader
        self.reader = baseModelClass.imageReader

        self.baseModelClass = baseModelClass

        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)

        self.widget = QVTKRenderWindowInteractor(self.frame)

        self.renderer = vtk.vtkRenderer()

        self.renderWindow = self.widget.GetRenderWindow()
        self.renderWindow.SetMultiSamples(0)
        self.renderWindow.AddRenderer(self.renderer)

        # Render Window Interactor
        self.renderWindowInteractor = self.widget.GetRenderWindow().GetInteractor()

        # Picker
        self.picker = baseModelClass.picker

        # ImageSliceViewer
        self.viewer = vtk.vtkResliceImageViewer()

        # Camera
        self.camera = self.viewer.GetRenderer().GetActiveCamera()

        # Slider
        self.slider = QtWidgets.QSlider()
        self.slider.setOrientation(QtCore.Qt.Vertical)

        # Slider label
        self.slider_label = QtWidgets.QLabel()
        self.slider_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)

        self.type = "XZ"

        self.update_viewer(self.viewer, self.widget, self.slider_label, self.slider)

    def update_viewer(self, viewer, vtkWidget, label, verticalSlider):

        bounds = self.baseModelClass.bounds
        center0 = (bounds[1] + bounds[0]) / 2.0
        center1 = (bounds[3] + bounds[2]) / 2.0
        center2 = (bounds[5] + bounds[4]) / 2.0

        viewer.SetInputData(self.reader.GetOutput())
        viewer.SetupInteractor(vtkWidget)
        viewer.SetRenderWindow(vtkWidget.GetRenderWindow())
        viewer.SetSliceOrientationToXZ()

        maxSlice = viewer.GetSliceMax()

        transform_XZ = vtk.vtkTransform()
        transform_XZ.Translate(center0, center1, center2)
        transform_XZ.RotateY(180)
        transform_XZ.RotateZ(180)
        transform_XZ.Translate(-center0, -center1, -center2)
        viewer.GetImageActor().SetUserTransform(transform_XZ)
        viewer.SetSlice(int(maxSlice / 2))

        viewer.SetColorLevel(ToolBarWidget.contrast_widget.window_level_slider.value())
        viewer.SetColorWindow(ToolBarWidget.contrast_widget.window_width_slider.value())
        viewer.SliceScrollOnMouseWheelOff()


        camera = viewer.GetRenderer().GetActiveCamera()
        camera.ParallelProjectionOn()
        camera.SetParallelScale(80)
        viewer.UpdateDisplayExtent()
        viewer.Render()

        wheelforward = MouseWheelForward(viewer, label, verticalSlider, id)
        wheelbackward = MouseWheelBackWard(viewer, label, verticalSlider, id)
        viewer_InteractorStyle = viewer.GetInteractorStyle()
        viewer_InteractorStyle.AddObserver("MouseWheelForwardEvent", wheelforward)
        viewer_InteractorStyle.AddObserver("MouseWheelBackwardEvent", wheelbackward)

        value = viewer.GetSlice()
        verticalSlider.setMaximum(maxSlice)
        verticalSlider.setMinimum(0)
        verticalSlider.setSingleStep(1)
        verticalSlider.setValue(value)
        label.setText("Slice %d/%d" % (verticalSlider.value(), maxSlice))
        viewer.Render()

