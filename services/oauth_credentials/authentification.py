import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import datetime

def load_credentials(token_path):
    with open(token_path, 'r') as token_file:
        creds_data = json.load(token_file)
        creds = Credentials.from_authorized_user_info(creds_data)
    return creds

def refresh_access_token(credentials, token_path):
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        # Save the updated credentials back to the file
        with open(token_path, 'w') as token_file:
            token_file.write(credentials.to_json())
    return credentials

def print_token_ttl(credentials):
    if credentials.expiry:
        expiry_aware = credentials.expiry.replace(tzinfo=datetime.timezone.utc)
        now_aware = datetime.datetime.now(tz=datetime.timezone.utc)
        ttl = (expiry_aware - now_aware).total_seconds()
        print(f"Token TTL (seconds): {ttl}")
    else:
        print("No expiry information available for the token.")
