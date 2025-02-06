import re
import os
import csv
import warnings
from typing import Dict, Any, Optional, Pattern, Match


class Parser:
    """
    A parser for extracting booking details from an email message.
    """

    def __init__(self, mail: Any) -> None:
        """
        Initializes the Parser with the provided mail.

        Args:
            mail (Any): The email content to parse (can be a string or dict).
        """
        self.person_name: str = "N/A"
        self.mail_date: str = "N/A"

        # If a dict is provided, extract relevant fields (mail_date, person_name, message_body).
        if isinstance(mail, dict):
            self.mail_date = mail.get("Date", "N/A")
            self.message_body: str = mail.get("Message_body", "")
            subject = mail.get("Subject", "")
            # Attempt to extract person's name from subject
            subject_clean = subject.replace("TR :", "").strip()
            match = re.search(
                r"(Réservation confirmée|Reservation confirmed)\s*[:\-\u2013\u2014\u00A0]+\s*(.*?)\s+(?:arrive|arrives)",
                subject_clean,
                re.IGNORECASE
            )
            if match:
                self.person_name = match.group(2).strip() or "N/A"
        else:
            self.message_body: str = mail or ""

        self.language: str = self.detect_language()

    def detect_language(self) -> str:
        """
        Detect the language of the email based on specific keywords.

        Returns:
            str: The detected language ('fr', 'en', or 'unknown').
        """
        body_lower = self.message_body.lower()

        # Simple checks on certain keywords
        if any(keyword in body_lower for keyword in ["arrivée", "départ", "confirmée"]):
            return "fr"
        elif any(keyword in body_lower for keyword in ["check-in", "checkout", "confirmed"]):
            return "en"
        return "unknown"

    def parse_data(self) -> Dict[str, Any]:
        """
        Parses the booking data from the message body.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        data: Dict[str, Any] = {}

        # Get the regex patterns based on the detected language
        patterns = self.get_language_patterns(self.language)
        if not patterns:
            raise ValueError("Language not detected or unsupported.")

        # Search all regex patterns in the message body
        matches = {
            key: pattern.search(self.message_body)
            for key, pattern in patterns.items()
        }

        # Optionally print missing fields and raise warnings
        
        for field_name, match in matches.items():
            if not match:
                warnings.warn(f"{field_name} not found")

        # Parse each field and populate the data dictionary
        self.parse_arrival_date(matches.get("arrival_date"), data)
        self.parse_departure_date(matches.get("departure_date"), data)
        self.parse_number_of_guests(matches.get("number_of_guests"), data)
        self.parse_confirmation_code(matches.get("confirmation_code"), data)
        self.parse_cleaning_fee(matches.get("cleaning_fee"), data)
        self.parse_guest_service_fee(matches.get("guest_service_fee"), data)
        self.parse_host_service_fee(matches.get("host_service_fee"), data)
        self.parse_tourist_tax(matches.get("tourist_tax"), data)
        self.parse_price_by_night_guest(matches.get("price_by_night_guest"), data)
        self.parse_host_payout(matches.get("host_payout"), data)
        self.parse_guest_payout(matches.get("guest_payout"), data)
        self.parse_guest_location(matches.get("guest_location"), data)

        # Add some extra fields from the original data
        data["Mail Date"] = self.mail_date
        data["Person Name"] = self.person_name

        return data

    @staticmethod
    def safe_get(match: Optional[Match], group, default: str = "N/A") -> str:
        """
        Helper method to safely extract a regex group.

        Args:
            match (Optional[Match]): The regex match object.
            group (int or str): The capture group index or name.
            default (str): The default value if no match or group is found.

        Returns:
            str: The extracted string or default if not found.
        """
        if match:
            val = match.group(group)
            if val:
                return val.strip()
        return default

    def parse_arrival_date(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set arrival date details (day of week, day, month, year).
        """
        if match:
            data["Arrival_DayOfWeek"] = self.safe_get(match, 1)
            data["Arrival_Day"] = self.safe_get(match, 2)
            data["Arrival_Month"] = self.safe_get(match, 3)
            data["Arrival_Year"] = self.safe_get(match, 4, self.mail_date[:4] if self.mail_date != "N/A" else "N/A")
        else:
            data.update({
                "Arrival_DayOfWeek": "N/A",
                "Arrival_Day": "N/A",
                "Arrival_Month": "N/A",
                "Arrival_Year": "N/A"
            })

    def parse_departure_date(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set departure date details (day of week, day, month, year).
        """
        if match:
            data["Departure_DayOfWeek"] = self.safe_get(match, 1)
            data["Departure_Day"] = self.safe_get(match, 2)
            data["Departure_Month"] = self.safe_get(match, 3)
            data["Departure_Year"] = self.safe_get(match, 4, self.mail_date[:4] if self.mail_date != "N/A" else "N/A")
        else:
            data.update({
                "Departure_DayOfWeek": "N/A",
                "Departure_Day": "N/A",
                "Departure_Month": "N/A",
                "Departure_Year": "N/A"
            })

    def parse_number_of_guests(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set the number of adults/children.
        """
        if match:
            data["Number of Adults"] = self.safe_get(match, 1)
            data["Number of child"] = self.safe_get(match, 2, "0")
        else:
            data.update({
                "Number of Adults": "N/A",
                "Number of child": "N/A"
            })

    def parse_confirmation_code(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set the confirmation code.
        """
        data["Confirmation Code"] = self.safe_get(match, 1)

    def parse_cleaning_fee(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set cleaning fee.
        """
        raw_value = self.safe_get(match, 1)
        data["Cleaning Fee"] = raw_value.replace(",", ".") if raw_value != "N/A" else "N/A"

    def parse_guest_service_fee(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set guest service fee.
        """
        raw_value = self.safe_get(match, 1)
        data["Guest Service Fee"] = raw_value.replace(",", ".") if raw_value != "N/A" else "N/A"

    def parse_host_service_fee(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set host service fee and tax.
        """
        if match:
            # Named groups for clarity
            fee_raw = self.safe_get(match, "host_service_fee")
            tax_raw = self.safe_get(match, "tax")
            data["Host Service Fee"] = fee_raw.replace(",", ".") if fee_raw != "N/A" else "N/A"
            data["Host Service Tax"] = tax_raw if tax_raw != "N/A" else "N/A"
        else:
            data["Host Service Fee"] = "N/A"
            data["Host Service Tax"] = "N/A"

    def parse_tourist_tax(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set tourist tax.
        """
        raw_value = self.safe_get(match, 1)
        data["Tourist Tax"] = raw_value.replace(",", ".") if raw_value != "N/A" else "N/A"

    def parse_price_by_night_guest(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set price per night, number of nights, and total price.
        """
        if match:
            data["Price by night"] = self.safe_get(match, 1).replace(",", ".")
            data["Number of nights"] = self.safe_get(match, 2)
            data["Total Price for all nights"] = self.safe_get(match, 3).replace(",", ".")
        else:
            data.update({
                "Price by night": "N/A",
                "Number of nights": "N/A",
                "Total Paid by Guest": "N/A"
            })

    def parse_guest_payout(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set the total payout from the guest (i.e., total amount guest pays).
        """
        raw_value = self.safe_get(match, 1)
        data["Guest Payout"] = raw_value.replace(",", ".") if raw_value != "N/A" else "N/A"

    def parse_host_payout(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set the host's final payout.
        """
        raw_value = self.safe_get(match, 1)
        data["Host Payout"] = raw_value.replace(",", ".") if raw_value != "N/A" else "N/A"

    def parse_guest_location(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set the guest's country/city.
        """
        if match:
            country = self.safe_get(match, "country")
            city = self.safe_get(match, "city")
            data["Country"] = country
            data["City"] = city
        else:
            data.update({"Country": "N/A", "City": "N/A"})

    def get_language_patterns(self, language: str) -> Dict[str, Pattern]:
        """
        Returns a dictionary of compiled regex patterns based on the language.

        Args:
            language (str): The detected language code.

        Returns:
            Dict[str, Pattern]: A dictionary of field name to regex pattern.
        """
        # Shared pattern for guest location
        guest_location_pattern = re.compile(
            r"[0-9a-zA-Z-]+bec06f\.jpg\]\s*(?:(?P<city>[A-Za-zÀ-ÖØ-öø-ÿ\s]+),\s*)?"
            r"(?P<country>[A-Za-zÀ-ÖØ-öø-ÿ\s]{1,20})(?=\r\n\r\n\S)"
        )

        if language == "fr":
            return {
                "arrival_date": re.compile(
                    r"(?:Arrivée\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.\s(\d{4}))?"
                ),
                "departure_date": re.compile(
                    r"(?:Départ\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.\s(\d{4}))?"
                ),
                "number_of_guests": re.compile(r"(?:Voyageurs)\r\n\r\n(\d{1,2})\s(?:adultes|adulte)(?:,\s(\d{1,2}))?"),
                "confirmation_code": re.compile(r"(?<=Code\sde\sconfirmation\r\n\r\n)(\w{10})"),
                "price_by_night_guest": re.compile(
                    r"(?<=Le\svoyageur\sa\spayé\r\n\r\n)([\d,\.]+)\s€\sx\s(\d{1,2})\snuits?\r\n\r\n([\d,\.\u202f]+)\s€"
                ),
                "cleaning_fee": re.compile(r"Frais de ménage\s*(?:pour les séjours courte durée\s*)?\r?\n\s*([\d\,\.]+) €", re.IGNORECASE),
                "guest_service_fee": re.compile(r"(?<=Frais\sde\sservice\svoyageur\r\n\r\n)([\d,\.]+)\s€"),
                "host_service_fee": re.compile(
                    r"service(?:\shôte\s\((?P<tax>\d.\d\s\%)\s\+\sTVA\))?\r\n\r\n(?P<host_service_fee>-[\d,\.]+)\s€"
                ),
                "tourist_tax": re.compile(r"Taxes de séjour\s*\r?\n\s*([\d,\.]+)\s€"),
                "host_payout": re.compile(r"(?:gagnez)?\r\n([\d\.,\u202f]+)\s€(?:\r\n\r\n)(?:L'argent)?"),
                "guest_payout": re.compile(r"(?<=Total\s\(EUR\)\r\n)([\d\.,\u202f]+)(?=\s?\€\r\nVersement)"),
                "guest_location": guest_location_pattern,
            }
        elif language == "en":
            return {
                "arrival_date": re.compile(
                    r"(?:Check-in\r\n\r\n)(\w{3}),\s(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\.\s(\d{4}))?"
                ),
                "departure_date": re.compile(
                    r"(?:Checkout\r\n\r\n)(\w{3}),\s(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\.\s(\d{4}))?"
                ),
                "number_of_guests": re.compile(r"(?:Guests)\r\n\r\n(\d{1,2})\s(?:adults|adult)(?:,\s(\d{1,2}))?"),
                "confirmation_code": re.compile(r"(?<=Confirmation\scode\r\n\r\n)(\w{10})"),
                "price_by_night_guest": re.compile(
                    r"(?<=Guest\spaid\r\n\r\n)€\s([\d,\.]+)\sx\s(\d{1,2})\snights?\r\n\r\n€\s([\d,\.]+)"
                ),
                "cleaning_fee": re.compile(r"(?<=Cleaning\sfee\r\n\r\n)€\s([\d,\.]+)", re.IGNORECASE),
                "guest_service_fee": re.compile(r"(?<=Guest\sservice\sfee\r\n\r\n)€\s([\d,\.]+)"),
                "host_service_fee": re.compile(
                    r"fee(?:\s\((?P<tax>\d.\d\%)\s\+\sVAT\))?\r\n\r\n(?P<host_service_fee>-€\s[\d,\.]+)"
                ),
                "tourist_tax": re.compile(r"(?<=\s€\s)([\d,\.]+)*\sin\sOccupancy\sTaxes\."),
                "host_payout": re.compile(r"(?:You\searn)?\r\n€\s([\d,\.]+)(?:\r\n\r\n)(?:The\smoney)?"),
                "guest_payout": re.compile(r"(?<=Total\s\(EUR\)\r\n)€\s?([\d\.,\u202f]+)(?=\r\nHost\spayout)"),
                "guest_location": guest_location_pattern,
            }
        else:
            return {}


def append_booking_data_to_csv(filename: str, data: Dict[str, Any]) -> None:
    """
    Appends booking data to a CSV file if the confirmation code is not already present.

    Args:
        filename (str): The path to the CSV file.
        data (Dict[str, Any]): A dictionary containing booking details, including a confirmation code.
    """
    confirmation_code = data.get("Confirmation Code")
    if not confirmation_code or confirmation_code == "N/A":
        print("No valid confirmation code found in the data.")
        raise ValueError("No valid confirmation code found in the data.")

    # Check if code already exists
    if confirmation_code_exists_in_csv(filename, confirmation_code):
        print(f"Confirmation code {confirmation_code} already exists. Data will not be appended.")
        return

    with open(filename, "a", encoding="utf-8", newline="") as csvfile:
        fieldnames = [
            "Date",
            "Arrival Date",
            "Departure Date",
            "Confirmation Code",
            "Cost per Night",
            "Number of Nights",
            "Total Nights Cost",
            "Cleaning Fee",
            "Guest Service Fee",
            "Host Service Fee",
            "Tourist Tax",
            "Total Paid by Guest",
            "Host Payout",
            "Number of Adults",
            "Number of Children",
            "Guest_Location",
            "Full_Name",
            "Subject",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=",")
        if os.stat(filename).st_size == 0:
            writer.writeheader()

        writer.writerow(data)
        print(f"Data with confirmation code {confirmation_code} has been appended to {filename}.")


def confirmation_code_exists_in_csv(filename: str, confirmation_code: str) -> bool:
    """
    Checks if a given confirmation code already exists in a CSV file.

    Args:
        filename (str): The path to the CSV file.
        confirmation_code (str): The confirmation code to search for.

    Returns:
        bool: True if the confirmation code is found, False otherwise.
    """
    if not os.path.exists(filename):
        return False

    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return any(row.get('Confirmation Code') == confirmation_code for row in reader)
