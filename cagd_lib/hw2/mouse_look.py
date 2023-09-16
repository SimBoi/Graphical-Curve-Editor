import numpy as np
from OpenGL.GLU import *
from OpenGL.GL import *


clamp = lambda x, m, M: max(m, min(x, M))
MOUSE_INVERT = np.array((1, -1))


class MouseLook:
    def __init__(self):
        self.position = np.array((0, 0), dtype=np.float32)
        self.prevMousePosition = None
        self.dragging = False
        self.zoom = 0.005
        self.zoomSensitivity = 1.3
        self.zoomRange = [0.000001, 10]
        self.screenHeight = 680
        self.UpdateCameraTransform()

    def MouseMoveEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        if not self.dragging:
            event.Skip()
            return

        newMousePosition = event.GetPosition()

        if self.prevMousePosition is None:
            self.prevMousePosition = newMousePosition
            event.Skip()
            return

        deltaMousePosition = np.array(newMousePosition - self.prevMousePosition, dtype=np.float32) * MOUSE_INVERT
        self.position += deltaMousePosition * self.zoom
        self.UpdateCameraTransform()

        self.prevMousePosition = newMousePosition
        event.Skip()

    def MouseMiddleDownEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        self.prevMousePosition = None
        self.dragging = True
        event.Skip()

    def MouseMiddleUpEvent(self, event):
        self.dragging = False
        event.Skip()

    def MouseWheelEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        scroll = event.GetWheelRotation()
        if scroll == 0:
            event.Skip()
            return
        self.zoom *= 1/self.zoomSensitivity if scroll > 0 else self.zoomSensitivity
        self.zoom = clamp(self.zoom, *self.zoomRange)
        self.UpdateCameraTransform()
        event.Skip()

    def UpdateCameraTransform(self):
        glLoadIdentity()
        orthoPlanes = np.array((-560, 560, -340, 340), dtype=np.float32) * self.zoom
        gluOrtho2D(*orthoPlanes)
        glTranslate(*self.position, 0)

    def InRange(self, event):
        mousePosition = event.GetPosition()
        return (self.screenHeight - mousePosition[1]) <= (self.screenHeight - 50)
