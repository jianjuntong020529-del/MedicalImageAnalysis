import math

import numpy as np
import vtkmodules.all as vtk
from PyQt5.QtCore import Qt
from vtkmodules.vtkInteractionWidgets import vtkResliceCursorWidget, vtkResliceCursorLineRepresentation

from src.utils.globalVariables import *
from math import sin, cos, pi, atan

from src.utils.globalVariables import set_left_down_is_clicked


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
        if self.type == "xy":
            self.start[2] = 100  # 将画线置于图像上层
        elif self.type == "yz":
            self.start[0] = 100
        else:
            self.start[1] = 0
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
        if self.type == "xy":
            self.start[2] = 100  # 将画线置于图像上层
        elif self.type == "yz":
            self.start[0] = 100
        else:
            self.start[1] = 0
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
            if self.type == "xy":
                self.end[2] = 100
            elif self.type == "yz":
                self.end[0] = 100
            else:
                self.end[1] = 0
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


class LeftButtonPressEvent2():
    def __init__(self, picker, viewer):
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
        self.ren = self.view.GetRenderer()
        self.actorSum = []

    def __call__(self, caller, ev):
        print("绘制矩形")
        setLong(90)
        setWidth(30)
        self.count += 1
        self.picker.AddPickList(self.actor)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.start = self.picker.GetPickPosition()  # 获得起点坐标

        self.start_pos = [int(self.start[i] - self.origin[i]) / self.spacing[i] for i in range(3)]
        self.start = list(self.start)
        self.start[2] = 100
        # self.start=tuple(self.start)#左下角顶点
        if self.count % 2 != 0:
            setState2True()
            setStartPoint(self.start)
        else:
            setState2False()
            setStartPoint([0, 0, 0])
        print(self.start)
        self.leftLeft = self.start
        self.leftLeft = tuple(self.start)

        self.leftRight = self.start
        self.leftRight[0] += getLong()
        self.leftRight = tuple(self.leftRight)

        self.rightUp = list(self.leftRight)
        self.rightUp[1] += getWidth()
        self.rightUp = tuple(self.rightUp)

        self.leftUp = list(self.rightUp)
        self.leftUp[0] -= getLong()
        self.leftUp = tuple(self.leftUp)

        self.points = vtk.vtkPoints()
        self.points.InsertNextPoint(self.leftLeft)
        self.points.InsertNextPoint(self.leftRight)
        self.points.InsertNextPoint(self.rightUp)
        self.points.InsertNextPoint(self.leftUp)
        self.points.InsertNextPoint(self.leftLeft)
        self.lineSource = vtk.vtkLineSource()
        print(self.leftLeft)
        print(self.leftRight)
        print(self.rightUp)
        print(self.leftUp)

        self.lineSource.SetPoints(self.points)
        # self.lineSource.SetPoint1(self.leftLeft)
        # self.lineSource.SetPoint2(self.leftRight)
        self.lineSource.Update()
        colors = vtk.vtkNamedColors()
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.lineSource.GetOutputPort())
        self.mapper.Update()
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetLineWidth(4)
        self.actor.GetProperty().SetColor(colors.GetColor3d("Peacock"))
        self.actorSum.append(self.actor)
        self.ren.AddActor(self.actorSum[-1])
        print(len(self.actorSum))
        if len(self.actorSum) >= 2:
            self.ren.RemoveActor(self.actorSum[0])
            self.actorSum.pop(0)
        self.iren.Render()
        self.ren.Render()
        self.view.Render()


class LeftButtonPressEvent3():  # 画可以偏转角度的矩形
    def __init__(self, picker, viewer):
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
        self.ren = self.view.GetRenderer()

    def __call__(self, caller, ev):
        print("绘制角度矩形")
        self.count += 1
        self.picker.AddPickList(self.actor)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.start = self.picker.GetPickPosition()  # 获得起点坐标
        setStartPoint(self.start)  # 起点坐标保存

        self.start_pos = [int(self.start[i] - self.origin[i]) / self.spacing[i] for i in range(3)]
        # self.start = list(self.start)
        print("初始:")
        print(getStartPoint())
        # self.start[2] = self.start_pos[2] + 100
        # self.start=tuple(self.start)#左下角顶点
        if self.count % 2 != 0:
            setState2True()
            setStartPoint(self.start)
        else:
            setState2False()
            # setStartPoint([0, 0, 0])
        print("偏转30度")
        self.leftLeft = getStartPoint()
        self.leftLeft = list(self.leftLeft)
        self.leftLeft[2] += 100
        # self.leftLeft = tuple(self.leftLeft)

        self.leftRight = getStartPoint()
        self.leftRight = list(self.leftRight)
        # 不旋转坐标
        leftright = getStartPoint()
        leftright = list(leftright)
        leftright[0] += 10
        self.leftRight[0] = (leftright[0] - self.leftLeft[0]) * cos(30 / 180 * pi) - (
                leftright[1] - self.leftLeft[1]) * sin(30 / 180 * pi) + self.leftLeft[0]
        self.leftRight[1] = (leftright[1] - self.leftLeft[1]) * sin(30 / 180 * pi) + (
                leftright[0] - self.leftLeft[0]) * cos(30 / 180 * pi) + self.leftLeft[1]
        self.leftRight[2] += 100
        print("第一次赋值")
        print(getStartPoint())
        self.leftRight = tuple(self.leftRight)

        self.rightUp = getStartPoint()
        self.rightUp = list(self.rightUp)
        # 不旋转坐标
        rightup = getStartPoint()
        rightup = list(leftright)
        rightup[0] += 10
        rightup[1] += 10
        self.rightUp[0] = (rightup[0] - self.leftLeft[0]) * cos(30 / 180 * pi) - (rightup[1] - self.leftLeft[1]) * sin(
            30 / 180 * pi) + self.leftLeft[0]
        self.rightUp[1] = (rightup[1] - self.leftLeft[1]) * sin(30 / 180 * pi) + (rightup[0] - self.leftLeft[0]) * cos(
            30 / 180 * pi) + self.leftLeft[1]
        self.rightUp[2] += 100
        print("第二次赋值")
        print(getStartPoint())
        self.rightUp = tuple(self.rightUp)

        self.leftUp = getStartPoint()
        self.leftUp = list(self.leftUp)
        leftUp = getStartPoint()
        leftUp = list(leftright)
        leftUp[1] += 10
        self.leftUp[0] = (leftUp[0] - self.leftLeft[0]) * cos(30 / 180 * pi) - (leftUp[1] - self.leftLeft[1]) * sin(
            30 / 180 * pi) + self.leftLeft[0]
        self.leftUp[1] = (leftUp[1] - self.leftLeft[1]) * sin(30 / 180 * pi) + (leftUp[0] - self.leftLeft[0]) * cos(
            30 / 180 * pi) + self.leftLeft[1]
        self.leftUp[2] += 100

        print("第三次赋值")
        print(getStartPoint())
        self.leftUp = tuple(self.leftUp)
        self.leftLeft = tuple(self.leftLeft)
        self.points = vtk.vtkPoints()
        self.points.InsertNextPoint(self.leftLeft)
        self.points.InsertNextPoint(self.leftRight)
        self.points.InsertNextPoint(self.rightUp)
        self.points.InsertNextPoint(self.leftUp)
        # self.points.InsertNextPoint(self.leftLeft)
        self.lineSource = vtk.vtkLineSource()
        print(self.leftLeft)
        print(self.leftRight)
        # print(self.rightUp)
        # print(self.leftUp)

        self.lineSource.SetPoints(self.points)
        # self.lineSource.SetPoint1(self.leftLeft)
        # self.lineSource.SetPoint2(self.leftRight)
        self.lineSource.Update()
        colors = vtk.vtkNamedColors()
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.lineSource.GetOutputPort())
        self.mapper.Update()
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetLineWidth(4)
        self.actor.GetProperty().SetColor(colors.GetColor3d("Peacock"))

        self.ren.AddActor(self.actor)
        self.iren.Render()
        self.ren.Render()
        self.view.Render()


class LeftButtonPressEvent4():
    def __init__(self, picker, viewer, type):
        print("初始化")
        self.picker = picker  # 坐标拾取
        self.pix = []  # 存储四个顶点坐标
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
        print("确定顶点")
        self.count += 1
        self.picker.AddPickList(self.actor)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.start = self.picker.GetPickPosition()  # 获得起点坐标
        self.start_pos = [int(self.start[i] - self.origin[i]) / self.spacing[i] for i in range(3)]
        self.start = list(self.start)
        if self.type == "xy":
            self.start[2] = 100
        elif self.type == "yz":
            self.start[0] = 100
        else:
            self.start[1] = 0

        setFourPoints(self.start)
        self.lineSource = vtk.vtkLineSource()
        self.lineSource.SetPoint1(self.start)
        self.start2 = self.start
        self.start2[0] += 2
        self.start = tuple(self.start)
        self.start2 = tuple(self.start2)
        self.lineSource.SetPoint2(self.start2)
        colors = vtk.vtkNamedColors()
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.lineSource.GetOutputPort())
        self.mapper.Update()
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetLineWidth(4)
        self.actor.GetProperty().SetColor(colors.GetColor3d("Red"))
        self.ren = self.view.GetRenderer()
        self.ren.AddActor(self.actor)
        self.iren.Render()
        self.ren.Render()
        self.view.Render()


class MouseWheelForward():
    def __init__(self, viewer, labeltext, verticalslider, id):
        print("鼠标前滚初始化")
        # self.picker = picker  # 坐标拾取
        self.start = []  # 起点坐标
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.label = labeltext
        self.verticalslider = verticalslider
        self.id = id  # 判断是哪个窗口

    def __call__(self, caller, ev):
        print("初始化")
        if self.id == "XY":
            setSliceXY(self.view.GetSlice())
            self.verticalslider.setValue(getSliceXY())  # 首先初始化为默认切片
        elif self.id == "YZ":
            print("view")
            print(self.view.GetSlice())
            setSliceYZ(self.view.GetSlice())
            self.verticalslider.setValue(getSliceYZ())
        else:
            setSliceXZ(self.view.GetSlice())
            self.verticalslider.setValue(getSliceXZ())
        print("滑轮前滚")
        if self.id == "XY":
            addSliceXY()
            if getSliceXY() <= self.view.GetSliceMax():
                self.verticalslider.setValue(getSliceXY())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
            else:
                setSliceXY(self.view.GetSliceMax())
                self.verticalslider.setValue(self.view.GetSliceMax())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
        elif self.id == "YZ":
            addSliceYZ()
            if getSliceYZ() <= self.view.GetSliceMax():
                self.verticalslider.setValue(getSliceYZ())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
            else:
                setSliceYZ(self.view.GetSliceMax())
                self.verticalslider.setValue(self.view.GetSliceMax())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
        else:
            addSliceXZ()
            if getSliceXZ() <= self.view.GetSliceMax():
                self.verticalslider.setValue(getSliceXZ())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
            else:
                setSliceXZ(self.view.GetSliceMax())
                self.verticalslider.setValue(self.view.GetSliceMax())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))


class MouseWheelBackWard():
    def __init__(self, viewer, labeltext, verticalslider, id):
        # self.picker = picker  # 坐标拾取
        self.start = []  # 起点坐标
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.label = labeltext
        self.verticalslider = verticalslider
        self.id = id

    def __call__(self, caller, ev):
        print("初始化")
        if self.id == "XY":
            setSliceXY(self.view.GetSlice())
            self.verticalslider.setValue(getSliceXY())  # 首先初始化为默认切片
        elif self.id == "YZ":
            print("view")
            print(self.view.GetSlice())
            setSliceYZ(self.view.GetSlice())
            self.verticalslider.setValue(getSliceYZ())
        else:
            setSliceXZ(self.view.GetSlice())
            self.verticalslider.setValue(getSliceXZ())
        print("滑轮后滚")
        if self.id == "XY":
            minSliceXY()
            if getSliceXY() >= 0:
                self.verticalslider.setValue(getSliceXY())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
            else:
                setSliceXY(0)
                self.verticalslider.setValue(0)
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
        elif self.id == "YZ":
            minSliceYZ()
            if getSliceYZ() >= 0:
                self.verticalslider.setValue(getSliceYZ())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
            else:
                setSliceYZ(0)
                self.verticalslider.setValue(0)
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
        else:
            minSliceXZ()
            if getSliceXZ() >= 0:
                self.verticalslider.setValue(getSliceXZ())
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
            else:
                setSliceXZ(0)
                self.verticalslider.setValue(0)
                self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))


