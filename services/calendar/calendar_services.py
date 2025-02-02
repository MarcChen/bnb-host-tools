# calendar-api-server/calendar_services.py
import datetime
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import auth functions
from services.oauth_credentials.authentification import (
    load_credentials,
    refresh_access_token,
    print_token_ttl,
)

# Initialize the credentials
token_path = os.getenv("TOKEN_PATH")
creds = load_credentials(token_path)

# Refresh the token if necessary
creds = refresh_access_token(creds, token_path)

# Print the TTL of the token
print_token_ttl(creds)

# Initialize the Google Calendar API service
try:
    service = build("calendar", "v3", credentials=creds)

    # Retrieve the list of calendars
    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get("items", [])

    # Example of selecting a different calendar (by its ID or summary)
    calendar_id = None
    calendar_summary = (
        "Airbnb réservation | Airbnb 预订"  # Change this to the desired calendar name
    )
    for calendar in calendars:
        if calendar["summary"] == calendar_summary:
            calendar_id = calendar["id"]
            break

    if not calendar_id:
        print(f"Calendar '{calendar_summary}' not found.")
    else:
        # Example of adding an event to the selected calendar
        summary = "Sample Event"
        location = "Online"
        description = "This is a sample event."
        start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        end_time = (
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        ).isoformat()

        def add_event(
            service, calendar_id, summary, location, description, start_time, end_time
        ):
            event = {
                "summary": summary,
                "location": location,
                "description": description,
                "start": {
                    "dateTime": start_time,
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": "UTC",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},
                        {"method": "popup", "minutes": 10},
                    ],
                },
            }

            try:
                event = (
                    service.events()
                    .insert(calendarId=calendar_id, body=event)
                    .execute()
                )
                print(f"Event created: {event.get('htmlLink')}")
            except HttpError as error:
                print(f"An error occurred: {error}")

        add_event(
            service, calendar_id, summary, location, description, start_time, end_time
        )

except HttpError as error:
    print(f"An error occurred: {error}")
