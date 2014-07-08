# coding=utf-8
import functools
import itertools
import os
import threading

from PySide import QtGui, QtCore
import time

from qthelpers.application import application
from qthelpers.menus import registered_menu_actions, registered_menus, menu_item, MenuAction
from qthelpers.shortcuts import get_icon, warning
from qthelpers.toolbars import registered_toolbars, registered_toolbar_actions
from qthelpers.translation import ugettext as _
from qthelpers.utils import p


__author__ = 'flanker'


class BaseMainWindow(QtGui.QMainWindow):
    description_icon = None
    verbose_name = _('Main application window')
    _window_counter = itertools.count()
    generic_signal = QtCore.Signal(list)

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, p(parent))

        self._window_id = next(BaseMainWindow._window_counter)
        application.windows[self._window_id] = self

        # retrieve menus and associated actions from the whole class hierarchy
        menubar = self.menuBar()
        defined_qmenus = {}
        created_action_keys = set()
        supernames = [x.__name__.rpartition('.')[2] for x in self.__class__.__mro__]
        supernames.reverse()
        for cls_name in supernames:
            for menu_name in registered_menus.get(cls_name, []):  # create all top-level menus
                if menu_name not in defined_qmenus:
                    defined_qmenus[menu_name] = menubar.addMenu(menu_name)
        supernames.reverse()
        for cls_name in supernames:
            for menu_action in registered_menu_actions.get(cls_name, []):
                if menu_action.uid in created_action_keys:  # skip overriden actions (there are already created)
                    continue
                created_action_keys.add(menu_action.uid)
                menu_action.create(self, defined_qmenus[menu_action.menu])

        # retrieve toolbar actions from the whole class hierarchy
        self.setUnifiedTitleAndToolBarOnMac(True)
        defined_qtoolbars = {}
        created_action_keys = set()
        for superclass in self.__class__.__mro__:
            cls_name = superclass.__name__.rpartition('.')[2]
            if cls_name not in registered_toolbars:
                continue
            for toolbar_name in registered_toolbars[cls_name]:  # create all top-level menus
                if toolbar_name not in defined_qtoolbars:
                    if toolbar_name is not None:
                        defined_qtoolbars[toolbar_name] = QtGui.QToolBar(toolbar_name, p(self))
                    else:
                        defined_qtoolbars[toolbar_name] = QtGui.QToolBar(_('Toolbar'), p(self))
                    self.addToolBar(defined_qtoolbars[toolbar_name])
            for toolbar_action in registered_toolbar_actions[cls_name]:
                if toolbar_action.uid in created_action_keys:  # skip overriden actions (there are already created)
                    continue
                created_action_keys.add(toolbar_action.uid)
                toolbar_action.create(self, defined_qtoolbars[toolbar_action.toolbar])

        # some extra stuff
        self.setWindowTitle(self.verbose_name)
        if self.description_icon:
            self.setWindowIcon(get_icon(self.description_icon))

        self.setCentralWidget(self.central_widget())
        self.generic_signal.connect(self.generic_slot)
        self.adjustSize()
        self.raise_()

    def central_widget(self):
        raise NotImplementedError

    def closeEvent(self, event):
        del application.windows[self._window_id]
        super().closeEvent(event)

    # noinspection PyMethodMayBeStatic
    def generic_slot(self, arguments: list):
        """
        Generic slot, connected to self.generic_signal
        :param arguments: list of a callable and its arguments
        :return: nothing
        """
        my_callable = arguments[0]
        my_callable(my_callable, *(arguments[1:]))


