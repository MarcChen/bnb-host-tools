import os
import pandas as pd
from services.notion_client.notion_api_client import NotionClient
from get_blocked_days import fetch_blocked_days_from_notion
from .cache import load_or_fetch
import pycountry

def convert_country_code(code):
    if not isinstance(code, str):
        return code
    # If it's a two-letter country code, try converting it
    if len(code) == 2:
        country = pycountry.countries.get(alpha_2=code.upper())
        if country:
            return country.name
    return code

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
    if "Country" in df.columns:
        df["Country"] = df["Country"].apply(convert_country_code)
    return df

def fetch_data_from_notion():
    cache_path = os.getenv("PROJECT_ROOT") + "/services/dataviz/data/df_notion_cache.csv"
    df = load_or_fetch(cache_path, get_notion_data)
    for col in ["Arrival Date", "Departure Date", "Mail Date", "Insert Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

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
