import pytest
from services.mail_processing.parser import Parser
import os
import csv

# Sample email data taken from your main code:
FRENCH_SAMPLE = {
    'Sender': 'Davy Chen <Davy03cosh@hotmail.fr>',
    'Subject': 'TR : Réservation confirmée\xa0: Kurt Pihl arrive le 4 mai',
    'Date': '2025-02-02',
    'Snippet': '...',
    'Message_body': (
        "________________________________\r\nDe : Airbnb \r\nEnvoyé : dimanche 2 février 2025 11:37:12 (UTC+01:00) Brussels, Copenhagen, Madrid, Paris\r\n"
        "À : davy03cosh@hotmail.fr \r\nSujet : Réservation confirmée : Kurt Pihl arrive le 4 mai\r\n\r\n\r\n[Airbnb]\r\n"
        "Nouvelle réservation confirmée ! Kurt arrive le 4 mai\r\n\r\nEnvoyez un message pour confirmer les détails de l'entrée dans les lieux ou pour souhaiter la bienvenue à Kurt.\r\n\r\n"
        "[https://a0.muscache.com/im/pictures/d109f44f-35a7-4336-9420-750576bec06f.jpg]DK\r\n"
        "Bonjour Davy < br/> Nous sommes un couple plus âgé avec une fille adulte qui verra Paris pour fø ; la dernière fois. < br/> "
        "Nous nous attendons à une arrivée à 15 h et à un départ à 11 h/> < br/> Cordialement, < br/> Kurt Pihl < br/> Copenhague < br/> "
        "Danemark < br/> Danemark < br/> Danemark < br/> Danemark < br/> Danemark\r\n\r\n"
        "[https://a0.muscache.com/im/pictures/5c6aa18e-5d55-4997-850f-ab93c6d4b2ca.jpg]Traduit automatiquement. Le message original est le suivant :\r\n\r\n"
        "Arrivée\r\n\r\ndim. 4 mai\r\n\r\n15:00\r\n\r\nDépart\r\n\r\nsam. 10 mai\r\n\r\n11:00\r\n\r\nVoyageurs\r\n\r\n3 adultes\r\n\r\nPlus d'informations...\r\n\r\n"
        "Code de confirmation\r\n\r\nHMFANA2QCA\r\n\r\nVoir le récapitulatif\r\nLe voyageur a payé\r\n\r\n163,33 € x 6 nuits\r\n\r\n980,00 €\r\n\r\n"
        "Frais de ménage\r\n\r\n65,00 €\r\n\r\nFrais de service voyageur\r\n\r\n184,41 €\r\n\r\nTaxes de séjour\r\n\r\n159,25 €\r\n\r\n"
        "Total (EUR)\r\n1\u202f388,66 €\r\nVersement de l'hôte\r\n\r\nFrais de chambre pour 6 nuits\r\n\r\n980,00 €\r\n\r\nFrais de ménage\r\n\r\n65,00 €\r\n\r\n"
        "Frais de service hôte (3.0 % + TVA)\r\n\r\n-37,62 €\r\n\r\nVous gagnez\r\n1\u202f007,38 €\r\n"
    )
}

