import datetime

import pandas as pd
import requests

# Import the module to test
from services.dataviz.src import get_blocked_days


# Dummy classes to simulate calendar events and datetime objects
class DummyDt:
    def __init__(self, date_val):
        self._date = date_val

    def date(self):
        return self._date


class DummyEvent:
    def __init__(self, name, begin, end):
        self.name = name
        self.begin = begin
        self.end = end


class DummyCalendar:
    def __init__(self, text):
        # Create one event that matches and one that doesn't
        self.events = [
            DummyEvent(
                "Airbnb (Not available)",
                DummyDt(datetime.date(2023, 10, 10)),
                DummyDt(datetime.date(2023, 10, 11)),
            ),
            DummyEvent(
                "Other event",
                DummyDt(datetime.date(2023, 10, 12)),
                DummyDt(datetime.date(2023, 10, 13)),
            ),
        ]


class DummyResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def dummy_get(url):
    return DummyResponse("dummy calendar text")


def test_fetch_blocked_days(monkeypatch):
    # Patch requests.get
    monkeypatch.setattr(requests, "get", dummy_get)

    # Patch Calendar in the module with our DummyCalendar
    monkeypatch.setattr(get_blocked_days, "Calendar", DummyCalendar)

    df = get_blocked_days.fetch_blocked_days_from_airbnb_ical("http://dummy-url")

    # Assert only one event (matching the "Airbnb (Not available)" string) is returned
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 1
    row = df.iloc[0]
    assert row["start_date"] == datetime.date(2023, 10, 10)
    assert row["end_date"] == datetime.date(2023, 10, 11)
    assert row["Name"] == "Airbnb (Not available)"
