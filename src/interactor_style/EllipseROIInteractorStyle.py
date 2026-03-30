# -*- coding: utf-8 -*-
"""
椭圆 ROI 标注交互器
交互：第一次点击起始点，移动预览，第二次点击完成标注。
特性：
  - 只显示在当前切片，切片变化时自动隐藏/显示
  - 统计数据来自当前切片
  - 统计文字显示在椭圆右侧（每个椭圆独立）
  - 只有鼠标在边框附近才能移动椭圆
  - 移动时统计实时更新
  - 删除后可继续绘制
  - 坐标钳制在图像边界内
"""
import numpy as np
import vtk
from src.utils.logger import get_logger

logger = get_logger(__name__)

_COLOR_ELLIPSE = (0.9, 0.2, 0.9)
_COLOR_HANDLE  = (0.2, 1.0, 0.2)
_COLOR_PREVIEW = (0.9, 0.9, 0.2)
_EDGE_HIT_MM   = 4.0   # 边框命中阈值（mm）


def _ellipse_params(p1, p2, vt, depth_val=None):
    """
    根据两点返回椭圆参数 (cx, cy, cz, a, b, angle_deg)
    - a: 长半轴 = 两点距离 / 2
    - b: 短半轴 = a * 0.5
    - angle_deg: 长轴方向角（用于旋转变换）
    - depth_val: 深度轴精确坐标
    """
    import math
    x1,y1,z1 = p1; x2,y2,z2 = p2
    if vt == "XY":
        z  = depth_val if depth_val is not None else (z1+z2)/2.0
        cx = (x1+x2)/2; cy = (y1+y2)/2
        dx = x2-x1;     dy = y2-y1
        a  = math.sqrt(dx*dx + dy*dy) / 2.0
        b  = a * 0.5
        angle = math.degrees(math.atan2(dy, dx))
        return (cx, cy, z, a, b, angle)
    elif vt == "YZ":
        x  = depth_val if depth_val is not None else (x1+x2)/2.0
        cy = (y1+y2)/2; cz = (z1+z2)/2
        dy = y2-y1;     dz = z2-z1
        a  = math.sqrt(dy*dy + dz*dz) / 2.0
        b  = a * 0.5
        angle = math.degrees(math.atan2(dz, dy))
        return (x, cy, cz, a, b, angle)
    else:  # XZ
        y  = depth_val if depth_val is not None else (y1+y2)/2.0
        cx = (x1+x2)/2; cz = (z1+z2)/2
        dx = x2-x1;     dz = z2-z1
        a  = math.sqrt(dx*dx + dz*dz) / 2.0
        b  = a * 0.5
        angle = math.degrees(math.atan2(dz, dx))
        return (cx, y, cz, a, b, angle)


def _world_to_pixel(pt, origin, spacing):
    return [int(round((pt[i]-origin[i])/spacing[i])) for i in range(3)]


def _clamp_world(pos, origin, spacing, dims, vt):
    """把世界坐标的平面分量钳制在图像边界内（不改变深度轴）"""
    p = list(pos)
    lo = [origin[i] for i in range(3)]
    hi = [origin[i] + (dims[i] - 1) * spacing[i] for i in range(3)]
    if vt == "XY":
        p[0] = max(lo[0], min(hi[0], p[0]))
        p[1] = max(lo[1], min(hi[1], p[1]))
    elif vt == "YZ":
        p[1] = max(lo[1], min(hi[1], p[1]))
        p[2] = max(lo[2], min(hi[2], p[2]))
    else:
        p[0] = max(lo[0], min(hi[0], p[0]))
        p[2] = max(lo[2], min(hi[2], p[2]))
    return p


def _plane_axes(vt):
    """返回视图平面的两个轴索引"""
    if vt == "XY":   return (0, 1)
    elif vt == "YZ": return (1, 2)
    else:            return (0, 2)


