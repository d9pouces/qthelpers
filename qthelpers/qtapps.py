# coding=utf-8
from PySide import QtGui
import pkg_resources

__author__ = 'flanker'


class BaseApplication(QtGui.QApplication):
    application_icon = None
    application_name = None
    organization_name = None
    organization_domain = None

    def __init__(self, args: list):
        super().__init__(args)
        # if self.application_icon:
        #     self.setWindowIcon()
        if self.application_name:
            self.setApplicationName(self.application_name)
            distribution = pkg_resources.get_distribution(self.application_name)
            if distribution.has_version():
                self.setApplicationVersion(distribution.version)


class BaseMainWindow(QtGui.QMainWindow):
    pass


if __name__ == '__main__':
    import doctest

    doctest.testmod()