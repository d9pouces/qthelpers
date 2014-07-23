# coding=utf-8
import base64
import functools
import itertools
import os
import threading

from PySide import QtGui, QtCore
import time

from qthelpers.application import application
from qthelpers.docks import BaseDock
from qthelpers.fields import ChoiceField
from qthelpers.forms import FormDialog, TabbedMultiForm, FormName, SubForm
from qthelpers.menus import registered_menu_actions, registered_menus, menu_item, MenuAction
from qthelpers.shortcuts import get_icon, warning, v_layout, get_pixmap, create_button
from qthelpers.toolbars import registered_toolbars, registered_toolbar_actions, toolbar_item, BaseToolBar
from qthelpers.translation import ugettext as _
from qthelpers.utils import p

__author__ = 'flanker'


class AboutWindow(QtGui.QDialog):
    def __init__(self, message, parent=None):
        super().__init__(p(parent))
        widgets = []
        if application.splashscreen_icon:
            pixmap = get_pixmap(application.splashscreen_icon)
            label = QtGui.QLabel(p(self))
            label.setPixmap(pixmap)
            widgets.append(label)
            edit = QtGui.QTextEdit(message, self)
            edit.setReadOnly(True)
            widgets.append(edit)
        widgets.append(create_button(_('Close'), min_size=True, parent=self, connect=self.close))
        self.setLayout(v_layout(self, *widgets))


class SettingsWindow(FormDialog):
    verbose_name = _('Preferences')
    text_cancel = None

    class Settings(TabbedMultiForm):
        class OtherSettings(SubForm):
            verbose_name = FormName(_('Other settings'))
            theme = ChoiceField(verbose_name=_('Graphical theme'), default='SnowIsh',
                                choices=(('SnowIsh', _('SnowIsh')), ('Faenza', _('Faenza'))), )

    @staticmethod
    def load_settings():
        values = {}
        from qthelpers.preferences import preferences
        if preferences.icon_theme_key:
            values['theme'] = preferences[preferences.icon_theme_key]
        return values

    @staticmethod
    def save_settings(values):
        from qthelpers.preferences import preferences
        if preferences.icon_theme_key:
            preferences[preferences.icon_theme_key] = values['theme']

    @classmethod
    def settings(cls):
        initial = cls.load_settings()
        values = cls.process(initial=initial)
        if values is not None:
            cls.save_settings(values)


