# -*- coding: utf-8 -*-
"""
Created on Thu Jul 22 13:52:44 2021

@author: Lipeng Xie
"""

#==========================2022/11/17 修改========================
# try:
import numpy as np
from medpy.io import load, save
import os
from scipy import ndimage
import skimage.measure as measure
from skimage import morphology
from skimage import segmentation
from skimage.measure import marching_cubes_lewiner
import trimesh
from random import shuffle
from sklearn.neighbors import NearestNeighbors
import glob
import threading
import math
from skimage.draw import circle
import open3d as o3d
import time
import medpy
from skimage.draw import polygon2mask
import matplotlib.pyplot as plt
# except:
#     exit(0)
#     print('The python environment is wrong!!!!')
#==========================2022/11/17 修改========================



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
            if direction > 0:
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
            if direction > 0:
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
            if direction > 0:
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


def Meshfeature_extraction(Mesh):
    faces = Mesh.faces
    vert = Mesh.vertices

    x1 = faces[:, 0]
    x2 = faces[:, 1]
    x3 = faces[:, 2]

    face_coordinate = (vert[x1, :] + vert[x2, :] + vert[x3, :]) / 3
    faces_normal = Mesh.face_normals
    faces_angel = Mesh.face_angles
    vert_curvature = trimesh.curvature.discrete_gaussian_curvature_measure(Mesh, Mesh.vertices, 1)
    face_curvature = np.vstack((vert_curvature[x1], vert_curvature[x2], vert_curvature[x3]))
    face_curvature = np.transpose(face_curvature)

    vert_degree = Mesh.vertex_degree
    face_degree = np.vstack((vert_degree[x1], vert_degree[x2], vert_degree[x3]))
    face_degree = np.transpose(face_degree)

    vert_defects = Mesh.vertex_defects
    face_defects = np.vstack((vert_defects[x1], vert_defects[x2], vert_defects[x3]))
    face_defects = np.transpose(face_defects)

    X = np.hstack((face_coordinate, faces_normal, faces_angel, face_curvature, face_degree, face_defects))  # feature
    return X


def face_coordinate_extraction(Mesh):
    faces = Mesh.faces
    vert = Mesh.vertices

    x1 = faces[:, 0]
    x2 = faces[:, 1]
    x3 = faces[:, 2]
    face_coordinate = (vert[x1, :] + vert[x2, :] + vert[x3, :]) / 3

    return face_coordinate


def face_coordinate_compute(faces, vert):
    x1 = faces[:, 0]
    x2 = faces[:, 1]
    x3 = faces[:, 2]
    face_coordinate = (vert[x1, :] + vert[x2, :] + vert[x3, :]) / 3

    return face_coordinate


def mesh_divide(Mesh_ori, mode, ratio=0.5):
    Mesh = Mesh_ori
    face_coordinate = face_coordinate_extraction(Mesh)
    Vt = face_coordinate
    Vtz = Vt[:, 2]
    Minz = np.min(Vtz[:])
    Maxz = np.max(Vtz[:])
    lenz = Maxz - Minz

    if mode == 'Upper':
        faces = Mesh.faces
        faceID = np.where(Vtz >= (Minz + lenz * ratio))
        faces[faceID, :] = 0
        Mesh.faces = faces[1:, :]
        Mesh.remove_duplicate_faces()
        Mesh.remove_unreferenced_vertices()
    else:
        faces = Mesh.faces
        faceID = np.where(Vtz <= (Maxz - lenz * ratio))
        faces[faceID, :] = 0
        Mesh.faces = faces[1:, :]
        Mesh.remove_duplicate_faces()
        Mesh.remove_unreferenced_vertices()

    return Mesh


def Relabel(Slice):
    if np.sum(Slice) > 0:
        Maxid = np.max(Slice)
        lablenew = np.zeros(Slice.shape, np.int32)
        max_label = 0
        for i in range(1, np.int32(Maxid + 1)):
            mask = Slice == i
            labels = measure.label(mask)
            lablenew = lablenew + (max_label * mask + labels)
            max_label = np.max(lablenew)
        return lablenew
    else:
        return np.zeros(Slice.shape, np.int32)


def Tooth3D_Reconstruct_3D_Coarse(Masktooth_multi, overlap_rate):
    # =============================从顶向下合并=================================
    img_shape = Masktooth_multi.shape
    Masktooth_rec = np.zeros(img_shape, np.int32)
    Masktooth_rec = Masktooth_rec + Masktooth_multi
    ids_union = np.unique(Masktooth_rec)
    ids_union = list(ids_union)
    if ids_union.count(0) == 1:
        ids_union.remove(0)
    for ii in range(len(ids_union)):
        mask = Masktooth_multi == ids_union[ii]
        mask_slicearea = np.sum(np.sum(mask, 0), 0)
        mask_id_list = np.where(mask_slicearea > 0)
        mask_id_down = np.int32(np.max(mask_id_list))
        mask_down = mask[:, :, mask_id_down]

        if (mask_id_down + 1) < img_shape[2]:
            mask_union = mask_down * Masktooth_multi[:, :, mask_id_down + 1]
        else:
            continue

        if np.sum(mask_union > 0) == 0:
            continue
        else:
            ids_union_slice = np.unique(mask_union)
            ids_union_slice = list(ids_union_slice)
            if ids_union_slice.count(0) == 1:
                ids_union_slice.remove(0)

            mask_union_area = []
            for kk in range(0, len(ids_union_slice)):
                mask_union_area.append(np.sum(mask_union == ids_union_slice[kk]))
            mask_union_max = np.int32(np.argmax(mask_union_area))

            if ((mask_union_area[mask_union_max]) / np.sum(mask_down)) > overlap_rate:
                Masktooth_rec[Masktooth_rec == ids_union[ii]] = ids_union_slice[mask_union_max]

    return Masktooth_rec


