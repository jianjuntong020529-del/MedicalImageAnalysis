# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, QtGui


def _colorize_icon(sp_icon, color: QtGui.QColor, size: int = 18) -> QtGui.QIcon:
    """从 QStyle 标准图标取 pixmap，染成指定颜色后返回。"""
    app = QtWidgets.QApplication.instance()
    style = app.style()
    pixmap = style.standardIcon(sp_icon).pixmap(size, size)

    # 用 QPainter 叠加颜色（SourceIn 模式保留 alpha，替换 RGB）
    colored = QtGui.QPixmap(pixmap.size())
    colored.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(colored)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
    painter.fillRect(colored.rect(), color)
    painter.end()
    return QtGui.QIcon(colored)


def _draw_speed_icon(color: QtGui.QColor, size: int = 18) -> QtGui.QIcon:
    """自绘双三角速率图标，颜色可控。"""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(color)
    h = size
    half = size // 2
    gap = max(2, size // 8)
    left = QtGui.QPolygon([
        QtCore.QPoint(0,          2),
        QtCore.QPoint(half - gap, h // 2),
        QtCore.QPoint(0,          h - 2),
    ])
    right = QtGui.QPolygon([
        QtCore.QPoint(half,  2),
        QtCore.QPoint(size,  h // 2),
        QtCore.QPoint(half,  h - 2),
    ])
    painter.drawPolygon(left)
    painter.drawPolygon(right)
    painter.end()
    return QtGui.QIcon(pixmap)


# 颜色常量
_COLOR_ACTIVE  = QtGui.QColor(255, 255, 255)       # 白色 — 可用
_COLOR_DISABLED = QtGui.QColor(100, 100, 100)      # 深灰 — 禁用
_COLOR_LOOP_ON  = QtGui.QColor(79, 195, 247)       # 蓝色 — 循环激活


class PlaybackBar(QtWidgets.QWidget):
    """
    播放控制工具栏，叠加在 VTK 渲染窗口左上角。
    收起时只显示一个小的展开按钮（不叠加在工具栏上）。
    """

    _ICON_PLAY  = QtWidgets.QStyle.SP_MediaPlay
    _ICON_PAUSE = QtWidgets.QStyle.SP_MediaPause
    _ICON_STOP  = QtWidgets.QStyle.SP_MediaStop
    _ICON_PREV  = QtWidgets.QStyle.SP_MediaSkipBackward
    _ICON_NEXT  = QtWidgets.QStyle.SP_MediaSkipForward
    _ICON_LOOP  = QtWidgets.QStyle.SP_BrowserReload

    _BTN_SIZE   = QtCore.QSize(26, 26)
    _ICON_SIZE  = QtCore.QSize(16, 16)

    def __init__(self, parent_widget, controller):
        super().__init__(parent_widget)
        self._controller = controller
        self._controller.playback_bar = self
        self._is_enabled = False
        self._is_loop    = True
        self._collapsed  = False

        self._build_ui()
        self._connect_signals()

        self.set_enabled(False)
        self.set_loop(True)

        self.move(8, 8)
        self.raise_()
        self.show()

    # ── 构建 UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── 工具栏面板 ────────────────────────────────────────────────────────
        self._bar = QtWidgets.QWidget(self)
        self._bar.setStyleSheet(
            "QWidget { background-color: rgba(20,20,20,200); border-radius: 6px; }"
        )
        bar_layout = QtWidgets.QHBoxLayout(self._bar)
        bar_layout.setContentsMargins(6, 4, 6, 4)
        bar_layout.setSpacing(2)

        self._btn_prev  = self._make_btn()
        self._btn_play  = self._make_btn()
        self._btn_next  = self._make_btn()
        self._btn_stop  = self._make_btn()
        self._btn_speed = self._make_btn()
        self._btn_loop  = self._make_btn()

        self._btn_prev.setToolTip("上一帧")
        self._btn_play.setToolTip("播放 / 暂停")
        self._btn_next.setToolTip("下一帧")
        self._btn_stop.setToolTip("停止")
        self._btn_speed.setToolTip("速率设置")
        self._btn_loop.setToolTip("循环播放")

        # 收起按钮放在工具栏最右侧
        self._btn_collapse = self._make_btn()
        self._btn_collapse.setToolTip("收起")
        self._btn_collapse.setEnabled(True)   # 始终可点

        for btn in [self._btn_prev, self._btn_play, self._btn_next,
                    self._btn_stop, self._btn_speed, self._btn_loop,
                    self._btn_collapse]:
            bar_layout.addWidget(btn)

        self._bar.adjustSize()
        outer.addWidget(self._bar)

        # ── 展开按钮（收起状态时替换整个 widget）────────────────────────────
        self._expand_btn = QtWidgets.QPushButton(self)
        self._expand_btn.setToolTip("展开播放控制栏")
        self._expand_btn.setFixedSize(28, 28)
        self._expand_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(20,20,20,200);
                border: none;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: rgba(60,60,60,230);
            }
        """)
        self._expand_btn.hide()
        self._expand_btn.clicked.connect(self.expand)

        # ── 速率菜单 ──────────────────────────────────────────────────────────
        self._speed_menu = QtWidgets.QMenu(self)
        self._speed_menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30,30,30,230);
                color: white;
                border: 1px solid rgba(255,255,255,50);
                border-radius: 4px;
            }
            QMenu::item { padding: 4px 20px; }
            QMenu::item:selected { background-color: rgba(255,255,255,40); }
        """)
        self._speed_actions = {}
        for name in ["慢速 (5 FPS)", "标准 (15 FPS)", "快速 (30 FPS)"]:
            action = self._speed_menu.addAction(name)
            action.setCheckable(True)
            self._speed_actions[name] = action
        self._speed_actions["标准 (15 FPS)"].setChecked(True)
        self._speed_menu.addSeparator()
        self._action_settings = self._speed_menu.addAction("更多设置...")
        self._action_settings.triggered.connect(
            lambda: self._controller.open_settings_dialog(parent=self)
        )

        self.adjustSize()

    def _make_btn(self) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(self._bar)
        btn.setFixedSize(self._BTN_SIZE)
        btn.setIconSize(self._ICON_SIZE)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover:enabled {
                background: rgba(255,255,255,35);
            }
        """)
        return btn

    def _refresh_icons(self):
        """根据当前启用状态重新渲染所有图标颜色。"""
        c = _COLOR_ACTIVE if self._is_enabled else _COLOR_DISABLED
        lc = _COLOR_LOOP_ON if self._is_loop else c

        self._btn_prev.setIcon(_colorize_icon(self._ICON_PREV,  c))
        self._btn_play.setIcon(_colorize_icon(self._ICON_PLAY,  c))
        self._btn_next.setIcon(_colorize_icon(self._ICON_NEXT,  c))
        self._btn_stop.setIcon(_colorize_icon(self._ICON_STOP,  c))
        self._btn_speed.setIcon(_draw_speed_icon(c))
        self._btn_loop.setIcon(_colorize_icon(self._ICON_LOOP,  lc))

        # 收起/展开按钮始终白色
        collapse_icon = _colorize_icon(QtWidgets.QStyle.SP_TitleBarMinButton,
                                       _COLOR_ACTIVE)
        self._btn_collapse.setIcon(collapse_icon)
        self._expand_btn.setIcon(_colorize_icon(self._ICON_PLAY, _COLOR_ACTIVE))
        self._expand_btn.setIconSize(QtCore.QSize(12, 12))

    # ── 信号连接 ──────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self._btn_prev.clicked.connect(self._controller.on_prev_frame)
        self._btn_play.clicked.connect(self._on_play_clicked)
        self._btn_next.clicked.connect(self._controller.on_next_frame)
        self._btn_stop.clicked.connect(self._controller.on_stop)
        self._btn_speed.clicked.connect(self._show_speed_menu)
        self._btn_loop.clicked.connect(self._controller.toggle_loop)
        self._btn_collapse.clicked.connect(self.collapse)

        for name, action in self._speed_actions.items():
            action.triggered.connect(lambda checked, n=name: self._on_speed_selected(n))

    def _on_play_clicked(self):
        if self._controller.state.is_playing:
            self._controller.on_pause()
        else:
            self._controller.on_play()

    def _show_speed_menu(self):
        pos = self._btn_speed.mapToGlobal(QtCore.QPoint(0, self._btn_speed.height()))
        self._speed_menu.exec_(pos)

    def _on_speed_selected(self, name: str):
        for n, action in self._speed_actions.items():
            action.setChecked(n == name)
        # 提取 FPS 对应的预设 key
        key_map = {"慢速 (5 FPS)": "慢速", "标准 (15 FPS)": "标准", "快速 (30 FPS)": "快速"}
        self._controller.set_speed(key_map.get(name, "标准"))

    # ── 公开接口 ──────────────────────────────────────────────────────────────

    def set_playing(self, playing: bool) -> None:
        c = _COLOR_ACTIVE if self._is_enabled else _COLOR_DISABLED
        icon_type = self._ICON_PAUSE if playing else self._ICON_PLAY
        self._btn_play.setIcon(_colorize_icon(icon_type, c))

    def set_loop(self, loop: bool) -> None:
        self._is_loop = loop
        c = _COLOR_ACTIVE if self._is_enabled else _COLOR_DISABLED
        lc = _COLOR_LOOP_ON if loop else c
        self._btn_loop.setIcon(_colorize_icon(self._ICON_LOOP, lc))

    def set_speed_label(self, speed_name: str) -> None:
        key_map = {"慢速": "慢速 (5 FPS)", "标准": "标准 (15 FPS)", "快速": "快速 (30 FPS)"}
        full = key_map.get(speed_name, speed_name)
        for n, action in self._speed_actions.items():
            action.setChecked(n == full)

    def set_enabled(self, enabled: bool) -> None:
        self._is_enabled = enabled
        for btn in [self._btn_prev, self._btn_play, self._btn_next,
                    self._btn_stop, self._btn_speed, self._btn_loop]:
            btn.setEnabled(enabled)
        self._refresh_icons()

    def collapse(self) -> None:
        """收起工具栏，只显示小圆形展开按钮。"""
        self._collapsed = True
        self._bar.hide()
        self.resize(28, 28)
        self._expand_btn.move(0, 0)
        self._expand_btn.show()
        self._expand_btn.raise_()

    def expand(self) -> None:
        """展开工具栏，隐藏展开按钮。"""
        self._collapsed = False
        self._expand_btn.hide()
        self._bar.show()
        self.adjustSize()

    # ── 事件 ──────────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.move(8, 8)
