import os
import numpy as np
from scipy.io import savemat, loadmat
import pydicom


def convertNsave(dicom_file_ori, file_dicom, file_dir, index=0):
    """
    `arr`: parameter will take a numpy array that represents only one slice.
    `file_dir`: parameter will take the path to save the slices
    `index`: parameter will represent the index of the slice, so this parameter will be used to put
    the name of each slice while using a for loop to convert all the slices
    """
    dicom_file = pydicom.dcmread(file_dicom)
    arr = dicom_file_ori.pixel_array
    arr = arr.astype('uint16')
    dicom_file.Rows = arr.shape[0]
    dicom_file.Columns = arr.shape[1]
    dicom_file.PhotometricInterpretation = "MONOCHROME2"
    dicom_file.SamplesPerPixel = 1
    dicom_file.BitsStored = 16
    dicom_file.BitsAllocated = 16
    dicom_file.HighBit = 15
    dicom_file.PixelRepresentation = 1
    dicom_file.SliceThickness = dicom_file_ori.SliceThickness
    dicom_file.PixelSpacing = dicom_file_ori.PixelSpacing
    dicom_file.PixelData = arr.tobytes()
    dicom_file.InstanceNumber = str(index + 1)
    dicom_file.save_as(os.path.join(file_dir, f'{"{:04d}".format(index + 1)}.dcm'))


def Load_IM0_BIM(inputfile):
    # ----------------------------------------------------------------------------------
    rootpath = '.'
    # ============IM0 data transform into matlab===========
    slicenumber = os.popen('get_slicenumber ' + inputfile).read()
    slicenumber = slicenumber.split(' ')[1]
    os.system('exportMath ' + inputfile + ' matlab ' + rootpath + '\\temp.mat' + ' 0 ' + slicenumber)
    input_mridata = loadmat(rootpath + '\\temp.mat')['scene']
    os.remove(rootpath + '\\temp.mat')
    return input_mridata


def Save_BIM(Img, output_file, input_file=None):
    # ----------------------------------------------------------------------------------
    rootpath = '.'
    img_shape = np.shape(Img)
    if input_file == None:
        savemat(rootpath + '\\temp.mat', {'scene': np.uint8(Img)})
        os.system(
            'importMath ' + rootpath + '/temp.mat ' + 'matlab ' + output_file + ' ' + str(img_shape[0]) + ' ' + str(
                img_shape[1]) + ' ' + str(img_shape[2]))
        os.remove(rootpath + '\\temp.mat')
    else:
        savemat(rootpath + '\\temp.mat', {'scene': np.uint8(Img)})
        os.system('importMath ' + rootpath + '\\temp.mat ' + 'matlab ' + rootpath + '\\temp.BIM ' + str(
            img_shape[0]) + ' ' + str(img_shape[1]) + ' ' + str(img_shape[2]))
        os.system('ndthreshold ' + rootpath + '\\temp.BIM ' + rootpath + '\\temp2.BIM 0 1 1')
        os.system('copy_pose ' + rootpath + '\\temp2.BIM ' + input_file + ' ' + output_file)
        os.remove(rootpath + '\\temp.BIM')
        os.remove(rootpath + '\\temp2.BIM')
        os.remove(rootpath + '\\temp.mat')
