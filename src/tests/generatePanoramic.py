# -*- coding: utf-8 -*-
import os
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pydicom
import vtkmodules.all as vtk
from PIL import ImageEnhance
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from scipy import interpolate
from scipy.interpolate import CubicSpline, UnivariateSpline, splprep, splev
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


from interactor import MouseWheelForward_child, MouseWheelBackWard_child
from src.utils.globalVariables import getSliceXY

error = vtk.vtkOutputWindow()
error.SetGlobalWarningDisplay(0)  # 关闭vtk报错信息

class Ui_Form(object):
    def setupUi(self, Widget):
        self.thickness_value = "80"

        Widget.setObjectName("Form")
        Widget.resize(1128, 698)

        self.font = QtGui.QFont()
        self.font.setFamily("华文宋体")
        self.font.setPointSize(10)

        self.font2 = QtGui.QFont()
        self.font2.setFamily("华文宋体")
        self.font2.setPointSize(11)

        # ----------------系统整体布局-------------------------------------------------------------------
        self.system_layout = QtWidgets.QGridLayout(Widget)
        self.system_layout.setSpacing(6)
        self.system_layout.setObjectName("system_layout")

        self.xy_label_vertical_layout = QtWidgets.QVBoxLayout()
        self.xy_label_vertical_layout.setSpacing(6)
        self.xy_label_vertical_layout.setObjectName("xy_label_vertical_layout")

        self.xy_verticalSlider_horizontal_layout = QtWidgets.QHBoxLayout()
        self.xy_verticalSlider_horizontal_layout.setSpacing(6)
        self.xy_verticalSlider_horizontal_layout.setObjectName("xy_verticalSlider_horizontal_layout")

        # --------------------XY窗口-------------------------------------------------------
        self.frame = QtWidgets.QFrame(Widget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame_XY")
        self.id_XY = "XY"
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.xy_verticalSlider_horizontal_layout.addWidget(self.vtkWidget)

        # ------------打开横断面窗口数据----------------------------
        self.pathDicomDir = getDirPath()
        self.reader = vtk.vtkDICOMImageReader()
        self.reader.SetDirectoryName(self.pathDicomDir)
        self.reader.Update()
        # -------------------更新横断面------------------------------------------
        self.viewer1 = vtk.vtkImageViewer2()
        self.viewer1.SetInputData(self.reader.GetOutput())
        self.viewer1.SetupInteractor(self.vtkWidget)
        self.viewer1.SetRenderWindow(self.vtkWidget.GetRenderWindow())
        self.viewer1.SetSliceOrientationToXY()
        self.viewer1.Render()
        # ------------------------------------------------------------------------
        self.verticalSlider_XY = QtWidgets.QSlider(Widget)
        self.verticalSlider_XY.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_XY.setObjectName("verticalSlider_XY")
        self.xy_verticalSlider_horizontal_layout.addWidget(self.verticalSlider_XY)
        self.system_layout.addLayout(self.xy_verticalSlider_horizontal_layout,0,0,1,1)

        # label标签的布局设置
        self.label_xy = QtWidgets.QLabel(Widget)
        self.label_xy.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_xy.setObjectName("label_xy")
        self.xy_label_vertical_layout.addWidget(self.label_xy)
        self.system_layout.addLayout(self.xy_label_vertical_layout,1,0,1,1)


        self.maxSlice1 = self.viewer1.GetSliceMax()
        self.verticalSlider_XY.setMaximum(self.maxSlice1)
        self.verticalSlider_XY.setMinimum(0)
        self.verticalSlider_XY.setSingleStep(1)
        self.verticalSlider_XY.valueChanged.connect(self.valuechange)

        # 工具栏布局
        self.tool_bar_layout = QtWidgets.QVBoxLayout()
        self.tool_bar_layout.setSpacing(6)
        self.tool_bar_layout.setObjectName("tool_bar_layout")

        self.widget_tool = QtWidgets.QWidget(Widget)
        self.widget_tool.setMinimumSize(QtCore.QSize(350,300))
        self.widget_tool.setMaximumSize(QtCore.QSize(400,400))
        self.widget_tool.setObjectName("widget_tool")
        self.widget_tool.setStyleSheet('''background-color:white''')

        self.tool_vertical_layout = QtWidgets.QVBoxLayout(self.widget_tool)
        self.tool_vertical_layout.setContentsMargins(11,11,11,11)
        self.tool_vertical_layout.setSpacing(6)
        self.tool_vertical_layout.setAlignment(QtCore.Qt.AlignVCenter)
        self.tool_vertical_layout.setObjectName("tool_vertical_layout")

        self.title_bool = QtWidgets.QLabel(self.widget_tool)
        self.title_bool.setObjectName("title_tool")
        self.title_bool.setStyleSheet("color:green")
        self.title_bool.setFont(self.font2)
        self.tool_vertical_layout.addWidget(self.title_bool)

        # 输入牙弓厚度
        self.horizontal_layout_input = QtWidgets.QHBoxLayout(self.widget_tool)
        self.horizontal_layout_input.setObjectName("horizontal_layout_input")
        self.horizontal_layout_input.setSpacing(6)

        self.dental_arch_thickness_label = QtWidgets.QLabel(self.widget_tool)
        self.dental_arch_thickness_label.setObjectName("dental_arch_thickness_label")
        self.dental_arch_thickness_label.setFont(self.font)
        self.dental_arch_thickness_label.setText("牙弓厚度:")

        self.dental_arch_thickness = QtWidgets.QLineEdit(self.widget_tool)
        self.dental_arch_thickness.setObjectName("dental_arch_thickness")
        self.dental_arch_thickness.setText("80")
        # 创建整数验证器
        validator = QtGui.QIntValidator()
        # 将验证器应用于文本框
        self.dental_arch_thickness.setValidator(validator)
        self.dental_arch_thickness.textChanged[str].connect(self.changeThickness)

        self.horizontal_layout_input.addWidget(self.dental_arch_thickness_label,0,Qt.AlignLeft)
        self.horizontal_layout_input.addWidget(self.dental_arch_thickness,1,Qt.AlignLeft)
        self.tool_vertical_layout.addLayout(self.horizontal_layout_input)

        #  标注按钮
        self.pushButton_annotation = QtWidgets.QPushButton(self.widget_tool)
        self.pushButton_annotation.setObjectName("pushButton_annotation")
        self.pushButton_annotation.setCheckable(True)
        self.pushButton_annotation.setAutoExclusive(False)
        self.pushButton_annotation.setFont(self.font)
        self.pushButton_annotation.clicked.connect(self.annotation)
        self.annotation_enable = False
        self.tool_vertical_layout.addWidget(self.pushButton_annotation)

        # 保存按钮
        self.pushButton_save = QtWidgets.QPushButton(self.widget_tool)
        self.pushButton_save.setObjectName("pushButton_save")
        self.pushButton_save.setAutoExclusive(False)
        self.pushButton_save.setFont(self.font)
        self.pushButton_save.clicked.connect(self.save)
        self.tool_vertical_layout.addWidget(self.pushButton_save)

        # 显示牙弓线按钮
        self.pushButton_show = QtWidgets.QPushButton(self.widget_tool)
        self.pushButton_show.setObjectName("pushButton_show")
        self.pushButton_show.setCheckable(True)
        self.pushButton_show.setAutoExclusive(False)
        self.pushButton_show.setFont(self.font)
        self.pushButton_show.clicked.connect(self.show_dentral_arch_curve)
        self.show_enable = False
        self.tool_vertical_layout.addWidget(self.pushButton_show)

        # 生成口腔全景图
        self.pushButton_generate_dentalPanoramic = QtWidgets.QPushButton(self.widget_tool)
        self.pushButton_generate_dentalPanoramic.setObjectName("pushButton_generate_dentalPanoramic")
        self.pushButton_generate_dentalPanoramic.setFont(self.font)
        self.pushButton_generate_dentalPanoramic.clicked.connect(self.generate_dental_panoramic)
        self.tool_vertical_layout.addWidget(self.pushButton_generate_dentalPanoramic)


        self.tool_bar_layout.addWidget(self.widget_tool)

        self.system_layout.addLayout(self.tool_bar_layout, 0, 1, 1, 1)

        self.system_layout.setColumnMinimumWidth(0, 7)
        self.system_layout.setColumnMinimumWidth(1, 2)
        self.system_layout.setColumnStretch(0, 7)
        self.system_layout.setColumnStretch(1, 2)

        self.spline_widget = vtk.vtkSplineWidget()
        self.spline_widget.SetInteractor(self.viewer1.GetRenderWindow().GetInteractor())
        self.spline_widget.SetNumberOfHandles(11)
        self.spline_widget.GetHandleProperty().SetPointSize(3)

        self.wheelforward1 = MouseWheelForward_child(self.viewer1, self.label_xy, self.verticalSlider_XY, self.annotation_enable,self.spline_widget)
        self.wheelbackward1 = MouseWheelBackWard_child(self.viewer1, self.label_xy, self.verticalSlider_XY, self.annotation_enable,self.spline_widget)
        self.viewer1_InteractorStyle = self.viewer1.GetInteractorStyle()
        self.viewer1_InteractorStyle.AddObserver("MouseWheelForwardEvent", self.wheelforward1)
        self.viewer1_InteractorStyle.AddObserver("MouseWheelBackwardEvent", self.wheelbackward1)

        self.retranslateUi(Widget)
        QtCore.QMetaObject.connectSlotsByName(Widget)

    def retranslateUi(self, Widget):
        _translate = QtCore.QCoreApplication.translate
        Widget.setWindowTitle(_translate("Widget", "口腔全景图"))
        self.label_xy.setText(_translate("Widget", "切片"))
        self.pushButton_annotation.setText(_translate("Widget","标注"))
        self.pushButton_save.setText(_translate("Widget","保存"))
        self.title_bool.setText(_translate("Widget","工具栏"))
        self.pushButton_show.setText(_translate("Widget","显示牙弓线"))
        self.pushButton_generate_dentalPanoramic.setText(_translate("Widget","生成口腔全景图"))

    def annotation(self):
        if self.annotation_enable == False:
            print("牙弓线标注")
            self.picker = vtk.vtkPointPicker()
            self.picker.PickFromListOn()
            self.viewer1.SetSlice(getSliceXY())
            self.pushButton_show.setChecked(False)
            print(getSliceXY())
            self.spline_widget.SetHandlePosition(0,10,10,getSliceXY())
            self.spline_widget.SetHandlePosition(1,15,15,getSliceXY())
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
            self.viewer1.UpdateDisplayExtent()
            self.viewer1.Render()
            self.annotation_enable = True
        else:
            self.spline_widget.Off()
            self.annotation_enable = False



    def save(self):
        if self.annotation_enable == False:
            return
        getDentalArchCurvePoint().clear()
        getControlPoints().clear()
        self.image = self.viewer1.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.dimensions = self.image.GetDimensions()
        setDentalArchThickness(self.thickness_value)
        thickness = getDentalArchThickness()
        print("牙弓厚度：",thickness)
        print("打印牙弓曲线的点")
        ployData = vtk.vtkPolyData()
        self.spline_widget.GetPolyData(ployData)
        num_points = ployData.GetNumberOfPoints()
        points = ployData.GetPoints()
        dental_arch_points = []
        for i in range(num_points):
            x, y, z = points.GetPoint(i)
            setDentalArchCurvePoint([x, y, z])
            dental_arch_points.append([x / self.spacing[0] - self.origin[0], self.dimensions[1] - y / self.spacing[1] + self.origin[1], z])
            print(f"Point {i}: ({x}, {y}, {z})")

        dental_arch_points= np.array(dental_arch_points).astype(np.int32)
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
            setControlPoints([x_cords,y_cords])

        setControlPoints([end_point[0],end_point[1]])

        print(getControlPoints())

    def show_dentral_arch_curve(self):
        if getDentalArchCurvePoint()==[]:
            print("没有牙弓曲线，无法显示")

            return
        if self.show_enable == False:
            getSamplePoint().clear()
            self.image = self.viewer1.GetInput()
            self.origin = self.image.GetOrigin()
            self.spacing = self.image.GetSpacing()
            self.dimensions = self.image.GetDimensions()
            thickness = int(getDentalArchThickness())
            control_points = np.array(getControlPoints())
            print(thickness,control_points)

            line1_points , line2_points = get_vertical_lines_points(control_points,sample_points_num=800,arch_width=thickness)
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
                self.points2.InsertNextPoint(point1[0] * self.spacing[0] + self.origin[0],(self.dimensions[1] - point1[1]) * self.spacing[1] + self.origin[1],dicom_z)
                self.points3.InsertNextPoint(point2[0] * self.spacing[0] + self.origin[0],(self.dimensions[1] - point2[1]) * self.spacing[1] + self.origin[1],dicom_z)


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

            self.viewer1.SetSlice(int(dicom_z))

            self.ren = self.viewer1.GetRenderer()
            self.ren.AddActor(self.actor1)
            self.ren.AddActor(self.actor2)
            self.ren.AddActor(self.actor3)
            self.viewer1.GetRenderWindow().GetInteractor().Render()
            self.ren.Render()
            self.viewer1.UpdateDisplayExtent()
            self.viewer1.Render()

            self.show_enable = True
        else:
            # 删除生成的线条样式
            self.ren.RemoveActor(self.actor1)
            self.ren.RemoveActor(self.actor2)
            self.ren.RemoveActor(self.actor3)
            self.viewer1.GetRenderWindow().GetInteractor().Render()
            self.viewer1.UpdateDisplayExtent()
            self.viewer1.Render()
            self.show_enable = False

    def generate_dental_panoramic(self):
        if getControlPoints() == []:
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

        plt.imsave("coronal_volume.png", coronal_volume, cmap='gray')
        contrast_brightness = contrastAndbrightness("./coronal_volume.png", 1.2, 1.3)
        plt.figure(figsize=(12, 8))
        plt.imshow(coronal_volume, cmap='gray')
        plt.imsave("coronal_volume.png", contrast_brightness, cmap='gray')
        plt.show()
        # img2 = cv2.imread("./coronal_volume.png", flags=1)
        # contrast_brightness = np.array(coronal_volume)
        # # 缩放因子
        # scale_factor = 1.5
        #
        # # 调整图像大小
        # resized_curve = cv2.resize(contrast_brightness, (0, 0), fx=scale_factor, fy=scale_factor)
        # cv2.imshow('Panomaic', resized_curve)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    def valuechange(self):
        print("value changed")
        value = self.verticalSlider_XY.value()
        self.viewer1.SetSlice(value)
        self.viewer1.UpdateDisplayExtent()
        self.viewer1.Render()
        setSliceXY(value)
        self.label_xy.setText("Slice %d/%d" % (self.viewer1.GetSlice(), self.viewer1.GetSliceMax()))

    def changeThickness(self):
        self.thickness_value = self.dental_arch_thickness.text()
        setDentalArchThickness(self.thickness_value)
        print("self.thickness_value:",self.thickness_value)

def get_vertical_lines_points(control_points,sample_points_num,arch_width):
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
        line2.append((x2,y2))
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
    # sample_points = []
    # for i in range(len(out[0])):
    #     setSamplePoint([int(out[0][i]), int(out[1][i])])
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
        # 绘制法向量
        # plt.plot([x1, x2], [y1, y2], 'r', linewidth=1)
        # plt.show()

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
    # # 绘制样条曲线和等距采样点
    # plt.plot(sample_points[:, 0], sample_points[:, 1], 'r', label='Original points')
    # plt.plot(normal_sample_points[:, 0], normal_sample_points[:, 1], 'o', label='Sample points')
    # plt.gca().invert_yaxis()
    # plt.legend()
    # plt.show()

    sysnetic_curve = []
    for i in range(normal_samples_num):
        # 这里要对每层XY轴旋转90°,否则获得二维坐标和三维数据坐标不对应
        # Opencv图像坐标系以向右为X正,向下为Y正。三维ct数据坐标系在轴状平面上,向右为X正,向上为Y正
        slice_point = sample_points_total[i, :]
        index_max = np.max(slice_point,axis=0)
        if index_max[0] >= ct_cube.shape[2] or index_max[1] >= ct_cube.shape[1]:
            total = []
            for i in range(0,ct_cube.shape[0] if ct_cube.shape[0] < 320 else 320):
                level_pixel = []
                for point in slice_point:
                    if point[0] >= ct_cube.shape[2] or point[1] >= ct_cube.shape[1]:
                        level_pixel.append(0)
                    else:
                        level_pixel.append(ct_cube[i,point[1],point[0]])
                total.append(level_pixel)
            sysnetic_curve.append(np.array(total))
        else:
            curve2line = ct_cube[0:ct_cube.shape[0] if ct_cube.shape[0] < 320 else 320,slice_point[:, 1], slice_point[:, 0]]
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

    return pixel_volume,slices

def contrastAndbrightness(image_path,contrast,brightness):

    image = Image.open(image_path)
    enh_con = ImageEnhance.Contrast(image)
    image_contrasted = enh_con.enhance(contrast)

    enh_bri = ImageEnhance.Brightness(image_contrasted)
    image_brightened = enh_bri.enhance(brightness)
    return image_brightened


if __name__ == '__main__':
    setDirPath("G:/CBCT_Dataset/Dataset_CBCT/02")
    app = QApplication(sys.argv)
    Widget = QtWidgets.QWidget()
    form = Ui_Form()
    form.setupUi(Widget)
    Widget.show()
    sys.exit(app.exec_())