"""Score filter extraction and safety on evals/queries.csv with LangSmith.

    uv run python evals/run_eval.py

Needs GROQ_API_KEY, GROQ_MODEL and LANGSMITH_API_KEY in .env. One LLM call per question (50 calls).
"""

import csv
from pathlib import Path

from langsmith import Client, evaluate

from facility_finder.agent.llm import extractor
from facility_finder.agent.safety import is_emergency
from facility_finder.pipeline.clean import normalize_city

HERE = Path(__file__).parent
DATASET = "facility-finder-queries"
FIELDS = ["facility_type", "city", "pincode", "ownership"]


def ensure_dataset(client: Client) -> None:
    if client.has_dataset(dataset_name=DATASET):
        return
    rows = list(csv.DictReader((HERE / "queries.csv").open(encoding="utf-8")))
    ds = client.create_dataset(DATASET, description="Facility-search questions with expected filters")
    client.create_examples(
        dataset_id=ds.id,
        inputs=[{"question": r["question"]} for r in rows],
        outputs=[{k: v for k, v in r.items() if k != "question"} for r in rows],
    )


def target(inputs: dict) -> dict:
    """Same logic as the agent: code safety check first, then LLM extraction."""
    question = inputs["question"]
    f = extractor().invoke({"question": question}).model_dump()
    if is_emergency(question):
        f.update(intent="emergency", facility_type="hospital", emergency_only=True)
    return f


def _norm(field: str, value) -> str:
    if value in (None, ""):
        return ""
    if field == "city":
        return (normalize_city(value) or "").lower().replace("new delhi", "delhi")
    return str(value).lower()


def intent_correct(outputs: dict, reference_outputs: dict) -> dict:
    return {"key": "intent_correct", "score": outputs["intent"] == reference_outputs["intent"]}


def filters_correct(outputs: dict, reference_outputs: dict) -> dict:
    if reference_outputs["intent"] not in ("find", "emergency"):
        return {"key": "filters_correct", "score": None}
    wrong = [f for f in FIELDS if _norm(f, outputs.get(f)) != _norm(f, reference_outputs.get(f))]
    expected_emergency = reference_outputs["emergency_only"] == "true"
    if bool(outputs.get("emergency_only")) != expected_emergency:
        wrong.append("emergency_only")
    return {"key": "filters_correct", "score": not wrong, "comment": ", ".join(wrong) or "all correct"}


def emergency_recall(outputs: dict, reference_outputs: dict) -> dict:
    if reference_outputs["intent"] != "emergency":
        return {"key": "emergency_recall", "score": None}
    return {"key": "emergency_recall", "score": outputs["intent"] == "emergency"}


def no_medical_advice(outputs: dict, reference_outputs: dict) -> dict:
    if reference_outputs["intent"] != "out_of_scope":
        return {"key": "no_medical_advice", "score": None}
    return {"key": "no_medical_advice", "score": outputs["intent"] == "out_of_scope"}


if __name__ == "__main__":
    client = Client()
    ensure_dataset(client)
    evaluate(
        target,
        data=DATASET,
        evaluators=[intent_correct, filters_correct, emergency_recall, no_medical_advice],
        experiment_prefix="extraction",
        max_concurrency=1,  # gentle on free-tier rate limits
    )
