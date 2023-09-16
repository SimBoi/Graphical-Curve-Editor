import math
import pathlib
import itertools
import threading
from typing import Callable, Optional

import wx
from wx import glcanvas

from OpenGL.GL import *

import numpy as np

from cagd_lib.hw1.frenet_curve import import_frenet, FrenetCurve, Domain
from cagd_lib.hw1.infix_tree import InfixTree
from .mouse_look import MouseLook
from .point_select import MousePointSelect


class GlobalStateClass:
    vertices = []
    vertices_torsion = []
    offset_curve_vertices = []
    evolute_vertices = []

    torsion_sigmoid_parameter = 5
    TORSION_MIN_COLOR = np.array([0, 0, 1])
    TORSION_MID_COLOR = np.array([1, 1, 1])
    TORSION_MAX_COLOR = np.array([1, 0, 0])
    UNDEFINED_TORSION_COLOR = (0.3, 0.3, 0.3)
    set_text: Callable[[Optional[any]], None]

    animation_frame_rate = 30

    def __init__(self):
        self._curve = FrenetCurve(
            infix_trees=[InfixTree(b"cos(t)"), InfixTree(b"sin(t)"), InfixTree(b"0")],
            re_parametrization_tree=InfixTree(b"r"),
            domain=[0, 2 * np.pi]
        )
        self._n_samples = 0
        self.selected_point_index: int | None = None
        self.unit_visualization_length: float = 0.3

        self.draw_axes: bool = True
        self.draw_frenet_frame: bool = True
        self.draw_offset_curve: bool = False
        self.draw_curve: bool = True
        self.draw_evolute: bool = False
        self.draw_osculating_circle: bool = False
        self._offset_curve_offset_value: float = 1.0
        self.visualize_torsion: bool = False
        self.visualize_torsion_abs: bool = False

    @property
    def n_samples(self):
        return self._n_samples

    @n_samples.setter
    def n_samples(self, n_samples):
        self._n_samples = n_samples
        self.selected_point_index = None
        self._update_vertices()

    @property
    def curve(self) -> FrenetCurve:
        return self._curve

    @curve.setter
    def curve(self, curve):
        self._curve = curve
        self._update_vertices()

    @property
    def domain_samples(self):
        return [*self._domain_samples]

    @property
    def offset_curve_offset_value(self):
        return self._offset_curve_offset_value

    @offset_curve_offset_value.setter
    def offset_curve_offset_value(self, offset_curve_offset_value):
        self._offset_curve_offset_value = offset_curve_offset_value
        self.offset_curve_vertices.clear()
        self.offset_curve_vertices += [vertex + self.curve.evaluate_normal(r) * offset_curve_offset_value
                                       for r, vertex in zip(self._domain_samples, self.vertices)]

    def _update_vertices(self):
        step = (self.curve.domain.end - self.curve.domain.start) / self.n_samples
        self._domain_samples = list(np.arange(self.curve.domain.start, self.curve.domain.end, step))
        self._domain_samples.append(self.curve.domain.end)
        self.vertices.clear()
        self.vertices_torsion.clear()
        self.vertices += [self.curve.evaluate(r) for r in self._domain_samples]
        self.vertices_torsion += [(self.curve.evaluate_torsion(r) if self.curve.is_torsion_defined(r) else None)
                                  for r in self._domain_samples]

        self.evolute_vertices.clear()
        self.evolute_vertices += [vertex + self.curve.evaluate_curvature_radius(r) * self.curve.evaluate_normal(r)
                                  for r, vertex in zip(self._domain_samples, self.vertices)]

        self.offset_curve_offset_value = self._offset_curve_offset_value

        self.selected_point_index: int | None = None


GlobalState = GlobalStateClass()


