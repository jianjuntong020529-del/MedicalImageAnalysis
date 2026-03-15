# -*- coding: utf-8 -*-
# @Time    : 2024/10/16 20:34
#
# @Author  : Jianjun Tong
import numpy as np
import vtk

from src.utils.globalVariables import *


class LeftButtonPressEvent():
    def __init__(self, picker, viewer, type):
        print("初始化")
        self.picker = picker  # 坐标拾取
        self.start = []  # 起点坐标
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.count = 0
        self.type = type

    def __call__(self, caller, ev):
        self.count += 1
        self.picker.AddPickList(self.actor)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.start = self.picker.GetPickPosition()  # 获得起点坐标
        # --------------------------------------------------------------------------------------------------
        self.start_pos = [int(self.start[i] - self.origin[i]) / self.spacing[i] for i in range(3)]
        self.start = list(self.start)
        if self.type == "XY":
            self.start[2] = 100  # 将画线置于图像上层
        elif self.type == "YZ":
            self.start[0] = 200
        else:
            self.start[1] = -1
        self.start = tuple(self.start)
        if self.count % 2 != 0:
            setState2True()
            setStartPoint(self.start)
        else:
            setState2False()
            setStartPoint([0, 0, 0])
        self.view.UpdateDisplayExtent()
        self.view.Render()
        print(self.start)


class MouseMoveEvent():
    def __init__(self, picker, viewer, type):
        self.picker = picker  # 坐标拾取
        self.end = []  # 中间点坐标
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.points = vtk.vtkPoints()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.type = type

    def __call__(self, caller, ev):

        if getState2():
            print("开始鼠标移动")
            x, y = self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1]
            print("X,Y", x, y)

            self.picker.AddPickList(self.actor)
            self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
            self.start = getStartPoint()
            # self.pixel_pos = [int(self.start[i] - self.origin[i]) / self.spacing[i] for i in range(3)]

            self.end = self.picker.GetPickPosition()  # 获得中间点坐标
            self.end_pos = [int(self.end[i] - self.origin[i]) / self.spacing[i] for i in range(3)]
            self.end = list(self.end)
            if self.type == "XY":
                self.end[2] = 100
            elif self.type == "YZ":
                self.end[0] = 200
            else:
                self.end[1] = -1
            self.end = tuple(self.end)
            print(self.end)
            # self.end_pos=[int(self.end[i] - self.origin[i]) / self.spacing[i] for i in range(3)]
            # self.points.InsertNextPoint(self.end)
            self.lineSource = vtk.vtkLineSource()
            self.lineSource.SetPoint1(self.start)
            self.lineSource.SetPoint2(self.end)
            self.lineSource.Update()
            setStartPoint(self.end)
            # Visualize
            colors = vtk.vtkNamedColors()

            self.mapper = vtk.vtkPolyDataMapper()
            self.mapper.SetInputConnection(self.lineSource.GetOutputPort())
            self.mapper.Update()
            self.actor_paint = vtk.vtkActor()
            self.actor_paint.SetMapper(self.mapper)
            self.actor_paint.GetProperty().SetLineWidth(4)
            self.actor_paint.GetProperty().SetColor(colors.GetColor3d("Peacock"))
            setActors_paint(self.actor_paint)

            self.ren = self.view.GetRenderer()
            self.ren.AddActor(self.actor_paint)
            self.iren.Render()
            self.ren.Render()
            self.view.UpdateDisplayExtent()
            self.view.Render()

        else:
            # print("请先点击左键")
            pass


