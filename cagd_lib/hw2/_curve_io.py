import itertools
import pathlib
from dataclasses import dataclass
from typing import NamedTuple, Sequence, MutableSequence

import wx


@dataclass
class BezierCurve:
    order: int
    control_points: MutableSequence[tuple[float, float, float]]


@dataclass
class BSpline:
    order: int
    knots: MutableSequence[float]
    control_points: MutableSequence[tuple[float, float, float]]


def _parse_control_point_line(line: str) -> tuple[float, float, float]:
    split_line = line.split()
    if len(split_line) == 2:
        x, y, w = (*split_line, 1.0)
    elif len(split_line) == 3:
        x, y, w = split_line
    else:
        raise ValueError(line)

    w = float(w)
    return float(x) / w, float(y) / w, w


def import_curves(path: pathlib.Path) -> Sequence[BezierCurve | BSpline]:
    with open(path.resolve(), "r") as f:
        lines = []
        for line in f.readlines():
            split_line = line.split()
            if len(split_line) == 0:
                continue
            if split_line[0].startswith("#"):
                continue
            lines.append(line.replace("\n", ""))

        curves = []
        lines_iterator = iter(lines)

        try:
            line = next(lines_iterator)
        except StopIteration:
            return curves

        while True:
            split_line = line.split()
            assert len(split_line) == 1
            order = int(split_line[0])

            line = next(lines_iterator)
            split_line = line.split()
            if split_line[0].startswith("knots"):  # BSPLINE CURVE
                curve = BSpline(order=order, knots=[], control_points=[])
                n_knots = int(line[line.find("[") + 1: line.find("]")])
                curve.knots.extend([float(knot_str) for knot_str in line[line.find("=") + 1:].split()])
                while len(curve.knots) < n_knots:
                    line = next(lines_iterator)
                    curve.knots.extend([float(knot_str) for knot_str in line.split()])
                assert len(curve.knots) == n_knots

                line = next(lines_iterator)
                split_line = line.split()
                while len(split_line) > 1:
                    curve.control_points.append(_parse_control_point_line(line))
                    try:
                        line = next(lines_iterator)
                    except StopIteration:
                        curves.append(curve)
                        return curves
                    split_line = line.split()
                curves.append(curve)
            else:  # BEZIER CURVE
                curve = BezierCurve(order=order, control_points=[_parse_control_point_line(line)])
                for _ in range(1, order):
                    line = next(lines_iterator)
                    curve.control_points.append(_parse_control_point_line(line))

                curves.append(curve)

                try:
                    line = next(lines_iterator)
                except StopIteration:
                    return curves


def export_curves(path: pathlib.Path, curves: Sequence[BezierCurve | BSpline]):
    with open(path.resolve(), "w") as f:
        for curve in curves:
            f.write(f"{curve.order}\n")

            if isinstance(curve, BSpline):
                f.write(f"knots[{len(curve.knots)}] = \n")
                for knot in curve.knots:
                    f.write(f"{knot}\n")

            for control_point in curve.control_points:
                w = control_point[2]
                f.write(f"{control_point[0] * w} {control_point[1] * w} {w}\n")