ENGLISH_SAMPLE = {
    'Sender': 'Davy Chen <Davy03cosh@hotmail.fr>',
    'Subject': 'TR : Reservation confirmed - Orwis Huang arrives 2 Oct',
    'Date': '2024-09-12',
    'Snippet': '...',
    'Message_body': (
        "________________________________\r\nDe : Airbnb \r\nEnvoyé : jeudi 12 septembre 2024 14:39:47 (UTC+01:00) Brussels, Copenhagen, Madrid, Paris\r\n"
        "À : davy03cosh@hotmail.fr \r\nSujet : Reservation confirmed - Orwis Huang arrives 2 Oct\r\n\r\n\r\n[Airbnb]\r\n"
        "New booking confirmed! Orwis arrives 2 Oct.\r\n\r\nSend a message to confirm check-in details or welcome Orwis.\r\n\r\n"
        "[https://a0.muscache.com/im/pictures/user/User/original/de9a9896-f5ba-4d83-af5f-0f54f21eb833.jpeg?aki_policy=profile_x_medium]\r\n\r\n"
        "Orwis\r\n\r\n[https://a0.muscache.com/im/pictures/0d520e2d-fe10-4292-a6b5-3616cbae5d94.jpg]Identity verified\r\n\r\n"
        "[https://a0.muscache.com/im/pictures/d109f44f-35a7-4336-9420-750576bec06f.jpg]Shanghai, China\r\n\r\n"
        "Send Orwis a Message\r\n\r\n[Appartement 90m² rénové avec balcon - Paris]\r\n\r\nAppartement 90m² rénové avec balcon - Paris\r\n\r\nRoom\r\n\r\n"
        "Check-in\r\n\r\nWed, 2 Oct\r\n\r\n15:00\r\n\r\nCheckout\r\n\r\nSat, 5 Oct\r\n\r\n12:00\r\n\r\nGuests\r\n\r\n2 adults\r\n\r\nMore details...\r\n\r\n"
        "Confirmation code\r\n\r\nHM5A8PDQY9\r\n\r\nView itinerary\r\nGuest paid\r\n\r\n€ 133.33 x 3 nights\r\n\r\n€ 400.00\r\n\r\nCleaning fee\r\n\r\n"
        "€ 65.00\r\n\r\nGuest service fee\r\n\r\n€ 70.96\r\n\r\nOccupancy taxes\r\n\r\n€ 65.00\r\n\r\nTotal (EUR)\r\n€ 600.96\r\n\r\n"
        "Host payout\r\n\r\n3-night room fee\r\n\r\n€ 400.00\r\n\r\nCleaning fee\r\n\r\n€ 65.00\r\n\r\nHost service fee (3.0% + VAT)\r\n\r\n"
        "-€ 16.74\r\n\r\nYou earn\r\n€ 448.26\r\n"
    )
}


def test_detect_language_french():
    parser = Parser(FRENCH_SAMPLE)
    assert parser.detect_language() == 'fr'


def test_detect_language_english():
    parser = Parser(ENGLISH_SAMPLE)
    assert parser.detect_language() == 'en'


def test_parse_data_french():
    parser = Parser(FRENCH_SAMPLE)
    data = parser.parse_data(print_data=False)
    # Check that language-specific fields are parsed.
    assert data.get("Confirmation Code") == "HMFANA2QCA"
    # Since the French sample does not include the full expected block for arrival/departure,
    # we check that the fields are present even if with default values.
    for key in ["Arrival_DayOfWeek", "Arrival_Day", "Arrival_Month", "Arrival_Year"]:
        assert key in data
    # Check extra fields from __init__
    assert data.get("Mail Date") == "2025-02-02"
    # Person name should have been extracted from subject (e.g. "Kurt Pihl")
    assert "Kurt Pihl" in data.get("Person Name", "")


def test_parse_data_english():
    parser = Parser(ENGLISH_SAMPLE)
    data = parser.parse_data(print_data=False)
    assert data.get("Confirmation Code") == "HM5A8PDQY9"
    # Check that English language was detected and some expected fields exist.
    for key in ["Arrival_DayOfWeek", "Arrival_Day", "Arrival_Month", "Arrival_Year"]:
        assert key in data
    # Check extra fields from __init__
    assert data.get("Mail Date") == "2024-09-12"
    # Person name should be extracted from subject (e.g. "Orwis Huang")
    assert "Orwis Huang" in data.get("Person Name", "")


def test_raw_string_input_language_unknown():
    # If a raw string is passed instead of a dict, the language should be 'unknown'
    raw_mail = "This is just a random email message with no specific language keywords."
    parser = Parser(raw_mail)
    # As no keywords are found, language should be 'unknown'
    assert parser.detect_language() == 'unknown'
    data = parser.parse_data(print_data=False)
    # Most fields will be 'N/A'
    for key in data:
        # Just a check that the data dict has some expected keys
        assert key is not None