class MouseWheelForward_child():
    def __init__(self, viewer, labeltext, verticalslider, annotation_enable, spline_widget):
        print("鼠标前滚初始化")
        self.start = []  # 起点坐标
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.label = labeltext
        self.verticalslider = verticalslider
        self.annotation_enable = annotation_enable
        self.spline_widget = spline_widget

    def __call__(self, caller, ev):
        print("初始化")
        setSliceXY(self.view.GetSlice())
        self.verticalslider.setValue(getSliceXY())

        print("滑轮前滚")
        addSliceXY()
        if getSliceXY() <= self.view.GetSliceMax():
            self.verticalslider.setValue(getSliceXY())
            self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
        else:
            setSliceXY(self.view.GetSliceMax())
            self.verticalslider.setValue(self.view.GetSliceMax())
            self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))

        if self.annotation_enable == False:
            point0 = self.spline_widget.GetHandlePosition(0)
            point1 = self.spline_widget.GetHandlePosition(1)
            point2 = self.spline_widget.GetHandlePosition(2)
            point3 = self.spline_widget.GetHandlePosition(3)
            point4 = self.spline_widget.GetHandlePosition(4)
            point5 = self.spline_widget.GetHandlePosition(5)
            point6 = self.spline_widget.GetHandlePosition(6)
            point7 = self.spline_widget.GetHandlePosition(7)
            point8 = self.spline_widget.GetHandlePosition(8)
            point9 = self.spline_widget.GetHandlePosition(9)
            point10 = self.spline_widget.GetHandlePosition(10)

            self.spline_widget.SetHandlePosition(0, point0[0], point0[1], getSliceXY())
            self.spline_widget.SetHandlePosition(1, point1[0], point1[1], getSliceXY())
            self.spline_widget.SetHandlePosition(2, point2[0], point2[1], getSliceXY())
            self.spline_widget.SetHandlePosition(3, point3[0], point3[1], getSliceXY())
            self.spline_widget.SetHandlePosition(4, point4[0], point4[1], getSliceXY())
            self.spline_widget.SetHandlePosition(5, point5[0], point5[1], getSliceXY())
            self.spline_widget.SetHandlePosition(6, point6[0], point6[1], getSliceXY())
            self.spline_widget.SetHandlePosition(7, point7[0], point7[1], getSliceXY())
            self.spline_widget.SetHandlePosition(8, point8[0], point8[1], getSliceXY())
            self.spline_widget.SetHandlePosition(9, point9[0], point9[1], getSliceXY())
            self.spline_widget.SetHandlePosition(10, point10[0], point10[1], getSliceXY())

        # self.view.GetRenderWindow().GetInteractor().Render()
        self.view.UpdateDisplayExtent()
        self.view.Render()


class MouseWheelBackWard_child():
    def __init__(self, viewer, labeltext, verticalslider, annotation_enable, spline_widget):
        # self.picker = picker  # 坐标拾取
        self.start = []  # 起点坐标
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.label = labeltext
        self.verticalslider = verticalslider
        self.annotation_enable = annotation_enable
        self.spline_widget = spline_widget

    def __call__(self, caller, ev):
        print("初始化")
        setSliceXY(self.view.GetSlice())
        self.verticalslider.setValue(getSliceXY())

        print("滑轮后滚")
        minSliceXY()
        if getSliceXY() >= 0:
            self.verticalslider.setValue(getSliceXY())
            self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))
        else:
            setSliceXY(0)
            self.verticalslider.setValue(0)
            self.label.setText("Slice %d/%d" % (self.view.GetSlice(), self.view.GetSliceMax()))

        if self.annotation_enable == False:
            point0 = self.spline_widget.GetHandlePosition(0)
            point1 = self.spline_widget.GetHandlePosition(1)
            point2 = self.spline_widget.GetHandlePosition(2)
            point3 = self.spline_widget.GetHandlePosition(3)
            point4 = self.spline_widget.GetHandlePosition(4)
            point5 = self.spline_widget.GetHandlePosition(5)
            point6 = self.spline_widget.GetHandlePosition(6)
            point7 = self.spline_widget.GetHandlePosition(7)
            point8 = self.spline_widget.GetHandlePosition(8)
            point9 = self.spline_widget.GetHandlePosition(9)
            point10 = self.spline_widget.GetHandlePosition(10)

            self.spline_widget.SetHandlePosition(0, point0[0], point0[1], getSliceXY())
            self.spline_widget.SetHandlePosition(1, point1[0], point1[1], getSliceXY())
            self.spline_widget.SetHandlePosition(2, point2[0], point2[1], getSliceXY())
            self.spline_widget.SetHandlePosition(3, point3[0], point3[1], getSliceXY())
            self.spline_widget.SetHandlePosition(4, point4[0], point4[1], getSliceXY())
            self.spline_widget.SetHandlePosition(5, point5[0], point5[1], getSliceXY())
            self.spline_widget.SetHandlePosition(6, point6[0], point6[1], getSliceXY())
            self.spline_widget.SetHandlePosition(7, point7[0], point7[1], getSliceXY())
            self.spline_widget.SetHandlePosition(8, point8[0], point8[1], getSliceXY())
            self.spline_widget.SetHandlePosition(9, point9[0], point9[1], getSliceXY())
            self.spline_widget.SetHandlePosition(10, point10[0], point10[1], getSliceXY())

        # self.view.GetRenderWindow().GetInteractor().Render()
        self.view.UpdateDisplayExtent()
        self.view.Render()


class LeftButton_gps():
    def __init__(self, viewer1, viewer2, viewer3, picker, vtkWidget, dicomdata, id, logoWidgets):
        print("定位初始化")
        self.vtkWidget = vtkWidget
        self.viewer1 = viewer1
        self.viewer2 = viewer2
        self.viewer3 = viewer3
        self.picker = picker
        self.iren = self.viewer1.GetRenderWindow().GetInteractor()
        self.render = self.viewer1.GetRenderer()
        self.image = self.viewer1.GetInput()
        self.actor = self.viewer1.GetImageActor()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.dicomdata = dicomdata
        self.id = id
        self.logoWidgets = logoWidgets
        Hv, Wv, Cv = np.shape(dicomdata)

    def __call__(self, caller, ev):
        if self.id == "XY":
            # -----------------------------------------------------------------------------------------------
            self.picker.AddPickList(self.viewer1.GetImageActor())
            self.picker.Pick(self.viewer1.GetRenderWindow().GetInteractor().GetEventPosition()[0],
                             self.viewer1.GetRenderWindow().GetInteractor().GetEventPosition()[1], 0,
                             self.viewer1.GetRenderer())
            self.pos = self.picker.GetPickPosition()  # 获取图像的世界坐标
            self.pixel_pos = [int(self.pos[i] - self.viewer1.GetInput().GetOrigin()[i])
                              / self.viewer1.GetInput().GetSpacing()[i] for i in range(3)]
            self.logo_pos_XY = np.array([self.pixel_pos[0], self.pixel_pos[1], self.viewer1.GetSlice()], np.int32)
            print("==========十字线位置========")
            print(self.logo_pos_XY)
            # --------------修改YZ面的十字线位置-----------------------------
            self.viewer2.SetSlice(self.logo_pos_XY[0])
            image2 = self.viewer2.GetInput()
            origin2 = image2.GetOrigin()
            spacing2 = image2.GetSpacing()

            camPos = self.logoWidgets[1].GetRepresentation().GetPosition()
            camPos2 = self.logoWidgets[1].GetRepresentation().GetPosition2()
            print(camPos)
            print(camPos2)
            vc = vtk.vtkCoordinate()
            vc.SetCoordinateSystemToNormalizedDisplay()
            vc.SetValue(camPos[0], camPos[1], 0)

            pickPosition = list(vc.GetComputedWorldValue(self.viewer2.GetRenderer()))
            pixel_pos1 = [int(pickPosition[i] - origin2[i]) / spacing2[i] for i in range(3)]

            vc.SetValue(camPos2[0] + camPos[0], camPos2[1] + camPos[1], 0)
            pickPosition = list(vc.GetComputedWorldValue(self.viewer2.GetRenderer()))
            pixel_pos2 = [int(pickPosition[i] - origin2[i]) / spacing2[i] for i in range(3)]

            pos_implant = [(pixel_pos2[1] + pixel_pos1[1]) // 2, (pixel_pos2[2] + pixel_pos1[2]) // 2,
                           self.viewer2.GetSlice()]
            print(pos_implant)

            self.viewer2.Render()
            # --------------修改XZ面的十字线位置-----------------------------




        elif self.id == "YZ":
            self.picker.AddPickList(self.viewer2.GetImageActor())
            self.picker.Pick(self.viewer2.GetRenderWindow().GetInteractor().GetEventPosition()[0],
                             self.viewer2.GetRenderWindow().GetInteractor().GetEventPosition()[1], 0,
                             self.viewer2.GetRenderer())
            self.pos = self.picker.GetPickPosition()  # 获取图像的世界坐标
            self.pixel_pos = [int(self.pos[i] - self.viewer2.GetInput().GetOrigin()[i])
                              / self.viewer2.GetInput().GetSpacing()[i] for i in range(3)]
            self.pixel_pos = np.int32(self.pixel_pos)
            print("开启定位yz")
            vc = vtk.vtkCoordinate()
            vc.SetCoordinateSystemToWorld()
            vc.SetValue(self.pixel_pos)
            self.viewer1.SetSlice(self.pixel_pos[2])
            self.viewer3.SetSlice(self.pixel_pos[1])
            self.viewer1.Render()
            self.viewer3.Render()
            vc = vtk.vtkCoordinate()
            vc.SetCoordinateSystemToDisplay()
            vc.SetValue(self.pixel_pos[1], self.pixel_pos[2])
            position = list(vc.GetComputedViewportValue(self.viewer2.GetRenderer()))
            # position[0] = 1 - position[0] / 1432
            # position[1] = position[1] / 1048

            # self.logoWidgets[0].GetRepresentation().SetPosition(position)
            # self.logoWidgets[0].Render()
            # position = list(vc.GetComputedDisplayValue(self.viewer3.GetRenderer()))
            # print(position)
            print(position)
            position[0] = position[0] / 479
            position[1] = position[1] / 319
            print(position)
            self.logoWidgets[2].GetRepresentation().SetPosition(position)
            self.logoWidgets[2].Render()
        else:
            self.picker.AddPickList(self.viewer3.GetImageActor())
            self.picker.Pick(self.viewer3.GetRenderWindow().GetInteractor().GetEventPosition()[0],
                             self.viewer3.GetRenderWindow().GetInteractor().GetEventPosition()[1], 0,
                             self.viewer3.GetRenderer())
            self.pos = self.picker.GetPickPosition()  # 获取图像的世界坐标
            self.pixel_pos = [int(self.pos[i] - self.viewer3.GetInput().GetOrigin()[i])
                              / self.viewer3.GetInput().GetSpacing()[i] for i in range(3)]
            self.pixel_pos = np.int32(self.pixel_pos)
            print("开启定位xz")
            vc = vtk.vtkCoordinate()
            vc.SetCoordinateSystemToDisplay()
            vc.SetValue(self.pixel_pos[0], self.pixel_pos[2])
            position = list(vc.GetComputedViewportValue(self.viewer3.GetRenderer()))
            print(position)
            self.viewer1.SetSlice(self.pixel_pos[0])
            self.viewer2.SetSlice(self.pixel_pos[1])
            self.viewer1.Render()
            self.viewer2.Render()


def createLine_Crosshair(p0, p1, p2, p3):
    # Create a vtkPoints object and store the points in it
    points = vtk.vtkPoints()
    points.InsertNextPoint(p0)
    points.InsertNextPoint(p1)
    points.InsertNextPoint(p2)
    points.InsertNextPoint(p3)

    # Create a cell array to store the lines in and add the lines to it
    lines = vtk.vtkCellArray()

    for i in range(0, 3, 2):
        line = vtk.vtkLine()
        line.GetPointIds().SetId(0, i)
        line.GetPointIds().SetId(1, i + 1)
        lines.InsertNextCell(line)

    linesPolyData = vtk.vtkPolyData()
    linesPolyData.SetPoints(points)
    linesPolyData.SetLines(lines)
    # ----------------------------------------------------
    colors = vtk.vtkCommonCore.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    try:
        colors.InsertNextTupleValue([255, 0, 0])
        colors.InsertNextTupleValue([0, 255, 0])
    except AttributeError:
        colors.InsertNextTypedTuple([255, 0, 0])
        colors.InsertNextTypedTuple([0, 255, 0])

    linesPolyData.GetCellData().SetScalars(colors)

    # Setup actor and mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(linesPolyData)
    return mapper


