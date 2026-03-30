# -*- coding: utf-8 -*-
# @Time    : 2024/10/16 14:02
#
# @Author  : Jianjun Tong
from medpy.io import load
from src.interactor_style.CrosshairInteractorStyle import CommandSelect
from src.interactor_style.DraggingImageInteractorStyle import LeftButtonPressEvent_Dragging, \
    LeftButtonReleaseEvent_Dragging, MouseMoveEvent_Dragging
from src.interactor_style.GetROIInteractorStyle import MouseMoveEvent_GetROI, LeftButtonPressEvent_GetROI, \
    LeftButtonReleaseEvent_GetROI

from src.interactor_style.ToolBarInteractorStyle import *
from src.model.AnnotationEnableModel import AnnotationEnable
from src.model.CameraPositionModel import CameraPosition
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.BaseModel import BaseModel
from src.model.ToolBarEnableModel import ToolBarEnable
from src.model.ToolBarWidgetModel import ToolBarWidget
from src.service.AnnotationService import AnnotationService
from src.utils.globalVariables import *
from src.interactor_style.FourViewerInteractorStyle import MouseWheelForward, MouseWheelBackWard
from src.interactor_style.RectROIInteractorStyle import RectROIManager
from src.interactor_style.EllipseROIInteractorStyle import EllipseROIManager


