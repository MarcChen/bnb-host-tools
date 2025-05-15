import datetime

import pytest

# Import CalendarService from its module.
from services.google_integration import calendar_services

# --- Minimal fake implementations for external dependencies ---


class FakeService:
    def __init__(self):
        self.fake_events = self.FakeEvents()  # store single FakeEvents instance

    def calendarList(self):
        return self.FakeCalendarList()

    class FakeCalendarList:
        def list(self):
            return self

        def execute(self):
            return {
                "items": [
                    {"summary": "Airbnb réservation | Airbnb 预订", "id": "primary"}
                ]
            }

    def events(self):
        return self.fake_events  # return the stored instance

    class FakeEvents:
        def __init__(self):
            self.deleted_ids = []  # track deleted event IDs
            self.events = []  # track inserted events

        def list(self, **kwargs):
            return self

        def execute(self):
            # Return events if set; otherwise, empty list
            return {"items": self.events}

        def insert(self, **kwargs):
            body = kwargs.get("body", {})
            body["htmlLink"] = "http://fake.calendar/event"
            # Add event to self.events for later reference.
            self.events.append(body)
            return FakeInsert(body)

        def delete(self, **kwargs):
            event_id = kwargs.get("eventId")
            self.deleted_ids.append(event_id)
            return FakeDelete()


class FakeInsert:
    def __init__(self, body):
        self.body = body

    def execute(self):
        return self.body


class FakeDelete:
    def execute(self):
        return None


def fake_load_credentials(token_path):
    return "fake_creds"


def fake_refresh_access_token(creds, token_path):
    return creds


def fake_print_token_ttl(creds):
    pass


def fake_build(service_name, version, credentials):
    return FakeService()


# --- Patch external dependencies ---
@pytest.fixture(autouse=True)
def patch_google(monkeypatch):
    monkeypatch.setattr(calendar_services, "build", fake_build)
    monkeypatch.setattr(calendar_services, "load_credentials", fake_load_credentials)
    monkeypatch.setattr(
        calendar_services, "refresh_access_token", fake_refresh_access_token
    )
    monkeypatch.setattr(calendar_services, "print_token_ttl", fake_print_token_ttl)
    monkeypatch.setenv("TOKEN_PATH", "/dummy/path")


# --- Tests ---


def test_init_calendar_service():
    svc = calendar_services.CalendarService()
    # Verify calendar_id is set to the fake calendar id.
    assert svc.calendar_id == "primary"
    # Initially, no events exist.
    assert svc.existing_event_summaries == set()


def test_event_exists(monkeypatch):
    svc = calendar_services.CalendarService()
    # Pre-populate existing events.
    svc.existing_event_summaries.add("Alice - DUPLICATE")
    assert svc.event_exists("DUPLICATE") is True
    assert svc.event_exists("NONEXISTENT") is False


def test_create_event_duplicate():
    svc = calendar_services.CalendarService()
    svc.existing_event_summaries.add("Alice - CODE123")
    reservation = {
        "arrival_date": datetime.datetime.now().isoformat(),
        "departure_date": (
            datetime.datetime.now() + datetime.timedelta(hours=2)
        ).isoformat(),
        "name": "Alice",
        "confirmation_code": "CODE123",
        "number_of_adults": 2,
        "number_of_children": 0,
        "country": "France",
    }
    with pytest.warns(UserWarning, match="already exists"):
        result = svc.create_event(**reservation)
    assert result is None


def test_create_event_success():
    svc = calendar_services.CalendarService()
    reservation = {
        "arrival_date": datetime.datetime.now().isoformat(),
        "departure_date": (
            datetime.datetime.now() + datetime.timedelta(hours=2)
        ).isoformat(),
        "name": "Bob",
        "confirmation_code": "NEWCODE",
        "number_of_adults": 1,
        "number_of_children": 0,
        "country": "France",
    }
    result = svc.create_event(**reservation)
    assert result is not None
    assert result.get("htmlLink") == "http://fake.calendar/event"
    assert "Bob - NEWCODE" in svc.existing_event_summaries


