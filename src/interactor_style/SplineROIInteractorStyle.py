# -*- coding: utf-8 -*-
"""
Spline ROI
"""
import math
import numpy as np
import vtk
from src.utils.logger import get_logger

logger = get_logger(__name__)

_COLOR_SPLINE  = (0.9, 0.2, 0.9)
_COLOR_HANDLE  = (0.2, 1.0, 0.2)
_COLOR_PREVIEW = (0.9, 0.9, 0.2)
_HANDLE_R_FACTOR = 4.0
_DOUBLE_CLICK_MS = 400


def _world_to_pixel(pt, origin, spacing):
    return [int(round((pt[i] - origin[i]) / spacing[i])) for i in range(3)]


def _clamp_world(pos, origin, spacing, dims, vt):
    p = list(pos)
    lo = [origin[i] for i in range(3)]
    hi = [origin[i] + (dims[i] - 1) * spacing[i] for i in range(3)]
    if vt == "XY":
        p[0] = max(lo[0], min(hi[0], p[0])); p[1] = max(lo[1], min(hi[1], p[1]))
    elif vt == "YZ":
        p[1] = max(lo[1], min(hi[1], p[1])); p[2] = max(lo[2], min(hi[2], p[2]))
    else:
        p[0] = max(lo[0], min(hi[0], p[0])); p[2] = max(lo[2], min(hi[2], p[2]))
    return p


def _plane_axes(vt):
    if vt == "XY":   return (0, 1)
    elif vt == "YZ": return (1, 2)
    else:            return (0, 2)


