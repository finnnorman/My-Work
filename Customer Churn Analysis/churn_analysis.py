# Customer Churn Analysis
# Dataset: IBM Telco Customer Churn (Kaggle)
# Download from: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
# Save the CSV as: data/telco_churn.csv

# To run as a notebook: pip install jupytext, then run:
# jupytext --to notebook churn_analysis.py
# Or just run sections in VS Code with the Jupyter extension


# ------------------------------------------------------------
# SECTION 1: IMPORTS AND SETUP
# ------------------------------------------------------------

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import warnings
warnings.filterwarnings("ignore")

plt.style.use("seaborn-v0_8")
sns.set_palette("Set2")


# ------------------------------------------------------------
# SECTION 2: LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv("{data,notebooks,outputs}/data/telco_churn.csv")

print("Shape:", df.shape)
print("\nFirst 5 rows:")
print(df.head())
print("\nColumn types:")
print(df.dtypes)
print("\nMissing values:")
print(df.isnull().sum())


# ------------------------------------------------------------
# SECTION 3: CLEAN DATA
# ------------------------------------------------------------

# TotalCharges comes in as a string due to blank values for new customers
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

# New customers with 0 tenure have blank TotalCharges, fill with 0
df["TotalCharges"] = df["TotalCharges"].fillna(0)

# Drop customer ID since it adds no predictive value
df.drop(columns=["customerID"], inplace=True)

# Convert churn column to binary integer
df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})

print("Cleaned data shape:", df.shape)
print("Churn rate: {:.1f}%".format(df["Churn"].mean() * 100))


# ------------------------------------------------------------
# SECTION 4: EXPLORATORY DATA ANALYSIS
# ------------------------------------------------------------

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle("Churn EDA: Key Variable Distributions", fontsize=14)

# Churn distribution
churn_counts = df["Churn"].value_counts()
axes[0, 0].bar(["No Churn", "Churned"], churn_counts.values, color=["steelblue", "tomato"])
axes[0, 0].set_title("Churn Distribution")
axes[0, 0].set_ylabel("Count")
for i, v in enumerate(churn_counts.values):
    axes[0, 0].text(i, v + 20, str(v), ha="center")

# Tenure by churn
df.groupby("Churn")["tenure"].plot(kind="kde", ax=axes[0, 1])
axes[0, 1].set_title("Tenure Distribution by Churn")
axes[0, 1].set_xlabel("Tenure (months)")
axes[0, 1].legend(["No Churn", "Churned"])

# Monthly charges by churn
df.boxplot(column="MonthlyCharges", by="Churn", ax=axes[0, 2])
axes[0, 2].set_title("Monthly Charges by Churn")
axes[0, 2].set_xlabel("Churned (0=No, 1=Yes)")

# Contract type vs churn rate
contract_churn = df.groupby("Contract")["Churn"].mean().sort_values(ascending=False)
axes[1, 0].bar(contract_churn.index, contract_churn.values * 100, color="coral")
axes[1, 0].set_title("Churn Rate by Contract Type")
axes[1, 0].set_ylabel("Churn Rate (%)")
axes[1, 0].tick_params(axis="x", rotation=15)

# Internet service vs churn rate
internet_churn = df.groupby("InternetService")["Churn"].mean().sort_values(ascending=False)
axes[1, 1].bar(internet_churn.index, internet_churn.values * 100, color="mediumpurple")
axes[1, 1].set_title("Churn Rate by Internet Service")
axes[1, 1].set_ylabel("Churn Rate (%)")

# Payment method vs churn rate
payment_churn = df.groupby("PaymentMethod")["Churn"].mean().sort_values(ascending=False)
axes[1, 2].barh(payment_churn.index, payment_churn.values * 100, color="teal")
axes[1, 2].set_title("Churn Rate by Payment Method")
axes[1, 2].set_xlabel("Churn Rate (%)")

plt.tight_layout()
plt.savefig("outputs/eda_overview.png", dpi=150, bbox_inches="tight")
plt.show()
print("EDA chart saved to outputs/eda_overview.png")


# ------------------------------------------------------------
# SECTION 5: DEEPER ANALYSIS - WHAT DRIVES CHURN?
# ------------------------------------------------------------

# Average metrics by churn group
print("Average metrics by churn status:")
print(df.groupby("Churn")[["tenure", "MonthlyCharges", "TotalCharges"]].mean().round(2))

# High risk segment: month-to-month + fiber + electronic check
high_risk = df[
    (df["Contract"] == "Month-to-month") &
    (df["InternetService"] == "Fiber optic") &
    (df["PaymentMethod"] == "Electronic check")
]
print("\nHigh-risk segment size:", len(high_risk))
print("High-risk segment churn rate: {:.1f}%".format(high_risk["Churn"].mean() * 100))
print("Overall churn rate: {:.1f}%".format(df["Churn"].mean() * 100))


# ------------------------------------------------------------
# SECTION 6: FEATURE ENGINEERING
# ------------------------------------------------------------

