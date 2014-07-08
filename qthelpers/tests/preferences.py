# coding=utf-8
import unittest
from qthelpers.exceptions import InvalidValueException
from qthelpers.fields import CharField, IntegerField, FloatField, BooleanField
from qthelpers.preferences import Preferences, Section

__author__ = 'flanker'


class SamplePreferences(Preferences):
    organization_name = 'my_organization'
    verbose_name = 'my_application'

    class Section1(Section):
        str_value = CharField(default='my_str')
        int_value = IntegerField(default=42, required=True)
        float_value = FloatField(default=10., required=True)
        float_value_none = FloatField(default=10., required=False)
        bool_value = BooleanField(default=True)


class PreferencesTest(unittest.TestCase):

    def test_generic(self):
        pref = SamplePreferences()
        self.assertEqual(list(pref._sections.keys()), ['Section1'])
        self.assertEqual(pref.Section1._field_order, ['str_value', 'int_value', 'float_value', 'float_value_none',
                                                      'bool_value'])

    def test_bool(self):
        pref = SamplePreferences()

        def set_bool_none():
            pref.Section1.bool_value = None

        self.assertEqual(pref.Section1.bool_value, True)
        pref.Section1.bool_value = False
        self.assertEqual(pref.Section1.bool_value, False)
        self.assertRaises(InvalidValueException, set_bool_none)

    def test_str(self):
        pref = SamplePreferences()

        def set_str_none():
            pref.Section1.str_value = None

        self.assertEqual(pref.Section1.str_value, 'my_str')
        self.assertRaises(InvalidValueException, set_str_none)

    def test_int(self):
        pref = SamplePreferences()

        def set_int_none():
            pref.Section1.int_value = None

        self.assertEqual(pref.Section1.int_value, 42)
        pref.Section1.int_value = 10
        self.assertEqual(pref.Section1.int_value, 10)
        self.assertRaises(InvalidValueException, set_int_none)

    def test_float(self):
        pref = SamplePreferences()

        def set_float_none():
            pref.Section1.float_value = None

        self.assertEqual(pref.Section1.float_value, 10.)
        pref.Section1.float_value = 42.
        self.assertEqual(pref.Section1.float_value, 42.)
        self.assertRaises(InvalidValueException, set_float_none)

        self.assertEqual(pref.Section1.float_value_none, 10.)
        pref.Section1.float_value_none = None
        self.assertIsNone(pref.Section1.float_value_none)

    def test_load(self):
        pref = SamplePreferences()
        pref.load()
        pref.save()
