import argparse
import random
import sys
from qthelpers.application import application, BaseApplication
from qthelpers.fields import BooleanField, FloatField, IntegerField, CharField
from qthelpers.forms import SimpleFormDialog, Form
from qthelpers.menus import MenuAction, menu_item
from qthelpers.toolbars import toolbar_item
from qthelpers.windows import BaseMainWindow


__author__ = 'flanker'


class SampleApplication(BaseApplication):
    application_name = 'Sample Application'
    application_version = '0.1'
    application_icon = 'qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png'
    systemtray_icon = 'qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png'

    @menu_item
    def test_systray(self):
        print('test_systray')

    def systray_message_clicked(self):
        print('systray message clicked')

    def systray_activated(self, reason):
        print('systray activated', reason)


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
        application.systray.showMessage('Systray message title', 'Systray message')

    def central_widget(self):
        return SampleForm()


def main():
    argument_parser = argparse.ArgumentParser('qtexample', description='QtHelpers example')
    argument_parser.add_argument('--style', action='store', default=None,
                                 help='Possible values are motif, windows, and platinum.')
    argument_parser.add_argument('--stylesheet', action='store', default=None,
                                 help='sets the application styleSheet. ')
    argument_parser.add_argument('--widgetcount', action='store_true', default=False,
                                 help=('prints debug message at the end about number of widgets left undestroyed '
                                       'and maximum number of widgets existed at the same time.'))
    argument_parser.add_argument('--reverse', action='store_true', default=False,
                                 help='sets the application\'s layout direction to Qt::RightToLeft.')

    pargs = argument_parser.parse_args()
    args = []
    if pargs.style:
        args += ['-style', pargs.style]
    if pargs.stylesheet:
        args += ['-stylesheet', pargs.stylesheet]
    if pargs.widgetcount:
        args += ['-widgetcount']
    if pargs.reverse:
        args += ['-reverse']
    SampleApplication(args)

    window = SampleBaseWindows()
    window.show()
    application.exec_()
