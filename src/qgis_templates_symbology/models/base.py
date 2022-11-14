
import dataclasses
import datetime
import enum
import json
import typing

from uuid import UUID, uuid4

from qgis.PyQt import (
    QtCore
)

from qgis.core import QgsRectangle


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


@dataclasses.dataclass
class Properties:
    links: typing.List[str]
    spatial: SpatialExtent
    temporal: TemporalExtent


