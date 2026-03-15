# -*- coding: utf-8 -*-
"""
Created on Fri Jul 23 10:28:56 2021

@author: Lipeng Xie
"""
import numpy as np
import torch
# try:
from medpy.io import load, save
import os
import sys
import skimage.measure as measure
import cv2
import time
import glob
import medpy
from skimage.measure import marching_cubes_lewiner
import trimesh
from random import shuffle
import skimage.morphology as morphology

from src.core.tooth_landmark_detc.nets.construct_models_pytorch import Resnet_Unet


# except:
#     print('The python environment is wrong!!!!')

def MaxMin_normalization_Intensity(I, Max_Minval, Min_Maxval):
    # ======================
    # I: HxW
    # ======================
    Ic = np.where(I > Min_Maxval, Min_Maxval, I)
    Ic = np.where(Ic < Max_Minval, Max_Minval, Ic)
    II = (Ic - Max_Minval) / (Min_Maxval - Max_Minval + 0.00001)

    return II

def MaxMin_normalization_Intensity_mask(I, mask, Max_Minval, Min_Maxval, CompressedVal=2500):
    #======================
    # I: HxW
    #======================
    I_f = I*mask
    I_b = I*(1-mask)
    I_bc = (I_b>Min_Maxval)*Min_Maxval+(I_b<Max_Minval)*Max_Minval+(I_b<=Min_Maxval)*(I_b>=Max_Minval)*I_b
    I_fc = (I_f>CompressedVal)*CompressedVal+(I_f<Max_Minval)*Max_Minval+(I_f<=CompressedVal)*(I_f>=Max_Minval)*I_f
    Ic = I_bc + I_fc
    II=(Ic-Max_Minval)/(Min_Maxval-Max_Minval)
    return II

def save_max_objects(img):
    if np.sum(img)<=0:
        return img
    labels = measure.label(img)
    jj = measure.regionprops(labels)
    # is_del = False
    if len(jj) == 1:
        out = img
        # is_del = False
    else:
        num = labels.max()
        del_array = np.array([0] * (num + 1))
        for k in range(num):
            if k == 0:
                initial_area = jj[0].area
                save_index = 1
            else:
                k_area = jj[k].area
                if initial_area < k_area:
                    initial_area = k_area
                    save_index = k + 1

        del_array[save_index] = 1
        del_mask = del_array[labels]
        out = img * del_mask
        # is_del = True
    return out


def save_max_numobjects(img, maxnum=8):
    if np.sum(img) <= 0:
        return img
    labels = measure.label(img)
    regions = measure.regionprops(labels)
    num = labels.max()
    if num <= maxnum:
        out = img
    else:
        regionarea_list = []
        for k in range(num):
            regionarea_list.append(regions[k].area)
        sortlist = np.argsort(regionarea_list)
        for k in range(num - maxnum):
            id = regions[k].label
            labels[labels==id] = 0

        out = labels > 0
        # is_del = True
    return out

def remove_objects_threshold(img,threshold=100):
    if np.sum(img)<=0:
        return img
    labels = measure.label(img, connectivity=3)
    jj = measure.regionprops(labels)
    if len(jj) == 1:
        out = img
    else:
        num = labels.max()
        del_array = np.array([0] * (num + 1))
        for k in range(num):
            k_area = jj[k].area
            if k_area < threshold:     
                labels[labels==(k+1)] = 0
    del_mask = labels>0
    out = img * del_mask
    return out


def MaxMin_normalization(I):
    #=================================================================================
    # I: HxW
    #======================
    Maxval = np.max(I)
    Minval = np.min(I)
    II=(I-Minval)/(Maxval-Minval)
    return II


def MaxMin_normalization_MeanSTD(I):
    # ======================
    # I: HxW
    # ======================
    Meanv = np.mean(I)
    Std = np.std(I)
    Minv = np.min(I)
    Max_Minval = Minv
    Min_Maxval = Meanv + 5 * Std

    Ic = (I > Min_Maxval) * Min_Maxval + (I < Max_Minval) * Max_Minval + (I <= Min_Maxval) * (I >= Max_Minval) * I
    II = (Ic - Max_Minval) / (Min_Maxval - Max_Minval)
    return II

