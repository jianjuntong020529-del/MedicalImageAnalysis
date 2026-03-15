# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtWidgets
from src.ui.MainWindow import Ui_MainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(widget)
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    # 主程序运行窗口
    main()
