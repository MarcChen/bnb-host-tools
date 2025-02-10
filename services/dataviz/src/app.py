import pandas as pd
import plotly.express as px
import streamlit as st

from services.notion_client.notion_api_client import NotionClient


# -----------------------------
# DATA FETCHING & CACHING
# -----------------------------
@st.cache_data(ttl=3600 * 24)
def fetch_data_from_notion():
    """Fetch data from Notion via the client and return a cleaned DataFrame."""
    notion_client = NotionClient()
    pages = notion_client.get_all_pages()
    data = [notion_client.parse_page(page) for page in pages]
    df = pd.DataFrame(data)

    # Convert date columns to datetime
    for col in ["Arrival Date", "Departure Date", "Mail Date", "Insert Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Ensure numeric columns are properly converted.
    # Adjust the list below if needed.
    for col in [
        "Host Service Fee",
        "Guest Service Fee",
        "Total Nights Cost",
        "Guest Payout",
        "Host Payout",
        "Cleaning Fee",
        "Tourist Tax",
        "Price by night",
        "Number of Nights",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# Button to refresh data manually (which clears the cache)
if st.button("Refresh Data"):
    st.cache_data.clear()  # clear the cached data
    st.rerun()

# Fetch (or load cached) data
df = fetch_data_from_notion()

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
