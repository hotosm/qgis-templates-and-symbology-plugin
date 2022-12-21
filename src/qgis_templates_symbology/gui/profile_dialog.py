# -*- coding: utf-8 -*-

"""
 Profile dialog class file
"""

import datetime
import os
import uuid


from qgis.PyQt import QtCore, QtGui, QtWidgets

from qgis.core import Qgis
from qgis.gui import QgsMessageBar

from qgis.PyQt.uic import loadUiType

from ..conf import (
    ProfileSettings,
    settings_manager
)


DialogUi, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/profile_dialog.ui")
)


class ProfileDialog(QtWidgets.QDialog, DialogUi):
    """ """

    def __init__(
            self,
            profile=None
    ):
        """ Constructor

        :param profile: Profile settings
        :type profile: ProfileSettings
        """
        super().__init__()
        self.setupUi(self)
        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Ok
        ).setEnabled(False)
        self.profile = profile

        ok_signals = [
            self.name_edit.textChanged,
            self.url_edit.textChanged,
        ]
        for signal in ok_signals:
            signal.connect(self.update_ok_buttons)


        self.grid_layout = QtWidgets.QGridLayout()
        self.message_bar = QgsMessageBar()
        self.progress_bar = QtWidgets.QProgressBar()

        self.prepare_message_bar()

    def prepare_message_bar(self):
        """ Initializes the widget message bar settings"""
        self.message_bar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Fixed
        )
        self.grid_layout.addWidget(
            self.profile_box,
            0, 0, 1, 1
        )
        self.grid_layout.addWidget(
            self.message_bar,
            0, 0, 1, 1,
            alignment=QtCore.Qt.AlignTop
        )
        self.layout().insertLayout(0, self.grid_layout)

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

    def show_progress(
            self,
            message,
            minimum=0,
            maximum=0,
            progress_bar=True):
        """ Shows the progress message on the main widget message bar

        :param message: Progress message
        :type message: str

        :param minimum: Minimum value that can be set on the progress bar
        :type minimum: int

        :param maximum: Maximum value that can be set on the progress bar
        :type maximum: int

        :param progress_bar: Whether to show progress bar status
        :type progress_bar: bool
        """
        self.message_bar.clearWidgets()
        message_bar_item = self.message_bar.createMessage(message)
        try:
            self.progress_bar.isEnabled()
        except RuntimeError as er:
            self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        if progress_bar:
            self.progress_bar.setMinimum(minimum)
            self.progress_bar.setMaximum(maximum)
        else:
            self.progress_bar.setMaximum(0)
        message_bar_item.layout().addWidget(self.progress_bar)
        self.message_bar.pushWidget(message_bar_item, Qgis.Info)

    def get_profile(self):
        """ 
        """
        if self.profile is not None:
            if self.profile.url != self.url_edit.text().strip():
                self.profile.url = self.url_edit.text().strip()
            return self.profile

        profile_id = uuid.uuid4()

        profile_settings = ProfileSettings(
            id=profile_id,
            name=self.name_edit.text().strip(),
            url=self.url_edit.text().strip(),
        )

        return profile_settings

    def load_profile_settings(self, profile_settings: ProfileSettings):
        """
        """
        self.name_edit.setText(profile_settings.name)
        self.url_edit.setText(profile_settings.url)

    def accept(self):
        """ Handles logic for adding new profiles"""
        profile_id = uuid.uuid4()
        if self.profile is not None:
            profile_id = self.profile.id


        profile_settings = ProfileSettings(
            id=profile_id,
            name=self.name_edit.text().strip(),
            url=self.url_edit.text().strip(),
        )
        existing_profile_names = []
        if profile_settings.name in (
                profile.name for profile in
                settings_manager.list_profiles()
                if profile.id != profile_settings.id
        ):
            existing_profile_names.append(profile_settings.name)
        if len(existing_profile_names) > 0:
            profile_settings.name = f"{profile_settings.name}" \
                                       f"({len(existing_profile_names)})"
        settings_manager.save_profile_settings(profile_settings)
        settings_manager.set_current_profile(profile_settings.id)
        super().accept()

    def update_ok_buttons(self):
        """ Responsible for changing the state of the
         profile dialog OK button.
        """
        enabled_state = self.name_edit.text() != "" and \
                        self.url_edit.text() != ""
        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled_state)

    def update_profile_inputs(self, enabled):
        """ Sets the profile inputs state using
        the provided enabled status

        :param enabled: Whether to enable the inputs
        :type enabled: bool
        """
        self.profile_box.setEnabled(enabled)

   