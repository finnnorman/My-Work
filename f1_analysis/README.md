F1 Race Strategy Analyzer
Analyzes how tire strategy and pit stop timing impact race pace and finishing position. Uses a relational SQLite database built from real F1 timing data pulled via the FastF1 API, with Python and Pandas for analysis and charting.
Project Structure
f1_analysis/
├── data/
│   ├── f1.db                  <- SQLite database (auto-created on first run)
│   └── fastf1_cache/          <- FastF1 download cache (auto-created)
├── sql/
│   ├── schema.sql             <- Database schema (5 tables)
│   └── queries.sql            <- Analytical SQL queries
├── outputs/
│   └── Bahrain_Grand_Prix_2023/  <- Each race gets its own subfolder
│       ├── 01_race_trace.png
│       ├── 02_compound_boxplot.png
│       ├── 03_degradation_curve.png
│       ├── 04_strategy_vs_result.png
│       ├── 05_pit_timing_scatter.png
│       └── *.csv
├── seed_database.py           <- Downloads real F1 data and populates the DB
├── analysis.py                <- Pandas analysis and chart generation
├── requirements.txt
└── README.md
Setup
Install dependencies:
bashpip install fastf1 pandas matplotlib numpy
Seed the database (downloads real race data from the FastF1 API):
bashpython3 seed_database.py
The first run downloads around 50-100MB of timing data and caches it locally. Subsequent runs use the cache and are instant.
Run the analysis:
bashpython3 analysis.py
Charts and CSVs are saved to outputs/<race_name>/.
Changing the Race
Open seed_database.py and edit the two lines at the top:
pythonSEASON = 2023
ROUND  = 1
To find the round number for any race:
bashpython3 -c "import fastf1; sched = fastf1.get_event_schedule(2023); print(sched[['RoundNumber','EventName']].to_string(index=False))"
FastF1 has data from 2018 onwards.
Database Schema
Five tables connected by race_id and driver_id foreign keys:
TableKey columnsdriversdriver_id, full_name, teamracesrace_id, grand_prix, circuit, seasonrace_resultsfinish_position, grid_position, points, statuslap_timeslap_number, lap_time_ms, is_pit_lappit_stopsstop_number, lap, duration_ms, tire_compoundtire_stintscompound, start_lap, end_lap
Analyses
Five charts are generated per race:

Race trace — lap-by-lap times for all drivers coloured by team
Compound boxplot — lap time distribution per tire compound
Degradation curve — average time loss per lap within a stint, by compound
Strategy vs result — finishing position grouped by pit stop strategy
Pit timing scatter — pit lap vs positions gained, bubble sized by stop duration

Four CSV exports are also written: compound_pace_summary, degradation_curve, pit_stop_analysis, strategy_vs_result.
The SQL queries in sql/queries.sql cover compound pace per driver, position delta at each pit stop, lap-by-lap degradation within a stint, 1-stop vs 2-stop outcome comparison, and undercut effectiveness.
VSCode Tips
Install the SQLite Viewer extension to browse data/f1.db directly in the editor without any external tools. Click the file in the explorer and it opens as a browsable table view.