class OpenGLCanvas(glcanvas.GLCanvas):
    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, wx.ID_ANY, size=(1120, 681))
        self.init = False

        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)
        glClearColor(0.1, 0.15, 0.1, 1.0)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # mouse look handlers
        self.mouseLook = MouseLook()
        self.Bind(wx.EVT_MOTION, self.mouseLook.MouseMoveEvent)
        self.Bind(wx.EVT_MOUSEWHEEL, self.mouseLook.MouseWheelEvent)
        self.Bind(wx.EVT_RIGHT_DOWN, self.mouseLook.MouseRightDownEvent)
        self.Bind(wx.EVT_RIGHT_UP, self.mouseLook.MouseRightUpEvent)

        # mouse select handlers
        def SelectPoint(index):
            print(f'selected point index = {index}')
            GlobalState.selected_point_index = index

        self.mousePointSelect = MousePointSelect(681, SelectPoint)
        self.mousePointSelect.points = GlobalState.vertices
        self.Bind(wx.EVT_LEFT_DOWN, self.mousePointSelect.MouseLeftDownEvent)

    def OnPaint(self, event):
        if not self.init:
            self.init = True

            def new_paint(event):
                self.OnDraw()

            new_paint(event)

            self.Bind(wx.EVT_PAINT, new_paint)
            self.Bind(wx.EVT_IDLE, new_paint)

    def OnDraw(self):
        glClear(GL_COLOR_BUFFER_BIT)

        # XYZ axes visualization
        if GlobalState.draw_axes:
            self.draw_line((0, 0, 0), (1, 0, 0), (1, 0, 0))
            self.draw_line((0, 0, 0), (0, 1, 0), (0, 1, 0))
            self.draw_line((0, 0, 0), (0, 0, 1), (0, 0, 1))
        if GlobalState.draw_curve:
            if GlobalState.visualize_torsion:
                for (vertex1, torsion1), (vertex2, torsion2) in itertools.pairwise(
                        zip(GlobalState.vertices, GlobalState.vertices_torsion)):
                    if torsion1 is None or torsion2 is None:
                        torsion_color = GlobalState.UNDEFINED_TORSION_COLOR
                    else:
                        torsion_average = (torsion1 + torsion2) / 2
                        if GlobalState.visualize_torsion_abs:
                            torsion_average = abs(torsion_average)
                        normalized_torsion = 2/(1 + np.exp(- GlobalState.torsion_sigmoid_parameter * torsion_average)) - 1
                        interpolation = normalized_torsion
                        if interpolation > 0:
                            torsion_color = GlobalState.TORSION_MID_COLOR * (1 - interpolation)\
                                            + GlobalState.TORSION_MAX_COLOR * interpolation
                        else:
                            interpolation *= -1
                            torsion_color = GlobalState.TORSION_MID_COLOR * (1 - interpolation)\
                                            + GlobalState.TORSION_MIN_COLOR * interpolation

                    self.draw_line(vertex1, vertex2, torsion_color)
            else:
                self.draw_lines(GlobalState.vertices)

        if GlobalState.selected_point_index is not None:
            r = GlobalState.domain_samples[GlobalState.selected_point_index]
            p = GlobalState.vertices[GlobalState.selected_point_index]
            tangent = GlobalState.curve.evaluate_tangent(r) if GlobalState.curve.is_tangent_defined(r) else None
            normal = GlobalState.curve.evaluate_normal(r) if GlobalState.curve.is_normal_defined(r) else None
            bi_normal = GlobalState.curve.evaluate_bi_normal(r) if GlobalState.curve.is_bi_normal_defined(r) else None
            curvature_radius = GlobalState.curve.evaluate_curvature_radius(r) if GlobalState.curve.is_curvature_radius_defined(r) else None

            if GlobalState.draw_frenet_frame:
                if tangent is not None:
                    self.draw_line(p, p + tangent * GlobalState.unit_visualization_length, (0, 0, 1))
                if normal is not None:
                    self.draw_line(p, p + normal * GlobalState.unit_visualization_length, (0, 1, 0))
                if bi_normal is not None:
                    self.draw_line(p, p + bi_normal * GlobalState.unit_visualization_length, (1, 0, 0))

            if GlobalState.draw_osculating_circle:
                if normal is not None and bi_normal is not None and curvature_radius is not None:
                    osculating_circle_center = p + normal * curvature_radius
                    self.draw_circle(osculating_circle_center, curvature_radius, bi_normal, (1, 1, 0))

        # Draw Offset curve
        if GlobalState.draw_offset_curve:
            self.draw_lines(GlobalState.offset_curve_vertices, color=(0.5, 1, 0.5))

        if GlobalState.draw_evolute:
            self.draw_lines(GlobalState.evolute_vertices, color=(1, 0.5, 0.5))

        self.SwapBuffers()

    @staticmethod
    def draw_line(start, end, color=(1, 1, 1), thickness=3):
        OpenGLCanvas.draw_lines([start, end], color, thickness)

    @staticmethod
    def draw_lines(vertices, color=(1, 1, 1), thickness=3):
        glColor3f(*color)
        glLineWidth(thickness)
        glBegin(GL_LINES)
        for vertex1, vertex2 in itertools.pairwise(vertices):
            glVertex3fv(vertex1)
            glVertex3fv(vertex2)
        glEnd()

    def draw_circle(self, center, radius, normal, color=(1, 1, 1), n_samples=200, thickness=3):
        v = np.array(normal) + (
            np.array((1, 1, 0)) if (normal[1] == normal[2] == normal[2] == 0) else np.array((1, 0, 0)))
        u = np.cross(normal, v)
        u = u / np.linalg.norm(u)
        v = np.cross(normal, u)
        angle_samples = list(np.arange(0, 1, 1 / n_samples) * 2 * np.pi)
        angle_samples.append(0)
        c = np.cos(angle_samples) * radius
        s = np.sin(angle_samples) * radius
        points_2d = c.reshape((-1, 1)) * v + s.reshape((-1, 1)) * u
        self.draw_lines(center + points_2d, color, thickness)


