"""
Invoice SQLModel class representing the database table
Defines invoice entity with fields: id, user_id, customer_name, total_price, created_at
"""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Invoice(SQLModel, table=True):
    """Invoice database model"""
    __tablename__ = "invoices"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    customer_name: Optional[str] = Field(default=None)
    total_price: float = Field(default=0.0, ge=0.0)  # Auto-calculated, must be >= 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
