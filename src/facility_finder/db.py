"""Database engine and schema setup.

uv run python -m facility_finder.db      # create tables and extensions (safe to re-run)
"""

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from . import config


@lru_cache
def get_engine() -> Engine:
    # pool_pre_ping reconnects cleanly after Neon scales to zero.
    return create_engine(config.DATABASE_URL, pool_pre_ping=True)


def init_schema(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    sql = config.SCHEMA_FILE.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)


if __name__ == "__main__":
    init_schema()
    print("Schema ready.")
