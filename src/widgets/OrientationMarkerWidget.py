# -*- coding: utf-8 -*-
"""
方位标识 (Anatomical Directional Markers)
- 在三视图四边中心显示解剖方位字母
- 固定在视口边缘，不随图像缩放/平移移动
- 支持显示/隐藏切换

方位映射（标准解剖位）：
  XY (Axial)   : Top=A  Bottom=P  Left=R  Right=L
  YZ (Sagittal): Top=S  Bottom=I  Left=A  Right=P
  XZ (Coronal) : Top=S  Bottom=I  Left=R  Right=L
"""
import vtk

# 各视图方位映射 {view_id: (top, bottom, left, right)}
_ORIENTATION_MAP = {
    "XY": ("A", "P", "R", "L"),
    "YZ": ("S", "I", "A", "P"),
    "XZ": ("S", "I", "R", "L"),
}

_FONT_SIZE = 20
_PADDING   = 12    # 距视口边缘像素


class OrientationMarker:
    """
    方位标识，叠加在指定 renderer 四边中心。
    使用 NormalizedViewport 坐标，固定位置不随图像移动。
    """

    def __init__(self, renderer: vtk.vtkRenderer, view_id: str = "XY"):
        self._renderer = renderer
        self._viewer   = None
        self._obs_id   = None
        self._visible  = False
        self._view_id  = view_id

        # 四个方位 actor：top / bottom / left / right
        self._actors: dict[str, vtk.vtkTextActor] = {}
        for pos in ("top", "bottom", "left", "right"):
            actor = self._make_actor()
            renderer.AddActor2D(actor)
            actor.SetVisibility(0)
            self._actors[pos] = actor

        self._apply_orientation(view_id)

    # ── 构建单个文字 actor ────────────────────────────────────────────────────

    def _make_actor(self) -> vtk.vtkTextActor:
        actor = vtk.vtkTextActor()
        tp = actor.GetTextProperty()
        tp.SetFontSize(_FONT_SIZE)
        tp.SetFontFamilyToArial()
        tp.BoldOn()
        tp.ShadowOn()
        tp.SetShadowOffset(1, -1)
        tp.SetColor(1.0, 1.0, 1.0)          # 白色
        # 黑色描边增强对比度
        tp.SetShadowOffset(1, -1)
        actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        actor.GetPosition2Coordinate().SetCoordinateSystemToNormalizedViewport()
        return actor

    # ── 设置方位文字和位置 ────────────────────────────────────────────────────

    def _apply_orientation(self, view_id: str):
        self._view_id = view_id
        labels = _ORIENTATION_MAP.get(view_id, ("?", "?", "?", "?"))
        top, bottom, left, right = labels

        # top：水平居中，靠上
        a = self._actors["top"]
        a.SetInput(top)
        tp = a.GetTextProperty()
        tp.SetJustificationToCentered()
        tp.SetVerticalJustificationToTop()
        a.GetPositionCoordinate().SetValue(0.5, 0.95)

        # bottom：水平居中，靠下
        a = self._actors["bottom"]
        a.SetInput(bottom)
        tp = a.GetTextProperty()
        tp.SetJustificationToCentered()
        tp.SetVerticalJustificationToBottom()
        a.GetPositionCoordinate().SetValue(0.5, 0.05)

        # left：垂直居中，靠左
        a = self._actors["left"]
        a.SetInput(left)
        tp = a.GetTextProperty()
        tp.SetJustificationToLeft()
        tp.SetVerticalJustificationToCentered()
        a.GetPositionCoordinate().SetValue(0.05, 0.5)

        # right：垂直居中，靠右
        a = self._actors["right"]
        a.SetInput(right)
        tp = a.GetTextProperty()
        tp.SetJustificationToRight()
        tp.SetVerticalJustificationToCentered()
        a.GetPositionCoordinate().SetValue(0.95, 0.5)

    # ── 绑定 viewer ───────────────────────────────────────────────────────────

    def attach(self, viewer):
        if self._viewer is not None and self._obs_id is not None:
            try:
                self._viewer.GetRenderWindow().RemoveObserver(self._obs_id)
            except Exception:
                pass
        self._viewer = viewer

    # ── 公开接口 ──────────────────────────────────────────────────────────────

    def set_view_id(self, view_id: str):
        """切换视图类型，更新方位文字"""
        if view_id not in _ORIENTATION_MAP:
            # 方位信息缺失，显示 ?
            for a in self._actors.values():
                a.SetInput("?")
            return
        self._apply_orientation(view_id)

    def set_visible(self, visible: bool):
        self._visible = visible
        v = 1 if visible else 0
        for actor in self._actors.values():
            actor.SetVisibility(v)

    def toggle(self) -> bool:
        self.set_visible(not self._visible)
        return self._visible

    def remove(self):
        if self._viewer is not None and self._obs_id is not None:
            try:
                self._viewer.GetRenderWindow().RemoveObserver(self._obs_id)
            except Exception:
                pass
        for actor in self._actors.values():
            self._renderer.RemoveActor2D(actor)