def _on_ellipse_edge(world_pt, cx, cy, cz, a, b, angle_deg, vt, thr):
    """判断点是否在椭圆边框附近（在旋转坐标系中判断）"""
    import math
    if a <= 0 or b <= 0:
        return False
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(-angle_rad)
    sin_a = math.sin(-angle_rad)

    if vt == "XY":
        dx = world_pt[0] - cx; dy = world_pt[1] - cy
        lx = cos_a * dx - sin_a * dy
        ly = sin_a * dx + cos_a * dy
        val = (lx/a)**2 + (ly/b)**2
    elif vt == "YZ":
        dy = world_pt[1] - cy; dz = world_pt[2] - cz
        lx = cos_a * dy - sin_a * dz
        ly = sin_a * dy + cos_a * dz
        val = (lx/a)**2 + (ly/b)**2
    else:  # XZ
        dx = world_pt[0] - cx; dz = world_pt[2] - cz
        lx = cos_a * dx - sin_a * dz
        ly = sin_a * dx + cos_a * dz
        val = (lx/a)**2 + (ly/b)**2

    return abs(val - 1.0) * b < thr


def _make_ellipse_polydata(cx, cy, cz, rx, ry, rz, vt, n=100):
    """
    用 vtkTransformPolyDataFilter 方式绘制椭圆。
    在局部坐标系画圆，再通过变换映射到世界坐标。
    短半轴 = 长半轴 * 0.5（参考代码风格）。
    """
    import math

    points = vtk.vtkPoints()
    lines  = vtk.vtkCellArray()
    lines.InsertNextCell(n + 1)

    for i in range(n + 1):
        theta = 2.0 * math.pi * i / n
        if vt == "XY":
            lx = rx * math.cos(theta)
            ly = ry * math.sin(theta)
            points.InsertNextPoint(lx, ly, 0)
        elif vt == "YZ":
            ly = ry * math.cos(theta)
            lz = rz * math.sin(theta)
            points.InsertNextPoint(0, ly, lz)
        else:  # XZ
            lx = rx * math.cos(theta)
            lz = rz * math.sin(theta)
            points.InsertNextPoint(lx, 0, lz)
        lines.InsertCellPoint(i)

    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetLines(lines)

    # 平移到世界坐标中心
    transform = vtk.vtkTransform()
    transform.PostMultiply()
    transform.Translate(cx, cy, cz)

    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(poly)
    tf.SetTransform(transform)
    tf.Update()

    return tf.GetOutput()   # vtkPolyData（已变换）


def _make_ellipse_actor(cx, cy, cz, a, b, angle_deg, vt, color, lw=1.5, stipple=False, n=100):
    """
    直接在世界坐标里计算椭圆点，不依赖旋转变换。
    返回 (actor, vtkPoints_world, vtkPolyData, None)  — 第4个为None占位
    """
    import math
    ar = math.radians(angle_deg)
    cos_a, sin_a = math.cos(ar), math.sin(ar)

    pts = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    lines.InsertNextCell(n + 1)

    for i in range(n + 1):
        theta = 2.0 * math.pi * i / n
        lx = a * math.cos(theta)   # 局部长轴方向
        ly = b * math.sin(theta)   # 局部短轴方向

        if vt == "XY":
            wx = cx + lx * cos_a - ly * sin_a
            wy = cy + lx * sin_a + ly * cos_a
            pts.InsertNextPoint(wx, wy, cz)
        elif vt == "YZ":
            wy = cy + lx * cos_a - ly * sin_a
            wz = cz + lx * sin_a + ly * cos_a
            pts.InsertNextPoint(cx, wy, wz)
        else:  # XZ
            wx = cx + lx * cos_a - ly * sin_a
            wz = cz + lx * sin_a + ly * cos_a
            pts.InsertNextPoint(wx, cy, wz)
        lines.InsertCellPoint(i)

    poly = vtk.vtkPolyData()
    poly.SetPoints(pts)
    poly.SetLines(lines)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetLineWidth(lw)
    if stipple:
        actor.GetProperty().SetLineStipplePattern(0xF0F0)
        actor.GetProperty().SetLineStippleRepeatFactor(1)

    return actor, pts, poly, None   # None 占位，保持返回值结构一致


