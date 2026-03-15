from vtkmodules.vtkInteractionWidgets import vtkResliceCursorLineRepresentation

from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel


class CommandSelect():
    def __init__(self, view_ID, baseModel:BaseModel, viewModel:OrthoViewerModel, resliceCursor):

        self.view_ID = view_ID

        self.viewModel = viewModel
        self.resliceCursor = resliceCursor

        self.viewerXY = viewModel.AxialOrthoViewer.viewer
        self.viewerYZ = viewModel.SagittalOrthoViewer.viewer
        self.viewerXZ = viewModel.CoronalOrthoViewer.viewer

        self.resliceCursorWidget_XY = self.viewerXY.GetResliceCursorWidget()
        self.resliceCursorWidget_YZ = self.viewerYZ.GetResliceCursorWidget()
        self.resliceCursorWidget_XZ = self.viewerXZ.GetResliceCursorWidget()


        self.vtkWidget = self.viewModel.AxialOrthoViewer.widget
        self.vtkWidget2 = self.viewModel.SagittalOrthoViewer.widget
        self.vtkWidget3 = self.viewModel.CoronalOrthoViewer.widget

        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider
        self.verticalSlider_YZ = self.viewModel.SagittalOrthoViewer.slider
        self.verticalSlider_XZ = self.viewModel.CoronalOrthoViewer.slider

        self.label_XY = self.viewModel.AxialOrthoViewer.slider_label
        self.label_YZ = self.viewModel.SagittalOrthoViewer.slider_label
        self.label_XZ = self.viewModel.CoronalOrthoViewer.slider_label

        self.reader = baseModel.imageReader
        self.origin = self.reader.GetOutput().GetOrigin()
        self.spacing = self.reader.GetOutput().GetSpacing()
        self.imageshape = self.reader.GetOutput().GetDimensions()

    def __call__(self, caller, ev):

        if self.view_ID == "XY":
            rep_YZ = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_YZ.GetRepresentation())
            rep_XZ = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_XZ.GetRepresentation())
            self.update()
        elif self.view_ID == "YZ":
            rep_XY = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_XY.GetRepresentation())
            rep_XZ = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_XZ.GetRepresentation())
            self.update()
        else:
            rep_XY = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_XY.GetRepresentation())
            rep_YZ = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_YZ.GetRepresentation())
            self.update()

    def update(self):
        slider_value = self.resliceCursor.GetCenter()
        self.verticalSlider_XY.setValue(int((slider_value[2] - self.origin[2]) / self.spacing[2]))
        self.verticalSlider_YZ.setValue(int((slider_value[0] - self.origin[0]) / self.spacing[0]))
        self.verticalSlider_XZ.setValue(int((slider_value[1] - self.origin[1]) / self.spacing[1]))
        self.label_XY.setText("Slice %d/%d" % (self.verticalSlider_XY.value(), self.imageshape[2]))
        self.label_YZ.setText("Slice %d/%d" % (self.verticalSlider_YZ.value(), self.imageshape[1]))
        self.label_XZ.setText("Slice %d/%d" % (self.verticalSlider_XZ.value(), self.imageshape[0]))
        self.vtkWidget3.GetRenderWindow().Render()
        self.vtkWidget.GetRenderWindow().Render()
        self.vtkWidget2.GetRenderWindow().Render()