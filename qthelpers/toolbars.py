# coding=utf-8
from PySide import QtGui
from qthelpers.shortcuts import get_icon
from qthelpers.utils import p

__author__ = 'flanker'
registered_toolbars = {}  # registered_menus[cls_name] = [Menu1, Menu2, …]
registered_toolbar_actions = {}  # registered_actions[cls_name][menu] = [MenuItem1, MenuItem2, …]


class BaseToolBar(QtGui.QToolBar):

    def __init__(self, *args, **kwargs):
        QtGui.QToolBar.__init__(self, *args, **kwargs)
        self.setObjectName(self.windowTitle())


class ToolbarAction(object):
    def __init__(self, method_name, verbose_name: str, toolbar: str=None, icon=None, sep: bool=False,
                 disabled: bool=False, shortcut: str=None, help_text: str=None, uid: str=None):
        """
        Description of a menu action.
        :param toolbar:
        :param method_name: any callable or (method name of the window)
            if submenu is True, then this callable (or method) must return an iterable of MenuAction
        :param verbose_name: str, or the raw name of the function by default.
        :param icon: str (of the form "modname:folder/%(THEME)s/picture.png") or QtGui.QIcon object
        :param sep: bool add a separator before this menu?
        :param disabled: bool do not show this menu entry?
        :param shortcut: str a shortcut, like Ctrl+D
        :param help_text: str tooltip
        :param uid: unique identifier (useful for referencing it in settings). Defaults to method_name
        """
        self.toolbar = toolbar
        self.help_text = help_text
        self.shortcut = shortcut
        self.disabled = disabled
        self.icon = icon
        self.verbose_name = verbose_name
        self.sep = sep
        self.method_name = method_name
        if uid is None:
            if callable(method_name) and hasattr(method_name, '__name__'):
                uid = method_name.__name__
            else:
                uid = str(method_name)
        self.uid = uid

    def create(self, window: QtGui.QMainWindow, parent: QtGui.QToolBar):
        if self.disabled:
            return
        if callable(self.method_name):
            method = self.method_name
        else:
            method = getattr(window, self.method_name)
        if self.sep:
            parent.addSeparator()
        if self.icon:
            action = QtGui.QAction(get_icon(self.icon), self.verbose_name, p(window))
        else:
            action = QtGui.QAction(self.verbose_name, p(window))
        # noinspection PyUnresolvedReferences
        action.triggered.connect(method)
        parent.addAction(action)
        if self.shortcut:
            action.setShortcut(self.shortcut)
        if self.help_text:
            action.setStatusTip(self.help_text)


def toolbar_item(method=None, verbose_name=None, icon=None, toolbar: str=None, sep: bool=False, disabled: bool=False,
                 shortcut: str=None, help_text: str=None, uid=None):
    """ Decorator to register method as menu action for the BaseMainWindow subclass.
    The registered method will be called when the menu action will be triggered
    :param method: do not use it if you want to use any of the keyword argument
    :param verbose_name: str, or the raw name of the function by default.
    :param icon: str (of the form "modname:folder/%(THEME)s/picture.png") or QtGui.QIcon object
    :param toolbar: str (name of the toolbar, None for the default toolbar)
    :param sep: bool add a separator before this action?
    :param disabled: bool do not show this toolbar action?
    :param shortcut: str a shortcut, like Ctrl+D
    :param help_text: str tooltip
    :param uid: unique identifier (useful for referencing it in settings). Defaults to method_name
    :return:
    """
    def wrapper(method_):
        cls_name = method_.__qualname__.partition('.')[0]
        obj = ToolbarAction(method_.__name__, verbose_name or method_.__name__, icon=icon, toolbar=toolbar, sep=sep,
                            disabled=disabled, shortcut=shortcut, help_text=help_text, uid=uid)
        registered_toolbars.setdefault(cls_name, [])
        registered_toolbar_actions.setdefault(cls_name, [])
        if toolbar not in registered_toolbar_actions[cls_name]:
            registered_toolbars[cls_name].append(toolbar)
        registered_toolbar_actions[cls_name].append(obj)
        return method_

    if method is not None:
        # @toolbar_item
        # def my_method(self):
        return wrapper(method)

    # @toolbar_item(verbose_name='Open')
    # def my_method(self):
    return wrapper


if __name__ == '__main__':
    import doctest

    doctest.testmod()