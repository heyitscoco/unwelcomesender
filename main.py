# models.py
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class EmailMessage(Base):
    __tablename__ = 'email_messages'
    
    id = Column(String, primary_key=True)  # Gmail message ID
    sender_name = Column(String)
    sender_email = Column(String)
    sender_domain = Column(String)
    received_date = Column(DateTime)
    subject = Column(String)
    
# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List
import pickle
import os
from datetime import datetime

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./gmail_analyzer.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_gmail_service():
    """Sets up and returns the Gmail service with proper authentication."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

@app.post("/api/sync")
async def sync_emails(db: Session = Depends(get_db)):
    """Syncs emails from Gmail to local database."""
    service = get_gmail_service()
    page_token = None
    total_processed = 0
    
    while True:
        try:
            results = service.users().messages().list(
                userId='me',
                pageToken=page_token,
                maxResults=500
            ).execute()
            
            messages = results.get('messages', [])
            
            for message in messages:
                # Skip if message already exists in DB
                if db.query(EmailMessage).filter_by(id=message['id']).first():
                    continue
                
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg['payload']['headers']
                from_header = next((h for h in headers if h['name'] == 'From'), None)
                subject_header = next((h for h in headers if h['name'] == 'Subject'), None)
                date_header = next((h for h in headers if h['name'] == 'Date'), None)
                
                if from_header:
                    sender = from_header['value']
                    sender_name = sender.split('<')[0].strip().strip('"')
                    sender_email = sender.split('<')[-1].strip('>')
                    sender_domain = sender_email.split('@')[-1]
                    
                    email_msg = EmailMessage(
                        id=message['id'],
                        sender_name=sender_name,
                        sender_email=sender_email,
                        sender_domain=sender_domain,
                        subject=subject_header['value'] if subject_header else None,
                        received_date=datetime.strptime(date_header['value'], "%a, %d %b %Y %H:%M:%S %z")
                        if date_header else None
                    )
                    
                    db.add(email_msg)
                    total_processed += 1
                    
                    if total_processed % 100 == 0:
                        db.commit()
            
            db.commit()
            page_token = results.get('nextPageToken')
            if not page_token:
                break
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return {"message": f"Processed {total_processed} new messages"}

@app.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """Returns email analytics."""
    # Top senders
    top_senders = db.query(
        EmailMessage.sender_email,
        EmailMessage.sender_name,
        func.count(EmailMessage.id).label('count')
    ).group_by(
        EmailMessage.sender_email
    ).order_by(
        func.count(EmailMessage.id).desc()
    ).limit(20).all()
    
    # Top domains
    top_domains = db.query(
        EmailMessage.sender_domain,
        func.count(EmailMessage.id).label('count')
    ).group_by(
        EmailMessage.sender_domain
    ).order_by(
        func.count(EmailMessage.id).desc()
    ).limit(20).all()
    
    return {
        "top_senders": [{"email": s[0], "name": s[1], "count": s[2]} for s in top_senders],
        "top_domains": [{"domain": d[0], "count": d[1]} for d in top_domains]
    }
