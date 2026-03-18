# -*- coding: utf-8 -*-
"""
冠状面下颌管标注数据模型
"""
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from src.constant.CoronalCanalConstant import CoronalCanalConstant


class AnnotationPoint:
    """标注点数据结构"""
    def __init__(self, x: float, y: float, z: float, canal_type: int, slice_index: int):
        self.x = x
        self.y = y  
        self.z = z
        self.canal_type = canal_type  # 0: 左侧下颌管, 1: 右侧下颌管
        self.slice_index = slice_index
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'canal_type': self.canal_type,
            'slice_index': self.slice_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AnnotationPoint':
        """从字典创建标注点"""
        return cls(
            x=data['x'],
            y=data['y'], 
            z=data['z'],
            canal_type=data['canal_type'],
            slice_index=data['slice_index']
        )


class CoronalCanalAnnotationModel:
    """冠状面下颌管标注数据模型"""
    
    def __init__(self):
        self.annotation_points: List[AnnotationPoint] = []
        self.undo_stack: List[List[AnnotationPoint]] = []
        self.redo_stack: List[List[AnnotationPoint]] = []
        self.current_canal_type = CoronalCanalConstant.DEFAULT_CANAL_TYPE
        self.max_undo_steps = 50  # 最大撤销步数
        
    def add_point(self, x: float, y: float, z: float, slice_index: int) -> AnnotationPoint:
        """添加标注点"""
        # 保存当前状态到撤销栈
        self._save_state_to_undo()
        
        # 创建新的标注点
        point = AnnotationPoint(x, y, z, self.current_canal_type, slice_index)
        self.annotation_points.append(point)
        
        # 清空重做栈
        self.redo_stack.clear()
        
        return point
    
    def remove_point(self, point: AnnotationPoint) -> bool:
        """移除标注点"""
        if point in self.annotation_points:
            self._save_state_to_undo()
            self.annotation_points.remove(point)
            self.redo_stack.clear()
            return True
        return False
    
    def clear_all_points(self):
        """清除所有标注点"""
        if self.annotation_points:
            self._save_state_to_undo()
            self.annotation_points.clear()
            self.redo_stack.clear()
    
    def undo(self) -> bool:
        """撤销操作"""
        if not self.undo_stack:
            return False
            
        # 保存当前状态到重做栈
        self.redo_stack.append(self.annotation_points.copy())
        
        # 恢复上一个状态
        self.annotation_points = self.undo_stack.pop()
        
        return True
    
    def redo(self) -> bool:
        """重做操作"""
        if not self.redo_stack:
            return False
            
        # 保存当前状态到撤销栈
        self.undo_stack.append(self.annotation_points.copy())
        
        # 恢复重做状态
        self.annotation_points = self.redo_stack.pop()
        
        return True
    
    def get_points_for_slice(self, slice_index: int) -> List[AnnotationPoint]:
        """获取指定切片的标注点"""
        return [point for point in self.annotation_points if point.slice_index == slice_index]
    
    def get_points_by_canal_type(self, canal_type: int) -> List[AnnotationPoint]:
        """根据下颌管类型获取标注点"""
        return [point for point in self.annotation_points if point.canal_type == canal_type]
    
    def get_point_count(self) -> Dict[str, int]:
        """获取各类型标注点数量"""
        left_count = len(self.get_points_by_canal_type(0))
        right_count = len(self.get_points_by_canal_type(1))
        return {
            'left': left_count,
            'right': right_count,
            'total': left_count + right_count
        }
    
    def set_canal_type(self, canal_type: int):
        """设置当前下颌管类型"""
        if 0 <= canal_type < len(CoronalCanalConstant.CANAL_TYPES):
            self.current_canal_type = canal_type
    
    def save_to_file(self, file_path: str) -> bool:
        """保存标注数据到文件"""
        try:
            data = {
                'version': '1.0',
                'canal_types': CoronalCanalConstant.CANAL_TYPES,
                'annotation_points': [point.to_dict() for point in self.annotation_points]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    def load_from_file(self, file_path: str) -> bool:
        """从文件加载标注数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 保存当前状态
            self._save_state_to_undo()
            
            # 清空当前数据
            self.annotation_points.clear()
            
            # 加载标注点
            for point_data in data.get('annotation_points', []):
                point = AnnotationPoint.from_dict(point_data)
                self.annotation_points.append(point)
            
            # 清空重做栈
            self.redo_stack.clear()
            
            return True
        except Exception as e:
            print(f"加载文件失败: {e}")
            return False
    
    def _save_state_to_undo(self):
        """保存当前状态到撤销栈"""
        # 限制撤销栈大小
        if len(self.undo_stack) >= self.max_undo_steps:
            self.undo_stack.pop(0)
        
        # 保存当前状态的深拷贝
        self.undo_stack.append(self.annotation_points.copy())
    
    def get_canal_color(self, canal_type: int) -> str:
        """获取下颌管类型对应的颜色"""
        if 0 <= canal_type < len(CoronalCanalConstant.CANAL_TYPES):
            return CoronalCanalConstant.CANAL_TYPES[canal_type][1]
        return "#FFFFFF"  # 默认白色
    
    def get_canal_name(self, canal_type: int) -> str:
        """获取下颌管类型名称"""
        if 0 <= canal_type < len(CoronalCanalConstant.CANAL_TYPES):
            return CoronalCanalConstant.CANAL_TYPES[canal_type][0]
        return "未知类型"