def _catmull_rom(p0, p1, p2, p3, n=20):
    pts = []
    for i in range(n):
        t = i / n
        t2, t3 = t*t, t*t*t
        x = 0.5*((2*p1[0]) + (-p0[0]+p2[0])*t + (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 + (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
        y = 0.5*((2*p1[1]) + (-p0[1]+p2[1])*t + (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 + (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
        z = 0.5*((2*p1[2]) + (-p0[2]+p2[2])*t + (2*p0[2]-5*p1[2]+4*p2[2]-p3[2])*t2 + (-p0[2]+3*p1[2]-3*p2[2]+p3[2])*t3)
        pts.append((x, y, z))
    return pts


def _spline_points(ctrl_pts, closed=False, n_seg=30):
    if len(ctrl_pts) < 2:
        return list(ctrl_pts)
    pts = list(ctrl_pts)
    if closed:
        pts = [pts[-1]] + pts + [pts[0]] + [pts[1]]
    else:
        pts = [pts[0]] + pts + [pts[-1]]
    result = []
    for i in range(1, len(pts) - 2):
        seg = _catmull_rom(pts[i-1], pts[i], pts[i+1], pts[i+2], n_seg)
        result.extend(seg)
    result.append(pts[-2])
    return result


def _seg_length(pts):
    total = 0.0
    for i in range(len(pts) - 1):
        d = sum((pts[i+1][j] - pts[i][j])**2 for j in range(3))
        total += math.sqrt(d)
    return total


def _make_polyline_actor(world_pts, color, lw=1.8, stipple=False):
    n = len(world_pts)
    vtk_pts = vtk.vtkPoints()
    vtk_pts.SetNumberOfPoints(n)
    for i, p in enumerate(world_pts):
        vtk_pts.SetPoint(i, p)
    lines = vtk.vtkCellArray()
    if n > 1:
        lines.InsertNextCell(n)
        for i in range(n):
            lines.InsertCellPoint(i)
    poly = vtk.vtkPolyData()
    poly.SetPoints(vtk_pts); poly.SetLines(lines)
    mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(poly)
    actor = vtk.vtkActor(); actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color); actor.GetProperty().SetLineWidth(lw)
    if stipple:
        actor.GetProperty().SetLineStipplePattern(0xF0F0)
        actor.GetProperty().SetLineStippleRepeatFactor(1)
    return actor, vtk_pts, poly


def _make_sphere(center, radius, color, renderer):
    src = vtk.vtkSphereSource()
    src.SetCenter(center); src.SetRadius(radius)
    src.SetPhiResolution(12); src.SetThetaResolution(12); src.Update()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(src.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.GetProperty().SetColor(*color)
    renderer.AddActor(a)
    return a, src


def _make_text_actor(renderer):
    ta = vtk.vtkTextActor()
    tp = ta.GetTextProperty()
    tp.SetFontSize(11); tp.SetColor(1.0, 1.0, 0.8)
    tp.SetBackgroundColor(0.05, 0.05, 0.05); tp.SetBackgroundOpacity(0.72)
    tp.BoldOn()
    ta.GetPositionCoordinate().SetCoordinateSystemToWorld()
    renderer.AddActor(ta)
    return ta


class SplineAnnotation:
    def __init__(self, ctrl_pts, vt, viewer, slice_idx, depth_val):
        self.ctrl_pts   = [list(p) for p in ctrl_pts]
        self.vt         = vt
        self._viewer    = viewer
        self._renderer  = viewer.GetRenderer()
        self.slice_idx  = slice_idx
        self._depth_val = depth_val
        try:
            sp = viewer.GetInput().GetSpacing()
            self._hr = max(sp) * _HANDLE_R_FACTOR
        except Exception:
            self._hr = 6.0
        self._curve_actor = None
        self._curve_pts   = None
        self._curve_poly  = None
        self._handles     = []
        self._text_actor  = None
        self._build()

    def _build(self):
        spts = _spline_points(self.ctrl_pts, closed=False)
        self._curve_actor, self._curve_pts, self._curve_poly = _make_polyline_actor(spts, _COLOR_SPLINE, lw=1.8)
        self._renderer.AddActor(self._curve_actor)
        for p in self.ctrl_pts:
            a, src = _make_sphere(p, self._hr, _COLOR_HANDLE, self._renderer)
            self._handles.append((a, src))
        self._text_actor = _make_text_actor(self._renderer)
        self._update_stats()

    def _update_stats(self):
        spts = _spline_points(self.ctrl_pts, closed=False)
        length = _seg_length(spts)
        self._text_actor.SetInput(f"Length: {length:.2f} mm")
        if self.ctrl_pts:
            p = self.ctrl_pts[0]
            try:
                sp = self._viewer.GetInput().GetSpacing()
                self._text_actor.GetPositionCoordinate().SetValue(p[0] + sp[0]*3, p[1] + sp[1]*3, p[2])
            except Exception:
                self._text_actor.GetPositionCoordinate().SetValue(p[0]+3, p[1]+3, p[2])

    def update_geometry(self):
        spts = _spline_points(self.ctrl_pts, closed=False)
        n = len(spts)
        new_lines = vtk.vtkCellArray()
        if n > 1:
            new_lines.InsertNextCell(n)
            for i in range(n): new_lines.InsertCellPoint(i)
        self._curve_pts.SetNumberOfPoints(n)
        for i, p in enumerate(spts): self._curve_pts.SetPoint(i, p)
        self._curve_pts.Modified()
        self._curve_poly.SetLines(new_lines)
        self._curve_poly.Modified()
        for a, _ in self._handles: self._renderer.RemoveActor(a)
        self._handles.clear()
        for p in self.ctrl_pts:
            a, src = _make_sphere(p, self._hr, _COLOR_HANDLE, self._renderer)
            self._handles.append((a, src))
        self._update_stats()

    def update_visibility(self, current_slice):
        vis = 1 if current_slice == self.slice_idx else 0
        self._curve_actor.SetVisibility(vis)
        for a, _ in self._handles: a.SetVisibility(vis)
        self._text_actor.SetVisibility(vis)

    def handle_hit(self, world_pt):
        t = self._hr * 3.0
        for i, p in enumerate(self.ctrl_pts):
            if sum((world_pt[j]-p[j])**2 for j in range(3))**0.5 < t:
                return i
        return -1

    def remove(self):
        self._renderer.RemoveActor(self._curve_actor)
        for a, _ in self._handles: self._renderer.RemoveActor(a)
        if self._text_actor: self._renderer.RemoveActor(self._text_actor)


class _SplinePolygonHandler:
    def __init__(self, ortho_viewer, vt, annotations):
        self.ortho  = ortho_viewer
        self.vt     = vt
        self.annots = annotations
        self._picker = vtk.vtkCellPicker()
        self._picker.SetTolerance(0.001)
        self._drawing         = False
        self._ctrl_pts        = []
        self._preview_actor   = None
        self._preview_pts     = None
        self._preview_poly    = None
        self._last_click_time = 0
        self._moving_handle_ann = None
        self._moving_handle_idx = -1
        self._selected_ann      = None

    def on_press(self, caller, ev):
        import time
        world = self._pick(caller)
        if world is None:
            return
        now = time.time() * 1000
        is_double = (now - self._last_click_time) < _DOUBLE_CLICK_MS
        self._last_click_time = now
        if self._moving_handle_ann is not None:
            self._moving_handle_ann.ctrl_pts[self._moving_handle_idx] = world
            self._moving_handle_ann.update_geometry()
            self._moving_handle_ann = None
            self._moving_handle_idx = -1
            self._render()
            return
        if is_double and self._drawing:
            self._finish()
            return
        for ann in reversed(self._visible_annots()):
            hi = ann.handle_hit(world)
            if hi >= 0:
                self._moving_handle_ann = ann
                self._moving_handle_idx = hi
                self._selected_ann = ann
                return
        if self._drawing:
            self._ctrl_pts.append(world)
            self._update_preview()
            self._render()
            return
        self._drawing = True
        self._ctrl_pts = [world]
        self._selected_ann = None
        self._update_preview()
        self._render()

    def on_move(self, caller, ev):
        world = self._pick(caller)
        if world is None:
            return
        if self._moving_handle_ann is not None:
            self._moving_handle_ann.ctrl_pts[self._moving_handle_idx] = world
            self._moving_handle_ann.update_geometry()
            self._render()
            return
        if self._drawing and self._ctrl_pts:
            self._update_preview(cursor=world)
            self._render()
            return
        caller.GetInteractorStyle().OnMouseMove()

    def on_release(self, caller, ev):
        pass

    def on_key(self, caller, ev):
        key = caller.GetKeySym()
        if key in ("Delete", "BackSpace") and self._selected_ann:
            self._selected_ann.remove()
            if self._selected_ann in self.annots:
                self.annots.remove(self._selected_ann)
            self._selected_ann = None
            self._moving_handle_ann = None
            self._moving_handle_idx = -1
            self._drawing = False
            self._ctrl_pts = []
            self._clear_preview()
            self._render()
        elif key == "Escape":
            if self._moving_handle_ann is not None:
                self._moving_handle_ann = None
                self._moving_handle_idx = -1
                self._render()
            elif self._drawing:
                self._drawing = False
                self._ctrl_pts = []
                self._clear_preview()
                self._render()

    def on_slice_changed(self, caller, ev):
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._refresh_visibility)

    def on_slice_changed_qt(self, _=None):
        self._refresh_visibility()

    def _finish(self):
        self._clear_preview()
        if len(self._ctrl_pts) >= 2:
            depth_val = self._get_depth_val()
            ann = SplineAnnotation(self._ctrl_pts, self.vt, self.ortho.viewer, self.ortho.viewer.GetSlice(), depth_val)
            self.annots.append(ann)
            self._selected_ann = ann
        self._drawing = False
        self._ctrl_pts = []
        self._render()

    def _update_preview(self, cursor=None):
        pts = list(self._ctrl_pts)
        if cursor:
            pts.append(cursor)
        if len(pts) < 2:
            self._clear_preview()
            return
        spts = _spline_points(pts, closed=False)
        viewer = self.ortho.viewer
        renderer = viewer.GetRenderer()
        if self._preview_actor is not None:
            renderer.RemoveActor(self._preview_actor)
            self._preview_actor = None
        self._preview_actor, self._preview_pts, self._preview_poly = _make_polyline_actor(spts, _COLOR_PREVIEW, lw=1.2, stipple=True)
        renderer.AddActor(self._preview_actor)

    def _clear_preview(self):
        if self._preview_actor:
            self.ortho.viewer.GetRenderer().RemoveActor(self._preview_actor)
            self._preview_actor = None
            self._preview_pts   = None
            self._preview_poly  = None

    def _visible_annots(self):
        try:
            cur = self.ortho.viewer.GetSlice()
        except Exception:
            return self.annots
        return [a for a in self.annots if a.slice_idx == cur]

    def _get_depth_val(self):
        try:
            ac = self.ortho.viewer.GetImageActor().GetCenter()
            if self.vt == "XY":   return ac[2]
            elif self.vt == "YZ": return ac[0]
            else:                 return ac[1]
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
            if self._picker.Pick(x, y, 0, viewer.GetRenderer()) == 0:
                return None
            pos = list(self._picker.GetPickPosition())
            img = viewer.GetInput()
            if img is None:
                return None
            origin  = img.GetOrigin()
            spacing = img.GetSpacing()
            dims    = img.GetDimensions()
            ac = actor.GetCenter()
            if self.vt == "XY":   pos[2] = ac[2]
            elif self.vt == "YZ": pos[0] = ac[0]
            else:                 pos[1] = ac[1]
            return _clamp_world(pos, origin, spacing, dims, self.vt)
        except Exception:
            logger.debug("pick error", exc_info=True)
            return None

    def _refresh_visibility(self):
        try:
            cur = self.ortho.viewer.GetSlice()
            for ann in self.annots:
                ann.update_visibility(cur)
            self.ortho.widget.GetRenderWindow().Render()
        except Exception:
            pass

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


class _BaseROIManager:
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
        for ortho, vt in configs:
            if self._handlers[vt] is None:
                h = _SplinePolygonHandler(ortho, vt, self._annotations[vt])
                self._handlers[vt] = h
                iren = ortho.widget.GetRenderWindow().GetInteractor()
                sids = [
                    iren.AddObserver("MouseWheelForwardEvent",  h.on_slice_changed, 0.5),
                    iren.AddObserver("MouseWheelBackwardEvent", h.on_slice_changed, 0.5),
                ]
                self._slice_obs[vt] = (iren, sids)
                try:
                    ortho.slider.valueChanged.connect(h.on_slice_changed_qt)
                    self._qt_obs[vt] = (ortho.slider, h.on_slice_changed_qt)
                except Exception:
                    pass
            else:
                h = self._handlers[vt]
            iren = ortho.widget.GetRenderWindow().GetInteractor()
            ids = [
                iren.AddObserver("LeftButtonPressEvent",   h.on_press,   1.0),
                iren.AddObserver("MouseMoveEvent",         h.on_move,    1.0),
                iren.AddObserver("LeftButtonReleaseEvent", h.on_release, 1.0),
                iren.AddObserver("KeyPressEvent",          h.on_key,     1.0),
            ]
            self._observers[vt] = (iren, ids)

    def deactivate(self):
        if not self._active:
            return
        self._active = False
        for vt, val in self._observers.items():
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
        for ortho in [self.view_model.AxialOrthoViewer,
                      self.view_model.SagittalOrthoViewer,
                      self.view_model.CoronalOrthoViewer]:
            try: ortho.widget.GetRenderWindow().Render()
            except Exception: pass


class SplineROIManager(_BaseROIManager):
    def __init__(self, view_model):
        super().__init__(view_model)