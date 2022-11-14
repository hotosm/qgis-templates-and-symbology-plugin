# -*- coding: utf-8 -*-

"""
 The plugin main window class file
"""

import os

from functools import partial

from qgis.PyQt import (
    QtCore,
    QtGui,
    QtNetwork,
    QtWidgets,
    QtXml,
)
from qgis.PyQt.uic import loadUiType

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsTask
)
from qgis.gui import QgsMessageBar
from qgis.utils import iface

from ..resources import *

from ..gui.template_dialog import TemplateDialog
from ..models.db import resource_manager


WidgetUi, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/qgis_templates_symbology_main.ui")
)


class QgisTemplatesSymbologyMain(QtWidgets.QMainWindow, WidgetUi):
    """ Main plugin UI"""

    def __init__(
            self,
            parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.prepare_connections()
        self.prepare_templates()

    def prepare_connections(self):

        self.new_connection_btn.clicked.connect(self.add_connection)
        self.edit_connection_btn.clicked.connect(self.edit_connection)
        self.remove_connection_btn.clicked.connect(self.remove_connection)

        self.connections_box.currentIndexChanged.connect(
            self.update_connection_buttons
        )

    def prepare_templates(self):

        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Title'])
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.templates_tree.setModel(self.proxy_model)
        self.templates_tree.selectionModel().selectionChanged.connect(
            self.display_selected_template
        )
        self.templates_tree.doubleClicked.connect(self.templates_tree_double_clicked)
        templates = resources_manager.get_all_templates()
        self.load_templates(templates)

    def edit_connection(self):
        """ Edits the passed connection and updates the connection box list.
        """
        current_text = self.connections_box.currentText()
        if current_text == "":
            return
        connection = settings_manager.find_connection_by_name(current_text)
        connection_dialog = ConnectionDialog(connection)
        connection_dialog.exec_()
        self.update_connections_box()

    def remove_connection(self):
        """ Removes the current active connection.
        """
        current_text = self.connections_box.currentText()
        if current_text == "":
            return
        connection = settings_manager.find_connection_by_name(current_text)
        reply = QtWidgets.QMessageBox.warning(
            self,
            tr('Templates and Symbology manager'),
            tr('Remove the connection "{}"?').format(current_text),
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            settings_manager.delete_connection(connection.id)
            latest_connection = settings_manager.get_latest_connection()
            settings_manager.set_current_connection(
                latest_connection.id
            ) if latest_connection is not None else None
            self.update_connections_box()

    def update_connection_buttons(self):
        """ Updates the edit and remove connection buttons state
        """
        current_name = self.connections_box.currentText()
        enabled = current_name != ""
        self.edit_connection_btn.setEnabled(enabled)
        self.remove_connection_btn.setEnabled(enabled)

    def update_current_connection(self, index: int):
        """ Sets the connection with the passed index to be the
        current selected connection.

        :param index: Index from the connection box item
        :type index: int
        """
        current_text = self.connections_box.itemText(index)
        if current_text == "":
            return
        current_connection = settings_manager. \
            find_connection_by_name(current_text)
        settings_manager.set_current_connection(current_connection.id)
        if current_connection:
            self.update_api_client()
            # Update the templates view to show the current connection
            # templates
            templates = resource_manager.get_templates(
                current_connection.id
            )
            self.model.removeRows(0, self.model.rowCount())
            self.load_templates(templates)
            # self.handle_queryable(Queryable())

        self.search_btn.setEnabled(current_connection is not None)

    def templates_tree_double_clicked(self, index):
        """ Opens the template dialog when an entry from the
        templates view tree has been double clicked.

        :param index: Index of the double clicked item.
        :type index: int

        """
        template = self.templates_tree.model().data(index, 1)
        template_dialog = TemplateDialog(template)
        template_dialog.exec_()

    def load_templates(self, templates):
        """ Adds the templates into the tree view

        :param templates: List of templates to be added
        :type templates: []
        """
        self.model.removeRows(0, self.model.rowCount())

        for template in templates:
            title = template.title if template.title else tr("No Title") + f" ({template.id})"
            item = QtGui.QStandardItem(title)
            item.setData(template, 1)
            self.model.appendRow(item)

        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.sort(QtCore.Qt.DisplayRole)
