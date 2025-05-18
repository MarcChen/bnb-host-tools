"""Integration tests for calendar_services module.

Tests in this file require actual credentials and interact with external services
like Google Calendar API. These tests are designed to validate the full
functionality of the calendar services in a real environment.

To run these tests:
    poetry run pytest tests/integration/test_calendar_services.py -v
"""

import datetime

import pytest

from services.google_integration.calendar_services import CalendarService


@pytest.mark.integration
def test_calendar_service_conflict_detection():
    """Integration test for calendar conflict detection functionality.

    This test:
    1. Creates a first calendar event
    2. Attempts to create an overlapping event to trigger conflict detection
    3. Verifies the conflict is properly identified and handled
    4. Cleans up by deleting both test events
    """
    # Initialize calendar service
    svc = CalendarService()

    # Test the create_event method with conflict detection
    print("\n=== Testing create_event with conflict detection ===")

    # Set up base datetime for testing - 5 months in the future to avoid conflicts with real events
    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5 * 30)

    # First reservation - Create a regular event
    start1 = now + datetime.timedelta(days=2)
    end1 = start1 + datetime.timedelta(days=3)
    print("\n1. Creating first reservation (should succeed):")
    reservation1 = {
        "arrival_date": start1.isoformat(),
        "departure_date": end1.isoformat(),
        "name": "John Smith",
        "confirmation_code": "TEST001",
        "number_of_adults": 2,
        "number_of_children": 0,
        "country": "USA",
    }

    # Create with standard notification email
    attendees = ["test@example.com"]
    event1 = svc.create_event(attendees=attendees, **reservation1)

    assert event1 is not None, "Failed to create first test event"
    print(f"First event created successfully: {event1.get('summary')}")

    try:
        # Second reservation - should create a conflict with first reservation
        print("\n2. Creating overlapping reservation (should show CONFLICT):")
        # Create partially overlapping period
        start2 = end1 - datetime.timedelta(
            hours=6
        )  # Overlaps with end of first reservation
        end2 = end1 + datetime.timedelta(days=2)

        reservation2 = {
            "arrival_date": start2.isoformat(),
            "departure_date": end2.isoformat(),
            "name": "Jane Doe",
            "confirmation_code": "TEST002",
            "number_of_adults": 1,
            "number_of_children": 1,
            "country": "France",
        }

        # For conflict notifications, include all necessary notification email addresses
        conflict_attendees = [
            "admin@example.com",  # Primary admin notification
            "host@example.com",  # Host notification
            "manager@example.com",  # Property manager notification
        ]
        event2 = svc.create_event(attendees=conflict_attendees, **reservation2)

        assert event2 is not None, "Failed to create second test event"
        print(f"Second event created with status: {event2.get('summary')}")

        # Check if [CONFLICT] prefix is present
        assert "[CONFLICT]" in event2.get("summary", ""), "Conflict detection failed"
        print("✅ Conflict detection successful!")

        # Additional checks on conflict event
        assert "⚠️ WARNING" in event2.get(
            "description", ""
        ), "Conflict warning not found in description"

        # Check reminders
        reminders = event2.get("reminders", {}).get("overrides", [])
        reminder_minutes = [
            r.get("minutes") for r in reminders if r.get("method") == "email"
        ]
        assert (
            3 * 24 * 60 in reminder_minutes
        ), "3-day email reminder not set for conflict event"
        assert (
            24 * 60 in reminder_minutes
        ), "1-day email reminder not set for conflict event"

        # Check attendees were properly included
        event_attendees = event2.get("attendees", [])
        attendee_emails = [a.get("email") for a in event_attendees]
        for email in conflict_attendees:
            assert (
                email in attendee_emails
            ), f"Expected attendee email {email} not found"

    finally:
        # Clean up test events
        print("\n3. Cleaning up test events:")
        svc.delete_event("TEST001")
        svc.delete_event("TEST002")


@pytest.mark.integration
def test_retrieve_events_by_proximity():
    """Integration test for the _retrieve_events_by_proximity method.

    This test verifies that the method correctly retrieves events near a reference date.
    """
    # Initialize calendar service
    svc = CalendarService()

    # Set reference date to current time
    now = datetime.datetime.now(datetime.timezone.utc)

    # Retrieve events
    events = svc._retrieve_events_by_proximity(now)
    print(f"Events by proximity to {now.strftime('%Y-%m-%d %H:%M:%S')}:")

    # Verify the returned structure
    assert isinstance(events, list), "Expected a list of events"

    # Display found events (if any)
    if events:
        for i, event in enumerate(events[:5]):  # Show first 5 events
            start_time = event.get("start", {}).get("dateTime")
            if start_time:
                print(f"{i+1}. {event.get('summary')} - Start: {start_time}")
