from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, ForeignKey, Text

class PolicyChunk(Base):
    __tablename__ = "policy_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, nullable=False)
    chunk_index = Column(Integer)
    content = Column(Text)
    embedding = Column(Text)  # Store as JSON string of vector
    section_title = Column(String(255))
    page_number = Column(Integer)
