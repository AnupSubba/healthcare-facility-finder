"""Data-quality report written to docs/data-quality.md on every pipeline run."""

from datetime import date

import pandas as pd


def pct(part: int, whole: int) -> str:
    return f"{(100 * part / whole):.1f}%" if whole else "n/a"


def report(raw: pd.DataFrame, cleaned: pd.DataFrame, merged: pd.DataFrame, geocoded: int, sources: list[str]) -> str:
    n = len(merged)
    by_source = raw["source"].value_counts().to_dict() if len(raw) else {}
    by_type = merged["type"].value_counts().to_dict() if n else {}
    lines = [
        "# Data quality report",
        "",
        f"Generated {date.today().isoformat()} by `facility_finder.pipeline.run`.",
        "",
        "| Step | Count |",
        "|------|-------|",
        *[f"| Raw records from {src} | {cnt:,} |" for src, cnt in sorted(by_source.items())],
        f"| After cleaning | {len(cleaned):,} |",
        f"| Duplicates merged | {len(cleaned) - n:,} |",
        f"| Facilities loaded | {n:,} |",
        f"| New addresses geocoded this run | {geocoded:,} |",
        "",
        "| Facilities | Count |",
        "|------------|-------|",
        *[f"| {t.title()} | {c:,} |" for t, c in sorted(by_type.items())],
        "",
        "| Completeness | Share |",
        "|--------------|-------|",
        f"| With coordinates | {pct(int(merged['lat'].notna().sum()) if n else 0, n)} |",
        f"| With phone number | {pct(int(merged['phone'].notna().sum()) if n else 0, n)} |",
        f"| With pincode | {pct(int(merged['pincode'].notna().sum()) if n else 0, n)} |",
        f"| Ownership known | {pct(int((merged['ownership'] != 'unknown').sum()) if n else 0, n)} |",
        f"| Cities covered | {merged['city'].nunique() if n else 0:,} |",
        "",
        "Sources: " + "; ".join(sources),
        "",
        "Data © OpenStreetMap contributors (ODbL) and data.gov.in (Government Open Data License - India).",
        "",
    ]
    return "\n".join(lines)