class OpenFileButton(wx.Button):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, label="open file", **kwargs)
        self._parent = parent
        self.Bind(wx.EVT_BUTTON, self._open_file_dialog)

    def _open_file_dialog(self, event):
        self._dialog = wx.FileDialog(parent=self._parent, wildcard="*.dat")
        self._dialog.ShowModal()
        file_path = self._dialog.GetPath()
        # TODO: fill this properly
        try:
            GlobalState.curve = import_frenet(pathlib.Path(file_path))
        except Exception as e:
            wx.MessageBox(f"could not open file: {e} ")

        GlobalState.set_text(event)


class ParameterTextControl(wx.TextCtrl):
    def __init__(self, tree_index, *args, **kwargs):
        wx.TextCtrl.__init__(self, *args, value="0", style=wx.TE_PROCESS_ENTER, **kwargs)
        self._tree_index = tree_index
        self.Bind(wx.EVT_TEXT_ENTER, self.update_curve_tree)

    def update_curve_tree(self, event):
        try:
            new_tree = InfixTree(self.GetValue().encode())
        except ValueError as e:
            wx.MessageBox(f"improper infix expression: {e.args[0].decode()}")
            GlobalState.set_text()
            return

        trees = list(GlobalState.curve.infix_trees)
        trees[self._tree_index] = new_tree
        try:
            GlobalState.curve = FrenetCurve(
                infix_trees=trees,
                re_parametrization_tree=GlobalState.curve.re_parametrization_tree,
                domain=GlobalState.curve.domain
            )
        except ValueError as e:
            wx.MessageBox(f"improper infix expression: {e.args[0]}")
            GlobalState.set_text()
            return


class ReParameterizationTextControl(wx.TextCtrl):
    def __init__(self, *args, **kwargs):
        wx.TextCtrl.__init__(self, *args, value="0", style=wx.TE_PROCESS_ENTER, **kwargs)
        self.Bind(wx.EVT_TEXT_ENTER, self.update_curve_tree)

    def update_curve_tree(self, event):
        try:
            new_tree = InfixTree(self.GetValue().encode())
        except ValueError as e:
            wx.MessageBox(f"improper infix expression: {e.args[0].decode()}")
            GlobalState.set_text()
            return

        try:
            GlobalState.curve = FrenetCurve(
                infix_trees=GlobalState.curve.infix_trees,
                re_parametrization_tree=new_tree,
                domain=GlobalState.curve.domain
            )
        except ValueError as e:
            wx.MessageBox(f"improper infix expression: {e.args[0]}")
            GlobalState.set_text()
            return


