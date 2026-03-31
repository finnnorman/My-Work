"""
analysis.py
───────────
Core analysis module: loads F1 data from SQLite and uses Pandas
to investigate how tire strategy and pit timing impact race pace
and finishing position.

Run:
    python3 analysis.py
"""

import sqlite3
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import numpy as np

DB_PATH = pathlib.Path("data/f1.db")

COMPOUND_COLORS = {
    "SOFT": "#E8002D",
    "MEDIUM": "#FFF200",
    "HARD": "#FFFFFF",
    "INTER": "#39B54A",
    "WET": "#0067FF",
}
TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "Aston Martin": "#358C75",
    "Mercedes": "#27F4D2",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
}

# ─────────────────────────────────────────────────────────────────────────────
# Data loading helpers
# ─────────────────────────────────────────────────────────────────────────────


def get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def load_query(sql: str, params=(), con=None) -> pd.DataFrame:
    _con = con or get_connection()
    df = pd.read_sql_query(sql, _con, params=params)
    if con is None:
        _con.close()
    return df


def load_race_id(con) -> int:
    row = con.execute("SELECT race_id FROM races LIMIT 1").fetchone()
    return row["race_id"]


def get_race_label(con) -> str:
    row = con.execute("SELECT grand_prix, season FROM races LIMIT 1").fetchone()
    label = f"{row[0]} {row[1]}".replace(" ", "_")
    return label


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 1 — Lap-time distribution by tire compound
# ─────────────────────────────────────────────────────────────────────────────


def analysis_compound_pace(race_id: int, con) -> pd.DataFrame:
    sql = """
        SELECT
            ts.compound,
            d.full_name AS driver,
            d.team,
            lt.lap_number,
            lt.lap_time_ms / 1000.0 AS lap_time_sec
        FROM tire_stints ts
        JOIN lap_times lt ON lt.race_id    = ts.race_id
                          AND lt.driver_id  = ts.driver_id
                          AND lt.lap_number BETWEEN ts.start_lap AND ts.end_lap
                          AND lt.is_pit_lap = 0
        JOIN drivers d ON d.driver_id = ts.driver_id
        WHERE ts.race_id = ?
    """
    df = load_query(sql, (race_id,), con)

    summary = (
        df.groupby("compound")["lap_time_sec"]
        .agg(["mean", "median", "std", "min", "count"])
        .rename(
            columns={
                "mean": "avg_sec",
                "median": "median_sec",
                "std": "std_sec",
                "min": "best_sec",
                "count": "laps",
            }
        )
        .reset_index()
        .sort_values("avg_sec")
    )
    print("\n📊  Compound Pace Summary")
    print(summary.to_string(index=False))
    return df, summary


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 2 — Tire degradation curve per driver
# ─────────────────────────────────────────────────────────────────────────────


def analysis_degradation(race_id: int, con) -> pd.DataFrame:
    sql = """
        SELECT
            ts.compound,
            ts.stint_number,
            d.abbreviation AS driver,
            lt.lap_number,
            (lt.lap_number - ts.start_lap + 1) AS lap_in_stint,
            lt.lap_time_ms / 1000.0            AS lap_time_sec
        FROM tire_stints ts
        JOIN lap_times lt ON lt.race_id    = ts.race_id
                          AND lt.driver_id  = ts.driver_id
                          AND lt.lap_number BETWEEN ts.start_lap AND ts.end_lap
                          AND lt.is_pit_lap = 0
        JOIN drivers d ON d.driver_id = ts.driver_id
        WHERE ts.race_id = ?
    """
    df = load_query(sql, (race_id,), con)

    best_per_stint = (
        df.groupby(["driver", "compound", "stint_number"])["lap_time_sec"]
        .min()
        .rename("best_lap_sec")
        .reset_index()
    )
    df = df.merge(best_per_stint, on=["driver", "compound", "stint_number"])
    df["delta_sec"] = df["lap_time_sec"] - df["best_lap_sec"]

    deg_curve = (
        df.groupby(["compound", "lap_in_stint"])["delta_sec"].mean().reset_index()
    )
    return df, deg_curve


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 3 — Pit stop timing vs positions gained
# ─────────────────────────────────────────────────────────────────────────────


