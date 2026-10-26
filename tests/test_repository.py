"""Search tests against a real PostGIS database (set TEST_DATABASE_URL)."""

import json
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text

from facility_finder import repository
from facility_finder.models import FacilitySearch
from facility_finder.pipeline import clean, data_gov, dedupe, load, osm

AIIMS = (28.5672, 77.2100)
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def loaded(db_engine):
    raw = pd.concat(
        [
            osm.to_frame(json.loads((FIXTURES / "osm_sample.json").read_text())),
            data_gov.load_csv(str(FIXTURES / "data_gov_sample.csv"), "Sample"),
        ],
        ignore_index=True,
    )
    cleaned = clean.clean(raw)
    load.load(dedupe.merge(cleaned, dedupe.duplicate_pairs(cleaned)), db_engine)
    return db_engine


def find(engine, **kw):
    lat, lon = kw.pop("lat", None), kw.pop("lon", None)
    return repository.search(FacilitySearch(intent="find", **kw), lat=lat, lon=lon, engine=engine)


def test_load_is_complete(loaded):
    assert repository.count(loaded) == 7


def test_filter_by_type_and_city(loaded):
    rows = find(loaded, facility_type="hospital", city="new delhi")
    assert "Safdarjung Hospital" in {r["name"] for r in rows}
    assert all(r["type"] == "hospital" for r in rows)


def test_city_filter_finds_lab(loaded):
    assert find(loaded, city="Noida", facility_type="lab")


def test_near_me_is_sorted_by_distance(loaded):
    rows = find(loaded, facility_type="hospital", lat=AIIMS[0], lon=AIIMS[1], radius_km=2)
    assert rows[0]["name"].startswith("All India") and rows[0]["distance_m"] < 50
    assert [r["distance_m"] for r in rows] == sorted(r["distance_m"] for r in rows)


def test_radius_cuts_off(loaded):
    rows = find(loaded, lat=AIIMS[0], lon=AIIMS[1], radius_km=0.5)
    assert all(r["distance_m"] <= 500 for r in rows)
    assert not any(r["city"] == "Noida" for r in rows)


def test_lat_lon_not_swapped(loaded):
    # The classic bug: swapping lat/lon puts Delhi in the Indian Ocean, so nothing would be found.
    rows = find(loaded, lat=AIIMS[0], lon=AIIMS[1], radius_km=1)
    assert rows and abs(rows[0]["lat"] - AIIMS[0]) < 0.01 and abs(rows[0]["lon"] - AIIMS[1]) < 0.01


def test_government_and_emergency_filters(loaded):
    rows = find(loaded, ownership="government", emergency_only=True)
    assert rows and all(r["ownership"] == "government" and r["emergency"] for r in rows)


def test_pincode_filter(loaded):
    assert {r["pincode"] for r in find(loaded, pincode="201301")} == {"201301"}


def test_values_are_bound_not_injected(loaded):
    assert find(loaded, name_contains="x' OR '1'='1") == []


def test_report_keeps_facility_name(loaded):
    first = find(loaded, facility_type="lab")[0]
    repository.add_report(first["id"], "Phone number is wrong", engine=loaded)
    with loaded.connect() as conn:
        name = conn.execute(text("SELECT facility_name FROM report ORDER BY id DESC LIMIT 1")).scalar_one()
    assert name == first["name"]
