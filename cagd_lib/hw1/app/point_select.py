import math
import time
from OpenGL.GLU import *

# distance functions
euclidean2D = lambda p1, p2: math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
manhattan2D = lambda p1, p2: max(p1[0] - p2[0], p1[1] - p2[1], p2[0] - p1[0], p2[1] - p1[1])
dist2D = euclidean2D


class MousePointSelect:
    def __init__(self, screenHeight, selectionHandler):
        self.points = None
        self.selectionRadius = 5
        self.screenHeight = screenHeight
        self.selectionHandler = selectionHandler

    def MouseLeftDownEvent(self, event):
        if self.points is None:
            return

        screenPoints = [gluProject(*p) for p in self.points]
        mousePosition = event.GetPosition()
        mousePosition[1] = -(mousePosition[1] - self.screenHeight)

        # within the radius of the mouse position, get the index of the point closest to the camera (highest z value)
        nearest = None
        for i, screenPoint in enumerate(screenPoints):
            if dist2D(mousePosition, screenPoint) <= self.selectionRadius:
                if nearest is None or screenPoint[2] < screenPoints[nearest][2]:
                    nearest = i

        self.selectionHandler(nearest)