def analysis_pit_timing(race_id: int, con) -> pd.DataFrame:
    sql = """
        SELECT
            d.full_name    AS driver,
            d.team,
            ps.stop_number,
            ps.lap         AS pit_lap,
            ps.tire_compound AS new_compound,
            ps.duration_ms / 1000.0 AS pit_duration_sec,
            rr.grid_position,
            rr.finish_position,
            (rr.grid_position - rr.finish_position) AS positions_gained
        FROM pit_stops ps
        JOIN drivers d      ON d.driver_id  = ps.driver_id
        JOIN race_results rr ON rr.race_id   = ps.race_id
                             AND rr.driver_id = ps.driver_id
        WHERE ps.race_id = ?
        ORDER BY rr.finish_position, ps.stop_number
    """
    df = load_query(sql, (race_id,), con)
    print("\n📊  Pit Stop Summary")
    print(
        df[
            [
                "driver",
                "pit_lap",
                "new_compound",
                "pit_duration_sec",
                "finish_position",
                "positions_gained",
            ]
        ].to_string(index=False)
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Analysis 4 — Strategy comparison (1-stop vs 2-stop vs 3-stop)
# ─────────────────────────────────────────────────────────────────────────────


def analysis_strategy_vs_result(race_id: int, con) -> pd.DataFrame:
    sql = """
        SELECT
            d.full_name  AS driver,
            d.team,
            rr.finish_position,
            rr.points,
            COUNT(ps.pit_id) AS num_stops,
            GROUP_CONCAT(ps.tire_compound, '→') AS strategy_sequence
        FROM race_results rr
        JOIN drivers d ON d.driver_id = rr.driver_id
        LEFT JOIN pit_stops ps ON ps.race_id   = rr.race_id
                               AND ps.driver_id = rr.driver_id
        WHERE rr.race_id = ?
          AND rr.status  = 'Finished'
        GROUP BY rr.race_id, rr.driver_id
        ORDER BY rr.finish_position
    """
    df = load_query(sql, (race_id,), con)
    print("\n📊  Strategy vs Finishing Position")
    print(df.to_string(index=False))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Visualisation helpers
# ─────────────────────────────────────────────────────────────────────────────


def _f1_style(fig, axes=None):
    fig.patch.set_facecolor("#0F0F0F")
    for ax in axes or fig.axes:
        ax.set_facecolor("#1A1A1A")
        ax.tick_params(colors="#CCCCCC")
        ax.xaxis.label.set_color("#CCCCCC")
        ax.yaxis.label.set_color("#CCCCCC")
        ax.title.set_color("#FFFFFF")
        for spine in ax.spines.values():
            spine.set_color("#333333")


def plot_lap_times(lap_df: pd.DataFrame, race_name: str, out_dir: pathlib.Path):
    fig, ax = plt.subplots(figsize=(14, 7))
    _f1_style(fig, [ax])

    for driver, grp in lap_df.groupby("driver"):
        team = grp["team"].iloc[0]
        color = TEAM_COLORS.get(team, "#AAAAAA")
        ax.plot(
            grp["lap_number"],
            grp["lap_time_sec"],
            linewidth=1.2,
            color=color,
            alpha=0.85,
            label=f"{driver}",
        )

    ax.set_title(f"Race Trace — {race_name}", fontsize=14, pad=12)
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time (s)")
    ax.legend(
        fontsize=7, ncol=2, facecolor="#111111", labelcolor="#CCCCCC", framealpha=0.8
    )
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    plt.tight_layout()
    path = out_dir / "01_race_trace.png"
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → saved {path}")


def plot_compound_boxplot(lap_df: pd.DataFrame, out_dir: pathlib.Path):
    fig, ax = plt.subplots(figsize=(8, 6))
    _f1_style(fig, [ax])

    compounds = [
        c
        for c in ["SOFT", "MEDIUM", "HARD", "INTER", "WET"]
        if c in lap_df["compound"].values
    ]
    data = [lap_df[lap_df["compound"] == c]["lap_time_sec"].values for c in compounds]

    bp = ax.boxplot(
        data,
        patch_artist=True,
        medianprops=dict(color="white", linewidth=2),
        whiskerprops=dict(color="#888888"),
        capprops=dict(color="#888888"),
        flierprops=dict(
            marker="o", markerfacecolor="#555555", markersize=3, linestyle="none"
        ),
    )
    for patch, compound in zip(bp["boxes"], compounds):
        patch.set_facecolor(COMPOUND_COLORS.get(compound, "#AAAAAA"))
        patch.set_alpha(0.85)

    ax.set_xticklabels(compounds)
    ax.set_title("Lap Time Distribution by Tire Compound", fontsize=13)
    ax.set_ylabel("Lap Time (s)")
    plt.tight_layout()
    path = out_dir / "02_compound_boxplot.png"
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → saved {path}")


def plot_degradation(deg_curve: pd.DataFrame, out_dir: pathlib.Path):
    fig, ax = plt.subplots(figsize=(10, 6))
    _f1_style(fig, [ax])

    for compound, grp in deg_curve.groupby("compound"):
        color = COMPOUND_COLORS.get(compound, "#AAAAAA")
        ax.plot(
            grp["lap_in_stint"],
            grp["delta_sec"],
            color=color,
            linewidth=2.2,
            label=compound,
            marker="o",
            markersize=3,
        )

    ax.set_title("Tire Degradation Curve (avg Δ from best lap in stint)", fontsize=13)
    ax.set_xlabel("Lap in Stint")
    ax.set_ylabel("Δ vs Best Lap (s)")
    ax.legend(facecolor="#111111", labelcolor="#CCCCCC")
    ax.axhline(0, color="#555555", linewidth=0.8, linestyle="--")
    plt.tight_layout()
    path = out_dir / "03_degradation_curve.png"
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → saved {path}")


def plot_strategy_bars(strategy_df: pd.DataFrame, out_dir: pathlib.Path):
    fig, ax = plt.subplots(figsize=(10, 7))
    _f1_style(fig, [ax])

    strategy_df = strategy_df.sort_values("finish_position")
    colors = {1: "#E8002D", 2: "#FF8000", 3: "#3671C6"}

    for _, row in strategy_df.iterrows():
        c = colors.get(row["num_stops"], "#AAAAAA")
        ax.barh(
            row["driver"],
            row["finish_position"],
            color=c,
            alpha=0.85,
            edgecolor="#333333",
        )
        ax.text(
            row["finish_position"] + 0.1,
            row["driver"],
            f"P{int(row['finish_position'])} · {row['strategy_sequence']}",
            va="center",
            fontsize=8,
            color="#CCCCCC",
        )

    patches = [mpatches.Patch(color=colors[k], label=f"{k}-stop") for k in colors]
    ax.legend(handles=patches, facecolor="#111111", labelcolor="#CCCCCC")
    ax.set_xlabel("Finishing Position")
    ax.set_title("Finishing Position by Tire Strategy", fontsize=13)
    ax.invert_xaxis()
    plt.tight_layout()
    path = out_dir / "04_strategy_vs_result.png"
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → saved {path}")


def plot_pitstop_scatter(pit_df: pd.DataFrame, out_dir: pathlib.Path):
    fig, ax = plt.subplots(figsize=(10, 6))
    _f1_style(fig, [ax])

    for _, row in pit_df.iterrows():
        color = TEAM_COLORS.get(row["team"], "#AAAAAA")
        ax.scatter(
            row["pit_lap"],
            row["positions_gained"],
            s=row["pit_duration_sec"] * 8,
            color=color,
            alpha=0.75,
            edgecolors="#111111",
            linewidths=0.5,
        )
        ax.annotate(
            row["driver"].split()[-1],
            (row["pit_lap"], row["positions_gained"]),
            fontsize=7,
            color="#DDDDDD",
            xytext=(3, 3),
            textcoords="offset points",
        )

    ax.axhline(0, color="#555555", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Pit Stop Lap")
    ax.set_ylabel("Positions Gained vs Grid")
    ax.set_title(
        "Pit Stop Timing vs Race Outcome\n(bubble size ∝ stop duration)", fontsize=13
    )
    plt.tight_layout()
    path = out_dir / "05_pit_timing_scatter.png"
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    con = get_connection()
    race_id = load_race_id(con)

    # ── Set up race-specific output folder ───────────────────────────────────
    race_label = get_race_label(con)
    out_dir = pathlib.Path("outputs") / race_label
    out_dir.mkdir(parents=True, exist_ok=True)

    race_name = race_label.replace("_", " ")
    print(f"🏎️  F1 Race Strategy Analysis — {race_name}")
    print(f"    Saving outputs to: outputs/{race_label}/")
    print("=" * 52)

    # ── Run analyses ─────────────────────────────────────────────────────────
    lap_df, compound_summary = analysis_compound_pace(race_id, con)
    raw_deg, deg_curve = analysis_degradation(race_id, con)
    pit_df = analysis_pit_timing(race_id, con)
    strategy_df = analysis_strategy_vs_result(race_id, con)

    # ── Save CSV exports ─────────────────────────────────────────────────────
    compound_summary.to_csv(out_dir / "compound_pace_summary.csv", index=False)
    deg_curve.to_csv(out_dir / "degradation_curve.csv", index=False)
    pit_df.to_csv(out_dir / "pit_stop_analysis.csv", index=False)
    strategy_df.to_csv(out_dir / "strategy_vs_result.csv", index=False)
    print(f"\n💾  CSVs exported to outputs/{race_label}/")

    # ── Render plots ─────────────────────────────────────────────────────────
    print("\n🖼️  Generating charts…")
    plot_lap_times(lap_df, race_name, out_dir)
    plot_compound_boxplot(lap_df, out_dir)
    plot_degradation(deg_curve, out_dir)
    plot_strategy_bars(strategy_df, out_dir)
    plot_pitstop_scatter(pit_df, out_dir)

    # ── Key insights ─────────────────────────────────────────────────────────
    print("\n💡  Key Insights")
    print("-" * 40)
    best_compound = compound_summary.iloc[0]
    print(
        f"  Fastest compound  : {best_compound['compound']} "
        f"(avg {best_compound['avg_sec']:.2f}s/lap)"
    )

    two_stop = strategy_df[strategy_df["num_stops"] == 2]
    if not two_stop.empty:
        avg_pos = two_stop["finish_position"].mean()
        print(f"  2-stop avg finish : P{avg_pos:.1f}")

    early_pit = pit_df[pit_df["pit_lap"] <= 20]
    if not early_pit.empty:
        avg_gain = early_pit["positions_gained"].mean()
        print(f"  Early stop (≤lap20) avg positions gained: {avg_gain:+.1f}")

    con.close()
    print(f"\n✅  Analysis complete — outputs/{race_label}/")


if __name__ == "__main__":
    main()
