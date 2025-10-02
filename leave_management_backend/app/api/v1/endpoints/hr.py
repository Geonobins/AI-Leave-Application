from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

from app.models.leave_balance import LeaveBalance
from app.models.leave import LeaveType
from app.schemas.leave_balance import LeaveBalanceResponse
from pydantic import BaseModel, Field

router = APIRouter()

class LeaveBalanceCreate(BaseModel):
    employee_id: int
    year: int
    leave_type: LeaveType
    total_allocated: int = Field(ge=0, description="Total days allocated")

class LeaveBalanceUpdate(BaseModel):
    total_allocated: int = Field(ge=0, description="Total days allocated")

class LeaveBalanceBulkUpdate(BaseModel):
    year: int
    leave_allocations: dict[LeaveType, int] = Field(
        ..., 
        description="Dictionary mapping leave types to allocated days"
    )


class RoleUpdate(BaseModel):
    user_id: int
    new_role: str

class ManagerUpdate(BaseModel):
    user_id: int
    new_manager_id: int

class UserManagementResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    department: str
    position: str
    manager_id: int | None
    is_active: bool

    class Config:
        from_attributes = True

def get_hr_user(current_user: User = Depends(get_current_user)):
    """Dependency to verify user is HR"""
    if current_user.role != UserRole.HR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. HR role required."
        )
    return current_user

