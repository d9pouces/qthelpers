# coding=utf-8
import json
import os
import re
import sys
import unicodedata

from qthelpers.exceptions import InvalidValueException
from qthelpers.fields import FieldGroup, Field

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


def slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^\w\.-]', '', value).strip()


class Preferences(object):
    organization_name = None
    verbose_name = None
    icon_theme_key = None   # %(theme)s will be replaced by the value of preferences.selected_theme_key
    icon_pattern = 'resources/%(theme)s/%(name)s.png'
    icon_search_modules = ['qtexample', 'qthelpers', ]
    icon_use_global_theme = True
    organization_domain = None

    def __init__(self):
        self._sections = {}
        fields_by_section = {}
        for cls in self.__class__.__mro__:
            for section_name, section_class in cls.__dict__.items():
                if not isinstance(section_class, type) or not issubclass(section_class, Section):
                    continue
                fields_by_section.setdefault(section_name, {})
                for field_name, field in section_class.__dict__.items():
                    if not isinstance(field, Field) or field_name in fields_by_section[section_name]:
                        continue
                    fields_by_section[section_name][field_name] = field
        for section_name, fields in fields_by_section.items():
            merged_cls = type(section_name, (Section, ), fields)
            self._sections[section_name] = merged_cls()
        global_dict[preferences_key] = self

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

    def application_settings_filenames(self):
        app_name = slugify(self.verbose_name)
        if sys.platform.startswith('darwin'):
            home = os.path.expanduser('~/Library/Preferences/%s.%s.plist' % (self.organization_name, app_name))
            allusers = '/Library/Preferences/%s.%s.plist' % (self.organization_name, app_name)
        elif sys.platform.startswith('win'):
            home = os.path.expandvars('%%APPDATA%%/%s/%s.plist' % (self.organization_name, app_name))
            allusers = os.path.expandvars('%%APPDATA%%/%s/%s.plist' % (self.organization_name, app_name))
        else:
            home = os.path.expanduser('~/.config/%s/%s.plist' % (self.organization_name, app_name))
            allusers = '/etc/%s/%s.plist' % (self.organization_name, app_name)
        return home, allusers

    def save(self):
        home, allusers = self.application_settings_filenames()
        dirname = os.path.dirname(home)
        if not os.path.isdir(dirname):  # TODO erreurs possibles
            os.makedirs(dirname)
        all_values = {}
        for section_name, section in self._sections.items():
            all_values[section_name] = {}
            # noinspection PyProtectedMember
            for key in section._field_order:
                # noinspection PyProtectedMember
                serialized = section._fields[key].serialize(section._values[key])
                all_values[section_name][key] = serialized
        with open(home, 'w') as fd:  # TODO erreurs possibles
            json.dump(all_values, fd, ensure_ascii=False, sort_keys=True)

    def reset(self):
        home, allusers = self.application_settings_filenames()
        dirname = os.path.dirname(home)
        if not os.path.isdir(dirname):  # TODO erreurs possibles
            os.makedirs(dirname)
        all_values = {}
        for section_name, section in self._sections.items():
            all_values[section_name] = {}
            # noinspection PyProtectedMember
            for key in section._field_order:
                # noinspection PyProtectedMember
                serialized = section._fields[key].serialize(section._fields[key].default)
                all_values[section_name][key] = serialized
        with open(home, 'w') as fd:  # TODO erreurs possibles
            json.dump(all_values, fd, ensure_ascii=False, sort_keys=True)

    def load(self):
        home, allusers = self.application_settings_filenames()
        for filename in home, allusers:
            if not os.path.isfile(filename):
                continue
            with open(filename, 'r') as fd:  # TODO erreurs possibles
                all_values = json.load(fd)
            for section_name, section in self._sections.items():
                if section_name not in all_values:
                    continue
                # noinspection PyProtectedMember
                for key in section._field_order:
                    if key not in all_values[section_name]:
                        continue
                    serialized = all_values[section_name][key]
                    # noinspection PyProtectedMember
                    deserialized = section._fields[key].deserialize(serialized)
                    try:
                        setattr(section, key, deserialized)
                    except InvalidValueException:  # TODO log the error
                        pass

if __name__ == '__main__':
    import doctest

    doctest.testmod()