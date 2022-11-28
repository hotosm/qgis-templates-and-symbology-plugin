
import dataclasses
import datetime
import enum
import json
import typing

from uuid import UUID, uuid4

from qgis.PyQt import (
    QtCore
)

from qgis.core import QgsDateTimeRange, QgsRectangle


@dataclasses.dataclass
class SpatialExtent:
    coordinates: typing.List[int]
    crs: str


@dataclasses.dataclass
class TemporalExtent:
    """Temporal extent as defined by the STAC API"""
    interval: QgsDateTimeRange


@dataclasses.dataclass
class Properties:
    links: typing.List[str]
    spatial: SpatialExtent
    temporal: TemporalExtent


@dataclasses.dataclass
class Template:

    id: UUID
    title: str
    description: str
    license: str
    properties: Properties
    name: str = None


@dataclasses.dataclass
class Symbology:

    id: UUID
    title: str
    description: str
    license: str
    properties: Properties
    name: str = None