class SingleDocumentWindow(BaseMainWindow):
    document_known_extensions = _('Text files (*.txt);;HTML files (*.html *.htm)')
    base_max_recent_documents = 10

    def __init__(self, filename=None):
        super().__init__()
        self.current_document_filename = None
        self.current_document_is_modified = False  # your responsibility!
        self.base_stop_threads = False
        self.base_threads = []
        if filename:
            self.base_open_document(filename)
        else:
            self.base_new_document()

        auto_save = threading.Thread(target=self.base_auto_save_thread, name='auto_save')
        auto_save.start()
        self.base_threads.append(auto_save)

    def closeEvent(self, event: QtCore.QEvent):
        if self.current_document_is_modified:
            ans = warning(_('The document has been modified'),
                          _('The current document has been modified. Any change will be lost if you close it. '
                            'Do you really want to continue?'))
            if not ans:
                event.ignore()
                return
        self.unload_document()
        super().closeEvent(event)
        self.base_stop_threads = True
        for thread in self.base_threads:
            thread.join()

    def base_auto_save_thread(self):
        while True:
            interval = application.GlobalInfos.auto_save_interval
            if interval <= 0:
                for i in range(10):
                    if self.base_stop_threads:
                        return
                    time.sleep(1)
            else:
                for i in range(interval):
                    if self.base_stop_threads:
                        return
                    time.sleep(1)
                if self.current_document_filename:
                    self.generic_signal.emit([self.base_save_document])

    @menu_item(verbose_name=_('New document'), menu=_('File'), shortcut='Ctrl+N')
    def base_new_document(self):
        self.unload_document()
        self.current_document_filename = None
        self.current_document_is_modified = False
        self.base_window_title()
        self.create_document()

    @menu_item(verbose_name=_('Open…'), menu=_('File'), shortcut='Ctrl+O')
    def base_open_document(self, filename=None):
        if not filename:
            # noinspection PyCallByClass
            (filename, selected_filter) = QtGui.QFileDialog.getOpenFileName(p(self), _('Please select a file'),
                                                                            application.GlobalInfos.last_open_folder,
                                                                            self.document_known_extensions)
            if not filename:
                return
            application.GlobalInfos.last_open_folder = os.path.dirname(filename)
        if not self.is_valid_document(filename):
            warning(_('Invalid document'), _('Unable to open document %(filename)s.') %
                    {'filename': os.path.basename(filename)},
                    only_ok=True)
            return
        self.unload_document()
        self.current_document_filename = filename
        self.current_document_is_modified = False
        self.base_window_title()
        self.base_add_recent_filename()
        self.load_document()

    @menu_item(verbose_name=_('Open recent…'), menu=_('File'), submenu=True)
    def base_open_recent(self):
        actions = []
        seen_basefilenames = set()
        for filename in application.GlobalInfos.last_documents:
            if not os.path.isfile(filename):
                continue
            basename = os.path.basename(filename)
            if basename in seen_basefilenames:
                basename = filename
            seen_basefilenames.add(basename)
            actions.append(MenuAction(functools.partial(self.base_open_document, filename),
                                      _('Open %(name)s') % {'name': basename}, _('File')))
        return actions

    @menu_item(verbose_name=_('Close document'), menu=_('File'), sep=True, shortcut='Ctrl+W')
    def base_close_document(self):
        self.close()

    @menu_item(verbose_name=_('Save document'), menu=_('File'), shortcut='Ctrl+S')
    def base_save_document(self, filename=None):
        if filename:
            self.current_document_filename = filename
        if not self.current_document_filename:
            # noinspection PyCallByClass
            (filename, selected_filter) = QtGui.QFileDialog.getSaveFileName(p(self), _('Please choose a name'),
                                                                            application.GlobalInfos.last_save_folder,
                                                                            filter=self.document_known_extensions)
            if not filename:
                return
            application.GlobalInfos.last_save_folder = os.path.dirname(filename)
            self.current_document_filename = filename
        self.save_document()
        self.current_document_is_modified = False
        self.base_window_title()
        self.base_add_recent_filename()

    @menu_item(verbose_name=_('Save as…'), menu=_('File'))
    def base_save_document_as(self):
        # noinspection PyCallByClass
        (filename, selected_filter) = QtGui.QFileDialog.getSaveFileName(p(self), _('Please choose a name'),
                                                                        application.GlobalInfos.last_save_folder,
                                                                        filter=self.document_known_extensions)
        if not filename:
            return
        application.GlobalInfos.last_save_folder = os.path.dirname(filename)
        self.current_document_filename = filename
        self.save_document()
        self.current_document_is_modified = False
        self.base_window_title()
        self.base_add_recent_filename()

    def base_add_recent_filename(self):
        new_filename = self.current_document_filename
        if not new_filename:
            return
        for filename in application.GlobalInfos.last_documents:
            if filename == new_filename:
                return
        application.GlobalInfos.last_documents.insert(0, new_filename)
        while len(application.GlobalInfos.last_documents) > self.base_max_recent_documents:
            del application.GlobalInfos.last_documents[self.base_max_recent_documents]

    def base_mark_document_as_modified(self):
        if not self.current_document_is_modified:
            self.current_document_is_modified = True
            self.base_window_title()

    def base_window_title(self):
        if self.current_document_filename is not None:
            # noinspection PyTypeChecker
            title = '%s%s - %s - [%s]' % (os.path.basename(self.current_document_filename),
                                          '*' if self.current_document_is_modified else '',
                                          application.verbose_name, os.path.dirname(self.current_document_filename))
        else:
            title = '%s%s - [%s]' % (application.verbose_name,
                                     '*' if self.current_document_is_modified else '',
                                     application.GlobalInfos.last_save_folder)
        self.setWindowTitle(title)

    def is_valid_document(self, filename):
        """ Check if filename is a valid document
        :return:
        """
        raise NotImplementedError

    def load_document(self):
        """ Load the document self.current_document_filename
        self.current_document_filename is set to None, self.current_document_is_modified is set to False
        :return: boolean if everything is ok
        """
        raise NotImplementedError

    def unload_document(self):
        """ Unload the current loaded document (if it exists)
        :return:
        """
        raise NotImplementedError

    def create_document(self):
        """ Create a new blank document
        self.current_document_filename is set to None, self.current_document_is_modified is set to False
        :return:
        """
        raise NotImplementedError

    def save_document(self):
        """ Save the current loaded document (if it exists) into self.current_document_filename
        It's your responsibility to update self.current_document_is_modified to True
        :return: boolean if everything is ok
        """
        raise NotImplementedError


if __name__ == '__main__':
    import doctest

    doctest.testmod()