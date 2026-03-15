import vtk


def volume(self):
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
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.5, 0.5, 0.5)
    renderer.AddVolume(volume_cbct)
    renderer.ResetCamera()
    self.vtkWidget.GetRenderWindow().AddRenderer(renderer)

    style = vtk.vtkInteractorStyleTrackballCamera()  # 交互器样式的一种，该样式下，用户是通过控制相机对物体作旋转、放大、缩小等操作
    style.SetDefaultRenderer(renderer)
    style.EnabledOn()
    self.iren.SetInteractorStyle(style)
    # ==================添加一个三维坐标指示=======================================
    axesActor = vtk.vtkAxesActor()
    axes = vtk.vtkOrientationMarkerWidget()
    axes.SetOrientationMarker(axesActor)
    axes.SetInteractor(self.iren)
    axes.EnabledOn()
    axes.SetEnabled(1)
    axes.InteractiveOff()
    renderer.ResetCamera()
    self.vtkWidget.Render()
    self.iren.Initialize()