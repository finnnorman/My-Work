-- ============================================================
-- F1 Race Analytics Database Schema
-- ============================================================

-- Drivers
CREATE TABLE IF NOT EXISTS drivers (
    driver_id       TEXT PRIMARY KEY,
    full_name       TEXT NOT NULL,
    abbreviation    TEXT NOT NULL,
    team            TEXT NOT NULL,
    nationality     TEXT
);

-- Races (Grands Prix)
CREATE TABLE IF NOT EXISTS races (
    race_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    season          INTEGER NOT NULL,
    round           INTEGER NOT NULL,
    grand_prix      TEXT NOT NULL,
    circuit         TEXT NOT NULL,
    race_date       TEXT NOT NULL,
    total_laps      INTEGER NOT NULL
);

-- Race Results (finishing positions)
CREATE TABLE IF NOT EXISTS race_results (
    result_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id         INTEGER NOT NULL REFERENCES races(race_id),
    driver_id       TEXT    NOT NULL REFERENCES drivers(driver_id),
    grid_position   INTEGER,
    finish_position INTEGER,
    points          REAL,
    status          TEXT,           -- 'Finished', 'DNF', 'DSQ', etc.
    total_race_time_ms INTEGER      -- milliseconds
);

-- Lap Times
CREATE TABLE IF NOT EXISTS lap_times (
    lap_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id         INTEGER NOT NULL REFERENCES races(race_id),
    driver_id       TEXT    NOT NULL REFERENCES drivers(driver_id),
    lap_number      INTEGER NOT NULL,
    lap_time_ms     INTEGER NOT NULL,   -- milliseconds
    position        INTEGER,
    is_pit_lap      INTEGER DEFAULT 0   -- boolean flag
);

-- Pit Stops
CREATE TABLE IF NOT EXISTS pit_stops (
    pit_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id         INTEGER NOT NULL REFERENCES races(race_id),
    driver_id       TEXT    NOT NULL REFERENCES drivers(driver_id),
    stop_number     INTEGER NOT NULL,   -- 1st stop, 2nd stop, etc.
    lap             INTEGER NOT NULL,
    duration_ms     INTEGER NOT NULL,   -- pit stop duration in ms
    tire_compound   TEXT NOT NULL       -- 'SOFT', 'MEDIUM', 'HARD', 'INTER', 'WET'
);

-- Tire Stints (derived: which compound on which laps)
CREATE TABLE IF NOT EXISTS tire_stints (
    stint_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id         INTEGER NOT NULL REFERENCES races(race_id),
    driver_id       TEXT    NOT NULL REFERENCES drivers(driver_id),
    stint_number    INTEGER NOT NULL,
    compound        TEXT    NOT NULL,
    start_lap       INTEGER NOT NULL,
    end_lap         INTEGER NOT NULL,
    laps_on_tire    INTEGER GENERATED ALWAYS AS (end_lap - start_lap + 1) VIRTUAL
);

-- ============================================================
-- Indexes for query performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_lap_times_race_driver  ON lap_times(race_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_pit_stops_race_driver  ON pit_stops(race_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_tire_stints_compound   ON tire_stints(compound);
CREATE INDEX IF NOT EXISTS idx_results_race           ON race_results(race_id, finish_position);