class LeftButtonPressEvent_poly():
    def __init__(self, picker, viewer, type):
        print("折线标注")
        self.picker = picker  # 坐标拾取
        self.start = []  # 起点坐标
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.points = vtk.vtkPoints()
        self.count = 0
        self.type = type

    def __call__(self, caller, ev):
        self.count += 1
        self.picker.AddPickList(self.actor)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.start = self.picker.GetPickPosition()  # 获得起点坐标
        # --------------------------------------------------------------------------------------------------
        self.start_pos = [int(self.start[i] - self.origin[i]) / self.spacing[i] for i in range(3)]
        self.start = list(self.start)
        if self.type == "XY":
            self.start[2] = 100  # 将画线置于图像上层
        elif self.type == "YZ":
            self.start[0] = 200
        else:
            self.start[1] = -1
        self.start = tuple(self.start)
        if self.count <= 2:
            if self.count % 2 != 0:
                setState_PolyTrue()
                setStart_Poly_Point(self.start)
            else:
                setState_PolyFalse()
                setEnd_Poly_Point(self.start)
                self.lineSource = vtk.vtkLineSource()
                self.lineSource.SetPoint1(getStart_Poly_Point())
                self.lineSource.SetPoint2(getEnd_Poly_Point())
                self.lineSource.Update()
                # Visualize
                colors = vtk.vtkNamedColors()
                self.mapper = vtk.vtkPolyDataMapper()
                self.mapper.SetInputConnection(self.lineSource.GetOutputPort())
                self.mapper.Update()
                self.actor_paint = vtk.vtkActor()
                self.actor_paint.SetMapper(self.mapper)
                self.actor_paint.GetProperty().SetLineWidth(4)
                self.actor_paint.GetProperty().SetColor(colors.GetColor3d("Green"))
                setActors_paint(self.actor_paint)

                self.ren = self.view.GetRenderer()
                self.ren.AddActor(self.actor_paint)
                self.iren.Render()
                self.ren.Render()
            self.view.UpdateDisplayExtent()
            self.view.Render()
        else:
            setStart_Poly_Point(getEnd_Poly_Point())
            setEnd_Poly_Point(self.start)
            self.lineSource = vtk.vtkLineSource()
            self.lineSource.SetPoint1(getStart_Poly_Point())
            self.lineSource.SetPoint2(getEnd_Poly_Point())
            self.lineSource.Update()
            # Visualize
            colors = vtk.vtkNamedColors()
            self.mapper = vtk.vtkPolyDataMapper()
            self.mapper.SetInputConnection(self.lineSource.GetOutputPort())
            self.mapper.Update()
            self.actor_paint = vtk.vtkActor()
            self.actor_paint.SetMapper(self.mapper)
            self.actor_paint.GetProperty().SetLineWidth(4)
            self.actor_paint.GetProperty().SetColor(colors.GetColor3d("Green"))
            setActors_paint(self.actor_paint)

            self.ren = self.view.GetRenderer()
            self.ren.AddActor(self.actor_paint)
            self.iren.Render()
            self.ren.Render()
        self.view.UpdateDisplayExtent()
        self.view.Render()


class CallBack():
    def __init__(self, viwer, picker, vtkWidget, dicomdata):
        self.vtkWidget = vtkWidget
        self.viwer = viwer
        self.picker = picker
        self.iren = self.viwer.GetRenderWindow().GetInteractor()
        self.render = self.viwer.GetRenderer()
        self.image = self.viwer.GetInput()
        self.actor = self.viwer.GetImageActor()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.dicomdata = dicomdata

    def __call__(self, caller, ev):
        # ------------------------------------------------------------------------------
        self.picker.AddPickList(self.actor)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.pos = self.picker.GetPickPosition()  # 获取图像的世界坐标
        self.pixel_pos = [int(self.pos[i] - self.origin[i]) / self.spacing[i] for i in range(3)]
        self.pixel_pos = np.int32(self.pixel_pos)
        print("像素索引")
        print(self.pixel_pos)
        if (self.pixel_pos[0] < 0) or (self.pixel_pos[1] < 0) or (self.pixel_pos[2] < 0):
            self.vtkWidget.setToolTip('')
        else:
            # ------------------------------------------------------------------------------
            # print(np.ceil(self.pixel_pos))
            try:
                self.pixel_value = self.dicomdata[self.pixel_pos[0], self.pixel_pos[1], self.pixel_pos[2]]
                print(self.pixel_value)
                self.vtkWidget.setToolTip(str(self.pixel_value))
            except:
                print("范围越界")
