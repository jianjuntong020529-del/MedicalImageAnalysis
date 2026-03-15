from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from src.constant.WindowConstant import WindowConstant
from src.style.AppVisualStyle import APPVisualStyle
from src.style.FontStyle import Font


class Annotation:
    def __init__(self):
        self.widget = None

    def init_widget(self):
        self.widget_labels = QtWidgets.QWidget(self.widget)
        self.widget_labels.setMinimumSize(QtCore.QSize(350, 100))
        self.widget_labels.setMaximumSize(QtCore.QSize(400, 100))
        self.widget_labels.hide()
        self.widget_labels.setObjectName("widget_label")
        self.widget_labels.setStyleSheet(APPVisualStyle.WIDGET_BACKGROUND_COLOR)
        self.labels_vertical_layout = QtWidgets.QVBoxLayout(self.widget_labels)
        self.labels_vertical_layout.setContentsMargins(11, 11, 11, 11)
        self.labels_vertical_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.labels_vertical_layout.setAlignment(Qt.AlignTop)

        # -----------------------------title---------------------------------------
        self.widget_title = QtWidgets.QLabel(self.widget_labels)
        self.widget_title.setMinimumSize(QtCore.QSize(100, 20))
        self.widget_title.setMaximumSize(QtCore.QSize(150, 20))
        self.widget_title.setStyleSheet(APPVisualStyle.WIDGET_LABEL_COLOR)
        self.widget_title.setFont(Font.font2)
        self.labels_vertical_layout.addWidget(self.widget_title, Qt.AlignLeft | Qt.AlignTop)

        self.pushButton_clear = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_clear.setFont(Font.font)
        self.pushButton_clear.setAutoExclusive(False)

        self.pushButton_undo = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_undo.setFont(Font.font)
        self.pushButton_undo.setAutoExclusive(False)

        self.pushButton_redo = QtWidgets.QPushButton(self.widget_labels)
        self.pushButton_redo.setFont(Font.font)
        self.pushButton_redo.setAutoExclusive(False)

        self.pushButton_layout = QtWidgets.QHBoxLayout()
        self.pushButton_layout.setSpacing(APPVisualStyle.LAYOUT_SPACING)
        self.pushButton_layout.setContentsMargins(11, 11, 11, 11)
        self.pushButton_layout.addWidget(self.pushButton_redo)
        self.pushButton_layout.addWidget(self.pushButton_undo)
        self.pushButton_layout.addWidget(self.pushButton_clear)
        self.labels_vertical_layout.addLayout(self.pushButton_layout)
        self.translateUi()

    def translateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.widget_title.setText(_translate("QMainWindow", WindowConstant.ANNOTATION_WIDGET_LABEL))
        self.pushButton_clear.setText(_translate("QMainWindow", WindowConstant.CLEAR_BUTTON))
        self.pushButton_undo.setText(_translate("QMainWindow", WindowConstant.UNDO_BUTTON))
        self.pushButton_redo.setText(_translate("QMainWindow", WindowConstant.REDO_BUTTON))
