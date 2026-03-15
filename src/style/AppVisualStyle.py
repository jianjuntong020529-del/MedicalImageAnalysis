from pyface.qt import QtGui

from src.constant.WindowConstant import WindowConstant


class APPVisualStyle:
    # 设置背景颜色
    color = QtGui.QColor(255, 255, 255)  # RGB颜色，可以根据需要调整值
    BACKGROUND_COLOR = f"background-color:{color.name()};"
    # 布局spacing
    LAYOUT_SPACING = 6

    WIDGET_BACKGROUND_COLOR = 'background-color:#fafafa'
    WIDGET_LABEL_COLOR = "color:green"

    # 主菜单栏样式
    menubar_style = """
                       QMenuBar{
                           background-color: rgba(255, 255, 255);
                           border: 1px solid rgba(240, 240, 240);
                       }
                       QMenuBar::item {
                           color: rgb(0, 0, 0);
                           background: rgba(255, 255, 255);
                           padding: 4px 10px;
                       }
                       QMenuBar::item:selected {
                           background: rgba(48, 140, 198);
                           color: rgb(255, 255, 255);
                       }
                       QMenuBar::item:pressed {
                           background: rgba(48, 140, 198,0.4);
                       }
                   """
    # 子菜单栏样式
    menu_style = """
                       QMenu {
                           background-color: rgba(255, 255, 255);
                           border: 1px solid rgba(244, 244, 244);
                       }
                       QMenu::item {
                           color: rgb(0, 0, 0);
                           background: rgba(255, 255, 255);
                       }
                       QMenu::item:selected {
                           background: rgba(48, 140, 198);
                           color: rgb(255, 255, 255);
                       }
                       QMenu::item:pressed {
                           background: rgba(48, 140, 198,0.4);
                       }
                   """

    # ToolBar Style
    RULER = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.RULER + "</span></p></body></html>"
    PAINT = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.PAINT + "</span></p></body></html>"
    POLY_LINE = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.POLY_LINE + "</span></p></body></html>"
    ANGLE = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.ANGLE + "</span></p></body></html>"
    HU = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.HU + "</span></p></body></html>"
    RESET = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.RESET + "</span></p></body></html>"
    CROSSHAIR = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.CROSSHAIR + "</span></p></body></html>"
    DRAGGING = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.DRAGGING + "</span></p></body></html>"
    ROI = "<html><head/><body><p><span style=\' font-size:11pt; font-weight:600;\'>" + WindowConstant.ROI + "</span></p></body></html>"


