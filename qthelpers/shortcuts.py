# coding=utf-8
from PySide import QtGui
import pkg_resources
from qthelpers.preferences import preferences

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


def get_icon(icon_name):
    modname, sep, filename = icon_name.partition(':')
    theme_key = preferences.selected_theme_key
    if theme_key is not None:
        filename = filename % {'THEME': preferences()[theme_key]}
    return QtGui.QIcon(pkg_resources.resource_filename(modname, filename))


def get_theme_icon(name, icon_name):
    return QtGui.QIcon.fromTheme(name, get_icon(icon_name))


def create_button(legend: str='', icon: str=None, min_size: bool=False, connect=None, help_text: str=None,
                  flat: bool=False):
    if isinstance(icon, str):
        button = QtGui.QPushButton(get_icon(icon), legend)
    elif icon:
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