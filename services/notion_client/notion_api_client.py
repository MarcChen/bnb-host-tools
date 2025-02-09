import datetime
import os
import warnings
from typing import Any, Dict, List

from notion_client import Client


class NotionClient:
    def __init__(self) -> None:
        """Initialize client with API key and database id from environment variables."""
        self.token = os.environ.get("NOTION_API")
        self.database_id = os.environ.get("DATABASE_ID")
        assert self.token, "Missing NOTION_API environment variable"
        assert self.database_id, "Missing DATABASE_ID environment variable"
        self.client = Client(auth=self.token)

    def create_page(self, **kwargs) -> Any:
        property_mapping = {
            "date": ("Date", lambda v: {"date": {"start": v}}),
            "arrival_date": ("Arrival Date", lambda v: {"date": {"start": v}}),
            "departure_date": ("Departure Date", lambda v: {"date": {"start": v}}),
            "confirmation_code": (
                "Confirmation Code",
                lambda v: {"rich_text": [{"text": {"content": v}}]},
            ),
            "price_by_night": ("Price by night", lambda v: {"number": v}),
            "number_of_nights": ("Number of Nights", lambda v: {"number": v}),
            "total_nights_cost": ("Total Nights Cost", lambda v: {"number": v}),
            "cleaning_fee": ("Cleaning Fee", lambda v: {"number": v}),
            "guest_service_fee": ("Guest Service Fee", lambda v: {"number": v}),
            "host_service_fee": ("Host Service Fee", lambda v: {"number": v}),
            "tourist_tax": ("Tourist Tax", lambda v: {"number": v}),
            "total_paid_by_guest": ("Total Paid by Guest", lambda v: {"number": v}),
            "host_payout": ("Host Payout", lambda v: {"number": v}),
            "number_of_adults": ("Number of Adults", lambda v: {"number": v}),
            "number_of_children": ("Number of Children", lambda v: {"number": v}),
            "country": ("Country", lambda v: {"select": {"name": v}}),
            "city": ("City", lambda v: {"select": {"name": v}}),
            "name": ("Name", lambda v: {"title": [{"text": {"content": v}}]}),
            "subject": ("Subject", lambda v: {"rich_text": [{"text": {"content": v}}]}),
            "insert_date": (
                "Insert Date",
                lambda v: {"rich_text": [{"text": {"content": v}}]},
            ),
            "arrival_day_of_week": (
                "Arrival DayOfWeek",
                lambda v: {"rich_text": [{"text": {"content": v}}]},
            ),
            "departure_day_of_week": (
                "Departure DayOfWeek",
                lambda v: {"rich_text": [{"text": {"content": v}}]},
            ),
            "host_service_tax": (
                "Host Service Tax",
                lambda v: {"rich_text": [{"text": {"content": v}}]},
            ),
            "guest_payout": ("Guest Payout", lambda v: {"number": v}),
            "mail_date": ("Mail Date", lambda v: {"date": {"start": v}}),
            "number_of_child": ("Number of child", lambda v: {"number": v}),
        }
        props = {}
        for field, value in kwargs.items():
            if field in property_mapping and value is not None:
                notion_key, builder = property_mapping[field]
                props[notion_key] = builder(value)

        props["Insert Date"] = {
            "rich_text": [
                {
                    "text": {
                        "content": datetime.datetime.now()
                        .replace(microsecond=0)
                        .isoformat()
                    }
                }
            ]
        }

        return self.client.pages.create(
            parent={"database_id": self.database_id}, properties=props
        )

    def delete_page_by_reservation_code(self, reservation_code: str) -> int:
        if not reservation_code or reservation_code == "N/A":
            return 0
        query = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Confirmation Code",
                "rich_text": {"equals": reservation_code},  # Updated filter type
            },
        )
        for result in query.get("results", []):
            page_id = result["id"]
            self.client.pages.update(page_id=page_id, archived=True)
        return len(query.get("results", []))

    def parse_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Notion page's properties into a simple dict for easier access."""
        parsed = {}
        for key, value in page.get("properties", {}).items():
            field_type = value.get("type")
            if field_type in ["rich_text", "title"]:
                texts = [t.get("plain_text", "") for t in value.get(field_type, [])]
                parsed[key] = "".join(texts)
            elif field_type == "number":
                parsed[key] = value.get("number")
            elif field_type == "date":
                date_info = value.get("date") or {}
                parsed[key] = date_info.get("start")
            elif field_type == "select":  # Handle select field type
                parsed[key] = value.get("select", {}).get("name", "")
            else:
                parsed[key] = value
        return parsed

    def get_pages_by_reservation_code(
        self, reservation_code: str
    ) -> List[Dict[str, Any]]:
        """Retrieve and parse pages that match the provided confirmation code."""
        query = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Confirmation Code",
                "rich_text": {"equals": reservation_code},
            },
        )
        pages = query.get("results", [])
        return [self.parse_page(page) for page in pages]

    def get_all_pages(self) -> List[Any]:
        """Retrieve all pages from the Notion database (pagination not handled)."""
        query = self.client.databases.query(database_id=self.database_id)
        return query.get("results", [])

    def row_exists_by_reservation_id(self, reservation_id: str) -> bool:
        if not reservation_id or reservation_id == "N/A":
            warnings.warn("Invalid reservation ID", UserWarning)
            print(f"Invalid reservation ID: {reservation_id}")
            return False
        query = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Confirmation Code",
                "rich_text": {"equals": reservation_id},
            },
        )
        results = query.get("results", [])
        return len(results) > 0

    def update_row_by_name(self, name: str, rating: int) -> Dict[str, Any]:
        """
        Update a row by setting the 'Rating' property based on the provided rating.
        Partial match is used for the provided name.
        """
        # Query page(s) matching the provided partial name in the 'Name' property
        query = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Name",
                "title": {"contains": name},
            },
        )
        results = query.get("results", [])
        if not results:
            warnings.warn(f"No page found with name containing: {name}", UserWarning)
            return {}
        page_id = results[0]["id"]
        update_properties = {"Rating": {"number": rating}}
        updated_page = self.client.pages.update(
            page_id=page_id, properties=update_properties
        )
        return updated_page


