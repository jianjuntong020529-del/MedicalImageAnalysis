# -*- coding: utf-8 -*-
"""
NIfTI分割编辑功能测试脚本
用于验证依赖安装和基本功能
"""
import sys

def test_dependencies():
    """测试依赖包是否正确安装"""
    print("=" * 60)
    print("NIfTI分割编辑功能 - 依赖检查")
    print("=" * 60)
    
    dependencies = {
        'nibabel': 'NIfTI文件读写',
        'cv2': '图像处理（opencv-python）',
        'numpy': '数值计算',
        'PyQt5': 'GUI界面'
    }
    
    missing_deps = []
    
    for module, description in dependencies.items():
        try:
            if module == 'cv2':
                import cv2
            elif module == 'nibabel':
                import nibabel
            elif module == 'numpy':
                import numpy
            elif module == 'PyQt5':
                from PyQt5 import QtWidgets
            
            print(f"✓ {module:15s} - {description}")
        except ImportError:
            print(f"✗ {module:15s} - {description} (未安装)")
            missing_deps.append(module)
    
    print("=" * 60)
    
    if missing_deps:
        print("\n缺少以下依赖包，请安装：")
        print("pip install", " ".join(missing_deps))
        return False
    else:
        print("\n所有依赖包已正确安装！")
        return True


def test_module_import():
    """测试模块导入"""
    print("\n" + "=" * 60)
    print("模块导入测试")
    print("=" * 60)
    
    modules = [
        ('src.utils.nii_utils', 'NIfTI工具函数'),
        ('src.core.segmentation_editor', '分割编辑核心'),
        ('src.widgets.SegmentationEditWidget', '界面组件'),
        ('src.controller.SegmentationEditController', '控制器')
    ]
    
    all_success = True
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name:45s} - {description}")
        except Exception as e:
            print(f"✗ {module_name:45s} - {description}")
            print(f"  错误: {str(e)}")
            all_success = False
    
    print("=" * 60)
    
    if all_success:
        print("\n所有模块导入成功！")
    else:
        print("\n部分模块导入失败，请检查代码。")
    
    return all_success


def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 60)
    print("基本功能测试")
    print("=" * 60)
    
    try:
        from src.core.segmentation_editor import SegmentationEditor
        
        # 创建编辑器实例
        editor = SegmentationEditor()
        print("✓ 创建SegmentationEditor实例")
        
        # 检查属性
        assert editor.current_slice == 0, "初始切片应为0"
        assert editor.current_label == 1, "初始标签应为1"
        assert editor.brush_size == 5, "初始画笔大小应为5"
        assert editor.alpha == 0.5, "初始透明度应为0.5"
        print("✓ 默认参数设置正确")
        
        # 检查方法存在
        assert hasattr(editor, 'load_data'), "应有load_data方法"
        assert hasattr(editor, 'edit_seg_mask'), "应有edit_seg_mask方法"
        assert hasattr(editor, 'undo'), "应有undo方法"
        assert hasattr(editor, 'redo'), "应有redo方法"
        assert hasattr(editor, 'save_edited_seg'), "应有save_edited_seg方法"
        print("✓ 所有必需方法存在")
        
        print("=" * 60)
        print("\n基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {str(e)}")
        print("=" * 60)
        return False


def main():
    """主测试函数"""
    print("\n开始测试NIfTI分割编辑功能...\n")
    
    # 测试依赖
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\n请先安装缺失的依赖包：")
        print("pip install -r requirements_nifti_editor.txt")
        return False
    
    # 测试模块导入
    import_ok = test_module_import()
    
    if not import_ok:
        print("\n模块导入失败，请检查代码文件是否完整。")
        return False
    
    # 测试基本功能
    func_ok = test_basic_functionality()
    
    if func_ok:
        print("\n" + "=" * 60)
        print("所有测试通过！NIfTI分割编辑功能已就绪。")
        print("=" * 60)
        print("\n使用方法：")
        print("1. 运行主程序: python main.py")
        print("2. 在菜单栏选择: 工具栏 → NIfTI分割结果编辑")
        print("3. 加载原始影像和分割掩码文件")
        print("4. 使用画笔/橡皮擦工具编辑分割结果")
        print("5. 保存修改后的分割结果")
        print("\n详细说明请参考: docs/NIfTI分割编辑功能说明.md")
        print("=" * 60)
        return True
    else:
        print("\n功能测试失败，请检查代码实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
