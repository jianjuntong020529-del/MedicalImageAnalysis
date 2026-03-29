# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Callable, Optional

from PyQt5 import QtCore, QtWidgets

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PlaybackState:
    is_playing: bool = False
    is_loop: bool = True
    current_slice: int = 0
    slice_min: int = 0
    slice_max: int = 0
    play_end: int = 0       # 播放范围结束帧（默认等于 slice_max）
    speed_name: str = "标准"
    fps: int = 15
    interval_ms: int = 60


class PlaybackController:
    """
    播放控制器，管理定时器、状态和与 VTK viewer 的交互。
    每个切片视图对应一个独立实例。
    """

    SPEED_PRESETS = {
        "慢速": (10, 100),    # 5 FPS, 200ms
        "标准": (15, 60),    # 15 FPS, 60ms
        "快速": (30, 30),    # 30 FPS, 33ms
    }
    DEFAULT_SPEED = "标准"

    def __init__(
        self,
        viewer_getter: Callable,
        slider: QtWidgets.QSlider,
        label: QtWidgets.QLabel,
        view_id: str,
    ):
        """
        viewer_getter: 返回当前 viewer 的可调用对象（延迟绑定，支持数据重载后更新）
        slider: QtOrthoViewer.slider
        label: QtOrthoViewer.slider_label
        view_id: "XY" / "YZ" / "XZ"
        """
        self.viewer_getter = viewer_getter
        self.slider = slider
        self.label = label
        self.view_id = view_id

        self.state = PlaybackState()

        # 关联的 PlaybackBar（由 PlaybackBar 自身注册）
        self.playback_bar = None

        # QTimer 驱动帧推进
        self._timer = QtCore.QTimer()
        self._timer.setInterval(self.state.interval_ms)
        self._timer.timeout.connect(self._tick)

        logger.debug("PlaybackController created for view %s", view_id)

    # ── 内部方法 ──────────────────────────────────────────────────────────────

    def _get_viewer(self):
        """通过 viewer_getter 获取当前 viewer，若无效返回 None。"""
        try:
            viewer = self.viewer_getter()
            if viewer is None:
                return None
            return viewer
        except Exception:
            logger.debug("viewer_getter raised exception", exc_info=True)
            return None

    def _set_slice(self, index: int) -> None:
        """设置切片，同步 viewer / slider / label。"""
        viewer = self._get_viewer()
        if viewer is None:
            return

        try:
            viewer.SetSlice(index)
            viewer.GetRenderWindow().Render()
        except Exception:
            logger.debug("Error setting slice on viewer", exc_info=True)

        self.state.current_slice = index

        try:
            self.slider.setValue(index)
        except Exception:
            logger.debug("Error setting slider value", exc_info=True)

        try:
            self.label.setText("Slice %d/%d" % (index, self.state.slice_max))
        except Exception:
            logger.debug("Error setting label text", exc_info=True)

    def _tick(self) -> None:
        """定时器回调，推进一帧。"""
        viewer = self._get_viewer()
        if viewer is None:
            # viewer 无效，停止定时器
            self._timer.stop()
            self.state.is_playing = False
            return

        next_slice = self.state.current_slice + 1
        end = self.state.play_end

        if next_slice > end:
            if self.state.is_loop:
                # 循环模式：跳回起始帧
                next_slice = self.state.slice_min
            else:
                # 非循环模式：停止播放，保持在末帧
                self._timer.stop()
                self.state.is_playing = False
                if self.playback_bar is not None:
                    self.playback_bar.set_playing(False)
                return

        self._set_slice(next_slice)

    # ── 公开接口 ──────────────────────────────────────────────────────────────

    def on_play(self) -> None:
        """开始播放。"""
        if self.state.slice_max == 0:
            return
        self.state.is_playing = True
        self._timer.setInterval(self.state.interval_ms)
        self._timer.start()
        if self.playback_bar is not None:
            self.playback_bar.set_playing(True)
        logger.debug("PlaybackController[%s] play started", self.view_id)

    def on_pause(self) -> None:
        """暂停播放。"""
        self._timer.stop()
        self.state.is_playing = False
        if self.playback_bar is not None:
            self.playback_bar.set_playing(False)
        logger.debug("PlaybackController[%s] paused", self.view_id)

    def on_stop(self) -> None:
        """停止播放，通知 PlaybackBar 收起。"""
        self._timer.stop()
        self.state.is_playing = False
        if self.playback_bar is not None:
            self.playback_bar.set_playing(False)
            self.playback_bar.collapse()
        logger.debug("PlaybackController[%s] stopped", self.view_id)

    def on_prev_frame(self) -> None:
        """跳转到上一帧。"""
        new_slice = max(self.state.current_slice - 1, self.state.slice_min)
        self._set_slice(new_slice)

    def on_next_frame(self) -> None:
        """跳转到下一帧。"""
        new_slice = min(self.state.current_slice + 1, self.state.slice_max)
        self._set_slice(new_slice)

    def set_speed(self, speed_name: str) -> None:
        """切换播放速率，播放中立即生效。"""
        if speed_name not in self.SPEED_PRESETS:
            logger.warning("Unknown speed preset: %s", speed_name)
            return
        fps, interval_ms = self.SPEED_PRESETS[speed_name]
        self.state.speed_name = speed_name
        self.state.fps = fps
        self.state.interval_ms = interval_ms
        self._timer.setInterval(interval_ms)
        # 若正在播放，重启定时器使新间隔立即生效
        if self.state.is_playing:
            self._timer.stop()
            self._timer.start()
        if self.playback_bar is not None:
            self.playback_bar.set_speed_label(speed_name)
        logger.debug("PlaybackController[%s] speed set to %s (%d FPS)", self.view_id, speed_name, fps)

    def toggle_loop(self) -> None:
        """切换循环模式。"""
        self.state.is_loop = not self.state.is_loop
        if self.playback_bar is not None:
            self.playback_bar.set_loop(self.state.is_loop)
        logger.debug("PlaybackController[%s] loop=%s", self.view_id, self.state.is_loop)

    def on_slider_changed(self, value: int) -> None:
        """响应 VerticalSlider 手动拖动，同步内部切片索引（不触发播放）。"""
        self.state.current_slice = value

    def open_settings_dialog(self, parent=None) -> None:
        """打开播放参数设置弹窗。"""
        from src.widgets.PlaybackSettingsDialog import PlaybackSettingsDialog
        dlg = PlaybackSettingsDialog(
            current_fps=self.state.fps,
            slice_max=self.state.slice_max,
            parent=parent,
        )
        dlg.settings_applied.connect(self._apply_settings)
        dlg.exec_()

    def _apply_settings(self, settings: dict) -> None:
        """应用设置面板传入的参数（fps、start、end）。"""
        fps = settings.get("fps", self.state.fps)
        start = settings.get("start", self.state.slice_min)
        end = settings.get("end", self.state.play_end)

        # 更新帧率（找到最接近的预设，或直接设置自定义值）
        self.state.fps = fps
        self.state.interval_ms = max(1, 1000 // fps)
        self._timer.setInterval(self.state.interval_ms)
        if self.state.is_playing:
            self._timer.stop()
            self._timer.start()

        # 更新播放范围
        self.state.slice_min = start
        self.state.play_end = end

        # 若当前切片超出新范围，跳到起始帧
        if self.state.current_slice < start or self.state.current_slice > end:
            self._set_slice(start)

        logger.debug(
            "PlaybackController[%s] settings applied: fps=%d, start=%d, end=%d",
            self.view_id, fps, start, end,
        )

    def on_data_loaded(self) -> None:
        """数据加载完成后调用，更新 SliceMax，启用按钮，停止当前播放。"""
        # 停止当前播放
        self._timer.stop()
        self.state.is_playing = False

        viewer = self._get_viewer()
        if viewer is not None:
            try:
                slice_max = viewer.GetSliceMax()
                self.state.slice_max = slice_max
                self.state.play_end = slice_max
                self.state.current_slice = viewer.GetSlice()
                logger.debug(
                    "PlaybackController[%s] data loaded: slice_max=%d, current=%d",
                    self.view_id, slice_max, self.state.current_slice
                )
            except Exception:
                logger.debug("Error reading slice info from viewer", exc_info=True)

        # 启用 PlaybackBar 按钮
        if self.playback_bar is not None:
            self.playback_bar.set_playing(False)
            self.playback_bar.set_enabled(True)