def Tooth3D_Reconstruct_3D(Masktooth_multi, Toothprob, threshold_th, mode, spacing, threshold_v, overlap_rate,
                           Id_used=0):
    img_shape = Masktooth_multi.shape
    Masktooth_rec = np.zeros(img_shape, np.int32)
    Masktooth_rec = Masktooth_rec + Masktooth_multi
    ids_union = np.unique(Masktooth_rec)
    ids_union = list(ids_union)
    if ids_union.count(0) == 1:
        ids_union.remove(0)
    for ii in range(len(ids_union)):
        mask = Masktooth_multi == ids_union[ii]
        mask_slicearea = np.sum(np.sum(mask, 0), 0)
        mask_id_list = np.where(mask_slicearea > 0)
        mask_id_up = np.int32(np.min(mask_id_list))
        mask_up = mask[:, :, mask_id_up]

        if (mask_id_up - 1) >= 0:
            mask_union = mask_up * Masktooth_multi[:, :, mask_id_up - 1]
        else:
            continue

        if np.sum(mask_union > 0) == 0:
            continue
        else:
            ids_union_slice = np.unique(mask_union)
            ids_union_slice = list(ids_union_slice)
            if ids_union_slice.count(0) == 1:
                ids_union_slice.remove(0)
            mask_union_area = []
            for kk in range(0, len(ids_union_slice)):
                mask_union_area.append(np.sum(mask_union == ids_union_slice[kk]))
            mask_union_max = np.int32(np.argmax(mask_union_area))

            if ((mask_union_area[mask_union_max]) / np.sum(mask_up)) > overlap_rate:
                Masktooth_rec[Masktooth_rec == ids_union[ii]] = ids_union_slice[mask_union_max]
    # ================Reduce the ID=============================================================
    Masktooth_Rec = np.zeros(img_shape, np.int32)
    ToothID_list = []
    ids_union = np.unique(Masktooth_rec)
    ids_union = list(ids_union)
    if ids_union.count(0) == 1:
        ids_union.remove(0)
    Id_used = Id_used
    for kk in range(len(ids_union)):
        mask = Masktooth_rec == ids_union[kk]
        mask_sum = np.sum(np.sum(mask, 0), 0)
        length = np.sum(mask_sum > 0)
        volume = np.sum(mask_sum)
        if ((volume * spacing[0] * spacing[1] * spacing[2]) > threshold_v) & (length * spacing[2] > 10):
            toothmask = ToothRefine(mask, Toothprob, threshold_th, mode)
            Masktooth_Rec = Masktooth_Rec + (toothmask) * (Id_used + 1)
            ToothID_list.append(Id_used + 1)
            Id_used = Id_used + 1
    return Masktooth_Rec, ToothID_list


def BoundingBox_Coordinate(Seg, offset=20):
    H, W, C = Seg.shape
    Mask = np.sum(Seg > 0, 2)
    Mask_H = np.sum(Mask, 1) > 0
    indx_H = np.where(Mask_H)
    Mask_V = np.sum(Mask, 0) > 0
    indx_V = np.where(Mask_V)

    TL_x = max(np.min(indx_H) - offset, 0)
    TL_y = max(np.min(indx_V) - offset, 0)
    BR_x = min(np.max(indx_H) + offset, H)
    BR_y = min(np.max(indx_V) + offset, W)

    Mask = np.sum(np.sum(Seg > 0, 0), 0)
    mask_id_list = np.where(Mask > 0)
    mask_id_low = min(np.max(mask_id_list) + offset, C)
    mask_id_up = max(np.min(mask_id_list) - offset, 0)

    return TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low


def Toothmask2mesh(mask, spacing, smoothfactor=2.0, threshold_mesh=2000):
    TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low = BoundingBox_Coordinate(mask)
    seg = np.float32(mask[TL_x:BR_x, TL_y: BR_y, mask_id_up:mask_id_low] > 0)
    seg = ndimage.filters.gaussian_filter(seg, sigma=smoothfactor, truncate=8.0)

    Seg = np.zeros(mask.shape)
    Seg[TL_x:BR_x, TL_y: BR_y, mask_id_up:mask_id_low] = seg
    verts, faces, normals, values = marching_cubes_lewiner(Seg, level=0.5, spacing=spacing, step_size=1.0)
    # ================save the surface=====================
    return faces, verts


