"""Fill in missing coordinates with Nominatim (OpenStreetMap's geocoder).

Usage policy: at most 1 request per second, identify the app in the User-Agent, cache results, credit OSM.
Results (including misses) are cached in data/interim/geocode_cache.csv so each address is looked up only once.
"""

import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

from .. import config

CACHE = config.INTERIM_DIR / "geocode_cache.csv"


def _query(row) -> str | None:
    parts = [row.get("address"), row.get("city"), row.get("district"), row.get("state"), row.get("pincode")]
    parts = [str(p) for p in parts if p is not None and str(p) not in ("", "nan", "None")]
    return ", ".join(parts + ["India"]) if len(parts) >= 2 else None


def geocode_missing(df: pd.DataFrame, limit: int = 500) -> tuple[pd.DataFrame, int]:
    """Geocode up to `limit` rows without coordinates. Returns (frame, number of new lookups)."""
    cache = (
        pd.read_csv(CACHE, dtype={"query": str}) if CACHE.exists() else pd.DataFrame(columns=["query", "lat", "lon"])
    )
    known = {q: (lat, lon) for q, lat, lon in cache.itertuples(index=False)}
    geocoder = Nominatim(user_agent=config.USER_AGENT, timeout=10)
    lookup = RateLimiter(geocoder.geocode, min_delay_seconds=1.1, max_retries=1, swallow_exceptions=True)

    df = df.copy()
    new = 0
    for idx, row in df[df["lat"].isna()].iterrows():
        query = _query(row)
        if not query:
            continue
        if query not in known:
            if new >= limit:
                continue
            place = lookup(query, country_codes="in")
            known[query] = (place.latitude, place.longitude) if place else (None, None)
            new += 1
        lat, lon = known[query]
        if lat is not None and pd.notna(lat):
            df.at[idx, "lat"], df.at[idx, "lon"] = lat, lon

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([(q, la, lo) for q, (la, lo) in known.items()], columns=["query", "lat", "lon"]).to_csv(
        CACHE, index=False
    )
    return df, new
