import itertools
import pathlib
from dataclasses import dataclass
from enum import Enum, auto
from functools import cache

import numpy as np
import wx
import wx.glcanvas as glcanvas

from OpenGL.GL import *
from OpenGL.GLU import gluUnProject

from cagd_lib.hw2._b_spline import evaluate_b_spline
from cagd_lib.hw2._bezier_curve import evaluate_bezier
from cagd_lib.hw2._curve_io import import_curves, export_curves, BezierCurve, BSpline
from cagd_lib.hw2.connect_curves_tool import ConnectCurvesTool
from cagd_lib.hw2.knot_editor import KnotEditor
from cagd_lib.hw2.mouse_add_delete import MouseAddDelete
from cagd_lib.hw2.mouse_point_move import MousePointMove
from cagd_lib.hw2.mouse_select import MouseSelect
from cagd_lib.hw2.mouse_look import MouseLook

CONTROL_POLYGON_COLOR = (1, 0, 0)
CONTROL_POINT_COLOR = (1, 1, 0)
SELECTED_CURVE_COLOR = (0, 1, 1)
SELECTED_POINT_COLOR = (0, 0.3, 1)

TANGENT_VECTOR_COLOR = (1, 0, 0)
NORMAL_VECTOR_COLOR = (0, 1, 0)
OSCULATING_CIRCLE_COLOR = (0, 0, 1)

N_SAMPLES = 1000
BEZIER_SAMPLE_POINTS = np.array(np.arange(0, 1 + 1 / N_SAMPLES, 1 / N_SAMPLES)).reshape((-1, 1))

EPSILON = 0.001


def B_SPLINE_SAMPLE_POINTS(curve: BSpline):
    sampling_start, sampling_end = curve.knots[curve.order - 1], curve.knots[-curve.order]
    sampling_step_size = sampling_end / N_SAMPLES - sampling_start / N_SAMPLES
    return np.array(
        np.arange(sampling_start, sampling_end + sampling_step_size, sampling_step_size)).reshape((-1, 1))


class Tools(Enum):
    SELECT = auto()
    MOVE = auto()
    ADD_DELETE = auto()
    CONNECT_CURVES = auto()


class CurveTypes(Enum):
    BEZIER = auto()
    BSPLINE = auto()


class EndConditions(Enum):
    FLOATING = auto()
    OPEN = auto()


@dataclass
class DifferentialGeometryProperties:
    tangent: np.ndarray
    normal: np.ndarray
    osculating_radius: np.float32


