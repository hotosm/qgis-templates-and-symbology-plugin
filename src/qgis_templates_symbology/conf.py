# -*- coding: utf-8 -*-
"""
    Handles storage and retrieval of the plugin QgsSettings.
"""

import contextlib
import dataclasses
import datetime
import enum
import typing
import uuid

from qgis.PyQt import (
    QtCore,
    QtWidgets,
)
from qgis.core import QgsRectangle, QgsSettings

from .models import Template, Symbology


@contextlib.contextmanager
def qgis_settings(group_root: str, settings=None):
    """Context manager to help defining groups when creating QgsSettings.

    :param group_root: Name of the root group for the settings.
    :type group_root: str

    :param settings: QGIS settings to use
    :type settings: QgsSettings

    :yields: Instance of the created settings.
    :type: QgsSettings
    """
    if settings is None:
        settings = QgsSettings()
    settings.beginGroup(group_root)
    try:
        yield settings
    finally:
        settings.endGroup()


@dataclasses.dataclass
class ProfileSettings:
    """Manages the plugin profile settings.
    """

    id: uuid.UUID
    name: str
    path: str
    templates: list
    symbology: list
    created_date: datetime.datetime = datetime.datetime.now()

    @classmethod
    def from_qgs_settings(
            cls,
            identifier: str,
            settings: QgsSettings):
        """Reads QGIS settings and parses them into a profile
        settings instance with the respective settings values as properties.

        :param identifier: Profile identifier
        :type identifier: str

        :param settings: QGIS settings.
        :type settings: QgsSettings

        :returns: Profile settings object
        :rtype: ProfileSettings
        """
        templates = []
        symbology = []
        try:
            templates = settings_manager.get_templates(
                uuid.UUID(identifier)
            )
            symbology = settings_manager.get_symbology(
                uuid.UUID(identifier)
            )

            created_date = datetime.datetime.strptime(
                settings.value("created_date"),
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ) if settings.value("created_date") is not None else None
        except AttributeError:
            created_date = datetime.datetime.now()

        return cls(
            id=uuid.UUID(identifier),
            name=settings.value("name"),
            path=settings.value("path"),
            templates=templates,
            symbology=symbology,
            created_date=created_date,
        )


@dataclasses.dataclass
class TemplateSettings(Template):
    """Plugin template setting
    """

    @classmethod
    def from_qgs_settings(
            cls,
            identifier: str,
            settings: QgsSettings):
        """Reads QGIS settings and parses them into a collection
        settings instance with the respective settings values as properties.

        :param identifier: Template identifier
        :type identifier: str

        :param settings: QGIS settings.
        :type settings: QgsSettings

        :returns: Templates settings object
        :rtype: TemplateSettings
        """

        return cls(
            uuid=uuid.UUID(identifier),
            title=settings.value("title", None),
            id=settings.value("id", None),
        )


@dataclasses.dataclass
class SymbologySettings(Symbology):
    """Plugin template setting
    """

    @classmethod
    def from_qgs_settings(
            cls,
            identifier: str,
            settings: QgsSettings):
        """Reads QGIS settings and parses them into a collection
        settings instance with the respective settings values as properties.

        :param identifier: Symbology identifier
        :type identifier: str

        :param settings: QGIS settings.
        :type settings: QgsSettings

        :returns: Symbology settings object
        :rtype: SymbologySettings
        """

        return cls(
            uuid=uuid.UUID(identifier),
            title=settings.value("title", None),
            id=settings.value("id", None),
        )
