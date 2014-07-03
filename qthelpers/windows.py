# coding=utf-8
from PySide import QtGui
from qthelpers.menus import registered_actions, registered_menus
from qthelpers.shortcuts import get_icon
from qthelpers.translation import ugettext as _

__author__ = 'flanker'


class BaseMainWindow(QtGui.QMainWindow):
    window_icon = None
    verbose_name = _('Main application window')

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        # retrieve menus and associated actions from the whole class hierarchy
        menubar = self.menuBar()
        defined_qmenus = {}
        created_action_keys = set()
        for qualname in self.__class__.__mro__:
            cls_name = qualname.__name__.rpartition('.')[2]
            if cls_name in registered_menus:
                for menu_name in registered_menus[cls_name]:  # create all top-level menus
                    if menu_name not in defined_qmenus:
                        defined_qmenus[menu_name] = menubar.addMenu(menu_name)
                for menu_action in registered_actions[cls_name]:
                    item_key = '%s.%s' % (menu_action.menu, menu_action.verbose_name)
                    if item_key in created_action_keys:  # skip overriden actions (there are already created)
                        continue
                    created_action_keys.add(item_key)
                    menu_action.create(self, defined_qmenus[menu_action.menu])

        # some extra stuff
        self.setWindowTitle(self.verbose_name)
        if self.window_icon:
            self.setWindowIcon(get_icon(self.window_icon))
        self.raise_()


if __name__ == '__main__':
    import doctest

    doctest.testmod()