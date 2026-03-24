# -*- coding: utf-8 -*-
"""
加载动画组件 - 顶部进度条 + 状态栏内联提示
不阻塞主界面操作，顶部进度条推进，状态栏显示加载状态/完成/失败
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen


class SpinnerWidget(QWidget):
    """小型旋转圆圈，用于状态栏"""

    def __init__(self, size=16, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer_id = None

    def start(self):
        if self._timer_id is None:
            self._timer_id = self.startTimer(16)

    def stop(self):
        if self._timer_id is not None:
            self.killTimer(self._timer_id)
            self._timer_id = None
        self._angle = 0
        self.update()

    def timerEvent(self, event):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self.width()
        from PyQt5.QtCore import QRectF
        pen = QPen(QColor('#555555'), 2, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(QRectF(2, 2, s-4, s-4), 0, 270*16)
        pen.setColor(QColor('#378ADD'))
        p.setPen(pen)
        p.drawArc(QRectF(2, 2, s-4, s-4), -self._angle*16, 90*16)


class TopProgressBar(QWidget):
    """顶部进度条，显示在主窗口顶部"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self.hide()

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet('''
            QProgressBar { background: transparent; border: none; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff, stop:1 #378ADD);
            }
        ''')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.progress)

    def set_progress(self, value):
        self.progress.setValue(value)

    def start_loading(self):
        self.progress.setValue(0)
        self.show()
        self.raise_()

    def finish_loading(self):
        self.progress.setValue(100)
        QTimer.singleShot(400, self.hide)

    def resizeEvent(self, event):
        if self.parent():
            self.setFixedWidth(self.parent().width())


class StatusBarWidget(QWidget):
    """嵌入状态栏的加载状态组件"""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        self.spinner = SpinnerWidget(16, self)
        layout.addWidget(self.spinner)

        self.message_label = QLabel()
        self.message_label.setStyleSheet('font-size: 12px;')
        layout.addWidget(self.message_label)

        self.hide()

    def show_loading(self, fmt, filename=''):
        """显示加载中"""
        msg = f'正在加载 {fmt}'
        if filename:
            msg += f'  {filename}'
        self.message_label.setText(msg)
        self.message_label.setStyleSheet('font-size: 12px;')
        self.spinner.start()
        self.show()

    def show_success(self, fmt, filename=''):
        """显示成功"""
        self.spinner.stop()
        msg = f'✓  {fmt} 加载完成'
        if filename:
            msg += f'  {filename}'
        self.message_label.setText(msg)
        self.message_label.setStyleSheet('font-size: 12px; color: #4CAF50;')
        QTimer.singleShot(4000, self.hide)

    def show_error(self, fmt, error_msg=''):
        """显示失败"""
        self.spinner.stop()
        msg = f'✗  {fmt} 加载失败'
        if error_msg:
            short = error_msg[:40] + '...' if len(error_msg) > 40 else error_msg
            msg += f'  {short}'
        self.message_label.setText(msg)
        self.message_label.setStyleSheet('font-size: 12px; color: #f44336;')
        QTimer.singleShot(6000, self.hide)


class LoadingIndicator:
    """加载指示器管理类 - 顶部进度条 + 状态栏内联提示"""

    def __init__(self, main_window):
        self.main_window = main_window

        # 顶部进度条
        self.top_progress = TopProgressBar(main_window)
        self.top_progress.move(0, 0)
        self.top_progress.setFixedWidth(main_window.width())
        self.top_progress.raise_()

        # 状态栏组件
        self.status_widget = StatusBarWidget()
        main_window.statusBar().addPermanentWidget(self.status_widget)
        main_window.statusBar().show()

        self._is_loading = False
        self._current_fmt = ''
        self._current_filename = ''

    def start_loading(self, fmt, filename=''):
        self._is_loading = True
        self._current_fmt = fmt
        self._current_filename = filename
        self.top_progress.start_loading()
        self.status_widget.show_loading(fmt, filename)

    def update_progress(self, value):
        if self._is_loading:
            self.top_progress.set_progress(value)

    def finish_success(self):
        if self._is_loading:
            self._is_loading = False
            self.top_progress.finish_loading()
            self.status_widget.show_success(self._current_fmt, self._current_filename)

    def finish_error(self, error_msg=''):
        if self._is_loading:
            self._is_loading = False
            self.top_progress.finish_loading()
            self.status_widget.show_error(self._current_fmt, error_msg)

    def is_loading(self):
        return self._is_loading

    def resize_event(self):
        """主窗口大小改变时调用"""
        self.top_progress.setFixedWidth(self.main_window.width())
