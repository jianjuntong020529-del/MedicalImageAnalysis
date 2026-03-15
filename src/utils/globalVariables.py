# 数据加载路劲
dirpath = " "
count = 1
state = False
startPoint = ()
endPoint = ()
start_poly_point=()
end_poly_point=()
state_poly=False
state2 = False  # 检测鼠标移动是否实在鼠标点击之后
long = 0
width = 0
fourPoints = []
slice_xy = 0
slice_yz = 0
slice_xz = 0
actors_paint = []
file_is_empty = True
is_put_implant = False
is_generate_implant = False
is_adjust = False
anchor_point_is_complete = False
dental_arch_curve_points = []
dental_arch_thickness = "80"
dicom_points = []
control_points = []
paint_points = []
sample_points = []
point_position = []
select_point_label_1 = True
select_single_box_label = True
left_button_down = False
single_bounding_box = []
multiple_bounding_box = []
multiple_bounding_box_original = []
box_points_original = []
single_bounding_box_actor = []
multiple_bounding_box_actor = []
last_bounding_box_actor = []
points_actor = []
points_undo_stack = []
points_redo_stack = []
points_dict = {}
single_undo_stack = []
single_redo_stack = []
single_boudingBox_dict = {}
multiple_undo_stack = []
multiple_redo_stack = []
multiple_boundingBox_dict ={}
control_roi_point = {}

left_down_is_clicked = False
left_mid_is_clicked = False
left_up_is_clicked = False
down_mid_is_clicked = False
up_mid_is_clicked = False
right_down_is_clicked = False
right_mid_is_clicked = False
right_up_is_clicked = False
mid_is_clicked = False


actors = []
undo_stack = []
redo_stack = []
color_index_list = []

def setColorIndexList(index):
    global color_index_list
    if index not in color_index_list:
        color_index_list.append(index)

def getColorIndexList():
    global color_index_list
    return color_index_list

def clearColorIndexList():
    global color_index_list
    color_index_list = []

def setPaintActor(actor):
    global actors
    actors.append(actor)

def getPaintActors():
    global actors
    return actors

def clearPaintActors():
    global actors
    actors = []
def setUndoStack(stack):
    global undo_stack
    undo_stack.append(stack)

def getUndoStack():
    global undo_stack
    return undo_stack

def clearUndoStack():
    global undo_stack
    undo_stack = []

def setRedoStack(stack):
    global redo_stack
    redo_stack.append(stack)

def getRedoStack():
    global redo_stack
    return redo_stack


def get_left_down_is_clicked():
    global left_down_is_clicked
    return left_down_is_clicked


def get_left_mid_is_clicked():
    global left_mid_is_clicked
    return left_mid_is_clicked


def get_left_up_is_clicked():
    global left_up_is_clicked
    return left_up_is_clicked


def get_down_mid_is_clicked():
    global down_mid_is_clicked
    return down_mid_is_clicked


def get_up_mid_is_clicked():
    global up_mid_is_clicked
    return up_mid_is_clicked


def get_right_down_is_clicked():
    global right_down_is_clicked
    return right_down_is_clicked


def get_right_mid_is_clicked():
    global right_mid_is_clicked
    return right_mid_is_clicked


def get_right_up_is_clicked():
    global right_up_is_clicked
    return right_up_is_clicked


def get_mid_is_clicked():
    global mid_is_clicked
    return mid_is_clicked




def set_left_down_is_clicked(value):
    global left_down_is_clicked
    left_down_is_clicked = value


def set_left_mid_is_clicked(value):
    global left_mid_is_clicked
    left_mid_is_clicked = value


def set_left_up_is_clicked(value):
    global left_up_is_clicked
    left_up_is_clicked = value


def set_down_mid_is_clicked(value):
    global down_mid_is_clicked
    down_mid_is_clicked = value


def set_up_mid_is_clicked(value):
    global up_mid_is_clicked
    up_mid_is_clicked = value


def set_right_down_is_clicked(value):
    global right_down_is_clicked
    right_down_is_clicked = value


def set_right_mid_is_clicked(value):
    global right_mid_is_clicked
    right_mid_is_clicked = value


def set_right_up_is_clicked(value):
    global right_up_is_clicked
    right_up_is_clicked = value


def set_mid_is_clicked(value):
    global mid_is_clicked
    mid_is_clicked = value

def setControlROIPoint(dict):
    global control_roi_point
    control_roi_point = dict

def getControlROIPoint():
    global control_roi_point
    return control_roi_point

def clearControllerROIPoint():
    global control_roi_point
    control_roi_point.clear()
    control_roi_point = {}

def setMultipleUndoStack(bounding_box):
    global multiple_undo_stack
    multiple_undo_stack.append(bounding_box)

