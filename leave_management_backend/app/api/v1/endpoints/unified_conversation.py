from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.database import get_db
from app.models.user import User
from app.models.leave import Leave, LeaveStatus
from app.api.deps import get_current_user
from app.services.unified_ai_service import UnifiedAIService
from app.schemas.leave import ConversationRequest, ConversationResponse
from app.services.policy_rag_service import PolicyRAGService


router = APIRouter()

@router.post("/conversation", response_model=ConversationResponse)
@router.post("/conversation", response_model=ConversationResponse)
def unified_conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified conversational interface for all leave management operations.
    """
    
    ai_service = UnifiedAIService()
    
    # Build user context
    user_context = {
        "user_id": current_user.id,
        "role": current_user.role,
        "department": current_user.department,
        "position": current_user.position,
        "full_name": current_user.full_name,
        "is_manager": current_user.role in ["MANAGER", "HR"],
        "is_hr": current_user.role == "HR"
    }
    
    # Parse intent with AI
    parsed = ai_service.parse_conversation(
        text=request.message,
        chat_history=[msg.dict() for msg in request.chat_history],
        user_context=user_context
    )
    
    intent = parsed["intent"]
    
    # ROLE-BASED INTENT CORRECTION
    if intent == "APPROVE_REJECT" and not user_context["is_manager"]:
        parsed["intent"] = "QUERY_LEAVES"
        if not parsed.get("status"):
            parsed["status"] = "PENDING"
        if not parsed.get("employee_name"):
            parsed["employee_name"] = user_context["full_name"]
        intent = "QUERY_LEAVES"
        print(f"Intent corrected from APPROVE_REJECT to QUERY_LEAVES for employee {user_context['full_name']}")
    
    if intent == "TEAM_STATUS" and not user_context["is_manager"]:
        parsed["intent"] = "QUERY_LEAVES"
        intent = "QUERY_LEAVES"
    
    if intent == "ANALYTICS" and not user_context["is_hr"]:
        parsed["intent"] = "QUERY_LEAVES"
        intent = "QUERY_LEAVES"
    
    # Route to appropriate handler
    try:
        if intent == "REQUEST_LEAVE":
            result = _handle_leave_request(db, current_user, parsed, ai_service)
        
        elif intent == "APPROVE_REJECT":
            if not user_context["is_manager"]:
                raise HTTPException(
                    status_code=403, 
                    detail="Only managers and HR can approve/reject leaves"
                )
            
            # KEY FIX: Route CHECK_PENDING to query handler
            action = parsed.get("action")
            if action == "CHECK_PENDING":
                # Convert to QUERY_LEAVES with PENDING filter
                parsed["status"] = "PENDING"
                parsed["intent"] = "QUERY_LEAVES"
                result = _handle_leave_query(db, current_user, parsed, user_context)
                # Keep intent as APPROVE_REJECT for response generation
                intent = "APPROVE_REJECT"
            else:
                # Handle actual approve/reject actions
                result = _handle_approval(db, current_user, parsed)
        
        elif intent == "QUERY_LEAVES":
            result = _handle_leave_query(db, current_user, parsed, user_context)
        
        elif intent == "CHECK_BALANCE":
            result = _handle_balance_check(db, current_user, parsed, user_context)
        
        elif intent == "ANALYTICS":
            if not user_context["is_hr"]:
                raise HTTPException(
                    status_code=403,
                    detail="Only HR can access analytics"
                )
            result = _handle_analytics(db, parsed)
        
        elif intent == "TEAM_STATUS":
            if not user_context["is_manager"]:
                raise HTTPException(
                    status_code=403,
                    detail="Only managers and HR can view team status"
                )
            result = _handle_team_status(db, current_user, parsed, user_context)
        
        else:
            result = {
                "message": "I can help you with leave requests, approvals, queries, and more. What would you like to do?"
            }
        
        # Generate natural response
        response_text = ai_service.generate_response(
            intent=intent,
            parsed=parsed,
            data=result,
            user_context=user_context
        )
        
        # Handle actions - filter based on user permissions
        actions = []
        suggested_actions = parsed.get("suggested_actions", [])
        
        if suggested_actions:
            for action in suggested_actions:
                if isinstance(action, dict):
                    action_text = action.get("text", "")
                elif isinstance(action, str):
                    action_text = action
                else:
                    action_text = str(action)
                
                # Skip approval actions for non-managers
                if not user_context["is_manager"] and any(approve_word in action_text.lower() for approve_word in ["approve", "reject", "pending approval"]):
                    continue
                    
                # Skip analytics actions for non-HR
                if not user_context["is_hr"] and any(analytics_word in action_text.lower() for analytics_word in ["analytics", "trends", "reports"]):
                    continue
                    
                # Skip team actions for non-managers
                if not user_context["is_manager"] and any(team_word in action_text.lower() for team_word in ["team", "department"]):
                    continue
                
                actions.append(action_text)
        
        return ConversationResponse(
            response=response_text,
            intent=intent,
            data=result,
            actions=actions
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to process request")


def _handle_leave_request(
    db: Session,
    current_user: User,
    parsed: Dict,
    ai_service: UnifiedAIService
) -> Dict:
    """Handle leave request with AI-suggested responsible person AND policy compliance check"""
    from datetime import datetime
    from app.config import settings
    
    # Calculate notice period
    notice_days = 0
    if parsed.get("start_date"):
        notice_days = (parsed["start_date"] - datetime.now().date()).days
        parsed["notice_days"] = notice_days
    
    # POLICY COMPLIANCE CHECK - This is the key addition
    policy_compliance = None
    if parsed.get("is_complete") and parsed.get("start_date") and parsed.get("end_date"):
        try:
            rag_service = PolicyRAGService(db, settings.GROQ_API_KEY)
            
            user_context = {
                "user_id": current_user.id,
                "role": current_user.role.value,
                "department": current_user.department,
                "position": current_user.position
            }
            
            policy_compliance = rag_service.check_policy_compliance(
                leave_request=parsed,
                user_context=user_context
            )
            
            # If there are violations, mark as needs clarification
            if not policy_compliance.get("compliant"):
                parsed["needs_clarification"] = True
                parsed["is_complete"] = False
                
        except Exception as e:
            print(f"Policy compliance check failed: {e}")
            # Continue without policy check if it fails
            policy_compliance = None
    
    # Get suggested responsible persons using AI
    suggested_persons = []
    
    if parsed.get("start_date") and parsed.get("end_date"):
        # Find colleagues with similar roles
        similar_role_colleagues = db.query(User).filter(
            User.department == current_user.department,
            User.position == current_user.position,
            User.id != current_user.id
        ).all()
        
        # If no exact matches, get same department
        if not similar_role_colleagues:
            similar_role_colleagues = db.query(User).filter(
                User.department == current_user.department,
                User.id != current_user.id
            ).limit(5).all()
        
        # Filter by availability during leave period
        for colleague in similar_role_colleagues:
            # Check if colleague is available
            conflicting = db.query(Leave).filter(
                Leave.employee_id == colleague.id,
                Leave.status == LeaveStatus.APPROVED,
                Leave.start_date <= parsed["end_date"],
                Leave.end_date >= parsed["start_date"]
            ).count()
            
            if conflicting == 0:
                suggested_persons.append({
                    "id": colleague.id,
                    "name": colleague.full_name,
                    "position": colleague.position,
                    "department": colleague.department,
                    "match_score": 100 if colleague.position == current_user.position else 80,
                    "reason": "Same role" if colleague.position == current_user.position else "Same department"
                })
        
        # Sort by match score
        suggested_persons.sort(key=lambda x: x["match_score"], reverse=True)
        suggested_persons = suggested_persons[:3]
    
    # Calculate team impact
    team_members = db.query(User).filter(
        User.department == current_user.department,
        User.id != current_user.id
    ).all()
    
    team_data = []
    if parsed.get("start_date") and parsed.get("end_date"):
        for member in team_members:
            on_leave = db.query(Leave).filter(
                Leave.employee_id == member.id,
                Leave.status == LeaveStatus.APPROVED,
                Leave.start_date <= parsed["end_date"],
                Leave.end_date >= parsed["start_date"]
            ).first()
            
            team_data.append({
                "name": member.full_name,
                "on_leave": on_leave is not None
            })
    
    impact = ai_service.calculate_impact_score(
        leave_data=parsed,
        team_data=team_data
    )
    
    # Get current leave balance
    from app.models.leave_balance import LeaveBalance
    current_year = datetime.now().year
    
    balance = None
    if parsed.get("leave_type"):
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == current_user.id,
            LeaveBalance.year == current_year,
            LeaveBalance.leave_type == parsed["leave_type"]
        ).first()
    
    return {
        "leave_data": parsed,
        "suggested_responsible_persons": suggested_persons,
        "team_impact": impact,
        "leave_balance": {
            "total": balance.total_allocated if balance else 0,
            "used": balance.used if balance else 0,
            "available": balance.available if balance else 0
        } if balance else None,
        "is_complete": parsed.get("is_complete", False),
        "needs_clarification": parsed.get("needs_clarification", False),
        "policy_compliance": policy_compliance  # NEW: Include policy compliance
    }


# Update _handle_approval to check policy compliance before approving
def _handle_approval(db: Session, current_user: User, parsed: Dict) -> Dict:
    """Handle leave approval/rejection WITH policy compliance check"""
    from datetime import datetime
    from app.models.leave_balance import LeaveBalance
    from app.config import settings
    
    leave_id = parsed.get("leave_id")
    action = parsed.get("action")
    
    # If no leave_id, try to find by employee name
    if not leave_id and parsed.get("employee_name"):
        employee = db.query(User).filter(
            User.full_name.ilike(f"%{parsed['employee_name']}%")
        ).first()
        
        if employee:
            # Get most recent pending leave
            leave = db.query(Leave).filter(
                Leave.employee_id == employee.id,
                Leave.status == LeaveStatus.PENDING
            ).order_by(Leave.created_at.desc()).first()
            
            if leave:
                leave_id = leave.id
    
    if not leave_id:
        return {
            "success": False,
            "message": "Could not identify the leave request"
        }
    
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    
    if not leave:
        return {"success": False, "message": "Leave not found"}
    
    # Permission check - managers can only approve their team members
    employee = db.query(User).filter(User.id == leave.employee_id).first()
    
    if current_user.role == "MANAGER":
        if employee.manager_id != current_user.id:
            return {
                "success": False,
                "message": "You can only approve leaves for your team members"
            }
    
    if leave.status != LeaveStatus.PENDING:
        return {
            "success": False,
            "message": f"Leave is already {leave.status.value.lower()}"
        }
    
    # POLICY COMPLIANCE CHECK BEFORE APPROVAL
    if action == "APPROVE":
        try:
            rag_service = PolicyRAGService(db, settings.GROQ_API_KEY)
            
            user_context = {
                "user_id": employee.id,
                "role": employee.role.value,
                "department": employee.department,
                "position": employee.position
            }
            
            leave_request_dict = {
                "leave_type": leave.leave_type.value,
                "start_date": leave.start_date,
                "end_date": leave.end_date,
                "reason": leave.reason,
                "notice_days": (leave.start_date - leave.created_at.date()).days
            }
            
            policy_compliance = rag_service.check_policy_compliance(
                leave_request=leave_request_dict,
                user_context=user_context
            )
            
            # If policy violations exist, prevent approval
            if not policy_compliance.get("compliant"):
                violations = policy_compliance.get("violations", [])
                return {
                    "success": False,
                    "message": "Cannot approve: Policy violations detected",
                    "violations": violations,
                    "relevant_policies": policy_compliance.get("relevant_policies", [])
                }
            
            # Show warnings but allow approval
            warnings = policy_compliance.get("warnings", [])
            
        except Exception as e:
            print(f"Policy compliance check failed during approval: {e}")
            warnings = []
    
    # Update leave status
    if action == "APPROVE":
        leave.status = LeaveStatus.APPROVED
        leave.manager_comments = parsed.get("comments")
        leave.decision_date = datetime.now()
        
        # Update leave balance
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == leave.employee_id,
            LeaveBalance.leave_type == leave.leave_type,
            LeaveBalance.year == datetime.now().year
        ).first()
        
        if balance:
            duration = (leave.end_date - leave.start_date).days + 1
            balance.used += duration
            balance.available -= duration
    
    elif action == "REJECT":
        leave.status = LeaveStatus.REJECTED
        leave.manager_comments = parsed.get("comments") or parsed.get("rejection_reason")
        leave.decision_date = datetime.now()
    
    db.commit()
    
    result = {
        "success": True,
        "action": action.lower(),
        "leave": {
            "id": leave.id,
            "employee": employee.full_name,
            "type": leave.leave_type.value,
            "dates": f"{leave.start_date} to {leave.end_date}",
            "status": leave.status.value
        }
    }
    
    if action == "APPROVE" and warnings:
        result["warnings"] = warnings
    
    return result


def _handle_leave_query(
    db: Session,
    current_user: User,
    parsed: Dict,
    user_context: Dict
) -> Dict:
    """Handle leave queries with permission filtering"""
    from datetime import date, timedelta
    
    query = db.query(Leave, User).join(User, Leave.employee_id == User.id)
    
    # Permission-based filtering
    if not user_context["is_manager"]:
        # Regular employees can only see their own leaves
        query = query.filter(Leave.employee_id == current_user.id)
    else:
        # Managers can see their team, HR can see all
        if user_context["role"] == "MANAGER":
            team_members = db.query(User).filter(
                User.manager_id == current_user.id
            ).all()
            team_ids = [m.id for m in team_members] + [current_user.id]
            query = query.filter(Leave.employee_id.in_(team_ids))
        # HR can see all (no additional filter)
    
    # Apply date filters - handle both string and dict formats
    date_filter = parsed.get("date_filter")
    if date_filter:
        # Handle both string and dictionary formats
        if isinstance(date_filter, dict):
            filter_type = date_filter.get("type")
        else:
            filter_type = date_filter
        
        today = date.today()
        
        if filter_type == "TODAY":
            query = query.filter(
                Leave.start_date <= today,
                Leave.end_date >= today,
                Leave.status == LeaveStatus.APPROVED
            )
        elif filter_type == "THIS_WEEK":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            query = query.filter(
                Leave.start_date <= week_end,
                Leave.end_date >= week_start
            )
        elif filter_type == "THIS_MONTH":
            query = query.filter(
                Leave.start_date >= date(today.year, today.month, 1)
            )
    
    # Apply status filter - this is key for "pending approval" queries
    status_filter = parsed.get("status")
    if status_filter:
        try:
            # Convert string to LeaveStatus enum
            if isinstance(status_filter, str):
                status_filter = LeaveStatus[status_filter.upper()]
            query = query.filter(Leave.status == status_filter)
        except (KeyError, AttributeError):
            # If status conversion fails, continue without status filter
            pass
    
    # Other filters
    if parsed.get("department") and user_context["is_hr"]:
        query = query.filter(User.department == parsed["department"])
    
    if parsed.get("leave_type"):
        query = query.filter(Leave.leave_type == parsed["leave_type"])
    
    results = query.all()
    
    leaves = []
    for leave, user in results:
        duration = (leave.end_date - leave.start_date).days + 1
        leaves.append({
            "id": leave.id,
            "employee_name": user.full_name,
            "department": user.department,
            "leave_type": leave.leave_type.value,
            "start_date": leave.start_date.isoformat(),
            "end_date": leave.end_date.isoformat(),
            "duration": duration,
            "status": leave.status.value,
            "reason": leave.reason
        })
    
    return {"leaves": leaves, "count": len(leaves)}


def _handle_balance_check(
    db: Session,
    current_user: User,
    parsed: Dict,
    user_context: Dict
) -> Dict:
    """Handle leave balance queries with permission filtering"""
    from datetime import datetime
    from app.models.leave_balance import LeaveBalance
    
    current_year = datetime.now().year
    
    query = db.query(LeaveBalance, User).join(
        User, LeaveBalance.employee_id == User.id
    ).filter(LeaveBalance.year == current_year)
    
    # Permission filtering
    if not user_context["is_manager"]:
        query = query.filter(LeaveBalance.employee_id == current_user.id)
    elif user_context["role"] == "MANAGER":
        team_members = db.query(User).filter(
            User.manager_id == current_user.id
        ).all()
        team_ids = [m.id for m in team_members] + [current_user.id]
        query = query.filter(LeaveBalance.employee_id.in_(team_ids))
    
    # Department filter (HR only)
    if parsed.get("department") and user_context["is_hr"]:
        query = query.filter(User.department == parsed["department"])
    
    results = query.all()
    
    balances = []
    for balance, user in results:
        balances.append({
            "employee_name": user.full_name,
            "department": user.department,
            "leave_type": balance.leave_type.value,
            "total": balance.total_allocated,
            "used": balance.used,
            "available": balance.available
        })
    
    return {"balances": balances, "count": len(balances)}


def _handle_analytics(db: Session, parsed: Dict) -> Dict:
    """Handle analytics queries (HR only)"""
    from sqlalchemy import func, extract
    from datetime import datetime
    
    current_year = datetime.now().year
    result = {}
    
    # Monthly distribution
    monthly_stats = db.query(
        extract('month', Leave.start_date).label('month'),
        func.count(Leave.id).label('count')
    ).filter(
        extract('year', Leave.start_date) == current_year
    ).group_by('month').all()
    
    result["monthly_distribution"] = [
        {"month": int(m), "count": c} for m, c in monthly_stats
    ]
    
    # Department stats
    dept_stats = db.query(
        User.department,
        func.count(Leave.id).label('leave_count')
    ).join(Leave, User.id == Leave.employee_id).filter(
        extract('year', Leave.start_date) == current_year
    ).group_by(User.department).all()
    
    result["department_stats"] = [
        {"department": d, "leave_count": c} for d, c in dept_stats
    ]
    
    return result


def _handle_team_status(
    db: Session,
    current_user: User,
    parsed: Dict,
    user_context: Dict
) -> Dict:
    """Handle team status queries"""
    from datetime import date
    
    today = date.today()
    
    query = db.query(User)
    
    # Permission-based filtering
    if user_context["role"] == "MANAGER":
        team_members = db.query(User).filter(
            User.manager_id == current_user.id
        ).all()
        team_ids = [m.id for m in team_members]
        query = query.filter(User.id.in_(team_ids))
    else:  # HR
        query = query.filter(User.role != "HR")
    
    if parsed.get("department"):
        query = query.filter(User.department == parsed["department"])
    
    users = query.all()
    
    team_status = []
    for user in users:
        on_leave = db.query(Leave).filter(
            Leave.employee_id == user.id,
            Leave.status == LeaveStatus.APPROVED,
            Leave.start_date <= today,
            Leave.end_date >= today
        ).first()
        
        team_status.append({
            "employee_name": user.full_name,
            "department": user.department,
            "position": user.position,
            "status": "On Leave" if on_leave else "Available",
            "leave_type": on_leave.leave_type.value if on_leave else None
        })
    
    return {
        "team_status": team_status,
        "total": len(team_status),
        "on_leave": len([s for s in team_status if s["status"] == "On Leave"]),
        "available": len([s for s in team_status if s["status"] == "Available"])
    }