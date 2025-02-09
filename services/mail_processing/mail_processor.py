from mail_processing.parser import Parser
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from services.google_integration.calendar_services import CalendarService
from services.google_integration.gmail_services import GmailService
from services.notion_client.notion_api_client import NotionClient


class MailProcessorService:
    def __init__(self, debug: bool = False) -> None:
        self.gmail_service = GmailService()
        self.debug = debug

    def parse_reserved_mails(self) -> list:
        """Second step: Get reserved emails and parse them"""
        reserved_emails = self.gmail_service.get_reserved_unread_emails_content()
        print(f"Mail content : {reserved_emails}") if self.debug else None
        parsed_results = []

        # fmt: off
        month_mapping = {
            "jan": "01", "janv": "01",
            "fév": "02", "févr": "02", "feb": "02",
            "mar": "03", "mars": "03",
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
        # fmt: on

        for email in reserved_emails:
            parser = Parser(email)
            parsed_data = parser.parse_data()

            arr_day = parsed_data.get("arrival_day", "")
            arr_month = parsed_data.get("arrival_month", "").lower()
            arr_year = parsed_data.get("arrival_year", "")
            arr_month_num = month_mapping.get(arr_month, "01")
            parsed_data[
                "arrival_date"
            ] = f"{arr_year}-{arr_month_num.zfill(2)}-{arr_day.zfill(2)}"

            dep_day = parsed_data.get("departure_day", "")
            dep_month = parsed_data.get("departure_month", "").lower()
            dep_year = parsed_data.get("departure_year", "")
            dep_month_num = month_mapping.get(dep_month, "01")
            parsed_data[
                "departure_date"
            ] = f"{dep_year}-{dep_month_num.zfill(2)}-{dep_day.zfill(2)}"
            keys_to_remove = [
                "arrival_day",
                "arrival_month",
                "arrival_year",
                "departure_day",
                "departure_month",
                "departure_year",
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
                print(parsed_data.get("name", "No name found."))
                for key, value in parsed_data.items():
                    if (
                        value == "N/A" and key != "city" and key != "host_service_tax"
                    ):  # Some users doesn't have city in their Airbnb profile
                        print(f"[bold red]{key}: No data found.[/bold red]")

            seen_codes = set()
            for reservation in parsed_results:
                code = reservation.get("confirmation_code")
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
            transient=True,
        ) as progress:
            print(
                "[bold blue]Step 1: Processing and tagging unread emails...[/bold blue]"
            )
            step1 = progress.add_task(
                description="[bold magenta]Processing unread mails...[/bold magenta]",
                total=None,
            )
            self.gmail_service.process_unread_emails()
            progress.update(step1, completed=True)
            print(
                "[bold green]✓[/bold green] Step 1 completed: Emails processed and tagged\n"
            )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            print("[bold blue]Step 2: Parsing reserved emails...[/bold blue]")
            step2 = progress.add_task(
                description="[bold magenta]Parsing reserved mails...[/bold magenta]",
                total=None,
            )
            parsed_reservations = self.parse_reserved_mails()
            progress.update(step2, completed=True)
            print("[bold green]✓[/bold green] Step 2 completed: Emails parsed\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            print(
                "[bold blue]Step 3: Saving reservations to Notion and creating Calendar Event...[/bold blue]"
            )
            step3 = progress.add_task(
                description="[bold magenta]Saving reservations to Notion and creating Calendar Event ...[/bold magenta]",
                total=None,
            )
            if parsed_reservations:
                notion_client = NotionClient()
                calendar_service = CalendarService()
                for reservation in parsed_reservations:
                    confirmation_code = reservation.get("confirmation_code")
                    if not notion_client.row_exists_by_reservation_id(
                        confirmation_code
                    ):
                        # print(f"Reservation is {reservation}")
                        notion_client.create_page(**reservation)
                        print(
                            f"[bold green]✓[/bold green] [bold cyan]Reservation {confirmation_code} saved to Notion[/bold cyan]\n"
                        )
                    else:
                        console.print(
                            f"[bold yellow]Warning:[/bold yellow] A reservation with confirmation code '{confirmation_code}' already exists.\n",
                            style="yellow",
                        )

                    if calendar_service.event_exists(confirmation_code):
                        console.print(
                            f"[bold yellow]Warning:[/bold yellow] An event with reservation code '{confirmation_code}' already exists.\n",
                            style="yellow",
                        )
                    else:
                        calendar_service.create_event(**reservation)
                        print(
                            f"[bold green]✓[/bold green] [bold cyan]Event created for reservation {confirmation_code}[/bold cyan]\n"
                        )
            else:
                print("[yellow]No reservations to save[/yellow]")
                return
            progress.update(step3, completed=True)
            print(
                "[bold green]✓[/bold green] Step 3 completed: Data saved to Notion and events are created\n"
            )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            print("[bold blue]Step 4: Marking reserved mails as read...[/bold blue]")
            step4 = progress.add_task(
                description="[bold magenta]Marking reserved mails as read...[/bold magenta]",
                total=None,
            )
            self.gmail_service.mark_reserved_mails_as_read()
            progress.update(step4, completed=True)
            print(
                "[bold green]✓[/bold green] Step 4 completed: Reserved mails marked as read\n"
            )

        # with Progress(
        #     SpinnerColumn(),
        #     TextColumn("[progress.description]{task.description}"),
        #     transient=True
        # ) as progress:
        #     print("[bold blue]Step 4: Saving reservations to CSV...[/bold blue]")
        #     step4 = progress.add_task(description="[bold magenta]Saving reservations to CSV...[/bold magenta]", total=None)
        #     if parsed_reservations:
        #         import os
        #         df = pd.DataFrame(parsed_reservations)
        #         output_path = 'reservations.csv'
        #         df.to_csv(output_path, index=False)
        #         print(f"[bold green]✓[/bold green] Data saved to {os.path.abspath(output_path)}")
        #     else:
        #         print("[yellow]No reservations to save[/yellow]")
        #     progress.update(step4, completed=True)
        #     print("[bold green]✓[/bold green] Step 4 completed: Data saved\n")

        print("\n[bold green]Workflow completed successfully![/bold green]")
        print(f"[blue]Processed {len(parsed_reservations)} reservations.[/blue]")
