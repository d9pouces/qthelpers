# coding=utf-8
import functools
import json
from PySide import QtGui, QtCore
import itertools
from qthelpers.exceptions import InvalidValueException
from qthelpers.shortcuts import create_button
from qthelpers.translation import ugettext as _
from qthelpers.utils import p
from qthelpers.widgets import FilepathWidget

__author__ = 'flanker'

palette_valid = QtGui.QPalette()
palette_valid.setColor(QtGui.QPalette.Base, QtGui.QColor(147, 234, 154))
palette_invalid = QtGui.QPalette()
palette_invalid.setColor(QtGui.QPalette.Base, QtGui.QColor(207, 0, 0))


class Field(object):
    _field_counter = itertools.count()

    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None, on_change=None):
        self.verbose_name = verbose_name
        self.name = None
        self.help_text = help_text
        self.default = default
        if validators is None:
            validators = []
        validators.insert(0, self.check_base_type)
        self.validators = validators
        self.disabled = disabled
        self.on_change = on_change
        self.group_field_order = next(Field._field_counter)

    @property
    def label(self):
        return self.verbose_name

    def is_valid(self, value) -> bool:
        if self.validators is not None:
            for validator in self.validators:
                validator(value)
        return True

    def check_base_type(self, value) -> None:
        raise NotImplementedError

    def serialize(self, value) -> str:
        raise NotImplementedError

    def deserialize(self, value: str):
        raise NotImplementedError

    def get_widget(self, field_group, parent=None):
        raise NotImplementedError

    def get_widget_value(self, widget):
        raise NotImplementedError

    def set_widget_value(self, widget, value):
        raise NotImplementedError

    def set_widget_valid(self, widget, valid: bool, msg: str):
        raise NotImplementedError

    def _on_change(self, on_change: callable, group, widget):
        value = self.get_widget_value(widget)
        on_change(group, widget, value)


class IndexedButtonField(Field):

    def __init__(self, connect=None, legend=None, icon=None, verbose_name='', help_text=None, default=None,
                 disabled=False, validators=None, on_change=None):
        super().__init__(verbose_name=verbose_name, help_text=help_text, default=default, disabled=disabled,
                         validators=validators, on_change=on_change)
        self.legend = legend
        self.icon = icon
        self.connect = connect

    def check_base_type(self, value):
        pass

    def serialize(self, value):
        return None

    def deserialize(self, value: str):
        return None

    def get_widget(self, field_group, parent=None):
        connect = functools.partial(self.connect, index=field_group.index)
        return create_button(self.legend, icon=self.icon, min_size=True, flat=True, help_text=self.help_text,
                             connect=connect, parent=parent)

    def get_widget_value(self, widget):
        return None

    def set_widget_value(self, widget, value):
        pass

    def set_widget_valid(self, widget, valid: bool, msg: str):
        pass


class CharField(Field):
    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None,
                 widget_validator=None, max_length=None, min_length=None, on_change=None):
        if validators is None:
            validators = []
        if min_length is not None:
            def valid_min(value):
                if value is not None and len(value) < min_length:
                    raise InvalidValueException(_('value must be at least %(m)d character long') % {'m': min_length})
            validators.append(valid_min)
        if max_length is not None:
            def valid_max(value):
                if value is not None and len(value) > max_length:
                    raise InvalidValueException(_('value must be at most %(m)d character long') % {'m': min_length})
            validators.append(valid_max)
        super().__init__(verbose_name, help_text, default, disabled, validators, on_change=on_change)
        self.widget_validator = widget_validator

    def check_base_type(self, value):
        if isinstance(value, str):
            return
        raise InvalidValueException(_('value must be a string'))

    def serialize(self, value) -> str:
        return value

    def deserialize(self, value: str):
        return value

    def get_widget(self, field_group, parent=None):
        editor = QtGui.QLineEdit(p(parent))
        if self.help_text is not None:
            editor.setToolTip(self.help_text)
        if self.widget_validator is not None:
            editor.setValidator(self.widget_validator)
        editor.setDisabled(self.disabled)
        return editor

    def get_widget_value(self, widget):
        return widget.text()

    def set_widget_value(self, widget, value: str):
        widget.setText(value)

    def set_widget_valid(self, widget, valid: bool, msg: str):
        widget.setPalette(palette_valid if valid else palette_invalid)


