

# 医学影像分析软件

一款功能强大的专业牙科/种植体医学影像分析软件，支持多种医学影像格式的加载、查看、分割、标注和三维重建。

## 功能特性

### 医学影像查看器
- 多平面重建（MPR）视图：轴向、冠状、矢状切面
- 支持窗宽/窗位调整
- 图像对比度/亮度调节
- 序列切片浏览
- 四视图布局显示

### 数据格式支持
- DICOM 医学影像
- NIFTI (.nii/.nii.gz) 格式
- NPY 数组数据
- IM0/BIM 格式
- STL 三维模型

### 核心功能模块

#### 1. 种植体规划 (Dental Implant)
- 种植体3D放置与调整
- 多角度旋转控制
- 种植体信息显示
- 横截面分析
- 牙位选择与定位

#### 2. 配准工具 (Registration)
- 自动锚点配准
- 手动锚点调整
- 三轴位置/角度调节
- CBCT 锚点分割

#### 3. 标注工具 (Annotation)
- 点标注
- 框选标注
- 折线标注
- 角度测量
- 标尺测量
- 画笔工具
- 撤销/重做支持

#### 4. 牙齿标志点检测 (Tooth Landmark)
- 自动牙齿标志点检测
- 牙槽骨分割
- 牙齿分割
- 标注保存与加载

#### 5. 牙槽骨标注 (Coronal Canal Annotation)
- 冠状沟标注
- 左右两侧独立标注
- 画笔模式切换

#### 6. 牙齿测量 (Tooth Measurement)
- 牙齿几何测量
- 角度计算
- 导出PDF报告
- 导出CSV数据
- FDI牙位系统

#### 7. 曲面重建 (CPR)
- 牙弓曲线生成
- 多平面曲面重建
- 标注与保存

#### 8. 分割编辑 (Segmentation Editor)
- 医学影像分割编辑
- 多种标签管理
- 撤销/重做
- 分割结果保存

#### 9. 体绘制 (Volume Render)
- 三维体绘制
- 多种渲染预设
- 透明度/光照调节

### 深度学习模型

- **SAM Med 2D**: 基于Segment Anything的医学图像分割模型
- **牙齿分割与标志点检测**: 联合分割与标志点检测网络
- **牙槽骨分割**: 牙槽骨区域自动分割

## 技术架构

```
├── main.py                    # 程序入口
├── npy_to_nii.py             # NPY转NIFTI工具
├── requirements.txt          # Python依赖
├── environment.yml           # Conda环境配置
├── src/
│   ├── constant/             # 常量定义
│   ├── controller/           # 控制器层
│   ├── core/                 # 核心算法
│   │   ├── sam_med2d/       # SAM医学分割
│   │   ├── tooth_measurement.py  # 牙齿测量
│   │   ├── cpr_engine.py    # CPR引擎
│   │   ├── tooth_landmark_detc/  # 标志点检测
│   │   └── tooth_seg_landmark_prior/  # 分割与标志点
│   ├── interactor_style/    # 交互样式
│   ├── model/               # 数据模型
│   ├── service/             # 服务层
│   ├── style/               # 样式定义
│   ├── ui/                  # UI窗口
│   ├── utils/               # 工具函数
│   └── widgets/             # UI组件
```

## 环境要求

- Python 3.8+
- PyQt5/PyQt6
- VTK (可视化库)
- NumPy
- SimpleITK (医学图像处理)
- PyTorch (深度学习)
- scipy, scikit-image

## 安装

### 1. 使用 Conda 创建环境

```bash
conda env create -f environment.yml
conda activate medical-image
```

### 2. 使用 pip 安装

```bash
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python main.py
```

## 使用说明

### 加载影像数据

1. 通过菜单 `文件` -> `加载DICOM数据` 选择DICOM文件夹
2. 通过 `加载NIFTI数据` 加载.nii格式文件
3. 通过 `加载NPY数据` 加载numpy数组文件

### 基本操作

- **鼠标滚轮**: 切换切片
- **左键拖拽**: 移动图像
- **右键拖拽**: 调整窗宽/窗位
- **Ctrl+滚轮**: 缩放视图

### 工具栏说明

| 图标 | 功能 |
|------|------|
| 📏 | 标尺测量 |
| ✏️ | 画笔标注 |
| 📐 | 角度测量 |
| ⬜ | 框选标注 |
| 🔄 | 重置视图 |
| ✛ | 十字线 |

### 数据管理

右侧面板显示已加载的数据列表，可进行：
- 显示/隐藏切换
- 颜色修改
- 删除数据

## 开发指南

### 添加新的数据格式支持

在 `src/utils/image_loader.py` 中注册新的读取器：

```python
class ImageLoaderRegistry:
    @classmethod
    def register(cls, reader_cls):
        # 注册新的读取器
```

### 添加新的分割模型

1. 在 `src/core/` 下创建新的模块目录
2. 实现模型推理接口
3. 在对应Controller中集成调用

## 许可证

本软件仅供学习和研究使用。

## 依赖项

核心依赖包括：
- PyQt5/PyQt6
- VTK >= 9.0
- SimpleITK
- NumPy, SciPy
- PyTorch >= 1.8
- scikit-image
- nibabel (NIFTI处理)
- pandas (数据导出)