import datetime
import os

import pandas as pd
import requests
from ics import Calendar
from notion_client import Client

BLOCKED_DATE_DB_ID = os.environ.get("DATE_DATABASE_ID")
TOKEN = os.environ.get("NOTION_API")


def fetch_blocked_days_from_airbnb_ical(calendar_url: str):
    r = requests.get(calendar_url)
    r.raise_for_status()

    calendar = Calendar(r.text)

    blocked_events = [
        event for event in calendar.events if "Airbnb (Not available)" in event.name
    ]

    data = []
    for evt in blocked_events:
        data.append(
            {
                "start_date": evt.begin.date(),
                "end_date": evt.end.date(),
                "Name": evt.name,
            }
        )
    df_blocked = pd.DataFrame(data)
    return df_blocked


def push_blocked_days_to_notion(calendar_url: str):
    """
    Pushes blocked day entries from an Airbnb iCal URL to a Notion database.

    This function fetches blocked dates from an Airbnb calendar by retrieving data
    from the provided calendar URL and then checks against existing entries in a
    Notion database. For each blocked day record that meets specific criteria (e.g.
    duration of block does not exceed 7 days), it creates a new page in the Notion
    database with the provided details.

    Parameters:
        calendar_url (str):
            The URL of the Airbnb calendar in iCal format from which to fetch blocked dates.

    Side Effects:
        - Queries and creates pages in a Notion database. Existing pages already present
          with the same start and end dates will not be duplicated.
        - Skips inserting records for blocked periods longer than 7 days.
        - The function uses the current timestamp as the insertion date for newly created pages.

    Raises:
        Any exceptions raised by the underlying Notion client upon failure to execute database
        queries or page creation may propagate up to the caller.
    """
    notion_client = Client(auth=TOKEN)
    df_blocked = fetch_blocked_days_from_airbnb_ical(calendar_url)
    existing_pages = notion_client.databases.query(database_id=BLOCKED_DATE_DB_ID).get(
        "results", []
    )

    for _, row in df_blocked.iterrows():
        start = row["start_date"]
        end = row["end_date"]

        if (end - start).days > 7:
            continue

        insert_date = datetime.datetime.now().isoformat()

        if not any(
            str(start) in str(page) and str(end) in str(page) for page in existing_pages
        ):
            notion_client.pages.create(
                parent={"database_id": BLOCKED_DATE_DB_ID},
                properties={
                    "Name": {"title": [{"text": {"content": row["Name"]}}]},
                    "Start Date": {"date": {"start": str(start)}},
                    "End Date": {"date": {"start": str(end)}},
                    "Insert Date": {"date": {"start": insert_date}},
                },
            )


def fetch_blocked_days_from_notion() -> pd.DataFrame:
    notion_client = Client(auth=TOKEN)
    pages = notion_client.databases.query(database_id=BLOCKED_DATE_DB_ID).get(
        "results", []
    )
    data = []
    for page in pages:
        props = page.get("properties", {})
        start_date = props.get("Start Date", {}).get("date", {}).get("start", None)
        end_date = props.get("End Date", {}).get("date", {}).get("start", None)
        name = (
            props.get("Name", {})
            .get("title", [{}])[0]
            .get("text", {})
            .get("content", "")
        )
        insert_date = props.get("Insert Date", {}).get("date", {}).get("start", None)
        data.append(
            {
                "start_date": start_date,
                "end_date": end_date,
                "Name": name,
                "Insert Date": insert_date,
            }
        )
    return pd.DataFrame(data)


if __name__ == "__main__":
    try:
        calendar_url = os.environ.get("CALENDAR_URL")
        push_blocked_days_to_notion(calendar_url)
        print("Successfully pushed blocked days from calendar to Notion")
    except Exception as e:
        print(f"Failed to push blocked days to Notion: {e}")
