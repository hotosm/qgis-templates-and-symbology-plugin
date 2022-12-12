# -*- coding: utf-8 -*-

"""
 Symbology dialog class file
"""

import os
import uuid

from pathlib import Path

from qgis.PyQt import QtCore, QtGui, QtWidgets, QtNetwork, QtXml

from qgis import processing

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsNetworkContentFetcherTask,
    QgsProject,
    QgsReadWriteContext,
    QgsProcessing,
    QgsProcessingFeedback,
    QgsRectangle,
    QgsTask
)

from qgis.gui import QgsMessageBar

from qgis.utils import iface

from qgis.PyQt.uic import loadUiType

from ..models import Template, Symbology
from ..conf import settings_manager, Settings
from ..utils import log, tr

from functools import partial

DialogUi, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/symbology_dialog.ui")
)

from ..constants import REPO_URL


class SymbologyDialog(QtWidgets.QDialog, DialogUi):
    """ Dialog for handling symbology details"""

    def __init__(
            self,
            symbology=None,
            main_widget=None
    ):
        """ Constructor

        :param symbology: symbology instance
        :type symbology: models.Symbology
        """
        super().__init__()
        self.setupUi(self)
        self.symbology = symbology
        self.main_widget = main_widget

        self.grid_layout = QtWidgets.QGridLayout()
        self.message_bar = QgsMessageBar()
        self.prepare_message_bar()

        self.profile = settings_manager.get_current_profile()
        self.populate_properties(symbology)

        self.download_symbology_btn.clicked.connect(self.download_symbology)
        self.download_result = {}

    def populate_properties(self, symbology):
        """ Populates the symbology dialog widgets with the
        respective information from passed symbology.

        :param symbology: Plugin symbology instance
        :type symbology: models.Symbology
        """
        symbology = symbology
        if symbology:
            self.title_le.setText(symbology.title)
            self.name_le.setText(symbology.name)
            self.description_le.setText(symbology.description)
            self.extension_le.setText(symbology.properties.extension)
            self.symbology_type_le.setText(symbology.properties.template_type)

            if symbology.license:
                self.license_le.setText(symbology.license)

        self.update_inputs(True)

    def prepare_message_bar(self):
        """ Initializes the widget message bar settings"""
        self.message_bar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Fixed
        )
        self.grid_layout.addWidget(
            self.tab_widget,
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

    def update_inputs(self, enabled):
        """ Updates the inputs widgets state in the dialog.

        :param enabled: Whether to enable the inputs or disable them.
        :type enabled: bool
        """
        self.tab_widget.setEnabled(enabled)

    def set_extent(self, extent):
        """ Sets the symbology spatial and temporal extents

        :param extent: Instance that contain spatial and temporal extents
        :type extent: models.Extent
        """
        spatial_extent = extent.spatial
        if spatial_extent:
            self.spatialExtentSelector.setOutputCrs(
                QgsCoordinateReferenceSystem("EPSG:4326")
            )

            bbox = spatial_extent.bbox[0] \
                if spatial_extent.bbox and isinstance(spatial_extent.bbox, list) \
                else None

            original_extent = QgsRectangle(
                bbox[0],
                bbox[1],
                bbox[2],
                bbox[3]
            ) if bbox and isinstance(bbox, list) else QgsRectangle()
            self.spatialExtentSelector.setOriginalExtent(
                original_extent,
                QgsCoordinateReferenceSystem("EPSG:4326")
            )
            self.spatialExtentSelector.setOutputExtentFromOriginal()

        temporal_extents = extent.temporal
        if temporal_extents:
            pass
        else:
            self.from_date.clear()
            self.to_date.clear()

    def add_thumbnail(self):
        """ Downloads and loads thumbnail"""

        url = f"{REPO_URL}/symbology/" \
              f"{self.symbology.properties.directory}/" \
              f"{self.symbology.properties.thumbnail}"
        request = QtNetwork.QNetworkRequest(
            QtCore.QUrl(
                url
            )
        )

        if self.main_widget:
            self.main_widget.update_inputs(False)
            self.main_widget.show_progress("Loading symbology information")

        self.network_task(
            request,
            self.thumbnail_response
        )

    def thumbnail_response(self, content):
        """ Callback to handle the thumbnail network response.
            Sets the thumbnail image data into the widget thumbnail label.

        :param content: Network response data
        :type content: QByteArray
        """
        thumbnail_image = QtGui.QImage.fromData(content)

        if thumbnail_image:
            thumbnail_pixmap = QtGui.QPixmap.fromImage(thumbnail_image)

            self.image_la.setPixmap(thumbnail_pixmap.scaled(
                500,
                350,
                QtCore.Qt.IgnoreAspectRatio)
            )

        if self.main_widget:
            self.main_widget.update_inputs(True)
            self.main_widget.clear_message_bar()

    def download_symbology_file(self, url, project_file, load=False):
        try:
            download_folder = settings_manager.get_value(Settings.DOWNLOAD_FOLDER)

            self.show_message(
                tr("Download for file {} to {} has started."
                   ).format(
                    project_file,
                    download_folder
                ),
                level=Qgis.Info
            )
            self.update_inputs(False)
            self.show_progress(
                f"Downloading {url}",
                minimum=0,
                maximum=100,
            )
            feedback = QgsProcessingFeedback()

            feedback.progressChanged.connect(
                self.update_progress_bar
            )
            feedback.progressChanged.connect(self.download_progress)

            file_name = self.clean_filename(project_file)

            output = os.path.join(
                download_folder, file_name
            ) if download_folder else QgsProcessing.TEMPORARY_OUTPUT
            params = {'URL': url, 'OUTPUT': output}

            self.download_result["file"] = output

            results = processing.run(
                "qgis:filedownloader",
                params,
                feedback=feedback
            )

            if results:
                log(tr(f"Finished downloading file to {self.download_result['file']}"))
                self.update_inputs(True)
                self.show_message(
                    tr(f"Finished downloading "
                       f"file to {self.download_result['file']}"),
                    level=Qgis.Info
                )

        except Exception as e:
            self.update_inputs(True)
            self.show_message(
                tr("Error in downloading file, {}").format(str(e))
            )
            log(tr("Error in downloading file, {}").format(str(e)))

        return True

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
            self.update_inputs(True)
            self.show_message(f"Fetching content via network, {reply.errorString()}")
            log(tr("Problem fetching response from network"))

    def download_symbology(self, load=False):
        """ Downloads symbology"""

        if not settings_manager.get_value(Settings.DOWNLOAD_FOLDER):
            self.show_message(
                tr("Set the download folder "
                   "first in the plugin settings tab!"
                   )
            )
            return

        symbology_name = self.symbology.name

        url = f"{REPO_URL}/symbology/" \
              f"{self.symbology.properties.directory}/" \
              f"{symbology_name}.{self.symbology.properties.extension}"

        try:
            download_task = QgsTask.fromFunction(
                'Download symbology function',
                self.download_symbology_file(
                    url,
                    f"{symbology_name}.{self.symbology.properties.extension}"
                )
            )
            QgsApplication.taskManager().addTask(download_task)

        except Exception as err:
            self.update_inputs(True)
            self.show_message("Problem running task for downloading project")
            log(tr("An error occured when running task for"
                   " downloading {}, error message \"{}\" ").format(
                symbology_name,
                err)
            )

    def clean_filename(self, filename):
        """ Creates a safe filename by removing operating system
        invalid filename characters.

        :param filename: File name
        :type filename: str

        :returns A clean file name
        :rtype str
        """
        characters = " %:/,\[]<>*?"

        for character in characters:
            if character in filename:
                filename = filename.replace(character, '_')

        return filename

    def download_progress(self, value):
        """Tracks the download progress of value and updates
        the info message when the download has finished

        :param value: Download progress value
        :type value: int
        """
        if value == 100:
            self.update_inputs(True)
            self.show_message(
                tr("Download for file {} has finished."
                   ).format(
                    self.download_result["file"]
                ),
                level=Qgis.Info
            )

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
