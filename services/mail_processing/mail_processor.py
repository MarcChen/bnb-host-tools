from services.gmail_services.gmail_services import GmailService
from mail_processing.parser import Parser
import pandas as pd
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

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
        # print(f"Mail content : {reserved_emails}")
        parsed_results = []
        
        for email in reserved_emails:
            parser = Parser(email)
            parsed_data = parser.parse_data()
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
                    if value == "N/A" and key != "City" and key != "Host Service Tax": # Some users doesn't have city in their Airbnb profile
                        print(f"\033[91m{key}: No data found.\033[0m")                
        return parsed_results

    def run_workflow(self) -> None:
        """Execute the complete workflow"""
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            step1 = progress.add_task(description="Processing unread mails...", total=None)
            self.process_all_unread_mails()
            progress.update(step1, completed=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            step2 = progress.add_task(description="Parsing reserved mails...", total=None)
            parsed_reservations = self.parse_reserved_mails()
            progress.update(step2, completed=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            step3 = progress.add_task(description="Saving reservations to CSV...", total=None)
            print("\nStep 3: Saving reservations to CSV...")
            if parsed_reservations:
                df = pd.DataFrame(parsed_reservations)
                output_path = 'reservations.csv'
                df.to_csv(output_path, index=False)
                print(f"Data saved to {os.path.abspath(output_path)}")
            else:
                print("No reservations to save")
            progress.update(step3, completed=True)
        print(f"\nWorkflow completed. Processed {len(parsed_reservations)} reservations.")

if __name__ == "__main__":
    # Set debug to True for verbose output
    processor = MailProcessorService(debug=True)
    processor.run_workflow()
