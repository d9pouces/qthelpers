# coding=utf-8
import os

from PySide import QtGui

from qthelpers.shortcuts import h_layout, create_button
from qthelpers.translation import ugettext as _
from qthelpers.utils import p


__author__ = 'flanker'


class FilepathWidget(QtGui.QWidget):
    def __init__(self, filename: str=None, selection_filter: str=None, parent: QtGui.QWidget=None):
        self.selection_filter = selection_filter
        self.filename = None
        super().__init__(parent)
        self.select_button = create_button(_('Choose a file…'), min_size=True, connect=self.select_file,
                                           icon='edit-find')
        self.line_editor = QtGui.QLineEdit(p(self))
        self.set_value(filename)
        layout = h_layout(self, self.select_button, self.line_editor)
        self.setLayout(layout)
        self.adjustSize()

    def select_file(self):
        try:
            from qthelpers.application import application
            dirname = application.GlobalInfos.last_open_folder
        except AttributeError:
            dirname = os.path.expanduser('~')
        # noinspection PyTypeChecker
        filename, selected_filter = QtGui.QFileDialog.getOpenFileName(p(self), _('Select a file'), dirname,
                                                                      self.selection_filter, '', 0)
        if filename:
            self.set_value(filename)

    def setPalette(self, *args, **kwargs):
        self.line_editor.setPalette(*args, **kwargs)

    def set_value(self, filename: str=None):
        self.filename = filename
        self.line_editor.setText(filename or '')

    def get_value(self):
        return self.filename if (self.filename and os.path.isfile(self.filename)) else None


if __name__ == '__main__':
    import doctest

    doctest.testmod()