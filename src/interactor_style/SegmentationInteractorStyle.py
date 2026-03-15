import vtk

from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.utils.globalVariables import *


class LeftButtonPressEvent_Point():
    def __init__(self, picker, baseModelClass: BaseModel, viewModel: OrthoViewerModel):
        self.picker = picker
        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.start = []
        self.view = self.viewModel.AxialOrthoViewer.viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.origin = self.baseModelClass.origin
        self.spacing = self.baseModelClass.spacing
        self.imageshape = self.baseModelClass.imageDimensions
        self.point_dict = {}

    def __call__(self, caller, ev):
        self.picker.AddPickList(self.actor)
        self.picker.SetTolerance(0.01)
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.render)
        self.start = self.picker.GetPickPosition()
        print(self.start)

        point_x = int((self.start[0] - self.origin[0]) / self.spacing[0])
        point_y = int((self.start[1] - self.origin[1]) / self.spacing[1])
        point_z = int((self.start[2] - self.origin[2]) / self.spacing[2])

        self.start_pos = [point_x, point_y, point_z]

        if point_x < 0 or point_x > self.imageshape[0] or point_y < 0 or point_y > self.imageshape[1]:
            return

        if getSelectPointLabel1():
            label = 1
        else:
            label = 0
        index = point_z
        if str(index) in self.point_dict:
            self.point_dict[str(index)]["points"].append([point_x, point_y])
            self.point_dict[str(index)]["label"].append(label)
        else:
            self.point_dict[str(index)] = {"points": [[point_x, point_y]], "label": [label],
                                           "image_name": "_image_" + str(point_z) + ".png"}
        setPointsDict(self.point_dict)
        print(getPointsDict())

        square = vtk.vtkPolyData()

        points = vtk.vtkPoints()
        points.InsertNextPoint(self.start[0] - 1, self.start[1] + 1, self.start[2] + 1)
        points.InsertNextPoint(self.start[0] + 1, self.start[1] + 1, self.start[2] + 1)
        points.InsertNextPoint(self.start[0] + 1, self.start[1] - 1, self.start[2] + 1)
        points.InsertNextPoint(self.start[0] - 1, self.start[1] - 1, self.start[2] + 1)

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

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0, 1, 0)
        setPointsUndoStack([point_x, point_y, point_z, label])
        print(getPointsUndoStack())
        self.square_actor = actor
        setPointsActor(self.square_actor)
        self.ren = self.view.GetRenderer()
        self.ren.AddActor(actor)
        self.iren.Render()
        self.render.Render()
        self.view.UpdateDisplayExtent()
        self.view.Render()


