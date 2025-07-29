"""
Product SQLModel class representing the database table
Defines product entity with fields: id, user_id, name, barcode, category, quantity, price, threshold, description, created_at
"""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Product(SQLModel, table=True):
    """Product database model"""
    __tablename__ = "products"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(...)
    barcode: str = Field(unique=True, index=True)
    category: Optional[str] = Field(default=None)
    quantity: int = Field(ge=0)  # Must be >= 0
    price: float = Field(ge=0.0)  # Must be >= 0
    threshold: int = Field(default=0, ge=0)  # Alert when running out, must be >= 0
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
