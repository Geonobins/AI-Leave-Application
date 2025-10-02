from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.leave_balance import LeaveBalance
from app.models.leave import LeaveType
from app.utils.security import get_password_hash
from datetime import datetime

def init_sample_data():
    init_db()
    db = SessionLocal()
    
    # Create sample users
    users = [
        User(
            email="manager@company.com",
            username="manager",
            full_name="Sarah Manager",
            hashed_password=get_password_hash("password123"),
            role="MANAGER",
            department="Engineering",
            position="Engineering Manager"
        ),
        User(
            email="employee@company.com",
            username="employee",
            full_name="John Employee",
            hashed_password=get_password_hash("password123"),
            role="EMPLOYEE",
            department="Engineering",
            position="Software Developer",
            manager_id=1
        ),
        User(
            email="hr@company.com",
            username="hr",
            full_name="Alice HR",
            hashed_password=get_password_hash("password123"),
            role="HR",
            department="Human Resources",
            position="HR Manager"
        )
    ]
    
    db.add_all(users)
    db.commit()
    
    # Create leave balances for employees
    current_year = datetime.now().year
    leave_types = [LeaveType.CASUAL, LeaveType.SICK, LeaveType.ANNUAL]
    
    for user in users:
        if user.role == "EMPLOYEE":
            for leave_type in leave_types:
                balance = LeaveBalance(
                    employee_id=user.id,
                    year=current_year,
                    leave_type=leave_type,
                    total_allocated=10 if leave_type == LeaveType.CASUAL else 15,
                    used=0,
                    available=10 if leave_type == LeaveType.CASUAL else 15
                )
                db.add(balance)
    
    db.commit()
    db.close()
    
    print("Sample data initialized successfully!")
    print("\nSample Users:")
    print("1. Manager - username: manager, password: password123")
    print("2. Employee - username: employee, password: password123")
    print("3. HR - username: hr, password: password123")

if __name__ == "__main__":
    init_sample_data()