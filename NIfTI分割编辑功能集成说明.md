# NIfTI分割编辑功能集成说明

## 概述

已成功将NIfTI分割结果编辑功能集成到MedicalImageAnalysisSoftware项目中。该功能允许用户导入、可视化编辑和保存nii.gz格式的医学影像分割结果。

## 新增文件清单

### 1. 核心功能文件
```
src/
├── core/
│   └── segmentation_editor.py          # 分割编辑核心算法（220行）
├── controller/
│   └── SegmentationEditController.py   # 分割编辑控制器（40行）
├── widgets/
│   └── SegmentationEditWidget.py       # 分割编辑界面组件（380行）
└── utils/
    └── nii_utils.py                    # NIfTI文件读写工具（70行）
```

### 2. 文档和配置文件
```
docs/
└── NIfTI分割编辑功能说明.md            # 详细使用文档

requirements_nifti_editor.txt           # 依赖包清单
test_nifti_editor.py                    # 功能测试脚本
NIfTI分割编辑功能集成说明.md            # 本文件
```

### 3. 修改的现有文件
```
src/constant/WindowConstant.py         # 添加菜单文本常量
src/widgets/MenuBarWidget.py           # 添加菜单项
src/controller/MenuBarController.py    # 添加菜单处理函数
```

## 功能特性

### 核心功能
1. **文件加载**
   - 支持nii.gz和nii格式
   - 自动检查原始影像与分割掩码尺寸匹配
   - 保留原始空间参数（仿射矩阵）

2. **可视化编辑**
   - 双窗格显示（原始影像 + 编辑区）
   - 伪彩色半透明叠加显示分割结果
   - 实时更新编辑效果

3. **编辑工具**
   - 画笔工具：绘制新的分割区域
   - 橡皮擦工具：删除分割区域
   - 可调节画笔大小（1-50像素）
   - 支持多标签编辑（标签值1-255）

4. **交互功能**
   - 切片浏览（滑块控制）
   - 透明度调节（0-100%）
   - 无限次撤销/重做
   - 鼠标拖动连续绘制

5. **结果保存**
   - 保存为nii.gz格式
   - 保持原始空间参数
   - 支持自定义保存路径

## 技术实现细节

### 1. 架构设计
遵循项目现有的MVC架构模式：
- **Model**: `SegmentationEditor`类管理数据和业务逻辑
- **View**: `SegmentationEditWidget`类提供用户界面
- **Controller**: `SegmentationEditController`类协调视图和模型

### 2. 关键技术点

#### 数据处理
```python
# 使用nibabel读取NIfTI文件
img = nib.load(nii_path)
data = img.get_fdata().astype(np.int32)
affine = img.affine  # 空间参数

# 使用opencv进行图像融合
fused = cv2.addWeighted(orig_rgb, 1-alpha, seg_color, alpha, 0)
```

#### 鼠标交互
```python
# 坐标转换（显示坐标 → 影像坐标）
x = int(adjusted_x / display_w * img_w)
y = int(adjusted_y / display_h * img_h)

# 圆形画笔掩码生成
dist = np.sqrt((xx - x)**2 + (yy - y)**2)
mask = dist <= brush_size
```

#### 历史管理
```python
# 撤销/重做栈
self.history_stack = [initial_state]
self.history_index = 0

# 编辑时保存状态
self.history_stack.append(current_state.copy())
self.history_index += 1
```

### 3. 与现有系统集成

#### 菜单系统集成
在`MenuBarWidget.py`中添加菜单项：
```python
self.action_nifti_segmentation_editor = QtWidgets.QAction(self.QMainWindow)
self.toolMenu.addAction(self.action_nifti_segmentation_editor)
```

在`MenuBarController.py`中添加处理函数：
```python
def on_action_nifti_segmentation_editor(self):
    self.seg_edit_controller = SegmentationEditController(self.QMainWindow)
    self.seg_edit_controller.show_segmentation_editor()
```

#### 样式适配
使用项目现有的样式系统：
```python
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font

self.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)
title_label.setFont(Font.font2)
```

## 安装和使用

### 1. 安装依赖
```bash
# 安装必需的依赖包
pip install -r requirements_nifti_editor.txt
```

必需依赖：
- `nibabel>=5.0.0` - NIfTI文件读写
- `opencv-python>=4.8.0` - 图像处理
- `numpy>=1.24.0` - 数值计算

