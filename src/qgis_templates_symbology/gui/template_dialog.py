# -*- coding: utf-8 -*-

"""
 Template dialog class file
"""

import os
import uuid

from pathlib import Path

from functools import partial

from qgis.PyQt import QtCore, QtGui, QtWidgets, QtNetwork, QtXml

import processing

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsNetworkContentFetcherTask,
    QgsMargins,
    QgsLayout,
    QgsLayoutItemLabel,
    QgsLayoutItemMap,
    QgsLayoutItemPicture,
    QgsLayoutItemScaleBar,
    QgsPrintLayout,
    QgsProject,
    QgsProcessing,
    QgsProcessingFeedback,
    QgsReadWriteContext,
    QgsRectangle,
    QgsScaleBarSettings,
    QgsTask,
    QgsUnitTypes
)

from qgis.gui import QgsMessageBar

from qgis.utils import iface

from qgis.PyQt.uic import loadUiType

from ..models import Template, Symbology
from ..conf import settings_manager, Settings
from ..utils import log, tr
from ..constants import THUMBNAIL_WIDTH_REDUCTION, THUMBNAIL_HEIGHT_REDUCTION

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
        self.progress_bar = QtWidgets.QProgressBar()
        self.prepare_message_bar()

        self.profile = settings_manager.get_current_profile()
        self.update_inputs(False)
        self.add_thumbnail()
        self.populate_properties(template)

        self.open_layout_btn.clicked.connect(self.add_layout)
        self.download_result = {}

        if not self.template.downloaded:
            if self.main_widget:
                self.main_widget.update_inputs(False)

            self.download_template(
                self.template,
                add_layout=False,
                prepare_layout=True,
                notify=False
            )
        else:
            self.prepare_layout_properties()

        self.template_title.textChanged.connect(self.save_template_custom_properties)
        self.template_subheading.textChanged.connect(self.save_template_custom_properties)
        self.template_narrative.textChanged.connect(self.save_template_custom_properties)
        self.logo_path.fileChanged.connect(self.save_template_custom_properties)
        self.hot_logo_path.fileChanged.connect(self.save_template_custom_properties)
        self.partner_logo_path.fileChanged.connect(self.save_template_custom_properties)

        reset_properties_partial = partial(self.prepare_layout_properties, True)
        self.reset_properties_btn.clicked.connect(reset_properties_partial)

    def save_template_custom_properties(self):

        custom_properties = {
            'heading': self.template_title.text(),
            'subheading': self.template_subheading.text(),
            'narrative': self.template_narrative.toPlainText(),
            'hub_logo': self.logo_path.filePath(),
            'hot_logo': self.hot_logo_path.filePath(),
            'partner_logo': self.partner_logo_path.filePath(),
        }

        profile = settings_manager.get_current_profile()

        settings_manager.save_custom_template_properties(
            custom_properties,
            self.template.id,
            profile.id
        )

    def populate_properties(self, template):
        """ Populates the template dialog widgets with the
        respective information from passed template.

        :param template: Plugin template instance
        :type template: models.Template
        """
        template = template
        if template:
            self.name_le.setText(template.name)
            self.extension_le.setText(template.properties.extension)
            self.template_type_le.setText(template.properties.template_type)

            if template.license:
                self.license_le.setText(template.license)

        self.update_inputs(True)

    def prepare_layout_properties(self, reset=False):

        if self.template.downloaded:
            layout_path = self.template.download_path

            project = QgsProject.instance()
            layout = QgsPrintLayout(project)

            try:
                with open(layout_path) as f:
                    template_content = f.read()
                doc = QtXml.QDomDocument()
                doc.setContent(template_content)

                _items, _value = layout.loadFromTemplate(
                    doc,
                    QgsReadWriteContext(),
                    False
                )
                for item in _items:
                    if isinstance(item, QgsLayoutItemLabel):
                        if 'map_heading' == item.id():
                            self.template_title.setText(item.text())
                        if 'map_sub_heading' == item.id():
                            self.template_subheading.setText(item.text())
                        if 'map_narrative' == item.id():
                            self.template_narrative.setText(item.text())
                    if isinstance(item, QgsLayoutItemMap):
                        if 'main_map' == item.id():
                            self.set_extent(item.extent())
                self.logo_path.setFilePath('')
                self.hot_logo_path.setFilePath('')
                self.partner_logo_path.setFilePath('')
            except Exception as e:
                log(f"Error preparing layout properties {e}")

        if not reset:
            profile = settings_manager.get_current_profile()
            custom_properties = settings_manager.get_templates_custom_properties(
                self.template.id,
                profile.id
            )
            if custom_properties['heading'] is not None:
                self.template_title.setText(custom_properties['heading'])
            if custom_properties['subheading'] is not None:
                self.template_subheading.setText(custom_properties['subheading'])
            if custom_properties['narrative'] is not None:
                self.template_narrative.setText(custom_properties['narrative'])
            if custom_properties['hub_logo'] is not None:
                self.logo_path.setFilePath(custom_properties['hub_logo'])
            if custom_properties['hot_logo'] is not None:
                self.hot_logo_path.setFilePath(custom_properties['hot_logo'])
            if custom_properties['partner_logo'] is not None:
                self.partner_logo_path.setFilePath(custom_properties['partner_logo'])

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
        try:
            self.message_bar.clearWidgets()
            message_bar_item = self.message_bar.createMessage(message)
            self.progress_bar.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.progress_bar.setMinimum(minimum)
            self.progress_bar.setMaximum(maximum)
            message_bar_item.layout().addWidget(self.progress_bar)
            self.message_bar.pushWidget(message_bar_item, Qgis.Info)
        except RuntimeError as e:
            log(f"Problem showing operation progress, {e}")

    def update_inputs(self, enabled):
        """ Updates the inputs widgets state in the dialog.

        :param enabled: Whether to enable the inputs or disable them.
        :type enabled: bool
        """
        self.tab_widget.setEnabled(enabled)

    def set_extent(self, extent):
        """ Sets the templates spatial and temporal extents

        :param extent: Spatial extent
        :type extent: models.Extent
        """
        spatial_extent = extent
        if spatial_extent:
            self.spatialExtentSelector.setOutputCrs(
                QgsCoordinateReferenceSystem("EPSG:4326")
            )

            original_extent = spatial_extent if spatial_extent else QgsRectangle()
            self.spatialExtentSelector.setOriginalExtent(
                original_extent,
                QgsCoordinateReferenceSystem("EPSG:4326")
            )
            self.spatialExtentSelector.setOutputExtentFromOriginal()

    def add_thumbnail(self):
        """ Downloads and loads thumbnail"""

        profile = settings_manager.get_current_profile()
        repo_url = profile.path

        url = f"{repo_url}/templates/" \
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

            pixmap_width = thumbnail_pixmap.width()
            pixmap_height = thumbnail_pixmap.height()

            target_width = int(pixmap_width)
            target_height = int(pixmap_height)

            if target_width > target_height:
                target_width = 500
                target_height = 350
            elif target_height > target_width:
                target_width = 350
                target_height = 500
            else:
                target_width = pixmap_width - \
                               (pixmap_width * THUMBNAIL_WIDTH_REDUCTION)
                target_height = pixmap_height - \
                                (pixmap_height * THUMBNAIL_HEIGHT_REDUCTION)

            log(f" Target height {target_height}, target width {target_width}")

            self.image_la.setPixmap(
                thumbnail_pixmap.scaled(
                    int(target_width),
                    int(target_height),
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
            )

        if self.main_widget:
            self.main_widget.update_inputs(True)
            self.main_widget.clear_message_bar()

    def download_template_file(
            self,
            url,
            template,
            add_layout=False,
            prepare_layout=False,
            notify=True
    ):
        try:
            download_folder = settings_manager.get_value(Settings.DOWNLOAD_FOLDER)

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

            if notify:
                self.show_message(
                    tr("Download for template {} to {} has started."
                       ).format(
                        template.name,
                        output
                    ),
                    level=Qgis.Info
                )
                self.update_inputs(False)
                self.show_progress(
                    f"Downloading {url}",
                    minimum=0,
                    maximum=100,
                )

            results = processing.run(
                "qgis:filedownloader",
                params,
                feedback=feedback
            )

            if results:
                self.download_result['file'] = results['OUTPUT']
                log(tr(f"Finished downloading file to {self.download_result['file']}"))
                if notify:
                    self.show_message(
                        tr(f"Finished downloading "
                           f"file to {self.download_result['file']}"),
                        level=Qgis.Info
                    )

                self.template.downloaded = True
                self.template.download_path = results['OUTPUT']

                if add_layout:
                    self.add_layout()

                if prepare_layout:
                    self.prepare_layout_properties()

            self.update_inputs(True)
            if self.main_widget:
                self.main_widget.update_inputs(True)
            self.message_bar.clearWidgets()

        except Exception as e:
            self.update_inputs(True)
            if self.main_widget:
                self.main_widget.update_inputs(True)
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
            if self.main_widget:
                self.main_widget.update_inputs(True)
                self.main_widget.clear_message_bar()
            self.update_inputs(True)
            self.show_message(f"Problem fetching content via network, {reply.errorString()}")
            log(tr("Problem fetching response from network"))

    def download_template(
            self,
            template=None,
            add_layout=False,
            prepare_layout=False,
            notify=True
    ):
        profile = settings_manager.get_current_profile()
        repo_url = profile.path

        url = f"{repo_url}/templates/" \
              f"{self.template.properties.directory}/" \
              f"{template.name}.qpt"

        try:
            download_task = QgsTask.fromFunction(
                'Download template function',
                self.download_template_file(
                    url,
                    template,
                    add_layout,
                    prepare_layout,
                    notify
                )
            )
            QgsApplication.taskManager().addTask(download_task)

        except Exception as err:
            self.update_inputs(True)
            self.show_message("Problem running task for downloading template")
            log(tr("An error occured when running task for"
                   " downloading {}, error message \"{}\" ").format(
                template.name,
                err)
            )

    def add_layout(self):
        template = self.template
        project = QgsProject.instance()
        layout = QgsPrintLayout(project)

        self.open_layout_btn.setEnabled(False)
        self.show_progress("Opening layout...")

        if template.downloaded:
            layout_path = Path(template.download_path)
        else:
            self.download_template(template, add_layout=True, prepare_layout=False)
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

            _items, _value = layout.loadFromTemplate(
                doc,
                QgsReadWriteContext(),
                False
            )

            map_scale_bar = None
            layout_map = None
            inset_map = None

            for item in _items:
                if isinstance(item, QgsLayoutItemScaleBar):
                    map_scale_bar = item
                if isinstance(item, QgsLayoutItemMap):
                    if item.id() is not None and \
                           'main_map' == item.id():
                        layout_map = item
                    if item.id() is not None and \
                            'inset_map' == item.id():
                        inset_map = item

                if isinstance(item, QgsLayoutItemPicture):
                    hub_path_exists = (self.logo_path.filePath() and
                                       self.logo_path.filePath() is not "")
                    hot_path_exists = (self.hot_logo_path.filePath() and
                                       self.hot_logo_path.filePath() is not "")
                    partner_path_exists = (self.partner_logo_path.filePath() and
                                           self.partner_logo_path.filePath() is not "")
                    if 'map_hub_logo' == item.id() and \
                            hub_path_exists:
                        item.setPicturePath(self.logo_path.filePath())
                    if 'map_partner_logo' == item.id() and \
                            partner_path_exists:
                        item.setPicturePath(self.partner_logo_path.filePath())
                    if 'map_main_logo' == item.id() and \
                            hot_path_exists:
                        item.setPicturePath(self.hot_logo_path.filePath())

                if isinstance(item, QgsLayoutItemLabel):
                    if 'map_heading' == item.id() and \
                            self.template_title.text() is not None:
                        item.setText(self.template_title.text())
                    if 'map_sub_heading' == item.id() and \
                            self.template_subheading.text() is not None:
                        item.setText(self.template_subheading.text())
                    if 'map_narrative' == item.id() and \
                            self.template_narrative.toPlainText() is not None:
                        item.setText(self.template_narrative.toPlainText())

            if layout_map is not None:
                layout_map.zoomToExtent(iface.mapCanvas().extent())

            crs = QgsCoordinateReferenceSystem('EPSG:4326')
            inset_map.setCrs(crs)

            manager.addLayout(layout)

            # Make sure the map items stay on the original page size
            # and the scale bar is always in line with the main map
            page_collection = layout.pageCollection()

            map_scale_bar.setUnits(QgsUnitTypes.DistanceKilometers)
            map_scale_bar.refresh()

            scale_width = map_scale_bar.sizeWithUnits().width()
            position = map_scale_bar.positionWithUnits().x()

            map_scale_width = layout_map.sizeWithUnits().width()
            map_position = layout_map.positionWithUnits().x()

            scale_loc = scale_width + position
            map_loc = map_scale_width + map_position

            # if scale bar is not inline with the main map
            # we are changing its width, hence resizing page content will
            # make every layout item to fall within the page size.
            if (scale_loc > (map_loc + 5)):
                scale_target_width = map_loc - position \
                    if map_loc > position else None
                size_sc = map_scale_bar.sizeWithUnits()
                size_sc.setWidth(scale_target_width)
                map_scale_bar.setFixedSize(size_sc)
                map_scale_bar.refreshItemSize()

            page_collection.resizeToContents(
                QgsMargins(0, 0, 0, 0),
                QgsUnitTypes.LayoutMillimeters
            )
            layout.refresh()

            designer = iface.openLayoutDesigner(layout)

            self.show_message(
                tr(f"Layout {layout_name} has been added."),
                level=Qgis.Info
            )
            log(tr(f"Layout {layout_name} has been added."))

        except Exception as e:
            log(f"Problem opening layout {template.name}, error {e}")
            self.message_bar.clearWidgets()
            self.show_message(f"Couldn't open the layout {template.name}")

        self.open_layout_btn.setEnabled(True)

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
                tr("Download for template {} file has finished."
                   ).format(
                    self.template.name
                ),
                level=Qgis.Info
            )

    def update_progress_bar(self, value):
        """Sets the value of the progress bar

        :param value: Value to be set on the progress bar
        :type value: float
        """

        try:
            if self.progress_bar:
                self.progress_bar.setValue(int(value))
        except RuntimeError:
            log(
                tr("Error setting value to a progress bar"),
                notify=False
            )
        except Exception as e:
            log(f"Problem accessing progress bar, {e}")
