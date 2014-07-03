# coding=utf-8
import functools
from PySide import QtCore, QtGui
from qthelpers.exceptions import InvalidValueException
from qthelpers.fields import FieldGroup
from qthelpers.shortcuts import v_layout, create_button, h_layout
from qthelpers.translation import ugettext as _

__author__ = 'flanker'


class Form(FieldGroup, QtGui.QWidget):

    def __init__(self, initial=None):
        FieldGroup.__init__(self, initial=initial, index=None)
        QtGui.QWidget.__init__(self)

        # widget creation
        self._widgets = {}
        layout = QtGui.QGridLayout()
        for row_index, field_name in enumerate(self._field_order):
            field = self._fields[field_name]
            widget = field.get_widget(self)
            self._widgets[field_name] = widget
            field.set_widget_value(widget, self._values[field_name])
            if field.verbose_name:
                layout.addWidget(QtGui.QLabel(field.verbose_name), row_index, 0)
            layout.addWidget(widget, row_index, 1)
        self.setLayout(layout)

    def get_widget(self, field_name):
        return self._widgets[field_name]

    def is_valid(self):
        valid = True
        for field_name, field in self._fields.items():
            widget = self._widgets[field_name]
            try:
                setattr(self, field_name, field.get_widget_value(widget))
                field.set_widget_valid(widget, True, '')
            except InvalidValueException as e:
                field.set_widget_valid(widget, False, str(e))
                valid = False
        return valid

    def get_values(self):
        return self._values


class TabbedForm(QtGui.QWidget):
    pass


class SimpleFormDialog(FieldGroup, QtGui.QDialog):
    verbose_name = None
    description = None
    text_confirm = _('Yes')
    text_cancel = _('Cancel')

    def __init__(self, initial=None):
        FieldGroup.__init__(self, initial=initial, index=None)
        QtGui.QDialog.__init__(self)

        # widget creation
        self._widgets = {}
        if self.verbose_name:
            self.setWindowTitle(self.verbose_name)

        widgets = []
        if self.description:
            widgets.append(QtGui.QLabel(self.description))

        sub_layout = QtGui.QGridLayout()
        for row_index, field_name in enumerate(self._field_order):
            field = self._fields[field_name]
            widget = field.get_widget(self)
            self._widgets[field_name] = widget
            field.set_widget_value(widget, self._values[field_name])
            if field.verbose_name:
                sub_layout.addWidget(QtGui.QLabel(field.verbose_name), row_index, 0)
            sub_layout.addWidget(widget, row_index, 1)

        widgets.append(sub_layout)
        self._buttons = []
        if self.text_confirm:
            self._buttons.append(create_button(self.text_confirm, connect=self.accept, min_size=True))
        if self.text_cancel:
            self._buttons.append(create_button(self.text_cancel, connect=self.reject, min_size=True))
        if self._buttons:
            widgets.append(h_layout(*self._buttons))

        self.setLayout(v_layout(*widgets))
        self.raise_()

    @classmethod
    def get_values(cls, initial=None):
        dialog = cls(initial=initial)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            # noinspection PyProtectedMember
            return dialog._values
        return None

    def accept(self):
        if not self.is_valid():
            return
        return QtGui.QDialog.accept(self)

    def is_valid(self):
        valid = True
        for field_name, field in self._fields.items():
            widget = self._widgets[field_name]
            try:
                setattr(self, field_name, field.get_widget_value(widget))
                field.set_widget_valid(widget, True, '')
            except InvalidValueException as e:
                field.set_widget_valid(widget, False, str(e))
                valid = False
        return valid


class InlineForm(QtGui.QWidget):
    __order__ = None
    __editable__ = True

    def __init__(self, list_of_values, title=''):
        super(InlineForm, self).__init__()
        self.__list_of_values = list_of_values
        self.__attributes = [ButtonField(verbose_name=_('Add element'), icon='edit_add',
                                         connect=self.__add_item),
                             ButtonField(verbose_name=_('Remove element'), icon='edit_remove',
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
        else:
            field_names = [field_name for field_name, field in self.__class__.__dict__.items()
                           if isinstance(field, FormField)]
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
        for i in xrange(index, max_index - 1):
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