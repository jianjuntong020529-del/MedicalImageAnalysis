from typing import Any

from src.utils.state_store import get_state_store

_STATE = get_state_store()


# ---------------------------------------------------------------------------
# Paint view state
# ---------------------------------------------------------------------------
def setColorIndexList(index: int):
    _STATE.append_unique("paint", "color_index_list", index)


def getColorIndexList():
    return _STATE.get("paint", "color_index_list")


def clearColorIndexList():
    _STATE.clear_collection("paint", "color_index_list")


def setPaintActor(actor: Any):
    _STATE.append("paint", "actors", actor)


def getPaintActors():
    return _STATE.get("paint", "actors")


def clearPaintActors():
    _STATE.clear_collection("paint", "actors")


def setUndoStack(stack: Any):
    _STATE.append("paint", "undo_stack", stack)


def getUndoStack():
    return _STATE.get("paint", "undo_stack")


def clearUndoStack():
    _STATE.clear_collection("paint", "undo_stack")


def setRedoStack(stack: Any):
    _STATE.append("paint", "redo_stack", stack)


def getRedoStack():
    return _STATE.get("paint", "redo_stack")


def clearRedoStack():
    _STATE.clear_collection("paint", "redo_stack")


def setActors_paint(actor_paint: Any):
    _STATE.append("paint", "actors_paint", actor_paint)


def getActors_paint():
    return _STATE.get("paint", "actors_paint")


def clearActors_paint():
    _STATE.clear_collection("paint", "actors_paint")


def setLeftButtonDown(state: bool):
    _STATE.set("paint", "left_button_down", state)


def getLeftButtonDown():
    return _STATE.get("paint", "left_button_down")


# ---------------------------------------------------------------------------
# Click state
# ---------------------------------------------------------------------------
def get_left_down_is_clicked():
    return _STATE.get("click", "left_down_is_clicked")


def get_left_mid_is_clicked():
    return _STATE.get("click", "left_mid_is_clicked")


def get_left_up_is_clicked():
    return _STATE.get("click", "left_up_is_clicked")


def get_down_mid_is_clicked():
    return _STATE.get("click", "down_mid_is_clicked")


def get_up_mid_is_clicked():
    return _STATE.get("click", "up_mid_is_clicked")


def get_right_down_is_clicked():
    return _STATE.get("click", "right_down_is_clicked")


def get_right_mid_is_clicked():
    return _STATE.get("click", "right_mid_is_clicked")


def get_right_up_is_clicked():
    return _STATE.get("click", "right_up_is_clicked")


def get_mid_is_clicked():
    return _STATE.get("click", "mid_is_clicked")


def set_left_down_is_clicked(value: bool):
    _STATE.set("click", "left_down_is_clicked", value)


def set_left_mid_is_clicked(value: bool):
    _STATE.set("click", "left_mid_is_clicked", value)


def set_left_up_is_clicked(value: bool):
    _STATE.set("click", "left_up_is_clicked", value)


def set_down_mid_is_clicked(value: bool):
    _STATE.set("click", "down_mid_is_clicked", value)


def set_up_mid_is_clicked(value: bool):
    _STATE.set("click", "up_mid_is_clicked", value)


def set_right_down_is_clicked(value: bool):
    _STATE.set("click", "right_down_is_clicked", value)


def set_right_mid_is_clicked(value: bool):
    _STATE.set("click", "right_mid_is_clicked", value)


def set_right_up_is_clicked(value: bool):
    _STATE.set("click", "right_up_is_clicked", value)


def set_mid_is_clicked(value: bool):
    _STATE.set("click", "mid_is_clicked", value)


# ---------------------------------------------------------------------------
# ROI / annotation control
# ---------------------------------------------------------------------------
def setControlROIPoint(data: dict):
    _STATE.set("annotation", "control_roi_point", data)


def getControlROIPoint():
    return _STATE.get("annotation", "control_roi_point")


def clearControllerROIPoint():
    _STATE.set("annotation", "control_roi_point", {})


def setMultipleUndoStack(bounding_box: Any):
    _STATE.append("annotation", "multiple_undo_stack", bounding_box)


def getMultipleUndoStack():
    return _STATE.get("annotation", "multiple_undo_stack")


def clearMultipleUndoStack():
    _STATE.clear_collection("annotation", "multiple_undo_stack")


def setMultipleRedoStack(bounding_box: Any):
    _STATE.append("annotation", "multiple_redo_stack", bounding_box)


def getMultipleRedoStack():
    return _STATE.get("annotation", "multiple_redo_stack")


def clearMultipleRedoStack():
    _STATE.clear_collection("annotation", "multiple_redo_stack")


def setMultipleBoundingBoxDict(data: dict):
    _STATE.set("annotation", "multiple_boundingBox_dict", data)


