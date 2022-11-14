# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisTemplatesSymbology

 A QGIS plugin that provides support for access and management of map templates and
  symbology.
                             -------------------
        begin                : 2021-11-15
        copyright            : (C) 2021 by Kartoza
        email                : info@kartoza.com
        git sha              : $Format:%H$
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
import os
import sys

LIB_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'lib'))
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QgisTemplatesSymbology class
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .main import QgisTemplatesSymbology

    return QgisTemplatesSymbology(iface)
