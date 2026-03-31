# -*- coding: utf-8 -*-
"""
伪彩条 (Pseudo-color LUT Bar)
- 叠加在 VTK renderer 右侧，显示当前窗宽/窗位下的颜色映射
- 支持 Jet / Hot / Bone / Rainbow / Gray 五种调色板
- 顶部显示 Max，底部显示 Min
- 可独立显示/隐藏
"""
import vtk
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── 调色板定义 ────────────────────────────────────────────────────────────────

def _build_lut(palette: str, val_min: float, val_max: float) -> vtk.vtkLookupTable:
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfColors(256)
    lut.SetTableRange(val_min, val_max)

    if palette == "Gray":
        for i in range(256):
            v = i / 255.0
            lut.SetTableValue(i, v, v, v, 1.0)

    elif palette == "Jet":
        import math
        for i in range(256):
            t = i / 255.0
            r = min(1.0, max(0.0, 1.5 - abs(4*t - 3)))
            g = min(1.0, max(0.0, 1.5 - abs(4*t - 2)))
            b = min(1.0, max(0.0, 1.5 - abs(4*t - 1)))
            lut.SetTableValue(i, r, g, b, 1.0)

    elif palette == "Hot":
        for i in range(256):
            t = i / 255.0
            r = min(1.0, t * 3.0)
            g = min(1.0, max(0.0, t * 3.0 - 1.0))
            b = min(1.0, max(0.0, t * 3.0 - 2.0))
            lut.SetTableValue(i, r, g, b, 1.0)

    elif palette == "Bone":
        for i in range(256):
            t = i / 255.0
            r = min(1.0, t * 7/8 + (1/8 if t > 3/4 else 0))
            g = min(1.0, t * 7/8 + (1/8 if t > 1/2 else 0))
            b = min(1.0, t * 7/8 + 1/8)
            lut.SetTableValue(i, r, g, b, 1.0)

    elif palette == "Rainbow":
        for i in range(256):
            t = i / 255.0
            # HSV: hue 从 0.67(蓝) 到 0(红)
            h = (1.0 - t) * 0.67
            s, v = 1.0, 1.0
            hi = int(h * 6) % 6
            f = h * 6 - int(h * 6)
            p, q, tv = v*(1-s), v*(1-f*s), v*(1-(1-f)*s)
            rgb = [(v,tv,p),(q,v,p),(p,v,tv),(p,q,v),(tv,p,v),(v,p,q)][hi]
            lut.SetTableValue(i, rgb[0], rgb[1], rgb[2], 1.0)

    else:
        for i in range(256):
            v = i / 255.0
            lut.SetTableValue(i, v, v, v, 1.0)

    lut.Build()
    return lut


PALETTES = ["Gray", "Jet", "Hot", "Bone", "Rainbow"]


class PseudoColorBar:
    """
    伪彩条，叠加在指定 renderer 的右侧。
    通过 update_window_level(window, level) 更新 Min/Max 显示。
    通过 set_palette(name) 切换调色板。
    通过 set_visible(bool) 显示/隐藏。
    """

    def __init__(self, renderer: vtk.vtkRenderer, window: float = 400, level: float = 40):
        self._renderer  = renderer
        self._window    = window
        self._level     = level
        self._palette   = "Gray"
        self._visible   = False
        self._actor: vtk.vtkScalarBarActor | None = None
        self._lut: vtk.vtkLookupTable | None = None
        self._build()

    # ── 构建 ─────────────────────────────────────────────────────────────────

    def _build(self):
        self._lut = _build_lut(self._palette, self._val_min(), self._val_max())

        cb = vtk.vtkScalarBarActor()
        cb.SetLookupTable(self._lut)
        cb.SetNumberOfLabels(5)
        cb.SetWidth(0.10)
        cb.SetHeight(0.65)
        cb.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        cb.SetPosition(0.02, 0.17)
        cb.SetOrientationToVertical()
        cb.SetTitle("")
        cb.SetLabelFormat("%.0f")          # 整数格式，避免科学计数法
        cb.UnconstrainedFontSizeOn()       # 不受彩条尺寸约束，字体才能真正变大

        ltp = cb.GetLabelTextProperty()
        ltp.SetFontSize(12)
        ltp.SetColor(1, 1, 1)
        ltp.ShadowOn()
        ltp.BoldOn()
        ltp.ItalicOff()
        ltp.SetFontFamilyToArial()

        ttp = cb.GetTitleTextProperty()
        ttp.SetFontSize(1); ttp.SetColor(0, 0, 0)

        cb.DrawFrameOff()
        cb.DrawBackgroundOff()
        cb.SetVisibility(0)

        self._actor = cb
        self._renderer.AddActor(cb)

    # ── 公开接口 ──────────────────────────────────────────────────────────────

    def update_window_level(self, window: float, level: float):
        """窗宽/窗位变化时调用，更新 LUT 范围"""
        self._window = window
        self._level  = level
        if self._visible:
            self._refresh_lut()

    def set_palette(self, palette: str):
        """切换调色板"""
        if palette not in PALETTES:
            return
        self._palette = palette
        self._refresh_lut()

    def set_visible(self, visible: bool):
        self._visible = visible
        self._actor.SetVisibility(1 if visible else 0)
        if visible:
            self._refresh_lut()

    def toggle(self) -> bool:
        self.set_visible(not self._visible)
        return self._visible

    def remove(self):
        if self._actor:
            self._renderer.RemoveActor(self._actor)

    # ── 内部 ─────────────────────────────────────────────────────────────────

    def _val_min(self) -> float:
        return self._level - self._window / 2.0

    def _val_max(self) -> float:
        return self._level + self._window / 2.0

    def _refresh_lut(self):
        new_lut = _build_lut(self._palette, self._val_min(), self._val_max())
        # 复制颜色到现有 lut（避免重建 actor）
        self._lut.SetTableRange(self._val_min(), self._val_max())
        for i in range(256):
            self._lut.SetTableValue(i, *new_lut.GetTableValue(i))
        self._lut.Modified()
        self._actor.Modified()
