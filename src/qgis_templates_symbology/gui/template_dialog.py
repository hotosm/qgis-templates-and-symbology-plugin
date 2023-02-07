# -*- coding: utf-8 -*-

"""
 Template dialog class file
"""

import os
import uuid

from pathlib import Path

from qgis.PyQt import QtCore, QtGui, QtWidgets, QtNetwork, QtXml

import processing

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsNetworkContentFetcherTask,
    QgsLayout,
    QgsPrintLayout,
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
    os.path.join(os.path.dirname(__file__), "../ui/template_dialog.ui")
)

from ..constants import REPO_URL


class TemplateDialog(QtWidgets.QDialog, DialogUi):
    """ Dialog for handling templates details"""

    def __init__(
            self,
            template=None,
            main_widget=None
    ):
        """ Constructor

        :param template: template instance
        :type template: models.Template
        """
        super().__init__()
        self.setupUi(self)
        self.template = template
        self.main_widget = main_widget

        self.grid_layout = QtWidgets.QGridLayout()
        self.message_bar = QgsMessageBar()
        self.prepare_message_bar()

        self.profile = settings_manager.get_current_profile()
        self.update_inputs(False)
        self.add_thumbnail()
        self.populate_properties(template)

        self.open_layout_btn.clicked.connect(self.add_layout)
        self.download_project_btn.clicked.connect(self.download_project)
        self.download_result = {}

    def populate_properties(self, template):
        """ Populates the template dialog widgets with the
        respective information from passed template.

        :param template: Plugin template instance
        :type template: models.Template
        """
        template = template
        if template:
            self.title_le.setText(template.title)
            self.name_le.setText(template.name)
            self.description_le.setText(template.description)
            self.extension_le.setText(template.properties.extension)
            self.template_type_le.setText(template.properties.template_type)

            if template.license:
                self.license_le.setText(template.license)

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
        """ Sets the templates spatial and temporal extents

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

        profile = settings_manager.get_current_profile()
        repo_url = profile.path
        profile_name = profile.name.lower()

        url = f"{repo_url}/{profile_name}/templates/" \
              f"{self.template.properties.directory}/" \
              f"{self.template.properties.thumbnail}"
        request = QtNetwork.QNetworkRequest(
            QtCore.QUrl(
                url
            )
        )

        if self.main_widget:
            self.main_widget.update_inputs(False)
            self.main_widget.show_progress("Loading template information")

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

    def download_project_file(self, url, project_file, load=False):
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

                if load:
                    self.load_project(self.download_result['file'], project_file)

        except Exception as e:
            self.update_inputs(True)
            self.show_message(
                tr("Error in downloading file, {}").format(str(e))
            )
            log(tr("Error in downloading file, {}").format(str(e)))

        return True

    def download_template_file(self, url, template, add_layout=False):
        try:
            download_folder = settings_manager.get_value(Settings.DOWNLOAD_FOLDER)

            self.show_message(
                tr("Download for template {} to {} has started."
                   ).format(
                    template.name,
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

            file_name = self.clean_filename(template.name)

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

                self.template.downloaded = True
                self.template.download_path = self.download_result['file']

                if add_layout:
                    self.add_layout()

        except Exception as e:
            self.update_inputs(True)
            self.show_message(
                tr("Error in downloading file, {}").format(str(e))
            )
            log(tr("Error in downloading file, {}").format(str(e)))

        return True

    def load_project(self, path, name):
        project_name = name.replace('_map.gpkg', '')
        uri = f"geopackage:{path}?projectName={project_name}"
        try:
            QgsProject.instance().read(uri)
            self.show_message(
                tr(f"Successfully loaded project {project_name}"),
                level=Qgis.Info
            )
            log(f"Successfully loaded project {project_name}")
        except Exception as err:
            self.show_message(
                tr(f"Problem loading project {project_name}, error {err}"),
                level=Qgis.Info
            )
            log(f"Problem loading project {project_name}, error {err}")

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
            if self.main_widget:
                self.main_widget.update_inputs(True)
                self.main_widget.clear_message_bar()
            self.update_inputs(True)
            self.show_message(f"Problem fetching content via network, {reply.errorString()}")
            log(tr("Problem fetching response from network"))

    def download_project(self, load=False):
        """ Downloads project"""

        if not settings_manager.get_value(Settings.DOWNLOAD_FOLDER):
            self.show_message(
                tr("Set the download folder "
                   "first in the plugin settings tab!"
                   ),
                level=Qgis.Warning
            )
            return

        project_name = self.template.properties.directory.replace("-templates", '')
        project_name = project_name.replace('-', '_')

        profile = settings_manager.get_current_profile()
        profile_url = profile.path
        profile_name = profile.name.lower()

        url = f"{profile_url}/{profile_name}/templates/" \
              f"{self.template.properties.directory}/" \
              f"{project_name}.gpkg"

        load = settings_manager.get_value(
                Settings.AUTO_PROJECT_LOAD,
                False,
                setting_type=bool
            )

        try:
            download_task = QgsTask.fromFunction(
                'Download project function',
                self.download_project_file(url, f"{project_name}.gpkg", load)
            )
            QgsApplication.taskManager().addTask(download_task)

        except Exception as err:
            self.update_inputs(True)
            self.show_message("Problem running task for downloading project")
            log(tr("An error occured when running task for"
                   " downloading {}, error message \"{}\" ").format(
                project_name,
                err)
            )

    def download_template(self, template=None):
        if not settings_manager.get_value(Settings.DOWNLOAD_FOLDER):
            self.show_message(
                tr("Set the download folder "
                   "first in the plugin settings tab!"
                   ),
                level=Qgis.Warning
            )
            return

        profile = settings_manager.get_current_profile()
        repo_url = profile.path
        profile_name = profile.name.lower()

        url = f"{repo_url}/{profile_name}/templates/" \
              f"{self.template.properties.directory}/" \
              f"{template.name}.qpt"

        try:
            download_task = QgsTask.fromFunction(
                'Download template function',
                self.download_template_file(url, template, True)
            )
            QgsApplication.taskManager().addTask(download_task)

        except Exception as err:
            self.update_inputs(True)
            self.show_message("Problem running task for downloading project")
            log(tr("An error occured when running task for"
                   " downloading {}, error message \"{}\" ").format(
                template.name,
                err)
            )

    def add_layout(self):
        template = self.template
        project = QgsProject.instance()
        layout = QgsPrintLayout(project)

        if template.downloaded:
            layout_path = Path(template.download_path)
        else:
            self.download_template(template)
            return

        log(f"Opening layout from {layout_path}")

        manager = project.layoutManager()
        layout_name = template.name

        # Create a layout name if another layout with similar name exists and can't be removed.

        existing_layout = manager.layoutByName(layout_name)

        if existing_layout:
            if not manager.removeLayout(existing_layout):
                suffix_id = uuid.uuid4()
                layout_name = f"{layout_name}_{str(suffix_id)}"

        layout.setName(layout_name)

        layout.initializeDefaults()

        try:
            with open(layout_path) as f:
                template_content = f.read()
            doc = QtXml.QDomDocument()
            doc.setContent(template_content)

            _items, _value = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)

            manager.addLayout(layout)
            iface.openLayoutDesigner(layout)
            self.show_message(
                tr(f"Layout {layout_name} has been added."),
                level=Qgis.Info
            )
            log(tr(f"Layout {layout_name} has been added."))

        except RuntimeError:
            log(f"Problem opening layout {template.name}")

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
