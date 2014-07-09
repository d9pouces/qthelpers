import argparse
import random

from qthelpers.application import application, SingleDocumentApplication
from qthelpers.fields import BooleanField, FloatField, IntegerField, CharField, FilepathField, ChoiceField
from qthelpers.forms import FormDialog, Form, SubForm, FormName, TabbedMultiForm, StackedMultiForm, ToolboxMultiForm
from qthelpers.menus import MenuAction, menu_item
from qthelpers.toolbars import toolbar_item
from qthelpers.windows import BaseMainWindow, SingleDocumentWindow


__author__ = 'flanker'


class SampleApplication(SingleDocumentApplication):
    verbose_name = 'Sample Application'
    application_version = '0.1'
    description_icon = 'qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png'
    systemtray_icon = 'qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png'

    @menu_item(submenu=False)
    def test_systray(self):
        print('test_systray')

    def systray_message_clicked(self):
        print('systray message clicked')

    def systray_activated(self, reason):
        print('systray activated', reason)


class SampleForm(Form):
    str_value = CharField(default='my_str', verbose_name='String value')

    class Sub1(SubForm):
        verbose_name = FormName('simple box')
        int_value = IntegerField(default=42, required=True, verbose_name='Integer value')
        float_value = FloatField(default=10., required=True, verbose_name='Float value')
        float_value_none = FloatField(default=10., required=False, verbose_name='Float value or None')

    class SampleTabbedWidget(TabbedMultiForm):
        verbose_name = FormName('Tab subforms')

        class Sub1(SubForm):
            verbose_name = FormName('first tab')
            str_value1 = CharField(default='str_value_1', verbose_name='My first string value')

        class Sub2(SubForm):
            verbose_name = FormName('second tab')
            str_value2 = CharField(default='str_value_2', verbose_name='My second string value')

        class Sub3(SubForm):
            verbose_name = FormName('third tab')
            str_value3 = CharField(default='str_value_3', verbose_name='My third string value')

    bool_value = BooleanField(default=True, verbose_name='Boolean value')

    class SampleStackedWidget(StackedMultiForm):
        verbose_name = FormName('Stacked subforms')

        class Sub1(SubForm):
            verbose_name = FormName('first tab')
            str_value1 = CharField(default='str_value_1', verbose_name='My first string value')

        class Sub2(SubForm):
            verbose_name = FormName('second tab')
            str_value2 = CharField(default='str_value_2', verbose_name='My second string value')

        class Sub3(SubForm):
            verbose_name = FormName('third tab')
            str_value3 = CharField(default='str_value_3', verbose_name='My third string value')

    class SampleToolboxWidget(ToolboxMultiForm):
        verbose_name = FormName('Stacked subforms')

        class Sub2(SubForm):
            verbose_name = FormName('second tab')
            str_value2 = CharField(default='str_value_2', verbose_name='My second string value')

        class Sub3(SubForm):
            verbose_name = FormName('third tab')
            str_value3 = CharField(default='str_value_3', verbose_name='My third string value')

    filename = FilepathField(verbose_name='A file path')


class SampleFormDialog(FormDialog):
    verbose_name = 'My sample dialog'
    description = 'A short description'
    str_value = CharField(default='my_str', verbose_name='String value')
    int_value = IntegerField(default=42, required=True, verbose_name='Integer value')
    float_value = FloatField(default=10., required=True, verbose_name='Float value')
    float_value_none = FloatField(default=10., required=False, verbose_name='Float value or None')
    bool_value = BooleanField(default=True, verbose_name='Boolean value')
    filename = FilepathField(verbose_name='A file path', required=False)
    choices = ChoiceField(verbose_name='Some choices', choices=((1, 'example 1'), (2, 'example 2')))


class SampleBaseWindows(BaseMainWindow):
    description_icon = 'qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png'

    @menu_item(menu='TestMenu', verbose_name='TestMenuItem')
    @toolbar_item(icon='qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png')
    def test_menu_1(self):
        print('test_menu_1')

    @menu_item(menu='TestMenu', verbose_name='TestSubmenu', submenu=True, sep=True)
    def test_menu_2(self):
        return [
            MenuAction(self.test_1, verbose_name='Test form %d' % random.randint(1, 65536), menu=''),
            MenuAction(self.test_2, verbose_name='Test systray %d' % random.randint(1, 65536), menu=''),
        ]

    @toolbar_item(icon='qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png')
    def test_1(self):
        SampleFormDialog.process(parent=self)

    # noinspection PyMethodMayBeStatic
    @toolbar_item(icon='qthelpers:resources/icons/ToolbarDocumentsFolderIcon.png')
    def test_2(self):
        application.systray.showMessage('Systray message title', 'Systray message')

    def central_widget(self):
        return SampleForm()


class SampleDocumentWindow(SingleDocumentWindow):
    def is_valid_document(self, filename):
        """ Check if filename is a valid document
        :return:
        """
        return True

    def load_document(self):
        """ Load the document self.current_document_filename
        self.current_document_filename is set to None, self.current_document_is_modified is set to False
        :return:
        """
        return True

    def unload_document(self):
        """ Unload the current loaded document (if it exists)
        :return:
        """
        return True

    def create_document(self):
        """ Create a new blank document
        self.current_document_filename is set to None, self.current_document_is_modified is set to False
        :return:
        """
        pass

    def save_document(self):
        """ Save the current loaded document (if it exists) into self.current_document_filename
        It's your responsibility to update self.current_document_is_modified to True
        :return:
        """
        return True

    @menu_item(menu='TestMenu', verbose_name='Mark as modified')
    def test_menu_2(self):
        self.base_mark_document_as_modified()

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
    window2 = SampleDocumentWindow()
    window2.show()
    application.exec_()