def getMultipleBoundingBoxDict():
    return _STATE.get("annotation", "multiple_boundingBox_dict")


def clearMultipleBoundingBoxDict():
    _STATE.set("annotation", "multiple_boundingBox_dict", {})


def setSingleBoundingBoxDict(data: dict):
    _STATE.set("annotation", "single_boundingBox_dict", data)


def getSingleBoundingBoxDict():
    return _STATE.get("annotation", "single_boundingBox_dict")


def clearSingleBoundingBoxDict():
    _STATE.set("annotation", "single_boundingBox_dict", {})


def setSingleUndoStack(bounding_box: Any):
    _STATE.append("annotation", "single_undo_stack", bounding_box)


def getSingleUndoStack():
    return _STATE.get("annotation", "single_undo_stack")


def clearSingleUndoStack():
    _STATE.clear_collection("annotation", "single_undo_stack")


def setSingleRedoStack(bounding_box: Any):
    _STATE.append("annotation", "single_redo_stack", bounding_box)


def getSingleRedoStack():
    return _STATE.get("annotation", "single_redo_stack")


def clearSingleRedoStack():
    _STATE.clear_collection("annotation", "single_redo_stack")


def setPointsDict(data: dict):
    _STATE.set("annotation", "points_dict", data)


def getPointsDict():
    return _STATE.get("annotation", "points_dict")


def clearPointsDict():
    _STATE.set("annotation", "points_dict", {})


def setPointsActor(actor: Any):
    _STATE.append("annotation", "points_actor", actor)


def getPointsActor():
    return _STATE.get("annotation", "points_actor")


def clearPointsActor():
    _STATE.clear_collection("annotation", "points_actor")


def setPointsUndoStack(point: Any):
    _STATE.append("annotation", "points_undo_stack", point)


def getPointsUndoStack():
    return _STATE.get("annotation", "points_undo_stack")


def clearPointsUndoStack():
    _STATE.clear_collection("annotation", "points_undo_stack")


def setPointsRedoStack(point: Any):
    _STATE.append("annotation", "points_redo_stack", point)


def getPointsRedoStack():
    return _STATE.get("annotation", "points_redo_stack")


def clearPointsRedoStack():
    _STATE.clear_collection("annotation", "points_redo_stack")


def setLastBoundingBoxActor(actor: Any):
    _STATE.set("annotation", "last_bounding_box_actor", actor)


def getLastBoundingBoxActor():
    return _STATE.get("annotation", "last_bounding_box_actor")


def setSingleBoundingBoxActor(actor: Any):
    _STATE.set("annotation", "single_bounding_box_actor", actor)


def getSingleBoundingBoxActor():
    return _STATE.get("annotation", "single_bounding_box_actor")


def setMultipleBoundingBoxActor(actor: Any):
    _STATE.append("annotation", "multiple_bounding_box_actor", actor)


def getMultipleBoundingBoxActor():
    return _STATE.get("annotation", "multiple_bounding_box_actor")


def clearMultipleBoundingBoxActor():
    _STATE.clear_collection("annotation", "multiple_bounding_box_actor")


def setBoundingBoxOriginal(point: Any):
    _STATE.set("annotation", "box_points_original", point)


def getBoundingBoxOriginal():
    return _STATE.get("annotation", "box_points_original")


def setSingleBoundingBox(point: Any):
    _STATE.set("annotation", "single_bounding_box", point)


def getSingleBoundingBox():
    return _STATE.get("annotation", "single_bounding_box")


def setSelectSingleBoxLabel(label: bool):
    _STATE.set("annotation", "select_single_box_label", label)


def getSelectSingleBoxLabel():
    return _STATE.get("annotation", "select_single_box_label")


def setPointPosition(position: Any):
    _STATE.set("annotation", "point_position", position)


def getPointPosition():
    return _STATE.get("annotation", "point_position")


def setSelectPointLabel1(label: bool):
    _STATE.set("annotation", "select_point_label_1", label)


def getSelectPointLabel1():
    return _STATE.get("annotation", "select_point_label_1")


# ---------------------------------------------------------------------------
# Polyline / measurement helpers
# ---------------------------------------------------------------------------
def setState_PolyTrue():
    _STATE.set("measurement", "state_poly", True)


def setState_PolyFalse():
    _STATE.set("measurement", "state_poly", False)


def getState_Poly():
    return _STATE.get("measurement", "state_poly")


def setStart_Poly_Point(start):
    _STATE.set("measurement", "start_poly_point", start)


def getStart_Poly_Point():
    return _STATE.get("measurement", "start_poly_point")


def setEnd_Poly_Point(end):
    _STATE.set("measurement", "end_poly_point", end)


def getEnd_Poly_Point():
    return _STATE.get("measurement", "end_poly_point")


