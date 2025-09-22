from datetime import datetime

import plotly.express as px
import streamlit as st

from services.notion_client.notion_api_client import NotionClient


# -----------------------------
# DATA FETCHING & CACHING
# -----------------------------
@st.cache_data(ttl=3600 * 24)
def fetch_data_from_notion():  # noqa: C901
    """Fetch data from Notion via the client and return a cleaned list of dicts."""
    notion_client = NotionClient()
    pages = notion_client.get_all_pages()
    data = [notion_client.parse_page(page) for page in pages]

    # Convert date columns to datetime
    date_cols = ["Arrival Date", "Departure Date", "Mail Date", "Insert Date"]
    for row in data:
        for col in date_cols:
            if col in row and row[col]:
                try:
                    row[col] = datetime.fromisoformat(str(row[col]))
                except Exception:
                    row[col] = None

    # Ensure numeric columns are properly converted.
    num_cols = [
        "Host Service Fee",
        "Guest Service Fee",
        "Total Nights Cost",
        "Guest Payout",
        "Host Payout",
        "Cleaning Fee",
        "Tourist Tax",
        "Price by night",
        "Number of Nights",
    ]
    for row in data:
        for col in num_cols:
            if col in row and row[col] is not None:
                try:
                    row[col] = float(row[col])
                except Exception:
                    row[col] = None

    return data


# Button to refresh data manually (which clears the cache)
if st.button("Refresh Data"):
    st.cache_data.clear()  # clear the cached data
    st.rerun()

# Fetch (or load cached) data
data = fetch_data_from_notion()

# -----------------------------
# GLOBAL FILTERS
# -----------------------------
st.title("Notion Data Visualization")
st.write(
    "Data fetched from Notion. Use the filters and charts below to explore the data."
)

# Create a global year filter based on the "Arrival Date"
years = sorted({row["Arrival Date"].year for row in data if row.get("Arrival Date")})
if years:
    selected_year = st.selectbox("Select Year", options=years)
    filtered = [
        row
        for row in data
        if row.get("Arrival Date") and row["Arrival Date"].year == selected_year
    ]
else:
    st.error("No valid 'Arrival Date' data found.")
    filtered = data.copy()

# -----------------------------
# GRAPH 1: Average Payouts vs. Number of Nights
# -----------------------------
st.subheader("Average Payouts vs. Number of Nights")

# Check required columns
for col in ["Number of Nights", "Host Payout", "Guest Payout"]:
    if not all(col in row for row in filtered):
        st.error(f"Column '{col}' is missing from the data.")
        st.stop()

# Group by Number of Nights and compute average payouts.
grouped = {}
for row in filtered:
    nights = row.get("Number of Nights")
    if nights is not None:
        if nights not in grouped:
            grouped[nights] = {"Host Payout": [], "Guest Payout": []}
        if row.get("Host Payout") is not None:
            grouped[nights]["Host Payout"].append(row["Host Payout"])
        if row.get("Guest Payout") is not None:
            grouped[nights]["Guest Payout"].append(row["Guest Payout"])

grouped_melted = []
for nights, payouts in grouped.items():
    host_avg = (
        sum(payouts["Host Payout"]) / len(payouts["Host Payout"])
        if payouts["Host Payout"]
        else 0
    )
    guest_avg = (
        sum(payouts["Guest Payout"]) / len(payouts["Guest Payout"])
        if payouts["Guest Payout"]
        else 0
    )
    grouped_melted.append(
        {
            "Number of Nights": nights,
            "Payout Type": "Host Payout",
            "Average Payout": host_avg,
        }
    )
    grouped_melted.append(
        {
            "Number of Nights": nights,
            "Payout Type": "Guest Payout",
            "Average Payout": guest_avg,
        }
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
if all("Arrival Date" in row and "Price by night" in row for row in filtered):
    for row in filtered:
        if row.get("Arrival Date"):
            row["month_year"] = row["Arrival Date"].strftime("%Y-%m")
        else:
            row["month_year"] = None
    fig2 = px.box(
        [
            row
            for row in filtered
            if row.get("month_year") and row.get("Price by night") is not None
        ],
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

if all("Arrival Date" in row and "Number of Nights" in row for row in filtered):
    for row in filtered:
        if row.get("Arrival Date"):
            row["month"] = row["Arrival Date"].strftime("%B")
        else:
            row["month"] = None
    fig3 = px.box(
        [
            row
            for row in filtered
            if row.get("month") and row.get("Number of Nights") is not None
        ],
        x="month",
        y="Number of Nights",
        title="Box Plot: Number of Nights by Month (Arrival Date)",
        labels={"month": "Month", "Number of Nights": "Days of Stay"},
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.error("Required columns for box plot analysis are missing.")
