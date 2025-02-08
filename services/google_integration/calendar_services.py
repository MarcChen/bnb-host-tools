# calendar-api-server/calendar_services.py
import datetime
import os
import warnings

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import auth functions
from oauth_credentials.authentification import (
    load_credentials,
    print_token_ttl,
    refresh_access_token,
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
        existing_events = (
            self.service.events()
            .list(calendarId=self.calendar_id, singleEvents=True)
            .execute()
            .get("items", [])
        )
        self.existing_event_summaries = set(
            evt.get("summary", "") for evt in existing_events
        )

    def create_event(self, attendees=None, **reservation):
        arrival_date_str = reservation.get("arrival_date")
        departure_date_str = reservation.get("departure_date")
        if not arrival_date_str or not departure_date_str:
            raise ValueError("Missing arrival_date or departure_date in reservation.")

        start_time = datetime.datetime.fromisoformat(arrival_date_str)
        end_time = datetime.datetime.fromisoformat(departure_date_str)
        person_name = reservation.get("name", "Unknown")
        reservation_code = reservation.get("confirmation_code", "")
        adults = reservation.get("number_of_adults", 1)
        children = reservation.get("number_of_children", 0)
        country = reservation.get("country", "France")
        # Replace the existing check with a call to event_exists.
        if self.event_exists(reservation_code):
            warnings.warn(
                f"An event with reservation code '{reservation_code}' already exists.",
                UserWarning,
            )
            return None
        # Create event title and description based on reservation details.
        event_summary = f"{person_name} - {reservation_code}"
        description_en = (
            f"Reservation by {person_name} from {country}. Adults: {adults}"
        )
        if children is not None:
            description_en += f", Children: {children}"
        description_cn = f"{person_name} 的预订，来自 {country}。成人: {adults}"
        if children is not None:
            description_cn += f"，儿童: {children}"
        description = description_en + "\n----\n" + description_cn
        event = {
            "summary": event_summary,
            "location": "7 Rue Curial, 75019 Paris, France",
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
            created_event = (
                self.service.events()
                .insert(calendarId=self.calendar_id, body=event)
                .execute()
            )
            print(f"Event created: {created_event.get('htmlLink')}")
            self.existing_event_summaries.add(event_summary)
            return created_event
        except HttpError as error:
            print(f"An error occurred: {error}")

    def retrieve_events(self, future=True):
        # Retrieve events: if future is True, list events from now onwards; otherwise, past events.
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            if future:
                events_result = (
                    self.service.events()
                    .list(
                        calendarId=self.calendar_id,
                        timeMin=now,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
            else:
                events_result = (
                    self.service.events()
                    .list(
                        calendarId=self.calendar_id,
                        timeMax=now,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
            events = events_result.get("items", [])
            return events
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def delete_event(self, reservation_code):
        # Delete events by filtering events with the given reservation code in their summary.
        try:
            events_result = (
                self.service.events()
                .list(calendarId=self.calendar_id, singleEvents=True)
                .execute()
            )
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

    def event_exists(self, reservation_code):
        # Check if any existing event summary contains the reservation code.
        for summary in self.existing_event_summaries:
            if reservation_code in summary:
                return True
        return False

    def delete_all_reservation_events(self):
        # Delete all events with a reservation code (i.e., with " - " in the summary)
        try:
            events_result = (
                self.service.events()
                .list(calendarId=self.calendar_id, singleEvents=True)
                .execute()
            )
            events = events_result.get("items", [])
            deleted = False
            for event in events:
                summary = event.get("summary", "")
                if (
                    " - " in summary
                ):  # Reservation events follow the "{name} - {reservation_code}" pattern.
                    self.service.events().delete(
                        calendarId=self.calendar_id, eventId=event.get("id")
                    ).execute()
                    print(f"Deleted event: {summary}")
                    deleted = True
            if not deleted:
                print("No reservation events found to delete.")
        except HttpError as error:
            print(f"An error occurred: {error}")


if __name__ == "__main__":
    # svc = CalendarService()
    # Set test start and end times.
    # start = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    # end = start + datetime.timedelta(hours=2)
    # Test: Create an event with reservation details.
    # print("Creating event...")
    # reservation = {
    #     "arrival_date": start.isoformat(),
    #     "departure_date": end.isoformat(),
    #     "name": "John Doe",
    #     "confirmation_code": "ABC123",
    #     "city": "23 Villa Curial",
    #     "number_of_adults": 2,
    #     "number_of_children": 1,
    #     "country": "France"
    # }
    # svc.create_event(**reservation)
    # Test: Retrieve future events.
    # print("Retrieving future events...")
    # future_events = svc.retrieve_events(future=True)
    # for event in future_events:
    #     print(event.get("summary"))
    # Test: Delete event by reservation code.
    # print("Deleting event with reservation code 'ABC123'...")
    # svc.delete_event("ABC123")

    # Test the new method with code "HM43WHMJXZ"
    # svc = CalendarService()
    # exists = svc.event_exists("HM43WHMJXZ")
    # print(f"Event with reservation code 'HM43WHMJXZ' exists:", exists)

    # Delete all events
    svc = CalendarService()
    svc.delete_all_reservation_events()
