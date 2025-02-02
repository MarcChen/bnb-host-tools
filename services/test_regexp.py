import re 

# message = """
# \r\n\r\nAppartement 90m² rénové avec balcon - Paris\r\n\r\nChambre\r\n\r\nArrivée\r\n\r\nlun. 20 janv. 2025\r\n\r\n15:00\r\n\r\nDépart\r\n\r\nlun. 27 janv. 2025\r\n\r\n11:00\r\n\r\n
# Voyageurs\r\n\r\n4 adultes\r\n\r\nPlus d\'informations concernant les voyageurs\r\n\r\nLes voyageurs vous préciseront désormais s\'ils seront accompagnés d\'enfants ou de bébés. Indiquez-leur si votre logement est adapté aux enfants en mettant à jour votre règlement intérieur.
# \r\n\r\nCode de confirmation\r\n\r\nHMHPDZNFPY\r\n\r\nVoir le récapitulatif\r\nLe voyageur a payé\r\n\r\n114,14 € x 7 nuits\r\n\r\n799,00 €\r\n\r\nFrais de ménage\r\n\r\n70,00 €\r\n\r\nFrais de service voyageur\r\n\r\n132,60 €\r\n\r\nTaxes de séjour\r\n\r\n129,83 €
# \r\n\r\nTotal (EUR)\r\n1\u202f131,43 €\r\nVersement de l\'hôte\r\n\r\nFrais de chambre pour 7 nuits\r\n\r\n940,00 €\r\n\r\nFrais de ménage\r\n\r\n70,00 €\r\n\r\nAjustement du tarif par nuit\r\n\r\n-141,00 €\r\n\r\nFrais de service hôte (3.0 % + TVA)\r\n\r\n-31,28 €\r\n\r\nVous gagnez\r\n837,72 €\r\n\r\nVotre voyageur a payé 129,83 € en taxes de séjour. Airbnb se charge de reverser ces taxes en votre nom.\r\n\r\nPour en savoir plus sur vos obligations sociales et fiscales, rendez vous sur nos pages .\r\n\r\nConditions d\'annulation\r\n\r\nVos conditions d\'annulation pour les voyageurs sont Strictes.\r\n\r\nLes pénalités d\'annulation de cette réservation incluent l\'obtention d\'un commentaire public indiquant que vous avez annulé, le paiement des frais d\'annulation ainsi que le blocage des nuits annulées sur votre calendrier.\r\n\r\nVoir les pénalités d\'annulation\r\nPréparez-vous pour l\'arrivée de Leandre\r\nConsulter les pratiques de sécurité liées au Covid-19\r\n\r\nNous avons créé un ensemble de pratiques de sécurité obligatoires liées au Covid-19 pour les hôtes Airbnb et les voyageurs. Ces pratiques incluent notamment la distanciation physique et le port d\'un masque.\r\n\r\nConsulter les pratiques\r\nAdoptez le processus de nettoyage renforcé en 5 étapes\r\n\r\nTous les hôtes doivent suivre le processus de nettoyage renforcé entre chaque séjour. Ce processus a été développé en partenariat avec des experts et vise à prévenir la propagation du Covid-19.\r\n\r\nConsulter le processus\r\nFournissez un plan d\'accès\r\n\r\nVérifiez que votre voyageur sait comment se rendre sur place.\r\n\r\nEnvoyer le message\r\n[AirCover pour les hôtes]\r\n\r\nUne protection complète, à chaque fois que vous accueillez des voyageurs.\r\n\r\nEn savoir plus\r\nAssistance utilisateurs\r\n\r\nContactez notre équipe d\'assistance 24h/24, 7j/7 partout dans le monde.\r\n\r\nVisiter le Centre d\'aideContacter Airbnb\r\n[Airbnb]\r\n\r\nAirbnb Ireland UC\r\n\r\n8 Hanover Quay\r\n\r\nDublin 2, Ireland\r\n\r\nConditions de paiement entre vous et :\r\n\r\nAirbnb Payments UK Ltd.\r\n\r\nSuite 1, 3rd Floor\r\n\r\n11-12 St. James’s Square\r\n\r\nLondon, SW1Y 4LB\r\n\r\nUnited Kingdom\r\n\r\nObtenir l\'application Airbnb\r\n\r\n[App Store]       [Google Play] \n'}"
# """


