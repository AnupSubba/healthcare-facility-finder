"""Cleaning and normalisation with Pandas."""

import re

import numpy as np
import pandas as pd

INDIA_LAT = (6.0, 37.5)
INDIA_LON = (68.0, 97.5)
VALID_TYPES = {"hospital", "clinic", "lab"}

CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "gurgaon": "Gurugram",
    "trivandrum": "Thiruvananthapuram",
    "poona": "Pune",
    "baroda": "Vadodara",
    "benaras": "Varanasi",
    "banaras": "Varanasi",
    "cochin": "Kochi",
    "mysore": "Mysuru",
    "mangalore": "Mangaluru",
    "allahabad": "Prayagraj",
    "pondicherry": "Puducherry",
}

_NAME_STOPWORDS = {"the", "pvt", "ltd", "private", "limited", "and"}
_GOVT = ("govt", "government", "public", "state", "central", "municipal", "district", "civil", "esic", "railway")


def norm_name(name: str) -> str:
    words = re.sub(r"[^a-z0-9 ]+", " ", str(name).lower()).split()
    return " ".join(w for w in words if w not in _NAME_STOPWORDS)


def normalize_city(city) -> str | None:
    if city is None or (isinstance(city, float) and np.isnan(city)):
        return None
    text = re.sub(r"\s+", " ", str(city)).strip()
    if not text:
        return None
    return CITY_ALIASES.get(text.lower(), text.title())


def clean_phone(value) -> str | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    first = re.split(r"[;,/]", str(value))[0]
    digits = re.sub(r"\D", "", first)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if 8 <= len(digits) <= 11 else None


def clean_pincode(value) -> str | None:
    match = re.search(r"(?<!\d)([1-9]\d{5})(?!\d)", str(value or ""))
    return match.group(1) if match else None


def map_ownership(value) -> str:
    v = str(value or "").lower()
    if "private" in v:
        return "private"
    if any(word in v for word in _GOVT):
        return "government"
    return "unknown"


def map_emergency(value) -> bool | None:
    v = str(value or "").strip().lower()
    if v in {"yes", "true", "1", "y", "24x7", "24/7", "available"}:
        return True
    if v in {"no", "false", "0", "n", "not available"}:
        return False
    return None


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise every column the pipeline uses and drop unusable rows."""
    df = df.copy()
    for col in (
        "name",
        "address",
        "city",
        "district",
        "state",
        "pincode",
        "phone",
        "website",
        "ownership_raw",
        "emergency_raw",
        "lat",
        "lon",
        "url",
    ):
        if col not in df:
            df[col] = None

    df["name"] = df["name"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    df = df[df["name"].notna() & (df["name"].str.len() >= 3)]
    df = df[df["type"].isin(VALID_TYPES)]

    df["norm_name"] = df["name"].map(norm_name)
    df["city"] = df["city"].map(normalize_city)
    df["phone"] = df["phone"].map(clean_phone)
    df["pincode"] = df["pincode"].map(clean_pincode)
    df["ownership"] = df["ownership_raw"].map(map_ownership)
    df["emergency"] = df["emergency_raw"].map(map_emergency)

    lat = pd.to_numeric(df["lat"], errors="coerce")
    lon = pd.to_numeric(df["lon"], errors="coerce")
    inside = lat.between(*INDIA_LAT) & lon.between(*INDIA_LON)
    df["lat"] = lat.where(inside)
    df["lon"] = lon.where(inside)

    df = df.drop_duplicates(subset=["source", "source_id"])
    return df.reset_index(drop=True)
