-- Healthcare Facility Finder schema (PostgreSQL 14+ with PostGIS)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS facility (
  id         BIGSERIAL PRIMARY KEY,
  name       TEXT NOT NULL,
  type       TEXT NOT NULL CHECK (type IN ('hospital', 'clinic', 'lab')),
  ownership  TEXT NOT NULL DEFAULT 'unknown'
             CHECK (ownership IN ('government', 'private', 'unknown')),
  address    TEXT,
  city       TEXT,
  district   TEXT,
  state      TEXT,
  pincode    CHAR(6),
  phone      TEXT,
  website    TEXT,
  emergency  BOOLEAN,
  geom       GEOGRAPHY(POINT, 4326),
  sources    JSONB NOT NULL,           -- [{"source": "osm", "id": "node/123", "url": "..."}]
  updated_on DATE NOT NULL DEFAULT CURRENT_DATE
);
CREATE INDEX IF NOT EXISTS facility_geom_idx  ON facility USING GIST (geom);
CREATE INDEX IF NOT EXISTS facility_name_trgm ON facility USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS facility_city_type ON facility (lower(city), type);
CREATE INDEX IF NOT EXISTS facility_pincode   ON facility (pincode);

-- "Report incorrect info". No personal data: just the facility and a short description.
-- facility_name is kept so reports stay readable after the monthly reload replaces facility ids.
CREATE TABLE IF NOT EXISTS report (
  id            BIGSERIAL PRIMARY KEY,
  facility_id   BIGINT REFERENCES facility(id) ON DELETE SET NULL,
  facility_name TEXT,
  issue         TEXT NOT NULL CHECK (length(issue) <= 500),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
