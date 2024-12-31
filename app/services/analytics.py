from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import EmailMessage
from ..schemas import Analytics, SenderStats, DomainStats

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_analytics(self) -> Analytics:
        top_senders = (
            self.db.query(
                EmailMessage.sender_email,
                EmailMessage.sender_name,
                func.count(EmailMessage.id).label('count')
            )
            .group_by(EmailMessage.sender_email)
            .order_by(func.count(EmailMessage.id).desc())
            .limit(20)
            .all()
        )

        top_domains = (
            self.db.query(
                EmailMessage.sender_domain,
                func.count(EmailMessage.id).label('count')
            )
            .group_by(EmailMessage.sender_domain)
            .order_by(func.count(EmailMessage.id).desc())
            .limit(20)
            .all()
        )

        return Analytics(
            top_senders=[
                SenderStats(email=s[0], name=s[1], count=s[2]) 
                for s in top_senders
            ],
            top_domains=[
                DomainStats(domain=d[0], count=d[1]) 
                for d in top_domains
            ]
        )
