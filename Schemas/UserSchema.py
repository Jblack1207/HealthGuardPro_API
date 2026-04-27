from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_admin: bool
    is_active: bool
    firebase_uid: str
    
    class Config:
        from_attributes = True  # SQLAlchemy -> Pydantic conversion

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(min_length=8)
    is_admin: bool = False
    is_active: bool = True
    firebase_uid: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] | None = None
    email: Optional[EmailStr] | None = None
    first_name: Optional[str] | None = None
    last_name: Optional[str] | None = None
    password: Optional[str] | None = Field(default=None, min_length=8)
    is_admin: Optional[bool] | None = None
    is_active: Optional[bool] | None = None
    firebase_uid: Optional[str] | None = None

class SyncUserRequest(BaseModel):
    username: str
    first_name: str
    last_name: str