class _PreviewEllipse:
    def __init__(self, renderer):
        self._renderer = renderer
        self._actor = None
        self._pts   = None
        self._poly  = None
        self._tf    = None

    def update(self, p1, p2, vt, depth_val=None):
        import math
        cx, cy, cz, a, b, angle_deg = _ellipse_params(p1, p2, vt, depth_val)
        a = a if a > 0 else 1e-4
        b = b if b > 0 else 1e-4
        ar = math.radians(angle_deg)
        cos_a, sin_a = math.cos(ar), math.sin(ar)
        n = 100

        if self._actor is None:
            self._actor, self._pts, self._poly, _ = _make_ellipse_actor(
                cx, cy, cz, a, b, angle_deg, vt, _COLOR_PREVIEW, lw=1.2, stipple=True, n=n
            )
            self._renderer.AddActor(self._actor)
        else:
            for i in range(self._pts.GetNumberOfPoints()):
                theta = 2.0 * math.pi * i / n
                lx = a * math.cos(theta)
                ly = b * math.sin(theta)
                if vt == "XY":
                    self._pts.SetPoint(i, cx + lx*cos_a - ly*sin_a,
                                          cy + lx*sin_a + ly*cos_a, cz)
                elif vt == "YZ":
                    self._pts.SetPoint(i, cx,
                                          cy + lx*cos_a - ly*sin_a,
                                          cz + lx*sin_a + ly*cos_a)
                else:
                    self._pts.SetPoint(i, cx + lx*cos_a - ly*sin_a,
                                          cy,
                                          cz + lx*sin_a + ly*cos_a)
            self._pts.Modified()
            self._poly.Modified()

    def remove(self):
        if self._actor:
            self._renderer.RemoveActor(self._actor)
            self._actor = None


