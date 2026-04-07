# Customer Churn Analysis

**Tools:** Python, pandas, scikit-learn, matplotlib, seaborn  
**Skills:** EDA, feature engineering, classification modeling, business impact framing

---

## Business Question

What factors predict customer churn, and which customer segments should a retention team prioritize to maximize ROI?

---

## Dataset

IBM Telco Customer Churn dataset — 7,043 telecom customers with 21 features including contract type, monthly charges, tenure, and service details.

**Download:** https://www.kaggle.com/datasets/blastchar/telco-customer-churn  
After downloading, rename the file to `telco_churn.csv` and place it in the `data/` folder.

---

## Setup

1. In your terminal, navigate to this project folder:
```bash
cd "/Users/your-username/path/to/Customer Churn Analysis"
```

2. Create the required folders if they don't exist:
```bash
mkdir -p data outputs notebooks
```

3. Install dependencies:
```bash
pip install pandas numpy matplotlib seaborn scikit-learn
```

4. Run the script:
```bash
python churn_analysis.py
```

Your folder should look like this before running:
```
Customer Churn Analysis/
├── churn_analysis.py
├── README.md
├── data/
│   └── telco_churn.csv
├── notebooks/
└── outputs/
```

Or open in VS Code with the Jupyter extension and run sections interactively.

---

## Key Findings

- Overall churn rate: ~26%
- Month-to-month customers churn at nearly 3x the rate of annual contract customers
- Fiber optic + electronic check + month-to-month = highest risk segment (~55% churn)
- Tenure is the strongest predictor: customers who survive past 24 months rarely churn
- Self-reported satisfaction surveys would miss most of this signal

---

## Models

| Model | ROC-AUC |
|---|---|
| Logistic Regression | ~0.84 |
| Random Forest | ~0.85 |

---

## Business Recommendation

Target high-risk customers (month-to-month, fiber optic, electronic check) with a contract upgrade offer and billing method switch incentive. At an estimated $50 retention cost vs. ~$1,100 customer lifetime value, the ROI is strongly positive.

---

## Outputs

- `outputs/eda_overview.png` - EDA charts
- `outputs/feature_importance.png` - Top churn drivers
- `outputs/confusion_matrices.png` - Model performance
