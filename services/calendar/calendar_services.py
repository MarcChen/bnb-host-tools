# calendar-api-server/calendar_services.py
import datetime
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import auth functions
from oauth_credentials.authentification import (
    load_credentials,
    refresh_access_token,
    print_token_ttl,
)

class CalendarService:
    def __init__(self, calendar_summary="Airbnb réservation | Airbnb 预订"):
        # Authenticate and build calendar service
        token_path = os.getenv("TOKEN_PATH")
        creds = load_credentials(token_path)
        creds = refresh_access_token(creds, token_path)
        print_token_ttl(creds)
        self.service = build("calendar", "v3", credentials=creds)
        # Select calendar by its summary
        calendar_list = self.service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])
        self.calendar_id = None
        for calendar in calendars:
            if calendar.get("summary") == calendar_summary:
                self.calendar_id = calendar.get("id")
                break
        if not self.calendar_id:
            raise ValueError(f"Calendar '{calendar_summary}' not found.")

    def create_event(self, start_time, end_time, person_name, reservation_code, location, adults, children=None, country="France", attendees=None):
        # Create event title and description based on reservation details.
        event_summary = f"{person_name} - {reservation_code}"
        description_en = f"Reservation by {person_name} from {country}. Adults: {adults}"
        if children is not None:
            description_en += f", Children: {children}"
        description_cn = f"{person_name} 的预订，来自 {country}。成人: {adults}"
        if children is not None:
            description_cn += f"，儿童: {children}"
        description = description_en + "\n----\n" + description_cn
        event = {
            "summary": event_summary,
            "location": location,
            "description": description,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 10},
            ],
            },
        }
        # Add attendees if provided.
        if attendees is not None:
            event["attendees"] = [{"email": email} for email in attendees]
        try:
            created_event = self.service.events().insert(
                calendarId=self.calendar_id, body=event
            ).execute()
            print(f"Event created: {created_event.get('htmlLink')}")
            return created_event
        except HttpError as error:
            print(f"An error occurred: {error}")

    def retrieve_events(self, future=True):
        # Retrieve events: if future is True, list events from now onwards; otherwise, past events.
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            if future:
                events_result = self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=now,
                    singleEvents=True,
                    orderBy="startTime"
                ).execute()
            else:
                events_result = self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMax=now,
                    singleEvents=True,
                    orderBy="startTime"
                ).execute()
            events = events_result.get("items", [])
            return events
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def delete_event(self, reservation_code):
        # Delete events by filtering events with the given reservation code in their summary.
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                singleEvents=True
            ).execute()
            events = events_result.get("items", [])
            deleted = False
            for event in events:
                if reservation_code in event.get("summary", ""):
                    self.service.events().delete(
                        calendarId=self.calendar_id, eventId=event.get("id")
                    ).execute()
                    print(f"Deleted event: {event.get('summary')}")
                    deleted = True
            if not deleted:
                print(f"No event found with reservation code: {reservation_code}")
        except HttpError as error:
            print(f"An error occurred: {error}")

if __name__ == '__main__':
    # Test the CalendarService functionalities
    svc = CalendarService()
    # Set test start and end times.
    start = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    end = start + datetime.timedelta(hours=2)
    # Test: Create an event with reservation details.
    print("Creating event...")
    svc.create_event(
        start_time=start,
        end_time=end,
        person_name="John Doe",
        reservation_code="ABC123",
        location="23 Villa Curial",
        adults=2,
        children=1,
        # attendees=["chen987415@gmail.com"]
    )
    # Test: Retrieve future events.
    print("Retrieving future events...")
    future_events = svc.retrieve_events(future=True)
    for event in future_events:
        print(event.get("summary"))
    # Test: Delete event by reservation code.
    print("Deleting event with reservation code 'ABC123'...")
    # svc.delete_event("ABC123")
