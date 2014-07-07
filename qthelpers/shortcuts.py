# coding=utf-8
from PySide import QtGui
import pkg_resources
from qthelpers.utils import p

__author__ = 'flanker'


def __generic_layout(parent, layout, args):
    for arg in args:
        if isinstance(arg, QtGui.QLayout):
            sub_widget = QtGui.QWidget(parent)
            sub_widget.setLayout(arg)
            layout.addWidget(sub_widget)
        elif isinstance(arg, QtGui.QWidget):
            layout.addWidget(arg)
    return layout


def v_layout(parent, *args):
    layout = QtGui.QVBoxLayout(parent, )
    return __generic_layout(parent, layout, args)


def h_layout(parent, *args):
    layout = QtGui.QHBoxLayout(parent)
    return __generic_layout(parent, layout, args)


__ICON_CACHE = {}


def get_icon(icon_name):
    if icon_name in __ICON_CACHE:
        return __ICON_CACHE[icon_name]
    from qthelpers.preferences import preferences
    modname, sep, filename = icon_name.partition(':')
    theme_key = preferences.selected_theme_key
    if theme_key is not None:
        filename = filename % {'THEME': preferences()[theme_key]}
    icon = QtGui.QIcon(pkg_resources.resource_filename(modname, filename))
    __ICON_CACHE[icon] = icon
    return icon


def get_theme_icon(name, icon_name):
    if name in __ICON_CACHE:
        return __ICON_CACHE[name]
    icon = QtGui.QIcon.fromTheme(name, get_icon(icon_name))
    __ICON_CACHE[name] = icon
    return icon


def create_button(legend: str='', icon: str=None, min_size: bool=False, connect=None, help_text: str=None,
                  flat: bool=False, parent=None):
    if isinstance(icon, str):
        button = QtGui.QPushButton(get_icon(icon), legend, p(parent))
    elif icon:
        button = QtGui.QPushButton(icon, legend, p(parent))
    else:
        button = QtGui.QPushButton(legend, p(parent))
    if min_size:
        button.setMinimumSize(button.minimumSize())
    if help_text:
        button.setToolTip(help_text)
    button.setFlat(flat)
    if connect is not None:
        # noinspection PyUnresolvedReferences
        button.clicked.connect(connect)
    return button


def warning(title, message, only_ok=False):
    other_button = QtGui.QMessageBox.NoButton if only_ok else QtGui.QMessageBox.Cancel
    # noinspection PyTypeChecker
    return QtGui.QMessageBox.warning(None, title, message, QtGui.QMessageBox.Ok, other_button) == QtGui.QMessageBox.Ok


def question(title, message, only_ok=False):
    other_button = QtGui.QMessageBox.NoButton if only_ok else QtGui.QMessageBox.Cancel
    # noinspection PyTypeChecker
    return QtGui.QMessageBox.question(None, title, message, QtGui.QMessageBox.Ok, other_button) == QtGui.QMessageBox.Ok


def critical(title, message, only_ok=False):
    other_button = QtGui.QMessageBox.NoButton if only_ok else QtGui.QMessageBox.Cancel
    # noinspection PyTypeChecker
    return QtGui.QMessageBox.critical(None, title, message, QtGui.QMessageBox.Ok, other_button) == QtGui.QMessageBox.Ok


def information(title, message, only_ok=False):
    other_button = QtGui.QMessageBox.NoButton if only_ok else QtGui.QMessageBox.Cancel
    # noinspection PyTypeChecker
    return QtGui.QMessageBox.information(None, title, message, QtGui.QMessageBox.Ok, other_button) == \
        QtGui.QMessageBox.Ok


if __name__ == '__main__':
    import doctest

    doctest.testmod()