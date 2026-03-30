# -*- coding: utf-8 -*-
"""
矩形 ROI 标注交互器
交互：第一次点击起始点，移动预览，第二次点击完成标注。
特性：
  - 只显示在当前切片，切片变化时自动隐藏/显示
  - 统计数据来自当前切片
  - 统计文字显示在矩形右上角旁边（每个矩形独立）
  - 只有鼠标在边框附近才能移动矩形
  - 移动时统计实时更新
  - 删除后可继续绘制
  - 坐标钳制在图像边界内
"""
import numpy as np
import vtk
from src.utils.logger import get_logger

logger = get_logger(__name__)

_COLOR_RECT    = (0.9, 0.2, 0.9)
_COLOR_HANDLE  = (0.2, 1.0, 0.2)
_COLOR_PREVIEW = (0.9, 0.9, 0.2)
_EDGE_HIT_MM   = 4.0   # 边框命中阈值（mm）


def _rect_corners(p1, p2, vt, depth_val=None):
    """根据两个对角点返回矩形四角（左上→右上→右下→左下）
    depth_val: 深度轴的精确世界坐标（来自 actor.GetCenter()），None 时用 p1/p2 平均值
    """
    x1,y1,z1 = p1; x2,y2,z2 = p2
    if vt == "XY":
        z = depth_val if depth_val is not None else (z1+z2)/2.0
        return [(x1,y1,z),(x2,y1,z),(x2,y2,z),(x1,y2,z)]
    elif vt == "YZ":
        x = depth_val if depth_val is not None else (x1+x2)/2.0
        return [(x,y1,z1),(x,y2,z1),(x,y2,z2),(x,y1,z2)]
    else:
        y = depth_val if depth_val is not None else (y1+y2)/2.0
        return [(x1,y,z1),(x2,y,z1),(x2,y,z2),(x1,y,z2)]


def _world_to_pixel(pt, origin, spacing):
    return [int(round((pt[i]-origin[i])/spacing[i])) for i in range(3)]


def _clamp_world(pos, origin, spacing, dims, vt):
    """把世界坐标的平面分量钳制在图像边界内（不改变深度轴）"""
    p = list(pos)
    # 各轴世界坐标范围
    lo = [origin[i] for i in range(3)]
    hi = [origin[i] + (dims[i] - 1) * spacing[i] for i in range(3)]
    if vt == "XY":          # 平面轴: X(0), Y(1)
        p[0] = max(lo[0], min(hi[0], p[0]))
        p[1] = max(lo[1], min(hi[1], p[1]))
    elif vt == "YZ":        # 平面轴: Y(1), Z(2)
        p[1] = max(lo[1], min(hi[1], p[1]))
        p[2] = max(lo[2], min(hi[2], p[2]))
    else:                   # XZ — 平面轴: X(0), Z(2)
        p[0] = max(lo[0], min(hi[0], p[0]))
        p[2] = max(lo[2], min(hi[2], p[2]))
    return p


def _plane_axes(vt):
    """返回视图平面的两个轴索引"""
    if vt == "XY":   return (0, 1)
    elif vt == "YZ": return (1, 2)
    else:            return (0, 2)   # XZ


