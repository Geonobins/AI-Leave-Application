from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.EMPLOYEE
    department: Optional[str] = None
    position: Optional[str] = None
    manager_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    department: str
    position: str
    manager_id: Optional[int] = None
    is_active: bool  # Make sure this exists

    class Config:
        from_attributes = True
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None