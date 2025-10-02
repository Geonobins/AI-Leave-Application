from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.leave import Leave
from app.api.deps import get_current_user
from app.services.ai_service import AIService
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/suggest-dates")
def suggest_optimal_dates(
    duration_days: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suggest optimal leave dates based on team availability"""
    # Get team members
    team_members = db.query(User).filter(
        User.department == current_user.department,
        User.id != current_user.id
    ).all()
    
    team_ids = [m.id for m in team_members]
    
    # Check next 60 days for conflicts
    suggestions = []
    today = datetime.now().date()
    
    for offset in range(0, 60, 7):  # Check weekly intervals
        start_date = today + timedelta(days=offset)
        end_date = start_date + timedelta(days=duration_days - 1)
        
        # Count overlapping leaves
        overlapping = db.query(Leave).filter(
            Leave.employee_id.in_(team_ids),
            Leave.status == "APPROVED",
            Leave.start_date <= end_date,
            Leave.end_date >= start_date
        ).count()
        
        conflict_score = overlapping * 25
        
        suggestions.append({
            "start_date": start_date,
            "end_date": end_date,
            "conflict_score": conflict_score,
            "overlapping_leaves": overlapping,
            "recommendation": "Optimal" if overlapping == 0 else "Moderate" if overlapping < 2 else "High Conflict"
        })
    
    # Sort by conflict score
    suggestions.sort(key=lambda x: x["conflict_score"])
    
    return {"suggestions": suggestions[:5]}  # Return top 5

@router.get("/responsible-person-suggestions")
def suggest_responsible_person(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suggest suitable colleagues to handle responsibilities"""
    from datetime import datetime
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # Get colleagues in same department
    colleagues = db.query(User).filter(
        User.department == current_user.department,
        User.id != current_user.id
    ).all()
    
    suggestions = []
    
    for colleague in colleagues:
        # Check if they're on leave during requested dates
        conflicting_leaves = db.query(Leave).filter(
            Leave.employee_id == colleague.id,
            Leave.status == "APPROVED",
            Leave.start_date <= end,
            Leave.end_date >= start
        ).count()
        
        if conflicting_leaves == 0:
            suggestions.append({
                "id": colleague.id,
                "name": colleague.full_name,
                "position": colleague.position,
                "department": colleague.department,
                "availability": "Available",
                "score": 100 if colleague.position == current_user.position else 80
            })
        else:
            suggestions.append({
                "id": colleague.id,
                "name": colleague.full_name,
                "position": colleague.position,
                "department": colleague.department,
                "availability": "On Leave",
                "score": 0
            })
    
    # Sort by score
    suggestions.sort(key=lambda x: x["score"], reverse=True)
    
    return {"suggestions": suggestions[:5]}