# -*- coding: utf-8 -*-

"""
 Layer selection dialog  file
"""

import os
from qgis.PyQt import QtCore, QtGui, QtWidgets, QtNetwork

from qgis.core import (
    Qgis,
    QgsProject
)

from qgis.PyQt.uic import loadUiType

from ..conf import settings_manager, Settings

from ..utils import log, tr


DialogUi, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/layers_selection_dialog.ui")
)


class LayersSelectionDialog(QtWidgets.QDialog, DialogUi):
    """ Dialog for handling layers selection"""

    def __init__(
            self,
            parent
    ):
        """ Constructor

        """
        super().__init__()
        self.setupUi(self)
        self.parent = parent

        select_all_btn = QtWidgets.QPushButton(tr("Select All"))
        select_all_btn.setToolTip(tr("Select the all listed layers"))
        select_all_btn.clicked.connect(self.select_all_clicked)
        self.mButtonBox.addButton(select_all_btn, QtWidgets.QDialogButtonBox.ActionRole)

        clear_all_btn = QtWidgets.QPushButton(tr("Clear Selection"))
        clear_all_btn.setToolTip(tr("Clear the current selection"))
        clear_all_btn.clicked.connect(self.clear_all_clicked)
        self.mButtonBox.addButton(clear_all_btn, QtWidgets.QDialogButtonBox.ActionRole)

        toggle_selection_btn = QtWidgets.QPushButton(tr("Toggle Selection"))
        toggle_selection_btn.clicked.connect(self.toggle_selection_clicked)
        self.mButtonBox.addButton(toggle_selection_btn, QtWidgets.QDialogButtonBox.ActionRole)

        self.mButtonBox.accepted.connect(self.accept)

        self.set_layers()

        profile = settings_manager.get_current_profile()
        custom_properties = settings_manager.get_templates_custom_properties(
            self.parent.template.id,
            profile.id
        )

        for index in range(self.list_widget.count()):
            layer_item = self.list_widget.item(index)
            if custom_properties['layer_names'] is not None:
                if layer_item.text() in custom_properties['layer_names']:
                    layer_item.setCheckState(QtCore.Qt.Checked)

    def set_layers(self):
        layers_values = QgsProject.instance().mapLayers().values()

        layer_names = [f"{layer.name()}" for layer in layers_values]
        for name in layer_names:
            list_widget_item = QtWidgets.QListWidgetItem(name)
            list_widget_item.setFlags(list_widget_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            list_widget_item.setCheckState(QtCore.Qt.Unchecked)
            self.list_widget.addItem(list_widget_item)

    def selected_layers(self):
        layer_items_text = []
        for index in range(self.list_widget.count()):
            layer_item = self.list_widget.item(index)
            if layer_item.checkState() == QtCore.Qt.Checked:
                layer_items_text.append(layer_item.text())
        layer_names = ','.join(layer_items_text)
        layers = [layer for layer in QgsProject.instance().mapLayers().values()
                  if layer.name() in layer_names]
        return layers

    def accept(self):
        self.parent.set_selected_layers(self.selected_layers())
        super().accept()

    def select_all_clicked(self):
        for item_index in range(self.list_widget.count()):
            layer_item = self.list_widget.item(item_index)
            layer_item.setCheckState(QtCore.Qt.Checked)

    def clear_all_clicked(self):
        for item_index in range(self.list_widget.count()):
            layer_item = self.list_widget.item(item_index)
            layer_item.setCheckState(QtCore.Qt.Unchecked)

    def toggle_selection_clicked(self):
        for item_index in range(self.list_widget.count()):
            layer_item = self.list_widget.item(item_index)
            state = layer_item.checkState()
            if state == QtCore.Qt.Checked:
                layer_item.setCheckState(QtCore.Qt.Unchecked)
            elif state == QtCore.Qt.Unchecked:
                layer_item.setCheckState(QtCore.Qt.Checked)
