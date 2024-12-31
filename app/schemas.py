from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class EmailMessageBase(BaseModel):
    sender_name: str
    sender_email: str
    sender_domain: str
    subject: Optional[str]
    received_date: datetime

class EmailMessage(EmailMessageBase):
    id: str

    class Config:
        from_attributes = True

class SenderStats(BaseModel):
    email: str
    name: str
    count: int

class DomainStats(BaseModel):
    domain: str
    count: int

class Analytics(BaseModel):
    top_senders: List[SenderStats]
    top_domains: List[DomainStats]
