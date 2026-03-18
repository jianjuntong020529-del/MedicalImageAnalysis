import os

import numpy as np
import vtk
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog

from src.constant.ParamConstant import ParamConstant
from src.core.tooth_seg_landmark_prior.Tooth_Alveolar_Construction import Step1_CBCT_ToothAlveolar_Seg
from src.interactor_style.ToothLandmarkInteractorStyle import LeftButtonPressEvent
from src.model.BaseModel import BaseModel
from src.ui.LoadToothSegWindow import LoadToothSegWindow
from src.ui.LoadAlveolarSegWindow import LoadAlveolarSegWindow
from src.utils.globalVariables import getPaintActors, getUndoStack, setPaintActor, clearColorIndexList, \
    clearPaintActors, clearUndoStack, getColorIndexList, setRedoStack, getRedoStack, setUndoStack, setColorIndexList, \
    getDirPath
from src.widgets.ContrastWidget import Contrast
from src.widgets.QtAxialViewerWidget import AxialViewer
from src.widgets.ToothLandmarkWidget import ToothLandmarkWidget


class ToothLandmarkController(ToothLandmarkWidget):
    def __init__(self, baseModelClass: BaseModel, axialViewer: AxialViewer, contrast: Contrast):
        super(ToothLandmarkController).__init__()

        self.baseModelClass = baseModelClass
        self.axialViewer = axialViewer
        self.contrast = contrast

        self.init_widget()

        self.contrast.window_level_slider.valueChanged.connect(self.window_level_slider_valuechange)
        self.contrast.window_width_slider.valueChanged.connect(self.window_width_slider_valuechange)
        self.axialViewer.slider.valueChanged.connect(self.valuechange)
        self.pushButton_paint.clicked.connect(self.paint)
        self.pushButton_clear.clicked.connect(self.clear)
        self.pushButton_undo.clicked.connect(self.undo)
        self.pushButton_redo.clicked.connect(self.redo)
        self.color_combobox.currentIndexChanged.connect(self.update_current_color)

        self.pushButton_load.clicked.connect(self.load)
        self.pushButton_save.clicked.connect(self.save)
        self.pushButton_segmentation.clicked.connect(self.segmentation)

        self.pushButton_load_alveolar_segResult.clicked.connect(self.load_alveolar_segmentation_result)
        self.pushButton_load_tooth_segResult.clicked.connect(self.load_tooth_segmentation_result)

    def valuechange(self):
        viewer = self.axialViewer.viewer
        verticalSlider = self.axialViewer.slider
        label = self.axialViewer.slider_label
        try:
            for i in getPaintActors():
                viewer.GetRenderer().RemoveActor(i)
            viewer.Render()
        except:
            print('Close viewer_XY actor_paint Failed!!!')
        value = verticalSlider.value()
        viewer.SetSlice(value)
        if getUndoStack():
            for point in getUndoStack():
                if point[1] == value:
                    print("valuechange")
                    self.paintPoints(point)
        viewer.UpdateDisplayExtent()
        viewer.Render()
        label.setText("Slice %d/%d" % (viewer.GetSlice(), viewer.GetSliceMax()))

    def window_level_slider_valuechange(self):
        self.viewer_XY = self.axialViewer.viewer
        self.viewer_XY.SetColorLevel(self.contrast.window_level_slider.value())
        self.viewer_XY.SetColorWindow(self.contrast.window_width_slider.value())
        self.viewer_XY.Render()

    def window_width_slider_valuechange(self):
        self.viewer_XY = self.axialViewer.viewer
        self.viewer_XY.SetColorLevel(self.contrast.window_level_slider.value())
        self.viewer_XY.SetColorWindow(self.contrast.window_width_slider.value())
        self.viewer_XY.Render()

    def paint(self):
        self.viewer_XY = self.axialViewer.viewer
        self.viewer_XY_InteractorStyle = self.viewer_XY.GetInteractorStyle()
        if not self.paint_enable:
            print("开始标注")
            picker = vtk.vtkPointPicker()
            picker.PickFromListOn()
            left_press = LeftButtonPressEvent(picker, self.viewer_XY, self.color_combobox)
            self.viewer_XY_InteractorStyle.AddObserver("LeftButtonPressEvent", left_press)
            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
            self.paint_enable = True
        else:
            print("结束标注")
            self.viewer_XY_InteractorStyle.RemoveObservers("LeftButtonPressEvent")
            self.paint_enable = False

    def clear(self):
        self.viewer_XY = self.axialViewer.viewer
        try:
            for i in getPaintActors():
                self.viewer_XY.GetRenderer().RemoveActor(i)
            self.viewer_XY.Render()
        except:
            print('Close viewer_XY actor_paint Failed!!!')
        if len(getUndoStack()) > 0:
            current_list = list(set(np.array(getUndoStack())[:, 0]))
            for index in getColorIndexList():
                if index in current_list:
                    self.color_combobox.setItemText(self.color_combobox.findText(str(index) + " √"), str(index))
                self.color_combobox.update()
        clearColorIndexList()
        clearPaintActors()
        clearUndoStack()

    def undo(self):
        self.viewer_XY = self.axialViewer.viewer
        self.verticalSlider_XY = self.axialViewer.slider
        try:
            for i in getPaintActors():
                self.viewer_XY.GetRenderer().RemoveActor(i)
        except:
            print('Close viewer_XY actor_paint Failed!!!')
        if len(getUndoStack()) > 0:
            setRedoStack(getUndoStack().pop())
        current_list = list(set(np.array(getUndoStack())[:, 0])) if len(getUndoStack()) > 0 else []
        for index in getColorIndexList():
            if index not in current_list:
                self.color_combobox.setItemText(self.color_combobox.findText(str(index) + " √"), str(index))
                self.color_combobox.update()
                getColorIndexList().remove(index)
        for point in getUndoStack():
            if point[1] == self.verticalSlider_XY.value():
                print("undo")
                self.paintPoints(point)
        self.viewer_XY.UpdateDisplayExtent()
        self.viewer_XY.Render()

    def redo(self):
        self.viewer_XY = self.axialViewer.viewer
        if len(getRedoStack()) > 0:
            setUndoStack(getRedoStack().pop())
        current_list = list(set(np.array(getUndoStack())[:, 0]))
        for index in current_list:
            if index not in getColorIndexList():
                setColorIndexList(index)
                self.color_combobox.setItemText(self.color_combobox.findText(str(index)), str(index) + " √")
            self.color_combobox.update()
        for point in getUndoStack():
            if point[1] == self.verticalSlider_XY.value():
                print("redo")
                self.paintPoints(point)
        self.viewer_XY.UpdateDisplayExtent()
        self.viewer_XY.Render()

    def update_current_color(self, index):
        self.current_color_data = ParamConstant.COLOR_DATA[index]
        if self.current_color_data[0] == "":
            self.current_color_data = ParamConstant.COLOR_DATA[index + 1]
            self.color_combobox.setCurrentIndex(index + 1)
        ParamConstant.CURRENT_COLOR = self.current_color_data[0]
        ParamConstant.CURRENT_COLOR_ID = self.current_color_data[1]
        ParamConstant.CURRENT_COLOR_INDEX = self.color_combobox.currentIndex()
        print(self.color_combobox.currentText(), ParamConstant.CURRENT_COLOR)
        print(self.color_combobox.findText(str(17)))

    def load(self):
        self.viewer_XY = self.axialViewer.viewer
        self.verticalSlider_XY = self.axialViewer.slider
        dicom_shape = self.baseModelClass.imageDimensions
        if len(getUndoStack()) > 0:
            current_list = list(set(np.array(getUndoStack())[:, 0]))
            for index in getColorIndexList():
                if index in current_list:
                    self.color_combobox.setItemText(self.color_combobox.findText(str(index) + " √"), str(index))
                self.color_combobox.update()
                getColorIndexList().remove(index)
        clearUndoStack()
        clearColorIndexList()
        try:
            for i in getPaintActors():
                self.viewer_XY.GetRenderer().RemoveActor(i)
        except:
            print('Close viewer_XY actor_paint Failed!!!')
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Open File", "", "Text Files (*.txt)")
        print(file_path)
        if file_path:
            with open(file_path, "r") as file:
                lines = file.readlines()
                for line in lines:
                    point = [int(p) for p in line.strip().split(",")]
                    point[1] = dicom_shape[2] - point[1] - 1
                    point[3] = dicom_shape[1] - point[3] - 1
                    setUndoStack(point)
            info = QtWidgets.QMessageBox()
            info.setIcon(QtWidgets.QMessageBox.Information)
            info.setWindowTitle('Information')
            info.setText('File loaded successfully!')
            info.show()
            info.exec_()
            print(getUndoStack())
            for point in getUndoStack():
                setColorIndexList(point[0])
                if point[1] == self.verticalSlider_XY.value():
                    print("redo")
                    self.paintPoints(point)
            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
            ParamConstant.LAND_MARK_PATH = file_path
            for index in getColorIndexList():
                self.color_combobox.setItemText(self.color_combobox.findText(str(index)), str(index) + " √")
                self.color_combobox.update()

    def save(self):
        dicom_shape = self.baseModelClass.imageDimensions
        if getUndoStack() == []:
            return
        save_file_path = QFileDialog.getSaveFileName(None, "Save File", "", "Text Files (*.txt)")[0]
        if save_file_path:
            with open(save_file_path, "w") as file:
                for point in getUndoStack():
                    point[1] = dicom_shape[2] - point[1] - 1
                    point[3] = dicom_shape[1] - point[3] - 1
                    file.write(",".join(str(p) for p in point) + "\n")
            info = QtWidgets.QMessageBox()
            info.setIcon(QtWidgets.QMessageBox.Information)
            info.setWindowTitle('Information')
            info.setText('File saved successfully!')
            info.show()
            info.exec_()
        ParamConstant.LAND_MARK_PATH = save_file_path

    def segmentation(self):
        patientum = getDirPath().split('/')[-1]
        self.output_file_path = ParamConstant.OUTPUT_FILE_PATH + patientum + "/"
        if not os.path.exists(self.output_file_path):
            os.makedirs(self.output_file_path)
        print("#===============Processing PatientID: " + patientum + "===============#")
        info = QtWidgets.QMessageBox()
        info.setIcon(QtWidgets.QMessageBox.Information)
        info.setWindowTitle('Teeth Segmentation in Progress!')
        info.setText('Teeth Segmentation Completed!')
        info.show()
        Step1_CBCT_ToothAlveolar_Seg(getDirPath(), ParamConstant.LAND_MARK_PATH, ParamConstant.ANNOTATION_SUBJECT_NAME,
                                     self.output_file_path, ParamConstant.FLAG_SEG,
                                     ParamConstant.TOOTH_LANDMARK_THRESHOLD_TH,
                                     ParamConstant.TOOTH_LANDMARK_THRESHOLD_AL, ParamConstant.SMOOTH_FACTOR,
                                     ParamConstant.EROSION_RADIUS_UP, ParamConstant.EROSION_RADIUS_LOW)
        info.exec_()

    def load_alveolar_segmentation_result(self):
        print("load alveolar segmentation result")
        self.load_alveolar_seg_window = LoadAlveolarSegWindow(self.baseModelClass)
        self.load_alveolar_seg_window.show()
        self.load_alveolar_seg_window.LoadSTL()

    def load_tooth_segmentation_result(self):
        print("load tooth segmentation result")
        self.load_tooth_seg_window = LoadToothSegWindow(self.baseModelClass)
        self.load_tooth_seg_window.show()
        self.load_tooth_seg_window.LoadSTL()

    def paintPoints(self, point):
        self.viewer_XY = self.axialViewer.viewer
        origin = self.baseModelClass.origin
        spacing = self.baseModelClass.spacing

        print(point)
        label_id = point[0]
        label_color = None
        for data in ParamConstant.COLOR_DATA:
            if data[0] == "":
                continue
            if int(data[1]) == label_id:
                label_color = data[0]
        point_z = point[1]
        point_x = point[2] * spacing[0] + origin[0]
        point_y = point[3] * spacing[1] + origin[1]
        print(label_color, label_id, point_x, point_y, point_z)
        
        # 如果没有找到对应的颜色，使用默认颜色
        if label_color is None:
            label_color = "#FFFFFF"  # 默认白色
            print(f"Warning: No color found for label_id {label_id}, using default white color")
        
        square = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        points.InsertNextPoint(point_x - 0.5, point_y + 0.5, point_z)
        points.InsertNextPoint(point_x + 0.5, point_y + 0.5, point_z)
        points.InsertNextPoint(point_x + 0.5, point_y - 0.5, point_z)
        points.InsertNextPoint(point_x - 0.5, point_y - 0.5, point_z)

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

        rgb = self.hex_to_rgb(label_color)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(rgb[0], rgb[1], rgb[2])

        setPaintActor(actor)
        self.viewer_XY.GetRenderer().AddActor(actor)

    def hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为RGB值"""
        if hex_color is None:
            # 如果颜色为None，返回白色
            return 1.0, 1.0, 1.0
        
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) != 6:
                # 如果颜色格式不正确，返回白色
                print(f"Warning: Invalid hex color format '{hex_color}', using white")
                return 1.0, 1.0, 1.0
            
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return r, g, b
        except (ValueError, AttributeError) as e:
            print(f"Error converting hex color '{hex_color}': {e}, using white")
            return 1.0, 1.0, 1.0

    @staticmethod
    def message_info_dialog(title, text):
        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, title, text)
        msg_box.exec_()

    # 警告提示框
    @staticmethod
    def message_warning_dialog(title, text):
        msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, title, text)
        msg_box.exec_()
