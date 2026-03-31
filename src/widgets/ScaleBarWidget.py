# -*- coding: utf-8 -*-
"""
标尺 (Scale Bar)
- 固定在视图底部（display 坐标），不随图像平移
- 总长度对应图像物理宽度，随缩放同步变化
- 每 1 cm 一个短刻度，单位显示 cm
"""
import vtk

_COLOR     = (0.2, 1.0, 0.2)   # 绿色
_Y_OFFSET  = 20                 # 距视口底边像素数
_TICK_MAIN = 10                 # 两端主刻度高度 px
_TICK_SUB  = 5                  # 每 1cm 小刻度高度 px


class ScaleBar:

    def __init__(self, renderer: vtk.vtkRenderer):
        self._renderer     = renderer
        self._viewer       = None
        self._obs_id       = None
        self._visible      = False
        self._img_width_mm = 0.0   # 图像物理宽度 mm（随 set_image_info 更新）

        # ── 所有线段用一个 vtkPolyData，动态更新点数 ─────────────────────────
        self._pts   = vtk.vtkPoints()
        self._cells = vtk.vtkCellArray()
        self._poly  = vtk.vtkPolyData()
        self._poly.SetPoints(self._pts)
        self._poly.SetLines(self._cells)

        mapper = vtk.vtkPolyDataMapper2D()
        mapper.SetInputData(self._poly)

        self._line_actor = vtk.vtkActor2D()
        self._line_actor.SetMapper(mapper)
        self._line_actor.GetProperty().SetColor(*_COLOR)
        self._line_actor.GetProperty().SetLineWidth(1.5)
        self._line_actor.GetPositionCoordinate().SetCoordinateSystemToDisplay()
        renderer.AddActor2D(self._line_actor)

        # ── 文字（右端标注总长度）────────────────────────────────────────────
        self._text_actor = vtk.vtkTextActor()
        tp = self._text_actor.GetTextProperty()
        tp.SetFontSize(12)
        tp.SetColor(*_COLOR)
        tp.BoldOn()
        tp.ShadowOn()
        tp.SetJustificationToLeft()
        tp.SetVerticalJustificationToCentered()
        self._text_actor.GetPositionCoordinate().SetCoordinateSystemToDisplay()
        renderer.AddActor2D(self._text_actor)

        self._line_actor.SetVisibility(0)
        self._text_actor.SetVisibility(0)

    # ── 图像信息 ──────────────────────────────────────────────────────────────

    def set_image_info(self, bounds, view_id: str):
        """
        bounds: (xmin,xmax, ymin,ymax, zmin,zmax)
        view_id: 'XY' / 'YZ' / 'XZ'
        """
        if view_id == "YZ":
            # 矢状面：水平方向是 Y 轴
            self._img_width_mm = abs(bounds[3] - bounds[2])
        elif view_id == "XZ":
            # 冠状面：水平方向是 X 轴
            self._img_width_mm = abs(bounds[1] - bounds[0])
        else:
            # 横断面 XY：水平方向是 X 轴
            self._img_width_mm = abs(bounds[1] - bounds[0])

    # ── 绑定 viewer ───────────────────────────────────────────────────────────

    def attach(self, viewer):
        if self._viewer is not None and self._obs_id is not None:
            try:
                self._viewer.GetRenderWindow().RemoveObserver(self._obs_id)
            except Exception:
                pass
        self._viewer = viewer
        try:
            self._obs_id = viewer.GetRenderWindow().AddObserver(
                "RenderEvent", self._on_render
            )
        except Exception:
            pass

    # ── 公开接口 ──────────────────────────────────────────────────────────────

    def set_visible(self, visible: bool):
        self._visible = visible
        v = 1 if visible else 0
        self._line_actor.SetVisibility(v)
        self._text_actor.SetVisibility(v)
        if visible:
            self._update()

    def toggle(self) -> bool:
        self.set_visible(not self._visible)
        return self._visible

    def remove(self):
        if self._viewer is not None and self._obs_id is not None:
            try:
                self._viewer.GetRenderWindow().RemoveObserver(self._obs_id)
            except Exception:
                pass
        self._renderer.RemoveActor2D(self._line_actor)
        self._renderer.RemoveActor2D(self._text_actor)

    # ── 内部 ─────────────────────────────────────────────────────────────────

    def _on_render(self, caller, ev):
        if self._visible:
            self._update()

    def _update(self):
        if not self._visible or self._viewer is None:
            return
        if self._img_width_mm <= 0:
            return
        try:
            renderer = self._renderer
            camera   = renderer.GetActiveCamera()

            rw = renderer.GetRenderWindow()
            win_w, win_h = rw.GetSize()
            if win_w == 0 or win_h == 0:
                return

            vp    = renderer.GetViewport()
            vp_x0 = int(vp[0] * win_w)
            vp_y0 = int(vp[1] * win_h)
            vp_x1 = int(vp[2] * win_w)
            vp_y1 = int(vp[3] * win_h)
            vp_w  = vp_x1 - vp_x0
            vp_h  = vp_y1 - vp_y0

            if not camera.GetParallelProjection():
                return

            # mm/pixel
            scale        = camera.GetParallelScale()
            mm_per_pixel = (2.0 * scale) / vp_h if vp_h > 0 else 1.0

            # 图像物理宽度对应的屏幕像素数（随缩放变化）
            bar_px = int(self._img_width_mm / mm_per_pixel)
            # 限制不超过视口宽度
            bar_px = min(bar_px, vp_w)

            # 比例尺起点：视口底部居中
            cx = vp_x0 + vp_w // 2
            x0 = cx - bar_px // 2
            x1 = x0 + bar_px
            y  = vp_y0 + _Y_OFFSET   # 距底边固定像素

            # ── 重建所有线段 ──────────────────────────────────────────────────
            pts   = []
            lines = []

            def add_line(ax, ay, bx, by):
                i = len(pts)
                pts.append((ax, ay, 0))
                pts.append((bx, by, 0))
                lines.append((i, i + 1))

            # 主横线
            add_line(x0, y, x1, y)
            # 左端主刻度（向上）
            add_line(x0, y, x0, y + _TICK_MAIN)
            # 右端主刻度（向上）
            add_line(x1, y, x1, y + _TICK_MAIN)

            # 每 1 cm 小刻度
            cm_per_pixel = mm_per_pixel / 10.0          # 1 cm 对应多少 pixel
            px_per_cm    = 1.0 / cm_per_pixel if cm_per_pixel > 0 else 0
            total_cm     = int(self._img_width_mm / 10)  # 总 cm 数

            for i in range(1, total_cm):
                tx = x0 + int(i * px_per_cm)
                if x0 < tx < x1:
                    add_line(tx, y, tx, y + _TICK_SUB)

            # 写入 vtkPoints / vtkCellArray
            new_pts = vtk.vtkPoints()
            new_pts.SetNumberOfPoints(len(pts))
            for idx, (px, py, pz) in enumerate(pts):
                new_pts.SetPoint(idx, px, py, pz)

            new_cells = vtk.vtkCellArray()
            for a, b in lines:
                ln = vtk.vtkLine()
                ln.GetPointIds().SetId(0, a)
                ln.GetPointIds().SetId(1, b)
                new_cells.InsertNextCell(ln)

            self._poly.SetPoints(new_pts)
            self._poly.SetLines(new_cells)
            self._poly.Modified()

            # 文字：右端右侧，显示总长度（cm）
            total_cm_val = self._img_width_mm / 10.0
            if total_cm_val == int(total_cm_val):
                label = f"{int(total_cm_val)} cm"
            else:
                label = f"{total_cm_val:.1f} cm"
            self._text_actor.SetInput(label)
            self._text_actor.SetPosition(x1 + 6, y + _TICK_MAIN // 2)

        except Exception:
            pass
