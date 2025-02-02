import os
import base64
from bs4 import BeautifulSoup
import dateutil.parser as parser
import csv
import re
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from services.oauth_credentials.authentification import load_credentials, refresh_access_token, print_token_ttl

# Initialize the credentials
token_path = os.getenv("TOKEN_PATH")
creds = load_credentials(token_path)

# Refresh the token if necessary
creds = refresh_access_token(creds, token_path)

# Print the TTL of the token
print_token_ttl(creds)

# Initialize the Gmail API service
GMAIL = build('gmail', 'v1', credentials=creds)

user_id = 'me'
label_id_one = 'INBOX'
label_id_two = 'UNREAD'
reservation_label_name = 'reserved'  # Replace with your actual reservation label ID

# Remaining code stays the same as before...

# Function to append content to CSV
def append_to_csv(filename, data):
    confirmation_code = data.get('Confirmation Code')
    if not confirmation_code:
        print("No confirmation code found in the data.")
        return

    if confirmation_code_exists(filename, confirmation_code):
        print(f"Confirmation code {confirmation_code} already exists. Data will not be appended.")
        return

    with open(filename, 'a', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['Date', 'Arrival Date', 'Departure Date', 'Confirmation Code', 'Cost per Night',
                      'Number of Nights', 'Total Nights Cost', 'Cleaning Fee', 'Guest Service Fee',
                      'Host Service Fee', 'Tourist Tax', 'Total Paid by Guest', 'Host Payout',
                      'Number of Adults', 'Number of Children', 'Country Code', 'Full_Name', 'Subject']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
        if os.stat(filename).st_size == 0:  # if file is empty, write the header
            writer.writeheader()
        writer.writerow(data)
        print(f"Data with confirmation code {confirmation_code} has been appended to {filename}.")

# Function to check if confirmation code exists in CSV
def confirmation_code_exists(filename, confirmation_code):
    if not os.path.exists(filename):
        return False  # File does not exist, so the code cannot exist
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get('Confirmation Code') == confirmation_code:
                return True
    return False

# Function to get label ID from label name
def get_label_id(service, user_id, label_name):
    try:
        response = service.users().labels().list(userId=user_id).execute()
        labels = response.get('labels', [])
        for label in labels:
            if label['name'].lower() == label_name.lower():
                return label['id']
        return None
    except HttpError as error:
        print(f"An error occurred while fetching the label ID: {error}")
        return None

# Function to tag emails with a specific label
def tag_email(service, user_id, msg_id, label_name):
    try:
        # Get the label ID for the reservation label name
        label_id = get_label_id(service, user_id, label_name)
        if not label_id:
            print(f"Label '{label_name}' not found.")
            return

        service.users().messages().modify(userId=user_id, id=msg_id, body={'addLabelIds': [label_id]}).execute()
    except HttpError as error:
        print(f"An error occurred while tagging the email: {error}")

# Function to mark an email as read
def mark_as_read(service, user_id, msg_id):
    try:
        service.users().messages().modify(userId=user_id, id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
        print(f"Marked email {msg_id} as read.")
    except HttpError as error:
        print(f"An error occurred while marking the email as read: {error}")

# Function to list objects of all unread mails and mark unnecessary mails as read
def list_unread_mails_objects(service, user_id, label_ids, reservation_label_name):
    try:
        unread_msgs = service.users().messages().list(userId=user_id, labelIds=label_ids).execute()
        mssg_list = unread_msgs.get('messages', [])
        print("Total unread messages in inbox: ", str(len(mssg_list)))

        final_list = []

        for mssg in mssg_list:
            temp_dict = {}
            m_id = mssg['id']  # get id of individual message
            message = service.users().messages().get(userId=user_id, id=m_id).execute()  # fetch the message using API
            payld = message['payload']  # get payload of the message
            headr = payld['headers']  # get header of the payload

            subject_contains_reservation = False

            for header in headr:  # Extract headers only once per message
                if header['name'] == 'Subject':
                    temp_dict['Subject'] = header['value']
                    if "Réservation confirmée" in header['value'] or "Reservation confirmed" in header['value']:
                        subject_contains_reservation = True
                elif header['name'] == 'Date':
                    date_parse = parser.parse(header['value'])
                    temp_dict['Date'] = str(date_parse.date())
                elif header['name'] == 'From':
                    temp_dict['Sender'] = header['value']

            temp_dict['Snippet'] = message.get('snippet', '')  # fetching message snippet

            final_list.append(temp_dict)  # This will create a dictionary item in the final list

            # Tag the message if the subject contains reservation confirmation
            if subject_contains_reservation:
                tag_email(service, user_id, m_id, reservation_label_name)
            else:
                # Mark the message as read if the subject does not contain reservation confirmation
                mark_as_read(service, user_id, m_id)

        print("Total objects retrieved: ", str(len(final_list)))
        return final_list

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

# Function to list all unread mail IDs
def list_unread_mails(service, user_id, label_ids):
    try:
        unread_msgs = service.users().messages().list(userId=user_id, labelIds=label_ids).execute()
        mssg_list = unread_msgs.get('messages', [])
        print("Total unread messages in inbox: ", str(len(mssg_list)))

        message_ids = [mssg['id'] for mssg in mssg_list]
        return message_ids

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

# Function to get the content of a selected mail by ID
def get_mail_content(service, user_id, msg_id, print_message=False):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
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
            print(temp_dict)
        return temp_dict

    except HttpError as error:
        print(f"An error occurred: {error}")
        return {}

# Function to detect the language of the email
def detect_language(message_body):
    if "Arrivée" in message_body or "Départ" in message_body:
        return 'fr'
    elif "Check-in" in message_body or "Checkout" in message_body:
        return 'en'
    return 'unknown'

# Function to fetch specific data from the message body in French or English
def fetch_specific_data(message_body, print_data=False):
    data = {}
    
    # Detect the language of the email
    language = detect_language(message_body)
    
    if language == 'fr':
        # Define regular expressions for each piece of information in French
        days_of_week = r"(lun\.|mar\.|mer\.|jeu\.|ven\.|sam\.|dim\.)"
        arrival_date_regex = re.compile(rf"Arrivée\s*\r?\n\r?\n\s*{days_of_week}\s*(\d+\s+\w+)")
        departure_date_regex = re.compile(rf"Départ\s*\r?\n\r?\n\s*{days_of_week}\s*(\d+\s+\w+)")
        number_of_adults_regex = re.compile(r"(\d+) adultes")
        number_of_children_regex = re.compile(r"(\d+) enfants")
        confirmation_code_regex = re.compile(r"Code de confirmation\s*\r?\n\r?\n\s*([\w\d]+)")
        total_paid_regex = re.compile(r"Total \(EUR\)\s*\r?\n\s*([\d\,\.]+) €")
        nights_cost_regex = re.compile(r"([\d\,\.]+) € x (\d+) nuit(?:s?)\s*\r?\n\s*([\d\,\.]+) €")
        cleaning_fee_regex = re.compile(r"Frais de ménage\s*(?:pour les séjours courte durée\s*)?\r?\n\s*([\d\,\.]+) €")
        guest_service_fee_regex = re.compile(r"Frais de service voyageur\s*\r?\n\s*([\d\,\.]+) €")
        host_service_fee_regex = re.compile(r"Frais de service\s*(?! voyageur)\r?\n\s*([\-\d\,\.]+) €")
        tourist_tax_regex = re.compile(r"Taxes de séjour\s*\r?\n\s*([\d\,\.]+) €")
        host_payout_regex = re.compile(r"Total \(EUR\)\s*\r?\n\s*([\d\,\.]+) €")
        country_code_regex = re.compile(r"\]([A-Z]{2})")
    elif language == 'en':
        # Define regular expressions for each piece of information in English
        days_of_week = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
        arrival_date_regex = re.compile(rf"Check-in\s*\r?\n\r?\n\s*{days_of_week},\s*(\d+\s+\w+)")
        departure_date_regex = re.compile(rf"Checkout\s*\r?\n\r?\n\s*{days_of_week},\s*(\d+\s+\w+)")
        number_of_adults_regex = re.compile(r"(\d+) adults")
        number_of_children_regex = re.compile(r"(\d+) children")
        confirmation_code_regex = re.compile(r"Confirmation code\s*\r?\n\r?\n\s*([\w\d]+)")
        total_paid_regex = re.compile(r"Total \(EUR\)\s*\r?\n\s*€ ([\d\,\.]+)")
        nights_cost_regex = re.compile(r"€ ([\d\,\.]+) x (\d+) nights")
        cleaning_fee_regex = re.compile(r"Cleaning fee\s*\r?\n\s*€ ([\d\,\.]+)")
        guest_service_fee_regex = re.compile(r"Guest service fee\s*\r?\n\s*€ ([\d\,\.]+)")
        host_service_fee_regex = re.compile(r"Service fee\s*\r?\n\s*-€ ([\d\,\.]+)")
        tourist_tax_regex = re.compile(r"Occupancy taxes\s*\r?\n\s*€ ([\d\,\.]+)")
        host_payout_regex = re.compile(r"Total \(EUR\)\s*\r?\n\s*€ ([\d\,\.]+)")
        country_code_regex = re.compile(r"\]([A-Z]{2})")
    else:
        print("Language not detected or unsupported.")
        return data

    # Search for the data in the message body
    arrival_date_match = arrival_date_regex.search(message_body)
    departure_date_match = departure_date_regex.search(message_body)
    number_of_adult_match = number_of_adults_regex.search(message_body)
    number_of_children_match = number_of_children_regex.search(message_body)
    confirmation_code_match = confirmation_code_regex.search(message_body)
    nights_cost_match = nights_cost_regex.search(message_body)
    cleaning_fee_match = cleaning_fee_regex.search(message_body)
    guest_service_fee_match = guest_service_fee_regex.search(message_body)
    host_service_fee_match = host_service_fee_regex.search(message_body)
    tourist_tax_match = tourist_tax_regex.search(message_body)
    total_paid_match = total_paid_regex.findall(message_body)
    host_payout_match = host_payout_regex.search(message_body)
    country_code_match = country_code_regex.search(message_body)
    
    # Print not found regex matches if print_data is True
    if print_data:
        if not arrival_date_match:
            print("arrival_date_match not found")
        if not departure_date_match:
            print("departure_date_match not found")
        if not number_of_adult_match:
            print("number_of_adult_match not found")
        if not confirmation_code_match:
            print("confirmation_code_match not found")
        if not nights_cost_match:
            print("nights_cost_match not found")
        if not cleaning_fee_match:
            print("cleaning_fee_match not found")
        if not guest_service_fee_match:
            print("guest_service_fee_match not found")
        if not host_service_fee_match:
            print("host_service_fee_match not found")
        if not tourist_tax_match:
            print("tourist_tax_match not found")
        if not total_paid_match:
            print("total_paid_match not found")
        if not host_payout_match:
            print("host_payout_match not found")
        if not country_code_match:
            print("country_code_match not found")
    
    # Store the matched data in the dictionary
    if arrival_date_match:
        data['Arrival Date'] = f"{arrival_date_match.group(1).strip()} {arrival_date_match.group(2).strip()}"
    if departure_date_match:
        data['Departure Date'] = f"{departure_date_match.group(1).strip()} {departure_date_match.group(2).strip()}"
    if number_of_adult_match:
        data['Number of Adults'] = number_of_adult_match.group(1).strip()
        #data['Number of Children'] = number_of_adult_match.group(2).strip() if number_of_adult_match.group(2).strip() else '0'
    if number_of_children_match: 
        data['Number of Children'] = number_of_children_match.group(1).strip()
    if confirmation_code_match:
        data['Confirmation Code'] = confirmation_code_match.group(1).strip()
    if nights_cost_match:
        data['Cost per Night'] = nights_cost_match.group(1).replace(",", ".").strip()
        data['Number of Nights'] = nights_cost_match.group(2).strip()
        if len(nights_cost_match.groups()) > 2:
            data['Total Nights Cost'] = "{:.2f}".format(float(nights_cost_match.group(3).replace(",", ".").strip()))
    if cleaning_fee_match:
        data['Cleaning Fee'] = cleaning_fee_match.group(1).replace(",", ".").strip()
    if guest_service_fee_match:
        data['Guest Service Fee'] = guest_service_fee_match.group(1).replace(",", ".").strip()
    if host_service_fee_match:
        data['Host Service Fee'] = host_service_fee_match.group(1).replace(",", ".").strip()
    if tourist_tax_match:
        data['Tourist Tax'] = tourist_tax_match.group(1).replace(",", ".").strip()
    if total_paid_match:
        data['Total Paid by Guest'] = total_paid_match[0].replace(",", ".").strip()
    if host_payout_match:
        data['Host Payout'] = total_paid_match[1].replace(",", ".").strip() if len(total_paid_match) > 1 else 'N/A'
    if country_code_match:
        data['Country Code'] = country_code_match.group(1).strip()
    
    return data

# Function to add additional email details to specific data
def add_additional_data(specific_data, message_details):
    subject = message_details.get('Subject', '')
    name_match = re.search(r"Réservation confirmée\s*:\s*(.*?)\s*arrive", subject) or re.search(r"Reservation confirmed\s*:\s*(.*?)\s*arrives", subject)
    if name_match:
        specific_data['Full_Name'] = name_match.group(1).strip()
    else:
        specific_data['Full_Name'] = 'Not Found'

    specific_data.update({
        'Subject': subject,
        'Date': message_details.get('Date', '')
    })

    return specific_data

#############################

if __name__ == "__main__":
    # List unread mail objects and mark unnecessary mails as read
    unread_mail_objects = list_unread_mails_objects(GMAIL, user_id, [label_id_one, label_id_two], reservation_label_name)
    print("Filtered Unread Mail Objects:", unread_mail_objects)

    # List unread mail IDs
    unread_mail_ids = list_unread_mails(GMAIL, user_id, [label_id_one, label_id_two])
    print("Unread Mail IDs:", unread_mail_ids)

    # Process each unread mail, extract specific data, and append to CSV
    csv_filename = 'reservations.csv'
    for msg_id in unread_mail_ids:
        message_details = get_mail_content(GMAIL, user_id, msg_id, print_message=False)
        specific_data = fetch_specific_data(message_details['Message_body'], print_data=False)
        if specific_data:
            specific_data = add_additional_data(specific_data, message_details)
            print(specific_data)
            append_to_csv(csv_filename, specific_data)
            #mark_as_read(GMAIL, user_id, msg_id)  # Mark email as read after processing
        else:
            print(f"No specific data extracted for message ID {msg_id}.")
    