def Toothfake_classify(Img_ori, Tooth_label):
    Voxelvalues = Img_ori * (Tooth_label > 0)
    Meanv = np.mean(Voxelvalues[Tooth_label > 0])
    Sigmav = np.std(Voxelvalues[Tooth_label > 0])
    #    print("Mean: %f, STD: %f" %(Meanv, Sigmav))
    threshold_tooth = Meanv + 5 * Sigmav
    ToothID = np.unique(Tooth_label)
    ToothID = list(ToothID)
    if ToothID.count(0) == 1:
        ToothID.remove(0)

    FaketoothID = []
    for ids in ToothID:
        mask = Tooth_label == ids
        maxv = np.max(Img_ori[mask])
        if maxv >= threshold_tooth:
            FaketoothID.append(ids)

    return ToothID, FaketoothID



def MaxMin_normalization_Intensity(I, Max_Minval, Min_Maxval):
    # ======================
    # I: HxW
    # ======================
    Ic = (I > Min_Maxval) * Min_Maxval + (I < Max_Minval) * Max_Minval + (I <= Min_Maxval) * (I >= Max_Minval) * I
    II = (Ic - Max_Minval) / (Min_Maxval - Max_Minval)
    return II


def save_max_objects(img):
    if np.sum(img) <= 0:
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


def savestl(mask, spacing, subjname, savepath, smoothfactor=2.0):
    TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low = BoundingBox_Coordinate(mask)
    seg = np.float32(mask[TL_x:BR_x, TL_y: BR_y, mask_id_up:mask_id_low] > 0)
    seg = ndimage.filters.gaussian_filter(seg, sigma=smoothfactor, truncate=8.0)

    Seg = np.zeros(mask.shape)
    Seg[TL_x:BR_x, TL_y: BR_y, mask_id_up:mask_id_low] = seg

    verts, faces, normals, values = marching_cubes_lewiner(Seg, level=0.5, spacing=spacing, step_size=1.0)
    # ================save the surface=====================
    surf_mesh = trimesh.Trimesh(verts, faces, validate=True)
    mesh_conn = trimesh.graph.connected_components(surf_mesh.face_adjacency, min_len=1)
    label = np.zeros(len(surf_mesh.faces), dtype=bool)
    label[mesh_conn[0]] = True
    surf_mesh.update_faces(label)
    surf_mesh.remove_duplicate_faces()
    surf_mesh.remove_unreferenced_vertices()

    surf_mesh.export(savepath + subjname + '.stl')


def Savestl_Mutithread(Mask, threadnum, spacing, subjname, savepath, smoothfactor=2.0, ids_list=None):
    if ids_list == None:
        ids_list = np.unique(Mask)
        ids_list = list(ids_list)
        ids_list.remove(0)
    iternum = np.int32(np.ceil(len(ids_list) / threadnum))
    ids_start = 0
    for jj in range(iternum):
        if len(ids_list) >= threadnum * (jj + 1):
            ids_list_temp = ids_list[ids_start:ids_start + threadnum]
            ids_start = ids_start + threadnum
        else:
            ids_list_temp = ids_list[ids_start:]

        t_obj = []
        for ii in ids_list_temp:
            mask = Mask == ii
            t = threading.Thread(target=savestl, args=(mask, spacing, subjname + '_' + str(ii), savepath, smoothfactor))
            t_obj.append(t)
            t.start()

        for t in t_obj:
            t.join()


def polar360(x, y):
    rdius = math.hypot(x, y)
    theta = math.degrees(math.atan2(y, x)) + (y < 0) * 360
    return rdius, theta


def Interactive_vert_read(txtfile):
    fp = open(txtfile, 'r')
    vertsdata = fp.readlines()
    fp.close()

    ii = 0
    verts = np.zeros((len(vertsdata), 3))
    for vert in vertsdata:
        vert = vert.split('\n')[0]
        vert_list = vert.split(' ')
        verts[ii, :] = np.array(vert_list, np.float32)
        ii = ii + 1
    return verts


def Verts_to_coordinate(verts, spacing):
    H, W = verts.shape
    spacingdata = np.array(spacing)
    spacingdata = np.reshape(spacingdata, (1, W))
    coordinates = np.zeros((H, 3))
    for ii in range(H):
        vert = verts[ii, :]
        coordinates[ii, :] = vert / spacingdata
    return np.int32(coordinates)


def Coordinate_interpolate(Coordinates):
    CoordinateZ = Coordinates[:, 2]
    Index = np.argsort(CoordinateZ)
    Coordinates_sort = Coordinates[Index, :]
    LenZaxis = Coordinates_sort[-1, 2] - Coordinates_sort[0, 2] + 1
    Coordinates_inter = np.zeros((LenZaxis, 3))
    star_id = 0
    for ii in range(0, len(Index) - 1):
        Num = Coordinates_sort[ii + 1, 2] - Coordinates_sort[ii, 2] + 1
        x_intp = np.linspace(Coordinates_sort[ii, 0], Coordinates_sort[ii + 1, 0], Num) + 5
        y_intp = np.linspace(Coordinates_sort[ii, 1], Coordinates_sort[ii + 1, 1], Num)
        z_intp = np.linspace(Coordinates_sort[ii, 2], Coordinates_sort[ii + 1, 2], Num)
        coord = np.stack((x_intp, y_intp, z_intp), axis=1)
        Coordinates_inter[star_id:(star_id + Num - 1), :] = coord[0:Num - 1, :]
        star_id = star_id + Num - 1
    Coordinates_inter[-1, :] = Coordinates_sort[-1, :] + np.array([5, 0, 0])
    return np.int32(Coordinates_inter)


