"""
参数常量配置
"""
import os
from argparse import Namespace

import torch


class ParamConstant:
    # 种植体“.stl”地址
    IMPLANT_PATH = "./resources/implants/"
    # 输出保存地址
    OUTPUT_FILE_PATH = './output/'
    # 患者名称
    SUBJECT_NAME = 'Subject'

    THRESHOLD_ID = 0.5

    MOLD_ANCHORPOINT_PATH = './resources/'

    MOLD_FILE_PATH = './resources/quanbu-gangzhu.stl'

    MOLD_ORIGIN_FILE_PATH = './resources/quanbu2.stl'

    MODEL_NUM = 8

    # 设置模型参数
    # 添加变量
    os.environ['VIEWNIX_ENV'] = './resources/CAVASS/'
    current_path = os.environ['Path']
    # 将新路径添加到PATH中，并移除重复项
    os.environ['Path'] = os.pathsep.join(current_path.split(os.pathsep) + ['./resources/CAVASS/'])
    # ---------------------------------------
    args = Namespace()
    device = torch.device("cpu")
    args.image_size = 256
    args.encoder_adapter = True

    IMAGE_DCM = './resources/image_dcm/DCT0000.dcm'

    universal_model = "./resources/checkpoints/sam-med2d_b.pth"

    lung_seg_model = "./resources/checkpoints/sam-med2d_refine.pth"

    # 口腔全景图
    THICKNESS_VALUE = "80"

    # 牙齿序列72
    TOOTH_ID = ["右上颌", "18", "17", "16", "15", "14", "13", "12", "11", "左上颌", "21", "22", "23",
                "24", "25", "26", "27", "28",
                "右下颌", "48", "47", "46", "45", "44", "43", "42", "41", "左下颌", "31", "32", "33",
                "34", "35", "36", "37", "38"]

    # 植体型号
    TOOTH_IMPLANT = ["3510", "3511_5", "3513", "3585", "4007", "4010", "4011_5", "4013", "4085", "4507",
                     "4510", "4511_5", "4513", "4585", "5006", "5007", "5010", "5011_5", "5013", "5085"]

    # Tooth Landmark Annotation
    COLOR_DATA = [
        ("", "maxilla:"), ("#ae5170", "18"), ("#f3722c", "17"), ("#f8d62e", "16"), ("#f9c74f", "15"), ("#f29676", "14"),
        ("#ffa4c7", "13"), ("#f15bb5", "12"), ("#ab8dff", "11"),
        ("#965df5", "21"), ("#3a86ff", "22"), ("#00f9f9", "23"), ("#92c7a5", "24"), ("#c08552", "25"),
        ("#742c05", "26"),
        ("#a566a6", "27"), ("#00fa85", "28"),
        ("", "mandible:"), ("#ffbabd", "38"), ("#ffdaf5", "37"), ("#fbe02f", "36"), ("#aecefd", "35"),
        ("#8fdbf8", "34"),
        ("#f2ffcf", "33"), ("#efd758", "32"), ("#fadcc8", "31"),
        ("#ffc52f", "41"), ("#ff0a1", "42"), ("#aad6ed", "43"), ("#a5f8df", "44"), ("#73abff", "45"), ("#a799ff", "46"),
        ("#add3aa", "47"), ("#fdd8ce", "48"),
        ("", "supernumerary teeth:"), ("#78adfc", "51"), ("#cefb5c", "52"), ("#d1a386", "53"), ("#51faf0", "54"),
        ("#f09ea4", "55"), ("#247bfd", "56"), ("#7b67f9", "57"),
        ("#646464", "58"), ("#9297c2", "59"), ("#8f00a7", "60")
    ]

    CURRENT_COLOR = "#ae5170"
    CURRENT_COLOR_ID = "18"
    CURRENT_COLOR_INDEX = 1
    ANNOTATION_SUBJECT_NAME = ""

    LAND_MARK_PATH = ''
    TOOTH_LANDMARK_THRESHOLD_TH = 0.95
    TOOTH_LANDMARK_THRESHOLD_AL = 0.9
    SMOOTH_FACTOR = 3.0
    EROSION_RADIUS_UP = 3
    EROSION_RADIUS_LOW = 3
    FLAG_SEG = 'True'


