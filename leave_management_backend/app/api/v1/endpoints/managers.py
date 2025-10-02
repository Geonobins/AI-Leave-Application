from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter
from app.database import get_db
from app.models.user import User, UserRole
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.leave_balance import LeaveBalance
from app.schemas.leave import LeaveResponse, LeaveApproval
from app.api.deps import get_current_manager
from app.services.ai_service import AIService

router = APIRouter()

@router.get("/pending-leaves", response_model=List[dict])
def get_pending_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get all pending leave requests for team members"""
    team_members = db.query(User).filter(User.manager_id == current_user.id).all()
    team_ids = [m.id for m in team_members]
    
    pending_leaves = db.query(Leave).filter(
        Leave.employee_id.in_(team_ids),
        Leave.status == LeaveStatus.PENDING
    ).all()
    
    ai_service = AIService()
    results = []
    
    for leave in pending_leaves:
        employee = db.query(User).filter(User.id == leave.employee_id).first()
        
        team_data = []
        impact = ai_service.calculate_impact_score({
            "start_date": leave.start_date,
            "end_date": leave.end_date
        }, team_data)
        
        results.append({
            "leave": LeaveResponse.from_orm(leave),
            "employee_name": employee.full_name,
            "employee_position": employee.position,
            "impact_score": impact
        })
    
    return results

@router.post("/leaves/approve")
def approve_reject_leave(
    approval: LeaveApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Approve or reject a leave request"""
    leave = db.query(Leave).filter(Leave.id == approval.leave_id).first()
    
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    
    employee = db.query(User).filter(User.id == leave.employee_id).first()
    if employee.manager_id != current_user.id and current_user.role != UserRole.HR:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    leave.status = LeaveStatus.APPROVED if approval.approved else LeaveStatus.REJECTED
    leave.manager_comments = approval.comments
    leave.decision_date = datetime.now()
    
    if approval.approved:
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == leave.employee_id,
            LeaveBalance.year == datetime.now().year,
            LeaveBalance.leave_type == leave.leave_type
        ).first()
        
        if balance:
            duration = (leave.end_date - leave.start_date).days + 1
            balance.used += duration
            balance.available -= duration
    
    db.commit()
    
    return {"message": "Leave request processed successfully", "status": leave.status}

