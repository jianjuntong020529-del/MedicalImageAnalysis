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


class MouseWheelForwardSeg():
    """
    分割叠加层专用的鼠标滚轮前滚事件处理器
    同时更新 DICOM 查看器和分割叠加层查看器
    """
    def __init__(self, viewer_dicom, viewer_seg, labeltext, verticalslider, id):
        print("分割叠加层鼠标前滚初始化")
        self.view_dicom = viewer_dicom  # DICOM 查看器
        self.view_seg = viewer_seg  # 分割叠加层查看器
        self.label = labeltext
        self.verticalslider = verticalslider
        self.id = id  # 判断是哪个窗口 (XY, YZ, XZ)

    def __call__(self, caller, ev):
        print(f"分割叠加层滑轮前滚 - {self.id}")
        
        # 获取当前切片和最大切片
        current_slice = self.view_dicom.GetSlice()
        max_slice = self.view_dicom.GetSliceMax()
        
        # 计算新的切片索引
        new_slice = min(current_slice + 1, max_slice)
        
        # 更新全局切片变量
        if self.id == "XY":
            setSliceXY(new_slice)
        elif self.id == "YZ":
            setSliceYZ(new_slice)
        else:
            setSliceXZ(new_slice)
        
        # 更新 DICOM 查看器
        self.view_dicom.SetSlice(new_slice)
        self.view_dicom.UpdateDisplayExtent()
        
        # 同步更新分割叠加层查看器
        if self.view_seg is not None:
            self.view_seg.SetSlice(new_slice)
            self.view_seg.UpdateDisplayExtent()
        
        # 强制刷新渲染窗口
        self.view_dicom.GetRenderWindow().Render()
        
        # 更新 UI
        self.verticalslider.setValue(new_slice)
        self.label.setText("Slice %d/%d" % (new_slice, max_slice))


class MouseWheelBackWardSeg():
    """
    分割叠加层专用的鼠标滚轮后滚事件处理器
    同时更新 DICOM 查看器和分割叠加层查看器
    """
    def __init__(self, viewer_dicom, viewer_seg, labeltext, verticalslider, id):
        print("分割叠加层鼠标后滚初始化")
        self.view_dicom = viewer_dicom  # DICOM 查看器
        self.view_seg = viewer_seg  # 分割叠加层查看器
        self.label = labeltext
        self.verticalslider = verticalslider
        self.id = id  # 判断是哪个窗口 (XY, YZ, XZ)

    def __call__(self, caller, ev):
        print(f"分割叠加层滑轮后滚 - {self.id}")
        
        # 获取当前切片
        current_slice = self.view_dicom.GetSlice()
        max_slice = self.view_dicom.GetSliceMax()
        
        # 计算新的切片索引
        new_slice = max(current_slice - 1, 0)
        
        # 更新全局切片变量
        if self.id == "XY":
            setSliceXY(new_slice)
        elif self.id == "YZ":
            setSliceYZ(new_slice)
        else:
            setSliceXZ(new_slice)
        
        # 更新 DICOM 查看器
        self.view_dicom.SetSlice(new_slice)
        self.view_dicom.UpdateDisplayExtent()
        
        # 同步更新分割叠加层查看器
        if self.view_seg is not None:
            self.view_seg.SetSlice(new_slice)
            self.view_seg.UpdateDisplayExtent()
        
        # 强制刷新渲染窗口
        self.view_dicom.GetRenderWindow().Render()
        
        # 更新 UI
        self.verticalslider.setValue(new_slice)
        self.label.setText("Slice %d/%d" % (new_slice, max_slice))
