# -*- coding: utf-8 -*-
"""
    Plugin utilities
"""

import os
import subprocess
import sys
import uuid

import xml.etree.ElementTree as ET

from pathlib import Path

import json

from qgis.PyQt import QtCore
from qgis.core import Qgis, QgsApplication, QgsMessageLog, QgsStyle

from .conf import (
    ProfileSettings,
    TemplateSettings,
    SymbologySettings,
    settings_manager
)

from .models import Properties
from .constants import HOT_STYLES_TAG

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
        name: str = "hot_templates_symbology",
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

    profiles_file = LOCAL_ROOT_DIR / "data/profiles.json"

    with profiles_file.open("r") as fh:
        data_json = json.load(fh)
        for profile in data_json['profiles']:
            profile_id = uuid.UUID(profile['id'])

            templates_settings = []
            templates_list = query_templates(profile_name=profile['name'])

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

            if not settings_manager.is_profile(
                    profile_id
            ):
                profile_settings = ProfileSettings(
                    id=profile_id,
                    name=profile['name'],
                    path=profile['path'],
                    templates=templates_settings,
                    symbology=[],
                    title=profile["title"],
                    description=profile["description"],
                    templates_url=profile["templates_url"],
                    symbology_url=profile["symbology_url"],
                )
                settings_manager.save_profile_settings(profile_settings)

                if profile['selected']:
                    settings_manager.set_current_profile(profile_id)
    setup_symbology()

    settings_manager.set_value("default_profiles_set", True)


def query_templates(profile_name=None):
    temp_directory = f"data/{profile_name}/templates/data" \
        if profile_name else "data/templates/data"
    data_file = LOCAL_ROOT_DIR / temp_directory / 'data.json'
    templates_list = []
    with data_file.open("r") as fh:
        data_json = json.load(fh)
        for template in data_json['templates']:
            templates_list.append(template)
    return templates_list


def query_symbology(profile_name=None):
    symb_directory = f"data/{profile_name}/symbology/data" \
        if profile_name else "data/symbology/data"
    symbology_directory = LOCAL_ROOT_DIR / symb_directory
    symbology_list = []
    data_file = symbology_directory / 'data.json'
    with data_file.open("r") as fh:
        data_json = json.load(fh)
        for symbology in data_json['symbology']:
            symbology_list.append(symbology)
    return symbology_list


def setup_symbology():
    plugin_root = os.path.dirname(__file__)
    fonts_directory = os.path.join(plugin_root, 'data', 'symbology', 'fonts')
    styles_folder = os.path.join(plugin_root, 'data', 'symbology', 'styles')
    icon_folders = os.path.join(plugin_root, 'data', 'symbology', 'symbol_libraries')

    # if os.path.exists(fonts_directory):
    #     # Check QGIS version, if it is lower than 3.28
    #     # then don't auto install the fonts since the
    #     # QgsFontManager doesn't exist.
    #     if Qgis.versionInt() >= 32800:
    #         for font_folder in os.listdir(fonts_directory):
    #             add_fonts(os.path.join(fonts_directory, font_folder))
    #         settings_manager.set_value('fonts_installed', True,)
    #     else:
    #         settings_manager.set_value('fonts_installed', False)
    #         log(f"Skipped adding fonts, font manager is not available")
    # else:
    #     log(f"Skipped adding fonts, fonts folder doesn't exists")

    if os.path.exists(styles_folder):
        for style_file in os.listdir(styles_folder):
            add_style_to_manager(os.path.join(styles_folder, style_file))
    else:
        log(f"Skipped adding style, style folder doesn't exists")

    if os.path.exists(icon_folders):
        for icon_folder in os.listdir(icon_folders):
            add_to_icons_path(os.path.join(icon_folders, icon_folder))
    else:
        log(f"Skipped adding icons, icons folder doesn't exists")


def add_fonts(icon_path):
    try:
        if os.path.isdir(icon_path):
            font_manager = QgsApplication.fontManager()
            font_manager.addUserFontDirectory(icon_path)

            log(
                f"Added fonts {icon_path} "
                f"into the QGIS font user directory list"
            )
    except Exception as e:
        log(f"Problem adding fonts into QGIS, error {e}")


def add_style_to_manager(path):
    try:
        extension = os.path.splitext(path)[1]

        if extension == '.xml':
            qstyles = QgsStyle.defaultStyle()

            new_symbols, new_ramps = get_style_entity(path)
            qstyles.importXml(path)
            if HOT_STYLES_TAG not in qstyles.tags():
                qstyles.addTag(HOT_STYLES_TAG)

            for s in new_symbols:
                qstyles.tagSymbol(
                    QgsStyle.StyleEntity.SymbolEntity,
                    s,
                    [HOT_STYLES_TAG]
                )
            for r in new_ramps:
                qstyles.tagSymbol(
                    QgsStyle.StyleEntity.ColorrampEntity,
                    r,
                    [HOT_STYLES_TAG]
                )

            log(
                f"Added style {path} "
                f"into the QGIS symbology"
            )
        else:
            raise NotImplementedError
    except Exception as e:
        log(f"Problem adding style {path} into QGIS, error {e}")


def get_style_entity(path):
    symbols_list = []
    color_ramps = []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        for symbols in root.findall('symbols'):
            for item in symbols.findall('symbol'):
                symbols_list.append(item.get('name'))
        for ramps in root.findall('colorramps'):
            for item in ramps.findall('colorramp'):
                color_ramps.append(item.get('name'))
    except Exception as e:
        log(f"Problem preparing style entity, error {e}")

    return symbols_list, color_ramps


def add_to_icons_path(path):
    try:

        icon_path = path
        svg_paths = QgsApplication.svgPaths()
        message = None

        if icon_path not in svg_paths:
            svg_paths.append(icon_path)
            message = f" Added {icon_path} " \
                      f"into the QGIS icon library path"
        else:
            message = f" Path {icon_path} " \
                      f"already exists in the " \
                      f"QGIS icon library path"

        QgsApplication.setSvgPaths(svg_paths)
        log(message) if message else None

    except Exception as e:
        log(f"Problem adding icons to QGIS, error {e}")


def get_sld_path():
    plugin_root = os.path.dirname(__file__)
    style_directory = os.path.join(plugin_root, 'data', 'symbology','styles')

    return os.path.join(style_directory, 'roads.sld')


def remove_fonts():
    plugin_dir = 'qgis_templates_symbology'

    font_manager = QgsApplication.fontManager()

    for key, value in font_manager.userFontToFamilyMap().items():
        if plugin_dir in key:
            font_manager.removeUserFont(key)
        log(f"Removed {key} user font")