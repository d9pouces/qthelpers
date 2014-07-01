# coding=utf-8
from PySide import QtGui
import unittest
from qthelpers.fields import CharField, IntegerField, FloatField, BooleanField
from qthelpers.forms import Form, SimpleDialog
from qthelpers.qtapps import BaseApplication

__author__ = 'flanker'


application = BaseApplication([])


class SampleForm(Form):
    str_value = CharField(default='my_str', verbose_name='String value')
    int_value = IntegerField(default=42, required=True, verbose_name='Integer value')
    float_value = FloatField(default=10., required=True, verbose_name='Float value')
    float_value_none = FloatField(default=10., required=False, verbose_name='Float value or None')
    bool_value = BooleanField(default=True, verbose_name='Boolean value')


class SampleDialog(SimpleDialog):
    verbose_name = 'My sample dialog'
    description = 'A short description'
    str_value = CharField(default='my_str', verbose_name='String value')
    int_value = IntegerField(default=42, required=True, verbose_name='Integer value')
    float_value = FloatField(default=10., required=True, verbose_name='Float value')
    float_value_none = FloatField(default=10., required=False, verbose_name='Float value or None')
    bool_value = BooleanField(default=True, verbose_name='Boolean value')


class FormTest(unittest.TestCase):
    def test_1(self):
        form = SampleForm()
        form.show()

        SampleDialog.get_values(initial={'int_value': 32})

        button = QtGui.QPushButton('Exit')
        # noinspection PyUnresolvedReferences
        button.clicked.connect(application.exit)
        button.show()
        application.exec_()

if __name__ == '__main__':
    import doctest

    doctest.testmod()