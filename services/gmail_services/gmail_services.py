import os
from typing import Optional, List, Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dateutil import parser
import base64
from bs4 import BeautifulSoup
import re
from oauth_credentials.authentification import (
    load_credentials,
    refresh_access_token,
    print_token_ttl,
)

class GmailService:
    """
    A service class for interacting with Gmail API operations.
    """

    def __init__(self) -> None:
        """
        Initializes credentials, builds the Gmail API client, and sets default parameters.
        """
        token_path = os.getenv("TOKEN_PATH")
        self.creds = load_credentials(token_path)
        self.creds = refresh_access_token(self.creds, token_path)
        print_token_ttl(self.creds)
        self.gmail = build('gmail', 'v1', credentials=self.creds)
        self.user_id = 'me'
        self.label_id_one = 'INBOX'
        self.label_id_two = 'UNREAD'
        self.reservation_label_name = 'reserved'
        self.trash_label_name = 'poubelle'

    def tag_email(self, msg_id: str, label_name: str) -> None:
        """
        Tags an email with the specified label.

        Args:
            msg_id (str): The email ID.
            label_name (str): The label to apply.
        """
        try:
            label_id = self.get_label_id(label_name)
            if not label_id:
                print(f"[yellow]Label '{label_name}' not found.[/yellow]")
                return
            self.gmail.users().messages().modify(
                userId=self.user_id, id=msg_id, body={"addLabelIds": [label_id]}
            ).execute()
        except HttpError as error:
            print(f"[red]An error occurred while tagging the email: {error}[/red]")

    def get_label_id(self, label_name: str) -> Optional[str]:
        """
        Retrieves the label ID for a given label name.

        Args:
            label_name (str): The name of the label.

        Returns:
            Optional[str]: The label ID if found; otherwise, None.
        """
        try:
            response = self.gmail.users().labels().list(userId=self.user_id).execute()
            labels = response.get("labels", [])
            for label in labels:
                if label["name"].lower() == label_name.lower():
                    return label["id"]
            return None
        except HttpError as error:
            print(f"[red]An error occurred while fetching the label ID: {error}[/red]")
            return None

    def mark_as_read(self, msg_id: str) -> None:
        """
        Marks an email as read by removing the 'UNREAD' label.

        Args:
            msg_id (str): The email message ID.
        """
        try:
            self.gmail.users().messages().modify(
                userId=self.user_id, id=msg_id, body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except HttpError as error:
            print(f"An error occurred while marking the email as read: {error}")

    def list_unread_mails(self) -> List[str]:
        """
        Lists unread mail IDs from specified labels.

        Returns:
            List[str]: List of unread email IDs.
        """
        try:
            unread_msgs = self.gmail.users().messages().list(
                userId=self.user_id, labelIds=[self.label_id_one, self.label_id_two]
            ).execute()
            mssg_list = unread_msgs.get('messages', [])
            print("Total unread messages in inbox: ", str(len(mssg_list)))
            return [mssg['id'] for mssg in mssg_list]
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_mail_content(self, msg_id: str, print_message: bool = False) -> Dict[str, str]:
        """
        Fetches and returns the content of an email by its ID.

        Args:
            msg_id (str): The email ID.
            print_message (bool, optional): Whether to print the message content.

        Returns:
            Dict[str, str]: A dictionary containing email details.
        """
        try:
            message = self.gmail.users().messages().get(userId=self.user_id, id=msg_id).execute()
            payld = message['payload']
            headr = payld['headers']
            temp_dict: Dict[str, str] = {}
            for header in headr:
                if header['name'] == 'Subject':
                    temp_dict['Subject'] = header['value']
                elif header['name'] == 'Date':
                    date_parse = parser.parse(header['value'])
                    temp_dict['Date'] = str(date_parse.date())
                elif header['name'] == 'From':
                    temp_dict['Sender'] = header['value']
            temp_dict['Snippet'] = message.get('snippet', '')
            try:
                if 'parts' in payld:
                    for part in payld['parts']:
                        if part['mimeType'] == 'text/plain':
                            part_data = part['body'].get('data', '')
                            clean_one = part_data.replace("-", "+").replace("_", "/")
                            decoded = base64.b64decode(clean_one)
                            temp_dict['Message_body'] = BeautifulSoup(decoded, "lxml").body.text
                            break
            except Exception as e:
                print("Error processing message body:", e)
                temp_dict['Message_body'] = ''
            if print_message:
                print("Message content :", temp_dict)
            return temp_dict
        except HttpError as error:
            print(f"An error occurred while reading mail content: {error}")
            return {}

    def fetch_data_from_mail_header(self, specific_data: Dict[str, Optional[str]], message_details: Dict[str, str]) -> Dict[str, Optional[str]]:
        """
        Enhances extracted reservation data with email header details.

        Args:
            specific_data (Dict[str, Optional[str]]): Extracted reservation data.
            message_details (Dict[str, str]): Email header details.

        Returns:
            Dict[str, Optional[str]]: Updated data with additional header info.
        """
        subject: str = message_details.get('Subject', '')
        name_match = (re.search(r"Réservation confirmée\s*:\s*(.*?)\s*arrive", subject) or 
                      re.search(r"Reservation confirmed\s*:\s*(.*?)\s*arrives", subject))
        specific_data['Full_Name'] = name_match.group(1).strip() if name_match else 'Not Found'
        specific_data.update({
            'Subject': subject,
            'Date': message_details.get('Date', '')
        })
        return specific_data

    def parse_reservation_header(self, content: Dict[str, str]) -> Dict[str, Optional[str]]:
        """
        Parses the email content to check if it is a reservation and extracts the full name.

        Args:
            content (Dict[str, str]): Email details (must include 'Subject').

        Returns:
            Dict[str, Optional[str]]: {'is_reservation': bool, 'full_name': Optional[str]}
        """
        subject = content.get("Subject", "")
        pattern_en = r"Reservation confirmed\s*[-:]\s*(?P<name>.*?)\s+arrives"
        pattern_fr = r"Réservation confirmée\s*[:\-]\s*(?P<name>.*?)\s+arrive"
        match_en = re.search(pattern_en, subject, re.IGNORECASE)
        match_fr = re.search(pattern_fr, subject, re.IGNORECASE)
        if match_en:
            return {"is_reservation": True, "full_name": match_en.group("name").strip()}
        elif match_fr:
            return {"is_reservation": True, "full_name": match_fr.group("name").strip()}
        return {"is_reservation": False, "full_name": None}


if __name__ == "__main__":
    assert os.getenv("TOKEN_PATH"), "TOKEN_PATH environment variable not set."
    service = GmailService()
    unread_ids = service.list_unread_mails()
    print("Unread mail IDs:", unread_ids)
    # Loop through all unread mails and process them with regex filtering
    for msg_id in unread_ids:
        content = service.get_mail_content(msg_id)
        reservation_info = service.parse_reservation_header(content)
        if reservation_info["is_reservation"]:
            # Tag reserved mails but leave unread
            service.tag_email(msg_id, service.reservation_label_name)
            print(f"Tagged email {msg_id} as reserved for {reservation_info['full_name']}.")
        else:
            # Tag non-reserved mails and mark as read
            service.tag_email(msg_id, service.trash_label_name)
            service.mark_as_read(msg_id)
            print(f"Tagged email {msg_id} as poubelle and marked as read.")
