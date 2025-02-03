import os
from notion_client import Client  # Using the Notion API client

class NotionClient:
    def __init__(self):
        # Initialize client with API key and database id from env variables
        self.token = os.environ.get("NOTION_API_KEY")
        self.database_id = os.environ.get("NOTION_DATABASE_ID")
        self.client = Client(auth=self.token)

    def create_page(
        self, date, arrival_date, departure_date, confirmation_code, cost_per_night,
        number_of_nights, total_nights_cost, cleaning_fee, guest_service_fee, host_service_fee,
        tourist_tax, total_paid_by_guest, host_payout, number_of_adults, number_of_children,
        country_code, full_name, subject
    ):
        # Create a new page in the database with the provided properties
        return self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "Date": {"date": {"start": date}},
                "Arrival Date": {"date": {"start": arrival_date}},
                "Departure Date": {"date": {"start": departure_date}},
                "Confirmation Code": {
                    "title": [{"text": {"content": confirmation_code}}]
                },
                "Cost per Night": {"number": cost_per_night},
                "Number of Nights": {"number": number_of_nights},
                "Total Nights Cost": {"number": total_nights_cost},
                "Cleaning Fee": {"number": cleaning_fee},
                "Guest Service Fee": {"number": guest_service_fee},
                "Host Service Fee": {"number": host_service_fee},
                "Tourist Tax": {"number": tourist_tax},
                "Total Paid by Guest": {"number": total_paid_by_guest},
                "Host Payout": {"number": host_payout},
                "Number of Adults": {"number": number_of_adults},
                "Number of Children": {"number": number_of_children},
                "Country Code": {"rich_text": [{"text": {"content": country_code}}]},
                "Full_Name": {"rich_text": [{"text": {"content": full_name}}]},
                "Subject": {"rich_text": [{"text": {"content": subject}}]},
            }
        )

    def delete_page_by_reservation_code(self, reservation_code):
        # Find pages by Confirmation Code and archive them (mark as deleted)
        query = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Confirmation Code",
                "title": {
                    "equals": reservation_code
                }
            }
        )
        for result in query.get("results", []):
            page_id = result["id"]
            self.client.pages.update(page_id=page_id, archived=True)
        return len(query.get("results", []))

    def get_pages_by_reservation_code(self, reservation_code):
        # Retrieve pages filtered by Confirmation Code
        query = self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Confirmation Code",
                "title": {
                    "equals": reservation_code
                }
            }
        )
        return query.get("results", [])

    def get_all_pages(self):
        # Retrieve all pages from the database (may need pagination handling)
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
        "cost_per_night": 100,
        "number_of_nights": 2,
        "total_nights_cost": 200,
        "cleaning_fee": 50,
        "guest_service_fee": 20,
        "host_service_fee": 15,
        "tourist_tax": 10,
        "total_paid_by_guest": 295,
        "host_payout": 280,
        "number_of_adults": 2,
        "number_of_children": 1,
        "country_code": "US",
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