class IntegerField(Field):
    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None,
                 widget_validator=None, min_value=None, max_value=None, required=True, on_change=None):
        if validators is None:
            validators = []
        if min_value is not None:
            def valid_min(value):
                if value is not None and value < min_value:
                    raise InvalidValueException(_('value must be greater than %(m)d') % {'m': min_value})
            validators.append(valid_min)
        if max_value is not None:
            def valid_max(value):
                if value is not None and value > max_value:
                    raise InvalidValueException(_('value must be smaller than %(m)d') % {'m': max_value})
            validators.append(valid_max)
        if required:
            validators.insert(0, self.check_required)
        super().__init__(verbose_name, help_text, default, disabled, validators, on_change=on_change)
        widget_validator = self.default_widget_validator(max_value, min_value, widget_validator)
        self.widget_validator = widget_validator
        self.required = required

    def serialize(self, value) -> str:
        if value is None:
            return ''
        return str(value)

    def deserialize(self, value: str):
        if value == '':
            return None
        return int(value)

    def get_widget(self, field_group, parent=None):
        editor = QtGui.QLineEdit(p(parent))
        if self.help_text is not None:
            editor.setToolTip(self.help_text)
        editor.setValidator(self.widget_validator)
        editor.setDisabled(self.disabled)
        return editor

    def get_widget_value(self, widget) -> int:
        value = widget.text()
        if not value:
            return None
        return int(value)

    def set_widget_value(self, widget, value: int):
        if value is None:
            widget.setText('')
        else:
            widget.setText(str(value))

    def set_widget_valid(self, widget, valid: bool, msg: str):
        widget.setPalette(palette_valid if valid else palette_invalid)

    @staticmethod
    def default_widget_validator(max_value, min_value, widget_validator):
        if widget_validator is None:
            if min_value is None and max_value is None:
                widget_validator = None
            elif min_value is None:
                widget_validator = QtGui.QIntValidator(-1000000, int(max_value), None)
            elif max_value is None:
                widget_validator = QtGui.QIntValidator(min_value, 1000000, None)
            else:
                widget_validator = QtGui.QIntValidator(min_value, max_value, None)
        return widget_validator

    def check_base_type(self, value):
        if value is None or isinstance(value, int):
            return
        raise InvalidValueException(_('value must be a integer'))

    @staticmethod
    def check_required(value):
        if value is None:
            raise InvalidValueException(_('no value provided'))


class FloatField(IntegerField):

    def deserialize(self, value: str):
        if value == '':
            return None
        return float(value)

    def get_widget_value(self, widget) -> float:
        value = widget.text()
        if not value:
            return None
        return float(value)

    def set_widget_value(self, widget, value: float):
        if value is None:
            widget.setText('')
        else:
            widget.setText(str(value))

    def check_base_type(self, value):
        if value is None or isinstance(value, float):
            return
        raise InvalidValueException(_('value must be a float'))

    @staticmethod
    def default_widget_validator(max_value, min_value, widget_validator):
        if widget_validator is None:
            if min_value is None and max_value is None:
                widget_validator = None
            elif min_value is None:
                widget_validator = QtGui.QDoubleValidator(-1000000, int(max_value), 12, None)
            elif max_value is None:
                widget_validator = QtGui.QDoubleValidator(min_value, 1000000, 12, None)
            else:
                widget_validator = QtGui.QDoubleValidator(min_value, max_value, 12, None)
        return widget_validator


class BooleanField(Field):

    def serialize(self, value: bool) -> bool:
        return bool(value)

    def deserialize(self, value: bool) -> bool:
        return bool(value)

    def get_widget(self, field_group, parent=None):
        if self.verbose_name:
            editor = QtGui.QCheckBox(self.verbose_name, p(parent))
        else:
            editor = QtGui.QCheckBox(p(parent))
        if self.help_text:
            editor.setToolTip(self.help_text)
        editor.setDisabled(self.disabled)
        return editor

    def get_widget_value(self, widget):
        return widget.isChecked()

    def set_widget_value(self, widget, value: bool):
        widget.setChecked(value)

    def set_widget_valid(self, widget, valid: bool, msg: str):
        pass

    def check_base_type(self, value):
        if not isinstance(value, bool):
            raise InvalidValueException(_('Value must be a boolean'))

    @property
    def label(self):
        return None


class FilepathField(CharField):
    def __init__(self, verbose_name: str='', help_text: str=None, default: str=None, disabled: bool=False,
                 validators: list=None, selection_filter: str=None, required=True, on_change=None):
        if validators is None:
            validators = []
        if required:
            validators.insert(0, self.check_required)
        self.required = required
        super().__init__(verbose_name=verbose_name, help_text=help_text, default=default, disabled=disabled,
                         validators=validators, on_change=on_change)
        self.selection_filter = selection_filter

    def get_widget(self, field_group, parent=None):
        widget = FilepathWidget(selection_filter=self.selection_filter, parent=parent)
        widget.setDisabled(self.disabled)
        return widget

    @staticmethod
    def check_required(value):
        if value is None:
            raise InvalidValueException(_('no value provided'))

    def get_widget_value(self, widget: FilepathWidget):
        return widget.get_value()

    def set_widget_valid(self, widget: FilepathWidget, valid: bool, msg: str):
        widget.setPalette(palette_valid if valid else palette_invalid)

    def set_widget_value(self, widget: FilepathWidget, value: str):
        widget.set_value(value)


