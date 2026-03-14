import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Superstore Profitability Explorer", layout="wide")

st.title("Superstore Profitability Explorer")
st.caption("A guided diagnostic walkthrough from headline performance → segment contribution → root-cause isolation (illustrative counterfactuals).")
st.markdown("""
This app walks through a structured profitability diagnostic using Superstore sales data.
It starts with company-level performance, then progressively narrows the analysis from regions to categories, sub-categories, and pricing behavior.
At each stage, users can test simple illustrative scenarios to understand how specific segments influence overall profitability.
""")
# -----------------------------
# Helpers
# -----------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    # encoding fallback
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except Exception:
            df = None
    if df is None:
        raise ValueError("Could not load CSV with common encodings.")
    
    # Dates
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    # Postal code as string (identifier)
    if "Postal Code" in df.columns:
        df["Postal Code"] = df["Postal Code"].astype(str)

    return df


def kpi_block(df: pd.DataFrame):
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    margin = (total_profit / total_sales) if total_sales != 0 else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"${total_sales:,.0f}")
    col2.metric("Total Profit", f"${total_profit:,.0f}")
    col3.metric("Profit Margin", f"{margin*100:.2f}%")

    return total_sales, total_profit, margin


def bar_plot(series: pd.Series, title: str, ylabel: str):
    fig, ax = plt.subplots(figsize=(8, 4))
    series.plot(kind="bar", ax=ax)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    plt.xticks(rotation=0)
    st.pyplot(fig)


# -----------------------------
# Load data
# -----------------------------
with st.sidebar:
    st.header("Data")
    data_path = st.text_input("CSV path", value="superstore.csv")
    st.caption("Tip: keep superstore.csv in the same folder as app.py")

df = load_data(data_path)

# -----------------------------
# Global filters (sidebar)
# -----------------------------
with st.sidebar:
    st.header("Global Filters")

    # Date filter (optional but helpful)
    min_date = df["Order Date"].min()
    max_date = df["Order Date"].max()
    date_range = st.date_input("Order Date range", value=(min_date, max_date))

    # Region & Category filters (inputs for professor requirement)
    region_options = ["All"] + sorted(df["Region"].dropna().unique().tolist())
    category_options = ["All"] + sorted(df["Category"].dropna().unique().tolist())

    selected_region = st.selectbox("Region", region_options, index=0)
    selected_category = st.selectbox("Category", category_options, index=0)

# Apply global filters
filtered = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[(filtered["Order Date"] >= start_date) & (filtered["Order Date"] <= end_date)]

if selected_region != "All":
    filtered = filtered[filtered["Region"] == selected_region]

if selected_category != "All":
    filtered = filtered[filtered["Category"] == selected_category]

st.divider()

# -----------------------------
# STEP 0: Baseline KPIs
# -----------------------------
with st.expander("Step 0 — Baseline Performance (Company KPIs)", expanded=True):
    st.markdown(""" 
This section establishes the baseline by showing total sales, total profit, and overall profit margin after applying the global filters.
It answers the question: *What does performance look like at a high level before deeper diagnosis begins?*
""")
    kpi_block(filtered)

    show_sample = st.checkbox("Show a small sample of the filtered data", value=False)

    if show_sample:
        st.dataframe(filtered.head(20), use_container_width=True, height=300)

st.divider()

# -----------------------------
# STEP 1: Region benchmark + exclude region
# -----------------------------
with st.expander("Step 1 — Regional Benchmark (Where is performance weak?)", expanded=True):
    st.markdown(
        "Once overall performance is established, the next question is whether profitability is evenly distributed across regions. This section highlights regional differences and allows users to see how overall performance changes if an underperforming region is removed."
        "Use the exclusion toggle to see how overall performance changes if a region’s contribution is removed (illustrative)."
    )

    region_summary = filtered.groupby("Region")[["Sales", "Profit"]].sum()
    region_summary["Profit Margin"] = region_summary["Profit"] / region_summary["Sales"]

    st.dataframe(region_summary.round(4), use_container_width=True)

    bar_plot((region_summary["Profit Margin"] * 100).sort_values(ascending=False),
             "Profit Margin by Region (%)", "Profit Margin (%)")

    # Exclude one region
    exclude_region = st.selectbox("What-if: Exclude a region", ["None"] + region_summary.index.tolist())

    if exclude_region != "None":
        whatif = filtered[filtered["Region"] != exclude_region]
        st.subheader(f"What-if KPIs (excluding {exclude_region})")
        kpi_block(whatif)

st.divider()

