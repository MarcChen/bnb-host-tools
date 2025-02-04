from services.gmail_services.gmail_services import GmailService
from services.parser.parser import fetch_specific_data_from_content

class MailProcessorService:
    def __init__(self) -> None:
        self.gmail_service = GmailService()

    def upload_booking_data_to_db(self, data: dict) -> None:
        # Stub: Implement the actual database upload logic here.
        print("Uploading to database:", data)

    def process_unread_mails(self) -> None:
        unread_mail_ids = self.gmail_service.list_unread_mails()
        for msg_id in unread_mail_ids:
            message_details = self.gmail_service.get_mail_content(msg_id, print_message=True)
            specific_data = fetch_specific_data_from_content(message_details.get('Message_body', ''), print_data=True)
            if specific_data:
                specific_data = self.gmail_service.fetch_data_from_mail_header(specific_data, message_details)
                print("Extracted Data:", specific_data)
                self.upload_booking_data_to_db(specific_data)
                self.gmail_service.mark_as_read(msg_id)
            else:
                print(f"No specific data extracted for message ID {msg_id}.")

if __name__ == "__main__":
    processor = MailProcessorService()
    processor.process_unread_mails()
