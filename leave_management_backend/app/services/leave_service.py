from sqlalchemy.orm import Session
from app.models.leave import Leave, LeaveStatus
from app.models.leave_balance import LeaveBalance
from datetime import datetime

class LeaveService:
    
    @staticmethod
    def create_leave_request(db: Session, leave_data: dict, employee_id: int):
        """Create a new leave request"""
        db_leave = Leave(
            employee_id=employee_id,
            **leave_data
        )
        db.add(db_leave)
        db.commit()
        db.refresh(db_leave)
        return db_leave
    
    @staticmethod
    def check_leave_balance(db: Session, employee_id: int, leave_type: str, duration: int) -> bool:
        """Check if employee has sufficient leave balance"""
        current_year = datetime.now().year
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == current_year,
            LeaveBalance.leave_type == leave_type
        ).first()
        
        if not balance:
            return False
        
        return balance.available >= duration
    
    @staticmethod
    def update_leave_balance(db: Session, employee_id: int, leave_type: str, duration: int):
        """Update leave balance after approval"""
        current_year = datetime.now().year
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == current_year,
            LeaveBalance.leave_type == leave_type
        ).first()
        
        if balance:
            balance.used += duration
            balance.available -= duration
            db.commit()