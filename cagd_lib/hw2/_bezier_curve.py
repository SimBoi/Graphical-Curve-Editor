from typing import Sequence

import numpy as np
import math

__all__ = [
    "evaluate_bezier",
]


def bernstein_basis(n: int, k: int, t: np.ndarray):
    return math.comb(n, k) * (t ** k) * (1 - t) ** (n - k)


def evaluate_bernstein(control_points: Sequence, weights: np.ndarray, t: np.ndarray):
    n = len(control_points) - 1

    evaluated_basis = np.array([bernstein_basis(n, k, t) for k in range(n + 1)]).reshape((n + 1, t.size)).transpose()
    weighted_evaluated_basis = weights * evaluated_basis
    normalized_weighted_evaluated_basis = \
        weighted_evaluated_basis / weighted_evaluated_basis.sum(axis=1).reshape((-1, 1))
    return normalized_weighted_evaluated_basis @ control_points


def evaluate_bezier(control_points: np.ndarray, t: np.ndarray):
    """

    :param control_points: N control points where each point is x, y, and weight in respective order (N x 3).
    :param t: sampling points (T x 1)
    :return:
    """
    return evaluate_bernstein(control_points[:, :2], control_points[:, 2], t)
