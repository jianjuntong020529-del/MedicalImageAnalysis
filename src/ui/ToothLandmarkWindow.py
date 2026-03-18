from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from src.constant.WindowConstant import WindowConstant
from src.controller.ToothLandmarkController import ToothLandmarkController
from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.model.ToolBarWidgetModel import ToolBarWidget
from src.style.AppVisualStyle import APPVisualStyle
from src.widgets.ContrastWidget import Contrast
from src.widgets.QtAxialViewerWidget import AxialViewer


class Tooth_Landmark(QWidget):
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel):
        super().__init__()

        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.origin = self.baseModelClass.origin
        self.spacing = self.baseModelClass.spacing
        self.dimensions = self.baseModelClass.imageDimensions

        self.resize(1240, 920)
        self.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)

        # ------------------ system layout ------------------------------
        self.system_layout = QtWidgets.QHBoxLayout()
        self.system_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        # ---------------- view layout -------------------------------
        self.view_layout = QtWidgets.QVBoxLayout()
        self.view_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)

        self.axialViewer = AxialViewer(self.baseModelClass)

        self.window_slider_layout = QtWidgets.QHBoxLayout()
        self.window_slider_layout.setSpacing(6)
        self.window_slider_layout.addWidget(self.axialViewer.widget)
        self.window_slider_layout.addWidget(self.axialViewer.slider)

        self.view_layout.addLayout(self.window_slider_layout)
        self.view_layout.addWidget(self.axialViewer.slider_label)
        self.system_layout.addLayout(self.view_layout, 7)

        # -----------------------------toolbar layout---------------------------------------------------------------
        self.tool_bar_layout = QtWidgets.QVBoxLayout()
        self.tool_bar_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.tool_bar_layout.setAlignment(Qt.AlignTop)

        self.contrast = Contrast()
        self.contrast.init_widget()
        self.tool_bar_layout.addWidget(self.contrast.widget_contrast)
        self.contrast.window_width_slider.setValue(ToolBarWidget.contrast_widget.window_width_slider.value())
        self.contrast.window_level_slider.setValue(ToolBarWidget.contrast_widget.window_level_slider.value())

        self.toothLandmark = ToothLandmarkController(self.baseModelClass, self.axialViewer, self.contrast)

        self.tool_bar_layout.addWidget(self.toothLandmark.widget_labels)
        self.tool_bar_layout.addWidget(self.toothLandmark.pushButton_load, Qt.AlignBottom)
        self.tool_bar_layout.addWidget(self.toothLandmark.pushButton_save, Qt.AlignBottom)
        self.tool_bar_layout.addWidget(self.toothLandmark.pushButton_segmentation, Qt.AlignBottom)
        self.tool_bar_layout.addWidget(self.toothLandmark.pushButton_load_alveolar_segResult, Qt.AlignBottom)
        self.tool_bar_layout.addWidget(self.toothLandmark.pushButton_load_tooth_segResult, Qt.AlignBottom)

        self.system_layout.addLayout(self.tool_bar_layout, 2)

        self.setLayout(self.system_layout)

        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Widget", WindowConstant.ACTION_TOOTH_LANDMARK_ANNOTATION))

