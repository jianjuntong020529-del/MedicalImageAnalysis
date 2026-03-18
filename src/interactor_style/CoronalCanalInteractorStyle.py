# -*- coding: utf-8 -*-
"""冠状面下颌管标注交互样式"""
import logging
import vtk
from src.model.CoronalCanalAnnotationModel import CoronalCanalAnnotationModel, AnnotationPoint
from src.constant.CoronalCanalConstant import CoronalCanalConstant


class CoronalCanalLeftButtonPressEvent:
    """冠状面下颌管标注鼠标左键点击事件处理"""

    def __init__(self, picker, viewer, annotation_model: CoronalCanalAnnotationModel, visualization_manager, update_callback=None):
        self.picker = picker
        self.viewer = viewer
        self.annotation_model = annotation_model
        self.visualization_manager = visualization_manager  # 添加可视化管理器引用
        self.update_callback = update_callback  # 更新UI的回调函数

        # 获取viewer相关对象
        self.actor = self.viewer.GetImageActor()
        self.interactor = self.viewer.GetRenderWindow().GetInteractor()
        self.renderer = self.viewer.GetRenderer()
        self.image = self.viewer.GetInput()

        # 获取图像信息
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.dimensions = self.image.GetDimensions()
        logging.info(f"Dimensions:{self.dimensions}")

    def __call__(self, caller, event):
        """处理鼠标左键点击事件"""
        # 执行拾取
        self.picker.AddPickList(self.actor)
        self.picker.SetTolerance(0.01)
        mouse_pos = self.interactor.GetEventPosition()
        logging.info(f"position：{mouse_pos}")

        # XZ视图：屏幕X对应世界X，屏幕Y对应世界Z，Y轴垂直于屏幕
        self.picker.Pick(mouse_pos[0], mouse_pos[1], 0, self.renderer)

        # 获取拾取位置（世界坐标）
        pick_position = self.picker.GetPickPosition()
        logging.info(f"pick_position：{pick_position}")

        # 获取当前切片索引（直接从viewer获取，确保一致性）
        current_slice = self.viewer.GetSlice()
        logging.info(f"当前切片索引: {current_slice}")

        # 检查坐标是否在有效范围内
        image_x = int((pick_position[0] - self.origin[0]) / self.spacing[0])
        image_z = int((pick_position[2] - self.origin[2]) / self.spacing[2])
        
        if (image_x < 0 or image_x >= self.dimensions[0] or
            image_z < 0 or image_z >= self.dimensions[2]):
            logging.info(f"坐标超出图像范围: ({image_x}, {current_slice}, {image_z}), 有效范围: {self.dimensions}")
            return

        # 添加标注点到模型（使用当前切片索引）
        annotation_point = self.annotation_model.add_point(
            x=pick_position[0],
            y=pick_position[1],
            z=pick_position[2],
            slice_index=current_slice
        )

        # 立即为当前切片创建可视化
        self.visualization_manager._create_point_visual(annotation_point)

        # 更新显示
        self.viewer.Render()
        self.viewer.UpdateDisplayExtent()

        # 调用更新回调
        if self.update_callback:
            self.update_callback()


class CoronalCanalVisualizationManager:
    """冠状面下颌管标注可视化管理器"""

    def __init__(self, viewer, annotation_model: CoronalCanalAnnotationModel):
        self.viewer = viewer
        self.annotation_model = annotation_model
        self.renderer = self.viewer.GetRenderer()
        self.point_actors = {}  # 存储点ID到actor的映射

    def update_visualization_for_slice(self, slice_index: int):
        """更新指定切片的可视化"""
        # 清除当前显示的所有标注点
        self.clear_all_visuals()

        # 获取当前切片的标注点
        points = self.annotation_model.get_points_for_slice(slice_index)
        logging.debug(f"更新切片 {slice_index} 的可视化，找到 {len(points)} 个标注点")

        # 为每个点创建可视化
        for point in points:
            self._create_point_visual(point)

        # 更新显示
        self.viewer.Render()
        self.viewer.UpdateDisplayExtent()

    def clear_all_visuals(self):
        """清除所有可视化对象"""
        for point_id, actor in self.point_actors.items():
            self.renderer.RemoveActor(actor)
        self.point_actors.clear()

    def refresh_all_visuals(self):
        """刷新所有可视化对象"""
        current_slice = self.viewer.GetSlice()
        self.update_visualization_for_slice(current_slice)

    def _create_point_visual(self, point: AnnotationPoint):
        """为单个点创建可视化
        
        Args:
            point: 标注点对象
        """
        # 创建正方形标记
        square = vtk.vtkPolyData()
        
        # 定义正方形的四个顶点
        # 对于冠状面（XZ视图），正方形应该在XZ平面上
        points = vtk.vtkPoints()
        size = CoronalCanalConstant.ANNOTATION_POINT_SIZE

        # 获取图像信息来计算正确的Y坐标
        image = self.viewer.GetInput()
        origin = image.GetOrigin()
        spacing = image.GetSpacing()
        dimensions = image.GetDimensions()

        # 计算世界坐标中的Y位置
        # 对于XZ视图，Y坐标应该对应切片位置
        world_y = origin[1] + point.slice_index * spacing[1]

        # 在XZ平面上创建正方形（Y坐标固定）
        points.InsertNextPoint(point.x - size, world_y, point.z + size)
        points.InsertNextPoint(point.x + size, world_y, point.z + size)
        points.InsertNextPoint(point.x + size, world_y, point.z - size)
        points.InsertNextPoint(point.x - size, world_y, point.z - size)

        # 创建多边形
        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(4)
        for i in range(4):
            polygon.GetPointIds().SetId(i, i)

        # 创建单元数组
        cells = vtk.vtkCellArray()
        cells.InsertNextCell(polygon)

        # 设置几何数据
        square.SetPoints(points)
        square.SetPolys(cells)

        # 创建映射器
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(square)

        # 创建演员
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # 设置颜色
        color = self.annotation_model.get_canal_color(point.canal_type)
        rgb = self._hex_to_rgb(color)
        actor.GetProperty().SetColor(rgb[0], rgb[1], rgb[2])

        # 添加到渲染器
        self.renderer.AddActor(actor)

        # 存储actor引用
        point_id = id(point)
        self.point_actors[point_id] = actor

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return r, g, b