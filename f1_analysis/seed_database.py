"""
seed_database.py  (fastf1 edition — fixed)
───────────────────────────────────────────
Pulls REAL F1 data from the FastF1 API and loads it into SQLite.

Install dependency first:
    pip install fastf1

Then run:
    python3 seed_database.py
"""

import sqlite3
import pathlib
import pandas as pd

try:
    import fastf1
except ImportError:
    raise SystemExit("fastf1 not installed.\nRun: pip install fastf1")

# ── Config ───────────────────────────────────────────────────────────────────
SEASON = 2025
ROUND = 1  # 1 = Bahrain GP

DB_PATH = pathlib.Path("data/f1.db")
SCHEMA_PATH = pathlib.Path("sql/schema.sql")
CACHE_DIR = pathlib.Path("data/fastf1_cache")

COMPOUND_MAP = {
    "SOFT": "SOFT",
    "MEDIUM": "MEDIUM",
    "HARD": "HARD",
    "INTERMEDIATE": "INTER",
    "WET": "WET",
    "UNKNOWN": "HARD",
    "TEST_UNKNOWN": "HARD",
}

POINTS_TABLE = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}


# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────


def init_db(db_path: pathlib.Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = OFF")  # abbreviation mismatch guard
    con.executescript(SCHEMA_PATH.read_text())
    return con


def clear_db(con: sqlite3.Connection):
    for tbl in [
        "tire_stints",
        "pit_stops",
        "lap_times",
        "race_results",
        "races",
        "drivers",
    ]:
        con.execute(f"DELETE FROM {tbl}")
    con.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Session loading
# ─────────────────────────────────────────────────────────────────────────────


def load_session(season: int, rnd: int) -> "fastf1.core.Session":
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    session = fastf1.get_session(season, rnd, "R")
    print(f"  Loading {session.event['EventName']} {season}...")
    session.load(telemetry=False, weather=False, messages=False)
    return session


# ─────────────────────────────────────────────────────────────────────────────
# Build number → abbreviation map
# ─────────────────────────────────────────────────────────────────────────────


def build_num_to_abbr(session) -> dict:
    """
    session.results index = driver numbers ('1','44',...)
    session.laps['Driver'] = abbreviations ('VER','HAM',...)
    Build a mapping so we can join them.
    """
    mapping = {}
    for num, row in session.results.iterrows():
        abbr = row.get("Abbreviation", None)
        if pd.notna(abbr) and abbr:
            mapping[str(num)] = str(abbr).upper()
    return mapping  # e.g. {'1': 'VER', '44': 'HAM', ...}


# ─────────────────────────────────────────────────────────────────────────────
# Extraction
# ─────────────────────────────────────────────────────────────────────────────


def extract_drivers(session, num_to_abbr: dict) -> list[tuple]:
    rows = []
    for num, row in session.results.iterrows():
        abbr = num_to_abbr.get(str(num), str(num))
        full_name = str(row.get("FullName", abbr))
        team = str(row.get("TeamName", "Unknown"))
        nationality = str(row.get("CountryCode", ""))
        rows.append((abbr, full_name, abbr, team, nationality))
    return rows


def extract_race_meta(session) -> dict:
    ev = session.event
    return {
        "season": int(session.date.year),
        "round": int(ev.get("RoundNumber", 0)),
        "grand_prix": str(ev.get("EventName", "Unknown GP")),
        "circuit": str(ev.get("Location", "Unknown Circuit")),
        "race_date": session.date.strftime("%Y-%m-%d"),
        "total_laps": int(session.laps["LapNumber"].max()),
    }


def extract_race_results(session, race_id: int, num_to_abbr: dict) -> list[tuple]:
    rows = []
    for num, res in session.results.iterrows():
        abbr = num_to_abbr.get(str(num), str(num))
        grid = int(res.get("GridPosition", 0) or 0)
        finish = int(res.get("Position", 0) or 0)
        status = str(res.get("Status", "Unknown"))
        pts = float(POINTS_TABLE.get(finish, 0))

        driver_laps = session.laps.pick_drivers(abbr)
        total_ms = int(driver_laps["LapTime"].dropna().dt.total_seconds().sum() * 1000)
        rows.append((race_id, abbr, grid, finish, pts, status, total_ms))
    return rows


def extract_pit_stops(session, race_id: int) -> tuple[list[tuple], dict]:
    """Uses abbreviations (from laps) as driver_id throughout."""
    rows = []
    pit_lap_map = {}  # {(abbr, lap_number): True}

    for abbr in session.laps["Driver"].unique():
        driver_laps = session.laps.pick_drivers(abbr).sort_values("LapNumber")
        stints = sorted(driver_laps.groupby("Stint"), key=lambda x: x[0])

        stop_num = 0
        prev_end_lap = None

        for stint_num, stint_df in stints:
            stint_df = stint_df.sort_values("LapNumber")
            first_lap = int(stint_df["LapNumber"].iloc[0])

            if stint_num == 1:
                prev_end_lap = int(stint_df["LapNumber"].iloc[-1])
                continue

            stop_num += 1
            compound_raw = str(stint_df["Compound"].iloc[0]).upper()
            compound = COMPOUND_MAP.get(compound_raw, "HARD")

            # Pit duration via PitInTime / PitOutTime
            duration_ms = 25_000
            pit_in_row = driver_laps[driver_laps["LapNumber"] == prev_end_lap]
            pit_out_row = driver_laps[driver_laps["LapNumber"] == first_lap]

            if not pit_in_row.empty and not pit_out_row.empty:
                pit_in_val = pit_in_row["PitInTime"].values[0]
                pit_out_val = pit_out_row["PitOutTime"].values[0]
                if pd.notna(pit_in_val) and pd.notna(pit_out_val):
                    duration_ms = max(
                        int((pit_out_val - pit_in_val) / 1_000_000), 18_000
                    )

            rows.append((race_id, abbr, stop_num, first_lap, duration_ms, compound))
            pit_lap_map[(abbr, first_lap)] = True
            prev_end_lap = int(stint_df["LapNumber"].iloc[-1])

    return rows, pit_lap_map


def extract_lap_times(session, race_id: int, pit_lap_map: dict) -> list[tuple]:
    rows = []
    laps = session.laps[["Driver", "LapNumber", "LapTime", "Position"]].copy()
    laps = laps.dropna(subset=["LapTime"])

    for _, row in laps.iterrows():
        abbr = row["Driver"]
        lap_num = int(row["LapNumber"])
        lap_ms = int(row["LapTime"].total_seconds() * 1000)
        pos = int(row["Position"]) if pd.notna(row["Position"]) else 0
        is_pit = 1 if (abbr, lap_num) in pit_lap_map else 0
        rows.append((race_id, abbr, lap_num, lap_ms, pos, is_pit))
    return rows


def extract_tire_stints(session, race_id: int) -> list[tuple]:
    rows = []
    for abbr in session.laps["Driver"].unique():
        driver_laps = session.laps.pick_drivers(abbr).sort_values("LapNumber")
        for stint_num, stint_df in sorted(
            driver_laps.groupby("Stint"), key=lambda x: x[0]
        ):
            stint_df = stint_df.sort_values("LapNumber")
            compound_raw = str(stint_df["Compound"].iloc[0]).upper()
            compound = COMPOUND_MAP.get(compound_raw, "HARD")
            start_lap = int(stint_df["LapNumber"].iloc[0])
            end_lap = int(stint_df["LapNumber"].iloc[-1])
            rows.append((race_id, abbr, int(stint_num), compound, start_lap, end_lap))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def seed_race(con: sqlite3.Connection, season: int, rnd: int):
    session = load_session(season, rnd)
    num_to_abbr = build_num_to_abbr(session)

    # Race metadata
    meta = extract_race_meta(session)
    con.execute(
        "INSERT INTO races (season,round,grand_prix,circuit,race_date,total_laps) "
        "VALUES (:season,:round,:grand_prix,:circuit,:race_date,:total_laps)",
        meta,
    )
    race_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"  ✔ Race     : {meta['grand_prix']} {season} (id={race_id})")

    # Drivers
    driver_rows = extract_drivers(session, num_to_abbr)
    con.executemany(
        "INSERT OR IGNORE INTO drivers "
        "(driver_id,full_name,abbreviation,team,nationality) VALUES (?,?,?,?,?)",
        driver_rows,
    )
    print(f"  ✔ Drivers  : {len(driver_rows)}")

    # Pit stops
    pit_rows, pit_lap_map = extract_pit_stops(session, race_id)
    con.executemany(
        "INSERT INTO pit_stops "
        "(race_id,driver_id,stop_number,lap,duration_ms,tire_compound) "
        "VALUES (?,?,?,?,?,?)",
        pit_rows,
    )
    print(f"  ✔ Pit stops: {len(pit_rows)}")

    # Lap times
    lap_rows = extract_lap_times(session, race_id, pit_lap_map)
    con.executemany(
        "INSERT INTO lap_times "
        "(race_id,driver_id,lap_number,lap_time_ms,position,is_pit_lap) "
        "VALUES (?,?,?,?,?,?)",
        lap_rows,
    )
    print(f"  ✔ Lap times: {len(lap_rows)}")

    # Tire stints
    stint_rows = extract_tire_stints(session, race_id)
    con.executemany(
        "INSERT INTO tire_stints "
        "(race_id,driver_id,stint_number,compound,start_lap,end_lap) "
        "VALUES (?,?,?,?,?,?)",
        stint_rows,
    )
    print(f"  ✔ Stints   : {len(stint_rows)}")

    # Race results
    result_rows = extract_race_results(session, race_id, num_to_abbr)
    con.executemany(
        "INSERT INTO race_results "
        "(race_id,driver_id,grid_position,finish_position,points,status,total_race_time_ms) "
        "VALUES (?,?,?,?,?,?,?)",
        result_rows,
    )
    print(f"  ✔ Results  : {len(result_rows)}")

    con.commit()
    print(f"\n✅  Done — {meta['grand_prix']} {season} loaded into {DB_PATH}")


if __name__ == "__main__":
    con = init_db(DB_PATH)
    clear_db(con)
    seed_race(con, SEASON, ROUND)
    con.close()
    print("    Now run: python3 analysis.py")