message_fr ='''

'Sender': 'Davy Chen Davy03cosh@hotmail.fr', 'Subject': 'TR : Réservation confirmée\xa0: Mohamed Nizar Ali arrive le 8 juil.', 'Date': '2024-06-09', 'Snippet': 'De : Airbnb <automated@airbnb.com> Envoyé : dimanche 9 juin 2024 13:26:44 (UTC+01:00) Brussels, Copenhagen, Madrid, Paris À : davy03cosh@hotmail.fr <davy03cosh@hotmail.fr> Sujet :', 'Message_body': '________________________________\r\nDe : Airbnb \r\nEnvoyé : dimanche 9 juin 2024 13:26:44 (UTC+01:00) Brussels, Copenhagen, Madrid, Paris\r\nÀ : davy03cosh@hotmail.fr \r\nSujet : Réservation confirmée : Mohamed Nizar Ali arrive le 8 juil.\r\n\r\n\r\n[Airbnb]\r\nNouvelle réservation confirmée ! Mohamed Nizar arrive le 8 juil.\r\n\r\nEnvoyez un message pour confirmer les détails de l\'entrée dans les lieux ou pour souhaiter la bienvenue à Mohamed Nizar.\r\n\r\n
[https://a0.muscache.com/im/pictures/user/User-190747960/original/c1facdbc-88dc-44e6-9a1c-16a6d368a9c5.jpeg?aki_policy=profile_x_medium]\n\r\n\r\nMohamed Nizar\r\n\r\n[https://a0.muscache.com/im/pictures/0d520e2d-fe10-4292-a6b5-3616cbae5d94.jpg]Identité vérifiée · 1 commentaire\r\n\r\n[https://a0.muscache.com/im/pictures/d109f44f-35a7-4336-9420-750576bec06f.jpg]Coimbatore, India\r\n\r\nBonjour Davy ! C\'est Nizar de Coimbatore, dans le sud de l\'Inde. Je prévois de venir à Paris le 8e matin de Londres avec ma femme et mes deux enfants adultes pour des vacances... j\'ai hâte de passer un excellent séjour chez vous et de vous guider pour des vacances mémorables 🌈👍\r\n\r\n[https://a0.muscache.com/im/pictures/5c6aa18e-5d55-4997-850f-ab93c6d4b2ca.jpg]Traduit automatiquement. Le message original est le suivant :\r\n\r\nHi Davy! This is Nizar from Coimbatore, southern part of India. planning to come to Paris on 8th morning from London with my wife and two grown up kids for a holiday.. looking forward to have a great stay at your place and guidance for a memorable vacation 🌈👍\r\n\r\nLes messages des voyageurs et des hôtes ont été traduits automatiquement dans la langue utilisée pour votre compte. Vous pouvez modifier cette fonctionnalité dans vos paramètres.\r\n\r\nEnvoyez à Mohamed Nizar un message\n\r\n[Appartement 90m² rénové avec balcon - Paris]\r\n\r\nAppartement 90m² rénové avec balcon - Paris\r\n\r\nChambre\r\n\r\nArrivée\r\n\r\nlun. 8 juil.\r\n\r\n15:00\r\n\r\nDépart\r\n\r\njeu. 11 juil.\r\n\r\n12:00\r\n\r\nVoyageurs\r\n\r\n4 adultes\r\n\r\nPlus d\'informations concernant les voyageurs\r\n\r\nLes voyageurs vous préciseront désormais s\'ils seront accompagnés d\'enfants ou de bébés. Indiquez-leur si votre logement est adapté aux enfants en mettant à jour votre règlement intérieur.\r\n\r\nCode de confirmation\r\n\r\nHMCF4THWJT\r\n\r\nVoir le récapitulatif\r\nLe voyageur a payé\r\n\r\n120,00 € x 3 nuits\r\n\r\n360,00 €\r\n\r\nFrais de ménage\r\n\r\n65,00 €\r\n\r\nFrais de service voyageur\r\n\r\n69,70 €\r\n\r\nTaxes de séjour\r\n\r\n58,50 €\r\n\r\nTotal (EUR)\r\n553,20 €\r\nVersement de l\'hôte\r\n\r\nFrais de chambre pour 3 nuits\r\n\r\n360,00 €\r\n\r\nFrais de ménage\r\n\r\n65,00 €\r\n\r\nFrais de service hôte (3.0 % + TVA)\r\n\r\n-15,30 €\r\n\r\nVous gagnez\r\n409,70 €\r\n\r\nL\'argent que vous gagnez en tant qu\'hôte vous sera envoyé 24 heures après l\'arrivée de votre voyageur. Vous pouvez consulter vos paiements à venir dans votre historique des transactions.\r\n\r\nVotre voyageur a payé 58,50 € en taxes de séjour. Airbnb se charge de reverser ces taxes en votre nom.\r\n\r\nPour en savoir plus sur vos obligations sociales et fiscales, rendez vous sur nos pages "Hôtes responsables".\r\n\r\nConditions d\'annulation\r\n\r\nVos conditions d\'annulation pour les voyageurs sont Strictes.\r\n\r\nLes pénalités d\'annulation de cette réservation incluent l\'obtention d\'un commentaire public indiquant que vous avez annulé, le paiement des frais d\'annulation ainsi que le blocage des nuits annulées sur votre calendrier.\r\n\r\nVoir les pénalités d\'annulation\r\nPréparez-vous pour l\'arrivée de Mohamed Nizar\r\nConsulter les pratiques de sécurité liées au Covid-19\r\n\r\nNous avons créé un ensemble de pratiques de sécurité obligatoires liées au Covid-19 pour les hôtes Airbnb et les voyageurs. Ces pratiques incluent notamment la distanciation physique et le port d\'un masque.\r\n\r\nConsulter les pratiques\r\nAdoptez le processus de nettoyage renforcé en 5 étapes\r\n\r\nTous les hôtes doivent suivre le processus de nettoyage renforcé entre chaque séjour. Ce processus a été développé en partenariat avec des experts et vise à prévenir la propagation du Covid-19.\r\n\r\nConsulter le processus\r\nFournissez un plan d\'accès\r\n\r\nVérifiez que votre voyageur sait comment se rendre sur place.\r\n\r\nEnvoyer le message\r\n[AirCover pour les hôtes]\r\n\r\nUne protection complète, à chaque fois que vous accueillez des voyageurs.\r\n\r\nEn savoir plus\r\nAssistance utilisateurs\r\n\r\nContactez notre équipe d\'assistance 24h/24, 7j/7 partout dans le monde.\r\n\r\nVisiter le Centre d\'aideContacter Airbnb\r\n[Airbnb]\r\n\r\nAirbnb Ireland UC\r\n\r\n8 Hanover Quay\r\n\r\nDublin 2, Ireland\r\n\r\nConditions de paiement entre vous et :\r\n\r\nAirbnb Payments India Pvt. Ltd.\r\n\r\nLevel 9, Spaze i-Tech Park\r\n\r\nA1 Tower, Sector-49, Sohna Road\r\n\r\nGurugram INDIA 122018\r\n\r\nObtenir l\'application Airbnb\r\n\r\n[App Store]       [Google Play] \n'}

'''

