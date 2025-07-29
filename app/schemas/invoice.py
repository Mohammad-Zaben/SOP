"""
Invoice Pydantic DTOs for request/response schemas
Contains InvoiceCreate, InvoiceRead schemas for API validation and serialization
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .invoice_item import InvoiceItemCreate, InvoiceItemRead


class InvoiceBase(BaseModel):
    """Base invoice schema with common fields"""
    customer_name: Optional[str] = Field(None, max_length=200)


class InvoiceCreate(InvoiceBase):
    """Schema for creating a new invoice"""
    items: List[InvoiceItemCreate] = Field(min_items=1)


class InvoiceRead(InvoiceBase):
    """Schema for reading invoice data (response model)"""
    id: int
    total_price: float
    created_at: datetime
    items: List[InvoiceItemRead]
    
    class Config:
        orm_mode = True
