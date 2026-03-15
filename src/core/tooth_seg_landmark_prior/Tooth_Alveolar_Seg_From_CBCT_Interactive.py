# -*- coding: utf-8 -*-
"""
Created on Fri Jul 23 10:28:56 2021

@author: Lipeng Xie
"""
# try:
import argparse
import os
import sys

import numpy as np
import torch
from medpy.io import load, save
from scipy import ndimage
import skimage.measure as measure
import cv2
import time
import glob
import medpy

from src.core.tooth_seg_landmark_prior.nets.construct_models_pytorch import Unet_Al_Seg, \
    Unet_ToothSeg_Landmark_Alveolar_Prior


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

def BoundingBox_Coordinate(Seg,offset=20):
    H, W, C = Seg.shape
    Mask = np.sum(Seg>0,2)
    Mask_H = np.sum(Mask,1)>0
    indx_H = np.where(Mask_H)
    Mask_V = np.sum(Mask,0)>0
    indx_V = np.where(Mask_V)
    
    TL_x = max(np.min(indx_H)-offset,0)
    TL_y = max(np.min(indx_V)-offset, 0)
    BR_x = min(np.max(indx_H)+offset, H)
    BR_y = min(np.max(indx_V)+offset, W)
    
    Mask = np.sum(np.sum(Seg>0,0),0)
    mask_id_list = np.where(Mask>0)  
    mask_id_low = min(np.max(mask_id_list)+offset,C) 
    mask_id_up = max(np.min(mask_id_list)-offset,0) 
    
    return TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low

 
    
def dist_transform_object(mask):
    dt = ndimage.distance_transform_edt(1-mask)
    return dt

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


def manual_landmark_generate(Mask_ld):
    ids_list = np.unique(Mask_ld)
    ids_list = list(ids_list)
    ids_list.remove(0)
    #===================生成牙齿标记=====================
    Mask_ld_refine = np.zeros(Mask_ld.shape)
    H, W, C = Mask_ld.shape
    for ids in ids_list:
        Mask_ld_temp = Mask_ld==ids
        mask_slicearea = np.sum(np.sum(Mask_ld_temp, 0), 0)
        mask_id_list = np.where(mask_slicearea > 0)
        for jj in range(np.size(mask_id_list)-1):
            id_up = mask_id_list[0][jj]
            id_low = mask_id_list[0][jj+1] - 1
            if id_up == id_low:
                Mask_ld_refine[:, :, id_up] = Mask_ld_refine[:, :, id_up] + Mask_ld_temp[:, :, id_up] * ids
            else:
                gapnum = np.abs(id_low-id_up) + 1
                Mask_ld_a = Mask_ld_temp[:, :, id_up]*ids
                Mask_ld_a = Mask_ld_a[:, :, np.newaxis]
                Mask_ld_refine[:, :, id_up:id_up+gapnum] = Mask_ld_refine[:, :, id_up:id_up+gapnum] + np.repeat(Mask_ld_a, gapnum, 2)
        id_up = mask_id_list[0][-1]
        Mask_ld_refine[:, :, id_up] = Mask_ld_refine[:, :, id_up] + Mask_ld_temp[:, :, id_up] * ids

    return Mask_ld_refine

def txtfile2landmark(input_landmark_txtfile_path, data_shape):
    fp = open(input_landmark_txtfile_path, 'r')
    coords_data = fp.readlines()
    fp.close()
    raduis = 2
    # ============================================
    ToothLandmark = np.zeros(data_shape, np.int32)
    for ld_info in coords_data:
        ld_info = ld_info.split('\n')[0]
        ld_info = ld_info.split(',')
        toothid = np.int32(ld_info[0])
        z = np.int32(ld_info[1])
        x = np.int32(ld_info[2])
        y = np.int32(ld_info[3])
        # ----------------------------------------
        ToothLandmark[(x - raduis):(x + raduis), (y - raduis):(y + raduis), z] = toothid
    #ToothLandmark = ToothLandmark[:, :, ::-1]
    return ToothLandmark


