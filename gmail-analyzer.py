from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from collections import Counter
import pickle
import os.path
import datetime

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Sets up and returns the Gmail service with proper authentication."""
    creds = None
    
    # Load existing credentials if available
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or create new credentials if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def analyze_senders(service, max_results=1000):
    """Analyzes email senders and returns statistics."""
    senders = Counter()
    domains = Counter()
    
    # Get messages
    results = service.users().messages().list(
        userId='me', 
        maxResults=max_results
    ).execute()
    
    messages = results.get('messages', [])
    total_messages = len(messages)
    
    print(f"Analyzing {total_messages} messages...")
    
    for i, message in enumerate(messages, 1):
        # Get message details
        msg = service.users().messages().get(
            userId='me', 
            id=message['id'], 
            format='metadata',
            metadataHeaders=['From']
        ).execute()
        
        # Extract sender
        headers = msg['payload']['headers']
        from_header = next((h for h in headers if h['name'] == 'From'), None)
        
        if from_header:
            sender = from_header['value']
            email = sender.split('<')[-1].strip('>')
            domain = email.split('@')[-1]
            
            senders[sender] += 1
            domains[domain] += 1
        
        # Show progress
        if i % 100 == 0:
            print(f"Processed {i}/{total_messages} messages...")

    return senders, domains

def print_results(senders, domains, top_n=20):
    """Prints analysis results in a formatted way."""
    print("\n=== Top Senders ===")
    print(f"{'Sender':<50} | {'Count':<10} | {'Percentage':<10}")
    print("-" * 72)
    
    total_emails = sum(senders.values())
    
    for sender, count in senders.most_common(top_n):
        percentage = (count / total_emails) * 100
        print(f"{sender[:50]:<50} | {count:<10} | {percentage:.1f}%")
    
    print("\n=== Top Domains ===")
    print(f"{'Domain':<30} | {'Count':<10} | {'Percentage':<10}")
    print("-" * 52)
    
    total_domains = sum(domains.values())
    
    for domain, count in domains.most_common(top_n):
        percentage = (count / total_domains) * 100
        print(f"{domain[:30]:<30} | {count:<10} | {percentage:.1f}%")

def main():
    try:
        service = get_gmail_service()
        senders, domains = analyze_senders(service)
        print_results(senders, domains)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main()
