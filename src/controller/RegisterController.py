import glob
import os

import vtk
from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox

from src.constant.ParamConstant import ParamConstant
from src.constant.WindowConstant import WindowConstant
from src.core.tooth_landmark_detc.Tooth_LandmarkDect_CBCT import ToothLandmark_Dect, Automatic_Registration_Landmark
from src.model.ToothImplantListModel import ToothImplantList
from src.model.VolumeRenderModel import VolumeRender
from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.utils.globalVariables import getFileIsEmpty, getDirPath, setAnchorPointIsComplete, getAnchorPointIsComplete
from src.widgets.RegisterWidget import Register


class RegisterController(Register):
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel, widget):
        super(RegisterController).__init__()

        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.widget = widget

        self.init_widget()

        self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget

        # 绑定槽函数
        self.pushButton_anchor_seg.clicked.connect(self.CBCT_anchor_seg)
        self.pushButton_anchor_load.clicked.connect(self.CBCT_anchor_load)
        self.anchor_direction_cb_up.stateChanged.connect(self.anchor_direction_cb_up_changed)
        self.anchor_direction_cb_down.stateChanged.connect(self.anchor_direction_cb_down_changed)
        self.autoanchor_cb1.stateChanged.connect(self.autoanchor_cb1_changed)
        self.autoanchor_cb2.stateChanged.connect(self.autoanchor_cb2_changed)
        self.autoanchor_cb3.stateChanged.connect(self.autoanchor_cb3_changed)
        self.autoanchor_cb4.stateChanged.connect(self.autoanchor_cb4_changed)
        self.autoanchor_cb5.stateChanged.connect(self.autoanchor_cb5_changed)
        self.autoanchor_cb6.stateChanged.connect(self.autoanchor_cb6_changed)
        self.autoanchor_cb7.stateChanged.connect(self.autoanchor_cb7_changed)
        self.autoanchor_cb8.stateChanged.connect(self.autoanchor_cb8_changed)
        self.manualanchor_cb1.stateChanged.connect(self.manualanchor_cb1_changed)
        self.manualanchor_cb2.stateChanged.connect(self.manualanchor_cb2_changed)
        self.manualanchor_cb3.stateChanged.connect(self.manualanchor_cb3_changed)
        self.manualanchor_cb4.stateChanged.connect(self.manualanchor_cb4_changed)
        self.manualanchor_cb5.stateChanged.connect(self.manualanchor_cb5_changed)
        self.manualanchor_cb6.stateChanged.connect(self.manualanchor_cb6_changed)
        self.manualanchor_cb7.stateChanged.connect(self.manualanchor_cb7_changed)
        self.manualanchor_cb8.stateChanged.connect(self.manualanchor_cb8_changed)
        self.pushButton_anchor_reg.clicked.connect(self.Anchor_Registration)
        self.pushButton_reg_adjust.clicked.connect(self.generate_implant_3D_adjust)
        self.horizontalSlider_X_Axis_Move.valueChanged.connect(self.horizontalSlider_X_Axis_Move_Function)
        self.horizontalSlider_X_Axis_Angle.valueChanged.connect(self.horizontalSlider_X_Axis_Angle_Function)
        self.horizontalSlider_Y_Axis_Move.valueChanged.connect(self.horizontalSlider_Y_Axis_Move_Function)
        self.horizontalSlider_Y_Axis_Angle.valueChanged.connect(self.horizontalSlider_Y_Axis_Angle_Function)
        self.horizontalSlider_Z_Axis_Move.valueChanged.connect(self.horizontalSlider_Z_Axis_Move_Function)
        self.horizontalSlider_Z_Axis_Angle.valueChanged.connect(self.horizontalSlider_Z_Axis_Angle_Function)


    def anchor_direction_cb_up_changed(self):
        if self.anchor_direction_cb_up.isChecked():
            self.anchor_direction_cb_down.setCheckState(0)

    def anchor_direction_cb_down_changed(self):
        if self.anchor_direction_cb_down.isChecked():
            self.anchor_direction_cb_up.setCheckState(0)

    def init_update_data_information(self):
        self.vtkWidget_Volume = self.viewModel.VolumeOrthorViewer.widget
        self.iren_Volume = self.viewModel.VolumeOrthorViewer.renderWindowInteractor
        self.renderer_volume = self.viewModel.VolumeOrthorViewer.renderer

        self.spacing = self.baseModelClass.spacing
        self.origin = self.baseModelClass.origin
        self.dims = self.baseModelClass.imageDimensions

    def CBCT_anchor_seg(self):
        if getFileIsEmpty():
            print("未导入文件，还不能开始分割与重建CBCT的金属锚点")
            return
        print('开始分割与重建CBCT的金属锚点！')
        # ----------------------------------------
        info = QtWidgets.QMessageBox()
        info.setIcon(QtWidgets.QMessageBox.Information)
        info.setWindowTitle(WindowConstant.TOOTH_LANDMARK_DETC_INFO_TITLE)
        info.setText(WindowConstant.TOOTH_LANDMARK_INFO_TEXT)
        info.show()
        ToothLandmark_Dect(getDirPath(), ParamConstant.SUBJECT_NAME, ParamConstant.OUTPUT_FILE_PATH,
                           ParamConstant.THRESHOLD_ID)
        info.exec_()
        print('分割与重建CBCT的金属锚点完成！')

    def CBCT_anchor_load(self):
        self.init_update_data_information()
        if getFileIsEmpty():
            print("未导入文件，还不能导入CBCT的金属锚点")
            return
        path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME
        landmark_files = glob.glob(path + '_ld*.stl')
        if len(landmark_files) == 0:
            api = self.loadanchor_information()
            if api == QMessageBox.AcceptRole:
                print("选择了确认")
                self.CBCT_anchor_seg()
            elif api == QMessageBox.RejectRole:
                print("选择了取消")
                return
        # ---------------------------------------------------------
        # ---------------------------------------------------------
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_mold_origin)
        except:
            print('actor_mold_origin is not found!!!')
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_reg)
        except:
            print('actor_ld_reg is not found!!!')
        try:
            self.renderer_volume.AddActor(VolumeRender.volume_cbct)
        except:
            print('volume_cbct is not found!!!')
        try:
            for actor in VolumeRender.actor_implant_reg:
                self.renderer_volume.RemoveActor(actor)
            VolumeRender.actor_implant_reg = []
        except:
            print("actor_implant_reg is not found")
        self.vtkWidget_Volume.Render()
        # ---------------------------------------------------------------------------------
        self.transform_anchor = vtk.vtkTransform()
        center_pos = VolumeRender.volume_cbct.GetCenter()

        if self.anchor_direction_cb_up.isChecked():
            self.transform_anchor.RotateX(180)
            self.transform_anchor.RotateY(180)
            self.transform_anchor.Translate(center_pos[0] - 125, center_pos[1] - 200, center_pos[2])
        else:
            self.transform_anchor.RotateX(180)
            self.transform_anchor.Translate(center_pos[0], center_pos[1] - 200, center_pos[2] - 75)

        # ============================detected anchors=================================================
        # 1-------------------------------------------------------------------------------------------
        if os.path.exists(path + '_ld_1.stl'):
            self.autoanchor_cb1.setEnabled(True)
            self.autoanchor_cb1.setCheckState(2)
        else:
            self.autoanchor_cb1.setEnabled(False)
            print('The detected 1st landmark is not found!!!')
        # 2-------------------------------------------------------------------------------------------
        if os.path.exists(path + '_ld_2.stl'):
            self.autoanchor_cb2.setEnabled(True)
            self.autoanchor_cb2.setCheckState(2)
        else:
            self.autoanchor_cb2.setEnabled(False)
            print('The detected 2nd landmark is not found!!!')

        # 3-------------------------------------------------------------------------------------------
        if os.path.exists(path + '_ld_3.stl'):
            self.autoanchor_cb3.setEnabled(True)
            self.autoanchor_cb3.setCheckState(2)
        else:
            self.autoanchor_cb3.setEnabled(False)
            print('The detected 3rd landmark is not found!!!')

        # 4-------------------------------------------------------------------------------------------
        if os.path.exists(path + '_ld_4.stl'):
            self.autoanchor_cb4.setEnabled(True)
            self.autoanchor_cb4.setCheckState(2)
        else:
            self.autoanchor_cb4.setEnabled(False)
            print('The detected 4th landmark is not found!!!')

        # 5-------------------------------------------------------------------------------------------
        if os.path.exists(path + '_ld_5.stl'):
            self.autoanchor_cb5.setEnabled(True)
            self.autoanchor_cb5.setCheckState(2)
        else:
            self.autoanchor_cb5.setEnabled(False)
            print('The detected 5th landmark is not found!!!')

        # 6-------------------------------------------------------------------------------------------
        if os.path.exists(path + '_ld_6.stl'):
            self.autoanchor_cb6.setEnabled(True)
            self.autoanchor_cb6.setCheckState(2)
        else:
            self.autoanchor_cb6.setEnabled(False)
            print('The detected 6th landmark is not found!!!')

        # 7-------------------------------------------------------------------------------------------
        if os.path.exists(path + '_ld_7.stl'):
            self.autoanchor_cb7.setEnabled(True)
            self.autoanchor_cb7.setCheckState(2)
        else:
            self.autoanchor_cb7.setEnabled(False)
            print('The detected 7th landmark is not found!!!')

        # 8-------------------------------------------------------------------------------------------
        if os.path.exists(path + '_ld_8.stl'):
            self.autoanchor_cb8.setEnabled(True)
            self.autoanchor_cb8.setCheckState(2)
        else:
            self.autoanchor_cb8.setEnabled(False)
            print('The detected 8th landmark is not found!!!')
        # --------------------------------------------------------------------------------
        # ============================manual anchors=================================================
        manualanchor_list = [self.manualanchor_cb1, self.manualanchor_cb2, self.manualanchor_cb3,
                             self.manualanchor_cb4,self.manualanchor_cb5, self.manualanchor_cb6,
                             self.manualanchor_cb7, self.manualanchor_cb8]
        for manualanchor in manualanchor_list:
            manualanchor.setEnabled(True)
            manualanchor.setCheckState(0)
            manualanchor.setCheckState(2)
        # --------------------------------------------------------------------------------
        self.vtkWidget_Volume.Render()
        self.anchor_load = True

    def loadanchor_information(self):
        font = QFont("宋体",12)
        info = QMessageBox()
        info.setIcon(QMessageBox.Information)
        info.setWindowTitle(WindowConstant.IMPLANT_INFO_TITLE)
        info.setText(WindowConstant.LOAD_ANCHOR_BEFORE_DETC_INFO_TEXT)
        info.setFixedSize(400,200)
        info.setFont(font)
        info.addButton(WindowConstant.IMPLANT_INFO_ACCEPT, QMessageBox.AcceptRole)
        info.addButton(WindowConstant.IMPLANT_INFO_REJECT, QMessageBox.RejectRole)
        api = info.exec_()
        return api

    def Anchor_Registration(self):
        if getFileIsEmpty():
            print("未导入文件，还不能开始配准锚点")
            return
        if not self.anchor_load:
            return
        setAnchorPointIsComplete(True)
        #-----------------------------------------------------------
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_implant)
        except:
            print('Close actor_implant Failed!!!')
        try:
            self.renderer_volume.RemoveActor(VolumeRender.volume_cbct)
        except:
            print('Close volume_cbct Failed!!!')
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_mold_origin)
        except:
            print('Close actor_mold_origin Failed!!!')
        try:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_reg)
        except:
            print('Close actor_ld_reg Failed!!!')
        #-------------------------------------------------------------------
        self.vtkWidget_Volume.Render()
        print('开始配准锚点！！！')
        #------------------------------------------------------------------
        self.manual_anchor_list = []
        if self.manualanchor_cb1.isChecked():
            self.manual_anchor_list.append('1')
        if self.manualanchor_cb2.isChecked():
            self.manual_anchor_list.append('2')
        if self.manualanchor_cb3.isChecked():
            self.manual_anchor_list.append('3')
        if self.manualanchor_cb4.isChecked():
            self.manual_anchor_list.append('4')
        if self.manualanchor_cb5.isChecked():
            self.manual_anchor_list.append('5')
        if self.manualanchor_cb6.isChecked():
            self.manual_anchor_list.append('6')
        if self.manualanchor_cb7.isChecked():
            self.manual_anchor_list.append('7')
        if self.manualanchor_cb8.isChecked():
            self.manual_anchor_list.append('8')
        #---------------------------------------------
        self.auto_anchor_list = []
        if self.autoanchor_cb1.isChecked():
            self.auto_anchor_list.append('1')
        if self.autoanchor_cb2.isChecked():
            self.auto_anchor_list.append('2')
        if self.autoanchor_cb3.isChecked():
            self.auto_anchor_list.append('3')
        if self.autoanchor_cb4.isChecked():
            self.auto_anchor_list.append('4')
        if self.autoanchor_cb5.isChecked():
            self.auto_anchor_list.append('5')
        if self.autoanchor_cb6.isChecked():
            self.auto_anchor_list.append('6')
        if self.autoanchor_cb7.isChecked():
            self.auto_anchor_list.append('7')
        if self.autoanchor_cb8.isChecked():
            self.auto_anchor_list.append('8')
        #--------------------------------------------------------------------------------------------
        print('Here!')
        ToothImplantList.Tooth_Implant_Reg_File_List = Automatic_Registration_Landmark(ParamConstant.SUBJECT_NAME, ParamConstant.OUTPUT_FILE_PATH,
                                                                          ParamConstant.MOLD_ANCHORPOINT_PATH,
                                                                          self.manual_anchor_list,
                                                                          self.auto_anchor_list,
                                                                          ToothImplantList.Tooth_Implant_File_List)
        print('配准锚点完成！！！')
        #--------------------------------------------------------------------------------------------
        self.manualanchor_cb1.setCheckState(0)
        self.manualanchor_cb2.setCheckState(0)
        self.manualanchor_cb3.setCheckState(0)
        self.manualanchor_cb4.setCheckState(0)
        self.manualanchor_cb5.setCheckState(0)
        self.manualanchor_cb6.setCheckState(0)
        self.manualanchor_cb7.setCheckState(0)
        self.manualanchor_cb8.setCheckState(0)

        self.autoanchor_cb1.setCheckState(0)
        self.autoanchor_cb2.setCheckState(0)
        self.autoanchor_cb3.setCheckState(0)
        self.autoanchor_cb4.setCheckState(0)
        self.autoanchor_cb5.setCheckState(0)
        self.autoanchor_cb6.setCheckState(0)
        self.autoanchor_cb7.setCheckState(0)
        self.autoanchor_cb8.setCheckState(0)
        self.vtkWidget_Volume.Render()
        # --------------------------------------------------------------------------------------------
        reader = vtk.vtkSTLReader()
        reader.SetFileName(ParamConstant.MOLD_ORIGIN_FILE_PATH)
        # ----------------------------------------------
        bounds = self.baseModelClass.bounds
        self.center0 = (bounds[1] + bounds[0]) / 2.0
        self.center1 = (bounds[3] + bounds[2]) / 2.0
        self.center2 = (bounds[5] + bounds[4]) / 2.0
        transform = vtk.vtkTransform()
        transform.Translate(self.center0, self.center1, self.center2)  # 将原点平移到中心
        # ----------------------------------------------
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        actor_mold_origin = vtk.vtkActor()
        actor_mold_origin.SetMapper(mapper)
        actor_mold_origin.GetProperty().SetColor(0, 1, 0)
        actor_mold_origin.SetUserTransform(transform)
        self.renderer_volume.AddActor(actor_mold_origin)
        VolumeRender.actor_mold_origin = actor_mold_origin
        # -----------------------------------------------------
        # --------------------------------------------------------------------------
        reader = vtk.vtkSTLReader()
        reader.SetFileName(ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_reg.stl')
        # ---------------------------------------------------------------------------
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        actor_ld_reg = vtk.vtkActor()
        actor_ld_reg.SetMapper(mapper)
        actor_ld_reg.GetProperty().SetColor(0, 0, 1)
        actor_ld_reg.SetUserTransform(transform)
        self.renderer_volume.AddActor(actor_ld_reg)
        VolumeRender.actor_ld_reg = actor_ld_reg
        # ---------------------------------------------------------------------------
        self.vtkWidget_Volume.Render()
        self.anchor_load = False

    def autoanchor_cb1_changed(self):
        if self.autoanchor_cb1.isChecked():
            anchorpoint_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_1.stl'
            VolumeRender.actor_ld_1 = self.update_auto_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_1)
        self.vtkWidget_Volume.Render()

    def autoanchor_cb2_changed(self):
        if self.autoanchor_cb2.isChecked():
            anchorpoint_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_2.stl'
            VolumeRender.actor_ld_2 = self.update_auto_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_2)
        self.vtkWidget_Volume.Render()

    def autoanchor_cb3_changed(self):
        if self.autoanchor_cb3.isChecked():
            anchorpoint_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_3.stl'
            VolumeRender.actor_ld_3 = self.update_auto_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_3)
        self.vtkWidget_Volume.Render()

    def autoanchor_cb4_changed(self):
        if self.autoanchor_cb4.isChecked():
            anchorpoint_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_4.stl'
            VolumeRender.actor_ld_4 = self.update_auto_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_4)
        self.vtkWidget_Volume.Render()

    def autoanchor_cb5_changed(self):
        if self.autoanchor_cb5.isChecked():
            anchorpoint_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_5.stl'
            VolumeRender.actor_ld_5 = self.update_auto_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_5)
        self.vtkWidget_Volume.Render()

    def autoanchor_cb6_changed(self):
        if self.autoanchor_cb6.isChecked():
            anchorpoint_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_6.stl'
            VolumeRender.actor_ld_6 = self.update_auto_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_6)
        self.vtkWidget_Volume.Render()

    def autoanchor_cb7_changed(self):
        if self.autoanchor_cb7.isChecked():
            anchorpoint_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_7.stl'
            VolumeRender.actor_ld_7 = self.update_auto_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_7)
        self.vtkWidget_Volume.Render()

    def autoanchor_cb8_changed(self):
        if self.autoanchor_cb8.isChecked():
            anchorpoint_path = ParamConstant.OUTPUT_FILE_PATH + ParamConstant.SUBJECT_NAME + '_ld_8.stl'
            VolumeRender.actor_ld_8 = self.update_auto_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_ld_8)
        self.vtkWidget_Volume.Render()

    def update_auto_anchor(self, anchorpoint_path):
        reader = vtk.vtkSTLReader()
        reader.SetFileName(anchorpoint_path)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0, 0, 1)
        self.renderer_volume.AddActor(actor)
        return actor

    def manualanchor_cb1_changed(self):
        if self.manualanchor_cb1.isChecked():
            anchorpoint_path = ParamConstant.MOLD_ANCHORPOINT_PATH + 'gangzhu-1.stl'
            VolumeRender.actor_anchor_1 = self.update_origin_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_1)
        self.vtkWidget_Volume.Render()

    def manualanchor_cb2_changed(self):
        if self.manualanchor_cb2.isChecked():
            anchorpoint_path = ParamConstant.MOLD_ANCHORPOINT_PATH + 'gangzhu-2.stl'
            VolumeRender.actor_anchor_2 = self.update_origin_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_2)
        self.vtkWidget_Volume.Render()

    def manualanchor_cb3_changed(self):
        if self.manualanchor_cb3.isChecked():
            anchorpoint_path = ParamConstant.MOLD_ANCHORPOINT_PATH + 'gangzhu-3.stl'
            VolumeRender.actor_anchor_3 = self.update_origin_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_3)
        self.vtkWidget_Volume.Render()

    def manualanchor_cb4_changed(self):
        if self.manualanchor_cb4.isChecked():
            anchorpoint_path = ParamConstant.MOLD_ANCHORPOINT_PATH + 'gangzhu-4.stl'
            VolumeRender.actor_anchor_4 = self.update_origin_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_4)
        self.vtkWidget_Volume.Render()

    def manualanchor_cb5_changed(self):
        if self.manualanchor_cb5.isChecked():
            anchorpoint_path = ParamConstant.MOLD_ANCHORPOINT_PATH + 'gangzhu-5.stl'
            VolumeRender.actor_anchor_5 = self.update_origin_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_5)
        self.vtkWidget_Volume.Render()

    def manualanchor_cb6_changed(self):
        if self.manualanchor_cb6.isChecked():
            anchorpoint_path = ParamConstant.MOLD_ANCHORPOINT_PATH + 'gangzhu-6.stl'
            VolumeRender.actor_anchor_6 = self.update_origin_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_6)
        self.vtkWidget_Volume.Render()

    def manualanchor_cb7_changed(self):
        if self.manualanchor_cb7.isChecked():
            anchorpoint_path = ParamConstant.MOLD_ANCHORPOINT_PATH + 'gangzhu-7.stl'
            VolumeRender.actor_anchor_7 = self.update_origin_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_7)
        self.vtkWidget_Volume.Render()

    def manualanchor_cb8_changed(self):
        if self.manualanchor_cb8.isChecked():
            anchorpoint_path = ParamConstant.MOLD_ANCHORPOINT_PATH + 'gangzhu-8.stl'
            VolumeRender.actor_anchor_8 = self.update_origin_anchor(anchorpoint_path)
        else:
            self.renderer_volume.RemoveActor(VolumeRender.actor_anchor_8)
        self.vtkWidget_Volume.Render()

    def update_origin_anchor(self, anchorpoint_path):
        reader = vtk.vtkSTLReader()
        reader.SetFileName(anchorpoint_path)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0, 1, 0)
        self.renderer_volume.AddActor(actor)
        return actor

    # ----------------X轴移动微调--------------------------------
    def horizontalSlider_X_Axis_Move_Function(self):
        if not getAnchorPointIsComplete():
            print("还未进行锚点配准，无法微调")
            return
        self.X_Axis_Move_value = self.horizontalSlider_X_Axis_Move.value()
        self.update_actor_ld_reg()

    # ----------------Y轴移动微调--------------------------------
    def horizontalSlider_Y_Axis_Move_Function(self):
        if not getAnchorPointIsComplete():
            print("还未进行锚点配准，无法微调")
            return
        self.Y_Axis_Move_value = self.horizontalSlider_Y_Axis_Move.value()
        self.update_actor_ld_reg()


    # ----------------Z轴移动微调--------------------------------
    def horizontalSlider_Z_Axis_Move_Function(self):
        if not getAnchorPointIsComplete():
            print("还未进行锚点配准，无法微调")
            return
        self.Z_Axis_Move_value = self.horizontalSlider_Z_Axis_Move.value()
        self.update_actor_ld_reg()

    # ----------------X轴角度微调--------------------------------
    def horizontalSlider_X_Axis_Angle_Function(self):
        if not getAnchorPointIsComplete():
            print("还未进行锚点配准，无法微调")
            return
        self.X_Axis_Angle_value = self.horizontalSlider_X_Axis_Angle.value()
        self.update_actor_ld_reg()

    # ----------------Y轴角度微调--------------------------------
    def horizontalSlider_Y_Axis_Angle_Function(self):
        if not getAnchorPointIsComplete():
            print("还未进行锚点配准，无法微调")
            return
        self.Y_Axis_Angle_value = self.horizontalSlider_Y_Axis_Angle.value()
        self.update_actor_ld_reg()

    # ----------------Z轴角度微调--------------------------------
    def horizontalSlider_Z_Axis_Angle_Function(self):
        if not getAnchorPointIsComplete():
            print("还未进行锚点配准，无法微调")
            return
        self.Z_Axis_Angle_value = self.horizontalSlider_Z_Axis_Angle.value()
        self.update_actor_ld_reg()

    def update_actor_ld_reg(self):
        transform = vtk.vtkTransform()
        transform.Translate(self.X_Axis_Move_value + self.center0, self.Y_Axis_Move_value + self.center1,
                            self.Z_Axis_Move_value + self.center2)
        transform.RotateX(self.X_Axis_Angle_value)
        transform.RotateY(self.Y_Axis_Angle_value)
        transform.RotateZ(self.Z_Axis_Angle_value)
        # -----------------------------------------------
        VolumeRender.actor_ld_reg.SetUserTransform(transform)
        self.vtkWidget_Volume.Render()

    def generate_implant_3D_adjust(self):
        if not getAnchorPointIsComplete():
            print("锚点还未配准，无法进行微调")
            return
        try:
            for actor in VolumeRender.actor_implant_reg:
                self.renderer_volume.RemoveActor(actor)
            VolumeRender.actor_implant_reg = []
        except:
            print('Close Implant_reg Actors Failed!!!')
        # --------------------------------------------------------------------------------------
        for implant_reg_file in ToothImplantList.Tooth_Implant_Reg_File_List:
            reader = vtk.vtkSTLReader()
            reader.SetFileName(implant_reg_file)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())
            actor_implant_reg = vtk.vtkActor()
            actor_implant_reg.SetMapper(mapper)
            actor_implant_reg.GetProperty().SetColor(0, 0, 1)
            # ------------------------------------------------------
            transform = vtk.vtkTransform()
            transform.Translate(self.X_Axis_Move_value, self.Y_Axis_Move_value,
                                self.Z_Axis_Move_value)
            transform.RotateX(self.X_Axis_Angle_value)
            transform.RotateY(self.Y_Axis_Angle_value)
            transform.RotateZ(self.Z_Axis_Angle_value)
            # self.actor_implant_reg.SetUserTransform(transform)
            # --------------------------------------------------------------------------
            transformedData = vtk.vtkTransformFilter()
            transformedData.SetInputConnection(reader.GetOutputPort())
            transformedData.SetTransform(transform)
            transformedData.Update()
            stlWriter = vtk.vtkSTLWriter()
            stlWriter.SetFileName(implant_reg_file)
            stlWriter.SetInputConnection(transformedData.GetOutputPort())
            stlWriter.Write()
            # -------------------------Show-------------------------------------------------------
            transform = vtk.vtkTransform()
            transform.Translate(self.X_Axis_Move_value + self.center0, self.Y_Axis_Move_value + self.center1,
                                self.Z_Axis_Move_value + self.center2)
            transform.RotateX(self.X_Axis_Angle_value)
            transform.RotateY(self.Y_Axis_Angle_value)
            transform.RotateZ(self.Z_Axis_Angle_value)
            actor_implant_reg.SetUserTransform(transform)
            VolumeRender.actor_implant_reg.append(actor_implant_reg)
            self.renderer_volume.AddActor(actor_implant_reg)
            self.vtkWidget_Volume.Render()
        print('完成植体配准！！！！')

