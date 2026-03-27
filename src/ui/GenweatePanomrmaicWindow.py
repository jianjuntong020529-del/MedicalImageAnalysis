import os

import cv2
import numpy as np
import pydicom
from PIL import Image, ImageEnhance

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5 import QtCore, QtGui, QtWidgets
import vtkmodules.all as vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from scipy import interpolate

from src.constant.ParamConstant import ParamConstant
from src.constant.WindowConstant import WindowConstant
from src.interactor_style.PanormaicInteractorStyle import MouseWheelForward, MouseWheelBackWard
from src.model.BaseModel import BaseModel
from src.model.ToolBarWidgetModel import ToolBarWidget
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font
from src.utils.globalVariables import *


class Generate_Panormaic_Widget(QWidget):
    def __init__(self, baseModelClass: BaseModel):
        super().__init__()

        self.baseModelClass = baseModelClass
        self.origin = self.baseModelClass.origin
        self.spacing = self.baseModelClass.spacing
        self.dimensions = self.baseModelClass.imageDimensions

        self.resize(1128, 698)
        self.setStyleSheet('background-color: #1e1e1e;')

        # ----------------系统整体布局-------------------------------------------------------------------
        self.system_layout = QtWidgets.QGridLayout(self)
        self.system_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.system_layout.setObjectName("system_layout")

        self.xy_label_vertical_layout = QtWidgets.QVBoxLayout(self)
        self.xy_label_vertical_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.xy_label_vertical_layout.setObjectName("xy_label_vertical_layout")

        self.xy_verticalSlider_horizontal_layout = QtWidgets.QHBoxLayout()
        self.xy_verticalSlider_horizontal_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.xy_verticalSlider_horizontal_layout.setObjectName("xy_verticalSlider_horizontal_layout")

        # --------------------XY窗口-------------------------------------------------------
        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.type = "XY"
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.xy_verticalSlider_horizontal_layout.addWidget(self.vtkWidget)

        self.reader = self.baseModelClass.imageReader
        # -------------------更新横断面------------------------------------------
        self.viewer = vtk.vtkResliceImageViewer()
        self.viewer.SetInputData(self.reader.GetOutput())
        self.viewer.SetupInteractor(self.vtkWidget)
        self.viewer.SetRenderWindow(self.vtkWidget.GetRenderWindow())
        self.viewer.SetSliceOrientationToXY()
        self.viewer.Render()

        self.camera = self.viewer.GetRenderer().GetActiveCamera()
        self.camera.ParallelProjectionOn()
        self.camera.SetParallelScale(80)

        self.viewer.SetColorLevel(ToolBarWidget.contrast_widget.window_level_slider.value())
        self.viewer.SetColorWindow(ToolBarWidget.contrast_widget.window_width_slider.value())
        self.viewer.SliceScrollOnMouseWheelOff()
        self.viewer.UpdateDisplayExtent()
        self.viewer.Render()
        # ------------------------------------------------------------------------
        self.verticalSlider_XY = QtWidgets.QSlider()
        self.verticalSlider_XY.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_XY.setObjectName("verticalSlider_XY")
        self.xy_verticalSlider_horizontal_layout.addWidget(self.verticalSlider_XY)
        self.system_layout.addLayout(self.xy_verticalSlider_horizontal_layout, 0, 0, 1, 1)

        # label标签的布局设置
        self.label_xy = QtWidgets.QLabel()
        self.label_xy.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_xy.setObjectName("label_xy")
        self.xy_label_vertical_layout.addWidget(self.label_xy)
        self.system_layout.addLayout(self.xy_label_vertical_layout, 1, 0, 1, 1)

        self.maxSlice = self.viewer.GetSliceMax()
        self.verticalSlider_XY.setMaximum(self.maxSlice)
        self.verticalSlider_XY.setMinimum(0)
        self.verticalSlider_XY.setSingleStep(1)
        self.verticalSlider_XY.valueChanged.connect(self.valuechange)

        # 工具栏布局
        self.tool_bar_layout = QtWidgets.QVBoxLayout()
        self.tool_bar_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.tool_bar_layout.setObjectName("tool_bar_layout")

        # ── 深色主题设计 Token ──────────────────────────────────────────────────
        _CARD   = '#2d2d2d'
        _BORDER = '#3a3a3a'
        _HOVER  = '#383838'
        _ACCENT = '#3b82f6'
        _TEXT   = '#e8e8e8'
        _SEC    = '#9ca3af'
        _WHITE  = '#ffffff'
        _FONT   = '"Microsoft YaHei", "PingFang SC", sans-serif'

        _BTN_PRIMARY = f'''
            QPushButton {{
                background: {_ACCENT}; color: {_WHITE}; border: none;
                border-radius: 5px; padding: 6px 12px;
                font-size: 12px; font-weight: 600; font-family: {_FONT};
            }}
            QPushButton:hover {{ background: #2563eb; }}
            QPushButton:pressed {{ background: #1d4ed8; }}
            QPushButton:checked {{ background: #1d4ed8; border: 1px solid #60a5fa; }}
        '''
        _BTN_SECONDARY = f'''
            QPushButton {{
                background: #333; color: {_TEXT}; border: 1px solid {_BORDER};
                border-radius: 5px; padding: 6px 12px;
                font-size: 12px; font-family: {_FONT};
            }}
            QPushButton:hover {{ background: {_HOVER}; color: {_WHITE}; }}
            QPushButton:pressed {{ background: #444; }}
            QPushButton:checked {{ background: #1d4ed8; border-color: {_ACCENT}; color: {_WHITE}; }}
        '''
        _INPUT_STYLE = f'''
            QLineEdit {{
                background: #333; color: {_TEXT}; border: 1px solid {_BORDER};
                border-radius: 4px; padding: 4px 8px;
                font-size: 12px; font-family: {_FONT};
            }}
            QLineEdit:focus {{ border-color: {_ACCENT}; }}
        '''
        _LABEL_KEY = (
            f'font-size: 11px; color: {_SEC}; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )

        self.widget_tool = QtWidgets.QWidget()
        self.widget_tool.setMinimumSize(QtCore.QSize(220, 200))
        self.widget_tool.setMaximumSize(QtCore.QSize(400, 400))
        self.widget_tool.setObjectName("widget_tool")
        self.widget_tool.setStyleSheet(
            f'background: {_CARD}; border-radius: 8px; border: 1px solid {_BORDER};'
        )

        # 阴影
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor as _QColor
        eff = QGraphicsDropShadowEffect(self.widget_tool)
        eff.setBlurRadius(12); eff.setOffset(0, 2)
        eff.setColor(_QColor(0, 0, 0, 60))
        self.widget_tool.setGraphicsEffect(eff)

        self.tool_vertical_layout = QtWidgets.QVBoxLayout(self.widget_tool)
        self.tool_vertical_layout.setContentsMargins(12, 10, 12, 12)
        self.tool_vertical_layout.setSpacing(8)
        self.tool_vertical_layout.setAlignment(QtCore.Qt.AlignTop)
        self.tool_vertical_layout.setObjectName("tool_vertical_layout")

        # ── 标题 ──
        self.title_bool = QtWidgets.QLabel(self.widget_tool)
        self.title_bool.setObjectName("title_tool")
        self.title_bool.setStyleSheet(
            f'font-size: 11px; font-weight: 700; color: {_WHITE};'
            f'letter-spacing: 1px; font-family: {_FONT};'
            f'background: transparent; border: none;'
        )
        self.tool_vertical_layout.addWidget(self.title_bool)

        # 分隔线
        _sep = QtWidgets.QFrame()
        _sep.setFrameShape(QtWidgets.QFrame.HLine)
        _sep.setFixedHeight(1)
        _sep.setStyleSheet(f'background: {_BORDER}; border: none;')
        self.tool_vertical_layout.addWidget(_sep)

        # ── 牙弓厚度输入行 ──
        self.horizontal_layout_input = QtWidgets.QHBoxLayout()
        self.horizontal_layout_input.setObjectName("horizontal_layout_input")
        self.horizontal_layout_input.setSpacing(8)

        self.dental_arch_thickness_label = QtWidgets.QLabel(self.widget_tool)
        self.dental_arch_thickness_label.setObjectName("dental_arch_thickness_label")
        self.dental_arch_thickness_label.setStyleSheet(_LABEL_KEY)
        self.dental_arch_thickness_label.setText(WindowConstant.DENTAL_ARCH_THICKNESS)

        self.dental_arch_thickness = QtWidgets.QLineEdit(self.widget_tool)
        self.dental_arch_thickness.setObjectName("dental_arch_thickness")
        self.dental_arch_thickness.setText(ParamConstant.THICKNESS_VALUE)
        self.dental_arch_thickness.setStyleSheet(_INPUT_STYLE)
        validator = QtGui.QIntValidator()
        self.dental_arch_thickness.setValidator(validator)
        self.dental_arch_thickness.textChanged[str].connect(self.changeThickness)

        self.horizontal_layout_input.addWidget(self.dental_arch_thickness_label)
        self.horizontal_layout_input.addWidget(self.dental_arch_thickness, 1)
        self.tool_vertical_layout.addLayout(self.horizontal_layout_input)

        # ── 标注按钮 ──
        self.pushButton_annotation = QtWidgets.QPushButton(self.widget_tool)
        self.pushButton_annotation.setObjectName("pushButton_annotation")
        self.pushButton_annotation.setCheckable(True)
        self.pushButton_annotation.setAutoExclusive(False)
        self.pushButton_annotation.setStyleSheet(_BTN_PRIMARY)
        self.pushButton_annotation.clicked.connect(self.annotation)
        self.annotation_enable = False
        self.tool_vertical_layout.addWidget(self.pushButton_annotation)

        # ── 保存按钮 ──
        self.pushButton_save = QtWidgets.QPushButton(self.widget_tool)
        self.pushButton_save.setObjectName("pushButton_save")
        self.pushButton_save.setAutoExclusive(False)
        self.pushButton_save.setStyleSheet(_BTN_SECONDARY)
        self.pushButton_save.clicked.connect(self.save)
        self.tool_vertical_layout.addWidget(self.pushButton_save)

        # ── 显示牙弓线按钮 ──
        self.pushButton_show = QtWidgets.QPushButton(self.widget_tool)
        self.pushButton_show.setObjectName("pushButton_show")
        self.pushButton_show.setCheckable(True)
        self.pushButton_show.setAutoExclusive(False)
        self.pushButton_show.setStyleSheet(_BTN_SECONDARY)
        self.pushButton_show.clicked.connect(self.show_dentral_arch_curve)
        self.show_enable = False
        self.tool_vertical_layout.addWidget(self.pushButton_show)

        # ── 生成口腔全景图按钮 ──
        self.pushButton_generate_dentalPanoramic = QtWidgets.QPushButton(self.widget_tool)
        self.pushButton_generate_dentalPanoramic.setObjectName("pushButton_generate_dentalPanoramic")
        self.pushButton_generate_dentalPanoramic.setStyleSheet(_BTN_PRIMARY)
        self.pushButton_generate_dentalPanoramic.clicked.connect(self.generate_dental_panoramic)
        self.tool_vertical_layout.addWidget(self.pushButton_generate_dentalPanoramic)

        self.tool_bar_layout.addWidget(self.widget_tool)
        self.tool_bar_layout.addStretch()

        self.system_layout.addLayout(self.tool_bar_layout, 0, 1, 1, 1)

        self.system_layout.setColumnMinimumWidth(0, 7)
        self.system_layout.setColumnMinimumWidth(1, 2)
        self.system_layout.setColumnStretch(0, 7)
        self.system_layout.setColumnStretch(1, 2)

        self.spline_widget = vtk.vtkSplineWidget()
        self.spline_widget.SetInteractor(self.viewer.GetRenderWindow().GetInteractor())
        self.spline_widget.SetNumberOfHandles(11)
        self.spline_widget.GetHandleProperty().SetPointSize(3)

        wheelforward = MouseWheelForward(self.viewer, self.label_xy, self.verticalSlider_XY,
                                               self.annotation_enable, self.spline_widget)
        wheelbackward = MouseWheelBackWard(self.viewer, self.label_xy, self.verticalSlider_XY,
                                                 self.annotation_enable, self.spline_widget)
        self.viewer_InteractorStyle = self.viewer.GetInteractorStyle()
        self.viewer_InteractorStyle.AddObserver("MouseWheelForwardEvent", wheelforward)
        self.viewer_InteractorStyle.AddObserver("MouseWheelBackwardEvent", wheelbackward)

        self.viewer.UpdateDisplayExtent()
        self.viewer.Render()

        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Widget", WindowConstant.PANORMAIC_WINDOW_TITLE))
        self.label_xy.setText(_translate("Widget", WindowConstant.LABEL_SLICE))
        self.pushButton_annotation.setText(_translate("Widget", WindowConstant.ANNOTATION_BUTTON))
        self.pushButton_save.setText(_translate("Widget", WindowConstant.SAVE_BUTTON))
        self.title_bool.setText(_translate("Widget", WindowConstant.TOOLBAR_TITLE))
        self.pushButton_show.setText(_translate("Widget", WindowConstant.SHOW_DENTAL_ARCH_BUTTON))
        self.pushButton_generate_dentalPanoramic.setText(_translate("Widget", WindowConstant.GENERATE_PANORMAIC_BUTTON))

    def annotation(self):
        if not self.annotation_enable:
            print("牙弓线标注")
            getDentalArchCurvePoint().clear()
            getControlPoints().clear()
            self.picker = vtk.vtkPointPicker()
            self.picker.PickFromListOn()
            self.viewer.SetSlice(getSliceXY())
            self.pushButton_show.setChecked(False)
            print(getSliceXY())
            self.spline_widget.SetHandlePosition(0, 10, 10, getSliceXY())
            self.spline_widget.SetHandlePosition(1, 15, 15, getSliceXY())
            self.spline_widget.SetHandlePosition(2, 25, 25, getSliceXY())
            self.spline_widget.SetHandlePosition(3, 35, 35, getSliceXY())
            self.spline_widget.SetHandlePosition(4, 45, 45, getSliceXY())
            self.spline_widget.SetHandlePosition(5, 55, 55, getSliceXY())
            self.spline_widget.SetHandlePosition(6, 65, 65, getSliceXY())
            self.spline_widget.SetHandlePosition(7, 75, 75, getSliceXY())
            self.spline_widget.SetHandlePosition(8, 85, 85, getSliceXY())
            self.spline_widget.SetHandlePosition(9, 95, 95, getSliceXY())
            self.spline_widget.SetHandlePosition(10, 105, 105, getSliceXY())
            self.spline_widget.On()
            self.viewer.UpdateDisplayExtent()
            self.viewer.Render()
            self.annotation_enable = True
        else:
            self.spline_widget.Off()
            self.annotation_enable = False

    def save(self):
        if not self.annotation_enable:
            return
        getDentalArchCurvePoint().clear()
        getControlPoints().clear()
        setDentalArchThickness(ParamConstant.THICKNESS_VALUE)
        thickness = getDentalArchThickness()
        print("牙弓厚度：", thickness)
        print("打印牙弓曲线的点")
        ployData = vtk.vtkPolyData()
        self.spline_widget.GetPolyData(ployData)
        num_points = ployData.GetNumberOfPoints()
        points = ployData.GetPoints()
        dental_arch_points = []
        for i in range(num_points):
            x, y, z = points.GetPoint(i)
            setDentalArchCurvePoint([x, y, z])
            dental_arch_points.append(
                [x / self.spacing[0] - self.origin[0], self.dimensions[1] - y / self.spacing[1] + self.origin[1], z])
            print(f"Point {i}: ({x}, {y}, {z})")

        dental_arch_points = np.array(dental_arch_points).astype(np.int32)
        # 对像素坐标按X坐标排序
        sorted_skeleton_x = sorted(dental_arch_points, key=lambda x: x[0])
        # 从骨架像素中找到起始点和结束点
        start_point = sorted_skeleton_x[0]  # 假设起始点是第一个找到的骨架像素
        end_point = sorted_skeleton_x[-1]  # 假设结束点是最后一个找到的骨架像素
        mid = (end_point[0] - start_point[0]) / 2
        print("start_point:", start_point)
        print("end_point:", end_point)
        sorted_data = []
        for point in sorted_skeleton_x:
            if point[0] < mid:
                if point[1] <= start_point[1]:
                    sorted_data.append(point)
            else:
                if point[1] <= end_point[1]:
                    sorted_data.append(point)
        sorted_data = np.array(sorted_data)
        sorted_points = sorted(sorted_data, key=lambda x: x[0])

        # 计算X轴上的总长度
        total_length = len(sorted_points)

        spacing = total_length // 10

        x = [i * spacing for i in range(10)]
        for i in x:
            x_cords = sorted_points[i][0]
            y_cords = sorted_points[i][1]
            setControlPoints([x_cords, y_cords])

        setControlPoints([end_point[0], end_point[1]])

        print(getControlPoints())

    def show_dentral_arch_curve(self):
        if not getDentalArchCurvePoint():
            if not self.annotation_enable:
                print("牙弓曲线标注未打开")
                return
            else:
                api = self.generate_panoramic_information()
                if api == QMessageBox.AcceptRole:
                    print("选择了确认")
                    self.save()
                elif api == QMessageBox.RejectRole:
                    print("选择了取消")
                    self.pushButton_show.setChecked(False)
                    return

        if not self.show_enable:
            getSamplePoint().clear()
            thickness = int(getDentalArchThickness())
            control_points = np.array(getControlPoints())
            print(thickness, control_points)

            line1_points, line2_points = get_vertical_lines_points(control_points, sample_points_num=800,
                                                                   arch_width=thickness)
            dental_curve_points = getSamplePoint()
            dicom_z = getDentalArchCurvePoint()[0][2]
            # 创建点集
            self.points1 = vtk.vtkPoints()
            self.points2 = vtk.vtkPoints()
            self.points3 = vtk.vtkPoints()

            for i in range(len(dental_curve_points)):
                points = dental_curve_points[i]
                x = points[0] * self.spacing[0] - self.origin[0]
                y = (self.dimensions[1] - points[1]) * self.spacing[1] - self.origin[1]
                self.points1.InsertNextPoint(x, y, dicom_z)

            for i in range(len(line1_points)):
                point1 = line1_points[i]
                point2 = line2_points[i]
                self.points2.InsertNextPoint(point1[0] * self.spacing[0] + self.origin[0],
                                             (self.dimensions[1] - point1[1]) * self.spacing[1] + self.origin[1],
                                             dicom_z)
                self.points3.InsertNextPoint(point2[0] * self.spacing[0] + self.origin[0],
                                             (self.dimensions[1] - point2[1]) * self.spacing[1] + self.origin[1],
                                             dicom_z)

            # 创建线条
            self.line1 = vtk.vtkPolyLine()
            self.line1.GetPointIds().SetNumberOfIds(len(dental_curve_points))
            for i in range(len(dental_curve_points)):
                self.line1.GetPointIds().SetId(i, i)

            self.line2 = vtk.vtkPolyLine()
            self.line2.GetPointIds().SetNumberOfIds(len(line1_points))
            for i in range(len(line1_points)):
                self.line2.GetPointIds().SetId(i, i)

            self.line3 = vtk.vtkPolyLine()
            self.line3.GetPointIds().SetNumberOfIds(len(line2_points))
            for i in range(len(line2_points)):
                self.line3.GetPointIds().SetId(i, i)

            # 创建单元
            self.cells1 = vtk.vtkCellArray()
            self.cells1.InsertNextCell(self.line1)

            self.cells2 = vtk.vtkCellArray()
            self.cells2.InsertNextCell(self.line2)

            self.cells3 = vtk.vtkCellArray()
            self.cells3.InsertNextCell(self.line3)

            # 创建数据集
            self.polyData1 = vtk.vtkPolyData()
            self.polyData1.SetPoints(self.points1)
            self.polyData1.SetLines(self.cells1)

            self.polyData2 = vtk.vtkPolyData()
            self.polyData2.SetPoints(self.points2)
            self.polyData2.SetLines(self.cells2)

            self.polyData3 = vtk.vtkPolyData()
            self.polyData3.SetPoints(self.points3)
            self.polyData3.SetLines(self.cells3)

            # 创建Mapper和Actor
            self.mapper1 = vtk.vtkPolyDataMapper()
            self.mapper1.SetInputData(self.polyData1)
            self.mapper1.Update()
            self.mapper2 = vtk.vtkPolyDataMapper()
            self.mapper2.SetInputData(self.polyData2)
            self.mapper2.Update()
            self.mapper3 = vtk.vtkPolyDataMapper()
            self.mapper3.SetInputData(self.polyData3)
            self.mapper3.Update()

            self.actor1 = vtk.vtkActor()
            self.actor1.SetMapper(self.mapper1)
            self.actor1.GetProperty().SetColor(1, 1, 1)
            self.actor1.GetProperty().SetLineWidth(3)

            self.actor2 = vtk.vtkActor()
            self.actor2.SetMapper(self.mapper2)
            self.actor2.GetProperty().SetColor(0, 1, 0)
            self.actor2.GetProperty().SetLineWidth(3)

            self.actor3 = vtk.vtkActor()
            self.actor3.SetMapper(self.mapper3)
            self.actor3.GetProperty().SetColor(0, 1, 0)
            self.actor3.GetProperty().SetLineWidth(3)

            self.viewer.SetSlice(int(dicom_z))

            self.ren = self.viewer.GetRenderer()
            self.ren.AddActor(self.actor1)
            self.ren.AddActor(self.actor2)
            self.ren.AddActor(self.actor3)
            self.viewer.GetRenderWindow().GetInteractor().Render()
            self.ren.Render()
            self.viewer.UpdateDisplayExtent()
            self.viewer.Render()

            self.show_enable = True
        else:
            # 删除生成的线条样式
            self.ren.RemoveActor(self.actor1)
            self.ren.RemoveActor(self.actor2)
            self.ren.RemoveActor(self.actor3)
            self.viewer.GetRenderWindow().GetInteractor().Render()
            self.viewer.UpdateDisplayExtent()
            self.viewer.Render()
            self.show_enable = False

    def generate_dental_panoramic(self):
        if not getControlPoints():
            if not self.annotation_enable:
                print("牙弓曲线标注未打开")
                return
            else:
                api = self.generate_panoramic_information()
                if api == QMessageBox.AcceptRole:
                    print("选择了确认")
                    self.save()
                elif api == QMessageBox.RejectRole:
                    print("选择了取消")
                    return
        control_points = np.array(getControlPoints())

        print(control_points)

        Hu, _ = get_dicom(getDirPath())

        thickness = int(getDentalArchThickness())
        sysnetic_curve = generate_Panormaic_MPR(control_points=control_points, ct_cube=Hu, sample_points_num=800,
                                                arch_width=thickness, normal_samples_num=40)

        sysnetic_curve = (sysnetic_curve - sysnetic_curve.min()) * (
                255.0 / (sysnetic_curve.max() - sysnetic_curve.min()))
        sysnetic_curve = sysnetic_curve.astype(np.uint8)

        coronal_volume = cv2.flip(sysnetic_curve, 0)
        contrast_brightness = np.array(coronal_volume)
        # 缩放因子
        scale_factor = 1.5

        # 调整图像大小
        resized_curve = cv2.resize(contrast_brightness, (0, 0), fx=scale_factor, fy=scale_factor)
        cv2.imshow('Panomaic', resized_curve)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def valuechange(self):
        print("value changed")
        value = self.verticalSlider_XY.value()
        setSliceXY(value)
        self.label_xy.setText("Slice %d/%d" % (self.viewer.GetSlice(), self.viewer.GetSliceMax()))
        self.viewer.SetSlice(value)
        self.viewer.UpdateDisplayExtent()
        self.viewer.Render()
    def changeThickness(self):
        ParamConstant.THICKNESS_VALUE = self.dental_arch_thickness.text()
        setDentalArchThickness(ParamConstant.THICKNESS_VALUE)
        print("ParamConstant.THICKNESS_VALUE:", ParamConstant.THICKNESS_VALUE)

    def generate_panoramic_information(self):
        info = QMessageBox()
        info.setIcon(QMessageBox.Information)
        info.setWindowTitle(WindowConstant.IMPLANT_INFO_TITLE)
        info.setText(WindowConstant.GENERATE_PANORMAIC_INFO_TEXT)
        info.setFixedSize(400, 200)
        info.setFont(Font.font2)
        info.addButton(WindowConstant.IMPLANT_INFO_ACCEPT, QMessageBox.AcceptRole)
        info.addButton(WindowConstant.IMPLANT_INFO_REJECT, QMessageBox.RejectRole)
        api = info.exec_()
        return api


def get_vertical_lines_points(control_points, sample_points_num, arch_width):
    x = control_points[:, 0]
    y = control_points[:, 1]
    # 进行三次样条拟合,可以换成其他样条拟合(后续测试改进)
    tck, u = interpolate.splprep([x, y], k=3, s=0)
    # 生成一组等弧长采样点
    unew = np.linspace(0, 1, sample_points_num)
    # 对样条曲线进行等弧长采样
    x_samples, y_samples = interpolate.splev(unew, tck)
    out = interpolate.splev(unew, tck)

    # 生成采样点
    # sample_points = []
    getSamplePoint().clear()
    for i in range(len(out[0])):
        setSamplePoint([int(out[0][i]), int(out[1][i])])
    sample_points = np.array(getSamplePoint())

    # 计算样条曲线上每个点的法向量
    dx, dy = interpolate.splev(unew, tck, der=1)
    norm = np.sqrt(dx ** 2 + dy ** 2)
    nx, ny = dy / norm, -dx / norm

    # 以采样点为中心，沿法向量正负方向绘制一定长度的直线
    scale = arch_width / 2  # 法向量长度为20像素
    line1 = []
    line2 = []
    for i in range(len(sample_points)):
        x0, y0 = sample_points[i, :]
        nx0, ny0 = nx[i], ny[i]
        x1, y1 = x0 + nx0 * scale, y0 + ny0 * scale
        x2, y2 = x0 - nx0 * scale, y0 - ny0 * scale
        line1.append((x1, y1))
        line2.append((x2, y2))
    return line1, line2


def generate_Panormaic_MPR(control_points, ct_cube, sample_points_num, arch_width, normal_samples_num):
    """
    生成弯曲的MPR图像集,并进行均值合成

    Args:
        control_points(numpy): 牙弓曲线上的控制点，注意采样点要按顺序排列 shape=(N, 2),有研究表明最好N=11,但还未实际实验测试
        ct_cube(numpy): shape=(320, 512, 512)
        sample_points_num(int): 800 拟合的牙弓曲线上采样点个数
        arch_width(int): 牙弓厚度,注意这里的牙弓厚度是指的像素值，实际的牙弓厚度=80*0.25
        normal_samples_num(int): 牙弓曲线上每个采样点的法向量直线上的采样点数

    Returns: sysnetic_curve_mean(numpy): shape = (sample_points, 2) 坐标值为ct三维数据相应位置Hu值

    """
    x = control_points[:, 0]
    y = control_points[:, 1]
    # 进行三次样条拟合,可以换成其他样条拟合(后续测试改进)
    tck, u = interpolate.splprep([x, y], k=3, s=0)
    # 生成一组等弧长采样点
    unew = np.linspace(0, 1, sample_points_num)
    # 对样条曲线进行等弧长采样
    x_samples, y_samples = interpolate.splev(unew, tck)
    out = interpolate.splev(unew, tck)

    # 生成采样点
    getSamplePoint().clear()
    for i in range(len(out[0])):
        setSamplePoint([int(out[0][i]), int(out[1][i])])
    sample_points = np.array(getSamplePoint())

    # 计算样条曲线上每个点的法向量
    dx, dy = interpolate.splev(unew, tck, der=1)
    norm = np.sqrt(dx ** 2 + dy ** 2)
    nx, ny = dy / norm, -dx / norm

    # 以采样点为中心，沿法向量正负方向绘制一定长度的直线
    scale = arch_width / 2  # 法向量长度为20像素
    lines = []
    for i in range(len(sample_points)):
        x0, y0 = sample_points[i, :]
        nx0, ny0 = nx[i], ny[i]
        x1, y1 = x0 + nx0 * scale, y0 + ny0 * scale
        x2, y2 = x0 - nx0 * scale, y0 - ny0 * scale
        lines.append([(x1, y1), (x2, y2)])

    # 等距采样每条法向量直线
    normal_sample_points = []
    for line in lines:
        x1, y1 = line[0]
        x2, y2 = line[1]
        x_samples = np.linspace(x1, x2, normal_samples_num, endpoint=True)
        y_samples = np.linspace(y1, y2, normal_samples_num, endpoint=True)
        normal_sample_points.append(list(zip(x_samples, y_samples)))

    normal_sample_points = np.array(normal_sample_points).reshape((-1, 2))

    # 对每条法向量上采样点按照原采样点顺序进行重新排序
    sample_points_total = []
    sample_points_slice = []
    for i in range(normal_samples_num):
        for j in range(sample_points.shape[0]):
            sample_points_slice.append(normal_sample_points[i + j * normal_samples_num])
        sample_points_total.append(sample_points_slice)
        sample_points_slice = []
    sample_points_total = np.array(sample_points_total).astype(np.int32)
    print(sample_points_total.shape)

    sysnetic_curve = []
    for i in range(normal_samples_num):
        # 这里要对每层XY轴旋转90°,否则获得二维坐标和三维数据坐标不对应
        # Opencv图像坐标系以向右为X正,向下为Y正。三维ct数据坐标系在轴状平面上,向右为X正,向上为Y正
        slice_point = sample_points_total[i, :]
        index_max = np.max(slice_point, axis=0)
        if index_max[0] >= ct_cube.shape[2] or index_max[1] >= ct_cube.shape[1]:
            total = []
            for i in range(0, ct_cube.shape[0] if ct_cube.shape[0] < 320 else 320):
                level_pixel = []
                for point in slice_point:
                    if point[0] >= ct_cube.shape[2] or point[1] >= ct_cube.shape[1]:
                        level_pixel.append(0)
                    else:
                        level_pixel.append(ct_cube[i, point[1], point[0]])
                total.append(level_pixel)
            sysnetic_curve.append(np.array(total))
        else:
            curve2line = ct_cube[0:ct_cube.shape[0] if ct_cube.shape[0] < 320 else 320, slice_point[:, 1],
                         slice_point[:, 0]]
            sysnetic_curve.append(curve2line)
    sysnetic_curve = np.array(sysnetic_curve)
    # 单个弯曲的MPR图像集
    # single_curve_MPR = sysnetic_curve[0, :, :]

    # TODO: 这里可以采用非线性合成算法，抑制非感兴趣曲线，提高全景图像对比度
    # 根据X-ray原理,将牙弓曲线上每个采样点的法向量的采样点对应ct数据的Hu求均值
    sysnetic_curve_mean = np.mean(sysnetic_curve, axis=0)
    # sysnetic_curve_mean = np.log(np.mean(np.exp(sysnetic_curve / 4000), 0)) * 1000
    print(sysnetic_curve_mean)
    return sysnetic_curve_mean


def get_dicom(datapath):
    # 用于存储加载的DICOM数据
    slices = []

    for root, dirs, files in os.walk(datapath):
        for file in files:
            if file.lower().endswith(".dcm"):
                dicom_file = os.path.join(root, file)
                dcm = pydicom.dcmread(dicom_file)
                slices.append(dcm)

    # 确保以正确的顺序排序切片
    slices.sort(key=lambda x: float(x.SliceLocation))

    pixel_volume = np.stack([s.pixel_array for s in slices])

    return pixel_volume, slices


def contrastAndbrightness(image_path, contrast, brightness):
    image = Image.open(image_path)
    enh_con = ImageEnhance.Contrast(image)
    image_contrasted = enh_con.enhance(contrast)

    enh_bri = ImageEnhance.Brightness(image_contrasted)
    image_brightened = enh_bri.enhance(brightness)
    return image_brightened
