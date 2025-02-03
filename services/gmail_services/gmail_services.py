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
from services.parser.parser import fetch_specific_data_from_content, append_booking_data_to_csv

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
