# coding=utf-8
import re
from PySide import QtGui, QtCore
import struct

__author__ = 'flanker'

COLORS = {}
BRUSHES = {}
PENS = {}

COLOR_RE = re.compile(r'#[0-9A-Fa-f]{6}')
COLOR_PATTERN = '#[0-9A-Fa-f]{6}'


def str_to_tuple(color: str, darken: float=None) -> tuple:
    a = 255
    if len(color) == 6:
        (r, g, b) = struct.unpack('BBB', bytes.fromhex(color))
    elif len(color) == 7:
        (r, g, b) = struct.unpack('BBB', bytes.fromhex(color[1:]))
    elif len(color) == 8:
        (r, g, b, a) = struct.unpack('BBBB', bytes.fromhex(color))
    elif len(color) == 9:
        (r, g, b, a) = struct.unpack('BBBB', bytes.fromhex(color[1:]))
    else:
        raise ValueError
    if darken is not None:
        r, g, b = map(lambda x: min(255, int(darken * x)), (r, g, b))
    return r, g, b, a


def tuple_to_str(r: int, g: int, b: int, a: int=255):
    return '#%02X%02X%02X%02X' % (r, g, b, a)


def darken_color(color: str, darken: float=None) -> str:
    values = str_to_tuple(color=color, darken=darken)
    return tuple_to_str(*values)


def get_color(r: int, g: int, b: int, a: int=255) -> QtGui.QColor:
    if (r, g, b, a) not in COLORS:
        color = QtGui.QColor(r, g, b, a)
        COLORS[(r, g, b, a)] = color
    return COLORS[(r, g, b, a)]


def get_color_from_str(color: str, darken: float=None) -> QtGui.QColor:
    r, g, b, a = str_to_tuple(color, darken=darken)
    return get_color(r, g, b, a)


def get_brush(r: int, g: int, b: int, a: int=255) -> QtGui.QBrush:
    if (r, g, b, a) not in BRUSHES:
        color = get_color(r, g, b, a=a)
        BRUSHES[(r, g, b, a)] = QtGui.QBrush(color, QtCore.Qt.SolidPattern)
    return BRUSHES[(r, g, b, a)]


def get_brush_from_str(color: str, darken: float=None) -> QtGui.QBrush:
    r, g, b, a = str_to_tuple(color, darken=darken)
    return get_brush(r, g, b, a=a)


def get_pen(r: int, g: int, b: int, a: int=255, width: float=1) -> QtGui.QPen:
    if (r, g, b, a) not in PENS:
        brush = get_brush(r, g, b, a=a)
        PENS[(r, g, b, a)] = QtGui.QPen(brush, width, QtCore.Qt.SolidLine)
    return PENS[(r, g, b, a)]


def get_pen_from_str(color: str, width: float=1, darken: float=None) -> QtGui.QPen:
    r, g, b, a = str_to_tuple(color, darken=darken)
    return get_pen(r, g, b, a=a, width=width)


if __name__ == '__main__':
    import doctest

    doctest.testmod()