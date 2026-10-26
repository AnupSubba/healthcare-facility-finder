# 🏥 Healthcare Facility Finder

**Find hospitals, clinics and labs across India in plain English or Hindi. Free, no sign-up.**

Live demo: _add your link after deployment_

> 🚨 In an emergency, call **112** (all emergencies) or **108** (ambulance).
> This app gives information only, not medical advice.

## Why I built it

Finding the right nearby hospital, clinic or lab in India means searching across government portals, maps and
private apps, which is hard for people who aren't comfortable with technology. I wanted one simple search that
understands everyday questions like *"Lucknow mein sarkari aspatal"*, and is honest about where its information
comes from.

## How it works

```
Question ─▶ Safety check ─▶ Filter extraction ─▶ Search ─────────▶ Results + map
            (plain code)    (LLM → Pydantic)     (PostGIS, SQL      (phone, directions,
             112 / 108                            built by code)      source, date)

Offline, monthly:  OpenStreetMap + data.gov.in ─▶ clean (Pandas) ─▶ de-duplicate (RapidFuzz + distance)
                   ─▶ geocode gaps (Nominatim) ─▶ PostGIS
```

Two rules keep it safe and trustworthy:

1. **Emergencies are detected in plain code before any AI runs** (`agent/safety.py`), so "chest pain" always shows
   112 / 108, even if the LLM is down.
2. **The LLM only extracts search filters.** Code builds the SQL with bound parameters, and every listing comes straight
   from the database, so the AI can never invent a hospital, address or phone number.

Design decisions are in [`docs/adr/`](docs/adr).

| Part | Tech |
|------|------|
| Data pipeline | Pandas, RapidFuzz, geopy (Nominatim), Overpass API |
| Database | PostgreSQL + PostGIS (Neon free tier) |
| Agent | LangGraph: safety → extract → search / ask for location / explain / decline |
| LLM | Groq (Gemini fallback), structured output with Pydantic |
| API | FastAPI, slowapi rate limits, API key between UI and API |
| Glossary | RAG over 12 knowledge cards (Chroma + fastembed) |
| MCP | `find_facilities` tool for Claude Desktop and other MCP clients |
| UI | Streamlit, English and Hindi |
| Quality | pytest (with a real PostGIS database), ruff, LangSmith evaluation, GitLab CI |

## Results

| Metric | Value |
|--------|-------|
| Facilities | _see [docs/data-quality.md](docs/data-quality.md)_ |
| Emergency recall (code check, 8 cases) | 100%, enforced in CI |
| Intent / filter accuracy (50 questions) | _run `evals/run_eval.py` and record it here_ |

## Run locally

Requires Python 3.12, [uv](https://docs.astral.sh/uv/) and Docker (for the local database).

```bash
uv sync
cp .env.example .env                                     # add Groq, LangSmith keys and CONTACT_EMAIL
docker compose up -d db                                  # PostgreSQL + PostGIS on localhost:5432
uv run python -m facility_finder.db                      # create tables
uv run python -m facility_finder.pipeline.run --states IN-DL   # load Delhi from OpenStreetMap
uv run python scripts/ingest_glossary.py                 # build the glossary index
uv run uvicorn facility_finder.api.main:app --reload     # API on http://localhost:8000/docs
uv run streamlit run ui/app.py                           # UI on http://localhost:8501
```

Add a data.gov.in CSV with `--data-gov "path/to/file.csv=Dataset title"` (check detected columns first with
`--show-columns`), and fill in missing coordinates with `--geocode 200`.

### MCP server

```bash
npx @modelcontextprotocol/inspector uv run python -m facility_finder.mcp_server
```

For Claude Desktop, add to `claude_desktop_config.json`:

```json
{ "mcpServers": { "facility-finder": {
    "command": "uv",
    "args": ["--directory", "/absolute/path/to/healthcare-facility-finder", "run", "python", "-m", "facility_finder.mcp_server"],
    "env": { "DATABASE_URL": "postgresql+psycopg://..." } } } }
```

## Development

```bash
uv run pre-commit install
uv run pytest                                            # database tests need TEST_DATABASE_URL (a separate database)
uv run ruff check . && uv run ruff format --check .
uv run python evals/run_eval.py                          # LangSmith evaluation (50 LLM calls)
uv export --format requirements-txt --no-hashes --no-dev --no-header -o requirements.txt   # after dependency changes
```

Workflow: protected `main`, one branch and merge request per change, [Conventional Commits](https://www.conventionalcommits.org/),
[Semantic Versioning](https://semver.org/) with tags and [CHANGELOG.md](CHANGELOG.md).

## Data and licences

Data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL) and data.gov.in
(Government Open Data License - India). See [`docs/data-sources.md`](docs/data-sources.md).

## Limitations

- Open data can be incomplete or out of date: always call ahead.
- Not medical advice; no doctors, prices or bookings.
- Free hosting sleeps when idle, so the first search can take up to a minute.

## Roadmap

Accreditation filters (NABH / NABL / PM-JAY, after a terms check), lab-test explanations, "use my location",
better de-duplication across map-cell borders, and a Telegram bot.

## Licence

[MIT](LICENSE) © 2026 Anup Kumar Subba
