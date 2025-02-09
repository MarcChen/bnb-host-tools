import base64
import os
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from dateutil import parser
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from services.google_integration.authentification import (
    load_credentials,
    print_token_ttl,
    refresh_access_token,
)


class GmailService:
    """
    A service class for interacting with Gmail API operations.
    """

    def __init__(self) -> None:
        """
        Initializes credentials, builds the Gmail API client, and sets default parameters.
        """
        assert os.getenv("TOKEN_PATH"), "TOKEN_PATH environment variable not set."
        token_path = os.getenv("TOKEN_PATH")
        self.creds = load_credentials(token_path)
        self.creds = refresh_access_token(self.creds, token_path)
        print_token_ttl(self.creds)
        self.gmail = build("gmail", "v1", credentials=self.creds)
        self.user_id = "me"
        self.label_id_one = "INBOX"
        self.label_id_two = "UNREAD"
        self.reservation_label_id = self.get_label_id("reserved")
        self.trash_label_id = self.get_label_id("poubelle")
        self.review_label_id = self.get_label_id("review")

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
                userId=self.user_id, id=msg_id, body={"removeLabelIds": ["UNREAD"]}
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
            unread_msgs = (
                self.gmail.users()
                .messages()
                .list(
                    userId=self.user_id, labelIds=[self.label_id_one, self.label_id_two]
                )
                .execute()
            )
            mssg_list = unread_msgs.get("messages", [])
            print("Total unread messages in inbox: ", str(len(mssg_list)))
            return [mssg["id"] for mssg in mssg_list]
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def _parse_headers(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
        temp_dict: Dict[str, str] = {}
        for header in headers:
            if header["name"] == "Subject":
                temp_dict["Subject"] = header["value"]
            elif header["name"] == "Date":
                date_parse = parser.parse(header["value"])
                temp_dict["Date"] = str(date_parse.date())
            elif header["name"] == "From":
                temp_dict["Sender"] = header["value"]
        return temp_dict

    def _parse_body(self, payload: dict) -> str:
        message_body = ""
        try:
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        part_data = part["body"].get("data", "")
                        clean_one = part_data.replace("-", "+").replace("_", "/")
                        decoded = base64.b64decode(clean_one)
                        message_body = BeautifulSoup(decoded, "lxml").body.text
                        break
        except Exception as e:
            print("Error processing message body:", e)
        return message_body

    def get_mail_content(
        self, msg_id: str, print_message: bool = False
    ) -> Dict[str, str]:
        """
        Fetches and returns the content of an email by its ID.

        Args:
            msg_id (str): The email ID.
            print_message (bool, optional): Whether to print the message content.

        Returns:
            Dict[str, str]: A dictionary containing email details.
        """
        try:
            message = (
                self.gmail.users()
                .messages()
                .get(userId=self.user_id, id=msg_id)
                .execute()
            )
            payload = message["payload"]
            temp_dict = self._parse_headers(payload["headers"])
            temp_dict["Snippet"] = message.get("snippet", "")
            temp_dict["Message_body"] = self._parse_body(payload)
            if print_message:
                print("Message content :", temp_dict)
            return temp_dict
        except HttpError as error:
            print(f"An error occurred while reading mail content: {error}")
            return {}

    def parse_reservation_header(
        self, content: Dict[str, str]
    ) -> Dict[str, Optional[str]]:
        """
        Parses the email content to check if it is a reservation and extracts the full name.

        Args:
            content (Dict[str, str]): Email details (must include 'Subject').

        Returns:
            Dict[str, Optional[str]]: {'type': str, 'full_name': Optional[str], 'rating': Optional[str]}
        """
        subject = content.get("Subject", "")
        # Check for reservation patterns
        pattern_res_en = r"Reservation confirmed(?:\s*[:\-]\s*|\s+for\s+)(?P<name>.*?)(?:\s+arrives\b.*)?$"
        pattern_res_fr = r"Réservation confirmée(?:\s*[:\-]\s*|\s+pour\s+)(?P<name>.*?)(?:\s+arrive\b.*)?$"
        match_res_en = re.search(pattern_res_en, subject, re.IGNORECASE)
        match_res_fr = re.search(pattern_res_fr, subject, re.IGNORECASE)
        if match_res_en:
            return {
                "type": "reservation",
                "full_name": match_res_en.group("name").strip(),
                "rating": None,
            }
        elif match_res_fr:
            return {
                "type": "reservation",
                "full_name": match_res_fr.group("name").strip(),
                "rating": None,
            }
        pattern_review = r"^TR\s*:\s*(?P<name>\S+).*?(?P<rating>\d+)(?:-star|\sétoiles)"
        match_review = re.search(pattern_review, subject, re.IGNORECASE)
        if match_review:
            return {
                "type": "review",
                "full_name": match_review.group("name").strip(),
                "rating": match_review.group("rating"),
            }
        return {"type": "none", "full_name": None, "rating": None}

    def process_unread_emails(self) -> None:
        """
        Processes unread mails:
        - Tags mails as 'reserved' if reservation confirmed,
        - Otherwise tags as 'poubelle' and marks as read.
        """
        try:
            unread_ids = self.list_unread_mails()
            for msg_id in unread_ids:
                content = self.get_mail_content(msg_id)
                reservation_info = self.parse_reservation_header(content)
                if reservation_info["type"] == "reservation":
                    if self.reservation_label_id:
                        self.gmail.users().messages().modify(
                            userId=self.user_id,
                            id=msg_id,
                            body={"addLabelIds": [self.reservation_label_id]},
                        ).execute()
                        print(
                            f"Tagged email {msg_id} as reserved for {reservation_info.get('full_name').split(' ')[0]}."
                        )
                # Check for review email with a regex matching 5-star patterns in both English and French
                elif reservation_info["type"] == "review":
                    self.gmail.users().messages().modify(
                        userId=self.user_id,
                        id=msg_id,
                        body={"addLabelIds": [self.review_label_id]},
                    ).execute()
                    print(f"Tagged email {msg_id} as review email.")
                else:
                    if self.trash_label_id:
                        self.gmail.users().messages().modify(
                            userId=self.user_id,
                            id=msg_id,
                            body={"addLabelIds": [self.trash_label_id]},
                        ).execute()
                    self.mark_as_read(msg_id)
                    print(f"Tagged email {msg_id} as poubelle and marked as read.")
        except Exception as error:
            print(f"An error occurred while processing unread emails: {error}")

    def get_unread_emails_content_by_label(self, label: str) -> List[Dict[str, str]]:
        """
        Retrieves the content of all unread emails tagged with the specified label.

        Args:
            label (str): The label to filter the emails.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing email details.
        """
        try:
            label_id = self.get_label_id(label)
            response = (
                self.gmail.users()
                .messages()
                .list(userId=self.user_id, labelIds=[label_id, "UNREAD"])
                .execute()
            )
            messages = response.get("messages", [])
            contents: List[Dict[str, str]] = []
            for msg in messages:
                contents.append(self.get_mail_content(msg["id"]))
            return contents
        except Exception as error:
            print(
                f"An error occurred while retrieving emails content for label {label_id}: {error}"
            )
            return []

    def mark_mails_as_read_for_label(self, label: str) -> None:
        """
        Marks all unread emails associated with a specific label as read.

        This method retrieves the unique identifier for the specified label and then fetches all unread
        messages that are tagged with that label. For each message found, it updates the message status
        to mark it as read. If the label is not found, a message is printed and the method exits gracefully.

        Note:
            - The method assumes that emails must have both the specified label and the "UNREAD" status
              to be processed.
            - Any exceptions that occur during the API calls will be caught and logged.

        Args:
            label (str): The name of the label for which the unread emails should be marked as read.

        Raises:
            Exception: Logs any unexpected errors encountered during the API request execution.

        Example:
            mark_mails_as_read_for_label("Important")
        """
        try:
            label_id = self.get_label_id(label)
            if not label_id:
                print(f"Label '{label}' not found.")
                return
            response = (
                self.gmail.users()
                .messages()
                .list(userId=self.user_id, labelIds=[label_id, "UNREAD"])
                .execute()
            )
            messages = response.get("messages", [])
            for msg in messages:
                self.mark_as_read(msg["id"])
            print(f"Marked {len(messages)} mails with label '{label}' as read.")
        except Exception as error:
            print(
                f"An error occurred while marking mails with label '{label}' as read: {error}"
            )