class LeftButton_Crosshair_GPS():
    def __init__(self, viewer_ID, viewer_XY, viewer_YZ, viewer_XZ, picker,
                 actor_Crosshair_XY, actor_Crosshair_YZ, actor_Crosshair_XZ,
                 label_XY, label_YZ, label_XZ):
        print("==============十字线定位开始=============")
        self.viewer_ID = viewer_ID
        self.viewer_XY = viewer_XY
        self.viewer_YZ = viewer_YZ
        self.viewer_XZ = viewer_XZ
        self.picker = picker
        self.actor_Crosshair_XY = actor_Crosshair_XY
        self.actor_Crosshair_YZ = actor_Crosshair_YZ
        self.actor_Crosshair_XZ = actor_Crosshair_XZ
        self.label_XY = label_XY
        self.label_YZ = label_YZ
        self.label_XZ = label_XZ

        self.image = self.viewer_XY.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.imageshape = self.image.GetDimensions()
        print("==============十字线定位开始2=============")

    def __call__(self, caller, ev):
        # -----------------------------------------------------------------------------------------------
        if self.viewer_ID == 'XY':
            print('Viewer_ID: ' + self.viewer_ID)
            viwer_current = self.viewer_XY
            self.picker.AddPickList(viwer_current.GetImageActor())
            self.picker.Pick(viwer_current.GetRenderWindow().GetInteractor().GetEventPosition()[0],
                             viwer_current.GetRenderWindow().GetInteractor().GetEventPosition()[1], 0,
                             viwer_current.GetRenderer())
            self.pos = self.picker.GetPickPosition()  # 获取图像的世界坐标
            self.pixel_pos = [int(self.pos[i] - viwer_current.GetInput().GetOrigin()[i])
                              / viwer_current.GetInput().GetSpacing()[i] for i in range(3)]
            self.pos_XY = np.array([self.pixel_pos[0], self.pixel_pos[1], viwer_current.GetSlice()], np.int32)
            print("==========十字线位置========")
            print(self.pos)
            # ---------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------------
            self.viewer_XY.SetSlice(self.pos_XY[2])
            self.label_XY.setText("Slice %d/%d" % (self.viewer_XY.GetSlice(), self.viewer_XY.GetSliceMax()))
            Origin_XY = self.viewer_XY.GetInput().GetOrigin()
            self.actor_Crosshair_XY.SetMapper(
                createLine_Crosshair([0, self.pos[1], self.pos[2]],
                                     [self.imageshape[0] * self.spacing[0] + Origin_XY[0], self.pos[1], self.pos[2]],
                                     [self.pos[0], 0, self.pos[2]],
                                     [self.pos[0], self.imageshape[1] * self.spacing[1] + Origin_XY[1], self.pos[2]]))

            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
            # ----------------------------------------------------------------------------------------------------------------
            self.viewer_YZ.SetSlice(self.pos_XY[0])
            self.label_YZ.setText("Slice %d/%d" % (self.viewer_YZ.GetSlice(), self.viewer_YZ.GetSliceMax()))
            Origin_YZ = self.viewer_YZ.GetInput().GetOrigin()
            self.actor_Crosshair_YZ.SetMapper(
                createLine_Crosshair(
                    [self.pos[0], self.imageshape[1] * self.spacing[1] + Origin_YZ[1] - self.pos[1], 0],
                    [self.pos[0], self.imageshape[1] * self.spacing[1] + Origin_YZ[1] - self.pos[1],
                     self.imageshape[2] * self.spacing[2] + Origin_YZ[2]],
                    [self.pos[0], 0, self.imageshape[2] * self.spacing[2] + Origin_YZ[2] - self.pos[2]],
                    [self.pos[0], self.imageshape[1] * self.spacing[1] + Origin_YZ[1],
                     self.imageshape[2] * self.spacing[2] + Origin_YZ[2] - self.pos[2]]))
            self.viewer_YZ.UpdateDisplayExtent()
            self.viewer_YZ.Render()
            # ----------------------------------------------------------------------------------------------------------------
            self.viewer_XZ.SetSlice(self.pos_XY[1])
            self.label_XZ.setText("Slice %d/%d" % (self.viewer_XZ.GetSlice(), self.viewer_XZ.GetSliceMax()))
            Origin_XZ = self.viewer_XZ.GetInput().GetOrigin()
            self.actor_Crosshair_XZ.SetMapper(
                createLine_Crosshair([self.pos[0], 0, 0],
                                     [self.pos[0], 0, self.imageshape[2] * self.spacing[2] + Origin_XZ[2]],
                                     [0, 0, self.imageshape[2] * self.spacing[2] + Origin_XZ[2] - self.pos[2]],
                                     [self.imageshape[0] * self.spacing[0] + Origin_XZ[0], 0,
                                      self.imageshape[2] * self.spacing[2] + Origin_XZ[2] - self.pos[2]]))
            self.viewer_XZ.UpdateDisplayExtent()
            self.viewer_XZ.Render()
        # ==============================================================================================================================================

        elif self.viewer_ID == 'YZ':
            print('Viewer_ID: ' + self.viewer_ID)
            viwer_current = self.viewer_YZ
            self.picker.AddPickList(viwer_current.GetImageActor())
            self.picker.Pick(viwer_current.GetRenderWindow().GetInteractor().GetEventPosition()[0],
                             viwer_current.GetRenderWindow().GetInteractor().GetEventPosition()[1], 0,
                             viwer_current.GetRenderer())
            self.pos = self.picker.GetPickPosition()  # 获取图像的世界坐标
            self.pixel_pos = [int(self.pos[i] - viwer_current.GetInput().GetOrigin()[i])
                              / viwer_current.GetInput().GetSpacing()[i] for i in range(3)]
            self.pos_XY = np.array([viwer_current.GetSlice(), self.pixel_pos[1], self.pixel_pos[2]], np.int32)
            print("==========十字线位置========")
            print(self.pos)
            # ---------------------------------------------------------------------------------------------
            # ----------------------------------------------------------------------------------------------------------------
            self.viewer_YZ.SetSlice(self.pos_XY[0])
            self.label_YZ.setText("Slice %d/%d" % (self.viewer_YZ.GetSlice(), self.viewer_YZ.GetSliceMax()))
            Origin_YZ = self.viewer_YZ.GetInput().GetOrigin()
            self.actor_Crosshair_YZ.SetMapper(
                createLine_Crosshair(
                    [self.pos[0], self.pos[1], 0],
                    [self.pos[0], self.pos[1], self.imageshape[2] * self.spacing[2] + Origin_YZ[2]],
                    [self.pos[0], 0, self.pos[2]],
                    [self.pos[0], self.imageshape[1] * self.spacing[1] + Origin_YZ[1], self.pos[2]]))
            self.viewer_YZ.UpdateDisplayExtent()
            self.viewer_YZ.Render()
            # ----------------------------------------------------------------------------------------------------------------
            self.viewer_XY.SetSlice(self.imageshape[2] - self.pos_XY[2])
            self.label_XY.setText("Slice %d/%d" % (self.viewer_XY.GetSlice(), self.viewer_XY.GetSliceMax()))
            Origin_XY = self.viewer_XY.GetInput().GetOrigin()
            self.actor_Crosshair_XY.SetMapper(
                createLine_Crosshair(
                    [0, self.imageshape[1] * self.spacing[1] + Origin_XY[1] - self.pos[1], self.imageshape[2]],
                    [self.imageshape[0] * self.spacing[0] + Origin_XY[0],
                     self.imageshape[1] * self.spacing[1] + Origin_XY[1] - self.pos[1], self.imageshape[2]],
                    [self.pos[0], 0, self.imageshape[2]],
                    [self.pos[0], self.imageshape[1] * self.spacing[1] + Origin_XY[1], self.imageshape[2]]))

            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
            # ----------------------------------------------------------------------------------------------------------------
            self.viewer_XZ.SetSlice(self.imageshape[1] - self.pos_XY[1])
            self.label_XZ.setText("Slice %d/%d" % (self.viewer_XZ.GetSlice(), self.viewer_XZ.GetSliceMax()))
            Origin_XZ = self.viewer_XZ.GetInput().GetOrigin()
            self.actor_Crosshair_XZ.SetMapper(
                createLine_Crosshair([self.pos[0], 0, 0],
                                     [self.pos[0], 0, self.imageshape[2] * self.spacing[2] + Origin_XZ[2]],
                                     [0, 0, self.pos[2]],
                                     [self.imageshape[0] * self.spacing[0] + Origin_XZ[0], 0, self.pos[2]]))
            self.viewer_XZ.UpdateDisplayExtent()
            self.viewer_XZ.Render()
        # ==============================================================================================================================================
        else:
            print('Viewer_ID: ' + self.viewer_ID)
            viwer_current = self.viewer_XZ
            self.picker.AddPickList(viwer_current.GetImageActor())
            self.picker.Pick(viwer_current.GetRenderWindow().GetInteractor().GetEventPosition()[0],
                             viwer_current.GetRenderWindow().GetInteractor().GetEventPosition()[1], 0,
                             viwer_current.GetRenderer())
            self.pos = self.picker.GetPickPosition()  # 获取图像的世界坐标
            self.pixel_pos = [int(self.pos[i] - viwer_current.GetInput().GetOrigin()[i])
                              / viwer_current.GetInput().GetSpacing()[i] for i in range(3)]
            self.pos_XY = np.array([self.pixel_pos[0], viwer_current.GetSlice(), self.pixel_pos[2]], np.int32)
            print("==========十字线位置========")
            print(self.pos)
            # ---------------------------------------------------------------------------------------------
            self.viewer_XZ.SetSlice(self.pos_XY[1])
            self.label_XZ.setText("Slice %d/%d" % (self.viewer_XZ.GetSlice(), self.viewer_XZ.GetSliceMax()))
            Origin_XZ = self.viewer_XZ.GetInput().GetOrigin()
            self.actor_Crosshair_XZ.SetMapper(
                createLine_Crosshair([self.pos[0], 0, 0],
                                     [self.pos[0], 0, self.imageshape[2] * self.spacing[2] + Origin_XZ[2]],
                                     [0, 0, self.pos[2]],
                                     [self.imageshape[0] * self.spacing[0] + Origin_XZ[0], 0, self.pos[2]]))
            self.viewer_XZ.UpdateDisplayExtent()
            self.viewer_XZ.Render()
            # ----------------------------------------------------------------------------------------------------------------
            self.viewer_YZ.SetSlice(self.pos_XY[0])
            self.label_YZ.setText("Slice %d/%d" % (self.viewer_YZ.GetSlice(), self.viewer_YZ.GetSliceMax()))
            Origin_YZ = self.viewer_YZ.GetInput().GetOrigin()
            self.actor_Crosshair_YZ.SetMapper(
                createLine_Crosshair(
                    [self.pos[0], self.pos[1], 0],
                    [self.pos[0], self.pos[1], self.imageshape[2] * self.spacing[2] + Origin_YZ[2]],
                    [self.pos[0], 0, self.pos[2]],
                    [self.pos[0], self.imageshape[1] * self.spacing[1] + Origin_YZ[1], self.pos[2]]))
            self.viewer_YZ.UpdateDisplayExtent()
            self.viewer_YZ.Render()
            # ----------------------------------------------------------------------------------------------------------------
            self.viewer_XY.SetSlice(self.imageshape[2] - self.pos_XY[2])
            self.label_XY.setText("Slice %d/%d" % (self.viewer_XY.GetSlice(), self.viewer_XY.GetSliceMax()))
            Origin_XY = self.viewer_XY.GetInput().GetOrigin()
            self.actor_Crosshair_XY.SetMapper(
                createLine_Crosshair(
                    [0, self.imageshape[1] * self.spacing[1] + Origin_XY[1] - self.pos[1], self.imageshape[2]],
                    [self.imageshape[0] * self.spacing[0] + Origin_XY[0],
                     self.imageshape[1] * self.spacing[1] + Origin_XY[1] - self.pos[1], self.imageshape[2]],
                    [self.pos[0], 0, self.imageshape[2]],
                    [self.pos[0], self.imageshape[1] * self.spacing[1] + Origin_XY[1], self.imageshape[2]]))

            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
            # ----------------------------------------------------------------------------------------------------------------
        # ==============================================================================================================================================


