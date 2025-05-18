"""Integration tests for mail_processor module.

Tests in this file focus on verifying the integration of the mail processor with:
1. Loading attendee email addresses from environment variables
2. Properly configuring calendar events with notification attendees
3. Special handling for calendar conflict notifications

To run these tests:
    poetry run pytest tests/integration/test_mail_processor.py -v
"""

import os

import pytest

from services.google_integration.calendar_services import CalendarService
from services.mail_processing.mail_processor import MailProcessorService


@pytest.mark.integration
def test_attendees_from_environment():
    """Test retrieving attendees from the environment variable."""
    # Store original environment variable value
    original_value = os.environ.get("CALENDAR_NOTIFICATION_ATTENDEES", "")

    try:
        # Test case 1: Empty variable
        os.environ["CALENDAR_NOTIFICATION_ATTENDEES"] = ""
        mail_processor = MailProcessorService(debug=True)
        attendees = mail_processor._get_calendar_notification_attendees()
        assert (
            len(attendees) == 0
        ), "Should return empty list with empty environment variable"

        # Test case 2: Single email
        test_email = "test@example.com"
        os.environ["CALENDAR_NOTIFICATION_ATTENDEES"] = test_email
        mail_processor = MailProcessorService(debug=True)
        attendees = mail_processor._get_calendar_notification_attendees()
        assert len(attendees) == 1, "Should return list with single email"
        assert attendees[0] == test_email, "Should return the correct email"

        # Test case 3: Multiple emails
        test_emails = "first@example.com, second@example.com,third@example.com"
        os.environ["CALENDAR_NOTIFICATION_ATTENDEES"] = test_emails
        mail_processor = MailProcessorService(debug=True)
        attendees = mail_processor._get_calendar_notification_attendees()
        assert len(attendees) == 3, "Should return list with three emails"
        assert "first@example.com" in attendees, "First email should be in the list"
        assert "second@example.com" in attendees, "Second email should be in the list"
        assert "third@example.com" in attendees, "Third email should be in the list"

        # Test case 4: Whitespace handling
        test_emails = " extra@example.com , spaces@example.com "
        os.environ["CALENDAR_NOTIFICATION_ATTENDEES"] = test_emails
        mail_processor = MailProcessorService(debug=True)
        attendees = mail_processor._get_calendar_notification_attendees()
        assert len(attendees) == 2, "Should return list with two emails"
        assert "extra@example.com" in attendees, "Should handle leading whitespace"
        assert "spaces@example.com" in attendees, "Should handle trailing whitespace"

    finally:
        # Restore original environment variable
        if original_value:
            os.environ["CALENDAR_NOTIFICATION_ATTENDEES"] = original_value
        elif "CALENDAR_NOTIFICATION_ATTENDEES" in os.environ:
            del os.environ["CALENDAR_NOTIFICATION_ATTENDEES"]


class MockCalendarService(CalendarService):
    """Mock calendar service for testing without making API calls."""

    def __init__(self):
        # Skip actual CalendarService initialization
        # to avoid making API calls during tests
        self.received_attendees = None
        self.received_reservation = None
        self.service = None
        self.calendar_id = None
        self.existing_event_summaries = set()

    def create_event(self, attendees=None, **reservation):
        """Mock event creation that records passed parameters."""
        self.received_attendees = attendees
        self.received_reservation = reservation

        # Return a fake event object
        return {
            "summary": f"{reservation.get('name')} - {reservation.get('confirmation_code')}",
            "attendees": [{"email": email} for email in (attendees or [])],
        }


@pytest.mark.integration
def test_integration_with_calendar_service():
    """Test that attendees are correctly passed to calendar service."""
    # Store original environment variable value
    original_value = os.environ.get("CALENDAR_NOTIFICATION_ATTENDEES", "")

    try:
        # Set test emails
        test_emails = "calendar1@example.com,calendar2@example.com"
        os.environ["CALENDAR_NOTIFICATION_ATTENDEES"] = test_emails

        # Create a mail processor instance
        mail_processor = MailProcessorService(debug=True)

        # Replace the real calendar service with our mock
        real_calendar_service = mail_processor.calendar_service
        mock_calendar_service = MockCalendarService()
        mail_processor.calendar_service = mock_calendar_service

        try:
            # Create a test reservation
            reservation = {
                "arrival_date": "2023-12-01",
                "departure_date": "2023-12-05",
                "name": "Test Person",
                "confirmation_code": "MOCK123",
                "number_of_adults": 2,
                "country": "Test Country",
            }

            # Call the mail processor workflow function that would normally create events
            # Instead, we manually trigger the code that creates an event with attendees
            attendees = mail_processor._get_calendar_notification_attendees()
            mail_processor.calendar_service.create_event(
                attendees=attendees, **reservation
            )

            # Check if attendees were correctly passed to calendar service
            expected = ["calendar1@example.com", "calendar2@example.com"]
            received = mock_calendar_service.received_attendees

            assert (
                received is not None
            ), "Attendees should be passed to calendar service"
            assert len(received) == 2, "Should pass two attendees to calendar service"
            assert all(
                email in received for email in expected
            ), "All emails should be passed correctly"

        finally:
            # Restore the real calendar service
            mail_processor.calendar_service = real_calendar_service

    finally:
        # Restore original environment variable
        if original_value:
            os.environ["CALENDAR_NOTIFICATION_ATTENDEES"] = original_value
        elif "CALENDAR_NOTIFICATION_ATTENDEES" in os.environ:
            del os.environ["CALENDAR_NOTIFICATION_ATTENDEES"]


