"""OpenStreetMap loader (Overpass API): hospitals, clinics and labs, one state at a time.

Data © OpenStreetMap contributors, available under the Open Database License (ODbL).
Overpass is a shared free service: query one state at a time, cache the raw result, and pause between requests.
"""

import json
import time

import pandas as pd
import requests

from .. import config

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
QUERY = """[out:json][timeout:180];
area["ISO3166-2"="{code}"]->.a;
( nwr["amenity"~"^(hospital|clinic)$"](area.a);
  nwr["healthcare"="laboratory"](area.a); );
out center tags;"""

# ISO 3166-2 codes for states and union territories. A few changed over the years, so both the
# older and newer code are listed; a code that OSM doesn't use simply returns no elements.
STATE_CODES = {
    "IN-AN": "Andaman and Nicobar Islands",
    "IN-AP": "Andhra Pradesh",
    "IN-AR": "Arunachal Pradesh",
    "IN-AS": "Assam",
    "IN-BR": "Bihar",
    "IN-CH": "Chandigarh",
    "IN-CT": "Chhattisgarh",
    "IN-CG": "Chhattisgarh",
    "IN-DH": "Dadra and Nagar Haveli and Daman and Diu",
    "IN-DL": "Delhi",
    "IN-GA": "Goa",
    "IN-GJ": "Gujarat",
    "IN-HR": "Haryana",
    "IN-HP": "Himachal Pradesh",
    "IN-JK": "Jammu and Kashmir",
    "IN-JH": "Jharkhand",
    "IN-KA": "Karnataka",
    "IN-KL": "Kerala",
    "IN-LA": "Ladakh",
    "IN-LD": "Lakshadweep",
    "IN-MP": "Madhya Pradesh",
    "IN-MH": "Maharashtra",
    "IN-MN": "Manipur",
    "IN-ML": "Meghalaya",
    "IN-MZ": "Mizoram",
    "IN-NL": "Nagaland",
    "IN-OR": "Odisha",
    "IN-OD": "Odisha",
    "IN-PY": "Puducherry",
    "IN-PB": "Punjab",
    "IN-RJ": "Rajasthan",
    "IN-SK": "Sikkim",
    "IN-TN": "Tamil Nadu",
    "IN-TG": "Telangana",
    "IN-TS": "Telangana",
    "IN-TR": "Tripura",
    "IN-UP": "Uttar Pradesh",
    "IN-UT": "Uttarakhand",
    "IN-UK": "Uttarakhand",
    "IN-WB": "West Bengal",
}


def fetch_state(code: str, refresh: bool = False, pause_s: float = 20) -> list[dict]:
    """Return raw Overpass elements for one state, using data/raw/ as a cache."""
    cache = config.RAW_DIR / f"osm_{code}.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text(encoding="utf-8"))
    response = requests.post(
        OVERPASS_URL, data={"data": QUERY.format(code=code)}, headers={"User-Agent": config.USER_AGENT}, timeout=300
    )
    response.raise_for_status()
    elements = response.json().get("elements", [])
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(elements), encoding="utf-8")
    time.sleep(pause_s)  # be polite to the shared service
    return elements


def to_frame(elements: list[dict], state: str | None = None) -> pd.DataFrame:
    rows = []
    for e in elements:
        tags, center = e.get("tags", {}), e.get("center", {})
        street = ", ".join(
            x for x in (tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:suburb")) if x
        )
        rows.append(
            {
                "source": "osm",
                "source_id": f"{e['type']}/{e['id']}",
                "url": f"https://www.openstreetmap.org/{e['type']}/{e['id']}",
                "name": tags.get("name:en") or tags.get("name"),
                "type": "lab" if tags.get("healthcare") == "laboratory" else tags.get("amenity"),
                "ownership_raw": tags.get("operator:type"),
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "website": tags.get("website") or tags.get("contact:website"),
                "address": tags.get("addr:full") or street or None,
                "city": tags.get("addr:city"),
                "district": tags.get("addr:district"),
                "state": tags.get("addr:state") or state,
                "pincode": tags.get("addr:postcode"),
                "emergency_raw": tags.get("emergency"),
                "lat": e.get("lat", center.get("lat")),
                "lon": e.get("lon", center.get("lon")),
            }
        )
    return pd.DataFrame(rows)