def Coordinate_to_landmark(Masktooth_multi, Toothlandmark, Coordinates_List):
    # =====================step1 separate the tooth==============================
    img_shape = Masktooth_multi.shape
    Landmark = np.zeros(img_shape, np.int32)
    Landmark_over = np.zeros(img_shape, np.int32)
    # ==========================================================================
    theta_range = 0.5
    TL_x, BR_x, TL_y, BR_y, _, _ = BoundingBox_Coordinate(Masktooth_multi > 0, offset=0)
    x_c = (TL_x + BR_x) / 2
    y_c = BR_y

    Angelmap = np.zeros((img_shape[0], img_shape[1]))
    for i in range(img_shape[0]):
        for j in range(img_shape[1]):
            Angelmap[i, j] = math.degrees(math.atan2(y_c - j, x_c - i)) + (y_c - j < 0) * 360

    for Coordinates in Coordinates_List:
        N = Coordinates.shape[0]
        for ii in range(N):
            r_ld, theta_ld = polar360(x_c - Coordinates[ii, 0], y_c - Coordinates[ii, 1])
            if (theta_ld + theta_range) > 360:
                Landmark[:, :, Coordinates[ii, 2]] = Landmark[:, :, Coordinates[ii, 2]] + (Angelmap >= theta_ld)
                Landmark[:, :, Coordinates[ii, 2]] = Landmark[:, :, Coordinates[ii, 2]] + (Angelmap >= 0) * (
                            Angelmap <= (theta_ld + theta_range - 360))
            else:
                Landmark[:, :, Coordinates[ii, 2]] = Landmark[:, :, Coordinates[ii, 2]] + (Angelmap >= theta_ld) * (
                            Angelmap <= (theta_ld + theta_range))

            if (theta_ld - theta_range) < 0:
                Landmark[:, :, Coordinates[ii, 2]] = Landmark[:, :, Coordinates[ii, 2]] + (Angelmap < theta_ld)
                Landmark[:, :, Coordinates[ii, 2]] = Landmark[:, :, ii] + (Angelmap < 360) * (
                            Angelmap > (360 - theta_range + theta_ld))
            else:
                Landmark[:, :, Coordinates[ii, 2]] = Landmark[:, :, Coordinates[ii, 2]] + (Angelmap < theta_ld) * (
                            Angelmap > (theta_ld - theta_range))

        Landmark_over = Landmark_over + Landmark
        temp = Landmark[:, :, Coordinates[0, 2]]
        Landmark[:, :, 0:Coordinates[0, 2]] = np.repeat(temp[:, :, np.newaxis], Coordinates[0, 2], axis=2)
        temp = Landmark[:, :, Coordinates[ii, 2]]
        Landmark[:, :, Coordinates[ii, 2]:] = np.repeat(temp[:, :, np.newaxis], img_shape[2] - Coordinates[ii, 2],
                                                        axis=2)
        # =======================create the interval===============================
    Landmark = Landmark > 0
    Mask_overlap = Masktooth_multi * (Landmark_over > 0)
    ids_over = list(np.unique(Mask_overlap))
    if np.max(ids_over) != 0:
        if ids_over.count(0) == 1:
            ids_over.remove(0)

        if len(ids_over) == 1:
            ids_over = ids_over[0]
        else:
            mask_union_area = []
            for jj in ids_over:
                mask_union_area.append(-np.sum(Mask_overlap == jj))
            mask_union_idx = np.int32(np.argsort(mask_union_area))
            ids_over = ids_over[mask_union_idx[0]]

        Mask_overlap = Masktooth_multi == ids_over
        Toothlandmark = Toothlandmark * Mask_overlap
        Mask_landmark = Toothlandmark * (1 - Landmark)

        landmarks = measure.label(Mask_landmark, connectivity=1)
        if np.max(landmarks) == 2:
            Toothlandmark_Rec = landmarks
        else:
            ids_union = np.unique(landmarks)
            ids_union = list(ids_union)
            if ids_union.count(0) == 1:
                ids_union.remove(0)
            mask_union_area = []
            for jj in ids_union:
                mask_union_area.append(-np.sum(landmarks == jj))
            mask_union_idx = np.int32(np.argsort(mask_union_area))
            mask = landmarks == ids_union[mask_union_idx[0]]
            Toothlandmark_Rec = mask
            mask = landmarks == ids_union[mask_union_idx[1]]
            Toothlandmark_Rec = Toothlandmark_Rec + mask * 2

    return Toothlandmark_Rec