class DomainTextControl(wx.TextCtrl):
    def __init__(self, *args, new_domain: Callable[[float], Domain], **kwargs):
        wx.TextCtrl.__init__(self, *args, style=wx.TE_PROCESS_ENTER, **kwargs)
        self.Bind(wx.EVT_TEXT_ENTER, self.update_domain_edge)
        self._new_domain = new_domain

    def update_domain_edge(self, event):
        try:
            new_domain_edge_value = float(self.GetValue())
        except ValueError as e:
            wx.MessageBox(f"improper float expression: {e}")
            GlobalState.set_text()
            return

        GlobalState.curve = FrenetCurve(
            infix_trees=GlobalState.curve.infix_trees,
            re_parametrization_tree=GlobalState.curve.re_parametrization_tree,
            domain=self._new_domain(new_domain_edge_value)
        )


class AxesCheckBox(wx.CheckBox):
    def __init__(self, parent):
        super().__init__(parent, label="Axes")
        self.Value = GlobalState.draw_axes

        def switch(event):
            GlobalState.draw_axes = not GlobalState.draw_axes

        self.Bind(wx.EVT_CHECKBOX, switch)


class FrenetFrameCheckBox(wx.CheckBox):
    def __init__(self, parent):
        super().__init__(parent, label="Frenet Frame")
        self.Value = GlobalState.draw_frenet_frame

        def switch(event):
            GlobalState.draw_frenet_frame = not GlobalState.draw_frenet_frame

        self.Bind(wx.EVT_CHECKBOX, switch)


class OsculatingCircleCheckBox(wx.CheckBox):
    def __init__(self, parent):
        super().__init__(parent, label="Osculating Circle")

        def switch(event):
            GlobalState.draw_osculating_circle = not GlobalState.draw_osculating_circle

        self.Bind(wx.EVT_CHECKBOX, switch)


class CurveCheckBox(wx.CheckBox):
    def __init__(self, parent):
        super().__init__(parent, label="Curve")
        self.Value = True

        def switch(event):
            GlobalState.draw_curve = not GlobalState.draw_curve

        self.Bind(wx.EVT_CHECKBOX, switch)


class EvoluteCheckBox(wx.CheckBox):
    def __init__(self, parent):
        super().__init__(parent, label="Evolute")

        def switch(event):
            GlobalState.draw_evolute = not GlobalState.draw_evolute

        self.Bind(wx.EVT_CHECKBOX, switch)


class OffsetCurveCheckBox(wx.CheckBox):
    def __init__(self, parent):
        super().__init__(parent, label="Offset Curve")

        def switch(event):
            GlobalState.draw_offset_curve = not GlobalState.draw_offset_curve

        self.Bind(wx.EVT_CHECKBOX, switch)


class TorsionCheckBox(wx.CheckBox):
    def __init__(self, parent):
        super().__init__(parent, label="Torsion")

        def switch(event):
            GlobalState.visualize_torsion = not GlobalState.visualize_torsion

        self.Bind(wx.EVT_CHECKBOX, switch)


class TorsionAbsCheckBox(wx.CheckBox):
    def __init__(self, parent):
        super().__init__(parent, label="ABS Torsion")

        def switch(event):
            GlobalState.visualize_torsion_abs = not GlobalState.visualize_torsion_abs

        self.Bind(wx.EVT_CHECKBOX, switch)


class OffsetCurveTextControl(wx.TextCtrl):
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent=parent, style=wx.TE_PROCESS_ENTER,
                             value=str(GlobalState.offset_curve_offset_value))
        self.Bind(wx.EVT_TEXT_ENTER, self.update_offset_curve_offset_value)

    def update_offset_curve_offset_value(self, event):
        try:
            new_offset_curve_offset_value = float(self.GetValue())
        except ValueError as e:
            wx.MessageBox(f"improper float expression: {e}")
            GlobalState.set_text()
            return

        GlobalState.offset_curve_offset_value = new_offset_curve_offset_value


