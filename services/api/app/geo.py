"""PostGIS helpers for building and reading geography points (manual section 11)."""

from __future__ import annotations

from geoalchemy2 import Geography, Geometry
from sqlalchemy import cast
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import func


def make_point(longitude: float, latitude: float) -> ColumnElement:
    """Build a SRID-4326 geography POINT from lon/lat for inserts and queries."""
    return cast(func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326), Geography)


def longitude_of(column: ColumnElement) -> ColumnElement:
    """Extract the longitude (X) from a geography point column."""
    return func.ST_X(cast(column, Geometry))


def latitude_of(column: ColumnElement) -> ColumnElement:
    """Extract the latitude (Y) from a geography point column."""
    return func.ST_Y(cast(column, Geometry))
