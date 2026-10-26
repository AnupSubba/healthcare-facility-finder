"""Load merged facilities into PostGIS in one transaction.

The old rows are deleted and the new ones inserted inside a single transaction, so the live app keeps
seeing the previous data until the new data is committed.
"""

import json
from datetime import date

import pandas as pd
from sqlalchemy import Engine, text

INSERT = text(
    """
    INSERT INTO facility (name, type, ownership, address, city, district, state, pincode, phone, website,
                          emergency, geom, sources, updated_on)
    VALUES (:name, :type, :ownership, :address, :city, :district, :state, :pincode, :phone, :website,
            :emergency,
            ST_SetSRID(ST_MakePoint(CAST(:lon AS double precision), CAST(:lat AS double precision)), 4326)::geography,
            CAST(:sources AS jsonb), :updated_on)
    """
)


def _clean(value):
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    return value


def to_rows(df: pd.DataFrame) -> list[dict]:
    today = date.today()
    rows = []
    for record in df.to_dict(orient="records"):
        row = {k: _clean(v) for k, v in record.items() if k != "sources"}
        row["sources"] = json.dumps(record["sources"])
        row["updated_on"] = today
        rows.append(row)
    return rows


def load(df: pd.DataFrame, engine: Engine) -> int:
    rows = to_rows(df)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM facility"))
        if rows:
            conn.execute(INSERT, rows)
    return len(rows)
