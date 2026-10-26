# ADR 0001: All-Python stack (FastAPI, LangGraph, Streamlit)
- Status: Accepted · Date: 2026-10-26

**Context:** one developer, free hosting, AI libraries are Python-first.
**Decision:** Python end to end: Pandas pipeline, FastAPI service, LangGraph agent, Streamlit UI, uv for packaging.
**Consequences:** one language and toolchain; the UI and API are deployed separately so the UI stays light.
