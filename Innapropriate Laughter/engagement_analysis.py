"""
Social Media Engagement Analysis
Inappropriate Laughter Inc — Summer 2025

Analyzes audience engagement across YouTube, Instagram, and TikTok
to identify content performance trends and inform posting strategy.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np
import os

# ── Output directory ──────────────────────────────────────────────────────────
os.makedirs("outputs", exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "figure.dpi": 150,
})

COLORS = {
    "YouTube": "#FF0000",
    "Instagram": "#C13584",
    "TikTok": "#000000",
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

yt  = pd.read_csv("data/youtube_analytics.csv",   parse_dates=["date"])
ig  = pd.read_csv("data/instagram_analytics.csv", parse_dates=["date"])
tt  = pd.read_csv("data/tiktok_analytics.csv",    parse_dates=["date"])

print("✓ Data loaded")
print(f"  YouTube:   {len(yt)} rows")
print(f"  Instagram: {len(ig)} rows")
print(f"  TikTok:    {len(tt)} rows\n")

# ─────────────────────────────────────────────────────────────────────────────
# 2. ENGAGEMENT RATE  =  (likes + comments + shares) / views * 100
# ─────────────────────────────────────────────────────────────────────────────

for df, name in [(yt, "YouTube"), (ig, "Instagram"), (tt, "TikTok")]:
    df["platform"]        = name
    df["engagement_rate"] = (df["likes"] + df["comments"] + df["shares"]) / df["views"] * 100

combined = pd.concat([yt, ig, tt], ignore_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. WEEKLY AGGREGATION
# ─────────────────────────────────────────────────────────────────────────────

combined["week"] = combined["date"].dt.to_period("W").apply(lambda r: r.start_time)

weekly = (combined
    .groupby(["week", "platform"])
    .agg(
        total_views        = ("views",           "sum"),
        total_likes        = ("likes",            "sum"),
        total_comments     = ("comments",         "sum"),
        total_shares       = ("shares",           "sum"),
        avg_engagement     = ("engagement_rate",  "mean"),
        posts              = ("views",            "count"),
        avg_watch_pct      = ("watch_pct",        "mean"),
    )
    .reset_index()
)

print("── Weekly Summary (last 4 weeks) ────────────────────────────────────")
recent = weekly[weekly["week"] >= weekly["week"].max() - pd.Timedelta(weeks=3)]
print(recent[["week","platform","total_views","avg_engagement","posts"]].to_string(index=False))
print()

# ─────────────────────────────────────────────────────────────────────────────
# 4. PLOT 1 — Weekly Views by Platform
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(10, 4.5))
for platform, grp in weekly.groupby("platform"):
    ax.plot(grp["week"], grp["total_views"] / 1000,
            label=platform, color=COLORS[platform], linewidth=2, marker="o", markersize=4)

ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
plt.xticks(rotation=30, ha="right")
ax.set_title("Weekly Views by Platform", fontsize=14, fontweight="bold", pad=12)
ax.set_ylabel("Views (thousands)")
ax.set_xlabel("")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig("outputs/01_weekly_views.png")
plt.close()
print("✓ Chart 1: Weekly views saved")

# ─────────────────────────────────────────────────────────────────────────────
# 5. PLOT 2 — Avg Engagement Rate by Platform
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(10, 4.5))
for platform, grp in weekly.groupby("platform"):
    ax.plot(grp["week"], grp["avg_engagement"],
            label=platform, color=COLORS[platform], linewidth=2, marker="s", markersize=4)

ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
plt.xticks(rotation=30, ha="right")
ax.set_title("Average Engagement Rate by Platform (%)", fontsize=14, fontweight="bold", pad=12)
ax.set_ylabel("Engagement Rate (%)")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig("outputs/02_engagement_rate.png")
plt.close()
print("✓ Chart 2: Engagement rate saved")

# ─────────────────────────────────────────────────────────────────────────────
# 6. PLOT 3 — Content Type Performance (bar chart)
# ─────────────────────────────────────────────────────────────────────────────

type_perf = (combined
    .groupby(["platform", "content_type"])
    .agg(avg_engagement=("engagement_rate", "mean"),
         avg_views=("views", "mean"))
    .reset_index()
)

platforms = ["YouTube", "Instagram", "TikTok"]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=False)

for ax, platform in zip(axes, platforms):
    data = type_perf[type_perf["platform"] == platform].sort_values("avg_engagement", ascending=True)
    bars = ax.barh(data["content_type"], data["avg_engagement"],
                   color=COLORS[platform], alpha=0.8)
    ax.set_title(platform, fontweight="bold", color=COLORS[platform])
    ax.set_xlabel("Avg Engagement Rate (%)")
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.05, bar.get_y() + bar.get_height()/2,
                f"{w:.1f}%", va="center", fontsize=8)

fig.suptitle("Engagement Rate by Content Type", fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("outputs/03_content_type_performance.png", bbox_inches="tight")
plt.close()
print("✓ Chart 3: Content type performance saved")

# ─────────────────────────────────────────────────────────────────────────────
# 7. PLOT 4 — Posting Day vs Engagement Heatmap
# ─────────────────────────────────────────────────────────────────────────────

combined["day_of_week"] = combined["date"].dt.day_name()
DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

heatmap_data = (combined
    .groupby(["platform", "day_of_week"])["engagement_rate"]
    .mean()
    .unstack("day_of_week")
    .reindex(columns=DAY_ORDER)
)

fig, ax = plt.subplots(figsize=(10, 3))
sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="YlOrRd",
            linewidths=0.5, ax=ax, cbar_kws={"label": "Avg Engagement Rate (%)"})
ax.set_title("Engagement Rate by Platform & Day of Week", fontsize=14, fontweight="bold", pad=12)
ax.set_ylabel("")
ax.set_xlabel("")
plt.tight_layout()
plt.savefig("outputs/04_posting_day_heatmap.png")
plt.close()
print("✓ Chart 4: Posting day heatmap saved")

# ─────────────────────────────────────────────────────────────────────────────
# 8. PLOT 5 — Follower Growth Over Time
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(10, 4.5))
for df, platform in [(yt, "YouTube"), (ig, "Instagram"), (tt, "TikTok")]:
    daily = df.groupby("date")["followers"].max().reset_index()
    ax.plot(daily["date"], daily["followers"],
            label=platform, color=COLORS[platform], linewidth=2)

ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
plt.xticks(rotation=30, ha="right")
ax.set_title("Follower Growth Over Time", fontsize=14, fontweight="bold", pad=12)
ax.set_ylabel("Total Followers")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig("outputs/05_follower_growth.png")
plt.close()
print("✓ Chart 5: Follower growth saved")

# ─────────────────────────────────────────────────────────────────────────────
# 9. SUMMARY STATS
# ─────────────────────────────────────────────────────────────────────────────

print("\n── Overall Summary ──────────────────────────────────────────────────")
summary = (combined
    .groupby("platform")
    .agg(
        total_views    = ("views",          "sum"),
        avg_eng_rate   = ("engagement_rate","mean"),
        total_posts    = ("views",          "count"),
        peak_followers = ("followers",      "max"),
    )
    .round(2)
)
print(summary.to_string())

# Best posting day per platform
print("\n── Best Posting Day by Platform ─────────────────────────────────────")
best_days = (combined
    .groupby(["platform","day_of_week"])["engagement_rate"]
    .mean()
    .reset_index()
    .sort_values("engagement_rate", ascending=False)
    .groupby("platform")
    .first()
    .reset_index()
[["platform","day_of_week","engagement_rate"]]
)
print(best_days.to_string(index=False))
print("\n✓ Analysis complete — charts saved to outputs/")
