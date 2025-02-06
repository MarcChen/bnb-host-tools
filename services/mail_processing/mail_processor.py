from services.gmail_services.gmail_services import GmailService
from mail_processing.parser import Parser

class MailProcessorService:
    def __init__(self, debug: bool = False) -> None:
        self.gmail_service = GmailService()
        self.debug = debug

    def process_all_unread_mails(self) -> None:
        """First step: Process and tag all unread emails"""
        print("Step 1: Processing and tagging unread emails...")
        self.gmail_service.process_unread_emails()

    def parse_reserved_mails(self) -> list:
        """Second step: Get reserved emails and parse them"""
        print("\nStep 2: Retrieving and parsing reserved emails...")
        reserved_emails = self.gmail_service.get_reserved_unread_emails_content()
        print(f"Mail content : {reserved_emails}")
        parsed_results = []
        
        for email in reserved_emails:
            parser = Parser(email)
            parsed_data = parser.parse_data(print_data=True)
            parsed_results.append(parsed_data)
            
            if self.debug:
                # print("\nParsed Reservation Data:")
                # print("-" * 30)
                # for key, value in parsed_data.items():
                #     if value != "N/A":
                #         print(f"{key}: {value}")
                #     else: 
                #         print(f"\033[91m{key}: No data found.\033[0m")
                # print("-" * 30)
                print(parsed_data.get("Person Name", "No name found."))
                for key, value in parsed_data.items():
                    if value == "N/A" and key != "City": # Some users doesn't have city in their Airbnb profile
                        print(f"\033[91m{key}: No data found.\033[0m")                
        return parsed_results

    def run_workflow(self) -> None:
        """Execute the complete workflow"""
        print("Starting mail processing workflow...")
        
        # Step 1: Process and tag all unread emails
        # self.process_all_unread_mails()
        
        # Step 2: Parse reserved emails
        parsed_reservations = self.parse_reserved_mails()
        
        # Summary
        print(f"\nWorkflow completed. Processed {len(parsed_reservations)} reservations.")

if __name__ == "__main__":
    # Set debug to True for verbose output
    processor = MailProcessorService(debug=True)
    processor.run_workflow()
