from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from app.database import Base

class CompanyPolicy(Base):
    __tablename__ = "company_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10))  # pdf, docx, txt
    upload_date = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer)  # HR user id
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    extracted_text = Column(Text)
    embedding_status = Column(String(20), default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    
    # Policy metadata
    effective_date = Column(DateTime)
    policy_type = Column(String(50))  # LEAVE, GENERAL, ATTENDANCE, etc.