# -----------------------------
# STEP 2: Category imbalance + exclude category
# -----------------------------
with st.expander("Step 2 — Category Profitability (Which category drives the gap?)", expanded=True):
    st.markdown(
        "**Insight:** After identifying regional variation, the next step is to determine whether certain product categories contribute disproportionately to weaken profitability. This section compares revenue contribution and profit contribution to reveal categories that generate sales without transalting efficiently into profit." \
        "Excluding a category shows how much it influences overall profitability (illustrative)."
    )

    cat_summary = filtered.groupby("Category")[["Sales", "Profit"]].sum()
    cat_summary["Profit Margin"] = cat_summary["Profit"] / cat_summary["Sales"]
    cat_summary["Sales %"] = cat_summary["Sales"] / cat_summary["Sales"].sum()
    cat_summary["Profit %"] = cat_summary["Profit"] / cat_summary["Profit"].sum()

    st.dataframe(cat_summary.round(4), use_container_width=True)

    # Plot: revenue share vs profit share
    share = (cat_summary[["Sales %", "Profit %"]] * 100).sort_values(by="Sales %", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 4))
    share.plot(kind="bar", ax=ax)
    ax.set_title("Revenue Share vs Profit Share by Category (%)")
    ax.set_ylabel("Contribution (%)")
    ax.set_xlabel("")
    plt.xticks(rotation=0)
    st.pyplot(fig)

    # Exclude one category
    exclude_category = st.selectbox("What-if: Exclude a category", ["None"] + cat_summary.index.tolist())

    if exclude_category != "None":
        whatif = filtered[filtered["Category"] != exclude_category]
        st.subheader(f"What-if KPIs (excluding {exclude_category})")
        kpi_block(whatif)

st.divider()

# -----------------------------
# STEP 3: Furniture deep dive + exclude sub-categories
# -----------------------------
with st.expander("Step 3 — Furniture Diagnostic (Which sub-category is the root cause?)", expanded=True):
    st.markdown(
        "**Insight:** If Furniture is underperforming, the root cause may be concentrated in specific sub-categories. This section breaks Furniture into sub-categories to identify whether losses are concentrated in a few product lines rather than s[read across the whole category." \
        "Exclude sub-categories to test contribution (illustrative)."
    )

    furniture = filtered[filtered["Category"] == "Furniture"].copy()
    if furniture.empty:
        st.warning("No Furniture records under the current global filters. Try selecting Category = All or Furniture.")
    else:
        sub_summary = furniture.groupby("Sub-Category")[["Sales", "Profit"]].sum()
        sub_summary["Profit Margin"] = sub_summary["Profit"] / sub_summary["Sales"]

        st.dataframe(sub_summary.round(4), use_container_width=True)

        # Plot sub-category profit margin
        margins = (sub_summary["Profit Margin"] * 100).sort_values()
        colors = ["red" if v < 0 else "green" for v in margins.values]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(margins.index, margins.values, color=colors)
        ax.axhline(0, color="black", linewidth=1)
        ax.set_title("Furniture Sub-Category Profit Margin (%)")
        ax.set_ylabel("Profit Margin (%)")
        plt.xticks(rotation=30, ha="right")
        st.pyplot(fig)

        # Exclude sub-categories
        exclude_subcats = st.multiselect(
            "What-if: Exclude sub-categories",
            options=sub_summary.index.tolist(),
            default=[]
        )

        if exclude_subcats:
            whatif = furniture[~furniture["Sub-Category"].isin(exclude_subcats)]
            st.subheader("What-if KPIs (Furniture only, excluding selected sub-categories)")
            kpi_block(whatif)

            st.subheader("What-if KPIs (Overall, excluding selected sub-categories)")
            overall_whatif = filtered.copy()
            mask = (overall_whatif["Category"] == "Furniture") & (overall_whatif["Sub-Category"].isin(exclude_subcats))
            overall_whatif = overall_whatif[~mask]
            kpi_block(overall_whatif)

st.divider()

# -----------------------------
# STEP 4 (Optional now): Tables focused view (no slider yet if keeping simple)
# -----------------------------
with st.expander("Step 4 — Tables Focus (Where do losses concentrate?)", expanded=False):
    st.markdown(
        "**Insight:** After identifying Tbles as a major loss-making sub-category, the next question is whether the issue is uniform across all regions or concentrated in a few." \
        "This section compares regional profitability and discount level to Tables to isolate where losses are most severe and what may be driving them."
    )

    tables = filtered[filtered["Sub-Category"] == "Tables"].copy()
    if tables.empty:
        st.warning("No Tables records under the current global filters. Try Category = All or Furniture.")
    else:
        t_summary = tables.groupby("Region")[["Sales", "Profit"]].sum()
        t_summary["Profit Margin"] = t_summary["Profit"] / t_summary["Sales"]
        t_summary["Avg Discount"] = tables.groupby("Region")["Discount"].mean()

        st.dataframe(t_summary.round(4), use_container_width=True)

        bar_plot((t_summary["Profit Margin"] * 100).sort_values(),
                 "Tables Profit Margin by Region (%)", "Profit Margin (%)")

        bar_plot((t_summary["Avg Discount"] * 100).sort_values(ascending=False),
                 "Average Discount on Tables by Region (%)", "Avg Discount (%)")