def Save_multistl_Rename_Repair(Mask, ID_sepa, mode, spacing, subjname, savepath, smoothfactor=2.5,
                                threshold_mesh=2000):
    ids_list = np.unique(Mask)
    ids_list = list(ids_list)
    ids_list.remove(0)

    for ii in ids_list:
        mask = Mask == ii
        TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low = BoundingBox_Coordinate(mask)
        seg = np.float32(mask[TL_x:BR_x, TL_y: BR_y, mask_id_up:mask_id_low] > 0)
        seg = ndimage.filters.gaussian_filter(seg, sigma=smoothfactor, truncate=8.0)

        Seg = np.zeros(mask.shape)
        Seg[TL_x:BR_x, TL_y: BR_y, mask_id_up:mask_id_low] = seg

        verts, faces, normals, values = marching_cubes_lewiner(Seg, level=0.5, spacing=spacing, step_size=1.0)
        # ================save the surface=====================
        surf_mesh = trimesh.Trimesh(verts, faces, validate=True)
        mesh_conn = trimesh.graph.connected_components(surf_mesh.face_adjacency, min_len=1)
        label = np.zeros(len(surf_mesh.faces), dtype=bool)
        label[mesh_conn[0]] = True
        surf_mesh.update_faces(label)
        surf_mesh.remove_duplicate_faces()
        surf_mesh.remove_unreferenced_vertices()
        surf_mesh.export(savepath + subjname + '_' + mode + 'Tooth_' + str(np.int32(ID_sepa)) + '.stl')


def Save_multitooth_stl(Mask, mode, spacing, subjname, savepath, smoothfactor=2.5):
    ids_list = np.unique(Mask)
    ids_list = list(ids_list)
    ids_list.remove(0)

    for ii in ids_list:
        mask = Mask == ii
        TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low = BoundingBox_Coordinate(mask)
        seg = np.float32(mask[TL_x:BR_x, TL_y: BR_y, mask_id_up:mask_id_low] > 0)
        seg = ndimage.filters.gaussian_filter(seg, sigma=smoothfactor, truncate=8.0)

        Seg = np.zeros(mask.shape)
        Seg[TL_x:BR_x, TL_y: BR_y, mask_id_up:mask_id_low] = seg

        verts, faces, normals, values = marching_cubes_lewiner(Seg, level=0.5, spacing=spacing, step_size=1.0)
        # ================save the surface=====================
        surf_mesh = trimesh.Trimesh(verts, faces, validate=True)
        mesh_conn = trimesh.graph.connected_components(surf_mesh.face_adjacency, min_len=1)
        label = np.zeros(len(surf_mesh.faces), dtype=bool)
        label[mesh_conn[0]] = True
        surf_mesh.update_faces(label)
        surf_mesh.remove_duplicate_faces()
        surf_mesh.remove_unreferenced_vertices()
        surf_mesh.export(savepath + subjname + '_' + mode + 'Tooth_' + str(np.int32(ii)) + '.stl')


def manual_landmark_generate2(Mask_ld, radius=3):
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


def manual_landmark_generate3(Mask_ld):
    regions = measure.regionprops(Mask_ld)
    #===================生成牙齿标记=====================
    Mask_ld_Refine = np.zeros(Mask_ld.shape)
    for region in regions:
        ids = region.label
        Mask_ld_temp = region.image
        TL_x, TL_y, mask_id_up, BR_x, BR_y, mask_id_low = region.bbox
        Mask_ld_refine = np.zeros(Mask_ld_temp.shape)
        #--------------------------------------------------
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
        Mask_ld_Refine[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low] = Mask_ld_Refine[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low] + Mask_ld_refine
    return Mask_ld_Refine

def dist_transform_object(mask):
    dt = ndimage.distance_transform_edt(1 - mask)
    return dt


def Toothsepa_upperlower(Multitooth, Dist_up, Dist_lower, Toothprob, threshold_ld):
    # -----------------------------------------------------------------------
    Multitooth_upper = np.zeros(Multitooth.shape, np.int32)
    ToothIDupper = []
    Multitooth_lower = np.zeros(Multitooth.shape, np.int32)
    ToothIDlower = []
    #------------------------------------------------------------------------
    ToothRegions = measure.regionprops(Multitooth)
    #===================================================
    for region in ToothRegions:
        mask_th = region.image
        TL_x, TL_y, mask_id_up, BR_x, BR_y, mask_id_low = region.bbox
        toothprob = Toothprob[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low]
        dist_up = np.sum(Dist_up[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low])
        dist_lower = np.sum(Dist_lower[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low])
        #------------------------------------------------------------------------
        if dist_up < dist_lower:
            mode = 'Upper'
            toothmask = ToothRefine(mask_th, toothprob, threshold_ld, mode)
            ToothIDupper.append(region.label)
            Multitooth_upper[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low] = Multitooth_upper[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low] + toothmask * region.label
        else:
            #---------------------------------------------------------
            mode = 'Lower'
            toothmask = ToothRefine(mask_th, toothprob, threshold_ld, mode)
            ToothIDlower.append(region.label)
            Multitooth_lower[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low] = Multitooth_lower[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low] + toothmask * region.label

    return Multitooth_upper, ToothIDupper, Multitooth_lower, ToothIDlower


def ToothRefine(Toothmask, Toothprob, threshold_th, mode):
    img_shape = Toothmask.shape
    threshold_val = np.linspace(threshold_th, 1, img_shape[2])
    if mode == 'Lower':
        threshold_val = threshold_val[::-1]
    threshold_val = np.reshape(threshold_val, (1, 1, img_shape[2]))
    threshold_val_matrix = np.repeat(threshold_val, img_shape[0], axis=0)
    threshold_val_matrix = np.repeat(threshold_val_matrix, img_shape[1], axis=1)
    Mask = (Toothmask * Toothprob) > threshold_val_matrix
    return Mask

