import plotly.express as px
import calendar
import pandas as pd

def plot_host_payout_world_map(df):
    grouped = df.groupby("Country", as_index=False)["Host Payout"].sum()
    fig = px.choropleth(
        grouped,
        locations="Country",
        locationmode="country names",
        color="Host Payout",
        hover_name="Country",
        color_continuous_scale=px.colors.sequential.Plasma,
        title="Host Payout by Country"
    )
    fig.update_layout(
        autosize=True,
        margin={'l': 10, 'r': 10, 't': 30, 'b': 10},
        height=800
    )
    # Update geos to zoom, show all borders and land.
    fig.update_geos(
        visible=True,
        showcountries=True,
        countrycolor="black",
        showland=True,
        landcolor="lightgray"
    )
    return fig

def plot_avg_payout_vs_nights(df):
    # Group by Number of Nights and compute average payouts.
    grouped = (
        df.groupby("Number of Nights")
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
    fig = px.bar(
        grouped_melted,
        x="Number of Nights",
        y="Average Payout",
        color="Payout Type",
        barmode="group",
        title="Average Payout vs. Number of Nights",
    )
    return fig

def plot_boxplot_nightly_price_by_month(df):
    # Ensure month_year column exists based on Arrival Date.
    if "month_year" not in df.columns and "Arrival Date" in df.columns:
        df["month_year"] = df["Arrival Date"].dt.to_period("M").astype(str)
    fig = px.box(
        df,
        x="month_year",
        y="Price by night",
        title="Box Plot: Nightly Price Distribution by Month (Based on Arrival Date)",
        labels={"month_year": "Month-Year", "Price by night": "Nightly Price"},
    )
    return fig

def plot_boxplot_nights_by_month(df):
    # Create month column if missing.
    if "month" not in df.columns and "Arrival Date" in df.columns:
        df["month"] = df["Arrival Date"].dt.strftime("%B")
    fig = px.box(
        df,
        x="month",
        y="Number of Nights",
        title="Box Plot: Number of Nights by Month (Arrival Date)",
        labels={"month": "Month", "Number of Nights": "Days of Stay"},
    )
    return fig

def plot_blocked_days(df_blocked_filtered):
    # Group blocked days data by month_year.
    df_grouped = df_blocked_filtered.groupby("month_year")["blocked_days"].sum().reset_index()
    fig = px.bar(
        df_grouped,
        x="month_year",
        y="blocked_days",
        title="Total Blocked Days per Month",
        labels={"month_year": "Month-Year", "blocked_days": "Total Blocked Days"},
    )
    return fig

def plot_boxplot_price_by_nights(df, category):
    """
    Create a box plot of 'Price by night' grouped by a specified category.
    """
    fig = px.box(
        df,
        x=category,
        y="Price by night",
        title=f"Box Plot: Price by Night by {category}"
    )
    # Add grid lines to the y-axis for enhanced readability.
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=1,
        autorange=True
    )
    return fig

def plot_stacked_month_days(df, df_blocked):
    # Ensure month_year exists in bookings data
    if "month_year" not in df.columns and "Arrival Date" in df.columns:
        df["month_year"] = df["Arrival Date"].dt.to_period("M").astype(str)
    # Aggregate booked days per month from "Number of Nights"
    booked = df.groupby("month_year")["Number of Nights"].sum().rename("Booked Days")
    # Aggregate blocked days per month
    blocked = df_blocked.groupby("month_year")["blocked_days"].sum().rename("Blocked Days")
    # Combine and compute total days per month using calendar.monthrange
    all_months = pd.concat([booked, blocked], axis=1).fillna(0)
    
    total_days = {}
    for month_str in all_months.index:
        year, month = map(int, month_str.split("-"))
        total_days[month_str] = calendar.monthrange(year, month)[1]
    all_months["Total Days"] = pd.Series(total_days)
    # Compute Available Days ensuring non-negative values
    all_months["Available Days"] = (all_months["Total Days"] - all_months["Booked Days"] - all_months["Blocked Days"]).clip(lower=0)
    all_months = all_months.reset_index().rename(columns={"month_year": "Month"})
    # Prepare data for stacked bar chart
    data = all_months.melt(id_vars="Month", value_vars=["Booked Days", "Blocked Days", "Available Days"],
                           var_name="Type", value_name="Days")
    fig = px.bar(data, x="Month", y="Days", color="Type", title="Monthly Days Breakdown",
                 barmode="stack")
    fig.update_layout(margin={'l': 10, 'r': 10, 't': 30, 'b': 10}, height=500)
    return fig
