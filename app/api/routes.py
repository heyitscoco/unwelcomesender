from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, distinct
from typing import Optional, Literal
from datetime import datetime
from ..database import get_db
from ..services.gmail import GmailService
from ..services.analytics import AnalyticsService
from ..models import EmailMessage
from ..schemas import Analytics

router = APIRouter()

@router.post("/sync")
async def sync_emails(db: Session = Depends(get_db)):
    """Syncs emails from Gmail to local database."""
    gmail_service = GmailService()
    service = gmail_service.get_service()
    page_token = None
    total_processed = 0
    total_skipped = 0
    
    while True:
        try:
            results = service.users().messages().list(
                userId='me',
                pageToken=page_token,
                maxResults=500
            ).execute()
            
            messages = results.get('messages', [])

            for message in messages:
                # Check if email exists
                existing = db.query(EmailMessage).filter_by(id=message['id']).first()
                if existing:
                    total_skipped += 1
                    continue
                
                try:
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
                except Exception as e:
                    print(f"Error processing message {message['id']}: {str(e)}")
                    continue
            
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Error committing batch: {str(e)}")
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "message": f"Processed {total_processed} new messages, skipped {total_skipped} existing messages"
    }

@router.get("/emails")
async def get_emails(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    after_date: Optional[str] = None,
    sort_by: Literal["date", "sender_frequency", "domain_frequency"] = "domain_frequency"
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

    # Handle different sort types
    if sort_by == "sender_frequency":
        groups = (
            base_query
            .group_by(EmailMessage.sender_email, EmailMessage.sender_name)
            .with_entities(
                EmailMessage.sender_email,
                EmailMessage.sender_name,
                func.count().label('email_count'),
                func.max(EmailMessage.received_date).label('latest_date')
            )
            .order_by(desc('email_count'))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # Get emails for each group
        result = []
        for group in groups:
            emails = (
                base_query
                .filter(EmailMessage.sender_email == group.sender_email)
                .order_by(desc(EmailMessage.received_date))
                .all()
            )
            result.append({
                "type": "sender",
                "email": group.sender_email,
                "name": group.sender_name,
                "count": group.email_count,
                "latest_date": group.latest_date,
                "emails": emails
            })
        
        total = db.query(func.count(distinct(EmailMessage.sender_email))).scalar()

    elif sort_by == "domain_frequency":
        groups = (
            base_query
            .group_by(EmailMessage.sender_domain)
            .with_entities(
                EmailMessage.sender_domain,
                func.count().label('email_count'),
                func.max(EmailMessage.received_date).label('latest_date')
            )
            .order_by(desc('email_count'))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # Get emails for each group
        result = []
        for group in groups:
            emails = (
                base_query
                .filter(EmailMessage.sender_domain == group.sender_domain)
                .order_by(desc(EmailMessage.received_date))
                .all()
            )
            result.append({
                "type": "domain",
                "domain": group.sender_domain,
                "count": group.email_count,
                "latest_date": group.latest_date,
                "emails": emails
            })
        
        total = db.query(func.count(distinct(EmailMessage.sender_domain))).scalar()

    else:  # date sorting
        # Create subqueries for counts
        sender_counts = (
            db.query(
                EmailMessage.sender_email,
                func.count().label('sender_count')
            )
            .group_by(EmailMessage.sender_email)
            .subquery()
        )

        domain_counts = (
            db.query(
                EmailMessage.sender_domain,
                func.count().label('domain_count')
            )
            .group_by(EmailMessage.sender_domain)
            .subquery()
        )

        # Join with the main query
        query = (
            base_query
            .outerjoin(
                sender_counts,
                EmailMessage.sender_email == sender_counts.c.sender_email
            )
            .outerjoin(
                domain_counts,
                EmailMessage.sender_domain == domain_counts.c.sender_domain
            )
            .add_columns(
                sender_counts.c.sender_count,
                domain_counts.c.domain_count
            )
            .order_by(desc(EmailMessage.received_date))
        )

        emails = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Format the results
        result = [
            {
                "id": email[0].id,
                "sender_name": email[0].sender_name,
                "sender_email": email[0].sender_email,
                "sender_domain": email[0].sender_domain,
                "subject": email[0].subject,
                "received_date": email[0].received_date,
                "sender_count": email[1] or 0,
                "domain_count": email[2] or 0
            }
            for email in emails
        ]
        
        total = base_query.count()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": result
    }

@router.get("/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """Returns email analytics."""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_analytics()
