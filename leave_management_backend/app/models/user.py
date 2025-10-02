from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    HR = "HR"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.EMPLOYEE)
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Added ForeignKey
    is_active = Column(Boolean, default=True)

    # Relationship - fixed
    manager = relationship("User", remote_side=[id], backref="subordinates")