def PCA_compute(Ver_source):
    Coord_means_s = np.mean(Ver_source, 0)
    Ver_source_rm = Ver_source - Coord_means_s
    VV_s = np.dot(np.transpose(Ver_source_rm), Ver_source_rm)
    [Vx_s, Vy_s] = np.linalg.eig(VV_s)
    # ===============sort==========================
    sort = Vx_s.argsort()[::-1]
    Vx_s = Vx_s[sort]
    Vy_s = Vy_s[:, sort]

    index = np.argmax(np.sum(Ver_source_rm * Ver_source_rm, 1))
    xm = Ver_source_rm[index, :]
    xm[2] = -abs(xm[2])
    p1 = Vy_s[1, :]
    if np.dot(xm, p1) < 0:
        p1 = -p1

    p2 = Vy_s[2, :]
    if np.dot(xm, p2) < 0:
        p2 = -p2

    p3 = np.cross(p1, p2)
    P_s = np.stack((p1, p2, p3))
    return Coord_means_s, P_s


def ICP_Compute(Vtrans, Ver_target, select_num=20000, reflectionflag=True, scaleflag=False, max_iterations=500):
    ids = np.int32(np.linspace(0, len(Vtrans) - 1, len(Vtrans)))
    shuffle(ids)
    ids = ids[0:select_num]
    Vtrans_sample = Vtrans[ids, :]

    ids = np.int32(np.linspace(0, len(Ver_target) - 1, len(Ver_target)))
    shuffle(ids)
    ids = ids[0:select_num]
    Ver_target_sample = Ver_target[ids, :]
    matrix, transformed, cost = trimesh.registration.icp(Vtrans_sample, Ver_target_sample,
                                                         max_iterations=max_iterations, reflection=reflectionflag,
                                                         scale=scaleflag)
    return matrix, transformed, cost


def Mutiple_ICP_Compute(vertics_source, vertics_std, vert_normals_source, vert_normals_std, select_num=5000,
                        reflectionflag=True, scaleflag=False, max_iterations=500):
    Coord_means_source, P_source = PCA_compute(vertics_source)
    Coord_means_std, P_std = PCA_compute(vertics_std)
    # ---------------------------------------------------------------
    Register_Parameters = []
    cost_list = []
    direction_list = []
    for ii in range(3):
        Parameters = []
        if ii == 0:
            Rotation_M = np.dot(np.linalg.inv(P_source), P_std)
            Trans_V = Coord_means_std - np.dot(Coord_means_source, Rotation_M)
            vert_normals_source_M = np.dot(vert_normals_source, Rotation_M)
            direction = np.dot(vert_normals_source_M, vert_normals_std)
            direction_list.append(direction)

            Vtrans = vertics_source
            Vtrans = np.dot(Vtrans, Rotation_M)
            Vtrans = Vtrans + Trans_V
            matrix, transformed, cost = ICP_Compute(Vtrans, vertics_std, select_num=select_num,
                                                    reflectionflag=reflectionflag, scaleflag=scaleflag,
                                                    max_iterations=max_iterations)
            Parameters.append(Rotation_M)
            Parameters.append(Trans_V)
            Parameters.append(matrix)
            Register_Parameters.append(Parameters)
            cost_list.append(cost)

        elif ii == 1:
            Rotation_M = np.dot(np.linalg.inv(P_source), P_std)
            Rm = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
            Rotation_M = np.dot(Rotation_M, Rm)
            Trans_V = Coord_means_std - np.dot(Coord_means_source, Rotation_M)
            vert_normals_source_M = np.dot(vert_normals_source, Rotation_M)
            direction = np.dot(vert_normals_source_M, vert_normals_std)
            direction_list.append(direction)

            Vtrans = vertics_source
            Vtrans = np.dot(Vtrans, Rotation_M)
            Vtrans = Vtrans + Trans_V
            matrix, transformed, cost = ICP_Compute(Vtrans, vertics_std, select_num=select_num,
                                                    reflectionflag=reflectionflag, scaleflag=scaleflag,
                                                    max_iterations=max_iterations)
            Parameters.append(Rotation_M)
            Parameters.append(Trans_V)
            Parameters.append(matrix)
            Register_Parameters.append(Parameters)
            cost_list.append(cost)
        else:
            Rotation_M = np.dot(np.linalg.inv(P_source), P_std)
            Rm = np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]])
            Rotation_M = np.dot(Rotation_M, Rm)
            Trans_V = Coord_means_std - np.dot(Coord_means_source, Rotation_M)
            vert_normals_source_M = np.dot(vert_normals_source, Rotation_M)
            direction = np.dot(vert_normals_source_M, vert_normals_std)
            direction_list.append(direction)

            Vtrans = vertics_source
            Vtrans = np.dot(Vtrans, Rotation_M)
            Vtrans = Vtrans + Trans_V
            matrix, transformed, cost = ICP_Compute(Vtrans, vertics_std, select_num=select_num,
                                                    reflectionflag=reflectionflag, scaleflag=scaleflag,
                                                    max_iterations=max_iterations)
            Parameters.append(Rotation_M)
            Parameters.append(Trans_V)
            Parameters.append(matrix)
            Register_Parameters.append(Parameters)
            cost_list.append(cost)


    print('Cost is ' + str(cost_list))
    print('Direction is ' + str(direction_list))

    Index = np.argmin(cost_list)
    Rotation_M, Trans_V, matrix = Register_Parameters[Index]
    return Rotation_M, Trans_V, matrix


