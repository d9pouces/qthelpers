# coding=utf-8
import functools
from PySide import QtGui

__author__ = 'flanker'
registered_menus = {}  # registered_menus[cls_name] = [Menu1, Menu2, …]
registered_actions = {}  # registered_actions[cls_name][menu] = [MenuItem1, MenuItem2, …]


class MenuAction(object):
    def __init__(self, method_name, verbose_name: str, menu: str, icon=None, sep: bool=False, disabled: bool=False,
                 shortcut: str=None, help_text: str=None, submenu: bool=False):
        """
        Description of a menu action.
        :param method_name: any callable or (method name of the window)
            if submenu is True, then this callable (or method) must return an iterable of MenuAction
        :param verbose_name: str, or the raw name of the function by default.
        :param icon: str (of the form "modname:folder/%(THEME)s/picture.png") or QtGui.QIcon object
        :param menu: str (name of the top menu)
        :param sep: bool add a separator before this menu?
        :param disabled: bool do not show this menu entry?
        :param shortcut: str a shortcut, like Ctrl+D
        :param help_text: str tooltip
        :param submenu:
        """
        self.help_text = help_text
        self.shortcut = shortcut
        self.menu = menu
        self.disabled = disabled
        self.icon = icon
        self.verbose_name = verbose_name
        self.sep = sep
        self.method_name = method_name
        self.submenu = submenu

    def create(self, window: QtGui.QMainWindow, parent: QtGui.QMenu):
        if self.disabled:
            return
        if callable(self.method_name):
            method = self.method_name
        else:
            method = getattr(window, self.method_name)
        if self.sep:
            parent.addSeparator()
        if self.submenu:
            menu = QtGui.QMenu(self.verbose_name, window)
            action = parent.addMenu(menu)
            action.hovered.connect(functools.partial(self.fill_submenu, window, menu, method))
        else:
            action = QtGui.QAction(self.verbose_name, window)
            # noinspection PyUnresolvedReferences
            action.triggered.connect(method)
            parent.addAction(action)
        if self.shortcut:
            action.setShortcut(self.shortcut)
        if self.help_text:
            action.setStatusTip(self.help_text)

    @staticmethod
    def fill_submenu(window: QtGui.QMainWindow, menu: QtGui.QMenu, method):
        menu.clear()
        for menu_action in method():
            menu_action.create(window, menu)


def menu_item(method=None, verbose_name=None, icon=None, menu: str=None, sep: bool=False, disabled: bool=False,
              shortcut: str=None, help_text: str=None, submenu: bool=False):
    """ Decorator to register method as menu action for the BaseMainWindow subclass.
    The registered method will be called when the menu action will be triggered
    :param method: do not use it if you want to use any of the keyword argument
    :param verbose_name: str, or the raw name of the function by default.
    :param icon: str (of the form "modname:folder/%(THEME)s/picture.png") or QtGui.QIcon object
    :param menu: str (name of the top menu)
    :param sep: bool add a separator before this menu?
    :param disabled: bool do not show this menu entry?
    :param shortcut: str a shortcut, like Ctrl+D
    :param help_text: str tooltip
    :param submenu:
    :return:
    """
    def wrapper(method_):
        cls_name = method_.__qualname__.partition('.')[0]
        obj = MenuAction(method_.__name__, verbose_name or method_.__name__, icon=icon, menu=menu, sep=sep,
                         disabled=disabled, shortcut=shortcut, help_text=help_text, submenu=submenu)
        registered_menus.setdefault(cls_name, [])
        registered_actions.setdefault(cls_name, [])
        if menu not in registered_actions[cls_name]:
            registered_menus[cls_name].append(menu)
        registered_actions[cls_name].append(obj)
        return method_

    if method is not None:
        # @menu_item
        # def my_method(self):
        return wrapper(method)

    # @menu_item(verbose_name='Open')
    # def my_method(self):
    return wrapper


if __name__ == '__main__':
    import doctest

    doctest.testmod()