class EllipseAnnotation:
    """
    完整椭圆标注。
    记录创建时的切片索引，切片不匹配时隐藏所有 actor。
    统计文字用世界坐标跟随椭圆右侧。
    """

    def __init__(self, p1, p2, vt, viewer, slice_idx):
        self.p1          = list(p1)
        self.p2          = list(p2)
        self.vt          = vt
        self._viewer     = viewer
        self._renderer   = viewer.GetRenderer()
        self.slice_idx   = slice_idx

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

        self._ellipse_actor = None
        self._ellipse_src   = None
        self._handles       = []   # (actor, sphere_src) × 4
        self._text_actor    = None
        self._custom_b      = None  # 用户拖拽短轴后的自定义短半轴
        self._build()

    # ── 构建 ─────────────────────────────────────────────────────────────────

    def _build(self):
        cx, cy, cz, a, b, angle_deg = _ellipse_params(self.p1, self.p2, self.vt, self._depth_val)
        self._ellipse_actor, self._ellipse_pts, self._ellipse_poly, self._ellipse_tf = \
            _make_ellipse_actor(
                cx, cy, cz, a if a > 0 else 1e-4, b if b > 0 else 1e-4,
                angle_deg, self.vt, _COLOR_ELLIPSE, lw=1.8, n=100
            )
        self._renderer.AddActor(self._ellipse_actor)

        # 4 个控制点：上/下/左/右
        for _ in range(4):
            src = vtk.vtkSphereSource()
            src.SetRadius(self._hr)
            src.SetPhiResolution(12); src.SetThetaResolution(12)
            src.Update()
            m = vtk.vtkPolyDataMapper(); m.SetInputConnection(src.GetOutputPort())
            a = vtk.vtkActor(); a.SetMapper(m)
            a.GetProperty().SetColor(*_COLOR_HANDLE)
            self._renderer.AddActor(a)
            self._handles.append((a, src))
        self._update_handles()

        self._text_actor = vtk.vtkTextActor()
        tp = self._text_actor.GetTextProperty()
        tp.SetFontSize(11); tp.SetColor(1.0, 1.0, 0.8)
        tp.SetBackgroundColor(0.05, 0.05, 0.05); tp.SetBackgroundOpacity(0.72)
        tp.BoldOn()
        self._text_actor.GetPositionCoordinate().SetCoordinateSystemToWorld()
        self._renderer.AddActor(self._text_actor)
        self._update_text_pos()
        self._calc_stats()

    def _apply_ellipse_transform(self):
        import math
        cx, cy, cz, a, b, angle_deg = _ellipse_params(self.p1, self.p2, self.vt, self._depth_val)
        if self._custom_b is not None:
            b = self._custom_b
        a = a if a > 0 else 1e-4
        b = b if b > 0 else 1e-4
        ar = math.radians(angle_deg)
        cos_a, sin_a = math.cos(ar), math.sin(ar)
        n = self._ellipse_pts.GetNumberOfPoints()
        for i in range(n):
            theta = 2.0 * math.pi * i / n
            lx = a * math.cos(theta)
            ly = b * math.sin(theta)
            if self.vt == "XY":
                self._ellipse_pts.SetPoint(i, cx + lx*cos_a - ly*sin_a,
                                              cy + lx*sin_a + ly*cos_a, cz)
            elif self.vt == "YZ":
                self._ellipse_pts.SetPoint(i, cx,
                                              cy + lx*cos_a - ly*sin_a,
                                              cz + lx*sin_a + ly*cos_a)
            else:
                self._ellipse_pts.SetPoint(i, cx + lx*cos_a - ly*sin_a,
                                              cy,
                                              cz + lx*sin_a + ly*cos_a)
        self._ellipse_pts.Modified()
        self._ellipse_poly.Modified()

    def _handle_positions(self):
        """返回 4 个控制点的世界坐标（长轴两端 + 短轴两端，已旋转）"""
        import math
        cx, cy, cz, a, b, angle_deg = _ellipse_params(self.p1, self.p2, self.vt, self._depth_val)
        ar = math.radians(angle_deg)
        cos_a, sin_a = math.cos(ar), math.sin(ar)
        if self.vt == "XY":
            return [
                (cx + a*cos_a,        cy + a*sin_a,        cz),  # 长轴正端
                (cx - a*cos_a,        cy - a*sin_a,        cz),  # 长轴负端
                (cx - b*sin_a,        cy + b*cos_a,        cz),  # 短轴正端
                (cx + b*sin_a,        cy - b*cos_a,        cz),  # 短轴负端
            ]
        elif self.vt == "YZ":
            return [
                (cx, cy + a*cos_a,    cz + a*sin_a),
                (cx, cy - a*cos_a,    cz - a*sin_a),
                (cx, cy - b*sin_a,    cz + b*cos_a),
                (cx, cy + b*sin_a,    cz - b*cos_a),
            ]
        else:  # XZ
            return [
                (cx + a*cos_a,        cy, cz + a*sin_a),
                (cx - a*cos_a,        cy, cz - a*sin_a),
                (cx - b*sin_a,        cy, cz + b*cos_a),
                (cx + b*sin_a,        cy, cz - b*cos_a),
            ]

    def _update_handles(self):
        for i, (a, src) in enumerate(self._handles):
            pos = self._handle_positions()[i]
            src.SetCenter(*pos); src.Update(); a.GetMapper().Update()

    def _update_text_pos(self):
        import math
        cx, cy, cz, a, b, angle_deg = _ellipse_params(self.p1, self.p2, self.vt, self._depth_val)
        try:
            sp = self._viewer.GetInput().GetSpacing()
        except Exception:
            sp = [1.0, 1.0, 1.0]
        ar = math.radians(angle_deg)
        if self.vt == "XY":
            # 长轴正端右侧
            ex = cx + a * math.cos(ar) + sp[0]*3
            ey = cy + a * math.sin(ar)
            self._text_actor.GetPositionCoordinate().SetValue(ex, ey, cz)
        elif self.vt == "YZ":
            ey = cy + a * math.cos(ar)
            ez = cz + a * math.sin(ar) + sp[2]*3
            self._text_actor.GetPositionCoordinate().SetValue(cx, ey, ez)
        else:
            ex = cx + a * math.cos(ar) + sp[0]*3
            ez = cz + a * math.sin(ar)
            self._text_actor.GetPositionCoordinate().SetValue(ex, cy, ez)

    # ── 统计 ─────────────────────────────────────────────────────────────────

    def _calc_stats(self):
        try:
            import math
            img = self._viewer.GetInput()
            if img is None:
                self._text_actor.SetInput("No image"); return
            origin  = img.GetOrigin()
            spacing = img.GetSpacing()
            dims    = img.GetDimensions()
            current_slice = self._viewer.GetSlice()

            cx, cy, cz, a, b, angle_deg = _ellipse_params(self.p1, self.p2, self.vt, self._depth_val)
            ar = math.radians(angle_deg)
            cos_a, sin_a = math.cos(-ar), math.sin(-ar)

            # 包围盒（用于遍历范围）
            px1 = _world_to_pixel(self.p1, origin, spacing)
            px2 = _world_to_pixel(self.p2, origin, spacing)
            vt  = self.vt

            def in_ellipse_2d(u, v):
                """在旋转坐标系中判断点是否在椭圆内"""
                lu = cos_a * u - sin_a * v
                lv = sin_a * u + cos_a * v
                return (lu/a)**2 + (lv/b)**2 <= 1.0 if a > 0 and b > 0 else False

            scalars = []
            if vt == "XY":
                xi = sorted([max(0,px1[0]),min(dims[0]-1,px2[0])])
                yi = sorted([max(0,px1[1]),min(dims[1]-1,px2[1])])
                zi = max(0, min(current_slice, dims[2]-1))
                for x in range(xi[0], xi[1]+1):
                    for y in range(yi[0], yi[1]+1):
                        wx = origin[0] + x*spacing[0] - cx
                        wy = origin[1] + y*spacing[1] - cy
                        if in_ellipse_2d(wx, wy):
                            scalars.append(img.GetScalarComponentAsFloat(x, y, zi, 0))
                w_mm = 2*a; h_mm = 2*b
            elif vt == "YZ":
                yi = sorted([max(0,px1[1]),min(dims[1]-1,px2[1])])
                zi = sorted([max(0,px1[2]),min(dims[2]-1,px2[2])])
                xi = max(0, min(current_slice, dims[0]-1))
                for y in range(yi[0], yi[1]+1):
                    for z in range(zi[0], zi[1]+1):
                        wy = origin[1] + y*spacing[1] - cy
                        wz = origin[2] + z*spacing[2] - cz
                        if in_ellipse_2d(wy, wz):
                            scalars.append(img.GetScalarComponentAsFloat(xi, y, z, 0))
                w_mm = 2*a; h_mm = 2*b
            else:
                xi = sorted([max(0,px1[0]),min(dims[0]-1,px2[0])])
                zi = sorted([max(0,px1[2]),min(dims[2]-1,px2[2])])
                yi = max(0, min(current_slice, dims[1]-1))
                for x in range(xi[0], xi[1]+1):
                    for z in range(zi[0], zi[1]+1):
                        wx = origin[0] + x*spacing[0] - cx
                        wz = origin[2] + z*spacing[2] - cz
                        if in_ellipse_2d(wx, wz):
                            scalars.append(img.GetScalarComponentAsFloat(x, yi, z, 0))
                w_mm = 2*a; h_mm = 2*b

            if scalars:
                arr  = np.array(scalars, dtype=np.float32)
                area = math.pi * a * b / 100.0
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
        vis = 1 if current_slice == self.slice_idx else 0
        self._ellipse_actor.SetVisibility(vis)
        for a, _ in self._handles: a.SetVisibility(vis)
        self._text_actor.SetVisibility(vis)
        if vis:
            self._calc_stats()

    # ── 几何更新 ──────────────────────────────────────────────────────────────

    def update_geometry(self):
        self._apply_ellipse_transform()
        self._update_handles()
        self._update_text_pos()
        self._calc_stats()

    # ── 命中检测 ──────────────────────────────────────────────────────────────

    def handle_hit(self, world_pt):
        """返回命中的控制点索引（0=top,1=bottom,2=left,3=right），未命中返回 -1"""
        t = self._hr * 3.0
        for i, pos in enumerate(self._handle_positions()):
            if sum((world_pt[j]-pos[j])**2 for j in range(3))**0.5 < t:
                return i
        return -1

    def edge_hit(self, world_pt):
        cx, cy, cz, a, b, angle_deg = _ellipse_params(self.p1, self.p2, self.vt, self._depth_val)
        return _on_ellipse_edge(world_pt, cx, cy, cz, a, b, angle_deg, self.vt, _EDGE_HIT_MM)

    def remove(self):
        self._renderer.RemoveActor(self._ellipse_actor)
        for a, _ in self._handles: self._renderer.RemoveActor(a)
        if self._text_actor: self._renderer.RemoveActor(self._text_actor)


