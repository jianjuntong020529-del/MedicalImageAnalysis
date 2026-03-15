import vtk

from src.model.AnnotationEnableModel import AnnotationEnable
from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.utils.globalVariables import *


class AnnotationService:
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel):

        self.baseModelClass = baseModelClass
        self.viewModel = viewModel

    def label_clear(self):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        try:
            for i in getPointsActor():
                self.viewer_XY.GetRenderer().RemoveActor(i)
            self.viewer_XY.Render()
        except:
            print('Close viewer_XY point actor Failed!!!')
        clearPointsActor()
        clearPointsUndoStack()
        clearPointsRedoStack()
        clearPointsDict()

        if getSelectSingleBoxLabel():
            clearSingleUndoStack()
            clearPointsRedoStack()
            clearSingleBoundingBoxDict()
            try:
                for i in getSingleBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")
        else:
            clearMultipleUndoStack()
            clearMultipleRedoStack()
            clearMultipleBoundingBoxDict()
            try:
                for i in getSingleBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
            except:
                print('Close viewer_XY actor_paint Failed!!!')
            try:
                for i in getLastBoundingBoxActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
            except:
                print('Close viewer_XY actor_paint Failed!!!')
            try:
                for actor in getMultipleBoundingBoxActor():
                    for i in actor:
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                clearMultipleBoundingBoxActor()
                self.viewer_XY.Render()
            except:
                print("clear the single box actor failed!!")

    def label_redo(self):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider
        if AnnotationEnable.pointAction.isChecked():
            point_dict = getPointsDict()
            if len(getPointsRedoStack()) > 0:
                redo_point = getPointsRedoStack().pop()
                setPointsUndoStack(redo_point)
                if str(redo_point[2]) in point_dict:
                    point_dict[str(redo_point[2])]["points"].append([redo_point[0], redo_point[1]])
                    point_dict[str(redo_point[2])]["label"].append(redo_point[3])
                else:
                    point_dict[str(redo_point[2])] = {"points": [[redo_point[0], redo_point[1]]],
                                                      "label": [redo_point[3]],
                                                      "image_name": "_image_" + str(redo_point[2]) + ".png"}
            for point in getPointsUndoStack():
                if point[2] == self.verticalSlider_XY.value():
                    self.point_paints(point)
            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
        else:
            if getSelectSingleBoxLabel():
                try:
                    for i in getSingleBoundingBoxActor():
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                if getSingleRedoStack():
                    setSingleUndoStack(getSingleRedoStack().pop())
                for data in getSingleUndoStack():
                    if data[4] == self.verticalSlider_XY.value():
                        actor_list = self.drwa_single_bounding_box(data)
                        setSingleBoundingBoxActor(actor_list)
                self.viewer_XY.UpdateDisplayExtent()
                self.viewer_XY.Render()
            else:
                try:
                    for i in getSingleBoundingBoxActor():
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                try:
                    for i in getLastBoundingBoxActor():
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                try:
                    for actor in getMultipleBoundingBoxActor():
                        for i in actor:
                            self.viewer_XY.GetRenderer().RemoveActor(i)
                    clearMultipleBoundingBoxActor()
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                boundingbox_dict = getMultipleBoundingBoxDict()
                print(boundingbox_dict)
                print(getMultipleRedoStack())
                if len(getMultipleRedoStack()) > 0:
                    redo_box = getMultipleRedoStack().pop()
                    print("redo_box:", redo_box)
                    setMultipleUndoStack(redo_box)
                    if str(redo_box[4]) in boundingbox_dict:
                        boundingbox_dict[str(redo_box[4])]["bounding_box"].append(redo_box)
                    else:
                        boundingbox_dict[str(redo_box[4])] = {"bounding_box": [redo_box],
                                                              "image_name": "_image_" + str(redo_box[4]) + ".png"}
                print(getMultipleUndoStack())
                print(getMultipleBoundingBoxDict())
                for data in getMultipleUndoStack():
                    if data[4] == self.verticalSlider_XY.value():
                        actor_list = self.drwa_single_bounding_box(data)
                        setMultipleBoundingBoxActor(actor_list)
                self.viewer_XY.UpdateDisplayExtent()
                self.viewer_XY.Render()

    def label_undo(self):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        self.verticalSlider_XY = self.viewModel.AxialOrthoViewer.slider
        if AnnotationEnable.pointAction.isChecked():
            point_dict = getPointsDict()
            try:
                for i in getPointsActor():
                    self.viewer_XY.GetRenderer().RemoveActor(i)
            except:
                print('Close viewer_XY actor_paint Failed!!!')
            if len(getPointsUndoStack()) > 0:
                undo_point = getPointsUndoStack().pop()
                setPointsRedoStack(undo_point)
                point_to_remove = [undo_point[0], undo_point[1]]
                for i, point in enumerate(point_dict[str(undo_point[2])]['points']):
                    # 检查点的坐标是否与要删除的点匹配
                    if point == point_to_remove:
                        # 删除该点
                        del point_dict[str(undo_point[2])]['points'][i]
                        # 删除标签
                        del point_dict[str(undo_point[2])]['label'][i]

            for point in getPointsUndoStack():
                if point[2] == self.verticalSlider_XY.value():
                    self.point_paints(point)
            self.viewer_XY.UpdateDisplayExtent()
            self.viewer_XY.Render()
        else:
            if getSelectSingleBoxLabel():
                try:
                    for i in getSingleBoundingBoxActor():
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                single_boundingBox_actor = getSingleUndoStack()
                if getSingleUndoStack() != []:
                    setSingleRedoStack(getSingleUndoStack().pop())
                for data in getSingleUndoStack():
                    if data[4] == self.verticalSlider_XY.value():
                        actor_list = self.drwa_single_bounding_box(data)
                        setSingleBoundingBoxActor(actor_list)
                self.viewer_XY.UpdateDisplayExtent()
                self.viewer_XY.Render()
            else:
                try:
                    for i in getSingleBoundingBoxActor():
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                try:
                    for i in getLastBoundingBoxActor():
                        self.viewer_XY.GetRenderer().RemoveActor(i)
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                try:
                    for actor in getMultipleBoundingBoxActor():
                        for i in actor:
                            self.viewer_XY.GetRenderer().RemoveActor(i)
                    clearMultipleBoundingBoxActor()
                except:
                    print('Close viewer_XY actor_paint Failed!!!')
                bounding_box = getMultipleBoundingBoxDict()
                if getMultipleUndoStack() != []:
                    undo_point = getMultipleUndoStack().pop()
                    setMultipleRedoStack(undo_point)
                    for i, point in enumerate(bounding_box[str(undo_point[4])]['bounding_box']):
                        # 检查点的坐标是否与要删除的点匹配
                        if point == undo_point:
                            # 删除该点
                            del bounding_box[str(undo_point[4])]['bounding_box'][i]

                for data in getMultipleUndoStack():
                    if data[4] == self.verticalSlider_XY.value():
                        actor_list = self.drwa_single_bounding_box(data)
                        setMultipleBoundingBoxActor(actor_list)
                self.viewer_XY.UpdateDisplayExtent()
                self.viewer_XY.Render()

    def point_paints(self, point):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
        origin = self.baseModelClass.origin
        spacing = self.baseModelClass.spacing

        point_x = point[0] * spacing[0] + origin[0]
        point_y = point[1] * spacing[1] + origin[1]
        point_z = point[2] * spacing[2] + origin[2]

        square = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        points.InsertNextPoint(point_x - 1, point_y + 1, point_z + 1)
        points.InsertNextPoint(point_x + 1, point_y + 1, point_z + 1)
        points.InsertNextPoint(point_x + 1, point_y - 1, point_z + 1)
        points.InsertNextPoint(point_x - 1, point_y - 1, point_z + 1)

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
        setPointsActor(actor)
        self.viewer_XY.GetRenderer().AddActor(actor)

    def SetLine(self, point1, point2):
        self.viewer_XY = self.viewModel.AxialOrthoViewer.viewer
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
        self.viewer_XY.GetRenderer().AddActor(actor)
        return actor

    def drwa_single_bounding_box(self, data):
        actor_list = []

        origin = self.baseModelClass.origin
        spacing = self.baseModelClass.spacing

        start_pointX = data[0] * spacing[0] + origin[0]
        start_pointY = data[1] * spacing[1] + origin[1]
        end_pointX = data[2] * spacing[0] + origin[0]
        end_pointY = data[3] * spacing[1] + origin[1]
        point_Z = data[4] * spacing[2] + origin[2] + 1

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

        actor_list.append(self.SetLine(point1, point2))
        actor_list.append(self.SetLine(point2, point3))
        actor_list.append(self.SetLine(point3, point4))
        actor_list.append(self.SetLine(point4, point1))
        return actor_list
