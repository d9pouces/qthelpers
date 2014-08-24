# coding=utf-8
from PySide import QtGui, QtCore
import pkg_resources
from qthelpers.utils import p
from qthelpers.translation import ugettext as _

__author__ = 'flanker'


def __generic_layout(parent, layout, extra_args, args):
    for arg in args:
        if isinstance(arg, QtGui.QLayout):
            sub_widget = QtGui.QWidget(p(parent))
            sub_widget.setLayout(arg)
            layout.addWidget(sub_widget, *extra_args)
        elif isinstance(arg, QtGui.QWidget):
            layout.addWidget(arg, *extra_args)
    return layout


def v_layout(parent, *args, direction=None):
    layout = QtGui.QVBoxLayout(None)
    if direction is not None:
        layout.setDirection(direction)
    return __generic_layout(parent, layout, [], args)


def h_layout(parent, *args, direction=None):
    layout = QtGui.QHBoxLayout(None)
    extra_args = []
    if direction == QtGui.QBoxLayout.RightToLeft:
        layout.setDirection(direction)
        extra_args = [0, QtCore.Qt.AlignRight]
    __generic_layout(parent, layout, extra_args, args)
    if direction == QtGui.QBoxLayout.RightToLeft:
        layout.addStretch(1)
    return layout


def v_widget(parent, *args, direction=None):
    layout = v_layout(parent, *args, direction=direction)
    widget_ = QtGui.QWidget(p(parent))
    widget_.setLayout(layout)
    return widget_


def h_widget(parent, *args, direction=None):
    layout = h_layout(parent, *args, direction=direction)
    widget_ = QtGui.QWidget(p(parent))
    widget_.setLayout(layout)
    return widget_


def widget(parent, layout):
    widget_ = QtGui.QWidget(p(parent))
    widget_.setLayout(layout)
    return widget_


__ICON_CACHE = {}
__PIXMAP_CACHE = {}


def __get_picture(picture_name, cache_dict, picture_class):
    if picture_name in cache_dict:
        return cache_dict[picture_name]
    from qthelpers.preferences import preferences
    if preferences.icon_use_global_theme and QtGui.QIcon.hasThemeIcon(picture_name) and picture_class == QtGui.QIcon:
        icon = QtGui.QIcon.fromTheme(picture_name)
        __ICON_CACHE[picture_name] = icon
    theme_key = preferences.icon_theme_key
    if theme_key is not None:
        filename = preferences.icon_pattern % {'theme': preferences[theme_key], 'name': picture_name}
    else:
        filename = preferences.icon_pattern % {'name': picture_name}
    for modname in preferences.icon_search_modules:
        if pkg_resources.resource_exists(modname, filename):
            fullpath = pkg_resources.resource_filename(modname, filename)
            break
    else:
        raise FileNotFoundError(picture_name)
    icon = picture_class(fullpath)
    cache_dict[picture_name] = icon
    return icon


def get_icon(icon_name):
    return __get_picture(icon_name, __ICON_CACHE, QtGui.QIcon)


def get_pixmap(pixmap_name):
    return __get_picture(pixmap_name, __PIXMAP_CACHE, QtGui.QPixmap)


def get_theme_icon(name, icon_name):
    if name in __ICON_CACHE:
        return __ICON_CACHE[name]
    icon = QtGui.QIcon.fromTheme(name, get_icon(icon_name))
    __ICON_CACHE[name] = icon
    return icon


def create_button(legend: str='', icon: str=None, min_size: bool=False, connect=None, help_text: str=None,
                  flat: bool=False, parent=None, default=False):
    if isinstance(icon, str):
        button = QtGui.QPushButton(get_icon(icon), legend, p(parent))
    elif icon:
        button = QtGui.QPushButton(icon, legend, p(parent))
    else:
        button = QtGui.QPushButton(legend, p(parent))
    if min_size:
        size = button.minimumSizeHint()
        if not legend:
            size.setWidth(button.iconSize().width() + 4)
        button.setFixedSize(size)
    if help_text:
        button.setToolTip(help_text)
    if default:
        button.setDefault(True)
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


def get_item(title: str, label: str, choices: list, initial: object=None) -> object:
    from qthelpers.fields import ChoiceField
    from qthelpers.forms import FormDialog

    class Dialog(FormDialog):
        verbose_name = title
        text_confirm = _('Select')
        value = ChoiceField(verbose_name=label, choices=choices, default=initial)

    values = Dialog.process(initial={'value': initial}, parent=p(None))
    if values is None:
        return None
    return values['value']


if __name__ == '__main__':
    import doctest

    doctest.testmod()