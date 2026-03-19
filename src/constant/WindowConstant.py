
class WindowConstant:
    WINDOW_TITLE = "MedicalImageAnalysisSoftware"
    LABEL_SUBJECTNAME = "输入患者名称:"
    LINEDIET_SUBJECTNAME = "Subject"
    LABEL_SLICE = "切片"
    LABEL_VOLUME = "体绘制窗口"
    FILE_MENU = "文件"
    TOOL_MENU = "工具栏"
    SAM_MED2D_SEG = "SAM-Med2D 分割"
    ADD_DICOM = "导入DICOM文件"
    ADD_IM0 = "导入IM0文件"
    ADD_NIFIT = "导入nii.gz文件"
    ADD_NPY = "导入NPY文件"
    ADD_STL = "导入STL文件"

    ACTION_GENERATE_PANORMAIC = "口腔全景图像"
    ACTION_TOOTH_LANDMARK_ANNOTATION = "牙齿标记"
    ACTION_CORONAL_CANAL_ANNOTATION = "冠状面下颌管标注"
    ACTION_IMPLANT_TOOLBAR = "打开植体工具栏"
    ACTION_REGISTRATION_TOOLBAR = "打开配准工具栏"
    ACTION_PARAMETERS_TOOLBAR = "打开参数计算工具栏"

    MODEL_LOAD = "加载分割模型"
    LOAD_UNIVERSAL_MODEL = "Load Universal model"
    LOAD_LUNGSEG_MODEL = "Load MRI Lungseg model"

    # Segmentation
    POINT = "点"
    POINT_TYPE = "点标签"
    POINT_LABEL_0 = "label 0"
    POINT_LABEL_1 = "label 1"
    BOUNDING_BOX = "边界框"
    BOUNDING_BOX_TYPE = "边界框类型"
    BOUNDING_BOX_SINGLE = "Single"
    BOUNDING_BOX_MULTIPLE = "Multiple"
    START_SEGMENTATION = "开始分割"
    SEGMENTATION_TYPE = "分割方式"
    SEGMENTATION_NONE = "None"
    SEGMENTATION_SLICE_RANGE = "Slice Range"
    SAVE_SEGMENTATION_RESULTS = "保存分割结果"
    GET_ROI = "提取ROI"

    # Constant
    CONTRAST_TOOL_TITLE = "对比度调整"
    WINDOW_LEVEL = "窗位"
    WINDOW_WIDTH = "窗宽"

    # ToolBar
    RULER = "直尺"
    PAINT = "画笔"
    POLY_LINE = "折线标注"
    ANGLE = "角度测量"
    HU = "骨密度"
    RESET = "复位"
    CROSSHAIR = "同步定位"
    DRAGGING = "拖动"
    ROI = "提取ROI区域"

    # 植体
    TOOTH_IMPLANT_LIST = '牙齿植体列表：'
    IMPLANT_WIDGET_LABEL = "植体工具栏"
    TOOTH_ID_LABEL = "选择牙齿序列"
    IMPLANT_LABEL = "选择植体型号"
    IMPLANT_DIRECTION = "植体朝向: "
    PUT_IMPLANT_BUTTON = "放置植体"
    CROSSHAIR_AXIS_ORTHOGONAL = "十字线正交"
    REGIS_XY_ADJUST = "XY面旋转"
    REGIS_YZ_ADJUST = "YZ面旋转"
    REGIS_XZ_ADJUST = "XZ面旋转"
    REGIS_MOVE_X_AXIS = "X轴位移"
    REGIS_MOVE_Y_AXIS = "Y轴位移"
    REGIS_MOVE_Z_AXIS = "Z轴位移"
    ADJUST_IMPLANT_BUTTON = "微调完成"

    # 配准
    REGISTER_WIDGET_LABEL = "配准工具栏"
    ANCHOR_SEG_BUTTON = "CT锚点检测"
    ANCHOR_LOAD_BUTTON = "加载锚点结果"
    ANCHOR_DIRECTION = "手动锚点显示方向"
    AUTO_ANCHOR = "自动"
    MANUAL_ANCHOR = "手动"
    ANCHOR_REG_BUTTON = "锚点与模具配准"
    REG_ADJUST_BUTTON = "配准微调完成"
    REGIS_X_ROATE = "x轴旋转"
    REGIS_Y_ROATE = "y轴旋转"
    REGIS_Z_ROATE = "z轴旋转"

    # 计算参数
    TABLE_HEADERS = ['植体号', 'X轴位移', 'Y轴位移', '底座旋转角度', '导板旋转角度']
    COMPUTE_PARAMETERS = "计算加工参数"
    CLEAR_IMPLANT_ACTOR = "清除植体"

    # 标注
    ANNOTATION_WIDGET_LABEL = "标注"
    CLEAR_BUTTON = "全部清除"
    UNDO_BUTTON = "撤回"
    REDO_BUTTON = "恢复"


    # Implant_Information
    IMPLANT_INFO_TITLE = "提示"
    IMPLANT_INFO_TEXT = "请先开启同步定位"
    IMPLANT_INFO_ACCEPT = "确认"
    IMPLANT_INFO_REJECT = "取消"

    # Tooth Landmark Dection
    TOOTH_LANDMARK_DETC_INFO_TITLE = '正在进行CT锚点检测!'
    TOOTH_LANDMARK_INFO_TEXT = "已完成CT锚点检测!"
    LOAD_ANCHOR_BEFORE_DETC_INFO_TEXT = "请先进行CT锚点检测"

    # 口腔全景图
    DENTAL_ARCH_THICKNESS = "牙弓厚度:"
    PANORMAIC_WINDOW_TITLE = "口腔全景图"
    ANNOTATION_BUTTON = "标注"
    SAVE_BUTTON = "保存"
    TOOLBAR_TITLE = "工具栏"
    SHOW_DENTAL_ARCH_BUTTON = "显示牙弓线"
    GENERATE_PANORMAIC_BUTTON = "生成口腔全景图"
    GENERATE_PANORMAIC_INFO_TEXT = "牙弓曲线未保存，请先保存！"

    # 牙齿标志点标注
    # TOOTH_LABELS_WIDGET = "Labels"
    # FDI_LABEL = "FDI: "
    # TOOTH_LANDMARK_PAINT_BUTTON = "Paint"
    # TOOTH_LANDMARK_CLEAR_BUTTON = "Clear"
    # TOOTH_LANDMARK_UNDO_BUTTON = "Undo"
    # TOOTH_LANDMARK_REDO_BUTTON = "Redo"
    # TOOTH_LANDMARK_LOAD_BUTTON = "Load"
    # TOOTH_LANDMARK_SAVE_BUTTON = "Save"
    # TOOTH_LANDMARK_Segmentation_BUTTON = "Segmentation"
    # TOOTH_LANDMARK_LOAD_RESULT_BUTTON = "Load Segmentation Result"
    
    TOOTH_LABELS_WIDGET = "标签"
    FDI_LABEL = "FDI: "
    TOOTH_LANDMARK_PAINT_BUTTON = "画笔"
    TOOTH_LANDMARK_CLEAR_BUTTON = "清除"
    TOOTH_LANDMARK_UNDO_BUTTON = "撤销"
    TOOTH_LANDMARK_REDO_BUTTON = "回退"
    TOOTH_LANDMARK_LOAD_BUTTON = "加载"
    TOOTH_LANDMARK_SAVE_BUTTON = "保存"
    TOOTH_LANDMARK_Segmentation_BUTTON = "分割"
    TOOTH_LANDMARK_LOAD_ALVEOLAR_RESULT_BUTTON = "加载颌骨分割结果"
    TOOTH_LANDMARK_LOAD_TOOTH_RESULT_BUTTON = "加载牙齿分割结果"

    # NIfTI分割编辑
    ACTION_NIFTI_SEGMENTATION_EDITOR = "NIfTI分割结果编辑"

    # 体绘制工具栏
    ACTION_VOLUME_RENDER_TOOLBAR = "体绘制工具栏"

    # 视图布局控制
    ACTION_VIEW_LAYOUT = "视图布局"











