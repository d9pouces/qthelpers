# coding=utf-8
import functools
from PySide import QtCore, QtGui
import itertools
from qthelpers.exceptions import InvalidValueException
from qthelpers.fields import FieldGroup, IndexedButtonField, Field
from qthelpers.shortcuts import create_button, get_icon, h_layout, v_layout
from qthelpers.translation import ugettext as _
from qthelpers.utils import p

__author__ = 'flanker'


class FormName(object):
    counter = itertools.count()

    def __init__(self, verbose_name=None):
        # noinspection PyProtectedMember
        self.index = next(Field._field_counter)
        self.verbose_name = verbose_name

    def __str__(self):
        return self.verbose_name


class BaseForm(FieldGroup):
    def __init__(self, initial=None):
        FieldGroup.__init__(self, initial=initial)
        self._multiforms = {}
        self._widgets = {}
        # retrieve all MultiForm classes from class definitions
        for cls in self.__class__.__mro__:
            for name, subcls in cls.__dict__.items():
                if not isinstance(subcls, type) or (not issubclass(subcls, MultiForm)
                                                    and not issubclass(subcls, SubForm)) or name in self._multiforms:
                    continue
                self._multiforms[name] = subcls(initial=initial, parent=self)

    def _fill_grid_layout(self, layout: QtGui.QGridLayout):
        """ Fill a QGridLayout with all MultiForms and Field, in the right order
        :param layout:
        :return:
        """
        all_components = []
        for multiform in self._multiforms.values():
            all_components.append(multiform)
        for field in self._fields.values():
            all_components.append(field)
        all_components.sort(key=self._sort_components)
        row_offset = layout.rowCount()
        for row_index, obj in enumerate(all_components):
            if isinstance(obj, MultiForm):  # a MultiForm already is a QWidget
                layout.addWidget(obj, row_offset + row_index, 0, 1, 2)
            elif isinstance(obj, SubForm):
                widget = QtGui.QGroupBox(str(obj.verbose_name), p(self))
                sub_layout = QtGui.QGridLayout(p(widget))
                obj._fill_grid_layout(sub_layout)
                widget.setLayout(sub_layout)
                layout.addWidget(widget, row_offset + row_index, 0, 1, 2)
            else:
                widget = obj.get_widget(self, self)
                self._widgets[obj.name] = widget
                obj.set_widget_value(widget, self._values[obj.name])
                if obj.label:
                    layout.addWidget(QtGui.QLabel(obj.label, p(self)), row_offset + row_index, 0)
                layout.addWidget(widget, row_offset + row_index, 1)

    def _fill_form_layout(self, layout: QtGui.QFormLayout):
        """ Fill a QGridLayout with all MultiForms and Field, in the right order
        :param layout:
        :return:
        """
        all_components = []
        for multiform in self._multiforms.values():
            all_components.append(multiform)
        for field in self._fields.values():
            all_components.append(field)
        all_components.sort(key=self._sort_components)
        for row_index, obj in enumerate(all_components):
            if isinstance(obj, MultiForm):  # a MultiForm already is a QWidget
                layout.addRow(obj)
            elif isinstance(obj, SubForm):
                widget = QtGui.QGroupBox(str(obj.verbose_name), p(self))
                sub_layout = QtGui.QFormLayout(p(widget))
                obj._fill_form_layout(sub_layout)
                widget.setLayout(sub_layout)
                layout.addRow(widget)
            else:
                widget = obj.get_widget(self, self)
                self._widgets[obj.name] = widget
                obj.set_widget_value(widget, self._values[obj.name])
                layout.addRow(obj.label or '', widget)

    def is_valid(self):
        valid = True
        self._values = {}
        for field_name, field in self._fields.items():
            widget = self._widgets[field_name]
            try:
                setattr(self, field_name, field.get_widget_value(widget))
                field.set_widget_valid(widget, True, '')
                self._values[field_name] = field.get_widget_value(widget)
            except InvalidValueException as e:
                field.set_widget_valid(widget, False, str(e))
                valid = False
        for multiform in self._multiforms.values():
            if multiform.is_valid():
                self._values.update(multiform.get_values())
            else:
                valid = False
        return valid

    def get_widget(self, field_name):  # TODO rechercher dans les multiforms
        return self._widgets[field_name]

    def get_widgets(self):
        return self._widgets

    def get_multiform(self, multiform_name):
        return self._multiforms[multiform_name]

    def get_values(self):
        return self._values

    @staticmethod
    def _sort_components(obj) -> int:
        if isinstance(obj, MultiForm) or isinstance(obj, SubForm):
            return getattr(obj.verbose_name, 'index', 0)
        return obj.group_field_order