class ListField(Field):
    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None,
                 base_type=None, min_length=None, max_length=None, on_change=None):
        self.min_length = min_length
        self.max_length = max_length
        self.base_type = base_type
        if default is None:
            default = []
        if validators is None:
            validators = []
        if min_length is not None:
            def valid_min(value):
                if value is not None and len(value) < min_length:
                    raise InvalidValueException(_('list must count at least %(m)d values') % {'m': min_length})
            validators.append(valid_min)
        if max_length is not None:
            def valid_max(value):
                if value is not None and len(value) > max_length:
                    raise InvalidValueException(_('list must count at most %(m)d values') % {'m': min_length})
            validators.append(valid_max)
        super().__init__(verbose_name=verbose_name, help_text=help_text, disabled=disabled, validators=validators,
                         default=default, on_change=on_change)

    def serialize(self, value: list) -> list:
        return value

    def deserialize(self, value: list) -> list:
        return value

    def get_widget(self, field_group, parent=None):
        regexp = None
        if self.base_type == int:
            regexp = r'\d+(,\d+)*'
        elif self.base_type == float:
            regexp = r'(\?.\d+|\d+\.\d*)(,\?.\d+|,\d+\.\d)*'
        editor = QtGui.QLineEdit(p(parent))
        editor.setDisabled(self.disabled)
        if self.help_text is not None:
            editor.setToolTip(self.help_text)
        if regexp is not None:
            editor.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp(regexp), p(parent)))
        return editor

    def get_widget_value(self, widget) -> list:
        value = widget.text()
        if not value:
            return []
        values = value.split(',')
        if self.base_type == int:
            values = [int(x) for x in values]
        elif self.base_type == float:
            values = [float(x) for x in values]
        return values

    def set_widget_value(self, widget, value: list):
        widget.setText(','.join([str(x) for x in value]))

    def set_widget_valid(self, widget, valid: bool, msg: str):
        widget.setPalette(palette_valid if valid else palette_invalid)

    def check_base_type(self, value):
        if not isinstance(value, list) and not isinstance(value, tuple):
            raise InvalidValueException(_('Value must be a list or tuple of base JSON types'))
        if self.base_type in (str, int, float, bool):
            pass
        try:
            json.dumps(value)
        except TypeError:
            raise InvalidValueException(_('Value must be a list of base JSON types'))


class DictField(Field):
    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None, on_change=None):
        if default is None:
            default = {}
        super().__init__(verbose_name=verbose_name, help_text=help_text, disabled=disabled, validators=validators,
                         default=default, on_change=on_change)

    def serialize(self, value: dict) -> dict:
        return value

    def deserialize(self, value: dict) -> dict:
        return value

    def check_base_type(self, value):
        if not isinstance(value, dict):
            raise InvalidValueException(_('Value must be a dict of standard JSON types'))
        try:
            json.dumps(value)
        except TypeError:
            raise InvalidValueException(_('Value must be a dict of standard JSON types'))


class ChoiceField(Field):
    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None,
                 choices=None, on_change=None):
        super().__init__(verbose_name=verbose_name, help_text=help_text, disabled=disabled, validators=validators,
                         default=default, on_change=on_change)
        if choices is None:
            raise InvalidValueException(_('You must provide a list of tuples for ‘choices’ argument.'))
        self.choices = choices

    def serialize(self, value: object) -> object:
        return value

    def deserialize(self, value: list) -> list:
        return value

    def get_widget(self, field_group, parent=None):
        widget = QtGui.QComboBox(p(parent))
        for value, text_value in self.choices:
            widget.addItem(text_value, value)
        widget.setDisabled(self.disabled)
        return widget

    def get_widget_value(self, widget: QtGui.QComboBox):
        return widget.itemData(widget.currentIndex(), QtCore.Qt.UserRole)

    def set_widget_value(self, widget: QtGui.QComboBox, value):
        for index, item in enumerate(self.choices):
            if item[0] == value:
                widget.setCurrentIndex(index)

    def set_widget_valid(self, widget, valid: bool, msg: str):
        widget.setPalette(palette_valid if valid else palette_invalid)

    def check_base_type(self, value):
        try:
            json.dumps(value)
        except TypeError:
            raise InvalidValueException(_('Value must be a list of base JSON types'))


class FieldGroup(object):

    def __init__(self, initial=None, index=None):
        """
        :param initial: initial values, as a dictionnary {field_name: field_value}
        :param index: index of this FieldGroup if there are several FieldGroup
        """
        if initial is None:
            initial = {}
        self._fields = {}
        self._values = {}
        fields = []
        for cls in self.__class__.__mro__:
            for field_name, field in cls.__dict__.items():
                if not isinstance(field, Field) or field_name in self._fields:
                    continue
                self._fields[field_name] = field
                field.name = field_name
                value = initial.get(field_name, field.default)
                self._values[field_name] = value
                fields.append((field.group_field_order, field_name))
        fields.sort()
        self._field_order = [f[1] for f in fields]
        self.index = index

    def __getattribute__(self, item: str):
        if not item.startswith('_') and item in self._fields:
            return self._values[item]
        return super().__getattribute__(item)

    def __setattr__(self, item: str, value):
        if not item.startswith('_') and item in self._fields:
            self._fields[item].is_valid(value)
            self._values[item] = value
            return
        super().__setattr__(item, value)


if __name__ == '__main__':
    import doctest

    doctest.testmod()