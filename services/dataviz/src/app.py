import os, time
import pandas as pd
import streamlit as st
import plotly.express as px
from services.dataviz.utils.data_fetch import fetch_data_from_notion, fetch_blocked_days_data
import datetime
from services.dataviz.utils.plotting import (
    plot_host_payout_world_map,
    plot_avg_payout_vs_nights,
    plot_boxplot_nightly_price_by_month,
    plot_boxplot_nights_by_month,
    plot_blocked_days,
    plot_stacked_month_days  # New import for the stacked bar chart
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
        
        # New: Compute previous year data
        df_previous = df[df["year"] == (selected_year - 1)].copy()
        df_blocked_previous = df_blocked[df_blocked["start_date"].dt.year == (selected_year - 1)].copy()
        
        met_cols = st.columns(4)
        with met_cols[0]:
            current_total = df_filtered["Host Payout"].sum() if "Host Payout" in df_filtered.columns else 0
            prev_total = df_previous["Host Payout"].sum() if "Host Payout" in df_previous.columns and not df_previous.empty else 0
            delta_total = f"{((current_total - prev_total) / prev_total * 100):+,.2f}%" if prev_total > 0 else "N/A"
            st.metric(label="Total Host Payout", value=f"{current_total:,.2f} €", delta=delta_total)
        with met_cols[1]:
            current_price = df_filtered["Price by night"].mean() if "Price by night" in df_filtered.columns else 0
            prev_price = df_previous["Price by night"].mean() if "Price by night" in df_previous.columns and not df_previous.empty else 0
            delta_price = f"{((current_price - prev_price) / prev_price * 100):+,.2f}%" if prev_price > 0 else "N/A"
            st.metric(label="Average Price by Night", value=f"{current_price:,.2f} €", delta=delta_price)
        with met_cols[2]:
            if not df_blocked_filterd.empty:
                monthly_blocked = df_blocked_filterd.groupby("month_year")["blocked_days"].sum()
                current_avg = monthly_blocked.mean()
            else:
                current_avg = 0
            if not df_blocked_previous.empty:
                prev_monthly = df_blocked_previous.groupby("month_year")["blocked_days"].sum()
                prev_avg = prev_monthly.mean()
            else:
                prev_avg = 0
            delta_blocked = f"{((current_avg - prev_avg) / prev_avg * 100):+,.2f}%" if prev_avg > 0 else "N/A"
            st.metric(label="Avg Days Blocked/Month", value=f"{current_avg:.1f}", delta=delta_blocked)
        with met_cols[3]:
            current_countries = df_filtered["Country"].nunique() if "Country" in df_filtered.columns else 0
            prev_countries = df_previous["Country"].nunique() if "Country" in df_previous.columns and not df_previous.empty else 0
            delta_countries = f"{((current_countries - prev_countries) / prev_countries * 100):+,.0f}%" if prev_countries > 0 else "N/A"
            st.metric(label="Number of Countries", value=current_countries, delta=delta_countries)
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

# Third row: New Box Plot of Price by Night by Rating
st.subheader("Box Plot: Price by Night by Rating")
if "Rating" not in df_filtered.columns:
    st.error("Column 'Rating' is missing from the data.")
else:
    from services.dataviz.utils.plotting import plot_boxplot_price_by_nights
    fig_rating = plot_boxplot_price_by_nights(df_filtered, "Rating")
    st.plotly_chart(fig_rating, use_container_width=True)

# New: Stacked Bar Chart for Monthly Days Breakdown
st.subheader("Stacked Bar Chart: Days in Month Breakdown")
if "Arrival Date" in df.columns and "Number of Nights" in df.columns and not df_blocked.empty:
    fig_stacked = plot_stacked_month_days(df_filtered, df_blocked_filterd)
    st.plotly_chart(fig_stacked, use_container_width=True)
else:
    st.error("Insufficient data for monthly days breakdown.")

# Host Payout World Map (existing)
st.subheader("Host Payout by Country")
fig_world = plot_host_payout_world_map(df_filtered)
st.plotly_chart(fig_world, use_container_width=True)
