from typing import Sequence

import numpy as np
import math


def omega(i: int, k: int, knot_vector, t):
    if knot_vector[i + k] == knot_vector[i]:
        return np.zeros_like(t)

    return (t - knot_vector[i]) / (knot_vector[i + k] - knot_vector[i])


def B(i, k, knot_vector, t):
    result = np.empty_like(t)
    if i + k + 1 == len(knot_vector):
        is_in_range = (knot_vector[i] <= t) & (t < knot_vector[i + k + 1])
    else:
        is_in_range = (knot_vector[i] <= t) & (t <= knot_vector[i + k + 1])

    result[np.logical_not(is_in_range)] = 0

    if k == 0:
        result[is_in_range] = 1
        return result

    t_in_range = t[is_in_range]
    if t_in_range.size == 0:
        return result

    left_term = omega(i, k, knot_vector, t_in_range) * B(i, k - 1, knot_vector, t_in_range)
    right_term = (1 - omega(i + 1, k, knot_vector, t_in_range)) * B(i + 1, k - 1, knot_vector, t_in_range)
    result[is_in_range] = left_term + right_term
    return result


def _evaluate_b_spline(control_points: Sequence, weights: np.ndarray, knot_vector, order, t: np.ndarray):
    n = len(control_points) - 1

    evaluated_basis = \
        np.array([B(i, order - 1, knot_vector, t) for i in range(n + 1)]).reshape((n + 1, t.size)).transpose()
    weighted_evaluated_basis = weights * evaluated_basis
    normalized_weighted_evaluated_basis = \
        weighted_evaluated_basis / weighted_evaluated_basis.sum(axis=1).reshape((-1, 1))
    return normalized_weighted_evaluated_basis @ control_points


def evaluate_b_spline(control_points: np.ndarray, knot_vector, order, t: np.ndarray):
    return _evaluate_b_spline(control_points[:, :2], control_points[:, 2], knot_vector, order, t)
