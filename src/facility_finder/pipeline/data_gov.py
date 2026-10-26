"""data.gov.in loader: map a downloaded CSV to the pipeline's standard columns.

Datasets on data.gov.in (Government Open Data License - India) use different column names, so columns are
detected from a list of likely names. Run with --show-columns first to check what was detected.
"""

import re

import pandas as pd

CANDIDATES = {
    "name": ["hospital_name", "name_of_hospital", "facility_name", "name_of_the_hospital", "hospital", "name"],
    "type": ["hospital_category", "facility_type", "type_of_facility", "category", "type"],
    "ownership_raw": ["hospital_care_type", "ownership", "type_of_management", "management", "sector"],
    "address": ["address_original_first_line", "address", "location", "full_address"],
    "city": ["city", "town", "city_name"],
    "district": ["district", "district_name"],
    "state": ["state", "state_name"],
    "pincode": ["pincode", "pin_code", "pin", "postal_code"],
    "phone": ["telephone", "phone", "contact_number", "mobile_number", "phone_number"],
    "website": ["website", "web_site"],
    "emergency_raw": ["emergency_services", "emergency", "emergency_num"],
    "lat": ["latitude", "lat"],
    "lon": ["longitude", "long", "lng", "lon"],
    "coordinates": ["location_coordinates", "coordinates", "lat_long"],
}


def _key(column: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", column.strip().lower()).strip("_")


def detect_columns(columns: list[str]) -> dict[str, str]:
    """Return {standard_name: original_column} for every standard column found."""
    by_key = {_key(c): c for c in columns}
    found = {}
    for standard, names in CANDIDATES.items():
        for name in names:
            if name in by_key:
                found[standard] = by_key[name]
                break
    return found


def map_type(value) -> str:
    v = str(value or "").lower()
    if "lab" in v or "diagnostic" in v or "pathology" in v:
        return "lab"
    if "clinic" in v or "dispensary" in v or "phc" in v or "primary health" in v:
        return "clinic"
    return "hospital"


def load_csv(path: str, dataset_title: str, dataset_url: str = "https://data.gov.in") -> pd.DataFrame:
    raw = pd.read_csv(path, dtype=str, encoding_errors="replace")
    mapping = detect_columns(list(raw.columns))
    if "name" not in mapping:
        raise ValueError(f"No facility-name column found in {path}. Columns: {list(raw.columns)}")

    out = pd.DataFrame({std: raw[col] for std, col in mapping.items() if std != "coordinates"})
    if "coordinates" in mapping and "lat" not in mapping:
        parts = raw[mapping["coordinates"]].fillna("").str.split(",", n=1, expand=True)
        out["lat"] = pd.to_numeric(parts[0], errors="coerce")
        out["lon"] = pd.to_numeric(parts.get(1), errors="coerce")
    for col in ("lat", "lon"):
        out[col] = pd.to_numeric(out.get(col), errors="coerce")

    out["type"] = out["type"].map(map_type) if "type" in out else "hospital"
    out["source"] = "data_gov"
    out["source_id"] = [f"{dataset_title}#{i}" for i in range(len(out))]
    out["url"] = dataset_url
    return out