def _dist_point_to_segment(pt, a, b):
    """点到线段的最短距离（2D，忽略深度轴）"""
    ax,ay = a[0],a[1]; bx,by = b[0],b[1]; px,py = pt[0],pt[1]
    dx,dy = bx-ax, by-ay
    if dx==0 and dy==0:
        return ((px-ax)**2+(py-ay)**2)**0.5
    t = max(0,min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return ((px-(ax+t*dx))**2+(py-(ay+t*dy))**2)**0.5


def _on_edge(world_pt, p1, p2, vt, thr, depth_val=None):
    """判断点是否在矩形边框附近（不是内部）"""
    corners = _rect_corners(p1, p2, vt, depth_val)
    for i in range(4):
        a = corners[i]; b = corners[(i+1)%4]
        if vt == "XY":
            d = _dist_point_to_segment(world_pt[:2], a[:2], b[:2])
        elif vt == "YZ":
            d = _dist_point_to_segment([world_pt[1],world_pt[2]], [a[1],a[2]], [b[1],b[2]])
        else:
            d = _dist_point_to_segment([world_pt[0],world_pt[2]], [a[0],a[2]], [b[0],b[2]])
        if d < thr:
            return True
    return False


def _make_line_rect(color, lw=1.5, stipple=False):
    pts = vtk.vtkPoints(); pts.SetNumberOfPoints(4)
    for i in range(4): pts.SetPoint(i,0,0,0)
    lines = vtk.vtkCellArray()
    for i in range(4):
        ln = vtk.vtkLine()
        ln.GetPointIds().SetId(0,i); ln.GetPointIds().SetId(1,(i+1)%4)
        lines.InsertNextCell(ln)
    poly = vtk.vtkPolyData(); poly.SetPoints(pts); poly.SetLines(lines)
    mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(poly)
    actor = vtk.vtkActor(); actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color); actor.GetProperty().SetLineWidth(lw)
    if stipple:
        actor.GetProperty().SetLineStipplePattern(0xF0F0)
        actor.GetProperty().SetLineStippleRepeatFactor(1)
    return actor, pts, poly


class _PreviewRect:
    def __init__(self, renderer):
        self._renderer = renderer
        self._actor, self._pts, self._poly = _make_line_rect(_COLOR_PREVIEW, lw=1.2, stipple=True)
        renderer.AddActor(self._actor)

    def update(self, p1, p2, vt):
        for i,c in enumerate(_rect_corners(p1,p2,vt)):
            self._pts.SetPoint(i,c)
        self._pts.Modified(); self._poly.Modified()

    def remove(self):
        self._renderer.RemoveActor(self._actor)


