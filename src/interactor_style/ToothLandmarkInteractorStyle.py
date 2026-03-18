import vtk

from src.constant.ParamConstant import ParamConstant
from src.constant.WindowConstant import WindowConstant
from src.utils.globalVariables import *


class LeftButtonPressEvent():
    def __init__(self, picker,viewer,color_combobox):
        self.picker = picker
        self.start = []
        self.view = viewer
        self.color_combobox = color_combobox
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.image = self.view.GetInput()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.square_actor = None
        self.imageshape = self.view.GetInput().GetDimensions()

    def __call__(self, caller, ev):
        self.picker.AddPickList(self.actor)
        self.picker.SetTolerance(0.01)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.start = self.picker.GetPickPosition()
        print(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1])
        print(self.start)

        point_x = int((self.start[0] - self.origin[0])/self.spacing[0])
        point_y = int((self.start[1] - self.origin[1]) / self.spacing[1])
        point_z = int((self.start[2] - self.origin[2]) / self.spacing[2])
        if point_x < 0 or point_x > self.imageshape[0] or point_y < 0 or point_y > self.imageshape[1]:
            return

        self.start_pos = [point_x,point_y,point_z]
        print(self.start_pos)

        square = vtk.vtkPolyData()

        points = vtk.vtkPoints()
        points.InsertNextPoint(self.start[0]-0.5, self.start[1]+0.5, point_z)
        points.InsertNextPoint(self.start[0]+0.5, self.start[1]+0.5, point_z)
        points.InsertNextPoint(self.start[0]+0.5, self.start[1]-0.5, point_z)
        points.InsertNextPoint(self.start[0]-0.5, self.start[1]-0.5, point_z)

        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(4)
        polygon.GetPointIds().SetId(0, 0)
        polygon.GetPointIds().SetId(1, 1)
        polygon.GetPointIds().SetId(2, 2)
        polygon.GetPointIds().SetId(3, 3)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(polygon)

        square.SetPoints(points)
        square.SetPolys(cells)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(square)

        rgb = hex_to_rgb(ParamConstant.CURRENT_COLOR)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(rgb[0],rgb[1],rgb[2])

        setUndoStack([int(ParamConstant.CURRENT_COLOR_ID),point_z,point_x,point_y])
        self.square_actor = actor
        setPaintActor(self.square_actor)
        setColorIndexList(int(ParamConstant.CURRENT_COLOR_ID))
        self.color_combobox.setItemText(ParamConstant.CURRENT_COLOR_INDEX,ParamConstant.CURRENT_COLOR_ID+" √")
        self.ren = self.view.GetRenderer()
        self.ren.AddActor(actor)
        self.iren.Render()
        self.render.Render()
        self.view.UpdateDisplayExtent()
        self.view.Render()

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b