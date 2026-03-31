import vtk
from PyQt5 import QtWidgets, QtCore
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src.model.VolumeRenderModel import VolumeRender
from src.model.BaseModel import BaseModel
from src.utils.state_store import get_state_store
from src.utils.logger import get_logger
from src.controller.PlaybackController import PlaybackController
from src.widgets.PlaybackBarWidget import PlaybackBar
from src.widgets.PseudoColorBar import PseudoColorBar
from src.widgets.ScaleBarWidget import ScaleBar

logger = get_logger(__name__)


# ── 解剖方位正方体 ─────────────────────────────────────────────────────────────

def _build_orientation_cube(interactor: vtk.vtkRenderWindowInteractor):
    """
    构建解剖方位正方体，固定在右下角，随主视图相机同步旋转。
    点击正方体面跳转到对应标准视角。
    """
    cube = vtk.vtkAnnotatedCubeActor()

    # 六面文字 —— 根据 vtkDICOMImageReader 实际加载方向校正
    # vtkDICOMImageReader 读取后：+Z = Superior, -Z = Inferior
    # Y 轴：+Y = Anterior, -Y = Posterior（与 LPS 相反）
    # X 轴：+X = Left, -X = Right
    cube.SetXPlusFaceText("L")    # +X = Left
    cube.SetXMinusFaceText("R")   # -X = Right
    cube.SetYPlusFaceText("A")    # +Y = Anterior
    cube.SetYMinusFaceText("P")   # -Y = Posterior
    cube.SetZPlusFaceText("I")    # +Z = Inferior
    cube.SetZMinusFaceText("S")   # -Z = Superior
    cube.SetFaceTextScale(0.55)
    cube.SetFaceTextVisibility(1)

    # 修正各面文字镜像问题
    cube.SetXFaceTextRotation(180)
    cube.SetYFaceTextRotation(180)
    cube.SetZFaceTextRotation(0)

    # 棱线
    cube.GetTextEdgesProperty().SetColor(0.2, 0.2, 0.2)
    cube.GetTextEdgesProperty().SetLineWidth(1)

    # 各面颜色
    cube.GetXPlusFaceProperty().SetColor(0.85, 0.35, 0.35)   # L 红
    cube.GetXMinusFaceProperty().SetColor(0.85, 0.35, 0.35)  # R 红
    cube.GetYPlusFaceProperty().SetColor(0.35, 0.65, 0.35)   # P 绿
    cube.GetYMinusFaceProperty().SetColor(0.35, 0.65, 0.35)  # A 绿
    cube.GetZPlusFaceProperty().SetColor(0.95, 0.75, 0.20)   # S 黄
    cube.GetZMinusFaceProperty().SetColor(0.35, 0.55, 0.85)  # I 蓝

    cube.GetCubeProperty().SetColor(0.25, 0.25, 0.25)

    # ── OrientationMarkerWidget 固定在右下角 ─────────────────────────────────
    marker_widget = vtk.vtkOrientationMarkerWidget()
    marker_widget.SetOrientationMarker(cube)
    marker_widget.SetInteractor(interactor)
    marker_widget.SetViewport(0.75, 0.0, 1.0, 0.25)
    marker_widget.EnabledOn()
    marker_widget.InteractiveOff()   # 固定，不可拖动

    # ── 点击面切换视角 ────────────────────────────────────────────────────────
    _VIEW_PRESETS = {
        "L": ((1, 0, 0),   (0, 0, 1)),   # 从左看 → 相机在 +X
        "R": ((-1, 0, 0),  (0, 0, 1)),   # 从右看 → 相机在 -X
        "A": ((0, 1, 0),   (0, 0, 1)),   # 从前看 → 相机在 +Y
        "P": ((0, -1, 0),  (0, 0, 1)),   # 从后看 → 相机在 -Y
        "S": ((0, 0, -1),  (0, 1, 0)),   # 从上看 → 相机在 -Z
        "I": ((0, 0, 1),   (0, -1, 0)),  # 从下看 → 相机在 +Z
    }

    def _snap_camera(renderer, rw, face):
        cam_dir, view_up = _VIEW_PRESETS[face]
        camera = renderer.GetActiveCamera()
        focal  = camera.GetFocalPoint()
        dist   = camera.GetDistance()
        camera.SetPosition(
            focal[0] + cam_dir[0] * dist,
            focal[1] + cam_dir[1] * dist,
            focal[2] + cam_dir[2] * dist,
        )
        camera.SetViewUp(*view_up)
        renderer.ResetCameraClippingRange()
        rw.Render()

    def _on_left_button_press(obj, event):
        try:
            x, y = obj.GetEventPosition()
            renderers = obj.GetRenderWindow().GetRenderers()
            renderers.InitTraversal()
            main_renderer = renderers.GetNextItem()

            picker = vtk.vtkCellPicker()
            picker.SetTolerance(0.005)
            picker.Pick(x, y, 0, main_renderer)

            actor = picker.GetActor()
            if actor is not None:
                normal = picker.GetPickNormal()
                abs_n  = [abs(normal[i]) for i in range(3)]
                max_i  = abs_n.index(max(abs_n))
                sign   = 1 if normal[max_i] > 0 else -1
                face_map = {
                    (0, 1): "L", (0, -1): "R",
                    (1, 1): "P", (1, -1): "A",
                    (2, 1): "S", (2, -1): "I",
                }
                face = face_map.get((max_i, sign))
                if face:
                    _snap_camera(main_renderer, obj.GetRenderWindow(), face)
        except Exception:
            pass

    interactor.AddObserver("LeftButtonPressEvent", _on_left_button_press, 1.0)
    return marker_widget


