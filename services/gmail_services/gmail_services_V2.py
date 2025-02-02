import csv
import os
from typing import Optional
from googleapiclient.discovery import Resource
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional
from typing import List, Dict
from dateutil import parser
import base64
from bs4 import BeautifulSoup
import re
from services.oauth_credentials.authentification import load_credentials, refresh_access_token, print_token_ttl

# Initialize the credentials
token_path = os.getenv("TOKEN_PATH")
creds = load_credentials(token_path)

# Refresh the token if necessary
creds = refresh_access_token(creds, token_path)

# Print the TTL of the token
print_token_ttl(creds)

# Global variables
GMAIL = build('gmail', 'v1', credentials=creds)
user_id = 'me'
label_id_one = 'INBOX'
label_id_two = 'UNREAD'
reservation_label_name = 'reserved'
trash_label_name = 'poubelle'  # New label for non-matching emails


def append_booking_data_to_csv(filename: str, data: Dict) -> None:
    """
    Appends booking data to a CSV file if the confirmation code is not already present.

    Args:
        filename (str): The path to the CSV file.
        data (Dict[str, str]): A dictionary containing booking details, including a confirmation code.

    Returns:
        None: The function prints a message and exits if the data is not appended.
    """
    # Extract confirmation code from the data dictionary.
    confirmation_code = data.get("Confirmation Code")

    # Check if confirmation code exists in the provided data.
    if not confirmation_code:
        print("No confirmation code found in the data.")
        return

    # Check if the confirmation code is already present in the CSV.
    if confirmation_code_exists_in_csv(filename, confirmation_code):
        print(
            f"Confirmation code {confirmation_code} already exists. Data will not be appended."
        )
        return

    # Append data to CSV if confirmation code is new.
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

        # Write header if the CSV file is empty.
        if os.stat(filename).st_size == 0:
            writer.writeheader()

        # Write the data row to the CSV.
        writer.writerow(data)
        print(
            f"Data with confirmation code {confirmation_code} has been appended to {filename}."
        )

def confirmation_code_exists_in_csv(filename: str, confirmation_code: str) -> bool:
    """
    Checks if a given confirmation code already exists in a CSV file.
    
    Args:
        filename (str): The path to the CSV file.
        confirmation_code (str): The confirmation code to search for.
        
    Returns:
        bool: True if the confirmation code is found, False otherwise.
    """
    # If the file does not exist, return False since no code can exist in it.
    if not os.path.exists(filename):
        return False

    # Open the file and search for the confirmation code.
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Iterate through each row to check if the confirmation code exists.
        return any(row.get('Confirmation Code') == confirmation_code for row in reader)

def tag_email(msg_id, label_name):
    """
    Tags an email with the specified label.
    
    Args:
        msg_id (str): The ID of the email to tag.
        label_name (str): The name of the label to apply.
        
    Returns:
        None
    """

    try:
        label_id = get_label_id(label_name)
        if not label_id:
            print(f"[yellow]Label '{label_name}' not found.[/yellow]")
            return

        GMAIL.users().messages().modify(userId=user_id, id=msg_id, body={"addLabelIds": [label_id]}).execute()
    except HttpError as error:
        print(f"[red]An error occurred while tagging the email: {error}[/red]")


def get_label_id(label_name):
    """
    Retrieves the label ID for a given label name.
    
    Args:
        label_name (str): The name of the label to search for.
        
    Returns:
        str or None: The ID of the label if found, otherwise None.
    """
    try:
        response = GMAIL.users().labels().list(userId=user_id).execute()
        labels = response.get("labels", [])
        for label in labels:
            if label["name"].lower() == label_name.lower():
                return label["id"]
        return None
    except HttpError as error:
        print(f"[red]An error occurred while fetching the label ID: {error}[/red]")
        return None

