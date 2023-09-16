import bisect
import math
from typing import List

from OpenGL.GLU import gluProject


# distance functions
dist2D = lambda p1, p2: math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


class KnotEditor:
    def __init__(self):
        self.padding = 10
        self.screenHeight = 680
        self.screenWidth = 1120
        self.minKnot = None
        self.maxKnot = None
        self.knotVector = None
        self.selectionRadius = 5
        self.editHandler = None

    def MouseLeftEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        if self.knotVector is None:
            event.Skip()
            return

        mousePosition = event.GetPosition()[0]
        knot = ((mousePosition - self.padding) / (self.screenWidth - 2 * self.padding)) * (self.maxKnot - self.minKnot) + self.minKnot

        bisect.insort(self.knotVector, knot)
        self.editHandler()

        event.Skip()

    def MouseRightEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        if self.knotVector is None or len(self.knotVector) <= 2:
            event.Skip()
            return

        points = [((knot - self.minKnot) / (self.maxKnot - self.minKnot)) * (self.screenWidth - 2*self.padding) + self.padding for knot in self.knotVector]
        mousePosition = event.GetPosition()[0]

        for i, point in enumerate(points):
            if i == 0 or i == len(points) - 1:
                continue
            if point - self.selectionRadius < mousePosition < point + self.selectionRadius:
                self.knotVector.pop(i)
                self.editHandler()
                event.Skip()
                return

        event.Skip()

    def InRange(self, event):
        mousePosition = event.GetPosition()
        return (self.screenHeight - mousePosition[1]) > (self.screenHeight - 50)
