# -*- coding: utf-8 -*-
"""
    Plugin utilities
"""

import datetime
import os
import subprocess
import sys
import uuid

from osgeo import gdal

from pathlib import Path

import json

from qgis.PyQt import QtCore, QtGui
from qgis.core import Qgis, QgsMessageLog

from .conf import (
    ProfileSettings,
    TemplateSettings,
    SymbologySettings,
    settings_manager
)

from .models import Properties

from .definitions.profiles import PROFILES

LOCAL_ROOT_DIR = Path(__file__).parent.resolve()


def tr(message):
    """Get the translation for a string using Qt translation API.
    We implement this ourselves since we do not inherit QObject.

    :param message: String for translation.
    :type message: str, QString

    :returns: Translated version of message.
    :rtype: QString
    """
    # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
    return QtCore.QCoreApplication.translate("QgisTemplatesSymbology", message)


def log(
        message: str,
        name: str = "qgis_templates_symbology",
        info: bool = True,
        notify: bool = True,
):
    """ Logs the message into QGIS logs using qgis_templates_symbology as the default
    log instance.
    If notify_user is True, user will be notified about the log.

    :param message: The log message
    :type message: str

    :param name: Name of te log instance, qgis_templates_symbology is the default
    :type message: str

    :param info: Whether the message is about info or a
    warning
    :type info: bool

    :param notify: Whether to notify user about the log
    :type notify: bool
     """
    level = Qgis.Info if info else Qgis.Warning
    QgsMessageLog.logMessage(
        message,
        name,
        level=level,
        notifyUser=notify,
    )


def open_folder(path):
    """ Opens the folder located at the passed path

    :param path: Folder path
    :type path: str

    :returns message: Message about whether the operation was
    successful or not.
    :rtype tuple
    """
    if not path:
        return False, tr("Path is not set")

    if not os.path.exists(path):
        return False, tr('Path do not exist: {}').format(path)

    if not os.access(path, mode=os.R_OK | os.W_OK):
        return False, tr('No read or write permission on path: {}').format(path)

    if sys.platform == 'darwin':
        subprocess.check_call(['open', path])
    elif sys.platform in ['linux', 'linux1', 'linux2']:
        subprocess.check_call(['xdg-open', path])
    elif sys.platform == 'win32':
        subprocess.check_call(['explorer', path])
    else:
        raise NotImplementedError

    return True, tr("Success")


def config_defaults_profiles():
    """ Initialize the plugin profiles
    """

    for profile in PROFILES:
        profile_id = uuid.UUID(profile['id'])

        templates_settings = []
        templates_list = query_templates()

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

        log(f"Templates settings {len(templates_settings)}")

        symbology_settings = []

        for symbology in profile.get('symbology'):
            symbology_setting = SymbologySettings(
                id=symbology.get('id'),
                name=symbology.get('name'),
            )
            symbology_settings.append(symbology_setting)

        if not settings_manager.is_profile(
                profile_id
        ):
            profile_settings = ProfileSettings(
                id=profile_id,
                name=profile['name'],
                path=profile['path'],
                templates=templates_settings,
                symbology=symbology_settings,
            )
            settings_manager.save_profile_settings(profile_settings)

            if profile['selected']:
                settings_manager.set_current_profile(profile_id)

    settings_manager.set_value("default_profiles_set", True)


def query_templates():
    templates_directory = LOCAL_ROOT_DIR / "data/templates"
    templates_list = []
    for template_directory in templates_directory.iterdir():
        data_file = template_directory / 'data.json'
        with data_file.open("r") as fh:
            data_json = json.load(fh)
            for template in data_json['templates']:
                templates_list.append(template)
    return templates_list

