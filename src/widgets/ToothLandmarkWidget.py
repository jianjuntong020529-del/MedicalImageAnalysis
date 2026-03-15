from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QComboBox, QHBoxLayout

from src.constant.ParamConstant import ParamConstant
from src.constant.WindowConstant import WindowConstant
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font


class ToothLandmarkWidget:
    def init_widget(self):
        # --------------------- Labels Layout -------------------------------------
        self.widget_labels = QtWidgets.QWidget()
        self.widget_labels.setMinimumSize(QtCore.QSize(200, 400))
        self.widget_labels.setMaximumSize(QtCore.QSize(240, 400))
        self.widget_labels.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)
        self.labels_vertical_layout = QtWidgets.QVBoxLayout(self.widget_labels)
        self.labels_vertical_layout.setContentsMargins(11, 11, 11, 11)
        self.labels_vertical_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.labels_vertical_layout.setAlignment(Qt.AlignTop)
        # -----------------------------title---------------------------------------
        self.widget_title = QtWidgets.QLabel(self.widget_labels)
        self.widget_title.setMinimumSize(QtCore.QSize(200, 20))
        self.widget_title.setMaximumSize(QtCore.QSize(240, 20))
        self.widget_title.setStyleSheet(APPVisualStyle.WIDGET_LABEL_COLOR)
        self.widget_title.setFont(Font.font_en)
        self.labels_vertical_layout.addWidget(self.widget_title, Qt.AlignLeft | Qt.AlignTop)

        self.pushButton_paint = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_paint.setFont(Font.font_en)
        self.pushButton_paint.setCheckable(True)
        self.pushButton_paint.setAutoExclusive(False)

        self.paint_enable = False
        self.pushButton_clear = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_clear.setFont(Font.font_en)
        self.pushButton_clear.setAutoExclusive(False)

        self.pushButton_undo = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_undo.setFont(Font.font_en)
        self.pushButton_undo.setAutoExclusive(False)

        self.pushButton_redo = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_redo.setFont(Font.font_en)
        self.pushButton_redo.setAutoExclusive(False)

        self.pushButton_layout = QtWidgets.QHBoxLayout()
        self.pushButton_layout.setSpacing(10)
        self.pushButton_layout.setContentsMargins(11, 11, 11, 11)
        self.pushButton_left_layout = QtWidgets.QVBoxLayout()
        self.pushButton_left_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.pushButton_right_layout = QtWidgets.QVBoxLayout()
        self.pushButton_right_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.pushButton_left_layout.addWidget(self.pushButton_paint)
        self.pushButton_left_layout.addWidget(self.pushButton_undo)
        self.pushButton_right_layout.addWidget(self.pushButton_clear)
        self.pushButton_right_layout.addWidget(self.pushButton_redo)
        self.pushButton_layout.addLayout(self.pushButton_left_layout)
        self.pushButton_layout.addLayout(self.pushButton_right_layout)
        self.labels_vertical_layout.addLayout(self.pushButton_layout)

        self.labels_title = QtWidgets.QLabel(self.widget_labels)
        self.labels_title.setFont(Font.font_en)
        self.color_combobox = QComboBox()
        self.color_combobox.setFont(Font.font_en)
        self.color_combobox.setMinimumSize(QtCore.QSize(180, 20))
        self.color_combobox.setMaximumSize(QtCore.QSize(200, 20))

        for color, name in ParamConstant.COLOR_DATA:
            if color == "":
                self.color_combobox.setFont(Font.font_en)
                self.color_combobox.addItem(name)
            else:
                pix_color = QPixmap(20, 20)
                pix_color.fill(QColor(color))
                self.color_combobox.addItem(QIcon(pix_color), name)
        self.color_combobox.setCurrentIndex(1)

        self.label_color_layout = QHBoxLayout()
        self.label_color_layout.setAlignment(Qt.AlignLeft)
        self.label_color_layout.addWidget(self.labels_title)
        self.label_color_layout.addWidget(self.color_combobox)
        self.labels_vertical_layout.addLayout(self.label_color_layout)

        self.pushButton_load = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_load.setFont(Font.font_en)
        self.pushButton_load.setAutoExclusive(False)

        self.pushButton_save = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_save.setFont(Font.font_en)
        self.pushButton_save.setAutoExclusive(False)

        self.pushButton_segmentation = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_segmentation.setFont(Font.font_en)
        self.pushButton_segmentation.setAutoExclusive(False)

        self.pushButton_loadSegmentationResult = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_loadSegmentationResult.setFont(Font.font_en)
        self.pushButton_loadSegmentationResult.setAutoExclusive(False)

        self.retranslateUi()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.widget_title.setText(_translate("MainWindow", WindowConstant.TOOTH_LABELS_WIDGET))
        self.labels_title.setText(_translate("MainWindow", WindowConstant.FDI_LABEL))
        self.pushButton_paint.setText(_translate("MainWindow", WindowConstant.TOOTH_LANDMARK_PAINT_BUTTON))
        self.pushButton_clear.setText(_translate("MainWindow", WindowConstant.TOOTH_LANDMARK_CLEAR_BUTTON))
        self.pushButton_undo.setText(_translate("MainWindow", WindowConstant.TOOTH_LANDMARK_UNDO_BUTTON))
        self.pushButton_redo.setText(_translate("MainWindow", WindowConstant.TOOTH_LANDMARK_REDO_BUTTON))
        self.pushButton_load.setText(_translate("MainWindow", WindowConstant.TOOTH_LANDMARK_LOAD_BUTTON))
        self.pushButton_save.setText(_translate("MainWindow", WindowConstant.TOOTH_LANDMARK_SAVE_BUTTON))
        self.pushButton_segmentation.setText(_translate("MainWindow", WindowConstant.TOOTH_LANDMARK_Segmentation_BUTTON))
        self.pushButton_loadSegmentationResult.setText(_translate("MainWindow", WindowConstant.TOOTH_LANDMARK_LOAD_RESULT_BUTTON))


