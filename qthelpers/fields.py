# coding=utf-8
from PySide import QtGui
import itertools
from qthelpers.exceptions import InvalidValueException
from qthelpers.translation import ugettext as _

__author__ = 'flanker'

palette_valid = QtGui.QPalette()
palette_valid.setColor(QtGui.QPalette.Base, QtGui.QColor(147, 234, 154))
palette_invalid = QtGui.QPalette()
palette_invalid.setColor(QtGui.QPalette.Base, QtGui.QColor(207, 0, 0))


class Field(object):
    _field_counter = itertools.count()

    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None):
        self.verbose_name = verbose_name
        self.help_text = help_text
        self.default = default
        if validators is None:
            validators = []
        validators.insert(0, self.check_base_type)
        self.validators = validators
        self.disabled = disabled
        self.group_field_order = next(Field._field_counter)

    def is_valid(self, value) -> bool:
        if self.validators is not None:
            for validator in self.validators:
                validator(value)
        return True

    @staticmethod
    def check_base_type(value) -> None:
        raise NotImplementedError

    def serialize(self, value) -> str:
        raise NotImplementedError

    def deserialize(self, value: str):
        raise NotImplementedError

    def get_widget(self, field_group):
        raise NotImplementedError

    def get_widget_value(self, widget):
        raise NotImplementedError

    def set_widget_value(self, widget, value):
        raise NotImplementedError

    def set_widget_valid(self, widget, valid: bool, msg: str):
        raise NotImplementedError


class CharField(Field):
    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None,
                 widget_validator=None, max_length=None, min_length=None):
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
        super().__init__(verbose_name, help_text, default, disabled, validators)
        self.widget_validator = widget_validator

    @staticmethod
    def check_base_type(value):
        if isinstance(value, str):
            return
        raise InvalidValueException(_('value must be a string'))

    def serialize(self, value) -> str:
        return value

    def deserialize(self, value: str):
        return value

    def get_widget(self, field_group):
        editor = QtGui.QLineEdit()
        if self.help_text is not None:
            editor.setToolTip(self.help_text)
        if self.widget_validator is not None:
            editor.setValidator(self.widget_validator)
        return editor

    def get_widget_value(self, widget):
        return widget.text()

    def set_widget_value(self, widget, value: str):
        widget.setText(value)

    def set_widget_valid(self, widget, valid: bool, msg: str):
        widget.setPalette(palette_valid if valid else palette_invalid)


class IntegerField(Field):
    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None,
                 widget_validator=None, min_value=None, max_value=None, required=True):
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
        super().__init__(verbose_name, help_text, default, disabled, validators)
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

    def get_widget(self, field_group):
        editor = QtGui.QLineEdit()
        if self.help_text is not None:
            editor.setToolTip(self.help_text)
        editor.setValidator(self.widget_validator)
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

    @staticmethod
    def check_base_type(value):
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

    @staticmethod
    def check_base_type(value):
        if value is None or isinstance(value, float):
            return
        raise InvalidValueException(_('value must be a float'))

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

    def get_widget(self, field_group):
        editor = QtGui.QCheckBox()
        if self.help_text:
            editor.setToolTip(self.help_text)
        return editor

    def get_widget_value(self, widget):
        return widget.isChecked()

    def set_widget_value(self, widget, value: bool):
        widget.setChecked(value)

    def set_widget_valid(self, widget, valid: bool, msg: str):
        pass

    @staticmethod
    def check_base_type(value):
        if not isinstance(value, bool):
            raise InvalidValueException(_('Value must be a boolean'))


class FilepathField(CharField):
    pass


class CharChoiceField(Field):
    def __init__(self, verbose_name='', help_text=None, default=None, disabled=False, validators=None):
        if default is None:
            default = []
        super().__init__(verbose_name=verbose_name, help_text=help_text, disabled=disabled, validators=validators,
                         default=default)

    def serialize(self, value: list) -> list:
        return [(str(x), str(y)) for (x, y) in value]

    def deserialize(self, value: list) -> list:
        return value

    def get_widget(self, field_group):
        pass

    def get_widget_value(self, widget):
        pass

    def set_widget_value(self, widget, value):
        pass

    def set_widget_valid(self, widget, valid: bool, msg: str):
        pass

    @staticmethod
    def check_base_type(value):
        if not isinstance(value, list) and not isinstance(value, tuple):
            raise InvalidValueException(_('Value must be a list or tuple of (str, str)'))
        for x, y in value:
            if not isinstance(x, str) or not isinstance(y, str):
                raise InvalidValueException(_('Values must be a list or tuple of (str, str)'))


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
        for field_name, field in self.__class__.__dict__.items():
            if not isinstance(field, Field):
                continue
            self._fields[field_name] = field
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