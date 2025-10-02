from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLEnum
from app.database import Base
from app.models.leave import LeaveType

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    year = Column(Integer, nullable=False)
    leave_type = Column(SQLEnum(LeaveType), nullable=False)
    total_allocated = Column(Integer, default=0)
    used = Column(Integer, default=0)
    available = Column(Integer, default=0)