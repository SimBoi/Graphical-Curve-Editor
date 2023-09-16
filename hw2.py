from cagd_lib.hw2 import MainApp


if __name__ == '__main__':
    MainApp().MainLoop()

# TODO: mustafa edition
#   1. add weights support in evaluation [DONE]
#   2. Evaluate and display B-spline curves [DONE]
#   3. open-ended/floating-ended support (button + evaluation) [DONE]
#   4. B-spline degree message box [DONE] (included in 7)
#   5. point weight slider [DONE]
#   6. tool radio button \ drop down [DONE]
#   7. add new curve type and curve order input fields [DONE]
#
# TODO: hamza edition
#   1. move tool [DONE]
#   2. add/delete tool [DONE]
#   3. graphical editing of the knot vector [DONE]
#   4. end conditions [DONE]
#   5. connect curves tool
#
# TODO:
#   additional feature

# features:
# Load data files of rational and polynomial 2D curve(s) descriptions [DONE]
# Evaluate and display Bezier curves [DONE]
# Evaluate and display B-spline curves
# Allow for a choice of open-end or floating end conditions of a B-spline curve
# Allow setting the degree of the B-spline curve to be created
# Display the control polygons of both types of curves
# Allow modifications (position and weight) of existing control points
# Allow insertion and deletion of control points
# Any modification should be interactive and interactively displayed [DONE]
# For B-spline curves, allow graphical editing of the knot vector: insert, delete, modify
# Allow the handling of multiple curves simultaneously in the scene [DONE]
# Select and implement one of the additional options
