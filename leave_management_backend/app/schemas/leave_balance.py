from pydantic import BaseModel
from app.models.leave import LeaveType

class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    year: int
    leave_type: LeaveType
    total_allocated: int
    used: int
    available: int
    
    class Config:
        from_attributes = True