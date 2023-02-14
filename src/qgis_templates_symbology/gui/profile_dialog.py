# -*- coding: utf-8 -*-

"""
 Profile dialog class file
"""

import os
import uuid
import json

from functools import partial


from qgis.PyQt import QtCore, QtNetwork, QtWidgets, QtGui

from qgis.core import Qgis, QgsNetworkContentFetcherTask
from qgis.gui import QgsMessageBar

from qgis.PyQt.uic import loadUiType

from ..models import Properties, Symbology, Template

from ..conf import (
    ProfileSettings,
    SymbologySettings,
    TemplateSettings,
    settings_manager
)

from ..utils import tr, log

ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")


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
        self.current_profile_id = None

        ok_signals = [
            self.name_edit.textChanged,
            self.url_edit.textChanged,
            self.templates_url.textChanged,
            self.symbology_url.textChanged,
        ]
        for signal in ok_signals:
            signal.connect(self.update_ok_buttons)

        self.grid_layout = QtWidgets.QGridLayout()
        self.message_bar = QgsMessageBar()
        self.progress_bar = QtWidgets.QProgressBar()

        self.templates = []
        self.symbology = []

        if profile:
            self.load_profile_settings(profile)
            self.templates = settings_manager.get_templates(profile.id)
            self.symbology = settings_manager.get_symbology(profile.id)
            self.setWindowTitle(tr("Edit Profile"))

        self.templates_fetch_btn.clicked.connect(self.fetch_templates)
        self.symbology_fetch_btn.clicked.connect(self.fetch_symbology)

        self.prepare_message_bar()

        self.templates_fetch_btn.setIcon(
            QtGui.QIcon(os.path.join(ICON_PATH, "mActionRefresh.svg"))
        )

        self.symbology_fetch_btn.setIcon(
            QtGui.QIcon(os.path.join(ICON_PATH, "mActionRefresh.svg"))
        )

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
            path=self.url_edit.text().strip(),
            title=self.title_le.text(),
            description=self.description_tb.toPlainText(),
            templates_url=self.templates_url.text(),
            symbology_url=self.symbology_url.text(),
        )

        return profile_settings

    def load_profile_settings(self, profile_settings: ProfileSettings):
        """
        """
        self.name_edit.setText(profile_settings.name)
        self.url_edit.setText(profile_settings.path)
        self.title_le.setText(profile_settings.title)
        self.description_tb.setText(profile_settings.description)
        self.templates_url.setText(profile_settings.templates_url)
        self.symbology_url.setText(profile_settings.symbology_url)

    def accept(self):
        """ Handles logic for adding new profiles"""
        profile_id = uuid.uuid4()

        if self.profile is not None:
            profile_id = self.profile.id
            templates = settings_manager.get_templates(profile_id)
            symbology = settings_manager.get_symbology(profile_id)
        else:
            templates = self.templates
            symbology = self.symbology

        self.current_profile_id = profile_id

        profile_settings = ProfileSettings(
            id=profile_id,
            name=self.name_edit.text().strip(),
            path=self.url_edit.text().strip(),
            title=self.title_le.text(),
            description=self.description_tb.toPlainText(),
            templates_url=self.templates_url.text(),
            symbology_url=self.symbology_url.text(),
            templates=templates,
            symbology=symbology
        )
        self.profile = profile_settings

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

    def fetch_templates(self, url=None):
        url = url if url else self.templates_url.text()

        if not url:
            self.show_message(
                tr("Input template URL first,"
                   " before fetching templates.")
            )
            return

        request = QtNetwork.QNetworkRequest(
            QtCore.QUrl(
                f"{url}/data/data.json"
            )
        )
        self.update_profile_inputs(False)
        self.show_progress("Loading template information...")

        self.network_task(
            request,
            self.templates_response
        )

    def templates_response(self, content):
        json_response = json.loads(content.data())

        templates_list = json_response['templates']
        templates_settings = []

        for template in templates_list:
            properties = Properties(
                extension=template.get('extension'),
                directory=template.get('directory'),
                template_type=template.get('type'),
                thumbnail=template.get('thumbnail'),
            )
            template_setting = TemplateSettings(
                id=template.get('id'),
                name=template.get('name'),
                description=template.get('description'),
                title=template.get('title'),
                properties=properties,
            )
            templates_settings.append(template_setting)

        self.templates = templates_settings

        self.show_message(
            tr(f"Profile has {len(templates_settings)} templates"),
            level=Qgis.Info
        )
        self.update_profile_inputs(True)

    def symbology_response(self, content):
        json_response = json.loads(content.data())
        symbology_settings = []

        for symbology in json_response["symbology"]:
            properties = Properties(
                extension=symbology.get('extension'),
                directory=symbology.get('directory'),
                template_type=symbology.get('type'),
                thumbnail=symbology.get('thumbnail'),
            )
            symbology_setting = SymbologySettings(
                id=symbology.get('id'),
                name=symbology.get('name'),
                description=symbology.get('description'),
                title=symbology.get('title'),
                properties=properties,
            )
            symbology_settings.append(symbology_setting)

        self.symbology = symbology_settings

        self.show_message(
            tr(f"Profile has {len(symbology_settings)} symbology"),
            level=Qgis.Info
        )
        self.update_profile_inputs(True)

    def fetch_symbology(self, url=None):
        url = url if url else self.symbology_url.text()

        if not url:
            self.show_message(
                tr("Input symbology url first, "
                   "before fetching the symbology."))
            return

        request = QtNetwork.QNetworkRequest(
            QtCore.QUrl(
                f"{url}/data/data.json"
            )
        )

        self.update_profile_inputs(False)
        self.show_progress("Loading symbology information")

        self.network_task(
            request,
            self.symbology_response
        )

    def network_task(
            self,
            request,
            handler,
    ):
        """Fetches the response from the given request.

        :param request: Network request
        :type request: QNetworkRequest

        :param handler: Callback function to handle the response
        :type handler: Callable
        """
        task = QgsNetworkContentFetcherTask(
            request
        )
        response_handler = partial(
            self.response,
            task,
            handler
        )
        task.fetched.connect(response_handler)
        task.run()

    def response(
            self,
            task,
            handler
    ):
        """Handle the return response

        :param task: QGIS task that fetches network content
        :type task:  QgsNetworkContentFetcherTask
        """
        reply = task.reply()
        error = reply.error()
        if error == QtNetwork.QNetworkReply.NoError:
            contents: QtCore.QByteArray = reply.readAll()
            handler(contents)
        else:
            self.update_profile_inputs(True)
            self.show_message(f"Fetching content via network, {reply.errorString()}")
            log(tr("Problem fetching response from network"))

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

   