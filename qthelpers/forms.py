# coding=utf-8
import itertools

import functools
from PySide import QtCore, QtGui

from qthelpers.exceptions import InvalidValueException
from qthelpers.fields import FieldGroup, IndexedButtonField, Field, ButtonField
from qthelpers.shortcuts import create_button, get_icon, h_layout, v_layout, warning
from qthelpers.translation import ugettext as _
from qthelpers.utils import p, ThreadedCalls


__author__ = 'flanker'


class FormName(object):
    counter = itertools.count()

    def __init__(self, verbose_name=None):
        # noinspection PyProtectedMember
        self.index = next(Field._field_counter)
        self.verbose_name = verbose_name

    def __str__(self):
        return self.verbose_name


class BaseForm(FieldGroup):
    def __init__(self, initial=None):
        FieldGroup.__init__(self, initial=initial)
        self._multiforms = {}
        """:type: dict of [str, MultiForm|SubForm]"""
        self._widgets = {}
        # retrieve all MultiForm classes from class definitions
        for cls in self.__class__.__mro__:
            for name, subcls in cls.__dict__.items():
                if not isinstance(subcls, type) or (not issubclass(subcls, MultiForm)
                                                    and not issubclass(subcls, SubForm)) or name in self._multiforms:
                    continue
                self._multiforms[name] = subcls(initial=initial, parent=self)

    def set_values(self, initial: dict) -> None:
        for name, field in self._fields.items():
            if name in initial:
                widget = self._widgets[name]
                field.set_widget_value(widget, initial[name])
        for multiform in self._multiforms.values():
            if isinstance(multiform, SubForm):
                multiform.set_values(initial)
            elif isinstance(multiform, MultiForm):
                multiform.set_values(initial)

    def _fill_grid_layout(self, layout: QtGui.QGridLayout):
        """ Fill a QGridLayout with all MultiForms and Field, in the right order
        :param layout:
        :return:
        """
        all_components = []
        for multiform in self._multiforms.values():
            all_components.append(multiform)
        for field in self._fields.values():
            all_components.append(field)
        all_components.sort(key=self._sort_components)
        row_offset = layout.rowCount()
        for row_index, obj in enumerate(all_components):
            if isinstance(obj, MultiForm):  # a MultiForm already is a QWidget
                layout.addWidget(obj, row_offset + row_index, 0, 1, 2)
            elif isinstance(obj, SubForm):
                widget = QtGui.QGroupBox(str(obj.verbose_name), p(self))
                sub_layout = QtGui.QGridLayout(p(widget))
                obj._fill_grid_layout(sub_layout)
                widget.setLayout(sub_layout)
                layout.addWidget(widget, row_offset + row_index, 0, 1, 2)
            else:
                widget = obj.get_widget(self, self)
                self._widgets[obj.name] = widget
                obj.set_widget_value(widget, self._values[obj.name])
                if obj.label:
                    label = QtGui.QLabel(obj.label, p(self))
                    label.setDisabled(obj.disabled)
                    layout.addWidget(label, row_offset + row_index, 0)
                layout.addWidget(widget, row_offset + row_index, 1)

    def _fill_form_layout(self, layout: QtGui.QFormLayout):
        """ Fill a QGridLayout with all MultiForms and Field, in the right order
        :param layout:
        :return:
        """
        all_components = []
        for multiform in self._multiforms.values():
            all_components.append(multiform)
        for field in self._fields.values():
            all_components.append(field)
        all_components.sort(key=self._sort_components)
        for row_index, obj in enumerate(all_components):
            if isinstance(obj, MultiForm):  # a MultiForm already is a QWidget
                layout.addRow(obj)
            elif isinstance(obj, SubForm):
                widget = QtGui.QGroupBox(str(obj.verbose_name), p(self))
                sub_layout = QtGui.QFormLayout(p(widget))
                obj._fill_form_layout(sub_layout)
                widget.setLayout(sub_layout)
                layout.addRow(widget)
            else:
                widget = obj.get_widget(self, self)
                self._widgets[obj.name] = widget
                obj.set_widget_value(widget, self._values[obj.name])
                layout.addRow(obj.label or '', widget)

    def is_valid(self):
        valid = True
        self._values = {}
        for field_name, field in self._fields.items():
            widget = self._widgets[field_name]
            try:
                setattr(self, field_name, field.get_widget_value(widget))
                field.set_widget_valid(widget, True, '')
                self._values[field_name] = field.get_widget_value(widget)
            except InvalidValueException as e:
                field.set_widget_valid(widget, False, str(e))
                valid = False
        for multiform in self._multiforms.values():
            if multiform.is_valid():
                self._values.update(multiform.get_values())
            else:
                valid = False
        return valid

    def get_widget(self, field_name):  # TODO rechercher dans les multiforms
        return self._widgets[field_name]

    def get_widgets(self):
        return self._widgets

    def get_multiform(self, multiform_name):
        return self._multiforms[multiform_name]

    def get_values(self):
        return self._values

    @staticmethod
    def _sort_components(obj) -> int:
        if isinstance(obj, MultiForm) or isinstance(obj, SubForm):
            return getattr(obj.verbose_name, 'index', 0)
        return obj.group_field_order


