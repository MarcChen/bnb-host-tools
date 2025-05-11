# calendar-api-server/calendar_services.py
import datetime
import os
import warnings
from rich import print

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import auth functions
from services.google_integration.authentification import (
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

    def _retrieve_past_day_events(self, reference_date):
        """Retrieve events from the past day relative to a reference date.
        
        Args:
            reference_date: The reference datetime to measure from
        
        Returns:
            List of past events ordered by startTime (earliest first)
            
        Raises:
            ValueError: If more than 2 events are found in the given time range
        """
        past_date = reference_date - datetime.timedelta(days=1)
        past_date_iso = past_date.isoformat()
        reference_date_iso = reference_date.isoformat()
        
        try:
            past_events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMax=reference_date_iso,
                    timeMin=past_date_iso,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = past_events_result.get("items", [])
            if len(events) > 2:
                raise ValueError(f"Too many events found in past day: {len(events)}. Maximum allowed is 2.")
            return events
        except HttpError as error:
            print(f"An error occurred retrieving past events: {error}")
            return []
    
    def _retrieve_future_day_events(self, reference_date):
        """Retrieve events for the next day relative to a reference date.
        
        Args:
            reference_date: The reference datetime to measure from
        
        Returns:
            List of future events ordered by startTime (earliest first)
            
        Raises:
            ValueError: If more than 2 events are found in the given time range
        """
        future_date = reference_date + datetime.timedelta(days=1)
        future_date_iso = future_date.isoformat()
        reference_date_iso = reference_date.isoformat()
        
        try:
            future_events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMax=future_date_iso,
                    timeMin=reference_date_iso,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = future_events_result.get("items", [])
            if len(events) > 2:
                raise ValueError(f"Too many events found in future day: {len(events)}. Maximum allowed is 2.")
            return events
        except HttpError as error:
            print(f"An error occurred retrieving future events: {error}")
            return []

    def _retrieve_events_by_proximity(self, reference_date=None):
        """Retrieve events sorted by proximity to a reference date.
        Returns closest past events (within one day) followed by closest future events (within one day).
        
        Args:
            reference_date: The reference date to measure proximity against.
                           Can be a datetime object or an ISO format string.
                           If None, current time is used.
        
        Returns:
            List of events sorted by proximity to the reference date.
            
        Raises:
            ValueError: If more than 2 events are found in either past or future time range
        """
        # Process reference date
        if reference_date is None:
            reference_date = datetime.datetime.now(datetime.timezone.utc)
        elif isinstance(reference_date, str):
            try:
                reference_date = datetime.datetime.fromisoformat(reference_date.replace('Z', '+00:00'))
                if reference_date.tzinfo is None:
                    reference_date = reference_date.replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                raise ValueError("Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS+00:00)")
        
        past_events = self._retrieve_past_day_events(reference_date)
        future_events = self._retrieve_future_day_events(reference_date)
        
        return past_events + future_events

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
    # svc = CalendarService()
    # svc.delete_all_reservation_events()


    # Test the new _retrieve_events_by_proximity function
    svc = CalendarService()
    
    # Test with current date
    print("\n=== Testing with current date ===")
    now = datetime.datetime.now(datetime.timezone.utc)
    events = svc._retrieve_events_by_proximity(now)
    print(f"Events by proximity to {now.strftime('%Y-%m-%d %H:%M:%S')}:")
    print(events)
    
    # Test with a specific date
    # print("\n=== Testing with specific date ===")
    # specific_date = datetime.datetime(2025, 5, 15, tzinfo=datetime.timezone.utc)
    # events = svc._retrieve_events_by_proximity(specific_date)
    # print(f"Events by proximity to {specific_date.strftime('%Y-%m-%d %H:%M:%S')}:")
    
    # # Test with string date
    # print("\n=== Testing with string date ===")
    # date_string = "2025-06-01T12:00:00+00:00"
    # events = svc._retrieve_events_by_proximity(date_string)
    # print(f"Events by proximity to {date_string}:")
    
    # # Display events
    # if events:
    #     reference_date = datetime.datetime.fromisoformat(date_string)
    #     for i, event in enumerate(events[:5]):  # Show first 5 events
    #         start_time = event.get("start", {}).get("dateTime")
    #         if start_time:
    #             try:
    #                 event_time = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    #                 time_diff = event_time - reference_date
    #                 days_diff = time_diff.days
    #                 hours_diff = (time_diff.seconds // 3600)
                    
    #                 past_future = "PAST" if time_diff.total_seconds() < 0 else "FUTURE"
    #                 print(f"{i+1}. {past_future}: {event.get('summary')} - {abs(days_diff)}d {abs(hours_diff)}h {'before' if past_future == 'PAST' else 'after'} reference date")
    #             except ValueError:
    #                 print(f"{i+1}. Error parsing date: {event.get('summary')} - {start_time}")
    # else:
    #     print("No events found")