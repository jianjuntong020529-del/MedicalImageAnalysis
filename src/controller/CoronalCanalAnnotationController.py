# -*- coding: utf-8 -*-
"""
冠状面下颌管标注控制器
"""
import os
import vtk
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from src.constant.CoronalCanalConstant import CoronalCanalConstant
from src.model.BaseModel import BaseModel
from src.model.CoronalCanalAnnotationModel import CoronalCanalAnnotationModel
from src.ui.LoadCanalSegWindow import LoadCanalSegWindow
from src.widgets.ContrastWidget import Contrast
from src.widgets.CoronalCanalAnnotationWidget import CoronalCanalAnnotationWidget
from src.interactor_style.CoronalCanalInteractorStyle import (
    CoronalCanalLeftButtonPressEvent, 
    CoronalCanalVisualizationManager
)
from src.utils.logger import get_logger
from src.widgets.QtCoronalViewerWidget import CoronalViewer

logger = get_logger(__name__)


class CoronalCanalAnnotationController(CoronalCanalAnnotationWidget):
    """冠状面下颌管标注控制器"""
    
    def __init__(self, baseModelClass: BaseModel, coronalViewer: CoronalViewer, contrast: Contrast):
        super(CoronalCanalAnnotationController, self).__init__()
        
        # 模型和视图
        self.baseModelClass = baseModelClass
        self.coronalViewer = coronalViewer
        self.contrast = contrast

        # 初始化组件
        self.init_widget()

        # 获取冠状面视图 - 现在接收独立的冠状面视图
        self.coronal_viewer = coronalViewer.viewer
        self.coronal_slider = coronalViewer.slider

        # 标注数据模型
        self.annotation_model = CoronalCanalAnnotationModel()

        # 可视化管理器
        self.visualization_manager = CoronalCanalVisualizationManager(
            self.coronal_viewer,
            self.annotation_model
        )

        # 交互事件处理器
        self.left_button_event = None

        # 初始化状态
        self.paint_enabled = False

        # 连接信号槽
        self._connect_signals()

        logger.info("冠状面下颌管标注控制器初始化完成")

    def _connect_signals(self):
        """连接信号槽"""
        # 按钮事件
        self.contrast.window_level_slider.valueChanged.connect(self.window_level_slider_valuechange)
        self.contrast.window_width_slider.valueChanged.connect(self.window_width_slider_valuechange)
        self.coronalViewer.slider.valueChanged.connect(self.valuechange)

        self.pushButton_paint.clicked.connect(self.toggle_paint_mode)
        self.pushButton_clear.clicked.connect(self.clear_all_annotations)
        self.pushButton_undo.clicked.connect(self.undo_annotation)
        self.pushButton_redo.clicked.connect(self.redo_annotation)
        self.pushButton_load.clicked.connect(self.load_annotations)
        self.pushButton_save.clicked.connect(self.save_annotations)

        # 下颌管类型选择
        self.canal_type_combobox.currentIndexChanged.connect(self.on_canal_type_changed)
        self.pushButton_setartSeg.clicked.connect(self.segmentation)
        self.pushButton_loadSegResult.clicked.connect(self.load_canal_segmentation_result)

    def window_level_slider_valuechange(self):
        self.viewer_XZ = self.coronalViewer.viewer
        self.viewer_XZ.SetColorLevel(self.contrast.window_level_slider.value())
        self.viewer_XZ.SetColorWindow(self.contrast.window_width_slider.value())
        self.viewer_XZ.Render()

    def window_width_slider_valuechange(self):
        self.viewer_XZ = self.coronalViewer.viewer
        self.viewer_XZ.SetColorLevel(self.contrast.window_level_slider.value())
        self.viewer_XZ.SetColorWindow(self.contrast.window_width_slider.value())
        self.viewer_XZ.Render()

    def valuechange(self):
        viewer = self.coronalViewer.viewer
        verticalSlider = self.coronalViewer.slider
        label = self.coronalViewer.slider_label

        value = verticalSlider.value()
        viewer.SetSlice(value)
        self.visualization_manager.update_visualization_for_slice(value)
        viewer.UpdateDisplayExtent()
        viewer.Render()
        label.setText("Slice %d/%d" % (viewer.GetSlice(), viewer.GetSliceMax()))

    def segmentation(self):
        print("执行下颌管分割")

    def load_canal_segmentation_result(self):
        print("load cancal segmentation result")
        self.load_calal_seg_window = LoadCanalSegWindow(self.baseModelClass)
        self.load_calal_seg_window.show()
        self.load_calal_seg_window.LoadSTL()


    def toggle_paint_mode(self):
        """切换标注模式"""
        if not self.paint_enabled:
            self._start_paint_mode()
        else:
            self._stop_paint_mode()

    def _start_paint_mode(self):
        """开始标注模式"""
        logger.info("开始冠状面下颌管标注")

        # 创建拾取器
        picker = vtk.vtkPointPicker()
        picker.PickFromListOn()

        # 创建左键点击事件处理器，传入可视化管理器
        self.left_button_event = CoronalCanalLeftButtonPressEvent(
            picker,
            self.coronalViewer.viewer,
            self.annotation_model,
            self.visualization_manager,  # 传入可视化管理器
            self.update_ui_display
        )

        # 获取交互样式并添加事件监听
        interactor_style = self.coronal_viewer.GetInteractorStyle()
        interactor_style.AddObserver("LeftButtonPressEvent", self.left_button_event)

        # 更新UI状态
        self.paint_enabled = True
        self.set_paint_enabled(True)

        # 更新显示
        self.coronal_viewer.UpdateDisplayExtent()
        self.coronal_viewer.Render()

    def _stop_paint_mode(self):
        """停止标注模式"""
        logger.info("结束冠状面下颌管标注")

        # 移除事件监听
        if self.left_button_event:
            interactor_style = self.coronal_viewer.GetInteractorStyle()
            interactor_style.RemoveObservers("LeftButtonPressEvent")
            self.left_button_event = None

        # 更新UI状态
        self.paint_enabled = False
        self.set_paint_enabled(False)

    def clear_all_annotations(self):
        """清除所有标注"""
        # 确认对话框
        reply = QMessageBox.question(
            self.widget_canal_annotation,
            "确认清除",
            CoronalCanalConstant.MSG_CLEAR_CONFIRM,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            logger.info("清除所有下颌管标注")

            # 清除数据模型中的标注
            self.annotation_model.clear_all_points()

            # 清除可视化
            self.visualization_manager.clear_all_visuals()

            # 更新UI显示
            self.update_ui_display()

            # 更新视图
            self.coronal_viewer.UpdateDisplayExtent()
            self.coronal_viewer.Render()

    def undo_annotation(self):
        """撤销标注"""
        if self.annotation_model.undo():
            logger.info("撤销下颌管标注")

            # 刷新可视化
            self.visualization_manager.refresh_all_visuals()

            # 更新UI显示
            self.update_ui_display()
        else:
            logger.info("没有可撤销的操作")

    def redo_annotation(self):
        """重做标注"""
        if self.annotation_model.redo():
            logger.info("重做下颌管标注")

            # 刷新可视化
            self.visualization_manager.refresh_all_visuals()

            # 更新UI显示
            self.update_ui_display()
        else:
            logger.info("没有可重做的操作")

    def on_canal_type_changed(self, index):
        """下颌管类型改变事件"""
        self.annotation_model.set_canal_type(index)
        canal_name = self.annotation_model.get_canal_name(index)
        logger.info(f"切换到下颌管类型: {canal_name}")

    def load_annotations(self):
        """加载标注文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.widget_canal_annotation,
            "加载下颌管标注文件",
            "",
            CoronalCanalConstant.ANNOTATION_FILE_FILTER
        )

        if file_path and os.path.exists(file_path):
            if self.annotation_model.load_from_file(file_path):
                logger.info(f"成功加载标注文件: {file_path}")

                # 刷新可视化
                self.visualization_manager.refresh_all_visuals()

                # 更新UI显示
                self.update_ui_display()

                # 显示成功消息
                QMessageBox.information(
                    self.widget_canal_annotation,
                    "加载成功",
                    CoronalCanalConstant.MSG_LOAD_SUCCESS
                )
            else:
                logger.error(f"加载标注文件失败: {file_path}")
                QMessageBox.warning(
                    self.widget_canal_annotation,
                    "加载失败",
                    CoronalCanalConstant.MSG_FILE_NOT_FOUND
                )

    def save_annotations(self):
        """保存标注文件"""
        if not self.annotation_model.annotation_points:
            QMessageBox.information(
                self.widget_canal_annotation,
                "保存提示",
                CoronalCanalConstant.MSG_NO_ANNOTATIONS
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.widget_canal_annotation,
            "保存下颌管标注文件",
            "",
            CoronalCanalConstant.ANNOTATION_FILE_FILTER
        )

        if file_path:
            if self.annotation_model.save_to_file(file_path):
                logger.info(f"成功保存标注文件: {file_path}")
                QMessageBox.information(
                    self.widget_canal_annotation,
                    "保存成功",
                    CoronalCanalConstant.MSG_SAVE_SUCCESS
                )
            else:
                logger.error(f"保存标注文件失败: {file_path}")
                QMessageBox.warning(
                    self.widget_canal_annotation,
                    "保存失败",
                    "保存文件时发生错误，请检查文件路径和权限。"
                )

    def update_ui_display(self):
        """更新UI显示"""
        # 获取点数量统计
        count_info = self.annotation_model.get_point_count()

        # 更新点数量显示
        self.update_point_count_display(
            count_info['left'],
            count_info['right'],
            count_info['total']
        )

        logger.debug(f"更新UI显示 - 左侧: {count_info['left']}, 右侧: {count_info['right']}, 总计: {count_info['total']}")

    def get_annotation_widget(self):
        """获取标注UI组件"""
        return self.widget_canal_annotation