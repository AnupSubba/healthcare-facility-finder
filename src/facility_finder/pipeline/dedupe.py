"""De-duplication: the same facility often appears in several sources with slightly different names."""

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

# Lower number = preferred for names, ownership and contact details (official data first).
TEXT_PRIORITY = {"data_gov": 0, "osm": 1}
# For coordinates OpenStreetMap is usually more precise.
COORD_PRIORITY = {"osm": 0, "data_gov": 1}
FIELDS = ["name", "type", "address", "city", "district", "state", "pincode", "phone", "website", "emergency"]


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6_371_000 * np.arcsin(np.sqrt(a))


def duplicate_pairs(df: pd.DataFrame, min_score: int = 88, max_m: float = 250) -> list[tuple[int, int]]:
    """Pairs of row labels that look like the same place: same type, similar name, close together.

    Rows are only compared within ~1 km map cells ("blocking"), which keeps this fast for all of India.
    Known limit: two records either side of a cell border are not compared.
    """
    located = df.dropna(subset=["lat", "lon"]).copy()
    located["cell"] = located["lat"].round(2).astype(str) + "," + located["lon"].round(2).astype(str)
    pairs = []
    for _, group in located.groupby("cell"):
        rows = list(group.itertuples())
        for i, a in enumerate(rows):
            for b in rows[i + 1 :]:
                if (
                    a.type == b.type
                    and fuzz.token_set_ratio(a.norm_name, b.norm_name) >= min_score
                    and haversine_m(a.lat, a.lon, b.lat, b.lon) <= max_m
                ):
                    pairs.append((a.Index, b.Index))
    return pairs


def clusters(labels: list, pairs: list[tuple]) -> list[list]:
    """Group labels into clusters with a small union-find."""
    parent = {label: label for label in labels}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        parent[find(a)] = find(b)
    groups: dict = {}
    for label in labels:
        groups.setdefault(find(label), []).append(label)
    return list(groups.values())


def _first(rows: pd.DataFrame, field: str):
    for value in rows[field]:
        if value is not None and not (isinstance(value, float) and np.isnan(value)) and value is not pd.NA:
            return value
    return None


def merge(df: pd.DataFrame, pairs: list[tuple]) -> pd.DataFrame:
    """Merge each cluster into one facility, keeping every source."""
    out = []
    for group in clusters(list(df.index), pairs):
        rows = df.loc[group]
        by_text = rows.sort_values("source", key=lambda s: s.map(TEXT_PRIORITY).fillna(9))
        by_coord = rows.dropna(subset=["lat", "lon"]).sort_values(
            "source", key=lambda s: s.map(COORD_PRIORITY).fillna(9)
        )
        record = {field: _first(by_text, field) for field in FIELDS}
        known = by_text[by_text["ownership"] != "unknown"]["ownership"]
        record["ownership"] = known.iloc[0] if len(known) else "unknown"
        record["lat"] = by_coord["lat"].iloc[0] if len(by_coord) else None
        record["lon"] = by_coord["lon"].iloc[0] if len(by_coord) else None
        record["sources"] = [{"source": r.source, "id": r.source_id, "url": r.url} for r in by_text.itertuples()]
        out.append(record)
    return pd.DataFrame(out)