class BaseMainWindow(QtGui.QMainWindow):
    description_icon = None
    verbose_name = _('Main application window')
    docks = []  # list of subclasses of qthelpers.docks.BaseDock
    _window_counter = itertools.count()
    _generic_signal = QtCore.Signal(list)

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, p(parent))

        self._window_id = next(BaseMainWindow._window_counter)
        self._docks = {}
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
                        defined_qtoolbars[toolbar_name] = BaseToolBar(toolbar_name, p(self))
                    else:
                        defined_qtoolbars[toolbar_name] = BaseToolBar(_('Toolbar'), p(self))
                    self.addToolBar(defined_qtoolbars[toolbar_name])
            for toolbar_action in registered_toolbar_actions[cls_name]:
                if toolbar_action.uid in created_action_keys:  # skip overriden actions (there are already created)
                    continue
                created_action_keys.add(toolbar_action.uid)
                toolbar_action.create(self, defined_qtoolbars[toolbar_action.toolbar])

        # create all dock widgets
        for dock_cls in self.docks:
            """:type dock_cls: type"""
            if not isinstance(dock_cls, type) or not issubclass(dock_cls, BaseDock):
                continue
            dock = dock_cls(parent=self)
            """:type dock: BaseDock"""
            self._docks[dock_cls] = dock
            self.addDockWidget(dock.default_position, dock)
            menu_name = dock.menu
            if menu_name is not None:
                if menu_name not in defined_qmenus:
                    defined_qmenus[menu_name] = menubar.addMenu(menu_name)
                    connect = functools.partial(self._base_swap_dock_display, dock_cls)
                    action = MenuAction(connect, verbose_name=dock.verbose_name, menu=menu_name, shortcut=dock.shortcut)
                    action.create(self, defined_qmenus[menu_name])

        # some extra stuff
        self.setWindowTitle(self.verbose_name)
        if self.description_icon:
            self.setWindowIcon(get_icon(self.description_icon))

        self.setCentralWidget(self.central_widget())
        self._generic_signal.connect(self._generic_slot)
        # restore state and geometry
        # noinspection PyBroadException
        try:
            cls_name = self.__class__.__name__
            if cls_name in application['GlobalInfos/main_window_geometries']:
                geometry_str = application['GlobalInfos/main_window_geometries'][cls_name].encode('utf-8')
                geometry = base64.b64decode(geometry_str)
                self.restoreGeometry(geometry)
            if cls_name in application['GlobalInfos/main_window_states']:
                state_str = application['GlobalInfos/main_window_states'][cls_name].encode('utf-8')
                state = base64.b64decode(state_str)
                self.restoreState(state)
        except Exception:
            pass

        self.adjustSize()
        self.raise_()

    def _base_swap_dock_display(self, dock_cls):
        dock = self._docks[dock_cls]
        """:type: qthelpers.docks.BaseDock"""
        if dock.isHidden():
            dock.show()
        else:
            dock.hide()

    def central_widget(self):
        raise NotImplementedError

    def closeEvent(self, event):
        state = self.saveState()
        state = bytes(state.data())
        str_state = base64.b64encode(state).decode('utf-8')  # automatically save window state
        """:type: str"""
        application['GlobalInfos/main_window_states'][self.__class__.__name__] = str_state
        geometry = self.saveGeometry()
        geometry = bytes(geometry.data())
        str_geometry = base64.b64encode(geometry).decode('utf-8')  # automatically save window geometry
        """:type: str"""
        application['GlobalInfos/main_window_geometries'][self.__class__.__name__] = str_geometry
        del application.windows[self._window_id]
        super().closeEvent(event)

    # noinspection PyMethodMayBeStatic
    def _generic_slot(self, arguments: list):
        """
        Generic slot, connected to self.generic_signal
        :param arguments: list of [callable, args: list, kwargs: dict]
        :return: nothing

        Never do it static! Segfault on the exit otherwise…
        """
        my_callable = arguments[0]
        my_callable(*(arguments[1]), **(arguments[2]))

    def generic_call(self, my_callable, *args, **kwargs):
        self._generic_signal.emit([my_callable, args, kwargs])