class Form(BaseForm, QtGui.QWidget):
    def __init__(self, initial=None, parent=None):
        BaseForm.__init__(self, initial=initial)
        QtGui.QWidget.__init__(self, p(parent))
        layout = QtGui.QGridLayout(p(parent))
        self._fill_grid_layout(layout)
        self.setLayout(layout)


class SubForm(Form):
    verbose_name = None  # TabName(_('My Tab Name'))
    enabled = True


# class MyDialog(GenericForm):
# field_1 = CharField()
#     class tabs(MultiForm):
#         class tab_1(SubForm):
#             verbose_name = FormName('First Tab')
#             field_str_1 = CharField()


class MultiForm(object):
    verbose_name = None  # FormName('')
    group_subforms = True

    def __init__(self, initial=None):
        """
        :param initial: Dictionnary of initial values
        :return:
        """
        self._subforms_by_name = {}
        self._subforms_list = []
        self._values = {}
        for cls in self.__class__.__mro__:
            for subform_name, subform_class in cls.__dict__.items():
                if isinstance(subform_class, type) and issubclass(subform_class, SubForm) \
                        and subform_name not in self._subforms_by_name:
                    subform = subform_class(initial=initial)
                    """:type: SubForm"""
                    self._subforms_by_name[subform_name] = subform
                    self._subforms_list.append((subform_name, subform))
        self._subforms_list.sort(key=lambda x: getattr(x[1].verbose_name, 'index', 0))
        for subform_index, (subform_name, subform) in enumerate(self._subforms_list):
            self.add_form(subform_index, subform_name, subform)
            self.set_form_enabled(subform_index, subform, bool(subform.enabled))

    def __getattribute__(self, item: str):
        if not item.startswith('_') and item in self._subforms_by_name:
            return self._subforms_by_name[item]
        return super().__getattribute__(item)

    def set_current(self, index: int, name: str, subform: SubForm):
        raise NotImplementedError

    def add_form(self, index: int, name: str, subform: SubForm):
        raise NotImplementedError

    def set_form_enabled(self, index, name, enabled):
        raise NotImplementedError

    def is_valid(self):
        valid = True
        self._values = {}
        for subform_index, subform_data in enumerate(self._subforms_list):
            subform_name, subform = subform_data
            """:type: (int, FormTab)"""
            if subform.is_valid():
                self._values.update(subform.get_values())
            elif valid:
                self.set_current(subform_index, str(subform.verbose_name), subform)
                valid = False
            else:
                valid = False
        return valid

    def get_values(self):
        return self._values


class FormDialog(BaseForm, QtGui.QDialog):
    verbose_name = None
    description = None
    text_confirm = _('Yes')
    text_cancel = _('Cancel')

    def __init__(self, initial=None, parent=None):
        QtGui.QDialog.__init__(self, p(parent))
        BaseForm.__init__(self, initial=initial)
        # widget creation
        widgets = []
        if self.description:
            widgets.append(QtGui.QLabel(self.description, p(self)))
        sub_layout = QtGui.QFormLayout(self)
        self._fill_form_layout(layout=sub_layout)
        widgets.append(sub_layout)
        self._buttons = []
        if self.text_confirm:
            self._buttons.append(create_button(self.text_confirm, connect=self.accept, min_size=True))
        if self.text_cancel:
            self._buttons.append(create_button(self.text_cancel, connect=self.reject, min_size=True))
        if self._buttons:
            widgets.append(h_layout(self, *self._buttons, direction=QtGui.QBoxLayout.RightToLeft))
        self.setLayout(v_layout(self, *widgets))
        if self.verbose_name:
            self.setWindowTitle(str(self.verbose_name))
        self.raise_()

    @classmethod
    def process(cls, initial=None, parent=None):
        dialog = cls(initial=initial, parent=parent)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            return dialog.get_values()
        return None

    def accept(self):
        if not self.is_valid():
            return
        return QtGui.QDialog.accept(self)