class RectAnnotation:
    """
    完整矩形标注。
    记录创建时的切片索引，切片不匹配时隐藏所有 actor。
    统计文字用世界坐标跟随矩形右上角。
    """

    def __init__(self, p1, p2, vt, viewer, slice_idx):
        self.p1          = list(p1)
        self.p2          = list(p2)
        self.vt          = vt
        self._viewer     = viewer
        self._renderer   = viewer.GetRenderer()
        self.slice_idx   = slice_idx

        # 记录 actor 中心的深度轴坐标，用于精确定位线段平面
        try:
            ac = viewer.GetImageActor().GetCenter()
            if vt == "XY":
                self._depth_val = ac[2]
            elif vt == "YZ":
                self._depth_val = ac[0]
            else:
                self._depth_val = ac[1]
        except Exception:
            self._depth_val = None

        try:
            sp = viewer.GetInput().GetSpacing()
            self._hr = max(sp) * 4.0
        except Exception:
            self._hr = 6.0

        self._rect_actor = None
        self._rect_pts   = None
        self._rect_poly  = None
        self._handles    = []
        self._text_actor = None
        self._build()

    # ── 构建 ─────────────────────────────────────────────────────────────────

    def _build(self):
        corners = _rect_corners(self.p1, self.p2, self.vt, self._depth_val)

        self._rect_actor, self._rect_pts, self._rect_poly = _make_line_rect(_COLOR_RECT, lw=1.8)
        for i,c in enumerate(corners): self._rect_pts.SetPoint(i,c)
        self._rect_pts.Modified()
        self._renderer.AddActor(self._rect_actor)

        for c in corners:
            src = vtk.vtkSphereSource()
            src.SetCenter(c); src.SetRadius(self._hr)
            src.SetPhiResolution(12); src.SetThetaResolution(12); src.Update()
            m = vtk.vtkPolyDataMapper(); m.SetInputConnection(src.GetOutputPort())
            a = vtk.vtkActor(); a.SetMapper(m)
            a.GetProperty().SetColor(*_COLOR_HANDLE)
            self._renderer.AddActor(a)
            self._handles.append((a, src))

        # 统计文字：世界坐标，跟随矩形右上角
        self._text_actor = vtk.vtkTextActor()
        tp = self._text_actor.GetTextProperty()
        tp.SetFontSize(11); tp.SetColor(1.0,1.0,0.8)
        tp.SetBackgroundColor(0.05,0.05,0.05); tp.SetBackgroundOpacity(0.72)
        tp.BoldOn()
        # 使用世界坐标，跟随矩形
        self._text_actor.GetPositionCoordinate().SetCoordinateSystemToWorld()
        self._renderer.AddActor(self._text_actor)
        self._update_text_pos()
        self._calc_stats()

    def _update_text_pos(self):
        """把文字定位到矩形右上角外侧（世界坐标，按视图平面轴计算）"""
        corners = _rect_corners(self.p1, self.p2, self.vt, self._depth_val)
        try:
            sp = self._viewer.GetInput().GetSpacing()
        except Exception:
            sp = [1.0, 1.0, 1.0]

        if self.vt == "XY":
            tx = max(c[0] for c in corners) + sp[0] * 3
            ty = max(c[1] for c in corners) + sp[1] * 3
            tz = corners[0][2]
        elif self.vt == "YZ":
            # 平面轴是 Y、Z；X 固定
            tx = corners[0][0]
            ty = max(c[1] for c in corners) + sp[1] * 3
            tz = max(c[2] for c in corners) + sp[2] * 3
        else:  # XZ
            # 平面轴是 X、Z；Y 固定
            tx = max(c[0] for c in corners) + sp[0] * 3
            ty = corners[0][1]
            tz = max(c[2] for c in corners) + sp[2] * 3

        self._text_actor.GetPositionCoordinate().SetValue(tx, ty, tz)

    # ── 统计（使用当前切片索引）─────────────────────────────────────────────

    def _calc_stats(self):
        try:
            img = self._viewer.GetInput()
            if img is None:
                self._text_actor.SetInput("No image"); return
            origin  = img.GetOrigin()
            spacing = img.GetSpacing()
            dims    = img.GetDimensions()
            # 使用当前实际切片（可能已切换）
            current_slice = self._viewer.GetSlice()
            px1 = _world_to_pixel(self.p1, origin, spacing)
            px2 = _world_to_pixel(self.p2, origin, spacing)
            vt  = self.vt

            if vt == "XY":
                xi = sorted([max(0,px1[0]),min(dims[0]-1,px2[0])])
                yi = sorted([max(0,px1[1]),min(dims[1]-1,px2[1])])
                zi = max(0,min(current_slice, dims[2]-1))
                scalars = [img.GetScalarComponentAsFloat(x,y,zi,0)
                           for x in range(xi[0],xi[1]+1) for y in range(yi[0],yi[1]+1)]
                w_mm = abs(self.p2[0]-self.p1[0]); h_mm = abs(self.p2[1]-self.p1[1])
            elif vt == "YZ":
                yi = sorted([max(0,px1[1]),min(dims[1]-1,px2[1])])
                zi = sorted([max(0,px1[2]),min(dims[2]-1,px2[2])])
                xi = max(0,min(current_slice, dims[0]-1))
                scalars = [img.GetScalarComponentAsFloat(xi,y,z,0)
                           for y in range(yi[0],yi[1]+1) for z in range(zi[0],zi[1]+1)]
                w_mm = abs(self.p2[1]-self.p1[1]); h_mm = abs(self.p2[2]-self.p1[2])
            else:
                xi = sorted([max(0,px1[0]),min(dims[0]-1,px2[0])])
                zi = sorted([max(0,px1[2]),min(dims[2]-1,px2[2])])
                yi = max(0,min(current_slice, dims[1]-1))
                scalars = [img.GetScalarComponentAsFloat(x,yi,z,0)
                           for x in range(xi[0],xi[1]+1) for z in range(zi[0],zi[1]+1)]
                w_mm = abs(self.p2[0]-self.p1[0]); h_mm = abs(self.p2[2]-self.p1[2])

            if scalars:
                arr = np.array(scalars, dtype=np.float32)
                area = (w_mm*h_mm)/100.0
                self._text_actor.SetInput(
                    f"Mean:{np.mean(arr):.1f} HU\n"
                    f"Min: {np.min(arr):.1f} HU\n"
                    f"Max: {np.max(arr):.1f} HU\n"
                    f"Std: {np.std(arr):.1f} HU\n"
                    f"W:   {w_mm:.1f}mm H:{h_mm:.1f}mm\n"
                    f"Area:{area:.3f}cm\u00b2"
                )
            else:
                self._text_actor.SetInput("No data")
        except Exception:
            logger.debug("stats error", exc_info=True)
            self._text_actor.SetInput("Error")

    # ── 切片可见性 ────────────────────────────────────────────────────────────

    def update_visibility(self, current_slice):
        """只在创建时的切片上显示"""
        vis = 1 if current_slice == self.slice_idx else 0
        self._rect_actor.SetVisibility(vis)
        for a,_ in self._handles: a.SetVisibility(vis)
        self._text_actor.SetVisibility(vis)
        if vis:
            self._calc_stats()   # 切回来时刷新统计

    # ── 几何更新 ──────────────────────────────────────────────────────────────

    def update_geometry(self):
        corners = _rect_corners(self.p1, self.p2, self.vt, self._depth_val)
        for i,c in enumerate(corners): self._rect_pts.SetPoint(i,c)
        self._rect_pts.Modified(); self._rect_poly.Modified()
        for i,(a,src) in enumerate(self._handles):
            src.SetCenter(corners[i]); src.Update(); a.GetMapper().Update()
        self._update_text_pos()
        self._calc_stats()

    # ── 命中检测 ──────────────────────────────────────────────────────────────

    def handle_hit(self, world_pt):
        t = self._hr * 3.0
        for i,c in enumerate(_rect_corners(self.p1,self.p2,self.vt,self._depth_val)):
            if sum((world_pt[j]-c[j])**2 for j in range(3))**0.5 < t:
                return i
        return -1

    def edge_hit(self, world_pt):
        """只有在边框附近才返回 True（用于移动）"""
        return _on_edge(world_pt, self.p1, self.p2, self.vt, _EDGE_HIT_MM, self._depth_val)

    def remove(self):
        self._renderer.RemoveActor(self._rect_actor)
        for a,_ in self._handles: self._renderer.RemoveActor(a)
        if self._text_actor: self._renderer.RemoveActor(self._text_actor)


