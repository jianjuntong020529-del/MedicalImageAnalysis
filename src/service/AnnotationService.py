import vtk

from src.model.AnnotationEnableModel import AnnotationEnable
from src.model.BaseModel import BaseModel
from src.model.OrthoViewerModel import OrthoViewerModel
from src.utils.state_store import get_state_store
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnnotationService:
    def __init__(self, baseModelClass: BaseModel, viewModel: OrthoViewerModel):

        self.baseModelClass = baseModelClass
        self.viewModel = viewModel
        self.state_store = get_state_store()

    def label_clear(self):
        viewer_xy = self.viewModel.AxialOrthoViewer.viewer
        state = self.state_store.annotation

        try:
            for actor in state.points_actor:
                viewer_xy.GetRenderer().RemoveActor(actor)
            viewer_xy.Render()
        except Exception:
            logger.warning('Close viewer_XY point actor Failed', exc_info=True)

        state.points_actor.clear()
        state.points_undo_stack.clear()
        state.points_redo_stack.clear()
        state.points_dict.clear()

        if state.select_single_box_label:
            state.single_undo_stack.clear()
            state.single_redo_stack.clear()
            state.single_boundingBox_dict.clear()
            try:
                for actor in state.single_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
                viewer_xy.Render()
            except Exception:
                logger.warning("clear the single box actor failed", exc_info=True)
            state.single_bounding_box_actor.clear()
        else:
            state.multiple_undo_stack.clear()
            state.multiple_redo_stack.clear()
            state.multiple_boundingBox_dict.clear()
            try:
                for actor in state.single_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            try:
                for actor in state.last_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            try:
                for actor_group in state.multiple_bounding_box_actor:
                    for actor in actor_group:
                        viewer_xy.GetRenderer().RemoveActor(actor)
                viewer_xy.Render()
            except Exception:
                logger.warning("clear the single box actor failed", exc_info=True)
            state.single_bounding_box_actor.clear()
            state.last_bounding_box_actor.clear()
            state.multiple_bounding_box_actor.clear()

    def label_redo(self):
        viewer_xy = self.viewModel.AxialOrthoViewer.viewer
        slider = self.viewModel.AxialOrthoViewer.slider
        state = self.state_store.annotation

        if AnnotationEnable.pointAction.isChecked():
            point_dict = state.points_dict
            if state.points_redo_stack:
                redo_point = state.points_redo_stack.pop()
                state.points_undo_stack.append(redo_point)
                slice_key = str(redo_point[2])
                entry = point_dict.setdefault(slice_key, {"points": [], "label": [], "image_name": "_image_" + slice_key + ".png"})
                entry["points"].append([redo_point[0], redo_point[1]])
                entry["label"].append(redo_point[3])
            for point in state.points_undo_stack:
                if point[2] == slider.value():
                    self.point_paints(point)
            viewer_xy.UpdateDisplayExtent()
            viewer_xy.Render()
            return

        if state.select_single_box_label:
            try:
                for actor in state.single_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            if state.single_redo_stack:
                state.single_undo_stack.append(state.single_redo_stack.pop())
            new_actor_list = []
            for data in state.single_undo_stack:
                if data[4] == slider.value():
                    new_actor_list = self.drwa_single_bounding_box(data)
            state.single_bounding_box_actor = new_actor_list
            viewer_xy.UpdateDisplayExtent()
            viewer_xy.Render()
            return

            try:
                for actor in state.single_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            try:
                for actor in state.last_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            try:
                for actor_group in state.multiple_bounding_box_actor:
                    for actor in actor_group:
                        viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
        state.multiple_bounding_box_actor.clear()

        boundingbox_dict = state.multiple_boundingBox_dict
        if state.multiple_redo_stack:
            redo_box = state.multiple_redo_stack.pop()
            state.multiple_undo_stack.append(redo_box)
            slice_key = str(redo_box[4])
            entry = boundingbox_dict.setdefault(slice_key,
                                                {"bounding_box": [],
                                                 "image_name": "_image_" + slice_key + ".png"})
            entry["bounding_box"].append(redo_box)

        for data in state.multiple_undo_stack:
            if data[4] == slider.value():
                actor_list = self.drwa_single_bounding_box(data)
                state.multiple_bounding_box_actor.append(actor_list)
        viewer_xy.UpdateDisplayExtent()
        viewer_xy.Render()

    def label_undo(self):
        viewer_xy = self.viewModel.AxialOrthoViewer.viewer
        slider = self.viewModel.AxialOrthoViewer.slider
        state = self.state_store.annotation

        if AnnotationEnable.pointAction.isChecked():
            point_dict = state.points_dict
            try:
                for actor in state.points_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            if state.points_undo_stack:
                undo_point = state.points_undo_stack.pop()
                state.points_redo_stack.append(undo_point)
                slice_key = str(undo_point[2])
                point_to_remove = [undo_point[0], undo_point[1]]
                if slice_key in point_dict:
                    for idx, point in enumerate(point_dict[slice_key]["points"]):
                        if point == point_to_remove:
                            del point_dict[slice_key]["points"][idx]
                            del point_dict[slice_key]["label"][idx]
                            break
            for point in state.points_undo_stack:
                if point[2] == slider.value():
                    self.point_paints(point)
            viewer_xy.UpdateDisplayExtent()
            viewer_xy.Render()
            return

        if state.select_single_box_label:
            try:
                for actor in state.single_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            if state.single_undo_stack:
                state.single_redo_stack.append(state.single_undo_stack.pop())
            new_actor_list = []
            for data in state.single_undo_stack:
                if data[4] == slider.value():
                    new_actor_list = self.drwa_single_bounding_box(data)
            state.single_bounding_box_actor = new_actor_list
            viewer_xy.UpdateDisplayExtent()
            viewer_xy.Render()
            return

            try:
                for actor in state.single_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            try:
                for actor in state.last_bounding_box_actor:
                    viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
            try:
                for actor_group in state.multiple_bounding_box_actor:
                    for actor in actor_group:
                        viewer_xy.GetRenderer().RemoveActor(actor)
            except Exception:
                logger.warning('Close viewer_XY actor_paint Failed', exc_info=True)
        state.multiple_bounding_box_actor.clear()

        bounding_box_dict = state.multiple_boundingBox_dict
        if state.multiple_undo_stack:
            undo_point = state.multiple_undo_stack.pop()
            state.multiple_redo_stack.append(undo_point)
            slice_key = str(undo_point[4])
            if slice_key in bounding_box_dict:
                for idx, point in enumerate(bounding_box_dict[slice_key]["bounding_box"]):
                    if point == undo_point:
                        del bounding_box_dict[slice_key]["bounding_box"][idx]
                        break

        for data in state.multiple_undo_stack:
            if data[4] == slider.value():
                actor_list = self.drwa_single_bounding_box(data)
                state.multiple_bounding_box_actor.append(actor_list)
        viewer_xy.UpdateDisplayExtent()
        viewer_xy.Render()

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
        self.state_store.annotation.points_actor.append(actor)
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
