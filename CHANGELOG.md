# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.0] - 2026-10-26
### Added
- MCP server with a `find_facilities` tool (MCP Python SDK 2.x).
- Streamlit UI in English and Hindi: emergency banner, results list and map, call and directions links,
  "Report incorrect info", friendly errors; UI smoke tests.
- Evaluation set of 50 questions, LangSmith evaluation script, and a CI test that every emergency is caught by code.
- `requirements.txt` for the API and `ui/requirements.txt` for the UI; monthly data refresh as a GitLab scheduled pipeline.

## [0.2.0] - 2026-10-26
### Added
- PostGIS search with bound parameters: type, ownership, emergency, city, pincode, name and distance filters.
- LangGraph agent: emergency check in code, LLM filter extraction (Groq, Gemini fallback), routing to search,
  ask-for-location, explain, decline and fallback; template answers in English and Hindi.
- Glossary: 12 knowledge cards, ingestion script and RAG explanations.
- FastAPI service with API key, rate limits and health check.

## [0.1.0] - 2026-10-26
### Added
- Project structure, pre-commit hooks, GitLab CI with a PostGIS service, local database with Docker Compose.
- Requirements, ADRs 0001–0006 and data-source notes.
- Database schema, configuration and Pydantic models.
- Data pipeline: OpenStreetMap and data.gov.in loaders, cleaning, de-duplication, geocoding, quality report, loading.
