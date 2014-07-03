# coding=utf-8
from PySide import QtGui

from qthelpers.preferences import Preferences, GlobalObject, global_dict
from qthelpers.shortcuts import get_icon


__author__ = 'flanker'
application_key = 'application'
application = GlobalObject(application_key)


class BaseApplication(Preferences):
    application_icon = None
    application_version = None
    organization_domain = None

    def __init__(self, args: list):
        super().__init__()
        self.application = QtGui.QApplication(args)
        global_dict[application_key] = self
        super().load()  # load preferences
        if self.application_icon:
            self.application.setWindowIcon(get_icon(self.application_icon))
        if self.application_name:
            self.application.setApplicationName(self.application_name)
        if self.application_version:
            self.application.setApplicationVersion(self.application_version)

    def exec_(self):
        self.application.exec_()
        super().save()  # save preferences

    def quit(self, *args, **kwargs):
        self.application.quit(*args, **kwargs)
        super().save()  # save preferences
        global_dict[application_key] = None


if __name__ == '__main__':
    import doctest

    doctest.testmod()