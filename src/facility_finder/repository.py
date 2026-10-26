"""Database access for search and reports.

Only fixed SQL fragments are ever joined into the query; every user-provided value is a bound parameter.
The LLM never writes SQL.
"""

import json

from sqlalchemy import Engine, text

from . import config
from .db import get_engine
from .models import FacilitySearch
from .pipeline.clean import normalize_city

COLUMNS = """id, name, type, ownership, address, city, state, pincode, phone, website, emergency,
             ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lon, sources, updated_on::text AS updated_on"""


def search(
    f: FacilitySearch,
    lat: float | None = None,
    lon: float | None = None,
    limit: int = config.MAX_RESULTS,
    engine: Engine | None = None,
) -> list[dict]:
    where, params = ["TRUE"], {"limit": max(1, min(limit, 50))}
    filters = [  # (is the filter set?, fixed SQL fragment, bound parameters)
        (f.facility_type, "type = :type", {"type": f.facility_type}),
        (f.ownership, "ownership = :own", {"own": f.ownership}),
        (f.emergency_only, "emergency IS TRUE", {}),
        (f.pincode, "pincode = :pin", {"pin": f.pincode}),
        (f.city and not f.pincode and lat is None, "lower(city) = lower(:city)", {"city": normalize_city(f.city)}),
        (f.name_contains, "name ILIKE :q", {"q": f"%{f.name_contains}%"}),
    ]
    for active, fragment, values in filters:
        if active:
            where.append(fragment)
            params.update(values)

    distance = "NULL::double precision"
    if lat is not None and lon is not None:
        point = "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography"  # longitude first!
        where.append(f"ST_DWithin(geom, {point}, :radius)")
        distance = f"ST_Distance(geom, {point})"
        params.update(lat=lat, lon=lon, radius=f.radius_km * 1000)

    sql = f"""SELECT {COLUMNS}, {distance} AS distance_m
              FROM facility WHERE {" AND ".join(where)}
              ORDER BY distance_m NULLS LAST, (emergency IS TRUE) DESC, name
              LIMIT :limit"""
    with (engine or get_engine()).connect() as conn:
        rows = [dict(r._mapping) for r in conn.execute(text(sql), params)]
    for row in rows:
        if isinstance(row["sources"], str):
            row["sources"] = json.loads(row["sources"])
        if row["distance_m"] is not None:
            row["distance_m"] = round(row["distance_m"])
    return rows


def add_report(facility_id: int, issue: str, engine: Engine | None = None) -> None:
    with (engine or get_engine()).begin() as conn:
        conn.execute(
            text(
                """INSERT INTO report (facility_id, facility_name, issue)
                   SELECT :id, (SELECT name FROM facility WHERE id = :id), :issue"""
            ),
            {"id": facility_id, "issue": issue.strip()[:500]},
        )


def count(engine: Engine | None = None) -> int:
    with (engine or get_engine()).connect() as conn:
        return conn.execute(text("SELECT count(*) FROM facility")).scalar_one()
