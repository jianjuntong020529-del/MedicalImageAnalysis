# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal


class PlaybackSettingsDialog(QtWidgets.QDialog):
    """
    播放参数设置弹窗。
    发出 settings_applied 信号，携带 {"fps": int, "start": int, "end": int}。
    """

    settings_applied = pyqtSignal(dict)

    def __init__(self, current_fps: int = 15, slice_max: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("播放设置")
        self.setModal(True)
        self.setMinimumWidth(280)

        self._slice_max = slice_max
        self._build_ui(current_fps, slice_max)
        self._connect_signals()
        self._validate()

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _build_ui(self, current_fps: int, slice_max: int):
        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        # FPS 输入框
        self._fps_spin = QtWidgets.QSpinBox()
        self._fps_spin.setRange(1, 60)
        self._fps_spin.setValue(current_fps)
        self._fps_spin.setSuffix(" FPS")
        layout.addRow("帧率：", self._fps_spin)

        # 起始帧
        self._start_spin = QtWidgets.QSpinBox()
        self._start_spin.setRange(0, slice_max)
        self._start_spin.setValue(0)
        layout.addRow("起始帧：", self._start_spin)

        # 结束帧
        self._end_spin = QtWidgets.QSpinBox()
        self._end_spin.setRange(0, slice_max)
        self._end_spin.setValue(slice_max)
        layout.addRow("结束帧：", self._end_spin)

        # 错误提示标签（默认隐藏）
        self._error_label = QtWidgets.QLabel("起始帧不能大于结束帧")
        self._error_label.setStyleSheet("color: red; font-size: 12px;")
        self._error_label.setAlignment(QtCore.Qt.AlignCenter)
        self._error_label.hide()
        layout.addRow(self._error_label)

        # 确认 / 取消按钮
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btn_box.button(QtWidgets.QDialogButtonBox.Ok).setText("确认")
        btn_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("取消")
        self._ok_btn = btn_box.button(QtWidgets.QDialogButtonBox.Ok)
        layout.addRow(btn_box)

        btn_box.accepted.connect(self._on_accepted)
        btn_box.rejected.connect(self.reject)

    # ── 信号连接 ──────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self._start_spin.valueChanged.connect(self._validate)
        self._end_spin.valueChanged.connect(self._validate)

    # ── 验证逻辑 ──────────────────────────────────────────────────────────────

    def _validate(self):
        """start > end 时显示错误并禁用确认按钮。"""
        invalid = self._start_spin.value() > self._end_spin.value()
        self._error_label.setVisible(invalid)
        self._ok_btn.setEnabled(not invalid)

    # ── 槽函数 ────────────────────────────────────────────────────────────────

    def _on_accepted(self):
        self.settings_applied.emit({
            "fps": self._fps_spin.value(),
            "start": self._start_spin.value(),
            "end": self._end_spin.value(),
        })
        self.accept()
