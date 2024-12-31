from sqlalchemy import Column, Integer, String, DateTime
from .database import Base

class EmailMessage(Base):
    __tablename__ = 'email_messages'
    
    id = Column(String, primary_key=True)
    sender_name = Column(String)
    sender_email = Column(String)
    sender_domain = Column(String)
    received_date = Column(DateTime)
    subject = Column(String)
