# coding=utf-8
from PySide import QtGui
from qthelpers.menus import registered_menus, registered_menu_actions, menu_item

from qthelpers.preferences import Preferences, GlobalObject, global_dict
from qthelpers.shortcuts import get_icon


__author__ = 'flanker'
application_key = 'application'
application = GlobalObject(application_key)


class BaseApplication(Preferences):
    application = None
    systray = None
    application_icon = None
    application_version = None
    organization_domain = None
    use_systemtray_icon = True

    def __init__(self, args: list):
        super().__init__()
        self.application = QtGui.QApplication(args)
        global_dict[application_key] = self
        super().load()  # load preferences

        # set some global stuff
        if self.application_icon:
            self.application.setWindowIcon(get_icon(self.application_icon))
        if self.application_name:
            self.application.setApplicationName(self.application_name)
        if self.application_version:
            self.application.setApplicationVersion(self.application_version)
        if self.use_systemtray_icon and self.application_icon:
            self.systray = QtGui.QSystemTrayIcon(get_icon(self.application_icon))
            self.systray.setVisible(True)
            self.systray.show()

            # retrieve menu and associated actions for the whole class hierarchy
            created_action_keys = set()
            menu = None
            for qualname in self.__class__.__mro__:
                cls_name = qualname.__name__.rpartition('.')[2]
                if cls_name not in registered_menus:
                    continue
                for menu_action in registered_menu_actions[cls_name]:
                    if menu is None:
                        menu = QtGui.QMenu(self.application_name)
                    if menu_action.uid in created_action_keys:  # skip overriden actions (there are already created)
                        continue
                    created_action_keys.add(menu_action.uid)
                    menu_action.create(self, menu)
            if menu is not None:
                self.systray.setContextMenu(menu)
            self.systray.activated.connect(self.systray_activated)
            self.systray.messageClicked.connect(self.systray_message_clicked)

    def exec_(self):
        self.application.exec_()
        super().save()  # save preferences

    def quit(self, *args, **kwargs):
        self.application.quit(*args, **kwargs)
        super().save()  # save preferences
        global_dict[application_key] = None

    def systray_message_clicked(self):
        pass

    def systray_activated(self, reason):
        pass


if __name__ == '__main__':
    import doctest

    doctest.testmod()