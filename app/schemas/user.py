"""
User Pydantic DTOs for request/response schemas
Contains UserCreate, UserRead, UserUpdate schemas for API validation and serialization
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^05\d{8}$")  # Phone format: 0597865441
    shop_type: str = Field(min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(min_length=8, max_length=100)


class UserRead(UserBase):
    """Schema for reading user data (response model)"""
    id: int
    role: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user data (partial update)"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^05\d{8}$")
    shop_type: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, pattern=r"^(active|suspended|banned)$")
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['active', 'suspended', 'banned']:
            raise ValueError('Status must be one of: active, suspended, banned')
        return v
