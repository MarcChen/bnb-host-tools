import datetime
import logging
import os

import pandas as pd
import requests
from ics import Calendar
from notion_client import Client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)

BLOCKED_DATE_DB_ID = os.environ.get("DATE_DATABASE_ID")
TOKEN = os.environ.get("NOTION_API")


def fetch_blocked_days_from_airbnb_ical(calendar_url: str):
    logger.info(f"Fetching Airbnb iCal from URL: {calendar_url}")
    r = requests.get(calendar_url)
    r.raise_for_status()

    logger.debug("Parsing calendar data from iCal response")
    calendar = Calendar(r.text)

    blocked_events = [
        event for event in calendar.events if "Airbnb (Not available)" in event.name
    ]
    logger.info(f"Found {len(blocked_events)} blocked events in calendar")

    data = []
    for evt in blocked_events:
        logger.debug(
            f"Blocked event: {evt.name}, {evt.begin.date()} to {evt.end.date()}"
        )
        data.append(
            {
                "start_date": evt.begin.date(),
                "end_date": evt.end.date(),
                "Name": evt.name,
            }
        )
    df_blocked = pd.DataFrame(data)
    logger.info(f"Returning DataFrame with {len(df_blocked)} blocked days")
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
    logger.info("Pushing blocked days to Notion database")
    notion_client = Client(auth=TOKEN)
    df_blocked = fetch_blocked_days_from_airbnb_ical(calendar_url)
    logger.debug(f"Fetched {len(df_blocked)} blocked days from Airbnb iCal")
    existing_pages = notion_client.databases.query(database_id=BLOCKED_DATE_DB_ID).get(
        "results", []
    )
    logger.info(f"Fetched {len(existing_pages)} existing pages from Notion database")

    for _, row in df_blocked.iterrows():
        start = row["start_date"]
        end = row["end_date"]

        if (end - start).days > 7:
            logger.debug(
                f"Skipping blocked period from {start} to {end} (>{(end-start).days} days)"
            )
            continue

        insert_date = datetime.datetime.now().isoformat()

        if not any(
            str(start) in str(page) and str(end) in str(page) for page in existing_pages
        ):
            logger.info(
                f"Creating Notion page for blocked period: {start} to {end}, Name: {row['Name']}"
            )
            notion_client.pages.create(
                parent={"database_id": BLOCKED_DATE_DB_ID},
                properties={
                    "Name": {"title": [{"text": {"content": row["Name"]}}]},
                    "Start Date": {"date": {"start": str(start)}},
                    "End Date": {"date": {"start": str(end)}},
                    "Insert Date": {"date": {"start": insert_date}},
                },
            )
        else:
            logger.debug(
                f"Blocked period {start} to {end} already exists in Notion, skipping."
            )


def fetch_blocked_days_from_notion() -> pd.DataFrame:
    logger.info("Fetching blocked days from Notion database")
    notion_client = Client(auth=TOKEN)
    pages = notion_client.databases.query(database_id=BLOCKED_DATE_DB_ID).get(
        "results", []
    )
    logger.debug(f"Fetched {len(pages)} pages from Notion database")
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
        logger.debug(f"Fetched page: {name}, {start_date} to {end_date}")
        data.append(
            {
                "start_date": start_date,
                "end_date": end_date,
                "Name": name,
                "Insert Date": insert_date,
            }
        )
    logger.info(f"Returning DataFrame with {len(data)} blocked days from Notion")
    return pd.DataFrame(data)


if __name__ == "__main__":
    try:
        calendar_url = os.environ.get("CALENDAR_URL")
        logger.info("Starting push_blocked_days_to_notion script")
        push_blocked_days_to_notion(calendar_url)
        logger.info("Successfully pushed blocked days from calendar to Notion")
    except Exception as e:
        logger.error(f"Failed to push blocked days to Notion: {e}", exc_info=True)