@router.get("/team-overview")
def get_team_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get comprehensive team overview with current status"""
    team_members = db.query(User).filter(
        User.manager_id == current_user.id,
        User.is_active == True
    ).all()
    
    today = date.today()
    team_overview = []
    
    for member in team_members:
        # Check if on leave today
        current_leave = db.query(Leave).filter(
            Leave.employee_id == member.id,
            Leave.status == LeaveStatus.APPROVED,
            Leave.start_date <= today,
            Leave.end_date >= today
        ).first()
        
        # Get upcoming leaves (next 30 days)
        upcoming_leaves = db.query(Leave).filter(
            Leave.employee_id == member.id,
            Leave.status.in_([LeaveStatus.APPROVED, LeaveStatus.PENDING]),
            Leave.start_date > today,
            Leave.start_date <= today + timedelta(days=30)
        ).all()
        
        # Get leave balance
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == member.id,
            LeaveBalance.year == today.year
        ).all()
        
        total_available = sum(b.available for b in balances)
        total_used = sum(b.used for b in balances)
        total_allocated = sum(b.total_allocated for b in balances)
        
        team_overview.append({
            "id": member.id,
            "name": member.full_name,
            "position": member.position,
            "email": member.email,
            "status": "ON_LEAVE" if current_leave else "AVAILABLE",
            "current_leave": {
                "type": current_leave.leave_type.value if current_leave else None,
                "end_date": current_leave.end_date.isoformat() if current_leave else None,
                "days_remaining": (current_leave.end_date - today).days if current_leave else 0
            } if current_leave else None,
            "upcoming_leaves": [
                {
                    "id": leave.id,
                    "type": leave.leave_type.value,
                    "start_date": leave.start_date.isoformat(),
                    "end_date": leave.end_date.isoformat(),
                    "duration": (leave.end_date - leave.start_date).days + 1,
                    "status": leave.status.value
                }
                for leave in upcoming_leaves
            ],
            "leave_balance": {
                "total_allocated": total_allocated,
                "used": total_used,
                "available": total_available,
                "utilization": round((total_used / total_allocated * 100), 1) if total_allocated > 0 else 0
            }
        })
    
    # Calculate team statistics
    available_count = len([m for m in team_overview if m["status"] == "AVAILABLE"])
    on_leave_count = len([m for m in team_overview if m["status"] == "ON_LEAVE"])
    
    return {
        "team_members": team_overview,
        "team_size": len(team_members),
        "available_count": available_count,
        "on_leave_count": on_leave_count,
        "availability_rate": round((available_count / len(team_members) * 100), 1) if team_members else 0
    }

@router.get("/team-calendar")
def get_team_calendar(
    days_ahead: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get team calendar showing leave distribution"""
    team_members = db.query(User).filter(
        User.manager_id == current_user.id,
        User.is_active == True
    ).all()
    team_ids = [m.id for m in team_members]
    
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    
    # Get all leaves in the period
    leaves = db.query(Leave, User).join(
        User, Leave.employee_id == User.id
    ).filter(
        Leave.employee_id.in_(team_ids),
        Leave.status == LeaveStatus.APPROVED,
        Leave.start_date <= end_date,
        Leave.end_date >= today
    ).all()
    
    # Build calendar grid
    calendar = {}
    current = today
    while current <= end_date:
        date_key = current.isoformat()
        calendar[date_key] = {
            "date": date_key,
            "day_of_week": current.strftime("%A"),
            "is_weekend": current.weekday() >= 5,
            "leaves": [],
            "available_count": len(team_members)
        }
        current += timedelta(days=1)
    
    # Populate leaves
    for leave, user in leaves:
        current = max(leave.start_date, today)
        while current <= min(leave.end_date, end_date):
            date_key = current.isoformat()
            if date_key in calendar:
                calendar[date_key]["leaves"].append({
                    "employee_id": user.id,
                    "employee_name": user.full_name,
                    "position": user.position,
                    "leave_type": leave.leave_type.value
                })
                calendar[date_key]["available_count"] -= 1
            current += timedelta(days=1)
    
    # Convert to list and calculate metrics
    calendar_list = sorted(calendar.values(), key=lambda x: x["date"])
    
    # Identify critical days (low availability)
    critical_days = [
        day for day in calendar_list 
        if not day["is_weekend"] and 
        len(day["leaves"]) > len(team_members) * 0.3  # More than 30% absent
    ]
    
    return {
        "calendar": calendar_list,
        "period": {
            "start": today.isoformat(),
            "end": end_date.isoformat(),
            "days": days_ahead
        },
        "team_size": len(team_members),
        "critical_days": len(critical_days),
        "max_concurrent_leaves": max((len(day["leaves"]) for day in calendar_list), default=0)
    }