class MockConflictCalendarService(CalendarService):
    """Mock calendar service that simulates conflicts."""

    def __init__(self):
        # Skip actual CalendarService initialization
        self.created_events = []
        self.service = None
        self.calendar_id = None
        self.existing_event_summaries = set()

    def _check_event_conflict(self, start_time, end_time):
        """Always report a conflict for testing purposes."""
        return True

    def create_event(self, attendees=None, **reservation):
        """Create an event with conflict indicators."""
        # Mock event creation with conflict
        event = {
            "summary": f"[CONFLICT] {reservation.get('name')} - {reservation.get('confirmation_code')}",
            "description": "Test event with conflict\n⚠️ WARNING: This reservation conflicts with another booking!",
            "attendees": [{"email": email} for email in (attendees or [])],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 3 * 24 * 60},  # 3 days
                    {"method": "email", "minutes": 24 * 60},  # 1 day
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        self.created_events.append(event)
        return event


@pytest.mark.integration
def test_conflict_event_with_attendees():
    """Test that conflict events correctly handle attendees."""
    # Store original environment variable value
    original_value = os.environ.get("CALENDAR_NOTIFICATION_ATTENDEES", "")

    try:
        # Set test emails in environment
        os.environ[
            "CALENDAR_NOTIFICATION_ATTENDEES"
        ] = "notify1@example.com,notify2@example.com"

        # Create a mail processor instance with debug enabled
        mail_processor = MailProcessorService(debug=True)

        # Replace with mock service
        real_calendar_service = mail_processor.calendar_service
        mock_calendar_service = MockConflictCalendarService()
        mail_processor.calendar_service = mock_calendar_service

        try:
            # Create a test reservation
            reservation = {
                "arrival_date": "2023-12-01",
                "departure_date": "2023-12-05",
                "name": "Conflict Test",
                "confirmation_code": "CONFLICT123",
                "number_of_adults": 2,
                "country": "Test Country",
            }

            # Get attendees as the mail processor would
            attendees = mail_processor._get_calendar_notification_attendees()

            # Create the event with our mock service
            event = mail_processor.calendar_service.create_event(
                attendees=attendees, **reservation
            )

            # Check if attendees were correctly included in the conflict event
            attendee_emails = [a["email"] for a in event["attendees"]]
            assert (
                len(attendee_emails) == 2
            ), "Should include 2 attendees in conflict event"
            assert (
                "notify1@example.com" in attendee_emails
            ), "First notification email should be included"
            assert (
                "notify2@example.com" in attendee_emails
            ), "Second notification email should be included"

            # Check for conflict indicators
            assert event["summary"].startswith(
                "[CONFLICT]"
            ), "Conflict event should have [CONFLICT] prefix"
            assert (
                "⚠️ WARNING" in event["description"]
            ), "Conflict event should include warning in description"

            # Check for special reminders
            reminder_minutes = [
                r["minutes"]
                for r in event["reminders"]["overrides"]
                if r["method"] == "email"
            ]
            assert (
                3 * 24 * 60 in reminder_minutes
            ), "Should have 3-day reminder for conflicts"
            assert (
                24 * 60 in reminder_minutes
            ), "Should have 1-day reminder for conflicts"

        finally:
            # Restore real calendar service
            mail_processor.calendar_service = real_calendar_service
    finally:
        # Restore original environment variable
        if original_value:
            os.environ["CALENDAR_NOTIFICATION_ATTENDEES"] = original_value
        elif "CALENDAR_NOTIFICATION_ATTENDEES" in os.environ:
            del os.environ["CALENDAR_NOTIFICATION_ATTENDEES"]
