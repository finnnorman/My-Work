"""
generate_data.py
Generates realistic mock social media analytics CSVs for
YouTube, Instagram, and TikTok (June–August 2025).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)
os.makedirs("data", exist_ok=True)

START = datetime(2025, 6, 1)
END = datetime(2025, 8, 31)
DATES = [START + timedelta(days=i) for i in range((END - START).days + 1)]

# Patreon/Substack launch mid-July — boosts revenue & follower growth
LAUNCH_DATE = datetime(2025, 7, 14)


def launch_boost(date, scale=1.0):
    """Gradual multiplier that kicks in after the Patreon/Substack launch."""
    if date < LAUNCH_DATE:
        return 1.0
    days_since = (date - LAUNCH_DATE).days
    return 1.0 + scale * min(days_since / 45, 1.0)


# ── YouTube ───────────────────────────────────────────────────────────────────
yt_content_types = [
    "Long-form Comedy",
    "Clip/Highlight",
    "Behind the Scenes",
    "Interview",
]
yt_type_weights = [0.35, 0.40, 0.15, 0.10]
yt_type_eng_boost = {
    "Long-form Comedy": 1.0,
    "Clip/Highlight": 1.3,
    "Behind the Scenes": 0.9,
    "Interview": 1.1,
}

# Post 3–5x per week
yt_rows = []
followers = 18_000
for date in DATES:
    if date.weekday() in [1, 3, 5] or (date.weekday() == 0 and np.random.rand() > 0.4):
        n_posts = np.random.randint(1, 3)
        boost = launch_boost(date, scale=0.4)
        followers = int(followers * (1 + np.random.uniform(0.001, 0.006) * boost))
        for _ in range(n_posts):
            ctype = np.random.choice(yt_content_types, p=yt_type_weights)
            views = int(
                np.random.normal(12000, 3500) * boost * yt_type_eng_boost[ctype]
            )
            views = max(views, 800)
            eng = yt_type_eng_boost[ctype]
            likes = int(views * np.random.uniform(0.04, 0.09) * eng)
            comments = int(views * np.random.uniform(0.005, 0.015) * eng)
            shares = int(views * np.random.uniform(0.002, 0.008) * eng)
            watch_pct = round(np.random.uniform(35, 68), 1)
            ctr = round(np.random.uniform(3.5, 8.5), 2)
            yt_rows.append(
                {
                    "date": date,
                    "content_type": ctype,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "watch_pct": watch_pct,
                    "ctr": ctr,
                    "followers": followers,
                }
            )

yt_df = pd.DataFrame(yt_rows)
yt_df.to_csv("data/youtube_analytics.csv", index=False)
print(f"✓ YouTube:   {len(yt_df)} rows, {yt_df['views'].sum():,} total views")

# ── Instagram ─────────────────────────────────────────────────────────────────
ig_content_types = ["Reel", "Carousel", "Static Post", "Story"]
ig_type_weights = [0.45, 0.25, 0.20, 0.10]
ig_type_eng_boost = {"Reel": 1.4, "Carousel": 1.2, "Static Post": 0.8, "Story": 0.6}

ig_rows = []
followers = 9_500
for date in DATES:
    if date.weekday() in [0, 2, 4, 6] or np.random.rand() > 0.3:
        n_posts = np.random.randint(1, 3)
        boost = launch_boost(date, scale=0.5)
        followers = int(followers * (1 + np.random.uniform(0.002, 0.008) * boost))
        for _ in range(n_posts):
            ctype = np.random.choice(ig_content_types, p=ig_type_weights)
            views = int(np.random.normal(5500, 1800) * boost * ig_type_eng_boost[ctype])
            views = max(views, 300)
            eng = ig_type_eng_boost[ctype]
            likes = int(views * np.random.uniform(0.06, 0.14) * eng)
            comments = int(views * np.random.uniform(0.008, 0.02) * eng)
            shares = int(views * np.random.uniform(0.01, 0.03) * eng)
            watch_pct = round(np.random.uniform(40, 75), 1)
            ctr = round(np.random.uniform(2.0, 6.0), 2)
            ig_rows.append(
                {
                    "date": date,
                    "content_type": ctype,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "watch_pct": watch_pct,
                    "ctr": ctr,
                    "followers": followers,
                }
            )

ig_df = pd.DataFrame(ig_rows)
ig_df.to_csv("data/instagram_analytics.csv", index=False)
print(f"✓ Instagram: {len(ig_df)} rows, {ig_df['views'].sum():,} total views")

# ── TikTok ────────────────────────────────────────────────────────────────────
tt_content_types = ["Comedy Clip", "Trending Audio", "Talking Head", "Collab"]
tt_type_weights = [0.40, 0.30, 0.20, 0.10]
tt_type_eng_boost = {
    "Comedy Clip": 1.3,
    "Trending Audio": 1.5,
    "Talking Head": 0.9,
    "Collab": 1.6,
}

tt_rows = []
followers = 22_000
for date in DATES:
    n_posts = np.random.randint(1, 4)
    boost = launch_boost(date, scale=0.6)
    followers = int(followers * (1 + np.random.uniform(0.003, 0.01) * boost))
    for _ in range(n_posts):
        ctype = np.random.choice(tt_content_types, p=tt_type_weights)
        # TikTok has occasional viral spikes
        viral = 8 if np.random.rand() > 0.97 else 1
        views = int(
            np.random.normal(18000, 7000) * boost * tt_type_eng_boost[ctype] * viral
        )
        views = max(views, 500)
        eng = tt_type_eng_boost[ctype]
        likes = int(views * np.random.uniform(0.05, 0.12) * eng)
        comments = int(views * np.random.uniform(0.006, 0.018) * eng)
        shares = int(views * np.random.uniform(0.008, 0.025) * eng)
        watch_pct = round(np.random.uniform(30, 65), 1)
        ctr = round(np.random.uniform(4.0, 10.0), 2)
        tt_rows.append(
            {
                "date": date,
                "content_type": ctype,
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "watch_pct": watch_pct,
                "ctr": ctr,
                "followers": followers,
            }
        )

tt_df = pd.DataFrame(tt_rows)
tt_df.to_csv("data/tiktok_analytics.csv", index=False)
print(f"✓ TikTok:    {len(tt_df)} rows, {tt_df['views'].sum():,} total views")
print("\n✓ All data written to data/")
