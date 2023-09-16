import ctypes

from enum import IntEnum
from functools import reduce
from pathlib import Path
from typing import Iterable

from cagd_lib.utils import unit_value

__all__ = [
    "Variables", "InfixTree"
]


class Variables(IntEnum):
    A   =  0
    B   =  1
    C   =  2
    D   =  3
    E   =  4
    F   =  5
    G   =  6
    H   =  7
    I   =  8
    J   =  9
    K   =  10
    L   =  11
    M   =  12
    N   =  13
    O   =  14
    P   =  15
    Q   =  16
    R   =  17
    S   =  18
    T   =  19
    U   =  20
    V   =  21
    W   =  22
    X   =  23
    Y   =  24
    Z   =  25
    Z1  =  26
    """Number of variables"""
    ALL =  -1
    """Match all E2T_PARAMs is searches"""


VARIABLE_TYPE = Variables | int | str

clib = ctypes.CDLL("./expr2tree.so")
clib.e2t_expr2tree.argtypes = [ctypes.c_char_p]
clib.e2t_expr2tree.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_printtree.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_char_p)]

clib.e2t_copytree.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_copytree.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_freetree.argtypes = [ctypes.POINTER(ctypes.c_void_p)]

clib.e2t_cmptree.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_cmptree.restype = ctypes.c_int

clib.e2t_paramintree.argstype = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
clib.e2t_paramintree.restype = ctypes.c_int

clib.e2t_setparamvalue.argstype = [ctypes.c_double, ctypes.c_int]

clib.e2t_evaltree.argstype = [ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_evaltree.restype = ctypes.c_double

clib.e2t_derivtree.argstype = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
clib.e2t_derivtree.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_treereparameter.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
clib.e2t_treereparameter.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_trees_op_division.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_trees_op_division.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_trees_op_subtraction.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_trees_op_subtraction.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_trees_op_multiplication.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_trees_op_multiplication.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_trees_op_addition.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_trees_op_addition.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_trees_op_power.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_trees_op_power.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_tree_op_sqr.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_tree_op_sqr.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_tree_op_sqrt.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_tree_op_sqrt.restype = ctypes.POINTER(ctypes.c_void_p)

clib.e2t_tree_op_unarminus.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
clib.e2t_tree_op_unarminus.restype = ctypes.POINTER(ctypes.c_void_p)


DummyTree = unit_value("DummyTree")


def _var_type_to_var_enum(variable: VARIABLE_TYPE):
    if isinstance(variable, str):
        return getattr(Variables, variable.upper())

    return Variables(variable)


class InfixTreeMeta(type):

    def __setattr__(self, key, value):
        if key.upper() in Variables.__members__:
            self.set_variable_value(key, value)
        else:
            super().__setattr__(key, value)


class InfixTree(metaclass=InfixTreeMeta):
    def __init__(self, expression: bytes):

        if isinstance(expression, bytes):
            self._tree_pointer = clib.e2t_expr2tree(expression)
            # TODO: Handle errors properly
            if not bool(self._tree_pointer):
                raise ValueError(expression)

        elif expression is DummyTree:
            pass
        else:
            raise ValueError(expression)

    def __repr__(self):
        # TODO Optimize and implement properly
        repr_str_ptr = ctypes.create_string_buffer(10000)
        clib.e2t_printtree(self._tree_pointer, ctypes.c_char_p.from_buffer(repr_str_ptr))
        return repr_str_ptr.value.decode()

    def __copy__(self) -> 'InfixTree':
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_copytree(self._tree_pointer)
        return new_tree

    def __del__(self):
        clib.e2t_freetree(self._tree_pointer)

    def __eq__(self, other: 'InfixTree') -> bool:
        return clib.e2t_cmptree(self._tree_pointer, other._tree_pointer) != 0

    def __contains__(self, item: VARIABLE_TYPE) -> bool:
        return clib.e2t_paramintree(self._tree_pointer, _var_type_to_var_enum(item)) != 0

    def __call__(self) -> float:
        return clib.e2t_evaltree(self._tree_pointer)

    def calculate_derivative(self, variable: VARIABLE_TYPE) -> 'InfixTree':
        derived_tree = InfixTree(DummyTree)
        derived_tree._tree_pointer = clib.e2t_derivtree(self._tree_pointer, _var_type_to_var_enum(variable))
        if not bool(self._tree_pointer):
            raise ValueError()
        return derived_tree

    def re_parametrize(self, re_parametrization_tree: 'InfixTree', parameter: VARIABLE_TYPE):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_treereparameter(self._tree_pointer, re_parametrization_tree._tree_pointer, parameter)
        return new_tree

    @classmethod
    def set_variable_value(cls, variable: VARIABLE_TYPE, value: float):
        clib.e2t_setparamvalue(ctypes.c_double(value), _var_type_to_var_enum(variable))

    def __truediv__(self, other):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_trees_op_division(self._tree_pointer, other._tree_pointer)
        return new_tree

    def __sub__(self, other):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_trees_op_subtraction(self._tree_pointer, other._tree_pointer)
        return new_tree

    def __mul__(self, other):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_trees_op_multiplication(self._tree_pointer, other._tree_pointer)
        return new_tree

    def __add__(self, other):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_trees_op_addition(self._tree_pointer, other._tree_pointer)
        return new_tree

    def __pow__(self, power, modulo=None):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_trees_op_power(self._tree_pointer, power._tree_pointer)
        return new_tree

    def sqr(self):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_tree_op_sqr(self._tree_pointer)
        return new_tree

    def sqrt(self):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_tree_op_sqrt(self._tree_pointer)
        return new_tree

    def __neg__(self):
        new_tree = InfixTree(DummyTree)
        new_tree._tree_pointer = clib.e2t_tree_op_unarminus(self._tree_pointer)
        return new_tree

    @staticmethod
    def norm(trees: Iterable):
        return reduce(InfixTree.__add__, [tree.sqr() for tree in trees]).sqrt()

    @staticmethod
    def dot(operand1, operand2):
        return reduce(InfixTree.__add__, [tree1 * tree2 for tree1, tree2 in zip(operand1, operand2)])