def mark_as_read(msg_id: str) -> None:
    """
    Marks an email as read by removing the 'UNREAD' label.
    
    Args:
        msg_id (str): The ID of the email message to mark as read.
        
    Returns:
        None
    """
    try:
        GMAIL.users().messages().modify(
            userId=user_id, id=msg_id, body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print(f"Marked email {msg_id} as read.")

    except HttpError as error:
        print(f"An error occurred while marking the email as read: {error}")

def pre_process_unread_mails() -> List[Dict[str, str]]:
    """
    Lists unread emails from the specified labels, extracts email details,
    and tags emails based on the content of the subject.
    
    Returns:
        list: A list of dictionaries containing email details such as Subject, Date, and Snippet.
    """
    try:
        unread_msgs = GMAIL.users().messages().list(userId=user_id, labelIds=[label_id_one, label_id_two]).execute()
        mssg_list = unread_msgs.get('messages', [])
        print("Total unread messages in inbox: ", str(len(mssg_list)))

        final_list = []

        for mssg in mssg_list:
            temp_dict = {}
            m_id = mssg['id']
            message = GMAIL.users().messages().get(userId=user_id, id=m_id).execute()
            payld = message['payload']
            headr = payld['headers']

            subject_contains_reservation = False

            for header in headr:
                if header['name'] == 'Subject':
                    temp_dict['Subject'] = header['value']
                    if "Réservation confirmée" in header['value'] or "Reservation confirmed" in header['value']:
                        subject_contains_reservation = True
                elif header['name'] == 'Date':
                    date_parse = parser.parse(header['value'])
                    temp_dict['Date'] = str(date_parse.date())
                elif header['name'] == 'From':
                    temp_dict['Sender'] = header['value']

            temp_dict['Snippet'] = message.get('snippet', '')
            final_list.append(temp_dict)

            if subject_contains_reservation:
                tag_email(m_id, reservation_label_name)
            else:
                tag_email(m_id, trash_label_name)
                mark_as_read(m_id)

        print("Total objects retrieved: ", str(len(final_list)))
        return final_list

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []



def get_mail_content(msg_id: str, print_message: bool = False) -> Dict[str, str]:
    """
    Fetches and returns the content of an email by its ID.
    
    Args:
        service (Resource): The Gmail API service instance.
        msg_id (str): The ID of the email to fetch.
        print_message (bool): Whether to print the fetched content.
        
    Returns:
        Dict[str, str]: A dictionary containing email details.
    """
    try:
        message = GMAIL.users().messages().get(userId=user_id, id=msg_id).execute()
        payld = message['payload']  # get payload of the message
        headr = payld['headers']  # get header of the payload

        temp_dict = {}
        for header in headr:  # Extract headers only once per message
            if header['name'] == 'Subject':
                temp_dict['Subject'] = header['value']
            elif header['name'] == 'Date':
                date_parse = parser.parse(header['value'])
                temp_dict['Date'] = str(date_parse.date())
            elif header['name'] == 'From':
                temp_dict['Sender'] = header['value']

        temp_dict['Snippet'] = message.get('snippet', '')  # fetching message snippet

        try:
            # Fetching message body
            if 'parts' in payld:
                for part in payld['parts']:
                    if part['mimeType'] == 'text/plain':
                        part_data = part['body'].get('data', '')
                        clean_one = part_data.replace("-", "+").replace("_", "/")
                        clean_two = base64.b64decode(clean_one)
                        temp_dict['Message_body'] = BeautifulSoup(clean_two, "lxml").body.text
                        break  # Stop after finding the first text/plain part
        except Exception as e:
            print("Error processing message body:", e)
            temp_dict['Message_body'] = ''

        if print_message:
            print("Message content :", temp_dict)
        return temp_dict

    except HttpError as error:
        print(f"An error occurred while reading mail content: {error}")
        return {}

def detect_language(message_body: str) -> str:
    """
    Detects the language of the email based on specific keywords.
    
    Args:
        message_body (str): The body of the email.
        
    Returns:
        str: The detected language ('fr', 'en', or 'unknown').
    """
    if "Arrivée" in message_body or "Départ" in message_body or "Confirmée" in message_body:
        return 'fr'
    elif "Check-in" in message_body or "Checkout" in message_body:
        return 'en'
    return 'unknown'

def fetch_data_from_mail_header(specific_data: Dict[str, Optional[str]], message_details: Dict[str, str]) -> Dict[str, Optional[str]]:
    """
    Adds additional email details like subject and sender information to the extracted data.
    
    Args:
        specific_data (Dict[str, Optional[str]]): Extracted reservation data.
        message_details (Dict[str, str]): Details fetched from the email headers.
        
    Returns:
        Dict[str, Optional[str]]: Updated dictionary with additional data.
    """
    subject = message_details.get('Subject', '')
    name_match = re.search(r"Réservation confirmée\s*:\s*(.*?)\s*arrive", subject) or \
                 re.search(r"Reservation confirmed\s*:\s*(.*?)\s*arrives", subject)
    specific_data['Full_Name'] = name_match.group(1).strip() if name_match else 'Not Found'

    specific_data.update({
        'Subject': subject,
        'Date': message_details.get('Date', '')
    })
    return specific_data


# Function to list all unread mail IDs
def list_unread_mails() -> List[str]:
    """
    Lists unread mail IDs from specified labels.
    
    Returns:
        list: A list of unread email message IDs.
    """
    try:
        unread_msgs = GMAIL.users().messages().list(userId=user_id, labelIds=[label_id_one, label_id_two]).execute()
        mssg_list = unread_msgs.get('messages', [])
        print("Total unread messages in inbox: ", str(len(mssg_list)))

        return [mssg['id'] for mssg in mssg_list]

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def fetch_specific_data_from_content(message_body, print_data=False):
    data = {}
    
    # Detect the language of the email
    language = detect_language(message_body)
    
    country_code_regex = re.compile(r"(?<=bec06f\.jpg\])([A-Z]{2})?(\w+\d*,\s*\w+\d*)?(?=\r\n)") ## Attention si modification de jpg
    if language == 'fr':
        # Define regular expressions for each piece of information in French
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
    elif language == 'en':
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
    else:
        print("Language not detected or unsupported.")
        return data

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

if __name__ == "__main__":
    # Fetch unread mail objects and mark unnecessary emails as read
    unread_mail_objects = pre_process_unread_mails(
    )

    # print("Filtered Unread Mail Objects:", unread_mail_objects)

    # List unread mail IDs
    unread_mail_ids = list_unread_mails()
    # print("Unread Mail IDs:", unread_mail_ids)

    # Process each unread email, extract specific data, and append to CSV
    csv_filename = 'reservations.csv'
    for msg_id in unread_mail_ids:
        message_details = get_mail_content(msg_id, print_message=True)
        specific_data = fetch_specific_data_from_content(message_details.get('Message_body', ''), print_data=True)

        if specific_data:
            specific_data = fetch_data_from_mail_header(specific_data, message_details)
            print("Extracted Data:", specific_data)
            append_booking_data_to_csv(csv_filename, specific_data)
            mark_as_read(msg_id)
        else:
            print(f"No specific data extracted for message ID {msg_id}.")