def setFourPoints(point):
    _STATE.append("measurement", "fourPoints", point)


def getFourPoints():
    return _STATE.get("measurement", "fourPoints")


def setLong(num1: int):
    _STATE.set("measurement", "long", num1)


def getLong():
    return _STATE.get("measurement", "long")


def setWidth(num2: int):
    _STATE.set("measurement", "width", num2)


def getWidth():
    return _STATE.get("measurement", "width")


def setState2True():
    _STATE.set("measurement", "state2", True)


def setState2False():
    _STATE.set("measurement", "state2", False)


def getState2():
    return _STATE.get("measurement", "state2")


def setStartPoint(start):
    _STATE.set("measurement", "startPoint", start)


def getStartPoint():
    return _STATE.get("measurement", "startPoint")


def setEndPoint(end):
    _STATE.set("measurement", "endPoint", end)


def getEndPoint():
    return _STATE.get("measurement", "endPoint")


# ---------------------------------------------------------------------------
# Slice helpers
# ---------------------------------------------------------------------------
def setSliceXY(number: int):
    _STATE.set("slice", "slice_xy", number)
    print("set")
    print(_STATE.get("slice", "slice_xy"))


def getSliceXY():
    value = _STATE.get("slice", "slice_xy")
    print("get")
    print(value)
    return value


def addSliceXY():
    _STATE.increment("slice", "slice_xy", 1)


def minSliceXY():
    _STATE.increment("slice", "slice_xy", -1)


def setSliceYZ(number: int):
    _STATE.set("slice", "slice_yz", number)


def getSliceYZ():
    return _STATE.get("slice", "slice_yz")


def addSliceYZ():
    _STATE.increment("slice", "slice_yz", 1)


def minSliceYZ():
    _STATE.increment("slice", "slice_yz", -1)


def setSliceXZ(number: int):
    _STATE.set("slice", "slice_xz", number)


def getSliceXZ():
    return _STATE.get("slice", "slice_xz")


def addSliceXZ():
    _STATE.increment("slice", "slice_xz", 1)


def minSliceXZ():
    _STATE.increment("slice", "slice_xz", -1)


# ---------------------------------------------------------------------------
# File level state
# ---------------------------------------------------------------------------
def autoReset():
    _STATE.set("file", "dirpath", "")


def getDirPath():
    return _STATE.get("file", "dirpath")


def setDirPath(path: str):
    _STATE.set("file", "dirpath", path)


def getNumber():
    return _STATE.get("file", "count")


def setNumber():
    _STATE.increment("file", "count", 1)


def setState():
    _STATE.set("file", "state", True)


def getState():
    return _STATE.get("file", "state")


def getFileIsEmpty():
    return _STATE.get("file", "file_is_empty")


def setFileIsEmpty(value: bool):
    _STATE.set("file", "file_is_empty", value)


# ---------------------------------------------------------------------------
# Implant / dental arch state
# ---------------------------------------------------------------------------
def getIsPutImplant():
    return _STATE.get("implant", "is_put_implant")


def setIsPutImplant(value: bool):
    _STATE.set("implant", "is_put_implant", value)


def getIsAdjust():
    return _STATE.get("implant", "is_adjust")


def setIsAdjust(value: bool):
    _STATE.set("implant", "is_adjust", value)


def getIsGenerateImplant():
    return _STATE.get("implant", "is_generate_implant")


def setIsGenerateImplant(value: bool):
    _STATE.set("implant", "is_generate_implant", value)


def getAnchorPointIsComplete():
    return _STATE.get("implant", "anchor_point_is_complete")


def setAnchorPointIsComplete(value: bool):
    _STATE.set("implant", "anchor_point_is_complete", value)


def getDentalArchCurvePoint():
    return _STATE.get("implant", "dental_arch_curve_points")


def setDentalArchCurvePoint(point: Any):
    _STATE.append("implant", "dental_arch_curve_points", point)


def setDentalArchThickness(value: str):
    _STATE.set("implant", "dental_arch_thickness", value)


def getDentalArchThickness():
    return _STATE.get("implant", "dental_arch_thickness")


def setDicomPoints(point: Any):
    _STATE.append("implant", "dicom_points", point)


def getDicomPoint():
    return _STATE.get("implant", "dicom_points")


def setControlPoints(point: Any):
    _STATE.append("implant", "control_points", point)


def getControlPoints():
    return _STATE.get("implant", "control_points")


def setPaintPoint(point: Any):
    _STATE.append("implant", "paint_points", point)


def getPaintPoint():
    return _STATE.get("implant", "paint_points")


def setSamplePoint(point: Any):
    _STATE.append("implant", "sample_points", point)


def getSamplePoint():
    return _STATE.get("implant", "sample_points")