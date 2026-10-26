"""Settings, read from environment variables (.env locally, platform secrets when hosted)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:dev@localhost:5432/facilities")
GROQ_MODEL = os.getenv("GROQ_MODEL", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip()
API_KEY = os.getenv("API_KEY", "").strip()
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "").strip()

USER_AGENT = f"healthcare-facility-finder/0.1 ({CONTACT_EMAIL or 'no-contact-set'})"

CHROMA_DIR = Path(os.getenv("CHROMA_DIR", ROOT / "data" / "chroma"))
COLLECTION = "glossary"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

RAW_DIR = ROOT / "data" / "raw"
INTERIM_DIR = ROOT / "data" / "interim"
SCHEMA_FILE = ROOT / "sql" / "001_schema.sql"
QUALITY_REPORT = ROOT / "docs" / "data-quality.md"

MAX_QUESTION_CHARS = 300
MAX_RESULTS = 20


class ConfigError(RuntimeError):
    """Raised when a required setting is missing."""


def require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing setting {name}. Add it to .env (local) or the platform's secrets (hosted).")
    return value