# def test_retrieve_events(monkeypatch):
#     svc = calendar_services.CalendarService()
#     # Populate fake events in the fake events service.
#     fake_events = svc.service.events()
#     fake_events.events = [
#         {"summary": "Event1", "start": {"dateTime": "2023-01-01T00:00:00Z"}},
#         {"summary": "Event2", "start": {"dateTime": "2023-12-31T00:00:00Z"}},
#     ]
#     # Test future events retrieval.
#     future_events = svc.retrieve_events(future=True)
#     assert isinstance(future_events, list)
#     # Test past events retrieval.
#     past_events = svc.retrieve_events(future=False)
#     assert isinstance(past_events, list)


def test_delete_event(monkeypatch):
    svc = calendar_services.CalendarService()
    fake_events = svc.service.events()
    # Create an event with a known reservation code.
    event = {"id": "evt1", "summary": "Diana - DEL123"}
    fake_events.events = [event]
    # Call delete_event.
    svc.delete_event("DEL123")
    # Check that deletion was recorded.
    assert "evt1" in fake_events.deleted_ids


def test_delete_all_reservation_events(monkeypatch):
    svc = calendar_services.CalendarService()
    fake_events = svc.service.events()
    # Create multiple events with and without reservation pattern.
    fake_events.events = [
        {"id": "evt1", "summary": "Eve - RES001"},
        {"id": "evt2", "summary": "Meeting"},
        {"id": "evt3", "summary": "Frank - RES002"},
    ]
    svc.delete_all_reservation_events()
    # Only events with " - " in summary should be deleted.
    assert "evt1" in fake_events.deleted_ids
    assert "evt3" in fake_events.deleted_ids
    assert "evt2" not in fake_events.deleted_ids


def test_check_event_conflict():
    """Test the _check_event_conflict method."""
    svc = calendar_services.CalendarService()
    
    # Setup: Override the _retrieve_events_by_proximity method to return fake events
    def mock_retrieve_events(reference_date=None):
        # Return fake events that overlap with our test period
        return [
            {
                "id": "evt1",
                "summary": "Existing Event",
                "start": {"dateTime": "2023-05-15T10:00:00Z"},
                "end": {"dateTime": "2023-05-18T12:00:00Z"}
            }
        ]
    
    # Replace the real method with our mock
    original_retrieve = svc._retrieve_events_by_proximity
    svc._retrieve_events_by_proximity = mock_retrieve_events
    
    try:
        # Test case 1: New event starts during existing event (conflict)
        start_time = datetime.datetime.fromisoformat("2023-05-17T08:00:00+00:00")
        end_time = datetime.datetime.fromisoformat("2023-05-20T12:00:00+00:00")
        assert svc._check_event_conflict(start_time, end_time) is True
        
        # Test case 2: New event ends during existing event (conflict)
        start_time = datetime.datetime.fromisoformat("2023-05-14T08:00:00+00:00")
        end_time = datetime.datetime.fromisoformat("2023-05-16T12:00:00+00:00")
        assert svc._check_event_conflict(start_time, end_time) is True
        
        # Test case 3: New event completely contains existing event (conflict)
        start_time = datetime.datetime.fromisoformat("2023-05-14T08:00:00+00:00")
        end_time = datetime.datetime.fromisoformat("2023-05-20T12:00:00+00:00")
        assert svc._check_event_conflict(start_time, end_time) is True
        
        # Test case 4: New event is completely contained within existing event (conflict)
        start_time = datetime.datetime.fromisoformat("2023-05-16T08:00:00+00:00")
        end_time = datetime.datetime.fromisoformat("2023-05-17T12:00:00+00:00")
        assert svc._check_event_conflict(start_time, end_time) is True
        
        # Test case 5: No overlap (no conflict)
        start_time = datetime.datetime.fromisoformat("2023-05-20T08:00:00+00:00")
        end_time = datetime.datetime.fromisoformat("2023-05-22T12:00:00+00:00")
        assert svc._check_event_conflict(start_time, end_time) is False
        
    finally:
        # Restore the original method
        svc._retrieve_events_by_proximity = original_retrieve


