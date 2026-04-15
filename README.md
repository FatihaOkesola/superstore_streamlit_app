# Superstore Profitability Explorer (Streamlit App)

## Overview

This project is an interactive Streamlit application built with the Superstore dataset to explore profitability drivers through a guided diagnostic workflow.

The app allows users to move from high-level company performance to deeper investigation of:

- regional profitability differences
- category-level contribution to sales and profit
- sub-category drivers of margin erosion
- the role of discounting in weak profitability
- the impact of a simplified pricing intervention scenario

This project extends my earlier Superstore sales diagnostic notebook by turning the analysis into a user-friendly app for non-technical users.

---

## Features

- Interactive filtering by region and category
- Company-level KPI view (Sales, Profit, Profit Margin)
- Region-level profitability analysis
- Category contribution analysis
- Furniture sub-category diagnostic
- Tables discount and profitability breakdown by region
- Scenario analysis to test the effect of improved discount discipline

---

## Tools Used

Python · Streamlit · Pandas · Matplotlib
---

## Project Structure

- `superstore_streamlit_code.py` — Streamlit app code
- `superstore.csv` — dataset used in the app
- `requirements.txt` — required Python packages

---

## How to Run the App Locally

### 1. Clone the repository

```bash
git clone https://github.com/FatihaOkesola/superstore_streamlit_app.git
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run superstore_streamlit_code.py
```

---

## Dataset

[Superstore Sales Dataset — Kaggle](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)

---

## Notes / Assumptions

This dataset is public and not tied to a specific company. The exclusion controls and discount scenario are illustrative counterfactuals — intended to show directional impact rather than predict exact real-world outcomes. All insights are based on assumptions stated within the app.

---

## Part of a Broader Portfolio

This project is one of four tools applied to the same dataset:

- Python → Profitability diagnostic notebook
- Streamlit → Interactive dashboard (this project)
- - Excel → Sales storytelling (completed after this)
- SQL → Planned next step
