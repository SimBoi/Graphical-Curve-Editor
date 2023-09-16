from functools import wraps


class UnitTypeMeta(type):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        new_class.__unitvalue__ = new_class()

        def new(cls, *args, **kwargs):
            return new_class.__unitvalue__

        def repr_(self: new_class):
            return f"{name}()"

        new_class.__new__ = new
        new_class.__repr__ = repr_
        return new_class


def unit_type(cls):

    @wraps(cls, updated=())
    class D(metaclass=UnitTypeMeta):
        pass
    return D


def unit_value(name: str):
    return UnitTypeMeta(name, (), {})()