class EllipseROIManager:
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
            if self._handlers.get(vtype) is None:
                handler = _EllipseViewHandler(ortho, vtype, self._annotations[vtype])
                self._handlers[vtype] = handler
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


class _EllipseViewHandler:
    def __init__(self, ortho_viewer, view_type, annotations):
        self.ortho  = ortho_viewer
        self.vtype  = view_type
        self.annots = annotations

        self._picker = vtk.vtkCellPicker()
        self._picker.SetTolerance(0.001)

        self._drawing     = False
        self._start_world = None
        self._preview: _PreviewEllipse | None = None

        self._editing_ann: EllipseAnnotation | None = None
        self._edit_handle = -1
        self._moving_ann:  EllipseAnnotation | None = None
        self._move_last   = None
        self._selected_ann: EllipseAnnotation | None = None

    # ── 事件 ─────────────────────────────────────────────────────────────────

    def on_press(self, caller, ev):
        world = self._pick(caller)
        if world is None:
            return

        # 正在移动中：第二次点击 → 停止移动
        if self._moving_ann:
            self._moving_ann = None
            self._move_last  = None
            self._render()
            return

        # 正在绘制中：第二次点击 → 完成标注
        if self._drawing and self._start_world:
            if self._preview:
                self._preview.remove(); self._preview = None
            if not self._is_too_small(self._start_world, world):
                ann = EllipseAnnotation(
                    self._start_world, world, self.vtype,
                    self.ortho.viewer,
                    self.ortho.viewer.GetSlice(),
                )
                self.annots.append(ann)
                self._selected_ann = ann
            self._drawing = False; self._start_world = None
            self._render()
            return

        # 命中控制点 → 编辑（拖拽模式）
        for ann in reversed(self._visible_annots()):
            hi = ann.handle_hit(world)
            if hi >= 0:
                self._editing_ann = ann; self._edit_handle = hi
                self._selected_ann = ann
                return

        # 命中边框 → 开始移动（点击跟随模式）
        for ann in reversed(self._visible_annots()):
            if ann.edge_hit(world):
                self._moving_ann = ann
                self._move_last  = world
                self._selected_ann = ann
                return

        # 空白区域：第一次点击 → 开始绘制
        self._drawing = True; self._start_world = world
        self._selected_ann = None
        depth_val = self._get_depth_val()
        self._preview = _PreviewEllipse(self.ortho.viewer.GetRenderer())
        self._preview.update(world, world, self.vtype, depth_val)
        self._render()

    def on_move(self, caller, ev):
        world = self._pick(caller)

        if self._editing_ann and self._edit_handle >= 0:
            if world is not None:
                self._do_edit(world)
            return

        if self._moving_ann:
            if world is not None:
                self._do_move(world)
            return

        if self._drawing and self._start_world and self._preview:
            if world is not None:
                depth_val = self._get_depth_val()
                self._preview.update(self._start_world, world, self.vtype, depth_val)
                self._render()
            return

        caller.GetInteractorStyle().OnMouseMove()

    def on_release(self, caller, ev):
        if self._editing_ann:
            self._editing_ann = None; self._edit_handle = -1
            self._render()
            return

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
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._refresh_visibility)

    def on_slice_changed_qt(self, _value=None):
        self._refresh_visibility()

    def _refresh_visibility(self):
        try:
            cur = self.ortho.viewer.GetSlice()
            for ann in self.annots:
                ann.update_visibility(cur)
            self.ortho.widget.GetRenderWindow().Render()
        except Exception:
            pass

    # ── 内部辅助 ─────────────────────────────────────────────────────────────

    def _visible_annots(self):
        try:
            cur = self.ortho.viewer.GetSlice()
        except Exception:
            return self.annots
        return [a for a in self.annots if a.slice_idx == cur]

    def _get_depth_val(self):
        try:
            ac = self.ortho.viewer.GetImageActor().GetCenter()
            if self.vtype == "XY":   return ac[2]
            elif self.vtype == "YZ": return ac[0]
            else:                    return ac[1]
        except Exception:
            return None

    def _pick(self, iren):
        try:
            viewer = self.ortho.viewer
            actor  = viewer.GetImageActor()
            x, y   = iren.GetEventPosition()

            self._picker.InitializePickList()
            self._picker.AddPickList(actor)
            self._picker.PickFromListOn()
            result = self._picker.Pick(x, y, 0, viewer.GetRenderer())

            if result == 0:
                return None

            pos = list(self._picker.GetPickPosition())

            img = viewer.GetInput()
            if img is None:
                return None
            origin  = img.GetOrigin()
            spacing = img.GetSpacing()
            dims    = img.GetDimensions()

            actor_center = actor.GetCenter()
            if self.vtype == "XY":
                pos[2] = actor_center[2]
            elif self.vtype == "YZ":
                pos[0] = actor_center[0]
            else:
                pos[1] = actor_center[1]

            pos = _clamp_world(pos, origin, spacing, dims, self.vtype)
            return pos
        except Exception:
            logger.debug("pick error", exc_info=True)
            return None

    def _do_edit(self, world):
        """拖拽控制点：长轴端点改变长度，短轴端点改变宽度（通过改变 p1/p2 距离实现）"""
        import math
        ann = self._editing_ann; hi = self._edit_handle; vt = self.vt
        cx, cy, cz, a, b, angle_deg = _ellipse_params(ann.p1, ann.p2, vt, ann._depth_val)
        ar = math.radians(angle_deg)
        cos_a, sin_a = math.cos(ar), math.sin(ar)

        if vt == "XY":
            if hi in (0, 1):  # 长轴端点 → 改变 a（重新计算 p1/p2 沿长轴方向）
                new_a = math.sqrt((world[0]-cx)**2 + (world[1]-cy)**2)
                ann.p1 = [cx - new_a*cos_a, cy - new_a*sin_a, ann.p1[2]]
                ann.p2 = [cx + new_a*cos_a, cy + new_a*sin_a, ann.p2[2]]
            else:  # 短轴端点 → 改变 b（不改变 p1/p2，只记录 b 比例）
                # 短轴不直接存储，通过缩放 p1/p2 距离来间接控制
                # 简化：短轴拖拽时整体缩放 b/a 比例（保持长轴不变）
                new_b = math.sqrt((world[0]-cx)**2 + (world[1]-cy)**2)
                ratio = new_b / a if a > 0 else 0.5
                # 通过调整 p1/p2 的垂直分量来改变 b
                # b = a * 0.5 是默认，这里允许自由调整
                # 存储 b 到 p1[2] 作为自定义短半轴（hack，但不影响深度轴）
                ann._custom_b = max(1e-4, new_b)
        elif vt == "YZ":
            if hi in (0, 1):
                new_a = math.sqrt((world[1]-cy)**2 + (world[2]-cz)**2)
                ann.p1 = [ann.p1[0], cy - new_a*cos_a, cz - new_a*sin_a]
                ann.p2 = [ann.p2[0], cy + new_a*cos_a, cz + new_a*sin_a]
            else:
                new_b = math.sqrt((world[1]-cy)**2 + (world[2]-cz)**2)
                ann._custom_b = max(1e-4, new_b)
        else:
            if hi in (0, 1):
                new_a = math.sqrt((world[0]-cx)**2 + (world[2]-cz)**2)
                ann.p1 = [cx - new_a*cos_a, ann.p1[1], cz - new_a*sin_a]
                ann.p2 = [cx + new_a*cos_a, ann.p2[1], cz + new_a*sin_a]
            else:
                new_b = math.sqrt((world[0]-cx)**2 + (world[2]-cz)**2)
                ann._custom_b = max(1e-4, new_b)
        ann.update_geometry(); self._render()

    def _do_move(self, world):
        if self._move_last is None:
            return
        delta = [world[i] - self._move_last[i] for i in range(3)]
        ann = self._moving_ann
        vt  = self.vtype

        new_p1 = [ann.p1[i] + delta[i] for i in range(3)]
        new_p2 = [ann.p2[i] + delta[i] for i in range(3)]

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
                    new_p1[ax] += shift; new_p2[ax] += shift
                elif mx > hi:
                    shift = mx - hi
                    new_p1[ax] -= shift; new_p2[ax] -= shift
        except Exception:
            pass

        ann.p1 = new_p1
        ann.p2 = new_p2
        ann.update_geometry()
        self._move_last = world
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