class RectROIManager:
    def __init__(self, view_model):
        self.view_model   = view_model
        self._annotations = {"XY": [], "YZ": [], "XZ": []}
        self._observers   = {"XY": None, "YZ": None, "XZ": None}
        self._slice_obs   = {"XY": None, "YZ": None, "XZ": None}
        self._qt_obs      = {"XY": None, "YZ": None, "XZ": None}
        self._handlers    = {"XY": None, "YZ": None, "XZ": None}
        self._active      = False

    def activate(self):
        if self._active:
            return
        self._active = True
        configs = [
            (self.view_model.AxialOrthoViewer,    "XY"),
            (self.view_model.SagittalOrthoViewer, "YZ"),
            (self.view_model.CoronalOrthoViewer,  "XZ"),
        ]
        for ortho, vtype in configs:
            # 若已有 handler（之前 deactivate 过），复用；否则新建
            if self._handlers.get(vtype) is None:
                handler = _ViewRectHandler(ortho, vtype, self._annotations[vtype])
                self._handlers[vtype] = handler
                # 切片监听：永久保持，不随 deactivate 移除
                iren = ortho.widget.GetRenderWindow().GetInteractor()
                slice_ids = [
                    iren.AddObserver("MouseWheelForwardEvent",  handler.on_slice_changed, 0.5),
                    iren.AddObserver("MouseWheelBackwardEvent", handler.on_slice_changed, 0.5),
                ]
                self._slice_obs[vtype] = (iren, slice_ids)
                try:
                    ortho.slider.valueChanged.connect(handler.on_slice_changed_qt)
                    self._qt_obs[vtype] = (ortho.slider, handler.on_slice_changed_qt)
                except Exception:
                    pass
            else:
                handler = self._handlers[vtype]

            iren = ortho.widget.GetRenderWindow().GetInteractor()
            ids = [
                iren.AddObserver("LeftButtonPressEvent",   handler.on_press,   1.0),
                iren.AddObserver("MouseMoveEvent",         handler.on_move,    1.0),
                iren.AddObserver("LeftButtonReleaseEvent", handler.on_release, 1.0),
                iren.AddObserver("KeyPressEvent",          handler.on_key,     1.0),
            ]
            self._observers[vtype] = (iren, ids)

    def deactivate(self):
        """只移除交互事件，保留切片可见性监听"""
        if not self._active:
            return
        self._active = False
        for vtype, val in self._observers.items():
            if val:
                iren, ids = val
                for oid in ids:
                    try: iren.RemoveObserver(oid)
                    except Exception: pass
        self._observers = {"XY": None, "YZ": None, "XZ": None}

    def clear_all(self):
        for annots in self._annotations.values():
            for ann in annots: ann.remove()
            annots.clear()
        self._render_all()

    def _render_all(self):
        for ortho in [self.view_model.AxialOrthoViewer,
                      self.view_model.SagittalOrthoViewer,
                      self.view_model.CoronalOrthoViewer]:
            try: ortho.widget.GetRenderWindow().Render()
            except Exception: pass


