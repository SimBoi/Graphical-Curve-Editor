import math
from OpenGL.GLU import gluUnProject, gluProject


# distance functions
dist2D = lambda p1, p2: math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


class MouseAddDelete:
    def __init__(self, screenHeight, AddPointHandler, DeletePointHandler, CreateNewCurve):
        self.controlPoints = None
        self.selectionRadius = 5
        self.screenHeight = screenHeight
        self.AddPointHandler = AddPointHandler
        self.DeletePointHandler = DeletePointHandler
        self.CreateNewCurve = CreateNewCurve

    # add point
    def MouseLeftDownEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        if self.controlPoints is None:
            self.CreateNewCurve()
        self.AddPoint(event.GetPosition())
        event.Skip()

    def AddPoint(self, mousePosition):
        mousePosition[1] = -(mousePosition[1] - self.screenHeight)
        self.AddPointHandler(gluUnProject(mousePosition[0], mousePosition[1], 0))

    # delete point
    def MouseRightDownEvent(self, event):
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
                self.DeletePointHandler(i)
                event.Skip()
                return

        event.Skip()

    def InRange(self, event):
        mousePosition = event.GetPosition()
        return (self.screenHeight - mousePosition[1]) <= (self.screenHeight - 50)
