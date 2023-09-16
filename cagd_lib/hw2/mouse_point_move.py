from OpenGL.GLU import gluUnProject


class MousePointMove:
    def __init__(self, screenHeight, pointMoveHandler):
        self.screenHeight = screenHeight
        self.pointMoveHandler = pointMoveHandler
        self.dragging = False

    def MouseMoveEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        if not self.dragging:
            event.Skip()
            return
        self.MovePoint(event.GetPosition())
        event.Skip()

    def MouseLeftDownEvent(self, event):
        if not self.InRange(event):
            event.Skip()
            return
        self.dragging = True
        self.MovePoint(event.GetPosition())
        event.Skip()

    def MouseLeftUpEvent(self, event):
        self.dragging = False
        event.Skip()

    def MovePoint(self, mousePosition):
        mousePosition[1] = -(mousePosition[1] - self.screenHeight)
        self.pointMoveHandler(gluUnProject(mousePosition[0], mousePosition[1], 0))

    def InRange(self, event):
        mousePosition = event.GetPosition()
        return (self.screenHeight - mousePosition[1]) <= (self.screenHeight - 50)
