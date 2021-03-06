# coding=utf-8
import threading
from PySide import QtGui, QtCore
import weakref

from qthelpers.forms import BaseForm
from qthelpers.shortcuts import v_layout
from qthelpers.utils import p, ThreadedCalls


__author__ = 'flanker'


class BaseDock(QtGui.QDockWidget, ThreadedCalls):
    verbose_name = None
    menu = None
    shortcut = None
    default_position = QtCore.Qt.RightDockWidgetArea

    def __init__(self, parent=None):
        QtGui.QDockWidget.__init__(self, str(self.verbose_name), p(parent))
        ThreadedCalls.__init__(self)
        self.parent_window = weakref.ref(parent)
        self.setObjectName(self.__class__.__name__)

    def close(self):
        return self.hide()


class FormDock(BaseForm, BaseDock):
    description = None

    def __init__(self, initial=None, parent=None):
        BaseForm.__init__(self, initial=initial)
        BaseDock.__init__(self, parent=p(parent))
        # widget creation
        widgets = []
        if self.description:
            widgets.append(QtGui.QLabel(self.description, p(self)))
        sub_layout = QtGui.QGridLayout(p(self))
        self._fill_grid_layout(layout=sub_layout)
        widgets.append(sub_layout)
        sub_widget = QtGui.QWidget(p(self))
        sub_widget.setLayout(v_layout(self, *widgets))
        self.setWidget(sub_widget)


if __name__ == '__main__':
    import doctest

    doctest.testmod()