def Verts_divide(Verts, Verts_normal, mode, ratio=0.5):
    Vt = Verts
    Vtz = Vt[:, 2]
    Minz = np.min(Vtz[:])
    Maxz = np.max(Vtz[:])
    lenz = Maxz - Minz

    if mode == 'Upper':
        VertID = Vtz <= (Minz + lenz * ratio)
        Verts_R = Verts[VertID, :]
        Verts_normal_R = Verts_normal[VertID, :]
    else:
        VertID = Vtz >= (Maxz - lenz * ratio)
        Verts_R = Verts[VertID, :]
        Verts_normal_R = Verts_normal[VertID, :]

    return Verts_R, Verts_normal_R


def landmark_refine(landmark_result, maxnum=8, radius=2):
    labels = measure.label(landmark_result)
    regions = measure.regionprops(labels)
    struct = morphology.ball(radius)
    num = labels.max()
    landmark_new = np.zeros_like(landmark_result)
    if num <= maxnum:
        for region in regions:
            center_coord = np.int32(region.centroid)
            landmark_new[(center_coord[0]-radius):(center_coord[0]+radius+1), (center_coord[1]-radius):(center_coord[1]+radius+1), (center_coord[2]-radius):(center_coord[2]+radius+1)] = struct
    else:
        regionarea_list = []
        for k in range(num):
            regionarea_list.append(regions[k].area)
        sortlist = np.argsort(regionarea_list)
        for k in range(num - maxnum):
            id = regions[sortlist[k]].label
            labels[labels == id] = 0
        regions = measure.regionprops(labels)
        for region in regions:
            center_coord = np.int32(region.centroid)
            landmark_new[(center_coord[0]-radius):(center_coord[0]+radius+1), (center_coord[1]-radius):(center_coord[1]+radius+1), (center_coord[2]-radius):(center_coord[2]+radius+1)] = struct
    return landmark_new


def Automatic_Registration_Landmark(subject_name, output_file_path, mold_anchorpoint_path, manual_anchor_list, auto_anchor_list, toothimplant_File_List):
    # =============================Step1: Load Source STL===========================================================
    Ver_source = []
    Ver_normal_source = []
    Face_source = []
    ii = 0
    for id in auto_anchor_list:
        output_file_path_landmark = output_file_path + subject_name + '_ld_' + id + '.stl'
        Meshdata_source = trimesh.load(output_file_path_landmark)
        Vt = Meshdata_source.vertices
        Vn = Meshdata_source.vertex_normals
        Ft = Meshdata_source.faces
        NumVt = len(Ver_source)
        if ii == 0:
            Face_source = Ft
            Ver_source = Vt
            Ver_normal_source = Vn
        else:
            Ft = Ft + NumVt
            Ver_source = np.vstack((Ver_source, Vt))
            Face_source = np.vstack((Face_source, Ft))
            Ver_normal_source = np.vstack((Ver_normal_source, Vn))
        ii = ii + 1

    #==============================Step2: Load Target STL===========================================================
    Ver_target = []
    Ver_normal_target = []
    ii = 0
    for id in manual_anchor_list:
        Meshdata_target = trimesh.load(mold_anchorpoint_path + 'gangzhu-' + id + '.stl')
        Vt = Meshdata_target.vertices
        Vn = Meshdata_target.vertex_normals
        if ii == 0:
            Ver_target = Vt
            Ver_normal_target = Vn
        else:
            Ver_target = np.vstack((Ver_target, Vt))
            Ver_normal_target = np.vstack((Ver_normal_target, Vn))
        ii = ii + 1
    # ==============================================================================================================
    # ============================Step3: Registeration1=============================================================
    print('Start Multiple ICP')
    vert_normals_source = np.mean(Ver_normal_source, 0)
    vert_normals_source = vert_normals_source / np.sqrt(np.sum(vert_normals_source ** 2))
    vert_normals_target = np.mean(Ver_normal_target, 0)
    vert_normals_target = vert_normals_target / np.sqrt(np.sum(vert_normals_target ** 2))
    Rotation_M, Trans_V, matrix = Mutiple_ICP_Compute(Ver_source, Ver_target,
                                                        vert_normals_source,
                                                        vert_normals_target, select_num=50000,
                                                        reflectionflag=True, scaleflag=False)

    np.save(output_file_path + subject_name + '_PCA_Trans_V.npy', Trans_V)
    np.save(output_file_path + subject_name + '_PCA_Rotation_M.npy', Rotation_M)
    np.save(output_file_path + subject_name + '_ICP_matrix.npy', matrix)
    # =================================================================================================================
    Vertices_up = Ver_source
    Vertices_up_trans = np.dot(Vertices_up, Rotation_M)
    Vertices_up_trans = Vertices_up_trans + Trans_V
    Vertices_up_trans = trimesh.transform_points(Vertices_up_trans, matrix)
    LandmarkMesh = trimesh.Trimesh(Vertices_up_trans, Face_source, validate=True)
    LandmarkMesh.export(output_file_path + subject_name + '_ld_reg.stl')
    #-------------------------------------------------------------------------------------------------
    toothimplant_Reg_File_List = []
    for implantfile in toothimplant_File_List:
        print(implantfile)
        filename = implantfile.split('.stl')[0]
        print(filename)
        ToothImplantMesh = trimesh.load(implantfile)
        Vertices_up = ToothImplantMesh.vertices
        Vertices_up_trans = np.dot(Vertices_up, Rotation_M)
        Vertices_up_trans = Vertices_up_trans + Trans_V
        Vertices_up_trans = trimesh.transform_points(Vertices_up_trans, matrix)
        implantMesh = trimesh.Trimesh(Vertices_up_trans, ToothImplantMesh.faces, validate=True)
        tempname = filename + '_reg.stl'
        toothimplant_Reg_File_List.append(tempname)
        implantMesh.export(tempname)
    return toothimplant_Reg_File_List