class GlobalState:

    @staticmethod
    def set_point_weight_text(text):
        pass

    @staticmethod
    def enable_weight_text_control():
        pass

    @staticmethod
    def disable_weight_text_control():
        pass

    @staticmethod
    def enable_new_b_spline_controls():
        pass

    @staticmethod
    def disable_new_b_spline_controls():
        pass

    def __init__(self):
        self.curves: list[BezierCurve | BSpline] = []
        self.curves_samples: list = []
        self.switch_tools = None  # def switch_tools(new_tool: Tools)
        self.selected_curve = None
        self._selected_point = None
        self._selected_sample = None
        self._new_curve_type = CurveTypes.BEZIER
        self.new_curve_order = 3
        self.new_curve_end_condition = EndConditions.FLOATING
        self._differential_geometry_properties: DifferentialGeometryProperties | None = None

    @property
    def selected_sample(self):
        return self._selected_sample

    @selected_sample.setter
    def selected_sample(self, selected_sample):
        self._selected_sample = selected_sample
        if None in[
            selected_sample,
            self.selected_curve,
        ]:
            return
        selected_curve = self.curves[self.selected_curve]
        if isinstance(selected_curve, BezierCurve):
            selected_sample_value = BEZIER_SAMPLE_POINTS[selected_sample]
        elif isinstance(selected_curve, BSpline):
            selected_sample_value = B_SPLINE_SAMPLE_POINTS(selected_curve)[selected_sample]
        else:
            raise TypeError(selected_curve)

        # epsilon = np.sqrt(np.finfo(np.float32).eps)
        epsilon = EPSILON

        evaluated_points = self.evaluate_curve(
            selected_curve,
            np.array([
                selected_sample_value - epsilon,
                selected_sample_value,
                selected_sample_value + epsilon,
            ], dtype=np.float32).reshape((-1, 1))
        )

        dc = evaluated_points[2]/(2 * epsilon) - evaluated_points[0]/(2 * epsilon)
        ddc = (evaluated_points[2] + evaluated_points[0] - 2 * evaluated_points[1])/(epsilon**2)

        dc_x_ddc = np.cross(dc, ddc)

        geometry_properties = DifferentialGeometryProperties(
            # T = dC / ||dC||
            tangent=dc/np.linalg.norm(dc),
            normal=None,
            # kappa = ||dC x ddC|| / ||dC||^3
            osculating_radius=np.linalg.norm(dc) ** 3 /np.linalg.norm(dc_x_ddc),
        )

        # B = (dC x ddC) / ||dC x ddC||
        # N = B x T
        geometry_properties.normal = np.cross(dc_x_ddc/np.linalg.norm(dc_x_ddc), geometry_properties.tangent)
        self._differential_geometry_properties = geometry_properties
        print(dc)
        print(ddc)
        print(dc_x_ddc)
        print(geometry_properties)

    @property
    def differential_geometry_properties(self) -> DifferentialGeometryProperties:
        return self._differential_geometry_properties

    @property
    def selected_point(self):
        return self._selected_point

    @selected_point.setter
    def selected_point(self, selected_point):
        self._selected_point = selected_point
        if selected_point is not None:
            self.set_point_weight_text(
                f"{self.curves[self.selected_curve].control_points[selected_point][2]}")
        else:
            self.set_point_weight_text("")

        if selected_point is None:
            self.disable_weight_text_control()
        else:
            self.enable_weight_text_control()

    @property
    def new_curve_type(self):
        return self._new_curve_type

    @new_curve_type.setter
    def new_curve_type(self, new_curve_type: CurveTypes):
        if new_curve_type == CurveTypes.BSPLINE:
            self.enable_new_b_spline_controls()
        else:
            self.disable_new_b_spline_controls()
        self._new_curve_type = new_curve_type

    def add_curve(self, curve):
        if isinstance(curve, BezierCurve):
            self.curves.append(curve)
            curves_samples_3d = self.sampleBezierCurve(curve)
            self.curves_samples.append(curves_samples_3d)
        elif isinstance(curve, BSpline):
            self.curves.append(curve)
            curves_samples_3d = self.sampleBSplineCurve(curve)
            self.curves_samples.append(curves_samples_3d)
        else:
            raise ValueError(curve)

    def delete_curve(self, index):
        if self.selected_curve is not None:
            if self.selected_curve == index:
                self.selected_curve = None
            elif self.selected_curve > index:
                self.selected_curve -= 1
        self.curves.pop(index)
        self.curves_samples.pop(index)
        GlobalState.selected_point = None

    @staticmethod
    def evaluate_bezier_curve(curve: BezierCurve, t: np.ndarray):
        """

        :param curve:
        :param t: shape (-1, 1)
        :return:
        """
        curves_samples_2d = evaluate_bezier(np.array(curve.control_points), t)
        """samples in x and y"""

        curves_samples_3d = np.empty(shape=(curves_samples_2d.shape[0], 3), dtype=np.float32)
        """samples in x and y with z set to z=0"""

        curves_samples_3d[:, 2] = 0
        curves_samples_3d[:, :2] = curves_samples_2d
        return curves_samples_3d

    @staticmethod
    def evaluate_b_spline_curve(curve: BSpline, t: np.ndarray):
        """

        :param curve:
        :param t: shape (-1, 1)
        :return:
        """

        curves_samples_2d = evaluate_b_spline(
            np.array(curve.control_points), curve.knots, curve.order, t)
        """samples in x and y"""

        curves_samples_3d = np.empty(shape=(curves_samples_2d.shape[0], 3), dtype=np.float32)
        """samples in x and y with z set to z=0"""

        curves_samples_3d[:, 2] = 0
        curves_samples_3d[:, :2] = curves_samples_2d
        return curves_samples_3d

    @staticmethod
    def evaluate_curve(curve: BSpline | BezierCurve, t: np.ndarray):
        if isinstance(curve, BSpline):
            return GlobalState.evaluate_b_spline_curve(curve, t)
        elif isinstance(curve, BezierCurve):
            return GlobalState.evaluate_bezier_curve(curve, t)
        else:
            raise TypeError(curve)

    @staticmethod
    def sampleBezierCurve(curve):
        if len(curve.control_points) < 2:
            return np.array([])

        return GlobalState.evaluate_bezier_curve(curve, BEZIER_SAMPLE_POINTS)

    @staticmethod
    def sampleBSplineCurve(curve):
        if (len(curve.control_points) < curve.order) or (len(curve.knots) == 0) or (len(curve.knots) != len(curve.control_points) + curve.order):
            return np.array([])

        return GlobalState.evaluate_b_spline_curve(
            curve, B_SPLINE_SAMPLE_POINTS(curve))

    @staticmethod
    def resample_curve(curve):
        if isinstance(curve, BezierCurve):
            new_samples = GlobalState.sampleBezierCurve(curve)
        elif isinstance(curve, BSpline):
            new_samples = GlobalState.sampleBSplineCurve(curve)
        else:
            raise TypeError(curve)
        GlobalState.curves_samples[GlobalState.curves.index(curve)] = new_samples

    @staticmethod
    def differentiate_curve(curve: BezierCurve | BSpline, t: float):
        epsilon = EPSILON
        evaluated_points = GlobalState.evaluate_curve(
            curve,
            np.array([
                t - epsilon,
                t,
                t + epsilon,
            ], dtype=np.float32).reshape((-1, 1))
        )

        return evaluated_points[2] / (2 * epsilon) - evaluated_points[0] / (2 * epsilon)

    def connect_curves(self, curve_0_index: int, curve_1_index: int):
        curve_0, curve_1 = self.curves[curve_0_index], self.curves[curve_1_index]

        if isinstance(curve_0, BezierCurve):
            curve_0_last_t = BEZIER_SAMPLE_POINTS[-1]
        elif isinstance(curve_0, BSpline):
            curve_0_last_t = curve_0.knots[-curve_0.order]

        if isinstance(curve_1, BezierCurve):
            curve_1_first_t = BEZIER_SAMPLE_POINTS[0]
        elif isinstance(curve_1, BSpline):
            curve_1_first_t = curve_1.knots[curve_1.order - 1]

        curve_0_end, curve_1_start = \
            self.curves_samples[curve_0_index][-1][:2], self.curves_samples[curve_1_index][0][:2]
        curve_0_tangent = self.differentiate_curve(curve_0, curve_0_last_t)
        curve_1_tangent = self.differentiate_curve(curve_1, curve_1_first_t)

        # G1 continuity
        difference_vector = curve_1_start - curve_0_end
        original_control_points = np.array(curve_1.control_points)

        cos_theta = (
            np.dot(curve_0_tangent, curve_1_tangent)
            /
            (np.linalg.norm(curve_0_tangent) * np.linalg.norm(curve_1_tangent))
        )
        theta = np.arccos(
            np.clip(cos_theta, -1, 1)
        )
        tangents_cross = np.cross(curve_0_tangent, curve_1_tangent)
        # theta = - np.arcsin(
        #     np.linalg.norm(tangents_cross)
        #     /
        #     (np.linalg.norm(curve_0_tangent) * np.linalg.norm(curve_1_tangent))
        # )
        if tangents_cross[2] > 0:
            theta = -theta

        rotation_matrix = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ], dtype=np.float32)
        # print("original points")
        # print(original_control_points[:, :2])
        # print(rotation_matrix)
        # print(curve_1_start)
        # print(difference_vector)
        new_control_points = \
            (rotation_matrix @ (original_control_points[:,
                                :2] - curve_1_start).transpose()).transpose() + curve_1_start - difference_vector
        for i, _ in enumerate(curve_1.control_points):
            curve_1.control_points[i] = (*tuple(new_control_points[i]), original_control_points[i][2])
        self.resample_curve(curve_1)

        if curve_0.order == curve_1.order:
            print("curves of same order. join to single bspline")


