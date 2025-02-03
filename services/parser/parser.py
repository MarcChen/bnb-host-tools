import re
import os
import csv
from typing import Dict, Any

class Parser:
    """
    A parser for extracting booking details from an email message.
    """

    def __init__(self, message_body: str) -> None:
        """
        Initializes the Parser with the provided message body.
        
        Args:
            message_body (str): The email body to parse.
        """
        self.message_body: str = message_body
        self.language: str = self.detect_language()

    def detect_language(self) -> str:
        """
        Detect the language of the email based on specific keywords.

        Returns:
            str: The detected language ('fr', 'en', or 'unknown').
        """
        if "Arrivée" in self.message_body or "Départ" in self.message_body or "Confirmée" in self.message_body:
            return 'fr'
        elif "Check-in" in self.message_body or "Checkout" in self.message_body:
            return 'en'
        return 'unknown'

    def parse_data(self, print_data: bool = False) -> Dict[str, Any]:
        """
        Parses the booking data from the message body.

        Args:
            print_data (bool): Whether to print regex match failures.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed data.
        """
        data: Dict[str, Any] = {}

        # Regular expressions for shared and language-specific data
        country_code_regex = re.compile(r"(?<=bec06f\.jpg\])([A-Z]{2})?(\w+\d*,\s*\w+\d*)?(?=\r\n)")
        if self.language == 'fr':
            arrival_date_regex = re.compile(r"(?:Arrivée\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.\s(\d{4}))?")
            departure_date_regex = re.compile(r"(?:Départ\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.\s(\d{4}))?")
            number_of_guests = re.compile(r"(?:Voyageurs)\r\n\r\n(\d{1,2})\s(?:adultes|adulte)(?:\,\s(\d{1,2}))?")
            confirmation_code_regex = re.compile(r"(?<=Code\sde\sconfirmation\r\n\r\n)(\w{10})")
            price_by_night_guest_regex = re.compile(r"(?<=Le\svoyageur\sa\spayé\r\n\r\n)([\d\,\.]+)\s€\sx\s(\d{1,2})\snuits\r\n\r\n([\d\,\.]+)\s€")
            cleaning_fee_regex = re.compile(r"Frais de ménage\s*(?:pour les séjours courte durée\s*)?\r?\n\s*([\d\,\.]+) €")
            guest_service_fee_regex = re.compile(r"(?<=Frais\sde\sservice\svoyageur\r\n\r\n)([\d\,\.]+)\s€")
            host_service_fee_regex = re.compile(r"(?<=hôte\s\((\d.\d\s\%)\s\+\sTVA\)\r\n\r\n)(-\d{1,5},\d{2})\s€")
            tourist_tax_regex = re.compile(r"Taxes de séjour\s*\r?\n\s*([\d\,\.]+) €")
            host_payout_regex = re.compile(r"(?<=gagnez\r\n)([\d\,\.]+)\s€")
            guest_payout_regex = re.compile(r"(?<=Total\s\(EUR\)\r\n)(\d{1,2})?(?:\u202f)?(\d{3,5},\d{2})(?=\s?\€\r\nVersement)")
        elif self.language == 'en':
            arrival_date_regex = re.compile(r"(?:Check-in\r\n\r\n)(\w{3}),\s(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\.\s(\d{4}))?")
            departure_date_regex = re.compile(r"(?:Checkout\r\n\r\n)(\w{3}),\s(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\.\s(\d{4}))?")
            number_of_guests = re.compile(r"(?:Guests)\r\n\r\n(\d{1,2})\s(?:adults|adult)(?:\,\s(\d{1,2}))?")
            confirmation_code_regex = re.compile(r"(?<=Confirmation\scode\r\n\r\n)(\w{10})")
            price_by_night_guest_regex = re.compile(r"(?<=Guest\spaid\r\n\r\n)€\s([\d\,\.]+)\sx\s(\d{1,2})\snights\r\n\r\n€\s([\d\,\.]+)")
            cleaning_fee_regex = re.compile(r"(?<=Cleaning\sfee\r\n\r\n)€\s([\d\,\.]+)")
            guest_service_fee_regex = re.compile(r"(?<=Guest\sservice\sfee\r\n\r\n)€\s([\d\,\.]+)")
            host_service_fee_regex = re.compile(r"(?<=Host\sservice\sfee\s\((\d.\d\%)\s\+\sVAT\)\r\n\r\n)(-(?:€)\s\d{1,5}\.\d{2})")
            tourist_tax_regex = re.compile(r"(?<=\s€\s)([\d\,\.]+)*\sin\sOccupancy\sTaxes\.")
            host_payout_regex = re.compile(r"(?<=You\searn\r\n)€\s([\d\,\.]+)")
            guest_payout_regex = re.compile(r"(?<=Total\s\(EUR\)\r\n)€\s(\d{1,2})?(?:\u202f)?(\d{3,5}\.\d{2})(?=\r\nHost\spayout)")
        else:
            print("Language not detected or unsupported.")
            return data

        # ...existing code for regex matching...
        arrival_date_match = arrival_date_regex.search(self.message_body)
        departure_date_match = departure_date_regex.search(self.message_body)
        number_of_guests_match = number_of_guests.search(self.message_body)
        confirmation_code_match = confirmation_code_regex.search(self.message_body)
        cleaning_fee_match = cleaning_fee_regex.search(self.message_body)
        guest_service_fee_match = guest_service_fee_regex.search(self.message_body)
        host_service_fee_match = host_service_fee_regex.search(self.message_body)
        tourist_tax_match = tourist_tax_regex.search(self.message_body)
        price_by_night_guest_match = price_by_night_guest_regex.search(self.message_body)
        host_payout_match = host_payout_regex.search(self.message_body)
        guest_payout_match = guest_payout_regex.search(self.message_body)
        country_code_match = country_code_regex.search(self.message_body)
        
        if print_data:
            not_found_fields = {
                "arrival_date_match": arrival_date_match,
                "departure_date_match": departure_date_match,
                "number_of_guests_match": number_of_guests_match,
                "confirmation_code_match": confirmation_code_match,
                "cleaning_fee_match": cleaning_fee_match,
                "guest_service_fee_match": guest_service_fee_match,
                "host_service_fee_match": host_service_fee_match,
                "tourist_tax_match": tourist_tax_match,
                "price_by_night_guest_match": price_by_night_guest_match,
                "host_payout_match": host_payout_match,
                "guest_payout_match": guest_payout_match,
                "country_code_match": country_code_match
            }
            for field, match in not_found_fields.items():
                if not match:
                    print(f"{field} not found")

        # Grouping matches and processing data
        if arrival_date_match and len(arrival_date_match.groups()) == 4:
            data['Arrival_DayOfWeek'] = arrival_date_match.group(1).strip()
            data['Arrival_Day'] = arrival_date_match.group(2).strip()
            data['Arrival_Month'] = arrival_date_match.group(3).strip()
            data['Arrival_Year'] = (arrival_date_match.group(4).strip()
                                    if arrival_date_match.group(4) is not None
                                    else "No year specified")
        else:
            data.update({'Arrival_DayOfWeek': 'N/A', 'Arrival_Day': 'N/A', 'Arrival_Month': 'N/A', 'Arrival_Year': 'N/A'})

        if departure_date_match:
            data['Departure_DayOfWeek'] = departure_date_match.group(1).strip()
            data['Departure_Day'] = departure_date_match.group(2).strip()
            data['Departure_Month'] = departure_date_match.group(3).strip()
            data['Departure_Year'] = (departure_date_match.group(4).strip()
                                      if departure_date_match.group(4) is not None
                                      else "No year specified")
        else:
            data.update({'Departure_DayOfWeek': 'N/A', 'Departure_Day': 'N/A', 'Departure_Month': 'N/A', 'Departure_Year': 'N/A'})

        if number_of_guests_match:
            data['Number of Adults'] = number_of_guests_match.group(1).strip()
            data['Number of child'] = (number_of_guests_match.group(2).strip()
                                       if number_of_guests_match.group(2) is not None
                                       else "0")
        else:
            data.update({'Number of Adults': 'N/A', 'Number of child': 'N/A'})

        if confirmation_code_match:
            data['Confirmation Code'] = confirmation_code_match.group(1).strip()
        else:
            data['Confirmation Code'] = 'N/A'

        if cleaning_fee_match:
            if len(cleaning_fee_match.groups()) == 2 and cleaning_fee_match.group(1) != cleaning_fee_match.group(2):
                data['Cleaning Fee'] = "ERROR : 2 different cleaning fees !"
            else:
                data['Cleaning Fee'] = cleaning_fee_match.group(1).replace(",", ".").strip()
        else:
            data['Cleaning Fee'] = 'N/A'

        if guest_service_fee_match:
            data['Guest Service Fee'] = guest_service_fee_match.group(1).replace(",", ".").strip()
        else:
            data['Guest Service Fee'] = 'N/A'

        if host_service_fee_match:
            data['Host Service Fee Percentage'] = host_service_fee_match.group(1)
            data['Host Service Fee'] = host_service_fee_match.group(2).replace(",", ".").strip()
        else:
            data.update({'Host Service Fee': 'N/A', 'Host Service Fee Percentage': 'N/A'})

        if tourist_tax_match:
            data['Tourist Tax'] = tourist_tax_match.group(1).replace(",", ".").strip()
        else:
            data['Tourist Tax'] = 'N/A'

        if price_by_night_guest_match:
            data['Price by night'] = price_by_night_guest_regex.search(self.message_body).group(1).replace(",", ".").strip()
            data['Number of nights'] = price_by_night_guest_match.group(2).strip()
            data['Total Price for all nights'] = price_by_night_guest_match.group(3).replace(",", ".").strip()
        else:
            data.update({'Price by night': 'N/A', 'Number of nights': 'N/A', 'Total Paid by Guest': 'N/A'})

        if country_code_match:
            if country_code_match.group(1) is not None:
                data['Country Code'] = country_code_match.group(1)
            elif country_code_match.group(2) is not None:
                data['Country Code'] = country_code_match.group(2)
            else:
                data['Country Code'] = 'N/A'
        else:
            data['Country Code'] = 'N/A'

        if host_payout_match:
            data['Host Payout'] = host_payout_match.group(1).replace(",", ".").strip()
        else:
            data['Host Payout'] = 'N/A'

        if guest_payout_match:
            if guest_payout_match.group(1) is not None:
                data['Guest Payout'] = guest_payout_match.group(1) + guest_payout_match.group(2).replace(",", ".")
            else:
                data['Guest Payout'] = guest_payout_match.group(2).replace(",", ".")
        else:
            data['Guest Payout'] = 'N/A'
        return data