if __name__ == "__main__":
    client = NotionClient()

    # Test get_all_pages
    # try:
    #     pages = client.get_all_pages()
    #     print("All pages:", pages)
    # except Exception as e:
    #     print("Error retrieving all pages:", e)

    # Prepare sample test data
    today = datetime.datetime.now().replace(microsecond=0).isoformat()
    print(f"Today's timestamp: {today}")
    sample_data = {
        "arrival_date": "2025-05-04",
        "departure_date": "2025-05-10",
        "number_of_adults": 3,
        "number_of_children": 0,
        "confirmation_code": "HMFANA2QCA",
        "cleaning_fee": 65.00,
        "guest_service_fee": 184.41,
        "host_service_fee": -37.62,
        "tourist_tax": 159.25,
        "cost_per_night": 163.33,
        "number_of_nights": 6,
        "total_nights_cost": 980.00,
        "total_paid_by_guest": 980.00,
        "host_payout": 1388.66,
        "country_code": "DK",
        "city": "N/A",
        "date": "2025-02-02",
        "name": "Kurt Pihl",
        "subject": "Reservation Test",
        "insert_date": today,
    }

    # Test create_page
    # try:
    #     new_page = client.create_page(**sample_data)
    #     print("Created page:", new_page)
    # except Exception as e:
    #     print("Error creating page:", e)

    # try:
    #     reservation_code = "HMFANA2QCA"
    #     exists = client.row_exists_by_reservation_id(reservation_code)
    #     print(f"Row with reservation code '{reservation_code}' exists:", exists)
    # except Exception as e:
    #     print("Error checking row existence:", e)

    # # Test get_pages_by_reservation_code
    # try:
    #     pages_by_code = client.get_pages_by_reservation_code("TEST123")
    #     print("Pages with reservation code 'TEST123':", pages_by_code)
    # except Exception as e:
    #     print("Error retrieving pages by reservation code:", e)

    # # Test delete_page_by_reservation_code
    # try:
    #     deleted_count = client.delete_page_by_reservation_code("TEST123")
    #     print("Number of deleted pages for reservation 'TEST123':", deleted_count)
    # except Exception as e:
    #     print("Error deleting pages by reservation code:", e)