@router.get("/team-insights")
def get_team_insights(
    period: str = Query(default="last_30_days", regex="^(last_30_days|last_quarter|current_year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get AI-powered insights about team leave patterns"""
    team_members = db.query(User).filter(
        User.manager_id == current_user.id,
        User.is_active == True
    ).all()
    team_ids = [m.id for m in team_members]
    
    if not team_members:
        return {"message": "No team members found"}
    
    # Determine date range
    today = date.today()
    if period == "last_30_days":
        start_date = today - timedelta(days=30)
    elif period == "last_quarter":
        start_date = today - timedelta(days=90)
    else:  # current_year
        start_date = date(today.year, 1, 1)
    
    # Get leaves in period
    leaves = db.query(Leave, User).join(
        User, Leave.employee_id == User.id
    ).filter(
        Leave.employee_id.in_(team_ids),
        Leave.start_date >= start_date,
        Leave.start_date <= today
    ).all()
    
    # Build analytics data
    analytics_data = {
        "leaves": [],
        "users": [],
        "balances": []
    }
    
    for leave, user in leaves:
        duration = (leave.end_date - leave.start_date).days + 1
        analytics_data["leaves"].append({
            "employee_id": user.id,
            "employee_name": user.full_name,
            "department": user.department,
            "position": user.position,
            "leave_type": leave.leave_type.value,
            "start_date": leave.start_date.isoformat(),
            "end_date": leave.end_date.isoformat(),
            "duration": duration,
            "status": leave.status.value,
            "approved": leave.status == LeaveStatus.APPROVED
        })
    
    for member in team_members:
        analytics_data["users"].append({
            "id": member.id,
            "name": member.full_name,
            "department": member.department,
            "position": member.position
        })
    
    # Get balances
    balances = db.query(LeaveBalance, User).join(
        User, LeaveBalance.employee_id == User.id
    ).filter(
        LeaveBalance.employee_id.in_(team_ids),
        LeaveBalance.year == today.year
    ).all()
    
    for balance, user in balances:
        analytics_data["balances"].append({
            "employee_id": user.id,
            "employee_name": user.full_name,
            "leave_type": balance.leave_type.value,
            "total": balance.total_allocated,
            "used": balance.used,
            "available": balance.available,
            "utilization": (balance.used / balance.total_allocated * 100) if balance.total_allocated > 0 else 0
        })
    
    # Calculate metrics
    total_leaves = len([l for l in analytics_data["leaves"] if l["approved"]])
    total_days = sum(l["duration"] for l in analytics_data["leaves"] if l["approved"])
    
    # Team member activity
    member_stats = defaultdict(lambda: {"leaves": 0, "days": 0})
    for leave in analytics_data["leaves"]:
        if leave["approved"]:
            member_stats[leave["employee_id"]]["leaves"] += 1
            member_stats[leave["employee_id"]]["days"] += leave["duration"]
    
    # Identify patterns
    leave_types = Counter(l["leave_type"] for l in analytics_data["leaves"] if l["approved"])
    most_common_type = leave_types.most_common(1)[0] if leave_types else ("N/A", 0)
    
    # Risk indicators
    risks = []
    
    # Check for team members not taking leave
    inactive_members = [
        member for member in team_members
        if member.id not in member_stats or member_stats[member.id]["days"] == 0
    ]
    
    if len(inactive_members) > len(team_members) * 0.3:
        risks.append({
            "type": "LOW_UTILIZATION",
            "severity": "MEDIUM",
            "message": f"{len(inactive_members)} team members haven't taken leave in {period.replace('_', ' ')}",
            "affected_count": len(inactive_members)
        })
    
    # Check for uneven distribution
    if member_stats:
        avg_days = total_days / len(team_members)
        high_usage = [
            uid for uid, stats in member_stats.items()
            if stats["days"] > avg_days * 1.5
        ]
        
        if high_usage:
            risks.append({
                "type": "UNEVEN_DISTRIBUTION",
                "severity": "LOW",
                "message": f"{len(high_usage)} team members using significantly more leave than average",
                "affected_count": len(high_usage)
            })
    
    # Generate insights summary
    insights_text = generate_team_insights_text(
        team_size=len(team_members),
        total_leaves=total_leaves,
        total_days=total_days,
        period=period,
        most_common_type=most_common_type,
        risks=risks,
        inactive_count=len(inactive_members)
    )
    
    return {
        "summary": {
            "team_size": len(team_members),
            "total_leaves": total_leaves,
            "total_days": total_days,
            "avg_days_per_person": round(total_days / len(team_members), 1) if team_members else 0,
            "period": period.replace("_", " ").title(),
            "most_common_leave_type": most_common_type[0]
        },
        "member_breakdown": [
            {
                "employee_id": member.id,
                "name": member.full_name,
                "position": member.position,
                "leaves_taken": member_stats[member.id]["leaves"],
                "days_taken": member_stats[member.id]["days"]
            }
            for member in team_members
        ],
        "risks": risks,
        "insights": insights_text
    }

@router.get("/team-availability-forecast")
def team_availability_forecast(
    days_ahead: int = Query(default=14, ge=7, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Forecast team availability for planning"""
    team_members = db.query(User).filter(
        User.manager_id == current_user.id,
        User.is_active == True
    ).all()
    team_ids = [m.id for m in team_members]
    team_size = len(team_members)
    
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    
    # Get approved and pending leaves
    leaves = db.query(Leave).filter(
        Leave.employee_id.in_(team_ids),
        Leave.status.in_([LeaveStatus.APPROVED, LeaveStatus.PENDING]),
        Leave.start_date <= end_date,
        Leave.end_date >= today
    ).all()
    
    # Build daily forecast
    forecast = []
    current = today
    
    while current <= end_date:
        approved_absences = []
        pending_absences = []
        
        for leave in leaves:
            if leave.start_date <= current <= leave.end_date:
                absence_info = {
                    "employee_id": leave.employee_id,
                    "leave_type": leave.leave_type.value
                }
                
                if leave.status == LeaveStatus.APPROVED:
                    approved_absences.append(absence_info)
                else:
                    pending_absences.append(absence_info)
        
        available_count = team_size - len(approved_absences)
        potential_available = available_count - len(pending_absences)
        
        availability_rate = (available_count / team_size * 100) if team_size > 0 else 0
        
        forecast.append({
            "date": current.isoformat(),
            "day_of_week": current.strftime("%A"),
            "is_weekend": current.weekday() >= 5,
            "available_count": available_count,
            "potential_available": potential_available,
            "approved_absences": len(approved_absences),
            "pending_absences": len(pending_absences),
            "availability_rate": round(availability_rate, 1),
            "capacity_level": get_capacity_level(availability_rate)
        })
        
        current += timedelta(days=1)
    
    # Identify critical periods
    critical_periods = [
        day for day in forecast
        if not day["is_weekend"] and day["availability_rate"] < 70
    ]
    
    return {
        "forecast": forecast,
        "team_size": team_size,
        "critical_periods": len(critical_periods),
        "avg_availability": round(
            sum(d["availability_rate"] for d in forecast if not d["is_weekend"]) / 
            len([d for d in forecast if not d["is_weekend"]]),
            1
        ) if forecast else 0
    }

def get_capacity_level(availability_rate: float) -> str:
    """Determine capacity level based on availability"""
    if availability_rate >= 90:
        return "FULL"
    elif availability_rate >= 70:
        return "GOOD"
    elif availability_rate >= 50:
        return "LIMITED"
    else:
        return "CRITICAL"

def generate_team_insights_text(
    team_size: int,
    total_leaves: int,
    total_days: int,
    period: str,
    most_common_type: tuple,
    risks: list,
    inactive_count: int
) -> str:
    """Generate human-readable insights"""
    insights = []
    
    # Overall activity
    avg_days = total_days / team_size if team_size > 0 else 0
    insights.append(f"Your team of {team_size} took {total_leaves} leave requests totaling {total_days} days in the {period.replace('_', ' ')}.")
    
    # Average usage
    if avg_days < 3:
        insights.append(f"With only {avg_days:.1f} days per person on average, your team may be underutilizing their leave benefits.")
    elif avg_days > 10:
        insights.append(f"At {avg_days:.1f} days per person, leave usage is above typical levels - ensure adequate coverage is maintained.")
    else:
        insights.append(f"Leave utilization appears healthy at {avg_days:.1f} days per person on average.")
    
    # Most common leave type
    if most_common_type[1] > 0:
        insights.append(f"The most common leave type is {most_common_type[0]}, accounting for {most_common_type[1]} requests.")
    
    # Risks
    if risks:
        high_severity = [r for r in risks if r["severity"] in ["HIGH", "CRITICAL"]]
        if high_severity:
            insights.append(f"⚠️ {len(high_severity)} high-priority concern(s) detected requiring your attention.")
    
    # Inactive members
    if inactive_count > 0:
        insights.append(f"Consider checking in with {inactive_count} team member(s) who haven't taken leave recently to ensure work-life balance.")
    
    return " ".join(insights)