class SingleDocumentWindow(BaseMainWindow):
    document_known_extensions = _('Text files (*.txt);;HTML files (*.html *.htm)')
    base_max_recent_documents = 10
    settings_class = SettingsWindow

    def __init__(self, filename=None):
        super().__init__()
        self.current_document_filename = None
        self.current_document_is_modified = False  # your responsibility!
        self.base_stop_threads = False
        self.base_threads = []
        self.statusBar()
        self._indicators = {}
        if filename:
            self.base_open_document(filename)
        else:
            self.base_new_document()
        auto_save = threading.Thread(target=self.base_auto_save_thread, name='auto_save')
        auto_save.start()
        self.base_threads.append(auto_save)

    def closeEvent(self, event: QtCore.QEvent):
        if self._base_check_is_modified():
            event.ignore()
            return
        self.unload_document()
        self.base_stop_threads = True
        for thread in self.base_threads:
            thread.join()
        super().closeEvent(event)

    def base_set_sb_indicator(self, key, icon_name=None, message=None):
        if key not in self._indicators:
            label = QtGui.QLabel(p(self))
            statusbar = self.statusBar()
            """:type: QtGui.QStatusBar"""
            statusbar.insertPermanentWidget(len(self._indicators), label, 0)
            self._indicators[key] = label
        else:
            label = self._indicators[key]
            """:type: QtGui.Label"""
        if icon_name is not None:
            label.setPixmap(get_pixmap(icon_name))
        if message is not None:
            label.setText(message)

    def base_set_sb_message(self, message, msecs=0):
        status = self.statusBar()
        """:type: QtGui.QStatusBar"""
        status.showMessage(message, msecs)

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
                    self.generic_call(self.base_save_document)

    @menu_item(verbose_name=_('New document'), menu=_('File'), shortcut='Ctrl+N')
    @toolbar_item(verbose_name=_('New document'), icon='document-new')
    def base_new_document(self):
        self.unload_document()
        self.current_document_filename = None
        self.current_document_is_modified = False
        self.base_window_title()
        self.create_document()

    def _base_check_is_modified(self):
        return self.current_document_is_modified and not warning(_('The document has been modified'),
                                                                 _('The current document has been modified. '
                                                                 'Any change will be lost if you close it. '
                                                                 'Do you really want to continue?'))

    @menu_item(verbose_name=_('Open…'), menu=_('File'), shortcut='Ctrl+O')
    @toolbar_item(verbose_name=_('Open…'), icon='document-open')
    def base_open_document(self, filename=None):
        if self._base_check_is_modified():
            return False
        if not filename:
            # noinspection PyCallByClass
            (filename, selected_filter) = QtGui.QFileDialog.getOpenFileName(p(self), _('Please select a file'),
                                                                            application.GlobalInfos.last_open_folder,
                                                                            self.document_known_extensions)
            if not filename:
                return False
            application.GlobalInfos.last_open_folder = os.path.dirname(filename)
        if not self.is_valid_document(filename):
            warning(_('Invalid document'), _('Unable to open document %(filename)s.') %
                    {'filename': os.path.basename(filename)},
                    only_ok=True)
            return False
        self.unload_document()
        self.current_document_filename = filename
        self.current_document_is_modified = False
        self.base_window_title()
        self.base_add_recent_filename()
        self.load_document()
        return True

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
        if self._base_check_is_modified():
            return False
        return self.close()

    @menu_item(verbose_name=_('Save document'), menu=_('File'), shortcut='Ctrl+S')
    @toolbar_item(verbose_name=_('Open…'), icon='document-save')
    def base_save_document(self, filename=None):
        if filename:
            self.current_document_filename = filename
        if not self.current_document_filename:
            # noinspection PyCallByClass
            (filename, selected_filter) = QtGui.QFileDialog.getSaveFileName(p(self), _('Please choose a name'),
                                                                            application.GlobalInfos.last_save_folder,
                                                                            filter=self.document_known_extensions)
            if not filename:
                return False
            application.GlobalInfos.last_save_folder = os.path.dirname(filename)
            self.current_document_filename = filename
        if not self.save_document():
            return False
        self.current_document_is_modified = False
        self.base_window_title()
        self.base_add_recent_filename()
        return True

    @menu_item(verbose_name=_('Save as…'), menu=_('File'))
    def base_save_document_as(self):
        # noinspection PyCallByClass
        (filename, selected_filter) = QtGui.QFileDialog.getSaveFileName(p(self), _('Please choose a name'),
                                                                        application.GlobalInfos.last_save_folder,
                                                                        filter=self.document_known_extensions)
        if not filename:
            return False
        application.GlobalInfos.last_save_folder = os.path.dirname(filename)
        self.current_document_filename = filename
        if self.save_document():
            self.current_document_is_modified = False
            self.base_window_title()
            self.base_add_recent_filename()
            return True
        return False

    @menu_item(verbose_name=_('New window'), menu=_('Window'))
    def base_new_window(self):
        new_window = self.__class__()
        new_window.show()

    @menu_item(verbose_name=_('About'), menu=_('Help'))
    def base_about(self):
        application.about()

    @menu_item(verbose_name=_('Preferences…'), menu=_('Help'))
    def base_settings(self):
        self.settings_class.settings()

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

    def base_mark_document_as_modified(self, modified=True):
        if not self.current_document_is_modified and modified:
            self.current_document_is_modified = True
            self.base_window_title()
        elif self.current_document_is_modified and not modified:
            self.current_document_is_modified = False
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