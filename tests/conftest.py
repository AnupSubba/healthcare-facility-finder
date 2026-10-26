import json
import os
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def osm_elements():
    return json.loads((FIXTURES / "osm_sample.json").read_text())


@pytest.fixture
def data_gov_csv():
    return str(FIXTURES / "data_gov_sample.csv")


@pytest.fixture(scope="session")
def db_engine():
    """A real PostGIS database. Set TEST_DATABASE_URL to run these tests (CI does).

    Use a separate test database: the tests delete and reload the facility table.
    """
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    from sqlalchemy import create_engine

    from facility_finder.db import init_schema

    engine = create_engine(url, pool_pre_ping=True)
    init_schema(engine)
    return engine
