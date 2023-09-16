import math
from itertools import pairwise

import numpy as np
from OpenGL.GLU import *

# distance functions
dist2D = lambda p1, p2: math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


class Line:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def eval(self, t):
        return self.p1 * (1 - t) + self.p2 * t


def distance(v: np.ndarray, w: np.ndarray):
    return np.linalg.norm(v - w)


def minimumDistance(v: np.ndarray, w: np.ndarray, p: np.ndarray):
    """
    returns distance between point p and line segment between points v and w
    """
    l2 = np.sum((v - w)**2)
    if l2 == 0.0:
        return distance(p, v)
    t = max(0, min(1, np.dot(p - v, w - v) / l2))
    projection = v + t * (w - v)
    return distance(p, projection)


class MouseSelect:
    def __init__(self, screenHeight, curvesSamples):
        self.curvesSamples = curvesSamples
        self.curveSamples = None
        self.controlPoints = None
        self.selectionRadius = 5
        self.screenHeight = screenHeight
        self.selectionHandler = None
        self.secondarySelectionHandler = None

    def SelectCurveEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        if self.curvesSamples is None:
            event.Skip()
            return

        mousePosition = [*event.GetPosition(), 0]
        mousePosition[1] = -(mousePosition[1] - self.screenHeight)
        mousePosition = np.array(mousePosition)

        for i, curveSamples in enumerate(self.curvesSamples):
            screenPoints = [np.array(gluProject(*p)) for p in curveSamples]
            for p1, p2 in pairwise(screenPoints):
                if minimumDistance(p1, p2, mousePosition) <= self.selectionRadius:
                    self.selectionHandler(i)
                    event.Skip()
                    return

        self.selectionHandler(None)
        event.Skip()

    def SelectPointEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        if self.controlPoints is None:
            event.Skip()
            return

        screenPoints = [gluProject(*p) for p in self.controlPoints]
        mousePosition = event.GetPosition()
        mousePosition[1] = -(mousePosition[1] - self.screenHeight)

        for i, screenPoint in enumerate(screenPoints):
            if dist2D(mousePosition, screenPoint) <= self.selectionRadius:
                self.selectionHandler(i)
                event.Skip()
                return

        self.selectionHandler(None)
        event.Skip()

    def SelectSampleEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        if self.curveSamples is None:
            event.Skip()
            return

        mousePosition = [*event.GetPosition(), 0]
        mousePosition[1] = -(mousePosition[1] - self.screenHeight)
        mousePosition = np.array(mousePosition)

        screenPoints = [np.array(gluProject(*p)) for p in self.curveSamples]
        for i, screenPoint in enumerate(screenPoints):
            if dist2D(mousePosition, screenPoint) <= self.selectionRadius:
                self.secondarySelectionHandler(i)
                event.Skip()
                return

        self.secondarySelectionHandler(None)
        event.Skip()

    def InRange(self, event):
        mousePosition = event.GetPosition()
        return (self.screenHeight - mousePosition[1]) <= (self.screenHeight - 50)
