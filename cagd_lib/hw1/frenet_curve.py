from typing import Sequence, NamedTuple

import numpy as np

from cagd_lib.hw1.infix_tree import InfixTree, Variables as v, Variables
import pathlib

epsilon = 1e-6
is_epsilon = lambda x: -epsilon <= x <= epsilon


def import_frenet(path: pathlib.Path) -> 'FrenetCurve':
    expressions = []
    with open(path.resolve()) as f:
        lines = [line.replace('\n', '') for line in f.readlines()]
        row = 1
        for line in lines:
            if line == '' or line[0] == '#':
                continue
            if row == 1:
                expressions.append(line)
            elif row == 2:
                expressions.append(line)
            elif row == 3:
                expressions.append(line)
            elif row == 4:
                line = line.split()
                if line[0][-1] == ',':
                    line[0] = line[0][:-1]
                domain = [float(line[0]), float(line[1])]
            else:
                break
            row += 1
    return FrenetCurve([InfixTree(e.encode()) for e in expressions], InfixTree(b"r"), domain)


class Domain(NamedTuple):
    start: float
    end: float


class XYZInfixTree(NamedTuple):
    x: InfixTree
    y: InfixTree
    z: InfixTree

    def cross(self, other):
        # a x b = [(a.y*b.z - a.z*b.y), (a.z*b.x - a.x*b.z), (a.x*b.y - a.y*b.x)]
        return XYZInfixTree(*np.cross(self, other))


class FrenetCurve:
    def __init__(self, infix_trees: XYZInfixTree | tuple[InfixTree, InfixTree, InfixTree] | Sequence[InfixTree],
                 re_parametrization_tree: InfixTree,
                 domain: Domain | tuple[float, float] | Sequence[float]):

        # Input checks: curve trees are only of T and re-parameterization tree is only of R
        for tree in infix_trees:
            for variable in Variables:
                if variable == Variables.T or variable == variable.Z1 or variable == variable.ALL:
                    continue

                if variable in tree:
                    raise ValueError(variable.name)

        for variable in Variables:
            if variable == Variables.R or variable == variable.Z1 or variable == variable.ALL:
                continue

            if variable in re_parametrization_tree:
                raise ValueError(variable.name)
        # end of input checks

        self.infix_trees = infix_trees
        self._re_parametrization_tree = re_parametrization_tree
        self._reparametrized_trees = XYZInfixTree(
            *[infix_tree.re_parametrize(re_parametrization_tree, v.T) for infix_tree in infix_trees])

        self.domain = Domain(*domain)

        # re parametrized curve C(t(r))
        self.dC_trees = XYZInfixTree(
            *[infix_tree.calculate_derivative(v.R) for infix_tree in self._reparametrized_trees])
        self.ddC_trees = XYZInfixTree(*[infix_tree.calculate_derivative(v.R) for infix_tree in self.dC_trees])
        self.dddC_trees = XYZInfixTree(*[infix_tree.calculate_derivative(v.R) for infix_tree in self.ddC_trees])
        self.dC_norm_tree = InfixTree.norm(self.dC_trees)
        self.dC_x_ddC_trees = XYZInfixTree.cross(self.dC_trees, self.ddC_trees)
        self.dC_x_ddC_norm_tree = InfixTree.norm(self.dC_x_ddC_trees)

        # T = dC / ||dC||
        self._T_trees = XYZInfixTree(*[tree / self.dC_norm_tree for tree in self.dC_trees])
        # self._dT_trees = XYZInfixTree(*[infix_tree.calculate_derivative(v.R) for infix_tree in self._T_trees])

        # B = (dC x ddC) / ||dC x ddC||
        self._B_trees = XYZInfixTree(*[tree / self.dC_x_ddC_norm_tree for tree in self.dC_x_ddC_trees])
        # self._dB_trees = XYZInfixTree(*[infix_tree.calculate_derivative(v.R) for infix_tree in self._B_trees])

        # kappa = ||dC x ddC|| / ||dC||^3
        self._kappa_tree = self.dC_x_ddC_norm_tree / self.dC_norm_tree ** InfixTree(b'3')
        self._osculating_circle_radius_tree = InfixTree(b'1') / self._kappa_tree

        # N = B x T
        self._N_trees = XYZInfixTree.cross(self._B_trees, self._T_trees)
        # self._dN_trees = XYZInfixTree(*[infix_tree.calculate_derivative(v.R) for infix_tree in self._N_trees])

        # tau = -dB / N
        self._tau_tree = InfixTree.dot(self.dC_x_ddC_trees, self.dddC_trees) / self.dC_x_ddC_norm_tree ** InfixTree(
            b'2')

    @property
    def re_parametrization_tree(self):
        return self._re_parametrization_tree

    def evaluate(self, r: float):
        InfixTree.r = r
        return np.array([tree() for tree in self._reparametrized_trees])

    def is_tangent_defined(self, r: float):
        InfixTree.r = r
        return not is_epsilon(self.dC_norm_tree())

    def evaluate_tangent(self, r: float):
        InfixTree.r = r
        return np.array([tree() for tree in self._T_trees])

    def is_curvature_defined(self, r: float):
        InfixTree.r = r
        return not is_epsilon(self.dC_norm_tree())

    def evaluate_curvature(self, r: float):
        InfixTree.r = r
        return self._kappa_tree()

    def is_curvature_radius_defined(self, r: float):
        InfixTree.r = r
        return self.is_curvature_defined(r) and not is_epsilon(self._kappa_tree())

    def evaluate_curvature_radius(self, r: float):
        InfixTree.r = r
        return self._osculating_circle_radius_tree()

    def is_normal_defined(self, r: float):
        return self.is_bi_normal_defined(r) and self.is_tangent_defined(r)

    def evaluate_normal(self, r: float):
        InfixTree.r = r
        return np.array([tree() for tree in self._N_trees])

    def is_bi_normal_defined(self, r: float):
        InfixTree.r = r
        return not is_epsilon(self.dC_x_ddC_norm_tree())

    def evaluate_bi_normal(self, r: float):
        InfixTree.r = r
        return np.array([tree() for tree in self._B_trees])

    def is_torsion_defined(self, r: float):
        InfixTree.r = r
        return not is_epsilon(self.dC_x_ddC_norm_tree())

    def evaluate_torsion(self, r: float):
        InfixTree.r = r
        return self._tau_tree()
