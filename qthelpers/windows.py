# coding=utf-8
import functools
import itertools
import os

from PySide import QtGui

from qthelpers.application import application
from qthelpers.menus import registered_menu_actions, registered_menus, menu_item, MenuAction
from qthelpers.shortcuts import get_icon, warning
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


class SingleDocumentWindow(BaseMainWindow):
    document_known_extensions = _('Text files (*.txt);;HTML files (*.html *.htm)')

    def __init__(self, filename=None):
        super().__init__()
        self.current_document_filename = None
        self.current_document_is_modified = False  # your responsibility!
        if filename:
            self.base_open_document(filename)
        else:
            self.create_document()

    @menu_item(verbose_name=_('Open document'), menu=_('File'))
    def base_open_document(self, filename=None):
        if not filename:
            # noinspection PyCallByClass
            (filename, selected_filter) = QtGui.QFileDialog.getOpenFileName(self, _('Please select a file'),
                                                                            application.GlobalInfos.last_open_folder,
                                                                            self.document_known_extensions)
            if not filename:
                return
            application.GlobalInfos.last_open_folder = os.path.dirname(filename)
        if not self.is_valid_document(filename):
            warning(_('Invalid document'), _('Unable to open document %(filename)s.') % {os.path.basename(filename)},
                    only_ok=True)
            return
        self.unload_document()
        self.current_document_filename = filename
        self.current_document_is_modified = False
        self.base_window_title()
        self.load_document()

    @menu_item(verbose_name=_('New document'), menu=_('File'))
    def base_new_document(self):
        self.unload_document()
        self.current_document_filename = None
        self.current_document_is_modified = False
        self.base_window_title()
        self.create_document()

    @menu_item(verbose_name=_('Save document'), menu=_('File'))
    def base_save_document(self, filename=None):
        if filename:
            self.current_document_filename = filename
        if not self.current_document_filename:
            # noinspection PyCallByClass
            (filename, selected_filter) = QtGui.QFileDialog.getSaveFileName(self, _('Please choose a name'),
                                                                            application.GlobalInfos.last_save_folder,
                                                                            filter=self.document_known_extensions)
            if not filename:
                return
            application.GlobalInfos.last_save_folder = os.path.dirname(filename)
            self.current_document_filename = filename
        self.save_document()
        self.current_document_is_modified = False
        self.base_window_title()

    @menu_item(verbose_name=_('Save as…'), menu=_('File'))
    def base_save_document_as(self):
        # noinspection PyCallByClass
        (filename, selected_filter) = QtGui.QFileDialog.getSaveFileName(self, _('Please choose a name'),
                                                                        application.GlobalInfos.last_save_folder,
                                                                        filter=self.document_known_extensions)
        if not filename:
            return
        application.GlobalInfos.last_save_folder = os.path.dirname(filename)
        self.current_document_filename = filename
        self.save_document()
        self.current_document_is_modified = False
        self.base_window_title()

    @menu_item(verbose_name=_('Open recent…'), menu=_('File'), submenu=True)
    def base_open_recent(self):
        actions = []
        for k, v in application.GlobalInfos.last_documents:
            if not os.path.isfile(k):
                continue
            actions.append(MenuAction(functools.partial(self.base_open_document, k), _('Open %(name)s') % {'name': v},
                                      _('File')))
        return actions

    def base_add_open_document(self):
        filename = self.current_document_filename
        if filename:
            application.GlobalInfos.last_documents.append((filename, os.path.basename(filename)))

    def base_window_title(self):
        if self.current_document_filename is not None:
            # noinspection PyTypeChecker
            title = '%s%s - %s - [%s]' % (os.path.basename(self.current_document_filename),
                                          '*' if self.current_document_is_modified else '',
                                          application.application_name, os.path.dirname(self.current_document_filename))
        else:
            title = '%s - [%s]' % (application.application_name, application.GlobalInfos.last_save_folder)
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