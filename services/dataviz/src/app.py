import os, time
import pandas as pd
import plotly.express as px
import streamlit as st

from services.notion_client.notion_api_client import NotionClient
from get_blocked_days import fetch_blocked_days_from_notion

# ---------- CSV CACHING UTILS ----------
def load_or_fetch(cache_path, fetch_func, *args, **kwargs):
    if os.path.exists(cache_path):
        if time.time() - os.path.getmtime(cache_path) < 3600 * 24:
            return pd.read_csv(cache_path)
    df = fetch_func(*args, **kwargs)
    df.to_csv(cache_path, index=False)
    return df

# ---------- NOTION DATA FETCHING ----------
def get_notion_data():
    notion_client = NotionClient()
    pages = notion_client.get_all_pages()
    data = [notion_client.parse_page(page) for page in pages]
    df = pd.DataFrame(data)
    for col in ["Arrival Date", "Departure Date", "Mail Date", "Insert Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in [
        "Host Service Fee", "Guest Service Fee", "Total Nights Cost",
        "Guest Payout", "Host Payout", "Cleaning Fee", "Tourist Tax",
        "Price by night", "Number of Nights",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def fetch_data_from_notion():
    cache_path = os.getenv("PROJECT_ROOT") + "/services/dataviz/data/df_notion_cache.csv"
    df = load_or_fetch(cache_path, get_notion_data)
    for col in ["Arrival Date", "Departure Date", "Mail Date", "Insert Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

# ---------- BLOCKED DAYS DATA FETCHING ----------
def get_blocked_days_data():
    df = fetch_blocked_days_from_notion()
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["blocked_days"] = (df["end_date"] - df["start_date"]).dt.days
    df["month_year"] = df["start_date"].dt.to_period("M").astype(str)
    return df

def fetch_blocked_days_data():
    cache_path = os.getenv("PROJECT_ROOT") + "/services/dataviz/data/df_blocked_days_cache.csv"
    df = load_or_fetch(cache_path, get_blocked_days_data)
    for col in ["start_date", "end_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

# Button to refresh data manually: clears CSV cache by deleting files (optional)
if st.button("Refresh Data"):
    for path in [
        os.getenv("PROJECT_ROOT") + "/services/dataviz/data/df_notion_cache.csv",
        os.getenv("PROJECT_ROOT") + "/services/dataviz/data/df_blocked_days_cache.csv",
    ]:
        if os.path.exists(path):
            os.remove(path)
    st.rerun()

# Fetch (or load cached) data
df = fetch_data_from_notion()
df_blocked = fetch_blocked_days_data()
# -----------------------------
# GLOBAL FILTERS
# -----------------------------
st.title("Notion Data Visualization")
st.write(
    "Data fetched from Notion. Use the filters and charts below to explore the data."
)

# Create a global year filter based on the "Arrival Date"
if "Arrival Date" in df.columns:
    df["year"] = df["Arrival Date"].dt.year
    available_years = sorted(df["year"].dropna().unique())
    if available_years:
        selected_year = st.selectbox("Select Year", options=available_years)
        df_filtered = df[df["year"] == selected_year].copy()
        df_blocked_filterd = df_blocked[df_blocked["start_date"].dt.year == selected_year].copy()
    else:
        st.error("No valid 'Arrival Date' data found.")
        df_filtered = df.copy()
else:
    st.error("'Arrival Date' column is missing from the data.")
    df_filtered = df.copy()

# -----------------------------
# GRAPH 1: Average Payouts vs. Number of Nights
# -----------------------------
st.subheader("Average Payouts vs. Number of Nights")

# Make sure the necessary columns are available and numeric.
for col in ["Number of Nights", "Host Payout", "Guest Payout"]:
    if col not in df_filtered.columns:
        st.error(f"Column '{col}' is missing from the data.")
        st.stop()

# Group by Number of Nights and compute average payouts.
grouped = (
    df_filtered.groupby("Number of Nights")
    .agg({"Host Payout": "mean", "Guest Payout": "mean"})
    .reset_index()
)

# Reshape for a grouped bar chart.
grouped_melted = grouped.melt(
    id_vars="Number of Nights",
    value_vars=["Host Payout", "Guest Payout"],
    var_name="Payout Type",
    value_name="Average Payout",
)

fig1 = px.bar(
    grouped_melted,
    x="Number of Nights",
    y="Average Payout",
    color="Payout Type",
    barmode="group",
    title="Average Payout vs. Number of Nights",
)
st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# GRAPH 2: Box Plot of Nightly Price Distribution by Month
# -----------------------------
if "Arrival Date" in df_filtered.columns and "Price by night" in df_filtered.columns:
    df_filtered.loc[:, "month_year"] = (
        df_filtered["Arrival Date"].dt.to_period("M").astype(str)
    )
    # Create a box plot showing the distribution of nightly prices for each month
    fig2 = px.box(
        df_filtered,
        x="month_year",
        y="Price by night",
        title="Box Plot: Nightly Price Distribution by Month (Based on Arrival Date)",
        labels={"month_year": "Month-Year", "Price by night": "Nightly Price"},
    )
    st.plotly_chart(fig2, use_container_width=False)
else:
    st.error("Required columns for monthly price analysis are missing.")

# -----------------------------
# GRAPH 3: Box Plot of Days of Stay by Month
# -----------------------------
st.subheader("Distribution of Number of Nights by Month")

if "Arrival Date" in df_filtered.columns and "Number of Nights" in df_filtered.columns:
    # Extract month name
    df_filtered.loc[:, "month"] = df_filtered["Arrival Date"].dt.strftime("%B")

    fig3 = px.box(
        df_filtered,
        x="month",
        y="Number of Nights",
        title="Box Plot: Number of Nights by Month (Arrival Date)",
        labels={"month": "Month", "Number of Nights": "Days of Stay"},
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.error("Required columns for box plot analysis are missing.")

# New section: Blocked Days Visualization
st.subheader("Blocked Days per Month")
if not df_blocked_filterd.empty and "month_year" in df_blocked_filterd.columns:
    df_blocked_grouped = df_blocked_filterd.groupby("month_year")["blocked_days"].sum().reset_index()
    fig_blocked = px.bar(
         df_blocked_grouped,
         x="month_year",
         y="blocked_days",
         title="Total Blocked Days per Month",
         labels={"month_year": "Month-Year", "blocked_days": "Total Blocked Days"},
    )
    st.plotly_chart(fig_blocked, use_container_width=True)
else:
    st.error("Blocked days data is unavailable.")