class LeftButtonPressEvent_labelBox():
    def __init__(self, picker, baseModelClass: BaseModel, viewModel: OrthoViewerModel):
        self.picker = picker
        self.start = []
        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.view = self.viewModel.AxialOrthoViewer.viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.origin = self.baseModelClass.origin
        self.spacing = self.baseModelClass.spacing
        self.imageshape = self.baseModelClass.imageDimensions
        self.count = 0
        self.actor_list = []
        self.single_boundingBox_dict = {}
        self.multiple_boundingBox_dict = {}

    def __call__(self, caller, ev):
        self.picker.AddPickList(self.actor)
        self.count += 1
        self.start, self.start_pos = self.get_point_position()  # tuple list
        print(self.start)
        if self.count % 2 != 0:
            setState2True()
            setStartPoint(self.start)
            if getSelectSingleBoxLabel():
                try:
                    for i in getSingleBoundingBoxActor():
                        self.view.GetRenderer().RemoveActor(i)
                    self.view.Render()
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
        else:
            setState2False()
            if getSelectSingleBoxLabel():
                boundingbox_dict = getSingleBoundingBoxDict()
                index = getSingleBoundingBox()[4]
                if str(index) in boundingbox_dict.keys():
                    del boundingbox_dict[str(index)]
                    single_boundingbox = getSingleUndoStack()
                    # 记录要删除的索引
                    indices_to_remove = [i for i, point in enumerate(single_boundingbox) if point[-1] == index]
                    # 原地删除元素
                    for i in sorted(indices_to_remove, reverse=True):
                        del single_boundingbox[i]
                setSingleUndoStack(getSingleBoundingBox())

                if str(index) in self.single_boundingBox_dict:
                    self.single_boundingBox_dict[str(index)]["bounding_box"] = getSingleBoundingBox()
                else:
                    self.single_boundingBox_dict[str(index)] = {"bounding_box": getSingleBoundingBox(),
                                                                "image_name": "_image_" + str(index) + ".png"}
                setSingleBoundingBoxDict(self.single_boundingBox_dict)
            else:
                try:
                    for actor in getMultipleBoundingBoxActor():
                        for i in actor:
                            self.view.GetRenderer().RemoveActor(i)
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                setMultipleUndoStack(getSingleBoundingBox())
                index = getSingleBoundingBox()[4]
                if str(index) in self.multiple_boundingBox_dict:
                    self.multiple_boundingBox_dict[str(index)]["bounding_box"].append(getSingleBoundingBox())
                else:
                    self.multiple_boundingBox_dict[str(index)] = {"bounding_box": [getSingleBoundingBox()],
                                                                  "image_name": "_image_" + str(index) + ".png"}
                setMultipleBoundingBoxDict(self.multiple_boundingBox_dict)

                value = self.view.GetSlice()
                if getMultipleUndoStack() != []:
                    for data in getMultipleUndoStack():
                        if data[4] == value:
                            self.actor_list = []
                            self.drwa_single_bounding_box(data)
                            setMultipleBoundingBoxActor(self.actor_list)
                self.view.UpdateDisplayExtent()
                self.view.Render()

        self.iren.Render()
        self.render.Render()
        self.view.UpdateDisplayExtent()
        self.view.Render()

    def drwa_single_bounding_box(self, data):
        start_pointX = data[0] * self.spacing[0] + self.origin[0]
        start_pointY = data[1] * self.spacing[1] + self.origin[1]
        end_pointX = data[2] * self.spacing[0] + self.origin[0]
        end_pointY = data[3] * self.spacing[1] + self.origin[1]
        point_Z = data[4] * self.spacing[2] + self.origin[2] + 1

        start = [start_pointX, start_pointY]
        end = [end_pointX, end_pointY]

        left = [0, 0]
        right = [0, 0]

        left[0] = start[0] if start[0] <= end[0] else end[0]
        left[1] = start[1] if start[1] <= end[1] else end[1]

        right[0] = start[0] if start[0] > end[0] else end[0]
        right[1] = start[1] if start[1] > end[1] else end[1]

        point1 = [left[0], left[1], point_Z]
        point2 = [left[0], right[1], point_Z]
        point3 = [right[0], right[1], point_Z]
        point4 = [right[0], left[1], point_Z]

        self.SetLine(point1, point2)
        self.SetLine(point2, point3)
        self.SetLine(point3, point4)
        self.SetLine(point4, point1)

    def SetLine(self, point1, point2):
        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(point1)
        lineSource.SetPoint2(point2)
        lineSource.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(2)
        actor.GetProperty().SetColor(0.0, 1.0, 1.0)
        self.actor_list.append(actor)
        self.view.GetRenderer().AddActor(actor)

    def get_point_position(self):
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.view.GetRenderer())
        pos = self.picker.GetPickPosition()
        point_x = int((pos[0] - self.origin[0]) / self.spacing[0])
        point_y = int((pos[1] - self.origin[1]) / self.spacing[1])
        point_z = int((pos[2] - self.origin[2]) / self.spacing[2])
        return pos, [point_x, point_y, point_z]


