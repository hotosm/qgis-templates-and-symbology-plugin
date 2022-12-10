# -*- coding: utf-8 -*-

"""
 Template dialog class file
"""

import os

from pathlib import Path

from qgis.PyQt import QtCore, QtGui, QtWidgets, QtNetwork

from qgis.core import (
    Qgis,
    QgsNetworkContentFetcherTask,
    QgsLayout,
    QgsPrintLayout,
    QgsProject,
    QgsReadWriteContext,
    QgsCoordinateReferenceSystem,
    QgsRectangle
)

from qgis.gui import QgsMessageBar

from qgis.utils import iface

from qgis.PyQt.uic import loadUiType

from ..models import Template, Symbology
from ..conf import settings_manager
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

        url = f"{REPO_URL}/templates/{self.template.properties.directory}/{self.template.properties.thumbnail}"
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

        :param auth_config: Authentication configuration string
        :type auth_config: str
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
            log(tr("Problem fetching response from network"))

    def add_layout(self):
        template = self.template
        project = QgsProject.instance()
        layout = QgsPrintLayout(project)

        layout_path = Path(__file__).parent.resolve() / 'data' / 'templates' /\
                     template.properties.directory / template.name / '.qpt'

        layout.setName(templates.name)
        layout.initializeDefaults()

        log(f"Opening layout from {layout_path}")

        with open(layout_path) as f:
            template_content = f.read()
        doc = QDomDocument()
        doc.setContent(template_content)

        _items, _value = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)

        manager = project.layoutManager()
        manager.addLayout(layout)

        iface.openLayoutDesigner(layout)
