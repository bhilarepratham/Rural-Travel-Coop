-- Table layout for the hosted Postgres database (Neon).
-- Run this once in the Neon SQL Editor. It is safe to run again (IF NOT EXISTS).

-- Who sells the trips. is_partner = true means a co-op partner.
CREATE TABLE IF NOT EXISTS operators (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,
    mode         TEXT NOT NULL CHECK (mode IN ('Rail', 'Bus')),
    is_partner   BOOLEAN NOT NULL DEFAULT FALSE,
    booking_url  TEXT,
    notes        TEXT
);

-- Scheduled trips shown in search results.
-- source_url and last_updated make it clear where each row came from and how old it is.
CREATE TABLE IF NOT EXISTS trips (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    operator_id   INTEGER NOT NULL REFERENCES operators(id),
    origin        TEXT NOT NULL,
    destination   TEXT NOT NULL,
    depart_time   TEXT NOT NULL,          -- for example '08:15'
    arrive_time   TEXT NOT NULL,
    price         NUMERIC(8, 2) NOT NULL CHECK (price >= 0),
    days_running  TEXT,                   -- for example 'Daily' or 'Sat, Sun'
    season_start  DATE,
    season_end    DATE,
    booking_url   TEXT,                   -- link to this trip's booking page, if different from the operator's
    source_url    TEXT,
    last_updated  DATE NOT NULL DEFAULT CURRENT_DATE,
    is_sample     BOOLEAN NOT NULL DEFAULT FALSE,  -- true for made up demo rows
    is_active     BOOLEAN NOT NULL DEFAULT TRUE    -- false hides an old or replaced row without deleting it
);
-- For databases created before Week 9 Day 3 (safe to run again):
ALTER TABLE trips ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
CREATE INDEX IF NOT EXISTS trips_route_idx ON trips (lower(origin), lower(destination));

-- One row per press of "Continue to operator site".
CREATE TABLE IF NOT EXISTS clicks (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ref           TEXT NOT NULL,                       -- tracking code, for example 'coop-12'
    trip_id       INTEGER NOT NULL REFERENCES trips(id),
    riders        INTEGER NOT NULL DEFAULT 1 CHECK (riders >= 1),
    price_at_click NUMERIC(8, 2) NOT NULL,             -- price per rider when clicked
    confirmed     BOOLEAN NOT NULL DEFAULT FALSE,      -- partner says this became a ticket sale
    clicked_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmed_at  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS clicks_trip_idx ON clicks (trip_id);

-- Sign ups for the co-op. tier 1 = free, tier 2 = paid (interest only for now).
CREATE TABLE IF NOT EXISTS members (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    tier        INTEGER NOT NULL CHECK (tier IN (1, 2)),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Weekly numbers the partner reports during the pilot (used from Week 9 Day 4).
-- capture rate for a week = tagged_value / partner_sales_total.
CREATE TABLE IF NOT EXISTS partner_weekly_reports (
    id                  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    operator_id         INTEGER NOT NULL REFERENCES operators(id),
    week_start          DATE NOT NULL,
    route_label         TEXT NOT NULL,                 -- for example 'Anchorage to Seward'
    partner_sales_total NUMERIC(12, 2) NOT NULL,       -- partner's total ticket sales on these routes
    tagged_tickets      INTEGER NOT NULL DEFAULT 0,    -- tickets carrying our tracking code
    tagged_value        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (operator_id, week_start, route_label)
);