GlobalState = GlobalState()


class OpenGLCanvas(glcanvas.GLCanvas):
    def __init__(self, parent, ):
        glcanvas.GLCanvas.__init__(self, parent, wx.ID_ANY, size=(1120, 681))
        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)
        glClearColor(0.1, 0.15, 0.1, 1.0)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # mouse look handlers
        self.mouseLook = MouseLook()
        self.Bind(wx.EVT_MOTION, self.mouseLook.MouseMoveEvent)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.mouseLook.MouseMiddleDownEvent)
        self.Bind(wx.EVT_MIDDLE_UP, self.mouseLook.MouseMiddleUpEvent)
        self.Bind(wx.EVT_MOUSEWHEEL, self.mouseLook.MouseWheelEvent)

        # knot editor
        def knotEditHandler():
            GlobalState.resample_curve(GlobalState.curves[GlobalState.selected_curve])
        self.knotEditor = KnotEditor()
        self.knotEditor.editHandler = knotEditHandler

        # mouse select
        self.mouseSelect = MouseSelect(681, GlobalState.curves_samples)

        # mouse point move
        self.mousePointMove = MousePointMove(681, self.updatePointPosition)

        # mouse add/delete
        self.mouseAddDelete = MouseAddDelete(681, self.AddPoint, self.DeletePoint, self.CreateNewCurve)

        # mouse add/delete
        self.connectCurvesTool = ConnectCurvesTool(681, GlobalState.curves_samples)
        self.connectCurvesTool.globalState = GlobalState
        self.connectCurvesTool.connectHandler = GlobalState.connect_curves

        self.current_tool = None
        GlobalState.switch_tools = self.switch_tools
        # switch to default tool
        self.switch_tools(Tools.SELECT)

    def OnPaint(self, event):
        def new_paint(event):
            self.OnDraw()

        new_paint(event)
        self.Bind(wx.EVT_PAINT, new_paint)
        self.Bind(wx.EVT_IDLE, new_paint)

    def OnDraw(self):
        glClear(GL_COLOR_BUFFER_BIT)

        # curves
        for i, (curve, curve_samples) in enumerate(zip(GlobalState.curves, GlobalState.curves_samples)):
            if i == GlobalState.selected_curve:
                self.draw_lines(curve_samples, SELECTED_CURVE_COLOR)
            else:
                self.draw_lines(curve_samples)

        if GlobalState.selected_curve is not None:
            # control polygon
            curve = GlobalState.curves[GlobalState.selected_curve]
            control_points = np.empty_like(curve.control_points)
            control_points[:, [0, 1]] = np.array(curve.control_points)[:, [0, 1]]
            control_points[:, 2] = 0
            self.draw_lines(control_points, CONTROL_POLYGON_COLOR, 1)

            # control points
            for point in curve.control_points:
                self.draw_point(point[0], point[1], CONTROL_POINT_COLOR, 5)

        if GlobalState.selected_point is not None:
            point = GlobalState.curves[GlobalState.selected_curve].control_points[GlobalState.selected_point]
            self.draw_point(point[0], point[1], SELECTED_POINT_COLOR, 5)

        if None not in \
                [GlobalState.selected_curve,
                 GlobalState.selected_sample,  GlobalState.differential_geometry_properties]:
            pass
            sample_coordinates = GlobalState.curves_samples[GlobalState.selected_curve][GlobalState.selected_sample]
            geometry_properties: DifferentialGeometryProperties = GlobalState.differential_geometry_properties
            self.draw_lines([sample_coordinates, sample_coordinates + geometry_properties.tangent],
                            color=TANGENT_VECTOR_COLOR)

            self.draw_lines([sample_coordinates, sample_coordinates + geometry_properties.normal],
                            color=NORMAL_VECTOR_COLOR)
            self.draw_circle(
                *(sample_coordinates + geometry_properties.normal*geometry_properties.osculating_radius)[:2],
                radius=geometry_properties.osculating_radius,
                color=OSCULATING_CIRCLE_COLOR,
            )

        # render knot graphical editing on top
        # draw background
        glColor3f(0, 0, 0)
        p1, p2 = gluUnProject(0, 630, 0), gluUnProject(1120, 680, 0)
        glRectf(p1[0], p1[1], p2[0], p2[1])
        if GlobalState.selected_curve is not None and isinstance(GlobalState.curves[GlobalState.selected_curve], BSpline):
            selected_curve = GlobalState.curves[GlobalState.selected_curve]
            # draw knot range line
            glColor3f(1, 1, 1)
            p1, p2 = gluUnProject(10, 670, 0), gluUnProject(1110, 672, 0)
            glRectf(p1[0], p1[1], p2[0], p2[1])
            # draw knots
            minKnot = selected_curve.knots[0]
            maxKnot = selected_curve.knots[-1]
            points = [((knot - minKnot) / (maxKnot - minKnot)) * (1120 - 2 * 10) + 10 for knot in selected_curve.knots]
            defaultY = 660
            currentY = 660
            prevPoint = -1000
            for point in points:
                if point < (prevPoint + 6):
                    currentY -= 10
                else:
                    currentY = defaultY
                p = gluUnProject(point, currentY, 0)
                self.draw_point(p[0], p[1], (1, 0, 0), 5)
                prevPoint = point

        self.SwapBuffers()

    def switch_tools(self, new_tool: Tools):
        self.current_tool = new_tool

        # disable tools
        while self.Unbind(wx.EVT_LEFT_DOWN):
            pass
        while self.Unbind(wx.EVT_LEFT_UP):
            pass
        while self.Unbind(wx.EVT_RIGHT_DOWN):
            pass
        while self.Unbind(wx.EVT_RIGHT_UP):
            pass
        while self.Unbind(wx.EVT_MOTION):
            pass
        self.Bind(wx.EVT_MOTION, self.mouseLook.MouseMoveEvent)
        self.Bind(wx.EVT_LEFT_DOWN, self.knotEditor.MouseLeftEvent)
        self.Bind(wx.EVT_RIGHT_DOWN, self.knotEditor.MouseRightEvent)

        # enable selected tool
        if new_tool == Tools.SELECT:
            self.select_tool()
        elif new_tool == Tools.MOVE:
            self.move_tool()
        elif new_tool == Tools.ADD_DELETE:
            self.add_delete_tool()
        elif new_tool == Tools.CONNECT_CURVES:
            self.connect_curves_tool()

    ################## select tool
    def select_tool(self):
        if GlobalState.selected_curve is None:
            self.Bind(wx.EVT_LEFT_DOWN, self.mouseSelect.SelectCurveEvent)
            self.mouseSelect.selectionHandler = self.SelectCurve
            GlobalState.selected_sample = None
            self.knotEditor.knotVector = None
        else:
            self.Bind(wx.EVT_LEFT_DOWN, self.mouseSelect.SelectPointEvent)
            self.Bind(wx.EVT_RIGHT_DOWN, self.mouseSelect.SelectSampleEvent)
            self.mouseSelect.selectionHandler = self.SelectPoint
            self.mouseSelect.secondarySelectionHandler = self.SelectSample
            self.mouseSelect.controlPoints = GlobalState.curves[GlobalState.selected_curve].control_points
            self.mouseSelect.curveSamples = GlobalState.curves_samples[GlobalState.selected_curve]
            if isinstance(GlobalState.curves[GlobalState.selected_curve], BSpline):
                self.knotEditor.knotVector = GlobalState.curves[GlobalState.selected_curve].knots
                self.knotEditor.minKnot = GlobalState.curves[GlobalState.selected_curve].knots[0]
                self.knotEditor.maxKnot = GlobalState.curves[GlobalState.selected_curve].knots[-1]

    def SelectCurve(self, index):
        print(f'selected curve index = {index}')
        GlobalState.selected_curve = index
        if index is not None:
            self.switch_tools(Tools.SELECT)

    def SelectPoint(self, index):
        print(f'selected point index = {index}')
        prev = GlobalState.selected_point
        GlobalState.selected_point = index
        if index is None and prev is None:
            GlobalState.selected_curve = None
            self.switch_tools(Tools.SELECT)

    def SelectSample(self, index):
        print(f'selected point index = {index}')
        GlobalState.selected_sample = index

    ################## move tool
    def move_tool(self):
        self.Bind(wx.EVT_MOTION, self.mousePointMove.MouseMoveEvent)
        self.Bind(wx.EVT_LEFT_DOWN, self.mousePointMove.MouseLeftDownEvent)
        self.Bind(wx.EVT_LEFT_UP, self.mousePointMove.MouseLeftUpEvent)

    def updatePointPosition(self, position):
        if GlobalState.selected_point is None:
            return
        selected_curve = GlobalState.curves[GlobalState.selected_curve]
        weight = selected_curve.control_points[GlobalState.selected_point][2]
        selected_curve.control_points[GlobalState.selected_point] = (float(position[0]), float(position[1]), weight)
        GlobalState.resample_curve(selected_curve)
        self.OnDraw()

    ################## Add/Delete tool
    def add_delete_tool(self):
        self.Bind(wx.EVT_LEFT_DOWN, self.mouseAddDelete.MouseLeftDownEvent)
        self.Bind(wx.EVT_RIGHT_DOWN, self.mouseAddDelete.MouseRightDownEvent)
        if GlobalState.selected_curve is not None:
            self.mouseAddDelete.controlPoints = GlobalState.curves[GlobalState.selected_curve].control_points
        else:
            self.mouseAddDelete.controlPoints = None

    def CreateNewCurve(self):
        if GlobalState.new_curve_type == CurveTypes.BEZIER:
            newCurve = BezierCurve(order=0, control_points=[])
        elif GlobalState.new_curve_type == CurveTypes.BSPLINE:
            newCurve = BSpline(order=GlobalState.new_curve_order, knots=[], control_points=[])
            if GlobalState.new_curve_end_condition == EndConditions.OPEN:
                newCurve.knots.extend(0.0 for _ in range(GlobalState.new_curve_order))
                newCurve.knots.extend(1.0 for _ in range(GlobalState.new_curve_order))
            else:
                newCurve.knots.append(0.0)
                newCurve.knots.append(1.0)
            self.knotEditor.knotVector = newCurve.knots
            self.knotEditor.minKnot = 0.0
            self.knotEditor.maxKnot = 1.0
        GlobalState.add_curve(newCurve)  # TODO: open/floating end
        GlobalState.selected_curve = len(GlobalState.curves) - 1
        self.mouseAddDelete.controlPoints = newCurve.control_points


    def AddPoint(self, position):
        newPoint = (float(position[0]), float(position[1]), float(1.0))
        self.mouseAddDelete.controlPoints.append(newPoint)
        selected_curve = GlobalState.curves[GlobalState.selected_curve]
        if isinstance(selected_curve, BezierCurve):
            selected_curve.order += 1
        GlobalState.resample_curve(selected_curve)
        self.OnDraw()

    def DeletePoint(self, index):
        if GlobalState.selected_point is not None:
            if GlobalState.selected_point == index:
                GlobalState.selected_point = None
            elif GlobalState.selected_point > index:
                GlobalState.selected_point -= 1
        selected_curve = GlobalState.curves[GlobalState.selected_curve]
        selected_curve.control_points.pop(index)
        if len(selected_curve.control_points) == 0:
            GlobalState.delete_curve(GlobalState.selected_curve)
            self.mouseAddDelete.controlPoints = None
        else:
            if isinstance(selected_curve, BezierCurve):
                selected_curve.order -= 1
            GlobalState.resample_curve(selected_curve)

        self.OnDraw()

    ################## Connect Curves tool
    def connect_curves_tool(self):
        self.Bind(wx.EVT_LEFT_DOWN, self.connectCurvesTool.MouseLeftEvent)

    @staticmethod
    def draw_lines(vertices, color=(1, 1, 1), thickness=3):
        glColor3f(*color)
        glLineWidth(thickness)
        glBegin(GL_LINES)
        for vertex1, vertex2 in itertools.pairwise(vertices):
            glVertex3fv(vertex1)
            glVertex3fv(vertex2)
        glEnd()

    @staticmethod
    def draw_circle(x: float, y: float, radius: float, color=(1, 1, 1), thickness=3, resolution=100):
        sampling_range = 2 * np.pi * np.arange(0, 1 + 1 / resolution, 1 / resolution)
        circle_at_origin = radius * np.array(
            [np.cos(sampling_range), np.sin(sampling_range), np.zeros_like(sampling_range)],
            dtype=np.float32).transpose()
        translated_circle = np.array([[x, y, 0]], dtype=np.float32) + circle_at_origin
        OpenGLCanvas.draw_lines(translated_circle, color, thickness)

    @staticmethod
    def draw_point(x: float, y: float, color=(1, 1, 1), thickness=3):
        glColor3f(*color)
        glPointSize(thickness)
        glBegin(GL_POINTS)
        glVertex2f(x, y)
        glEnd()


