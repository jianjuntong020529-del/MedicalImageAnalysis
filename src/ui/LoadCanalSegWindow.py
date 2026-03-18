import os

import vtk
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src.constant.ParamConstant import ParamConstant
from src.model.BaseModel import BaseModel
from src.utils.globalVariables import getDirPath


class LoadCanalSegWindow(QWidget):
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
        self.reader_stl_renderer.SetBackground(1, 1, 1)
        self.reader_stl_renderer.ResetCamera()

        self.reader_stl_iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.reader_stl_renderer)

        self.reader_stl_style = vtk.vtkInteractorStyleTrackballCamera()
        self.reader_stl_style.SetDefaultRenderer(self.reader_stl_renderer)
        self.reader_stl_style.EnabledOn()
        self.vtkWidget.Render()

        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Widget", "下颌管分割结果"))

    def LoadSTL(self):
        path = ParamConstant.OUTPUT_FILE_PATH + "canal/"
        data_names = os.listdir(path)

        self.stl_path.append(data_names[0])
        
        print("Found alveolar STL files:", self.stl_path)

        # 获取图像边界用于变换
        bounds = self.baseModelClass.bounds
        self.center0 = (bounds[1] + bounds[0]) / 2.0
        self.center1 = (bounds[3] + bounds[2]) / 2.0
        self.center2 = (bounds[5] + bounds[4]) / 2.0
        
        # 设置交互样式
        self.reader_stl_iren.SetInteractorStyle(self.reader_stl_style)

        for filename in self.stl_path:
            full_filename = path + "/" + filename

            # 创建变换
            transform = vtk.vtkTransform()
            transform.Translate(self.center0, self.center1, self.center2)
            
            # 读取STL文件
            reader = vtk.vtkSTLReader()
            reader.SetFileName(full_filename)
            
            # 创建映射器
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            
            # 创建演员
            actor = vtk.vtkLODActor()
            actor.SetMapper(mapper)
            actor.SetUserTransform(transform)

            # 深灰色（RGB: 80,80,80）
            actor.GetProperty().SetColor(80 / 255.0, 80 / 255.0, 80 / 255.0)

            # 添加到渲染器
            self.reader_stl_renderer.AddActor(actor)
        
        # 渲染和初始化
        self.vtkWidget.Render()
        self.reader_stl_renderer.ResetCamera()
        self.reader_stl_iren.Initialize()