class MouseMoveEvent_labelBox():
    def __init__(self, picker, baseModelClass: BaseModel, viewModel: OrthoViewerModel):
        self.picker = picker
        self.start = []
        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.view = self.viewModel.AxialOrthoViewer.viewer
        self.actor = self.view.GetImageActor()
        self.iren = self.view.GetRenderWindow().GetInteractor()
        self.render = self.view.GetRenderer()
        self.origin = self.baseModelClass.origin
        self.spacing = self.baseModelClass.spacing
        self.imageshape = self.baseModelClass.imageDimensions
        self.square_actor = None
        self.actor_list = []

    def __call__(self, caller, ev):
        if getSelectSingleBoxLabel():
            if getState2():
                setSingleBoundingBox([])
                try:
                    for i in range(len(self.actor_list)):
                        self.view.GetRenderer().RemoveActor(self.actor_list[i])
                    self.actor_list = []
                except:
                    print("clear actor failed!!!")
                self.picker.AddPickList(self.actor)
                self.start = getStartPoint()
                self.start_pos = [int((self.start[i] - self.origin[i]) / self.spacing[i]) for i in range(3)]
                self.end, self.end_pos = self.get_point_position()
                setSingleBoundingBox(
                    [self.start_pos[0], self.start_pos[1], self.end_pos[0], self.end_pos[1], self.end_pos[2]])
                self.draw_single_label_box(self.start, self.end)
                setSingleBoundingBoxActor(self.actor_list)
                self.view.UpdateDisplayExtent()
                self.view.Render()
            else:
                pass
        else:
            if getState2():
                setBoundingBoxOriginal([])
                try:
                    for i in range(len(self.actor_list)):
                        self.view.GetRenderer().RemoveActor(self.actor_list[i])
                    self.actor_list = []
                except:
                    print("clear actor failed!!!")
                self.picker.AddPickList(self.actor)
                self.start = getStartPoint()
                self.start_pos = [int((self.start[i] - self.origin[i]) / self.spacing[i]) for i in range(3)]
                self.end, self.end_pos = self.get_point_position()
                setSingleBoundingBox(
                    [self.start_pos[0], self.start_pos[1], self.end_pos[0], self.end_pos[1], self.end_pos[2]])
                setBoundingBoxOriginal([self.start[0], self.start[1], self.end[0], self.end[1], self.end[2]])
                self.draw_single_label_box(self.start, self.end)
                setLastBoundingBoxActor(self.actor_list)
                self.view.UpdateDisplayExtent()
                self.view.Render()

    def get_point_position(self):
        self.picker.Pick(self.iren.GetEventPosition()[0], self.iren.GetEventPosition()[1], 0, self.view.GetRenderer())
        pos = self.picker.GetPickPosition()
        point_x = int((pos[0] - self.origin[0]) / self.spacing[0])
        point_y = int((pos[1] - self.origin[1]) / self.spacing[1])
        point_z = int((pos[2] - self.origin[2]) / self.spacing[2])
        return pos, [point_x, point_y, point_z]

    def SetLine(self, point1, point2):
        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(point1)
        lineSource.SetPoint2(point2)
        lineSource.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(2)
        actor.GetProperty().SetColor(0.0, 1.0, 1.0)
        self.actor_list.append(actor)
        self.view.GetRenderer().AddActor(actor)

    def draw_single_label_box(self, start, end):
        left = [0, 0]
        right = [0, 0]

        left[0] = start[0] if start[0] <= end[0] else end[0]
        left[1] = start[1] if start[1] <= end[1] else end[1]

        right[0] = start[0] if start[0] > end[0] else end[0]
        right[1] = start[1] if start[1] > end[1] else end[1]

        point1 = [left[0], left[1], start[2]]
        point2 = [left[0], right[1], start[2]]
        point3 = [right[0], right[1], start[2]]
        point4 = [right[0], left[1], start[2]]

        self.SetLine(point1, point2)
        self.SetLine(point2, point3)
        self.SetLine(point3, point4)
        self.SetLine(point4, point1)
