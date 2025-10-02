from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.leave import Leave, LeaveStatus
from app.models.leave_balance import LeaveBalance
from app.schemas.leave import (
    LeaveCreate, LeaveResponse
)
from app.schemas.leave_balance import LeaveBalanceResponse
from app.api.deps import get_current_user
from app.services.ai_service import AIService
from datetime import datetime

router = APIRouter()

# @router.post("/leaves/conversation", response_model=LeaveConversationResponse)
# def leave_conversation(
#     request: LeaveConversationRequest,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # Initialize AI service (will auto-detect OpenAI or Ollama)
#     ai_service = AIService()

#     # Parse with LLM
#     parsed = ai_service.parse_leave_request_with_context(
#         text=request.message,
#         chat_history=[msg.dict() for msg in request.chat_history],
#         user_context=request.context or {}
#     )

#     # Get suggested persons
#     suggested_persons = []
#     if parsed.get("start_date") and parsed.get("end_date"):
#         suggested_persons_query = db.query(User).filter(
#             User.department == current_user.department,
#             User.id != current_user.id
#         ).limit(3).all()

#         for person in suggested_persons_query:
#             conflicting = db.query(Leave).filter(
#                 Leave.employee_id == person.id,
#                 Leave.status == LeaveStatus.APPROVED,
#                 Leave.start_date <= parsed["end_date"],
#                 Leave.end_date >= parsed["start_date"]
#             ).count()

#             if conflicting == 0:
#                 suggested_persons.append({
#                     "id": person.id,
#                     "name": person.full_name,
#                     "position": person.position
#                 })

#     # Generate response
#     response_text = ai_service.generate_conversational_response(parsed, suggested_persons)

#     return LeaveConversationResponse(
#         response=response_text,
#         leave_data=parsed,
#         is_complete=parsed.get("is_complete", False),
#         needs_clarification=parsed.get("needs_clarification", False),
#         suggested_responsible_persons=suggested_persons
#     )

# @router.post("/leaves/natural", response_model=LeaveDraftResponse)
# def create_leave_natural(
#     request: LeaveNaturalRequest,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Parse natural language leave request (legacy endpoint)"""
#     ai_service = AIService()
#     parsed = ai_service.parse_leave_request_with_context(
#         text=request.request_text,
#         chat_history=[],
#         user_context={}
#     )

#     # Suggest responsible persons
#     suggested_persons = db.query(User).filter(
#         User.department == current_user.department,
#         User.id != current_user.id
#     ).limit(3).all()

#     return LeaveDraftResponse(
#         leave_type=parsed.get("leave_type"),
#         start_date=parsed.get("start_date"),
#         end_date=parsed.get("end_date"),
#         reason=parsed.get("reason"),
#         missing_fields=parsed.get("missing_fields", []),
#         needs_clarification=parsed.get("needs_clarification", False),
#         clarification_question=parsed.get("clarification_question"),
#         suggested_responsible_persons=[
#             {"id": p.id, "name": p.full_name, "position": p.position}
#             for p in suggested_persons
#         ]
#     )

@router.post("/leaves", response_model=LeaveResponse)
def create_leave(
    leave: LeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit leave request"""
    # Check leave balance
    current_year = datetime.now().year
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_user.id,
        LeaveBalance.year == current_year,
        LeaveBalance.leave_type == leave.leave_type
    ).first()

    duration = (leave.end_date - leave.start_date).days + 1

    if balance and balance.available < duration:
        raise HTTPException(status_code=400, detail="Insufficient leave balance")

    # Create leave request
    db_leave = Leave(
        employee_id=current_user.id,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        responsible_person_id=leave.responsible_person_id,
        manager_id=current_user.manager_id,
        status=LeaveStatus.PENDING
    )

    db.add(db_leave)
    db.commit()
    db.refresh(db_leave)

    return db_leave

@router.get("/leaves", response_model=List[LeaveResponse])
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all leaves for current user"""
    leaves = db.query(Leave).filter(Leave.employee_id == current_user.id).all()
    return leaves

@router.get("/leaves/{leave_id}", response_model=LeaveResponse)
def get_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific leave details"""
    leave = db.query(Leave).filter(
        Leave.id == leave_id,
        Leave.employee_id == current_user.id
    ).first()

    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    return leave

@router.get("/leave-balances", response_model=List[LeaveBalanceResponse])
def get_leave_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get leave balances for current user"""
    current_year = datetime.now().year
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_user.id,
        LeaveBalance.year == current_year
    ).all()

    return balances