message_eng ="""
 Reservation confirmed - Xiangqian Shao arrives 18 Jul\r\n\r\n\r\n[Airbnb]\r\nNew booking confirmed! Xiangqian arrives 18 Jul.\r\n\r\nSend a message to confirm check-in details or welcome Xiangqian.\r\n\r\n[https://a0.muscache.com/im/Portrait/Avatars/messaging/b3e03835-ade9-4eb7-a0bb-2466ab9a534d.jpg?im_policy=medq_w_text&im_t=X&im_w=240&im_f=airbnb-cereal-medium.ttf&im_c=ffffff]\n\r\n\r\nXiangqian\r\n\r\n[https://a0.muscache.com/im/pictures/0d520e2d-fe10-4292-a6b5-3616cbae5d94.jpg]Identity verified · 5 reviews\r\n\r\n[https://a0.muscache.com/im/pictures/d109f44f-35a7-4336-9420-750576bec06f.jpg]CN\r\n\r\nSend Xiangqian a Message\n\r\n[Appartement 90m² rénové avec balcon - Paris]\r\n\r\nAppartement 90m² rénové avec balcon - Paris\r\n\r\
nRoom\r\n\r\nCheck-in\r\n\r\nThu, 18 Jul\r\n\r\n15:00\r\n\r\nCheckout\r\n\r\nSun, 21 Jul\r\n\r\n12:00\r\n\r\nGuests\r\n\r\n2 adults, 1 child\r\n\r\nMore details about who’s coming\r\n\r\nGuests will now let you know if they’re bringing children and infants. Let them know upfront if your listing is suitable for children by updating your House Rules.
 \r\n\r\nConfirmation code\r\n\r\nHMAYJXEQCQ\r\n\r\nView itinerary\r\nGuest paid\r\n\r\n€ 100.00 x 3 nights\r\n\r\n€ 300.00\r\n\r\nCleaning fee\r\n\r\n€ 65.00\r\n\r\nGuest service fee\r\n\r\n€ 55.70\r\n\r\nOccupancy taxes\r\n\r\n€ 48.75\r\n\r\nTotal (EUR)\r\n€ 469.45\r\nHost payout\r\n\r\n3-night room fee\r\n\r\n€ 300.00\r\n\r\nCleaning fee\r\n\r\n€ 65.00\r\n\r\nHost service fee (3.0% + VAT)\r\n\r\n-€ 13.14\r\n\r\nYou earn\r\n€ 351.86\r\n\r\nThe money you earn hosting will be sent to you 24 hours after your guest arrives. You can check your upcoming payments in your Transaction History.\r\n\r\nYour guest paid € 48.75 in Occupancy Taxes. Airbnb remits these taxes on your behalf.\r\n\r\nTo learn more about your fiscal and social obligations, please visit our Responsible Hosting pages.\r\n\r\nCancellations\r\n\r\nYour cancellation policy for guests is Strict.\r\n\r\nThe penalties for canceling this reservation include getting a public review that shows you canceled, paying a cancellation fee, and having the canceled nights blocked on your calendar.\r\n\r\nRead cancellation penalties\r\nGet ready for Xiangqian’s arrival\r\nReview the COVID-19 safety practices\r\n\r\nWe’ve created a set of mandatory COVID-19 safety practices for both Airbnb hosts and guests. These include practising social distancing and wearing a mask.\r\n\r\nReview practices\r\nFollow the 5-step enhanced cleaning process\r\n\r\nAll hosts are required to follow the enhanced cleaning process between guest stays. They were developed in partnership with experts in an effort to curb the spread of COVID-19.\r\n\r\nReview process\r\nProvide directions\r\n\r\nCheck that your guest knows how to get to your place.\r\n\r\nSend message\r\n[AirCover for Hosts]\r\n\r\nTop-to-bottom protection, included every time you host.\r\n\r\nLearn more\r\nCustomer support\r\n\r\nContact our support team 24/7 from anywhere in the world.\r\n\r\nVisit help centreContact Airbnb\r\n[Airbnb]\r\n\r\nAirbnb Ireland UC\r\n\r\n8 Hanover Quay\r\n\r\nDublin 2, Ireland\r\n\r\nPayment Terms between you and:\r\n\r\nAirbnb Payments UK Ltd.\r\n\r\nSuite 1, 3rd Floor\r\n\r\n11-12 St. James’s Square\r\n\r\nLondon, SW1Y 4LB\r\n\r\nUnited Kingdom\r\n\r\nGet the Airbnb app\r\n\r\n[App Store]    [Google Play] \n'}
host_service_fee_match not found
Extracted Data: {'Arrival Date': 'Thu 18 Jul', 'Departure Date': 'Sun 21 Jul', 'Number of Adults': '2', 'Confirmation Code': 'HMAYJXEQCQ', 'Cost per Night': '100.00', 'Number of Nights': '3', 'Cleaning Fee': '65.00', 'Guest Service Fee': '55.70', 'Tourist Tax': '48.75', 'Total Paid by Guest': '469.45', 'Host Payout': 'N/A', 'Country Code': 'CN', 'Full_Name': 'Not Found', 'Subject': 'TR : Reservation confirmed - Xiangqian Shao arrives 18 Jul', 'Date': '2024-07-08'}
"""