class LoadCurvesButton(wx.Button):
    def __init__(self, parent):
        super().__init__(parent, label="Import Curves")
        self._parent = parent
        self.Bind(wx.EVT_BUTTON, self._open_file_dialog)

    def _open_file_dialog(self, event):
        dialog = wx.FileDialog(parent=self._parent, wildcard="*.dat")
        dialog.ShowModal()
        file_path = dialog.GetPath()
        try:
            curves = import_curves(pathlib.Path(file_path))
            for curve in curves:
                GlobalState.add_curve(curve)
        except Exception as e:
            wx.MessageBox(f"could not load file: {e}")
            return


class SaveCurvesButton(wx.Button):
    def __init__(self, parent):
        super().__init__(parent, label="Save Curves")
        self._parent = parent
        self.Bind(wx.EVT_BUTTON, self._open_file_dialog)

    def _open_file_dialog(self, event):
        dialog = wx.FileDialog(parent=self._parent, wildcard="*.dat")
        dialog.ShowModal()
        file_path = dialog.GetPath()
        try:
            export_curves(path=pathlib.Path(file_path), curves=GlobalState.curves)
        except Exception as e:
            wx.MessageBox(f"could not save file: {e}")


class ToolsRadioBox(wx.RadioBox):
    def __init__(self, parent):
        self.choices = list(Tools.__members__.keys())
        super().__init__(parent=parent, majorDimension=1, choices=self.choices,
                         label="Tool")
        self.Bind(wx.EVT_RADIOBOX, self.switch_tool)

    def switch_tool(self, event):
        GlobalState.switch_tools(getattr(Tools, self.choices[self.GetSelection()]))


