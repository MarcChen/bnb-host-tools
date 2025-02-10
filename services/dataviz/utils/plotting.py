import plotly.express as px

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

# ...existing code if any...
