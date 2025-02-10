import os, time
import pandas as pd
import streamlit as st

from services.dataviz.utils.data_fetch import fetch_data_from_notion, fetch_blocked_days_data
import datetime
from services.dataviz.utils.plotting import (
    plot_host_payout_world_map,
    plot_avg_payout_vs_nights,
    plot_boxplot_nightly_price_by_month,
    plot_boxplot_nights_by_month,
    plot_blocked_days
)

st.set_page_config(layout="wide")

if st.button("Refresh Data"):
    for path in [
        os.getenv("PROJECT_ROOT") + "/services/dataviz/data/df_notion_cache.csv",
        os.getenv("PROJECT_ROOT") + "/services/dataviz/data/df_blocked_days_cache.csv",
    ]:
        if os.path.exists(path):
            os.remove(path)
    st.rerun()

df = fetch_data_from_notion()
df_blocked = fetch_blocked_days_data()

st.title("Notion Data Visualization")
st.write("Data fetched from Notion. Use the filters and charts below to explore the data.")

if "Arrival Date" in df.columns:
    df["year"] = df["Arrival Date"].dt.year
    available_years = sorted(df["year"].dropna().unique())
    if available_years:
        current_year = datetime.datetime.now().year
        default_index = available_years.index(current_year) if current_year in available_years else 0
        selected_year = st.sidebar.selectbox("Select Year", options=available_years, index=default_index)
        df_filtered = df[df["year"] == selected_year].copy()
        df_blocked_filterd = df_blocked[df_blocked["start_date"].dt.year == selected_year].copy()

        met_cols = st.columns(4)
        with met_cols[0]:
            total_host_payout = df_filtered["Host Payout"].sum() if "Host Payout" in df_filtered.columns else 0
            st.metric(label="Total Host Payout", value=f"{total_host_payout:,.2f} €")
        with met_cols[1]:
            avg_price = df_filtered["Price by night"].mean() if "Price by night" in df_filtered.columns else 0
            st.metric(label="Average Price by Night", value=f"{avg_price:,.2f} €")
        with met_cols[2]:
            if not df_blocked_filterd.empty:
                monthly_blocked = df_blocked_filterd.groupby("month_year")["blocked_days"].sum()
                avg_blocked = monthly_blocked.mean()
            else:
                avg_blocked = 0
            st.metric(label="Avg Days Blocked/Month", value=f"{avg_blocked:.1f}")
        with met_cols[3]:
            if "Country" in df_filtered.columns:
                num_countries = df_filtered["Country"].nunique()
            else:
                num_countries = 0
            st.metric(label="Number of Countries", value=num_countries)
    else:
        st.error("No valid 'Arrival Date' data found.")
        df_filtered = df.copy()
else:
    st.error("'Arrival Date' column is missing from the data.")
    df_filtered = df.copy()

# -----------------------------
# Dashboard Layout with Columns
# -----------------------------

# First row: Graph 1 and Graph 2 side by side
cols = st.columns(2)
with cols[0]:
    st.subheader("Average Payouts vs. Number of Nights")
    for col in ["Number of Nights", "Host Payout", "Guest Payout"]:
        if col not in df_filtered.columns:
            st.error(f"Column '{col}' is missing from the data.")
            st.stop()
    fig1 = plot_avg_payout_vs_nights(df_filtered)
    st.plotly_chart(fig1, use_container_width=True)
with cols[1]:
    if "Arrival Date" in df_filtered.columns and "Price by night" in df_filtered.columns:
        st.subheader("Box Plot: Nightly Price Distribution by Month")
        fig2 = plot_boxplot_nightly_price_by_month(df_filtered)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.error("Required columns for monthly price analysis are missing.")

# Second row: Graph 3 and Blocked Days Visualization side by side
cols2 = st.columns(2)
with cols2[0]:
    st.subheader("Distribution of Number of Nights by Month")
    if "Arrival Date" in df_filtered.columns and "Number of Nights" in df_filtered.columns:
        fig3 = plot_boxplot_nights_by_month(df_filtered)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.error("Required columns for box plot analysis are missing.")
with cols2[1]:
    st.subheader("Blocked Days per Month")
    if not df_blocked_filterd.empty and "month_year" in df_blocked_filterd.columns:
        fig_blocked = plot_blocked_days(df_blocked_filterd)
        st.plotly_chart(fig_blocked, use_container_width=True)
    else:
        st.error("Blocked days data is unavailable.")

# Third row: Host Payout World Map
st.subheader("Host Payout by Country")
fig_world = plot_host_payout_world_map(df_filtered)
st.plotly_chart(fig_world, use_container_width=True)
