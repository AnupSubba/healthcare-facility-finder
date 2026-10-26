import pandas as pd

from facility_finder.pipeline import clean, data_gov, osm


def test_norm_name_removes_noise():
    assert clean.norm_name("The City Hospital Pvt. Ltd.") == "city hospital"


def test_city_aliases_and_title_case():
    assert clean.normalize_city("bangalore") == "Bengaluru"
    assert clean.normalize_city("  new   delhi ") == "New Delhi"
    assert clean.normalize_city(None) is None


def test_phone_cleaning():
    assert clean.clean_phone("+91 98765 43210") == "9876543210"
    assert clean.clean_phone("011-26588500") == "1126588500"
    assert clean.clean_phone("12345") is None
    assert clean.clean_phone("9876543210; 011-2345678") == "9876543210"


def test_pincode_cleaning():
    assert clean.clean_pincode("New Delhi 110029") == "110029"
    assert clean.clean_pincode("012345") is None
    assert clean.clean_pincode(None) is None


def test_ownership_mapping():
    assert clean.map_ownership("Public") == "government"
    assert clean.map_ownership("Govt.") == "government"
    assert clean.map_ownership("private") == "private"
    assert clean.map_ownership(None) == "unknown"


def test_emergency_mapping():
    assert clean.map_emergency("yes") is True
    assert clean.map_emergency("No") is False
    assert clean.map_emergency("") is None


def test_osm_frame_and_clean(osm_elements):
    df = clean.clean(osm.to_frame(osm_elements, state="Delhi"))
    names = set(df["name"])
    assert "Safdarjung Hospital" in names  # way with a center point
    assert len(df) == 5  # nameless clinic dropped
    wrong = df[df["name"] == "Wrongly Placed Hospital"].iloc[0]
    assert pd.isna(wrong["lat"])  # coordinates outside India removed
    lab = df[df["name"] == "City Diagnostic Lab"].iloc[0]
    assert lab["type"] == "lab" and lab["phone"] == "1204567890"


def test_data_gov_detects_columns(data_gov_csv):
    df = data_gov.load_csv(data_gov_csv, "Sample directory")
    assert list(df["type"]) == ["hospital", "clinic", "lab"]
    assert df.loc[0, "lat"] == 28.5671 and df.loc[0, "lon"] == 77.2102
    assert set(df["source"]) == {"data_gov"}
