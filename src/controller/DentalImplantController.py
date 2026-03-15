# -*- coding: utf-8 -*-
# @Time    : 2024/10/15 19:41
#
# @Author  : Jianjun Tong
import math
import os

import numpy as np
import pyautogui
import trimesh
import vtk
from PyQt5.QtWidgets import QMessageBox
from medpy.io import save
from skimage.draw import circle
from skimage.measure._marching_cubes_lewiner import marching_cubes_lewiner

from src.constant.ParamConstant import ParamConstant
from src.constant.WindowConstant import WindowConstant
from src.controller.ToolBarController import ToolBarController
from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.ToolBarEnableModel import ToolBarEnable
from src.model.ToothImplantListModel import ToothImplantList
from src.model.VolumeRenderModel import VolumeRender
from src.service.ToolBarService import ToolBarService
from src.style.FontStyle import Font
from src.utils.globalVariables import *
from src.widgets.ImplantWidget import ImplantWidget


class DentalImplantController(ImplantWidget):
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel, toolBarController:ToolBarController, widget):
        super(DentalImplantController).__init__()

        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.widget = widget
        self.toolBarController = toolBarController
        self.init_widget()

        # ---------------植体放置2D图参数---------------------------------------------
        self.drawpaper_size = 200
        self.drawimplant_len = 50
        self.drawimplant_width = 20
        self.drawpaper_center = self.drawpaper_size // 2
        self.drawcircle_radius = self.drawimplant_width // 2
        self.coords_origin = [self.drawpaper_size // 2, self.drawpaper_size // 2]
        self.coords_list = self.drawimplant_coordinate(self.drawpaper_size, self.drawimplant_len,
                                                       self.drawimplant_width)
        self.rotation_angle = 0

        # 绑定槽函数
        self.implant_direction_cb_up.stateChanged.connect(self.implant_direction_cb_up_changed)
        self.implant_direction_cb_down.stateChanged.connect(self.implant_direction_cb_down_changed)
        self.pushButton_implant.clicked.connect(self.implant_place)
        self.pushButton_crosshair_axis_orthogonal.clicked.connect(self.cross_hairaxis_orthogonal)
        self.pushButton_adjust_imp.clicked.connect(self.implant_3D_adjust)

        self.horizontalSlider_implant_angle_XY.valueChanged.connect(self.horizontalSlider_implant_XY_angle_valuechange)
        self.horizontalSlider_implant_angle_YZ.valueChanged.connect(self.horizontalSlider_implant_YZ_angle_valuechange)
        self.horizontalSlider_implant_angle_XZ.valueChanged.connect(self.horizontalSlider_implant_XZ_angle_valuechange)

        self.horizontalSlider_implant_move_Xaxis.valueChanged.connect(self.horizontalSlider_implant_move_Axis_valuechange)
        self.horizontalSlider_implant_move_Yaxis.valueChanged.connect(self.horizontalSlider_implant_move_Axis_valuechange)
        self.horizontalSlider_implant_move_Zaxis.valueChanged.connect(self.horizontalSlider_implant_move_Axis_valuechange)

        self.ToothID_Implant_QListView.doubleClicked.connect(self.ToothID_Implant_QListView_Func)


    def polar360(self, x_input, y_input, x_ori=0, y_ori=0):
        x = x_input - x_ori
        y = y_input - y_ori
        rdius = math.hypot(y, x)
        theta = math.degrees(math.atan2(x, y)) + (x < 0) * 360
        return rdius, theta

    def rotation_shape(self, coords_list, coords_origin, rotation_angle):
        rotation_coords_list = []
        for i in range(len(coords_list)):
            coords = coords_list[i]
            rdius, theta = self.polar360(coords[0], coords[1], coords_origin[0], coords_origin[1])
            x_r = np.int32(coords_origin[0] + rdius * math.sin((theta + rotation_angle) / 180 * math.pi))
            y_r = np.int32(coords_origin[1] + rdius * math.cos((theta + rotation_angle) / 180 * math.pi))
            rotation_coords_list.append([x_r, y_r])

        return rotation_coords_list

    def drawimplant_coordinate(self, drawpaper_size, drawimplant_len, drawimplant_width):
        coord_center = drawpaper_size // 2
        len_center = drawimplant_len // 2
        width_center = drawimplant_width // 2
        coords_list = [[coord_center, coord_center], [coord_center + width_center, coord_center + len_center],
                       [coord_center + width_center, coord_center - len_center],
                       [coord_center - width_center, coord_center - len_center],
                       [coord_center - width_center, coord_center + len_center],
                       [coord_center, coord_center], [coord_center, drawpaper_size], [coord_center, 0]]
        return coords_list

    def implant_direction_cb_up_changed(self):
        if self.implant_direction_cb_up.isChecked():
            self.implant_direction_cb_down.setCheckState(0)

    def implant_direction_cb_down_changed(self):
        if self.implant_direction_cb_down.isChecked():
            self.implant_direction_cb_up.setCheckState(0)

    def init_update_viewer_information(self):

        # self.toolBarService = ToolBarService(self.baseModelClass, self.viewModel)

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

        self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
        self.iren_Volume = self.viewModel.VolumeOrthorViewer.renderWindowInteractor
        self.renderer_volume = self.viewModel.VolumeOrthorViewer.renderer

        self.spacing = self.baseModelClass.spacing
        self.origin = self.baseModelClass.origin
        self.dims = self.baseModelClass.imageDimensions

    def implant_place(self):
        self.init_update_viewer_information()
        print("！！！ 放置植体 ！！！")
        # -----------------------------------------------------------
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_implant)
        except:
            print('Close implant Actors Failed!!!')
        try:
            for actor in VolumeRender.actor_implant_reg:
                self.renderer_volume.RemoveActor(actor)
        except:
            print("close actor_implant_reg failed")
        # -----------------------------------------------------------
        if getFileIsEmpty():
            print("未导入文件，不能放置植体")
            return
        if not ToolBarEnable.crosshair_enable:
            api = self.implant_information()
            if api == QMessageBox.AcceptRole:
                print("选择了确认")
                self.toolBarController.action_crosshair.setChecked(True)
                self.toolBarController.on_action_crosshair()
            elif api == QMessageBox.RejectRole:
                print("选择了取消")
                return
        setIsPutImplant(True)
        # ------------------------------------------------------------------------------
        self.horizontalSlider_implant_angle_XY.setValue(0)
        self.horizontalSlider_implant_angle_YZ.setValue(0)
        self.horizontalSlider_implant_angle_XZ.setValue(0)
        self.horizontalSlider_implant_move_Xaxis.setValue(0)
        self.horizontalSlider_implant_move_Yaxis.setValue(0)
        self.horizontalSlider_implant_move_Zaxis.setValue(0)
        # -----------------------------------------------------------------------------
        self.rotation_angle_X = 0
        self.rotation_angle_Y = 0
        self.rotation_angle_Z = 0
        # ------------------------------------------------------------------------------
        self.templateimplant_file_path = ParamConstant.IMPLANT_PATH + self.ToothImplant_QComboBox.currentText() + '.stl'
        # ------------------------------------------------------------------------------
        source_mesh = trimesh.load(self.templateimplant_file_path)
        vertices = source_mesh.vertices
        Hmax = np.max(vertices[:, 1])
        Hmin = np.min(vertices[:, 1])
        Zsort = np.sort(vertices[:, 2])
        self.Implant_Len = Zsort[-3] - Zsort[2]
        self.Implant_Diameter = Hmax - Hmin
        # -----------------------------------------------------------------------------
        self.drawimplant_len = self.Implant_Len / self.spacing[2]
        self.drawimplant_width = np.int32(self.Implant_Diameter / self.spacing[0])
        self.drawcircle_radius = self.drawimplant_width // 2
        # --------------------XY 2D 绘制---------------------------------------------------------
        self.drawing_XY = vtk.vtkImageCanvasSource2D()
        self.drawing_XY.SetScalarTypeToUnsignedChar()
        self.drawing_XY.SetNumberOfScalarComponents(4)
        self.drawing_XY.SetExtent(0, self.drawpaper_size, 0, self.drawpaper_size, 0, 0)
        self.drawing_XY.SetDrawColor(0, 0, 0, 0)
        self.drawing_XY.FillBox(0, self.drawpaper_size, 0, self.drawpaper_size)
        self.drawing_XY.SetDrawColor(0, 255, 0, 255)
        self.drawing_XY.FillTube(100, 75, 100, 125, 1)
        self.drawing_XY.FillTube(75, 100, 125, 100, 1)
        self.drawing_XY.SetDrawColor(255, 0, 0, 255)
        self.drawing_XY.DrawCircle(100, 100, self.drawcircle_radius)
        self.drawing_XY.Update()
        # -------------------------------------------------
        # print('计算画布位置开始：')
        cursorposition = self.viewer_XY.GetResliceCursor().GetCenter()
        # print('cursorposition', cursorposition)
        # --------------------------------------------------------------------------------
        Xangle = np.absolute(self.viewer_XZ.GetResliceCursor().GetXAxis()[0])
        Yangle = np.absolute(self.viewer_XY.GetResliceCursor().GetYAxis()[1])
        Zangle = np.absolute(self.viewer_YZ.GetResliceCursor().GetZAxis()[2])
        print([Xangle, Yangle, Zangle])
        # --------------------------------------------------------------------------------
        framewidth = self.vtkWidget_XY.frameSize().width()
        frameheight = self.vtkWidget_XY.frameSize().height()
        print([frameheight, framewidth])
        # -----------------centerpoint---------------------------------------------------
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToWorld()
        # -----------------leftbottom----------------------------------------------------
        leftbottom_point = [cursorposition[0] - self.drawpaper_center * self.spacing[0] / Xangle,
                            cursorposition[1] - self.drawpaper_center * self.spacing[1] / Yangle,
                            cursorposition[2]]
        vc.SetValue(leftbottom_point[0], leftbottom_point[1], leftbottom_point[2])
        leftbottom_point_disp = list(vc.GetComputedDisplayValue(self.viewer_XY.GetRenderer()))
        leftbottom_point_disp_normalize = [leftbottom_point_disp[0] / framewidth,
                                           leftbottom_point_disp[1] / frameheight]
        # -----------------righttop_point-------------------------------
        righttop_point = [cursorposition[0] + self.drawpaper_center * self.spacing[0] / Xangle,
                          cursorposition[1] + self.drawpaper_center * self.spacing[1] / Yangle,
                          cursorposition[2]]
        vc.SetValue(righttop_point[0], righttop_point[1], righttop_point[2])
        righttop_point_disp = list(vc.GetComputedDisplayValue(self.viewer_XY.GetRenderer()))
        righttop_point_disp_normalize = [righttop_point_disp[0] / framewidth, righttop_point_disp[1] / frameheight]
        # print('leftbottom_point_disp', leftbottom_point_disp)
        # print('righttop_point_disp', righttop_point_disp)
        # -------------------------------------------------------------------------------------
        self.logoRepresentation_XY = vtk.vtkLogoRepresentation()
        self.logoRepresentation_XY.SetImage(self.drawing_XY.GetOutput())
        self.logoRepresentation_XY.SetPosition(leftbottom_point_disp_normalize[0], leftbottom_point_disp_normalize[1])
        self.logoRepresentation_XY.SetPosition2(righttop_point_disp_normalize[0] - leftbottom_point_disp_normalize[0],
                                                righttop_point_disp_normalize[1] - leftbottom_point_disp_normalize[1])
        self.logoRepresentation_XY.GetImageProperty().SetOpacity(1)

        self.logoWidget_XY = vtk.vtkLogoWidget()
        self.logoWidget_XY.SetResizable(0)
        self.logoWidget_XY.SetProcessEvents(0)
        self.logoWidget_XY.SetInteractor(self.viewer_XY.GetInteractor())
        self.logoWidget_XY.SetRepresentation(self.logoRepresentation_XY)
        self.logoWidget_XY.On()
        self.viewer_XY.Render()
        # -----------------------------XZ 2D 绘制----------------------------------------------------------------
        self.coords_list = self.drawimplant_coordinate(self.drawpaper_size, self.drawimplant_len,
                                                       self.drawimplant_width)
        self.drawing_XZ = vtk.vtkImageCanvasSource2D()  # 画布
        self.drawing_XZ.SetScalarTypeToUnsignedChar()
        self.drawing_XZ.SetNumberOfScalarComponents(4)
        self.drawing_XZ.SetExtent(0, self.drawpaper_size, 0, self.drawpaper_size, 0, 0)
        self.drawing_XZ.SetDrawColor(0, 0, 0, 0)
        self.drawing_XZ.FillBox(0, self.drawpaper_size, 0, self.drawpaper_size)
        self.drawing_XZ.SetDrawColor(0, 255, 0, 255)
        if self.implant_direction_cb_up.isChecked():
            rotation_angle = 0
        else:
            rotation_angle = 180
        # ==================================
        self.rotation_coords_list = self.rotation_shape(self.coords_list, self.coords_origin, rotation_angle)
        for i in range(len(self.rotation_coords_list)):
            if i == (len(self.rotation_coords_list) - 1):
                self.drawing_XZ.FillTube(self.rotation_coords_list[i][0], self.rotation_coords_list[i][1],
                                         self.rotation_coords_list[0][0],
                                         self.rotation_coords_list[0][1], 1)
            else:
                self.drawing_XZ.FillTube(self.rotation_coords_list[i][0], self.rotation_coords_list[i][1],
                                         self.rotation_coords_list[i + 1][0],
                                         self.rotation_coords_list[i + 1][1], 1)

        self.drawing_XZ.SetDrawColor(0, 255, 0, 255)
        self.drawing_XZ.DrawCircle(100, 100, 50)
        self.drawing_XZ.Update()
        # --------------------------------------------------------------------------------
        # --------------------------------------------------------------------
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToWorld()
        # -----------------leftbottom----------------------------------------------------
        leftbottom_point = [cursorposition[0] - self.drawpaper_center * self.spacing[0] / Xangle, cursorposition[1],
                            cursorposition[2] - self.drawpaper_center * self.spacing[2] / Zangle]
        vc.SetValue(leftbottom_point[0], leftbottom_point[1], leftbottom_point[2])
        leftbottom_point_disp = list(vc.GetComputedDisplayValue(self.viewer_XZ.GetRenderer()))
        leftbottom_point_disp_normalize = [leftbottom_point_disp[0] / framewidth,
                                           leftbottom_point_disp[1] / frameheight]
        # -----------------righttop_point-------------------------------
        righttop_point = [cursorposition[0] + self.drawpaper_center * self.spacing[0] / Xangle, cursorposition[1],
                          cursorposition[2] + self.drawpaper_center * self.spacing[2] / Zangle]
        vc.SetValue(righttop_point[0], righttop_point[1], righttop_point[2])
        righttop_point_disp = list(vc.GetComputedDisplayValue(self.viewer_XZ.GetRenderer()))
        righttop_point_disp_normalize = [righttop_point_disp[0] / framewidth, righttop_point_disp[1] / frameheight]
        # print('leftbottom_point_disp', leftbottom_point_disp)
        # print('righttop_point_disp', righttop_point_disp)
        # -------------------------------------------------------------------------------------
        # -------------------------------------------------
        self.logoRepresentation_XZ = vtk.vtkLogoRepresentation()  # 显示控件
        self.logoRepresentation_XZ.SetImage(self.drawing_XZ.GetOutput())
        self.logoRepresentation_XZ.SetPosition(leftbottom_point_disp_normalize[0], leftbottom_point_disp_normalize[1])
        self.logoRepresentation_XZ.SetPosition2(righttop_point_disp_normalize[0] - leftbottom_point_disp_normalize[0],
                                                righttop_point_disp_normalize[1] - leftbottom_point_disp_normalize[1])
        self.logoRepresentation_XZ.GetImageProperty().SetOpacity(1)
        self.logoWidget_XZ = vtk.vtkLogoWidget()  # 显示控件
        self.logoWidget_XZ.SetResizable(0)  # 尺寸不变
        self.logoWidget_XZ.SetProcessEvents(0)  # 位置不变
        self.logoWidget_XZ.SetInteractor(self.viewer_XZ.GetInteractor())
        self.logoWidget_XZ.SetRepresentation(self.logoRepresentation_XZ)
        self.logoWidget_XZ.On()
        self.viewer_XZ.Render()
        # -----------------------------YZ 2D 绘制----------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------
        self.drawing_YZ = vtk.vtkImageCanvasSource2D()
        self.drawing_YZ.SetScalarTypeToUnsignedChar()
        self.drawing_YZ.SetNumberOfScalarComponents(4)
        self.drawing_YZ.SetExtent(0, self.drawpaper_size, 0, self.drawpaper_size, 0, 0)
        self.drawing_YZ.SetDrawColor(0, 0, 0, 0)
        self.drawing_YZ.FillBox(0, self.drawpaper_size, 0, self.drawpaper_size)
        self.drawing_YZ.SetDrawColor(0, 255, 0, 255)
        if self.implant_direction_cb_up.isChecked():
            rotation_angle = 0
        else:
            rotation_angle = 180
        # ==================================
        self.rotation_coords_list = self.rotation_shape(self.coords_list, self.coords_origin, rotation_angle)
        for i in range(len(self.rotation_coords_list)):
            if i == (len(self.rotation_coords_list) - 1):
                self.drawing_YZ.FillTube(self.rotation_coords_list[i][0], self.rotation_coords_list[i][1],
                                         self.rotation_coords_list[0][0],
                                         self.rotation_coords_list[0][1], 1)
            else:
                self.drawing_YZ.FillTube(self.rotation_coords_list[i][0], self.rotation_coords_list[i][1],
                                         self.rotation_coords_list[i + 1][0],
                                         self.rotation_coords_list[i + 1][1], 1)

        self.drawing_YZ.SetDrawColor(0, 255, 0, 255)
        self.drawing_YZ.DrawCircle(100, 100, 50)
        self.drawing_YZ.Update()
        # --------------------------------------------------------------------------------
        # -----------------centerpoint---------------------------------------------------
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToWorld()
        # -----------------leftbottom----------------------------------------------------
        leftbottom_point = [cursorposition[0], cursorposition[1] - self.drawpaper_center * self.spacing[1] / Yangle,
                            cursorposition[2] - self.drawpaper_center * self.spacing[2] / Zangle]
        vc.SetValue(leftbottom_point[0], leftbottom_point[1], leftbottom_point[2])
        leftbottom_point_disp = list(vc.GetComputedDisplayValue(self.viewer_YZ.GetRenderer()))
        leftbottom_point_disp_normalize = [leftbottom_point_disp[0] / framewidth,
                                           leftbottom_point_disp[1] / frameheight]
        # -----------------righttop_point-------------------------------
        righttop_point = [cursorposition[0], cursorposition[1] + self.drawpaper_center * self.spacing[1] / Yangle,
                          cursorposition[2] + self.drawpaper_center * self.spacing[2] / Zangle]
        vc.SetValue(righttop_point[0], righttop_point[1], righttop_point[2])
        righttop_point_disp = list(vc.GetComputedDisplayValue(self.viewer_YZ.GetRenderer()))
        righttop_point_disp_normalize = [righttop_point_disp[0] / framewidth, righttop_point_disp[1] / frameheight]
        # print('leftbottom_point_disp', leftbottom_point_disp)
        # print('righttop_point_disp', righttop_point_disp)
        # -------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------
        self.logoRepresentation_YZ = vtk.vtkLogoRepresentation()
        self.logoRepresentation_YZ.SetImage(self.drawing_YZ.GetOutput())
        self.logoRepresentation_YZ.SetPosition(leftbottom_point_disp_normalize[0], leftbottom_point_disp_normalize[1])
        self.logoRepresentation_YZ.SetPosition2(righttop_point_disp_normalize[0] - leftbottom_point_disp_normalize[0],
                                                righttop_point_disp_normalize[1] - leftbottom_point_disp_normalize[1])
        self.logoRepresentation_YZ.GetImageProperty().SetOpacity(1)
        self.logoWidget_YZ = vtk.vtkLogoWidget()
        self.logoWidget_YZ.SetResizable(0)
        self.logoWidget_YZ.SetProcessEvents(0)
        self.logoWidget_YZ.SetInteractor(self.viewer_YZ.GetInteractor())
        self.logoWidget_YZ.SetRepresentation(self.logoRepresentation_YZ)
        self.logoWidget_YZ.On()
        self.viewer_YZ.Render()
        # -----------------------------3D 模型生成------------------------------------------------------------------------------
        # -----------------------------------------------------------------------------
        self.templateimplant_file_path = ParamConstant.IMPLANT_PATH + self.ToothImplant_QComboBox.currentText() + '.stl'
        self.toothimplant_temp_file_path = ParamConstant.OUTPUT_FILE_PATH + 'temp_tooth_implant.stl'
        # -----------------------------------------------------------------------------
        # try:
        #     self.renderer_volume.RemoveActor(self.actor_implant)
        # except:
        #     print('Close implant Actors Failed!!!')
        # ----------------------------------------------------------------
        # cursorposition = self.viewer_XY.GetResliceCursor().GetCenter()
        # print('cursorposition', cursorposition)
        xv = int((cursorposition[0] - self.origin[0]) / self.spacing[0])
        yv = int((cursorposition[1] - self.origin[1]) / self.spacing[1])
        zv = int((cursorposition[2] - self.origin[2]) / self.spacing[2])
        # print([xv, yv, zv])
        cursorposition_cent = [xv, yv, zv]
        # print('cursorposition_cent', cursorposition_cent)
        # --------------------------------------------------------------------------------
        # --------------------------------------------------------------
        source_mesh = trimesh.load(self.templateimplant_file_path)
        Zsort = np.sort(source_mesh.vertices[:, 2])
        Zcenter = (Zsort[-3] + Zsort[2]) / 2
        Numlarge = np.sum(source_mesh.vertices[:, 2] > Zcenter)
        Numvert = len(source_mesh.vertices[:, 2])
        if Numlarge > (Numvert // 2):
            implant_dirrction_Flag = 'DOWN'
        else:
            implant_dirrction_Flag = 'UP'
        # --------------------------------------------------------------
        # print('implant XY')
        # --------------------------------------------------------------------------
        pos_implant = [cursorposition_cent[0] - self.drawpaper_center,
                       cursorposition_cent[1] - self.drawpaper_center, cursorposition_cent[2]]
        # print('pos_implant', pos_implant)
        # ---------------------------------------------------------------------------------------
        # ------------------------生成3D Mask----------------------------------------------------
        [X_cent, Y_cent] = np.array([pos_implant[0], pos_implant[1]]) + np.array(self.coords_origin)
        Y_cent = self.dims[1] - Y_cent
        implantMask3D = np.zeros(self.dims, np.int32)
        # ------------------------------------------------------
        temp = np.int32(pos_implant[2] - self.drawimplant_len // 2)
        if temp >= 0:
            Zs = temp
        else:
            Zs = 0
        temp = np.int32(pos_implant[2] + self.drawimplant_len // 2)
        if temp < self.dims[2]:
            Ze = temp
        else:
            Ze = self.dims[2]
        # -----------------------------------------------------
        for ii in range(Zs, Ze):
            rr, cc = circle(X_cent, Y_cent, np.int32(self.drawcircle_radius))
            implantMask3D[rr, cc, ii] = 1
        save(np.int32(implantMask3D),
             ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_tooth_implant.nii.gz')

        # ------------------------------------------------------
        implantMask3D = np.rot90(implantMask3D, 2, axes=(0, 1))
        implantMask3D = np.flip(implantMask3D, axis=2)
        implantMask3D = np.flip(implantMask3D, axis=0)
        # # # ------------------------------------------------------------------------------------------
        verts, faces, normals, values = marching_cubes_lewiner(implantMask3D, level=0.5, spacing=self.spacing,
                                                               step_size=1.0)
        # ================植体配准=====================
        target_mesh = trimesh.Trimesh(verts, faces, validate=True)
        source_vertices = source_mesh.vertices
        if implant_dirrction_Flag == 'UP':
            if self.implant_direction_cb_up.isChecked():
                matrix = np.zeros((4, 4))
                Rm = np.array([[1, 0, 0], [0, 1, 0], [0, 0, -1]])
                matrix[0:3, 0:3] = Rm
                matrix[3, 3] = 1
                source_vertices = trimesh.transform_points(source_vertices, matrix)
        else:
            if self.implant_direction_cb_down.isChecked():
                matrix = np.zeros((4, 4))
                Rm = np.array([[1, 0, 0], [0, 1, 0], [0, 0, -1]])
                matrix[0:3, 0:3] = Rm
                matrix[3, 3] = 1
                source_vertices = trimesh.transform_points(source_vertices, matrix)
        # --------------------------------------------------------------------------------------
        matrix, transformed, cost = trimesh.registration.icp(source_vertices, target_mesh.vertices,
                                                             max_iterations=5000, reflection=True, scale=False)
        print('Cost is ' + str(cost))
        vertices_trans = trimesh.transform_points(source_vertices, matrix)
        implant_mesh = trimesh.Trimesh(vertices_trans, source_mesh.faces, validate=True)
        implant_mesh.export(self.toothimplant_temp_file_path)
        # ------------------------------------------------------------------------------------
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_mold_origin)
        except:
            print('actor_mold_origin is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_implant)
        except:
            print('actor_implant is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_implant_reg)
        except:
            print('Close Implant_reg Actors Failed!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_reg)
        except:
            print('actor_implant_reg is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_1)
        except:
            print('actor_ld_1 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_2)
        except:
            print('actor_ld_2 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_3)
        except:
            print('actor_ld_3 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_4)
        except:
            print('actor_ld_4 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_5)
        except:
            print('actor_ld_5 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_6)
        except:
            print('actor_ld_6 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_7)
        except:
            print('actor_ld_8 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_8)
        except:
            print('actor_ld_8 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_1)
        except:
            print('actor_anchor_1 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_2)
        except:
            print('actor_anchor_2 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_3)
        except:
            print('actor_anchor_3 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_4)
        except:
            print('actor_anchor_4 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_5)
        except:
            print('actor_anchor_5 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_6)
        except:
            print('actor_anchor_6 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_7)
        except:
            print('actor_anchor_7 is not found!!!')

        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_8)
        except:
            print('actor_anchor_8 is not found!!!')

        try:
            self.renderer_volume.AddActor(VolumeRender.volume_cbct)
        except:
            print('volume_cbct is not found!!!')
        self.vtkWidget_Volume.Render()
        # ------------------------------------------------------------------------------------
        self.reader_toothimplant = vtk.vtkSTLReader()
        self.reader_toothimplant.SetFileName(self.toothimplant_temp_file_path)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.reader_toothimplant.GetOutputPort())
        mapper.SetColorModeToDefault()
        mapper.SetColorModeToDirectScalars()
        actor_implant = vtk.vtkActor()
        actor_implant.SetMapper(mapper)
        actor_implant.GetProperty().SetColor(0, 1, 0)
        self.renderer_volume.AddActor(actor_implant)
        VolumeRender.actor_implant = actor_implant
        # ----------------------------------------------------------------------------
        self.vtkWidget_XY.Render()
        self.vtkWidget_YZ.Render()
        self.vtkWidget_XZ.Render()
        self.vtkWidget_Volume.Render()

    def implant_information(self):
        info = QMessageBox()
        info.setIcon(QMessageBox.Information)
        info.setWindowTitle(WindowConstant.IMPLANT_INFO_TITLE)
        info.setText(WindowConstant.IMPLANT_INFO_TEXT)
        info.setFixedSize(400, 200)
        info.setFont(Font.font2)
        info.addButton(WindowConstant.IMPLANT_INFO_ACCEPT, QMessageBox.AcceptRole)
        info.addButton(WindowConstant.IMPLANT_INFO_REJECT, QMessageBox.RejectRole)
        api = info.exec_()
        return api

    def cross_hairaxis_orthogonal(self):
        if not self.cross_hairaxis_orthogonal_enable:
            self.cross_hairaxis_orthogonal_enable = True
            pyautogui.keyDown('Ctrl')
        else:
            self.cross_hairaxis_orthogonal_enable = False
            pyautogui.keyUp('Ctrl')

    def implant_3D_adjust(self):
        self.init_update_viewer_information()
        if not getIsPutImplant():
            print("未放置植体，还不能移动滑块")
            return
        print('植体微调完成！！！')
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_implant)
        except:
            print('actor_implant is not found!!!')
        # --------------------------------------------------------------------------------------------------------------
        self.toothimplant_file_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_' + self.ToothID_QComboBox.currentText() + '_' + self.ToothImplant_QComboBox.currentText() + '_tooth_implant.stl'
        # ---------------------------------------------------------
        self.move_X = self.horizontalSlider_implant_move_Xaxis.value() / 10
        self.move_Y = self.horizontalSlider_implant_move_Yaxis.value() / 10
        self.move_Z = self.horizontalSlider_implant_move_Zaxis.value() / 10
        print([self.move_X, self.move_Y, self.move_Z])
        # ----------------------------------------------
        transform = vtk.vtkTransform()
        center_pos = VolumeRender.actor_implant.GetCenter()
        transform.Translate(center_pos)
        transform.RotateX(self.rotation_angle_Y)
        transform.RotateY(-self.rotation_angle_X)
        transform.RotateZ(self.rotation_angle_Z)
        transform.Translate(- center_pos[0] + self.move_X,
                            - center_pos[1] + self.move_Y,
                            - center_pos[2] - self.move_Z)
        # --------------------------------------------------------------------------------------------------------------
        transformedData = vtk.vtkTransformFilter()
        transformedData.SetInputConnection(self.reader_toothimplant.GetOutputPort())
        transformedData.SetTransform(transform)
        transformedData.Update()
        stlWriter = vtk.vtkSTLWriter()
        stlWriter.SetFileName(self.toothimplant_file_path)
        stlWriter.SetInputConnection(transformedData.GetOutputPort())
        stlWriter.Write()
        # --------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        self.ToothID_Implant_QStringList.insertRows(self.ToothID_Implant_QStringList.rowCount(), 1)
        index = self.ToothID_Implant_QStringList.index(self.ToothID_Implant_QStringList.rowCount() - 1)
        self.ToothID_Implant_QStringList.setData(index,
                                                 'ToothID: ' + self.ToothID_QComboBox.currentText() + ' Implant: ' + self.ToothImplant_QComboBox.currentText())
        # --------------------------------------------------------------
        ToothImplantList.Tooth_Implant_File_List.append(self.toothimplant_file_path)
        # -------------------------------------------------------
        self.logoWidget_XZ.Off()
        self.logoWidget_XY.Off()
        self.logoWidget_YZ.Off()
        self.vtkWidget_XY.Render()
        self.vtkWidget_YZ.Render()
        self.vtkWidget_XZ.Render()
        self.vtkWidget_Volume.Render()
        setIsPutImplant(False)

    def ToothID_Implant_QListView_Func(self):
        index = self.ToothID_Implant_QListView.currentIndex().row()
        if index == 0:
            return
        toothimplant_file = ToothImplantList.Tooth_Implant_File_List[index - 1]
        os.remove(toothimplant_file)
        ToothImplantList.Tooth_Implant_File_List.pop(index - 1)
        self.ToothID_Implant_QStringList.removeRows(self.ToothID_Implant_QListView.currentIndex().row(), 1)

    def horizontalSlider_implant_XY_angle_valuechange(self):
        # 判断是否点击了放置植体的面
        if not getIsPutImplant():
            print("未放置植体，还不能移动滑块")
            return
        self.init_update_viewer_information()
        # ----------------------------------------------------
        self.horizontalSlider_implant_angle_XY.setToolTip(str(self.horizontalSlider_implant_angle_XY.value()))
        self.rotation_angle_Z = self.horizontalSlider_implant_angle_XY.value()
        self.drawing_XY.Update()
        self.drawing_XY.SetDrawColor(0, 0, 0, 0)
        self.drawing_XY.FillBox(0, self.drawpaper_size, 0, self.drawpaper_size)
        self.drawing_XY.Update()
        # -------------------------------------------------------
        coords_list_temp = [[100, 75], [100, 125], [75, 100], [125, 100]]
        self.rotation_coords_list = self.rotation_shape(coords_list_temp, self.coords_origin, self.rotation_angle_Z)
        self.drawing_XY.SetDrawColor(0, 255, 0, 255)
        self.drawing_XY.FillTube(self.rotation_coords_list[0][0], self.rotation_coords_list[0][1],
                                 self.rotation_coords_list[1][0], self.rotation_coords_list[1][1], 1)
        self.drawing_XY.FillTube(self.rotation_coords_list[2][0], self.rotation_coords_list[2][1],
                                 self.rotation_coords_list[3][0], self.rotation_coords_list[3][1], 1)
        self.drawing_XY.SetDrawColor(255, 0, 0, 255)
        self.drawing_XY.DrawCircle(100, 100, self.drawcircle_radius)
        self.drawing_XY.Update()
        self.viewer_XY.Render()
        # ---------------------------------------------------------------------------
        print([self.rotation_angle_X, self.rotation_angle_Y, self.rotation_angle_Z])
        # ----------------------------------------------
        # ---------------------------------------------------------
        self.move_X = self.horizontalSlider_implant_move_Xaxis.value() / 10
        self.move_Y = self.horizontalSlider_implant_move_Yaxis.value() / 10
        self.move_Z = self.horizontalSlider_implant_move_Zaxis.value() / 10
        print([self.move_X, self.move_Y, self.move_Z])
        # ----------------------------------------------
        transform = vtk.vtkTransform()
        center_pos = VolumeRender.actor_implant.GetCenter()
        transform.Translate(center_pos)
        transform.RotateX(self.rotation_angle_Y)
        transform.RotateY(-self.rotation_angle_X)
        transform.RotateZ(self.rotation_angle_Z)
        transform.Translate(- center_pos[0] + self.move_X,
                            - center_pos[1] + self.move_Y,
                            - center_pos[2] - self.move_Z)
        # -----------------------------------------------
        VolumeRender.actor_implant.SetUserTransform(transform)
        self.vtkWidget_Volume.Render()

    def horizontalSlider_implant_YZ_angle_valuechange(self):
        self.init_update_viewer_information()
        # 判断是否点击了放置植体的面
        if not getIsPutImplant():
            print("未放置植体，还不能移动滑块")
            return
        # ------------------------------------------------------------------------------
        self.horizontalSlider_implant_angle_YZ.setToolTip(str(self.horizontalSlider_implant_angle_YZ.value()))
        self.rotation_angle_Y = self.horizontalSlider_implant_angle_YZ.value()
        self.drawing_YZ.Update()
        self.drawing_YZ.SetDrawColor(0, 0, 0, 0)
        self.drawing_YZ.FillBox(0, self.drawpaper_size, 0, self.drawpaper_size)
        self.drawing_YZ.Update()
        # -----------------------------------
        self.drawing_YZ.SetDrawColor(0, 255, 0, 255)
        # ==================================
        if self.implant_direction_cb_up.isChecked():
            rotation_angle = 0
        else:
            rotation_angle = 180
        self.rotation_coords_list = self.rotation_shape(self.coords_list, self.coords_origin,
                                                        self.rotation_angle_Y + rotation_angle)
        for i in range(len(self.rotation_coords_list)):
            if i == (len(self.rotation_coords_list) - 1):
                self.drawing_YZ.FillTube(self.rotation_coords_list[i][0], self.rotation_coords_list[i][1],
                                         self.rotation_coords_list[0][0],
                                         self.rotation_coords_list[0][1], 1)
            else:
                self.drawing_YZ.FillTube(self.rotation_coords_list[i][0], self.rotation_coords_list[i][1],
                                         self.rotation_coords_list[i + 1][0],
                                         self.rotation_coords_list[i + 1][1], 1)

        self.drawing_YZ.SetDrawColor(0, 255, 0, 255)
        self.drawing_YZ.DrawCircle(100, 100, 50)
        self.drawing_YZ.Update()
        self.viewer_YZ.Render()
        # ---------------------------------------------------------------------------
        print([self.rotation_angle_X, self.rotation_angle_Y, self.rotation_angle_Z])
        # ----------------------------------------------
        # ---------------------------------------------------------
        self.move_X = self.horizontalSlider_implant_move_Xaxis.value() / 10
        self.move_Y = self.horizontalSlider_implant_move_Yaxis.value() / 10
        self.move_Z = self.horizontalSlider_implant_move_Zaxis.value() / 10
        print([self.move_X, self.move_Y, self.move_Z])
        # ----------------------------------------------
        transform = vtk.vtkTransform()
        center_pos = VolumeRender.actor_implant.GetCenter()
        transform.Translate(center_pos)
        transform.RotateX(self.rotation_angle_Y)
        transform.RotateY(-self.rotation_angle_X)
        transform.RotateZ(self.rotation_angle_Z)
        transform.Translate(- center_pos[0] + self.move_X,
                            - center_pos[1] + self.move_Y,
                            - center_pos[2] - self.move_Z)
        # -----------------------------------------------
        VolumeRender.actor_implant.SetUserTransform(transform)
        self.vtkWidget_Volume.Render()

    def horizontalSlider_implant_XZ_angle_valuechange(self):
        self.init_update_viewer_information()
        # 判断是否点击了放置植体的面
        if not getIsPutImplant():
            print("未放置植体，还不能移动滑块")
            return
        # -------------------------------------------------------------------------------
        self.horizontalSlider_implant_angle_XZ.setToolTip(str(self.horizontalSlider_implant_angle_XZ.value()))
        self.rotation_angle_X = self.horizontalSlider_implant_angle_XZ.value()
        self.drawing_XZ.Update()
        self.drawing_XZ.SetDrawColor(0, 0, 0, 0)
        self.drawing_XZ.FillBox(0, self.drawpaper_size, 0, self.drawpaper_size)
        self.drawing_XZ.Update()
        # -----------------------------------
        self.drawing_XZ.SetDrawColor(0, 255, 0, 255)
        # ==================================
        if self.implant_direction_cb_up.isChecked():
            rotation_angle = 0
        else:
            rotation_angle = 180
        self.rotation_coords_list = self.rotation_shape(self.coords_list, self.coords_origin,
                                                        self.rotation_angle_X + rotation_angle)
        for i in range(len(self.rotation_coords_list)):
            if i == (len(self.rotation_coords_list) - 1):
                self.drawing_XZ.FillTube(self.rotation_coords_list[i][0], self.rotation_coords_list[i][1],
                                         self.rotation_coords_list[0][0],
                                         self.rotation_coords_list[0][1], 1)
            else:
                self.drawing_XZ.FillTube(self.rotation_coords_list[i][0], self.rotation_coords_list[i][1],
                                         self.rotation_coords_list[i + 1][0],
                                         self.rotation_coords_list[i + 1][1], 1)

        self.drawing_XZ.SetDrawColor(0, 255, 0, 255)
        self.drawing_XZ.DrawCircle(100, 100, 50)
        self.drawing_XZ.Update()
        self.viewer_XZ.Render()
        # ------------------------------------------------------------------------
        print([self.rotation_angle_X, self.rotation_angle_Y, self.rotation_angle_Z])
        # ----------------------------------------------
        # ----------------------------------------------
        # ---------------------------------------------------------
        self.move_X = self.horizontalSlider_implant_move_Xaxis.value() / 10
        self.move_Y = self.horizontalSlider_implant_move_Yaxis.value() / 10
        self.move_Z = self.horizontalSlider_implant_move_Zaxis.value() / 10
        print([self.move_X, self.move_Y, self.move_Z])
        # ----------------------------------------------
        transform = vtk.vtkTransform()
        center_pos = VolumeRender.actor_implant.GetCenter()
        transform.Translate(center_pos)
        transform.RotateX(self.rotation_angle_Y)
        transform.RotateY(-self.rotation_angle_X)
        transform.RotateZ(self.rotation_angle_Z)
        transform.Translate(- center_pos[0] + self.move_X,
                            - center_pos[1] + self.move_Y,
                            - center_pos[2] - self.move_Z)
        # -----------------------------------------------
        VolumeRender.actor_implant.SetUserTransform(transform)
        self.vtkWidget_Volume.Render()

    # ----------------------轴向的偏移---------------------------
    def horizontalSlider_implant_move_Axis_valuechange(self):
        self.init_update_viewer_information()
        # 判断是否点击了放置植体的面
        if not getIsPutImplant():
            print("未放置植体，还不能移动滑块")
            return
        # ---------------------------------------------------------
        self.move_X = self.horizontalSlider_implant_move_Xaxis.value() / 10
        self.horizontalSlider_implant_move_Xaxis.setToolTip(str(self.move_X))
        self.move_Y = self.horizontalSlider_implant_move_Yaxis.value() / 10
        self.horizontalSlider_implant_move_Yaxis.setToolTip(str(self.move_Y))
        self.move_Z = self.horizontalSlider_implant_move_Zaxis.value() / 10
        self.horizontalSlider_implant_move_Zaxis.setToolTip(str(self.move_Z))
        print([self.move_X, self.move_Y, self.move_Z])
        # ---------------------------------------------------------------
        print('计算画布位置开始：')
        cursorposition_ori = self.viewer_XY.GetResliceCursor().GetCenter()
        x = cursorposition_ori[0] + self.move_X
        y = cursorposition_ori[1] + self.move_Y
        z = cursorposition_ori[2] + self.move_Z
        cursorposition = [x, y, z]
        print('cursorposition', cursorposition)
        # --------------------------------------------------------------------------------
        Xangle = np.absolute(self.viewer_XZ.GetResliceCursor().GetXAxis()[0])
        Yangle = np.absolute(self.viewer_XY.GetResliceCursor().GetYAxis()[1])
        Zangle = np.absolute(self.viewer_YZ.GetResliceCursor().GetZAxis()[2])
        print([Xangle, Yangle, Zangle])
        # --------------------------------------------------------------------------------
        framewidth = self.vtkWidget_XY.frameSize().width()
        frameheight = self.vtkWidget_XY.frameSize().height()
        print([frameheight, framewidth])
        # -----------------centerpoint---------------------------------------------------
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToWorld()
        # -----------------leftbottom----------------------------------------------------
        leftbottom_point = [cursorposition[0] - self.drawpaper_center * self.spacing[0] / Xangle,
                            cursorposition[1] - self.drawpaper_center * self.spacing[1] / Yangle,
                            cursorposition[2]]
        vc.SetValue(leftbottom_point[0], leftbottom_point[1], leftbottom_point[2])
        leftbottom_point_disp = list(vc.GetComputedDisplayValue(self.viewer_XY.GetRenderer()))
        leftbottom_point_disp_normalize = [leftbottom_point_disp[0] / framewidth,
                                           leftbottom_point_disp[1] / frameheight]
        # -----------------righttop_point-------------------------------
        righttop_point = [cursorposition[0] + self.drawpaper_center * self.spacing[0] / Xangle,
                          cursorposition[1] + self.drawpaper_center * self.spacing[1] / Yangle,
                          cursorposition[2]]
        vc.SetValue(righttop_point[0], righttop_point[1], righttop_point[2])
        righttop_point_disp = list(vc.GetComputedDisplayValue(self.viewer_XY.GetRenderer()))
        righttop_point_disp_normalize = [righttop_point_disp[0] / framewidth, righttop_point_disp[1] / frameheight]
        # -------------------------------------------------------------------------------------
        # -------------------------------------------------------------------------------------
        self.logoRepresentation_XY.SetPosition(leftbottom_point_disp_normalize[0],
                                               leftbottom_point_disp_normalize[1])
        self.logoRepresentation_XY.SetPosition2(
            righttop_point_disp_normalize[0] - leftbottom_point_disp_normalize[0],
            righttop_point_disp_normalize[1] - leftbottom_point_disp_normalize[1])
        self.viewer_XY.Render()
        # -----------------------------XZ 2D 绘制----------------------------------------------------------------
        # --------------------------------------------------------------------------------
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToWorld()
        # -----------------leftbottom----------------------------------------------------
        leftbottom_point = [cursorposition[0] - self.drawpaper_center * self.spacing[0] / Xangle, cursorposition[1],
                            cursorposition[2] - self.drawpaper_center * self.spacing[2] / Zangle]
        vc.SetValue(leftbottom_point[0], leftbottom_point[1], leftbottom_point[2])
        leftbottom_point_disp = list(vc.GetComputedDisplayValue(self.viewer_XZ.GetRenderer()))
        leftbottom_point_disp_normalize = [leftbottom_point_disp[0] / framewidth,
                                           leftbottom_point_disp[1] / frameheight]
        # -----------------righttop_point-------------------------------
        righttop_point = [cursorposition[0] + self.drawpaper_center * self.spacing[0] / Xangle, cursorposition[1],
                          cursorposition[2] + self.drawpaper_center * self.spacing[2] / Zangle]
        vc.SetValue(righttop_point[0], righttop_point[1], righttop_point[2])
        righttop_point_disp = list(vc.GetComputedDisplayValue(self.viewer_XZ.GetRenderer()))
        righttop_point_disp_normalize = [righttop_point_disp[0] / framewidth, righttop_point_disp[1] / frameheight]
        # -------------------------------------------------------------------------------------
        # -------------------------------------------------
        self.logoRepresentation_XZ.SetPosition(leftbottom_point_disp_normalize[0],
                                               leftbottom_point_disp_normalize[1])
        self.logoRepresentation_XZ.SetPosition2(
            righttop_point_disp_normalize[0] - leftbottom_point_disp_normalize[0],
            righttop_point_disp_normalize[1] - leftbottom_point_disp_normalize[1])
        self.viewer_XZ.Render()
        # -----------------------------YZ 2D 绘制----------------------------------------------------------------
        # -----------------centerpoint--------------------------------------------------------------------------
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToWorld()
        # -----------------leftbottom-----------------------------------------------------------------------------
        leftbottom_point = [cursorposition[0], cursorposition[1] - self.drawpaper_center * self.spacing[1] / Yangle,
                            cursorposition[2] - self.drawpaper_center * self.spacing[2] / Zangle]
        vc.SetValue(leftbottom_point[0], leftbottom_point[1], leftbottom_point[2])
        leftbottom_point_disp = list(vc.GetComputedDisplayValue(self.viewer_YZ.GetRenderer()))
        leftbottom_point_disp_normalize = [leftbottom_point_disp[0] / framewidth,
                                           leftbottom_point_disp[1] / frameheight]
        # -----------------righttop_point-------------------------------
        righttop_point = [cursorposition[0], cursorposition[1] + self.drawpaper_center * self.spacing[1] / Yangle,
                          cursorposition[2] + self.drawpaper_center * self.spacing[2] / Zangle]
        vc.SetValue(righttop_point[0], righttop_point[1], righttop_point[2])
        righttop_point_disp = list(vc.GetComputedDisplayValue(self.viewer_YZ.GetRenderer()))
        righttop_point_disp_normalize = [righttop_point_disp[0] / framewidth, righttop_point_disp[1] / frameheight]
        # --------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------
        self.logoRepresentation_YZ.SetPosition(leftbottom_point_disp_normalize[0],
                                               leftbottom_point_disp_normalize[1])
        self.logoRepresentation_YZ.SetPosition2(
            righttop_point_disp_normalize[0] - leftbottom_point_disp_normalize[0],
            righttop_point_disp_normalize[1] - leftbottom_point_disp_normalize[1])
        self.viewer_YZ.Render()
        # -------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------
        transform = vtk.vtkTransform()
        center_pos = VolumeRender.actor_implant.GetCenter()
        transform.Translate(center_pos)
        transform.RotateX(self.rotation_angle_Y)
        transform.RotateY(-self.rotation_angle_X)
        transform.RotateZ(self.rotation_angle_Z)
        transform.Translate(- center_pos[0] + self.move_X,
                            - center_pos[1] + self.move_Y,
                            - center_pos[2] - self.move_Z)
        # -----------------------------------------------
        VolumeRender.actor_implant.SetUserTransform(transform)
        self.vtkWidget_Volume.Render()
