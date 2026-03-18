# -*- coding: utf-8 -*-
"""
冠状面下颌管标注常量定义
"""

class CoronalCanalConstant:
    # 窗口标题
    WINDOW_TITLE = "冠状面下颌管标注"
    WIDGET_TITLE = "下颌管标注"
    
    # 按钮文本
    PAINT_BUTTON = "开始标注"
    CLEAR_BUTTON = "清除全部"
    UNDO_BUTTON = "撤销"
    REDO_BUTTON = "恢复"
    LOAD_BUTTON = "导入标注"
    SAVE_BUTTON = "保存标注"
    SEG_BUTTON = "开始分割"
    LOAD_SEG_RESULT_BUTTON = "加载分割结果"
    
    # 标签文本
    CANAL_TYPE_LABEL = "下颌管类型:"
    ANNOTATION_INFO = "标注信息"
    POINT_COUNT_LABEL = "标注点数量:"
    
    # 下颌管类型和颜色定义 (只需要两种颜色)
    CANAL_TYPES = [
        ("左侧下颌管", "#FF6B6B"),  # 红色
        ("右侧下颌管", "#4ECDC4")   # 青色
    ]
    
    # 默认选中的类型
    DEFAULT_CANAL_TYPE = 0
    
    # 文件格式
    ANNOTATION_FILE_EXTENSION = "*.json"
    ANNOTATION_FILE_FILTER = "JSON Files (*.json)"
    
    # 标注点大小
    ANNOTATION_POINT_SIZE = 1.0
    
    # 消息提示
    MSG_SAVE_SUCCESS = "标注文件保存成功!"
    MSG_LOAD_SUCCESS = "标注文件加载成功!"
    MSG_CLEAR_CONFIRM = "确定要清除所有标注点吗?"
    MSG_NO_ANNOTATIONS = "没有标注点可以保存!"
    MSG_FILE_NOT_FOUND = "文件不存在或格式错误!"