class Form(BaseForm, QtGui.QWidget):
    def __init__(self, initial=None, parent=None):
        BaseForm.__init__(self, initial=initial)
        QtGui.QWidget.__init__(self, p(parent))
        layout = QtGui.QGridLayout(p(parent))
        self._fill_grid_layout(layout)
        self.setLayout(layout)


class SubForm(Form):
    verbose_name = None  # FormName(_('My Tab Name'))
    enabled = True


# class MyDialog(GenericForm):
# field_1 = CharField()
#     class tabs(MultiForm):
#         class tab_1(SubForm):
#             verbose_name = FormName('First Tab')
#             field_str_1 = CharField()


class MultiForm(object):
    verbose_name = None  # FormName('')

    def __init__(self, initial=None):
        """
        :param initial: Dictionnary of initial values
        :return:
        """
        self._subforms_by_name = {}
        self._subforms_list = []
        self._values = {}
        for cls in self.__class__.__mro__:
            for subform_name, subform_class in cls.__dict__.items():
                if isinstance(subform_class, type) and issubclass(subform_class, SubForm) \
                        and subform_name not in self._subforms_by_name:
                    subform = subform_class(initial=initial)
                    """:type: SubForm"""
                    self._subforms_by_name[subform_name] = subform
                    self._subforms_list.append((subform_name, subform))
        self._subforms_list.sort(key=lambda x: getattr(x[1].verbose_name, 'index', 0))
        for subform_index, (subform_name, subform) in enumerate(self._subforms_list):
            self.add_form(subform_index, subform_name, subform)
            self.set_form_enabled(subform_index, subform, bool(subform.enabled))

    def set_values(self, initial: dict) -> None:
        for subform in self._subforms_list:
            subform.set_values(initial)

    def __getattribute__(self, item: str):
        if not item.startswith('_') and item in self._subforms_by_name:
            return self._subforms_by_name[item]
        return super().__getattribute__(item)

    def set_current(self, index: int, name: str, subform: SubForm):
        raise NotImplementedError

    def add_form(self, index: int, name: str, subform: SubForm):
        raise NotImplementedError

    def set_form_enabled(self, index, name, enabled):
        raise NotImplementedError

    def is_valid(self):
        valid = True
        self._values = {}
        for subform_index, subform_data in enumerate(self._subforms_list):
            subform_name, subform = subform_data
            """:type: (int, FormTab)"""
            if subform.is_valid():
                self._values.update(subform.get_values())
            elif valid:
                self.set_current(subform_index, str(subform.verbose_name), subform)
                valid = False
            else:
                valid = False
        return valid

    def get_values(self):
        return self._values


class FormDialog(BaseForm, QtGui.QDialog, ThreadedCalls):
    verbose_name = None
    description = None
    text_confirm = _('Yes')
    text_cancel = _('Cancel')

    def __init__(self, initial=None, parent=None):
        QtGui.QDialog.__init__(self, p(parent))
        BaseForm.__init__(self, initial=initial)
        ThreadedCalls.__init__(self)
        # widget creation
        widgets = []
        if self.description:
            widgets.append(QtGui.QLabel(self.description, p(self)))
        sub_layout = QtGui.QFormLayout(self)
        self._fill_form_layout(layout=sub_layout)
        widgets.append(sub_layout)
        self._buttons = []
        if self.text_confirm:
            self._buttons.append(create_button(self.text_confirm, connect=self.accept, min_size=True))
        if self.text_cancel:
            self._buttons.append(create_button(self.text_cancel, connect=self.reject, min_size=True))
        if self._buttons:
            widgets.append(h_layout(self, *self._buttons, direction=QtGui.QBoxLayout.RightToLeft))
        self.setLayout(v_layout(self, *widgets))
        if self.verbose_name:
            self.setWindowTitle(str(self.verbose_name))
        self.raise_()

    @classmethod
    def process(cls, initial=None, parent=None):
        dialog = cls(initial=initial, parent=parent)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            return dialog.get_values()
        return None

    def accept(self):
        if not self.is_valid():
            return
        return QtGui.QDialog.accept(self)


class TabbedMultiForm(MultiForm, QtGui.QTabWidget):
    def __init__(self, initial=None, parent=None):
        QtGui.QTabWidget.__init__(self, p(parent))
        MultiForm.__init__(self, initial=initial)

    def set_current(self, index: int, name: str, subform: SubForm):
        self.setCurrentIndex(index)

    def add_form(self, index: int, name: str, subform: SubForm):
        self.addTab(subform, str(subform.verbose_name))

    def set_form_enabled(self, index, name, enabled):
        self.setTabEnabled(index, enabled)


