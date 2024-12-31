from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from typing import Optional, Literal
from ..database import get_db
from ..services.gmail import GmailService
from ..services.analytics import AnalyticsService
from ..schemas import Analytics
from ..models import EmailMessage

router = APIRouter()

@router.post("/sync")
async def sync_emails(db: Session = Depends(get_db)):
    gmail_service = GmailService()
    service = gmail_service.get_service()
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
                if db.query(EmailMessage).filter_by(id=message['id']).first():
                    continue
                
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                email_msg = gmail_service.parse_message(msg)
                if email_msg:
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

@router.get("/analytics", response_model=Analytics)
async def get_analytics(db: Session = Depends(get_db)):
    analytics_service = AnalyticsService(db)
    return analytics_service.get_analytics()

@router.get("/emails")
async def get_emails(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    after_date: Optional[str] = None,
    sort_by: Literal["date", "sender_frequency", "domain_frequency"] = "sender_frequency"
):
    # Start with base query
    base_query = db.query(EmailMessage)
    
    # Apply filters
    if search:
        search_filter = f"%{search}%"
        base_query = base_query.filter(
            (EmailMessage.sender_email.ilike(search_filter)) |
            (EmailMessage.sender_name.ilike(search_filter)) |
            (EmailMessage.subject.ilike(search_filter))
        )
    
    if after_date:
        try:
            date_filter = datetime.fromisoformat(after_date)
            base_query = base_query.filter(EmailMessage.received_date >= date_filter)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")

    # Apply sorting
    if sort_by == "sender_frequency":
        sender_counts = (
            db.query(
                EmailMessage.sender_email,
                func.count().label('email_count')
            )
            .group_by(EmailMessage.sender_email)
            .subquery()
        )

        query = (
            base_query
            .outerjoin(
                sender_counts,
                EmailMessage.sender_email == sender_counts.c.sender_email
            )
            .order_by(
                desc(sender_counts.c.email_count),
                desc(EmailMessage.received_date)
            )
        )
    elif sort_by == "domain_frequency":
        domain_counts = (
            db.query(
                EmailMessage.sender_domain,
                func.count().label('domain_count')
            )
            .group_by(EmailMessage.sender_domain)
            .subquery()
        )

        query = (
            base_query
            .outerjoin(
                domain_counts,
                EmailMessage.sender_domain == domain_counts.c.sender_domain
            )
            .order_by(
                desc(domain_counts.c.domain_count),
                desc(EmailMessage.received_date)
            )
        )
    else:
        # Default date sorting
        query = base_query.order_by(desc(EmailMessage.received_date))
    
    # Get total count and paginate
    total = base_query.count()
    emails = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "emails": emails
    }
