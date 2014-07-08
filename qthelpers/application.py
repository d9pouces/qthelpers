#coding=utf-8
import os

from PySide import QtGui
from qthelpers import fields

from qthelpers.menus import registered_menus, registered_menu_actions
from qthelpers.preferences import Preferences, GlobalObject, global_dict, Section
from qthelpers.shortcuts import get_icon


__author__ = 'flanker'
application_key = 'application'
application = GlobalObject(application_key)


class BaseApplication(Preferences):
    application = None
    systray = None
    description_icon = None
    application_version = None
    systemtray_icon = None
    windows = {}

    def __init__(self, args: list):
        super().__init__()
        self.load()  # load preferences

        # initialize QtApplication
        self.application = QtGui.QApplication(args)
        self.parent = QtGui.QWidget()
        global_dict[application_key] = self

        # set some global stuff
        if self.description_icon:
            self.application.setWindowIcon(get_icon(self.description_icon))
        if self.verbose_name:
            self.application.setApplicationName(str(self.verbose_name))
        if self.application_version:
            self.application.setApplicationVersion(self.application_version)
        if self.systemtray_icon:
            self._parent_obj = QtGui.QWidget()
            self.systray = QtGui.QSystemTrayIcon(get_icon(self.systemtray_icon), self._parent_obj)
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
                        menu = QtGui.QMenu(self.verbose_name, self._parent_obj)
                    if menu_action.uid in created_action_keys:  # skip overriden actions (there are already created)
                        continue
                    created_action_keys.add(menu_action.uid)
                    menu_action.create(self, menu)
            if menu is not None:
                self.systray.setContextMenu(menu)
            # noinspection PyUnresolvedReferences
            self.systray.activated.connect(self.systray_activated)
            # noinspection PyUnresolvedReferences
            self.systray.messageClicked.connect(self.systray_message_clicked)

            # noinspection PyUnresolvedReferences
            self.application.lastWindowClosed.connect(self.save)

    def exec_(self):
        self.application.exec_()
        self.save()  # save preferences

    def quit(self, *args, **kwargs):
        self.application.quit(*args, **kwargs)
        self.save()  # save preferences
        global_dict[application_key] = None

    def systray_message_clicked(self):
        pass

    def systray_activated(self, reason):
        pass


class SingleDocumentApplication(BaseApplication):
    class GlobalInfos(Section):
        last_open_folder = fields.FilepathField(default=os.path.expanduser('~'))
        last_save_folder = fields.FilepathField(default=os.path.expanduser('~'))
        last_documents = fields.ListField(default=[])
        auto_save_interval = fields.IntegerField(default=0, min_value=0)


if __name__ == '__main__':
    import doctest

    doctest.testmod()