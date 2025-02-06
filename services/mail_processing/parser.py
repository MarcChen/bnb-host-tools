import re
import os
import csv
from typing import Dict, Any

class Parser:
    """
    A parser for extracting booking details from an email message.
    """

    def __init__(self, mail: str) -> None:
        """
        Initializes the Parser with the provided mail.
        
        Args:
            mail (str): The email content to parse.
        """
        # If a dict is provided, extract extra fields and update mail accordingly.
        if isinstance(mail, dict):
            self.mail_date = mail.get("Date", "N/A")
            subject = mail.get("Subject", "")
            # Remove any prefix like "TR :" and attempt to extract the person name.
            subject_clean = subject.replace("TR :", "").strip()
            print(f"Subject: {subject_clean}")
            match = re.search(r"(Réservation confirmée|Reservation confirmed)\s*[:\-\u2013\u2014\u00A0]+\s*(.*?)\s+(?:arrive|arrives)", subject_clean, re.IGNORECASE)
            self.person_name = match.group(2).strip() if match else "N/A"
            self.message_body = mail.get("Message_body", "")
        else:
            self.message_body: str = mail
            self.mail_date = "N/A"
            self.person_name = "N/A"
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
            host_payout_regex = re.compile(r"(?<=gagnez\r\n)([\d\.,\u202f]+)\s€")
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
            default_year = self.mail_date[:4] if self.mail_date != "N/A" else "N/A"
            data['Arrival_Year'] = (arrival_date_match.group(4).strip() 
                                    if arrival_date_match.group(4) is not None 
                                    else default_year)
        else:
            data.update({'Arrival_DayOfWeek': 'N/A', 'Arrival_Day': 'N/A', 'Arrival_Month': 'N/A', 'Arrival_Year': 'N/A'})

        if departure_date_match:
            data['Departure_DayOfWeek'] = departure_date_match.group(1).strip()
            data['Departure_Day'] = departure_date_match.group(2).strip()
            data['Departure_Month'] = departure_date_match.group(3).strip()
            default_year = self.mail_date[:4] if self.mail_date != "N/A" else "N/A"
            data['Departure_Year'] = (departure_date_match.group(4).strip() 
                                      if departure_date_match.group(4) is not None 
                                      else default_year)
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

        # Append extra fields from the sample
        data["Mail Date"] = self.mail_date
        data["Person Name"] = self.person_name

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
    samples = [{'Sender': 'Davy Chen <Davy03cosh@hotmail.fr>', 'Subject': 'TR : Réservation confirmée\xa0: Kurt Pihl arrive le 4 mai', 'Date': '2025-02-02', 'Snippet': 'De : Airbnb &lt;automated@airbnb.com&gt; Envoyé : dimanche 2 février 2025 11:37:12 (UTC+01:00) Brussels, Copenhagen, Madrid, Paris À : davy03cosh@hotmail.fr &lt;davy03cosh@hotmail.fr&gt; Sujet :', 'Message_body': '________________________________\r\nDe : Airbnb \r\nEnvoyé : dimanche 2 février 2025 11:37:12 (UTC+01:00) Brussels, Copenhagen, Madrid, Paris\r\nÀ : davy03cosh@hotmail.fr \r\nSujet : Réservation confirmée : Kurt Pihl arrive le 4 mai\r\n\r\n\r\n[Airbnb]\r\nNouvelle réservation confirmée ! Kurt arrive le 4 mai\r\n\r\nEnvoyez un message pour confirmer les détails de l\'entrée dans les lieux ou pour souhaiter la bienvenue à Kurt.\r\n\r\n[https://a0.muscache.com/im/Portrait/Avatars/messaging/b3e03835-ade9-4eb7-a0bb-2466ab9a534d.jpg?im_t=K&im_w=240&im_f=airbnb-cereal-medium.ttf&im_c=ffffff]\n\r\n\r\nKurt\r\n\r\n[https://a0.muscache.com/im/pictures/0d520e2d-fe10-4292-a6b5-3616cbae5d94.jpg]Identité vérifiée\r\n\r\n[https://a0.muscache.com/im/pictures/d109f44f-35a7-4336-9420-750576bec06f.jpg]DK\r\n\r\nBonjour Davy < br/> Nous sommes un couple plus âgé avec une fille adulte qui verra Paris pour fø ; la dernière fois. < br/> Nous nous attendons à une arrivée à 15 h et à un départ à 11 h/> < br/> Cordialement, < br/> Kurt Pihl < br/> Copenhague < br/> Danemark < br/> Danemark < br/> Danemark < br/> Danemark < br/> Danemark\r\n\r\n[https://a0.muscache.com/im/pictures/5c6aa18e-5d55-4997-850f-ab93c6d4b2ca.jpg]Traduit automatiquement. Le message original est le suivant :\r\n\r\nHej Davy\r\nVi er et ældre par med en voksen datter som vil se Paris for første gang.\r\nVi forventer ankomst kl 15 og afrejse kl 11\r\n\r\nMed Venlig hilsen\r\nKurt Pihl\r\nCopenhagen\r\nDenmark\r\n\r\nLes messages des voyageurs et des hôtes ont été traduits automatiquement dans la langue utilisée pour votre compte. Vous pouvez modifier cette fonctionnalité dans vos paramètres.\r\n\r\nEnvoyez à Kurt un message\n\r\n[Appartement 90m² rénové avec balcon - Paris]\r\n\r\nAppartement 90m² rénové avec balcon - Paris\r\n\r\nChambre\r\n\r\nArrivée\r\n\r\ndim. 4 mai\r\n\r\n15:00\r\n\r\nDépart\r\n\r\nsam. 10 mai\r\n\r\n11:00\r\n\r\nVoyageurs\r\n\r\n3 adultes\r\n\r\nPlus d\'informations concernant les voyageurs\r\n\r\nLes voyageurs vous préciseront désormais s\'ils seront accompagnés d\'enfants ou de bébés. Indiquez-leur si votre logement est adapté aux enfants en mettant à jour votre règlement intérieur.\r\n\r\nCode de confirmation\r\n\r\nHMFANA2QCA\r\n\r\nVoir le récapitulatif\r\nLe voyageur a payé\r\n\r\n163,33 € x 6 nuits\r\n\r\n980,00 €\r\n\r\nFrais de ménage\r\n\r\n65,00 €\r\n\r\nFrais de service voyageur\r\n\r\n184,41 €\r\n\r\nTaxes de séjour\r\n\r\n159,25 €\r\n\r\nTotal (EUR)\r\n1\u202f388,66 €\r\nVersement de l\'hôte\r\n\r\nFrais de chambre pour 6 nuits\r\n\r\n980,00 €\r\n\r\nFrais de ménage\r\n\r\n65,00 €\r\n\r\nFrais de service hôte (3.0 % + TVA)\r\n\r\n-37,62 €\r\n\r\nVous gagnez\r\n1\u202f007,38 €\r\n\r\nVotre voyageur a payé 159,25 € en taxes de séjour. Airbnb se charge de reverser ces taxes en votre nom.\r\n\r\nPour en savoir plus sur vos obligations sociales et fiscales, rendez vous sur nos pages "Hôtes responsables".\r\n\r\nConditions d\'annulation\r\n\r\nVos conditions d\'annulation pour les voyageurs sont Strictes.\r\n\r\nLes pénalités d\'annulation de cette réservation incluent l\'obtention d\'un commentaire public indiquant que vous avez annulé, le paiement des frais d\'annulation ainsi que le blocage des nuits annulées sur votre calendrier.\r\n\r\nVoir les pénalités d\'annulation\r\nPréparez-vous pour l\'arrivée de Kurt\r\nConsulter les pratiques de sécurité liées au Covid-19\r\n\r\nNous avons créé un ensemble de pratiques de sécurité obligatoires liées au Covid-19 pour les hôtes Airbnb et les voyageurs. Ces pratiques incluent notamment la distanciation physique et le port d\'un masque.\r\n\r\nConsulter les pratiques\r\nAdoptez le processus de nettoyage renforcé en 5 étapes\r\n\r\nTous les hôtes doivent suivre le processus de nettoyage renforcé entre chaque séjour. Ce processus a été développé en partenariat avec des experts et vise à prévenir la propagation du Covid-19.\r\n\r\nConsulter le processus\r\nFournissez un plan d\'accès\r\n\r\nVérifiez que votre voyageur sait comment se rendre sur place.\r\n\r\nEnvoyer le message\r\n[AirCover pour les hôtes]\r\n\r\nUne protection complète, à chaque fois que vous accueillez des voyageurs.\r\n\r\nEn savoir plus\r\nAssistance utilisateurs\r\n\r\nContactez notre équipe d\'assistance 24h/24, 7j/7 partout dans le monde.\r\n\r\nVisiter le Centre d\'aideContacter Airbnb\r\n[Airbnb]\r\n\r\nAirbnb Ireland UC\r\n\r\n8 Hanover Quay\r\n\r\nDublin 2, Ireland\r\n\r\nConditions de paiement entre vous et :\r\n\r\nAirbnb Payments Luxembourg S.A.\r\n\r\n4 Rue Henri M. Schnadt\r\n\r\n2530 Luxembourg\r\n\r\nObtenir l\'application Airbnb\r\n\r\n[App Store]       [Google Play] \n'}, {'Sender': 'Davy Chen <Davy03cosh@hotmail.fr>', 'Subject': 'TR : Reservation confirmed - Orwis Huang arrives 2 Oct', 'Date': '2024-09-12', 'Snippet': 'De : Airbnb &lt;automated@airbnb.com&gt; Envoyé : jeudi 12 septembre 2024 14:39:47 (UTC+01:00) Brussels, Copenhagen, Madrid, Paris À : davy03cosh@hotmail.fr &lt;davy03cosh@hotmail.fr&gt; Sujet :', 'Message_body': '________________________________\r\nDe : Airbnb \r\nEnvoyé : jeudi 12 septembre 2024 14:39:47 (UTC+01:00) Brussels, Copenhagen, Madrid, Paris\r\nÀ : davy03cosh@hotmail.fr \r\nSujet : Reservation confirmed - Orwis Huang arrives 2 Oct\r\n\r\n\r\n[Airbnb]\r\nNew booking confirmed! Orwis arrives 2 Oct.\r\n\r\nSend a message to confirm check-in details or welcome Orwis.\r\n\r\n[https://a0.muscache.com/im/pictures/user/User/original/de9a9896-f5ba-4d83-af5f-0f54f21eb833.jpeg?aki_policy=profile_x_medium]\n\r\n\r\nOrwis\r\n\r\n[https://a0.muscache.com/im/pictures/0d520e2d-fe10-4292-a6b5-3616cbae5d94.jpg]Identity verified\r\n\r\n[https://a0.muscache.com/im/pictures/d109f44f-35a7-4336-9420-750576bec06f.jpg]Shanghai, China\r\n\r\nSend Orwis a Message\n\r\n[Appartement 90m² rénové avec balcon - Paris]\r\n\r\nAppartement 90m² rénové avec balcon - Paris\r\n\r\nRoom\r\n\r\nCheck-in\r\n\r\nWed, 2 Oct\r\n\r\n15:00\r\n\r\nCheckout\r\n\r\nSat, 5 Oct\r\n\r\n12:00\r\n\r\nGuests\r\n\r\n2 adults\r\n\r\nMore details about who’s coming\r\n\r\nGuests will now let you know if they’re bringing children and infants. Let them know upfront if your listing is suitable for children by updating your House Rules.\r\n\r\nConfirmation code\r\n\r\nHM5A8PDQY9\r\n\r\nView itinerary\r\nGuest paid\r\n\r\n€ 133.33 x 3 nights\r\n\r\n€ 400.00\r\n\r\nCleaning fee\r\n\r\n€ 65.00\r\n\r\nGuest service fee\r\n\r\n€ 70.96\r\n\r\nOccupancy taxes\r\n\r\n€ 65.00\r\n\r\nTotal (EUR)\r\n€ 600.96\r\nHost payout\r\n\r\n3-night room fee\r\n\r\n€ 400.00\r\n\r\nCleaning fee\r\n\r\n€ 65.00\r\n\r\nHost service fee (3.0% + VAT)\r\n\r\n-€ 16.74\r\n\r\nYou earn\r\n€ 448.26\r\n\r\nYour guest paid € 65.00 in Occupancy Taxes. Airbnb remits these taxes on your behalf.\r\n\r\nTo learn more about your fiscal and social obligations, please visit our Responsible Hosting pages.\r\n\r\nCancellations\r\n\r\nYour cancellation policy for guests is Strict.\r\n\r\nThe penalties for cancelling this reservation include getting a public review that shows you cancelled, paying a cancellation fee and having the cancelled nights blocked on your calendar.\r\n\r\nRead cancellation penalties\r\nGet ready for Orwis’s arrival\r\nReview the COVID-19 safety practices\r\n\r\nWe’ve created a set of mandatory COVID-19 safety practices for both Airbnb hosts and guests. These include practising social distancing and wearing a mask.\r\n\r\nReview practices\r\nFollow the 5-step enhanced cleaning process\r\n\r\nAll hosts are required to follow the enhanced cleaning process between guest stays. They were developed in partnership with experts in an effort to curb the spread of COVID-19.\r\n\r\nReview process\r\nProvide directions\r\n\r\nCheck that your guest knows how to get to your place.\r\n\r\nSend message\r\n[AirCover for Hosts]\r\n\r\nTop-to-bottom protection, included every time you host.\r\n\r\nLearn more\r\nCustomer support\r\n\r\nContact our support team 24/7 from anywhere in the world.\r\n\r\nVisit help centreContact Airbnb\r\n[Airbnb]\r\n\r\nAirbnb Ireland UC\r\n\r\n8 Hanover Quay\r\n\r\nDublin 2, Ireland\r\n\r\nPayment Terms between you and:\r\n\r\nAirbnb Payments UK Ltd.\r\n\r\nSuite 1, 3rd Floor\r\n\r\n11-12 St. James’s Square\r\n\r\nLondon, SW1Y 4LB\r\n\r\nUnited Kingdom\r\n\r\nGet the Airbnb app\r\n\r\n[App Store]    [Google Play] \n'}]
    results = []
    for sample in samples:
        parser = Parser(sample)
        parsed_data = parser.parse_data(print_data=True)
        results.append(parsed_data)
        for key, value in parsed_data.items():
            # if value == "N/A":
            #     print(f"{key} not found")
            print(f"{key}: {value}")
        print("-----")
    # # Assertions to ensure extra data was extracted correctly.
    # assert results[0].get("Mail Date") == "2025-02-02"
    # assert results[0].get("Person Name") == "N/A"  # no person name from subject
    # assert results[1].get("Mail Date") == "2025-02-02"
    # assert results[1].get("Person Name") == "Kurt Pihl"
    # assert results[2].get("Mail Date") == "2024-09-12"
    # assert results[2].get("Person Name") == "Orwis Huang"
    # print("All tests passed.")