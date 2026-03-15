from src.utils.globalVariables import *


class MouseWheelForward():
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

        if not self.annotation_enable:
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

        self.view.UpdateDisplayExtent()
        self.view.Render()


class MouseWheelBackWard():
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

        if not self.annotation_enable:
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

        self.view.UpdateDisplayExtent()
        self.view.Render()
