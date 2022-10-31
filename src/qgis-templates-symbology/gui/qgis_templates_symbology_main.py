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

from ..gui.connection_dialog import ConnectionDialog
from ..gui.collection_dialog import CollectionDialog
from ..gui.queryable_property import QueryablePropertyWidget

from ..conf import ConnectionSettings, Settings, settings_manager

from ..api.models import (
    FilterLang,
    ItemSearch,
    ResourceType,
    SearchFilters,
    SortField,
    SortOrder,
    QueryableFetchType
)
from ..api.client import Client

from .result_item_model import ItemsModel, ItemsSortFilterProxyModel
from .json_highlighter import JsonHighlighter

from ..utils import (
    open_folder,
    log,
    tr,
)

from .result_item_widget import add_footprint_helper, ResultItemWidget

WidgetUi, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/qgis_templates_symbology_main.ui")
)


class QgisTemplatesSymbologyMain(QtWidgets.QMainWindow, WidgetUi):
    """ Main plugin UI that contains tabs for search, results and settings
    functionalities"""

    result_items = []

    def __init__(
            self,
            parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)
