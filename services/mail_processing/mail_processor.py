from services.gmail_services.gmail_services import GmailService
from mail_processing.parser import Parser
from services.notion_client.notion_api_client import NotionClient
from services.google_calendar.calendar_services import CalendarService

import pandas as pd
import warnings
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

class MailProcessorService:
    def __init__(self, debug: bool = False) -> None:
        self.gmail_service = GmailService()
        self.debug = debug
        
    def parse_reserved_mails(self) -> list:
        """Second step: Get reserved emails and parse them"""
        reserved_emails = self.gmail_service.get_reserved_unread_emails_content()
        # print(f"Mail content : {reserved_emails}")
        parsed_results = []
        
        month_mapping = {
            "jan": "01", "janv": "01",
            "fév": "02", "févr": "02", "feb": "02",
            "mar": "03",
            "avr": "04", "apr": "04",
            "mai": "05", "may": "05",
            "jun": "06", "juin": "06",
            "jul": "07", "juil": "07",
            "août": "08", "aoû": "08", "aug": "08",
            "sep": "09", "sept": "09",
            "oct": "10",
            "nov": "11",
            "déc": "12", "dec": "12"
        }

        for email in reserved_emails:
            parser = Parser(email)
            parsed_data = parser.parse_data()

            arr_day = parsed_data.get("arrival_day", "")
            arr_month = parsed_data.get("arrival_month", "").lower()
            arr_year = parsed_data.get("arrival_year", "")
            arr_month_num = month_mapping.get(arr_month, "01")
            parsed_data["arrival_date"] = f"{arr_year}-{arr_month_num.zfill(2)}-{arr_day.zfill(2)}"

            dep_day = parsed_data.get("departure_day", "")
            dep_month = parsed_data.get("departure_month", "").lower()
            dep_year = parsed_data.get("departure_year", "")
            dep_month_num = month_mapping.get(dep_month, "01")
            parsed_data["departure_date"] = f"{dep_year}-{dep_month_num.zfill(2)}-{dep_day.zfill(2)}"
            keys_to_remove = [
                "arrival_day", "arrival_month", "arrival_year",
                "departure_day", "departure_month", "departure_year"
            ]
            for key in keys_to_remove:
                parsed_data.pop(key, None)
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
                print(parsed_data.get("Name", "No name found."))
                for key, value in parsed_data.items():
                    if value == "N/A" and key != "City" and key != "Host Service Tax": # Some users doesn't have city in their Airbnb profile
                        print(f"\033[91m{key}: No data found.\033[0m")

            seen_codes = set()
            for reservation in parsed_results:
                code = reservation.get("Confirmation Code")
                if code in seen_codes:
                    raise ValueError(f"Duplicate reservation code found: {code}")
                seen_codes.add(code)
        return parsed_results

    def run_workflow(self) -> None:
        """Execute the complete workflow"""
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            print("[bold blue]Step 1: Processing and tagging unread emails...[/bold blue]")
            step1 = progress.add_task(description="[bold magenta]Processing unread mails...[/bold magenta]", total=None)
            self.gmail_service.process_unread_emails()
            progress.update(step1, completed=True)
            print("[bold green]✓[/bold green] Step 1 completed: Emails processed and tagged\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            print("[bold blue]Step 2: Parsing reserved emails...[/bold blue]")
            step2 = progress.add_task(description="[bold magenta]Parsing reserved mails...[/bold magenta]", total=None)
            parsed_reservations = self.parse_reserved_mails()
            progress.update(step2, completed=True)
            print("[bold green]✓[/bold green] Step 2 completed: Emails parsed\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            print("[bold blue]Step 3: Saving reservations to Notion and creating Calendar Event...[/bold blue]")
            step3 = progress.add_task(description="[bold magenta]Saving reservations to Notion and creating Calendar Event ...[/bold magenta]", total=None)
            if parsed_reservations:
                notion_client = NotionClient()
                calendar_service = CalendarService()
                for reservation in parsed_reservations:
                    if not notion_client.row_exists_by_reservation_id(reservation.get("Confirmation Code")):
                        print(f"Reservation is {reservation}")
                        notion_client.create_page(**reservation)
                        # calendar_service.create_event(**reservation)
                print(f"[bold green]✓[/bold green] Data saved to Notion and events created \n")
            else:
                print("[yellow]No reservations to save[/yellow]")
                return
            progress.update(step3, completed=True)
            print("[bold green]✓[/bold green] Step 3 completed: Data saved\n")

        # with Progress(
        #     SpinnerColumn(),
        #     TextColumn("[progress.description]{task.description}"),
        #     transient=True
        # ) as progress:
        #     print("[bold blue]Step 4: Marking reserved mails as read...[/bold blue]")
        #     step4 = progress.add_task(description="[bold magenta]Marking reserved mails as read...[/bold magenta]", total=None)
        #     self.gmail_service.mark_reserved_mails_as_read()
        #     progress.update(step4, completed=True)
        #     print("[bold green]✓[/bold green] Step 4 completed: Reserved mails marked as read\n")


        # with Progress(
        #     SpinnerColumn(),
        #     TextColumn("[progress.description]{task.description}"),
        #     transient=True
        # ) as progress:
        #     print("[bold blue]Step 4: Saving reservations to CSV...[/bold blue]")
        #     step3 = progress.add_task(description="[bold magenta]Saving reservations to CSV...[/bold magenta]", total=None)
        #     if parsed_reservations:
        #         import os 
        #         df = pd.DataFrame(parsed_reservations)
        #         output_path = 'reservations.csv'
        #         df.to_csv(output_path, index=False)
        #         print(f"[bold green]✓[/bold green] Data saved to {os.path.abspath(output_path)}")
        #     else:
        #         print("[yellow]No reservations to save[/yellow]")
        #     progress.update(step3, completed=True)
        #     print("[bold green]✓[/bold green] Step 4 completed: Data saved\n")

        print(f"\n[bold green]Workflow completed successfully![/bold green]")
        print(f"[blue]Processed {len(parsed_reservations)} reservations.[/blue]")

if __name__ == "__main__":
    # Set debug to True for verbose output
    processor = MailProcessorService(debug=True)
    processor.run_workflow()