def getMultipleUndoStack():
    global multiple_undo_stack
    return multiple_undo_stack

def clearMultipleUndoStack():
    global multiple_undo_stack
    multiple_undo_stack.clear()
    multiple_undo_stack = []

def setMultipleRedoStack(bounding_box):
    global multiple_redo_stack
    multiple_redo_stack.append(bounding_box)

def getMultipleRedoStack():
    global multiple_redo_stack
    return multiple_redo_stack

def clearMultipleRedoStack():
    global multiple_redo_stack
    multiple_redo_stack.clear()
    multiple_redo_stack = []

def setMultipleBoundingBoxDict(dict):
    global multiple_boundingBox_dict
    multiple_boundingBox_dict = dict

def getMultipleBoundingBoxDict():
    global multiple_boundingBox_dict
    return multiple_boundingBox_dict

def clearMultipleBoundingBoxDict():
    global multiple_boundingBox_dict
    multiple_boundingBox_dict.clear()
    multiple_boundingBox_dict = {}

def setSingleBoundingBoxDict(dict):
    global single_boudingBox_dict
    single_boudingBox_dict = dict

def getSingleBoundingBoxDict():
    global single_boudingBox_dict
    return single_boudingBox_dict

def clearSingleBoundingBoxDict():
    global single_boudingBox_dict
    single_boudingBox_dict.clear()
    single_boudingBox_dict = {}

def setSingleUndoStack(bounding_box):
    global single_undo_stack
    single_undo_stack.append(bounding_box)

def getSingleUndoStack():
    global single_undo_stack
    return single_undo_stack

def clearSingleUndoStack():
    global single_undo_stack
    single_undo_stack.clear()
    single_undo_stack = []

def setSingleRedoStack(bounding_box):
    global single_redo_stack
    single_redo_stack.append(bounding_box)

def getSingleRedoStack():
    global single_redo_stack
    return single_redo_stack

def clearSingleRedoStack():
    global single_redo_stack
    single_redo_stack.clear()
    single_redo_stack = []

def setPointsDict(dict):
    global points_dict
    points_dict = dict

def getPointsDict():
    global points_dict
    return points_dict

def clearPointsDict():
    global points_dict
    points_dict.clear()
    points_dict = {}

def setPointsActor(actor):
    global points_actor
    points_actor.append(actor)

def getPointsActor():
    global points_actor
    return points_actor

def clearPointsActor():
    global points_actor
    points_actor.clear()
    points_actor = []

def setPointsUndoStack(point):
    global points_undo_stack
    points_undo_stack.append(point)

def getPointsUndoStack():
    global points_undo_stack
    return points_undo_stack

def clearPointsUndoStack():
    global points_undo_stack
    points_undo_stack.clear()
    points_undo_stack = []

def setPointsRedoStack(point):
    global points_redo_stack
    points_redo_stack.append(point)

def getPointsRedoStack():
    global points_redo_stack
    return points_redo_stack

def clearPointsRedoStack():
    global points_redo_stack
    points_redo_stack.clear()
    points_redo_stack = []

def setLastBoundingBoxActor(actor):
    global last_bounding_box_actor
    last_bounding_box_actor = actor

def getLastBoundingBoxActor():
    global last_bounding_box_actor
    return last_bounding_box_actor

def setSingleBoundingBoxActor(actor):
    global single_bounding_box_actor
    single_bounding_box_actor = actor

def getSingleBoundingBoxActor():
    global single_bounding_box_actor
    return single_bounding_box_actor

def setMultipleBoundingBoxActor(actor):
    global multiple_bounding_box_actor
    multiple_bounding_box_actor.append(actor)

def getMultipleBoundingBoxActor():
    global multiple_bounding_box_actor
    return multiple_bounding_box_actor

def clearMultipleBoundingBoxActor():
    global multiple_bounding_box_actor
    multiple_bounding_box_actor.clear()
    multiple_bounding_box_actor = []

def setBoundingBoxOriginal(point):
    global box_points_original
    box_points_original = point

def getBoundingBoxOriginal():
    global box_points_original
    return box_points_original

def setSingleBoundingBox(point):
    global single_bounding_box
    single_bounding_box = point

def getSingleBoundingBox():
    global single_bounding_box
    return single_bounding_box

def setLeftButtonDown(state):
    global left_button_down
    left_button_down = state

def getLeftButtonDown():
    global left_button_down
    return left_button_down

def setSelectSingleBoxLabel(label):
    global select_single_box_label
    select_single_box_label = label

def getSelectSingleBoxLabel():
    global select_single_box_label
    return select_single_box_label

def setPointPosition(positon):
    global point_position
    point_position = positon

