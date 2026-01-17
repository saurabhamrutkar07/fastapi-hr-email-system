from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.database import Base

class HRContacts(Base):
    __tablename__ = "hr_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)




# class EmailLogs(Base):
#     __tablename__ = "email_logs"

#     id = Column(Integer, primary_key=True)
#     recipient_email = Column(String(100), nullable=False)
#     status = Column(String(20), nullable=False)
#     error_message = Column(Text)
#     sent_at = Column(DateTime, default=datetime.utcnow)