class ToolBarService:
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel):
        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.reader = self.baseModelClass.imageReader

        self.annotationService = AnnotationService(self.baseModelClass, self.viewModel)


        # 横截面
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.id_XY = self.viewModel.AxialOrthoViewer.type
        self.label_XY = self.viewModel.AxialOrthoViewer.slider_label
        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider
        self.vtkWidget_XY = self.viewModel.AxialOrthoViewer.widget
        self.camera_XY = self.viewModel.AxialOrthoViewer.camera

        # 矢状面
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.id_YZ = self.viewModel.SagittalOrthoViewer.type
        self.label_YZ = self.viewModel.SagittalOrthoViewer.slider_label
        self.verticalSlider_YZ = self.viewModel.SagittalOrthoViewer.slider
        self.vtkWidget_YZ = self.viewModel.SagittalOrthoViewer.widget
        self.camera_YZ = self.viewModel.SagittalOrthoViewer.camera

        # 冠状面
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        self.id_XZ = self.viewModel.CoronalOrthoViewer.type
        self.label_XZ = self.viewModel.CoronalOrthoViewer.slider_label
        self.verticalSlider_XZ = self.viewModel.CoronalOrthoViewer.slider
        self.vtkWidget_XZ = self.viewModel.CoronalOrthoViewer.widget
        self.camera_XZ = self.viewModel.CoronalOrthoViewer.camera

        self.picker = vtk.vtkPointPicker()
        self.picker.PickFromListOn()

        # 直尺测量存储数据
        self.distance_widgets_1 = []
        self.distance_widgets_2 = []
        self.distance_widgets_3 = []

        # 角度测量存储数据
        self.angle_widgets_1 = []
        self.angle_widgets_2 = []
        self.angle_widgets_3 = []

        # 矩形 ROI 标注管理器
        self._rect_roi_manager = RectROIManager(self.viewModel)
        # 椭圆 ROI 标注管理器
        self._ellipse_roi_manager = EllipseROIManager(self.viewModel)

    # 直尺测量功能
    def on_action_ruler(self):
        print("测量距离")
        rulers = [
            vtk.vtkDistanceWidget(),
            vtk.vtkDistanceWidget(),
            vtk.vtkDistanceWidget()
        ]

        interactors = [
            self.vtkWidget_XY.GetRenderWindow().GetInteractor(),
            self.vtkWidget_YZ.GetRenderWindow().GetInteractor(),
            self.vtkWidget_XZ.GetRenderWindow().GetInteractor()
        ]

        for ruler, interactor in zip(rulers, interactors):
            ruler.SetInteractor(interactor)
            ruler.CreateDefaultRepresentation()
            ruler.On()

        self.distance_widgets_1.append(rulers[0])
        self.distance_widgets_2.append(rulers[1])
        self.distance_widgets_3.append(rulers[2])

        # 设置直尺功能状态为被选中
        ToolBarEnable.ruler_enable = True

    # 清除直尺标注
    def clear_ruler(self):
        # 清除直尺标注
        for ruler_list in [self.distance_widgets_1, self.distance_widgets_2, self.distance_widgets_3]:
            for ruler in ruler_list:
                ruler.Off()
            ruler_list.clear()
        # 设置直尺功能状态为未被选中
        ToolBarEnable.ruler_enable = False

    # 画笔标注功能
    def on_action_paint(self):
        print("画笔标注")
        # 设置画笔功能为选中转态
        ToolBarEnable.paint_enable = True
        event_callbacks = self.create_event_callbacks()
        self.add_observers(self.picker, event_callbacks)

    # 清除画笔标注
    def clear_paint(self):
        # 清除画笔标注
        self.clear_observers("LeftButtonPressEvent", "MouseMoveEvent")
        self.remove_paint_actors()
        ToolBarEnable.paint_enable = False

    # 折线标注功能
    def on_action_polyline(self):
        print("折线标注")
        # 设置折线标注功能为选中状态
        ToolBarEnable.polyline_enable = True
        event_callbacks = self.create_event_callbacks()
        self.add_observers(self.picker, event_callbacks)

    def clear_polyline(self):
        self.clear_observers("LeftButtonPressEvent")
        self.remove_paint_actors()
        # 设置折线标注功能为未被选中状态
        ToolBarEnable.polyline_enable = False

    # 角度测量功能
    def on_action_angle(self):
        print("角度测量")

        angle_widgets = [
            vtk.vtkAngleWidget(),
            vtk.vtkAngleWidget(),
            vtk.vtkAngleWidget()
        ]

        interactors = [
            self.vtkWidget_XY.GetRenderWindow().GetInteractor(),
            self.vtkWidget_YZ.GetRenderWindow().GetInteractor(),
            self.vtkWidget_XZ.GetRenderWindow().GetInteractor()
        ]

        for angle_widget, interactor in zip(angle_widgets, interactors):
            angle_widget.SetInteractor(interactor)
            angle_widget.On()
            angle_widget.CreateDefaultRepresentation()

        self.angle_widgets_1.append(angle_widgets[0])
        self.angle_widgets_2.append(angle_widgets[1])
        self.angle_widgets_3.append(angle_widgets[2])

        # 设置角度测量功能为选中状态
        ToolBarEnable.angle_enable = True

    def clear_angle(self):
        for angle_list in [self.angle_widgets_1,self.angle_widgets_2,self.angle_widgets_3]:
            for angle in angle_list:
                angle.Off()
            angle_list.clear()
        # 设置角度测量功能为未被选中状态
        ToolBarEnable.angle_enable = False

    # 骨密度显示 HU
    def on_action_pixel(self):
        # 读取DICOM数据
        self.dicomdata, self.header = load(getDirPath())
        # 显示HU值
        self.show_pixel(self.picker, self.viewModel.AxialOrthoViewer.viewer, self.vtkWidget_XY, self.dicomdata, self.id_XY)
        self.show_pixel(self.picker, self.viewModel.SagittalOrthoViewer.viewer, self.vtkWidget_YZ, self.dicomdata, self.id_YZ)
        self.show_pixel(self.picker, self.viewModel.CoronalOrthoViewer.viewer, self.vtkWidget_XZ, self.dicomdata, self.id_XZ)
        # 设置骨密度显示功能为选中状态
        ToolBarEnable.pixel_enable = True

    def clear_pixel(self):
        self.vtkWidget_XY.setToolTip('')
        self.vtkWidget_YZ.setToolTip('')
        self.vtkWidget_XZ.setToolTip('')
        self.clear_observers("MouseMoveEvent")
        # 设置骨密度显示功能为未被选中状态
        ToolBarEnable.pixel_enable = False

    # 复位功能
    def on_action_reset(self):
        views = [self.viewModel.AxialOrthoViewer.viewer, self.viewModel.SagittalOrthoViewer.viewer,
                 self.viewModel.CoronalOrthoViewer.viewer]
        cameras = [viewer.GetRenderer().GetActiveCamera() for viewer in views]

        focalPoints = [CameraPosition.focalPoint_XY, CameraPosition.focalPoint_YZ, CameraPosition.focalPoint_XZ]
        positions = [CameraPosition.position_XY, CameraPosition.position_YZ, CameraPosition.position_XZ]

        for viewer, camera, focalPoint, position in zip(views, cameras, focalPoints, positions):
            camera.SetParallelScale(80)
            camera.SetFocalPoint(focalPoint[0], focalPoint[1], focalPoint[2])
            camera.SetPosition(position[0], position[1], position[2])
            self.update_and_render(viewer)

    # 同步定位功能
    def on_action_crosshair(self):
        self.clear_mousewheel_forward_backward_event([self.viewer_XY, self.viewer_YZ, self.viewer_XZ])
        # --------------------------------XY-----------------------------------------------------------------
        # 对图像沿Y轴翻转
        flipYFilter = vtk.vtkImageFlip()
        flipYFilter.SetFilteredAxis(2)
        flipYFilter.FlipAboutOriginOff()
        flipYFilter.SetInputData(self.reader.GetOutput())
        flipYFilter.SetOutputSpacing(self.reader.GetDataSpacing())
        flipYFilter.Update()
        self.CT_Image = flipYFilter.GetOutput()
        # ------------------------------------------------------------
        self.viewer_XY = vtk.vtkResliceImageViewer()
        self.viewer_XY.SetInputData(self.CT_Image)
        self.viewer_XY.SetupInteractor(self.vtkWidget_XY)
        self.viewer_XY.SetRenderWindow(self.vtkWidget_XY.GetRenderWindow())
        self.viewer_XY.SetResliceModeToOblique()
        # -----------------------------------------------
        self.viewer_XY.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCursorAlgorithm().SetResliceCursor(
            self.viewer_XY.GetResliceCursor())
        self.viewer_XY.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCursorAlgorithm().SetReslicePlaneNormal(
            2)
        self.viewer_XY.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            0).SetRepresentationToWireframe()
        self.viewer_XY.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            1).SetRepresentationToWireframe()
        self.viewer_XY.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            2).SetRepresentationToWireframe()
        self.viewer_XY.GetResliceCursorWidget().SetManageWindowLevel(False)
        self.viewer_XY.GetResliceCursorWidget().EnabledOn()
        # --------------------------------------------------------------
        self.viewer_XY.SetSliceOrientationToXY()
        self.viewer_XY.Render()
        self.camera_XY = self.viewer_XY.GetRenderer().GetActiveCamera()
        self.camera_XY.ParallelProjectionOn()  # 开启平行投影
        self.camera_XY.SetParallelScale(80)  # 设置放大倍数（参数跟某个数据有着数学关系，越小图像越大）
        self.viewer_XY.SliceScrollOnMouseWheelOff()
        self.viewer_XY.Render()
        self.wheelforward1 = MouseWheelForward(self.viewer_XY, self.label_XY, self.verticalSlider_XY, self.id_XY)
        self.wheelbackward1 = MouseWheelBackWard(self.viewer_XY, self.label_XY, self.verticalSlider_XY, self.id_XY)
        self.viewer_XY.GetResliceCursorWidget().AddObserver("MouseWheelForwardEvent", self.wheelforward1)
        self.viewer_XY.GetResliceCursorWidget().AddObserver("MouseWheelBackwardEvent", self.wheelbackward1)
        self.viewer_XY.Render()
        # 更新横截面
        self.viewModel.AxialOrthoViewer.viewer = self.viewer_XY

        # --------------------------------YZ-----------------------------------------------------------------
        self.viewer_YZ = vtk.vtkResliceImageViewer()
        self.viewer_YZ.SetInputData(self.CT_Image)
        self.viewer_YZ.SetupInteractor(self.vtkWidget_YZ)
        self.viewer_YZ.SetRenderWindow(self.vtkWidget_YZ.GetRenderWindow())
        self.viewer_YZ.SetResliceModeToOblique()
        self.viewer_YZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCursorAlgorithm().SetResliceCursor(
            self.viewer_XY.GetResliceCursor())
        self.viewer_YZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCursorAlgorithm().SetReslicePlaneNormal(
            0)
        self.viewer_YZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            0).SetRepresentationToWireframe()
        self.viewer_YZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            1).SetRepresentationToWireframe()
        self.viewer_YZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            2).SetRepresentationToWireframe()
        self.viewer_YZ.GetResliceCursorWidget().SetManageWindowLevel(False)

        self.viewer_YZ.SetSliceOrientationToYZ()
        self.viewer_YZ.Render()
        self.viewer_YZ.SliceScrollOnMouseWheelOff()
        self.camera_YZ = self.viewer_YZ.GetRenderer().GetActiveCamera()
        self.camera_YZ.ParallelProjectionOn()
        self.camera_YZ.SetParallelScale(80)
        self.viewer_YZ.Render()
        self.viewer_YZ_InteractorStyle = self.viewer_YZ.GetInteractorStyle()
        self.wheelforward2 = MouseWheelForward(self.viewer_YZ, self.label_YZ, self.verticalSlider_YZ, self.id_YZ)
        self.wheelbackward2 = MouseWheelBackWard(self.viewer_YZ, self.label_YZ, self.verticalSlider_YZ, self.id_YZ)
        self.viewer_YZ.GetResliceCursorWidget().AddObserver("MouseWheelForwardEvent", self.wheelforward2)
        self.viewer_YZ.GetResliceCursorWidget().AddObserver("MouseWheelBackwardEvent", self.wheelbackward2)
        # 更新矢状面
        self.viewModel.SagittalOrthoViewer.viewer = self.viewer_YZ

        # --------------------------------XZ-----------------------------------------------------------------
        self.viewer_XZ = vtk.vtkResliceImageViewer()
        self.viewer_XZ.SetInputData(self.CT_Image)
        self.viewer_XZ.SetupInteractor(self.vtkWidget_XZ)
        self.viewer_XZ.SetRenderWindow(self.vtkWidget_XZ.GetRenderWindow())
        self.viewer_XZ.SetResliceModeToOblique()
        self.viewer_XZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCursorAlgorithm().SetResliceCursor(
            self.viewer_XY.GetResliceCursor())
        self.viewer_XZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCursorAlgorithm().SetReslicePlaneNormal(
            1)
        self.viewer_XZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            0).SetRepresentationToWireframe()
        self.viewer_XZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            1).SetRepresentationToWireframe()
        self.viewer_XZ.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(
            2).SetRepresentationToWireframe()
        self.viewer_XZ.GetResliceCursorWidget().SetManageWindowLevel(False)
        self.viewer_XZ.SetSliceOrientationToXZ()
        # -------------------------------------------------------
        self.viewer_XZ.Render()
        self.viewer_XZ.SliceScrollOnMouseWheelOff()
        self.camera_XZ = self.viewer_XZ.GetRenderer().GetActiveCamera()
        self.camera_XZ.ParallelProjectionOn()
        self.camera_XZ.SetParallelScale(80)
        self.viewer_XZ.Render()
        # -------------------------------------------------------------------
        self.viewer_XZ_InteractorStyle = self.viewer_XZ.GetInteractorStyle()
        self.wheelforward3 = MouseWheelForward(self.viewer_XZ, self.label_XZ, self.verticalSlider_XZ, self.id_XZ)
        self.wheelbackward3 = MouseWheelBackWard(self.viewer_XZ, self.label_XZ, self.verticalSlider_XZ, self.id_XZ)
        self.viewer_XZ.GetResliceCursorWidget().AddObserver("MouseWheelForwardEvent", self.wheelforward3)
        self.viewer_XZ.GetResliceCursorWidget().AddObserver("MouseWheelBackwardEvent", self.wheelbackward3)
        # 更新冠状面
        self.viewModel.CoronalOrthoViewer.viewer = self.viewer_XZ

        # -------------------------------------------------------------------
        self.origin = self.reader.GetOutput().GetOrigin()
        self.spacing = self.reader.GetOutput().GetSpacing()
        center = self.reader.GetOutput().GetCenter()
        self.verticalSlider_XZ.setValue(int((center[0] - self.origin[0]) / self.spacing[0]))
        self.verticalSlider_YZ.setValue(int((center[1] - self.origin[1]) / self.spacing[1]))
        self.verticalSlider_XY.setValue(int((center[2] - self.origin[2]) / self.spacing[2]))

        self.label_XZ.setText("Slice %d/%d" % (self.verticalSlider_XZ.value(), self.viewer_XZ.GetSliceMax()))
        self.label_YZ.setText("Slice %d/%d" % (self.verticalSlider_YZ.value(), self.viewer_YZ.GetSliceMax()))
        self.label_XY.setText("Slice %d/%d" % (self.verticalSlider_XY.value(), self.viewer_XY.GetSliceMax()))

        self.viewer_XY.GetResliceCursorWidget().GetResliceCursorRepresentation().SetWindowLevel(
            ToolBarWidget.contrast_widget.window_width_slider.value(),
            ToolBarWidget.contrast_widget.window_level_slider.value())

        self.viewer_YZ.GetResliceCursorWidget().GetResliceCursorRepresentation().SetWindowLevel(
            ToolBarWidget.contrast_widget.window_width_slider.value(),
            ToolBarWidget.contrast_widget.window_level_slider.value())

        self.viewer_XZ.GetResliceCursorWidget().GetResliceCursorRepresentation().SetWindowLevel(
            ToolBarWidget.contrast_widget.window_width_slider.value(),
            ToolBarWidget.contrast_widget.window_level_slider.value())
        # -------------------------------------------------------------------------------------------------------------------

        self.commandSliceSelect_XY = CommandSelect(self.id_XY, self.baseModelClass, self.viewModel,
                                                   self.viewer_XY.GetResliceCursor())
        self.viewer_XY.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent,
                                                            self.commandSliceSelect_XY)
        self.commandSliceSelect_YZ = CommandSelect(self.id_YZ, self.baseModelClass, self.viewModel,
                                                   self.viewer_XY.GetResliceCursor())
        self.viewer_YZ.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent,
                                                            self.commandSliceSelect_YZ)
        self.commandSliceSelect_XZ = CommandSelect(self.id_XZ, self.baseModelClass, self.viewModel,
                                                   self.viewer_XY.GetResliceCursor())
        self.viewer_XZ.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent,
                                                            self.commandSliceSelect_XZ)
        self.viewer_XY.Render()
        self.viewer_YZ.Render()
        self.viewer_XZ.Render()
        ToolBarEnable.crosshair_enable = True


    def clear_crosshair(self):
        # 加载更新后的视图
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        # 去除窗口的Event
        self.clear_mousewheel_forward_backward_event([self.viewer_XY, self.viewer_YZ, self.viewer_XZ])
        # ------------------------------------------------------------------------
        self.viewer_XY.GetResliceCursorWidget().EnabledOff()
        self.viewer_YZ.GetResliceCursorWidget().EnabledOff()
        self.viewer_XZ.GetResliceCursorWidget().EnabledOff()

        self.window_level = ToolBarWidget.contrast_widget.window_level_slider.value()
        self.window_width = ToolBarWidget.contrast_widget.window_width_slider.value()

        self.reader.SetDirectoryName(getDirPath())
        self.reader.Update()
        # 更新Data
        self.baseModelClass.imageReader = self.reader
        self.baseModelClass.update_data_information()

        self.dims = self.reader.GetOutput().GetDimensions()
        self.dicomdata, self.header = load(getDirPath())

        bounds = self.baseModelClass.bounds
        self.center0 = (bounds[1] + bounds[0]) / 2.0
        self.center1 = (bounds[3] + bounds[2]) / 2.0
        self.center2 = (bounds[5] + bounds[4]) / 2.0

        # 更新横断面
        self.focalPoint_XY, self.position_XY = self.update_viewer(self.viewModel.AxialOrthoViewer,
                                                                  self.vtkWidget_XY, self.label_XY,
                                                                  self.verticalSlider_XY, self.id_XY)
        # 更新矢状面
        self.focalPoint_YZ, self.position_YZ = self.update_viewer(self.viewModel.SagittalOrthoViewer,
                                                                  self.vtkWidget_YZ, self.label_YZ,
                                                                  self.verticalSlider_YZ, self.id_YZ)
        # 更新冠状面
        self.focalPoint_XZ, self.position_XZ = self.update_viewer(self.viewModel.CoronalOrthoViewer,
                                                                  self.vtkWidget_XZ, self.label_XZ,
                                                                  self.verticalSlider_XZ, self.id_XZ)
        # 记录相机位置
        CameraPosition.position_XY = self.position_XY
        CameraPosition.position_YZ = self.position_YZ
        CameraPosition.position_XZ = self.position_XZ
        CameraPosition.focalPoint_XY = self.focalPoint_XY
        CameraPosition.focalPoint_YZ = self.focalPoint_YZ
        CameraPosition.focalPoint_XZ = self.focalPoint_XZ

        ToolBarEnable.crosshair_enable = False

    def update_viewer(self, viewModel, vtkWidget, label, verticalSlider, id):
        print("id_type:", id)
        viewer = vtk.vtkResliceImageViewer()
        viewer.SetInputData(self.reader.GetOutput())
        viewer.SetupInteractor(vtkWidget)
        viewer.SetRenderWindow(vtkWidget.GetRenderWindow())
        if id == "XY":
            viewer.SetSliceOrientationToXY()
        elif id == "YZ":
            viewer.SetSliceOrientationToYZ()
            transform_YZ = vtk.vtkTransform()
            transform_YZ.Translate(self.center0, self.center1, self.center2)
            transform_YZ.RotateX(180)
            transform_YZ.RotateZ(180)
            transform_YZ.Translate(-self.center0, -self.center1, -self.center2)
            viewer.GetImageActor().SetUserTransform(transform_YZ)
        elif id == "XZ":
            viewer.SetSliceOrientationToXZ()
            transform_XZ = vtk.vtkTransform()
            transform_XZ.Translate(self.center0, self.center1, self.center2)
            transform_XZ.RotateY(180)
            transform_XZ.RotateZ(180)
            transform_XZ.Translate(-self.center0, -self.center1, -self.center2)
            viewer.GetImageActor().SetUserTransform(transform_XZ)
        viewer.Render()

        camera = viewer.GetRenderer().GetActiveCamera()
        camera.ParallelProjectionOn()
        camera.SetParallelScale(80)
        focalPoint = camera.GetFocalPoint()
        position = camera.GetPosition()

        viewer.SliceScrollOnMouseWheelOff()
        viewer.UpdateDisplayExtent()
        viewer.Render()

        wheelforward = MouseWheelForward(viewer, label, verticalSlider, id)
        wheelbackward = MouseWheelBackWard(viewer, label, verticalSlider, id)
        viewer_InteractorStyle = viewer.GetInteractorStyle()
        viewer_InteractorStyle.AddObserver("MouseWheelForwardEvent", wheelforward)
        viewer_InteractorStyle.AddObserver("MouseWheelBackwardEvent", wheelbackward)

        viewer.SetColorLevel(ToolBarWidget.contrast_widget.window_level_slider.value())
        viewer.SetColorWindow(ToolBarWidget.contrast_widget.window_width_slider.value())

        value = viewModel.slider.value()
        viewer.SetSlice(value)
        viewModel.slider_label.setText("Slice %d/%d" % (viewer.GetSlice(), viewer.GetSliceMax()))
        viewer.UpdateDisplayExtent()
        viewer.Render()

        vtkWidget.GetRenderWindow().Render()

        viewModel.viewer = viewer

        return focalPoint, position

    def on_action_dragging_image(self):
        ToolBarEnable.dragging_enable = True
        event_callbacks = self.create_event_callbacks()
        self.add_observers(self.picker, event_callbacks)

    def clear_dragging_image(self):
        self.clear_observers("LeftButtonPressEvent", "MouseMoveEvent", "LeftButtonReleaseEvent")
        ToolBarEnable.dragging_enable = False

    def on_action_get_roi(self):
        ToolBarEnable.roi_enable = True
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        self.viewer_XY_InteractorStyle = self.viewer_XY.GetInteractorStyle()
        self.viewer_YZ_InteractorStyle = self.viewer_YZ.GetInteractorStyle()
        self.viewer_XZ_InteractorStyle = self.viewer_XZ.GetInteractorStyle()

        roi_point_dict = {}

        dim = self.baseModelClass.imageDimensions
        origin = self.baseModelClass.origin
        spacing = self.baseModelClass.spacing
        radius_xy = (3 - origin[0]) / spacing[0]
        view_xy = "view_xy"
        left_down_x = 0
        left_down_y = 0
        left_up_x = 0
        left_up_y = dim[1]
        right_down_x = dim[0]
        right_down_y = 0
        right_up_x = dim[0]
        right_up_y = dim[1]
        left_mid_x = 0
        left_mid_y = dim[1] / 2
        right_mid_x = dim[0]
        right_mid_y = dim[1] / 2
        up_mid_x = dim[0] / 2
        up_mid_y = dim[1]
        down_mid_x = dim[0] / 2
        down_mid_y = 0
        mid_x = dim[0] / 2
        mid_y = dim[1] / 2

        temp_actor = self.draw_point(left_down_x, left_down_y, dim[2] + 1, color=[1, 1, 1], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "left_down_point",
                       [left_down_x, left_down_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_point(left_up_x, left_up_y, dim[2] + 1, color=[1, 1, 1], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "left_up_point",
                       [left_up_x, left_up_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_point(right_down_x, right_down_y, dim[2] + 1, color=[1, 1, 1], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "right_down_point",
                       [right_down_x, right_down_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_point(right_up_x, right_up_y, dim[2] + 1, color=[1, 1, 1], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "right_up_point",
                       [right_up_x, right_up_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_point(left_mid_x, left_mid_y, dim[2] + 1, color=[1, 0, 0], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "left_mid_point",
                       [left_mid_x, left_mid_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_point(right_mid_x, right_mid_y, dim[2] + 1, color=[1, 0, 0], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "right_mid_point",
                       [right_mid_x, right_mid_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_point(up_mid_x, up_mid_y, dim[2] + 1, color=[0, 1, 0], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "up_mid_point",
                       [up_mid_x, up_mid_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_point(down_mid_x, down_mid_y, dim[2] + 1, color=[0, 1, 0], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "down_mid_point",
                       [down_mid_x, down_mid_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_point(mid_x, mid_y, dim[2] + 1, color=[1, 0.5, 0], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "mid_point",
                       [mid_x, mid_y, dim[2] + 1], temp_actor)

        temp_actor = self.draw_line([left_down_x, left_down_y + radius_xy, dim[2] + 1],
                       [left_mid_x, left_mid_y - radius_xy, dim[2] + 1],
                       color=[1, 0.5, 0.5], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "left_down_line",
                       None, temp_actor)

        temp_actor = self.draw_line([left_mid_x, left_mid_y + radius_xy, dim[2] + 1],
                       [left_up_x, left_up_y - radius_xy, dim[2] + 1],
                       color=[1, 0.5, 0.5], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "left_up_line",
                       None, temp_actor)

        temp_actor = self.draw_line([left_down_x + radius_xy, left_down_y, dim[2] + 1],
                       [down_mid_x - radius_xy, down_mid_y, dim[2] + 1],
                       color=[1, 0.5, 0.5], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "down_left_line",
                       None, temp_actor)

        temp_actor = self.draw_line([down_mid_x + radius_xy, down_mid_y, dim[2] + 1],
                       [right_down_x - radius_xy, right_down_y, dim[2] + 1],
                       color=[1, 0.5, 0.5], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "down_right_line",
                       None, temp_actor)

        temp_actor = self.draw_line([right_down_x, right_down_y + radius_xy, dim[2] + 1],
                       [right_mid_x, right_mid_y - radius_xy, dim[2] + 1],
                       color=[1, 0.5, 0.5], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "right_down_line",
                       None, temp_actor)

        temp_actor = self.draw_line([right_mid_x, right_mid_y + radius_xy, dim[2] + 1],
                       [right_up_x, right_up_y - radius_xy, dim[2] + 1],
                       color=[1, 0.5, 0.5], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "right_up_line",
                       None, temp_actor)

        temp_actor = self.draw_line([left_up_x + radius_xy, left_up_y, dim[2] + 1],
                       [up_mid_x - radius_xy, up_mid_y, dim[2] + 1],
                       color=[1, 0.5, 0.5], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "up_left_line",
                       None, temp_actor)

        temp_actor = self.draw_line([up_mid_x + radius_xy, up_mid_y, dim[2] + 1],
                       [right_up_x - radius_xy, right_up_y, dim[2] + 1],
                       color=[1, 0.5, 0.5], view_type=view_xy)
        self.add_point(roi_point_dict, view_xy, "up_right_line",
                       None, temp_actor)

        view_xz = "view_xz"
        left_down_x = 0
        left_down_z = 0
        left_up_x = 0
        left_up_z = dim[2]
        right_down_x = dim[0]
        right_down_z = 0
        right_up_x = dim[0]
        right_up_z = dim[2]
        left_mid_x = 0
        left_mid_z = dim[2] / 2
        right_mid_x = dim[0]
        right_mid_z = dim[2] / 2
        up_mid_x = dim[0] / 2
        up_mid_z = dim[2]
        down_mid_x = dim[0] / 2
        down_mid_z = 0
        mid_x = dim[0] / 2
        mid_z = dim[2] / 2

        temp_actor = self.draw_point(left_down_x, 0, left_down_z, color=[1, 1, 1], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "left_down_point",
                       [left_down_x, 0, left_down_z], temp_actor)

        temp_actor = self.draw_point(left_up_x, 0, left_up_z, color=[1, 1, 1], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "left_up_point",
                       [left_up_x, 0, left_up_z], temp_actor)

        temp_actor = self.draw_point(right_down_x, 0, right_down_z, color=[1, 1, 1], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "right_down_point",
                       [right_down_x, 0, right_down_z], temp_actor)

        temp_actor = self.draw_point(right_up_x, 0, right_up_z, color=[1, 1, 1], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "right_up_point",
                       [right_up_x, 0, right_up_z], temp_actor)

        temp_actor = self.draw_point(left_mid_x, 0, left_mid_z, color=[1, 0, 0], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "left_mid_point",
                       [left_mid_x, 0, left_mid_z], temp_actor)

        temp_actor = self.draw_point(right_mid_x, 0, right_mid_z, color=[1, 0, 0], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "right_mid_point",
                       [right_mid_x, 0, right_mid_z], temp_actor)

        temp_actor = self.draw_point(up_mid_x, 0, up_mid_z, color=[0, 0, 1], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "up_mid_point",
                       [up_mid_x, 0, up_mid_z], temp_actor)

        temp_actor = self.draw_point(down_mid_x, 0, down_mid_z, color=[0, 0, 1], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "down_mid_point",
                       [down_mid_x, 0, down_mid_z], temp_actor)

        temp_actor = self.draw_point(mid_x, 0, mid_z, color=[1, 0.5, 0], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "mid_point",
                       [mid_x, 0, mid_z], temp_actor)

        temp_actor = self.draw_line([left_down_x, 0, left_down_z + radius_xy], [left_mid_x, 0, left_mid_z - radius_xy],
                       color=[1, 0.5, 0.5], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "left_down_line",
                       None, temp_actor)

        temp_actor = self.draw_line([left_mid_x, 0, left_mid_z + radius_xy, ], [left_up_x, 0, left_up_z - radius_xy],
                       color=[1, 0.5, 0.5], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "left_up_line",
                       None, temp_actor)

        temp_actor = self.draw_line([left_down_x + radius_xy, 0, left_down_z], [down_mid_x - radius_xy, 0, down_mid_z],
                       color=[1, 0.5, 0.5], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "down_left_line",
                       None, temp_actor)

        temp_actor = self.draw_line([down_mid_x + radius_xy, 0, down_mid_z], [right_down_x - radius_xy, 0, right_down_z],
                       color=[1, 0.5, 0.5], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "down_right_line",
                       None, temp_actor)

        temp_actor = self.draw_line([right_down_x, 0, right_down_z + radius_xy], [right_mid_x, 0, right_mid_z - radius_xy],
                       color=[1, 0.5, 0.5], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "right_down_line",
                       None, temp_actor)

        temp_actor = self.draw_line([right_mid_x, 0, right_mid_z + radius_xy], [right_up_x, 0, right_up_z - radius_xy],
                       color=[1, 0.5, 0.5], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "right_up_line",
                       None, temp_actor)

        temp_actor = self.draw_line([left_up_x + radius_xy, 0, left_up_z], [up_mid_x - radius_xy, 0, up_mid_z],
                       color=[1, 0.5, 0.5], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "up_left_line",
                       None, temp_actor)

        temp_actor = self.draw_line([up_mid_x + radius_xy, 0, up_mid_z], [right_up_x - radius_xy, 0, right_up_z],
                       color=[1, 0.5, 0.5], view_type=view_xz)
        self.add_point(roi_point_dict, view_xz, "up_right_line",
                       None, temp_actor)

        view_yz = "view_yz"
        left_down_y = 0
        left_down_z = 0
        left_up_y = 0
        left_up_z = dim[2]
        right_down_y = dim[1]
        right_down_z = 0
        right_up_y = dim[1]
        right_up_z = dim[2]
        left_mid_y = 0
        left_mid_z = dim[2] / 2
        right_mid_y = dim[1]
        right_mid_z = dim[2] / 2
        up_mid_y = dim[1] / 2
        up_mid_z = dim[2]
        down_mid_y = dim[1] / 2
        down_mid_z = 0
        mid_y = dim[1] / 2
        mid_z = dim[2] / 2

        temp_actor = self.draw_point(dim[0] + 1, left_down_y, left_down_z, color=[1, 1, 1], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "left_down_point",
                       [dim[0] + 1, left_down_y, left_down_z], temp_actor)

        temp_actor = self.draw_point(dim[0] + 1, left_up_y, left_up_z, color=[1, 1, 1], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "left_up_point",
                       [dim[0] + 1, left_up_y, left_up_z], temp_actor)

        temp_actor = self.draw_point(dim[0] + 1, right_down_y, right_down_z, color=[1, 1, 1], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "right_down_point",
                       [dim[0] + 1, right_down_y, right_down_z], temp_actor)

        temp_actor = self.draw_point(dim[0] + 1, right_up_y, right_up_z, color=[1, 1, 1], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "right_up_point",
                       [dim[0] + 1, right_up_y, right_up_z], temp_actor)

        temp_actor = self.draw_point(dim[0] + 1, left_mid_y, left_mid_z, color=[0, 1, 0], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "left_mid_point",
                       [dim[0] + 1, left_mid_y, left_mid_z], temp_actor)

        temp_actor = self.draw_point(dim[0] + 1, right_mid_y, right_mid_z, color=[0, 1, 0], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "right_mid_point",
                       [dim[0] + 1, right_mid_y, right_mid_z], temp_actor)

        temp_actor = self.draw_point(dim[0] + 1, up_mid_y, up_mid_z, color=[0, 0, 1], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "up_mid_point",
                       [dim[0] + 1, up_mid_y, up_mid_z], temp_actor)

        temp_actor = self.draw_point(dim[0] + 1, down_mid_y, down_mid_z, color=[0, 0, 1], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "down_mid_point",
                       [dim[0] + 1, down_mid_y, down_mid_z], temp_actor)

        temp_actor = self.draw_point(dim[0] + 1, mid_y, mid_z, color=[1, 0.5, 0], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "mid_point",
                       [dim[0] + 1, mid_y, mid_z], temp_actor)

        temp_actor = self.draw_line([dim[0], left_down_y, left_down_z + radius_xy],
                       [dim[0], left_mid_y, left_mid_z - radius_xy],
                       color=[1, 0.5, 0.5], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "left_down_line",
                       None, temp_actor)

        temp_actor = self.draw_line([dim[0], left_mid_y, left_mid_z + radius_xy, ],
                       [dim[0], left_up_y, left_up_z - radius_xy],
                       color=[1, 0.5, 0.5], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "left_up_line",
                       None, temp_actor)

        temp_actor = self.draw_line([dim[0], left_down_y + radius_xy, left_down_z],
                       [dim[0], down_mid_y - radius_xy, down_mid_z],
                       color=[1, 0.5, 0.5], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "down_left_line",
                       None, temp_actor)

        temp_actor = self.draw_line([dim[0], down_mid_y + radius_xy, down_mid_z],
                       [dim[0], right_down_y - radius_xy, right_down_z],
                       color=[1, 0.5, 0.5], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "down_right_line",
                       None, temp_actor)

        temp_actor = self.draw_line([dim[0], right_down_y, right_down_z + radius_xy],
                       [dim[0], right_mid_y, right_mid_z - radius_xy],
                       color=[1, 0.5, 0.5], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "right_down_line",
                       None, temp_actor)

        temp_actor = self.draw_line([dim[0], right_mid_y, right_mid_z + radius_xy],
                       [dim[0], right_up_y, right_up_z - radius_xy],
                       color=[1, 0.5, 0.5], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "right_up_line",
                       None, temp_actor)

        temp_actor = self.draw_line([dim[0], left_up_y + radius_xy, left_up_z], [dim[0], up_mid_y - radius_xy, up_mid_z],
                       color=[1, 0.5, 0.5], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "up_left_line",
                       None, temp_actor)

        temp_actor = self.draw_line([dim[0], up_mid_y + radius_xy, up_mid_z], [dim[0], right_up_y - radius_xy, right_up_z],
                       color=[1, 0.5, 0.5], view_type=view_yz)
        self.add_point(roi_point_dict, view_yz, "up_right_line",
                       None, temp_actor)

        setControlROIPoint(roi_point_dict)

        self.picker = vtk.vtkPointPicker()
        self.picker.PickFromListOn()
        self.get_roi_press_xy = MouseMoveEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ,
                                                      self.viewer_XZ,
                                                      view_xy)
        self.press_xy = LeftButtonPressEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ, self.viewer_XZ,
                                                    view_xy)
        self.release_xy = LeftButtonReleaseEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ,
                                                        self.viewer_XZ,
                                                        view_xy)
        self.viewer_XY_InteractorStyle.AddObserver("MouseMoveEvent", self.get_roi_press_xy)
        self.viewer_XY_InteractorStyle.AddObserver("LeftButtonPressEvent", self.press_xy)
        self.viewer_XY_InteractorStyle.AddObserver("LeftButtonReleaseEvent", self.release_xy)
        self.viewer_XY.UpdateDisplayExtent()
        self.viewer_XY.Render()

        self.get_roi_press_yz = MouseMoveEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ,
                                                      self.viewer_XZ,
                                                      view_yz)
        self.press_yz = LeftButtonPressEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ, self.viewer_XZ,
                                                    view_yz)
        self.release_yz = LeftButtonReleaseEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ,
                                                        self.viewer_XZ,
                                                        view_yz)
        self.viewer_YZ_InteractorStyle.AddObserver("MouseMoveEvent", self.get_roi_press_yz)
        self.viewer_YZ_InteractorStyle.AddObserver("LeftButtonPressEvent", self.press_yz)
        self.viewer_YZ_InteractorStyle.AddObserver("LeftButtonReleaseEvent", self.release_yz)
        self.viewer_YZ.UpdateDisplayExtent()
        self.viewer_YZ.Render()

        self.get_roi_press_xz = MouseMoveEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ,
                                                      self.viewer_XZ,
                                                      view_xz)
        self.press_xz = LeftButtonPressEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ, self.viewer_XZ,
                                                    view_xz)
        self.release_xz = LeftButtonReleaseEvent_GetROI(self.picker, self.viewer_XY, self.viewer_YZ,
                                                        self.viewer_XZ,
                                                        view_xz)
        self.viewer_XZ_InteractorStyle.AddObserver("MouseMoveEvent", self.get_roi_press_xz)
        self.viewer_XZ_InteractorStyle.AddObserver("LeftButtonPressEvent", self.press_xz)
        self.viewer_XZ_InteractorStyle.AddObserver("LeftButtonReleaseEvent", self.release_xz)
        self.viewer_XZ.UpdateDisplayExtent()
        self.viewer_XZ.Render()

    def clear_get_roi(self):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        dict = getControlROIPoint()
        print(dict)
        name_list = ["left_down_point", "left_mid_point", "left_up_point", "right_down_point",
                     "right_mid_point",
                     "right_up_point",
                     "down_mid_point", "up_mid_point", "mid_point", "left_down_line", "left_up_line",
                     "right_down_line", "right_up_line",
                     "down_left_line", "down_right_line", "up_left_line", "up_right_line"]
        try:
            for name in name_list:
                self.viewer_XY.GetRenderer().RemoveActor(dict["view_xy"][name]["actor"])
                self.viewer_YZ.GetRenderer().RemoveActor(dict["view_yz"][name]["actor"])
                self.viewer_XZ.GetRenderer().RemoveActor(dict["view_xz"][name]["actor"])
            self.viewer_XY.Render()
            self.viewer_XZ.Render()
            self.viewer_YZ.Render()
        except:
            print("remove roi actor failed!!!")

        clearControllerROIPoint()

        self.clear_observers("MouseMoveEvent", "LeftButtonPressEvent", "LeftButtonReleaseEvent")
        ToolBarEnable.roi_enable = False

    def add_point(self, roi_point_dict, view, point_name, point, actor):
        if view not in roi_point_dict:
            roi_point_dict[view] = {}
        roi_point_dict[view][point_name] = {"point": point, "actor": actor}

    def draw_line(self, point1, point2, color=None, view_type=None):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        origin = self.baseModelClass.origin
        spacing = self.baseModelClass.spacing
        if view_type == "view_xy":
            point1[0] = point1[0] * spacing[0] + origin[0]
            point1[1] = point1[1] * spacing[1] + origin[1]
            point2[0] = point2[0] * spacing[0] + origin[0]
            point2[1] = point2[1] * spacing[1] + origin[1]
        elif view_type == "view_yz":
            point1[0] = point1[0] * spacing[0] + origin[0]
            point1[1] = point1[1] * spacing[1] + origin[1]
            point1[2] = point1[2] * spacing[2] + origin[2]
            point2[0] = point2[0] * spacing[0] + origin[0]
            point2[1] = point2[1] * spacing[1] + origin[1]
            point2[2] = point2[2] * spacing[2] + origin[2]
        else:
            point1[0] = point1[0] * spacing[0] + origin[0]
            point1[2] = point1[2] * spacing[2] + origin[2]
            point2[0] = point2[0] * spacing[0] + origin[0]
            point2[2] = point2[2] * spacing[2] + origin[2]
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
        if view_type == "view_xy":
            self.viewer_XY.GetRenderer().AddActor(actor)
        elif view_type == "view_xz":
            self.viewer_XZ.GetRenderer().AddActor(actor)
        elif view_type == "view_yz":
            self.viewer_YZ.GetRenderer().AddActor(actor)
        return actor

    def draw_point(self, x, y, z, color=None, view_type=None):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.viewer_YZ = self.viewModel.SagittalOrthoViewer.viewer
        self.viewer_XZ = self.viewModel.CoronalOrthoViewer.viewer
        origin = self.baseModelClass.origin
        spacing = self.baseModelClass.spacing

        radius_xy = 3
        point_x = x * spacing[0] + origin[0]
        point_y = y * spacing[1] + origin[1]
        point_z = z * spacing[2] + origin[2]

        square = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        if view_type == "view_xy":
            points.InsertNextPoint(point_x - radius_xy, point_y + radius_xy, point_z)
            points.InsertNextPoint(point_x + radius_xy, point_y + radius_xy, point_z)
            points.InsertNextPoint(point_x + radius_xy, point_y - radius_xy, point_z)
            points.InsertNextPoint(point_x - radius_xy, point_y - radius_xy, point_z)
        elif view_type == "view_yz":
            points.InsertNextPoint(point_x, point_y - radius_xy, point_z + radius_xy)
            points.InsertNextPoint(point_x, point_y + radius_xy, point_z + radius_xy)
            points.InsertNextPoint(point_x, point_y + radius_xy, point_z - radius_xy)
            points.InsertNextPoint(point_x, point_y - radius_xy, point_z - radius_xy)
        elif view_type == "view_xz":
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
        if view_type == "view_xy":
            self.viewer_XY.GetRenderer().AddActor(actor)
        if view_type == "view_xz":
            self.viewer_XZ.GetRenderer().AddActor(actor)
        if view_type == "view_yz":
            self.viewer_YZ.GetRenderer().AddActor(actor)
        return actor

    def show_pixel(self, picker, viewer, widget, dicomdata, axis):
        dicomdata_rotated = self.rotate_dicom_data(dicomdata, axis)
        observer = CallBack(viewer, picker, widget, dicomdata_rotated)
        interactorStyle = viewer.GetInteractorStyle()
        interactorStyle.AddObserver("MouseMoveEvent", observer)

    def rotate_dicom_data(self, dicomdata, axis):
        if axis == 'XY':
            dicomdata_rotated = np.rot90(dicomdata, 2, axes=(0, 1))
            return np.rot90(dicomdata_rotated, 2, axes=(0, 2))
        elif axis == 'YZ':
            return np.rot90(dicomdata, 2, axes=(0, 1))
        elif axis == 'XZ':
            return dicomdata
        else:
            raise ValueError("Unsupported axis")

    def add_observers(self, picker, event_callbacks):
        viewers = [self.viewModel.AxialOrthoViewer.viewer, self.viewModel.SagittalOrthoViewer.viewer, self.viewModel.CoronalOrthoViewer.viewer]
        ids = [self.id_XY, self.id_YZ, self.id_XZ]

        for viewer, id_type in zip(viewers, ids):
            interactorStyle = viewer.GetInteractorStyle()
            for event, callback in event_callbacks.items():
                if ToolBarEnable.dragging_enable:
                    observer = callback(viewer, id_type)
                else:
                    observer = callback(picker, viewer, id_type)
                interactorStyle.AddObserver(event, observer)
            self.update_and_render(viewer)

    def update_and_render(self, viewer):
        viewer.UpdateDisplayExtent()
        viewer.Render()

    def create_event_callbacks(self):
        event_callbacks = {}
        if ToolBarEnable.paint_enable:
            event_callbacks['LeftButtonPressEvent'] = LeftButtonPressEvent
            event_callbacks['MouseMoveEvent'] = MouseMoveEvent
        elif ToolBarEnable.polyline_enable:
            event_callbacks['LeftButtonPressEvent'] = LeftButtonPressEvent_poly
        elif ToolBarEnable.dragging_enable:
            event_callbacks["LeftButtonPressEvent"] = LeftButtonPressEvent_Dragging
            event_callbacks["LeftButtonReleaseEvent"] = LeftButtonReleaseEvent_Dragging
            event_callbacks["MouseMoveEvent"] = MouseMoveEvent_Dragging

        return event_callbacks

    def clear_observers(self, *events):
        try:
            viewers = [self.viewModel.AxialOrthoViewer.viewer, self.viewModel.SagittalOrthoViewer.viewer,
                       self.viewModel.CoronalOrthoViewer.viewer]
            for viewer in viewers:
                for event in events:
                    viewer.GetInteractorStyle().RemoveObservers(event)
        except:
            print("event not exist")

    def remove_paint_actors(self):
        try:
            for viewer in [self.viewModel.AxialOrthoViewer.viewer, self.viewModel.SagittalOrthoViewer.viewer, self.viewModel.CoronalOrthoViewer.viewer]:
                for actor in getActors_paint():
                    viewer.GetRenderer().RemoveActor(actor)
                self.update_and_render(viewer)
        except Exception as e:
            print(f"Error removing paint actors: {e}")

    def disable_point_action(self):
        if AnnotationEnable.pointAction.isChecked():
            AnnotationEnable.pointAction.setChecked(False)
            self.viewer_XY_InteractorStyle = self.viewModel.AxialOrthoViewer.viewer.GetInteractorStyle()
            print("结束标注 point")
            self.annotationService.label_clear()
            ToolBarWidget.annotation_widget.widget_labels.hide()
            self.viewer_XY_InteractorStyle.RemoveObservers("LeftButtonPressEvent")

    def disable_label_box_action(self):
        if AnnotationEnable.labelBoxAction.isChecked():
            self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
            self.viewer_XY_InteractorStyle = self.viewer_XY.GetInteractorStyle()
            ToolBarWidget.annotation_widget.widget_labels.hide()
            self.viewer_XY_InteractorStyle.RemoveObservers("LeftButtonPressEvent")
            self.viewer_XY_InteractorStyle.RemoveObservers("MouseMoveEvent")
            AnnotationEnable.labelBoxAction.setChecked(False)


    def clear_mousewheel_forward_backward_event(self, viewer_list):
        try:
            for viewer in viewer_list:
                viewer_InteractorStyle = viewer.GetInteractorStyle()
                viewer_InteractorStyle.RemoveObservers("MouseWheelForwardEvent")
                viewer_InteractorStyle.RemoveObservers("MouseWheelBackwardEvent")
        except:
            print("event not exist")

    # 矩形 ROI 标注功能
    def on_action_rect_roi(self):
        self._rect_roi_manager.activate()
        ToolBarEnable.rect_roi_enable = True

    def clear_rect_roi(self):
        self._rect_roi_manager.deactivate()
        ToolBarEnable.rect_roi_enable = False

    def clear_all_rect_roi(self):
        """清除全部矩形标注（含已绘制的）"""
        self._rect_roi_manager.clear_all()
        ToolBarEnable.rect_roi_enable = False

    def on_action_ellipse_roi(self):
        self._ellipse_roi_manager.activate()
        ToolBarEnable.ellipse_roi_enable = True

    def clear_ellipse_roi(self):
        self._ellipse_roi_manager.deactivate()
        ToolBarEnable.ellipse_roi_enable = False

    def clear_all_ellipse_roi(self):
        self._ellipse_roi_manager.clear_all()
        ToolBarEnable.ellipse_roi_enable = False

    def clear_all_annotations(self):
        """清除所有矩形和椭圆标注"""
        self._rect_roi_manager.clear_all()
        self._ellipse_roi_manager.clear_all()
        ToolBarEnable.rect_roi_enable = False
        ToolBarEnable.ellipse_roi_enable = False