class CommandSelect():
    def __init__(self, view_ID, reader, vtkWidget, vtkWidget2, vtkWidget3, resliceCursorWidget_XY,
                 resliceCursorWidget_YZ, resliceCursorWidget_XZ, resliceCursor,
                 verticalSlider_XY, verticalSlider_YZ, verticalSlider_XZ, label_XY, label_YZ, label_XZ):
        self.view_ID = view_ID
        # self.resliceCursorPicker = resliceCursorPicker
        self.resliceCursorWidget_XY = resliceCursorWidget_XY
        self.resliceCursorWidget_YZ = resliceCursorWidget_YZ
        self.resliceCursorWidget_XZ = resliceCursorWidget_XZ
        self.resliceCursor = resliceCursor
        self.vtkWidget = vtkWidget
        self.vtkWidget2 = vtkWidget2
        self.vtkWidget3 = vtkWidget3
        self.verticalSlider_XY = verticalSlider_XY
        self.verticalSlider_YZ = verticalSlider_YZ
        self.verticalSlider_XZ = verticalSlider_XZ
        self.label_XY = label_XY
        self.label_YZ = label_YZ
        self.label_XZ = label_XZ
        self.reader = reader
        self.image = self.reader.GetOutput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.imageshape = self.image.GetDimensions()

    def __call__(self, caller, ev):
        # print( self.resliceCursor.GetCenter())
        slider_value = self.resliceCursor.GetCenter()
        # print("Picker Center:", slider_value)
        # xv = int((slider_value[0] - self.origin[0]) / self.spacing[0])
        # yv = int((slider_value[1] - self.origin[1]) / self.spacing[1])
        # zv = int((slider_value[2] - self.origin[2]) / self.spacing[2])
        # print([xv, yv, zv])

        if self.view_ID == "XY":
            rep_YZ = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_YZ.GetRepresentation())
            rep_XZ = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_XZ.GetRepresentation())
            # self.verticalSlider_YZ.setValue(slider_value[0])
            # self.verticalSlider_XZ.setValue(slider_value[1])
            # print("Picker XY:", self.resliceCursorPicker.GetPickedCenter())
            self.verticalSlider_YZ.setValue(int((slider_value[0] - self.origin[0]) / self.spacing[0]))
            self.verticalSlider_XZ.setValue(int((slider_value[1] - self.origin[1]) / self.spacing[1]))
            self.verticalSlider_XY.setValue(int((slider_value[2] - self.origin[2]) / self.spacing[2]))
            self.label_XY.setText("Slice %d/%d" % (self.verticalSlider_XY.value(), self.imageshape[2]))
            self.label_YZ.setText("Slice %d/%d" % (self.verticalSlider_YZ.value(), self.imageshape[1]))
            self.label_XZ.setText("Slice %d/%d" % (self.verticalSlider_XZ.value(), self.imageshape[0]))

            self.vtkWidget.GetRenderWindow().Render()
            self.vtkWidget2.GetRenderWindow().Render()
            self.vtkWidget3.GetRenderWindow().Render()
        elif self.view_ID == "YZ":
            rep_XY = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_XY.GetRepresentation())
            rep_XZ = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_XZ.GetRepresentation())
            self.verticalSlider_XY.setValue(int((slider_value[2] - self.origin[2]) / self.spacing[2]))
            self.verticalSlider_XZ.setValue(int((slider_value[1] - self.origin[1]) / self.spacing[1]))
            self.verticalSlider_YZ.setValue(int((slider_value[0] - self.origin[0]) / self.spacing[0]))
            # self.verticalSlider_XY.setValue(slider_value[2])
            # self.verticalSlider_XZ.setValue(slider_value[1])
            # print("Picker YZ:", self.resliceCursorPicker.GetPickedCenter())
            self.label_XY.setText("Slice %d/%d" % (self.verticalSlider_XY.value(), self.imageshape[2]))
            self.label_YZ.setText("Slice %d/%d" % (self.verticalSlider_YZ.value(), self.imageshape[1]))
            self.label_XZ.setText("Slice %d/%d" % (self.verticalSlider_XZ.value(), self.imageshape[0]))
            self.vtkWidget2.GetRenderWindow().Render()
            self.vtkWidget.GetRenderWindow().Render()
            self.vtkWidget3.GetRenderWindow().Render()
        else:
            rep_XY = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_XY.GetRepresentation())
            rep_YZ = vtkResliceCursorLineRepresentation.SafeDownCast(self.resliceCursorWidget_YZ.GetRepresentation())
            # rc_YZ = rep_YZ.GetResliceCursorActor().GetCursorAlgorithm().GetResliceCursor()
            self.verticalSlider_XY.setValue(int((slider_value[2] - self.origin[2]) / self.spacing[2]))
            self.verticalSlider_YZ.setValue(int((slider_value[0] - self.origin[0]) / self.spacing[0]))
            self.verticalSlider_XZ.setValue(int((slider_value[1] - self.origin[1]) / self.spacing[1]))
            # self.verticalSlider_XY.setValue(slider_value[2])
            # self.verticalSlider_YZ.setValue(slider_value[0])
            # print("Picker XZ:", self.resliceCursorPicker.GetPickedCenter())
            self.label_XY.setText("Slice %d/%d" % (self.verticalSlider_XY.value(), self.imageshape[2]))
            self.label_YZ.setText("Slice %d/%d" % (self.verticalSlider_YZ.value(), self.imageshape[1]))
            self.label_XZ.setText("Slice %d/%d" % (self.verticalSlider_XZ.value(), self.imageshape[0]))
            self.vtkWidget3.GetRenderWindow().Render()
            self.vtkWidget.GetRenderWindow().Render()
            self.vtkWidget2.GetRenderWindow().Render()


class LeftButtonPressEvent_Point():
    def __init__(self, picker,viewer):
        self.picker = picker
        self.start = []
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.imageshape = self.view.GetInput().GetDimensions()
        self.point_dict = {}

    def __call__(self, caller, ev):
        self.picker.AddPickList(self.actor)
        self.picker.SetTolerance(0.01)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.start = self.picker.GetPickPosition()
        print(self.start)

        point_x = int((self.start[0] - self.origin[0])/self.spacing[0])
        point_y = int((self.start[1] - self.origin[1]) / self.spacing[1])
        point_z = int((self.start[2] - self.origin[2]) / self.spacing[2])

        if point_x < 0 or point_x > self.imageshape[0] or point_y < 0 or point_y > self.imageshape[1]:
            return

        self.start_pos = [point_x,point_y,point_z]

        if getSelectPointLabel1():
            label = 1
        else:
            label = 0
        index = point_z
        if str(index) in self.point_dict:
            self.point_dict[str(index)]["points"].append([point_x, point_y])
            self.point_dict[str(index)]["label"].append(label)
        else:
            self.point_dict[str(index)] = {"points": [[point_x,point_y]], "label":[label], "image_name": "_image_"+str(point_z)+".png"}
        setPointsDict(self.point_dict)
        print(getPointsDict())

        square = vtk.vtkPolyData()

        points = vtk.vtkPoints()
        points.InsertNextPoint(self.start[0]-1, self.start[1]+1, point_z)
        points.InsertNextPoint(self.start[0]+1, self.start[1]+1, point_z)
        points.InsertNextPoint(self.start[0]+1, self.start[1]-1, point_z)
        points.InsertNextPoint(self.start[0]-1, self.start[1]-1, point_z)

        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(4)
        polygon.GetPointIds().SetId(0, 0)
        polygon.GetPointIds().SetId(1, 1)
        polygon.GetPointIds().SetId(2, 2)
        polygon.GetPointIds().SetId(3, 3)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(polygon)

        square.SetPoints(points)
        square.SetPolys(cells)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(square)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0,1,0)
        setPointsUndoStack([point_x,point_y,point_z,label])
        print(getPointsUndoStack())
        self.square_actor = actor
        setPointsActor(self.square_actor)
        self.ren = self.view.GetRenderer()
        self.ren.AddActor(actor)
        self.iren.Render()
        self.render.Render()
        self.view.UpdateDisplayExtent()
        self.view.Render()

class LeftButtonPressEvent_labelBox():
    def __init__(self, picker,viewer):
        self.picker = picker
        self.start = []
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.imageshape = self.view.GetInput().GetDimensions()
        self.count = 0
        self.actor_list = []
        self.single_boundingBox_dict = {}
        self.multiple_boundingBox_dict = {}

    def __call__(self, caller, ev):
        self.picker.AddPickList(self.actor)
        self.count += 1
        self.start, self.start_pos= self.get_point_position() # tuple list
        print(self.start)
        if self.count % 2 != 0:
            setState2True()
            setStartPoint(self.start)
            if getSelectSingleBoxLabel():
                try:
                    for i in getSingleBoundingBoxActor():
                        self.view.GetRenderer().RemoveActor(i)
                    self.view.Render()
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
        else:
            setState2False()
            if getSelectSingleBoxLabel():
                boundingbox_dict = getSingleBoundingBoxDict()
                index = getSingleBoundingBox()[4]
                if str(index) in boundingbox_dict.keys():
                    del boundingbox_dict[str(index)]
                    single_boundingbox = getSingleUndoStack()
                    # 记录要删除的索引
                    indices_to_remove = [i for i, point in enumerate(single_boundingbox) if point[-1] == index]
                    # 原地删除元素
                    for i in sorted(indices_to_remove, reverse=True):
                        del single_boundingbox[i]
                setSingleUndoStack(getSingleBoundingBox())

                if str(index) in self.single_boundingBox_dict:
                    self.single_boundingBox_dict[str(index)]["bounding_box"] = getSingleBoundingBox()
                else:
                    self.single_boundingBox_dict[str(index)] = {"bounding_box": getSingleBoundingBox(),"image_name": "_image_" + str(index) + ".png"}
                setSingleBoundingBoxDict(self.single_boundingBox_dict)
            else:
                try:
                    for actor in getMultipleBoundingBoxActor():
                        for i in actor:
                            self.view.GetRenderer().RemoveActor(i)
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                setMultipleUndoStack(getSingleBoundingBox())
                index = getSingleBoundingBox()[4]
                if str(index) in self.multiple_boundingBox_dict:
                    self.multiple_boundingBox_dict[str(index)]["bounding_box"].append(getSingleBoundingBox())
                else:
                    self.multiple_boundingBox_dict[str(index)] = {"bounding_box": [getSingleBoundingBox()], "image_name": "_image_" + str(index) + ".png"}
                setMultipleBoundingBoxDict(self.multiple_boundingBox_dict)

                value = self.view.GetSlice()
                if getMultipleUndoStack() != []:
                    for data in getMultipleUndoStack():
                        if data[4] == value:
                            self.actor_list = []
                            self.drwa_single_bounding_box(data)
                            setMultipleBoundingBoxActor(self.actor_list)
                self.view.UpdateDisplayExtent()
                self.view.Render()


        self.iren.Render()
        self.render.Render()
        self.view.UpdateDisplayExtent()
        self.view.Render()

    def drwa_single_bounding_box(self,data):
        start_pointX = data[0] * self.spacing[0] + self.origin[0]
        start_pointY = data[1] * self.spacing[1] + self.origin[1]
        end_pointX = data[2] * self.spacing[0] + self.origin[0]
        end_pointY = data[3] * self.spacing[1] + self.origin[1]

        start=[start_pointX,start_pointY]
        end=[end_pointX,end_pointY]

        left = [0, 0]
        right = [0, 0]

        left[0] = start[0] if start[0] <= end[0] else end[0]
        left[1] = start[1] if start[1] <= end[1] else end[1]

        right[0] = start[0] if start[0] > end[0] else end[0]
        right[1] = start[1] if start[1] > end[1] else end[1]

        point1 = [left[0], left[1], data[4]]
        point2 = [left[0], right[1], data[4]]
        point3 = [right[0], right[1], data[4]]
        point4 = [right[0], left[1], data[4]]

        self.SetLine(point1, point2)
        self.SetLine(point2, point3)
        self.SetLine(point3, point4)
        self.SetLine(point4, point1)

    def SetLine(self, point1, point2):
        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(point1)
        lineSource.SetPoint2(point2)
        lineSource.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(2)
        actor.GetProperty().SetColor(0.0, 1.0, 1.0)
        self.actor_list.append(actor)
        self.view.GetRenderer().AddActor(actor)

    def get_point_position(self):
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.view.GetRenderer())
        pos = self.picker.GetPickPosition()
        point_x = int((pos[0] - self.origin[0]) / self.spacing[0])
        point_y = int((pos[1] - self.origin[1]) / self.spacing[1])
        point_z = int((pos[2] - self.origin[2]) / self.spacing[2])
        return pos,[point_x, point_y, point_z]

