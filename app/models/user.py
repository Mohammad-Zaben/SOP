"""
User SQLModel class representing the database table
Defines user entity with fields: id, username, password, role, email, phone, shop_type, location, status, created_at
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """User status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class User(SQLModel, table=True):
    """User database model"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(min_length=3, unique=True, index=True)
    password: str = Field(min_length=8)  # Hashed password, not exposed in read
    role: UserRole = Field(default=UserRole.USER)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    phone: Optional[str] = Field(default=None)
    shop_type: str = Field(...)  # Required field for shop type
    location: Optional[str] = Field(default=None)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
