import re
import warnings
from typing import Any, Dict, Match, Optional, Pattern


class Parser:
    """
    A parser for extracting booking details from an email message.
    """

    def __init__(self, mail: Any, debug: bool = False) -> None:
        """
        Initializes the Parser with the provided mail.

        Args:
            mail (Any): The email content to parse (can be a string or dict).
        """
        self.debug = debug
        self.person_name: str = "N/A"
        if isinstance(mail, dict):
            self.mail_date = self.parse_mail_date(mail)
            print(f"Mail date: {self.mail_date}") if self.debug else None
            self.message_body: str = mail.get("Message_body", "")
            subject = mail.get("Subject", "")
            # Attempt to extract person's name from subject
            subject_clean = subject.replace("TR :", "").strip()
            match = re.search(
                r"(Réservation confirmée|Reservation confirmed)\s*[:\-\u2013\u2014\u00A0]+\s*(.*?)\s+(?:arrive|arrives)",
                subject_clean,
                re.IGNORECASE,
            )
            if match:
                self.person_name = match.group(2).strip() or "N/A"
        else:
            self.mail_date = "N/A"
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
        elif any(
            keyword in body_lower for keyword in ["check-in", "checkout", "confirmed"]
        ):
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
            key: pattern.search(self.message_body) for key, pattern in patterns.items()
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
        data["mail_date"] = self.mail_date
        data["name"] = self.person_name

        numeric_fields = [
            "number_of_adults",
            "number_of_children",
            "price_by_night",
            "number_of_nights",
            "total_nights_cost",
            "cleaning_fee",
            "guest_service_fee",
            "host_service_fee",
            "tourist_tax",
            "guest_payout",
            "host_payout",
        ]
        for field in numeric_fields:
            print(
                f"Numeric field {field} before casted: {data[field]}"
            ) if self.debug else None
            try:
                data[field] = float(data[field].replace("\u202f", ""))
            except ValueError:
                data[field] = 0.0

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
            data["arrival_day_of_week"] = self.safe_get(match, 1)
            data["arrival_day"] = self.safe_get(match, 2)
            data["arrival_month"] = self.safe_get(match, 3)
            data["arrival_year"] = self.safe_get(
                match, 4, self.mail_date[:4] if self.mail_date != "N/A" else "N/A"
            )
        else:
            data.update(
                {
                    "arrival_day_of_week": "N/A",
                    "arrival_day": "N/A",
                    "arrival_month": "N/A",
                    "arrival_year": "N/A",
                }
            )

    def parse_departure_date(
        self, match: Optional[Match], data: Dict[str, Any]
    ) -> None:
        """
        Extract and set departure date details (day of week, day, month, year).
        """
        if match:
            data["departure_day_of_week"] = self.safe_get(match, 1)
            data["departure_day"] = self.safe_get(match, 2)
            data["departure_month"] = self.safe_get(match, 3)
            data["departure_year"] = self.safe_get(
                match, 4, self.mail_date[:4] if self.mail_date != "N/A" else "N/A"
            )
        else:
            data.update(
                {
                    "departure_day_of_week": "N/A",
                    "departure_day": "N/A",
                    "departure_month": "N/A",
                    "departure_year": "N/A",
                }
            )

    def parse_number_of_guests(
        self, match: Optional[Match], data: Dict[str, Any]
    ) -> None:
        """
        Extract and set the number of adults/children.
        """
        if match:
            data["number_of_adults"] = self.safe_get(match, 1)
            data["number_of_children"] = self.safe_get(match, 2, "0")
        else:
            data.update({"number_of_adults": "N/A", "number_of_children": "N/A"})

    def parse_confirmation_code(
        self, match: Optional[Match], data: Dict[str, Any]
    ) -> None:
        """
        Extract and set the confirmation code.
        """
        data["confirmation_code"] = self.safe_get(match, 1)

    def parse_cleaning_fee(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set cleaning fee.
        """
        raw_value = self.safe_get(match, 1)
        data["cleaning_fee"] = (
            raw_value.replace(",", ".") if raw_value != "N/A" else "N/A"
        )

    def parse_guest_service_fee(
        self, match: Optional[Match], data: Dict[str, Any]
    ) -> None:
        """
        Extract and set guest service fee.
        """
        raw_value = self.safe_get(match, 1)
        data["guest_service_fee"] = (
            raw_value.replace(",", ".") if raw_value != "N/A" else "N/A"
        )

    def parse_host_service_fee(
        self, match: Optional[Match], data: Dict[str, Any]
    ) -> None:
        """
        Extract and set host service fee and tax.
        """
        if match:
            # Named groups for clarity
            fee_raw = self.safe_get(match, "host_service_fee")
            tax_raw = self.safe_get(match, "tax")
            data["host_service_fee"] = (
                fee_raw.replace(",", ".").replace("€", "").replace(" ", "")
                if fee_raw != "N/A"
                else "N/A"
            )
            data["host_service_tax"] = tax_raw if tax_raw != "N/A" else "N/A"
        else:
            data["host_service_fee"] = "N/A"
            data["host_service_tax"] = "N/A"

    def parse_tourist_tax(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set tourist tax.
        """
        raw_value = self.safe_get(match, 1)
        data["tourist_tax"] = (
            raw_value.replace(",", ".") if raw_value != "N/A" else "N/A"
        )

    def parse_price_by_night_guest(
        self, match: Optional[Match], data: Dict[str, Any]
    ) -> None:
        """
        Extract and set price per night, number of nights, and total price.
        """
        if match:
            data["price_by_night"] = self.safe_get(match, 1).replace(",", ".")
            data["number_of_nights"] = self.safe_get(match, 2)
            night_cost_raw = self.safe_get(match, 3)
            data["total_nights_cost"] = self.fix_payout_value(night_cost_raw)
        else:
            data.update(
                {
                    "price_by_night": "N/A",
                    "number_of_nights": "N/A",
                    "total_nights_cost": "N/A",
                }
            )

    def fix_payout_value(self, raw_value: str) -> str:
        """
        Cleans numeric string by removing thousands separators and ensuring a single decimal point.
        """

        cleaned = raw_value.replace("\u202f", "").strip()
        # Remove any non-digit or punctuation except '.' and ','
        cleaned = re.sub(r"[^\d.,]", "", cleaned)
        # Find all punctuation positions
        seps = [m.start() for m in re.finditer(r"[.,]", cleaned)]
        if len(seps) > 1:
            # Last punctuation is the decimal
            main = re.sub(r"[.,]", "", cleaned[: seps[-1]])
            decimal = cleaned[seps[-1] :].replace(",", ".")
            return main + decimal
        return cleaned.replace(",", ".")

    def parse_guest_payout(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set the total payout from the guest.
        """
        raw_value = self.safe_get(match, 1)
        if raw_value != "N/A":
            data["guest_payout"] = self.fix_payout_value(raw_value)
        else:
            data["guest_payout"] = "N/A"

    def parse_host_payout(self, match: Optional[Match], data: Dict[str, Any]) -> None:
        """
        Extract and set the host's final payout.
        """
        raw_value = self.safe_get(match, 1)
        data["host_payout"] = self.fix_payout_value(raw_value)

    def parse_guest_location(
        self, match: Optional[Match], data: Dict[str, Any]
    ) -> None:
        """
        Extract and set the guest's country/city.
        """
        if match:
            country = self.safe_get(match, "country")
            city = self.safe_get(match, "city")
            data["country"] = country
            data["city"] = city
        else:
            data.update({"country": "N/A", "city": "N/A"})

    def parse_mail_date(self, mail: dict) -> str:
        """
        Extracts the mail date from the 'Snippet' field if present. Because the 'Date' field as a small lag in time (UTC+1) and one booking was input on the wrong year,
        the 'Snippet' field is used to get the correct date.
        """
        snippet = mail.get("Snippet", "")
        if snippet:
            date_match = re.search(
                r"Envoyé\s*:\s*[\wé]+ (\d{1,2}) (\w+) (\d{4}) (?:\d{2}:\d{2}:\d{2})",
                snippet,
            )
            if date_match:
                date = date_match.group(1)
                month = date_match.group(2)
                month_mapping = {
                    "janvier": "01",
                    "février": "02",
                    "mars": "03",
                    "avril": "04",
                    "mai": "05",
                    "juin": "06",
                    "juillet": "07",
                    "août": "08",
                    "septembre": "09",
                    "octobre": "10",
                    "novembre": "11",
                    "décembre": "12",
                }
                month = month_mapping.get(month.lower(), month)
                year = date_match.group(3)
                return f"{year}-{month.zfill(2)}-{date.zfill(2)}"
        return mail.get("Date", "N/A")

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
                    r"(?:Arrivée\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.?\s(\d{4}))?"
                ),
                "departure_date": re.compile(
                    r"(?:Départ\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.?\s(\d{4}))?"
                ),
                "number_of_guests": re.compile(
                    r"(?:Voyageurs)\r\n\r\n(\d{1,2})\s(?:adultes|adulte)(?:,\s(\d{1,2}))?"
                ),
                "confirmation_code": re.compile(
                    r"(?<=Code\sde\sconfirmation\r\n\r\n)(\w{10})"
                ),
                "price_by_night_guest": re.compile(
                    r"(?<=Le\svoyageur\sa\spayé\r\n\r\n)([\d,\.]+)\s€\sx\s(\d{1,2})\snuits?\r\n\r\n([\d,\.\u202f]+)\s€"
                ),
                "cleaning_fee": re.compile(
                    r"Frais de ménage\s*(?:pour les séjours courte durée\s*)?\r?\n\s*([\d\,\.]+) €",
                    re.IGNORECASE,
                ),
                "guest_service_fee": re.compile(
                    r"(?<=Frais\sde\sservice\svoyageur\r\n\r\n)([\d,\.]+)\s€"
                ),
                "host_service_fee": re.compile(
                    r"service(?:\shôte\s\((?P<tax>\d.\d\s\%)\s\+\sTVA\))?\r\n\r\n(?P<host_service_fee>-[\d,\.]+)\s€"
                ),
                "tourist_tax": re.compile(r"Taxes de séjour\s*\r?\n\s*([\d,\.]+)\s€"),
                "host_payout": re.compile(
                    r"(?:gagnez|EUR\))\r\n([\d\.,\u202f]+)\s€(?:\r\n\r\n)(?:Votre|L'argent)"
                ),
                "guest_payout": re.compile(
                    r"(?<=Total\s\(EUR\)\r\n)([\d\.,\u202f]+)(?=\s?\€\r\nVersement)"
                ),
                "guest_location": guest_location_pattern,
            }
        elif language == "en":
            return {
                "arrival_date": re.compile(
                    r"(?:Check-in\r\n\r\n)(\w{3}),\s(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\.?\s(\d{4}))?"
                ),
                "departure_date": re.compile(
                    r"(?:Checkout\r\n\r\n)(\w{3}),\s(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\.?\s(\d{4}))?"
                ),
                "number_of_guests": re.compile(
                    r"(?:Guests)\r\n\r\n(\d{1,2})\s(?:adults|adult)(?:,\s(\d{1,2}))?"
                ),
                "confirmation_code": re.compile(
                    r"(?<=Confirmation\scode\r\n\r\n)(\w{10})"
                ),
                "price_by_night_guest": re.compile(
                    r"(?<=Guest\spaid\r\n\r\n)€\s([\d,\.]+)\sx\s(\d{1,2})\snights?\r\n\r\n€\s([\d,\.]+)"
                ),
                "cleaning_fee": re.compile(
                    r"(?<=Cleaning\sfee\r\n\r\n)€\s([\d,\.]+)", re.IGNORECASE
                ),
                "guest_service_fee": re.compile(
                    r"(?<=Guest\sservice\sfee\r\n\r\n)€\s([\d,\.]+)"
                ),
                "host_service_fee": re.compile(
                    r"fee(?:\s\((?P<tax>\d.\d\%)\s\+\sVAT\))?\r\n\r\n(?P<host_service_fee>-€\s[\d,\.]+)"
                ),
                "tourist_tax": re.compile(
                    r"(?<=\s€\s)([\d,\.]+)*\sin\sOccupancy\sTaxes\."
                ),
                "host_payout": re.compile(
                    r"(?:earn|EUR\))\r\n€\s([\d\.,\u202f]+)(?:\r\n\r\n)(?:The|Your)"
                ),
                "guest_payout": re.compile(
                    r"(?<=Total\s\(EUR\)\r\n)€\s?([\d\.,\u202f]+)(?=\r\nHost\spayout)"
                ),
                "guest_location": guest_location_pattern,
            }
        else:
            return {}
