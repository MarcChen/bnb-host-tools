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
