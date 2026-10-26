import pandas as pd

from facility_finder.pipeline import clean, data_gov, dedupe, osm


def test_haversine_known_distance():
    # AIIMS to Safdarjung Hospital, New Delhi: roughly 350 m apart
    assert 300 < dedupe.haversine_m(28.5672, 77.2100, 28.5683, 77.2066) < 400


def test_clusters_union_find():
    groups = dedupe.clusters([1, 2, 3, 4], [(1, 2), (2, 3)])
    assert sorted(map(sorted, groups)) == [[1, 2, 3], [4]]


def test_same_hospital_from_two_sources_is_merged(osm_elements, data_gov_csv):
    raw = pd.concat([osm.to_frame(osm_elements), data_gov.load_csv(data_gov_csv, "Sample")], ignore_index=True)
    cleaned = clean.clean(raw)
    merged = dedupe.merge(cleaned, dedupe.duplicate_pairs(cleaned))

    aiims = merged[merged["name"].str.contains("All India", case=False)]
    assert len(aiims) == 1, "AIIMS appears in both sources and should be merged"
    record = aiims.iloc[0]
    assert {s["source"] for s in record["sources"]} == {"osm", "data_gov"}
    assert record["lat"] == 28.5672  # coordinates prefer OpenStreetMap
    assert record["ownership"] == "government"

    # Safdarjung is 350 m away with a different name: must NOT be merged with AIIMS
    assert (merged["name"] == "Safdarjung Hospital").sum() == 1
    # A lab and a hospital are never merged, even at the same spot
    assert set(merged[merged["pincode"] == "201301"]["type"]) == {"lab"}