def getPointPosition():
    global point_position
    return point_position

def setSelectPointLabel1(label):
    global select_point_label_1
    select_point_label_1 = label

def getSelectPointLabel1():
    global select_point_label_1
    return select_point_label_1

def setState_PolyTrue():
    global state_poly
    state_poly = True


def setState_PolyFalse():
    global state_poly
    state_poly = False


def getState_Poly():
    global state_poly
    return state_poly


def setStart_Poly_Point(start):
    global start_poly_point
    start_poly_point = start


def getStart_Poly_Point():
    global start_poly_point
    return start_poly_point


def setEnd_Poly_Point(end):
    global end_poly_point
    end_poly_point = end


def getEnd_Poly_Point():
    global end_poly_point
    return end_poly_point

def setActors_paint(actor_paint):
    global actors_paint
    actors_paint.append(actor_paint)


def getActors_paint():
    global actors_paint
    return actors_paint


def setSliceXY(number):
    global slice_xy
    slice_xy = number
    print("set")
    print(slice_xy)


def getSliceXY():
    global slice_xy
    print("get")
    print(slice_xy)
    return slice_xy


def addSliceXY():
    global slice_xy
    slice_xy += 1


def minSliceXY():
    global slice_xy
    slice_xy -= 1


def setSliceYZ(number):
    global slice_yz
    slice_yz = number


def getSliceYZ():
    global slice_yz
    return slice_yz


def addSliceYZ():
    global slice_yz
    slice_yz += 1


def minSliceYZ():
    global slice_yz
    slice_yz -= 1


def setSliceXZ(number):
    global slice_xz
    slice_xz = number


def getSliceXZ():
    global slice_xz
    return slice_xz


def addSliceXZ():
    global slice_xz
    slice_xz += 1


def minSliceXZ():
    global slice_xz
    slice_xz -= 1


def setFourPoints(point):
    global fourPoints
    fourPoints.append(point)


def getFourPoints():
    global fourPoints
    return fourPoints


def setLong(num1):
    global long
    long = num1


def getLong():
    global long
    return long


def setWidth(num2):
    global width
    width = num2


def getWidth():
    global width
    return width


def setState2True():
    global state2
    state2 = True


def setState2False():
    global state2
    state2 = False


def getState2():
    global state2
    return state2

def setStartPoint(start):
    global startPoint
    startPoint = start


def getStartPoint():
    global startPoint
    return startPoint


def setEndPoint(end):
    global endPoint
    endPoint = end


def getEndPoint():
    global endPoint
    return endPoint


def autoReset():
    global dirpath
    dirpath = ""


def getDirPath():
    global dirpath
    return dirpath


def setDirPath(s):
    global dirpath
    dirpath = s


def getNumber():
    global count
    return count


def setNumber():
    global count
    count += 1


def setState():
    global state
    state = True


def getState():
    global state
    return state

def getFileIsEmpty():
    global file_is_empty
    return  file_is_empty

def setFileIsEmpty(s):
    global  file_is_empty
    file_is_empty = s

def getIsPutImplant():
    global is_put_implant
    return is_put_implant

def setIsPutImplant(s):
    global is_put_implant
    is_put_implant = s

def getIsAdjust():
    global is_adjust
    return is_adjust

def setIsAdjust(s):
    global is_adjust
    is_adjust = s

def getIsGenerateImplant():
    global is_generate_implant
    return  is_generate_implant

def setIsGenerateImplant(s):
    global is_generate_implant
    is_generate_implant = s

def getAnchorPointIsComplete():
    global anchor_point_is_complete
    return anchor_point_is_complete

def setAnchorPointIsComplete(s):
    global anchor_point_is_complete
    anchor_point_is_complete = s

def getDentalArchCurvePoint():
    global dental_arch_curve_points
    return dental_arch_curve_points

def setDentalArchCurvePoint(point):
    global dental_arch_curve_points
    dental_arch_curve_points.append(point)

def setDentalArchThickness(s):
    global dental_arch_thickness
    dental_arch_thickness = s

def getDentalArchThickness():
    global dental_arch_thickness
    return dental_arch_thickness

def setDicomPoints(point):
    global dicom_points
    dicom_points.append(point)

def getDicomPoint():
    global dicom_points
    return dicom_points

def setControlPoints(point):
    global control_points
    control_points.append(point)

def getControlPoints():
    global control_points
    return control_points

def setPaintPoint(point):
    global paint_points
    paint_points.append(point)

def getPaintPoint():
    global paint_points
    return paint_points

def setSamplePoint(point):
    global sample_points
    sample_points.append(point)

def getSamplePoint():
    global sample_points
    return sample_points