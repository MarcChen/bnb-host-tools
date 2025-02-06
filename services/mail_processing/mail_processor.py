from services.gmail_services.gmail_services import GmailService
from mail_processing.parser import Parser
import pandas as pd
import os
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
            print("[bold blue]Step 3: Marking reserved mails as read...[/bold blue]")
            step2_5 = progress.add_task(description="[bold magenta]Marking reserved mails as read...[/bold magenta]", total=None)
            self.gmail_service.mark_reserved_mails_as_read()
            progress.update(step2_5, completed=True)
            print("[bold green]✓[/bold green] Step 3 completed: Emails marked as read\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            print("[bold blue]Step 4: Saving reservations to CSV...[/bold blue]")
            step3 = progress.add_task(description="[bold magenta]Saving reservations to CSV...[/bold magenta]", total=None)
            if parsed_reservations:
                df = pd.DataFrame(parsed_reservations)
                output_path = 'reservations.csv'
                df.to_csv(output_path, index=False)
                print(f"[bold green]✓[/bold green] Data saved to {os.path.abspath(output_path)}")
            else:
                print("[yellow]No reservations to save[/yellow]")
            progress.update(step3, completed=True)
            print("[bold green]✓[/bold green] Step 4 completed: Data saved\n")

        print(f"\n[bold green]Workflow completed successfully![/bold green]")
        print(f"[blue]Processed {len(parsed_reservations)} reservations.[/blue]")

if __name__ == "__main__":
    # Set debug to True for verbose output
    processor = MailProcessorService(debug=True)
    processor.run_workflow()
