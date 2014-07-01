# coding=utf-8
from PySide import QtCore
from qthelpers.exceptions import InvalidValueException
from qthelpers.fields import FieldGroup

__author__ = 'flanker'


class Section(FieldGroup):
    pass


class Preferences(object):
    organization = '19pouces.net'
    application = 'qthelpers'
    converters = {}

    def __init__(self):
        self._sections = {}
        for section_name, section_class in self.__class__.__dict__.items():
            if isinstance(section_class, type) and issubclass(section_class, Section):
                self._sections[section_name] = section_class()

    def __getitem__(self, item: str):
        section, key = item.split('/', 1)
        return getattr(self._sections[section], key)

    def __setitem__(self, item: str, value):
        section, key = item.split('/', 1)
        return setattr(self._sections[section], key, value)

    def __getattribute__(self, item: str):
        if not item.startswith('_') and item in self._sections:
            return self._sections[item]
        return super().__getattribute__(item)

    def save(self):
        settings = QtCore.QSettings(self.organization, self.application)
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
        settings = QtCore.QSettings(self.organization, self.application)
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
        settings = QtCore.QSettings(self.organization, self.application)
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