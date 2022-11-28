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
from ..models.db import db_manager


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

        self.prepare_profiles()
        self.prepare_templates()

    def prepare_profiles(self):

        self.new_profile_btn.clicked.connect(self.add_profile)
        self.edit_profile_btn.clicked.connect(self.edit_profile)
        self.remove_profile_btn.clicked.connect(self.remove_profile)

        self.profiles_box.currentIndexChanged.connect(
            self.update_profile_buttons
        )

    def add_profile(self):
        """ Adds a new profile into the plugin, then updates
        the profiles combo box list to show the added profile.
        """
        profile_dialog = ProfileDialog()
        profile_dialog.exec_()
        self.update_profiles_box()

    def edit_profile(self):
        """ Edits the passed profile and updates the profile box list.
        """
        current_text = self.profiles_box.currentText()
        if current_text == "":
            return
        profile = settings_manager.find_profile_by_name(current_text)
        profile_dialog = ProfileDialog(profile)
        profile_dialog.exec_()
        self.update_profiles_box()

    def remove_profile(self):
        """ Removes the current active profile.
        """
        current_text = self.profiles_box.currentText()
        if current_text == "":
            return
        profile = settings_manager.find_profile_by_name(current_text)
        reply = QtWidgets.QMessageBox.warning(
            self,
            tr('Qgis Templates and Symbology Manager'),
            tr('Remove the profile "{}"?').format(current_text),
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            settings_manager.delete_profile(profile.id)
            latest_profile = settings_manager.get_latest_profile()
            settings_manager.set_current_profile(
                latest_profile.id
            ) if latest_profile is not None else None
            self.update_profiles_box()

    def prepare_templates(self):

        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Title'])
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.templates_tree.setModel(self.proxy_model)
        self.templates_tree.doubleClicked.connect(self.templates_tree_double_clicked)
        templates = db_manager.get_all_templates()
        self.load_templates(templates)

    def edit_profile(self):
        """ Edits the passed profile and updates the profile box list.
        """
        current_text = self.profiles_box.currentText()
        if current_text == "":
            return
        profile = settings_manager.find_profile_by_name(current_text)
        profile_dialog = ProfileDialog(profile)
        profile_dialog.exec_()
        self.update_profiles_box()

    def remove_profile(self):
        """ Removes the current active profile.
        """
        current_text = self.profiles_box.currentText()
        if current_text == "":
            return
        profile = settings_manager.find_profile_by_name(current_text)
        reply = QtWidgets.QMessageBox.warning(
            self,
            tr('Templates and Symbology manager'),
            tr('Remove the profile "{}"?').format(current_text),
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            settings_manager.delete_profile(profile.id)
            latest_profile = settings_manager.get_latest_profile()
            settings_manager.set_current_profile(
                latest_profile.id
            ) if latest_profile is not None else None
            self.update_profiles_box()

    def update_profile_buttons(self):
        """ Updates the edit and remove profile buttons state
        """
        current_name = self.profiles_box.currentText()
        enabled = current_name != ""
        self.edit_profile_btn.setEnabled(enabled)
        self.remove_profile_btn.setEnabled(enabled)

    def update_current_profile(self, index: int):
        """ Sets the profile with the passed index to be the
        current selected profile.

        :param index: Index from the profile box item
        :type index: int
        """
        current_text = self.profiles_box.itemText(index)
        if current_text == "":
            return
        current_profile = settings_manager. \
            find_profile_by_name(current_text)
        settings_manager.set_current_profile(current_profile.id)
        if current_profile:
            templates = db.get_templates(
                current_profile.id
            )
            self.model.removeRows(0, self.model.rowCount())
            self.load_templates(templates)
            # self.handle_queryable(Queryable())

        self.search_btn.setEnabled(current_profile is not None)

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