class MouseMoveEvent_labelBox():
    def __init__(self, picker,viewer):
        self.picker = picker
        self.start = []
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.square_actor = None
        self.imageshape = self.view.GetInput().GetDimensions()
        self.actor_list = []

    def __call__(self, caller, ev):
        if getSelectSingleBoxLabel():
            if getState2():
                setSingleBoundingBox([])
                try:
                    for i in range(len(self.actor_list)):
                        self.view.GetRenderer().RemoveActor(self.actor_list[i])
                    self.actor_list = []
                except:
                    print("clear actor failed!!!")
                self.picker.AddPickList(self.actor)
                self.start = getStartPoint()
                self.start_pos = [int((self.start[i] - self.origin[i])/self.spacing[i]) for i in range(3)]
                self.end, self.end_pos = self.get_point_position()
                setSingleBoundingBox([self.start_pos[0],self.start_pos[1],self.end_pos[0],self.end_pos[1],self.end_pos[2]])
                self.draw_single_label_box(self.start,self.end)
                setSingleBoundingBoxActor(self.actor_list)
                self.view.UpdateDisplayExtent()
                self.view.Render()
            else:
                pass
        else:
            if getState2():
                setBoundingBoxOriginal([])
                try:
                    for i in range(len(self.actor_list)):
                        self.view.GetRenderer().RemoveActor(self.actor_list[i])
                    self.actor_list = []
                except:
                    print("clear actor failed!!!")
                self.picker.AddPickList(self.actor)
                self.start = getStartPoint()
                self.start_pos = [int((self.start[i] - self.origin[i]) / self.spacing[i]) for i in range(3)]
                self.end, self.end_pos = self.get_point_position()
                setSingleBoundingBox([self.start_pos[0], self.start_pos[1], self.end_pos[0], self.end_pos[1], self.end_pos[2]])
                setBoundingBoxOriginal([self.start[0], self.start[1], self.end[0], self.end[1], self.end[2]])
                self.draw_single_label_box(self.start,self.end)
                setLastBoundingBoxActor(self.actor_list)
                self.view.UpdateDisplayExtent()
                self.view.Render()

    def get_point_position(self):
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.view.GetRenderer())
        pos = self.picker.GetPickPosition()
        point_x = int((pos[0] - self.origin[0]) / self.spacing[0])
        point_y = int((pos[1] - self.origin[1]) / self.spacing[1])
        point_z = int((pos[2] - self.origin[2]) / self.spacing[2])
        return pos, [point_x, point_y, point_z]

    def SetLine(self, point1, point2):
        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(point1)
        lineSource.SetPoint2(point2)
        lineSource.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(2)
        actor.GetProperty().SetColor(0.0, 1.0, 1.0)
        self.actor_list.append(actor)
        self.view.GetRenderer().AddActor(actor)

    def draw_single_label_box(self,start,end):
        left = [0, 0]
        right = [0, 0]

        left[0] = start[0] if start[0] <= end[0] else end[0]
        left[1] = start[1] if start[1] <= end[1] else end[1]

        right[0] = start[0] if start[0] > end[0] else end[0]
        right[1] = start[1] if start[1] > end[1] else end[1]

        point1 = [left[0], left[1], start[2]]
        point2 = [left[0], right[1], start[2]]
        point3 = [right[0], right[1], start[2]]
        point4 = [right[0], left[1], start[2]]

        self.SetLine(point1, point2)
        self.SetLine(point2, point3)
        self.SetLine(point3, point4)
        self.SetLine(point4, point1)

class LeftButtonPressEvent_Dragging():
    def __init__(self, viewer):
        self.view = viewer
        self.iren = self.view.GetRenderWindow().GetInteractor()

    def __call__(self, caller, ev):
        self.start = self.iren.GetEventPosition()
        setStartPoint(self.start)
        setLeftButtonDown(True)


class LeftButtonReleaseEvent_Dragging():
    def __init__(self, viewer):
        self.view = viewer

    def __call__(self, caller, ev):
        setLeftButtonDown(False)


class MouseMoveEvent_Dragging():
    def __init__(self, viewer):
        self.start = []
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.square_actor = None
        self.imageshape = self.view.GetInput().GetDimensions()
        self.camera = self.view.GetRenderer().GetActiveCamera()

    def ComputeWorldToDisplay(self, renderer, worldPt, displayPt):
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToWorld()
        coord.SetValue(worldPt)
        displayPt = coord.GetComputedDisplayValue(renderer)

    def ComputeDisplayToWorld(self, renderer, displayPt, worldPt):
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToDisplay()
        coord.SetValue(displayPt[0], displayPt[1], displayPt[2])
        worldPt[:] = coord.GetComputedWorldValue(renderer)

    def __call__(self, caller, ev):
        if getLeftButtonDown():
            print("左键按下")
            self.start = getStartPoint()
            self.end = self.iren.GetEventPosition()
            delta_x = self.end[0] - self.start[0]
            delta_y = self.end[1] - self.start[1]
            self.camera = self.render.GetActiveCamera()
            self.move_camera(self.start[0], self.start[1], delta_x, delta_y)
            setStartPoint(self.end)
            self.view.SliceScrollOnMouseWheelOff()
            self.view.Render()
            self.view.UpdateDisplayExtent()
            self.view.Render()

    def move_camera(self, x, y, delta_x, delta_y):
        view_focus_3d = self.camera.GetFocalPoint()
        view_focus_2d = [0, 0, 0]
        self.ComputeWorldToDisplay(self.render, view_focus_3d, view_focus_2d)
        new_mouse_point = [0, 0, 0, 1]
        self.ComputeDisplayToWorld(self.render, [x, y, view_focus_2d[2]], new_mouse_point)
        old_mouse_point = [0, 0, 0, 1]
        self.ComputeDisplayToWorld(self.render, [x - delta_x, y - delta_y, view_focus_2d[2]], old_mouse_point)
        motion_vector = [0, 0, 0]
        motion_vector[0] = old_mouse_point[0] - new_mouse_point[0]
        motion_vector[1] = old_mouse_point[1] - new_mouse_point[1]
        motion_vector[2] = old_mouse_point[2] - new_mouse_point[2]

        view_focus = self.camera.GetFocalPoint()
        view_point = self.camera.GetPosition()
        self.camera.SetFocalPoint(motion_vector[0] + view_focus[0], motion_vector[1] + view_focus[1],
                                  motion_vector[2] + view_focus[2])
        self.camera.SetPosition(motion_vector[0] + view_point[0], motion_vector[1] + view_point[1],
                                motion_vector[2] + view_point[2])
        self.iren.Render()


