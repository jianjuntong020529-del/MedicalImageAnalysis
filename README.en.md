# Medical Imaging Analysis Software

A powerful professional dental/implant medical imaging analysis software supporting loading, viewing, segmentation, annotation, and 3D reconstruction of multiple medical imaging formats.

## Features

### Medical Image Viewer
- Multi-Planar Reconstruction (MPR) views: axial, coronal, and sagittal planes
- Support for window width/level adjustment
- Image contrast/brightness adjustment
- Slice sequence browsing
- Four-view layout display

### Data Format Support
- DICOM medical images
- NIFTI (.nii/.nii.gz) format
- NPY array data
- IM0/BIM format
- STL 3D models

### Core Functional Modules

#### 1. Implant Planning (Dental Implant)
- 3D placement and adjustment of implants
- Multi-angle rotation control
- Implant information display
- Cross-sectional analysis
- Tooth position selection and localization

#### 2. Registration Tool (Registration)
- Automatic landmark registration
- Manual landmark adjustment
- Three-axis position/angle adjustment
- CBCT landmark segmentation

#### 3. Annotation Tool (Annotation)
- Point annotation
- Box selection annotation
- Polyline annotation
- Angle measurement
- Ruler measurement
- Brush tool
- Undo/redo support

#### 4. Tooth Landmark Detection (Tooth Landmark)
- Automatic tooth landmark detection
- Alveolar bone segmentation
- Tooth segmentation
- Annotation saving and loading

#### 5. Coronal Canal Annotation (Coronal Canal Annotation)
- Coronal groove annotation
- Independent annotation for left and right sides
- Brush mode switching

#### 6. Tooth Measurement (Tooth Measurement)
- Geometric tooth measurements
- Angle calculation
- Export PDF reports
- Export CSV data
- FDI tooth numbering system

#### 7. Curved Planar Reconstruction (CPR)
- Dental arch curve generation
- Multi-planar curved surface reconstruction
- Annotation and saving

#### 8. Segmentation Editor (Segmentation Editor)
- Medical image segmentation editing
- Multiple label management
- Undo/redo
- Segmentation result saving

#### 9. Volume Rendering (Volume Render)
- 3D volume rendering
- Multiple rendering presets
- Transparency and lighting adjustment

### Deep Learning Models

- **SAM Med 2D**: Medical image segmentation model based on Segment Anything
- **Tooth Segmentation and Landmark Detection**: Joint segmentation and landmark detection network
- **Alveolar Bone Segmentation**: Automatic segmentation of alveolar bone regions

## Technical Architecture

```
├── main.py                    # Program entry point
├── npy_to_nii.py             # NPY to NIFTI conversion tool
├── requirements.txt          # Python dependencies
├── environment.yml           # Conda environment configuration
├── src/
│   ├── constant/             # Constant definitions
│   ├── controller/           # Controller layer
│   ├── core/                 # Core algorithms
│   │   ├── sam_med2d/       # SAM medical segmentation
│   │   ├── tooth_measurement.py  # Tooth measurement
│   │   ├── cpr_engine.py    # CPR engine
│   │   ├── tooth_landmark_detc/  # Landmark detection
│   │   └── tooth_seg_landmark_prior/  # Segmentation and landmark prior
│   ├── interactor_style/    # Interaction styles
│   ├── model/               # Data models
│   ├── service/             # Service layer
│   ├── style/               # Style definitions
│   ├── ui/                  # UI windows
│   ├── utils/               # Utility functions
│   └── widgets/             # UI components
```

## System Requirements

- Python 3.8+
- PyQt5/PyQt6
- VTK (Visualization Toolkit)
- NumPy
- SimpleITK (Medical image processing)
- PyTorch (Deep learning)
- scipy, scikit-image

## Installation

### 1. Create Environment with Conda

```bash
conda env create -f environment.yml
conda activate medical-image
```

### 2. Install via pip

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python main.py
```

## Usage Instructions

### Loading Imaging Data

1. Select `File` → `Load DICOM Data` to choose a DICOM folder
2. Use `Load NIFTI Data` to load .nii files
3. Use `Load NPY Data` to load numpy array files

### Basic Operations

- **Mouse wheel**: Switch slices
- **Left-click and drag**: Move image
- **Right-click and drag**: Adjust window width/level
- **Ctrl + mouse wheel**: Zoom view

### Toolbar Guide

| Icon | Function |
|------|----------|
| 📏 | Ruler measurement |
| ✏️ | Brush annotation |
| 📐 | Angle measurement |
| ⬜ | Box selection annotation |
| 🔄 | Reset view |
| ✛ | Crosshair |

### Data Management

The right panel displays a list of loaded data, allowing you to:
- Toggle visibility
- Modify colors
- Delete data

## Development Guide

### Adding New Data Format Support

Register a new reader in `src/utils/image_loader.py`:

```python
class ImageLoaderRegistry:
    @classmethod
    def register(cls, reader_cls):
        # Register new reader
```

### Adding a New Segmentation Model

1. Create a new module directory under `src/core/`
2. Implement the model inference interface
3. Integrate and invoke within the corresponding Controller

## License

This software is for educational and research purposes only.

## Dependencies

Core dependencies include:
- PyQt5/PyQt6
- VTK >= 9.0
- SimpleITK
- NumPy, SciPy
- PyTorch >= 1.8
- scikit-image
- nibabel (NIFTI processing)
- pandas (data export)