class PointWeightTextCtrl(wx.TextCtrl):
    def __init__(self, parent):
        super().__init__(parent=parent, name="Point Weight", style=wx.TE_PROCESS_ENTER)
        self.Disable()
        self.Bind(wx.EVT_TEXT_ENTER, self.set_point_weight)

    def set_point_weight(self, event):
        try:
            value = float(self.GetValue())
        except Exception as e:
            wx.MessageBox(f"could not set weight: {e}")
            return
        selected_curve = GlobalState.curves[GlobalState.selected_curve]
        selected_curve.control_points[GlobalState.selected_point] = \
            *selected_curve.control_points[GlobalState.selected_point][:2], value
        GlobalState.resample_curve(selected_curve)


class NewCurveTypeRadioBox(wx.RadioBox):
    def __init__(self, parent):
        self.choices = list(CurveTypes.__members__.keys())
        super().__init__(parent=parent, majorDimension=1, choices=self.choices,
                         label="Curve Type")
        self.Bind(wx.EVT_RADIOBOX, self.switch_new_curve_type)

    def switch_new_curve_type(self, event):
        GlobalState.new_curve_type = getattr(CurveTypes, self.choices[self.GetSelection()])
        print(GlobalState.new_curve_type)


class NewBSplineCurveSpinCtrl(wx.SpinCtrl):
    def __init__(self, parent):
        super().__init__(parent=parent, initial=3, min=1, max=2**16)
        self.Bind(wx.EVT_SPINCTRL, self.switch_new_b_spline_order)

    def switch_new_b_spline_order(self, event):
        GlobalState.new_curve_order = self.GetValue()
        print(f"New BSpline Order: {GlobalState.new_curve_order}")


