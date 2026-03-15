import vtk

from src.utils.globalVariables import *


class LeftButtonPressEvent_Dragging():
    def __init__(self, viewer, type):
        self.view = viewer
        self.iren = self.view.GetRenderWindow().GetInteractor()

    def __call__(self, caller, ev):
        self.start = self.iren.GetEventPosition()
        setStartPoint(self.start)
        setLeftButtonDown(True)


class LeftButtonReleaseEvent_Dragging():
    def __init__(self, viewer, type):
        self.view = viewer

    def __call__(self, caller, ev):
        setLeftButtonDown(False)

class MouseMoveEvent_Dragging():
    def __init__(self, viewer, type):
        self.start = []
        self.type = type
        self.view = viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.square_actor = None
        self.imageshape = self.view.GetInput().GetDimensions()
        self.camera = self.view.GetRenderer().GetActiveCamera()

    def ComputeWorldToDisplay(self, renderer, worldPt, displayPt):
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToWorld()
        coord.SetValue(worldPt)
        displayPt = coord.GetComputedDisplayValue(renderer)

    def ComputeDisplayToWorld(self, renderer, displayPt, worldPt):
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToDisplay()
        coord.SetValue(displayPt[0], displayPt[1], displayPt[2])
        worldPt[:] = coord.GetComputedWorldValue(renderer)

    def __call__(self, caller, ev):
        if getLeftButtonDown():
            print("左键按下")
            self.start = getStartPoint()
            self.end = self.iren.GetEventPosition()
            delta_x = self.end[0] - self.start[0]
            delta_y = self.end[1] - self.start[1]
            # self.camera = self.render.GetActiveCamera()
            self.move_camera(self.start[0], self.start[1], delta_x, delta_y)
            setStartPoint(self.end)
            self.view.SliceScrollOnMouseWheelOff()
            self.view.UpdateDisplayExtent()
            self.view.Render()

    def move_camera(self, x, y, delta_x, delta_y):
        view_focus_3d = self.camera.GetFocalPoint()
        view_focus_2d = [0, 0, 0]
        self.ComputeWorldToDisplay(self.render, view_focus_3d, view_focus_2d)
        new_mouse_point = [0, 0, 0, 1]
        self.ComputeDisplayToWorld(self.render, [x, y, view_focus_2d[2]], new_mouse_point)
        old_mouse_point = [0, 0, 0, 1]
        self.ComputeDisplayToWorld(self.render, [x - delta_x, y - delta_y, view_focus_2d[2]], old_mouse_point)
        motion_vector = [0, 0, 0]
        motion_vector[0] = old_mouse_point[0] - new_mouse_point[0]
        motion_vector[1] = old_mouse_point[1] - new_mouse_point[1]
        motion_vector[2] = old_mouse_point[2] - new_mouse_point[2]

        view_focus = self.camera.GetFocalPoint()
        view_point = self.camera.GetPosition()
        self.camera.SetFocalPoint(motion_vector[0] + view_focus[0], motion_vector[1] + view_focus[1],
                                  motion_vector[2] + view_focus[2])
        self.camera.SetPosition(motion_vector[0] + view_point[0], motion_vector[1] + view_point[1],
                                motion_vector[2] + view_point[2])
        self.iren.Render()
