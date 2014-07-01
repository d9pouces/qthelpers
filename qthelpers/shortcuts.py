# coding=utf-8
from PySide import QtGui

__author__ = 'flanker'


def __generic_layout(layout, args):
    for arg in args:
        if isinstance(arg, QtGui.QLayout):
            sub_widget = QtGui.QWidget()
            sub_widget.setLayout(arg)
            layout.addWidget(sub_widget)
        elif isinstance(arg, QtGui.QWidget):
            layout.addWidget(arg)
    return layout


def v_layout(*args):
    layout = QtGui.QVBoxLayout()
    return __generic_layout(layout, args)


def h_layout(*args):
    layout = QtGui.QHBoxLayout()
    return __generic_layout(layout, args)


def create_button(legend: str='', icon=None, min_size: bool=False, connect=None, help_text: str=None, flat: bool=False):
    if icon:
        button = QtGui.QPushButton(icon, legend)
    else:
        button = QtGui.QPushButton(legend)
    if min_size:
        button.setMinimumSize(button.minimumSize())
    if help_text:
        button.setToolTip(help_text)
    button.setFlat(flat)
    if connect is not None:
        # noinspection PyUnresolvedReferences
        button.clicked.connect(connect)
    return button


if __name__ == '__main__':
    import doctest

    doctest.testmod()