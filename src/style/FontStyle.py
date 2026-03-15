from pyface.qt import QtGui


class Font:
    # 中文字体样式
    font = QtGui.QFont()
    font.setFamily("华文宋体")
    font.setPointSize(10)

    font2 = QtGui.QFont()
    font2.setFamily("华文宋体")
    font2.setPointSize(11)

    # 英文字体样式
    # font = QtGui.QFont()
    # font.setFamily("Times New Roman")
    # font.setPointSize(10)
    #
    # font2 = QtGui.QFont()
    # font2.setFamily("Times New Roman")
    # font2.setPointSize(11)

    font_en = QtGui.QFont()
    font_en.setFamily("Times New Roman")
    font_en.setPointSize(14)
