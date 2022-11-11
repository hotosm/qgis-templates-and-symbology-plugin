
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
    type: str
    resources: typing.List[str]
    name: str = None


@dataclasses.dataclass
class Symbology:

    id: UUID
    title: str
    description: str
    type: str
    resources: typing.List[str]
    name: str = None