def append_booking_data_to_csv(filename: str, data: Dict[str, Any]) -> None:
    """
    Appends booking data to a CSV file if the confirmation code is not already present.

    Args:
        filename (str): The path to the CSV file.
        data (Dict[str, Any]): A dictionary containing booking details, including a confirmation code.
    """
    confirmation_code = data.get("Confirmation Code")
    if not confirmation_code:
        print("No confirmation code found in the data.")
        return

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
            "Country Code",
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

if __name__ == "__main__":
    # Sample message body for testing (French sample)
    sample_message = (
        "Arrivée\r\n\r\nMon. 21 jun\r\n"
        "Départ\r\n\r\nTue. 22 jun\r\n"
        "Code de confirmation\r\n\r\nABCDEFGHIJ\r\n"
        "Frais de ménage\r\n\r\n120,50 €\r\n"
        "Frais de service voyageur\r\n\r\n15,00 €\r\n"
        "hôte (10,0 % + TVA)\r\n\r\n-20,00 €\r\n"
        "Taxes de séjour\r\n\r\n5,00 €\r\n"
        "Le voyageur a payé\r\n\r\n100,00 € x 2 nuits\r\n\r\n200,00 €\r\n"
        "gagnez\r\n\r\n180,00 €\r\n"
        "bec06f.jpg]FR\r\n"
    )
    parser = Parser(sample_message)
    parsed_data = parser.parse_data(print_data=True)
    print("Parsed Data:")
    for key, value in parsed_data.items():
        print(f"{key}: {value}")