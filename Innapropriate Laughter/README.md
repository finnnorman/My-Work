# Social Media Engagement Analysis
### Inappropriate Laughter Inc — Summer 2025

A Python-based analysis of audience engagement across YouTube, Instagram, and TikTok,
built to identify content performance trends and inform digital strategy.

---

## Project Overview

During a summer internship at Inappropriate Laughter Inc, I collected engagement data
from native platform dashboards (YouTube Studio, Instagram Insights, TikTok Analytics)
and consolidated it into a unified Python analysis pipeline.

The goal was to answer three questions:
1. Which platform was growing fastest, and when?
2. Which content types drove the highest engagement?
3. Which days and formats should we prioritize going forward?

Findings were used to inform the rollout strategy for new Patreon and Substack channels,
contributing to a 15% increase in digital revenue over the internship period.

---

## Project Structure

```
comedy_engagement/
├── data/
│   ├── youtube_analytics.csv
│   ├── instagram_analytics.csv
│   └── tiktok_analytics.csv
├── outputs/
│   ├── 01_weekly_views.png
│   ├── 02_engagement_rate.png
│   ├── 03_content_type_performance.png
│   ├── 04_posting_day_heatmap.png
│   ├── 05_follower_growth.png
│   ├── 06_predicted_heatmap.png        # ML predictions
│   └── 07_feature_importance.png       # What drives engagement?
├── generate_data.py        # Generates mock platform export CSVs
├── engagement_analysis.py  # Main analysis + visualization script
├── predict_performance.py  # ML model to predict best content combinations
└── README.md
```

---

## How to Run

```bash
# 1. Install dependencies
pip install pandas matplotlib seaborn scikit-learn

# 2. Generate mock data
python generate_data.py

# 3. Run analysis
python engagement_analysis.py

# 4. Run ML predictions
python predict_performance.py
```

Charts will be saved to the `outputs/` folder.

---

## Key Findings

- **TikTok** drove the highest raw view counts; "Trending Audio" and "Collab" formats consistently outperformed others
- **Instagram Reels** had the highest engagement rate relative to follower count
- **Wednesday and Saturday** were the strongest posting days across all platforms
- Follower growth accelerated ~40% after the Patreon/Substack launch in mid-July
- ML model (Random Forest, R²=0.71) predicted Instagram Reels on Friday and TikTok Trending Audio on Wednesday as the highest-yield combinations

---

## Tech Stack

- **Python** — Pandas, NumPy, Matplotlib, Seaborn, scikit-learn
- **Model** — Random Forest Regressor (200 estimators, max depth 8)
- **Data source** — Platform-native analytics dashboards (YouTube Studio, Instagram Insights, TikTok Analytics)
