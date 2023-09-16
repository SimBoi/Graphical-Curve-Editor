import math

from OpenGL.GLU import *
from OpenGL.GL import *


clamp = lambda x, m, M: max(m, min(x, M))


class MouseLook:
    def __init__(self):
        self.sensitivity = 1
        self.lookDegrees = [0, 0]
        self.prevMousePosition = None
        self.dragging = False
        self.zoom = 10
        self.zoomSensitivity = 1.3
        self.zoomRange = [0.01, 100]
        self.UpdateCameraTransform()

    def MouseMoveEvent(self, event):
        if not self.dragging:
            return

        newMousePosition = event.GetPosition()

        if self.prevMousePosition is None:
            self.prevMousePosition = newMousePosition
            return

        self.lookDegrees += (newMousePosition - self.prevMousePosition) * self.sensitivity
        self.lookDegrees[1] = clamp(self.lookDegrees[1], -90, 90)
        self.lookDegrees[0] = self.lookDegrees[0] % 360
        self.UpdateCameraTransform()

        self.prevMousePosition = newMousePosition

    def MouseRightDownEvent(self, event):
        self.prevMousePosition = None
        self.dragging = True

    def MouseRightUpEvent(self, event):
        self.dragging = False

    def MouseWheelEvent(self, event):
        scroll = event.GetWheelRotation()
        if scroll == 0:
            return
        self.zoom *= 1/self.zoomSensitivity if scroll > 0 else self.zoomSensitivity
        self.zoom = clamp(self.zoom, *self.zoomRange)
        self.UpdateCameraTransform()

    def UpdateCameraTransform(self):
        equator_x = math.cos(math.radians(self.lookDegrees[0]))
        equator_z = math.sin(math.radians(self.lookDegrees[0]))
        y = math.sin(math.radians(self.lookDegrees[1])) * self.zoom
        multiplier = math.cos(math.radians(self.lookDegrees[1]))
        x = multiplier * equator_x * self.zoom
        z = multiplier * equator_z * self.zoom
        glLoadIdentity()
        gluPerspective(90, 1120 / 630, 0.001, 1000)
        gluLookAt(x, y, z, 0, 0, 0, 0, 1, 0)