class QtOrthoViewer:

    def __init__(self, baseModelClass: BaseModel, widget, label):
        super(QtOrthoViewer, self).__init__()

        # self.orientation = orientation
        # print("self.orientation:",self.orientation)
        # self.widget = widget
        self.label = label
        self.state_store = get_state_store()
        logger.debug("Initialize QtOrthoViewer with label %s", self.label)

        self.current_slice = 0
        self.min_slice = 0
        self.max_slice = 0
        self.labelsPositions = [
            [0.05, 0.5],
            [0.95, 0.5],
            [0.5, 0.05],
            [0.5, 0.9]
        ]

        # # Image Window Level
        # self.imageWindowLevel = baseModelClass.imageWindowLevel
        #
        # # Image Shift Scale
        # self.imageShiftScale = baseModelClass.imageShiftScale

        # Reader
        self.reader = baseModelClass.imageReader

        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)

        self.widget = QVTKRenderWindowInteractor(self.frame)

        self.renderer = vtk.vtkRenderer()

        self.renderWindow = self.widget.GetRenderWindow()
        self.renderWindow.SetMultiSamples(0)
        self.renderWindow.AddRenderer(self.renderer)

        # Render Window Interactor
        self.renderWindowInteractor = self.widget.GetRenderWindow().GetInteractor()

        # Interactor Style Image and Events
        # self.interactorStyleImage = vtk.vtkInteractorStyleImage()
        # self.interactorStyleImage.SetInteractor(self.renderWindowInteractor)
        # self.interactorStyleImage.SetInteractionModeToImageSlicing()
        # self.renderWindowInteractor.SetInteractorStyle(self.interactorStyleImage)

        # Picker
        self.picker = baseModelClass.picker

        # ImageSliceViewer
        self.viewer = vtk.vtkResliceImageViewer()

        # ResliceCursorWidget
        self.resliceCursorWidget = self.viewer.GetResliceCursorWidget()

        # ResliceCurosr
        self.resliceCursor = self.viewer.GetResliceCursor()

        # Camera
        self.camera = self.viewer.GetRenderer().GetActiveCamera()
        # self.camera.SetParallelScale(80)
        # self.focalPoint = self.camera.GetFocalPoint()
        # self.position = self.camera.GetPosition()
        # print("focalPoint:",self.focalPoint)
        # print("position:",self.position)

        # imageView
        self.imageView = vtk.vtkImageViewer2()

        # Slider
        self.slider = QtWidgets.QSlider()
        self.slider.setOrientation(QtCore.Qt.Vertical)

        # Slider label
        self.slider_label = QtWidgets.QLabel()
        self.slider_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        if self.label == "3D Viewer":
            self.type = "Volume"
            self.volume()
        else:
            self.imageView.SetInputData(self.reader.GetOutput())
            self.imageView.SetupInteractor(self.widget)
            self.imageView.SetRenderWindow(self.widget.GetRenderWindow())
            if self.label == "Axial":
                self.type = "XY"
                self.imageView.SetSliceOrientationToXY()
            elif self.label == "Sagittal":
                self.type = "YZ"
                self.imageView.SetSliceOrientationToYZ()
            elif self.label == "Coronal":
                self.type = "XZ"
                self.imageView.SetSliceOrientationToXZ()
            self.imageView.Render()
        logger.debug("QtOrthoViewer type set to %s", self.type)

        # 播放控制器 & 工具栏（仅切片视图）
        if self.label != "3D Viewer":
            self.playback_controller = PlaybackController(
                viewer_getter=lambda: self.viewer,
                slider=self.slider,
                label=self.slider_label,
                view_id=self.type,
            )
            self.playback_bar = PlaybackBar(self.widget, self.playback_controller)
            self.slider.valueChanged.connect(self.playback_controller.on_slider_changed)

            # 伪彩条（叠加在 renderer 右侧）
            self.pseudo_color_bar = PseudoColorBar(self.viewer.GetRenderer())
            self.playback_bar.set_pseudo_color_bar(self.pseudo_color_bar)

            # 标尺（底部，随缩放更新）
            self.scale_bar = ScaleBar(self.viewer.GetRenderer())
            self.scale_bar.set_visible(False)
            self.playback_bar.set_scale_bar(self.scale_bar)

            # 方位标识
            from src.widgets.OrientationMarkerWidget import OrientationMarker
            self.orientation_marker = OrientationMarker(self.viewer.GetRenderer(), self.type)
            self.orientation_marker.set_visible(False)
            self.playback_bar.set_orientation_marker(self.orientation_marker)
        else:
            self.playback_controller = None
            self.playback_bar = None
            self.pseudo_color_bar = None
            self.scale_bar = None
            self.orientation_marker = None

    # def update_viewer(self):
    #     type = None
    #     if self.label == "Axial":
    #         type = "XY"
    #         self.imageView.SetSliceOrientationToXY()
    #     elif self.label == "Sagittal":
    #         type = "YZ"
    #         self.imageView.SetSliceOrientationToYZ()
    #     elif self.label == "Coronal":
    #         type = "XZ"
    #         self.imageView.SetSliceOrientationToXZ()
    #     self.imageView.Render()
    #     return type

    # def update_viewer(self, viewer, vtkWidget, label, verticalSlider, id):
    #     print("id_type:", id)
    #     viewer.SetInputData(self.reader.GetOutput())
    #     viewer.SetupInteractor(vtkWidget)
    #     viewer.SetRenderWindow(vtkWidget.GetRenderWindow())
    #     if id == "XY":
    #         viewer.SetSliceOrientationToXY()
    #     elif id == "YZ":
    #         viewer.SetSliceOrientationToYZ()
    #         transform_YZ = vtk.vtkTransform()
    #         transform_YZ.Translate(self.center0, self.center1, self.center2)
    #         transform_YZ.RotateX(180)
    #         transform_YZ.RotateZ(180)
    #         transform_YZ.Translate(-self.center0, -self.center1, -self.center2)
    #         viewer.GetImageActor().SetUserTransform(transform_YZ)
    #     elif id == "XZ":
    #         viewer.SetSliceOrientationToXZ()
    #         transform_XZ = vtk.vtkTransform()
    #         transform_XZ.Translate(self.center0, self.center1, self.center2)
    #         transform_XZ.RotateY(180)
    #         transform_XZ.RotateZ(180)
    #         transform_XZ.Translate(-self.center0, -self.center1, -self.center2)
    #         viewer.GetImageActor().SetUserTransform(transform_XZ)
    #     viewer.Render()
    #
    #     camera = viewer.GetRenderer().GetActiveCamera()
    #     camera.ParallelProjectionOn()
    #     camera.SetParallelScale(80)
    #     focalPoint = camera.GetFocalPoint()
    #     position = camera.GetPosition()
    #
    #     viewer.SliceScrollOnMouseWheelOff()
    #     viewer.UpdateDisplayExtent()
    #     viewer.Render()
    #
    #     wheelforward = MouseWheelForward(viewer, label, verticalSlider, id)
    #     wheelbackward = MouseWheelBackWard(viewer, label, verticalSlider, id)
    #     viewer_InteractorStyle = viewer.GetInteractorStyle()
    #     viewer_InteractorStyle.AddObserver("MouseWheelForwardEvent", wheelforward)
    #     viewer_InteractorStyle.AddObserver("MouseWheelBackwardEvent", wheelbackward)
    #
    #     value = viewer.GetSlice()
    #     maxSlice = viewer.GetSliceMax()
    #     verticalSlider.setMaximum(maxSlice)
    #     verticalSlider.setMinimum(0)
    #     verticalSlider.setSingleStep(1)
    #     verticalSlider.setValue(value)
    #     label.setText("Slice %d/%d" % (verticalSlider.value(), maxSlice))
    #     viewer.Render()
    #
    #     return focalPoint, position


    def volume(self):
        self.renderer.SetBackground(0.5, 0.5, 0.5)

        if not self.state_store.get("file", "file_is_empty"):
            # 创建体绘制映射器
            volumeMapper = vtk.vtkGPUVolumeRayCastMapper()  # 提高渲染性能
            volumeMapper.SetInputConnection(self.reader.GetOutputPort())

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
            self.renderer.SetBackground(0.5, 0.5, 0.5)
            self.renderer.AddVolume(volume_cbct)
            self.renderer.ResetCamera()
            self.widget.GetRenderWindow().AddRenderer(self.renderer)
            VolumeRender.volume_cbct = volume_cbct
        else:
            VolumeRender.volume_cbct = None

        style = vtk.vtkInteractorStyleTrackballCamera()
        style.SetDefaultRenderer(self.renderer)
        style.EnabledOn()
        self.renderWindowInteractor.SetInteractorStyle(style)

        # ── 解剖方位正方体（替代坐标轴）────────────────────────────────────
        self._orientation_cube_widget = _build_orientation_cube(
            self.renderWindowInteractor
        )

        self.renderer.ResetCamera()
        self.widget.Render()
        self.renderWindowInteractor.Initialize()
