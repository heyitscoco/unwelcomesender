from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
from datetime import datetime
import email.utils
from ..config import settings
from ..models import EmailMessage

class GmailService:
    def __init__(self):
        self.scopes = settings.GMAIL_SCOPES
        self.credentials_file = settings.CREDENTIALS_FILE
        self.token_file = settings.TOKEN_FILE

    def get_service(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        return build('gmail', 'v1', credentials=creds)

    def parse_message(self, msg_data):
        headers = msg_data['payload']['headers']
        from_header = next((h for h in headers if h['name'] == 'From'), None)
        subject_header = next((h for h in headers if h['name'] == 'Subject'), None)
        date_header = next((h for h in headers if h['name'] == 'Date'), None)

        if from_header:
            sender = from_header['value']
            sender_name = sender.split('<')[0].strip().strip('"')
            sender_email = sender.split('<')[-1].strip('>')
            sender_domain = sender_email.split('@')[-1]

            # Parse the date using email.utils.parsedate_to_datetime
            received_date = None
            if date_header:
                try:
                    # This handles various email date formats including UTC
                    received_date = email.utils.parsedate_to_datetime(date_header['value'])
                except Exception as e:
                    print(f"Error parsing date: {date_header['value']} - {str(e)}")
                    received_date = None

            return EmailMessage(
                id=msg_data['id'],
                sender_name=sender_name,
                sender_email=sender_email,
                sender_domain=sender_domain,
                subject=subject_header['value'] if subject_header else None,
                received_date=received_date
            )
        return None
