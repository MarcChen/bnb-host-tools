import os
from typing import Any, Dict, List, Union, Optional  # Added Optional type
from notion_client import Client

class NotionClient:
    def __init__(self) -> None:
        """Initialize client with API key and database id from environment variables."""
        self.token = os.environ.get("NOTION_API_KEY")
        self.database_id = os.environ.get("NOTION_DATABASE_ID")
        self.client = Client(auth=self.token)

    def create_page(
        self,
        date: Optional[str] = None,
        arrival_date: Optional[str] = None,
        departure_date: Optional[str] = None,
        confirmation_code: Optional[str] = None,
        cost_per_night: Optional[Union[int, float]] = None,
        number_of_nights: Optional[Union[int, float]] = None,
        total_nights_cost: Optional[Union[int, float]] = None,
        cleaning_fee: Optional[Union[int, float]] = None,
        guest_service_fee: Optional[Union[int, float]] = None,
        host_service_fee: Optional[Union[int, float]] = None,
        tourist_tax: Optional[Union[int, float]] = None,
        total_paid_by_guest: Optional[Union[int, float]] = None,
        host_payout: Optional[Union[int, float]] = None,
        number_of_adults: Optional[int] = None,
        number_of_children: Optional[int] = None,
        country_code: Optional[str] = None,
        city: Optional[str] = None,
        full_name: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Any:
        """Create a new page in the Notion database.
        Fields with None values are omitted from the page properties.
        """
        props = {}
        if date:
            props["Date"] = {"date": {"start": date}}
        if arrival_date:
            props["Arrival Date"] = {"date": {"start": arrival_date}}
        if departure_date:
            props["Departure Date"] = {"date": {"start": departure_date}}
        if confirmation_code:
            props["Confirmation Code"] = {"rich_text": [{"text": {"content": confirmation_code}}]}
        if cost_per_night is not None:
            props["Cost per Night"] = {"number": cost_per_night}
        if number_of_nights is not None:
            props["Number of Nights"] = {"number": number_of_nights}
        if total_nights_cost is not None:
            props["Total Nights Cost"] = {"number": total_nights_cost}
        if cleaning_fee is not None:
            props["Cleaning Fee"] = {"number": cleaning_fee}
        if guest_service_fee is not None:
            props["Guest Service Fee"] = {"number": guest_service_fee}
        if host_service_fee is not None:
            props["Host Service Fee"] = {"number": host_service_fee}
        if tourist_tax is not None:
            props["Tourist Tax"] = {"number": tourist_tax}
        if total_paid_by_guest is not None:
            props["Total Paid by Guest"] = {"number": total_paid_by_guest}
        if host_payout is not None:
            props["Host Payout"] = {"number": host_payout}
        if number_of_adults is not None:
            props["Number of Adults"] = {"number": number_of_adults}
        if number_of_children is not None:
            props["Number of Children"] = {"number": number_of_children}
        if country_code:
            props["Country"] = {"select": {"name": country_code}}
        if city:
            props["City"] = {"select": {"name": city}}
        if full_name:
            props["Name"] = {"title": [{"text": {"content": full_name}}]}
        if subject:
            props["Subject"] = {"rich_text": [{"text": {"content": subject}}]}
        return self.client.pages.create(parent={"database_id": self.database_id}, properties=props)

    def delete_page_by_reservation_code(self, reservation_code: str) -> int:
        """Archive pages matching the confirmation code and return the count."""
        query = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Confirmation Code",
                "rich_text": {  # Updated filter type
                    "equals": reservation_code
                }
            }
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

    def get_pages_by_reservation_code(self, reservation_code: str) -> List[Dict[str, Any]]:
        """Retrieve and parse pages that match the provided confirmation code."""
        query = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Confirmation Code",
                "rich_text": {
                    "equals": reservation_code
                }
            }
        )
        pages = query.get("results", [])
        return [self.parse_page(page) for page in pages]

    def get_all_pages(self) -> List[Any]:
        """Retrieve all pages from the Notion database (pagination not handled)."""
        query = self.client.databases.query(database_id=self.database_id)
        return query.get("results", [])

if __name__ == "__main__":
    import datetime
    client = NotionClient()

    # Test get_all_pages
    try:
        pages = client.get_all_pages()
        print("All pages:", pages)
    except Exception as e:
        print("Error retrieving all pages:", e)

    # Prepare sample test data
    today = datetime.date.today().isoformat()
    sample_data = {
        "date": today,
        "arrival_date": today,
        "departure_date": today,
        "confirmation_code": "TEST123",
        "number_of_children": 1,
        "country_code": "US",
        "city": "Unknown",
        "full_name": "John Doe",
        "subject": "Reservation Test"
    }

    # Test create_page
    try:
        new_page = client.create_page(**sample_data)
        print("Created page:", new_page)
    except Exception as e:
        print("Error creating page:", e)

    # Test get_pages_by_reservation_code
    try:
        pages_by_code = client.get_pages_by_reservation_code("TEST123")
        print("Pages with reservation code 'TEST123':", pages_by_code)
    except Exception as e:
        print("Error retrieving pages by reservation code:", e)

    # Test delete_page_by_reservation_code
    try:
        deleted_count = client.delete_page_by_reservation_code("TEST123")
        print("Number of deleted pages for reservation 'TEST123':", deleted_count)
    except Exception as e:
        print("Error deleting pages by reservation code:", e)
