from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.schemas.user import UserResponse


class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    role: str
    joined_at: datetime
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)


class GroupCreate(GroupBase):
    member_emails: Optional[List[EmailStr]] = Field(default_factory=list, description="Optional emails of initial members to invite")


class GroupResponse(GroupBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    members: List[GroupMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)


class GroupMemberAdd(BaseModel):
    email: EmailStr
    role: str = Field(default="MEMBER", pattern="^(ADMIN|MEMBER)$")

