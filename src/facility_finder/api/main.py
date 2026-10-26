"""FastAPI service used by the Streamlit UI (and anything else that wants to search).

uv run uvicorn facility_finder.api.main:app --reload      # docs at http://localhost:8000/docs
"""

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .. import __version__, config, repository
from ..agent import graph

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Healthcare Facility Finder API", version=__version__)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class Ask(BaseModel):
    question: str = Field(min_length=2, max_length=config.MAX_QUESTION_CHARS)
    lat: float | None = Field(default=None, ge=6, le=38)  # rough bounds of India
    lon: float | None = Field(default=None, ge=68, le=98)


class Report(BaseModel):
    facility_id: int
    issue: str = Field(min_length=3, max_length=500)


def check_key(x_api_key: str | None = Header(default=None)) -> None:
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}


@app.post("/ask", dependencies=[Depends(check_key)])
@limiter.limit("20/minute")
def ask(request: Request, body: Ask):
    try:
        return graph.ask(body.question, body.lat, body.lon)
    except Exception as err:  # database unreachable, missing settings...
        raise HTTPException(status_code=503, detail="Search is temporarily unavailable.") from err


@app.post("/reports", status_code=201, dependencies=[Depends(check_key)])
@limiter.limit("5/minute")
def report(request: Request, body: Report):
    repository.add_report(body.facility_id, body.issue)
    return {"status": "thanks"}
