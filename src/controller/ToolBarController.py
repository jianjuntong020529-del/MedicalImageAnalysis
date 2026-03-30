# -*- coding: utf-8 -*-
# @Time    : 2024/10/16 14:02
#
# @Author  : Jianjun Tong

from PyQt5.QtCore import Qt

from src.constant.ParamConstant import ParamConstant
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.BaseModel import BaseModel
from src.model.ToolBarEnableModel import ToolBarEnable
from src.service.ToolBarService import ToolBarService
from src.utils.globalVariables import *
from src.widgets.ToolBarWidget import ToolBarManager


class ToolBarController(ToolBarManager):
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel, QMainWindow):
        super(ToolBarController, self).__init__()

        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.QMainWindow = QMainWindow
        # 初始化工具栏组件布局
        self.init_toolBar()
        # 调用工具栏方法
        self.toolBarService = ToolBarService(self.baseModelClass, self.viewModel)

        # 状态栏工具槽函数
        self.action_ruler.triggered.connect(self.on_action_ruler)
        self.action_paint.triggered.connect(self.on_action_paint)
        self.action_polyline.triggered.connect(self.on_action_polyline)
        self.action_angle.triggered.connect(self.on_action_angle)
        self.action_pixel.triggered.connect(self.on_action_pixel)
        self.action_crosshair.triggered.connect(self.on_action_crosshair)
        self.action_reset.triggered.connect(self.on_action_reset)
        self.action_dragging_image.triggered.connect(self.on_action_dragging_image)
        self.action_get_roi.triggered.connect(self.on_action_get_roi)
        self.action_view_layout_toolbar.triggered.connect(self.on_action_view_layout_toolbar)
        self.action_rect_roi.triggered.connect(self.on_action_rect_roi)
        self.action_ellipse_roi.triggered.connect(self.on_action_ellipse_roi)
        self.action_clear_all_annotations.triggered.connect(self.on_action_clear_all_annotations)
        # self.lineedit_Subjectname.textChanged[str].connect(self.lineedit_Subjectname_change_Func)  # 槽函数绑定

    # 直尺测量功能
    def on_action_ruler(self):
        if getFileIsEmpty():
            print("未导入文件，不能使用直尺功能")
            self.action_ruler.setChecked(False)
            return
        if not ToolBarEnable.ruler_enable:
            # 清除分割模型的标注
            self.toolBarService.disable_point_action()
            self.toolBarService.disable_label_box_action()
            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)

            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)

            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)

            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)

            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)

            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)

            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)

            self.toolBarService.on_action_ruler()
        else:
            self.toolBarService.clear_ruler()
            self.action_ruler.setChecked(False)

    # 画笔标注功能
    def on_action_paint(self):
        if getFileIsEmpty():
            print("未导入文件，不能使用画笔功能")
            self.action_paint.setChecked(False)
            return
        if not ToolBarEnable.paint_enable:
            # 清除分割模型的标注
            self.toolBarService.disable_point_action()
            self.toolBarService.disable_label_box_action()
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)

            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)

            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)

            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)

            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)

            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)

            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)

            self.toolBarService.on_action_paint()
        else:
            self.toolBarService.clear_paint()
            self.action_paint.setChecked(False)

    # 折线标注功能
    def on_action_polyline(self):
        if getFileIsEmpty():
            print("未导入文件，不能使用折线标注功能")
            self.action_polyline.setChecked(False)
            return
        if not ToolBarEnable.polyline_enable:
            # 清除分割模型的标注
            self.toolBarService.disable_point_action()
            self.toolBarService.disable_label_box_action()
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)

            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)

            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)

            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)

            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)

            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)

            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)

            self.toolBarService.on_action_polyline()
        else:
            self.toolBarService.clear_polyline()
            self.action_polyline.setChecked(False)

    # 角度测量功能
    def on_action_angle(self):
        if getFileIsEmpty():
            print("未导入文件，不能使用角度测量工具")
            self.action_angle.setChecked(False)
            return
        if not ToolBarEnable.angle_enable:
            # 清除分割模型的标注
            self.toolBarService.disable_point_action()
            self.toolBarService.disable_label_box_action()
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)

            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)

            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)

            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)

            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)

            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)

            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)

            self.toolBarService.on_action_angle()
        else:
            self.toolBarService.clear_angle()
            self.action_angle.setChecked(False)

    # 骨密度显示 HU
    def on_action_pixel(self):
        if getFileIsEmpty():
            print("未导入文件，不能使用骨密度功能")
            self.action_pixel.setChecked(False)
            return
        if not ToolBarEnable.pixel_enable:
            # 清除分割模型的标注
            self.toolBarService.disable_point_action()
            self.toolBarService.disable_label_box_action()
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)

            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)

            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)

            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)

            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)

            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)

            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)

            self.toolBarService.on_action_pixel()
        else:
            self.toolBarService.clear_pixel()
            self.action_pixel.setChecked(False)

    # 复位功能
    def on_action_reset(self):
        if getFileIsEmpty():
            print("未导入文件，不能使用复位功能")
            self.action_reset.setChecked(False)
            return
        print("开始复位")
        self.toolBarService.on_action_reset()

    # 同步定位功能
    def on_action_crosshair(self):
        if getFileIsEmpty():
            print("未导入文件，不能使用十字定位功能")
            self.action_crosshair.setChecked(False)
            return
        if not ToolBarEnable.crosshair_enable:
            # 清除分割模型的标注
            self.toolBarService.disable_point_action()
            self.toolBarService.disable_label_box_action()
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)

            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)

            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)

            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)

            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)

            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)

            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)

            self.toolBarService.on_action_crosshair()
        else:
            self.toolBarService.clear_crosshair()
            self.action_crosshair.setChecked(False)

    def on_action_dragging_image(self):
        if getFileIsEmpty():
            print("未导入文件")
            self.action_dragging_image.setChecked(False)
            return
        if not ToolBarEnable.dragging_enable:
            self.QMainWindow.setCursor(Qt.SizeAllCursor)
            # 清除分割模型的标注
            self.toolBarService.disable_point_action()
            self.toolBarService.disable_label_box_action()
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)

            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)

            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)

            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)

            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)

            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)

            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)

            self.toolBarService.on_action_dragging_image()
        else:
            self.QMainWindow.setCursor(Qt.ArrowCursor)
            self.toolBarService.clear_dragging_image()
            self.action_dragging_image.setChecked(False)

    def on_action_get_roi(self):
        if getFileIsEmpty():
            print("文件未导入")
            self.action_get_roi.setChecked(False)
            return
        if not ToolBarEnable.roi_enable:
            # 清除分割模型的标注
            self.toolBarService.disable_point_action()
            self.toolBarService.disable_label_box_action()
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)

            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)

            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)

            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)

            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)

            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)

            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)

            self.toolBarService.on_action_get_roi()
        else:

            self.toolBarService.clear_get_roi()
            self.action_get_roi.setChecked(False)

    def on_action_view_layout_toolbar(self):
        """点击工具栏视图布局按钮，弹出布局选择面板"""
        from src.model.ToolBarWidgetModel import ToolBarWidget
        if ToolBarWidget.view_layout_widget is not None:
            ToolBarWidget.view_layout_widget.show_panel()

    def on_action_rect_roi(self):
        if getFileIsEmpty():
            self.action_rect_roi.setChecked(False)
            return
        if not ToolBarEnable.rect_roi_enable:
            # 关闭其他互斥工具
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)
            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)
            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)
            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)
            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)
            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)
            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)
            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)
            if ToolBarEnable.ellipse_roi_enable:
                self.toolBarService.clear_ellipse_roi()
                self.action_ellipse_roi.setChecked(False)
            self.toolBarService.on_action_rect_roi()
        else:
            self.toolBarService.clear_rect_roi()
            self.action_rect_roi.setChecked(False)

    def on_action_ellipse_roi(self):
        if getFileIsEmpty():
            self.action_ellipse_roi.setChecked(False)
            return
        if not ToolBarEnable.ellipse_roi_enable:
            # 关闭其他互斥工具
            if ToolBarEnable.ruler_enable:
                self.toolBarService.clear_ruler()
                self.action_ruler.setChecked(False)
            if ToolBarEnable.paint_enable:
                self.toolBarService.clear_paint()
                self.action_paint.setChecked(False)
            if ToolBarEnable.polyline_enable:
                self.toolBarService.clear_polyline()
                self.action_polyline.setChecked(False)
            if ToolBarEnable.angle_enable:
                self.toolBarService.clear_angle()
                self.action_angle.setChecked(False)
            if ToolBarEnable.pixel_enable:
                self.toolBarService.clear_pixel()
                self.action_pixel.setChecked(False)
            if ToolBarEnable.crosshair_enable:
                self.toolBarService.clear_crosshair()
                self.action_crosshair.setChecked(False)
            if ToolBarEnable.dragging_enable:
                self.QMainWindow.setCursor(Qt.ArrowCursor)
                self.toolBarService.clear_dragging_image()
                self.action_dragging_image.setChecked(False)
            if ToolBarEnable.roi_enable:
                self.toolBarService.clear_get_roi()
                self.action_get_roi.setChecked(False)
            if ToolBarEnable.rect_roi_enable:
                self.toolBarService.clear_rect_roi()
                self.action_rect_roi.setChecked(False)
            self.toolBarService.on_action_ellipse_roi()
        else:
            self.toolBarService.clear_ellipse_roi()
            self.action_ellipse_roi.setChecked(False)

    def on_action_clear_all_annotations(self):
        """清除所有矩形和椭圆标注"""
        self.toolBarService.clear_all_annotations()
        self.action_rect_roi.setChecked(False)
        self.action_ellipse_roi.setChecked(False)