def test_create_event_with_conflict():
    """Test creating an event that conflicts with another event."""
    svc = calendar_services.CalendarService()
    
    # Setup: Override the _check_event_conflict method to simulate a conflict
    original_check = svc._check_event_conflict
    svc._check_event_conflict = lambda start_time, end_time: True
    
    try:
        # Create an event (with simulated conflict)
        reservation = {
            "arrival_date": datetime.datetime.now().isoformat(),
            "departure_date": (
                datetime.datetime.now() + datetime.timedelta(hours=24)
            ).isoformat(),
            "name": "Conflict Person",
            "confirmation_code": "CONFLICT123",
            "number_of_adults": 2,
            "number_of_children": 1,
            "country": "USA",
        }
        
        # Test with attendees for notifications
        attendees = ["notify1@example.com", "notify2@example.com"]
        result = svc.create_event(attendees=attendees, **reservation)
        
        # Verify the event was created with conflict indicators
        assert result is not None
        assert result.get("summary").startswith("[CONFLICT]")
        assert "Conflict Person - CONFLICT123" in result.get("summary")
        
        # Check reminders were set for 3 days and 1 day before
        reminders = result.get("reminders", {}).get("overrides", [])
        reminder_minutes = [r.get("minutes") for r in reminders if r.get("method") == "email"]
        assert 3 * 24 * 60 in reminder_minutes  # 3 days
        assert 24 * 60 in reminder_minutes  # 1 day
        
        # Verify attendees were properly set
        event_attendees = result.get("attendees", [])
        attendee_emails = [a.get("email") for a in event_attendees]
        assert "notify1@example.com" in attendee_emails
        assert "notify2@example.com" in attendee_emails
        
        # Verify the event description contains conflict warning
        assert "⚠️ WARNING" in result.get("description")
        
    finally:
        # Restore the original method
        svc._check_event_conflict = original_check


def test_create_event_without_conflict():
    """Test creating an event that does not conflict with other events."""
    svc = calendar_services.CalendarService()
    
    # Setup: Override the _check_event_conflict method to simulate no conflict
    original_check = svc._check_event_conflict
    svc._check_event_conflict = lambda start_time, end_time: False
    
    try:
        # Create an event (with no conflict)
        reservation = {
            "arrival_date": datetime.datetime.now().isoformat(),
            "departure_date": (
                datetime.datetime.now() + datetime.timedelta(hours=24)
            ).isoformat(),
            "name": "Normal Person",
            "confirmation_code": "NORMAL123",
            "number_of_adults": 2,
            "number_of_children": 0,
            "country": "Canada",
        }
        
        # Test with regular attendees
        attendees = ["regular@example.com"]
        result = svc.create_event(attendees=attendees, **reservation)
        
        # Verify the event was created without conflict indicators
        assert result is not None
        assert not result.get("summary").startswith("[CONFLICT]")
        assert result.get("summary") == "Normal Person - NORMAL123"
        
        # Check reminders were set only for 1 day before (standard behavior)
        reminders = result.get("reminders", {}).get("overrides", [])
        reminder_minutes = [r.get("minutes") for r in reminders if r.get("method") == "email"]
        assert 3 * 24 * 60 not in reminder_minutes  # No 3-day reminder
        assert 24 * 60 in reminder_minutes  # 1 day
        
        # Verify only the regular attendee was set
        event_attendees = result.get("attendees", [])
        attendee_emails = [a.get("email") for a in event_attendees]
        assert len(attendee_emails) == 1
        assert "regular@example.com" in attendee_emails
        
        # Verify the event description does not contain conflict warning
        assert "⚠️ WARNING" not in result.get("description")
        
    finally:
        # Restore the original method
        svc._check_event_conflict = original_check