class NewBSplineCurveEndConditionRadioBox(wx.RadioBox):
    def __init__(self, parent):
        self.choices = list(EndConditions.__members__.keys())
        super().__init__(parent=parent, majorDimension=1, choices=self.choices,
                         label="Curve Type")
        self.Bind(wx.EVT_RADIOBOX, self.switch_new_curve_end_condition)

    def switch_new_curve_end_condition(self, event):
        GlobalState.new_curve_end_condition = getattr(EndConditions, self.choices[self.GetSelection()])
        print(f"New BSpline end condition: {self.choices[self.GetSelection()]}")


class MainApp(wx.App):
    def OnInit(self) -> bool:
        # for path in itertools.chain(pathlib.Path("./Bsplines/").iterdir(), pathlib.Path("./Beziers/").iterdir()):
        #     try:
        #         curves = import_curves(path)
        #         # print({type(curve) for curve in curves})
        #         print(path)
        #     except Exception as e:
        #         print(f"Failed to import: {path}: {e}")

        window_size = (1280, 720)
        frame = wx.Frame(
            None,
            title="CAGD Bezier and B-Spline Editor",
            size=window_size,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
        )

        frame.SetMaxSize((-1, 720))
        frame.SetMinSize(window_size)

        panel = wx.Panel(parent=frame)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(main_sizer)
        global_controls_sizer = wx.BoxSizer(wx.VERTICAL)

        canvas = OpenGLCanvas(parent=panel)
        main_sizer.Add(canvas, wx.EXPAND)
        main_sizer.Add(global_controls_sizer)

        global_controls_sizer.Add(LoadCurvesButton(parent=panel))
        global_controls_sizer.Add(SaveCurvesButton(parent=panel))
        global_controls_sizer.Add(ToolsRadioBox(parent=panel))
        global_controls_sizer.Add(wx.StaticText(parent=panel, label="Point Weight:"))

        point_weight_text_control = PointWeightTextCtrl(parent=panel)
        global_controls_sizer.Add(point_weight_text_control)

        GlobalState.set_point_weight_text = lambda text: point_weight_text_control.SetValue(text)
        GlobalState.enable_weight_text_control = point_weight_text_control.Enable
        GlobalState.disable_weight_text_control = point_weight_text_control.Disable

        global_controls_sizer.Add(wx.StaticText(parent=panel, label="New Curve Controls:"))
        global_controls_sizer.Add(NewCurveTypeRadioBox(parent=panel))

        new_b_spline_controls = [
            NewBSplineCurveSpinCtrl(parent=panel),
            NewBSplineCurveEndConditionRadioBox(parent=panel),
        ]
        global_controls_sizer.Add(wx.StaticText(parent=panel, label="New BSpline Controls:"))
        for control in new_b_spline_controls:
            global_controls_sizer.Add(control)

        def enable_new_b_spline_controls():
            for control in new_b_spline_controls:
                control.Enable()

        def disable_new_b_spline_controls():
            for control in new_b_spline_controls:
                control.Disable()

        GlobalState.enable_new_b_spline_controls = enable_new_b_spline_controls
        GlobalState.disable_new_b_spline_controls = disable_new_b_spline_controls
        disable_new_b_spline_controls()
        frame.Show()
        return True