st.divider()

# -----------------------------
# STEP 5: Scenario impact - discount intervention
# -----------------------------
with st.expander("Step 5 — Scenario Impact (What happens if discount discipline improves?)", expanded=True):
    st.markdown(""" 
    The earlier steps identify where profitability is weakest and suggest that discounting is a major driver of losses in Tables, particularly in the East region.  
    This final step tests a simplified pricing intervention by reducing discount while holding volume and cost structure constant.  
    It answers the question: *If discount discipline improves, how much could profitability improve?*
    """)

    scenario_region_options = sorted(filtered["Region"].dropna().unique().tolist())
    scenario_subcat_options = sorted(filtered["Sub-Category"].dropna().unique().tolist())

    col1, col2 = st.columns(2)
    with col1:
        scenario_region = st.selectbox(
            "Select region for scenario analysis",
            scenario_region_options,
            index=scenario_region_options.index("East") if "East" in scenario_region_options else 0
        )
    with col2:
        scenario_subcat = st.selectbox(
            "Select sub-category for scenario analysis",
            scenario_subcat_options,
            index=scenario_subcat_options.index("Tables") if "Tables" in scenario_subcat_options else 0
        )

    scenario_df = filtered[
        (filtered["Region"] == scenario_region) &
        (filtered["Sub-Category"] == scenario_subcat)
    ].copy()

    if scenario_df.empty:
        st.warning("No records match the selected scenario filters.")
    else:
        current_discount = scenario_df["Discount"].mean()

        new_discount = st.slider(
            "Adjust average discount",
            min_value=0.0,
            max_value=0.5,
            value=float(round(current_discount, 2)),
            step=0.01
        )

        # Original values
        original_profit = scenario_df["Profit"].sum()
        original_sales = scenario_df["Sales"].sum()

        # Reconstruct implied full price
        scenario_df["Implied_Full_Price"] = scenario_df["Sales"] / (1 - scenario_df["Discount"])

        # Apply new discount
        scenario_df["New_Sales"] = scenario_df["Implied_Full_Price"] * (1 - new_discount)

        # Estimate cost from original sales and profit
        scenario_df["Estimated_Cost"] = scenario_df["Sales"] - scenario_df["Profit"]

        # Compute new profit
        scenario_df["New_Profit"] = scenario_df["New_Sales"] - scenario_df["Estimated_Cost"]

        new_profit = scenario_df["New_Profit"].sum()
        improvement = new_profit - original_profit

        col1, col2, col3 = st.columns(3)
        col1.metric("Current Avg Discount", f"{current_discount*100:.2f}%")
        col2.metric("Original Profit", f"${original_profit:,.0f}")
        col3.metric("Scenario Profit", f"${new_profit:,.0f}")

        st.metric("Estimated Profit Improvement", f"${improvement:,.0f}")

        scenario_compare = pd.Series({
            "Original Profit": original_profit,
            "Scenario Profit": new_profit
        })

        fig, ax = plt.subplots(figsize=(7, 4))
        scenario_compare.plot(kind="bar", ax=ax, color=["#4C78A8", "#F58518"])
        ax.axhline(0, color="black", linewidth=1)
        ax.set_title(f"Profit Comparison: {scenario_region} - {scenario_subcat}")
        ax.set_ylabel("Profit ($)")
        ax.set_xlabel("")
        plt.xticks(rotation=0)
        st.pyplot(fig)

        st.markdown(f"""
        **Interpretation:**  
        Under this simplified scenario, changing the average discount for **{scenario_subcat}** in **{scenario_region}**
        from **{current_discount*100:.2f}% to {new_discount*100:.2f}%**
        changes estimated profit from **${original_profit:,.0f}** to **${new_profit:,.0f}**.
        This provides a directional estimate of the potential benefit of improved pricing discipline.
        """)

        st.markdown("""
---
**How to use this app:**  
This app is designed as a guided profitability diagnostic. Users can move from high-level performance to region, category, and sub-category analysis, then test simple illustrative interventions to understand which levers matter most.

**Important note:**  
The exclusion controls and discount scenario are illustrative counterfactuals. They are intended to show contribution and directional impact rather than predict exact real-world outcomes.
""")