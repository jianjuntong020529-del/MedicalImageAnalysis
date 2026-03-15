import os

import vtk
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src.constant.ParamConstant import ParamConstant
from src.model.BaseModel import BaseModel
from src.utils.globalVariables import getDirPath


class LoadToothSegWindow(QWidget):
    def __init__(self, baseModelClass: BaseModel):
        super().__init__()

        self.baseModelClass = baseModelClass

        self.stl_path = []
        self.resize(1128, 698)
        self.system_layout = QtWidgets.QHBoxLayout(self)
        self.system_layout.setSpacing(6)

        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)

        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)

        self.system_layout.addWidget(self.vtkWidget)

        self.reader_stl_renderer = vtk.vtkRenderer()
        self.reader_stl_renderer.SetBackground(0.5, 0.5, 0.5)
        self.reader_stl_renderer.ResetCamera()

        self.reader_stl_iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.reader_stl_renderer)

        self.reader_stl_style = vtk.vtkInteractorStyleTrackballCamera()
        self.reader_stl_style.SetDefaultRenderer(self.reader_stl_renderer)
        self.reader_stl_style.EnabledOn()
        self.vtkWidget.Render()

        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Widget", "Segmentation Result"))

    def LoadSTL(self):
        print("subject_name: " + ParamConstant.ANNOTATION_SUBJECT_NAME)
        path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.ANNOTATION_SUBJECT_NAME
        data_names = os.listdir(path)
        for data_name in data_names:
            if os.path.splitext(data_name)[1] == '.stl':
                list = data_name.split("_")
                if len(list) > 2 and list[0] == ParamConstant.ANNOTATION_SUBJECT_NAME:
                    self.stl_path.append(data_name)
        print(self.stl_path)

        for filename in self.stl_path:
            filename = path + "/" + filename
            bounds = self.baseModelClass.bounds
            self.center0 = (bounds[1] + bounds[0]) / 2.0
            self.center1 = (bounds[3] + bounds[2]) / 2.0
            self.center2 = (bounds[5] + bounds[4]) / 2.0
            transform = vtk.vtkTransform()
            transform.Translate(self.center0, self.center1, self.center2)
            reader = vtk.vtkSTLReader()
            reader.SetFileName(filename)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            actor = vtk.vtkLODActor()
            actor.SetMapper(mapper)
            actor.SetUserTransform(transform)
            self.reader_stl_iren.SetInteractorStyle(self.reader_stl_style)
            self.reader_stl_renderer.AddActor(actor)
        self.vtkWidget.Render()
        self.reader_stl_renderer.ResetCamera()
        self.reader_stl_iren.Initialize()
