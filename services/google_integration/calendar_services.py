# calendar-api-server/calendar_services.py
import datetime
import os
import warnings

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rich import print

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

    def _parse_reservation_data(self, reservation):
        """Parse and validate reservation data.

        Args:
            reservation (dict): Reservation details

        Returns:
            tuple: Parsed data (start_time, end_time, person_name, reservation_code, adults, children, country)

        Raises:
            ValueError: If required fields are missing
        """
        arrival_date_str = reservation.get("arrival_date")
        departure_date_str = reservation.get("departure_date")
        if not arrival_date_str or not departure_date_str:
            raise ValueError("Missing arrival_date or departure_date in reservation.")

        # Parse dates and ensure they have timezone info (UTC)
        start_time = datetime.datetime.fromisoformat(arrival_date_str)
        end_time = datetime.datetime.fromisoformat(departure_date_str)

        # Add timezone info if missing
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=datetime.timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=datetime.timezone.utc)

        person_name = reservation.get("name", "Unknown")
        reservation_code = reservation.get("confirmation_code", "")
        adults = reservation.get("number_of_adults", 1)
        children = reservation.get("number_of_children", 0)
        country = reservation.get("country", "France")

        return (
            start_time,
            end_time,
            person_name,
            reservation_code,
            adults,
            children,
            country,
        )

    def _create_event_content(
        self, person_name, reservation_code, adults, children, country, has_conflict
    ):
        """Create event summary and description.

        Args:
            person_name (str): Guest name
            reservation_code (str): Reservation confirmation code
            adults (int): Number of adult guests
            children (int): Number of child guests
            country (str): Country of origin
            has_conflict (bool): Whether this event conflicts with existing events

        Returns:
            tuple: (event_summary, description)
        """
        # Create event title
        event_summary = f"{person_name} - {reservation_code}"
        if has_conflict:
            event_summary = f"[CONFLICT] {event_summary}"

        # Create English description
        description_en = (
            f"Reservation by {person_name} from {country}. Adults: {adults}"
        )
        if children is not None:
            description_en += f", Children: {children}"
        if has_conflict:
            description_en += (
                "\n⚠️ WARNING: This reservation conflicts with another booking!"
            )

        # Create Chinese description
        description_cn = f"{person_name} 的预订，来自 {country}。成人: {adults}"
        if children is not None:
            description_cn += f"，儿童: {children}"
        if has_conflict:
            description_cn += "\n⚠️ 警告：此预订与其他预订冲突！"

        # Combine descriptions
        description = description_en + "\n----\n" + description_cn

        return event_summary, description

    def _create_reminders(self, has_conflict):
        """Create reminders configuration based on conflict status.

        Args:
            has_conflict (bool): Whether this event conflicts with existing events

        Returns:
            dict: Reminders configuration for the event
        """
        # Default reminders for regular events
        reminders = {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},  # 1 day before
                {"method": "popup", "minutes": 10},
            ],
        }

        # Enhanced reminders for conflicting events
        if has_conflict:
            reminders["overrides"] = [
                {"method": "email", "minutes": 3 * 24 * 60},  # 3 days before
                {"method": "email", "minutes": 24 * 60},  # 1 day before
                {"method": "popup", "minutes": 10},
            ]

        return reminders

    def _build_event_object(
        self, summary, description, start_time, end_time, reminders, attendees=None
    ):
        """Build the complete event object for the API.

        Args:
            summary (str): Event summary/title
            description (str): Event description
            start_time (datetime): Event start time
            end_time (datetime): Event end time
            reminders (dict): Reminders configuration
            attendees (list, optional): List of attendee email addresses

        Returns:
            dict: Complete event object ready for API submission
        """
        event = {
            "summary": summary,
            "location": "7 Rue Curial, 75019 Paris, France",
            "description": description,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            "reminders": reminders,
        }

        # Add attendees if provided
        if attendees is not None:
            event["attendees"] = [{"email": email} for email in attendees]

        return event

    def create_event(self, attendees=None, **reservation):
        """Create a calendar event for a reservation.

        This method creates a Google Calendar event with details from the reservation.
        If the event conflicts with existing events (based on date/time overlap),
        special handling is applied:
        - The event title is prefixed with "[CONFLICT]"
        - Email notifications are set for 3 days and 1 day before the event

        Args:
            attendees (list[str], optional): List of email addresses to be added as attendees.
                For conflict notifications, make sure to include all necessary notification
                email addresses in this list.
            **reservation: Keyword arguments for reservation details including:
                arrival_date (str): ISO format date string for check-in.
                departure_date (str): ISO format date string for check-out.
                name (str): Guest name.
                confirmation_code (str): Reservation confirmation code.
                number_of_adults (int, optional): Number of adult guests. Default is 1.
                number_of_children (int, optional): Number of child guests. Default is 0.
                country (str, optional): Country of origin. Default is "France".

        Returns:
            dict: Created event object from Google Calendar API, or None if event already exists
                  or if an error occurs during creation.

        Raises:
            ValueError: If arrival_date or departure_date are missing from the reservation.
            HttpError: If an API error occurs during event creation.
        """
        # Parse reservation data
        (
            start_time,
            end_time,
            person_name,
            reservation_code,
            adults,
            children,
            country,
        ) = self._parse_reservation_data(reservation)

        # Check for duplicate events
        if self.event_exists(reservation_code):
            warnings.warn(
                f"An event with reservation code '{reservation_code}' already exists.",
                UserWarning,
            )
            return None

        # Check for conflicts with existing events
        has_conflict = self._check_event_conflict(start_time, end_time)

        # Create event content
        event_summary, description = self._create_event_content(
            person_name, reservation_code, adults, children, country, has_conflict
        )

        # Set up reminders
        reminders = self._create_reminders(has_conflict)

        # Build the complete event object
        event = self._build_event_object(
            event_summary, description, start_time, end_time, reminders, attendees
        )

        # Submit the event to Google Calendar API
        try:
            created_event = (
                self.service.events()
                .insert(calendarId=self.calendar_id, body=event)
                .execute()
            )
            print(f"Event created: {created_event.get('htmlLink')}")
            if has_conflict:
                print("⚠️ WARNING: This event conflicts with another booking!")
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

        # Format dates as RFC3339 strings for Google Calendar API
        # Create proper RFC3339 format (always use Z for UTC)
        # This ensures we don't have issues with URL encoding
        past_date = past_date.astimezone(datetime.timezone.utc).replace(microsecond=0)
        reference_date = reference_date.astimezone(datetime.timezone.utc).replace(
            microsecond=0
        )

        past_date_iso = past_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        reference_date_iso = reference_date.strftime("%Y-%m-%dT%H:%M:%SZ")

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
                raise ValueError(
                    f"Too many events found in past day: {len(events)}. Maximum allowed is 2."
                )
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

        # Format dates as RFC3339 strings for Google Calendar API
        # Create proper RFC3339 format (always use Z for UTC)
        # This ensures we don't have issues with URL encoding
        future_date = future_date.astimezone(datetime.timezone.utc).replace(
            microsecond=0
        )
        reference_date = reference_date.astimezone(datetime.timezone.utc).replace(
            microsecond=0
        )

        future_date_iso = future_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        reference_date_iso = reference_date.strftime("%Y-%m-%dT%H:%M:%SZ")

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
                raise ValueError(
                    f"Too many events found in future day: {len(events)}. Maximum allowed is 2."
                )
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
                # Handle different ISO format variations
                if reference_date.endswith("Z"):
                    # If it ends with Z, it's already in UTC
                    dt_str = reference_date[:-1]  # Remove the Z
                    reference_date = datetime.datetime.fromisoformat(dt_str).replace(
                        tzinfo=datetime.timezone.utc
                    )
                elif "+" in reference_date:
                    # If it has a timezone offset
                    reference_date = datetime.datetime.fromisoformat(reference_date)
                else:
                    # No timezone info, assume UTC
                    reference_date = datetime.datetime.fromisoformat(
                        reference_date
                    ).replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                # Fallback to current time if parsing fails
                print(
                    f"Warning: Could not parse date '{reference_date}'. Using current time instead."
                )
                reference_date = datetime.datetime.now(datetime.timezone.utc)

        past_events = self._retrieve_past_day_events(reference_date)
        future_events = self._retrieve_future_day_events(reference_date)

        return past_events + future_events

    def _check_event_conflict(self, start_time, end_time):  # noqa: C901
        """Check if a new event overlaps with existing events.

        Args:
            start_time: The start datetime of the new event
            end_time: The end datetime of the new event

        Returns:
            bool: True if there is a conflict, False otherwise
        """
        # Get events that might overlap with the new event
        past_events = self._retrieve_events_by_proximity(start_time)
        future_events = self._retrieve_events_by_proximity(end_time)

        # Combine events and remove duplicates
        all_events = []
        event_ids = set()

        for event in past_events + future_events:
            event_id = event.get("id")
            if event_id and event_id not in event_ids:
                all_events.append(event)
                event_ids.add(event_id)

        # Check for overlaps
        for event in all_events:
            event_start = event.get("start", {}).get("dateTime")
            event_end = event.get("end", {}).get("dateTime")
            event_summary = event.get("summary", "Unknown event")

            if not event_start or not event_end:
                print(f"Skipping event '{event_summary}' - missing start or end time")
                continue

            try:
                event_start_dt = datetime.datetime.fromisoformat(
                    event_start.replace("Z", "+00:00")
                )
                event_end_dt = datetime.datetime.fromisoformat(
                    event_end.replace("Z", "+00:00")
                )

                # Ensure start_time and end_time have timezone info
                if start_time.tzinfo is None:
                    print("Warning: start_time has no timezone, adding UTC")
                    start_time_aware = start_time.replace(tzinfo=datetime.timezone.utc)
                else:
                    start_time_aware = start_time

                if end_time.tzinfo is None:
                    print("Warning: end_time has no timezone, adding UTC")
                    end_time_aware = end_time.replace(tzinfo=datetime.timezone.utc)
                else:
                    end_time_aware = end_time

                # Check if there's an overlap
                # Case 1: New event starts during an existing event
                case1 = event_start_dt <= start_time_aware <= event_end_dt
                # Case 2: New event ends during an existing event
                case2 = event_start_dt <= end_time_aware <= event_end_dt
                # Case 3: New event completely contains an existing event
                case3 = (
                    start_time_aware <= event_start_dt
                    and end_time_aware >= event_end_dt
                )
                # Case 4: New event is completely contained within an existing event
                case4 = (
                    start_time_aware >= event_start_dt
                    and end_time_aware <= event_end_dt
                )

                if case1 or case2 or case3 or case4:
                    print("CONFLICT DETECTED")
                    return True

            except ValueError as e:
                print(f"Error parsing event dates for '{event_summary}': {e}")
                # Skip events with invalid datetime format
                continue
            except TypeError as e:
                print(f"TypeError comparing dates for '{event_summary}': {e}")
                # Add more diagnostic information without accessing potentially unbound variables
                print(
                    f"New event start timezone: {start_time.tzinfo if hasattr(start_time, 'tzinfo') else 'None'}"
                )
                print(
                    f"New event end timezone: {end_time.tzinfo if hasattr(end_time, 'tzinfo') else 'None'}"
                )
                continue

        print("No conflicts found with any existing events")
        return False

    def delete_event(self, reservation_code):
        """Delete calendar events associated with a specific reservation code.

        This method searches for and deletes any events that contain the specified
        reservation code in their summary.

        Args:
            reservation_code (str): The reservation confirmation code to search for in events.

        Returns:
            None

        Raises:
            HttpError: If an API error occurs during event deletion.
        """
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
        """Check if an event with the given reservation code already exists.

        This method checks the cached event summaries to determine if an event
        with the specified reservation code already exists in the calendar.

        Args:
            reservation_code (str): The reservation confirmation code to check.

        Returns:
            bool: True if an event with this reservation code exists, False otherwise.
        """
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
    # This section has been moved to integration tests.
    # Run integration tests with: poetry run pytest tests/integration/test_calendar_services.py -v
    pass