### 2. 测试安装
```bash
# 运行测试脚本验证安装
python test_nifti_editor.py
```

测试脚本会检查：
- 依赖包是否正确安装
- 模块是否能正常导入
- 基本功能是否正常

### 3. 使用功能
1. 启动主程序：
   ```bash
   python main.py
   ```

2. 在菜单栏选择：**工具栏 → NIfTI分割结果编辑**

3. 操作流程：
   - 点击"加载影像"按钮
   - 选择原始影像文件（.nii.gz）
   - 选择分割掩码文件（.nii.gz）
   - 使用画笔/橡皮擦工具编辑
   - 点击"保存结果"保存修改

## 代码质量

### 1. 代码规范
- 遵循PEP 8编码规范
- 完整的中文注释和文档字符串
- 统一的文件头注释（作者、时间）

### 2. 错误处理
```python
try:
    self.editor.load_data(orig_path, seg_path)
    QtWidgets.QMessageBox.information(self, "成功", "加载成功")
except Exception as e:
    QtWidgets.QMessageBox.critical(self, "错误", f"加载失败：{str(e)}")
```

### 3. 内存管理
- 使用numpy数组的copy()避免引用问题
- QImage使用copy()避免数据被释放
- 历史栈在编辑时动态管理

## 性能考虑

### 1. 优化措施
- 仅在当前切片进行编辑，减少内存占用
- 图像显示使用缩放而非重采样
- 历史栈仅保存必要的状态

### 2. 性能建议
- 大尺寸影像（>512×512×300）建议16GB以上内存
- 频繁编辑时注意历史栈占用的内存
- 可在代码中限制历史栈最大长度

## 扩展性

### 1. 易于扩展的部分
- **标签颜色**：修改`SegmentationEditor.label_colors`字典
- **画笔形状**：修改`_create_brush_mask()`方法
- **快捷键**：在`SegmentationEditWidget`中添加键盘事件处理
- **工具类型**：添加新的编辑模式（如填充、魔棒等）

### 2. 未来功能建议
1. 批量填充工具
2. 3D可视化预览
3. AI辅助分割
4. 批量处理多个文件
5. 分割质量评估

## 兼容性

### 1. 系统兼容性
- Windows：完全支持
- Linux：完全支持
- macOS：完全支持（需安装PyQt5）

### 2. Python版本
- Python 3.7+
- 推荐Python 3.8或3.9

### 3. 文件格式
- 输入：.nii, .nii.gz
- 输出：.nii.gz（推荐）

## 故障排除

### 常见问题

1. **导入nibabel失败**
   ```bash
   pip install nibabel
   ```

2. **opencv-python安装问题**
   ```bash
   pip install opencv-python-headless  # 无GUI版本
   ```

3. **尺寸不匹配错误**
   - 确保原始影像和分割掩码尺寸完全相同
   - 使用ITK-SNAP等工具检查文件信息

4. **内存不足**
   - 关闭其他应用释放内存
   - 考虑分批处理大文件

## 测试建议

### 1. 单元测试
运行提供的测试脚本：
```bash
python test_nifti_editor.py
```

### 2. 功能测试
1. 加载小尺寸测试数据（如64×64×30）
2. 测试画笔和橡皮擦工具
3. 测试撤销/重做功能
4. 保存并用其他软件验证结果

### 3. 压力测试
1. 加载大尺寸数据（如512×512×300）
2. 进行大量编辑操作
3. 监控内存使用情况

## 文档资源

- **详细使用文档**：`docs/NIfTI分割编辑功能说明.md`
- **API文档**：代码中的文档字符串
- **测试脚本**：`test_nifti_editor.py`

## 总结

本次集成完成了以下工作：

1. ✅ 实现了完整的NIfTI分割编辑功能
2. ✅ 遵循项目现有的架构和编码规范
3. ✅ 提供了详细的文档和测试脚本
4. ✅ 集成到主程序的菜单系统
5. ✅ 支持多标签编辑和撤销/重做
6. ✅ 保持原始空间参数的完整性

功能已就绪，可以立即使用。如有问题或需要进一步定制，请参考代码注释或联系开发团队。

---

**集成日期**: 2024年10月  
**版本**: 1.0  
**开发者**: Jianjun Tong
