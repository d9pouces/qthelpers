# coding=utf-8
from PySide import QtCore
from qthelpers.exceptions import InvalidValueException
from qthelpers.fields import FieldGroup

__author__ = 'flanker'


class Section(FieldGroup):
    pass


class GlobalObject(object):
    def __init__(self, key):
        self.__key = key

    def __getattr__(self, item):
        if not item.startswith('_'):
            return getattr(global_dict[self.__key], item)

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            return setattr(global_dict[self.__key], key, value)
        super().__setattr__(key, value)

    def __getitem__(self, item: str):
        section, key = item.split('/', 1)
        # noinspection PyProtectedMember
        return getattr(global_dict[self.__key]._sections[section], key)

    def __setitem__(self, item: str, value):
        section, key = item.split('/', 1)
        # noinspection PyProtectedMember
        return setattr(global_dict[self.__key]._sections[section], key, value)


global_dict = {}
preferences_key = 'preferences'
preferences = GlobalObject(preferences_key)


class Preferences(object):
    organization_name = None
    application_name = None
    selected_theme_key = None   # %(THEME)s will be replaced by the value of preferences.selected_theme_key

    def __init__(self):
        self._sections = {}
        for section_name, section_class in self.__class__.__dict__.items():
            if isinstance(section_class, type) and issubclass(section_class, Section):
                self._sections[section_name] = section_class()
        global_dict[preferences_key] = self

    def __getitem__(self, item: str):
        section, key = item.split('/', 1)
        return getattr(self._sections[section], key)

    def __setitem__(self, item: str, value):
        section, key = item.split('/', 1)
        return setattr(self._sections[section], key, value)

    def __getattr__(self, item: str):
        if not item.startswith('_') and item in self._sections:
            return self._sections[item]

    def save(self):
        settings = QtCore.QSettings(self.organization_name, self.application_name)
        for section_name, section in self._sections.items():
            settings.beginGroup(section_name)
            # noinspection PyProtectedMember
            for key in section._field_order:
                # noinspection PyProtectedMember
                serialized = section._fields[key].serialize(section._values[key])
                settings.setValue(key, serialized)
            settings.endGroup()
        settings.sync()

    def reset(self):
        settings = QtCore.QSettings(self.organization_name, self.application_name)
        for section_name, section in self._sections.items():
            settings.beginGroup(section_name)
            # noinspection PyProtectedMember
            for key in section._field_order:
                # noinspection PyProtectedMember
                serialized = section._fields[key].serialize(section._fields[key].default)
                settings.setValue(key, serialized)
            settings.endGroup()
        settings.sync()

    def load(self):
        settings = QtCore.QSettings(self.organization_name, self.application_name)
        for section_name, section in self._sections.items():
            settings.beginGroup(section_name)
            # noinspection PyProtectedMember
            for key in section._field_order:
                if settings.contains(key):
                    serialized = settings.value(key)
                    # noinspection PyProtectedMember
                    deserialized = section._fields[key].deserialize(serialized)
                    try:
                        setattr(section, key, deserialized)
                    except InvalidValueException:  # TODO log the error
                        pass
            settings.endGroup()

if __name__ == '__main__':
    import doctest

    doctest.testmod()