class TabbedMultiForm(MultiForm, QtGui.QTabWidget):
    def __init__(self, initial=None, parent=None):
        QtGui.QTabWidget.__init__(self, p(parent))
        MultiForm.__init__(self, initial=initial)

    def set_current(self, index: int, name: str, subform: SubForm):
        self.setCurrentIndex(index)

    def add_form(self, index: int, name: str, subform: SubForm):
        self.addTab(subform, str(subform.verbose_name))

    def set_form_enabled(self, index, name, enabled):
        self.setTabEnabled(index, enabled)


class StackedMultiForm(MultiForm, QtGui.QGroupBox):
    def __init__(self, initial=None, parent=None):
        QtGui.QGroupBox.__init__(self, p(parent))
        self._stacked_names = QtGui.QComboBox(p(self))
        # noinspection PyUnresolvedReferences
        self._stacked_names.currentIndexChanged.connect(self._change_widget)
        self._stacked_widget = QtGui.QStackedWidget(p(self))
        MultiForm.__init__(self, initial=initial)
        self.setTitle(str(self.verbose_name))
        self.setLayout(v_layout(self, self._stacked_names, self._stacked_widget))

    def set_current(self, index: int, name: str, subform: SubForm):
        self._stacked_widget.setCurrentIndex(index)
        self._stacked_names.setCurrentIndex(index)

    def add_form(self, index: int, name: str, subform: SubForm):
        self._stacked_widget.addWidget(subform)
        self._stacked_names.addItem(str(subform.verbose_name))

    def _change_widget(self, index):
        self._stacked_widget.setCurrentIndex(index)

    def set_form_enabled(self, index, name, enabled):
        pass


class ToolboxMultiForm(MultiForm, QtGui.QToolBox):
    def __init__(self, initial=None, parent=None):
        QtGui.QToolBox.__init__(self, p(parent))
        MultiForm.__init__(self, initial=initial)

    def set_current(self, index: int, name: str, subform: SubForm):
        self.setCurrentIndex(index)

    def add_form(self, index: int, name: str, subform: SubForm):
        self.addItem(subform, str(subform.verbose_name))

    def set_form_enabled(self, index, name, enabled):
        self.setItemEnabled(index, enabled)


