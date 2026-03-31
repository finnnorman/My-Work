"""
predict_performance.py
Uses a Random Forest model to predict content engagement rate
based on platform, content type, and posting day.

Trained on historical engagement data from June–August 2025.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score

os.makedirs("outputs", exist_ok=True)

COLORS = {
    "YouTube": "#FF0000",
    "Instagram": "#C13584",
    "TikTok": "#000000",
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD & PREPARE DATA
# ─────────────────────────────────────────────────────────────────────────────

yt = pd.read_csv("data/youtube_analytics.csv",   parse_dates=["date"])
ig = pd.read_csv("data/instagram_analytics.csv", parse_dates=["date"])
tt = pd.read_csv("data/tiktok_analytics.csv",    parse_dates=["date"])

for df, name in [(yt, "YouTube"), (ig, "Instagram"), (tt, "TikTok")]:
    df["platform"] = name

combined = pd.concat([yt, ig, tt], ignore_index=True)
combined["engagement_rate"] = (
    (combined["likes"] + combined["comments"] + combined["shares"])
    / combined["views"] * 100
)
combined["day_of_week"] = combined["date"].dt.day_name()

print(f"✓ Loaded {len(combined)} posts across 3 platforms\n")

# ─────────────────────────────────────────────────────────────────────────────
# 2. ENCODE FEATURES
# ─────────────────────────────────────────────────────────────────────────────

le_platform = LabelEncoder()
le_content  = LabelEncoder()
le_day      = LabelEncoder()

combined["platform_enc"]     = le_platform.fit_transform(combined["platform"])
combined["content_type_enc"] = le_content.fit_transform(combined["content_type"])
combined["day_enc"]          = le_day.fit_transform(combined["day_of_week"])

FEATURES = ["platform_enc", "content_type_enc", "day_enc", "watch_pct", "ctr"]
TARGET   = "engagement_rate"

X = combined[FEATURES]
y = combined[TARGET]

# ─────────────────────────────────────────────────────────────────────────────
# 3. TRAIN / TEST SPLIT & MODEL
# ─────────────────────────────────────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae    = mean_absolute_error(y_test, y_pred)
r2     = r2_score(y_test, y_pred)

print(f"── Model Performance ────────────────────────────────────────────────")
print(f"   MAE : {mae:.2f}%  (avg prediction error)")
print(f"   R²  : {r2:.3f}   (higher = better fit)\n")

# ─────────────────────────────────────────────────────────────────────────────
# 4. PREDICT ALL COMBINATIONS
# ─────────────────────────────────────────────────────────────────────────────

platforms     = ["YouTube", "Instagram", "TikTok"]
days          = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# Content types per platform
content_map = {
    "YouTube":   ["Long-form Comedy", "Clip/Highlight", "Behind the Scenes", "Interview"],
    "Instagram": ["Reel", "Carousel", "Static Post", "Story"],
    "TikTok":    ["Comedy Clip", "Trending Audio", "Talking Head", "Collab"],
}

# Use median watch_pct and ctr as baseline inputs
med_watch = combined["watch_pct"].median()
med_ctr   = combined["ctr"].median()

rows = []
for platform in platforms:
    for content_type in content_map[platform]:
        for day in days:
            rows.append({
                "platform":     platform,
                "content_type": content_type,
                "day_of_week":  day,
                "platform_enc":     le_platform.transform([platform])[0],
                "content_type_enc": le_content.transform([content_type])[0],
                "day_enc":          le_day.transform([day])[0],
                "watch_pct": med_watch,
                "ctr":       med_ctr,
            })

pred_df = pd.DataFrame(rows)
pred_df["predicted_engagement"] = model.predict(pred_df[FEATURES]).round(2)
pred_df = pred_df.sort_values("predicted_engagement", ascending=False)

# ─────────────────────────────────────────────────────────────────────────────
# 5. PRINT TOP RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

print("── Top 10 Predicted Content Combinations ────────────────────────────")
top10 = pred_df.head(10)[["platform","content_type","day_of_week","predicted_engagement"]]
print(top10.to_string(index=False))

print("\n── Best Combo Per Platform ──────────────────────────────────────────")
best = pred_df.groupby("platform").first().reset_index()
for _, row in best.iterrows():
    print(f"  {row['platform']:12s} → {row['content_type']:22s} on {row['day_of_week']:10s}  ({row['predicted_engagement']:.1f}% predicted engagement)")

# ─────────────────────────────────────────────────────────────────────────────
# 6. PLOT 1 — Predicted Engagement by Content Type & Day (heatmap per platform)
# ─────────────────────────────────────────────────────────────────────────────

DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

for ax, platform in zip(axes, platforms):
    data = pred_df[pred_df["platform"] == platform].copy()
    pivot = data.pivot_table(
        index="content_type", columns="day_of_week",
        values="predicted_engagement"
    ).reindex(columns=DAY_ORDER)

    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto",
                   vmin=pred_df["predicted_engagement"].min(),
                   vmax=pred_df["predicted_engagement"].max())

    ax.set_xticks(range(len(DAY_ORDER)))
    ax.set_xticklabels([d[:3] for d in DAY_ORDER], fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=8)
    ax.set_title(platform, fontweight="bold", color=COLORS[platform], fontsize=11)

    # Annotate cells
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    fontsize=7, color="black")

plt.colorbar(im, ax=axes[-1], label="Predicted Engagement Rate (%)", shrink=0.8)
fig.suptitle("Predicted Engagement Rate by Content Type & Day",
             fontsize=13, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("outputs/06_predicted_heatmap.png", bbox_inches="tight")
plt.close()
print("\n✓ Chart 6: Prediction heatmap saved")

# ─────────────────────────────────────────────────────────────────────────────
# 7. PLOT 2 — Feature Importance
# ─────────────────────────────────────────────────────────────────────────────

importances = model.feature_importances_
feat_names  = ["Platform", "Content Type", "Day of Week", "Watch %", "CTR"]
sorted_idx  = np.argsort(importances)

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.barh(
    [feat_names[i] for i in sorted_idx],
    importances[sorted_idx],
    color="#2c5f8a", alpha=0.85
)
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.005, bar.get_y() + bar.get_height()/2,
            f"{w:.3f}", va="center", fontsize=9)

ax.set_title("Feature Importance — What Drives Engagement?",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Importance Score")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig("outputs/07_feature_importance.png")
plt.close()
print("✓ Chart 7: Feature importance saved")

print("\n✓ Prediction complete — charts saved to outputs/")
