import datetime
from unittest.mock import MagicMock, patch

import pytest

from services.dataviz.src import get_blocked_days


def test_fetch_blocked_days_from_airbnb_ical_parses_events():
    fake_ical = """
BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:Airbnb (Not available)
DTSTART;VALUE=DATE:20230901
DTEND;VALUE=DATE:20230903
END:VEVENT
END:VCALENDAR
"""
    with patch("services.dataviz.src.get_blocked_days.requests.get") as mock_get, patch(
        "services.dataviz.src.get_blocked_days.Calendar"
    ) as mock_calendar:
        mock_get.return_value.text = fake_ical
        mock_get.return_value.raise_for_status = lambda: None

        mock_event = MagicMock()
        mock_event.name = "Airbnb (Not available)"
        mock_event.begin.date.return_value = datetime.date(2023, 9, 1)
        mock_event.end.date.return_value = datetime.date(2023, 9, 3)
        mock_calendar.return_value.events = [mock_event]

        result = get_blocked_days.fetch_blocked_days_from_airbnb_ical("http://fake-url")
        assert result == [
            {
                "start_date": datetime.date(2023, 9, 1),
                "end_date": datetime.date(2023, 9, 3),
                "Name": "Airbnb (Not available)",
            }
        ]


@patch("services.dataviz.src.get_blocked_days.Client")
def test_fetch_blocked_days_from_notion_parses_pages(mock_client):
    mock_notion = MagicMock()
    mock_client.return_value = mock_notion
    mock_notion.databases.query.return_value = {
        "results": [
            {
                "properties": {
                    "Start Date": {"date": {"start": "2023-09-01"}},
                    "End Date": {"date": {"start": "2023-09-03"}},
                    "Name": {
                        "title": [{"text": {"content": "Airbnb (Not available)"}}]
                    },
                    "Insert Date": {"date": {"start": "2023-09-01T12:00:00"}},
                }
            }
        ]
    }
    result = get_blocked_days.fetch_blocked_days_from_notion()
    assert result == [
        {
            "start_date": "2023-09-01",
            "end_date": "2023-09-03",
            "Name": "Airbnb (Not available)",
            "Insert Date": "2023-09-01T12:00:00",
        }
    ]


@patch("services.dataviz.src.get_blocked_days.Client")
@patch("services.dataviz.src.get_blocked_days.fetch_blocked_days_from_airbnb_ical")
def test_push_blocked_days_to_notion_creates_new_pages(mock_fetch, mock_client):
    mock_notion = MagicMock()
    mock_client.return_value = mock_notion
    mock_notion.databases.query.return_value = {"results": []}
    mock_fetch.return_value = [
        {
            "start_date": datetime.date(2023, 9, 1),
            "end_date": datetime.date(2023, 9, 3),
            "Name": "Airbnb (Not available)",
        }
    ]
    get_blocked_days.BLOCKED_DATE_DB_ID = "fake_db_id"
    get_blocked_days.TOKEN = "fake_token"
    get_blocked_days.push_blocked_days_to_notion("http://fake-url")
    assert mock_notion.pages.create.called


if __name__ == "__main__":
    pytest.main(["-v", __file__])
