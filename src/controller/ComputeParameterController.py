import math

import numpy as np
import trimesh
from PyQt5.QtWidgets import QTableWidgetItem

from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.ToothImplantListModel import ToothImplantList
from src.model.VolumeRenderModel import VolumeRender
from src.widgets.ComputeParameterWidget import ComputeParameter


class ComputeParameterController(ComputeParameter):
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel, widget):
        super(ComputeParameterController).__init__()

        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.widget = widget

        self.init_widget()

        self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
        self.iren_Volume = self.viewModel.VolumeOrthorViewer.renderWindowInteractor
        self.renderer_volume = self.viewModel.VolumeOrthorViewer.renderer

        self.pushButton_compute_process_parameters.clicked.connect(self.compute_process_parameters)
        self.pushButton_clear_implant_actor.clicked.connect(self.clear_implant_actor)

    def compute_process_parameters(self):
        if len(ToothImplantList.Tooth_Implant_File_List) == 0:
            print("没有植体数据")
            return
        if not ToothImplantList.Tooth_Implant_Reg_File_List:
            return
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        # ------------------------------------------------------------------------------
        vertices_original = [0, 29.3739, 30]  # 原点`位置
        vertices_rotate_XZ = [0, 0, -92.72]  # XZ面原点位置
        vertices_rotate_YZ = [0, 4.58, 47]  # YZ面原点位置
        print(ToothImplantList.Tooth_Implant_Reg_File_List)
        # ------------------------------------------------------------------------------
        for implant_reg_file in ToothImplantList.Tooth_Implant_Reg_File_List:
            implant_name = implant_reg_file.split('/')[-1]
            implant_name = implant_name.split('_tooth_implant')[0]
            # ---------------------------------------------
            target_mesh = trimesh.load(implant_reg_file)
            vertices = target_mesh.vertices
            vertices_data = np.array(vertices)
            Zmax_ID = np.argmax(vertices_data[:, 2])
            Zmin_ID = np.argmin(vertices_data[:, 2])
            vert_top_ori = vertices_data[Zmax_ID, :]
            vert_bottom_ori = vertices_data[Zmin_ID, :]

            vert_top = vert_top_ori - vertices_original
            vert_bottom = vert_bottom_ori - vertices_original
            print(vert_top)
            print(vert_bottom)
            # ---------------YZ面---------------------------------------------
            vert_top_YZ = [vert_top[1], vert_top[2]]
            vert_bottom_YZ = [vert_bottom[1], vert_bottom[2]]
            print(vert_top_YZ)
            print(vert_bottom_YZ)
            # ------------------------------------------
            vertices_YZ_ori = [vertices_rotate_YZ[1], vertices_rotate_YZ[2]]
            print('vertices_YZ_ori', vertices_YZ_ori)
            [vert_top_rdius, vert_top_theta] = self.polar360(vert_top_YZ[0], vert_top_YZ[1], x_ori=vertices_YZ_ori[0],
                                                             y_ori=vertices_YZ_ori[1])
            [vert_bottom_rdius, vert_bottom_theta] = self.polar360(vert_bottom_YZ[0], vert_bottom_YZ[1],
                                                                   x_ori=vertices_YZ_ori[0], y_ori=vertices_YZ_ori[1])
            print([vert_top_rdius, vert_top_theta])
            print([vert_bottom_rdius, vert_bottom_theta])
            # ----------------------------------------------------------------------------------
            tanval = (vert_top_YZ[0] - vert_bottom_YZ[0]) / (vert_bottom_YZ[1] - vert_top_YZ[1])
            theta_YZ = math.degrees(math.atan(tanval))
            vert_top_y = math.sin((vert_top_theta + theta_YZ) / 180 * math.pi) * vert_top_rdius + vertices_YZ_ori[0]
            vert_bottom_y = math.sin((vert_bottom_theta + theta_YZ) / 180 * math.pi) * vert_bottom_rdius + \
                            vertices_YZ_ori[
                                0]
            vert_top_z = math.cos((vert_top_theta + theta_YZ) / 180 * math.pi) * vert_top_rdius + vertices_YZ_ori[1]
            vert_bottom_z = math.cos((vert_bottom_theta + theta_YZ) / 180 * math.pi) * vert_bottom_rdius + \
                            vertices_YZ_ori[
                                1]
            # ---------------------------------------------------------------------------------
            Delta_Y = vertices_rotate_XZ[1] - ((vert_top_y + vert_bottom_y) / 2)
            if vert_bottom[0] < 0:
                Delta_Y = - Delta_Y

            Theta_YZ_axis = theta_YZ
            # -----------------XZ面--------------------------------------------------
            kval = (vert_top_z - vertices_rotate_XZ[2]) / (vert_bottom_z - vertices_rotate_XZ[2])
            Delta_X = (kval * (vert_bottom[0] - vertices_rotate_XZ[0]) - (vert_top[0] - vertices_rotate_XZ[0])) / (
                    1 - kval)
            # -----------------------------------------------------------------
            Theta_XZ_axis = math.degrees(
                math.atan((vert_bottom[0] + Delta_X - vertices_rotate_XZ[0]) / (vert_bottom_z - vertices_rotate_XZ[2])))
            # ----------------------------------------------------------
            print(['X轴位移', 'Y轴位移', '底座旋转角度', '导板旋转角度'])
            print([Delta_Y, -Delta_X, Theta_YZ_axis, Theta_XZ_axis])
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, 0, QTableWidgetItem(implant_name))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(str(round(Delta_Y, 4))))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(str(round(-Delta_X, 4))))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(str(round(Theta_YZ_axis, 4))))
            self.tableWidget.setItem(row, 4, QTableWidgetItem(str(round(Theta_XZ_axis, 4))))
            self.tableWidget.resizeColumnsToContents()
        # ----------------------------------------------------------------------
        # show the List
        # 植体号： implant_name，X轴位移：Delta_Y, Y轴位移：-Delta_X, 底座旋转角度：Theta_YZ_axis, 导板旋转角度：Theta_XZ_axis

    def polar360(self, x_input, y_input, x_ori=0, y_ori=0):
        x = x_input - x_ori
        y = y_input - y_ori
        rdius = math.hypot(y, x)
        theta = math.degrees(math.atan2(x, y)) + (x < 0) * 360
        return rdius, theta

    def clear_implant_actor(self):
        self.renderer_volume = self.viewModel.VolumeOrthorViewer.renderer
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_implant)
        except:
            print('Close implant Actors Failed!!!')
        try:
            for actor in VolumeRender.actor_implant_reg:
                self.renderer_volume.RemoveActor(actor)
        except:
            print("close actor_implant_reg failed")

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
