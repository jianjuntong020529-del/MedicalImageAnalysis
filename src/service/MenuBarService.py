# -*- coding: utf-8 -*-
# @Time    : 2024/10/8 17:05
#
# @Author  : Jianjun Tong
import os

import vtk
from PyQt5 import QtWidgets
from medpy.io import load

from src.controller.ToolBarController import ToolBarController
from src.interactor_style.FourViewerInteractorStyle import MouseWheelForward, MouseWheelBackWard
from src.model.AnnotationEnableModel import AnnotationEnable
from src.model.DataAndModelType import DataAndModelType
from src.model.VolumeRenderModel import VolumeRender
from src.model.BaseModel import BaseModel
from src.model.CameraPositionModel import CameraPosition
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.ToolBarEnableModel import ToolBarEnable
from src.service.AnnotationService import AnnotationService
from src.service.ConstantService import ContrastService
from src.service.ToolBarService import ToolBarService
from src.utils.globalVariables import *


class MenuBarService:
    def __init__(self, baseModelClass: BaseModel, viewer_model: OrthoViewerModel):

        self.baseModelClass = baseModelClass
        self.viewModel = viewer_model

        self.reader = self.baseModelClass.imageReader


        self.contrastService = ContrastService(self.baseModelClass, self.viewModel)
        self.toolBarService = ToolBarService(self.baseModelClass, self.viewModel)
        self.annotationService = AnnotationService(self.baseModelClass, self.viewModel)


        # XY 窗口
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.vtkWidget_XY = self.viewModel.AxialOrthoViewer.widget
        self.label_XY = self.viewModel.AxialOrthoViewer.slider_label
        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider
        self.id_XY = self.viewModel.AxialOrthoViewer.type

        # YZ 窗口
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.vtkWidget_YZ = self.viewModel.SagittalOrthoViewer.widget
        self.label_YZ = self.viewModel.SagittalOrthoViewer.slider_label
        self.verticalSlider_YZ = self.viewModel.SagittalOrthoViewer.slider
        self.id_YZ = self.viewModel.SagittalOrthoViewer.type

        # XZ 窗口
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        self.vtkWidget_XZ = self.viewModel.CoronalOrthoViewer.widget
        self.label_XZ = self.viewModel.CoronalOrthoViewer.slider_label
        self.verticalSlider_XZ = self.viewModel.CoronalOrthoViewer.slider
        self.id_XZ = self.viewModel.CoronalOrthoViewer.type

        self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
        self.iren_Volume = self.viewModel.VolumeOrthorViewer.renderWindowInteractor



    def on_actionAdd_DICOM_Data(self):
        setFileIsEmpty(False)
        setIsPutImplant(False)
        setIsGenerateImplant(False)
        setAnchorPointIsComplete(False)
        setIsAdjust(False)

        self.spacing = self.baseModelClass.spacing
        if self.spacing[2] == 0:
            newspacing = (self.spacing[0], self.spacing[1], 1)
            self.baseModelClass.imageReader.GetOutput().SetSpacing(newspacing)
            self.baseModelClass.imageReader.Update()
            self.baseModelClass.update_data_information()

        self.clear_mousewheel_forward_backward_event([self.viewer_XY,self.viewer_YZ,self.viewer_XZ])


        # 更新横断面
        focalPoint_XY, position_XY = self.update_viewer(self.viewModel.AxialOrthoViewer, self.vtkWidget_XY, self.label_XY,
                                                                  self.verticalSlider_XY, self.id_XY)
        # 更新矢状面
        focalPoint_YZ, position_YZ = self.update_viewer(self.viewModel.SagittalOrthoViewer, self.vtkWidget_YZ, self.label_YZ,
                                                                  self.verticalSlider_YZ, self.id_YZ)
        # 更新冠状面
        focalPoint_XZ, position_XZ = self.update_viewer(self.viewModel.CoronalOrthoViewer, self.vtkWidget_XZ, self.label_XZ,
                                                                  self.verticalSlider_XZ, self.id_XZ)

        CameraPosition.position_XY = position_XY
        CameraPosition.position_YZ = position_YZ
        CameraPosition.position_XZ = position_XZ
        CameraPosition.focalPoint_XY = focalPoint_XY
        CameraPosition.focalPoint_YZ = focalPoint_YZ
        CameraPosition.focalPoint_XZ = focalPoint_XZ


        # 调整图像对比度
        self.contrastService.adjust_window_width_and_level()

        # 更新体绘制窗口
        self.update_volume_viewer()

    def on_actionAdd_IM0_Data(self, slice_thickness):
        setFileIsEmpty(False)
        setIsPutImplant(False)
        setIsGenerateImplant(False)
        setAnchorPointIsComplete(False)
        setIsAdjust(False)

        self.spacing = self.baseModelClass.spacing
        if self.spacing[2] == 0:
            newspacing = (self.spacing[0], self.spacing[1], slice_thickness)
            self.baseModelClass.imageReader.GetOutput().SetSpacing(newspacing)
            self.baseModelClass.imageReader.Update()
            self.baseModelClass.update_data_information()

        self.clear_mousewheel_forward_backward_event([self.viewer_XY,self.viewer_YZ,self.viewer_XZ])

        # 更新横断面
        focalPoint_XY, position_XY = self.update_viewer(self.viewModel.AxialOrthoViewer, self.vtkWidget_XY, self.label_XY,
                                                                  self.verticalSlider_XY, self.id_XY)
        # 更新矢状面
        focalPoint_YZ, position_YZ = self.update_viewer(self.viewModel.SagittalOrthoViewer, self.vtkWidget_YZ, self.label_YZ,
                                                                  self.verticalSlider_YZ, self.id_YZ)
        # 更新冠状面
        focalPoint_XZ, position_XZ = self.update_viewer(self.viewModel.CoronalOrthoViewer, self.vtkWidget_XZ, self.label_XZ,
                                                                  self.verticalSlider_XZ, self.id_XZ)

        CameraPosition.position_XY = position_XY
        CameraPosition.position_YZ = position_YZ
        CameraPosition.position_XZ = position_XZ
        CameraPosition.focalPoint_XY = focalPoint_XY
        CameraPosition.focalPoint_YZ = focalPoint_YZ
        CameraPosition.focalPoint_XZ = focalPoint_XZ

        # 调整图像对比度
        self.contrastService.adjust_window_width_and_level()

        # ------------更新体绘制窗口数据-----------------------------------------
        try:
            self.update_volume_viewer()
        except:
            print('Creat Volume error!')

    def update_viewer(self, ortho_viewer, vtkWidget, label, verticalSlider, id):
        bounds = self.baseModelClass.bounds
        print(bounds)
        self.center0 = (bounds[1] + bounds[0]) / 2.0
        self.center1 = (bounds[3] + bounds[2]) / 2.0
        self.center2 = (bounds[5] + bounds[4]) / 2.0

        viewer = vtk.vtkResliceImageViewer()
        viewer.SetInputData(self.reader.GetOutput())
        viewer.SetupInteractor(vtkWidget)
        viewer.SetRenderWindow(vtkWidget.GetRenderWindow())
        if id == "XY":
            viewer.SetSliceOrientationToXY()
        elif id == "YZ":
            viewer.SetSliceOrientationToYZ()
            if DataAndModelType.DATA_TYPE == "DICOM":
                transform_YZ = vtk.vtkTransform()
                transform_YZ.Translate(self.center0, self.center1, self.center2)
                transform_YZ.RotateX(180)
                transform_YZ.RotateZ(180)
                transform_YZ.Translate(-self.center0, -self.center1, -self.center2)
                viewer.GetImageActor().SetUserTransform(transform_YZ)
        elif id == "XZ":
            viewer.SetSliceOrientationToXZ()
            if DataAndModelType.DATA_TYPE == "DICOM":
                transform_XZ = vtk.vtkTransform()
                transform_XZ.Translate(self.center0, self.center1, self.center2)
                transform_XZ.RotateY(180)
                transform_XZ.RotateZ(180)
                transform_XZ.Translate(-self.center0, -self.center1, -self.center2)
                viewer.GetImageActor().SetUserTransform(transform_XZ)
        viewer.SliceScrollOnMouseWheelOff()
        viewer.UpdateDisplayExtent()
        viewer.Render()

        camera = viewer.GetRenderer().GetActiveCamera()
        camera.ParallelProjectionOn()
        camera.SetParallelScale(80)
        focalPoint = camera.GetFocalPoint()
        position = camera.GetPosition()

        wheelforward = MouseWheelForward(viewer, label, verticalSlider, id)
        wheelbackward = MouseWheelBackWard(viewer, label, verticalSlider, id)
        viewer_InteractorStyle = viewer.GetInteractorStyle()
        viewer_InteractorStyle.AddObserver("MouseWheelForwardEvent", wheelforward)
        viewer_InteractorStyle.AddObserver("MouseWheelBackwardEvent", wheelbackward)

        value = viewer.GetSlice()
        maxSlice = viewer.GetSliceMax()
        verticalSlider.setMaximum(maxSlice)
        verticalSlider.setMinimum(0)
        verticalSlider.setSingleStep(1)
        verticalSlider.setValue(value)
        label.setText("Slice %d/%d" % (verticalSlider.value(), maxSlice))
        viewer.Render()

        ortho_viewer.viewer = viewer

        return focalPoint, position

    def clear_mousewheel_forward_backward_event(self, viewer_list):
        try:
            for viewer in viewer_list:
                viewer_InteractorStyle = viewer.GetInteractorStyle()
                viewer_InteractorStyle.RemoveObservers("MouseWheelForwardEvent")
                viewer_InteractorStyle.RemoveObservers("MouseWheelBackwardEvent")
        except:
            print("event not exist")

    def update_volume_viewer(self):
        # 创建体绘制映射器
        volumeMapper = vtk.vtkGPUVolumeRayCastMapper()  # 提高渲染性能
        volumeMapper.SetInputConnection(self.baseModelClass.imageReader.GetOutputPort())

        # 设置体绘制颜色
        color_transfer_function = vtk.vtkColorTransferFunction()
        color_transfer_function.AddRGBPoint(0, 0.0, 0.0, 0.0)
        color_transfer_function.AddRGBPoint(1000, 1.0, 0.5, 0.3)
        color_transfer_function.AddRGBPoint(1500, 1.0, 0.5, 0.3)
        color_transfer_function.AddRGBPoint(2000, 1.0, 0.7, 0.4)
        color_transfer_function.AddRGBPoint(4000, 1.0, 1.0, 1.0)  # 4095

        # 设置体绘制不透明度
        opacity_transfer_function = vtk.vtkPiecewiseFunction()
        opacity_transfer_function.AddPoint(0, 0.0)
        opacity_transfer_function.AddPoint(900, 0.0)
        opacity_transfer_function.AddPoint(1500, 0.3)
        opacity_transfer_function.AddPoint(2000, 0.6)
        opacity_transfer_function.AddPoint(4000, 0.9)  # 4095

        # 添加体绘制光照效果
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(color_transfer_function)
        volumeProperty.SetScalarOpacity(opacity_transfer_function)
        volumeProperty.ShadeOn()
        volumeProperty.SetAmbient(0.5)
        volumeProperty.SetDiffuse(0.7)
        volumeProperty.SetSpecular(0.5)

        # 创建体绘制对象
        volume_cbct = vtk.vtkVolume()
        volume_cbct.SetMapper(volumeMapper)
        volume_cbct.SetProperty(volumeProperty)
        # 添加体绘制到渲染器
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(0.5, 0.5, 0.5)
        renderer.AddVolume(volume_cbct)
        renderer.ResetCamera()
        self.vtkWidget_Volume.GetRenderWindow().AddRenderer(renderer)

        VolumeRender.volume_cbct = volume_cbct

        style = vtk.vtkInteractorStyleTrackballCamera()  # 交互器样式的一种，该样式下，用户是通过控制相机对物体作旋转、放大、缩小等操作
        style.SetDefaultRenderer(renderer)
        style.EnabledOn()
        self.iren_Volume.SetInteractorStyle(style)
        # ==================添加一个三维坐标指示=======================================
        axesActor = vtk.vtkAxesActor()
        axes = vtk.vtkOrientationMarkerWidget()
        axes.SetOrientationMarker(axesActor)
        axes.SetInteractor(self.iren_Volume)
        axes.EnabledOn()
        axes.SetEnabled(1)
        axes.InteractiveOff()
        renderer.ResetCamera()
        self.vtkWidget_Volume.Render()

        self.viewModel.VolumeOrthorViewer.renderer = renderer

        self.iren_Volume.Initialize()

    def valuechange1(self):
        viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        if not ToolBarEnable.crosshair_enable:
            value_XY = self.verticalSlider_XY.value()
            if AnnotationEnable.pointAction.isChecked():
                try:
                    for i in getPointsActor():
                        viewer_XY.GetRenderer().RemoveActor(i)
                    viewer_XY.Render()
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                viewer_XY.SetSlice(value_XY)
                if getPointsUndoStack() != []:
                    for point in getPointsUndoStack():
                        print(point)
                        if point[2] == value_XY:
                            self.annotationService.point_paints(point)
            if AnnotationEnable.labelBoxAction.isChecked():
                print("bound_box")
                if getSelectSingleBoxLabel():
                    try:
                        for i in getSingleBoundingBoxActor():
                            viewer_XY.GetRenderer().RemoveActor(i)
                        viewer_XY.Render()
                    except:
                        print('Close viewer_XY actor_paint Failed!!!')
                    value = value_XY
                    viewer_XY.SetSlice(value)
                    if getSingleUndoStack():
                        for data in getSingleUndoStack():
                            if data[4] == value_XY:
                                print("single redo")
                                actor_list = self.annotationService.drwa_single_bounding_box(data)
                                setSingleBoundingBoxActor(actor_list)
                    viewer_XY.UpdateDisplayExtent()
                    viewer_XY.Render()
                else:
                    try:
                        for i in getSingleBoundingBoxActor():
                            viewer_XY.GetRenderer().RemoveActor(i)
                    except:
                        print('Close viewer_XY actor_paint Failed!!!')
                    try:
                        for i in getLastBoundingBoxActor():
                            viewer_XY.GetRenderer().RemoveActor(i)
                    except:
                        print('Close viewer_XY actor_paint Failed!!!')
                    try:
                        for actor in getMultipleBoundingBoxActor():
                            for i in actor:
                                viewer_XY.GetRenderer().RemoveActor(i)
                        clearMultipleBoundingBoxActor()
                        viewer_XY.Render()
                    except:
                        print('Close viewer_XY actor_paint Failed!!!')
                    value = value_XY
                    viewer_XY.SetSlice(value)
                    if getMultipleUndoStack():
                        for data in getMultipleUndoStack():
                            if data[4] == value_XY:
                                print("multiple redo")
                                actor_list = self.annotationService.drwa_single_bounding_box(data)
                                setMultipleBoundingBoxActor(actor_list)
                    viewer_XY.UpdateDisplayExtent()
                    viewer_XY.Render()
            else:
                viewer_XY.SetSlice(value_XY)
            viewer_XY.UpdateDisplayExtent()
            viewer_XY.Render()
            self.label_XY.setText("Slice %d/%d" % (viewer_XY.GetSlice(), viewer_XY.GetSliceMax()))
        else:
            center = list(viewer_XY.GetResliceCursor().GetCenter())
            value_XY = self.verticalSlider_XY.value()
            value_YZ = self.verticalSlider_YZ.value()
            value_XZ = self.verticalSlider_XZ.value()
            origin = self.baseModelClass.origin
            spacing = self.baseModelClass.spacing
            center[2] = value_XY * spacing[2] - origin[2]
            viewer_XY.GetResliceCursor().SetCenter(center)
            viewer_XY.GetResliceCursor().Update()
            viewer_XY.GetResliceCursorWidget().Render()
            viewer_YZ.GetResliceCursorWidget().Render()
            viewer_XZ.GetResliceCursorWidget().Render()
            self.label_XY.setText("Slice %d/%d" % (value_XY, viewer_XY.GetSliceMax()))
            self.label_YZ.setText("Slice %d/%d" % (value_YZ, viewer_YZ.GetSliceMax()))
            self.label_XZ.setText("Slice %d/%d" % (value_XZ, viewer_XZ.GetSliceMax()))
            self.vtkWidget_XY.GetRenderWindow().Render()
            self.vtkWidget_YZ.GetRenderWindow().Render()
            self.vtkWidget_XZ.GetRenderWindow().Render()

    def valuechange2(self):
        viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        if not ToolBarEnable.crosshair_enable:
            print("ResliceImageView Change YZ")
            value = self.verticalSlider_YZ.value()
            viewer_YZ.SetSlice(value)
            viewer_YZ.UpdateDisplayExtent()
            viewer_YZ.Render()
            self.label_YZ.setText("Slice %d/%d" % (viewer_YZ.GetSlice(), viewer_YZ.GetSliceMax()))
        else:
            center = list(viewer_XY.GetResliceCursor().GetCenter())
            value_XY = self.verticalSlider_XY.value()
            value_YZ = self.verticalSlider_YZ.value()
            value_XZ = self.verticalSlider_XZ.value()
            origin = self.baseModelClass.origin
            spacing = self.baseModelClass.spacing
            center[0] = value_YZ * spacing[0] - origin[0]
            viewer_XY.GetResliceCursor().SetCenter(center)
            viewer_XY.GetResliceCursor().Update()
            viewer_XY.GetResliceCursorWidget().Render()
            viewer_YZ.GetResliceCursorWidget().Render()
            viewer_XZ.GetResliceCursorWidget().Render()
            self.label_XY.setText("Slice %d/%d" % (value_XY, viewer_XY.GetSliceMax()))
            self.label_YZ.setText("Slice %d/%d" % (value_YZ, viewer_YZ.GetSliceMax()))
            self.label_XZ.setText("Slice %d/%d" % (value_XZ, viewer_XZ.GetSliceMax()))
            self.vtkWidget_XY.GetRenderWindow().Render()
            self.vtkWidget_YZ.GetRenderWindow().Render()
            self.vtkWidget_XZ.GetRenderWindow().Render()

    def valuechange3(self):
        viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        if not ToolBarEnable.crosshair_enable:
            print("ResliceImageView Change XZ")
            value = self.verticalSlider_XZ.value()
            viewer_XZ.SetSlice(value)
            viewer_XZ.UpdateDisplayExtent()
            viewer_XZ.Render()
            self.label_XZ.setText("Slice %d/%d" % (viewer_XZ.GetSlice(), viewer_XZ.GetSliceMax()))
        else:
            center = list(viewer_XY.GetResliceCursor().GetCenter())
            value_XY = self.verticalSlider_XY.value()
            value_YZ = self.verticalSlider_YZ.value()
            value_XZ = self.verticalSlider_XZ.value()
            origin = self.baseModelClass.origin
            spacing = self.baseModelClass.spacing
            center[1] = value_XZ * spacing[1] - origin[1]
            viewer_XY.GetResliceCursor().SetCenter(center)
            viewer_XY.GetResliceCursor().Update()
            viewer_XY.GetResliceCursorWidget().Render()
            viewer_YZ.GetResliceCursorWidget().Render()
            viewer_XZ.GetResliceCursorWidget().Render()
            self.label_XY.setText("Slice %d/%d" % (value_XY, viewer_XY.GetSliceMax()))
            self.label_YZ.setText("Slice %d/%d" % (value_YZ, viewer_YZ.GetSliceMax()))
            self.label_XZ.setText("Slice %d/%d" % (value_XZ, viewer_XZ.GetSliceMax()))
            self.vtkWidget_XY.GetRenderWindow().Render()
            self.vtkWidget_YZ.GetRenderWindow().Render()
            self.vtkWidget_XZ.GetRenderWindow().Render()