def txtfile2landmark(input_landmark_txtfile_path, data_shape):
    fp = open(input_landmark_txtfile_path, 'r')
    coords_data = fp.readlines()
    fp.close()
    raduis = 3
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
    return  ToothLandmark

#===================2022/11/15 修改==================================================
def txtfile2al_landmark(input_landmark_txtfile_path, data_shape):
    fp = open(input_landmark_txtfile_path, 'r')
    coords_data = fp.readlines()
    fp.close()
    Lower_mask = []
    Lower_z = 0
    Up_mask = []
    Up_z = 0
    # ============================================
    AlLandmark = np.zeros(data_shape, np.int32)
    for ld_info in coords_data:
        ld_info = ld_info.split('\n')[0]
        ld_info = ld_info.split(',')
        toothid = np.int32(ld_info[0])
        z = np.int32(ld_info[1])
        x = np.int32(ld_info[2])
        y = np.int32(ld_info[3])
        if toothid == 1:
            Lower_mask.append([x, y])
            Lower_z = z
        elif toothid == 2:
            Up_mask.append([x, y])
            Up_z = z
    # ----------------------------------------
    AlLandmark[:, :, Lower_z] = polygon2mask((data_shape[0], data_shape[1]), np.array(Lower_mask))
    AlLandmark[:, :, Up_z] = polygon2mask((data_shape[0], data_shape[1]), np.array(Up_mask))
    return AlLandmark

# ===================2022/12/05 修改==================================================
def toothseg2txtfile(Tooth_Multi, toothtxtfile_path):
    #==============================================
    fp = open(toothtxtfile_path, 'w+')
    #=============================================
    ids_union = np.unique(Tooth_Multi)
    ids_union = list(ids_union)
    ids_union.remove(0)
    for kk in range(len(ids_union)):
        toothID = ids_union[kk]
        mask = Tooth_Multi == toothID
        TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low = BoundingBox_Coordinate(mask, offset=1)
        for ii in range(mask_id_up, mask_id_low):
            mask2d = mask[:, :, ii]
            if np.sum(mask2d)==0:
                continue
            mask2d = ndimage.binary_fill_holes(mask2d)
            labels = measure.label(mask2d, connectivity=1)
            ids_list = np.unique(labels)
            ids_list = list(ids_list)
            ids_list.remove(0)
            for ids in ids_list:
                mask_r = labels==ids
                # mask_r = ndimage.binary_fill_holes(mask_r)
                contour_coord = measure.find_contours(mask_r, 0.5)
                if len(contour_coord)>0:
                    contour_coord = contour_coord[0]
                    for jj in range(len(contour_coord)):
                        temp = str(toothID) + ',' + str(ii) + ',' + str(ids) + ','+ str(contour_coord[jj,0]) + ',' + str(contour_coord[jj,1]) + '\n'
                        fp.write(temp)
    fp.close()

def txtfile2toothseg(toothtxtfile_path, data_shape):
    #==============================================
    fp = open(toothtxtfile_path, 'r')
    coords_data = fp.readlines()
    fp.close()
    #=============================================
    Tooth_Multi = np.zeros(data_shape, np.int32)
    ld_info = coords_data[0]
    ld_info = ld_info.split('\n')[0]
    ld_info = ld_info.split(',')
    toothid = np.int32(ld_info[0])
    z = np.int32(ld_info[1])
    regid = np.int32(ld_info[2])
    #=============================================
    coord_list = []
    start_id = toothid
    start_z = z
    start_regid = regid
    kk = 0
    for ld_info in range(len(coords_data)):
        ld_info = coords_data[kk]
        ld_info = ld_info.split('\n')[0]
        ld_info = ld_info.split(',')
        toothid = np.int32(ld_info[0])
        z = np.int32(ld_info[1])
        regid = np.int32(ld_info[2])
        x = np.float(ld_info[3])
        y = np.float(ld_info[4])
        #===========================================
        if (kk + 1) == len(coords_data):
            coord_list.append([x, y])
            mask = polygon2mask((data_shape[0], data_shape[1]), np.array(coord_list))
            Tooth_Multi[mask, start_z] = start_id
            return Tooth_Multi
        else:
            if (z==start_z) & (toothid==start_id) &(regid==start_regid):
                coord_list.append([x,y])
            else:
                mask = polygon2mask((data_shape[0], data_shape[1]), np.array(coord_list))
                Tooth_Multi[mask, start_z] = start_id
                coord_list = []
                coord_list.append([x, y])
                #=================================
                start_id = toothid
                start_z = z
                start_regid = regid
        kk = kk + 1

