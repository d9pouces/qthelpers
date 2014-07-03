# coding=utf-8
import itertools

from PySide import QtGui

from qthelpers.application import application
from qthelpers.menus import registered_menu_actions, registered_menus
from qthelpers.shortcuts import get_icon
from qthelpers.toolbars import registered_toolbars, registered_toolbar_actions
from qthelpers.translation import ugettext as _


__author__ = 'flanker'


class BaseMainWindow(QtGui.QMainWindow):
    window_icon = None
    verbose_name = _('Main application window')
    _window_counter = itertools.count()

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self._window_id = next(BaseMainWindow._window_counter)
        application.windows[self._window_counter] = self

        # retrieve menus and associated actions from the whole class hierarchy
        menubar = self.menuBar()
        defined_qmenus = {}
        created_action_keys = set()
        for qualname in self.__class__.__mro__:
            cls_name = qualname.__name__.rpartition('.')[2]
            if cls_name not in registered_menus:
                continue
            for menu_name in registered_menus[cls_name]:  # create all top-level menus
                if menu_name not in defined_qmenus:
                    defined_qmenus[menu_name] = menubar.addMenu(menu_name)
            for menu_action in registered_menu_actions[cls_name]:
                if menu_action.uid in created_action_keys:  # skip overriden actions (there are already created)
                    continue
                created_action_keys.add(menu_action.uid)
                menu_action.create(self, defined_qmenus[menu_action.menu])

        # retrieve toolbar actions from the whole class hierarchy
        self.setUnifiedTitleAndToolBarOnMac(True)
        defined_qtoolbars = {}
        created_action_keys = set()
        for qualname in self.__class__.__mro__:
            cls_name = qualname.__name__.rpartition('.')[2]
            if cls_name not in registered_toolbars:
                continue
            for toolbar_name in registered_toolbars[cls_name]:  # create all top-level menus
                if toolbar_name not in defined_qtoolbars:
                    if toolbar_name is not None:
                        defined_qtoolbars[toolbar_name] = QtGui.QToolBar(toolbar_name, self)
                    else:
                        defined_qtoolbars[toolbar_name] = QtGui.QToolBar(_('Toolbar'), self)
                    self.addToolBar(defined_qtoolbars[toolbar_name])
            for toolbar_action in registered_toolbar_actions[cls_name]:
                if toolbar_action.uid in created_action_keys:  # skip overriden actions (there are already created)
                    continue
                created_action_keys.add(toolbar_action.uid)
                toolbar_action.create(self, defined_qtoolbars[toolbar_action.toolbar])

        # some extra stuff
        self.setWindowTitle(self.verbose_name)
        if self.window_icon:
            self.setWindowIcon(get_icon(self.window_icon))

        self.setCentralWidget(self.central_widget())

        self.raise_()

    def central_widget(self):
        raise NotImplementedError

    def close(self, *args, **kwargs):
        del application.windows[self._window_id]
        super().close()


if __name__ == '__main__':
    import doctest

    doctest.testmod()