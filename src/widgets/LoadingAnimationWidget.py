# -*- coding: utf-8 -*-
"""
加载动画组件
提供文件加载时的可视化反馈，包括进度条、步骤指示和旋转动画
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QFrame
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen


class SpinnerWidget(QWidget):
    """旋转圆圈 spinner，纯 QPainter 绘制"""
    
    def __init__(self, size=32, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = None
        
    def start(self):
        """启动旋转动画"""
        if self._timer is None:
            self._timer = self.startTimer(16)  # ~60fps
    
    def stop(self):
        """停止旋转动画"""
        if self._timer is not None:
            self.killTimer(self._timer)
            self._timer = None
    
    def timerEvent(self, event):
        """定时器事件，更新旋转角度"""
        self._angle = (self._angle + 6) % 360
        self.update()
    
    def paintEvent(self, event):
        """绘制旋转圆圈"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        
        # 灰色底弧（270°）
        pen = QPen(QColor('#3a3a3a'), 3)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(4, 4, w-8, w-8, 0, 270*16)
        
        # 蓝色动画弧（90°）
        pen.setColor(QColor('#378ADD'))
        p.setPen(pen)
        from PyQt5.QtCore import QRectF
        p.drawArc(QRectF(4, 4, w-8, w-8), (-self._angle)*16, 90*16)


class LoadingOverlay(QWidget):
    """
    半透明遮罩，叠加在目标 widget 上方
    显示加载进度、步骤和取消按钮
    """
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent, fmt='', filename=''):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet('background: rgba(0, 0, 0, 0.75)')
        
        # 用于淡出动画
        self._opacity = 1.0
        self._fade_timer = None
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        
        # 背景卡片 - 更大更美观
        card = QFrame()
        card.setFixedWidth(380)
        card.setStyleSheet('''
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d2d, stop:1 #252525);
                border: 1px solid #404040;
                border-radius: 16px;
            }
        ''')
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(16)
        
        # 顶部：spinner + 文件信息
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        
        self.spinner = SpinnerWidget(40)  # 更大的 spinner
        top_row.addWidget(self.spinner)
        
        info = QVBoxLayout()
        info.setSpacing(6)
        
        # 文件名 - 更大更清晰
        self.lbl_name = QLabel(filename)
        self.lbl_name.setStyleSheet('''
            font-weight: 600; 
            font-size: 15px; 
            color: #ffffff;
            letter-spacing: 0.5px;
        ''')
        self.lbl_name.setWordWrap(True)
        
        # 格式信息 - 更清晰的层次
        self.lbl_fmt = QLabel(f'{fmt} · 正在加载...')
        self.lbl_fmt.setStyleSheet('''
            font-size: 12px; 
            color: #aaaaaa;
            letter-spacing: 0.3px;
        ''')
        
        info.addWidget(self.lbl_name)
        info.addWidget(self.lbl_fmt)
        top_row.addLayout(info, 1)
        
        card_layout.addLayout(top_row)
        
        # 进度条 - 更高更明显
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet('''
            QProgressBar { 
                background: #1a1a1a; 
                border-radius: 3px; 
                border: none; 
            }
            QProgressBar::chunk { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff, stop:1 #378ADD);
                border-radius: 3px; 
            }
        ''')
        card_layout.addWidget(self.progress_bar)
        
        # 步骤描述 - 更大更清晰
        self.lbl_step = QLabel('准备中...')
        self.lbl_step.setStyleSheet('''
            font-size: 13px; 
            color: #bbbbbb;
            font-weight: 500;
            letter-spacing: 0.3px;
        ''')
        self.lbl_step.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.lbl_step)
        
        # 步骤列表容器
        self.step_list = QWidget()
        step_v = QVBoxLayout(self.step_list)
        step_v.setContentsMargins(0, 4, 0, 4)
        step_v.setSpacing(6)
        card_layout.addWidget(self.step_list)
        
        self.step_widgets = []
        
        # 取消按钮 - 更美观
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.setFixedHeight(32)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet('''
            QPushButton {
                background: transparent;
                border: 1.5px solid #555555;
                border-radius: 16px;
                color: #aaaaaa;
                font-size: 12px;
                font-weight: 500;
                padding: 0 20px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: rgba(211, 47, 47, 0.15);
                border-color: #d32f2f;
                color: #ff5252;
            }
            QPushButton:pressed {
                background: rgba(211, 47, 47, 0.25);
            }
        ''')
        self.cancel_btn.clicked.connect(self.cancelled.emit)
        card_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(card)
        self.hide()
    
    def set_steps(self, steps: list):
        """传入步骤名称列表，动态生成步骤行"""
        # 清除旧步骤
        for sw in self.step_widgets:
            sw.setParent(None)
            sw.deleteLater()
        self.step_widgets.clear()
        
        # 创建新步骤 - 更美观的样式
        for name in steps:
            row = QLabel(f'○  {name}')
            row.setStyleSheet('''
                font-size: 12px; 
                color: #777777;
                padding: 2px 0;
                letter-spacing: 0.3px;
            ''')
            self.step_list.layout().addWidget(row)
            self.step_widgets.append(row)
    
    def mark_step(self, idx: int, state: str):
        """
        标记步骤状态
        state: 'pending' | 'active' | 'done'
        """
        if idx >= len(self.step_widgets):
            return
        
        w = self.step_widgets[idx]
        name = w.text().split('  ', 1)[-1]
        
        if state == 'done':
            w.setText(f'✓  {name}')
            w.setStyleSheet('''
                font-size: 12px; 
                color: #4CAF50;
                font-weight: 500;
                padding: 2px 0;
                letter-spacing: 0.3px;
            ''')
        elif state == 'active':
            w.setText(f'›  {name}')
            w.setStyleSheet('''
                font-size: 12px; 
                color: #4a9eff; 
                font-weight: 600;
                padding: 2px 0;
                letter-spacing: 0.3px;
            ''')
        else:
            w.setText(f'○  {name}')
            w.setStyleSheet('''
                font-size: 12px; 
                color: #777777;
                padding: 2px 0;
                letter-spacing: 0.3px;
            ''')
    
    def update_progress(self, pct: int, step_desc: str):
        """更新进度条和步骤描述"""
        self.progress_bar.setValue(pct)
        self.lbl_step.setText(step_desc)
    
    def show_over(self, target: QWidget):
        """在目标控件上方显示遮罩"""
        self.setParent(target)
        self.resize(target.size())
        self.show()
        self.raise_()
        self.spinner.start()
    
    def fade_out_and_close(self):
        """淡出动画后关闭"""
        # 停止 spinner
        self.spinner.stop()
        
        # 创建淡出动画
        from PyQt5.QtCore import QTimer
        self._opacity = 1.0
        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._fade_step)
        self._fade_timer.start(16)  # 约60fps
    
    def _fade_step(self):
        """淡出动画步骤"""
        self._opacity -= 0.08  # 每步减少8%，约需12帧（200ms）
        
        if self._opacity <= 0:
            self._fade_timer.stop()
            self.hide()
            self.deleteLater()
        else:
            # 更新透明度
            self.setStyleSheet(f'background: rgba(0, 0, 0, {self._opacity * 0.75})')
    
    def hideEvent(self, event):
        """隐藏时停止动画"""
        self.spinner.stop()
        if self._fade_timer:
            self._fade_timer.stop()
        super().hideEvent(event)
    
    def resizeEvent(self, event):
        """跟随父控件大小变化"""
        if self.parent():
            self.resize(self.parent().size())
