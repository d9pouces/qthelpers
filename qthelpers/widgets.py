# coding=utf-8
import os

from PySide import QtGui, QtCore
from qthelpers.colors import get_color_from_str, COLOR_PATTERN, COLOR_RE

from qthelpers.shortcuts import h_layout, create_button, get_icon
from qthelpers.translation import ugettext as _
from qthelpers.utils import p


__author__ = 'flanker'


class Button(QtGui.QPushButton):
    def __init__(self, parent, connect: callable=None, legend: str=None, min_size: bool=True, icon: str=None,
                 flat: bool=False, tooltip: str=None):
        QtGui.QPushButton.__init__(self, parent)
        if icon is not None:
            self.setIcon(get_icon(icon))
        if min_size:
            if legend:
                self.setText(legend)
            size = self.minimumSizeHint()
            if not legend:
                size.setWidth(self.iconSize().width() + 8)
            self.setFixedSize(size)
        self.connected_function = connect
        self.setFlat(flat)
        if tooltip:
            self.setToolTip(tooltip)
        self.args = []
        self.kwargs = {}
        if connect:
            # noinspection PyUnresolvedReferences
            self.clicked.connect(self.button_clicked)

    def button_clicked(self):
        self.connected_function(*self.args, **self.kwargs)


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

    def setDisabled(self, value):
        self.line_editor.setDisabled(value)
        self.select_button.setDisabled(value)

    def set_value(self, filename: str=None):
        self.filename = filename
        self.line_editor.setText(filename or '')

    def get_value(self):
        return self.filename if (self.filename and os.path.isfile(self.filename)) else None


class ColorWidget(QtGui.QWidget):
    validator = QtGui.QRegExpValidator(QtCore.QRegExp('|%s' % COLOR_PATTERN, QtCore.Qt.CaseInsensitive,
                                                      QtCore.QRegExp.RegExp))

    def __init__(self, color: str=None, parent: QtGui.QWidget=None):
        self.color = None
        super().__init__(parent)
        self.select_button = create_button(_('Choose a color…'), min_size=True, connect=self.select_color,
                                           icon='preferences-color')
        self.line_editor = QtGui.QLineEdit(p(self))
        self.line_editor.setValidator(self.validator)
        if not color or not COLOR_RE.match(color):
            color = None
        self.set_value(color)
        layout = h_layout(self, self.select_button, self.line_editor)
        self.setLayout(layout)
        self.adjustSize()

    def select_color(self):
        color = get_color_from_str(self.color if self.color is not None else '#FFFFFF')
        color = QtGui.QColorDialog.getColor(color, self)
        """:type: QtGui.QColor"""
        if color.isValid():
            self.set_value(color.name())

    def setPalette(self, *args, **kwargs):
        self.line_editor.setPalette(*args, **kwargs)

    def setDisabled(self, value):
        self.line_editor.setDisabled(value)
        self.select_button.setDisabled(value)

    def set_value(self, color: str=None):
        if not color or not COLOR_RE.match(color):
            color = None
        self.color = color
        self.line_editor.setText('' if not color else color.upper())

    def get_value(self):
        color = self.line_editor.text()
        if not COLOR_RE.match(color):
            return None
        return color


class SearchEdit(QtGui.QLineEdit):
    def __init__(self, *args, **kwargs):
        QtGui.QLineEdit.__init__(self, *args, **kwargs)
        self.setPlaceholderText(_('Search…'))
        self.setStyleSheet("QLineEdit { padding: 2px; border-radius: 9px; border-color: #8e8e8e; };"
                           "QLineEdit:focus { padding: 2px; border-radius: 9px; };")




if __name__ == '__main__':
    import doctest

    doctest.testmod()