#==========================================================
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
def ToothLandmark_Dect(input_cbct_file_path, subject_name,  output_file_path, threshold_ld=0.5, moldnum = 8):
    rootpath = sys.path[0]
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # print(current_dir)
    current_dir = './resources'
    #=============Load Trained Network====================
    #------------------------------------------------
    modelname_ld = 'Resnet_Unet'
    checkpoint_id_ld = '299'
    BN_enable = True
    resnet_pretrain = False
    in_channels = 1
    out_channels = 2
    #===============================================
    mean_file_name = current_dir +'/training.tfrecords_mean.npy'
    meanval = np.load(mean_file_name)
    img_size = [320, 320]
    # data_shape = [320, 320, 1]
    # offset = 50
    #---------------------------------------------
    batch_size = 1
    #========================================================================================
    #=========================Creat AL Network===================================================
    #------------------------------
    print('Construct the landmark segmentation model!')
    model_ld = Resnet_Unet(BN_enable=BN_enable, resnet_pretrain=resnet_pretrain, in_channels= in_channels, out_channels= out_channels)
    if torch.cuda.is_available():
        print('CUDA is available!!!!')
        model_ld = model_ld.cuda()
    else:
        print("No GPU found, please run without --cuda")
    #----------------------------------------------------------------
    print("Load existing landmark segmentation model " + "!" * 10)
    if torch.cuda.is_available():
        model_ld.load_state_dict(torch.load(current_dir+'/checkpoints/'+ modelname_ld+'/' + "model_tfrecord_"+checkpoint_id_ld+".pth"))
    else:
        model_ld.load_state_dict(torch.load(current_dir+'/checkpoints/'+ modelname_ld+'/' + "model_tfrecord_"+checkpoint_id_ld+".pth", map_location ='cpu'))
    model_ld.train()
    start_time = time.time()
    #================================Load Image======================================================
    dcmfiles = glob.glob(input_cbct_file_path + '*.dcm')
    if len(dcmfiles) == 1:
        Img_ORI, Img_header_temp = load(dcmfiles[0])
        Img_header = medpy.io.Header(spacing=Img_header_temp.get_voxel_spacing())
    else:
        Img_ORI, Img_header = load(input_cbct_file_path)
    #----------------------------------------------------------------------
    data_shape_ori = Img_ORI.shape
    #======================================================================================
    Img_ori = MaxMin_normalization_MeanSTD(Img_ORI)
    if (data_shape_ori[0]!=img_size[0])|(data_shape_ori[1]!=img_size[1]):
        Flag_resize = True
        Img = np.zeros((img_size[0], img_size[1], data_shape_ori[2]), np.float32)
        for i in range(data_shape_ori[2]):
            Img[:,:,i] = cv2.resize(np.float32(Img_ori[:,:,i]),(img_size[1], img_size[0]),interpolation=cv2.INTER_LINEAR)
    else:
        Flag_resize = False
        Img = np.float32(Img_ori)
    #--------------------------------------------------------
    img_shape = Img.shape
    Seg_ld = np.zeros(img_shape, np.float32)
    start_id = 0
    iternum = np.int32(np.ceil(img_shape[2]/batch_size))
    #=====================Seg al=======================================================================
    for ii in range(0, iternum):
        Img_a = np.zeros((batch_size,img_shape[0],img_shape[1]))
        if (start_id + batch_size) <= img_shape[2]:
            end_id = start_id + batch_size
            end_id_a = batch_size
            Img_a[0:end_id_a,:,:] = np.transpose(Img[:,:,start_id:end_id],(2,0,1))
        else:
            end_id = img_shape[2]
            end_id_a = img_shape[2]-start_id
            Img_a[0:end_id_a,:,:] = np.transpose(Img[:,:,start_id:end_id],(2,0,1))
        
        Img_a = np.float32(Img_a-meanval)
        Img_a = Img_a[:,np.newaxis,:,:]
        #==================input data============================
        if torch.cuda.is_available():
            inputs = torch.tensor(Img_a, dtype=torch.float32).cuda()
            outputs = model_ld.forward(inputs)
            prediction_prob_ld = outputs.detach().cpu().numpy()
        else:
            inputs = torch.tensor(Img_a, dtype=torch.float32).cpu()
            outputs = model_ld.forward(inputs)
            prediction_prob_ld = outputs.detach().numpy()
        prediction_class_ld = prediction_prob_ld[0:end_id_a, 1, :, :]
        Seg_ld[:, :, start_id:end_id] = np.transpose(prediction_class_ld, (1, 2, 0))
        start_id = start_id + batch_size
    #===========================Resize the al results==========================
    if Flag_resize==True:
        Seg_ori_ld = np.float32(Seg_ld)
        Seg_ld = np.zeros((data_shape_ori[0], data_shape_ori[1], data_shape_ori[2]), np.float32)
        for i in range(data_shape_ori[2]):
            Seg_ld[:,:,i] = cv2.resize(Seg_ori_ld[:,:,i],(data_shape_ori[1], data_shape_ori[0]),interpolation=cv2.INTER_LINEAR)
    #=====================上下颌骨分开=========================================
    del Seg_ori_ld
    #-----------------------------------------------------------------------
    Seg_ld = Seg_ld > threshold_ld
    Seg_ld = landmark_refine(Seg_ld, maxnum=moldnum, radius=3)
    save(np.int32(Seg_ld), output_file_path + subject_name + '_ld.nii.gz', hdr=Img_header)
    #-------------------adjust the direction---------------------------------------------------
    Seg_ld = np.rot90(Seg_ld, 2, axes=(0, 1))
    Seg_ld = np.rot90(Seg_ld, 2, axes=(0, 2))
    Seg_ld = measure.label(Seg_ld > 0)
    num = Seg_ld.max()
    for ii in range(num):
        temp = Seg_ld==(ii + 1)
        verts, faces, normals, values = marching_cubes_lewiner(temp, level=0.5, spacing=Img_header.get_voxel_spacing())
        surf_mesh = trimesh.Trimesh(verts, faces, validate=True)
        surf_mesh.export(output_file_path + subject_name + '_ld_'+ str(ii + 1) +'.stl')
    print('#=======CBCT锚点检测完成！=======')
    print("#=======牙齿锚点检测时间：%f" % (time.time() - start_time))
    del model_ld
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    #=======================================Get the ROI====================================================



# if __name__ == "__main__":
#     print('Start!')
#     Datapath = '../../Dataset_CBCT/'
#     threshold_ld = 0.7
#     output_file_path = './output/'
#     # =================================================
#     #---------------------------------------------------
#     if not os.path.exists(output_file_path):
#         os.mkdir(output_file_path)
#     #===========================================
#     patientnum = '43'
#     print('#======Processing PatientID: ' + patientnum + '===========#')
#     input_cbct_file_path = Datapath + patientnum + '/'
#     subject_name = patientnum
#     moldnum = 8
#     #=========================================================================================
#     # ToothLandmark_Dect(input_cbct_file_path,  subject_name,  output_file_path,  threshold_ld, moldnum)
#     Automatic_Registration_Landmark(subject_name,  output_file_path, './', ['1', '2', '3', '4', '5', '6', '7', '8'],
#                                     ['1', '2', '3', '4', '5', '6', '7', '8'], ['./output/43_45_3510_tooth_implant.stl'])