#==========================================================
parser = argparse.ArgumentParser(description='Segment the alveolar and tooth mask from the CBCT.')
parser.add_argument('input_cbct_file_path',  help='File path of input ct images.')
parser.add_argument('input_landmark_file_path',  help='File path of input manual landmark file.')
parser.add_argument('subject_name',  help='Name of the subject.')
parser.add_argument('threshold_al',  help='Threshold value of al.')
parser.add_argument('output_file_path', help='File path of output segmentation results.')

args = parser.parse_args()
#==========================================================
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
if __name__ == '__main__':

    rootpath = sys.path[0]
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = "./resources"
    #=============Load Trained Network====================
    #====================Set parameters================================== 
    modelname_th = 'Unet_ToothSeg_Landmark_Alveolar_Prior'
    checkpoint_id_th = '19'
    #------------------------------------------------
    modelname_al = 'Unet_Al_Seg'
    checkpoint_id_al = '399'
    #===============================================
    inputchanelnum = 1
    adjnum = 1
    mean_file_name =  "./src/core/tooth_seg_landmark_prior/training.tfrecords_mean.npy"
    meanval = np.load(mean_file_name)
    img_size = [320, 320]
    data_shape = [320, 320, 1]
    offset = 50
    threshold_al = float(args.threshold_al)
    #---------------------------------------------
    batch_size = 1
    reuse= False
    #========================================================================================
    #=========================Creat AL Network===================================================
    #------------------------------
    print('Construct the alveolar segmentation model!')
    model_al = Unet_Al_Seg(feature_scale=1, up_dim=32, n_classes=2, in_channels=inputchanelnum, is_batchnorm=True,
                           is_drop=True)
    if torch.cuda.is_available():
        print('CUDA is available!!!!')
        model_al = model_al.cuda()
    else:
        print("No GPU found, please run without --cuda")
    #----------------------------------------------------------------
    print("Load existing alveolar segmentationmodel " + "!" * 10)
    if torch.cuda.is_available():
        model_al.load_state_dict(torch.load(current_dir+'/checkpoints/'+ modelname_al+'/' + "model_tfrecord_"+checkpoint_id_al+".pth"))
    else:
        model_al.load_state_dict(torch.load(current_dir+'/checkpoints/'+ modelname_al+'/' + "model_tfrecord_"+checkpoint_id_al+".pth", map_location ='cpu'))
    model_al.train()
    start_time_all = time.time()
    #================================Load Image======================================================
    dcmfiles = glob.glob(args.input_cbct_file_path + '*.dcm')
    if len(dcmfiles) == 1:
        Img_ORI, Img_header_temp = load(dcmfiles[0])
        Img_header = medpy.io.Header(spacing=Img_header_temp.get_voxel_spacing())
    else:
        Img_ORI, Img_header = load(args.input_cbct_file_path)
    #----------------------------------------------------------------------
    data_shape_ori = Img_ORI.shape
    ToothLandmark = txtfile2landmark(args.input_landmark_file_path, data_shape_ori)
    # ===============================Analyze the volume value distribution==========================
    Meanv = np.mean(Img_ORI)
    Std = np.std(Img_ORI)
    Minv = np.min(Img_ORI)
    Maxv = np.max(Img_ORI)
    normal_val_min = np.max([Minv, Meanv - 3 * Std])
    normal_val_max = np.min([Maxv, Meanv + 3 * Std])
    #======================================================================================
    Img_ori = MaxMin_normalization_Intensity(Img_ORI, normal_val_min, normal_val_max)

    if (data_shape_ori[0]!=img_size[0])|(data_shape_ori[1]!=img_size[1]):
        Flag_resize = True
        Img = np.zeros((img_size[0], img_size[1], data_shape_ori[2]))
        for i in range(data_shape_ori[2]):
            Img[:,:,i] = cv2.resize(np.float32(Img_ori[:,:,i]),(img_size[1], img_size[0]),interpolation=cv2.INTER_LINEAR)
    else:
        Flag_resize = False
        Img = np.float32(Img_ori)
    #--------------------------------------------------------
    img_shape = Img.shape
    Seg_al = np.zeros(img_shape)  
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
            outputs = model_al.forward(inputs)
            prediction_prob_al = outputs.detach().cpu().numpy()
        else:
            inputs = torch.tensor(Img_a, dtype=torch.float32).cpu()
            outputs = model_al.forward(inputs)
            prediction_prob_al = outputs.detach().numpy()
        prediction_class_al = prediction_prob_al[0:end_id_a, 1, :, :]
        Seg_al[:, :, start_id:end_id] = np.transpose(prediction_class_al, (1, 2, 0))
        start_id = start_id + batch_size

    #===========================Resize the al results==========================
    if Flag_resize==True:
        Seg_ori_al = np.float32(Seg_al)
        Seg_al = np.zeros((data_shape_ori[0], data_shape_ori[1], data_shape_ori[2]))
        for i in range(data_shape_ori[2]):
            Seg_al[:,:,i] = cv2.resize(Seg_ori_al[:,:,i],(data_shape_ori[1], data_shape_ori[0]),interpolation=cv2.INTER_LINEAR)

    #=====================上下颌骨分开=========================================
    save(np.int32(Seg_al*4096), args.output_file_path+args.subject_name+'_AlveolarProb.nii.gz',hdr=Img_header)  
    print('=======CBCT颌骨分割完成！=======')
    del model_al
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    #=======================================Get the ROI====================================================
    Seg_al = Seg_al > threshold_al
    TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low = BoundingBox_Coordinate(Seg_al, offset=offset)
    Img_crop = Img_ORI[TL_x:BR_x,TL_y:BR_y, mask_id_up:mask_id_low]
    if np.max(Img_crop) > 2500:
        Mask = np.sum(Seg_al > 0, 2)
        Mask_Al = Mask > 0
        Mask_Al_crop = Mask_Al[TL_x:BR_x, TL_y:BR_y]
        print("Mask_Al_crop.shape:",str(Mask_Al_crop.shape))
        Mask_Al_crop = np.repeat(Mask_Al_crop[:, :, np.newaxis], mask_id_low - mask_id_up, axis=2)
        Img_crop = MaxMin_normalization_Intensity_mask(Img_crop, Mask_Al_crop, normal_val_min, normal_val_max,
                                                       CompressedVal=2500)
    else:
        Img_crop = MaxMin_normalization_Intensity(Img_crop, normal_val_min, normal_val_max)
    #-------------------------------------------------------------
    Mask_al_crop = Seg_al[TL_x:BR_x,TL_y:BR_y, mask_id_up:mask_id_low]
    Mask_ld_crop = ToothLandmark[TL_x:BR_x,TL_y:BR_y, mask_id_up:mask_id_low]
    #-------------------------------------------------------------
    Mask_ld_crop = manual_landmark_generate(Mask_ld_crop)
    #--------------------------------------------------
    data_shape_crop = Img_crop.shape
    #==========================================================================================================
    if (data_shape_crop[0]!=img_size[0])|(data_shape_crop[1]!=img_size[1]):
        Flag_resize = True
        Img = np.zeros((img_size[0], img_size[1], data_shape_crop[2]))
        Mask_al = np.zeros((img_size[0], img_size[1], data_shape_crop[2]))
        Mask_ld = np.zeros((img_size[0], img_size[1], data_shape_crop[2]))
        for i in range(data_shape_crop[2]):
            Img[:,:,i] = cv2.resize(np.float32(Img_crop[:,:,i]),(img_size[1], img_size[0]),interpolation=cv2.INTER_LINEAR)
            Mask_al[:,:,i] = cv2.resize(np.float32(Mask_al_crop[:,:,i]),(img_size[1], img_size[0]),interpolation=cv2.INTER_NEAREST)
            Mask_ld[:,:,i] = cv2.resize(np.float32(Mask_ld_crop[:,:,i]),(img_size[1], img_size[0]),interpolation=cv2.INTER_NEAREST)
    else:
        Flag_resize = False
        Img = np.float32(Img_crop)
        Mask_al = np.float32(Mask_al_crop)
        Mask_ld = np.float32(Mask_ld_crop)

    img_shape = Img.shape
    Seg_th = np.zeros(img_shape, np.float32)
    start_id = 0
    iternum = np.int32(np.ceil(img_shape[2]/batch_size))
    # ----------------------------------------------------------------------------------------------
    print('Construct the tooth segmentation model!')
    model_th = Unet_ToothSeg_Landmark_Alveolar_Prior(feature_scale=1, up_dim=32, n_classes_th=2,
                                                     in_channels=inputchanelnum, is_batchnorm=True, is_drop=True)
    model_th.train()
    if torch.cuda.is_available():
        print('CUDA is available, Run with GPU')
        model_th = model_th.cuda()
    else:
        print("No GPU found, Run with CPU")

    print("Load existing model " + "!" * 10)
    if torch.cuda.is_available():
        model_th.load_state_dict(torch.load(
            current_dir + '/checkpoints/' + modelname_th + '/' + "model_tfrecord_" + checkpoint_id_th + ".pth"))
    else:
        model_th.load_state_dict(torch.load(
            current_dir + '/checkpoints/' + modelname_th + '/' + "model_tfrecord_" + checkpoint_id_th + ".pth",
            map_location='cpu'))
    # ----------------------------------------------------------------------------------------------
    #=====================Seg al=======================================================================
    for ii in range(0, iternum):
        Img_a = np.zeros((batch_size,img_shape[0],img_shape[1]), np.float32)
        Dist_al = np.zeros((batch_size, 2, img_shape[0],img_shape[1]), np.float32)
        if (start_id + batch_size) <= img_shape[2]:
            end_id = start_id + batch_size
            end_id_a = batch_size
            Img_a[0:end_id_a,:,:] = np.transpose(Img[:,:,start_id:end_id],(2,0,1))
            for kk in range(end_id_a):
                Dist_al[kk, 0, :,:] = MaxMin_normalization(dist_transform_object(Mask_al[:,:,start_id+kk]>0.5))
                Dist_al[kk, 1, :,:] = MaxMin_normalization(dist_transform_object(Mask_ld[:,:,start_id+kk]>0.5))
        else:
            end_id = img_shape[2]
            end_id_a = img_shape[2]-start_id
            Img_a[0:end_id_a,:,:] = np.transpose(Img[:,:,start_id:end_id],(2,0,1))
            for kk in range(end_id_a):
                Dist_al[kk, 0, :,:] = MaxMin_normalization(dist_transform_object(Mask_al[:,:,start_id+kk]>0.5))
                Dist_al[kk, 1, :,:] = MaxMin_normalization(dist_transform_object(Mask_ld[:,:,start_id+kk]>0.5))

        Img_a = np.float32(Img_a-meanval)
        Img_a = Img_a[:,np.newaxis,:,:]
        #==================input data============================
        if torch.cuda.is_available():
            inputs = torch.tensor(Img_a, dtype=torch.float32).cuda()
            inputs_Dist = torch.tensor(Dist_al, dtype=torch.float32).cuda()
            outputs_th = model_th.forward(inputs, inputs_Dist)
            prediction_prob_th = outputs_th.detach().cpu().numpy()
        else:
            inputs = torch.tensor(Img_a, dtype=torch.float32).cpu()
            inputs_Dist = torch.tensor(Dist_al, dtype=torch.float32).cpu()
            outputs_th = model_th.forward(inputs, inputs_Dist)
            prediction_prob_th = outputs_th.detach().numpy()

        #--------------------------------------------------------------------
        prediction_class_th = prediction_prob_th[0:end_id_a, 1, :, :]
        Seg_th[:, :, start_id:end_id] = np.transpose(prediction_class_th, (1, 2, 0))
        start_id = start_id + batch_size
    #===========================evaluate results==========================
    if Flag_resize==True:
        Seg_ori_th = np.float32(Seg_th)
        Seg_th = np.zeros((data_shape_crop[0], data_shape_crop[1], data_shape_crop[2]),np.float32)
        for i in range(data_shape_crop[2]):
            Seg_th[:,:,i] = cv2.resize(Seg_ori_th[:,:,i],(data_shape_crop[1], data_shape_crop[0]), interpolation=cv2.INTER_LINEAR)

    Seg_th_ori = np.zeros(data_shape_ori, np.float32)
    Seg_th_ori[TL_x:BR_x,TL_y:BR_y, mask_id_up:mask_id_low] = Seg_th

    save(np.int32(Seg_th_ori*4096), args.output_file_path+args.subject_name+'_ToothProb.nii.gz',hdr=Img_header)
    print('=======CBCT牙齿分割完成！=======')
    