class _ViewRectHandler:
    def __init__(self, ortho_viewer, view_type, annotations):
        self.ortho  = ortho_viewer
        self.vtype  = view_type
        self.annots = annotations

        self._picker = vtk.vtkCellPicker()
        self._picker.SetTolerance(0.001)

        self._drawing     = False
        self._start_world = None
        self._preview: _PreviewRect | None = None

        self._editing_ann: RectAnnotation | None = None
        self._edit_handle = -1
        self._moving_ann:  RectAnnotation | None = None
        self._move_last   = None
        self._selected_ann: RectAnnotation | None = None

    # ── 事件 ─────────────────────────────────────────────────────────────────

    def on_press(self, caller, ev):
        world = self._pick(caller)
        if world is None:
            return

        # ── 正在移动中：第二次点击 → 停止移动 ───────────────────────────────
        if self._moving_ann:
            self._moving_ann = None
            self._move_last  = None
            self._render()
            return

        # ── 正在绘制中：第二次点击 → 完成标注 ───────────────────────────────
        if self._drawing and self._start_world:
            if self._preview:
                self._preview.remove(); self._preview = None
            if not self._is_too_small(self._start_world, world):
                ann = RectAnnotation(
                    self._start_world, world, self.vtype,
                    self.ortho.viewer,
                    self.ortho.viewer.GetSlice(),
                )
                self.annots.append(ann)
                self._selected_ann = ann
            self._drawing = False; self._start_world = None
            self._render()
            return

        # ── 命中控制点 → 编辑（拖拽模式，松开结束）─────────────────────────
        for ann in reversed(self._visible_annots()):
            hi = ann.handle_hit(world)
            if hi >= 0:
                self._editing_ann = ann; self._edit_handle = hi
                self._selected_ann = ann
                return

        # ── 命中边框 → 开始移动（点击跟随模式，再次点击停止）───────────────
        for ann in reversed(self._visible_annots()):
            if ann.edge_hit(world):
                self._moving_ann = ann
                self._move_last  = world
                self._selected_ann = ann
                return

        # ── 空白区域：第一次点击 → 开始绘制 ─────────────────────────────────
        self._drawing = True; self._start_world = world
        self._selected_ann = None
        self._preview = _PreviewRect(self.ortho.viewer.GetRenderer())
        self._preview.update(world, world, self.vtype)
        self._render()

    def on_move(self, caller, ev):
        world = self._pick(caller)

        # 编辑控制点：拖拽模式（需要有效坐标）
        if self._editing_ann and self._edit_handle >= 0:
            if world is not None:
                self._do_edit(world)
            return

        # 移动矩形：跟随鼠标（鼠标出图像外时停止更新但不退出移动模式）
        if self._moving_ann:
            if world is not None:
                self._do_move(world)
            return

        # 绘制预览（需要有效坐标）
        if self._drawing and self._start_world and self._preview:
            if world is not None:
                self._preview.update(self._start_world, world, self.vtype)
                self._render()
            return

        caller.GetInteractorStyle().OnMouseMove()

    def on_release(self, caller, ev):
        # 只有编辑控制点是拖拽模式（按住拖，松开结束）
        if self._editing_ann:
            self._editing_ann = None; self._edit_handle = -1
            self._render()
            return
        # 移动和绘制都是点击模式，松开不结束

    def on_key(self, caller, ev):
        key = caller.GetKeySym()
        if key in ("Delete", "BackSpace") and self._selected_ann:
            self._selected_ann.remove()
            if self._selected_ann in self.annots:
                self.annots.remove(self._selected_ann)
            self._selected_ann = None
            self._drawing = False
            if self._preview:
                self._preview.remove(); self._preview = None
            self._start_world = None
            self._render()

    def on_slice_changed(self, caller, ev):
        """VTK 滚轮事件触发的切片变化 — 延迟一帧读取新切片值"""
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._refresh_visibility)

    def on_slice_changed_qt(self, _value=None):
        """Qt 滑块 valueChanged 触发的切片变化"""
        self._refresh_visibility()

    def _refresh_visibility(self):
        """读取当前切片，更新所有标注的可见性并重绘"""
        try:
            cur = self.ortho.viewer.GetSlice()
            for ann in self.annots:
                ann.update_visibility(cur)
            self.ortho.widget.GetRenderWindow().Render()
        except Exception:
            pass

    # ── 内部辅助 ─────────────────────────────────────────────────────────────

    def _visible_annots(self):
        """只返回当前切片上可见的标注"""
        try:
            cur = self.ortho.viewer.GetSlice()
        except Exception:
            return self.annots
        return [a for a in self.annots if a.slice_idx == cur]

    def _pick(self, iren):
        """
        只拾取图像 actor 表面的世界坐标。
        鼠标在图像外时返回 None，禁止在图像外绘制/移动。
        """
        try:
            viewer = self.ortho.viewer
            actor  = viewer.GetImageActor()
            x, y   = iren.GetEventPosition()

            self._picker.InitializePickList()
            self._picker.AddPickList(actor)
            self._picker.PickFromListOn()
            result = self._picker.Pick(x, y, 0, viewer.GetRenderer())

            # result == 0 表示没有命中任何 actor → 鼠标在图像外，直接拒绝
            if result == 0:
                return None

            pos = list(self._picker.GetPickPosition())

            img = viewer.GetInput()
            if img is None:
                return None
            origin  = img.GetOrigin()
            spacing = img.GetSpacing()
            dims    = img.GetDimensions()

            # 深度轴固定到 actor 的实际平面位置
            # 用 actor 的中心点来获取深度轴的精确世界坐标，避免变换误差
            actor_center = actor.GetCenter()
            if self.vtype == "XY":
                pos[2] = actor_center[2]
            elif self.vtype == "YZ":
                pos[0] = actor_center[0]
            else:  # XZ
                pos[1] = actor_center[1]

            # 平面轴钳制在图像边界内（防止浮点误差越界）
            pos = _clamp_world(pos, origin, spacing, dims, self.vtype)
            return pos
        except Exception:
            logger.debug("pick error", exc_info=True)
            return None

    def _do_edit(self, world):
        ann = self._editing_ann; hi = self._edit_handle; vt = self.vtype
        if vt == "XY":
            pts = [(ann.p1[0],ann.p1[1]),(ann.p2[0],ann.p1[1]),
                   (ann.p2[0],ann.p2[1]),(ann.p1[0],ann.p2[1])]
            pts[hi] = (world[0],world[1])
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            ann.p1[0],ann.p2[0]=min(xs),max(xs); ann.p1[1],ann.p2[1]=min(ys),max(ys)
        elif vt == "YZ":
            pts = [(ann.p1[1],ann.p1[2]),(ann.p2[1],ann.p1[2]),
                   (ann.p2[1],ann.p2[2]),(ann.p1[1],ann.p2[2])]
            pts[hi] = (world[1],world[2])
            ys=[p[0] for p in pts]; zs=[p[1] for p in pts]
            ann.p1[1],ann.p2[1]=min(ys),max(ys); ann.p1[2],ann.p2[2]=min(zs),max(zs)
        else:
            pts = [(ann.p1[0],ann.p1[2]),(ann.p2[0],ann.p1[2]),
                   (ann.p2[0],ann.p2[2]),(ann.p1[0],ann.p2[2])]
            pts[hi] = (world[0],world[2])
            xs=[p[0] for p in pts]; zs=[p[1] for p in pts]
            ann.p1[0],ann.p2[0]=min(xs),max(xs); ann.p1[2],ann.p2[2]=min(zs),max(zs)
        ann.update_geometry(); self._render()

    def _do_move(self, world):
        if self._move_last is None:
            return
        delta = [world[i] - self._move_last[i] for i in range(3)]
        ann = self._moving_ann
        vt  = self.vtype

        new_p1 = [ann.p1[i] + delta[i] for i in range(3)]
        new_p2 = [ann.p2[i] + delta[i] for i in range(3)]

        # 整体平移边界约束：保持矩形尺寸，只在平面轴上限制
        try:
            img     = self.ortho.viewer.GetInput()
            origin  = img.GetOrigin()
            spacing = img.GetSpacing()
            dims    = img.GetDimensions()

            for ax in _plane_axes(vt):
                lo = origin[ax]
                hi = origin[ax] + (dims[ax] - 1) * spacing[ax]
                mn = min(new_p1[ax], new_p2[ax])
                mx = max(new_p1[ax], new_p2[ax])
                if mn < lo:
                    shift = lo - mn
                    new_p1[ax] += shift
                    new_p2[ax] += shift
                elif mx > hi:
                    shift = mx - hi
                    new_p1[ax] -= shift
                    new_p2[ax] -= shift
        except Exception:
            pass

        ann.p1 = new_p1
        ann.p2 = new_p2
        ann.update_geometry()
        self._move_last = world   # 始终跟鼠标，不跟矩形
        self._render()

    def _is_too_small(self, p1, p2, min_mm=2.0):
        vt = self.vtype
        if vt == "XY":   return abs(p2[0]-p1[0])<min_mm or abs(p2[1]-p1[1])<min_mm
        elif vt == "YZ": return abs(p2[1]-p1[1])<min_mm or abs(p2[2]-p1[2])<min_mm
        else:            return abs(p2[0]-p1[0])<min_mm or abs(p2[2]-p1[2])<min_mm

    def _render(self):
        try:
            cur = self.ortho.viewer.GetSlice()
            for ann in self.annots:
                ann.update_visibility(cur)
        except Exception:
            pass
        try:
            self.ortho.widget.GetRenderWindow().Render()
        except Exception:
            pass
