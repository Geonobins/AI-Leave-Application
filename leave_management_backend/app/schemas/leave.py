from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date
from app.models.leave import LeaveType, LeaveStatus

# ============================================================================
# Unified Conversation Schemas
# ============================================================================

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")

class ConversationRequest(BaseModel):
    message: str = Field(..., description="User's message")
    chat_history: List[ChatMessage] = Field(default=[], description="Previous conversation")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class ConversationResponse(BaseModel):
    response: str = Field(..., description="AI-generated response")
    intent: str = Field(..., description="Detected intent")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Structured data returned")
    actions: List[str] = Field(default=[], description="Suggested next actions")

# ============================================================================
# Legacy Schemas (for backward compatibility)
# ============================================================================

class LeaveCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None
    responsible_person_id: Optional[int] = None

class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str]
    responsible_person_id: Optional[int]
    status: LeaveStatus
    manager_id: Optional[int]
    manager_comments: Optional[str]
    
    class Config:
        from_attributes = True

class LeaveApproval(BaseModel):
    leave_id: int
    approved: bool
    comments: Optional[str] = None

class ResponsiblePersonSuggestion(BaseModel):
    id: int
    name: str
    position: str
    department: str
    match_score: int
    reason: str