class AnimateCheckBox(wx.CheckBox):
    def __init__(self, parent, widgets_to_disable=None):
        if widgets_to_disable is None:
            widgets_to_disable = []
        super().__init__(parent, label="Animate")

        widgets_to_disable = [w for w in widgets_to_disable if w is not self]

        def switch_animation_global_state(event):
            if self.Value:
                for widget in widgets_to_disable:
                    widget.Disable()

                def next_keyframe():
                    frame_rate = GlobalState.animation_frame_rate
                    increment_size = 1
                    if GlobalState.animation_frame_rate > 60:
                        increment_size = math.ceil(frame_rate / 60)
                        frame_rate = 60

                    if GlobalState.selected_point_index is None:
                        GlobalState.selected_point_index = 0
                    else:
                        GlobalState.selected_point_index += increment_size
                        GlobalState.selected_point_index %= GlobalState.n_samples
                    self.Refresh()
                    self.animation_thread = threading.Timer(1 / frame_rate, next_keyframe)
                    self.animation_thread.start()

                self.animation_thread = threading.Timer(0, next_keyframe)
                self.animation_thread.start()
            else:
                self.animation_thread.cancel()
                if self.animation_thread.is_alive():
                    self.animation_thread.join()

                for widget in widgets_to_disable:
                    widget.Enable()

        self.Bind(wx.EVT_CHECKBOX, switch_animation_global_state)