class MouseMoveEvent_GetROI():
    def __init__(self, picker, viewer_xy, viewer_yz, viewer_xz, type):
        self.picker = picker  # 坐标拾取
        self.view_xy = viewer_xy
        self.view_yz = viewer_yz
        self.view_xz = viewer_xz
        self.actor_xy = self.view_xy.GetImageActor()
        self.actor_yz = self.view_yz.GetImageActor()
        self.actor_xz = self.view_xz.GetImageActor()
        self.iren_xy = self.view_xy.GetRenderWindow().GetInteractor()
        self.iren_yz = self.view_yz.GetRenderWindow().GetInteractor()
        self.iren_xz = self.view_xz.GetRenderWindow().GetInteractor()
        self.render_xy = self.view_xy.GetRenderer()
        self.render_yz = self.view_yz.GetRenderer()
        self.render_xz = self.view_xz.GetRenderer()
        self.origin_xy = self.view_xy.GetInput().GetOrigin()
        self.origin_yz = self.view_yz.GetInput().GetOrigin()
        self.origin_xz = self.view_xz.GetInput().GetOrigin()
        self.spacing_xy = self.view_xy.GetInput().GetSpacing()
        self.spacing_yz = self.view_yz.GetInput().GetSpacing()
        self.spacing_xz = self.view_xz.GetInput().GetSpacing()
        self.ren_xy = self.view_xy.GetRenderer()
        self.ren_yz = self.view_yz.GetRenderer()
        self.ren_xz = self.view_xz.GetRenderer()
        self.imageshape = self.view_xy.GetInput().GetDimensions()
        self.temp_actor = None
        self.type = type
        self.radius_xy = (3 - self.origin_xy[0]) / self.spacing_xy[0]

    def __call__(self, caller, ev):
        roi_dict = getControlROIPoint()
        if self.type == "view_xy":
            self.picker.AddPickList(self.actor_xy)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_xy.GetEventPosition()[0], self.iren_xy.GetEventPosition()[1], 0, self.render_xy)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_xy[i])) / self.spacing_xy[i] for i in range(3)]
            if self.start_pos[0] < 0 or self.start_pos[0] > self.imageshape[0] or self.start_pos[1] < 0 or \
                    self.start_pos[1] > self.imageshape[1]:
                return
        elif self.type == "view_yz":
            self.picker.AddPickList(self.actor_yz)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_yz.GetEventPosition()[0], self.iren_yz.GetEventPosition()[1], 0, self.render_yz)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_yz[i])) / self.spacing_yz[i] for i in range(3)]
            if self.start_pos[1] < 0 or self.start_pos[1] > self.imageshape[1] or self.start_pos[2] < 0 or \
                    self.start_pos[2] > self.imageshape[2]:
                return
        elif self.type == "view_xz":
            self.picker.AddPickList(self.actor_xz)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_xz.GetEventPosition()[0], self.iren_xz.GetEventPosition()[1], 0, self.render_xz)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_xz[i])) / self.spacing_xz[i] for i in range(3)]
            if self.start_pos[0] < 0 or self.start_pos[0] > self.imageshape[0] or self.start_pos[2] < 0 or \
                    self.start_pos[2] > self.imageshape[2]:
                return

        self.update_rectangle_position(roi_dict, self.type)

    def is_point_inside_circle(self, circle_center, point, radius=3):
        if self.type == "view_xy":
            cx, cy = circle_center
            cx = cx * self.spacing_xy[0] + self.origin_xy[0]
            cy = cy * self.spacing_xy[1] + self.origin_xy[1]
            c1 = cx
            c2 = cy
        elif self.type == "view_yz":
            cy, cz = circle_center
            cy = cy * self.spacing_yz[1] + self.origin_yz[1]
            cz = cz * self.spacing_yz[2] + self.origin_yz[2]
            c1 = cy
            c2 = cz
        else:
            cx, cz = circle_center
            cx = cx * self.spacing_xz[0] + self.origin_xz[0]
            cz = cz * self.spacing_xz[2] + self.origin_xz[2]
            c1 = cx
            c2 = cz
        px, py = point
        if (-radius <= px - c1 <= radius) and (-radius <= py - c2 <= radius):
            return True
        return False

    def update_rectangle_position(self, roi_dict, type):
        if type == "view_xy":
            if get_left_down_is_clicked():
                #  这里还要判断移动的点与固定的点的位置  然后进行位置更新
                end_point_x = roi_dict[type]["right_up_point"]["point"][0]
                end_point_y = roi_dict[type]["right_up_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][0]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][1]
                roi_dict[type]["left_down_point"]["point"] = [self.start_pos[0], self.start_pos[1],
                                                              self.imageshape[2] + 1]
                roi_dict[type]["left_up_point"]["point"] = [self.start_pos[0], end_point_y, self.imageshape[2] + 1]
                roi_dict[type]["right_down_point"]["point"] = [end_point_x, self.start_pos[1], self.imageshape[2] + 1]

                roi_dict[type]["left_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["right_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                # 更新XZ视图
                roi_dict["view_xz"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2
                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_mid_is_clicked():
                end_point_x = roi_dict[type]["left_mid_point"]["point"][0]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - end_point_x
                roi_dict[type]["left_down_point"]["point"][0] += dx
                roi_dict[type]["left_up_point"]["point"][0] += dx
                roi_dict[type]["left_mid_point"]["point"][0] += dx
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_xz"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_up_is_clicked():
                end_point_x = roi_dict[type]["right_down_point"]["point"][0]
                end_point_y = roi_dict[type]["right_down_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    0]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    1]
                roi_dict[type]["left_up_point"]["point"] = [self.start_pos[0], self.start_pos[1],
                                                            self.imageshape[2] + 1]
                roi_dict[type]["left_down_point"]["point"] = [self.start_pos[0], end_point_y, self.imageshape[2] + 1]
                roi_dict[type]["right_up_point"]["point"] = [end_point_x, self.start_pos[1], self.imageshape[2] + 1]
                roi_dict[type]["left_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["right_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_up_mid_is_clicked():
                end_point_y = roi_dict[type]["up_mid_point"]["point"][1]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                roi_dict[type]["up_mid_point"]["point"][1] += dy
                roi_dict[type]["left_up_point"]["point"][1] += dy
                roi_dict[type]["right_up_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_yz"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)


            elif get_down_mid_is_clicked():
                end_point_y = roi_dict[type]["down_mid_point"]["point"][1]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                roi_dict[type]["down_mid_point"]["point"][1] += dy
                roi_dict[type]["left_down_point"]["point"][1] += dy
                roi_dict[type]["right_down_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_yz"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_down_is_clicked():
                end_point_x = roi_dict[type]["left_up_point"]["point"][0]
                end_point_y = roi_dict[type]["left_up_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][0]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][1]
                roi_dict[type]["right_down_point"]["point"] = [self.start_pos[0], self.start_pos[1],
                                                               self.imageshape[2] + 1]
                roi_dict[type]["right_up_point"]["point"] = [self.start_pos[0], end_point_y, self.imageshape[2] + 1]
                roi_dict[type]["left_down_point"]["point"] = [end_point_x, self.start_pos[1], self.imageshape[2] + 1]
                roi_dict[type]["right_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["left_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["right_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["right_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_mid_is_clicked():
                end_point_x = roi_dict[type]["right_mid_point"]["point"][0]
                dx = end_point_x - max(0, min(self.start_pos[0], self.imageshape[0] - 1))
                roi_dict[type]["right_down_point"]["point"][0] -= dx
                roi_dict[type]["right_up_point"]["point"][0] -= dx
                roi_dict[type]["right_mid_point"]["point"][0] -= dx
                roi_dict[type]["down_mid_point"]["point"][0] -= dx / 2
                roi_dict[type]["up_mid_point"]["point"][0] -= dx / 2
                roi_dict[type]["mid_point"]["point"][0] -= dx / 2

                roi_dict["view_xz"]["right_down_point"]["point"][0] -= dx
                roi_dict["view_xz"]["right_up_point"]["point"][0] -= dx
                roi_dict["view_xz"]["right_mid_point"]["point"][0] -= dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] -= dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] -= dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] -= dx / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_up_is_clicked():
                end_point_x = roi_dict[type]["left_down_point"]["point"][0]
                end_point_y = roi_dict[type]["left_down_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    0]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    1]
                roi_dict[type]["right_up_point"]["point"] = [self.start_pos[0], self.start_pos[1],
                                                             self.imageshape[2] + 1]
                roi_dict[type]["right_down_point"]["point"] = [self.start_pos[0], end_point_y, self.imageshape[2] + 1]
                roi_dict[type]["left_up_point"]["point"] = [end_point_x, self.start_pos[1], self.imageshape[2] + 1]
                roi_dict[type]["right_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["left_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["right_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["right_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_mid_is_clicked():
                end_point_x = roi_dict[type]["mid_point"]["point"][0]
                end_point_y = roi_dict[type]["mid_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - end_point_x
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                roi_dict[type]["mid_point"]["point"] = [self.start_pos[0], self.start_pos[1], self.imageshape[2] + 1]
                roi_dict[type]["right_down_point"]["point"][0] += dx
                roi_dict[type]["right_down_point"]["point"][1] += dy
                roi_dict[type]["right_mid_point"]["point"][0] += dx
                roi_dict[type]["right_mid_point"]["point"][1] += dy
                roi_dict[type]["down_mid_point"]["point"][0] += dx
                roi_dict[type]["down_mid_point"]["point"][1] += dy
                roi_dict[type]["up_mid_point"]["point"][0] += dx
                roi_dict[type]["up_mid_point"]["point"][1] += dy
                roi_dict[type]["left_up_point"]["point"][0] += dx
                roi_dict[type]["left_up_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][0] += dx
                roi_dict[type]["left_mid_point"]["point"][1] += dy
                roi_dict[type]["left_down_point"]["point"][0] += dx
                roi_dict[type]["left_down_point"]["point"][1] += dy
                roi_dict[type]["right_up_point"]["point"][0] += dx
                roi_dict[type]["right_up_point"]["point"][1] += dy

                roi_dict["view_xz"]["right_down_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_up_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_up_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_down_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_up_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_up_point"]["point"][1] += dy
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
        elif type == "view_yz":
            if get_left_down_is_clicked():
                end_point_y = roi_dict[type]["right_up_point"]["point"][1]
                end_point_z = roi_dict[type]["right_up_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][1]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][2]

                roi_dict[type]["left_down_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1],
                                                              self.start_pos[2]]
                roi_dict[type]["left_up_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], end_point_z]
                roi_dict[type]["right_down_point"]["point"] = [self.imageshape[0] + 1, end_point_y, self.start_pos[2]]
                roi_dict[type]["left_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["right_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["down_mid_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2
                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_mid_is_clicked():
                end_point_y = roi_dict[type]["left_mid_point"]["point"][1]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                roi_dict[type]["left_down_point"]["point"][1] += dy
                roi_dict[type]["left_up_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][1] += dy
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["down_mid_point"]["point"][1] += dy

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_up_is_clicked():
                end_point_y = roi_dict[type]["right_down_point"]["point"][1]
                end_point_z = roi_dict[type]["right_down_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    1]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    2]
                roi_dict[type]["left_up_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1],
                                                            self.start_pos[2]]
                roi_dict[type]["left_down_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], end_point_z]
                roi_dict[type]["right_up_point"]["point"] = [self.imageshape[0] + 1, end_point_y, self.start_pos[2]]
                roi_dict[type]["left_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["right_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["down_mid_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_up_mid_is_clicked():
                end_point_z = roi_dict[type]["up_mid_point"]["point"][2]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["up_mid_point"]["point"][2] += dz
                roi_dict[type]["left_up_point"]["point"][2] += dz
                roi_dict[type]["right_up_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_down_mid_is_clicked():
                end_point_z = roi_dict[type]["down_mid_point"]["point"][2]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["down_mid_point"]["point"][2] += dz
                roi_dict[type]["left_down_point"]["point"][2] += dz
                roi_dict[type]["right_down_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_down_is_clicked():
                end_point_y = roi_dict[type]["left_up_point"]["point"][1]
                end_point_z = roi_dict[type]["left_up_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][1]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][2]
                roi_dict[type]["right_down_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1],
                                                               self.start_pos[2]]
                roi_dict[type]["right_up_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], end_point_z]
                roi_dict[type]["left_down_point"]["point"] = [self.imageshape[0] + 1, end_point_y, self.start_pos[2]]
                roi_dict[type]["right_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["left_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["right_up_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_up_point"]["point"][1] += dy
                roi_dict["view_xy"]["up_mid_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_mid_is_clicked():
                end_point_y = roi_dict[type]["right_mid_point"]["point"][1]
                dy = end_point_y - max(0, min(self.start_pos[1], self.imageshape[1] - 1))
                roi_dict[type]["right_down_point"]["point"][1] -= dy
                roi_dict[type]["right_up_point"]["point"][1] -= dy
                roi_dict[type]["right_mid_point"]["point"][1] -= dy
                roi_dict[type]["down_mid_point"]["point"][1] -= dy / 2
                roi_dict[type]["up_mid_point"]["point"][1] -= dy / 2
                roi_dict[type]["mid_point"]["point"][1] -= dy / 2

                roi_dict["view_xy"]["left_up_point"]["point"][1] -= dy
                roi_dict["view_xy"]["right_up_point"]["point"][1] -= dy
                roi_dict["view_xy"]["up_mid_point"]["point"][1] -= dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] -= dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] -= dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] -= dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_up_is_clicked():
                end_point_y = roi_dict[type]["left_down_point"]["point"][1]
                end_point_z = roi_dict[type]["left_down_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    1]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    2]
                roi_dict[type]["right_up_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1],
                                                             self.start_pos[2]]
                roi_dict[type]["right_down_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], end_point_z]
                roi_dict[type]["left_up_point"]["point"] = [self.imageshape[0] + 1, end_point_y, self.start_pos[2]]
                roi_dict[type]["right_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["left_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["left_up_point"]["point"][1] += dy
                roi_dict["view_xy"]["right_up_point"]["point"][1] += dy
                roi_dict["view_xy"]["up_mid_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_mid_is_clicked():
                end_point_y = roi_dict[type]["mid_point"]["point"][1]
                end_point_z = roi_dict[type]["mid_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["mid_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], self.start_pos[2]]
                roi_dict[type]["right_down_point"]["point"][1] += dy
                roi_dict[type]["right_down_point"]["point"][2] += dz
                roi_dict[type]["right_mid_point"]["point"][1] += dy
                roi_dict[type]["right_mid_point"]["point"][2] += dz
                roi_dict[type]["down_mid_point"]["point"][1] += dy
                roi_dict[type]["down_mid_point"]["point"][2] += dz
                roi_dict[type]["up_mid_point"]["point"][1] += dy
                roi_dict[type]["up_mid_point"]["point"][2] += dz
                roi_dict[type]["left_up_point"]["point"][1] += dy
                roi_dict[type]["left_up_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][2] += dz
                roi_dict[type]["left_down_point"]["point"][1] += dy
                roi_dict[type]["left_down_point"]["point"][2] += dz
                roi_dict[type]["right_up_point"]["point"][1] += dy
                roi_dict[type]["right_up_point"]["point"][2] += dz

                roi_dict["view_xy"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["down_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["up_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_up_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xy"]["right_up_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
        elif type == "view_xz":
            if get_left_down_is_clicked():
                end_point_x = roi_dict[type]["right_up_point"]["point"][0]
                end_point_z = roi_dict[type]["right_up_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][0]
                dz = max(0, min(self.start_pos[2], self.imageshape[2])) - \
                     roi_dict[type]["left_down_point"]["point"][2]
                roi_dict[type]["left_down_point"]["point"] = [self.start_pos[0], 0, self.start_pos[2]]
                roi_dict[type]["left_up_point"]["point"] = [self.start_pos[0], 0, end_point_z]
                roi_dict[type]["right_down_point"]["point"] = [end_point_x, 0, self.start_pos[2]]

                roi_dict[type]["left_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["right_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2
                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_mid_is_clicked():
                end_point_x = roi_dict[type]["left_mid_point"]["point"][0]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - end_point_x
                roi_dict[type]["left_down_point"]["point"][0] += dx
                roi_dict[type]["left_up_point"]["point"][0] += dx
                roi_dict[type]["left_mid_point"]["point"][0] += dx
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_xy"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_up_is_clicked():
                end_point_x = roi_dict[type]["right_down_point"]["point"][0]
                end_point_z = roi_dict[type]["right_down_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    0]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    2]
                roi_dict[type]["left_up_point"]["point"] = [self.start_pos[0], 0,
                                                            self.start_pos[2]]
                roi_dict[type]["left_down_point"]["point"] = [self.start_pos[0], 0, end_point_z]
                roi_dict[type]["right_up_point"]["point"] = [end_point_x, 0, self.start_pos[2]]
                roi_dict[type]["left_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["right_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_up_mid_is_clicked():
                end_point_z = roi_dict[type]["up_mid_point"]["point"][2]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["up_mid_point"]["point"][2] += dz
                roi_dict[type]["left_up_point"]["point"][2] += dz
                roi_dict[type]["right_up_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_yz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_down_mid_is_clicked():
                end_point_z = roi_dict[type]["down_mid_point"]["point"][2]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["down_mid_point"]["point"][2] += dz
                roi_dict[type]["left_down_point"]["point"][2] += dz
                roi_dict[type]["right_down_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_yz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_down_is_clicked():
                end_point_x = roi_dict[type]["left_up_point"]["point"][0]
                end_point_z = roi_dict[type]["left_up_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][0]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][2]
                roi_dict[type]["right_down_point"]["point"] = [self.start_pos[0], 0, self.start_pos[2]]

                roi_dict[type]["right_up_point"]["point"] = [self.start_pos[0], 0, end_point_z]
                roi_dict[type]["left_down_point"]["point"] = [end_point_x, 0, self.start_pos[2]]
                roi_dict[type]["right_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["left_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["right_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["right_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_mid_is_clicked():
                end_point_x = roi_dict[type]["right_mid_point"]["point"][0]
                dx = end_point_x - max(0, min(self.start_pos[0], self.imageshape[0] - 1))
                roi_dict[type]["right_down_point"]["point"][0] -= dx
                roi_dict[type]["right_up_point"]["point"][0] -= dx
                roi_dict[type]["right_mid_point"]["point"][0] -= dx
                roi_dict[type]["down_mid_point"]["point"][0] -= dx / 2
                roi_dict[type]["up_mid_point"]["point"][0] -= dx / 2
                roi_dict[type]["mid_point"]["point"][0] -= dx / 2

                roi_dict["view_xy"]["right_down_point"]["point"][0] -= dx
                roi_dict["view_xy"]["right_up_point"]["point"][0] -= dx
                roi_dict["view_xy"]["right_mid_point"]["point"][0] -= dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] -= dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] -= dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] -= dx / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_up_is_clicked():
                end_point_x = roi_dict[type]["left_down_point"]["point"][0]
                end_point_z = roi_dict[type]["left_down_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    0]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    2]
                roi_dict[type]["right_up_point"]["point"] = [self.start_pos[0], 0, self.start_pos[2]]
                roi_dict[type]["right_down_point"]["point"] = [self.start_pos[0], 0, end_point_z]
                roi_dict[type]["left_up_point"]["point"] = [end_point_x, 0, self.start_pos[2]]
                roi_dict[type]["right_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["left_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["right_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["right_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_mid_is_clicked():
                end_point_x = roi_dict[type]["mid_point"]["point"][0]
                end_point_z = roi_dict[type]["mid_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - end_point_x
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["mid_point"]["point"] = [self.start_pos[0], 0, self.start_pos[2]]
                roi_dict[type]["right_down_point"]["point"][0] += dx
                roi_dict[type]["right_down_point"]["point"][2] += dz
                roi_dict[type]["right_mid_point"]["point"][0] += dx
                roi_dict[type]["right_mid_point"]["point"][2] += dz
                roi_dict[type]["down_mid_point"]["point"][0] += dx
                roi_dict[type]["down_mid_point"]["point"][2] += dz
                roi_dict[type]["up_mid_point"]["point"][0] += dx
                roi_dict[type]["up_mid_point"]["point"][2] += dz
                roi_dict[type]["left_up_point"]["point"][0] += dx
                roi_dict[type]["left_up_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][0] += dx
                roi_dict[type]["left_mid_point"]["point"][2] += dz
                roi_dict[type]["left_down_point"]["point"][0] += dx
                roi_dict[type]["left_down_point"]["point"][2] += dz
                roi_dict[type]["right_up_point"]["point"][0] += dx
                roi_dict[type]["right_up_point"]["point"][2] += dz

                roi_dict["view_xy"]["right_down_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xy"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_up_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_down_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xy"]["right_up_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

        self.view_xy.UpdateDisplayExtent()
        self.view_xy.Render()
        self.view_yz.UpdateDisplayExtent()
        self.view_yz.Render()
        self.view_xz.UpdateDisplayExtent()
        self.view_xz.Render()

    def draw_roi_rectangle(self, roi_dict, type):
        #  先清除actor
        name_list = ["left_down_point", "left_mid_point", "left_up_point", "right_down_point", "right_mid_point",
                     "right_up_point",
                     "down_mid_point", "up_mid_point", "mid_point", "left_down_line", "left_up_line", "right_down_line",
                     "right_up_line",
                     "down_left_line", "down_right_line", "up_left_line", "up_right_line"]
        try:
            for name in name_list:
                self.view_xy.GetRenderer().RemoveActor(roi_dict["view_xy"][name]["actor"])
                self.view_yz.GetRenderer().RemoveActor(roi_dict["view_yz"][name]["actor"])
                self.view_xz.GetRenderer().RemoveActor(roi_dict["view_xz"][name]["actor"])
        except:
            print("remove roi actor failed!!!")

        dict_type = roi_dict["view_xy"]
        left_down_x, left_down_y = dict_type["left_down_point"]["point"][0], dict_type["left_down_point"]["point"][
            1]
        left_up_x, left_up_y = dict_type["left_up_point"]["point"][0], dict_type["left_up_point"]["point"][1]
        left_mid_x, left_mid_y = dict_type["left_mid_point"]["point"][0], dict_type["left_mid_point"]["point"][1]
        right_down_x, right_down_y = dict_type["right_down_point"]["point"][0], \
            dict_type["right_down_point"]["point"][
                1]
        right_up_x, right_up_y = dict_type["right_up_point"]["point"][0], dict_type["right_up_point"]["point"][1]
        right_mid_x, right_mid_y = dict_type["right_mid_point"]["point"][0], dict_type["right_mid_point"]["point"][
            1]
        down_mid_x, down_mid_y = dict_type["down_mid_point"]["point"][0], dict_type["down_mid_point"]["point"][1]
        up_mid_x, up_mid_y = dict_type["up_mid_point"]["point"][0], dict_type["up_mid_point"]["point"][1]
        mid_x, mid_y = dict_type["mid_point"]["point"][0], dict_type["mid_point"]["point"][1]

        self.draw_point(left_down_x, left_down_y, self.imageshape[2] + 1, color=[1, 1, 1], type="view_xy")
        roi_dict["view_xy"]["left_down_point"]["actor"] = self.temp_actor

        self.draw_point(left_up_x, left_up_y, self.imageshape[2] + 1, color=[1, 1, 1], type="view_xy")
        roi_dict["view_xy"]["left_up_point"]["actor"] = self.temp_actor

        self.draw_point(right_down_x, right_down_y, self.imageshape[2] + 1, color=[1, 1, 1], type="view_xy")
        roi_dict["view_xy"]["right_down_point"]["actor"] = self.temp_actor

        self.draw_point(right_up_x, right_up_y, self.imageshape[2] + 1, color=[1, 1, 1], type="view_xy")
        roi_dict["view_xy"]["right_up_point"]["actor"] = self.temp_actor

        self.draw_point(left_mid_x, left_mid_y, self.imageshape[2] + 1, color=[1, 0, 0], type="view_xy")
        roi_dict["view_xy"]["left_mid_point"]["actor"] = self.temp_actor

        self.draw_point(right_mid_x, right_mid_y, self.imageshape[2] + 1, color=[1, 0, 0], type="view_xy")
        roi_dict["view_xy"]["right_mid_point"]["actor"] = self.temp_actor

        self.draw_point(up_mid_x, up_mid_y, self.imageshape[2] + 1, color=[0, 1, 0], type="view_xy")
        roi_dict["view_xy"]["up_mid_point"]["actor"] = self.temp_actor

        self.draw_point(down_mid_x, down_mid_y, self.imageshape[2] + 1, color=[0, 1, 0], type="view_xy")
        roi_dict["view_xy"]["down_mid_point"]["actor"] = self.temp_actor

        self.draw_point(mid_x, mid_y, self.imageshape[2] + 1, color=[1, 0.5, 0], type="view_xy")
        roi_dict["view_xy"]["mid_point"]["actor"] = self.temp_actor

        self.draw_line([left_down_x, left_down_y + self.radius_xy, self.imageshape[2] + 1],
                       [left_mid_x, left_mid_y - self.radius_xy, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["left_down_line"]["actor"] = self.temp_actor

        self.draw_line([left_mid_x, left_mid_y + self.radius_xy, self.imageshape[2] + 1],
                       [left_up_x, left_up_y - self.radius_xy, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["left_up_line"]["actor"] = self.temp_actor

        self.draw_line([left_down_x + self.radius_xy, left_down_y, self.imageshape[2] + 1],
                       [down_mid_x - self.radius_xy, down_mid_y, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["down_left_line"]["actor"] = self.temp_actor

        self.draw_line([down_mid_x + self.radius_xy, down_mid_y, self.imageshape[2] + 1],
                       [right_down_x - self.radius_xy, right_down_y, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["down_right_line"]["actor"] = self.temp_actor

        self.draw_line([right_down_x, right_down_y + self.radius_xy, self.imageshape[2] + 1],
                       [right_mid_x, right_mid_y - self.radius_xy, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["right_down_line"]["actor"] = self.temp_actor

        self.draw_line([right_mid_x, right_mid_y + self.radius_xy, self.imageshape[2] + 1],
                       [right_up_x, right_up_y - self.radius_xy, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["right_up_line"]["actor"] = self.temp_actor

        self.draw_line([left_up_x + self.radius_xy, left_up_y, self.imageshape[2] + 1],
                       [up_mid_x - self.radius_xy, up_mid_y, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["up_left_line"]["actor"] = self.temp_actor

        self.draw_line([up_mid_x + self.radius_xy, up_mid_y, self.imageshape[2] + 1],
                       [right_up_x - self.radius_xy, right_up_y, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["up_right_line"]["actor"] = self.temp_actor

        dict_type = roi_dict["view_xz"]
        left_down_x, left_down_z = dict_type["left_down_point"]["point"][0], dict_type["left_down_point"]["point"][
            2]
        left_up_x, left_up_z = dict_type["left_up_point"]["point"][0], dict_type["left_up_point"]["point"][2]
        left_mid_x, left_mid_z = dict_type["left_mid_point"]["point"][0], dict_type["left_mid_point"]["point"][2]
        right_down_x, right_down_z = dict_type["right_down_point"]["point"][0], \
            dict_type["right_down_point"]["point"][
                2]
        right_up_x, right_up_z = dict_type["right_up_point"]["point"][0], dict_type["right_up_point"]["point"][2]
        right_mid_x, right_mid_z = dict_type["right_mid_point"]["point"][0], dict_type["right_mid_point"]["point"][
            2]
        down_mid_x, down_mid_z = dict_type["down_mid_point"]["point"][0], dict_type["down_mid_point"]["point"][2]
        up_mid_x, up_mid_z = dict_type["up_mid_point"]["point"][0], dict_type["up_mid_point"]["point"][2]
        mid_x, mid_z = dict_type["mid_point"]["point"][0], dict_type["mid_point"]["point"][2]

        self.draw_point(left_down_x, 0, left_down_z, color=[1, 1, 1], type="view_xz")
        roi_dict["view_xz"]["left_down_point"]["actor"] = self.temp_actor

        self.draw_point(left_up_x, 0, left_up_z, color=[1, 1, 1], type="view_xz")
        roi_dict["view_xz"]["left_up_point"]["actor"] = self.temp_actor

        self.draw_point(right_down_x, 0, right_down_z, color=[1, 1, 1], type="view_xz")
        roi_dict["view_xz"]["right_down_point"]["actor"] = self.temp_actor

        self.draw_point(right_up_x, 0, right_up_z, color=[1, 1, 1], type="view_xz")
        roi_dict["view_xz"]["right_up_point"]["actor"] = self.temp_actor

        self.draw_point(left_mid_x, 0, left_mid_z, color=[1, 0, 0], type="view_xz")
        roi_dict["view_xz"]["left_mid_point"]["actor"] = self.temp_actor

        self.draw_point(right_mid_x, 0, right_mid_z, color=[1, 0, 0], type="view_xz")
        roi_dict["view_xz"]["right_mid_point"]["actor"] = self.temp_actor

        self.draw_point(up_mid_x, 0, up_mid_z, color=[0, 0, 1], type="view_xz")
        roi_dict["view_xz"]["up_mid_point"]["actor"] = self.temp_actor

        self.draw_point(down_mid_x, 0, down_mid_z, color=[0, 0, 1], type="view_xz")
        roi_dict["view_xz"]["down_mid_point"]["actor"] = self.temp_actor

        self.draw_point(mid_x, 0, mid_z, color=[1, 0.5, 0], type="view_xz")
        roi_dict["view_xz"]["mid_point"]["actor"] = self.temp_actor

        self.draw_line([left_down_x, 0, left_down_z + self.radius_xy], [left_mid_x, 0, left_mid_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["left_down_line"]["actor"] = self.temp_actor

        self.draw_line([left_mid_x, 0, left_mid_z + self.radius_xy, ], [left_up_x, 0, left_up_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["left_up_line"]["actor"] = self.temp_actor

        self.draw_line([left_down_x + self.radius_xy, 0, left_down_z], [down_mid_x - self.radius_xy, 0, down_mid_z],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["down_left_line"]["actor"] = self.temp_actor

        self.draw_line([down_mid_x + self.radius_xy, 0, down_mid_z],
                       [right_down_x - self.radius_xy, 0, right_down_z],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["down_right_line"]["actor"] = self.temp_actor

        self.draw_line([right_down_x, 0, right_down_z + self.radius_xy],
                       [right_mid_x, 0, right_mid_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["right_down_line"]["actor"] = self.temp_actor

        self.draw_line([right_mid_x, 0, right_mid_z + self.radius_xy], [right_up_x, 0, right_up_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["right_up_line"]["actor"] = self.temp_actor

        self.draw_line([left_up_x + self.radius_xy, 0, left_up_z], [up_mid_x - self.radius_xy, 0, up_mid_z],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["up_left_line"]["actor"] = self.temp_actor

        self.draw_line([up_mid_x + self.radius_xy, 0, up_mid_z], [right_up_x - self.radius_xy, 0, right_up_z],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["up_right_line"]["actor"] = self.temp_actor

        dict_type = roi_dict["view_yz"]
        left_down_y, left_down_z = dict_type["left_down_point"]["point"][1], dict_type["left_down_point"]["point"][2]
        left_up_y, left_up_z = dict_type["left_up_point"]["point"][1], dict_type["left_up_point"]["point"][2]
        left_mid_y, left_mid_z = dict_type["left_mid_point"]["point"][1], dict_type["left_mid_point"]["point"][2]
        right_down_y, right_down_z = dict_type["right_down_point"]["point"][1], dict_type["right_down_point"]["point"][
            2]
        right_up_y, right_up_z = dict_type["right_up_point"]["point"][1], dict_type["right_up_point"]["point"][2]
        right_mid_y, right_mid_z = dict_type["right_mid_point"]["point"][1], dict_type["right_mid_point"]["point"][2]
        down_mid_y, down_mid_z = dict_type["down_mid_point"]["point"][1], dict_type["down_mid_point"]["point"][2]
        up_mid_y, up_mid_z = dict_type["up_mid_point"]["point"][1], dict_type["up_mid_point"]["point"][2]
        mid_y, mid_z = dict_type["mid_point"]["point"][1], dict_type["mid_point"]["point"][2]

        self.draw_point(self.imageshape[0] + 1, left_down_y, left_down_z, color=[1, 1, 1], type="view_yz")
        roi_dict["view_yz"]["left_down_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, left_up_y, left_up_z, color=[1, 1, 1], type="view_yz")
        roi_dict["view_yz"]["left_up_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, right_down_y, right_down_z, color=[1, 1, 1], type="view_yz")
        roi_dict["view_yz"]["right_down_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, right_up_y, right_up_z, color=[1, 1, 1], type="view_yz")
        roi_dict["view_yz"]["right_up_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, left_mid_y, left_mid_z, color=[0, 1, 0], type="view_yz")
        roi_dict["view_yz"]["left_mid_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, right_mid_y, right_mid_z, color=[0, 1, 0], type="view_yz")
        roi_dict["view_yz"]["right_mid_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, up_mid_y, up_mid_z, color=[0, 0, 1], type="view_yz")
        roi_dict["view_yz"]["up_mid_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, down_mid_y, down_mid_z, color=[0, 0, 1], type="view_yz")
        roi_dict["view_yz"]["down_mid_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, mid_y, mid_z, color=[1, 0.5, 0], type="view_yz")
        roi_dict["view_yz"]["mid_point"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], left_down_y, left_down_z + self.radius_xy],
                       [self.imageshape[0], left_mid_y, left_mid_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["left_down_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], left_mid_y, left_mid_z + self.radius_xy, ],
                       [self.imageshape[0], left_up_y, left_up_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["left_up_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], left_down_y + self.radius_xy, left_down_z],
                       [self.imageshape[0], down_mid_y - self.radius_xy, down_mid_z],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["down_left_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], down_mid_y + self.radius_xy, down_mid_z],
                       [self.imageshape[0], right_down_y - self.radius_xy, right_down_z],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["down_right_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], right_down_y, right_down_z + self.radius_xy],
                       [self.imageshape[0], right_mid_y, right_mid_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["right_down_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], right_mid_y, right_mid_z + self.radius_xy],
                       [self.imageshape[0], right_up_y, right_up_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["right_up_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], left_up_y + self.radius_xy, left_up_z],
                       [self.imageshape[0], up_mid_y - self.radius_xy, up_mid_z],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["up_left_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], up_mid_y + self.radius_xy, up_mid_z],
                       [self.imageshape[0], right_up_y - self.radius_xy, right_up_z],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["up_right_line"]["actor"] = self.temp_actor

    def draw_line(self, point1, point2, color=None, type=None):
        if type == "view_xy":
            point1[0] = point1[0] * self.spacing_xy[0] + self.origin_xy[0]
            point1[1] = point1[1] * self.spacing_xy[1] + self.origin_xy[1]
            point2[0] = point2[0] * self.spacing_xy[0] + self.origin_xy[0]
            point2[1] = point2[1] * self.spacing_xy[1] + self.origin_xy[1]
        elif type == "view_yz":
            point1[0] = point1[0] * self.spacing_yz[0] + self.origin_yz[0]
            point1[1] = point1[1] * self.spacing_yz[1] + self.origin_yz[1]
            point1[2] = point1[2] * self.spacing_yz[2] + self.origin_yz[2]
            point2[0] = point2[0] * self.spacing_yz[0] + self.origin_yz[0]
            point2[1] = point2[1] * self.spacing_yz[1] + self.origin_yz[1]
            point2[2] = point2[2] * self.spacing_yz[2] + self.origin_yz[2]
        elif type == "view_xz":
            point1[0] = point1[0] * self.spacing_xz[0] + self.spacing_xz[0]
            point1[2] = point1[2] * self.spacing_xz[2] + self.spacing_xz[2]
            point2[0] = point2[0] * self.spacing_xz[0] + self.spacing_xz[0]
            point2[2] = point2[2] * self.spacing_xz[2] + self.spacing_xz[2]

        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(point1)
        lineSource.SetPoint2(point2)
        lineSource.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(3)
        actor.GetProperty().SetColor(color[0], color[1], color[2])
        self.temp_actor = actor
        if type == "view_xy":
            self.view_xy.GetRenderer().AddActor(actor)
        elif type == "view_yz":
            self.view_yz.GetRenderer().AddActor(actor)
        elif type == "view_xz":
            self.view_xz.GetRenderer().AddActor(actor)

    def draw_point(self, x, y, z, color=None, type=None):
        radius_xy = 3
        square = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        if type == "view_xy":
            point_x = x * self.spacing_xy[0] + self.origin_xy[0]
            point_y = y * self.spacing_xy[1] + self.origin_xy[1]
            point_z = z * self.spacing_xy[2] + self.origin_xy[2]
            points.InsertNextPoint(point_x - radius_xy, point_y + radius_xy, point_z)
            points.InsertNextPoint(point_x + radius_xy, point_y + radius_xy, point_z)
            points.InsertNextPoint(point_x + radius_xy, point_y - radius_xy, point_z)
            points.InsertNextPoint(point_x - radius_xy, point_y - radius_xy, point_z)
        elif type == "view_yz":
            point_x = x * self.spacing_yz[0] + self.origin_yz[0]
            point_y = y * self.spacing_yz[1] + self.origin_yz[1]
            point_z = z * self.spacing_yz[2] + self.origin_yz[2]

            points.InsertNextPoint(point_x, point_y - radius_xy, point_z + radius_xy)
            points.InsertNextPoint(point_x, point_y + radius_xy, point_z + radius_xy)
            points.InsertNextPoint(point_x, point_y + radius_xy, point_z - radius_xy)
            points.InsertNextPoint(point_x, point_y - radius_xy, point_z - radius_xy)
        elif type == "view_xz":
            point_x = x * self.spacing_xz[0] + self.origin_xz[0]
            point_y = y * self.spacing_xz[1] + self.origin_xz[1]
            point_z = z * self.spacing_xz[2] + self.origin_xz[2]

            points.InsertNextPoint(point_x - radius_xy, point_y, point_z + radius_xy)
            points.InsertNextPoint(point_x + radius_xy, point_y, point_z + radius_xy)
            points.InsertNextPoint(point_x + radius_xy, point_y, point_z - radius_xy)
            points.InsertNextPoint(point_x - radius_xy, point_y, point_z - radius_xy)

        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(4)
        polygon.GetPointIds().SetId(0, 0)
        polygon.GetPointIds().SetId(1, 1)
        polygon.GetPointIds().SetId(2, 2)
        polygon.GetPointIds().SetId(3, 3)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(polygon)

        square.SetPoints(points)
        square.SetPolys(cells)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(square)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color[0], color[1], color[2])
        self.temp_actor = actor
        if type == "view_xy":
            self.view_xy.GetRenderer().AddActor(actor)
        elif type == "view_yz":
            self.view_yz.GetRenderer().AddActor(actor)
        elif type == "view_xz":
            self.view_xz.GetRenderer().AddActor(actor)


class LeftButtonPressEvent_GetROI():
    def __init__(self, picker, viewer_xy, viewer_yz, viewer_xz, type):
        self.picker = picker  # 坐标拾取
        self.view_xy = viewer_xy
        self.view_yz = viewer_yz
        self.view_xz = viewer_xz
        self.actor_xy = self.view_xy.GetImageActor()
        self.actor_yz = self.view_yz.GetImageActor()
        self.actor_xz = self.view_xz.GetImageActor()
        self.iren_xy = self.view_xy.GetRenderWindow().GetInteractor()
        self.iren_yz = self.view_yz.GetRenderWindow().GetInteractor()
        self.iren_xz = self.view_xz.GetRenderWindow().GetInteractor()
        self.render_xy = self.view_xy.GetRenderer()
        self.render_yz = self.view_yz.GetRenderer()
        self.render_xz = self.view_xz.GetRenderer()
        self.origin_xy = self.view_xy.GetInput().GetOrigin()
        self.origin_yz = self.view_yz.GetInput().GetOrigin()
        self.origin_xz = self.view_xz.GetInput().GetOrigin()
        self.spacing_xy = self.view_xy.GetInput().GetSpacing()
        self.spacing_yz = self.view_yz.GetInput().GetSpacing()
        self.spacing_xz = self.view_xz.GetInput().GetSpacing()
        self.ren_xy = self.view_xy.GetRenderer()
        self.ren_yz = self.view_yz.GetRenderer()
        self.ren_xz = self.view_xz.GetRenderer()
        self.origin = self.view_xy.GetInput().GetOrigin()
        self.spacing = self.view_xy.GetInput().GetSpacing()
        self.imageshape = self.view_xy.GetInput().GetDimensions()
        self.type = type

    def __call__(self, caller, ev):
        roi_dict = getControlROIPoint()
        if self.type == "view_xy":
            self.picker.AddPickList(self.actor_xy)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_xy.GetEventPosition()[0], self.iren_xy.GetEventPosition()[1], 0, self.render_xy)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_xy[i])) / self.spacing_xy[i] for i in range(3)]
        elif self.type == "view_yz":
            self.picker.AddPickList(self.actor_yz)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_yz.GetEventPosition()[0], self.iren_yz.GetEventPosition()[1], 0, self.render_yz)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_yz[i])) / self.spacing_yz[i] for i in range(3)]
        elif self.type == "view_xz":
            self.picker.AddPickList(self.actor_xz)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_xz.GetEventPosition()[0], self.iren_xz.GetEventPosition()[1], 0, self.render_xz)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_xz[i])) / self.spacing_xz[i] for i in range(3)]
        print(self.type)
        self.point_is_clicked(roi_dict, self.type)

    def is_point_inside_circle(self, circle_center, point, radius=3):
        if self.type == "view_xy":
            cx, cy = circle_center
            cx = cx * self.spacing[0] + self.origin[0]
            cy = cy * self.spacing[1] + self.origin[1]
            c1 = cx
            c2 = cy
        elif self.type == "view_yz":
            cy, cz = circle_center
            cy = cy * self.spacing[1] + self.origin[1]
            cz = cz * self.spacing[2] + self.origin[2]
            c1 = cy
            c2 = cz
        else:
            cx, cz = circle_center
            cx = cx * self.spacing[0] + self.origin[0]
            cz = cz * self.spacing[2] + self.origin[2]
            c1 = cx
            c2 = cz
        px, py = point
        if (-radius <= px - c1 <= radius) and (-radius <= py - c2 <= radius):
            return True
        return False

    def point_is_clicked(self, roi_dict, type):
        if type == "view_xy":
            self.is_click(0, 1, roi_dict, type)
        elif type == "view_yz":
            self.is_click(1, 2, roi_dict, type)
        elif type == "view_xz":
            self.is_click(0, 2, roi_dict, type)

        self.view_xy.UpdateDisplayExtent()
        self.view_xy.Render()
        self.view_yz.UpdateDisplayExtent()
        self.view_yz.Render()
        self.view_xz.UpdateDisplayExtent()
        self.view_xz.Render()

    def is_click(self, index1, index2, roi_dict, type):
        if self.is_point_inside_circle(
                (
                        roi_dict[type]["left_down_point"]["point"][index1],
                        roi_dict[type]["left_down_point"]["point"][index2]),
                (self.start[index1], self.start[index2])):
            roi_dict[type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(True)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["left_mid_point"]["point"][index1],
                                          roi_dict[type]["left_mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_xz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xy"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_xy"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(True)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["left_up_point"]["point"][index1],
                                          roi_dict[type]["left_up_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(True)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)


        elif self.is_point_inside_circle((roi_dict[type]["up_mid_point"]["point"][index1],
                                          roi_dict[type]["up_mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_yz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xz"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_yz"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(True)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["down_mid_point"]["point"][index1],
                                          roi_dict[type]["down_mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_yz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xz"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_yz"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(True)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["right_down_point"]["point"][index1],
                                          roi_dict[type]["right_down_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(True)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["right_mid_point"]["point"][index1],
                                          roi_dict[type]["right_mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_xz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xy"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_xy"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(True)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["right_up_point"]["point"][index1],
                                          roi_dict[type]["right_up_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(True)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["mid_point"]["point"][index1],
                                          roi_dict[type]["mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(True)

        else:
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)


class LeftButtonReleaseEvent_GetROI():
    def __init__(self, picker, viewer_xy,viewer_yz,viewer_xz, type):
        self.view_xy = viewer_xy
        self.view_yz = viewer_yz
        self.view_xz = viewer_xz
        self.type = type

    def __call__(self, caller, ev):
        roi_dict = getControlROIPoint()
        if self.type == "view_xy":
            roi_dict[self.type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict[self.type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict[self.type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict[self.type]["down_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict[self.type]["up_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)

            roi_dict["view_xz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict["view_xz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict["view_yz"]["left_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict["view_yz"]["right_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)

        elif self.type == "view_yz":
            roi_dict[self.type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict[self.type]["left_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict[self.type]["right_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict[self.type]["down_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict[self.type]["up_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)

            roi_dict["view_xy"]["down_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict["view_xy"]["up_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict["view_xz"]["down_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict["view_xz"]["up_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
        else:
            roi_dict[self.type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict[self.type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict[self.type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict[self.type]["down_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict[self.type]["up_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)

            roi_dict["view_xy"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict["view_xy"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict["view_yz"]["down_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict["view_yz"]["up_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
        self.view_xy.UpdateDisplayExtent()
        self.view_xy.Render()
        self.view_yz.UpdateDisplayExtent()
        self.view_yz.Render()
        self.view_xz.UpdateDisplayExtent()
        self.view_xz.Render()
        set_left_down_is_clicked(False)
        set_left_mid_is_clicked(False)
        set_left_up_is_clicked(False)
        set_down_mid_is_clicked(False)
        set_up_mid_is_clicked(False)
        set_right_down_is_clicked(False)
        set_right_mid_is_clicked(False)
        set_right_up_is_clicked(False)
        set_mid_is_clicked(False)