df_model = df.copy()

# Binary yes/no columns to 0/1
binary_cols = [
    "Partner", "Dependents", "PhoneService", "PaperlessBilling",
    "MultipleLines", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"
]
for col in binary_cols:
    df_model[col] = df_model[col].map({"Yes": 1, "No": 0, "No phone service": 0, "No internet service": 0})

# Encode remaining categorical columns
cat_cols = ["gender", "InternetService", "Contract", "PaymentMethod"]
le = LabelEncoder()
for col in cat_cols:
    df_model[col] = le.fit_transform(df_model[col])

# Create a tenure bucket feature (0-12, 13-24, 25-48, 49+)
df_model["tenure_bucket"] = pd.cut(
    df_model["tenure"],
    bins=[0, 12, 24, 48, 72],
    labels=[0, 1, 2, 3]
).astype(int)

print("Features ready. Shape:", df_model.shape)


# ------------------------------------------------------------
# SECTION 7: TRAIN/TEST SPLIT
# ------------------------------------------------------------

X = df_model.drop(columns=["Churn"])
y = df_model["Churn"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training samples:", len(X_train))
print("Test samples:", len(X_test))
print("Train churn rate: {:.1f}%".format(y_train.mean() * 100))
print("Test churn rate: {:.1f}%".format(y_test.mean() * 100))


# ------------------------------------------------------------
# SECTION 8: LOGISTIC REGRESSION MODEL
# ------------------------------------------------------------

lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
lr_preds = lr.predict(X_test)
lr_proba = lr.predict_proba(X_test)[:, 1]

print("Logistic Regression Results:")
print(classification_report(y_test, lr_preds))
print("ROC-AUC:", round(roc_auc_score(y_test, lr_proba), 3))


# ------------------------------------------------------------
# SECTION 9: RANDOM FOREST MODEL
# ------------------------------------------------------------

rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
rf.fit(X_train, y_train)
rf_preds = rf.predict(X_test)
rf_proba = rf.predict_proba(X_test)[:, 1]

print("Random Forest Results:")
print(classification_report(y_test, rf_preds))
print("ROC-AUC:", round(roc_auc_score(y_test, rf_proba), 3))


# ------------------------------------------------------------
# SECTION 10: FEATURE IMPORTANCE
# ------------------------------------------------------------

importances = pd.Series(rf.feature_importances_, index=X.columns)
importances = importances.sort_values(ascending=True).tail(15)

fig, ax = plt.subplots(figsize=(10, 7))
importances.plot(kind="barh", ax=ax, color="steelblue")
ax.set_title("Top 15 Features Driving Churn (Random Forest)", fontsize=13)
ax.set_xlabel("Feature Importance Score")
plt.tight_layout()
plt.savefig("outputs/feature_importance.png", dpi=150, bbox_inches="tight")
plt.show()
print("Feature importance chart saved.")


# ------------------------------------------------------------
# SECTION 11: CONFUSION MATRIX
# ------------------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for ax, preds, title in zip(
    axes,
    [lr_preds, rf_preds],
    ["Logistic Regression", "Random Forest"]
):
    cm = confusion_matrix(y_test, preds)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

plt.tight_layout()
plt.savefig("outputs/confusion_matrices.png", dpi=150, bbox_inches="tight")
plt.show()


# ------------------------------------------------------------
# SECTION 12: BUSINESS IMPACT - COST/BENEFIT ANALYSIS
# ------------------------------------------------------------

# Assumptions (adjust to fit a real business scenario)
avg_monthly_revenue = df["MonthlyCharges"].mean()
avg_tenure_remaining = 18  # estimated months a retained customer would stay
retention_offer_cost = 50  # one-time discount or incentive cost per customer

customer_lifetime_value = avg_monthly_revenue * avg_tenure_remaining
net_benefit_per_retained_customer = customer_lifetime_value - retention_offer_cost

# How many customers are flagged as high churn risk by the model
churn_prob_threshold = 0.6
high_risk_customers = (rf_proba >= churn_prob_threshold).sum()
total_test_customers = len(y_test)

print("Business Impact Estimate")
print("-" * 40)
print(f"Avg monthly charges: ${avg_monthly_revenue:.2f}")
print(f"Estimated CLV if retained: ${customer_lifetime_value:.2f}")
print(f"Retention offer cost: ${retention_offer_cost:.2f}")
print(f"Net benefit per retained customer: ${net_benefit_per_retained_customer:.2f}")
print(f"\nHigh-risk customers flagged (>{churn_prob_threshold:.0%} prob): {high_risk_customers}")
print(f"Potential revenue saved if 50% retained: ${net_benefit_per_retained_customer * high_risk_customers * 0.5:,.0f}")

print("\nRecommendation:")
print("Target month-to-month customers with fiber optic and electronic check payment.")
print("These customers churn at 2-3x the base rate.")
print("A targeted retention campaign (contract upgrade offer + billing switch incentive)")
print("at $50 per customer yields a positive ROI given the estimated CLV.")
