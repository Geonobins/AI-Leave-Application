from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models.user import User, UserRole
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.leave_balance import LeaveBalance
from app.api.deps import get_current_user
from app.services.analytics_ai_service import AnalyticsAIService
from pydantic import BaseModel

router = APIRouter()

class AnalyticsRequest(BaseModel):
    timeframe: str = "current_year"  # current_year, last_6_months, last_quarter
    department: Optional[str] = None
    include_predictions: bool = True

class AnalyticsResponse(BaseModel):
    summary: Dict
    trends: Dict
    predictions: Dict
    risks: Dict
    recommendations: List[Dict]
    insights: str

def get_hr_user(current_user: User = Depends(get_current_user)):
    """Dependency to verify user is HR"""
    if current_user.role != UserRole.HR:
        raise HTTPException(
            status_code=403,
            detail="Access denied. HR role required for analytics."
        )
    return current_user

@router.post("/insights", response_model=AnalyticsResponse)
def get_ai_insights(
    request: AnalyticsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """
    Get AI-powered analytics insights with predictions and recommendations
    """
    
    # Determine date range
    today = date.today()
    if request.timeframe == "current_year":
        start_date = date(today.year, 1, 1)
        end_date = today
    elif request.timeframe == "last_6_months":
        start_date = today - timedelta(days=180)
        end_date = today
    elif request.timeframe == "last_quarter":
        start_date = today - timedelta(days=90)
        end_date = today
    else:
        start_date = date(today.year, 1, 1)
        end_date = today
    
    # Build base query
    query = db.query(Leave, User).join(User, Leave.employee_id == User.id)
    query = query.filter(
        Leave.start_date >= start_date,
        Leave.start_date <= end_date
    )
    
    if request.department:
        query = query.filter(User.department == request.department)
    
    leaves = query.all()
    
    # Gather comprehensive data
    analytics_data = {
        "leaves": [],
        "users": [],
        "balances": [],
        "timeframe": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": (end_date - start_date).days
        }
    }
    
    # Process leaves
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
            "created_at": leave.created_at.isoformat(),
            "approved": leave.status == LeaveStatus.APPROVED
        })
    
    # Get all users in scope
    user_query = db.query(User).filter(User.role != UserRole.HR)
    if request.department:
        user_query = user_query.filter(User.department == request.department)
    
    users = user_query.all()
    for user in users:
        analytics_data["users"].append({
            "id": user.id,
            "name": user.full_name,
            "department": user.department,
            "position": user.position,
            "role": user.role.value
        })
    
    # Get leave balances
    balance_query = db.query(LeaveBalance, User).join(
        User, LeaveBalance.employee_id == User.id
    ).filter(LeaveBalance.year == today.year)
    
    if request.department:
        balance_query = balance_query.filter(User.department == request.department)
    
    balances = balance_query.all()
    for balance, user in balances:
        analytics_data["balances"].append({
            "employee_id": user.id,
            "employee_name": user.full_name,
            "department": user.department,
            "leave_type": balance.leave_type.value,
            "total": balance.total_allocated,
            "used": balance.used,
            "available": balance.available,
            "utilization": (balance.used / balance.total_allocated * 100) if balance.total_allocated > 0 else 0
        })
    
    # Calculate summary statistics
    total_leaves = len(analytics_data["leaves"])
    approved_leaves = len([l for l in analytics_data["leaves"] if l["approved"]])
    total_days = sum(l["duration"] for l in analytics_data["leaves"])
    
    avg_duration = total_days / total_leaves if total_leaves > 0 else 0
    approval_rate = (approved_leaves / total_leaves * 100) if total_leaves > 0 else 0
    
    # Department breakdown
    dept_stats = {}
    for leave in analytics_data["leaves"]:
        dept = leave["department"]
        if dept not in dept_stats:
            dept_stats[dept] = {"count": 0, "days": 0}
        dept_stats[dept]["count"] += 1
        dept_stats[dept]["days"] += leave["duration"]
    
    summary = {
        "total_requests": total_leaves,
        "approved_requests": approved_leaves,
        "total_days_taken": total_days,
        "avg_duration": round(avg_duration, 1),
        "approval_rate": round(approval_rate, 1),
        "active_employees": len(analytics_data["users"]),
        "departments": dept_stats
    }
    
    # Use AI service for advanced analytics
    ai_service = AnalyticsAIService()
    
    # Get trends
    trends = ai_service.analyze_trends(analytics_data)
    
    # Get predictions (if requested)
    predictions = {}
    if request.include_predictions:
        predictions = ai_service.predict_patterns(analytics_data)
    
    # Identify risks
    risks = ai_service.identify_risks(analytics_data)
    
    # Generate recommendations
    recommendations = ai_service.generate_recommendations(
        analytics_data, trends, risks
    )
    
    # Generate natural language insights
    insights = ai_service.generate_insights_summary(
        summary, trends, predictions, risks
    )
    
    return AnalyticsResponse(
        summary=summary,
        trends=trends,
        predictions=predictions,
        risks=risks,
        recommendations=recommendations,
        insights=insights
    )