# Update your HR routes to use proper serialization
@router.get("/users", response_model=List[UserManagementResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Get all users in the system"""
    users = db.query(User).all()
    # Convert to response model
    return [UserManagementResponse.from_orm(user) for user in users]

@router.get("/users/{user_id}", response_model=UserManagementResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserManagementResponse.from_orm(user)

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Update a user's role"""
    if role_data.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    
    valid_roles = ["EMPLOYEE", "MANAGER", "HR"]
    if role_data.new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = UserRole[role_data.new_role]
    db.commit()
    db.refresh(user)
    
    return {"message": f"Role updated successfully to {role_data.new_role}", "user": user}

@router.put("/users/{user_id}/manager")
def update_user_manager(
    user_id: int,
    manager_data: ManagerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Update a user's manager"""
    if manager_data.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify new manager exists
    if manager_data.new_manager_id:
        manager = db.query(User).filter(User.id == manager_data.new_manager_id).first()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        if manager.role not in [UserRole.MANAGER, UserRole.HR]:
            raise HTTPException(status_code=400, detail="Assigned user must be a Manager or HR")
    
    user.manager_id = manager_data.new_manager_id
    db.commit()
    db.refresh(user)
    
    return {"message": "Manager updated successfully", "user": user}

@router.put("/users/{user_id}/activate")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Activate or deactivate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    status_text = "activated" if user.is_active else "deactivated"
    return {"message": f"User {status_text} successfully", "user": user}

@router.get("/managers", response_model=List[UserManagementResponse])
def get_all_managers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Get all users with Manager or HR role"""
    managers = db.query(User).filter(User.role.in_([UserRole.MANAGER, UserRole.HR])).all()
    return managers




def get_hr_user(current_user: User = Depends(get_current_user)):
    """Dependency to verify user is HR"""
    if current_user.role != UserRole.HR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. HR role required."
        )
    return current_user

@router.get("/leave-balances", response_model=List[LeaveBalanceResponse])
def get_all_leave_balances(
    year: int = None,
    employee_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Get all leave balances with optional filters"""
    query = db.query(LeaveBalance)
    
    if year:
        query = query.filter(LeaveBalance.year == year)
    if employee_id:
        query = query.filter(LeaveBalance.employee_id == employee_id)
    
    balances = query.all()
    return balances

@router.get("/leave-balances/{balance_id}", response_model=LeaveBalanceResponse)
def get_leave_balance(
    balance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Get a specific leave balance by ID"""
    balance = db.query(LeaveBalance).filter(LeaveBalance.id == balance_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="Leave balance not found")
    return balance

@router.post("/leave-balances", response_model=LeaveBalanceResponse, status_code=status.HTTP_201_CREATED)
def create_leave_balance(
    balance_data: LeaveBalanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Create a new leave balance for an employee"""
    # Verify employee exists
    employee = db.query(User).filter(User.id == balance_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if balance already exists for this employee, year, and leave type
    existing = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == balance_data.employee_id,
        LeaveBalance.year == balance_data.year,
        LeaveBalance.leave_type == balance_data.leave_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Leave balance already exists for this employee, year, and leave type"
        )
    
    # Create new balance
    new_balance = LeaveBalance(
        employee_id=balance_data.employee_id,
        year=balance_data.year,
        leave_type=balance_data.leave_type,
        total_allocated=balance_data.total_allocated,
        used=0,
        available=balance_data.total_allocated
    )
    
    db.add(new_balance)
    db.commit()
    db.refresh(new_balance)
    
    return new_balance

@router.put("/leave-balances/{balance_id}", response_model=LeaveBalanceResponse)
def update_leave_balance(
    balance_id: int,
    balance_data: LeaveBalanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Update a leave balance allocation"""
    balance = db.query(LeaveBalance).filter(LeaveBalance.id == balance_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="Leave balance not found")
    
    # Update total allocated
    balance.total_allocated = balance_data.total_allocated
    
    # Recalculate available (total - used)
    balance.available = balance.total_allocated - balance.used
    
    # Ensure available doesn't go negative
    if balance.available < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot set allocation to {balance_data.total_allocated}. "
                   f"Employee has already used {balance.used} days."
        )
    
    db.commit()
    db.refresh(balance)
    
    return balance

@router.delete("/leave-balances/{balance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave_balance(
    balance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Delete a leave balance"""
    balance = db.query(LeaveBalance).filter(LeaveBalance.id == balance_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="Leave balance not found")
    
    db.delete(balance)
    db.commit()
    
    return None

@router.post("/leave-balances/bulk-create")
def bulk_create_leave_balances(
    bulk_data: LeaveBalanceBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Create leave balances for all active employees for a given year"""
    # Get all active employees
    employees = db.query(User).filter(User.is_active == True).all()
    
    created_count = 0
    skipped_count = 0
    
    for employee in employees:
        for leave_type, allocated_days in bulk_data.leave_allocations.items():
            # Check if already exists
            existing = db.query(LeaveBalance).filter(
                LeaveBalance.employee_id == employee.id,
                LeaveBalance.year == bulk_data.year,
                LeaveBalance.leave_type == leave_type
            ).first()
            
            if not existing:
                new_balance = LeaveBalance(
                    employee_id=employee.id,
                    year=bulk_data.year,
                    leave_type=leave_type,
                    total_allocated=allocated_days,
                    used=0,
                    available=allocated_days
                )
                db.add(new_balance)
                created_count += 1
            else:
                skipped_count += 1
    
    db.commit()
    
    return {
        "message": "Bulk leave balance creation completed",
        "year": bulk_data.year,
        "employees_processed": len(employees),
        "balances_created": created_count,
        "balances_skipped": skipped_count
    }

@router.put("/leave-balances/employee/{employee_id}/reset")
def reset_employee_balances(
    employee_id: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Reset all leave balances for an employee for a specific year"""
    # Verify employee exists
    employee = db.query(User).filter(User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get all balances for this employee and year
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == year
    ).all()
    
    if not balances:
        raise HTTPException(
            status_code=404, 
            detail=f"No leave balances found for employee {employee_id} in year {year}"
        )
    
    # Reset used to 0 and recalculate available
    for balance in balances:
        balance.used = 0
        balance.available = balance.total_allocated
    
    db.commit()
    
    return {
        "message": f"Leave balances reset successfully for employee {employee_id}",
        "year": year,
        "balances_reset": len(balances)
    }

@router.get("/leave-balances/employee/{employee_id}/summary")
def get_employee_balance_summary(
    employee_id: int,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Get a summary of leave balances for a specific employee"""
    # Verify employee exists
    employee = db.query(User).filter(User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    query = db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee_id)
    
    if year:
        query = query.filter(LeaveBalance.year == year)
    
    balances = query.all()
    
    summary = {
        "employee_id": employee_id,
        "employee_name": employee.full_name,
        "year": year,
        "balances": [LeaveBalanceResponse.from_orm(b) for b in balances],
        "total_allocated": sum(b.total_allocated for b in balances),
        "total_used": sum(b.used for b in balances),
        "total_available": sum(b.available for b in balances)
    }
    
    return summary    