class StackedMultiForm(MultiForm, QtGui.QGroupBox):
    def __init__(self, initial=None, parent=None):
        QtGui.QGroupBox.__init__(self, p(parent))
        self._stacked_names = QtGui.QComboBox(p(self))
        # noinspection PyUnresolvedReferences
        self._stacked_names.currentIndexChanged.connect(self._change_widget)
        self._stacked_widget = QtGui.QStackedWidget(p(self))
        MultiForm.__init__(self, initial=initial)
        self.setTitle(str(self.verbose_name))
        self.setLayout(v_layout(self, self._stacked_names, self._stacked_widget))

    def set_current(self, index: int, name: str, subform: SubForm):
        self._stacked_widget.setCurrentIndex(index)
        self._stacked_names.setCurrentIndex(index)

    def add_form(self, index: int, name: str, subform: SubForm):
        self._stacked_widget.addWidget(subform)
        self._stacked_names.addItem(str(subform.verbose_name))

    def _change_widget(self, index):
        self._stacked_widget.setCurrentIndex(index)

    def set_form_enabled(self, index, name, enabled):
        pass


class ToolboxMultiForm(MultiForm, QtGui.QToolBox):
    def __init__(self, initial=None, parent=None):
        QtGui.QToolBox.__init__(self, p(parent))
        MultiForm.__init__(self, initial=initial)

    def set_current(self, index: int, name: str, subform: SubForm):
        self.setCurrentIndex(index)

    def add_form(self, index: int, name: str, subform: SubForm):
        self.addItem(subform, str(subform.verbose_name))

    def set_form_enabled(self, index, name, enabled):
        self.setItemEnabled(index, enabled)


class Formset(QtGui.QTreeWidget):
    """
    """
    min_number = None
    max_number = None
    show_headers = True  # display treewidget headers?
    add_button = False  # display + / -
    remove_button = False
    add_help_text = ''
    remove_help_text = ''

    def __init__(self, initial: list=None, parent=None):
        """
        :param initial: initial values, as a dictionnary {field_name: field_value}
        """
        QtGui.QTreeWidget.__init__(self, p(parent))
        if initial is None:
            initial = []
        self._fields = {}
        item_count = len(initial)
        if self.min_number is not None:
            item_count = max(self.min_number, item_count)
        if self.max_number is not None:
            item_count = min(self.max_number, item_count)
        # noinspection PyUnusedLocal
        self._values = [{} for i in range(item_count)]
        fields = []
        for cls in self.__class__.__mro__:
            for field_name, field in cls.__dict__.items():
                if not isinstance(field, Field) or field_name in self._fields:
                    continue
                self._fields[field_name] = field
                field.name = field_name
                for index in range(item_count):  # get initial values
                    if index < len(initial):
                        self._values[index][field_name] = initial[index].get(field_name, field.default)
                    else:
                        self._values[index][field_name] = field.default
                fields.append((field.group_field_order, field_name))
        fields.sort()
        self._field_order = [f[1] for f in fields]
        headers = [self._fields[field_name].verbose_name for field_name in self._field_order]
        if self.remove_button:
            key = '1__'
            self._field_order.insert(0, key)
            headers.insert(0, '')
            self._fields[key] = ButtonField(connect=self.remove_item, legend='', icon='list-remove',
                                            verbose_name='', help_text=self.remove_help_text, default=None)
        if self.add_button:
            key = '0__'
            self._field_order.insert(0, key)
            headers.insert(0, '')
            self._fields[key] = ButtonField(connect=self.add_item, legend='', icon='list-add',
                                            verbose_name='', help_text=self.add_help_text, default=None)
        if self.show_headers:
            self.setHeaderLabels(headers)
        else:
            self.header().close()
        for values in self._values:
            self.__insert_item(values, index=None)

    def __insert_item(self, values: dict, index: int or None=None):
        item = QtGui.QTreeWidgetItem(self, QtGui.QTreeWidgetItem.Type)
        if index is None:
            self.addTopLevelItem(item)
        else:
            self.insertTopLevelItem(index, item)
        for column, field_name in enumerate(self._field_order):
            field = self._fields[field_name]
            widget = field.get_widget(item, self)
            field.set_widget_value(widget, values.get(field_name, field.default))
            self.setItemWidget(item, column, widget)
        for index in range(self.columnCount()):
            self.resizeColumnToContents(index)

    def add_item(self, item):
        if self.max_number is not None and self.topLevelItemCount() >= self.max_number:
            warning(_('Unable to add item'), _('Unable to add more than %(s)d items.') % {'s': self.max_number},
                    only_ok=True)
            return
        index = self.indexOfTopLevelItem(item)
        self.__insert_item(values={}, index=index)

    def remove_item(self, item):
        if self.min_number is not None and self.topLevelItemCount() <= self.min_number:
            warning(_('Unable to remove item'), _('At least %(s)d items are required.') % {'s': self.min_number},
                    only_ok=True)
            return
        index = self.indexOfTopLevelItem(item)
        self.takeTopLevelItem(index)

    def get_values(self):
        values = []
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            data = {}
            for column, field_name in enumerate(self._field_order):
                field = self._fields[field_name]
                widget = self.itemWidget(item, column)
                data[field_name] = field.get_widget_value(widget)
            values.append(data)
        return values


if __name__ == '__main__':
    import doctest

    doctest.testmod()