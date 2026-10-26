"""The emergency check is a hard rule, so it's tested on the whole evaluation set in CI (no LLM needed)."""

import csv
from collections import Counter
from pathlib import Path

from facility_finder.agent.safety import is_emergency
from facility_finder.models import FacilitySearch

ROWS = list(csv.DictReader((Path(__file__).parents[1] / "evals" / "queries.csv").open(encoding="utf-8")))


def test_evaluation_set_shape():
    assert len(ROWS) == 50
    assert Counter(r["intent"] for r in ROWS) == {"find": 30, "emergency": 8, "explain": 6, "out_of_scope": 6}


def test_every_emergency_is_caught_without_the_llm():
    missed = [r["question"] for r in ROWS if r["intent"] == "emergency" and not is_emergency(r["question"])]
    assert missed == []


def test_no_false_alarms_on_the_evaluation_set():
    flagged = [r["question"] for r in ROWS if r["intent"] != "emergency" and is_emergency(r["question"])]
    assert flagged == []


def test_expected_filters_are_valid():
    for r in ROWS:
        FacilitySearch(
            intent=r["intent"],
            facility_type=r["facility_type"] or None,
            city=r["city"] or None,
            pincode=r["pincode"] or None,
            ownership=r["ownership"] or None,
            emergency_only=r["emergency_only"] == "true",
        )
