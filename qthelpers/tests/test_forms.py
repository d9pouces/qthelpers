# coding=utf-8
import random
import unittest

from PySide import QtTest, QtCore

from qthelpers.fields import CharField, IntegerField, FloatField, BooleanField
from qthelpers.forms import Form, SimpleFormDialog
from qthelpers.menus import menu_item, MenuAction
from qthelpers.application import BaseApplication
from qthelpers.toolbars import toolbar_item
from qthelpers.windows import BaseMainWindow


__author__ = 'flanker'


class SampleApplication(BaseApplication):
    application_name = 'Sample Application'
    application_version = '0.1'
    application_icon = 'qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png'


class SampleForm(Form):
    str_value = CharField(default='my_str', verbose_name='String value')
    int_value = IntegerField(default=42, required=True, verbose_name='Integer value')
    float_value = FloatField(default=10., required=True, verbose_name='Float value')
    float_value_none = FloatField(default=10., required=False, verbose_name='Float value or None')
    bool_value = BooleanField(default=True, verbose_name='Boolean value')


class SampleFormDialog(SimpleFormDialog):
    verbose_name = 'My sample dialog'
    description = 'A short description'
    str_value = CharField(default='my_str', verbose_name='String value')
    int_value = IntegerField(default=42, required=True, verbose_name='Integer value')
    float_value = FloatField(default=10., required=True, verbose_name='Float value')
    float_value_none = FloatField(default=10., required=False, verbose_name='Float value or None')
    bool_value = BooleanField(default=True, verbose_name='Boolean value')


class SampleBaseWindows(BaseMainWindow):
    window_icon = 'qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png'

    @menu_item(menu='TestMenu', verbose_name='TestMenuItem')
    @toolbar_item(icon='qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png')
    def test_menu_1(self):
        print('test_menu_1')

    @menu_item(menu='TestMenu', verbose_name='TestSubmenu', submenu=True, sep=True)
    def test_menu_2(self):
        return [
            MenuAction(self.test_1, verbose_name='Submenu %d' % random.randint(1, 65536), menu=''),
            MenuAction(self.test_2, verbose_name='Submenu %d' % random.randint(1, 65536), menu=''),
        ]

    @staticmethod
    def test_1():
        print('111')

    @staticmethod
    def test_2():
        print('222')

    def central_widget(self):
        return SampleForm()


class FormTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = SampleApplication([])

    def test_forms(self):
        pass
        form = SampleForm()
        form.show()
        form.close()

        dialog = SampleFormDialog(initial={'int_value': 32})
        dialog.show()
        QtTest.QTest.mouseClick(dialog._buttons[0], QtCore.Qt.LeftButton)
        self.assertEqual(dialog._values, {'float_value': 10.0, 'bool_value': True, 'float_value_none': 10.0,
                                          'int_value': 32, 'str_value': 'my_str'})

        dialog = SampleFormDialog(initial={'int_value': 32})
        dialog.show()
        QtTest.QTest.mouseClick(dialog._buttons[1], QtCore.Qt.LeftButton)
        self.assertEqual(dialog._values, {'float_value': 10.0, 'bool_value': True, 'float_value_none': 10.0,
                                          'int_value': 32, 'str_value': 'my_str'})
        window = SampleBaseWindows()
        # print(application())
        # print('window_1')
        window.show()
        # window.close()
        self.application.exec_()
        self.application.quit()


if __name__ == '__main__':
    import doctest

    doctest.testmod()