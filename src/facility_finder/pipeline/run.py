"""Run the whole data pipeline.

    # Start small: one state from OpenStreetMap
    uv run python -m facility_finder.pipeline.run --states IN-DL

    # Add a data.gov.in CSV you downloaded, and geocode up to 200 missing addresses
    uv run python -m facility_finder.pipeline.run --states IN-DL IN-UP \\
        --data-gov "data/raw/hospital_directory.csv=National Hospital Directory" --geocode 200

    # Everything (slow: one Overpass request per state, with pauses)
    uv run python -m facility_finder.pipeline.run --all-states
"""

import argparse

import pandas as pd

from .. import config
from ..db import get_engine, init_schema
from . import clean, data_gov, dedupe, geocode, load, osm, quality


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--states", nargs="*", default=[], help="ISO codes such as IN-DL IN-MH")
    parser.add_argument("--all-states", action="store_true")
    parser.add_argument("--data-gov", nargs="*", default=[], metavar="CSV=TITLE")
    parser.add_argument("--geocode", type=int, default=0, metavar="N", help="look up at most N missing addresses")
    parser.add_argument("--refresh", action="store_true", help="re-download instead of using data/raw/ caches")
    parser.add_argument("--dry-run", action="store_true", help="don't write to the database")
    parser.add_argument("--show-columns", action="store_true", help="print detected data.gov.in columns and stop")
    args = parser.parse_args()

    frames, source_notes = [], []
    if args.show_columns:
        for item in args.data_gov:
            path = item.split("=", 1)[0]
            print(path, data_gov.detect_columns(list(pd.read_csv(path, nrows=0).columns)))
        return

    codes = list(osm.STATE_CODES) if args.all_states else args.states
    for code in codes:
        elements = osm.fetch_state(code, refresh=args.refresh)
        print(f"OSM {code}: {len(elements)} elements")
        frames.append(osm.to_frame(elements, state=osm.STATE_CODES.get(code)))
    if codes:
        source_notes.append(f"OpenStreetMap via Overpass ({len(codes)} state codes)")

    for item in args.data_gov:
        path, _, title = item.partition("=")
        frame = data_gov.load_csv(path, title or path)
        print(f"data.gov.in {title or path}: {len(frame)} rows")
        frames.append(frame)
        source_notes.append(f"data.gov.in: {title or path}")

    if not frames:
        parser.error("Nothing to load: pass --states, --all-states or --data-gov")

    raw = pd.concat(frames, ignore_index=True)
    cleaned = clean.clean(raw)
    geocoded = 0
    if args.geocode:
        cleaned, geocoded = geocode.geocode_missing(cleaned, limit=args.geocode)
    merged = dedupe.merge(cleaned, dedupe.duplicate_pairs(cleaned))
    print(f"{len(raw)} raw -> {len(cleaned)} cleaned -> {len(merged)} facilities")

    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_csv(config.INTERIM_DIR / "facilities.csv", index=False)
    config.QUALITY_REPORT.write_text(quality.report(raw, cleaned, merged, geocoded, source_notes), encoding="utf-8")
    print(f"Report written to {config.QUALITY_REPORT}")

    if not args.dry_run:
        engine = get_engine()
        init_schema(engine)
        print(f"Loaded {load.load(merged, engine)} facilities into the database")


if __name__ == "__main__":
    main()
