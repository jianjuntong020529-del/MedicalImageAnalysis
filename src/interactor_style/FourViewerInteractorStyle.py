# -*- coding: utf-8 -*-
# @Time    : 2024/10/10 13:19
#
# @Author  : Jianjun Tong
from src.utils.globalVariables import *


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