@router.get("/department-comparison")
def department_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Compare leave patterns across departments"""
    today = date.today()
    year_start = date(today.year, 1, 1)
    
    departments = db.query(User.department).distinct().all()
    comparison = []
    
    for (dept,) in departments:
        # Get leaves for department
        leaves = db.query(Leave, User).join(
            User, Leave.employee_id == User.id
        ).filter(
            User.department == dept,
            Leave.start_date >= year_start
        ).all()
        
        total_leaves = len(leaves)
        total_days = sum((l.end_date - l.start_date).days + 1 for l, _ in leaves)
        
        # Get employee count
        emp_count = db.query(User).filter(
            User.department == dept,
            User.role != UserRole.HR
        ).count()
        
        comparison.append({
            "department": dept,
            "total_leaves": total_leaves,
            "total_days": total_days,
            "employee_count": emp_count,
            "avg_leaves_per_employee": round(total_leaves / emp_count, 1) if emp_count > 0 else 0,
            "avg_days_per_employee": round(total_days / emp_count, 1) if emp_count > 0 else 0
        })
    
    return {"departments": comparison}

@router.get("/burnout-indicators")
def burnout_indicators(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Identify employees with potential burnout indicators"""
    today = date.today()
    six_months_ago = today - timedelta(days=180)
    
    # Get all employees with their leave data
    users = db.query(User).filter(User.role != UserRole.HR).all()
    
    indicators = []
    
    for user in users:
        # Count leaves in last 6 months
        recent_leaves = db.query(Leave).filter(
            Leave.employee_id == user.id,
            Leave.start_date >= six_months_ago,
            Leave.status == LeaveStatus.APPROVED
        ).all()
        
        total_days = sum((l.end_date - l.start_date).days + 1 for l in recent_leaves)
        
        # Get balance utilization
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == user.id,
            LeaveBalance.year == today.year
        ).all()
        
        total_available = sum(b.available for b in balances)
        total_allocated = sum(b.total_allocated for b in balances)
        
        utilization = ((total_allocated - total_available) / total_allocated * 100) if total_allocated > 0 else 0
        
        # Risk factors
        risk_factors = []
        risk_score = 0
        
        # Low leave utilization (< 20%)
        if utilization < 20 and total_allocated > 0:
            risk_factors.append("Very low leave utilization")
            risk_score += 30
        
        # No leaves in last 6 months
        if len(recent_leaves) == 0:
            risk_factors.append("No leaves taken in 6 months")
            risk_score += 40
        
        # Only sick leaves (potential stress indicator)
        if recent_leaves and all(l.leave_type == LeaveType.SICK for l in recent_leaves):
            risk_factors.append("Only sick leaves taken")
            risk_score += 20
        
        # High number of short leaves (fragmented time off)
        short_leaves = [l for l in recent_leaves if (l.end_date - l.start_date).days == 0]
        if len(short_leaves) > 5:
            risk_factors.append("Many single-day leaves (fragmented rest)")
            risk_score += 15
        
        if risk_score > 30:  # Only include moderate to high risk
            indicators.append({
                "employee_id": user.id,
                "employee_name": user.full_name,
                "department": user.department,
                "position": user.position,
                "risk_score": risk_score,
                "risk_level": "HIGH" if risk_score > 60 else "MEDIUM",
                "risk_factors": risk_factors,
                "days_taken_6m": total_days,
                "leave_utilization": round(utilization, 1),
                "available_days": total_available
            })
    
    # Sort by risk score
    indicators.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return {
        "at_risk_employees": indicators,
        "total_at_risk": len(indicators),
        "high_risk": len([i for i in indicators if i["risk_level"] == "HIGH"]),
        "medium_risk": len([i for i in indicators if i["risk_level"] == "MEDIUM"])
    }

@router.get("/coverage-gaps")
def coverage_gaps(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_user)
):
    """Identify potential coverage gaps in upcoming period"""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)
    
    # Get all approved future leaves
    future_leaves = db.query(Leave, User).join(
        User, Leave.employee_id == User.id
    ).filter(
        Leave.status == LeaveStatus.APPROVED,
        Leave.start_date <= end_date,
        Leave.end_date >= today
    ).all()
    
    # Group by department and date
    coverage_map = {}
    
    for leave, user in future_leaves:
        dept = user.department
        if dept not in coverage_map:
            coverage_map[dept] = {}
        
        # Mark each day
        current = max(leave.start_date, today)
        while current <= min(leave.end_date, end_date):
            date_key = current.isoformat()
            if date_key not in coverage_map[dept]:
                coverage_map[dept][date_key] = []
            coverage_map[dept][date_key].append({
                "employee": user.full_name,
                "position": user.position
            })
            current += timedelta(days=1)
    
    # Identify gaps (days with high absence %)
    gaps = []
    
    for dept, dates in coverage_map.items():
        # Get department size
        dept_size = db.query(User).filter(
            User.department == dept,
            User.role != UserRole.HR
        ).count()
        
        for date_str, absences in dates.items():
            absence_count = len(absences)
            absence_rate = (absence_count / dept_size * 100) if dept_size > 0 else 0
            
            if absence_rate > 30:  # More than 30% absent
                gaps.append({
                    "date": date_str,
                    "department": dept,
                    "absent_count": absence_count,
                    "department_size": dept_size,
                    "absence_rate": round(absence_rate, 1),
                    "severity": "HIGH" if absence_rate > 50 else "MEDIUM",
                    "absent_employees": absences
                })
    
    # Sort by date and severity
    gaps.sort(key=lambda x: (x["date"], -x["absence_rate"]))
    
    return {
        "coverage_gaps": gaps,
        "total_gaps": len(gaps),
        "days_analyzed": days_ahead,
        "high_severity": len([g for g in gaps if g["severity"] == "HIGH"])
    }