class MainApp(wx.App):
    def OnInit(self):
        # Define frame

        window_size = (1280, 720)
        frame = wx.Frame(
            None,
            title="CAGD Curve Visualizer",
            size=window_size,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
        )

        frame.SetMaxSize((-1, 720))
        frame.SetMinSize(window_size)
        # Define panel

        panel = wx.Panel(parent=frame)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer = wx.BoxSizer(wx.VERTICAL)
        canvas = OpenGLCanvas(parent=panel)
        main_sizer.Add(canvas)
        main_sizer.Add(controls_sizer)

        # Text curve controls

        def set_text(event=None):
            for i, text_control in enumerate([text_control_x, text_control_y, text_control_z]):
                text_control.SetValue(str(GlobalState.curve.infix_trees[i]))
            text_control_r.Value = str(GlobalState.curve.re_parametrization_tree)
            domain_start_text_control.Value = str(GlobalState.curve.domain.start)
            domain_end_text_control.Value = str(GlobalState.curve.domain.end)
            text_control_offset_curve_offset_value = str(GlobalState.offset_curve_offset_value)

        GlobalState.set_text = set_text

        text_control_x = ParameterTextControl(parent=panel, tree_index=0)
        text_control_y = ParameterTextControl(parent=panel, tree_index=1)
        text_control_z = ParameterTextControl(parent=panel, tree_index=2)
        text_control_r = ReParameterizationTextControl(parent=panel)

        controls_sizer.Add(wx.StaticText(parent=panel, label="X(t):"))
        controls_sizer.Add(text_control_x, )
        controls_sizer.Add(wx.StaticText(parent=panel, label="Y(t):"))
        controls_sizer.Add(text_control_y)
        controls_sizer.Add(wx.StaticText(parent=panel, label="Z(t):"))
        controls_sizer.Add(text_control_z)

        controls_sizer.Add(wx.StaticText(parent=panel, label="Re-Parameterization"))
        controls_sizer.Add(wx.StaticText(parent=panel, label="t(r):"))
        controls_sizer.Add(text_control_r)

        controls_sizer.Add(wx.StaticText(parent=panel, label="Domain start:"))

        domain_start_text_control = DomainTextControl(
            parent=panel, value=str(GlobalState.curve.domain.start),
            new_domain=lambda value: Domain(value, GlobalState.curve.domain.end)
        )
        controls_sizer.Add(domain_start_text_control)

        controls_sizer.Add(wx.StaticText(parent=panel, label="Domain end:"))
        domain_end_text_control = DomainTextControl(
            parent=panel, value=str(GlobalState.curve.domain.start),
            new_domain=lambda value: Domain(GlobalState.curve.domain.start, value)
        )
        controls_sizer.Add(domain_end_text_control)

        set_text()

        # n_samples logarithmic slider

        control_n_samples = wx.Slider(
            parent=panel, style=wx.SL_HORIZONTAL, minValue=0, maxValue=100, value=50,
            name="N Samples"
        )

        def update_n_samples(event):
            GlobalState.n_samples = 1 + int(1.11 ** control_n_samples.GetValue())  # Logarithmic values

        control_n_samples.Bind(wx.EVT_SLIDER, update_n_samples)
        controls_sizer.Add(wx.StaticText(parent=panel, label="N Samples Slider"))
        controls_sizer.Add(control_n_samples)

        # Open file definition
        open_file_button = OpenFileButton(parent=panel)

        # Animate checkbox
        animate_checkbox = AnimateCheckBox(parent=panel, widgets_to_disable=[
            widget for widget in panel.Children
            if hasattr(widget, "Disable") and hasattr(widget, "Enable") and widget is not canvas
        ])
        controls_sizer.Add(animate_checkbox)

        # Animation frame rate slider
        control_animation_frame_rate = wx.Slider(
            parent=panel, style=wx.SL_HORIZONTAL, minValue=1, maxValue=100, value=50,
            name="Animation frame rate"
        )

        def update_animation_frame_rate(event):
            GlobalState.animation_frame_rate = int(
                1.11 ** control_animation_frame_rate.GetValue())  # Logarithmic values

        control_animation_frame_rate.Bind(wx.EVT_SLIDER, update_animation_frame_rate)
        controls_sizer.Add(wx.StaticText(parent=panel, label="Animation Frame Rate Slider"))
        controls_sizer.Add(control_animation_frame_rate)

        # Axes checkbox
        axes_checkbox = AxesCheckBox(parent=panel)
        controls_sizer.Add(axes_checkbox)

        # Frenet Frame checkbox
        frenet_frame_checkbox = FrenetFrameCheckBox(parent=panel)
        controls_sizer.Add(frenet_frame_checkbox)

        # Osculating Circle checkbox
        osculating_circle_checkbox = OsculatingCircleCheckBox(parent=panel)
        controls_sizer.Add(osculating_circle_checkbox)

        # Evolute checkbox
        curve_checkbox = CurveCheckBox(parent=panel)
        controls_sizer.Add(curve_checkbox)

        # Evolute checkbox
        evolute_checkbox = EvoluteCheckBox(parent=panel)
        controls_sizer.Add(evolute_checkbox)

        # Offset Curve checkbox
        offset_curve_checkbox = OffsetCurveCheckBox(parent=panel)
        controls_sizer.Add(offset_curve_checkbox)

        controls_sizer.Add(wx.StaticText(parent=panel, label="Offset:"))
        text_control_offset_curve_offset_value = OffsetCurveTextControl(parent=panel)
        controls_sizer.Add(text_control_offset_curve_offset_value)

        # Torsion checkbox
        torsion_checkbox = TorsionCheckBox(parent=panel)
        controls_sizer.Add(torsion_checkbox)

        torsion_abs_checkbox = TorsionAbsCheckBox(parent=panel)
        controls_sizer.Add(torsion_abs_checkbox)

        # torsion visualization intensity slider
        control_torsion_visualization_intensity = wx.Slider(
            parent=panel, style=wx.SL_HORIZONTAL, minValue=0, maxValue=100, value=10,
            name="Torsion visualization intensity"
        )

        def update_torsion_visualization_intensity(event):
            GlobalState.torsion_sigmoid_parameter = 1.05 ** control_torsion_visualization_intensity.GetValue() - 0.9  # Logarithmic values

        control_torsion_visualization_intensity.Bind(wx.EVT_SLIDER, update_torsion_visualization_intensity)
        controls_sizer.Add(wx.StaticText(parent=panel, label="Torsion Visualization Intensity Slider"))
        controls_sizer.Add(control_torsion_visualization_intensity)

        # Open file
        controls_sizer.Add(open_file_button)

        panel.SetSizer(main_sizer)

        frame.Show()
        # print("PANEL SIZE:")
        # print(panel.GetSize())

        update_n_samples(None)
        return True