#=================================================================================
# Function: 分割CBCT中的颌骨与单牙齿，并进行三维重建
# Parameters: 1) input_cbct_file_path: 待分割CBCT数据路径
#             2) input_landmark_txtfile_path: 手工标记的关键点坐标txt文件路径
#             3) subject_name: 受试者名称
#             4) output_file_path: 输出文件路径
#             5) flag_seg: 是否调用深度学习模型分割CBCT
#             6) threshold_th: 牙齿分割阈值
#             7) threshold_al: 颌骨分割阈值
#             8) smoothfactor: 平滑因子
# Return: None
#=================================================================================
def Step1_CBCT_ToothAlveolar_Seg(input_cbct_file_path, input_landmark_txtfile_path, subject_name, output_file_path, flag_seg, threshold_th, threshold_al, smoothfactor, erosion_radius_up, erosion_radius_low):
    Time_start = time.time()  # 开始时间
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = "./src/core/tooth_seg_landmark_prior/"
    # =====================================
    if not os.path.exists(output_file_path):
        os.mkdir(output_file_path)
    # =====================================
    output_file_path = output_file_path
    if not os.path.exists(output_file_path):
        os.mkdir(output_file_path)
    # =====================================
    if flag_seg == 'True':
        cmdline = 'python ' + current_dir + 'Tooth_Alveolar_Seg_From_CBCT_Interactive.py ' + input_cbct_file_path + ' ' + input_landmark_txtfile_path + ' ' + subject_name + ' ' + str(
            threshold_al) + ' ' + output_file_path
        print('=============开始分割CBCT!============\n')
        os.system(cmdline)
        print('=============分割CBCT结束!=============\n')
        print("深度学习耗费时间：%f" % (time.time() - Time_start))
    else:
        print('=============跳过CBCT分割步骤!============\n')

    # =======================================
    # =========================颌骨分开====================================================================
    print('=============开始分离上下颌骨!=============\n')
    try:
        print(output_file_path + subject_name + '_AlveolarProb.nii.gz')
        Alprob, Img_header = load(output_file_path + subject_name + '_AlveolarProb.nii.gz')
    except:
        print('错误：=============请设置arg_flag_seg=True，完成牙齿分割!============\n')
        exit()
    Alprob = np.float64(Alprob)

    Seg_al_prob = Alprob / 4096
    Seg_al = Seg_al_prob > threshold_al
    # ==========================2023/02/07 修改================================
    labels = measure.label(Seg_al > 0, connectivity=2)
    regions = measure.regionprops(labels)
    regions_area = []
    for region in regions:
        regions_area.append(region.area)
    regions_list = np.argsort(-np.array(regions_area))
    Seg_al1 = labels == (regions_list[0] + 1)
    x1, y1, z1, x2, y2, z2 = regions[regions_list[0]].bbox
    minz1 = z1
    Seg_al2 = labels == (regions_list[1] + 1)
    x1, y1, z1, x2, y2, z2 = regions[regions_list[1]].bbox
    minz2 = z1
    #-------------------------------------------------------------------------
    if minz1 < minz2:
        Seg_al_up = Seg_al2
        Seg_al_bottom = Seg_al1
    else:
        Seg_al_up = Seg_al1
        Seg_al_bottom = Seg_al2
    #-----------------------------------------------------------------------------
    save(np.int32(Seg_al_up > 0), output_file_path + subject_name + '_AlveolarUpper.nii.gz', hdr=Img_header,
         use_compression=True)
    save(np.int32(Seg_al_bottom > 0), output_file_path + subject_name + '_AlveolarLower.nii.gz', hdr=Img_header,
         use_compression=True)
    print('=============分离上下颌骨结束!=============\n')
    del Seg_al
    del Seg_al_prob
    del Seg_al1
    del Seg_al2
    del Alprob
    del labels
    del regions
    # =====================================================================================================
    ToothProb, Img_header = load(output_file_path + subject_name + '_ToothProb.nii.gz')
    data_shape_ori = ToothProb.shape
    Seg_th_ori = np.float32(ToothProb) / 4096
    del ToothProb
    # ====================================================================================================
    ToothLandmark = txtfile2landmark(input_landmark_txtfile_path, data_shape_ori)
    # ====================================================================================================
    # ====================牙齿分开=============================================
    print('=============开始分离牙齿!=============\n')
    Seg_th = Seg_th_ori > threshold_th
    TL_x, BR_x, TL_y, BR_y, mask_id_up, mask_id_low = BoundingBox_Coordinate(Seg_th, offset=10)
    Seg_th = Seg_th[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low]
    Seg_th_prob = Seg_th_ori[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low]
    # ========================================================================
    print('=============生成牙齿标记!=============')
    toothmarkers = ToothLandmark[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low]
    toothmarkers = manual_landmark_generate3(toothmarkers)
    # =========================================================================
    Seg_al_upmask = Seg_al_up[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low]
    Seg_al_lowmask = Seg_al_bottom[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low]
    # -------------------------------------------------------------------------
    markers = toothmarkers * (Seg_th > 0)
    distance = ndimage.distance_transform_edt(Seg_th > 0)
    Multitooth = segmentation.watershed(-distance, markers=markers, mask=Seg_th > 0)
    Dist_up = -distance * Seg_al_upmask
    Dist_lower = -distance * Seg_al_lowmask
    # ==========================================================================
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    del distance
    del markers
    del Seg_th
    # =====================================================================================================================
    Tooth_label_upper, ToothIDupper, Tooth_label_lower, ToothIDlower = Toothsepa_upperlower(Multitooth, Dist_up,
                                                                                            Dist_lower, Seg_th_prob,
                                                                                            threshold_th)

    Tooth_label = Tooth_label_upper + Tooth_label_lower
    print('=============分离牙齿结束!=============\n')
    print('===========Upper ID: ' + str(ToothIDupper))
    print('===========Lower ID: ' + str(ToothIDlower))
    np.save(output_file_path + subject_name +'_ToothIDupper.npy', ToothIDupper)
    np.save(output_file_path + subject_name +'_ToothIDlower.npy', ToothIDlower)
    # =================================================================================================
    # ==================================================================================================
    Tooth_Rec = np.zeros(data_shape_ori, np.int32)
    Tooth_Rec[TL_x:BR_x, TL_y:BR_y, mask_id_up:mask_id_low] = np.int32(Tooth_label)
    save(Tooth_Rec, output_file_path + subject_name + '_individualtooth_seg.nii.gz', hdr=Img_header,
         use_compression=True)
    print("牙齿分割与重建耗费时间：%f" % (time.time() - Time_start))
    #====================================================================================================
    # =================================================================
    # --------------------------------------------------------
    print('=============Generate Upper Tooth mesh!=============\n')
    Savestl_Mutithread(Tooth_Rec, 2, Img_header.spacing, subject_name + '_' + 'UpperTooth', output_file_path,
                       smoothfactor=smoothfactor, ids_list=ToothIDupper)
    print('=============Generate Lower Tooth mesh!=============\n')
    Savestl_Mutithread(Tooth_Rec, 2, Img_header.spacing, subject_name + '_' + 'LowerTooth', output_file_path,
                       smoothfactor=smoothfactor, ids_list=ToothIDlower)
    # ===========================================================================
    Mask = Tooth_Rec == 0
    Mask = ndimage.binary_dilation(Mask, structure=morphology.ball(erosion_radius_up))
    Seg_al_up_refine = np.logical_and(Seg_al_up, Mask)
    Seg_al_up_refine = save_max_objects(Seg_al_up_refine)
    save(np.int32(Seg_al_up_refine > 0), output_file_path + subject_name + '_AlveolarUpper_Refine.nii.gz',
         hdr=Img_header,
         use_compression=True)
    Faces_up, Vertices_up = Toothmask2mesh(Seg_al_up_refine, Img_header.spacing, smoothfactor)
    AlMeshupper = trimesh.Trimesh(Vertices_up, Faces_up, validate=True)
    mesh_conn = trimesh.graph.connected_components(AlMeshupper.face_adjacency, min_len=1)
    label = np.zeros(len(AlMeshupper.faces), dtype=bool)
    label[mesh_conn[0]] = True
    AlMeshupper.update_faces(label)
    AlMeshupper.remove_duplicate_faces()
    AlMeshupper.remove_unreferenced_vertices()
    AlMeshupper.export(output_file_path + subject_name + '_UpperAl.stl')
    del Seg_al_up_refine
    del Seg_al_up
    # --------------------------------------------------------------------------
    Mask = Tooth_Rec == 0
    Mask = ndimage.binary_dilation(Mask, structure=morphology.ball(erosion_radius_low))
    Seg_al_bottom_refine = np.logical_and(Seg_al_bottom, Mask)
    Seg_al_bottom_refine = save_max_objects(Seg_al_bottom_refine)
    save(np.int32(Seg_al_bottom_refine > 0), output_file_path + subject_name + '_AlveolarLower_Refine.nii.gz',
         hdr=Img_header, use_compression=True)
    Faces_bottom, Vertices_bottom = Toothmask2mesh(Seg_al_bottom_refine, Img_header.spacing, smoothfactor)
    AlMeshbottom = trimesh.Trimesh(Vertices_bottom, Faces_bottom, validate=True)
    mesh_conn = trimesh.graph.connected_components(AlMeshbottom.face_adjacency, min_len=1)
    label = np.zeros(len(AlMeshbottom.faces), dtype=bool)
    label[mesh_conn[0]] = True
    AlMeshbottom.update_faces(label)
    AlMeshbottom.remove_duplicate_faces()
    AlMeshbottom.remove_unreferenced_vertices()
    AlMeshbottom.export(output_file_path + subject_name + '_LowerAl.stl')
    # =============================================================================
    print('#============Step1 CBCT ToothAlveolar Segmentation is completed!==========#')


    return 0


if __name__ == "__main__":
    Datapath = './testdata/'
    Landmarkpath = './testdata/'
    flag_seg = 'True'
    threshold_th = 0.95
    threshold_al = 0.9
    smoothfactor = 3.0
    erosion_radius_up = 3
    erosion_radius_low = 3
    output_file_path = './output/'
    # =================================================
    #---------------------------------------------------
    if not os.path.exists(output_file_path):
        os.mkdir(output_file_path)
    #===========================================
    patientnum = '04'
    print('#======Processing PatientID: ' + patientnum + '===========#')
    input_cbct_file_path = Datapath + patientnum + '/'
    input_landmark_txtfile_path = Landmarkpath + patientnum + '/' + patientnum + '_landmark.txt'
    subject_name = patientnum
    Step1_CBCT_ToothAlveolar_Seg(input_cbct_file_path, input_landmark_txtfile_path, subject_name, output_file_path, flag_seg, threshold_th,
                                     threshold_al, smoothfactor, erosion_radius_up, erosion_radius_low)

