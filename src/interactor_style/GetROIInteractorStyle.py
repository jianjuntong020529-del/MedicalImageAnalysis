import vtk

from src.utils.globalVariables import *


class MouseMoveEvent_GetROI():
    def __init__(self, picker, viewer_xy, viewer_yz, viewer_xz, type):
        self.picker = picker  # 坐标拾取
        self.view_xy = viewer_xy
        self.view_yz = viewer_yz
        self.view_xz = viewer_xz
        self.actor_xy = self.view_xy.GetImageActor()
        self.actor_yz = self.view_yz.GetImageActor()
        self.actor_xz = self.view_xz.GetImageActor()
        self.iren_xy = self.view_xy.GetRenderWindow().GetInteractor()
        self.iren_yz = self.view_yz.GetRenderWindow().GetInteractor()
        self.iren_xz = self.view_xz.GetRenderWindow().GetInteractor()
        self.render_xy = self.view_xy.GetRenderer()
        self.render_yz = self.view_yz.GetRenderer()
        self.render_xz = self.view_xz.GetRenderer()
        self.origin_xy = self.view_xy.GetInput().GetOrigin()
        self.origin_yz = self.view_yz.GetInput().GetOrigin()
        self.origin_xz = self.view_xz.GetInput().GetOrigin()
        self.spacing_xy = self.view_xy.GetInput().GetSpacing()
        self.spacing_yz = self.view_yz.GetInput().GetSpacing()
        self.spacing_xz = self.view_xz.GetInput().GetSpacing()
        self.ren_xy = self.view_xy.GetRenderer()
        self.ren_yz = self.view_yz.GetRenderer()
        self.ren_xz = self.view_xz.GetRenderer()
        self.imageshape = self.view_xy.GetInput().GetDimensions()
        self.temp_actor = None
        self.type = type
        self.radius_xy = (3 - self.origin_xy[0]) / self.spacing_xy[0]

    def __call__(self, caller, ev):
        roi_dict = getControlROIPoint()
        if self.type == "view_xy":
            self.picker.AddPickList(self.actor_xy)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_xy.GetEventPosition()[0], self.iren_xy.GetEventPosition()[1], 0, self.render_xy)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_xy[i])) / self.spacing_xy[i] for i in range(3)]
            if self.start_pos[0] < 0 or self.start_pos[0] > self.imageshape[0] or self.start_pos[1] < 0 or \
                    self.start_pos[1] > self.imageshape[1]:
                return
        elif self.type == "view_yz":
            self.picker.AddPickList(self.actor_yz)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_yz.GetEventPosition()[0], self.iren_yz.GetEventPosition()[1], 0, self.render_yz)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_yz[i])) / self.spacing_yz[i] for i in range(3)]
            if self.start_pos[1] < 0 or self.start_pos[1] > self.imageshape[1] or self.start_pos[2] < 0 or \
                    self.start_pos[2] > self.imageshape[2]:
                return
        elif self.type == "view_xz":
            self.picker.AddPickList(self.actor_xz)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_xz.GetEventPosition()[0], self.iren_xz.GetEventPosition()[1], 0, self.render_xz)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_xz[i])) / self.spacing_xz[i] for i in range(3)]
            if self.start_pos[0] < 0 or self.start_pos[0] > self.imageshape[0] or self.start_pos[2] < 0 or \
                    self.start_pos[2] > self.imageshape[2]:
                return

        self.update_rectangle_position(roi_dict, self.type)

    def is_point_inside_circle(self, circle_center, point, radius=3):
        if self.type == "view_xy":
            cx, cy = circle_center
            cx = cx * self.spacing_xy[0] + self.origin_xy[0]
            cy = cy * self.spacing_xy[1] + self.origin_xy[1]
            c1 = cx
            c2 = cy
        elif self.type == "view_yz":
            cy, cz = circle_center
            cy = cy * self.spacing_yz[1] + self.origin_yz[1]
            cz = cz * self.spacing_yz[2] + self.origin_yz[2]
            c1 = cy
            c2 = cz
        else:
            cx, cz = circle_center
            cx = cx * self.spacing_xz[0] + self.origin_xz[0]
            cz = cz * self.spacing_xz[2] + self.origin_xz[2]
            c1 = cx
            c2 = cz
        px, py = point
        if (-radius <= px - c1 <= radius) and (-radius <= py - c2 <= radius):
            return True
        return False

    def update_rectangle_position(self, roi_dict, type):
        if type == "view_xy":
            if get_left_down_is_clicked():
                #  这里还要判断移动的点与固定的点的位置  然后进行位置更新
                end_point_x = roi_dict[type]["right_up_point"]["point"][0]
                end_point_y = roi_dict[type]["right_up_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][0]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][1]
                roi_dict[type]["left_down_point"]["point"] = [self.start_pos[0], self.start_pos[1],
                                                              self.imageshape[2] + 1]
                roi_dict[type]["left_up_point"]["point"] = [self.start_pos[0], end_point_y, self.imageshape[2] + 1]
                roi_dict[type]["right_down_point"]["point"] = [end_point_x, self.start_pos[1], self.imageshape[2] + 1]

                roi_dict[type]["left_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["right_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                # 更新XZ视图
                roi_dict["view_xz"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2
                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_mid_is_clicked():
                end_point_x = roi_dict[type]["left_mid_point"]["point"][0]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - end_point_x
                roi_dict[type]["left_down_point"]["point"][0] += dx
                roi_dict[type]["left_up_point"]["point"][0] += dx
                roi_dict[type]["left_mid_point"]["point"][0] += dx
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_xz"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_up_is_clicked():
                end_point_x = roi_dict[type]["right_down_point"]["point"][0]
                end_point_y = roi_dict[type]["right_down_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    0]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    1]
                roi_dict[type]["left_up_point"]["point"] = [self.start_pos[0], self.start_pos[1],
                                                            self.imageshape[2] + 1]
                roi_dict[type]["left_down_point"]["point"] = [self.start_pos[0], end_point_y, self.imageshape[2] + 1]
                roi_dict[type]["right_up_point"]["point"] = [end_point_x, self.start_pos[1], self.imageshape[2] + 1]
                roi_dict[type]["left_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["right_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_up_mid_is_clicked():
                end_point_y = roi_dict[type]["up_mid_point"]["point"][1]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                roi_dict[type]["up_mid_point"]["point"][1] += dy
                roi_dict[type]["left_up_point"]["point"][1] += dy
                roi_dict[type]["right_up_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_yz"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)


            elif get_down_mid_is_clicked():
                end_point_y = roi_dict[type]["down_mid_point"]["point"][1]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                roi_dict[type]["down_mid_point"]["point"][1] += dy
                roi_dict[type]["left_down_point"]["point"][1] += dy
                roi_dict[type]["right_down_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_yz"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_down_is_clicked():
                end_point_x = roi_dict[type]["left_up_point"]["point"][0]
                end_point_y = roi_dict[type]["left_up_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][0]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][1]
                roi_dict[type]["right_down_point"]["point"] = [self.start_pos[0], self.start_pos[1],
                                                               self.imageshape[2] + 1]
                roi_dict[type]["right_up_point"]["point"] = [self.start_pos[0], end_point_y, self.imageshape[2] + 1]
                roi_dict[type]["left_down_point"]["point"] = [end_point_x, self.start_pos[1], self.imageshape[2] + 1]
                roi_dict[type]["right_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["left_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["right_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["right_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["left_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_mid_is_clicked():
                end_point_x = roi_dict[type]["right_mid_point"]["point"][0]
                dx = end_point_x - max(0, min(self.start_pos[0], self.imageshape[0] - 1))
                roi_dict[type]["right_down_point"]["point"][0] -= dx
                roi_dict[type]["right_up_point"]["point"][0] -= dx
                roi_dict[type]["right_mid_point"]["point"][0] -= dx
                roi_dict[type]["down_mid_point"]["point"][0] -= dx / 2
                roi_dict[type]["up_mid_point"]["point"][0] -= dx / 2
                roi_dict[type]["mid_point"]["point"][0] -= dx / 2

                roi_dict["view_xz"]["right_down_point"]["point"][0] -= dx
                roi_dict["view_xz"]["right_up_point"]["point"][0] -= dx
                roi_dict["view_xz"]["right_mid_point"]["point"][0] -= dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] -= dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] -= dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] -= dx / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_up_is_clicked():
                end_point_x = roi_dict[type]["left_down_point"]["point"][0]
                end_point_y = roi_dict[type]["left_down_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    0]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    1]
                roi_dict[type]["right_up_point"]["point"] = [self.start_pos[0], self.start_pos[1],
                                                             self.imageshape[2] + 1]
                roi_dict[type]["right_down_point"]["point"] = [self.start_pos[0], end_point_y, self.imageshape[2] + 1]
                roi_dict[type]["left_up_point"]["point"] = [end_point_x, self.start_pos[1], self.imageshape[2] + 1]
                roi_dict[type]["right_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["right_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["left_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["left_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_xz"]["right_down_point"]["point"][0] += dx
                roi_dict["view_xz"]["right_up_point"]["point"][0] += dx
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_down_point"]["point"][1] += dy
                roi_dict["view_yz"]["right_up_point"]["point"][1] += dy
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy / 2
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_mid_is_clicked():
                end_point_x = roi_dict[type]["mid_point"]["point"][0]
                end_point_y = roi_dict[type]["mid_point"]["point"][1]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - end_point_x
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                roi_dict[type]["mid_point"]["point"] = [self.start_pos[0], self.start_pos[1], self.imageshape[2] + 1]
                roi_dict[type]["right_down_point"]["point"][0] += dx
                roi_dict[type]["right_down_point"]["point"][1] += dy
                roi_dict[type]["right_mid_point"]["point"][0] += dx
                roi_dict[type]["right_mid_point"]["point"][1] += dy
                roi_dict[type]["down_mid_point"]["point"][0] += dx
                roi_dict[type]["down_mid_point"]["point"][1] += dy
                roi_dict[type]["up_mid_point"]["point"][0] += dx
                roi_dict[type]["up_mid_point"]["point"][1] += dy
                roi_dict[type]["left_up_point"]["point"][0] += dx
                roi_dict[type]["left_up_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][0] += dx
                roi_dict[type]["left_mid_point"]["point"][1] += dy
                roi_dict[type]["left_down_point"]["point"][0] += dx
                roi_dict[type]["left_down_point"]["point"][1] += dy
                roi_dict[type]["right_up_point"]["point"][0] += dx
                roi_dict[type]["right_up_point"]["point"][1] += dy

                roi_dict["view_xz"]["right_down_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["down_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["down_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["up_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["up_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_up_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_up_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_down_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_up_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_up_point"]["point"][1] += dy
                roi_dict["view_xz"]["mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["mid_point"]["point"][1] += dy

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
        elif type == "view_yz":
            if get_left_down_is_clicked():
                end_point_y = roi_dict[type]["right_up_point"]["point"][1]
                end_point_z = roi_dict[type]["right_up_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][1]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][2]

                roi_dict[type]["left_down_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1],
                                                              self.start_pos[2]]
                roi_dict[type]["left_up_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], end_point_z]
                roi_dict[type]["right_down_point"]["point"] = [self.imageshape[0] + 1, end_point_y, self.start_pos[2]]
                roi_dict[type]["left_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["right_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["down_mid_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2
                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_mid_is_clicked():
                end_point_y = roi_dict[type]["left_mid_point"]["point"][1]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                roi_dict[type]["left_down_point"]["point"][1] += dy
                roi_dict[type]["left_up_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][1] += dy
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["down_mid_point"]["point"][1] += dy

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_up_is_clicked():
                end_point_y = roi_dict[type]["right_down_point"]["point"][1]
                end_point_z = roi_dict[type]["right_down_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    1]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    2]
                roi_dict[type]["left_up_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1],
                                                            self.start_pos[2]]
                roi_dict[type]["left_down_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], end_point_z]
                roi_dict[type]["right_up_point"]["point"] = [self.imageshape[0] + 1, end_point_y, self.start_pos[2]]
                roi_dict[type]["left_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["right_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xy"]["down_mid_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_up_mid_is_clicked():
                end_point_z = roi_dict[type]["up_mid_point"]["point"][2]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["up_mid_point"]["point"][2] += dz
                roi_dict[type]["left_up_point"]["point"][2] += dz
                roi_dict[type]["right_up_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_down_mid_is_clicked():
                end_point_z = roi_dict[type]["down_mid_point"]["point"][2]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["down_mid_point"]["point"][2] += dz
                roi_dict[type]["left_down_point"]["point"][2] += dz
                roi_dict[type]["right_down_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_down_is_clicked():
                end_point_y = roi_dict[type]["left_up_point"]["point"][1]
                end_point_z = roi_dict[type]["left_up_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][1]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][2]
                roi_dict[type]["right_down_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1],
                                                               self.start_pos[2]]
                roi_dict[type]["right_up_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], end_point_z]
                roi_dict[type]["left_down_point"]["point"] = [self.imageshape[0] + 1, end_point_y, self.start_pos[2]]
                roi_dict[type]["right_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["left_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["right_up_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_up_point"]["point"][1] += dy
                roi_dict["view_xy"]["up_mid_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_mid_is_clicked():
                end_point_y = roi_dict[type]["right_mid_point"]["point"][1]
                dy = end_point_y - max(0, min(self.start_pos[1], self.imageshape[1] - 1))
                roi_dict[type]["right_down_point"]["point"][1] -= dy
                roi_dict[type]["right_up_point"]["point"][1] -= dy
                roi_dict[type]["right_mid_point"]["point"][1] -= dy
                roi_dict[type]["down_mid_point"]["point"][1] -= dy / 2
                roi_dict[type]["up_mid_point"]["point"][1] -= dy / 2
                roi_dict[type]["mid_point"]["point"][1] -= dy / 2

                roi_dict["view_xy"]["left_up_point"]["point"][1] -= dy
                roi_dict["view_xy"]["right_up_point"]["point"][1] -= dy
                roi_dict["view_xy"]["up_mid_point"]["point"][1] -= dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] -= dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] -= dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] -= dy / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_up_is_clicked():
                end_point_y = roi_dict[type]["left_down_point"]["point"][1]
                end_point_z = roi_dict[type]["left_down_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    1]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    2]
                roi_dict[type]["right_up_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1],
                                                             self.start_pos[2]]
                roi_dict[type]["right_down_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], end_point_z]
                roi_dict[type]["left_up_point"]["point"] = [self.imageshape[0] + 1, end_point_y, self.start_pos[2]]
                roi_dict[type]["right_mid_point"]["point"][1] = self.start_pos[1]
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["down_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["up_mid_point"]["point"][1] += dy / 2
                roi_dict[type]["up_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["left_mid_point"]["point"][1] = end_point_y
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][1] += dy / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["left_up_point"]["point"][1] += dy
                roi_dict["view_xy"]["right_up_point"]["point"][1] += dy
                roi_dict["view_xy"]["up_mid_point"]["point"][1] += dy
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy / 2
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy / 2

                roi_dict["view_xz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_mid_is_clicked():
                end_point_y = roi_dict[type]["mid_point"]["point"][1]
                end_point_z = roi_dict[type]["mid_point"]["point"][2]
                dy = max(0, min(self.start_pos[1], self.imageshape[1] - 1)) - end_point_y
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["mid_point"]["point"] = [self.imageshape[0] + 1, self.start_pos[1], self.start_pos[2]]
                roi_dict[type]["right_down_point"]["point"][1] += dy
                roi_dict[type]["right_down_point"]["point"][2] += dz
                roi_dict[type]["right_mid_point"]["point"][1] += dy
                roi_dict[type]["right_mid_point"]["point"][2] += dz
                roi_dict[type]["down_mid_point"]["point"][1] += dy
                roi_dict[type]["down_mid_point"]["point"][2] += dz
                roi_dict[type]["up_mid_point"]["point"][1] += dy
                roi_dict[type]["up_mid_point"]["point"][2] += dz
                roi_dict[type]["left_up_point"]["point"][1] += dy
                roi_dict[type]["left_up_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][1] += dy
                roi_dict[type]["left_mid_point"]["point"][2] += dz
                roi_dict[type]["left_down_point"]["point"][1] += dy
                roi_dict[type]["left_down_point"]["point"][2] += dz
                roi_dict[type]["right_up_point"]["point"][1] += dy
                roi_dict[type]["right_up_point"]["point"][2] += dz

                roi_dict["view_xy"]["right_down_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xy"]["right_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["down_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["up_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_up_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_down_point"]["point"][1] += dy
                roi_dict["view_xz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xy"]["right_up_point"]["point"][1] += dy
                roi_dict["view_xz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xy"]["mid_point"]["point"][1] += dy
                roi_dict["view_xz"]["mid_point"]["point"][2] += dz

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
        elif type == "view_xz":
            if get_left_down_is_clicked():
                end_point_x = roi_dict[type]["right_up_point"]["point"][0]
                end_point_z = roi_dict[type]["right_up_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - \
                     roi_dict[type]["left_down_point"]["point"][0]
                dz = max(0, min(self.start_pos[2], self.imageshape[2])) - \
                     roi_dict[type]["left_down_point"]["point"][2]
                roi_dict[type]["left_down_point"]["point"] = [self.start_pos[0], 0, self.start_pos[2]]
                roi_dict[type]["left_up_point"]["point"] = [self.start_pos[0], 0, end_point_z]
                roi_dict[type]["right_down_point"]["point"] = [end_point_x, 0, self.start_pos[2]]

                roi_dict[type]["left_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["right_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2
                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_mid_is_clicked():
                end_point_x = roi_dict[type]["left_mid_point"]["point"][0]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - end_point_x
                roi_dict[type]["left_down_point"]["point"][0] += dx
                roi_dict[type]["left_up_point"]["point"][0] += dx
                roi_dict[type]["left_mid_point"]["point"][0] += dx
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_xy"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_left_up_is_clicked():
                end_point_x = roi_dict[type]["right_down_point"]["point"][0]
                end_point_z = roi_dict[type]["right_down_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    0]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - roi_dict[type]["left_up_point"]["point"][
                    2]
                roi_dict[type]["left_up_point"]["point"] = [self.start_pos[0], 0,
                                                            self.start_pos[2]]
                roi_dict[type]["left_down_point"]["point"] = [self.start_pos[0], 0, end_point_z]
                roi_dict[type]["right_up_point"]["point"] = [end_point_x, 0, self.start_pos[2]]
                roi_dict[type]["left_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["right_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["left_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_up_mid_is_clicked():
                end_point_z = roi_dict[type]["up_mid_point"]["point"][2]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["up_mid_point"]["point"][2] += dz
                roi_dict[type]["left_up_point"]["point"][2] += dz
                roi_dict[type]["right_up_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_yz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_down_mid_is_clicked():
                end_point_z = roi_dict[type]["down_mid_point"]["point"][2]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["down_mid_point"]["point"][2] += dz
                roi_dict[type]["left_down_point"]["point"][2] += dz
                roi_dict[type]["right_down_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_yz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_down_is_clicked():
                end_point_x = roi_dict[type]["left_up_point"]["point"][0]
                end_point_z = roi_dict[type]["left_up_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][0]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - \
                     roi_dict[type]["right_down_point"]["point"][2]
                roi_dict[type]["right_down_point"]["point"] = [self.start_pos[0], 0, self.start_pos[2]]

                roi_dict[type]["right_up_point"]["point"] = [self.start_pos[0], 0, end_point_z]
                roi_dict[type]["left_down_point"]["point"] = [end_point_x, 0, self.start_pos[2]]
                roi_dict[type]["right_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["left_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["right_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["right_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_yz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_mid_is_clicked():
                end_point_x = roi_dict[type]["right_mid_point"]["point"][0]
                dx = end_point_x - max(0, min(self.start_pos[0], self.imageshape[0] - 1))
                roi_dict[type]["right_down_point"]["point"][0] -= dx
                roi_dict[type]["right_up_point"]["point"][0] -= dx
                roi_dict[type]["right_mid_point"]["point"][0] -= dx
                roi_dict[type]["down_mid_point"]["point"][0] -= dx / 2
                roi_dict[type]["up_mid_point"]["point"][0] -= dx / 2
                roi_dict[type]["mid_point"]["point"][0] -= dx / 2

                roi_dict["view_xy"]["right_down_point"]["point"][0] -= dx
                roi_dict["view_xy"]["right_up_point"]["point"][0] -= dx
                roi_dict["view_xy"]["right_mid_point"]["point"][0] -= dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] -= dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] -= dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] -= dx / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_right_up_is_clicked():
                end_point_x = roi_dict[type]["left_down_point"]["point"][0]
                end_point_z = roi_dict[type]["left_down_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    0]
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - roi_dict[type]["right_up_point"]["point"][
                    2]
                roi_dict[type]["right_up_point"]["point"] = [self.start_pos[0], 0, self.start_pos[2]]
                roi_dict[type]["right_down_point"]["point"] = [self.start_pos[0], 0, end_point_z]
                roi_dict[type]["left_up_point"]["point"] = [end_point_x, 0, self.start_pos[2]]
                roi_dict[type]["right_mid_point"]["point"][0] = self.start_pos[0]
                roi_dict[type]["right_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["down_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["down_mid_point"]["point"][2] = end_point_z
                roi_dict[type]["up_mid_point"]["point"][0] += dx / 2
                roi_dict[type]["up_mid_point"]["point"][2] = self.start_pos[2]
                roi_dict[type]["left_mid_point"]["point"][0] = end_point_x
                roi_dict[type]["left_mid_point"]["point"][2] += dz / 2
                roi_dict[type]["mid_point"]["point"][0] += dx / 2
                roi_dict[type]["mid_point"]["point"][2] += dz / 2

                roi_dict["view_xy"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_xy"]["right_down_point"]["point"][0] += dx
                roi_dict["view_xy"]["right_up_point"]["point"][0] += dx
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx / 2
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx / 2

                roi_dict["view_yz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_yz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz / 2
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz / 2

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)

            elif get_mid_is_clicked():
                end_point_x = roi_dict[type]["mid_point"]["point"][0]
                end_point_z = roi_dict[type]["mid_point"]["point"][2]
                dx = max(0, min(self.start_pos[0], self.imageshape[0] - 1)) - end_point_x
                dz = max(0, min(self.start_pos[2], self.imageshape[2] - 1)) - end_point_z
                roi_dict[type]["mid_point"]["point"] = [self.start_pos[0], 0, self.start_pos[2]]
                roi_dict[type]["right_down_point"]["point"][0] += dx
                roi_dict[type]["right_down_point"]["point"][2] += dz
                roi_dict[type]["right_mid_point"]["point"][0] += dx
                roi_dict[type]["right_mid_point"]["point"][2] += dz
                roi_dict[type]["down_mid_point"]["point"][0] += dx
                roi_dict[type]["down_mid_point"]["point"][2] += dz
                roi_dict[type]["up_mid_point"]["point"][0] += dx
                roi_dict[type]["up_mid_point"]["point"][2] += dz
                roi_dict[type]["left_up_point"]["point"][0] += dx
                roi_dict[type]["left_up_point"]["point"][2] += dz
                roi_dict[type]["left_mid_point"]["point"][0] += dx
                roi_dict[type]["left_mid_point"]["point"][2] += dz
                roi_dict[type]["left_down_point"]["point"][0] += dx
                roi_dict[type]["left_down_point"]["point"][2] += dz
                roi_dict[type]["right_up_point"]["point"][0] += dx
                roi_dict[type]["right_up_point"]["point"][2] += dz

                roi_dict["view_xy"]["right_down_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_down_point"]["point"][2] += dz
                roi_dict["view_xy"]["right_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["down_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["down_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["up_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["up_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_up_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_up_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_mid_point"]["point"][2] += dz
                roi_dict["view_xy"]["left_down_point"]["point"][0] += dx
                roi_dict["view_yz"]["left_down_point"]["point"][2] += dz
                roi_dict["view_xy"]["right_up_point"]["point"][0] += dx
                roi_dict["view_yz"]["right_up_point"]["point"][2] += dz
                roi_dict["view_xy"]["mid_point"]["point"][0] += dx
                roi_dict["view_yz"]["mid_point"]["point"][2] += dz

                self.draw_roi_rectangle(roi_dict, type)
                roi_dict[type]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)

        self.view_xy.UpdateDisplayExtent()
        self.view_xy.Render()
        self.view_yz.UpdateDisplayExtent()
        self.view_yz.Render()
        self.view_xz.UpdateDisplayExtent()
        self.view_xz.Render()

    def draw_roi_rectangle(self, roi_dict, type):
        #  先清除actor
        name_list = ["left_down_point", "left_mid_point", "left_up_point", "right_down_point", "right_mid_point",
                     "right_up_point",
                     "down_mid_point", "up_mid_point", "mid_point", "left_down_line", "left_up_line", "right_down_line",
                     "right_up_line",
                     "down_left_line", "down_right_line", "up_left_line", "up_right_line"]
        try:
            for name in name_list:
                self.view_xy.GetRenderer().RemoveActor(roi_dict["view_xy"][name]["actor"])
                self.view_yz.GetRenderer().RemoveActor(roi_dict["view_yz"][name]["actor"])
                self.view_xz.GetRenderer().RemoveActor(roi_dict["view_xz"][name]["actor"])
        except:
            print("remove roi actor failed!!!")

        dict_type = roi_dict["view_xy"]
        left_down_x, left_down_y = dict_type["left_down_point"]["point"][0], dict_type["left_down_point"]["point"][
            1]
        left_up_x, left_up_y = dict_type["left_up_point"]["point"][0], dict_type["left_up_point"]["point"][1]
        left_mid_x, left_mid_y = dict_type["left_mid_point"]["point"][0], dict_type["left_mid_point"]["point"][1]
        right_down_x, right_down_y = dict_type["right_down_point"]["point"][0], \
            dict_type["right_down_point"]["point"][
                1]
        right_up_x, right_up_y = dict_type["right_up_point"]["point"][0], dict_type["right_up_point"]["point"][1]
        right_mid_x, right_mid_y = dict_type["right_mid_point"]["point"][0], dict_type["right_mid_point"]["point"][
            1]
        down_mid_x, down_mid_y = dict_type["down_mid_point"]["point"][0], dict_type["down_mid_point"]["point"][1]
        up_mid_x, up_mid_y = dict_type["up_mid_point"]["point"][0], dict_type["up_mid_point"]["point"][1]
        mid_x, mid_y = dict_type["mid_point"]["point"][0], dict_type["mid_point"]["point"][1]

        self.draw_point(left_down_x, left_down_y, self.imageshape[2] + 1, color=[1, 1, 1], type="view_xy")
        roi_dict["view_xy"]["left_down_point"]["actor"] = self.temp_actor

        self.draw_point(left_up_x, left_up_y, self.imageshape[2] + 1, color=[1, 1, 1], type="view_xy")
        roi_dict["view_xy"]["left_up_point"]["actor"] = self.temp_actor

        self.draw_point(right_down_x, right_down_y, self.imageshape[2] + 1, color=[1, 1, 1], type="view_xy")
        roi_dict["view_xy"]["right_down_point"]["actor"] = self.temp_actor

        self.draw_point(right_up_x, right_up_y, self.imageshape[2] + 1, color=[1, 1, 1], type="view_xy")
        roi_dict["view_xy"]["right_up_point"]["actor"] = self.temp_actor

        self.draw_point(left_mid_x, left_mid_y, self.imageshape[2] + 1, color=[1, 0, 0], type="view_xy")
        roi_dict["view_xy"]["left_mid_point"]["actor"] = self.temp_actor

        self.draw_point(right_mid_x, right_mid_y, self.imageshape[2] + 1, color=[1, 0, 0], type="view_xy")
        roi_dict["view_xy"]["right_mid_point"]["actor"] = self.temp_actor

        self.draw_point(up_mid_x, up_mid_y, self.imageshape[2] + 1, color=[0, 1, 0], type="view_xy")
        roi_dict["view_xy"]["up_mid_point"]["actor"] = self.temp_actor

        self.draw_point(down_mid_x, down_mid_y, self.imageshape[2] + 1, color=[0, 1, 0], type="view_xy")
        roi_dict["view_xy"]["down_mid_point"]["actor"] = self.temp_actor

        self.draw_point(mid_x, mid_y, self.imageshape[2] + 1, color=[1, 0.5, 0], type="view_xy")
        roi_dict["view_xy"]["mid_point"]["actor"] = self.temp_actor

        self.draw_line([left_down_x, left_down_y + self.radius_xy, self.imageshape[2] + 1],
                       [left_mid_x, left_mid_y - self.radius_xy, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["left_down_line"]["actor"] = self.temp_actor

        self.draw_line([left_mid_x, left_mid_y + self.radius_xy, self.imageshape[2] + 1],
                       [left_up_x, left_up_y - self.radius_xy, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["left_up_line"]["actor"] = self.temp_actor

        self.draw_line([left_down_x + self.radius_xy, left_down_y, self.imageshape[2] + 1],
                       [down_mid_x - self.radius_xy, down_mid_y, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["down_left_line"]["actor"] = self.temp_actor

        self.draw_line([down_mid_x + self.radius_xy, down_mid_y, self.imageshape[2] + 1],
                       [right_down_x - self.radius_xy, right_down_y, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["down_right_line"]["actor"] = self.temp_actor

        self.draw_line([right_down_x, right_down_y + self.radius_xy, self.imageshape[2] + 1],
                       [right_mid_x, right_mid_y - self.radius_xy, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["right_down_line"]["actor"] = self.temp_actor

        self.draw_line([right_mid_x, right_mid_y + self.radius_xy, self.imageshape[2] + 1],
                       [right_up_x, right_up_y - self.radius_xy, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["right_up_line"]["actor"] = self.temp_actor

        self.draw_line([left_up_x + self.radius_xy, left_up_y, self.imageshape[2] + 1],
                       [up_mid_x - self.radius_xy, up_mid_y, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["up_left_line"]["actor"] = self.temp_actor

        self.draw_line([up_mid_x + self.radius_xy, up_mid_y, self.imageshape[2] + 1],
                       [right_up_x - self.radius_xy, right_up_y, self.imageshape[2] + 1],
                       color=[1, 0.5, 0.5], type="view_xy")
        roi_dict["view_xy"]["up_right_line"]["actor"] = self.temp_actor

        dict_type = roi_dict["view_xz"]
        left_down_x, left_down_z = dict_type["left_down_point"]["point"][0], dict_type["left_down_point"]["point"][
            2]
        left_up_x, left_up_z = dict_type["left_up_point"]["point"][0], dict_type["left_up_point"]["point"][2]
        left_mid_x, left_mid_z = dict_type["left_mid_point"]["point"][0], dict_type["left_mid_point"]["point"][2]
        right_down_x, right_down_z = dict_type["right_down_point"]["point"][0], \
            dict_type["right_down_point"]["point"][
                2]
        right_up_x, right_up_z = dict_type["right_up_point"]["point"][0], dict_type["right_up_point"]["point"][2]
        right_mid_x, right_mid_z = dict_type["right_mid_point"]["point"][0], dict_type["right_mid_point"]["point"][
            2]
        down_mid_x, down_mid_z = dict_type["down_mid_point"]["point"][0], dict_type["down_mid_point"]["point"][2]
        up_mid_x, up_mid_z = dict_type["up_mid_point"]["point"][0], dict_type["up_mid_point"]["point"][2]
        mid_x, mid_z = dict_type["mid_point"]["point"][0], dict_type["mid_point"]["point"][2]

        self.draw_point(left_down_x, 0, left_down_z, color=[1, 1, 1], type="view_xz")
        roi_dict["view_xz"]["left_down_point"]["actor"] = self.temp_actor

        self.draw_point(left_up_x, 0, left_up_z, color=[1, 1, 1], type="view_xz")
        roi_dict["view_xz"]["left_up_point"]["actor"] = self.temp_actor

        self.draw_point(right_down_x, 0, right_down_z, color=[1, 1, 1], type="view_xz")
        roi_dict["view_xz"]["right_down_point"]["actor"] = self.temp_actor

        self.draw_point(right_up_x, 0, right_up_z, color=[1, 1, 1], type="view_xz")
        roi_dict["view_xz"]["right_up_point"]["actor"] = self.temp_actor

        self.draw_point(left_mid_x, 0, left_mid_z, color=[1, 0, 0], type="view_xz")
        roi_dict["view_xz"]["left_mid_point"]["actor"] = self.temp_actor

        self.draw_point(right_mid_x, 0, right_mid_z, color=[1, 0, 0], type="view_xz")
        roi_dict["view_xz"]["right_mid_point"]["actor"] = self.temp_actor

        self.draw_point(up_mid_x, 0, up_mid_z, color=[0, 0, 1], type="view_xz")
        roi_dict["view_xz"]["up_mid_point"]["actor"] = self.temp_actor

        self.draw_point(down_mid_x, 0, down_mid_z, color=[0, 0, 1], type="view_xz")
        roi_dict["view_xz"]["down_mid_point"]["actor"] = self.temp_actor

        self.draw_point(mid_x, 0, mid_z, color=[1, 0.5, 0], type="view_xz")
        roi_dict["view_xz"]["mid_point"]["actor"] = self.temp_actor

        self.draw_line([left_down_x, 0, left_down_z + self.radius_xy], [left_mid_x, 0, left_mid_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["left_down_line"]["actor"] = self.temp_actor

        self.draw_line([left_mid_x, 0, left_mid_z + self.radius_xy, ], [left_up_x, 0, left_up_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["left_up_line"]["actor"] = self.temp_actor

        self.draw_line([left_down_x + self.radius_xy, 0, left_down_z], [down_mid_x - self.radius_xy, 0, down_mid_z],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["down_left_line"]["actor"] = self.temp_actor

        self.draw_line([down_mid_x + self.radius_xy, 0, down_mid_z],
                       [right_down_x - self.radius_xy, 0, right_down_z],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["down_right_line"]["actor"] = self.temp_actor

        self.draw_line([right_down_x, 0, right_down_z + self.radius_xy],
                       [right_mid_x, 0, right_mid_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["right_down_line"]["actor"] = self.temp_actor

        self.draw_line([right_mid_x, 0, right_mid_z + self.radius_xy], [right_up_x, 0, right_up_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["right_up_line"]["actor"] = self.temp_actor

        self.draw_line([left_up_x + self.radius_xy, 0, left_up_z], [up_mid_x - self.radius_xy, 0, up_mid_z],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["up_left_line"]["actor"] = self.temp_actor

        self.draw_line([up_mid_x + self.radius_xy, 0, up_mid_z], [right_up_x - self.radius_xy, 0, right_up_z],
                       color=[1, 0.5, 0.5], type="view_xz")
        roi_dict["view_xz"]["up_right_line"]["actor"] = self.temp_actor

        dict_type = roi_dict["view_yz"]
        left_down_y, left_down_z = dict_type["left_down_point"]["point"][1], dict_type["left_down_point"]["point"][2]
        left_up_y, left_up_z = dict_type["left_up_point"]["point"][1], dict_type["left_up_point"]["point"][2]
        left_mid_y, left_mid_z = dict_type["left_mid_point"]["point"][1], dict_type["left_mid_point"]["point"][2]
        right_down_y, right_down_z = dict_type["right_down_point"]["point"][1], dict_type["right_down_point"]["point"][
            2]
        right_up_y, right_up_z = dict_type["right_up_point"]["point"][1], dict_type["right_up_point"]["point"][2]
        right_mid_y, right_mid_z = dict_type["right_mid_point"]["point"][1], dict_type["right_mid_point"]["point"][2]
        down_mid_y, down_mid_z = dict_type["down_mid_point"]["point"][1], dict_type["down_mid_point"]["point"][2]
        up_mid_y, up_mid_z = dict_type["up_mid_point"]["point"][1], dict_type["up_mid_point"]["point"][2]
        mid_y, mid_z = dict_type["mid_point"]["point"][1], dict_type["mid_point"]["point"][2]

        self.draw_point(self.imageshape[0] + 1, left_down_y, left_down_z, color=[1, 1, 1], type="view_yz")
        roi_dict["view_yz"]["left_down_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, left_up_y, left_up_z, color=[1, 1, 1], type="view_yz")
        roi_dict["view_yz"]["left_up_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, right_down_y, right_down_z, color=[1, 1, 1], type="view_yz")
        roi_dict["view_yz"]["right_down_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, right_up_y, right_up_z, color=[1, 1, 1], type="view_yz")
        roi_dict["view_yz"]["right_up_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, left_mid_y, left_mid_z, color=[0, 1, 0], type="view_yz")
        roi_dict["view_yz"]["left_mid_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, right_mid_y, right_mid_z, color=[0, 1, 0], type="view_yz")
        roi_dict["view_yz"]["right_mid_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, up_mid_y, up_mid_z, color=[0, 0, 1], type="view_yz")
        roi_dict["view_yz"]["up_mid_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, down_mid_y, down_mid_z, color=[0, 0, 1], type="view_yz")
        roi_dict["view_yz"]["down_mid_point"]["actor"] = self.temp_actor

        self.draw_point(self.imageshape[0] + 1, mid_y, mid_z, color=[1, 0.5, 0], type="view_yz")
        roi_dict["view_yz"]["mid_point"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], left_down_y, left_down_z + self.radius_xy],
                       [self.imageshape[0], left_mid_y, left_mid_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["left_down_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], left_mid_y, left_mid_z + self.radius_xy, ],
                       [self.imageshape[0], left_up_y, left_up_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["left_up_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], left_down_y + self.radius_xy, left_down_z],
                       [self.imageshape[0], down_mid_y - self.radius_xy, down_mid_z],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["down_left_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], down_mid_y + self.radius_xy, down_mid_z],
                       [self.imageshape[0], right_down_y - self.radius_xy, right_down_z],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["down_right_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], right_down_y, right_down_z + self.radius_xy],
                       [self.imageshape[0], right_mid_y, right_mid_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["right_down_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], right_mid_y, right_mid_z + self.radius_xy],
                       [self.imageshape[0], right_up_y, right_up_z - self.radius_xy],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["right_up_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], left_up_y + self.radius_xy, left_up_z],
                       [self.imageshape[0], up_mid_y - self.radius_xy, up_mid_z],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["up_left_line"]["actor"] = self.temp_actor

        self.draw_line([self.imageshape[0], up_mid_y + self.radius_xy, up_mid_z],
                       [self.imageshape[0], right_up_y - self.radius_xy, right_up_z],
                       color=[1, 0.5, 0.5], type="view_yz")
        roi_dict["view_yz"]["up_right_line"]["actor"] = self.temp_actor

    def draw_line(self, point1, point2, color=None, type=None):
        if type == "view_xy":
            point1[0] = point1[0] * self.spacing_xy[0] + self.origin_xy[0]
            point1[1] = point1[1] * self.spacing_xy[1] + self.origin_xy[1]
            point2[0] = point2[0] * self.spacing_xy[0] + self.origin_xy[0]
            point2[1] = point2[1] * self.spacing_xy[1] + self.origin_xy[1]
        elif type == "view_yz":
            point1[0] = point1[0] * self.spacing_yz[0] + self.origin_yz[0]
            point1[1] = point1[1] * self.spacing_yz[1] + self.origin_yz[1]
            point1[2] = point1[2] * self.spacing_yz[2] + self.origin_yz[2]
            point2[0] = point2[0] * self.spacing_yz[0] + self.origin_yz[0]
            point2[1] = point2[1] * self.spacing_yz[1] + self.origin_yz[1]
            point2[2] = point2[2] * self.spacing_yz[2] + self.origin_yz[2]
        elif type == "view_xz":
            point1[0] = point1[0] * self.spacing_xz[0] + self.spacing_xz[0]
            point1[2] = point1[2] * self.spacing_xz[2] + self.spacing_xz[2]
            point2[0] = point2[0] * self.spacing_xz[0] + self.spacing_xz[0]
            point2[2] = point2[2] * self.spacing_xz[2] + self.spacing_xz[2]

        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(point1)
        lineSource.SetPoint2(point2)
        lineSource.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(3)
        actor.GetProperty().SetColor(color[0], color[1], color[2])
        self.temp_actor = actor
        if type == "view_xy":
            self.view_xy.GetRenderer().AddActor(actor)
        elif type == "view_yz":
            self.view_yz.GetRenderer().AddActor(actor)
        elif type == "view_xz":
            self.view_xz.GetRenderer().AddActor(actor)

    def draw_point(self, x, y, z, color=None, type=None):
        radius_xy = 3
        square = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        if type == "view_xy":
            point_x = x * self.spacing_xy[0] + self.origin_xy[0]
            point_y = y * self.spacing_xy[1] + self.origin_xy[1]
            point_z = z * self.spacing_xy[2] + self.origin_xy[2]
            points.InsertNextPoint(point_x - radius_xy, point_y + radius_xy, point_z)
            points.InsertNextPoint(point_x + radius_xy, point_y + radius_xy, point_z)
            points.InsertNextPoint(point_x + radius_xy, point_y - radius_xy, point_z)
            points.InsertNextPoint(point_x - radius_xy, point_y - radius_xy, point_z)
        elif type == "view_yz":
            point_x = x * self.spacing_yz[0] + self.origin_yz[0]
            point_y = y * self.spacing_yz[1] + self.origin_yz[1]
            point_z = z * self.spacing_yz[2] + self.origin_yz[2]

            points.InsertNextPoint(point_x, point_y - radius_xy, point_z + radius_xy)
            points.InsertNextPoint(point_x, point_y + radius_xy, point_z + radius_xy)
            points.InsertNextPoint(point_x, point_y + radius_xy, point_z - radius_xy)
            points.InsertNextPoint(point_x, point_y - radius_xy, point_z - radius_xy)
        elif type == "view_xz":
            point_x = x * self.spacing_xz[0] + self.origin_xz[0]
            point_y = y * self.spacing_xz[1] + self.origin_xz[1]
            point_z = z * self.spacing_xz[2] + self.origin_xz[2]

            points.InsertNextPoint(point_x - radius_xy, point_y, point_z + radius_xy)
            points.InsertNextPoint(point_x + radius_xy, point_y, point_z + radius_xy)
            points.InsertNextPoint(point_x + radius_xy, point_y, point_z - radius_xy)
            points.InsertNextPoint(point_x - radius_xy, point_y, point_z - radius_xy)

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
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color[0], color[1], color[2])
        self.temp_actor = actor
        if type == "view_xy":
            self.view_xy.GetRenderer().AddActor(actor)
        elif type == "view_yz":
            self.view_yz.GetRenderer().AddActor(actor)
        elif type == "view_xz":
            self.view_xz.GetRenderer().AddActor(actor)


class LeftButtonPressEvent_GetROI():
    def __init__(self, picker, viewer_xy, viewer_yz, viewer_xz, type):
        self.picker = picker  # 坐标拾取
        self.view_xy = viewer_xy
        self.view_yz = viewer_yz
        self.view_xz = viewer_xz
        self.actor_xy = self.view_xy.GetImageActor()
        self.actor_yz = self.view_yz.GetImageActor()
        self.actor_xz = self.view_xz.GetImageActor()
        self.iren_xy = self.view_xy.GetRenderWindow().GetInteractor()
        self.iren_yz = self.view_yz.GetRenderWindow().GetInteractor()
        self.iren_xz = self.view_xz.GetRenderWindow().GetInteractor()
        self.render_xy = self.view_xy.GetRenderer()
        self.render_yz = self.view_yz.GetRenderer()
        self.render_xz = self.view_xz.GetRenderer()
        self.origin_xy = self.view_xy.GetInput().GetOrigin()
        self.origin_yz = self.view_yz.GetInput().GetOrigin()
        self.origin_xz = self.view_xz.GetInput().GetOrigin()
        self.spacing_xy = self.view_xy.GetInput().GetSpacing()
        self.spacing_yz = self.view_yz.GetInput().GetSpacing()
        self.spacing_xz = self.view_xz.GetInput().GetSpacing()
        self.ren_xy = self.view_xy.GetRenderer()
        self.ren_yz = self.view_yz.GetRenderer()
        self.ren_xz = self.view_xz.GetRenderer()
        self.origin = self.view_xy.GetInput().GetOrigin()
        self.spacing = self.view_xy.GetInput().GetSpacing()
        self.imageshape = self.view_xy.GetInput().GetDimensions()
        self.type = type

    def __call__(self, caller, ev):
        roi_dict = getControlROIPoint()
        if self.type == "view_xy":
            self.picker.AddPickList(self.actor_xy)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_xy.GetEventPosition()[0], self.iren_xy.GetEventPosition()[1], 0, self.render_xy)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_xy[i])) / self.spacing_xy[i] for i in range(3)]
        elif self.type == "view_yz":
            self.picker.AddPickList(self.actor_yz)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_yz.GetEventPosition()[0], self.iren_yz.GetEventPosition()[1], 0, self.render_yz)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_yz[i])) / self.spacing_yz[i] for i in range(3)]
        elif self.type == "view_xz":
            self.picker.AddPickList(self.actor_xz)
            self.picker.SetTolerance(0.001)
            self.picker.Pick(self.iren_xz.GetEventPosition()[0], self.iren_xz.GetEventPosition()[1], 0, self.render_xz)
            self.start = self.picker.GetPickPosition()
            self.start_pos = [int((self.start[i] - self.origin_xz[i])) / self.spacing_xz[i] for i in range(3)]
        print(self.type)
        self.point_is_clicked(roi_dict, self.type)

    def is_point_inside_circle(self, circle_center, point, radius=3):
        if self.type == "view_xy":
            cx, cy = circle_center
            cx = cx * self.spacing[0] + self.origin[0]
            cy = cy * self.spacing[1] + self.origin[1]
            c1 = cx
            c2 = cy
        elif self.type == "view_yz":
            cy, cz = circle_center
            cy = cy * self.spacing[1] + self.origin[1]
            cz = cz * self.spacing[2] + self.origin[2]
            c1 = cy
            c2 = cz
        else:
            cx, cz = circle_center
            cx = cx * self.spacing[0] + self.origin[0]
            cz = cz * self.spacing[2] + self.origin[2]
            c1 = cx
            c2 = cz
        px, py = point
        if (-radius <= px - c1 <= radius) and (-radius <= py - c2 <= radius):
            return True
        return False

    def point_is_clicked(self, roi_dict, type):
        if type == "view_xy":
            self.is_click(0, 1, roi_dict, type)
        elif type == "view_yz":
            self.is_click(1, 2, roi_dict, type)
        elif type == "view_xz":
            self.is_click(0, 2, roi_dict, type)

        self.view_xy.UpdateDisplayExtent()
        self.view_xy.Render()
        self.view_yz.UpdateDisplayExtent()
        self.view_yz.Render()
        self.view_xz.UpdateDisplayExtent()
        self.view_xz.Render()

    def is_click(self, index1, index2, roi_dict, type):
        if self.is_point_inside_circle(
                (
                        roi_dict[type]["left_down_point"]["point"][index1],
                        roi_dict[type]["left_down_point"]["point"][index2]),
                (self.start[index1], self.start[index2])):
            roi_dict[type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(True)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["left_mid_point"]["point"][index1],
                                          roi_dict[type]["left_mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_xz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xy"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_xy"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(True)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["left_up_point"]["point"][index1],
                                          roi_dict[type]["left_up_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(True)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)


        elif self.is_point_inside_circle((roi_dict[type]["up_mid_point"]["point"][index1],
                                          roi_dict[type]["up_mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_yz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xz"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_yz"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(True)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["down_mid_point"]["point"][index1],
                                          roi_dict[type]["down_mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_yz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xz"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_yz"]["down_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(True)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["right_down_point"]["point"][index1],
                                          roi_dict[type]["right_down_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(True)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["right_mid_point"]["point"][index1],
                                          roi_dict[type]["right_mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_xz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xy"]["up_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_xy"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(True)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["right_up_point"]["point"][index1],
                                          roi_dict[type]["right_up_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(True)
            set_mid_is_clicked(False)

        elif self.is_point_inside_circle((roi_dict[type]["mid_point"]["point"][index1],
                                          roi_dict[type]["mid_point"]["point"][index2]),
                                         (self.start[index1], self.start[index2])):
            roi_dict[type]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            if type == "view_xy":
                roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_yz":
                roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            elif type == "view_xz":
                roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
                roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 1, 0)
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(True)

        else:
            set_left_down_is_clicked(False)
            set_left_mid_is_clicked(False)
            set_left_up_is_clicked(False)
            set_down_mid_is_clicked(False)
            set_up_mid_is_clicked(False)
            set_right_down_is_clicked(False)
            set_right_mid_is_clicked(False)
            set_right_up_is_clicked(False)
            set_mid_is_clicked(False)


class LeftButtonReleaseEvent_GetROI():
    def __init__(self, picker, viewer_xy,viewer_yz,viewer_xz, type):
        self.view_xy = viewer_xy
        self.view_yz = viewer_yz
        self.view_xz = viewer_xz
        self.type = type

    def __call__(self, caller, ev):
        roi_dict = getControlROIPoint()
        if self.type == "view_xy":
            roi_dict[self.type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict[self.type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict[self.type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict[self.type]["down_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict[self.type]["up_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)

            roi_dict["view_xz"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict["view_xz"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict["view_yz"]["left_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict["view_yz"]["right_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)

        elif self.type == "view_yz":
            roi_dict[self.type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict[self.type]["left_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict[self.type]["right_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict[self.type]["down_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict[self.type]["up_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)

            roi_dict["view_xy"]["down_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict["view_xy"]["up_mid_point"]["actor"].GetProperty().SetColor(0, 1, 0)
            roi_dict["view_xz"]["down_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict["view_xz"]["up_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict["view_xz"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
        else:
            roi_dict[self.type]["left_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["left_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_down_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["right_up_point"]["actor"].GetProperty().SetColor(1, 1, 1)
            roi_dict[self.type]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict[self.type]["left_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict[self.type]["right_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict[self.type]["down_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict[self.type]["up_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)

            roi_dict["view_xy"]["left_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict["view_xy"]["right_mid_point"]["actor"].GetProperty().SetColor(1, 0, 0)
            roi_dict["view_yz"]["down_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict["view_yz"]["up_mid_point"]["actor"].GetProperty().SetColor(0, 0, 1)
            roi_dict["view_xy"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
            roi_dict["view_yz"]["mid_point"]["actor"].GetProperty().SetColor(1, 0.5, 0.5)
        self.view_xy.UpdateDisplayExtent()
        self.view_xy.Render()
        self.view_yz.UpdateDisplayExtent()
        self.view_yz.Render()
        self.view_xz.UpdateDisplayExtent()
        self.view_xz.Render()
        set_left_down_is_clicked(False)
        set_left_mid_is_clicked(False)
        set_left_up_is_clicked(False)
        set_down_mid_is_clicked(False)
        set_up_mid_is_clicked(False)
        set_right_down_is_clicked(False)
        set_right_mid_is_clicked(False)
        set_right_up_is_clicked(False)
        set_mid_is_clicked(False)