class InlineForm(QtGui.QWidget):
    __editable__ = True

    def __init__(self, list_of_values, title=''):
        super(InlineForm, self).__init__()
        self.__list_of_values = list_of_values
        self.__attributes = [IndexedButtonField(verbose_name=_('Add element'), icon='edit_add',
                                                connect=self.__add_item),
                             IndexedButtonField(verbose_name=_('Remove element'), icon='edit_remove',
                                                connect=self.__remove_item)]
        layout = QtGui.QGridLayout()
        if title:
            layout.addWidget(QtGui.QLabel(title), 0, 0)
        if self.__editable__:
            add_button = create_button('', get_icon('edit_add', theme='crystal'), min_size=True,
                                       connect=functools.partial(self.__add_item, index=None))
            layout.addWidget(add_button, 0, 2)
        self.__main_widget = QtGui.QTreeWidget()
        if self.__editable__:
            headers = [_('Insert'), _('Remove')]
            self.__keys = ['', '']
        else:
            self.__keys = []
            headers = []
        if self.__order__ is not None:
            field_names = self.__order__
        # else:
        #     field_names = [field_name for field_name, field in self.__class__.__dict__.items()
        #                    if isinstance(field, FormField)]
        for field_name in field_names:
            field = self.__class__.__dict__[field_name]
            self.__keys.append(field_name)
            #noinspection PyTypeChecker
            self.__attributes.append(field)
            headers.append(field.verbose_name)
        self.__main_widget.setHeaderLabels(headers)
        for item_index, item_data in enumerate(list_of_values):
            tree_widget_item = QtGui.QTreeWidgetItem([''] * len(self.__keys), QtGui.QTreeWidgetItem.Type)
            tree_widget_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.__main_widget.addTopLevelItem(tree_widget_item)
            for col_index, field_name in enumerate(self.__keys):
                attribute = self.__attributes[col_index]
                widget = attribute.get_widget(value=item_data.get(field_name, attribute.default), index=item_index)
                self.__main_widget.setItemWidget(tree_widget_item, col_index, widget)
        for column_index in range(len(self.__keys)):
            self.__main_widget.resizeColumnToContents(column_index)
        layout.addWidget(self.__main_widget, 1, 0, 1, 3)
        self.setLayout(layout)

    def is_valid(self):
        valid = True
        for tree_item_index in range(self.__main_widget.topLevelItemCount()):
            tree_item = self.__main_widget.topLevelItem(tree_item_index)
            for col_index, field_name in enumerate(self.__keys):
                attribute = self.__attributes[col_index]
                widget = self.__main_widget.itemWidget(tree_item, col_index)
                valid = attribute.is_valid(widget) and valid
        return valid

    def get_values(self):
        row_values = []
        for tree_item_index in range(self.__main_widget.topLevelItemCount()):
            tree_item = self.__main_widget.topLevelItem(tree_item_index)
            row = {}
            for col_index, field_name in enumerate(self.__keys):
                attribute = self.__attributes[col_index]
                widget = self.__main_widget.itemWidget(tree_item, col_index)
                if field_name:
                    row[field_name] = attribute.get_widget_value(widget)
            row_values.append(row)
        return row_values

    def __remove_item(self, index):
        u"""supprime le champ de l'index spécifié, quitte à décaler vers le haut tout ce qu'il y a après
        ne fait rien s'il n'y a qu'une ligne dans la liste
        exemple : 4 lignes de champs, on clique sur la 2ème ligne (index=1, maxIndex=4) :
        on décale 2 vers 1 (3ème ligne vers 2ème), 3 vers 1 (4ème vers 3ème), on supprime 3 (4ème ligne) """
        max_index = self.__main_widget.topLevelItemCount()
        if max_index <= 0:
            return
        for i in range(index, max_index - 1):
            dst_widget_item = self.__main_widget.topLevelItem(i)
            src_widget_item = self.__main_widget.topLevelItem(i + 1)
            for col_index, field_name in enumerate(self.__keys):
                if col_index <= 1:
                    continue
                dst_widget = self.__main_widget.itemWidget(dst_widget_item, col_index)
                src_widget = self.__main_widget.itemWidget(src_widget_item, col_index)
                field = self.__attributes[col_index]
                field.set_widget_value(dst_widget, field.get_widget_value(src_widget))
        self.__main_widget.takeTopLevelItem(max_index - 1)

    def __add_item(self, index=None):
        tree_widget_item = QtGui.QTreeWidgetItem([''] * len(self.__keys), QtGui.QTreeWidgetItem.Type)
        tree_widget_item.setFlags(QtCore.Qt.ItemIsEnabled)
        max_index = self.__main_widget.topLevelItemCount()
        self.__main_widget.addTopLevelItem(tree_widget_item)
        item_data = {}
        # on met des valeurs par défaut dans celui qu'on vient d'ajouter
        for col_index, field_name in enumerate(self.__keys):
            field = self.__attributes[col_index]
            widget = field.get_widget(value=item_data.get(field_name, field.default), index=max_index)
            self.__main_widget.setItemWidget(tree_widget_item, col_index, widget)
        # schéma explicatif. max_index = 3
        # Ligne0
        # Ligne1
        # Ligne2
        # Ligne3 [nouvelle ligne]

        # index = None => on ajoute à la fin
        # index = 0: on insère avant Ligne0 ; on décale 2 dans 3, on décale 1 dans 2, on décale 0 dans 1

        if index is not None and max_index >= index >= 0:  # il est tout en bas, il faut décaler le contenu
            for col_index, field_name in enumerate(self.__keys):
                field = self.__attributes[col_index]
                if col_index <= 1:
                    continue
                current_dst_index = max_index
                dst_widget = self.__main_widget.itemWidget(self.__main_widget.topLevelItem(current_dst_index),
                                                           col_index)
                src_widget = self.__main_widget.itemWidget(self.__main_widget.topLevelItem(current_dst_index - 1),
                                                           col_index)
                while current_dst_index > index:
                    field.set_widget_value(dst_widget, field.get_widget_value(src_widget))
                    dst_widget = src_widget
                    current_dst_index -= 1
                    src_widget = self.__main_widget.itemWidget(self.__main_widget.topLevelItem(current_dst_index - 1),
                                                               col_index)
                field.set_widget_value(dst_widget, item_data.get(field_name, field.default))
        if max_index == 0:
            for column_index in range(len(self.__keys)):
                self.__main_widget.resizeColumnToContents(column_index)


if __name__ == '__main__':
    import doctest

    doctest.testmod()