pattern =re.compile(r"(?<=Le\svoyageur\sa\spayé\r\n\r\n)([\d\,\.]+)\s€\sx\s(\d{1,2})\snuits\r\n\r\n([\d\,\.]+)\s€")

match = re.search(pattern, message_fr)

#nAjustement du tarif par nuit !!!!

def fetch_specific_data(message_body, print_data=False, language='fr'):
    data = {}
### REMPLACER € par [€$£] pour prendre en compte les autres devises !!!
    country_code_regex = re.compile(r"(?<=bec06f\.jpg\])([A-Z]{2})?(\w+\d*,\s*\w+\d*)?(?=\r\n)") ## Attention si modification de jpg

    # # Define regular expressions for each piece of information in French
    if language == 'fr':
        arrival_date_regex = re.compile(r"(?:Arrivée\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.\s(\d{4}))?")
        # arrival_date_regex = re.compile(r"(?:Arrivée\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.\s)?(\d{4})?")
        departure_date_regex = re.compile(r"(?:Départ\r\n\r\n)(\w{3})\.\s(\d{1,2})\s(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)(?:\.\s(\d{4}))?")
        number_of_guests = re.compile(r"(?:Voyageurs)\r\n\r\n(\d{1,2})\s(?:adultes|adulte)(?:\,\s(\d{1,2}))?")
        confirmation_code_regex = re.compile(r"(?<=Code\sde\sconfirmation\r\n\r\n)(\w{10})")
        price_by_night_guest_regex = re.compile(r"(?<=Le\svoyageur\sa\spayé\r\n\r\n)([\d\,\.]+)\s€\sx\s(\d{1,2})\snuits\r\n\r\n([\d\,\.]+)\s€")
        cleaning_fee_regex = re.compile(r"Frais de ménage\s*(?:pour les séjours courte durée\s*)?\r?\n\s*([\d\,\.]+) €")
        guest_service_fee_regex = re.compile(r"(?<=Frais\sde\sservice\svoyageur\r\n\r\n)([\d\,\.]+)\s€")
        host_service_fee_regex = re.compile(r"(?<=hôte\s\((\d.\d\s\%)\s\+\sTVA\)\r\n\r\n)(-\d{1,5},\d{2})\s€")
        tourist_tax_regex = re.compile(r"Taxes de séjour\s*\r?\n\s*([\d\,\.]+) €")
        host_payout_regex = re.compile(r"(?<=gagnez\r\n)([\d\,\.]+)\s€") # ATTENTION ANCIENNE METHODE C'EST TOTAL !! 
        guest_payout_regex = re.compile(r"(?<=Total\s\(EUR\)\r\n)(\d{1,2})?(?:\u202f)?(\d{3,5},\d{2})(?=\s?\€\r\nVersement)") # ATTENTION GERER LE CAS AVEC DES MILIERS
    

    else:
        # Define regular expressions for each piece of information in English
        arrival_date_regex = re.compile(r"(?:Check-in\r\n\r\n)(\w{3}),\s(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\.\s(\d{4}))?")
        departure_date_regex = re.compile(r"(?:Checkout\r\n\r\n)(\w{3}),\s(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\.\s(\d{4}))?")
        number_of_guests = re.compile(r"(?:Guests)\r\n\r\n(\d{1,2})\s(?:adults|adult)(?:\,\s(\d{1,2}))?")
        confirmation_code_regex = re.compile(r"(?<=Confirmation\scode\r\n\r\n)(\w{10})")
        price_by_night_guest_regex = re.compile(r"(?<=Guest\spaid\r\n\r\n)€\s([\d\,\.]+)\sx\s(\d{1,2})\snights\r\n\r\n€\s([\d\,\.]+)")
        cleaning_fee_regex = re.compile(r"(?<=Cleaning\sfee\r\n\r\n)€\s([\d\,\.]+)")
        guest_service_fee_regex = re.compile(r"(?<=Guest\sservice\sfee\r\n\r\n)€\s([\d\,\.]+)")
        host_service_fee_regex = re.compile(r"(?<=Host\sservice\sfee\s\((\d.\d\%)\s\+\sVAT\)\r\n\r\n)(-(?:€)\s\d{1,5}\.\d{2})")
        tourist_tax_regex = re.compile(r"(?<=\s€\s)([\d\,\.]+)*\sin\sOccupancy\sTaxes\.")
        host_payout_regex = re.compile(r"(?<=You\searn\r\n)€\s([\d\,\.]+)") # ATTENTION ANCIENNE METHODE C'EST TOTAL !! 
        guest_payout_regex = re.compile(r"(?<=Total\s\(EUR\)\r\n)€\s(\d{1,2})?(?:\u202f)?(\d{3,5}\.\d{2})(?=\r\nHost\spayout)") # ATTENTION GERER LE CAS AVEC DES MILIERS
    

    # Search for the data in the message body
    arrival_date_match = arrival_date_regex.search(message_body)
    departure_date_match = departure_date_regex.search(message_body)
    number_of_guests_match = number_of_guests.search(message_body)
    confirmation_code_match = confirmation_code_regex.search(message_body)
    cleaning_fee_match = cleaning_fee_regex.search(message_body)
    guest_service_fee_match = guest_service_fee_regex.search(message_body)
    host_service_fee_match = host_service_fee_regex.search(message_body)
    tourist_tax_match = tourist_tax_regex.search(message_body)
    price_by_night_guest_match = price_by_night_guest_regex.search(message_body)
    host_payout_match = host_payout_regex.search(message_body)
    guest_payout_match = guest_payout_regex.search(message_body)
    country_code_match = country_code_regex.search(message_body)
    
    # Print not found regex matches if print_data is True
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
            "guest_payout_match" :guest_payout_match,
            "country_code_match": country_code_match
        }
        
        for field, match in not_found_fields.items():
            if not match:
                print(f"{field} not found")

    # Store the matched data in the dictionary
    data = {}

    # Grouping matches and else statements
    if len(arrival_date_match.groups()) == 4:
    # if arrival_date_match:
        data['Arrival_Day'] = arrival_date_match.group(2).strip()
        data['Arrival_DayOfWeek'] = arrival_date_match.group(1).strip()
        data['Arrival_Month'] = arrival_date_match.group(3).strip()
        if not arrival_date_match.group(4) == None : 
            data['Arrival_Year'] =arrival_date_match.group(4).strip()
        else : 
            data['Arrival_Year'] = "No year specified"
    else:
        data['Arrival_Day'] = 'N/A'
        data['Arrival_DayOfWeek'] = 'N/A' 
        data['Arrival_Month'] = 'N/A'
        data['Arrival_Year'] = 'N/A'

    if departure_date_match:
        data['Departure_Day'] = departure_date_match.group(2).strip()
        data['Departure_DayOfWeek'] = departure_date_match.group(1).strip()
        data['Departure_Month'] = departure_date_match.group(3).strip()
        if not arrival_date_match.group(4) == None : 
            data['Departure_Year'] =departure_date_match.group(4).strip()
        else : 
            data['Departure_Year'] = "No year specified"
    else:
        data['Departure_Day'] = 'N/A'
        data['Departure_DayOfWeek'] = 'N/A' 
        data['Departure_Month'] = 'N/A'
        data['Departure_Year'] = 'N/A'

    if number_of_guests_match:
        data['Number of Adults'] = number_of_guests_match.group(1).strip()
        if number_of_guests_match.group(2) != None:
            data['Number of child'] = number_of_guests_match.group(2).strip()
        else : 
            data['Number of child'] = "0"
    else:
        data['Number of Adults'] = 'N/A'
        data['Number of child'] = 'N/A'


    if confirmation_code_match:
        data['Confirmation Code'] = confirmation_code_match.group(1).strip()
    else:
        data['Confirmation Code'] = 'N/A'

    if cleaning_fee_match:
        if len(cleaning_fee_match.groups()) == 2 and cleaning_fee_match.group(1)!= cleaning_fee_match.group(2):
            data['Cleaning Fee'] = "ERROR : 2 different cleaning fees !"
        data['Cleaning Fee'] = cleaning_fee_match.group(1).replace(",", ".").strip()
    else:
        data['Cleaning Fee'] = 'N/A'

    if guest_service_fee_match:
        data['Guest Service Fee'] = guest_service_fee_match.group(1).replace(",", ".").strip()
    else:
        data['Guest Service Fee'] = 'N/A'

    if host_service_fee_match:
        data['Host Service Fee'] = host_service_fee_match.group(2).replace(",", ".").strip()
        data['Host Service Fee Percentage'] = host_service_fee_match.group(1)
    else:
        data['Host Service Fee'] = 'N/A'
        data['Host Service Fee Percentage'] = 'N/A'

    if tourist_tax_match:
        data['Tourist Tax'] = tourist_tax_match.group(1).replace(",", ".").strip()
    else:
        data['Tourist Tax'] = 'N/A'

    if price_by_night_guest_match:
        data['Total Price for all nights'] = price_by_night_guest_match.group(3).replace(",",".").strip()
        data['Number of nights'] = price_by_night_guest_match.group(2).strip()
        data['Price by night'] = price_by_night_guest_match.group(1).replace(",",".").strip()
    else:
        data['Total Paid by Guest'] = 'N/A'
        data['Number of nights'] = 'N/A'
        data['Price by night'] = 'N/A'
    if country_code_match.group(1) != None:
        data['Country Code'] = country_code_match.group(1)
    elif country_code_match.group(2) != None :
        data['Country Code'] = country_code_match.group(2)
    else:
        data['Country Code'] = 'N/A'
    
    if host_payout_match:
        data['Host Payout'] = host_payout_match.group(1).replace(",",".").strip()
    else:
        data['Host Payout'] = 'N/A'

    if guest_payout_match:
        if len(guest_payout_match.groups()) == 2 and guest_payout_match.group(1)!= None :
            data['Guest Payout'] = guest_payout_match.group(1) + guest_payout_match.group(2).replace(",",".") 
        else : 
            data['Guest Payout'] = guest_payout_match.group(2).replace(",",".")
    else:
        data['Guest Payout'] = 'N/A'


    return data



# if match:
#     print(match.group(1))  # Capture le jour de la semaine
#     print(match.group(2))
#     print(match.group(3))


# data = fetch_specific_data(message_fr, False, 'fr')
data = fetch_specific_data(message_eng, False, 'en')
print(data)
