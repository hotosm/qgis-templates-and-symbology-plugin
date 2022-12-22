# -*- coding: utf-8 -*-

"""
 The plugin main window class file
"""

import os

from functools import partial

from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets,
)
from qgis.PyQt.uic import loadUiType

from qgis.core import (
    Qgis,
)
from qgis.gui import QgsMessageBar

from ..resources import *

from ..gui.template_dialog import TemplateDialog
from ..gui.symbology_dialog import SymbologyDialog
from ..gui.profile_dialog import ProfileDialog
from ..conf import settings_manager, Settings

from ..utils import open_folder, tr, log


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

        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Title'])
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)


        self.symbology_model = QtGui.QStandardItemModel()
        self.symbology_model.setHorizontalHeaderLabels(['Title'])
        self.symbology_proxy_model = QtCore.QSortFilterProxyModel()
        self.symbology_proxy_model.setSourceModel(self.symbology_model)
        self.symbology_proxy_model.setDynamicSortFilter(True)
        self.symbology_proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.symbology_proxy_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.prepare_profiles()
        self.prepare_templates()
        self.prepare_symbology()

        self.grid_layout = QtWidgets.QGridLayout()
        self.message_bar = QgsMessageBar()
        self.progress_bar = None
        self.prepare_message_bar()

        download_folder = settings_manager.get_value(
            Settings.DOWNLOAD_FOLDER
        )
        self.download_folder_btn.setFilePath(
            download_folder
        ) if download_folder else None

        self.download_folder_btn.fileChanged.connect(
            self.save_download_folder)
        self.open_folder_btn.clicked.connect(self.open_download_folder)

        self.project_auto_load.setChecked(
            settings_manager.get_value(
                Settings.AUTO_PROJECT_LOAD,
                False,
                setting_type=bool
            )
        )

        self.project_auto_load.toggled.connect(self.change_auto_load_setting)

        self.symbology_sort_cmb.activated.connect(self.sort_symbology)
        self.template_sort_cmb.activated.connect(self.sort_template)

        self.symbology_order.toggled.connect(self.sort_symbology)
        self.template_order.toggled.connect(self.sort_template)

    def sort_symbology(self):
        order = self.symbology_order.isChecked()
        symbology_order = QtCore.Qt.SortOrder.DescendingOrder \
            if order else QtCore.Qt.SortOrder.AscendingOrder
        self.symbology_proxy_model.sort(QtCore.Qt.DisplayRole, symbology_order)

    def sort_template(self):
        order = self.template_order.isChecked()
        templates_order = QtCore.Qt.SortOrder.DescendingOrder \
            if order else QtCore.Qt.SortOrder.AscendingOrder
        self.proxy_model.sort(QtCore.Qt.DisplayRole, templates_order)

    def change_auto_load_setting(self, enabled):

        settings_manager.set_value(
            Settings.AUTO_PROJECT_LOAD,
            enabled
        )

    def save_download_folder(self, folder):
        """ Saves the passed folder into the plugin settings

        :param folder: Folder intended to be saved
        :type folder: str
        """
        if folder:
            try:
                if not os.path.exists(folder):
                    os.makedirs(folder)

                settings_manager.set_value(
                    Settings.DOWNLOAD_FOLDER,
                    str(folder)
                )
            except PermissionError:
                self.show_message(
                    tr("Unable to write to {} due to permissions. "
                       "Choose a different folder".format(
                        folder)
                    ),
                    level=Qgis.Critical
                )
        else:
            settings_manager.set_value(
                Settings.DOWNLOAD_FOLDER,
                folder
            )
            self.show_message(
                tr(
                    'Download folder has not been set, '
                    'a system temporary folder will be used'
                ),
                level=Qgis.Warning
            )

    def open_download_folder(self):
        """ Opens the current download folder"""
        result = open_folder(
            self.download_folder_btn.filePath()
        )

        if not result[0]:
            self.show_message(result[1], level=Qgis.Critical)

    def prepare_profiles(self):

        self.new_profile_btn.clicked.connect(self.add_profile)
        self.edit_profile_btn.clicked.connect(self.edit_profile)
        self.remove_profile_btn.clicked.connect(self.remove_profile)

        self.profiles_box.currentIndexChanged.connect(
            self.update_profile_buttons
        )

        self.update_profiles_box()

    def update_profiles_box(self):
        existing_profiles = settings_manager.list_profiles()
        self.profiles_box.clear()
        if len(existing_profiles) > 0:
            self.profiles_box.addItems(
                profile.name for profile in existing_profiles
            )
            current_profile = settings_manager.get_current_profile()
            if current_profile is not None:
                current_index = self.profiles_box. \
                    findText(current_profile.name)
                self.profiles_box.setCurrentIndex(current_index)
                templates = settings_manager.get_templates(
                    current_profile.id
                )
                self.model.removeRows(0, self.model.rowCount())
                self.load_templates(templates)
            else:
                self.profiles_box.setCurrentIndex(0)

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

        self.templates_tree.setModel(self.proxy_model)
        self.templates_tree.doubleClicked.connect(self.templates_tree_double_clicked)
        current_profile = settings_manager.get_current_profile()
        if current_profile:
            templates = settings_manager.get_templates(current_profile.id)
            self.load_templates(templates)

    def prepare_symbology(self):

        self.symbology_tree.setModel(self.symbology_proxy_model)
        self.symbology_tree.doubleClicked.connect(self.symbology_tree_double_clicked)
        current_profile = settings_manager.get_current_profile()
        if current_profile:
            symbology_list = settings_manager.get_symbology(current_profile.id)
            self.load_symbology(symbology_list)

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
            templates = settings_manager.get_templates(
                current_profile.id
            )
            self.model.removeRows(0, self.model.rowCount())
            self.load_templates(templates)

        self.search_btn.setEnabled(current_profile is not None)


    def symbology_tree_double_clicked(self, index):
        """ Opens the symbology dialog when an entry from the
        symbology view tree has been double clicked.

        :param index: Index of the double clicked item.
        :type index: int

        """
        symbology = self.symbology_tree.model().data(index, 1)
        symbology_dialog = SymbologyDialog(symbology)
        symbology_dialog.exec_()

    def templates_tree_double_clicked(self, index):
        """ Opens the template dialog when an entry from the
        templates view tree has been double clicked.

        :param index: Index of the double clicked item.
        :type index: int

        """
        template = self.templates_tree.model().data(index, 1)
        template_dialog = TemplateDialog(template, self)
        template_dialog.exec_()

    def load_symbology(self, symbology_list):
        """ Adds the templates into the tree view

        :param templates: List of templates to be added
        :type templates: []
        """
        self.symbology_model.removeRows(0, self.model.rowCount())

        for symbology in symbology_list:
            name = symbology.name if symbology.name else tr("No Title") + f" ({symbology.id})"
            item = QtGui.QStandardItem(name)
            item.setData(symbology, 1)
            self.symbology_model.appendRow(item)

        self.symbology_proxy_model.setSourceModel(self.symbology_model)
        self.symbology_proxy_model.sort(QtCore.Qt.DisplayRole)

    def load_templates(self, templates):
        """ Adds the templates into the tree view

        :param templates: List of templates to be added
        :type templates: []
        """
        self.model.removeRows(0, self.model.rowCount())

        for template in templates:
            name = template.name if template.name else tr("No Title") + f" ({template.id})"
            item = QtGui.QStandardItem(name)
            item.setData(template, 1)
            self.model.appendRow(item)

        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.sort(QtCore.Qt.DisplayRole)

    def show_message(
            self,
            message,
            level=Qgis.Warning
    ):
        """ Shows message on the main widget message bar

        :param message: Message text
        :type message: str

        :param level: Message level type
        :type level: Qgis.MessageLevel
        """
        self.message_bar.clearWidgets()
        self.message_bar.pushMessage(message, level=level)

    def show_progress(self, message, minimum=0, maximum=0):
        """ Shows the progress message on the main widget message bar

        :param message: Progress message
        :type message: str

        :param minimum: Minimum value that can be set on the progress bar
        :type minimum: int

        :param maximum: Maximum value that can be set on the progress bar
        :type maximum: int
        """
        self.message_bar.clearWidgets()
        message_bar_item = self.message_bar.createMessage(message)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.progress_bar.setMinimum(minimum)
        self.progress_bar.setMaximum(maximum)
        message_bar_item.layout().addWidget(self.progress_bar)
        self.message_bar.pushWidget(message_bar_item, Qgis.Info)

    def update_progress_bar(self, value):
        """Sets the value of the progress bar

        :param value: Value to be set on the progress bar
        :type value: float
        """
        if self.progress_bar:
            try:
                self.progress_bar.setValue(int(value))
            except RuntimeError:
                log(
                    tr("Error setting value to a progress bar"),
                    notify=False
                )

    def clear_message_bar(self):
        self.message_bar.clearWidgets()

    def update_inputs(self, enabled):
        self.search.setEnabled(enabled)
        self.settings.setEnabled(enabled)

    def prepare_message_bar(self):
        """ Initializes the widget message bar settings"""
        self.message_bar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Fixed
        )
        self.grid_layout.addWidget(
            self.container,
            0, 0, 1, 1
        )
        self.grid_layout.addWidget(
            self.message_bar,
            0, 0, 1, 1,
            alignment=QtCore.Qt.AlignTop
        )
        self.central_widget.layout().insertLayout(0, self.grid_layout)
